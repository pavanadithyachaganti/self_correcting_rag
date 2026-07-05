import os
import glob
import json
import shutil
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import settings
from .schemas import (
    QueryRequest, QueryResponse, IngestResponse, EvalRequest, EvalAggregate,
    UploadResponse, KbResponse,
)
from .retrieval import Index, load_corpus
from .extract import SUPPORTED, extract_text
from .agent import SelfCorrectingAgent
from . import store

app = FastAPI(title="Self-Correcting Agentic RAG")
_origins = (["*"] if settings.allowed_origins.strip() == "*"
            else [o.strip() for o in settings.allowed_origins.split(",") if o.strip()])
app.add_middleware(
    CORSMiddleware, allow_origins=_origins, allow_methods=["*"], allow_headers=["*"],
)

STATE = {"index": None, "agent": None}
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def get_agent():
    if STATE["agent"] is None:
        idx = Index()
        if settings.vector_backend == "numpy" and os.path.exists(settings.index_path):
            idx.load(settings.index_path)
        else:
            idx.build(settings.corpus_dir)
            if settings.vector_backend == "numpy":
                idx.save(settings.index_path)
        STATE["index"] = idx
        STATE["agent"] = SelfCorrectingAgent(idx)
    return STATE["agent"]


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "embedder": settings.embedder,
        "vector_backend": settings.vector_backend,
        "reranker": settings.reranker,
    }


@app.post("/api/ingest", response_model=IngestResponse)
def ingest():
    idx = Index()
    n = idx.build(settings.corpus_dir)
    if settings.vector_backend == "numpy":
        idx.save(settings.index_path)
    STATE["index"] = idx
    STATE["agent"] = SelfCorrectingAgent(idx)
    return IngestResponse(chunks=n, status="rebuilt")


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question is empty.")
    result = get_agent().run(req.question)
    store.save_trace(result)
    keys = ["question", "answer", "sources", "scores", "trace", "total_ms", "provider"]
    return QueryResponse(**{k: result[k] for k in keys})


@app.get("/api/traces")
def traces():
    return store.recent_traces()


@app.post("/api/eval", response_model=EvalAggregate)
def run_eval(req: EvalRequest):
    agent = get_agent()
    questions = req.questions
    if not questions:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "eval_set.json")
        if os.path.exists(path):
            with open(path) as f:
                questions = [q["question"] for q in json.load(f)]
        else:
            questions = []
    per = []
    agg = {"faithfulness": 0.0, "context_precision": 0.0, "answer_relevancy": 0.0}
    for q in questions:
        r = agent.run(q)
        per.append({"question": q, "answer": r["answer"], "scores": r["scores"]})
        for k in agg:
            agg[k] += r["scores"][k]
    n = max(len(questions), 1)
    return EvalAggregate(
        n=len(questions),
        faithfulness=round(agg["faithfulness"] / n, 3),
        context_precision=round(agg["context_precision"] / n, 3),
        answer_relevancy=round(agg["answer_relevancy"] / n, 3),
        per_question=per,
    )


def _rebuild():
    idx = Index()
    n = idx.build(settings.corpus_dir)
    if settings.vector_backend == "numpy":
        idx.save(settings.index_path)
    STATE["index"] = idx
    STATE["agent"] = SelfCorrectingAgent(idx)
    return n


@app.get("/api/kb", response_model=KbResponse)
def kb():
    docs = load_corpus(settings.corpus_dir, settings.uploads_dir)
    return KbResponse(documents=[d[0] for d in docs], count=len(docs))


@app.post("/api/upload", response_model=UploadResponse)
def upload(files: List[UploadFile] = File(...)):
    if not settings.enable_uploads:
        raise HTTPException(403, "Uploads are disabled on this deployment.")
    os.makedirs(settings.uploads_dir, exist_ok=True)
    saved, skipped = [], []
    for f in files:
        name = os.path.basename(f.filename or "")
        ext = os.path.splitext(name)[1].lower()
        if not name or ext not in SUPPORTED:
            skipped.append(name or "unnamed")
            continue
        dest = os.path.join(settings.uploads_dir, name)
        with open(dest, "wb") as out:
            shutil.copyfileobj(f.file, out)
        try:
            ok = bool(extract_text(dest).strip())
        except Exception:
            ok = False
        if ok:
            saved.append(name)
        else:
            os.remove(dest)
            skipped.append(name)
    n = _rebuild() if saved else (STATE["index"].chunks.__len__() if STATE["index"] else 0)
    return UploadResponse(files=saved, skipped=skipped, chunks=n, status="indexed" if saved else "no valid files")


@app.post("/api/reset")
def reset():
    if not settings.enable_uploads:
        raise HTTPException(403, "Uploads are disabled on this deployment.")
    if os.path.isdir(settings.uploads_dir):
        for f in glob.glob(os.path.join(settings.uploads_dir, "*")):
            try:
                os.remove(f)
            except OSError:
                pass
    n = _rebuild()
    return {"status": "reset to samples", "chunks": n}


@app.get("/")
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
