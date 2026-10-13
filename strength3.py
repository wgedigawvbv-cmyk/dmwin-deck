#!/usr/bin/env python3
"""第3版：操縦の強さを確かめる（同じデッキどうしで、操縦だけを変えて戦わせる）

  A. 学習済みの進め方を使う探索 対 乱数で進める探索（探索回数は同じ）
     → どのデッキでも学習済みが勝ち越すなら、学習は全デッキの操縦を底上げしている。
  B. 探索回数を2倍にした側 対 元の側（どちらも学習済み）
     → 2倍にしても50%に近いままなら、その回数でこの方法の強さは頭打ち。

  python strength3.py --policy runs7/policy3_5.json --games 30 --mode A --budget 300
  python strength3.py --policy runs7/policy3_5.json --games 30 --mode B --budget 300
"""
import argparse
import json
import random
import time
from multiprocessing import Pool

import ai3
from cards3 import DECKS
from matrix3 import SHORT


def one(job):
    name, seed, first, budgets, p0, p1 = job
    g = ai3.play_game(DECKS[name], DECKS[name], random.Random(seed), first, budgets, names=(name, name), pols=(p0, p1))
    return name, g.winner


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--base", default=None, help="比べる相手の進め方ファイル（省くと乱数）")
    ap.add_argument("--games", type=int, default=30)
    ap.add_argument("--budget", type=int, default=300)
    ap.add_argument("--mode", choices=("A", "B"), default="A")
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--decks", nargs="*", default=None)
    x = ap.parse_args()
    pol = json.load(open(x.policy, encoding="utf-8"))
    base = json.load(open(x.base, encoding="utf-8")) if x.base else {}
    names = x.decks or list(DECKS)
    jobs = []
    for i, n in enumerate(names):
        for g in range(x.games):
            seed = x.seed * 100003 + i * 1009 + g
            if x.mode == "A":
                jobs.append((n, seed, g % 2, (x.budget, x.budget), pol, base))
            else:
                jobs.append((n, seed, g % 2, (x.budget * 2, x.budget), pol, pol))
    t0 = time.time()
    with Pool(x.procs) as pool:
        rs = pool.map(one, jobs, chunksize=1)
    if x.mode == "A":
        print(f"【A】学習済みの進め方 対 {'乱数' if not x.base else x.base}（どちらも探索{x.budget}回）：学習済み側の勝率")
    else:
        print(f"【B】探索{x.budget * 2}回 対 探索{x.budget}回（どちらも学習済み）：回数が多い側の勝率")
    tot = 0
    for n in names:
        w = sum((1 if r[1] == 0 else 0.5 if r[1] is None else 0) for r in rs if r[0] == n)
        tot += w
        print(f"  {SHORT[n]}｜{w / x.games * 100:.0f}%（{x.games}戦）")
    print(f"  全体｜{tot / len(rs) * 100:.0f}%（{len(rs)}戦）　{time.time() - t0:.0f}秒")


if __name__ == "__main__":
    main()
