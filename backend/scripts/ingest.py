import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.retrieval import Index


def main():
    idx = Index()
    n = idx.build(settings.corpus_dir)
    if settings.vector_backend == "numpy":
        idx.save(settings.index_path)
    print(f"Indexed {n} chunks from {settings.corpus_dir}")
    print(f"Embedder={settings.embedder}  vector_backend={settings.vector_backend}")


if __name__ == "__main__":
    main()
