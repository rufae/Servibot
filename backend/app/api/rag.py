"""
RAG API endpoints: index uploaded files and query the vector DB
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import logging

from app.core.config import settings
from app.rag.ingest import index_file
from app.rag.query import semantic_search
from app.db.chroma_client import get_chroma_client, get_collection

logger = logging.getLogger(__name__)
router = APIRouter()


class IndexRequest(BaseModel):
    file_id: Optional[str] = None
    filename: Optional[str] = None


class IndexResponse(BaseModel):
    status: str
    indexed: int = 0
    collection: Optional[str] = None
    message: Optional[str] = None


@router.post("/rag/index", response_model=IndexResponse)
async def rag_index(req: IndexRequest):
    """Index a previously uploaded file into the RAG vector store."""
    try:
        if req.filename:
            file_path = os.path.join(settings.UPLOAD_DIR, req.filename)
        elif req.file_id:
            file_path = os.path.join(settings.UPLOAD_DIR, req.file_id)
        else:
            raise HTTPException(status_code=400, detail="filename or file_id is required")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        res = index_file(file_path, file_id=req.file_id or None)
        return IndexResponse(**res)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None


class QueryResponse(BaseModel):
    query: str
    results: list


@router.post("/rag/query", response_model=QueryResponse)
async def rag_query(req: QueryRequest):
    """Perform a semantic search against the vector DB."""
    try:
        top_k = req.top_k or settings.TOP_K_RESULTS
        
        results = semantic_search(
            query=req.query,
            top_k=top_k,
            collection_name="servibot_docs"
        )
        
        return QueryResponse(query=req.query, results=results)
        
    except Exception as e:
        logger.error(f"Error running RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/vectors")
async def debug_vectors():
    """Debug endpoint: list collections with samples."""
    try:
        client = get_chroma_client()
        persist_dir = os.path.abspath(settings.VECTOR_DB_PATH)
        
        collections = []
        try:
            cols = client.list_collections()
        except Exception:
            cols = []
        
        for c in cols:
            name = c.get("name") if isinstance(c, dict) else getattr(c, "name", str(c))
            entry = {"name": name, "count": None, "samples": []}
            
            try:
                coll = get_collection(name)
                
                try:
                    entry["count"] = coll.count()
                except Exception:
                    try:
                        got = coll.get(include=["metadatas"]) or {}
                        metas = got.get("metadatas") or []
                        if metas and isinstance(metas[0], list):
                            entry["count"] = len(metas[0])
                        else:
                            entry["count"] = len(metas)
                    except Exception:
                        entry["count"] = None
                
                try:
                    q = coll.query(n_results=5, include=["documents", "metadatas", "distances"]) or {}
                    docs_r = q.get("documents", [])
                    metas_r = q.get("metadatas", [])
                    dists_r = q.get("distances", [])
                    
                    docs = docs_r[0] if docs_r and isinstance(docs_r[0], list) else docs_r
                    metas = metas_r[0] if metas_r and isinstance(metas_r[0], list) else metas_r
                    dists = dists_r[0] if dists_r and isinstance(dists_r[0], list) else dists_r
                    
                    for i in range(min(5, len(docs))):
                        entry["samples"].append({
                            "document_preview": (docs[i][:300] + '...') if docs[i] else None,
                            "metadata": (metas[i] if i < len(metas) else None),
                            "distance": (dists[i] if i < len(dists) else None),
                        })
                except Exception:
                    pass
            except Exception:
                pass
            
            collections.append(entry)
        
        return {"persist_directory": persist_dir, "collections": collections}
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
