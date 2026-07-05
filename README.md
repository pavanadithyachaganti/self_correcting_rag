# Self-Correcting Agentic RAG

A retrieval-augmented generation system that does not trust its own first attempt. It grades the passages it retrieves, rewrites the query and retrieves again when they are weak, verifies that the generated answer is actually grounded in those passages, and regenerates when it is not. Every answer comes back with three evaluation scores and a full execution trace, so you can see exactly how it was produced.

Most RAG demos stop at "retrieve, stuff into prompt, answer." This one adds the parts that decide whether a RAG system is trustworthy in production: self-correction loops, automated evaluation, and observability.

> Runs with zero API keys and zero cost. A built-in mock provider exercises the entire pipeline offline; drop in a free Groq or Gemini key for real answers.

## What makes it different

- **Two self-correction loops.** A relevance grader can trigger query rewriting and re-retrieval. A faithfulness check can trigger regeneration under stricter grounding. Both are visible in the trace.
- **Built-in evaluation.** Every response is scored for faithfulness, context precision, and answer relevancy using an LLM-as-judge, and a batch eval suite turns the fixed question set into a regression test.
- **Full observability.** Each request returns a step-by-step trace with per-step timing, retrieval hits, and grader scores. History is persisted to SQLite.
- **Framework-free orchestration.** The agent loop, hybrid retrieval, RRF fusion, and evals are written from scratch in plain Python. No LangChain or LangGraph, which keeps the control flow explicit and easy to reason about.
- **Hybrid retrieval.** Dense embeddings and BM25 are fused with reciprocal rank fusion, with optional cross-encoder reranking.
- **Bring your own documents.** PDF, DOCX, Markdown, and text files can be dropped into the corpus folder or uploaded from the UI. They are extracted, chunked, and indexed on the fly.

## How the self-correction works

```
question
   -> hybrid retrieve (dense + BM25 + RRF)
   -> grade relevance ----- weak? --> rewrite query, retrieve again
   -> generate answer (grounded, cited)
   -> check faithfulness -- unfaithful? --> regenerate, stricter grounding
   -> answer + faithfulness / context precision / answer relevancy + trace
```

## Quickstart

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://localhost:8000. The index builds automatically from `data/corpus` on the first query.

That runs with `LLM_PROVIDER=mock`, so answers are placeholders but retrieval, grading, scores, and the trace are all live. For real answers, get a free key from [Groq](https://console.groq.com) or [Google AI Studio](https://aistudio.google.com) and set it in `.env`:

```
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

No Python environment handy? `docker compose up --build` then open http://localhost:8000.

## Frontend (Next.js dashboard)

A separate Next.js + TypeScript front end lives in `frontend/`. It has two views: an **Ask** page (answer, trust scores, reasoning trace) and an **Evaluation dashboard** (run the suite, aggregate metric cards, a metric-comparison bar chart, a per-question table, and a live faithfulness trend across recent queries, all with recharts).

```bash
# with the backend already running on :8000
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000. The API base URL is set by `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

### Verify it without the server

```bash
python scripts/smoke_test.py     # offline end-to-end check, no keys, no model download
python scripts/run_eval.py       # batch eval over the question set
pip install pytest && pytest     # unit tests
```

## Configuration

Everything is controlled from `.env`. The defaults are chosen so it runs anywhere.

| Variable | Default | Options |
| --- | --- | --- |
| `LLM_PROVIDER` | `mock` | `mock`, `groq`, `gemini` |
| `EMBEDDER` | `sentence-transformers` | `sentence-transformers`, `hash` |
| `VECTOR_BACKEND` | `numpy` | `numpy`, `chroma` |
| `RERANKER` | `none` | `none`, `cross-encoder` |
| `RELEVANCE_THRESHOLD` | `0.5` | grade below this triggers a rewrite |
| `FAITHFULNESS_THRESHOLD` | `0.7` | score below this triggers a regenerate |
| `ENABLE_WEB_FALLBACK` | `false` | web search when retrieval stays weak |

The `numpy` store is a from-scratch cosine-similarity index. Switch `VECTOR_BACKEND=chroma` (after `pip install chromadb`) to use ChromaDB with the same interface.

## Evaluation methodology

Three metrics, computed by a judge model, cover the two stages of a RAG system and the link between them:

- **Faithfulness** — is every claim in the answer supported by the retrieved context? This is the hallucination signal.
- **Context precision** — what fraction of retrieved passages were actually relevant? This is the retrieval-quality signal.
- **Answer relevancy** — does the answer address the question that was asked?

`scripts/run_eval.py` and the "run eval suite" button run all questions in `data/eval_set.json` and report per-question and average scores, so any change to chunking, retrieval, or prompting can be measured rather than guessed at.

## Project structure

```
backend/
  app/
    agent.py         self-correction loops (retrieval-grade, generate-verify)
    retrieval.py     chunking, hybrid retrieval, RRF, reranking, index
    embeddings.py    sentence-transformers and hashing embedders
    llm.py           Groq / Gemini / mock providers
    evals.py         faithfulness, context precision, answer relevancy
    trace.py         execution trace with timing spans
    store.py         SQLite trace history
    main.py          FastAPI app and endpoints
    static/index.html  the UI
  data/corpus/       sample knowledge base
  scripts/           ingest, run_eval, smoke_test
  tests/             pytest suite
frontend/
  app/
    page.tsx             ask view
    evaluation/page.tsx  eval dashboard (charts + per-question table)
  components/         header, meters, trace, answer card
  lib/               api client and types
```

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /api/query` | run the agent on a question, return answer + scores + trace |
| `POST /api/eval` | run the batch eval suite |
| `POST /api/upload` | upload PDF / DOCX / MD / TXT files, extract, index them |
| `GET /api/kb` | list the documents currently in the knowledge base |
| `POST /api/reset` | clear uploaded files, restore the sample corpus |
| `POST /api/ingest` | rebuild the index from the corpus |
| `GET /api/traces` | recent query history |
| `GET /api/health` | active provider, embedder, and store |

## Deployment

Deploy free with the backend on a Render web service and the dashboard on Vercel. Full step-by-step in [DEPLOY.md](DEPLOY.md). The deploy uses API-based Gemini embeddings and a lean requirements file so it fits Render's free 512 MB instance without torch.

## Roadmap

- Streaming token output and live trace updates
- Config comparison mode in the dashboard (chunk size, retriever, reranker side by side)
- GraphRAG mode for multi-hop questions
- Optional Langfuse or Phoenix export for the trace data

## What this demonstrates

Agentic control flow, hybrid retrieval, reranking, RAG evaluation, LLM-as-judge, observability, provider abstraction, and clean API design, built end to end without a framework doing the thinking.
