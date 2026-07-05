from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    scores: Dict[str, float]
    trace: List[Dict[str, Any]]
    total_ms: float
    provider: str


class IngestResponse(BaseModel):
    chunks: int
    status: str


class UploadResponse(BaseModel):
    files: List[str]
    skipped: List[str]
    chunks: int
    status: str


class KbResponse(BaseModel):
    documents: List[str]
    count: int


class EvalRequest(BaseModel):
    questions: Optional[List[str]] = None


class EvalAggregate(BaseModel):
    n: int
    faithfulness: float
    context_precision: float
    answer_relevancy: float
    per_question: List[Dict[str, Any]]
