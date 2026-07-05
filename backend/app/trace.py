import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict


@dataclass
class Step:
    name: str
    detail: str = ""
    duration_ms: float = 0.0
    meta: dict = field(default_factory=dict)


class Trace:
    def __init__(self):
        self.steps = []

    def to_list(self):
        return [asdict(s) for s in self.steps]

    @property
    def total_ms(self):
        return round(sum(s.duration_ms for s in self.steps), 1)


@contextmanager
def span(trace, name, detail="", **meta):
    t0 = time.perf_counter()
    holder = dict(meta)
    try:
        yield holder
    finally:
        trace.steps.append(
            Step(name=name, detail=detail,
                 duration_ms=round((time.perf_counter() - t0) * 1000, 1),
                 meta=holder)
        )
