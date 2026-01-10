"""
RAG ingestion utilities: extract text, chunk, embed, and store in Chroma
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
        encodings_to_try = ["utf-8", "cp1252", "latin-1"]
        for enc in encodings_to_try:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except Exception:
                continue
        try:
            with open(file_path, "rb") as f:
                raw = f.read()
                return raw.decode("utf-8", errors="replace")
        except Exception:
            return ""


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """Simple whitespace chunker."""
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
    """Generate embeddings (delegates to embeddings module)."""
    from app.rag.embeddings import generate_embeddings
    return generate_embeddings(texts, model_name=model_name)


def store_in_chroma(doc_id_prefix: str, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Store documents in Chroma."""
    from app.db.chroma_client import get_collection, persist_client
    
    collection = get_collection("servibot_docs")
    
    ids = [f"{doc_id_prefix}_{i}" for i in range(len(texts))]
    if metadatas is None:
        metadatas = [{} for _ in texts]
    
    try:
        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        persist_client()
        logger.info(f"✅ Stored {len(texts)} documents")
    except Exception as e:
        logger.exception(f"❌ Error adding to Chroma: {e}")
        raise
    
    return {"collection": "servibot_docs", "count": len(texts)}


def delete_file_from_chroma(file_id: str) -> Dict[str, Any]:
    """Delete file chunks from Chroma."""
    from app.db.chroma_client import get_collection, persist_client
    
    try:
        collection = get_collection("servibot_docs")
    except Exception as e:
        logger.error(f"Failed to get collection: {e}")
        return {"status": "error", "message": f"Collection error: {e}"}
    
    try:
        results = collection.get(where={"file_id": file_id})
        ids_to_delete = results.get("ids", [])
        
        if not ids_to_delete:
            return {"status": "success", "deleted": 0, "message": "No vectors found"}
        
        collection.delete(ids=ids_to_delete)
        persist_client()
        
        logger.info(f"✅ Deleted {len(ids_to_delete)} vectors")
        return {"status": "success", "deleted": len(ids_to_delete)}
        
    except Exception as e:
        logger.exception(f"❌ Error deleting: {e}")
        return {"status": "error", "message": f"Delete failed: {e}"}


def clear_all_chroma() -> Dict[str, Any]:
    """Clear all documents from Chroma."""
    from app.db.chroma_client import get_chroma_client, persist_client, reset_client
    
    try:
        client = get_chroma_client()
        collection_name = "servibot_docs"
        
        try:
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection {collection_name}")
        except ValueError:
            logger.info(f"Collection did not exist")
        
        client.create_collection(name=collection_name)
        persist_client()
        reset_client()
        
        logger.info("✅ Cleared all vectors")
        return {"status": "success", "message": "All vectors cleared"}
        
    except Exception as e:
        logger.exception(f"❌ Error clearing: {e}")
        return {"status": "error", "message": f"Clear failed: {e}"}


def index_file(file_path: str, file_id: Optional[str] = None) -> Dict[str, Any]:
    """Full pipeline: extract -> chunk -> embed -> store."""
    if not file_id:
        file_id = Path(file_path).stem

    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}

    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {"status": "error", "message": "File is empty"}
        logger.info(f"Indexing: {file_path} ({file_size} bytes)")
    except Exception as e:
        return {"status": "error", "message": f"Error checking file: {e}"}

    try:
        text = extract_text(file_path)
        if not text or not text.strip():
            return {"status": "error", "message": "No text extracted"}
    except Exception as e:
        logger.exception(f"Extraction error: {e}")
        return {"status": "error", "message": f"Extraction failed: {str(e)[:200]}"}

    try:
        chunks = chunk_text(text)
        if not chunks:
            return {"status": "error", "message": "No chunks created"}
        logger.info(f"Created {len(chunks)} chunks")
    except Exception as e:
        logger.exception(f"Chunking error: {e}")
        return {"status": "error", "message": f"Chunking failed: {str(e)[:200]}"}

    try:
        embeddings = embed_texts(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")
    except Exception as e:
        logger.exception(f"Embedding error: {e}")
        return {"status": "error", "message": f"Embedding failed: {str(e)[:200]}"}

    metadatas = [{"source": os.path.basename(file_path), "chunk_index": i, "file_id": file_id} for i in range(len(chunks))]

    try:
        res = store_in_chroma(doc_id_prefix=file_id, texts=chunks, embeddings=embeddings, metadatas=metadatas)
        logger.info(f"✅ Indexed {res.get('count', 0)} chunks")
        return {"status": "success", "indexed": res.get("count", 0), "collection": res.get("collection")}
    except Exception as e:
        logger.exception(f"Storage error: {e}")
        return {"status": "error", "message": f"Storage failed: {str(e)[:200]}"}
