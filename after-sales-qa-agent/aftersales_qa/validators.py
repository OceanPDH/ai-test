"""确定性校验器。

每个校验器吃一个 bundle（同一售后单的三页归一化记录）并产出 Finding 列表。
bundle = {
    "list_entry": {...} | None,   # 订单列表页某订单卡片（可选）
    "order":      {...} | None,   # 订单详情 order_detail 记录
    "refund":     {...} | None,   # 售后详情 refund_detail 记录
}
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .money import parse_money, fmt_cents

# 售后详情金额明细里，typeCode==0 是"实退金额"，>=1 是构成实退的各明细行
PAID_TYPECODE = 0

# 已知合法的订单状态文案（列表页/详情页共用），用于枚举校验
KNOWN_STATUSES = {
    "Processing", "Shipped", "Delivered", "Refunded",
    "Returned", "Return/Refund", "Canceled", "Cancelled", "Unpaid",
}


@dataclass
class Finding:
    check: str
    ok: bool
    severity: str           # "error" | "warn"
    sn: str
    message: str
    detail: Optional[dict] = field(default=None)

    @property
    def status(self) -> str:
        return "PASS" if self.ok else ("WARN" if self.severity == "warn" else "FAIL")


def _sn(bundle) -> str:
    r = bundle.get("refund") or {}
    o = bundle.get("order") or {}
    return r.get("parentAfterSalesSn") or o.get("orderSn") or "<unknown>"


# --------------------------------------------------------------------------- #
# 校验器
# --------------------------------------------------------------------------- #

def v_field_completeness(bundle) -> list[Finding]:
    """售后详情核心字段完整性。"""
    out, sn = [], _sn(bundle)
    r = bundle.get("refund")
    if not r:
        return out
    methods = r.get("methods") or []
    # ARN 不作为硬性必填：取消退款(canceled item)等场景本就无 ARN，
    # 缺 ARN 交由 refund.arn_format 出 WARN，避免误判为 FAIL。
    ok_methods = bool(methods) and all(
        m.get("refundMethod") and m.get("refundMethodAmount") is not None
        for m in methods
    )
    out.append(Finding(
        "refund.field_completeness", ok_methods, "error", sn,
        "退款方式含 方式/金额" if ok_methods else "退款方式缺少 方式/金额字段",
        {"methodCount": len(methods)},
    ))
    breakdown = r.get("amountBreakdown") or []
    out.append(Finding(
        "refund.breakdown_present", bool(breakdown), "error", sn,
        f"金额明细 {len(breakdown)} 行" if breakdown else "金额明细缺失",
    ))
    return out


def v_amount_reconciliation(bundle) -> list[Finding]:
    """金额勾稽：明细各行之和 == 实退金额 == 各退款方式金额之和 == 国币价。"""
    out, sn = [], _sn(bundle)
    r = bundle.get("refund")
    if not r:
        return out
    paid = None
    line_items = []
    for row in r.get("amountBreakdown") or []:
        cents = parse_money(row.get("value"))
        if row.get("typeCode") == PAID_TYPECODE:
            paid = cents
        elif cents is not None:
            line_items.append(cents)

    if paid is None or not line_items:
        out.append(Finding(
            "refund.amount_reconciliation", False, "error", sn,
            "无法定位实退金额或明细行，跳过勾稽",
        ))
        return out

    items_sum = sum(line_items)
    ok_break = items_sum == paid
    out.append(Finding(
        "refund.amount_reconciliation", ok_break, "error", sn,
        (f"明细勾稽通过：Σ明细 {fmt_cents(items_sum)} = 实退 {fmt_cents(paid)}"
         if ok_break else
         f"明细勾稽失败：Σ明细 {fmt_cents(items_sum)} ≠ 实退 {fmt_cents(paid)}"),
        {"itemsSum": items_sum, "paid": paid},
    ))

    methods_sum = sum(
        (parse_money(m.get("refundMethodAmount")) or 0) for m in (r.get("methods") or [])
    )
    ok_methods = methods_sum == paid
    out.append(Finding(
        "refund.method_amount_matches_paid", ok_methods, "error", sn,
        (f"退款方式合计 {fmt_cents(methods_sum)} = 实退 {fmt_cents(paid)}"
         if ok_methods else
         f"退款方式合计 {fmt_cents(methods_sum)} ≠ 实退 {fmt_cents(paid)}"),
    ))

    # 国币价交叉核对（refundAmountNationalPrice.price 已是分）
    for m in (r.get("methods") or []):
        nat = (m.get("refundAmountNationalPrice") or {}).get("price")
        amt = parse_money(m.get("refundMethodAmount"))
        if nat is not None and amt is not None:
            out.append(Finding(
                "refund.national_price_matches", nat == amt, "warn", sn,
                (f"国币价 {nat}¢ = 方式金额 {amt}¢"
                 if nat == amt else
                 f"国币价 {nat}¢ ≠ 方式金额 {amt}¢"),
            ))
    return out


def v_arn_format(bundle) -> list[Finding]:
    """ARN 应为纯数字且长度合理（Visa/MC ARN 通常 23 位）。"""
    out, sn = [], _sn(bundle)
    r = bundle.get("refund")
    if not r:
        return out
    for m in (r.get("methods") or []):
        arn = m.get("arn")
        ok = bool(arn) and arn.isdigit() and 15 <= len(arn) <= 30
        out.append(Finding(
            "refund.arn_format", ok, "warn", sn,
            f"ARN 合法（{len(arn)}位）" if ok else f"ARN 非法：{arn!r}",
        ))
    return out


def v_sn_rule(bundle) -> list[Finding]:
    """售后单号规则：parent_after_sales_sn = 订单号 + -D0x；并可推导 PA 票据号。"""
    out = []
    o, r = bundle.get("order"), bundle.get("refund")
    if not (o and r):
        return out
    order_sn = o.get("orderSn") or ""
    sn = r.get("parentAfterSalesSn") or ""
    ok = bool(order_sn) and sn.startswith(order_sn + "-D") and re.search(r"-D\d{2}$", sn)
    msg = f"售后单号符合 订单号+-D0x：{sn}" if ok else f"售后单号不符合规则：{sn!r}（订单号 {order_sn!r}）"
    detail = None
    if ok:
        pa = "PA" + order_sn[2:] + sn[len(order_sn):]   # PO->PA 换前缀
        detail = {"parentAfterSalesSn": sn, "derivedTicketSn": pa}
    out.append(Finding("refund.sn_rule", bool(ok), "error", sn, msg, detail))
    return out


def v_status_consistency(bundle) -> list[Finding]:
    """跨页状态一致性：列表 ↔ 订单详情 ↔ 售后详情。"""
    out = []
    o, r, le = bundle.get("order"), bundle.get("refund"), bundle.get("list_entry")
    sn = _sn(bundle)
    if not o:
        return out
    prompt = ((o.get("orderStatus") or {}).get("orderStatusPrompt")) or ""

    out.append(Finding(
        "order.status_known", prompt in KNOWN_STATUSES, "warn", sn,
        f"订单状态 {prompt!r} 为已知枚举" if prompt in KNOWN_STATUSES
        else f"订单状态 {prompt!r} 不在已知枚举内",
    ))

    # 列表状态 == 订单详情状态
    if le and le.get("status"):
        ok = le["status"] == prompt
        out.append(Finding(
            "list_vs_order.status", ok, "error", sn,
            f"列表={le['status']} 与 详情={prompt} 一致" if ok
            else f"列表={le['status']} 与 详情={prompt} 不一致",
        ))

    # 存在售后详情 → 订单详情的 afterSales 里应能连上同一个 parentAfterSalesSn
    if r:
        target = r.get("parentAfterSalesSn")
        linked = any(
            (a.get("parentAfterSalesSn") == target) for a in (o.get("afterSales") or [])
        )
        out.append(Finding(
            "order_links_refund", linked, "error", sn,
            "订单详情已关联该售后单" if linked
            else "订单详情未关联该售后单（列表/详情/售后三页未打通）",
        ))
    return out


ALL_VALIDATORS = [
    v_field_completeness,
    v_amount_reconciliation,
    v_arn_format,
    v_sn_rule,
    v_status_consistency,
]


def run_all(bundle) -> list[Finding]:
    findings: list[Finding] = []
    for v in ALL_VALIDATORS:
        try:
            findings.extend(v(bundle))
        except Exception as e:  # 校验器自身异常也算一条 error，方便定位
            findings.append(Finding(
                f"{v.__name__}.crashed", False, "error", _sn(bundle),
                f"校验器异常：{type(e).__name__}: {e}",
            ))
    return findings
