# 售后接口校验报告

总计 90 项 · 通过 88 · 失败 0 · 警告 2 · 结论 通过 ✅

| 状态 | 校验项 | 单号 | 说明 |
| --- | --- | --- | --- |
| ⚠️  | `refund.arn_format` | `PO-211-03195296431993659-D01` | ARN 非法：None |
| ⚠️  | `refund.arn_format` | `PO-211-18828955848953659-D01` | ARN 非法：None |
| ✅ | `refund.field_completeness` | `PO-211-01820879023353659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-01820879023353659-D01` | 金额明细 5 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-01820879023353659-D01` | 明细勾稽通过：Σ明细 $0.26 = 实退 $0.26 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-01820879023353659-D01` | 退款方式合计 $0.26 = 实退 $0.26 |
| ✅ | `refund.national_price_matches` | `PO-211-01820879023353659-D01` | 国币价 26¢ = 方式金额 26¢ |
| ✅ | `refund.arn_format` | `PO-211-01820879023353659-D01` | ARN 合法（23位） |
| ✅ | `refund.sn_rule` | `PO-211-01820879023353659-D01` | 售后单号符合 订单号+-D0x：PO-211-01820879023353659-D01 |
| ✅ | `order.status_known` | `PO-211-01820879023353659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-01820879023353659-D01` | 订单详情已关联该售后单 |
| ✅ | `refund.field_completeness` | `PO-211-01820889508473659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-01820889508473659-D01` | 金额明细 5 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-01820889508473659-D01` | 明细勾稽通过：Σ明细 $0.26 = 实退 $0.26 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-01820889508473659-D01` | 退款方式合计 $0.26 = 实退 $0.26 |
| ✅ | `refund.national_price_matches` | `PO-211-01820889508473659-D01` | 国币价 26¢ = 方式金额 26¢ |
| ✅ | `refund.arn_format` | `PO-211-01820889508473659-D01` | ARN 合法（23位） |
| ✅ | `refund.sn_rule` | `PO-211-01820889508473659-D01` | 售后单号符合 订单号+-D0x：PO-211-01820889508473659-D01 |
| ✅ | `order.status_known` | `PO-211-01820889508473659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-01820889508473659-D01` | 订单详情已关联该售后单 |
| ✅ | `refund.field_completeness` | `PO-211-01820899995513659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-01820899995513659-D01` | 金额明细 5 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-01820899995513659-D01` | 明细勾稽通过：Σ明细 $0.26 = 实退 $0.26 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-01820899995513659-D01` | 退款方式合计 $0.26 = 实退 $0.26 |
| ✅ | `refund.national_price_matches` | `PO-211-01820899995513659-D01` | 国币价 26¢ = 方式金额 26¢ |
| ✅ | `refund.arn_format` | `PO-211-01820899995513659-D01` | ARN 合法（23位） |
| ✅ | `refund.sn_rule` | `PO-211-01820899995513659-D01` | 售后单号符合 订单号+-D0x：PO-211-01820899995513659-D01 |
| ✅ | `order.status_known` | `PO-211-01820899995513659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-01820899995513659-D01` | 订单详情已关联该售后单 |
| ✅ | `refund.field_completeness` | `PO-211-03195296431993659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-03195296431993659-D01` | 金额明细 5 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-03195296431993659-D01` | 明细勾稽通过：Σ明细 $0.19 = 实退 $0.19 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-03195296431993659-D01` | 退款方式合计 $0.19 = 实退 $0.19 |
| ✅ | `refund.national_price_matches` | `PO-211-03195296431993659-D01` | 国币价 19¢ = 方式金额 19¢ |
| ✅ | `refund.sn_rule` | `PO-211-03195296431993659-D01` | 售后单号符合 订单号+-D0x：PO-211-03195296431993659-D01 |
| ✅ | `order.status_known` | `PO-211-03195296431993659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-03195296431993659-D01` | 订单详情已关联该售后单 |
| ✅ | `refund.field_completeness` | `PO-211-10754408378873659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-10754408378873659-D01` | 金额明细 4 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-10754408378873659-D01` | 明细勾稽通过：Σ明细 $0.49 = 实退 $0.49 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-10754408378873659-D01` | 退款方式合计 $0.49 = 实退 $0.49 |
| ✅ | `refund.national_price_matches` | `PO-211-10754408378873659-D01` | 国币价 49¢ = 方式金额 49¢ |
| ✅ | `refund.arn_format` | `PO-211-10754408378873659-D01` | ARN 合法（23位） |
| ✅ | `refund.sn_rule` | `PO-211-10754408378873659-D01` | 售后单号符合 订单号+-D0x：PO-211-10754408378873659-D01 |
| ✅ | `order.status_known` | `PO-211-10754408378873659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-10754408378873659-D01` | 订单详情已关联该售后单 |
| ✅ | `refund.field_completeness` | `PO-211-10754410998393659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-10754410998393659-D01` | 金额明细 5 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-10754410998393659-D01` | 明细勾稽通过：Σ明细 $0.30 = 实退 $0.30 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-10754410998393659-D01` | 退款方式合计 $0.30 = 实退 $0.30 |
| ✅ | `refund.national_price_matches` | `PO-211-10754410998393659-D01` | 国币价 30¢ = 方式金额 30¢ |
| ✅ | `refund.arn_format` | `PO-211-10754410998393659-D01` | ARN 合法（23位） |
| ✅ | `refund.sn_rule` | `PO-211-10754410998393659-D01` | 售后单号符合 订单号+-D0x：PO-211-10754410998393659-D01 |
| ✅ | `order.status_known` | `PO-211-10754410998393659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-10754410998393659-D01` | 订单详情已关联该售后单 |
| ✅ | `refund.field_completeness` | `PO-211-10754421484793659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-10754421484793659-D01` | 金额明细 5 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-10754421484793659-D01` | 明细勾稽通过：Σ明细 $0.30 = 实退 $0.30 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-10754421484793659-D01` | 退款方式合计 $0.30 = 实退 $0.30 |
| ✅ | `refund.national_price_matches` | `PO-211-10754421484793659-D01` | 国币价 30¢ = 方式金额 30¢ |
| ✅ | `refund.arn_format` | `PO-211-10754421484793659-D01` | ARN 合法（23位） |
| ✅ | `refund.sn_rule` | `PO-211-10754421484793659-D01` | 售后单号符合 订单号+-D0x：PO-211-10754421484793659-D01 |
| ✅ | `order.status_known` | `PO-211-10754421484793659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-10754421484793659-D01` | 订单详情已关联该售后单 |
| ✅ | `refund.field_completeness` | `PO-211-10754431970553659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-10754431970553659-D01` | 金额明细 5 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-10754431970553659-D01` | 明细勾稽通过：Σ明细 $0.30 = 实退 $0.30 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-10754431970553659-D01` | 退款方式合计 $0.30 = 实退 $0.30 |
| ✅ | `refund.national_price_matches` | `PO-211-10754431970553659-D01` | 国币价 30¢ = 方式金额 30¢ |
| ✅ | `refund.arn_format` | `PO-211-10754431970553659-D01` | ARN 合法（23位） |
| ✅ | `refund.sn_rule` | `PO-211-10754431970553659-D01` | 售后单号符合 订单号+-D0x：PO-211-10754431970553659-D01 |
| ✅ | `order.status_known` | `PO-211-10754431970553659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-10754431970553659-D01` | 订单详情已关联该售后单 |
| ✅ | `refund.field_completeness` | `PO-211-10754442455673659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-10754442455673659-D01` | 金额明细 4 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-10754442455673659-D01` | 明细勾稽通过：Σ明细 $0.42 = 实退 $0.42 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-10754442455673659-D01` | 退款方式合计 $0.42 = 实退 $0.42 |
| ✅ | `refund.national_price_matches` | `PO-211-10754442455673659-D01` | 国币价 42¢ = 方式金额 42¢ |
| ✅ | `refund.arn_format` | `PO-211-10754442455673659-D01` | ARN 合法（23位） |
| ✅ | `refund.sn_rule` | `PO-211-10754442455673659-D01` | 售后单号符合 订单号+-D0x：PO-211-10754442455673659-D01 |
| ✅ | `order.status_known` | `PO-211-10754442455673659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-10754442455673659-D01` | 订单详情已关联该售后单 |
| ✅ | `refund.field_completeness` | `PO-211-18828955848953659-D01` | 退款方式含 方式/金额 |
| ✅ | `refund.breakdown_present` | `PO-211-18828955848953659-D01` | 金额明细 5 行 |
| ✅ | `refund.amount_reconciliation` | `PO-211-18828955848953659-D01` | 明细勾稽通过：Σ明细 $0.26 = 实退 $0.26 |
| ✅ | `refund.method_amount_matches_paid` | `PO-211-18828955848953659-D01` | 退款方式合计 $0.26 = 实退 $0.26 |
| ✅ | `refund.national_price_matches` | `PO-211-18828955848953659-D01` | 国币价 26¢ = 方式金额 26¢ |
| ✅ | `refund.sn_rule` | `PO-211-18828955848953659-D01` | 售后单号符合 订单号+-D0x：PO-211-18828955848953659-D01 |
| ✅ | `order.status_known` | `PO-211-18828955848953659-D01` | 订单状态 'Refunded' 为已知枚举 |
| ✅ | `order_links_refund` | `PO-211-18828955848953659-D01` | 订单详情已关联该售后单 |