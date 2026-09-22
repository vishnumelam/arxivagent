from datetime import datetime, timezone
import numpy as np

def _recency_score(published: str) -> float:
    if not published:
        return 0.0
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        age_days = max(0.0, (datetime.now(timezone.utc) - dt).days)
        return 1.0 / (1.0 + age_days / 365.0)
    except ValueError:
        return 0.0

def rank_candidates(query: str, candidates: list[dict], embedder, limit: int = 3) -> list[dict]:
    if not candidates:
        return []
    texts = [f"{p.get('title','')} {p.get('abstract','')}" for p in candidates]
    vectors = embedder.encode([query] + texts, normalize_embeddings=True)
    query_vec = vectors[0]
    similarities = np.dot(vectors[1:], query_vec)
    ranked = []
    for paper, sim in zip(candidates, similarities):
        # Relevance dominates; recency is only a small tie-breaker.
        score = 0.90 * float(sim) + 0.10 * _recency_score(paper.get("published", ""))
        item = dict(paper)
        item["selection_score"] = round(score, 5)
        ranked.append(item)
    ranked.sort(key=lambda x: x["selection_score"], reverse=True)
    return ranked[:limit]
