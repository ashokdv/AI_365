"""Streamlit frontend for semantic API explorer (updated to match backend v0.2)."""
import streamlit as st
import requests
import json

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Semantic API Explorer", layout="wide")
st.title("🔎 Semantic API Explorer")

with st.sidebar:
    st.markdown("**Backend**")
    backend_url = st.text_input("URL", BACKEND_URL)
    top_k = st.slider("Top K", 1, 15, 5)

uploaded_file = st.file_uploader("Upload OpenAPI JSON", type=["json"])

if uploaded_file and st.button("Index Spec", type="primary"):
    try:
        # Need to send multipart form-data with the file pointer
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/json")}
        res = requests.post(f"{backend_url}/upload", files=files, timeout=120)
        if res.ok:
            data = res.json()
            st.success(
                f"Indexed {data.get('indexed', 0)} endpoints (persist dir: {data.get('persist_directory')})."
            )
        else:
            st.error(f"Upload failed {res.status_code}: {res.text}")
    except Exception as e:
        st.error(f"Error uploading spec: {e}")

query = st.text_input("Ask a question about the API", placeholder="How do I create a user?")

if st.button("Search", disabled=not query.strip()):
    try:
        payload = {"query": query, "k": top_k}
        res = requests.post(f"{backend_url}/query", json=payload, timeout=60)
        if not res.ok:
            st.error(f"Search failed {res.status_code}: {res.text}")
        else:
            results = res.json().get("results", [])
            if not results:
                st.info("No results")
            else:
                st.subheader("Results")
                for r in results:
                    header = f"{r.get('method')} {r.get('path')}"
                    with st.expander(header):
                        if r.get("summary"):
                            st.markdown(f"**Summary:** {r['summary']}")
                        if r.get("description"):
                            st.markdown(r["description"])  # may contain markdown
                        params = r.get("parameters") or []
                        if params:
                            st.markdown("**Parameters**")
                            st.code("\n".join(params), language="text")
                        st.caption(r.get("content")[:400])
    except Exception as e:
        st.error(f"Error performing search: {e}")

st.caption("Frontend aligned with backend response fields (indexed, persist_directory, results).")
