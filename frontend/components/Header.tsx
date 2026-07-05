"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Health } from "@/lib/types";

const tabs = [
  { href: "/", label: "ask" },
  { href: "/evaluation", label: "evaluation" },
];

export default function Header() {
  const path = usePathname();
  const [health, setHealth] = useState<Health | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setOffline(true));
  }, []);

  return (
    <header className="border-b border-line">
      <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-5 py-4">
        <div className="flex items-center gap-7">
          <span className="font-mono text-[13px] tracking-wide text-fg">
            self-correcting-rag<span className="caret ml-1 inline-block h-[14px] w-[7px] translate-y-[2px] bg-accent" />
          </span>
          <nav className="flex gap-1">
            {tabs.map((t) => {
              const active = path === t.href;
              return (
                <Link
                  key={t.href}
                  href={t.href}
                  className={`rounded-md px-3 py-1.5 font-mono text-[12.5px] transition-colors ${
                    active ? "bg-panel2 text-fg" : "text-faint hover:text-fg"
                  }`}
                >
                  {t.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex flex-wrap justify-end gap-1.5 font-mono text-[11px] text-faint">
          {offline && <span className="rounded border border-line px-1.5 py-0.5 text-bad">backend offline</span>}
          {health && (
            <>
              <span className="rounded border border-line px-1.5 py-0.5">
                <span className="text-muted">llm</span> {health.provider}
              </span>
              <span className="rounded border border-line px-1.5 py-0.5">
                <span className="text-muted">embed</span> {health.embedder}
              </span>
              <span className="rounded border border-line px-1.5 py-0.5">
                <span className="text-muted">store</span> {health.vector_backend}
              </span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
