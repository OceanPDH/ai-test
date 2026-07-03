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

# 售后详情金额明细里，typeCode==0 是"实退金额"
PAID_TYPECODE = 0
# 已观测到的、构成实退金额的加性明细行类型：
# 1=Item(s) total, 2=Coupon applied, 3=Shipping, 4=Tax。
# 出现白名单外的 typeCode 时不静默计入，而是显式告警交人工确认，
# 避免非加性信息行（原价/积分等）被误当加项导致勾稽假失败。
ADDITIVE_TYPECODES = {1, 2, 3, 4}

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
    incomplete = False   # 出现未知类型或无法解析的加项 → 勾稽不完整，避免误判 FAIL
    for row in r.get("amountBreakdown") or []:
        tc = row.get("typeCode")
        cents = parse_money(row.get("value"))
        if tc == PAID_TYPECODE:
            paid = cents
        elif tc in ADDITIVE_TYPECODES:
            if cents is None:
                incomplete = True
                out.append(Finding(
                    "refund.breakdown_parse", False, "warn", sn,
                    f"明细行金额无法解析，未纳入勾稽：{row.get('key')!r}={row.get('value')!r}",
                ))
            else:
                line_items.append(cents)
        else:
            # 白名单外的 typeCode：不计入求和，显式告警交人工确认
            incomplete = True
            out.append(Finding(
                "refund.unknown_breakdown_type", False, "warn", sn,
                f"未知明细类型 typeCode={tc}（{row.get('key')!r}），未纳入勾稽，请人工确认",
            ))

    if paid is None or not line_items:
        out.append(Finding(
            "refund.amount_reconciliation", False, "error", sn,
            "无法定位实退金额或可勾稽明细，跳过勾稽",
        ))
        return out

    items_sum = sum(line_items)
    matched = items_sum == paid
    if matched:
        out.append(Finding(
            "refund.amount_reconciliation", True, "error", sn,
            f"明细勾稽通过：Σ明细 {fmt_cents(items_sum)} = 实退 {fmt_cents(paid)}",
            {"itemsSum": items_sum, "paid": paid},
        ))
    elif incomplete:
        # 有未纳入的行，不能断言是缺陷；降级为告警
        out.append(Finding(
            "refund.amount_reconciliation", False, "warn", sn,
            f"含未纳入明细，勾稽不完整：Σ已知明细 {fmt_cents(items_sum)} ≠ 实退 {fmt_cents(paid)}，请人工确认",
            {"itemsSum": items_sum, "paid": paid},
        ))
    else:
        out.append(Finding(
            "refund.amount_reconciliation", False, "error", sn,
            f"明细勾稽失败：Σ明细 {fmt_cents(items_sum)} ≠ 实退 {fmt_cents(paid)}",
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

    # 国币价交叉核对：用格式化串 priceStr 解析，避免对 price 原始整数做 ×100 假设
    # （零位小数币种如 JPY/KRW 的 price 非"分"，priceStr 才是可比的展示金额）
    for m in (r.get("methods") or []):
        nat_cents = parse_money((m.get("refundAmountNationalPrice") or {}).get("priceStr"))
        amt = parse_money(m.get("refundMethodAmount"))
        if nat_cents is not None and amt is not None:
            out.append(Finding(
                "refund.national_price_matches", nat_cents == amt, "warn", sn,
                (f"国币价 {fmt_cents(nat_cents)} = 方式金额 {fmt_cents(amt)}"
                 if nat_cents == amt else
                 f"国币价 {fmt_cents(nat_cents)} ≠ 方式金额 {fmt_cents(amt)}"),
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


def v_boundary_failsafe(record) -> list[Finding]:
    """越权/边界探针：非法/不存在/越界单号必须 fail-safe——空数据、不泄露、不串单。

    record 由浏览器边界探针产出：
        {page:'boundary_probe', requestedSn, category, hasVO, leaksRealSn, redirected}
    """
    sn = record.get("requestedSn") or "<tampered>"
    out = [
        Finding(
            "boundary.no_data_leak", not record.get("leaksRealSn"), "error", sn,
            "未泄露任何真实订单数据" if not record.get("leaksRealSn")
            else "⚠️ 非法单号竟泄露了真实订单数据（越权风险）",
        ),
        Finding(
            "boundary.no_unexpected_redirect", not record.get("redirected"), "error", sn,
            "无意外重定向" if not record.get("redirected")
            else "⚠️ 非法单号被重定向到其它订单",
        ),
        Finding(
            "boundary.fail_safe_empty", not record.get("hasVO"), "warn", sn,
            f"非法单号返回空(fail-safe)：{record.get('category')}" if not record.get("hasVO")
            else "⚠️ 非法单号竟渲染出售后数据",
        ),
    ]
    return out


def run_boundary(record) -> list[Finding]:
    try:
        return v_boundary_failsafe(record)
    except Exception as e:
        return [Finding("boundary.crashed", False, "error",
                        record.get("requestedSn", "<tampered>"),
                        f"边界校验异常：{type(e).__name__}: {e}")]


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
