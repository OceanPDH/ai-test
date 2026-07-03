"""把 Finding 列表渲染成控制台/Markdown 报告。"""

from __future__ import annotations

from .validators import Finding


def summarize(findings: list[Finding]) -> dict:
    passed = sum(1 for f in findings if f.ok)
    fails = [f for f in findings if not f.ok and f.severity == "error"]
    warns = [f for f in findings if not f.ok and f.severity == "warn"]
    return {
        "total": len(findings),
        "passed": passed,
        "failed": len(fails),
        "warned": len(warns),
        "ok": len(fails) == 0,
    }


def render_report(findings: list[Finding], title: str = "售后接口校验报告") -> str:
    s = summarize(findings)
    icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}
    lines = [
        f"# {title}",
        "",
        f"总计 {s['total']} 项 · 通过 {s['passed']} · 失败 {s['failed']} · 警告 {s['warned']} · "
        f"结论 {'通过 ✅' if s['ok'] else '未通过 ❌'}",
        "",
        "| 状态 | 校验项 | 单号 | 说明 |",
        "| --- | --- | --- | --- |",
    ]
    order = {"FAIL": 0, "WARN": 1, "PASS": 2}
    for f in sorted(findings, key=lambda x: order[x.status]):
        lines.append(f"| {icon[f.status]} | `{f.check}` | `{f.sn}` | {f.message} |")
    return "\n".join(lines)


def render_console(findings: list[Finding]) -> str:
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
    out = []
    for f in findings:
        out.append(f"{icon[f.status]} [{f.check}] {f.message}")
    s = summarize(findings)
    out.append("")
    out.append(f"通过 {s['passed']}/{s['total']} · 失败 {s['failed']} · 警告 {s['warned']} · "
               f"{'PASS' if s['ok'] else 'FAIL'}")
    return "\n".join(out)
