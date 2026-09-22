from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL

class Embedder:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
