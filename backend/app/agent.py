from .config import settings
from .llm import get_llm, complete_json
from .retrieval import HybridRetriever
from .trace import Trace, span
from . import evals
from .evals import _clip

GRADE_SYS = "You grade whether retrieved passages help answer a question. Output only JSON."
GEN_SYS = (
    "You are a precise assistant. Answer ONLY using the provided context. "
    "Cite sources in square brackets like [source.md]. "
    "If the context does not contain the answer, say you do not have enough information."
)
REWRITE_SYS = "You rewrite search queries to improve retrieval. Output only the rewritten query."


class SelfCorrectingAgent:
    def __init__(self, index):
        self.index = index
        self.retriever = HybridRetriever(index)
        self.llm = get_llm()

    def run(self, question):
        trace = Trace()
        query = question
        cands = []
        grade = {"score": 0.0, "reason": ""}

        # ---- Retrieval + relevance-grading loop ----
        attempt = 0
        while attempt < settings.max_retrieval_attempts:
            attempt += 1
            with span(trace, "retrieve", f"attempt {attempt} · dense + BM25 + RRF") as m:
                cands = self.retriever.retrieve(query)
                m["query"] = query
                m["hits"] = [{"id": c["id"], "source": c["source"]} for c in cands]
            with span(trace, "grade_relevance", "LLM grades retrieved context") as m:
                grade = self._grade(question, cands)
                m["score"] = grade["score"]
                m["reason"] = grade["reason"]
            if grade["score"] >= settings.relevance_threshold or attempt >= settings.max_retrieval_attempts:
                break
            with span(trace, "rewrite_query", "low relevance · rewrite and retry", correction=True) as m:
                query = self._rewrite(question, query)
                m["new_query"] = query

        ctx_pairs = [(c["source"], c["text"]) for c in cands]
        if grade["score"] < settings.relevance_threshold and settings.enable_web_fallback:
            with span(trace, "web_fallback", "low relevance · web search", correction=True) as m:
                web = self._web_search(question)
                ctx_pairs += [("web", w) for w in web]
                m["added"] = len(web)

        contexts = [t for _, t in ctx_pairs]
        context_block = "\n\n".join(f"[{s}]\n{t}" for s, t in ctx_pairs) or "(no context retrieved)"
        sources = list(dict.fromkeys(s for s, _ in ctx_pairs))

        # ---- Generation + combined self-check loop ----
        answer = ""
        scores = {"faithfulness": 0.0, "context_precision": 0.0, "answer_relevancy": 0.0}
        strict = ""
        gattempt = 0
        while gattempt < settings.max_generation_attempts:
            gattempt += 1
            with span(trace, "generate", f"attempt {gattempt} · grounded generation") as m:
                answer = self._generate(question, context_block, strict)
                m["chars"] = len(answer)
            with span(trace, "check_faithfulness", "one judge call: verify grounding + score answer") as m:
                scores, parsed = evals.evaluate_all(self.llm, question, answer, contexts)
                m["score"] = scores["faithfulness"]
                m["context_precision"] = scores["context_precision"]
                m["answer_relevancy"] = scores["answer_relevancy"]
            if (scores["faithfulness"] >= settings.faithfulness_threshold or not parsed
                    or gattempt >= settings.max_generation_attempts):
                break
            with span(trace, "regenerate", "unfaithful · regenerate with stricter grounding", correction=True):
                strict = ("\n\nNote: a previous draft contained unsupported claims. "
                          "Use ONLY the context and do not introduce outside facts.")

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "contexts": contexts,
            "scores": scores,
            "trace": trace.to_list(),
            "total_ms": trace.total_ms,
            "provider": self.llm.name,
        }

    def _grade(self, question, cands):
        joined = "\n\n".join(f"[{i+1}] {c['text'][:500]}" for i, c in enumerate(cands)) or "(no passages)"
        user = (
            f"Question: {question}\n\nRetrieved passages:\n{joined}\n\n"
            "Rate 0..1 how well these passages collectively support answering the "
            "question. Return JSON with keys score and reason."
        )
        return _clip(complete_json(self.llm, GRADE_SYS, user))

    def _rewrite(self, question, query):
        user = (
            f"Original question: {question}\nCurrent query: {query}\n"
            "Rewrite as a better search query using keywords and synonyms. Query:"
        )
        out = self.llm.complete(REWRITE_SYS, user, temperature=0.2)
        return (out.strip().split("\n")[0][:200]) or query

    def _generate(self, question, context_block, strict):
        user = (
            f"Context:\n{context_block}\n\nQuestion: {question}\n\n"
            f"Answer using only the context above. Cite sources in square brackets.{strict}"
        )
        return self.llm.complete(GEN_SYS, user, temperature=0.1)

    def _web_search(self, query):
        try:
            from ddgs import DDGS
            with DDGS() as d:
                results = list(d.text(query, max_results=3))
            return [r.get("body", "") for r in results if r.get("body")]
        except Exception:
            return []