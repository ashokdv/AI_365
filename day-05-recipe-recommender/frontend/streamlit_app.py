import streamlit as st
import requests
import json
from typing import List, Dict, Any

# BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Recipe RAG Chatbot", page_icon="🍲", layout="wide")

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {role: user|assistant|system, content: str, sources: optional}
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# --- Sidebar: Upload PDF(s) ---
st.sidebar.header("📄 Upload Cookbooks")
with st.sidebar.form("upload_form"):
    pdf_files = st.file_uploader("Select PDF cookbook(s)", type=["pdf"], accept_multiple_files=True)
    reset = st.checkbox("Reset embeddings (wipe & rebuild)", value=False, help="Deletes existing vector store before adding new PDFs.")
    chunk_size = st.number_input("Chunk size", 200, 4000, 1000, step=100)
    chunk_overlap = st.number_input("Chunk overlap", 0, 1000, 120, step=10)
    submitted = st.form_submit_button("Process PDFs")

if submitted and pdf_files:
    for idx, pdf in enumerate(pdf_files):
        with st.spinner(f"Embedding {pdf.name} ({idx+1}/{len(pdf_files)})..."):
            try:
                files = {"file": (pdf.name, pdf.getvalue(), "application/pdf")}
                params = {
                    "reset": str(reset).lower() if idx == 0 else "false",  # only first triggers reset
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                }
                resp = requests.post(f"http://localhost:8000/embeddings/", files=files, params=params, timeout=120)
                if resp.status_code == 200:
                    st.success(f"Embedded: {pdf.name}")
                    st.session_state.uploaded_files.append(pdf.name)
                else:
                    st.error(f"Failed {pdf.name}: {resp.text}")
            except Exception as e:
                st.error(f"Error {pdf.name}: {e}")

# --- Sidebar: Options ---
st.sidebar.header("⚙️ Chat Settings")
model = st.sidebar.selectbox("Model", ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"], index=0)
retrieval_k = st.sidebar.slider("Top-K Chunks", 1, 15, 3)
mode = st.sidebar.radio("Mode", ["Chat", "Recipe Extract"], horizontal=True)

st.sidebar.markdown("---")
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []

# --- Main Header ---
st.title("🍲 Recipe Knowledge Chatbot")
st.caption("Ask questions about your uploaded cookbooks, or extract structured recipes.")


def render_recipe(recipe: Dict[str, Any], sources: List[Dict[str, Any]] | None = None, show_sources: bool = True):
    """Pretty render the structured recipe instead of raw JSON, optionally showing sources."""
    title = recipe.get("recipe_title") or "Recipe"
    desc = recipe.get("description")
    ingredients = recipe.get("ingredients") or []
    steps = recipe.get("steps") or []
    equipment = recipe.get("equipment") or []
    categories = recipe.get("categories") or []
    cuisine = recipe.get("cuisine")
    notes = recipe.get("notes")

    st.subheader(title)
    if desc:
        st.markdown(desc)

    cols = st.columns(2)
    with cols[0]:
        st.markdown("### Ingredients")
        if not ingredients:
            st.write("(none parsed)")
        else:
            for ing in ingredients:
                line = ing.get("original_line") or ""
                qty = ing.get("quantity")
                unit = ing.get("unit")
                item = ing.get("item")
                prep = ing.get("preparation_notes")
                parts = []
                if qty: parts.append(str(qty))
                if unit: parts.append(unit)
                if item: parts.append(item)
                main_line = " ".join(parts) if parts else line
                if not main_line:
                    main_line = line
                if prep:
                    main_line += f" _( {prep} )_"
                st.markdown(f"- {main_line}")

    with cols[1]:
        st.markdown("### Meta")
        if categories:
            st.write("**Categories:**", ", ".join(categories))
        if cuisine:
            st.write("**Cuisine:**", cuisine)
        if equipment:
            st.write("**Equipment:**")
            st.write(", ".join(equipment))
        if notes:
            st.write("**Notes:**", notes)

    st.markdown("### Steps")
    if steps:
        for i, s in enumerate(steps, 1):
            st.markdown(f"**{i}.** {s}")
    else:
        st.write("(no steps parsed)")

    if show_sources and sources:
        st.markdown("### Sources")
        for s in sources:
            origins = ", ".join(s.get("all_origins", []) or [])
            page = s.get("page")
            st.write(f"• {s.get('source')} (page {page}) origins: {origins}")

    with st.expander("Raw JSON"):
        st.json(recipe)

# --- Chat Display ---
chat_container = st.container()
with chat_container:
    for m in st.session_state.messages:
        role = "assistant" if m["role"] != "user" else "user"
        with st.chat_message(role):
            if m.get("recipe_json"):
                render_recipe(m["recipe_json"], m.get("sources"))
            else:
                st.markdown(m["content"])
                if m.get("sources"):
                    with st.expander("Sources"):
                        for s in m["sources"]:
                            st.write(f"• {s.get('source')} (page {s.get('page')}) origins: {', '.join(s.get('all_origins', []))}")

# --- User Input ---
prompt = st.chat_input("Ask a question or request a recipe (e.g., 'Show me the paneer recipe')")


def call_chat_backend(question: str) -> Dict[str, Any]:
    try:
        params = {"q": question, "k": retrieval_k, "model": model}
        r = requests.get(f"http://localhost:8000/chat/", params=params, timeout=60)
        if r.status_code != 200:
            return {"error": r.text}
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def call_recipe_backend(question: str) -> Dict[str, Any]:
    try:
        params = {"q": question, "k": retrieval_k, "model": model}
        r = requests.get(f"http://localhost:8000/recipe/", params=params, timeout=90)
        if r.status_code != 200:
            return {"error": r.text}
        return r.json()
    except Exception as e:
        return {"error": str(e)}

if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if mode == "Chat":
                resp = call_chat_backend(prompt)
            else:
                resp = call_recipe_backend(prompt)

        if resp.get("error"):
            st.error(resp["error"])
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {resp['error']}"})
        else:
            if mode == "Chat":
                answer = resp.get("answer", "(no answer)")
                sources = resp.get("sources", [])
                st.markdown(answer)
                if sources:
                    with st.expander("Sources"):
                        for s in sources:
                            st.write(f"• {s.get('source')} (page {s.get('page')}) origins: {', '.join(s.get('all_origins', []))}")
                st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
            else:
                if resp.get("found") is False:
                    msg = resp.get("reason", "Recipe not found")
                    st.warning(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                else:
                    render_recipe(resp, resp.get("sources"))
                    st.session_state.messages.append({"role": "assistant", "content": f"Extracted recipe: {resp.get('recipe_title')}", "recipe_json": resp, "sources": resp.get("sources")})

# Footer
st.markdown("---")
st.caption("Backend: FastAPI + Chroma + OpenAI | Frontend: Streamlit")
