/* 实况抽卡概率计算 —— 界面逻辑 */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };

  var mode = Calc.GUARANTEE.NONE;
  var ids = ["rate", "five", "featured", "ten", "single"];

  function readInt(id, label) {
    var raw = ($(id).value || "").trim();
    if (!/^-?\d+$/.test(raw)) throw new Error(label + "要填整数");
    return parseInt(raw, 10);
  }

  function fmtPct(v) {
    return (Math.abs(v) < 0.005 ? 0 : v).toFixed(2) + "%";
  }

  function fmtCoins(v) {
    if (v === null || !isFinite(v)) return "无法计算";
    return Math.round(v).toLocaleString("zh-CN") + " 金币";
  }

  function setError(msg) {
    $("error").textContent = msg || "";
    $("error").classList.toggle("show", !!msg);
  }

  function clearResults() {
    ["hit", "p0", "p1", "p2", "p3", "coins"].forEach(function (id) {
      $(id).textContent = "-";
    });
    $("bar0").style.width = $("bar1").style.width = "0%";
    $("bar2").style.width = $("bar3").style.width = "0%";
  }

  function recalc() {
    try {
      var rateRaw = ($("rate").value || "").trim();
      if (rateRaw === "" || isNaN(parseFloat(rateRaw))) throw new Error("5星概率要填数字");
      var rate = parseFloat(rateRaw);

      var five = readInt("five", "5星球员数量");
      var featured = readInt("featured", "目标球员数量");
      var ten = readInt("ten", "十连次数");
      var single = readInt("single", "单抽券张数");

      if (ten < 0 || ten > 200) throw new Error("十连次数需在 0~200 之间");
      if (single < 0 || single > 2000) throw new Error("单抽券张数需在 0~2000 之间");

      var r = Calc.compute(rate, five, featured, ten, single, mode);

      $("hit").textContent = fmtPct(r.hitRate);
      $("p0").textContent = fmtPct(r.p0);
      $("p1").textContent = fmtPct(r.p1);
      $("p2").textContent = fmtPct(r.p2);
      $("p3").textContent = fmtPct(r.p3);
      $("coins").textContent = fmtCoins(r.avgCoins);

      $("bar0").style.width = r.p0 + "%";
      $("bar1").style.width = r.p1 + "%";
      $("bar2").style.width = r.p2 + "%";
      $("bar3").style.width = r.p3 + "%";

      setError("");
    } catch (err) {
      clearResults();
      setError("输入有误：" + err.message);
    }
  }

  function setMode(next) {
    mode = next;
    var buttons = document.querySelectorAll("#guarantee button");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].classList.toggle("on", buttons[i].getAttribute("data-mode") === next);
    }
    recalc();
  }

  function init() {
    ids.forEach(function (id) {
      $(id).addEventListener("input", recalc);
      $(id).addEventListener("change", recalc);
    });
    $("guarantee").addEventListener("click", function (e) {
      var btn = e.target.closest("button");
      if (btn) setMode(btn.getAttribute("data-mode"));
    });
    recalc();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

