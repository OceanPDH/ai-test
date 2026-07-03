#!/usr/bin/env python3
"""用本会话从测试账号抽取的真实数据，生成 fixtures/live/ 下的归一化 case。

数据来源：浏览器抽取层（extractor/extract.js）在已登录会话内读 SSR 数据。
共 10 个 Refunded 订单，各 1 笔 -D01 售后。仅含业务字段（卡号已脱敏为 ...9199）。
"""

import json
from pathlib import Path

LIVE = Path(__file__).parent / "fixtures" / "live"

LOST = "Refund issued for 1 item from lost package"
CANCEL = "Refund issued for 1 canceled item"

# (orderSn, afterSalesStatusPrompt)
ORDERS = [
    ("PO-211-10754408378873659", LOST),
    ("PO-211-10754442455673659", LOST),
    ("PO-211-10754421484793659", LOST),
    ("PO-211-10754431970553659", LOST),
    ("PO-211-10754410998393659", LOST),
    ("PO-211-01820889508473659", LOST),
    ("PO-211-01820899995513659", LOST),
    ("PO-211-01820879023353659", LOST),
    ("PO-211-03195296431993659", CANCEL),
    ("PO-211-18828955848953659", CANCEL),
]

# 售后详情归一化记录（抽取所得）。b=breakdown 用简写元组 (key, value, typeCode)。
def refund(sn, arn, amt, price, breakdown):
    return {
        "page": "refund_detail",
        "parentAfterSalesSn": sn,
        "refundMethodNote": None,
        "isEstimate": False,
        "totalReturnCreditAmount": 0,
        "methods": [{
            "refundMethod": "Mastercard ...9199",
            "refundMethodType": 1,
            "arn": arn,
            "refundMethodAmount": amt,
            "refundAmountNationalPrice": {"price": price, "cur": "USD", "priceStr": amt},
        }],
        "amountBreakdown": [{"key": k, "value": v, "typeCode": t} for (k, v, t) in breakdown],
    }


PAID = "Amount you paid for the refund items:"
ITEM = "Item(s) total:"
COUPON = "Coupon applied:"
SHIP = "Shipping:"
TAX = "Tax:"

REFUNDS = [
    refund("PO-211-10754408378873659-D01", "72703402352016366598081", "0.49", 49,
           [(PAID, "$0.49", 0), (ITEM, "$5.49", 1), (COUPON, "-$5.00", 2), (SHIP, "FREE", 3)]),
    refund("PO-211-10754442455673659-D01", "72703402352016366498738", "0.42", 42,
           [(PAID, "$0.42", 0), (ITEM, "$0.39", 1), (SHIP, "FREE", 3), (TAX, "$0.03", 4)]),
    refund("PO-211-10754421484793659-D01", "72703402352016367203947", "0.30", 30,
           [(PAID, "$0.30", 0), (ITEM, "$0.39", 1), (COUPON, "-$0.11", 2), (SHIP, "FREE", 3), (TAX, "$0.02", 4)]),
    refund("PO-211-10754431970553659-D01", "72703402352016367203863", "0.30", 30,
           [(PAID, "$0.30", 0), (ITEM, "$0.39", 1), (COUPON, "-$0.11", 2), (SHIP, "FREE", 3), (TAX, "$0.02", 4)]),
    refund("PO-211-10754410998393659-D01", "72703402352016366598206", "0.30", 30,
           [(PAID, "$0.30", 0), (ITEM, "$0.39", 1), (COUPON, "-$0.11", 2), (SHIP, "FREE", 3), (TAX, "$0.02", 4)]),
    refund("PO-211-01820889508473659-D01", "72703403024018002154770", "0.26", 26,
           [(PAID, "$0.26", 0), (ITEM, "$0.34", 1), (COUPON, "-$0.10", 2), (SHIP, "FREE", 3), (TAX, "$0.02", 4)]),
    refund("PO-211-01820899995513659-D01", "72703403024018002648755", "0.26", 26,
           [(PAID, "$0.26", 0), (ITEM, "$0.34", 1), (COUPON, "-$0.10", 2), (SHIP, "FREE", 3), (TAX, "$0.02", 4)]),
    refund("PO-211-01820879023353659-D01", "72703403024018002452166", "0.26", 26,
           [(PAID, "$0.26", 0), (ITEM, "$0.34", 1), (COUPON, "-$0.10", 2), (SHIP, "FREE", 3), (TAX, "$0.02", 4)]),
    # 以下两笔为 canceled item：无 ARN
    refund("PO-211-03195296431993659-D01", None, "0.19", 19,
           [(PAID, "$0.19", 0), (ITEM, "$0.24", 1), (COUPON, "-$0.07", 2), (SHIP, "FREE", 3), (TAX, "$0.02", 4)]),
    refund("PO-211-18828955848953659-D01", None, "0.26", 26,
           [(PAID, "$0.26", 0), (ITEM, "$0.34", 1), (COUPON, "-$0.10", 2), (SHIP, "FREE", 3), (TAX, "$0.02", 4)]),
]


def main():
    LIVE.mkdir(parents=True, exist_ok=True)
    for order_sn, as_prompt in ORDERS:
        rec = {
            "page": "order_detail",
            "orderSn": order_sn,
            "orderStatus": {"orderStatusPrompt": "Refunded", "orderId": order_sn},
            "parentStatus": 6,
            "afterSales": [{"statusPrompt": as_prompt, "parentAfterSalesSn": order_sn + "-D01"}],
        }
        (LIVE / f"order_{order_sn}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2))
    for r in REFUNDS:
        (LIVE / f"refund_{r['parentAfterSalesSn']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2))
    # list.json：extractList() 在列表页产出的每单状态（本账号 10 单均 Refunded），
    # 用于 list_vs_order.status 跨页一致性校验。
    listing = [{"orderSn": order_sn, "status": "Refunded"} for order_sn, _ in ORDERS]
    (LIVE / "list.json").write_text(json.dumps(listing, ensure_ascii=False, indent=2))
    print(f"wrote {len(ORDERS)} orders + {len(REFUNDS)} refunds + list.json → {LIVE}")


if __name__ == "__main__":
    main()
