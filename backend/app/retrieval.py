import os
import re
import glob
import pickle
import numpy as np
from rank_bm25 import BM25Okapi
from .config import settings
from .embeddings import get_embedder
from .extract import extract_text, SUPPORTED


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def load_corpus(*dirs):
    docs = []
    seen = set()
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for path in sorted(glob.glob(os.path.join(d, "**", "*"), recursive=True)):
            if not os.path.isfile(path) or not path.lower().endswith(SUPPORTED):
                continue
            name = os.path.basename(path)
            if name in seen:
                continue
            try:
                text = extract_text(path)
            except Exception:
                continue
            if text.strip():
                docs.append((name, text))
                seen.add(name)
    return docs


def chunk_text(text, size, overlap):
    """Paragraph-aware packing into ~size-char chunks, with hard-splitting of
    over-long paragraphs and a small overlap tail for continuity."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if not cur:
            cur = p
        elif len(cur) + len(p) + 1 <= size:
            cur = cur + "\n" + p
        else:
            chunks.append(cur)
            cur = p
        while len(cur) > size:
            chunks.append(cur[:size])
            cur = cur[max(size - overlap, 1):]
    if cur:
        chunks.append(cur)
    return chunks


def rrf_fuse(rank_lists, k=60):
    """Reciprocal rank fusion. Combines multiple ranked id lists into one."""
    scores = {}
    for rl in rank_lists:
        for rank, doc_id in enumerate(rl):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])


class NumpyVectorStore:
    """From-scratch cosine-similarity store. Embeddings are L2-normalised, so a
    dot product is the cosine. Zero external dependencies beyond NumPy."""

    def __init__(self):
        self.embeddings = None
        self.ids = []

    def add(self, ids, embs):
        self.ids = list(ids)
        self.embeddings = np.asarray(embs, dtype=np.float32)

    def search(self, query_emb, k):
        if self.embeddings is None or not self.ids:
            return []
        sims = self.embeddings @ np.asarray(query_emb, dtype=np.float32)
        idx = np.argsort(-sims)[:k]
        return [(self.ids[i], float(sims[i])) for i in idx]


class ChromaVectorStore:
    """Optional production backend. Enable with VECTOR_BACKEND=chroma."""

    def __init__(self):
        import chromadb
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.col = self.client.get_or_create_collection("docs")

    def add(self, ids, embs, documents=None):
        self.col.upsert(
            ids=list(ids),
            embeddings=[np.asarray(e, dtype=np.float32).tolist() for e in embs],
        )

    def search(self, query_emb, k):
        res = self.col.query(
            query_embeddings=[np.asarray(query_emb, dtype=np.float32).tolist()],
            n_results=k,
        )
        ids = res["ids"][0]
        dists = res["distances"][0]
        return [(i, 1.0 - float(d)) for i, d in zip(ids, dists)]


class NoOpReranker:
    def rerank(self, query, candidates, top_n):
        return candidates[:top_n]


class CrossEncoderReranker:
    """Local cross-encoder reranking. Enable with RERANKER=cross-encoder."""

    def __init__(self, model_name):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name)

    def rerank(self, query, candidates, top_n):
        if not candidates:
            return []
        pairs = [(query, c["text"]) for c in candidates]
        scores = self.model.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: -float(x[1]))
        out = []
        for c, s in ranked[:top_n]:
            c = dict(c)
            c["rerank_score"] = float(s)
            out.append(c)
        return out


def get_reranker():
    if settings.reranker == "cross-encoder":
        return CrossEncoderReranker(settings.ce_model)
    return NoOpReranker()


class Index:
    def __init__(self):
        self.embedder = get_embedder()
        self.chunks = []
        self.id2chunk = {}
        self.bm25 = None
        self.bm25_tokens = []
        self.vstore = None
        self._embs = None

    def build(self, corpus_dir):
        docs = load_corpus(corpus_dir, settings.uploads_dir)
        self.chunks = []
        cid = 0
        for src, text in docs:
            for ch in chunk_text(text, settings.chunk_size, settings.chunk_overlap):
                self.chunks.append({"id": f"c{cid}", "text": ch, "source": src})
                cid += 1
        self.id2chunk = {c["id"]: c for c in self.chunks}
        texts = [c["text"] for c in self.chunks]
        self.bm25_tokens = [tokenize(t) for t in texts]
        self.bm25 = BM25Okapi(self.bm25_tokens) if texts else None
        self._embs = self.embedder.embed(texts)
        ids = [c["id"] for c in self.chunks]
        if settings.vector_backend == "chroma":
            self.vstore = ChromaVectorStore()
            self.vstore.add(ids, self._embs)
        else:
            self.vstore = NumpyVectorStore()
            self.vstore.add(ids, self._embs)
        return len(self.chunks)

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {"chunks": self.chunks, "embeddings": self._embs, "tokens": self.bm25_tokens},
                f,
            )

    def load(self, path):
        with open(path, "rb") as f:
            d = pickle.load(f)
        self.chunks = d["chunks"]
        self.id2chunk = {c["id"]: c for c in self.chunks}
        self.bm25_tokens = d["tokens"]
        self.bm25 = BM25Okapi(self.bm25_tokens) if self.bm25_tokens else None
        self._embs = d["embeddings"]
        self.vstore = NumpyVectorStore()
        self.vstore.add([c["id"] for c in self.chunks], self._embs)


class HybridRetriever:
    def __init__(self, index):
        self.index = index
        self.reranker = get_reranker()

    def retrieve(self, query, top_k=None, rerank_top_n=None):
        top_k = top_k or settings.top_k
        rerank_top_n = rerank_top_n or settings.rerank_top_n
        if not self.index.chunks:
            return []
        q_emb = self.index.embedder.embed([query])[0]
        dense = self.index.vstore.search(q_emb, top_k)
        bm_scores = self.index.bm25.get_scores(tokenize(query))
        order = list(np.argsort(-bm_scores)[:top_k])
        sparse = [(self.index.chunks[i]["id"], float(bm_scores[i])) for i in order]
        fused = rrf_fuse([[i for i, _ in dense], [i for i, _ in sparse]])
        fused_ids = [i for i, _ in fused][:top_k]
        candidates = [dict(self.index.id2chunk[i]) for i in fused_ids if i in self.index.id2chunk]
        return self.reranker.rerank(query, candidates, rerank_top_n)
