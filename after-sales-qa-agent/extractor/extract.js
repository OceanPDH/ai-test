/*
 * Temu 售后数据抽取层 —— 在【已登录测试账号】的浏览器会话里运行。
 *
 * 为什么在浏览器里跑：Temu 统一接口 POST /api/poppy/v1/order?scene=... 有
 * anti-content 签名保护，Python/裸 fetch 会得到 {"error_code":403,"message":"request illegal"}。
 * 页面是 SSR，业务数据已渲染进 window.rawData / DOM，读它即可拿到"接口返回"的等价数据。
 *
 * 三页抽取（都返回归一化对象，只含业务字段，不含 URL/token/cookie）：
 *   extractList()          —— bgt_orders.html            （DOM 解析，含每单状态）
 *   extractOrderDetail()   —— bgt_order_detail.html       （读 rawData.store）
 *   extractRefundDetail()  —— bgas_refund_detail.html     （读 refundDetailsVO）
 *   extractBoundaryProbe() —— 篡改 SN 后的售后详情页       （越权/边界 fail-safe 判定）
 *
 * 用法：分别导航到对应页面后执行对应函数，把返回的 JSON 存成
 *   list.json / order_<orderSn>.json / refund_<parentAfterSalesSn>.json / boundary_<x>.json
 * 放进一个 case 目录，交给 `python run.py <case目录>` 校验。
 */

// 已知订单状态词（class 名是混淆的，会随构建变化，故用文案匹配而非 class）
const KNOWN_STATUSES = [
  'Refunded', 'Return/Refund', 'Returned', 'Processing',
  'Shipped', 'Delivered', 'Canceled', 'Cancelled', 'Unpaid',
];

// ── 订单列表页：DOM 解析，枚举订单号 + 每单状态 ──────────────────────────
// 订单号渲染为 <span>PO-...</span>；状态是卡片内某个文案恰为状态词的叶子元素。
// 从订单号 span 向上爬找卡片，在卡片子树内取状态叶子——顶部筛选 tab 不是订单号的
// 祖先，因此天然被排除。
function extractList() {
  const SN_RE = /^PO-\d{3}-\d{10,}$/;
  const isStatusLeaf = (el) =>
    KNOWN_STATUSES.includes((el.textContent || '').trim()) && el.querySelector('*') === null;
  // 统计子树内"不同"的订单号数量：同一卡片里订单号常渲染多个 span（显示+复制等），
  // 按 span 计数会误判越界，故按去重后的 SN 值计数。
  const distinctSnInSubtree = (root) =>
    new Set(
      [...root.querySelectorAll('span')]
        .map((s) => (s.textContent || '').trim())
        .filter((t) => SN_RE.test(t))
    ).size;

  const snSpans = [...document.querySelectorAll('span')].filter((e) =>
    SN_RE.test((e.textContent || '').trim())
  );
  const seen = new Set();
  const out = [];
  for (const span of snSpans) {
    const sn = span.textContent.trim();
    if (seen.has(sn)) continue;         // 每单的订单号可能渲染多次，去重
    seen.add(sn);
    let card = span;
    let status = null;
    for (let i = 0; i < 10 && card; i++) {
      card = card.parentElement;
      if (!card) break;
      // 越过单卡边界（祖先含 >1 个不同订单号）就停：宁可 status=null 也不串到邻单
      if (distinctSnInSubtree(card) > 1) break;
      const hit = [...card.querySelectorAll('*')].find(isStatusLeaf);
      if (hit) { status = hit.textContent.trim(); break; }
    }
    out.push({ orderSn: sn, status });
  }
  // 回退：若精确 span 匹配一无所获（DOM 结构变了），退回 body 文本枚举订单号
  if (out.length === 0) {
    const ids = [...new Set(
      [...(document.body.innerText || '').matchAll(/PO-\d{3}-\d{10,}/g)].map((m) => m[0])
    )];
    return ids.map((sn) => ({ orderSn: sn, status: null }));
  }
  return out;
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

// ── 越权/边界探针：导航到篡改后的售后详情 URL 后运行，判断是否 fail-safe ──
// 注意：读取前应等待页面加载完成（约 1s），否则可能读到 bfcache/上一页残留。
function extractBoundaryProbe(requestedSn, category) {
  const st = (window.rawData && window.rawData.store) || {};
  const rdd = st.refundDetailData;
  const s = JSON.stringify(rdd || {});
  const sn = requestedSn || '';
  const inUrl = sn !== '' &&
    (location.search.includes(sn) || location.search.includes(encodeURIComponent(sn)));
  return {
    page: 'boundary_probe',
    requestedSn: requestedSn || null,
    category: category || null,             // nonexistent | out_of_range_suffix | malformed
    hasVO: !!(rdd && rdd.refundDetailsVO),   // 非法单号应为 false
    leaksRealSn: /PO-211-\d{10,}/.test(s),   // 不应出现任何真实单号
    redirected: sn !== '' && !inUrl,         // 请求的 SN 不在最终 URL 里 = 被重定向
  };
}

// 便于在 MCP javascript_tool 里取用（Node 环境下也可 require）
if (typeof module !== 'undefined') {
  module.exports = { extractList, extractOrderDetail, extractRefundDetail, extractBoundaryProbe };
}
