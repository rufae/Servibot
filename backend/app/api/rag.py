"""
RAG API endpoints: index uploaded files and query the vector DB (POC)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging

from app.core.config import settings
from app.rag.ingest import index_file

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except Exception:
    chromadb = None
    ChromaSettings = None

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
    """Index a previously uploaded file into the RAG vector store.

    The request should provide either `filename` (the saved name in UPLOAD_DIR) or a full path.
    """
    try:
        if req.filename:
            file_path = os.path.join(settings.UPLOAD_DIR, req.filename)
        elif req.file_id:
            # try to resolve by id
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
    """Perform a semantic search against the vector DB and return top-k documents.

    This is a POC: uses sentence-transformers for embedding the query and chroma for retrieval.
    """
    try:
        top_k = req.top_k or settings.TOP_K_RESULTS

        try:
            from sentence_transformers import SentenceTransformer
            import chromadb
            from chromadb.config import Settings as ChromaSettings
        except Exception as e:
            logger.error(f"Dependencies for RAG query missing: {e}")
            raise HTTPException(status_code=500, detail="RAG dependencies missing on server")

        model = SentenceTransformer("all-MiniLM-L6-v2")
        q_emb = model.encode([req.query], show_progress_bar=False)[0].tolist()

        # Use the same persistence directory as ingestion so queries see indexed collections
        persist_dir = os.path.abspath(settings.VECTOR_DB_PATH)
        try:
            client = chromadb.Client(ChromaSettings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
        except Exception:
            # Fallback to non-persistent client if creation with settings fails
            try:
                client = chromadb.Client()
            except Exception as e:
                logger.error(f"Failed to create chromadb client: {e}")
                raise HTTPException(status_code=500, detail="Failed to initialize vector DB client")

        try:
            collection = client.get_collection("servibot_docs")
        except Exception:
            raise HTTPException(status_code=404, detail="No collection found. Index some documents first.")

        # Chroma client API may vary by version; request documents, metadatas and distances
        query_res = collection.query(query_embeddings=[q_emb], n_results=top_k, include=["documents", "metadatas", "distances"]) 

        results = []
        docs_raw = query_res.get("documents", [])
        metas_raw = query_res.get("metadatas", [])
        dists_raw = query_res.get("distances", [])

        # Normalize: Chroma may return lists per query (e.g., [[doc1,doc2,...]]).
        # If so, take the first element as the list of results for our single query.
        if docs_raw and isinstance(docs_raw[0], list):
            docs = docs_raw[0]
        else:
            docs = docs_raw

        if metas_raw and isinstance(metas_raw[0], list):
            metadatas = metas_raw[0]
        else:
            metadatas = metas_raw

        if dists_raw and isinstance(dists_raw[0], list):
            distances = dists_raw[0]
        else:
            distances = dists_raw

        # Build result objects
        for i in range(min(len(docs), top_k)):
            doc_text = docs[i] if docs and i < len(docs) else None
            metadata = metadatas[i] if metadatas and i < len(metadatas) else None
            distance = distances[i] if distances and i < len(distances) else None
            results.append({
                "document": doc_text,
                "metadata": metadata,
                "distance": distance,
            })

        return QueryResponse(query=req.query, results=results)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/debug/vectors")
async def debug_vectors():
    """Debug endpoint: list collections, their approximate sizes and sample metadatas/documents.

    Useful to inspect whether documents were indexed and what metadata they have.
    """
    if chromadb is None:
        raise HTTPException(status_code=500, detail="chromadb not available on server")

    persist_dir = os.path.abspath(settings.VECTOR_DB_PATH)
    try:
        client = chromadb.Client(ChromaSettings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
    except Exception:
        try:
            client = chromadb.Client()
        except Exception as e:
            logger.error(f"Failed to create chromadb client for debug: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize vector DB client")

    collections = []
    try:
        cols = client.list_collections()
    except Exception:
        cols = []

    for c in cols:
        name = c.get("name") if isinstance(c, dict) else getattr(c, "name", str(c))
        entry = {"name": name, "count": None, "samples": []}
        try:
            coll = client.get_collection(name)
            # Try to get count() if available
            try:
                entry["count"] = coll.count()
            except Exception:
                try:
                    got = coll.get(include=["metadatas"]) or {}
                    metas = got.get("metadatas") or []
                    # normalize
                    if metas and isinstance(metas[0], list):
                        entry["count"] = len(metas[0])
                    else:
                        entry["count"] = len(metas)
                except Exception:
                    entry["count"] = None

            # fetch a few sample docs/metadatas
            try:
                q = coll.query(n_results=5, include=["documents", "metadatas", "distances"]) or {}
                docs_r = q.get("documents", [])
                metas_r = q.get("metadatas", [])
                dists_r = q.get("distances", [])

                # normalize shapes
                if docs_r and isinstance(docs_r[0], list):
                    docs = docs_r[0]
                else:
                    docs = docs_r
                if metas_r and isinstance(metas_r[0], list):
                    metas = metas_r[0]
                else:
                    metas = metas_r
                if dists_r and isinstance(dists_r[0], list):
                    dists = dists_r[0]
                else:
                    dists = dists_r

                for i in range(min(5, len(docs))):
                    entry["samples"].append({
                        "document_preview": (docs[i][:300] + '...') if docs[i] else None,
                        "metadata": (metas[i] if i < len(metas) else None),
                        "distance": (dists[i] if i < len(dists) else None),
                    })
            except Exception:
                # ignore sample fetch errors
                pass
        except Exception:
            # unable to open collection
            pass

        collections.append(entry)

    return {"persist_directory": persist_dir, "collections": collections}
