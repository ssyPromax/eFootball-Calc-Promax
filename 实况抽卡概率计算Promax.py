#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实况抽卡概率计算（修复版）

单文件、仅依赖 Python 标准库，Python 3.9+。

相比原版：
- 计算层与界面层分离，概率模型可以单独跑单元测试（见 test_calc.py）
- 修正「保黑包」恰好出 1 张的指数错误
- 支持普通包和保黑包（第 10 抽必出 5星）两种规则
- 单抽券与金币抽使用同一概率（原版把券写死成 10%）
- 输入全部校验，不再输出负数概率或直接崩溃
- 结果统一为「0 / 1 / 2 / 3+ 张」，标签不再名不副实
- 支持高 DPI，窗口可拉伸，布局不再贴边
"""
from __future__ import annotations

import math
import sys
import webbrowser
from dataclasses import dataclass

COINS_PER_PULL = 100  # 一抽 100 金币；十连 1000 金币
MAX_TEN_PULLS = 200   # 防止输入过大导致界面卡死
MAX_SINGLES = 2000

AUTHOR = {
    "outlook": ("sss15006@outlook.com", "sss15006@outlook.com"),
    "qq": ("QQ: 3192491461", "3192491461"),
    "pingqiu": ("大众评球：mc方", "mc方"),
    "efootball": ("实况id：983736108", "983736108"),
    "github": ("Github：ssyPromax", "https://github.com/ssyPromax"),
    "bilibili": ("B站：证明及其限度", "https://space.bilibili.com/677960956"),
}

# ---------------------------------------------------------------- 概率模型
GUARANTEE_NONE = "普通包（无保底）"
GUARANTEE_FIXED = "保黑包：第 10 抽必出 5星"
GUARANTEE_MODES = (GUARANTEE_NONE, GUARANTEE_FIXED)


def binom_pmf(n: int, p: float) -> list[float]:
    """二项分布 P(X=k), k=0..n。用对数计算，避免大 n 时组合数上溢。"""
    if n < 0:
        raise ValueError("抽卡次数不能为负")
    if not 0.0 <= p <= 1.0:
        raise ValueError("概率必须在 0~1 之间")
    if n == 0:
        return [1.0]
    if p == 0.0:
        return [1.0] + [0.0] * n
    if p == 1.0:
        return [0.0] * n + [1.0]
    log_p, log_q = math.log(p), math.log1p(-p)
    lgamma_n = math.lgamma(n + 1)
    return [
        math.exp(lgamma_n - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                 + k * log_p + (n - k) * log_q)
        for k in range(n + 1)
    ]


def convolve(a: list[float], b: list[float]) -> list[float]:
    """两个「出货数量」分布相加。"""
    out = [0.0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0.0:
            continue
        for j, bj in enumerate(b):
            out[i + j] += ai * bj
    return out


@dataclass(frozen=True)
class DrawModel:
    """一次抽卡活动的概率模型。

    five_rate       单抽出 5星 的概率（0~1），即游戏里公示的概率
    five_count      卡池里 5星 球员总数 a
    featured_count  其中目标（高光/黄传/精选）数量 b
    guarantee       十连保底语义，见 GUARANTEE_MODES
    """

    five_rate: float
    five_count: int
    featured_count: int
    guarantee: str = GUARANTEE_NONE

    def __post_init__(self) -> None:
        if not 0.0 < self.five_rate <= 1.0:
            raise ValueError("5星 概率必须大于 0 且不超过 100%")
        if self.five_count < 1:
            raise ValueError("卡池 5星 球员数量至少为 1")
        if not 0 <= self.featured_count <= self.five_count:
            raise ValueError("目标球员数量必须在 0 到 5星 总数之间")
        if self.guarantee not in GUARANTEE_MODES:
            raise ValueError(f"未知保底方式：{self.guarantee}")

    @property
    def hit_rate(self) -> float:
        """单抽命中目标球员的概率 e = 5星 概率 × b/a。"""
        return self.five_rate * self.featured_count / self.five_count

    @property
    def featured_share(self) -> float:
        """一张 5星 恰好是目标球员的概率 q = b/a。"""
        return self.featured_count / self.five_count

    def pack_pmf(self) -> list[float]:
        """一次十连的出货数量分布（不含单抽券）。"""
        e = self.hit_rate
        q = self.featured_share

        if self.guarantee == GUARANTEE_NONE:
            return binom_pmf(10, e)

        # 保黑包：9 次普通抽 + 第 10 抽固定 5星（是否命中按 b/a 决定）
        out = [0.0] * 11
        for k, p in enumerate(binom_pmf(9, e)):
            out[k] += p * (1 - q)
            out[k + 1] += p * q
        return out

    def distribution(self, ten_pulls: int, singles: int) -> list[float]:
        """ten_pulls 个十连 + singles 张单抽券的出货数量分布。"""
        if ten_pulls < 0 or singles < 0:
            raise ValueError("抽卡次数不能为负")
        if ten_pulls == 0 and singles == 0:
            raise ValueError("至少要有一次抽卡")
        dist = [1.0]
        pack = self.pack_pmf()
        for _ in range(ten_pulls):
            dist = convolve(dist, pack)
        if singles:
            dist = convolve(dist, binom_pmf(singles, self.hit_rate))
        return dist

    def expected_coins(self) -> float | None:
        """平均出货金币（只算金币抽，单抽券不折算）。不可能出货时返回 None。"""
        e, q = self.hit_rate, self.featured_share
        if e <= 0.0:
            return None
        if self.guarantee == GUARANTEE_NONE:
            return COINS_PER_PULL / e
        # 保黑包：每个十连平均命中 9e + q
        return 10 * COINS_PER_PULL / (9 * e + q)


@dataclass(frozen=True)
class Result:
    p0: float           # 一张都不出
    p1: float           # 恰好 1 张
    p2: float           # 恰好 2 张
    p3: float           # 3 张及以上
    hit_rate: float     # 单抽命中率
    avg_coins: float | None


def calculate(model: DrawModel, ten_pulls: int, singles: int) -> Result:
    dist = model.distribution(ten_pulls, singles)
    p0 = dist[0]
    p1 = dist[1] if len(dist) > 1 else 0.0
    p2 = dist[2] if len(dist) > 2 else 0.0
    p3 = max(0.0, 1.0 - p0 - p1 - p2)
    return Result(p0 * 100, p1 * 100, p2 * 100, p3 * 100,
                  model.hit_rate, model.expected_coins())


# ---------------------------------------------------------------- 界面层
def enable_high_dpi() -> None:
    """让 Windows 高分屏下的界面不糊。必须在创建 Tk 之前调用。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def copy_to_clipboard(widget, text: str) -> None:
    widget.clipboard_clear()
    widget.clipboard_append(text)
    widget.update()


