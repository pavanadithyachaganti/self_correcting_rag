import re
import json
import time
import httpx
from .config import settings


def _post_with_retry(url, payload, headers=None, timeout=60, max_attempts=5):
    """POST with exponential backoff on 429 rate limits, honoring Retry-After.

    A self-correcting agent makes several model calls per query, so free-tier
    per-minute limits are easy to hit in bursts. This waits and retries rather
    than failing the whole request."""
    r = None
    for attempt in range(max_attempts):
        r = httpx.post(url, json=payload, headers=headers or {}, timeout=timeout)
        if r.status_code == 429 and attempt < max_attempts - 1:
            ra = r.headers.get("retry-after", "")
            wait = float(ra) if ra.replace(".", "", 1).isdigit() else 2 ** attempt
            time.sleep(min(wait, 30))
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r


class LLMError(Exception):
    pass


class MockProvider:
    """Runs the full pipeline with no API key. Answers are canned, but every
    step (retrieval, grading, generation, faithfulness, evals) still executes so
    the app and UI are fully demonstrable offline."""

    name = "mock"

    def complete(self, system, user, temperature=0.0, json_mode=False):
        text = user.lower()
        if json_mode:
            if "how faithful" in text:
                return json.dumps({"score": 0.82, "reason": "Mock: answer is grounded in the provided context."})
            if "fraction" in text:
                return json.dumps({"score": 0.71, "reason": "Mock: most retrieved passages look relevant."})
            if "addresses the question" in text:
                return json.dumps({"score": 0.78, "reason": "Mock: answer addresses the question."})
            if "support answering" in text:
                return json.dumps({"score": 0.70, "reason": "Mock: retrieved context appears topically relevant."})
            return json.dumps({"score": 0.70, "reason": "Mock judge default."})
        if "rewrite" in text and "query" in text:
            return user.split(":")[-1].strip()[:120] or "rewritten query"
        return ("[mock answer] Based on the retrieved context, here is a grounded summary. "
                "Set LLM_PROVIDER=groq or gemini with a free API key for real answers.")


class GroqProvider:
    name = "groq"

    def __init__(self):
        if not settings.groq_api_key:
            raise LLMError("GROQ_API_KEY not set")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = settings.groq_model
        self.key = settings.groq_api_key

    def complete(self, system, user, temperature=0.0, json_mode=False):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        r = _post_with_retry(self.url, payload,
                             headers={"Authorization": f"Bearer {self.key}"})
        return r.json()["choices"][0]["message"]["content"]


class GeminiProvider:
    name = "gemini"

    def __init__(self):
        if not settings.gemini_api_key:
            raise LLMError("GEMINI_API_KEY not set")
        self.model = settings.gemini_model
        self.key = settings.gemini_api_key

    def complete(self, system, user, temperature=0.0, json_mode=False):
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent?key={self.key}")
        gen = {"temperature": temperature}
        if json_mode:
            gen["response_mime_type"] = "application/json"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": gen,
        }
        r = _post_with_retry(url, payload)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


_provider = None


def get_llm():
    global _provider
    if _provider is not None:
        return _provider
    p = settings.llm_provider
    try:
        if p == "groq":
            _provider = GroqProvider()
        elif p == "gemini":
            _provider = GeminiProvider()
        else:
            _provider = MockProvider()
    except LLMError:
        _provider = MockProvider()
    return _provider


def _safe_json(raw):
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return {"score": 0.5, "reason": "Could not parse judge output."}


def complete_json(llm, system, user, temperature=0.0):
    raw = llm.complete(system, user, temperature=temperature, json_mode=True)
    return _safe_json(raw)