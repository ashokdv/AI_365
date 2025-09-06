from fastapi import FastAPI, UploadFile, File, HTTPException, Query
import os
from pathlib import Path

from create_embeddings import create_embeddings
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from typing import List, Dict, Any
import json
import re

app = FastAPI()

BASE_DIR = Path(__file__).parent
PERSIST_DIR = BASE_DIR / "chroma_db"
os.makedirs(PERSIST_DIR, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/embeddings/")
async def generate_embeddings(
    file: UploadFile = File(...),
    reset: bool = Query(False, description="Reset existing vector store before adding"),
    chunk_size: int = Query(1000, ge=200, le=4000),
    chunk_overlap: int = Query(120, ge=0, le=1000)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF too large (max 20MB)")

    try:
        out_dir = create_embeddings(
            pdf_bytes=pdf_bytes,
            original_filename=file.filename,
            persist_dir=str(PERSIST_DIR),
            reset=reset,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding creation failed: {e}")

    return {
        "message": "Embeddings updated",
        "persist_directory": out_dir,
        "reset": reset
    }


@app.get("/chat/")
def chat_with_embeddings(
    q: str = Query(..., description="Your question"),
    k: int = Query(3, ge=1, le=15, description="Top-k retrieved chunks"),
    model: str = Query("gpt-3.5-turbo", description="OpenAI chat model")
):
    if not PERSIST_DIR.exists() or not any(PERSIST_DIR.iterdir()):
        raise HTTPException(status_code=400, detail="No embeddings yet. Upload a PDF first.")

    try:
        embeddings = OpenAIEmbeddings()
        vectordb = Chroma(persist_directory=str(PERSIST_DIR), embedding_function=embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load vector store: {e}")

    retriever = vectordb.as_retriever(search_kwargs={"k": k})

    try:
        qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model=model),
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        result = qa.invoke({"query": q})
        answer = result["result"]

        sources = []
        for d in result.get("source_documents", []):
            meta = d.metadata or {}
            origins_raw = meta.get("origins")
            origins_list = []
            if isinstance(origins_raw, str):
                try:
                    import json as _json
                    parsed = _json.loads(origins_raw)
                    if isinstance(parsed, list):
                        origins_list = parsed
                except Exception:
                    # Fallback: maybe comma-separated string
                    origins_list = [o.strip() for o in origins_raw.split(",") if o.strip()]
            elif isinstance(origins_raw, list):
                origins_list = origins_raw
            if not origins_list:
                origins_list = [meta.get("source")]
            sources.append({
                "source": meta.get("source"),
                "page": meta.get("page"),
                "hash": meta.get("_hash"),
                "all_origins": origins_list
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

    return {"question": q, "answer": answer, "k": k, "sources": sources}


@app.get("/recipe/")
def extract_recipe(
    q: str = Query(..., description="Recipe name or description you want"),
    k: int = Query(6, ge=1, le=25, description="Top-k chunks for extraction"),
    model: str = Query("gpt-3.5-turbo", description="OpenAI chat model"),
    max_context_chars: int = Query(8000, ge=1000, le=20000, description="Max characters from retrieved docs to pass to LLM")
):
    """Return a structured recipe (ingredients, steps, etc.) extracted from the PDFs.

    Model output is forced to strict JSON; we apply light repair for common mistakes.
    """
    if not PERSIST_DIR.exists() or not any(PERSIST_DIR.iterdir()):
        raise HTTPException(status_code=400, detail="No embeddings yet. Upload a PDF first.")

    try:
        embeddings = OpenAIEmbeddings()
        vectordb = Chroma(persist_directory=str(PERSIST_DIR), embedding_function=embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load vector store: {e}")

    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    try:
        docs = retriever.get_relevant_documents(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")

    if not docs:
        return {"query": q, "found": False, "message": "No relevant recipe text found."}

    # Build context (deduplicate identical page_content while preserving order)
    seen = set()
    context_blocks: List[str] = []
    source_map: List[Dict[str, Any]] = []
    for d in docs:
        txt = d.page_content.strip()
        if txt and txt not in seen:
            seen.add(txt)
            context_blocks.append(txt)
        meta = d.metadata or {}
        origins_raw = meta.get("origins")
        origins_list: List[str] = []
        if isinstance(origins_raw, str):
            try:
                parsed = json.loads(origins_raw)
                if isinstance(parsed, list):
                    origins_list = parsed
            except Exception:
                origins_list = [o.strip() for o in origins_raw.split(",") if o.strip()]
        elif isinstance(origins_raw, list):
            origins_list = origins_raw
        if not origins_list:
            origins_list = [meta.get("source")]
        source_map.append({
            "source": meta.get("source"),
            "page": meta.get("page"),
            "hash": meta.get("_hash"),
            "all_origins": origins_list
        })

    context_text = "\n---\n".join(context_blocks)
    if len(context_text) > max_context_chars:
        context_text = context_text[:max_context_chars] + "\n...[truncated]"

    system_prompt = (
        "You extract exactly ONE cooking recipe matching the user query from provided cookbook excerpts.\n"
        "Rules:\n"
        "- OUTPUT ONLY COMPACT JSON (no code fences, no markdown).\n"
        "- No trailing commas.\n"
        "- Use null for unknown optional fields.\n"
        "- If recipe not found return {\"found\": false, \"reason\": \"Not found\"}.\n"
        "Schema keys (snake_case): found (bool), recipe_title (string), description (string), ingredients (list), steps (list), equipment (list), categories (list), cuisine (string|null), notes (string|null).\n"
        "Each ingredient object: {original_line, quantity (string|null), unit (string|null), item (string|null), preparation_notes (string|null)}.\n"
        "No additional top-level keys."
    )

    user_prompt = (
        f"User query: {q}\n\n" 
        f"Cookbook excerpts (may include multiple recipes; extract the best match):\n{context_text}\n\n" 
        "Return ONLY the JSON object."
    )

    def _repair_json(s: str) -> str:
        # Remove code fences
        s = re.sub(r"```[a-zA-Z0-9]*", "", s)
        # Trim
        s = s.strip()
        # Common: trailing commas before ] or }
        s = re.sub(r",\s*(]\s*)", r"\1", s)
        s = re.sub(r",\s*(}\s*)", r"\1", s)
        return s

    try:
        llm = ChatOpenAI(model=model, temperature=0)
        msg = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        raw = msg.content.strip()
        # Extract first balanced JSON object via brace counting
        brace_stack = 0
        start_idx = None
        for i, ch in enumerate(raw):
            if ch == '{':
                if start_idx is None:
                    start_idx = i
                brace_stack += 1
            elif ch == '}':
                if brace_stack > 0:
                    brace_stack -= 1
                    if brace_stack == 0 and start_idx is not None:
                        candidate = raw[start_idx:i+1]
                        break
        else:
            raise ValueError("No complete JSON object found in model output")

        candidate = _repair_json(candidate)
        try:
            parsed = json.loads(candidate)
        except Exception:
            # Secondary repair: replace single quotes with double quotes for keys/strings (rough heuristic)
            cand2 = re.sub(r"'", '"', candidate)
            cand2 = _repair_json(cand2)
            parsed = json.loads(cand2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {e}")

    parsed["query"] = q
    parsed["sources"] = source_map
    return parsed