def main() -> None:
    import tkinter as tk
    from tkinter import ttk

    enable_high_dpi()
    root = tk.Tk()
    root.title("实况抽卡概率计算")
    root.minsize(430, 340)

    style = ttk.Style()
    try:
        style.configure("Result.TLabel", font=("Microsoft YaHei UI", 11))
    except Exception:
        pass

    inputs = {
        "rate": tk.StringVar(value="5"),
        "five": tk.StringVar(value="10"),
        "featured": tk.StringVar(value="2"),
        "ten": tk.StringVar(value="1"),
        "single": tk.StringVar(value="0"),
        "guarantee": tk.StringVar(value=GUARANTEE_NONE),
        "status": tk.StringVar(value=""),
    }

    frame_in = ttk.LabelFrame(root, text="卡池与抽卡", padding=10)
    frame_in.pack(fill="x", padx=12, pady=(12, 6))

    rows = [
        ("5星 单抽概率 (%)", "rate"),
        ("卡池 5星 球员数量", "five"),
        ("其中高光/黄传/精选数量", "featured"),
        ("金币十连次数", "ten"),
        ("单抽券张数", "single"),
    ]
    for r, (label, key) in enumerate(rows):
        ttk.Label(frame_in, text=label).grid(row=r, column=0, sticky="w", pady=3)
        entry = ttk.Entry(frame_in, textvariable=inputs[key], width=8,
                          justify="right")
        entry.grid(row=r, column=1, sticky="e", padx=(8, 0), pady=3)
        entry.bind("<KeyRelease>", lambda _e: recalc())

    ttk.Label(frame_in, text="保底方式").grid(row=0, column=2, sticky="w",
                                             padx=(24, 6))
    combo = ttk.Combobox(frame_in, textvariable=inputs["guarantee"],
                         values=GUARANTEE_MODES, state="readonly", width=26)
    combo.grid(row=1, column=2, rowspan=1, sticky="w", padx=(24, 0))
    combo.bind("<<ComboboxSelected>>", lambda _e: recalc())

    frame_out = ttk.LabelFrame(root, text="结果", padding=10)
    frame_out.pack(fill="both", expand=True, padx=12, pady=6)
    frame_out.columnconfigure(0, weight=1)

    result_vars = {
        "hit": tk.StringVar(value="-"),
        "p0": tk.StringVar(value="-"),
        "p1": tk.StringVar(value="-"),
        "p2": tk.StringVar(value="-"),
        "p3": tk.StringVar(value="-"),
        "coins": tk.StringVar(value="-"),
    }
    labels = [
        ("单抽命中率", "hit"),
        ("一张都不出", "p0"),
        ("恰好出 1 张", "p1"),
        ("恰好出 2 张", "p2"),
        ("出 3 张及以上", "p3"),
        ("平均出货金币（仅金币，约）", "coins"),
    ]
    for r, (label, key) in enumerate(labels):
        ttk.Label(frame_out, text=label).grid(row=r, column=0, sticky="w", pady=2)
        ttk.Label(frame_out, textvariable=result_vars[key],
                  style="Result.TLabel").grid(row=r, column=1, sticky="e", pady=2)

    ttk.Label(root, textvariable=inputs["status"], foreground="#b00020").pack(
        fill="x", padx=14)

    footer = ttk.Frame(root)
    footer.pack(fill="x", padx=12, pady=(0, 12))

    def open_author() -> None:
        win = tk.Toplevel(root)
        win.title("作者")
        win.transient(root)
        win.resizable(False, False)
        for r, (label, value) in enumerate(AUTHOR.values()):
            is_link = value.startswith("http")
            lab = tk.Label(win, text=label, fg="blue" if is_link else "black",
                           cursor="hand2" if is_link else "")
            lab.grid(row=r, column=0, sticky="w", padx=(16, 8), pady=6)
            if is_link:
                lab.bind("<Button-1>", lambda _e, u=value: webbrowser.open(u))
            ttk.Button(win, text="复制",
                       command=lambda v=value: copy_to_clipboard(win, v)).grid(
                row=r, column=1, padx=(8, 16), pady=6)

    def read_int(key: str, label: str) -> int:
        raw = inputs[key].get().strip()
        try:
            return int(raw)
        except ValueError:
            raise ValueError(f"{label}要填整数，当前是 {raw!r}") from None

    def recalc() -> None:
        try:
            rate_raw = inputs["rate"].get().strip()
            try:
                rate = float(rate_raw)
            except ValueError:
                raise ValueError(f"5星 概率要填数字，当前是 {rate_raw!r}") from None
            ten = read_int("ten", "十连次数")
            single = read_int("single", "单抽券张数")
            if not 0 <= ten <= MAX_TEN_PULLS:
                raise ValueError(f"十连次数需在 0~{MAX_TEN_PULLS} 之间")
            if not 0 <= single <= MAX_SINGLES:
                raise ValueError(f"单抽券张数需在 0~{MAX_SINGLES} 之间")
            model = DrawModel(
                rate / 100.0,
                read_int("five", "5星 球员数量"),
                read_int("featured", "目标球员数量"),
                inputs["guarantee"].get(),
            )
            result = calculate(model, ten, single)
        except ValueError as exc:
            inputs["status"].set(f"输入有误：{exc}")
            for key in ("hit", "p0", "p1", "p2", "p3", "coins"):
                result_vars[key].set("-")
            return

        result_vars["hit"].set(f"{result.hit_rate * 100:.2f}%")
        result_vars["p0"].set(f"{result.p0:.2f}%")
        result_vars["p1"].set(f"{result.p1:.2f}%")
        result_vars["p2"].set(f"{result.p2:.2f}%")
        result_vars["p3"].set(f"{result.p3:.2f}%")
        result_vars["coins"].set(
            "无法计算" if result.avg_coins is None
            else f"{result.avg_coins:,.0f} 金币")
        inputs["status"].set("")

    ttk.Button(footer, text="作者", command=open_author).pack(side="right")
    ttk.Button(footer, text="计算", command=recalc).pack(side="right", padx=8)

    root.bind("<Return>", lambda _e: recalc())
    recalc()
    root.mainloop()


if __name__ == "__main__":
    main()
