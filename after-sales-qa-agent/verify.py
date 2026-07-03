#!/usr/bin/env python3
"""自证脚本：不连浏览器、不烧 token，证明校验层本身是对的。

两个断言：
  1) 黄金基准（你账号里真实的 $0.49 退款单）跑校验必须【全过】。
  2) 注入缺陷版（Coupon 被改成 -$4.00）必须【被金额勾稽逮到】——
     证明校验器不是"总是通过"，而是真的能抓错（dogfooding：注入已知缺陷看召回）。

退出码 0 表示两个预期都满足。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from aftersales_qa import run_all
from aftersales_qa.report import render_console, summarize

ROOT = Path(__file__).parent
GOLDEN = ROOT / "fixtures" / "golden"
BROKEN = ROOT / "fixtures" / "broken"


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def check_golden() -> bool:
    order = _load(GOLDEN / "order_PO-211-10754408378873659.json")
    refund = _load(GOLDEN / "refund_PO-211-10754408378873659-D01.json")
    findings = run_all({"order": order, "refund": refund, "list_entry": None})
    s = summarize(findings)
    print("── 黄金基准（真实 $0.49 退款单）──")
    print(render_console(findings))
    ok = s["ok"] and s["failed"] == 0
    print(f"\n预期：全过。实际：{'全过 ✅' if ok else '出现失败 ❌'}\n")
    return ok


def check_broken_is_caught() -> bool:
    order = _load(GOLDEN / "order_PO-211-10754408378873659.json")
    refund = _load(BROKEN / "refund_PO-211-10754408378873659-D01.json")
    findings = run_all({"order": order, "refund": refund, "list_entry": None})
    recon = [f for f in findings if f.check == "refund.amount_reconciliation"]
    caught = bool(recon) and all(not f.ok for f in recon)
    print("── 注入缺陷（Coupon 篡改为 -$4.00）──")
    for f in findings:
        if not f.ok:
            print(f"  抓到：[{f.check}] {f.message}")
    print(f"\n预期：金额勾稽失败。实际：{'已抓到 ✅' if caught else '未抓到 ❌'}\n")
    return caught


def main() -> int:
    ok1 = check_golden()
    ok2 = check_broken_is_caught()
    print("=" * 48)
    if ok1 and ok2:
        print("verify: PASS ✅ 校验层对真实单全过，且能抓到注入缺陷。")
        return 0
    print("verify: FAIL ❌ 见上方明细。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
