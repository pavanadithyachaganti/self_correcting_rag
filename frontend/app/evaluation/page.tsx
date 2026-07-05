"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
  LineChart, Line, Legend,
} from "recharts";
import { api } from "@/lib/api";
import type { EvalAggregate, TraceRow } from "@/lib/types";
import { scoreColor, scoreClass } from "@/lib/types";
import { ScoreMeter, Label } from "@/components/Meters";

const AXIS = { stroke: "#39414a", fontSize: 11, fontFamily: "ui-monospace, monospace" };
const TOOLTIP = {
  contentStyle: { background: "#15171a", border: "1px solid #262a30", borderRadius: 8, fontSize: 12 },
  labelStyle: { color: "#9aa1a9" },
};

export default function EvaluationPage() {
  const [agg, setAgg] = useState<EvalAggregate | null>(null);
  const [history, setHistory] = useState<TraceRow[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    api.traces().then(setHistory).catch(() => {});
  }, []);

  async function run() {
    setRunning(true);
    setError("");
    try {
      const d = await api.evaluate();
      setAgg(d);
      api.traces().then(setHistory).catch(() => {});
    } catch (e) {
      setError((e as Error).message + ". Is the backend running on " + api.base + "?");
    } finally {
      setRunning(false);
    }
  }

  const barData = agg
    ? [
        { metric: "faithfulness", value: agg.faithfulness },
        { metric: "context prec.", value: agg.context_precision },
        { metric: "answer rel.", value: agg.answer_relevancy },
      ]
    : [];

  const trend = [...history]
    .reverse()
    .map((t, i) => ({
      i: i + 1,
      faithfulness: t.scores.faithfulness,
      "context precision": t.scores.context_precision,
      "answer relevancy": t.scores.answer_relevancy,
    }));

  return (
    <div>
      <h1 className="mb-1.5 text-[22px] font-medium tracking-[-0.01em]">Evaluation dashboard</h1>
      <p className="mb-5 text-[14px] text-muted">
        Run the fixed question set through the agent and measure faithfulness, context precision, and answer
        relevancy. Treat it as a regression test after any change to chunking, retrieval, or prompting.
      </p>

      <button
        onClick={run}
        disabled={running}
        className="rounded-[10px] bg-accent px-4 py-2.5 font-mono text-[13px] font-medium text-[#072016] disabled:opacity-50"
      >
        {running ? "running suite..." : "run eval suite"}
      </button>

      {error && (
        <div className="mt-5 rounded-lg border border-warn/30 bg-warn/5 px-3 py-2.5 font-mono text-[12.5px] text-warn">
          {error}
        </div>
      )}

      {agg && (
        <div className="mt-6 animate-rise">
          <Label>suite average · {agg.n} questions</Label>
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
            <ScoreMeter name="faithfulness" value={agg.faithfulness} />
            <ScoreMeter name="context precision" value={agg.context_precision} />
            <ScoreMeter name="answer relevancy" value={agg.answer_relevancy} />
          </div>

          <Label>metric comparison</Label>
          <div className="rounded-xl border border-line bg-panel p-4">
            <div className="h-[220px]">
              {mounted && (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barData} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#20242a" vertical={false} />
                    <XAxis dataKey="metric" tick={AXIS} axisLine={{ stroke: "#262a30" }} tickLine={false} />
                    <YAxis domain={[0, 1]} tick={AXIS} axisLine={false} tickLine={false} />
                    <Tooltip {...TOOLTIP} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={70}>
                      {barData.map((d, i) => (
                        <Cell key={i} fill={scoreColor(d.value)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <Label>per-question scores</Label>
          <div className="overflow-hidden rounded-xl border border-line">
            <table className="w-full border-collapse text-[13px]">
              <thead>
                <tr className="bg-panel2 font-mono text-[11px] text-faint">
                  <th className="px-3.5 py-2.5 text-left font-normal">question</th>
                  <th className="px-2 py-2.5 text-right font-normal">faith</th>
                  <th className="px-2 py-2.5 text-right font-normal">ctx&nbsp;prec</th>
                  <th className="px-3 py-2.5 text-right font-normal">ans&nbsp;rel</th>
                </tr>
              </thead>
              <tbody>
                {agg.per_question.map((p, i) => (
                  <tr key={i} className="border-t border-line bg-panel">
                    <td className="px-3.5 py-2.5 text-muted">{p.question}</td>
                    <td className={`px-2 py-2.5 text-right font-mono text-[12px] ${scoreClass(p.scores.faithfulness)}`}>
                      {p.scores.faithfulness.toFixed(2)}
                    </td>
                    <td className={`px-2 py-2.5 text-right font-mono text-[12px] ${scoreClass(p.scores.context_precision)}`}>
                      {p.scores.context_precision.toFixed(2)}
                    </td>
                    <td className={`px-3 py-2.5 text-right font-mono text-[12px] ${scoreClass(p.scores.answer_relevancy)}`}>
                      {p.scores.answer_relevancy.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Label>recent query history</Label>
      {trend.length === 0 ? (
        <div className="rounded-xl border border-line bg-panel px-4 py-6 text-center font-mono text-[12.5px] text-faint">
          no queries yet · ask something on the ask tab, then return here
        </div>
      ) : (
        <div className="rounded-xl border border-line bg-panel p-4">
          <div className="h-[220px]">
            {mounted && (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend} margin={{ top: 6, right: 10, left: -18, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#20242a" vertical={false} />
                  <XAxis dataKey="i" tick={AXIS} axisLine={{ stroke: "#262a30" }} tickLine={false} />
                  <YAxis domain={[0, 1]} tick={AXIS} axisLine={false} tickLine={false} />
                  <Tooltip {...TOOLTIP} />
                  <Legend wrapperStyle={{ fontSize: 11, fontFamily: "ui-monospace, monospace" }} />
                  <Line type="monotone" dataKey="faithfulness" stroke="#3ddc97" strokeWidth={1.5} dot={false} />
                  <Line type="monotone" dataKey="context precision" stroke="#e0a83e" strokeWidth={1.5} dot={false} />
                  <Line type="monotone" dataKey="answer relevancy" stroke="#6ea8fe" strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
