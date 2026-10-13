#!/usr/bin/env python3
"""第3版：「最後まで進める」やり方を、探索の記録から学ぶ（全デッキ同じ手順）

  1. いまの進め方（最初は乱数）で探索しながら、全デッキの総当たりを打つ。
  2. 探索が選んだ手を数える：「このデッキで、この自分のターン数で、この手を打てた回数と、実際に選んだ回数」。
  3. 選んだ割合を重みにして、新しい進め方の表を作る。
  4. 1〜3をくり返す。進め方が良くなると探索の見立てが良くなり、次の記録も良くなる。

  人がデッキごとに作戦を書く代わりに、探索が見つけた打ち方を写し取る。どのデッキにも同じ手順を当てる。

  python learn3.py --iters 4 --games 6 --budget 300 --out policy3
"""
import argparse
import json
import random
import time
from multiprocessing import Pool

import ai3
from cards3 import DECKS

GAMMA = 1.5        # 重み＝（選んだ割合）のGAMMA乗
MINSEEN = 4        # これより少ない回数しか出てこなかった場面は、ターンを問わない集計で代える


def one(job):
    a, b, seed, first, budget, pol = job
    ai3.load_policy(pol if pol else {})
    rec = []
    g = ai3.play_game(DECKS[a], DECKS[b], random.Random(seed), first, (budget, budget), names=(a, b), record=rec)
    cnt = {}
    for name, t, offered, chosen in rec:
        d = cnt.setdefault(name, {})
        for x in set(offered):
            for key in (f"{t}|{x}", f"0|{x}"):
                v = d.get(key)
                if v is None:
                    v = d[key] = [0, 0]
                v[0] += 1
                if x == chosen:
                    v[1] += 1
    return a, b, g.winner, cnt


def build(counts):
    pol = {}
    for name, d in counts.items():
        tab = {}
        for key, (off, ch) in d.items():
            if off >= MINSEEN or key.startswith("0|"):
                tab[key] = round(((ch + 0.5) / (off + 1.5)) ** GAMMA, 4)
        pol[name] = tab
    return pol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=4)
    ap.add_argument("--games", type=int, default=6, help="デッキの組（順序つき49通り）ごとの対戦数")
    ap.add_argument("--budget", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--start", default=None, help="途中から続ける時の進め方ファイル")
    ap.add_argument("--first-iter", type=int, default=1)
    ap.add_argument("--out", default="policy3")
    x = ap.parse_args()
    names = list(DECKS)
    pol = json.load(open(x.start, encoding="utf-8")) if x.start else {}
    old = {}
    for it in range(x.first_iter, x.first_iter + x.iters):
        t0 = time.time()
        jobs = []
        for ia, a in enumerate(names):
            for ib, b in enumerate(names):
                for gno in range(x.games):
                    jobs.append((a, b, x.seed * 1000003 + it * 100003 + (ia * 7 + ib) * 101 + gno, gno % 2, x.budget, pol))
        with Pool(x.procs) as pool:
            res = pool.map(one, jobs, chunksize=2)
        counts = {}
        for name, d in old.items():                    # 前の回の記録は半分の重みで残す
            counts[name] = {k: [v[0] * 0.5, v[1] * 0.5] for k, v in d.items()}
        wins = {n: [0, 0] for n in names}
        for a, b, w, cnt in res:
            for i, n in enumerate((a, b)):
                wins[n][1] += 1
                wins[n][0] += 1 if w == i else (0.5 if w is None else 0)
            for name, d in cnt.items():
                c = counts.setdefault(name, {})
                for k, v in d.items():
                    u = c.get(k)
                    if u is None:
                        c[k] = [v[0], v[1]]
                    else:
                        u[0] += v[0]
                        u[1] += v[1]
        old = counts
        pol = build(counts)
        path = f"{x.out}_{it}.json"
        json.dump(pol, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"[{it}] {len(jobs)}戦 {time.time() - t0:.0f}秒 → {path}　勝率 "
              + " ".join(f"{n[:6]}{wins[n][0] / wins[n][1] * 100:.0f}" for n in names), flush=True)


if __name__ == "__main__":
    main()
