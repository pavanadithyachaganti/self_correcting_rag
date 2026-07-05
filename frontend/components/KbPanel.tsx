"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

export function KbPanel({ onChange }: { onChange?: () => void }) {
  const [count, setCount] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  async function refresh() {
    try {
      const kb = await api.kb();
      setCount(kb.count);
    } catch {
      setCount(null);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleFiles(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return;
    setBusy(true);
    setStatus("indexing...");
    try {
      const res = await api.upload(Array.from(fileList));
      const added = res.files.length;
      const skipped = res.skipped.length;
      setStatus(
        added > 0
          ? `added ${added} file${added > 1 ? "s" : ""} · ${res.chunks} chunks indexed` +
              (skipped ? ` · ${skipped} skipped` : "")
          : "no supported files (use pdf, docx, md, txt)"
      );
      await refresh();
      onChange?.();
    } catch (e) {
      setStatus((e as Error).message);
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function reset() {
    setBusy(true);
    setStatus("resetting...");
    try {
      const r = await api.reset();
      setStatus(`reset to samples · ${r.chunks} chunks`);
      await refresh();
      onChange?.();
    } catch (e) {
      setStatus((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-[10px] border border-line bg-panel px-3.5 py-2.5">
      <span className="font-mono text-[11.5px] text-muted">
        knowledge base
        <span className="ml-2 text-fg">{count === null ? "—" : `${count} docs`}</span>
      </span>

      <div className="ml-auto flex items-center gap-2">
        <button
          onClick={() => inputRef.current?.click()}
          disabled={busy}
          className="rounded-md border border-line2 px-2.5 py-1 font-mono text-[12px] text-fg hover:border-accent hover:text-accent disabled:opacity-50"
        >
          + add documents
        </button>
        <button
          onClick={reset}
          disabled={busy}
          className="font-mono text-[11.5px] text-faint hover:text-muted disabled:opacity-50"
        >
          reset
        </button>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.md,.txt"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {status && (
        <div className="w-full font-mono text-[11px] text-faint">{status}</div>
      )}
    </div>
  );
}
