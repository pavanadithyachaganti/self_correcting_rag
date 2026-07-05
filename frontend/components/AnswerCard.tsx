"use client";

import React from "react";

function SourceChip({ label }: { label: string }) {
  return (
    <span className="mx-0.5 inline-flex items-center rounded-[5px] border border-accent/25 bg-accent/10 px-1.5 py-px font-mono text-[11.5px] text-accent">
      {label}
    </span>
  );
}

function renderInline(text: string, keyBase: string) {
  // Split on [source.md] / [web] citations and **bold**.
  const parts = text.split(/(\[[^\]]+?\.(?:md|txt)\]|\[web\]|\*\*[^*]+\*\*)/g);
  return parts.map((p, i) => {
    const cite = p.match(/^\[([^\]]+)\]$/);
    if (cite) return <SourceChip key={`${keyBase}-${i}`} label={cite[1]} />;
    const bold = p.match(/^\*\*([^*]+)\*\*$/);
    if (bold) return <strong key={`${keyBase}-${i}`} className="font-semibold">{bold[1]}</strong>;
    return <React.Fragment key={`${keyBase}-${i}`}>{p}</React.Fragment>;
  });
}

export function AnswerCard({ answer, sources }: { answer: string; sources: string[] }) {
  const lines = answer.split("\n");
  return (
    <div className="rounded-xl border border-line bg-panel px-[18px] py-[18px]">
      <div className="whitespace-pre-wrap text-[15.5px] leading-[1.72]">
        {lines.map((ln, i) => (
          <React.Fragment key={i}>
            {renderInline(ln, `l${i}`)}
            {i < lines.length - 1 ? "\n" : null}
          </React.Fragment>
        ))}
      </div>
      {sources.length > 0 && (
        <div className="mt-3.5 flex flex-wrap gap-1.5 border-t border-line pt-3.5">
          {sources.map((s) => (
            <SourceChip key={s} label={s} />
          ))}
        </div>
      )}
    </div>
  );
}
