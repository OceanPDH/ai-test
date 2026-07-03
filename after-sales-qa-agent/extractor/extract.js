/*
 * Temu 售后数据抽取层 —— 在【已登录测试账号】的浏览器会话里运行。
 *
 * 为什么在浏览器里跑：Temu 统一接口 POST /api/poppy/v1/order?scene=... 有
 * anti-content 签名保护，Python/裸 fetch 会得到 {"error_code":403,"message":"request illegal"}。
 * 页面是 SSR，业务数据已渲染进 window.rawData / DOM，读它即可拿到"接口返回"的等价数据。
 *
 * 三页抽取（都返回归一化对象，只含业务字段，不含 URL/token/cookie）：
 *   extractList()          —— bgt_orders.html            （DOM 解析）
 *   extractOrderDetail()   —— bgt_order_detail.html       （读 rawData.store）
 *   extractRefundDetail(sn)—— bgas_refund_detail.html     （读 refundDetailsVO）
 *
 * 用法：分别导航到对应页面后执行对应函数，把返回的 JSON 存成
 *   list.json / order_<orderSn>.json / refund_<parentAfterSalesSn>.json
 * 放进一个 case 目录，交给 `python run.py <case目录>` 校验。
 */

// ── 订单列表页：DOM 解析，主要用于枚举订单号 + 状态 ───────────────────────
function extractList() {
  const text = document.body.innerText;
  const ids = [...new Set([...text.matchAll(/PO-\d{3}-\d{10,}/g)].map((m) => m[0]))];
  // 状态与订单卡片一一对应较脆弱，这里只取订单号集合 + 粗粒度状态清单
  const statuses = [...new Set(
    [...text.matchAll(/\b(Refunded|Processing|Shipped|Delivered|Returned|Canceled|Unpaid)\b/g)]
      .map((m) => m[1])
  )];
  return ids.map((sn) => ({ orderSn: sn, status: null, _statusesSeen: statuses }));
}

// ── 订单详情页：读 rawData.store，取状态 + 关联的售后单号 ──────────────────
function extractOrderDetail() {
  const st = window.rawData.store;
  const findList = (root, key) => {
    let hit = null; const seen = new Set();
    (function w(o) {
      if (hit || o == null || typeof o !== 'object' || seen.has(o)) return;
      seen.add(o);
      for (const k of Object.keys(o)) {
        if (k === key && Array.isArray(o[k])) { hit = o[k]; return; }
        if (o[k] && typeof o[k] === 'object') w(o[k]);
      }
    })(root);
    return hit || [];
  };
  const afterSales = findList(st, 'afterSalesInfoList').map((it) => {
    const ju = String(it.jumpUrl || '');
    const sn = (ju.match(/(P[AO]-\d{3}-\d{6,}-D\d{2})/) || [])[1] || null;
    return { statusPrompt: it.statusPrompt || null, parentAfterSalesSn: sn };
  });
  return {
    page: 'order_detail',
    orderSn: st.orderSn || null,
    orderStatus: st.orderStatus ?? null,
    parentStatus: st.parentStatus ?? null,
    afterSales,
  };
}

// ── 售后详情页：读 refundDetailsVO，取退款方式/金额/明细 ──────────────────
function extractRefundDetail(parentAfterSalesSn) {
  const vo = window.rawData.store.refundDetailData.refundDetailsVO;
  const methods = [];
  (vo.refundMethodAndAmountList || []).forEach((m) =>
    (m.refundMethodAndAmountItemList || []).forEach((it) =>
      (it.baseRefundMethodAndAmountList || []).forEach((b) =>
        methods.push({
          refundMethod: b.refundMethod || null,
          refundMethodType: b.refundMethodType ?? null,
          arn: b.arn || null,
          refundMethodAmount: b.refundMethodAmount ?? null,
          refundAmountNationalPrice: b.refundAmountNationalPrice
            ? {
                price: b.refundAmountNationalPrice.price,
                cur: b.refundAmountNationalPrice.cur,
                priceStr: b.refundAmountNationalPrice.priceStr,
              }
            : null,
        })
      )
    )
  );
  const amountBreakdown = [];
  (vo.subRefundDetailItemVOGroupList || []).forEach((grp) =>
    (grp || []).forEach((row) => {
      if (row && (row.keyStr || row.valueStr)) {
        amountBreakdown.push({ key: row.keyStr || null, value: row.valueStr || null, typeCode: row.typeCode ?? null });
      }
    })
  );
  return {
    page: 'refund_detail',
    parentAfterSalesSn: parentAfterSalesSn || null,
    refundMethodNote: vo.refundMethodNote || null,
    isEstimate: !!vo.isEstimate,
    totalReturnCreditAmount: vo.totalReturnCreditAmount ?? null,
    methods,
    amountBreakdown,
  };
}

// 便于在 MCP javascript_tool 里取用（Node 环境下也可 require）
if (typeof module !== 'undefined') {
  module.exports = { extractList, extractOrderDetail, extractRefundDetail };
}
