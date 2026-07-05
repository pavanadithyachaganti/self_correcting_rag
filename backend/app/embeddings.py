import hashlib
import numpy as np
from .config import settings


class HashingEmbedder:
    """Deterministic, dependency-free embeddings for offline runs and tests.

    Hashes tokens into a fixed-dimension vector. Not semantic, but stable and
    fast, so the whole pipeline runs with zero model downloads.
    """

    def __init__(self, dim=384):
        self.dim = dim

    def _embed_one(self, text):
        vec = np.zeros(self.dim, dtype=np.float32)
        for tok in text.lower().split():
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def embed(self, texts):
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self._embed_one(t) for t in texts])

    @property
    def dimension(self):
        return self.dim


class SentenceTransformerEmbedder:
    """Real semantic embeddings, computed locally on CPU. No API cost."""

    def __init__(self, model_name):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self._dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts):
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        return np.asarray(
            self.model.encode(list(texts), normalize_embeddings=True),
            dtype=np.float32,
        )

    @property
    def dimension(self):
        return self._dim


class GeminiEmbedder:
    """API-based embeddings. No torch, tiny memory footprint, so it fits a
    512 MB free-tier box. Uses the same free Gemini key as the LLM."""

    def __init__(self, api_key, model="text-embedding-004"):
        self.key = api_key
        self.model = model
        self._dim = 768

    def embed(self, texts):
        import httpx
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:batchEmbedContents?key={self.key}")
        out = []
        for i in range(0, len(texts), 100):
            batch = texts[i:i + 100]
            body = {"requests": [
                {"model": f"models/{self.model}", "content": {"parts": [{"text": t}]}}
                for t in batch
            ]}
            r = httpx.post(url, json=body, timeout=60)
            r.raise_for_status()
            for e in r.json()["embeddings"]:
                v = np.asarray(e["values"], dtype=np.float32)
                n = np.linalg.norm(v)
                out.append(v / n if n > 0 else v)
        return np.vstack(out)

    @property
    def dimension(self):
        return self._dim


def get_embedder():
    if settings.embedder == "sentence-transformers":
        return SentenceTransformerEmbedder(settings.st_model)
    if settings.embedder == "gemini" and settings.gemini_api_key:
        return GeminiEmbedder(settings.gemini_api_key, settings.gemini_embed_model)
    return HashingEmbedder(dim=settings.embed_dim or 384)
