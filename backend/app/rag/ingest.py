"""
RAG ingestion utilities: extract text, chunk, embed, and store in Chroma (POC)
"""
from typing import List, Dict, Any, Optional
import os
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using pypdf as a fallback method."""
    try:
        from pypdf import PdfReader
    except Exception:
        logger.warning("pypdf not available; returning empty text")
        return ""

    text_chunks: List[str] = []
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            if txt:
                text_chunks.append(txt)
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        return ""

    return "\n\n".join(text_chunks)


def extract_text(file_path: str) -> str:
    """Dispatch extraction based on file extension."""
    p = Path(file_path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    else:
        # For images, try OCR
        if ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
            try:
                from PIL import Image
                import pytesseract
            except Exception:
                logger.warning("PIL or pytesseract not available; returning empty text for image")
                return ""
            try:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
                return text
            except Exception as e:
                logger.error(f"OCR error for {file_path}: {e}")
                return ""
        # For text-like files
        # Try common encodings to avoid mojibake (utf-8, cp1252/latin-1)
        encodings_to_try = ["utf-8", "cp1252", "latin-1"]
        for enc in encodings_to_try:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except Exception:
                continue
        # As a last resort, read bytes and decode replacing errors
        try:
            with open(file_path, "rb") as f:
                raw = f.read()
                return raw.decode("utf-8", errors="replace")
        except Exception:
            return ""


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """Simple whitespace chunker.

    Splits text into chunks of approximately `chunk_size` characters with `overlap`.
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if overlap is None:
        overlap = settings.CHUNK_OVERLAP

    if not text:
        return []

    text = text.replace("\r\n", "\n")
    start = 0
    chunks: List[str] = []
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap if end < length else end
    return chunks


def embed_texts(texts: List[str], model_name: Optional[str] = None) -> List[List[float]]:
    """Generate embeddings for a list of texts using sentence-transformers (local) as default.

    Returns list of embeddings (list of floats).
    """
    if model_name is None:
        model_name = "all-MiniLM-L6-v2"

    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        logger.error("sentence-transformers not available; cannot embed texts")
        raise

    # Prefer CPU to avoid CUDA/meta tensor issues on some environments.
    # Try to instantiate the model with proper device handling
    model = None
    try:
        import torch
        # Force CPU and disable meta tensors
        torch.set_default_device("cpu")
        
        try:
            # Try with explicit device first
            model = SentenceTransformer(model_name, device="cpu")
            logger.debug(f"Loaded {model_name} on CPU")
        except (TypeError, RuntimeError) as e:
            # Fallback: load without device param, then move to CPU
            logger.debug(f"Fallback loading for {model_name}: {e}")
            model = SentenceTransformer(model_name)
            # Don't call .to() if model is already on meta device
            if hasattr(model, 'device') and str(model.device) != 'meta':
                try:
                    model = model.to("cpu")
                except Exception as move_err:
                    logger.debug(f"Could not move model to CPU: {move_err}")

        # Encode with explicit CPU device
        try:
            embeddings = model.encode(texts, show_progress_bar=False, device="cpu", batch_size=8)
        except TypeError:
            # Fallback for older sentence-transformers versions
            try:
                embeddings = model.encode(texts, show_progress_bar=False, batch_size=8)
            except Exception:
                # Last resort: simplest call
                embeddings = model.encode(texts, show_progress_bar=False)

    except Exception as e:
        logger.exception(f"Embedding attempt failed for model {model_name}: {e}")
        # Re-raise to be handled by caller
        raise

    # Convert to list of lists
    return [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]


