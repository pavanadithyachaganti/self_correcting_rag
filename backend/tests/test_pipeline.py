import os
import sys

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("EMBEDDER", "hash")
os.environ.setdefault("VECTOR_BACKEND", "numpy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.retrieval import chunk_text, rrf_fuse, Index, HybridRetriever  # noqa: E402
from app.agent import SelfCorrectingAgent  # noqa: E402
from app.config import settings  # noqa: E402


def test_chunk_text_respects_size():
    chunks = chunk_text("x" * 3000, size=500, overlap=100)
    assert len(chunks) >= 6
    assert all(len(c) <= 500 for c in chunks)


def test_rrf_prefers_consensus():
    fused = dict(rrf_fuse([["a", "b", "c"], ["b", "a", "d"]]))
    assert fused["a"] > fused["c"]
    assert fused["b"] > fused["d"]


def _index():
    idx = Index()
    idx.build(settings.corpus_dir)
    return idx


def test_retriever_returns_candidates():
    idx = _index()
    cands = HybridRetriever(idx).retrieve("reciprocal rank fusion")
    assert len(cands) > 0
    assert all("text" in c and "source" in c for c in cands)


def test_agent_run_shape():
    idx = _index()
    result = SelfCorrectingAgent(idx).run("How does reranking work?")
    assert result["answer"]
    assert set(result["scores"]) == {"faithfulness", "context_precision", "answer_relevancy"}
    assert result["trace"]
