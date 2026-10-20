/* 用 Python 版的结果交叉验证 web/app.js 的数学实现 */
"use strict";

const assert = require("assert");
const Calc = require("./app.js");
const refs = require("./reference.json");

let passed = 0;

for (const item of refs) {
  const [rate, five, featured, ten, single, mode] = item.args;
  const got = Calc.compute(rate, five, featured, ten, single, mode);
  for (const key of ["hitRate", "p0", "p1", "p2", "p3"]) {
    const diff = Math.abs(got[key] - item.result[key]);
    assert.ok(diff < 1e-9, `${mode} ${key}: got ${got[key]}, want ${item.result[key]}`);
  }
  if (item.result.avgCoins !== null) {
    const diff = Math.abs(got.avgCoins - item.result.avgCoins) / item.result.avgCoins;
    assert.ok(diff < 1e-9, `${mode} avgCoins: got ${got.avgCoins}, want ${item.result.avgCoins}`);
  }
  passed++;
}

/* 概率之和自洽 */
const dist = Calc.distribution(Calc.makeModel(0.08, 10, 2, Calc.GUARANTEE.FIXED), 3, 5);
const total = dist.reduce((a, b) => a + b, 0);
assert.ok(Math.abs(total - 1) < 1e-9, `distribution sums to ${total}`);

/* 输入校验 */
assert.throws(() => Calc.compute(8, 0, 2, 1, 0, "none"), /至少为 1/);
assert.throws(() => Calc.compute(8, 5, 6, 1, 0, "none"), /目标球员数量/);
assert.throws(() => Calc.compute(0, 10, 2, 1, 0, "none"), /5星概率/);

console.log(`OK: ${passed} 组结果与 Python 版一致，分布和为 ${total.toFixed(12)}`);

