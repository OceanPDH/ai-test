#!/usr/bin/env python3
"""对一个 case 目录里的归一化 JSON 跑校验并出报告。

case 目录约定（由 extractor/extract.js 在浏览器里产出）：
    order_<orderSn>.json          订单详情记录
    refund_<parentAfterSalesSn>.json  售后详情记录
    list.json                     （可选）订单列表卡片数组

按 order.afterSales[].parentAfterSalesSn 把订单与售后配成 bundle。

用法：
    python run.py fixtures/golden
    python run.py fixtures/golden --md report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aftersales_qa import run_all
from aftersales_qa.report import render_console, render_report, summarize


def load_case(case_dir: Path):
    orders, refunds = {}, {}
    list_entries = {}
    for p in sorted(case_dir.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        if p.name == "list.json":
            for e in data:
                if e.get("orderSn"):
                    list_entries[e["orderSn"]] = e
        elif p.name.startswith("order_"):
            orders[data.get("orderSn")] = data
        elif p.name.startswith("refund_"):
            refunds[data.get("parentAfterSalesSn")] = data
    return orders, refunds, list_entries


def build_bundles(orders, refunds, list_entries):
    """一个售后单 = 一个 bundle。以 refund 为主，回连订单与列表卡片。"""
    bundles = []
    used_refunds = set()
    for order_sn, order in orders.items():
        for a in order.get("afterSales") or []:
            sn = a.get("parentAfterSalesSn")
            if sn and sn in refunds:
                used_refunds.add(sn)
                bundles.append({
                    "order": order,
                    "refund": refunds[sn],
                    "list_entry": list_entries.get(order_sn),
                })
    # 落单的 refund（订单详情没连上）也单独成 bundle，便于暴露"三页未打通"
    for sn, refund in refunds.items():
        if sn not in used_refunds:
            bundles.append({"order": None, "refund": refund, "list_entry": None})
    return bundles


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", help="含归一化 JSON 的目录")
    ap.add_argument("--md", help="额外写出 Markdown 报告到该路径")
    args = ap.parse_args(argv)

    case_dir = Path(args.case_dir)
    if not case_dir.is_dir():
        print(f"目录不存在：{case_dir}", file=sys.stderr)
        return 2

    orders, refunds, list_entries = load_case(case_dir)
    bundles = build_bundles(orders, refunds, list_entries)
    if not bundles:
        print("未在目录里配出任何 (订单, 售后) bundle。", file=sys.stderr)
        return 2

    all_findings = []
    for b in bundles:
        all_findings.extend(run_all(b))

    print(render_console(all_findings))
    if args.md:
        Path(args.md).write_text(render_report(all_findings), encoding="utf-8")
        print(f"\nMarkdown 报告已写入 {args.md}")

    return 0 if summarize(all_findings)["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