def store_in_chroma(doc_id_prefix: str, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Store documents and embeddings in a Chroma collection (POC).

    This function is defensive: if chromadb is not available or persistence fails, it will log and raise.
    """
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
    except Exception as e:
        logger.error(f"chromadb not available: {e}")
        raise

    # Create client with persistence to VECTOR_DB_PATH if possible
    persist_dir = os.path.abspath(settings.VECTOR_DB_PATH)
    os.makedirs(persist_dir, exist_ok=True)

    # Try to create a persistent client using the recommended Settings import
    try:
        try:
            from chromadb.config import Settings as ChromaSettings
            client = chromadb.Client(ChromaSettings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
        except Exception:
            # Fallback if import path differs
            try:
                client = chromadb.Client(chromadb.config.Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
            except Exception:
                client = chromadb.Client()
    except Exception as e:
        logger.error(f"Failed to create chromadb client: {e}")
        raise

    collection_name = "servibot_docs"
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        collection = client.create_collection(name=collection_name)

    ids = [f"{doc_id_prefix}_{i}" for i in range(len(texts))]
    if metadatas is None:
        metadatas = [{} for _ in texts]

    try:
        collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
        # Persist if client supports it
        try:
            client.persist()
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"Error adding to Chroma collection: {e}")
        raise

    return {"collection": collection_name, "count": len(texts)}


def delete_file_from_chroma(file_id: str) -> Dict[str, Any]:
    """Delete all document chunks for a given file_id from the Chroma collection.
    
    Returns a summary dict with status and count of deleted items.
    """
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
    except Exception as e:
        logger.error(f"chromadb not available: {e}")
        return {"status": "error", "message": f"chromadb not available: {e}"}

    persist_dir = os.path.abspath(settings.VECTOR_DB_PATH)
    
    try:
        try:
            from chromadb.config import Settings as ChromaSettings
            client = chromadb.Client(ChromaSettings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
        except Exception:
            try:
                client = chromadb.Client(chromadb.config.Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
            except Exception:
                client = chromadb.Client()
    except Exception as e:
        logger.error(f"Failed to create chromadb client: {e}")
        return {"status": "error", "message": f"Failed to create client: {e}"}

    collection_name = "servibot_docs"
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        logger.warning(f"Collection {collection_name} not found: {e}")
        return {"status": "error", "message": f"Collection not found: {e}"}

    # Query all documents with this file_id in metadata
    try:
        results = collection.get(where={"file_id": file_id})
        ids_to_delete = results.get("ids", [])
        
        if not ids_to_delete:
            logger.info(f"No vectors found for file_id={file_id}")
            return {"status": "success", "deleted": 0, "message": "No vectors found"}
        
        collection.delete(ids=ids_to_delete)
        
        try:
            client.persist()
        except Exception:
            pass
            
        logger.info(f"Deleted {len(ids_to_delete)} vectors for file_id={file_id}")
        return {"status": "success", "deleted": len(ids_to_delete)}
        
    except Exception as e:
        logger.exception(f"Error deleting from Chroma: {e}")
        return {"status": "error", "message": f"Delete failed: {e}"}


def clear_all_chroma() -> Dict[str, Any]:
    """Clear all documents from the Chroma collection (nuclear option).
    
    Returns a summary dict with status.
    """
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
    except Exception as e:
        logger.error(f"chromadb not available: {e}")
        return {"status": "error", "message": f"chromadb not available: {e}"}

    persist_dir = os.path.abspath(settings.VECTOR_DB_PATH)
    
    try:
        try:
            from chromadb.config import Settings as ChromaSettings
            client = chromadb.Client(ChromaSettings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
        except Exception:
            try:
                client = chromadb.Client(chromadb.config.Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
            except Exception:
                client = chromadb.Client()
    except Exception as e:
        logger.error(f"Failed to create chromadb client: {e}")
        return {"status": "error", "message": f"Failed to create client: {e}"}

    collection_name = "servibot_docs"
    try:
        # Try to delete collection if it exists
        try:
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection {collection_name}")
        except ValueError:
            # Collection doesn't exist, that's fine
            logger.info(f"Collection {collection_name} did not exist, nothing to delete")
        
        # Recreate empty collection
        client.create_collection(name=collection_name)
        
        try:
            client.persist()
        except Exception:
            pass
            
        logger.info("Cleared all vectors from collection")
        return {"status": "success", "message": "All vectors cleared"}
        
    except Exception as e:
        logger.exception(f"Error clearing Chroma collection: {e}")
        return {"status": "error", "message": f"Clear failed: {e}"}


def index_file(file_path: str, file_id: Optional[str] = None) -> Dict[str, Any]:
    """Full pipeline: extract -> chunk -> embed -> store.

    Returns a summary dict with counts.
    """
    if not file_id:
        file_id = Path(file_path).stem

    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {"status": "error", "message": f"File not found: {file_path}"}

    # Check file size
    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.warning(f"File is empty: {file_path}")
            return {"status": "error", "message": "File is empty (0 bytes)"}
        logger.info(f"Indexing file: {file_path} ({file_size} bytes)")
    except Exception as e:
        logger.error(f"Error checking file size: {e}")
        return {"status": "error", "message": f"Error checking file: {e}"}

    # Extract text
    try:
        text = extract_text(file_path)
        if not text or not text.strip():
            logger.warning(f"No text extracted from {file_path} (possibly empty or unsupported format)")
            return {"status": "error", "message": "No text could be extracted from file. It may be empty, password-protected, or in an unsupported format."}
    except Exception as e:
        logger.exception(f"Error extracting text from {file_path}: {e}")
        return {"status": "error", "message": f"Text extraction failed: {str(e)[:200]}"}

    # Chunk text
    try:
        chunks = chunk_text(text)
        if not chunks:
            logger.warning(f"No chunks produced from {file_path}")
            return {"status": "error", "message": "No text chunks could be created from extracted text"}
        logger.info(f"Created {len(chunks)} chunks from {file_path}")
    except Exception as e:
        logger.exception(f"Error chunking text from {file_path}: {e}")
        return {"status": "error", "message": f"Text chunking failed: {str(e)[:200]}"}

    # Generate embeddings
    try:
        embeddings = embed_texts(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings for {file_path}")
    except Exception as e:
        logger.exception(f"Embedding failed for {file_path}: {e}")
        return {"status": "error", "message": f"Embedding failed: {str(e)[:200]}"}

    # Store in Chroma
    metadatas = [{"source": os.path.basename(file_path), "chunk_index": i, "file_id": file_id} for i in range(len(chunks))]

    try:
        res = store_in_chroma(doc_id_prefix=file_id, texts=chunks, embeddings=embeddings, metadatas=metadatas)
        logger.info(f"Successfully indexed {res.get('count', 0)} chunks for {file_path}")
        return {"status": "success", "indexed": res.get("count", 0), "collection": res.get("collection")}
    except Exception as e:
        logger.exception(f"Storing to Chroma failed for {file_path}: {e}")
        return {"status": "error", "message": f"Database storage failed: {str(e)[:200]}"}
