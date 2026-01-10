"""
Embedding generation utilities using sentence-transformers
"""
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def generate_embeddings(
    texts: List[str],
    model_name: Optional[str] = None,
    batch_size: int = 8
) -> List[List[float]]:
    """Generate embeddings for a list of texts using sentence-transformers.
    
    Args:
        texts: List of text strings to embed
        model_name: Model to use (default: all-MiniLM-L6-v2)
        batch_size: Batch size for encoding
        
    Returns:
        List of embeddings (list of floats per text)
        
    Uses CPU-only mode for stability across environments.
    """
    if model_name is None:
        model_name = "all-MiniLM-L6-v2"
    
    if not texts:
        logger.warning("Empty text list provided for embedding")
        return []
    
    try:
        from sentence_transformers import SentenceTransformer
        import torch
    except ImportError as e:
        logger.error(f"Required libraries not available: {e}")
        raise RuntimeError("sentence-transformers or torch not installed")
    
    logger.info(f"🧠 Generating embeddings for {len(texts)} texts with {model_name}")
    
    try:
        # Force CPU to avoid CUDA/meta tensor issues
        torch.set_default_device("cpu")
        
        # Load model with explicit CPU device
        logger.debug(f"Loading model {model_name} on CPU...")
        model = SentenceTransformer(model_name, device="cpu")
        logger.debug(f"Model loaded on {model.device}")
        
        # Encode with explicit parameters for stability
        logger.debug(f"Encoding {len(texts)} texts...")
        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            device="cpu",
            batch_size=batch_size,
            convert_to_numpy=True
        )
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")
        
        # Convert to list of lists
        result = [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]
        return result
        
    except TypeError as te:
        # Fallback for older sentence-transformers versions
        logger.warning(f"⚠️ TypeError in encoding (older API), retrying without device param: {te}")
        try:
            embeddings = model.encode(
                texts,
                show_progress_bar=False,
                batch_size=batch_size,
                convert_to_numpy=True
            )
            result = [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]
            logger.info(f"✅ Generated {len(embeddings)} embeddings (fallback mode)")
            return result
        except Exception as fallback_err:
            logger.error(f"❌ Fallback encoding failed: {fallback_err}")
            raise
            
    except RuntimeError as re:
        if "meta" in str(re).lower() or "device" in str(re).lower():
            logger.error(f"❌ Device/meta tensor error: {re}")
            logger.error("This indicates CUDA issues. Ensure torch is CPU-only.")
        raise
        
    except Exception as e:
        logger.exception(f"❌ Unexpected error during embedding: {e}")
        raise RuntimeError(f"Embedding generation failed: {str(e)}")


def embed_query(query: str, model_name: Optional[str] = None) -> List[float]:
    """Generate embedding for a single query string.
    
    Args:
        query: Query text to embed
        model_name: Model to use (default: all-MiniLM-L6-v2)
        
    Returns:
        Single embedding as list of floats
    """
    if not query or not query.strip():
        logger.warning("Empty query provided for embedding")
        return []
    
    embeddings = generate_embeddings([query], model_name=model_name, batch_size=1)
    return embeddings[0] if embeddings else []
