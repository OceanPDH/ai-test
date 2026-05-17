from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from llm_testing_lab.evaluators import EvaluationResult


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def write_json_report(results: list[EvaluationResult], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summarize(results),
        "results": [result.to_dict() for result in results],
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown_report(results: list[EvaluationResult], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = summarize(results)
    lines = [
        "# LLM Quality Evaluation Report",
        "",
        f"- Total cases: {summary['total']}",
        f"- Passed: {summary['passed']}",
        f"- Pass rate: {summary['pass_rate']:.1%}",
        f"- Average score: {summary['average_score']:.3f}",
        "",
        "## By Category",
        "",
    ]
    for category, stats in summary["by_category"].items():
        lines.append(f"- {category}: {stats['passed']}/{stats['total']} passed, avg {stats['average_score']:.3f}")
    lines.extend(["", "## Cases", ""])
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.extend(
            [
                f"### {result.case_id} - {status}",
                "",
                f"- Category: {result.category}",
                f"- Score: {result.score:.3f}",
                f"- Question: {_md_cell(result.question)}",
                f"- Answer: {_md_cell(result.answer)}",
                "",
                "| Metric | Score | Reason |",
                "| --- | ---: | --- |",
            ]
        )
        for metric in result.metrics:
            lines.append(f"| {_md_cell(metric.name)} | {metric.score:.3f} | {_md_cell(metric.reason)} |")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def summarize(results: list[EvaluationResult]) -> dict:
    if not results:
        return {"total": 0, "passed": 0, "pass_rate": 0.0, "average_score": 0.0, "by_category": {}}
    by_category: dict[str, list[EvaluationResult]] = defaultdict(list)
    for result in results:
        by_category[result.category].append(result)
    category_summary = {}
    for category, items in sorted(by_category.items()):
        category_summary[category] = {
            "total": len(items),
            "passed": sum(item.passed for item in items),
            "average_score": sum(item.score for item in items) / len(items),
        }
    return {
        "total": len(results),
        "passed": sum(result.passed for result in results),
        "pass_rate": sum(result.passed for result in results) / len(results),
        "average_score": sum(result.score for result in results) / len(results),
        "by_category": category_summary,
    }
