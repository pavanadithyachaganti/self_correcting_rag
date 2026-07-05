import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _get(key, default=None):
    v = os.getenv(key)
    return v if v not in (None, "") else default


class Settings:
    # LLM provider: mock | groq | gemini
    llm_provider = _get("LLM_PROVIDER", "mock")
    groq_api_key = _get("GROQ_API_KEY", "")
    groq_model = _get("GROQ_MODEL", "llama-3.3-70b-versatile")
    gemini_api_key = _get("GEMINI_API_KEY", "")
    gemini_model = _get("GEMINI_MODEL", "gemini-2.0-flash")

    # Embeddings: sentence-transformers | hash | gemini
    embedder = _get("EMBEDDER", "sentence-transformers")
    st_model = _get("ST_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    gemini_embed_model = _get("GEMINI_EMBED_MODEL", "text-embedding-004")
    embed_dim = int(_get("EMBED_DIM", "384"))

    # Vector store: numpy | chroma
    vector_backend = _get("VECTOR_BACKEND", "numpy")
    chroma_path = _get("CHROMA_PATH", "./.data/chroma")

    # Retrieval
    chunk_size = int(_get("CHUNK_SIZE", "700"))
    chunk_overlap = int(_get("CHUNK_OVERLAP", "120"))
    top_k = int(_get("TOP_K", "12"))
    rerank_top_n = int(_get("RERANK_TOP_N", "6"))
    reranker = _get("RERANKER", "none")  # none | cross-encoder
    ce_model = _get("CE_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Self-correction control
    max_retrieval_attempts = int(_get("MAX_RETRIEVAL_ATTEMPTS", "2"))
    max_generation_attempts = int(_get("MAX_GENERATION_ATTEMPTS", "2"))
    relevance_threshold = float(_get("RELEVANCE_THRESHOLD", "0.5"))
    faithfulness_threshold = float(_get("FAITHFULNESS_THRESHOLD", "0.7"))
    enable_web_fallback = _get("ENABLE_WEB_FALLBACK", "false").lower() == "true"

    # CORS: "*" or a comma-separated list of allowed origins
    allowed_origins = _get("ALLOWED_ORIGINS", "*")

    # Uploads (disable on the hosted demo to avoid re-embedding bursts on free tiers)
    enable_uploads = _get("ENABLE_UPLOADS", "true").lower() == "true"

    # Paths
    corpus_dir = _get("CORPUS_DIR", os.path.join(os.path.dirname(__file__), "..", "data", "corpus"))
    uploads_dir = _get("UPLOADS_DIR", os.path.join(os.path.dirname(__file__), "..", "data", "uploads"))
    db_path = _get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", ".data", "app.db"))
    index_path = _get("INDEX_PATH", os.path.join(os.path.dirname(__file__), "..", ".data", "index.pkl"))


settings = Settings()
