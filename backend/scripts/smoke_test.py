import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force a fully offline, dependency-light configuration.
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDER"] = "hash"
os.environ["VECTOR_BACKEND"] = "numpy"
os.environ["RERANKER"] = "none"

from app.config import settings  # noqa: E402
from app.retrieval import Index, chunk_text, rrf_fuse  # noqa: E402
from app.agent import SelfCorrectingAgent  # noqa: E402


def check(name, ok):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    assert ok, name


def main():
    print("Smoke test (offline: mock LLM, hashing embeddings, numpy store)\n")

    # unit-level checks
    chunks = chunk_text("a\n\nb\n\n" + "x" * 2000, size=700, overlap=120)
    check("chunk_text splits long text", len(chunks) >= 3)

    fused = rrf_fuse([["a", "b", "c"], ["c", "b", "d"]])
    check("rrf_fuse ranks shared items higher", fused[0][0] in {"b", "c"})

    # pipeline check
    idx = Index()
    n = idx.build(settings.corpus_dir)
    check("index builds chunks from corpus", n > 0)

    agent = SelfCorrectingAgent(idx)
    result = agent.run("What is reciprocal rank fusion?")

    check("answer is produced", isinstance(result["answer"], str) and len(result["answer"]) > 0)
    check("sources returned", len(result["sources"]) > 0)
    check("three eval scores present",
          set(result["scores"]) == {"faithfulness", "context_precision", "answer_relevancy"})
    check("trace has retrieval and faithfulness steps",
          any(s["name"] == "retrieve" for s in result["trace"]) and
          any(s["name"] == "check_faithfulness" for s in result["trace"]))
    check("total latency recorded", result["total_ms"] >= 0)

    print("\nTrace:")
    for s in result["trace"]:
        extra = ""
        if "score" in s["meta"]:
            extra = f"  score={s['meta']['score']}"
        print(f"  - {s['name']:<18} {s['duration_ms']:>7.1f} ms  {s['detail']}{extra}")

    print("\nAll smoke checks passed.")


if __name__ == "__main__":
    main()
