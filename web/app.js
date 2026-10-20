/* 实况抽卡概率计算 —— 共享计算逻辑（浏览器 / Node 通用） */
(function (root, factory) {
  var api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Calc = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var COINS_PER_PULL = 100;
  var GUARANTEE = {
    NONE: "none",
    FIXED: "fixed"
  };

  /* ---------- 基础分布 ---------- */
  var logFact = [0, 0];

  function ensureLogFact(n) {
    for (var i = logFact.length; i <= n; i++) {
      logFact[i] = logFact[i - 1] + Math.log(i);
    }
  }

  function binomPmf(n, p) {
    if (n < 0) throw new Error("抽卡次数不能为负");
    if (!(p >= 0 && p <= 1)) throw new Error("概率必须在 0~1 之间");
    var out = new Array(n + 1).fill(0);
    if (n === 0) { out[0] = 1; return out; }
    if (p === 0) { out[0] = 1; return out; }
    if (p === 1) { out[n] = 1; return out; }
    ensureLogFact(n);
    var lp = Math.log(p), lq = Math.log1p(-p);
    for (var k = 0; k <= n; k++) {
      out[k] = Math.exp(
        logFact[n] - logFact[k] - logFact[n - k] + k * lp + (n - k) * lq
      );
    }
    return out;
  }

  function convolve(a, b) {
    var out = new Array(a.length + b.length - 1).fill(0);
    for (var i = 0; i < a.length; i++) {
      if (a[i] === 0) continue;
      for (var j = 0; j < b.length; j++) out[i + j] += a[i] * b[j];
    }
    return out;
  }

  /* ---------- 模型 ---------- */
  function makeModel(ratePct, five, featured, guarantee) {
    var rate = ratePct / 100;
    if (!(rate > 0 && rate <= 1)) throw new Error("5星概率必须大于 0 且不超过 100%");
    if (!(five >= 1)) throw new Error("卡池 5星球员数量至少为 1");
    if (!(featured >= 0 && featured <= five)) {
      throw new Error("目标球员数量必须在 0 到 5星总数之间");
    }
    if ([GUARANTEE.NONE, GUARANTEE.FIXED].indexOf(guarantee) < 0) {
      throw new Error("未知保底方式");
    }
    return {
      rate: rate,
      five: five,
      featured: featured,
      guarantee: guarantee,
      hitRate: rate * featured / five,
      share: featured / five
    };
  }

  function packPmf(m) {
    var e = m.hitRate, q = m.share;
    if (m.guarantee === GUARANTEE.NONE) return binomPmf(10, e);

    // 保黑包：9 次普通抽 + 第 10 抽固定 5星
    var base = binomPmf(9, e);
    var out = new Array(11).fill(0);
    for (var k = 0; k < base.length; k++) {
      out[k] += base[k] * (1 - q);
      out[k + 1] += base[k] * q;
    }
    return out;
  }

  function distribution(m, tenPulls, singles) {
    if (tenPulls < 0 || singles < 0) throw new Error("抽卡次数不能为负");
    if (tenPulls === 0 && singles === 0) throw new Error("至少要有一次抽卡");
    var dist = [1];
    var pack = packPmf(m);
    for (var i = 0; i < tenPulls; i++) dist = convolve(dist, pack);
    if (singles > 0) dist = convolve(dist, binomPmf(singles, m.hitRate));
    return dist;
  }

  function expectedCoins(m) {
    var e = m.hitRate, q = m.share;
    if (e <= 0) return null;
    if (m.guarantee === GUARANTEE.NONE) return COINS_PER_PULL / e;
    return 10 * COINS_PER_PULL / (9 * e + q);
  }

  function compute(ratePct, five, featured, tenPulls, singles, guarantee) {
    var m = makeModel(ratePct, five, featured, guarantee);
    var dist = distribution(m, tenPulls, singles);
    var p0 = dist[0] || 0;
    var p1 = dist[1] || 0;
    var p2 = dist[2] || 0;
    var p3 = Math.max(0, 1 - p0 - p1 - p2);
    return {
      hitRate: m.hitRate * 100,
      p0: p0 * 100,
      p1: p1 * 100,
      p2: p2 * 100,
      p3: p3 * 100,
      avgCoins: expectedCoins(m)
    };
  }

  return {
    COINS_PER_PULL: COINS_PER_PULL,
    GUARANTEE: GUARANTEE,
    binomPmf: binomPmf,
    convolve: convolve,
    makeModel: makeModel,
    packPmf: packPmf,
    distribution: distribution,
    expectedCoins: expectedCoins,
    compute: compute
  };
});
