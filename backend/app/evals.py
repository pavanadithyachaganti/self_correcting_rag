from .llm import complete_json

JUDGE_SYS = "You are a strict, calibrated evaluator. Output only valid JSON."


def _clip(res):
    """Clamp a single-score judge result: {'score','reason'} -> normalized."""
    try:
        s = float(res.get("score", 0.5))
    except (TypeError, ValueError):
        s = 0.5
    return {"score": round(max(0.0, min(1.0, s)), 3), "reason": res.get("reason", "")}


def _clip_val(v, default=0.5):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    return round(max(0.0, min(1.0, f)), 3)


def evaluate_all(llm, question, answer, contexts):
    """Single judge call returning all three metrics at once.

    Cuts three eval calls down to one, and falls back to a neutral 0.5 per field
    on a missing or malformed response, so a throttled judge reply is never
    mistaken for a genuine faithfulness failure (which would trigger a needless
    regeneration)."""
    ctx = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts)) if contexts else "(no context)"
    user = (
        "Evaluate the ANSWER to the QUESTION using the CONTEXT. "
        "Return ONLY JSON with three float fields between 0 and 1:\n"
        '{"faithfulness": _, "context_precision": _, "answer_relevancy": _}\n\n'
        "faithfulness: every claim in the answer is supported by the context, nothing fabricated.\n"
        "context_precision: the fraction of context passages relevant to the question.\n"
        "answer_relevancy: the answer addresses the question that was asked.\n\n"
        f"QUESTION: {question}\n\nCONTEXT:\n{ctx}\n\nANSWER:\n{answer}"
    )
    res = complete_json(llm, JUDGE_SYS, user)
    parsed = any(k in res for k in ("faithfulness", "context_precision", "answer_relevancy"))
    scores = {
        "faithfulness": _clip_val(res.get("faithfulness")),
        "context_precision": _clip_val(res.get("context_precision")),
        "answer_relevancy": _clip_val(res.get("answer_relevancy")),
    }
    return scores, parsed
