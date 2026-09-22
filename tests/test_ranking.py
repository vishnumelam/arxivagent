import numpy as np
from app.arxiv.ranking import rank_candidates

class FakeEmbedder:
    def encode(self, texts, normalize_embeddings=True):
        # First vector is query. Candidate 1 is close; candidate 2 is orthogonal.
        return np.array([
            [1.0, 0.0],
            [0.99, 0.01],
            [0.0, 1.0],
        ], dtype=float)

def test_rank_candidates():
    candidates = [
        {"arxiv_id": "1", "title": "relevant", "abstract": "", "published": ""},
        {"arxiv_id": "2", "title": "irrelevant", "abstract": "", "published": ""},
    ]
    ranked = rank_candidates("query", candidates, FakeEmbedder(), limit=2)
    assert ranked[0]["arxiv_id"] == "1"
    assert ranked[0]["selection_score"] > ranked[1]["selection_score"]
