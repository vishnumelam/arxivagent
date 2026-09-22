import json
from pathlib import Path

from app.graph.workflow import build_graph
from app.retrieval.embeddings import Embedder
from app.retrieval.vector_store import LocalVectorStore
from app.config import TOP_K, QA_MIN_SIMILARITY
from app.llm.qa import answer_question

def _print_briefing(briefing: dict):
    print("\n" + "=" * 70)
    print("EXECUTIVE BRIEFING")
    print("=" * 70)
    print(f"Title: {briefing['title']}")
    print(f"Authors: {', '.join(briefing['authors'])}")
    print(f"arXiv ID: {briefing['arxiv_id']}")
    print(f"Publish date: {briefing['publish_date']}")
    print(f"Link: {briefing['link']}\n")

    print("WHY THIS PAPER MATTERS")
    print(briefing["why_this_paper_matters"] + "\n")

    print("PROBLEM STATEMENT")
    print(briefing["problem_statement"] + "\n")

    for heading, key in [
        ("METHOD / APPROACH", "method"),
        ("KEY RESULTS / CLAIMS", "key_results"),
        ("LIMITATIONS", "limitations"),
        ("SUGGESTED FOLLOW-UP QUESTIONS", "follow_up_questions"),
    ]:
        print(heading)
        for item in briefing[key]:
            print(f"• {item}")
        print()

def _print_candidates(candidates):
    if len(candidates) > 1:
        print("\nTop candidates:")
        for i, p in enumerate(candidates[:3], start=1):
            print(f"{i}. {p.get('title')} [{p.get('arxiv_id')}] score={p.get('selection_score','n/a')}")

def run_cli():
    print("=" * 70)
    print("AUTONOMOUS arXiv PAPER DIGEST & QA AGENT")
    print("=" * 70)
    print("Enter a research topic, arXiv ID, or arXiv URL.")
    query = input("\n> ").strip()
    if not query:
        print("No input provided.")
        return

    graph = build_graph()
    print("\n[1/7] Understanding query...")
    state = graph.invoke({"user_query": query, "conversation_history": []})

    if state.get("status") != "completed":
        print(f"\nAgent stopped safely: {state.get('error', 'Unknown error')}")
        return

    print("[2/7] Paper selected.")
    _print_candidates(state.get("candidate_papers", []))
    print("[3/7] PDF downloaded.")
    print("[4/7] PDF parsed: "
          f"{state.get('page_count')} pages, {state.get('character_count')} extracted characters.")
    print("[5/7] Chunks and FAISS index created: "
          f"{len(state.get('chunks', []))} chunks.")
    print("[6/7] Executive briefing generated.")
    _print_briefing(state["briefing"])

    print("[7/7] QA mode ready.")
    embedder = Embedder()
    store = LocalVectorStore(
        Path(state["vector_store_path"]),
        Path(state["metadata_path"]),
        embedder,
    ).load()

    while True:
        question = input("\nAsk a question (or type 'exit'): ").strip()
        if question.lower() in {"exit", "quit"}:
            print("Session ended.")
            break
        if not question:
            continue

        try:
            result = answer_question(
                question, store, top_k=TOP_K, min_similarity=QA_MIN_SIMILARITY
            )
        except Exception as exc:
            print(f"\nQA failed safely: {exc}")
            continue

        print("\nANSWER")
        print(result["answer"])

        if result["sources"]:
            print("\nRETRIEVED SOURCES")
            for source in result["sources"]:
                print(
                    f"• page {source['page']}, section '{source['section']}', "
                    f"{source['chunk_id']}, similarity={source['similarity']:.3f}"
                )
        state.setdefault("conversation_history", []).append({
            "question": question,
            "answer": result["answer"],
        })
