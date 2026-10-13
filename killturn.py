#!/usr/bin/env python3
"""キルターンと「封殺の完了」をはかる

決着 ＝ 勝つ、または封殺が完了する（相手に刺さる封殺が2種類そろう。刺さるのが1種類の相手ならその1種類）。

  1. 一人回し：何もしない相手（盾5枚・トリガーなし）に勝つターン
  2. 実戦：純粋な型の総当たりで、勝ったターン／封殺が完了したターン／どちらかが起きたターン、
           封殺を先に完了させた側の勝率
  3. ミスの影響：腕ごとの一人回しのキルターン

テンポ（両者が最初から持つマナ）を 0・1・2 と変えて、3〜4ターン目に決着する設定を探す。

  python killturn.py            全部
  python killturn.py 1          1 だけ
"""
import random
import sys
from collections import Counter

import engine
from cards import deck_difficulty
from engine import Game
from seeds import LOCK_SEED, PASSIVE, SEEDS

DECKS = dict(SEEDS)
DECKS["一手封殺（入れ替えで封殺を並べる）"] = LOCK_SEED


def pilot_err(k, d, skill):
    return min(0.9, k * d * (1 - skill)) if k else 0.0


def by(c, t):
    n = sum(c.values())
    return sum(k for x, k in c.items() if x <= t) / n if n else 0.0


def avg(c):
    won = [(t, k) for t, k in c.items() if t < 99]
    return sum(t * k for t, k in won) / max(1, sum(k for _, k in won))


def goldfish(deck, rng, err=0.0, n=2000):
    c = Counter()
    for i in range(n):
        g = Game(deck, PASSIVE, rng, first=i % 2, errs=(err, 0.0))
        c[g.round if g.play() == "A" else 99] += 1
    return c


def part1(rng):
    print("【1】一人回しのキルターン（平均｜3ターン目までに勝つ｜4ターン目までに勝つ）")
    for tempo in (0, 1, 2):
        engine.TEMPO = tempo
        print(f" テンポ{tempo}")
        for name, deck in DECKS.items():
            c = goldfish(deck, rng)
            print(f"  {name}｜{avg(c):.1f}｜{by(c, 3) * 100:.0f}%｜{by(c, 4) * 100:.0f}%")
    engine.TEMPO = 0


def duel_stats(decks, rng, n=300):
    """総当たり。勝ったターン、勝者の封殺完了ターン、決着（どちらか早いほう）、封殺を先に完了した側の勝率"""
    win, lock, dec = Counter(), Counter(), Counter()
    first_lock = first_lock_win = 0
    early = early_win = 0
    names = list(decks)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for g in range(n):
                gm = Game(decks[names[i]], decks[names[j]], rng, first=g % 2)
                r = gm.play()
                if r is None:
                    win[99] += 1
                    dec[99] += 1
                    continue
                lk = gm.stats["lock"]
                win[gm.round] += 1
                lock[lk.get(r, 99)] += 1
                dec[min(gm.round, lk.get(r, 99))] += 1
                if lk:
                    a, b = lk.get("A", 99), lk.get("B", 99)
                    if a != b:
                        who = "A" if a < b else "B"
                        first_lock += 1
                        first_lock_win += who == r
                        if min(a, b) <= 4:
                            early += 1
                            early_win += who == r
    return win, lock, dec, (first_lock_win / first_lock if first_lock else None), (early_win / early if early else None), early / max(1, sum(win.values()))


def part2(rng):
    print("\n【2】実戦（純粋な型＋一手封殺の総当たり・各組300戦）")
    print("テンポ｜勝ったターンの平均｜4ターン目までに勝ち｜4ターン目までに勝者の封殺が完了｜4ターン目までに決着（どちらか）"
          "｜3ターン目までに決着｜封殺を先に完了させた側の勝率（4ターン目までに完了させた場合）")
    for tempo in (0, 1, 2):
        engine.TEMPO = tempo
        win, lock, dec, flw, ew, es = duel_stats(DECKS, rng)
        print(f"  {tempo}｜{avg(win):.1f}｜{by(win, 4) * 100:.0f}%｜{by(lock, 4) * 100:.0f}%｜{by(dec, 4) * 100:.0f}%｜{by(dec, 3) * 100:.0f}%"
              f"｜{flw * 100:.0f}%（{ew * 100:.0f}%）")
    engine.TEMPO = 0


def part3(rng):
    print("\n【3】腕ごとの一人回しのキルターン（テンポ1・コンボ速い設定・難しさの係数2）")
    engine.TEMPO = 1
    engine.CHAIN_NEED, engine.LOOP_MANA = 3, 4
    for name in ("連鎖の特殊勝利", "呪文ループ", "入れ替え", "速さ（攻撃で割る）"):
        deck = DECKS[name]
        d = deck_difficulty(deck[0])
        cells = []
        for sk in (1.0, 0.5, 0.1):
            c = goldfish(deck, rng, pilot_err(2.0, d, sk))
            cells.append(f"腕{sk:.1f}：平均{avg(c):.1f}・4ターン目まで{by(c, 4) * 100:.0f}%")
        print(f"  {name}（難しさ{d:.2f}）｜" + "｜".join(cells))
    engine.TEMPO = 0
    engine.CHAIN_NEED, engine.LOOP_MANA = 4, 5


if __name__ == "__main__":
    rng = random.Random(5)
    which = sys.argv[1:] or ["1", "2", "3"]
    if "1" in which:
        part1(rng)
    if "2" in which:
        part2(rng)
    if "3" in which:
        part3(rng)
