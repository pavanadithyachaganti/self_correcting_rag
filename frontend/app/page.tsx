"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { QueryResponse } from "@/lib/types";
import { AnswerCard } from "@/components/AnswerCard";
import { MeterGrid, Label } from "@/components/Meters";
import { Trace } from "@/components/Trace";
import { KbPanel } from "@/components/KbPanel";

const EXAMPLES: { q: string; hard?: boolean }[] = [
  { q: "What is reciprocal rank fusion?" },
  { q: "How does corrective RAG handle bad retrieval?" },
  { q: "Why use a cross-encoder for reranking?" },
  { q: "What does the faithfulness metric measure?" },
  { q: "How does HNSW indexing speed up vector search?", hard: true },
];

export default function AskPage() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState("");

  async function ask(question?: string) {
    const text = (question ?? q).trim();
    if (!text) return;
    setQ(text);
    setLoading(true);
    setError("");
    try {
      setResult(await api.query(text));
    } catch (e) {
      setError((e as Error).message + ". Is the backend running on " + api.base + "?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="mb-1.5 text-[22px] font-medium tracking-[-0.01em]">Ask the knowledge base</h1>
      <p className="mb-5 text-[14px] text-muted">
        Every answer is graded for relevance, verified for faithfulness, and returned with its full reasoning trace.
      </p>

      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder="e.g. What is reciprocal rank fusion?"
          className="flex-1 rounded-[10px] border border-line bg-panel px-3.5 py-3 text-[15px] outline-none placeholder:text-faint focus:border-line2"
        />
        <button
          onClick={() => ask()}
          disabled={loading}
          className="rounded-[10px] bg-accent px-5 text-[14px] font-medium text-[#072016] disabled:opacity-50"
        >
          {loading ? "..." : "Ask"}
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {EXAMPLES.map((e) => (
          <button
            key={e.q}
            onClick={() => ask(e.q)}
            title={
              e.hard
                ? "Not covered by the knowledge base. Watch the agent grade retrieval as weak, rewrite the query, and retry before answering honestly."
                : undefined
            }
            className={
              e.hard
                ? "rounded-full border border-warn/40 bg-warn/5 px-2.5 py-1.5 text-[12.5px] text-warn hover:border-warn"
                : "rounded-full border border-line bg-panel px-2.5 py-1.5 text-[12.5px] text-muted hover:border-line2 hover:text-fg"
            }
          >
            {e.q}
          </button>
        ))}
      </div>

      <KbPanel />

      {error && (
        <div className="mt-5 rounded-lg border border-warn/30 bg-warn/5 px-3 py-2.5 font-mono text-[12.5px] text-warn">
          {error}
        </div>
      )}

      {result && !error && (
        <div className="mt-7 animate-rise">
          <AnswerCard answer={result.answer} sources={result.sources} />

          <Label>trust scores</Label>
          <MeterGrid scores={result.scores} />

          <div className="mt-3 flex flex-wrap gap-3.5 font-mono text-[11.5px] text-faint">
            <span>provider: {result.provider}</span>
            <span>latency: {result.total_ms.toFixed(0)} ms</span>
            <span>steps: {result.trace.length}</span>
          </div>

          <Label>reasoning trace</Label>
          <Trace steps={result.trace} />
        </div>
      )}
    </div>
  );
}
