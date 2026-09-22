from app.config import QA_MIN_SIMILARITY, TOP_K
from app.llm.prompts import QA_SYSTEM
from app.llm.provider import chat

def answer_question(question: str, vector_store, top_k: int = TOP_K, min_similarity: float = QA_MIN_SIMILARITY):
    results = vector_store.search(question, top_k=top_k)
    if not results:
        return {
            "answer": "I couldn't find that information in the paper.",
            "sources": [],
            "retrieved_chunks": [],
        }

    best = results[0]["similarity"]
    if best < min_similarity:
        return {
            "answer": "I couldn't find that information in the paper.",
            "sources": results,
            "retrieved_chunks": results,
        }

    context = "\n\n".join(
        f"[Page {r['page']} | {r['section']} | {r['chunk_id']} | similarity={r['similarity']:.3f}]\n{r['text']}"
        for r in results
    )
    user_prompt = f"""Question:
{question}

Retrieved paper excerpts:
{context}

Answer using only these excerpts. If they do not contain the answer, say:
"I couldn't find that information in the paper."
"""
    answer = chat(QA_SYSTEM, user_prompt).strip()
    return {
        "answer": answer,
        "sources": results,
        "retrieved_chunks": results,
    }
