"use client";

import { scoreColor } from "@/lib/types";
import type { TraceStep } from "@/lib/types";

function stepKind(s: TraceStep): "correction" | "check" | "normal" {
  if (s.meta?.correction) return "correction";
  if (s.name === "grade_relevance" || s.name === "check_faithfulness") return "check";
  return "normal";
}

export function Trace({ steps }: { steps: TraceStep[] }) {
  return (
    <div className="relative ml-1.5 mt-1 pl-5">
      <div className="absolute left-[5px] top-1.5 bottom-1.5 w-px bg-line" />
      {steps.map((s, i) => {
        const kind = stepKind(s);
        const dot =
          kind === "correction"
            ? "bg-warn border-warn"
            : kind === "check"
            ? "bg-accent border-accent"
            : "bg-panel2 border-line2";
        const hasScore = typeof s.meta?.score === "number";
        return (
          <div
            key={i}
            className="relative border-b border-dashed border-line/70 py-2.5 last:border-none"
          >
            <span
              className={`absolute -left-[19px] top-[15px] h-[9px] w-[9px] rounded-full border-[1.5px] ${dot}`}
            />
            <div className="flex items-baseline justify-between gap-3">
              <span className="font-mono text-[13px]">
                <span className={kind === "correction" ? "text-warn" : "text-fg"}>{s.name}</span>
                {hasScore && (
                  <span
                    className="ml-2 rounded-[5px] border px-1.5 py-px font-mono text-[11px]"
                    style={{
                      color: scoreColor(s.meta.score as number),
                      borderColor: `${scoreColor(s.meta.score as number)}33`,
                    }}
                  >
                    score {(s.meta.score as number).toFixed(2)}
                  </span>
                )}
              </span>
              <span className="whitespace-nowrap font-mono text-[11px] text-faint">
                {s.duration_ms.toFixed(1)} ms
              </span>
            </div>
            <div className="mt-0.5 text-[12.5px] text-muted">{s.detail}</div>
          </div>
        );
      })}
    </div>
  );
}
