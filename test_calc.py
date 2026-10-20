#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实况抽卡概率计算 Promax 的单元测试（标准库 unittest，无第三方依赖）。

运行：
    python -m unittest -v test_calc.py
"""
import importlib.util
import math
import random
import sys
import unittest
from pathlib import Path

APP_FILE = Path(__file__).resolve().with_name("实况抽卡概率计算Promax.py")
if not APP_FILE.exists():  # 兼容改成 ASCII 文件名的情况
    APP_FILE = Path(__file__).resolve().with_name("efootball_calc.py")

_spec = importlib.util.spec_from_file_location("efootball_calc", APP_FILE)
_app = importlib.util.module_from_spec(_spec)
sys.modules["efootball_calc"] = _app
_spec.loader.exec_module(_app)

GUARANTEE_FIXED = _app.GUARANTEE_FIXED
GUARANTEE_NONE = _app.GUARANTEE_NONE
DrawModel = _app.DrawModel
binom_pmf = _app.binom_pmf
calculate = _app.calculate
convolve = _app.convolve


class TestBinom(unittest.TestCase):
    def test_sums_to_one(self):
        self.assertAlmostEqual(sum(binom_pmf(37, 0.13)), 1.0, places=12)

    def test_matches_comb(self):
        n, p = 6, 0.3
        for k in range(n + 1):
            expected = math.comb(n, k) * p ** k * (1 - p) ** (n - k)
            self.assertAlmostEqual(binom_pmf(n, p)[k], expected, places=12)

    def test_edges(self):
        self.assertEqual(binom_pmf(3, 0.0), [1.0, 0.0, 0.0, 0.0])
        self.assertEqual(binom_pmf(3, 1.0), [0.0, 0.0, 0.0, 1.0])

    def test_convolve(self):
        self.assertEqual(convolve([0.5, 0.5], [0.5, 0.5]), [0.25, 0.5, 0.25])


class TestModels(unittest.TestCase):
    RATE, A, B = 0.08, 10, 2
    TEN, SINGLE = 3, 5

    def model(self, mode):
        return DrawModel(self.RATE, self.A, self.B, mode)

    def test_distribution_sums_to_one(self):
        for mode in (GUARANTEE_NONE, GUARANTEE_FIXED):
            dist = self.model(mode).distribution(self.TEN, self.SINGLE)
            self.assertAlmostEqual(sum(dist), 1.0, places=10, msg=mode)

    def test_none_model_is_binomial(self):
        e = self.RATE * self.B / self.A
        dist = self.model(GUARANTEE_NONE).distribution(self.TEN, self.SINGLE)
        self.assertAlmostEqual(dist[0], (1 - e) ** (10 * self.TEN + self.SINGLE),
                               places=12)

    def test_fixed_last_p0(self):
        # 每个十连 = 9 次普通抽 + 第 10 抽必出 5星
        e = self.RATE * self.B / self.A
        q = self.B / self.A
        expected = ((1 - e) ** 9 * (1 - q)) ** self.TEN * (1 - e) ** self.SINGLE
        dist = self.model(GUARANTEE_FIXED).distribution(self.TEN, self.SINGLE)
        self.assertAlmostEqual(dist[0], expected, places=12)

    def test_fixed_last_p1_regression(self):
        """原版 bug：保底命中的两项用了 e2**9，应为 e2**(9c)。"""
        e = self.RATE * self.B / self.A
        q = self.B / self.A
        c, d = self.TEN, self.SINGLE
        e2 = 1 - e

        # 修正后的「恰好 1 张」：普通抽出 1 次 / 保底出 1 次 / 单抽券出 1 次
        expected = (
            math.comb(9 * c, 1) * e * e2 ** (9 * c - 1)
            * (1 - q) ** c * e2 ** d
            + c * q * (1 - q) ** (c - 1) * e2 ** (9 * c) * e2 ** d
            + e2 ** (9 * c) * (1 - q) ** c
            * math.comb(d, 1) * e * e2 ** (d - 1)
        )
        dist = self.model(GUARANTEE_FIXED).distribution(c, d)
        self.assertAlmostEqual(dist[1], expected, places=12)

        # 只把「保底命中」两项的指数换回原版错误的 e2**9（券仍按同一概率），
        # 结果会明显偏大——这就是原版那处 bug 的影响。
        buggy_exponent = (
            math.comb(9 * c, 1) * e * e2 ** (9 * c - 1)
            * (1 - q) ** c * e2 ** d
            + e2 ** 9 * (1 - q) ** (c - 1) * q * c * e2 ** d
            + e2 ** 9 * (1 - q) ** c * math.comb(d, 1) * e * e2 ** (d - 1)
        )
        self.assertGreater(buggy_exponent, dist[1] + 0.05)

    def test_expected_coins(self):
        self.assertAlmostEqual(self.model(GUARANTEE_NONE).expected_coins(),
                               100 / (self.RATE * self.B / self.A), places=6)


class TestValidation(unittest.TestCase):
    def test_bad_rate(self):
        for rate in (0, -0.1, 1.01):
            with self.assertRaises(ValueError):
                DrawModel(rate, 10, 2)

    def test_featured_too_large(self):
        with self.assertRaises(ValueError):
            DrawModel(0.1, 5, 6)

    def test_zero_five_count(self):
        with self.assertRaises(ValueError):
            DrawModel(0.1, 0, 0)

    def test_no_draws(self):
        with self.assertRaises(ValueError):
            DrawModel(0.1, 10, 2).distribution(0, 0)

    def test_negative_draws(self):
        with self.assertRaises(ValueError):
            DrawModel(0.1, 10, 2).distribution(-1, 0)


class TestMonteCarlo(unittest.TestCase):
    """用模拟器交叉验证两种模型（固定种子，结果可复现）。"""

    RATE, A, B, TEN, SINGLE = 0.08, 10, 2, 3, 5
    TRIALS = 120_000
    TOLERANCE = 0.007  # 0.7 个百分点

    def simulate_p0(self, mode):
        rng = random.Random(20261019)
        a0 = self.RATE
        e = a0 * self.B / self.A
        q = self.B / self.A
        none_hit = 0
        for _ in range(self.TRIALS):
            total = 0
            for _ in range(self.TEN):
                if mode == GUARANTEE_FIXED:
                    total += sum(1 for _ in range(9) if rng.random() < e)
                    total += rng.random() < q
                else:
                    total += sum(1 for _ in range(10) if rng.random() < e)
            total += sum(1 for _ in range(self.SINGLE) if rng.random() < e)
            none_hit += total == 0
        return none_hit / self.TRIALS

    def _check(self, mode):
        expected = calculate(DrawModel(self.RATE, self.A, self.B, mode),
                             self.TEN, self.SINGLE).p0 / 100
        self.assertAlmostEqual(self.simulate_p0(mode), expected,
                               delta=self.TOLERANCE, msg=mode)

    def test_none(self):
        self._check(GUARANTEE_NONE)

    def test_fixed(self):
        self._check(GUARANTEE_FIXED)


if __name__ == "__main__":
    unittest.main(verbosity=2)

