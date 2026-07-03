# after-sales-qa-agent (P1)

Temu 售后测试提效 agent —— **接口/数据一致性校验层**。
针对三个页面（订单列表 / 订单详情 / 售后详情）在已登录的**测试账号**里抽取数据并跑确定性断言。

## 为什么是"浏览器抽取 + Python 校验"两层

Temu 三页背后是统一接口 `POST /api/poppy/v1/order?scene=...`，带 **anti-content 签名**保护，
Python/裸 fetch 直接调会被拒（`403 request illegal`）。而页面是 **SSR**，业务数据已渲染进
`window.rawData` / DOM —— 读它就等于拿到"接口返回"。因此：

| 层 | 位置 | 职责 |
| --- | --- | --- |
| 抽取层 | `extractor/extract.js`（浏览器会话内） | 导航→读 SSR 数据→归一化成 JSON（只含业务字段，无 URL/token） |
| 校验层 | `aftersales_qa/`（Python，本地） | 吃归一化 JSON→确定性断言→报告。**不触网、不烧 token** |

## 三页数据来源（已实测）

- 订单列表 `bgt_orders.html` → SSR 直出 **DOM** → `extractList()` 枚举订单号/状态
- 订单详情 `bgt_order_detail.html?parent_order_sn=<订单号>` → `window.rawData.store` → `extractOrderDetail()`
- 售后详情 `bgas_refund_detail.html?parent_after_sales_sn=<PO形式>` → `rawData.store.refundDetailData.refundDetailsVO` → `extractRefundDetail()`

**售后单号规则**：`parent_after_sales_sn`（驱动售后详情页）= 订单号 + `-D0x`（x=该 PO 第几次售后申请）。
售后票据号则是 `PA` + 订单号去 `PO` + `-D0x`（前缀 PO↔PA，数字段/后缀一致，校验器会顺带推导）。

## 校验项（P1）

- `refund.field_completeness` 退款方式/金额/明细字段完整
- `refund.amount_reconciliation` **金额勾稽**：Σ明细 = 实退 = 退款方式合计（硬指标）
- `refund.national_price_matches` 国币价 = 方式金额
- `refund.arn_format` ARN 纯数字、长度合理
- `refund.sn_rule` 售后单号符合 订单号+-D0x
- `order.status_known` / `list_vs_order.status` / `order_links_refund` 跨页状态一致 & 三页打通

### 越权/边界（boundary probe）

篡改 `parent_after_sales_sn`（不存在 / 越界后缀 / 畸形输入），断言页面 **fail-safe**：

- `boundary.no_data_leak` 非法单号不得泄露任何真实订单数据（越权风险）
- `boundary.no_unexpected_redirect` 不被静默重定向到其它订单
- `boundary.fail_safe_empty` 非法单号返回空

> 实测结论：三类非法输入均安全 fail-safe（空数据、不泄露、不崩溃、不串单）；
> 唯一 UX 瑕疵是空白页而非友好"未找到"提示。探针见 `extractor/extract.js` 的
> `extractBoundaryProbe()`；读取前需等页面加载 ~1s，否则会读到 bfcache 残留。

## 用法

```bash
# 自证：不连浏览器即可证明校验层正确（真实单全过 + 注入缺陷被抓）
python3 verify.py

# 对一个 case 目录跑校验并出报告
python3 run.py fixtures/golden --md report.md
```

`fixtures/golden/` 是你账号里真实的 $0.49 退款单（订单详情 + 售后详情），作为黄金基准。
`fixtures/broken/` 是把 Coupon 篡改为 `-$4.00` 的注入缺陷版，用于验证"校验器能抓错"。
`fixtures/live/` 是全量抽取的 10 个真实售后单；`fixtures/boundary/` 是 3 类越权/边界探针的真实观测。

`verify.py` 三重自证：真实单全过 · 抓到金额缺陷 · 抓到（模拟的）越权泄露。

## 目录

```
after-sales-qa-agent/
  extractor/extract.js        浏览器抽取层（三页归一化函数）
  aftersales_qa/
    money.py                  金额→整数分解析
    validators.py             确定性校验器
    report.py                 报告渲染
  fixtures/golden|broken/     真实基准 & 注入缺陷
  run.py                      case 目录 → 校验 → 报告
  verify.py                   离线自证脚本
```
