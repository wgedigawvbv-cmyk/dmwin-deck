#!/usr/bin/env python3
"""3つの要素を1つずつ切り離して確かめる

  1. 難しさ：ミスを入れると難しいデッキの勝率が下がるか。上手い人が使う（自己選択）と戻るか
  2. 封殺によるトリガー抑制：抑制を強めると、トリガーに頼る守りの価値が下がるか
  3. トリガーを抜く価値：抑制があるとき、トリガーを攻め札に替えたデッキは強くなるか
"""
import random
import sys

import engine
from cards import deck_difficulty
from engine import Game
from evolve3 import pilot_err
from seeds import SEEDS

N = 1500


def field_wr(name, cfg, seed=3):
    """純粋な型どうしの総当たりで、name の平均勝率"""
    rng = random.Random(seed)
    me = SEEDS[name]
    d_me = deck_difficulty(me[0])
    tot = 0.0
    others = [k for k in SEEDS if k != name]
    for o in others:
        opp = SEEDS[o]
        d_op = deck_difficulty(opp[0])
        w = 0.0
        for i in range(N):
            errs = (pilot_err(rng, d_me, cfg), pilot_err(rng, d_op, cfg))
            r = Game(me, opp, rng, first=i % 2, errs=errs).play()
            w += 1 if r == "A" else (0.5 if r is None else 0)
        tot += w / N
    return tot / len(others)


def match(a, b, seed=11, n=3000):
    rng = random.Random(seed)
    w = 0.0
    for i in range(n):
        r = Game(a, b, rng, first=i % 2).play()
        w += 1 if r == "A" else (0.5 if r is None else 0)
    return w / n


def part1():
    print("【1】難しさ（純粋な型6つの総当たり・各相手1500戦。コンボは速い設定）")
    print("デッキ｜難しさ｜ミスなし｜ミスあり（腕はばらばら）｜ミスあり（難しいデッキほど上手い人が使う）")
    none = {"difficulty": 0.0, "selfsel": False}
    rnd = {"difficulty": 0.6, "selfsel": False}
    sel = {"difficulty": 0.6, "selfsel": True}
    for name, (counts, _) in SEEDS.items():
        d = deck_difficulty(counts)
        a, b, c = field_wr(name, none), field_wr(name, rnd), field_wr(name, sel)
        print(f"  {name}｜{d:.2f}｜{a * 100:.1f}%｜{b * 100:.1f}%｜{c * 100:.1f}%")


LOCK_FREE = ({"m_free": 4, "m_spell": 4, "b1": 8, "b2": 8, "ramp": 6, "removal": 4, "sa2": 6}, 1)   # トリガー封じを持たない封殺
LOCK_ONE = ({"m_free": 4, "b1": 8, "b2": 8, "ramp": 8, "removal": 4, "sa2": 8}, 1)
GUARD = SEEDS["受け（トリガー）"]
SPEED = SEEDS["速さ（攻撃で割る）"]
# 速さに、トリガーを10枚足したもの／足さないもの（残りは同じ）
MID_T = ({"ramp": 8, "b1": 6, "b2": 6, "sa2": 6, "removal": 4, "t_stop": 3, "t_tap": 3, "t_remove": 4}, 1)
MID_0 = ({"ramp": 8, "b1": 8, "b2": 8, "sa2": 8, "sa3": 2, "removal": 6}, 1)


def part2():
    print("\n【2】封殺によるトリガー抑制（各3000戦）。左のデッキの勝率")
    print("抑制の強さ｜受け 対 封殺2種（踏み倒し封じ＋呪文制限）｜受け 対 封殺1種（踏み倒し封じ）｜受け 対 速さ（封殺なし）")
    for s in (0.0, 0.2, 0.4, 0.6, 0.8):
        engine.SUPPRESS = {k: s for k in engine.SUPPRESS}
        print(f"  {s:.1f}｜{match(GUARD, LOCK_FREE) * 100:.1f}%｜{match(GUARD, LOCK_ONE) * 100:.1f}%｜{match(GUARD, SPEED) * 100:.1f}%")


def part3():
    print("\n【3】トリガーを抜く価値（各3000戦）。「トリガー10枚入り」が「トリガー0枚（攻め札に替えた）」に勝つ割合と、")
    print("    それぞれが封殺1種・封殺2種に勝つ割合")
    print("抑制の強さ｜10枚入り 対 0枚｜10枚入り 対 封殺1種｜0枚 対 封殺1種｜10枚入り 対 封殺2種｜0枚 対 封殺2種")
    for s in (0.0, 0.4, 0.8):
        engine.SUPPRESS = {k: s for k in engine.SUPPRESS}
        print(f"  {s:.1f}｜{match(MID_T, MID_0) * 100:.1f}%｜{match(MID_T, LOCK_ONE) * 100:.1f}%｜{match(MID_0, LOCK_ONE) * 100:.1f}%"
              f"｜{match(MID_T, LOCK_FREE) * 100:.1f}%｜{match(MID_0, LOCK_FREE) * 100:.1f}%")
    engine.SUPPRESS = {k: 0.0 for k in engine.SUPPRESS}


if __name__ == "__main__":
    engine.CHAIN_NEED, engine.LOOP_MANA = 3, 4
    which = sys.argv[1:] or ["1", "2", "3"]
    if "1" in which:
        part1()
    if "2" in which:
        part2()
    if "3" in which:
        part3()
