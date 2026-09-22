import json
from pathlib import Path
import faiss
import numpy as np

class LocalVectorStore:
    def __init__(self, index_path: Path, metadata_path: Path, embedder):
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.embedder = embedder
        self.index = None
        self.metadata = []

    def build(self, chunks: list[dict]):
        if not chunks:
            raise ValueError("Cannot build a vector index from zero chunks.")
        vectors = self.embedder.encode([c["text"] for c in chunks]).astype("float32")
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.metadata = chunks
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        self.metadata_path.write_text(
            json.dumps(self.metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self):
        if not self.index_path.exists() or not self.metadata_path.exists():
            raise FileNotFoundError("Vector store files are missing.")
        self.index = faiss.read_index(str(self.index_path))
        self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return self

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self.index is None:
            raise RuntimeError("Vector store has not been built or loaded.")
        vector = self.embedder.encode([query]).astype("float32")
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(vector, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            item = dict(self.metadata[idx])
            item["similarity"] = float(score)
            results.append(item)
        return results
