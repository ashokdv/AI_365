<div align="center">

# 🚀 Local API Explorer

Turn any OpenAPI / Swagger spec into a searchable natural‑language explorer. Upload a spec, embed endpoints, and ask questions like *"How do I create a user?"*.

</div>

## ✨ Current Features (Implemented)

- Upload OpenAPI / Swagger JSON (`/upload` FastAPI endpoint via Streamlit UI)
- Parse endpoints (path, method, summary, description, parameters)
- Generate embeddings (OpenAI if key present, otherwise local backend to be added; currently OpenAI only in `embedding_utils.py` fallback logic partially stubbed)
- Persist vector store with Chroma (`chroma_store/` folder)
- Semantic similarity search over endpoints (`/query`)
- Streamlit UI to index + search
- Health check endpoint (`/health`)

## 🧭 Architecture

```
OpenAPI Spec → Parse → Build Documents → Embed → Chroma (persist)
													↑
User Query ─────────────→ Embed ──────────► Similarity Search ──► Ranked Endpoints → UI
```

## 🗂 Project Structure (Actual)

```
day-06-AskMyAPI/
├── backend/
│   ├── api.py               # FastAPI app (upload/query)
│   ├── embedding_utils.py   # Parsing + embedding + Chroma persistence
│   ├── __init__.py
│   └── readme.md
├── frontend/
│   └── app.py               # Streamlit UI
├── requirements.txt         # Root dependency list (backend + frontend)
├── .env.example             # Environment variable template
└── readme.md                # This file
```

## ⚙️ Environment Variables

Copy `.env.example` to `.env` (optional):

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | Enables OpenAI embeddings | (none) |
| `EMBEDDING_MODEL` | Override model name | `text-embedding-3-small` (OpenAI) |
| `CHROMA_PERSIST_DIR` | Vector DB directory | `chroma_store` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

> Local (non‑OpenAI) embedding fallback placeholder exists; install sentence-transformers & add logic if needed.

## 🚀 Quick Start

### 1. Create & Activate Virtual Env (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run Backend (FastAPI)
```powershell
python -m backend.api  # or: uvicorn backend.api:app --reload
```
Visit: http://localhost:8000/docs

### 4. Run Frontend (Streamlit)
```powershell
streamlit run frontend/app.py
```

### 5. Use It
1. In Streamlit, upload your `openapi.json` file
2. Wait for indexing success message
3. Enter a natural language question
4. Expand results to view endpoint details

## 🔍 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service status |
| `POST` | `/upload` | Multipart file upload (`file` field) to index spec |
| `POST` | `/query` | JSON body: `{ "query": str, "k": int }` returns ranked endpoints |

## 📦 Internals

Parsing builds a normalized list of endpoints with joined textual representation used for embedding. Chroma stores embeddings persistently so repeated queries don't recompute them. The `/upload` endpoint currently recreates the store each time (simple MVP strategy). Incremental updates are a potential enhancement.

## ✅ MVP Status

| Capability | Status |
|------------|--------|
| Spec Upload | Done |
| Endpoint Parsing | Done |
| Embedding Generation | Done (OpenAI path) |
| Vector Store Persistence | Done (Chroma) |
| Semantic Search | Done |
| Streamlit UI | Done |
| Local Embedding Fallback | Partial (placeholder) |
| Try-it-out Request Builder | Planned |
