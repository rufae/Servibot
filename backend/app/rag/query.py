"""
RAG query utilities for semantic search
"""
from typing import List, Dict, Any, Optional
import logging

from app.db.chroma_client import get_collection
from app.rag.embeddings import embed_query

logger = logging.getLogger(__name__)


def semantic_search(
    query: str,
    top_k: int = 5,
    collection_name: str = "servibot_docs",
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Perform semantic search against the vector database.
    
    Args:
        query: Query text to search for
        top_k: Number of results to return
        collection_name: Name of the collection to query
        filter_metadata: Optional metadata filters (e.g., {"file_id": "doc123"})
        
    Returns:
        List of result dicts with keys: document, metadata, distance
    """
    if not query or not query.strip():
        logger.warning("Empty query provided for semantic search")
        return []
    
    try:
        # Generate query embedding
        logger.debug(f"Generating embedding for query: {query[:100]}...")
        query_embedding = embed_query(query)
        
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        # Get collection
        collection = get_collection(collection_name)
        
        # Build query parameters
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        
        if filter_metadata:
            query_params["where"] = filter_metadata
        
        # Execute query
        logger.debug(f"Querying collection '{collection_name}' with top_k={top_k}")
        query_result = collection.query(**query_params)
        
        # Parse results
        results = _parse_chroma_results(query_result, top_k)
        
        logger.info(f"✅ Found {len(results)} results for query")
        return results
        
    except Exception as e:
        logger.exception(f"❌ Error during semantic search: {e}")
        raise RuntimeError(f"Semantic search failed: {str(e)}")


def _parse_chroma_results(query_result: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
    """Parse ChromaDB query results into normalized format.
    
    Handles different ChromaDB API versions that return nested lists.
    """
    results = []
    
    docs_raw = query_result.get("documents", [])
    metas_raw = query_result.get("metadatas", [])
    dists_raw = query_result.get("distances", [])
    
    # Normalize: ChromaDB returns lists per query [[doc1, doc2, ...]]
    # Take first element if nested
    docs = docs_raw[0] if docs_raw and isinstance(docs_raw[0], list) else docs_raw
    metadatas = metas_raw[0] if metas_raw and isinstance(metas_raw[0], list) else metas_raw
    distances = dists_raw[0] if dists_raw and isinstance(dists_raw[0], list) else dists_raw
    
    # Build result objects
    for i in range(min(len(docs), top_k)):
        doc_text = docs[i] if i < len(docs) else None
        metadata = metadatas[i] if i < len(metadatas) else None
        distance = distances[i] if i < len(distances) else None
        
        results.append({
            "document": doc_text,
            "metadata": metadata,
            "distance": distance,
        })
    
    return results


def get_context_for_query(query: str, top_k: int = 3, max_chars: int = 2000) -> str:
    """Get formatted context string for a query to use in LLM prompts.
    
    Args:
        query: Query text
        top_k: Number of documents to retrieve
        max_chars: Maximum characters in context string
        
    Returns:
        Formatted context string with relevant documents
    """
    try:
        results = semantic_search(query, top_k=top_k)
        
        if not results:
            return "No relevant documents found in knowledge base."
        
        # Format context
        context_parts = []
        total_chars = 0
        
        for i, result in enumerate(results, 1):
            doc_text = result.get("document", "")
            metadata = result.get("metadata", {})
            
            if not doc_text:
                continue
            
            # Add source info if available
            source = metadata.get("source", "Unknown")
            chunk_idx = metadata.get("chunk_index", "?")
            
            context_part = f"[Document {i} - {source} chunk {chunk_idx}]\n{doc_text}\n"
            
            # Check if adding this would exceed limit
            if total_chars + len(context_part) > max_chars:
                # Truncate and stop
                remaining = max_chars - total_chars
                if remaining > 100:  # Only add if meaningful space left
                    context_parts.append(context_part[:remaining] + "...")
                break
            
            context_parts.append(context_part)
            total_chars += len(context_part)
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"Error getting context for query: {e}")
        return "Error retrieving context from knowledge base."
