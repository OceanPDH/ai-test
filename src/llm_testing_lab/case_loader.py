from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    category: str
    question: str
    reference_answer: str
    context: str
    must_include: list[str]
    must_not_include: list[str]
    sample_answer: str = ""


def load_cases(path: str | Path) -> list[EvaluationCase]:
    """Load JSON test cases into typed case objects."""
    raw_cases = json.loads(Path(path).read_text(encoding="utf-8"))
    return [EvaluationCase(**item) for item in raw_cases]
