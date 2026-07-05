# Deploying free: backend on Render, dashboard on Vercel

This puts the FastAPI backend on a Render free web service and the Next.js dashboard on Vercel Hobby, at zero cost. Total time is about 15 minutes.

## Why the deploy config differs from local

Render's free web service has **512 MB RAM and 0.1 CPU**. That is not enough to load torch and a local sentence-transformers model, so the deploy does not use them. Instead it uses:

- `requirements-deploy.txt` — a lean dependency set with no torch.
- `EMBEDDER=gemini` — embeddings come from the Gemini API (no local model, tiny memory). The same free Gemini key powers both the LLM and the embeddings.

If you would rather keep local sentence-transformers embeddings, host the backend on Hugging Face Spaces instead (free CPU Spaces get ~16 GB RAM). The Dockerfile in this repo works there as-is.

## Prerequisites

1. Push this repo to GitHub.
2. Get a free Gemini API key at https://aistudio.google.com (or a Groq key at https://console.groq.com if you only want it for the LLM and will use `EMBEDDER=hash`).

## Part 1 — Backend on Render

### Option A: Blueprint (uses render.yaml)

1. In Render, click **New → Blueprint** and connect this repo. Render reads `render.yaml`.
2. When prompted, set the two secret env vars:
   - `GEMINI_API_KEY` = your key
   - `ALLOWED_ORIGINS` = `*` for now (you will tighten it in Part 3)
3. Click **Apply**. First build takes a few minutes.

### Option B: Manual (if you prefer clicking through)

New → Web Service → connect the repo, then set:

| Field | Value |
| --- | --- |
| Root Directory | `backend` |
| Runtime | Python |
| Build Command | `pip install -r requirements-deploy.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

Add environment variables: `LLM_PROVIDER=gemini`, `EMBEDDER=gemini`, `VECTOR_BACKEND=numpy`, `GEMINI_API_KEY=<your key>`, `ALLOWED_ORIGINS=*`.

### Verify

When it is live, open `https://your-service.onrender.com/api/health`. You should see the provider and embedder. The index builds from the sample corpus on the first query.

## Part 2 — Dashboard on Vercel

1. In Vercel, **Add New → Project** and import the same GitHub repo.
2. Set **Root Directory** to `frontend`. Vercel auto-detects Next.js.
3. Add an environment variable:
   - `NEXT_PUBLIC_API_URL` = your Render URL, e.g. `https://your-service.onrender.com`
4. Deploy. Vercel gives you a URL like `https://your-app.vercel.app`.

## Part 3 — Lock down CORS

Back in Render, set `ALLOWED_ORIGINS` to your Vercel URL so only your dashboard can call the API:

```
ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

Save. Render redeploys automatically. Done.

## Gotchas worth knowing

- **Cold starts.** A free Render service spins down after 15 minutes of inactivity and takes 30 to 60 seconds to wake on the next request. The first query after idle will be slow. This is expected on the free tier. If a demo needs to feel instant, an external uptime pinger every 10 minutes keeps it warm, or upgrade to the $7 Starter instance.
- **Ephemeral filesystem.** On spin-up, the NumPy index and the SQLite trace history are rebuilt from scratch, so the query history resets and the first query re-embeds the corpus (a few extra seconds). Fine for a portfolio demo; attach a persistent disk on a paid plan if you need history to survive.
- **Gemini free tier limits.** The embedding and generation calls share your key's free quota. Light demo traffic is well within it.
- **Model names drift.** `gemini-2.0-flash` and `text-embedding-004` are current. If a call 400s after deploy, update `GEMINI_MODEL` or `GEMINI_EMBED_MODEL` in the Render env.
