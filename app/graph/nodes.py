from pathlib import Path
import json
import re

from app.config import (
    PAPERS_DIR, INDEXES_DIR, SESSIONS_DIR,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
)
from app.arxiv.client import extract_arxiv_id, is_specific_paper, get_paper, search_papers, ArxivError
from app.arxiv.ranking import rank_candidates
from app.ingestion.downloader import download_pdf
from app.ingestion.parser import parse_pdf, PDFParseError
from app.ingestion.chunker import chunk_pages
from app.retrieval.embeddings import Embedder
from app.retrieval.vector_store import LocalVectorStore
from app.llm.briefing import generate_briefing

def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)

def understand_query(state):
    query = state["user_query"].strip()
    paper_id = extract_arxiv_id(query)
    if paper_id:
        return {"query_type": "paper_id", "paper_id": paper_id, "status": "query_understood"}
    if len(query) < 3:
        return {"query_type": "invalid", "error": "Please enter an arXiv ID/URL or a research topic with at least 3 characters.", "status": "failed"}
    return {"query_type": "topic", "status": "query_understood"}

def search_arxiv_node(state):
    try:
        candidates = search_papers(state["user_query"])
        if not candidates:
            return {"candidate_papers": [], "error": "No relevant arXiv papers were found for this topic.", "status": "failed"}
        return {"candidate_papers": candidates, "status": "candidates_found"}
    except (ArxivError, ValueError) as exc:
        return {"error": str(exc), "status": "failed"}

def select_paper_node(state):
    try:
        embedder = Embedder()
        ranked = rank_candidates(state["user_query"], state["candidate_papers"], embedder, limit=3)
        if not ranked:
            return {"error": "No candidates could be selected.", "status": "failed"}
        return {"candidate_papers": ranked, "paper_metadata": ranked[0], "paper_id": ranked[0]["arxiv_id"], "status": "paper_selected"}
    except Exception as exc:
        return {"error": f"Paper ranking failed: {exc}", "status": "failed"}

def get_direct_paper_node(state):
    try:
        metadata = get_paper(state["paper_id"])
        return {"paper_metadata": metadata, "status": "paper_selected"}
    except ArxivError as exc:
        return {"error": str(exc), "status": "failed"}

def fetch_pdf_node(state):
    paper_id = state["paper_id"]
    metadata = state["paper_metadata"]
    pdf_url = metadata.get("pdf_url") or f"https://arxiv.org/pdf/{paper_id}.pdf"
    destination = PAPERS_DIR / f"{_safe_id(paper_id)}.pdf"
    try:
        download_pdf(pdf_url, destination)
        return {"pdf_url": pdf_url, "pdf_path": str(destination), "status": "pdf_downloaded"}
    except RuntimeError as exc:
        return {"error": str(exc), "status": "failed"}

def parse_pdf_node(state):
    try:
        parsed = parse_pdf(Path(state["pdf_path"]))
        return {
            "parsed_text": parsed["full_text"],
            "abstract": parsed.get("abstract", ""),
            "pages": parsed["pages"],
            "page_count": parsed["page_count"],
            "character_count": parsed["character_count"],
            "has_references_section": parsed["has_references_section"],
            "status": "pdf_parsed",
        }
    except PDFParseError as exc:
        return {"error": str(exc), "status": "failed"}

def chunk_and_index_node(state):
    try:
        chunks = chunk_pages(state["pages"], CHUNK_SIZE, CHUNK_OVERLAP)
        if len(chunks) < 2:
            return {"error": "PDF parsing produced too little usable content for RAG.", "status": "failed"}

        safe = _safe_id(state["paper_id"])
        index_path = INDEXES_DIR / f"{safe}.faiss"
        metadata_path = INDEXES_DIR / f"{safe}.json"

        embedder = Embedder()
        store = LocalVectorStore(index_path, metadata_path, embedder)
        store.build(chunks)

        return {
            "chunks": chunks,
            "vector_store_path": str(index_path),
            "metadata_path": str(metadata_path),
            "status": "indexed",
        }
    except Exception as exc:
        return {"error": f"Chunking/indexing failed: {exc}", "status": "failed"}

def briefing_node(state):
    try:
        briefing = generate_briefing(
            state["paper_metadata"],
            state["parsed_text"],
            state["chunks"],
        )
        return {"briefing": briefing, "status": "completed"}
    except Exception as exc:
        return {"error": f"Briefing generation failed: {exc}", "status": "failed"}

def save_session(state):
    safe = _safe_id(state.get("paper_id", "session"))
    session_path = SESSIONS_DIR / f"{safe}.json"
    serializable = dict(state)
    # Full parsed text is not needed in the session JSON because the PDF is persisted.
    serializable.pop("parsed_text", None)
    serializable["conversation_history"] = serializable.get("conversation_history", [])
    session_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": state.get("status", "completed")}
