export type Scores = {
  faithfulness: number;
  context_precision: number;
  answer_relevancy: number;
};

export type TraceStep = {
  name: string;
  detail: string;
  duration_ms: number;
  meta: {
    score?: number;
    correction?: boolean;
    new_query?: string;
    [k: string]: unknown;
  };
};

export type QueryResponse = {
  question: string;
  answer: string;
  sources: string[];
  scores: Scores;
  trace: TraceStep[];
  total_ms: number;
  provider: string;
};

export type EvalAggregate = {
  n: number;
  faithfulness: number;
  context_precision: number;
  answer_relevancy: number;
  per_question: { question: string; answer: string; scores: Scores }[];
};

export type Health = {
  status: string;
  provider: string;
  embedder: string;
  vector_backend: string;
  reranker: string;
};

export type TraceRow = {
  ts: number;
  question: string;
  answer: string;
  scores: Scores;
  provider: string;
  total_ms: number;
};

export type Kb = { documents: string[]; count: number };

export type UploadResult = {
  files: string[];
  skipped: string[];
  chunks: number;
  status: string;
};

export function scoreColor(v: number): string {
  return v >= 0.7 ? "#3ddc97" : v >= 0.4 ? "#e0a83e" : "#e06c5b";
}

export function scoreClass(v: number): string {
  return v >= 0.7 ? "text-ok" : v >= 0.4 ? "text-warn" : "text-bad";
}
