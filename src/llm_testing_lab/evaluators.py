from __future__ import annotations

from dataclasses import asdict, dataclass

from llm_testing_lab.case_loader import EvaluationCase


@dataclass(frozen=True)
class MetricScore:
    name: str
    score: float
    reason: str


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    category: str
    question: str
    answer: str
    passed: bool
    score: float
    metrics: list[MetricScore]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["metrics"] = [asdict(metric) for metric in self.metrics]
        return data


def _contains_all(answer: str, terms: list[str]) -> tuple[float, str]:
    if not terms:
        return 1.0, "No required terms configured."
    hits = [term for term in terms if term in answer]
    missing = [term for term in terms if term not in answer]
    score = len(hits) / len(terms)
    if missing:
        return score, f"Missing required terms: {', '.join(missing)}"
    return score, "All required terms are present."


def _contains_none(answer: str, terms: list[str]) -> tuple[float, str]:
    hits = [term for term in terms if term in answer]
    if hits:
        return 0.0, f"Contains prohibited terms: {', '.join(hits)}"
    return 1.0, "No prohibited terms found."


def _character_overlap(answer: str, reference: str) -> tuple[float, str]:
    answer_chars = {char for char in answer if char.strip()}
    reference_chars = {char for char in reference if char.strip()}
    if not reference_chars:
        return 1.0, "No reference answer configured."
    score = len(answer_chars & reference_chars) / len(reference_chars)
    return score, f"Reference character coverage is {score:.2f}."


def evaluate_answer(case: EvaluationCase, answer: str, *, pass_threshold: float = 0.75) -> EvaluationResult:
    """Run deterministic checks that are easy to inspect and CI-friendly."""
    required_score, required_reason = _contains_all(answer, case.must_include)
    prohibited_score, prohibited_reason = _contains_none(answer, case.must_not_include)
    reference_score, reference_reason = _character_overlap(answer, case.reference_answer)

    metrics = [
        MetricScore("required_terms", required_score, required_reason),
        MetricScore("prohibited_terms", prohibited_score, prohibited_reason),
        MetricScore("reference_overlap", reference_score, reference_reason),
    ]
    score = (required_score * 0.45) + (prohibited_score * 0.35) + (reference_score * 0.20)
    return EvaluationResult(
        case_id=case.id,
        category=case.category,
        question=case.question,
        answer=answer,
        passed=score >= pass_threshold,
        score=round(score, 4),
        metrics=metrics,
    )
