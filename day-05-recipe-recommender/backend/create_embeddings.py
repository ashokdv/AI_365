import os
import json
import hashlib
import shutil
from typing import Optional, List
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def create_embeddings(
    pdf_path: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
    original_filename: str = "uploaded.pdf",
    persist_dir: str = "./chroma_db",
    temp_filename: str = "_upload.pdf",
    reset: bool = False,
    chunk_size: int = 1000,
    chunk_overlap: int = 120
) -> str:
    """
    Build / extend a Chroma store.
    Tracks identical chunk overlaps across PDFs:
      - Each chunk hashed (sha256)
      - origins_index.json keeps hash -> [filenames]
      - Metadata on each stored chunk: _hash, source, origins
    Duplicate chunk text across files is stored once; origins aggregated.
    """
    persist_dir = str(persist_dir)
    persist_path = Path(persist_dir)
    if reset and os.path.isdir(persist_dir):
        shutil.rmtree(persist_dir, ignore_errors=True)
    os.makedirs(persist_dir, exist_ok=True)

    origins_index_path = persist_path / "origins_index.json"
    if origins_index_path.exists():
        try:
            with open(origins_index_path, "r", encoding="utf-8") as f:
                origins_index = json.load(f)
        except Exception:
            origins_index = {}
    else:
        origins_index = {}

    # Materialize PDF if bytes provided
    if pdf_bytes is not None:
        pdf_path = os.path.join(persist_dir, temp_filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
    if not pdf_path:
        raise ValueError("Either pdf_path or pdf_bytes must be provided")

    # Load pages
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    # Split
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    docs = splitter.split_documents(pages)

    # Prepare embeddings + vector store (create or open)
    embeddings = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    # Collect existing IDs (hashes) to know what is already stored
    existing_ids = set()
    try:
        raw = vectordb._collection.get(include=["metadatas"], limit=100000)
        metas = raw.get("metadatas", []) or []
        ids = raw.get("ids", []) or []
        for _id, m in zip(ids, metas):
            if m and "_hash" in m:
                existing_ids.add(m["_hash"])
            else:
                # Fallback: consider the chroma id if no _hash yet
                existing_ids.add(_id)
    except Exception:
        pass

    # Decide which chunks to add or update
    add_texts: List[str] = []
    add_metas: List[dict] = []
    add_ids: List[str] = []
    hashes_to_update = []  # existing chunk hashes whose origins need update
    new_origins_meta = {}

    for d in docs:
        text = d.page_content or ""
        h = _hash_text(text)
        # Update origins index
        current = set(origins_index.get(h, []))
        current.add(original_filename)
        origins_index[h] = sorted(current)

        metadata = d.metadata or {}
        metadata["_hash"] = h
        metadata["source"] = original_filename
        # Chroma requires primitive metadata values; store list as JSON string
        try:
            metadata["origins"] = json.dumps(origins_index[h], ensure_ascii=False)
        except Exception:
            # Fallback: join as comma-separated string (should not normally happen)
            metadata["origins"] = ",".join(origins_index[h])

        if h in existing_ids:
            hashes_to_update.append(h)
            new_origins_meta[h] = metadata
        else:
            add_texts.append(text)
            add_metas.append(metadata)
            add_ids.append(h)

    # Add new unique chunks
    if add_texts:
        vectordb.add_texts(texts=add_texts, metadatas=add_metas, ids=add_ids)

    # Update metadata for existing hashes where origins expanded
    # (Chroma python client low-level update)
    if hashes_to_update:
        try:
            vectordb._collection.update(
                ids=hashes_to_update,
                metadatas=[new_origins_meta[h] for h in hashes_to_update]
            )
        except Exception:
            pass

    vectordb.persist()

    # Persist origins index
    with open(origins_index_path, "w", encoding="utf-8") as f:
        json.dump(origins_index, f, ensure_ascii=False, indent=2)

    # Cleanup temp
    if pdf_bytes is not None and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except OSError:
            pass

    print(f"Embeddings stored at '{persist_dir}'")
    return persist_dir