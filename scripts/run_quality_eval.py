#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from llm_testing_lab.case_loader import load_cases
from llm_testing_lab.evaluators import EvaluationResult, MetricScore, evaluate_answer
from llm_testing_lab.providers import ProviderError, get_provider
from llm_testing_lab.reporting import summarize, write_json_report, write_markdown_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a portfolio-friendly LLM quality evaluation.")
    parser.add_argument("--cases", default="test_cases/customer_support_quality.json", help="Path to JSON test cases.")
    parser.add_argument("--provider", default="sample", choices=["sample", "deepseek"], help="Answer provider to evaluate.")
    parser.add_argument("--json-report", default="reports/quality_eval_report.json", help="JSON report path.")
    parser.add_argument("--md-report", default="reports/quality_eval_report.md", help="Markdown report path.")
    parser.add_argument("--threshold", type=float, default=0.75, help="Pass threshold for each case.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        provider = get_provider(args.provider)
    except ProviderError as exc:
        print(f"Provider error: {exc}", file=sys.stderr)
        return 2

    cases = load_cases(ROOT / args.cases)
    results = []
    for case in cases:
        try:
            answer = provider.answer(case)
            result = evaluate_answer(case, answer, pass_threshold=args.threshold)
        except Exception as exc:
            result = EvaluationResult(
                case_id=case.id,
                category=case.category,
                question=case.question,
                answer="",
                passed=False,
                score=0.0,
                metrics=[MetricScore("provider_error", 0.0, f"{type(exc).__name__}: {exc}")],
            )
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {case.id:<32} score={result.score:.3f}")

    write_json_report(results, ROOT / args.json_report)
    write_markdown_report(results, ROOT / args.md_report)

    summary = summarize(results)
    print()
    print(f"Total: {summary['total']} | Passed: {summary['passed']} | Pass rate: {summary['pass_rate']:.1%}")
    print(f"Reports: {args.json_report}, {args.md_report}")
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
