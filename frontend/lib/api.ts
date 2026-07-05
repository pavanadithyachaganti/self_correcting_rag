import type { QueryResponse, EvalAggregate, Health, TraceRow, Kb, UploadResult } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json();
}

async function upload(files: File[]): Promise<UploadResult> {
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`/api/upload failed (${res.status})`);
  return res.json();
}

export const api = {
  query: (question: string) => post<QueryResponse>("/api/query", { question }),
  evaluate: () => post<EvalAggregate>("/api/eval", {}),
  health: () => get<Health>("/api/health"),
  traces: () => get<TraceRow[]>("/api/traces"),
  kb: () => get<Kb>("/api/kb"),
  upload,
  reset: () => post<{ status: string; chunks: number }>("/api/reset", {}),
  base: BASE,
};
