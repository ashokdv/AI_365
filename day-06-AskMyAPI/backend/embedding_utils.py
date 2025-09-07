"""Utilities for parsing OpenAPI specs, generating embeddings, and persisting a Chroma store.

Features:
 - Parse OpenAPI / Swagger spec JSON
 - Build LangChain Document objects
 - Embedding backend priority: OpenAI -> local sentence-transformers
 - Persist vector store locally so server restarts keep data
 - Provide search helper

Env Vars:
  OPENAI_API_KEY       (optional)
  EMBEDDING_MODEL      (override default model name)
  CHROMA_PERSIST_DIR   (folder path, default 'chroma_store')
"""
from __future__ import annotations

import os
import json
from typing import Any, Dict, List

from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma


def get_embedding_function():
    """Return an embedding function with fallback logic."""
    model_name = os.getenv("EMBEDDING_MODEL")
    api_key = os.getenv("OPENAI_API_KEY") 
    print("openai key:", api_key)
    if api_key:
        from langchain_community.embeddings import OpenAIEmbeddings  # lazy import

        return OpenAIEmbeddings(model=model_name or "text-embedding-3-small")


def parse_spec(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    paths = spec.get("paths", {})
    endpoints: List[Dict[str, Any]] = []
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, details in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            if not isinstance(details, dict):
                continue
            desc = details.get("description", "") or ""
            summary = details.get("summary", "") or ""
            params_raw = details.get("parameters", []) or []
            params = []
            for p in params_raw:
                if isinstance(p, dict):
                    nm = p.get("name")
                    loc = p.get("in")
                    if nm:
                        params.append(f"{nm}:{loc}" if loc else nm)
            text_lines = [f"{method.upper()} {path}"]
            if summary:
                text_lines.append(f"Summary: {summary}")
            if desc:
                text_lines.append(f"Description: {desc}")
            if params:
                text_lines.append("Parameters: " + ", ".join(params))
            text = "\n".join(text_lines)
            endpoints.append(
                {
                    "id": f"{method.upper()} {path}",
                    "path": path,
                    "method": method.upper(),
                    "summary": summary,
                    "description": desc,
                    "parameters": params,
                    "text": text,
                }
            )
    return endpoints


def build_documents(endpoints: List[Dict[str, Any]]) -> List[Document]:
    docs: List[Document] = []
    for e in endpoints:
        meta = {k: e[k] for k in ["path", "method", "summary", "description"]}
        meta["parameters"] = json.dumps(e.get("parameters", []))
        docs.append(Document(page_content=e["text"], metadata=meta))
    return docs


def load_or_create_store(embedding_fn, persist_directory: str) -> Chroma:
    os.makedirs(persist_directory, exist_ok=True)
    try:
        store = Chroma(persist_directory=persist_directory, embedding_function=embedding_fn)
        return store
    except Exception:  # pragma: no cover - chroma internal variation
        # Fallback to from_documents when empty
        return Chroma(persist_directory=persist_directory, embedding_function=embedding_fn)


def index_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    embedding_fn = get_embedding_function()
    persist_dir = "chroma_store"
    endpoints = parse_spec(spec)
    if not endpoints:
        return {"indexed": 0, "message": "No endpoints found"}
    docs = build_documents(endpoints)
    # Recreate collection each time for simplicity (could be incremental)
    # Remove existing index files if re-indexing is desired - optional future feature.
    store = Chroma.from_documents(docs, embedding_fn, persist_directory=persist_dir)
    store.persist()
    return {"indexed": len(endpoints), "persist_directory": persist_dir}


def search(query: str, k: int = 5) -> List[Dict[str, Any]]:
    embedding_fn = get_embedding_function()
    persist_dir = "chroma_store"
    store = load_or_create_store(embedding_fn, persist_dir)
    results = store.similarity_search(query, k=k)
    out: List[Dict[str, Any]] = []
    for r in results:
        md = r.metadata or {}
        params = md.get("parameters")
        try:
            params_list = json.loads(params) if isinstance(params, str) else []
        except json.JSONDecodeError:
            params_list = []
        out.append(
            {
                "content": r.page_content,
                "path": md.get("path"),
                "method": md.get("method"),
                "summary": md.get("summary"),
                "description": md.get("description"),
                "parameters": params_list,
            }
        )
    return out


__all__ = [
    "index_spec",
    "search",
]
