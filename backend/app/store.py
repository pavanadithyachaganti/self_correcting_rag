import os
import time
import json
import sqlite3
from .config import settings


def _conn():
    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
    c = sqlite3.connect(settings.db_path)
    c.execute(
        """CREATE TABLE IF NOT EXISTS traces(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL, question TEXT, answer TEXT,
            scores TEXT, trace TEXT, provider TEXT, total_ms REAL)"""
    )
    return c


def save_trace(result):
    c = _conn()
    c.execute(
        "INSERT INTO traces(ts,question,answer,scores,trace,provider,total_ms) VALUES (?,?,?,?,?,?,?)",
        (time.time(), result["question"], result["answer"],
         json.dumps(result["scores"]), json.dumps(result["trace"]),
         result["provider"], result["total_ms"]),
    )
    c.commit()
    c.close()


def recent_traces(limit=20):
    c = _conn()
    rows = c.execute(
        "SELECT ts,question,answer,scores,provider,total_ms FROM traces ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    c.close()
    return [
        {"ts": r[0], "question": r[1], "answer": r[2],
         "scores": json.loads(r[3]), "provider": r[4], "total_ms": r[5]}
        for r in rows
    ]
