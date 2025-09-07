"""FastAPI API for OpenAPI semantic explorer with persistent embeddings."""
from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
import json
import os
from typing import Optional

# Support both "python -m backend.api" (package) and "python backend/api.py" (script)
try:  # pragma: no cover - import resolution logic
    from .embedding_utils import index_spec, search  # type: ignore
except ImportError:  # running as a script without package context
    from embedding_utils import index_spec, search  # type: ignore

app = FastAPI(title="OpenAPI Semantic Explorer", version="0.2.0")


class QueryBody(BaseModel):
    query: str
    k: Optional[int] = 5


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_spec(file: UploadFile):
    try:
        spec = json.load(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    result = index_spec(spec)
    return {"status": "indexed", **result}


@app.post("/query")
async def query_api(body: QueryBody):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query is empty")
    results = search(body.query, k=body.k or 5)
    return {"results": results, "count": len(results)}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.api:app", host="0.0.0.0", port=port, reload=True)

