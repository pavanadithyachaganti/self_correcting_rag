"use client";

import { scoreColor } from "@/lib/types";

export function ScoreMeter({ name, value }: { name: string; value: number }) {
  const color = scoreColor(value);
  return (
    <div className="rounded-[10px] border border-line bg-panel px-3.5 py-3">
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[11.5px] text-muted">{name}</span>
        <span className="font-mono text-[16px]" style={{ color }}>
          {value.toFixed(2)}
        </span>
      </div>
      <div className="mt-2.5 h-[5px] overflow-hidden rounded-[3px] bg-[#23272d]">
        <div
          className="h-full rounded-[3px] transition-[width] duration-500"
          style={{ width: `${Math.round(value * 100)}%`, background: color }}
        />
      </div>
    </div>
  );
}

export function MeterGrid({ scores }: { scores: { faithfulness: number; context_precision: number; answer_relevancy: number } }) {
  return (
    <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
      <ScoreMeter name="faithfulness" value={scores.faithfulness} />
      <ScoreMeter name="context precision" value={scores.context_precision} />
      <ScoreMeter name="answer relevancy" value={scores.answer_relevancy} />
    </div>
  );
}

export function Label({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-2.5 mt-6 font-mono text-[11px] uppercase tracking-[0.09em] text-faint">
      {children}
    </div>
  );
}
