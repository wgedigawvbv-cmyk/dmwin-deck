#!/usr/bin/env python3
"""第3版：2つのデッキ（と探索の量）を戦わせる

  python duel3.py "4c der'Bande" "光自然ウィリデ" --games 40 --budget 400 400
  python duel3.py "創世竜ループ" "創世竜ループ" --games 40 --budget 400 100     同じデッキで探索の量だけ変える
"""
import argparse
import json
import random
import time
from multiprocessing import Pool

import ai3
from cards3 import DECKS


def one(job):
    a, b, seed, first, budgets, pol = job
    if pol:
        ai3.load_policy(pol)
    rng = random.Random(seed)
    g = ai3.play_game(DECKS[a], DECKS[b], rng, first, budgets, names=(a, b))
    return {"w": g.winner, "how": g.how, "turn": (g.turn + 1) // 2, "first": first, "trig": g.trig, "fa": g.fa, "chg": g.chg,
            "loopt": g.loopt, "hold": getattr(g, "hold", [0, 0])}


def run(a, b, games, budgets, seed=1, procs=2, pol=None):
    jobs = [(a, b, seed * 100003 + t, t % 2, tuple(budgets), pol) for t in range(games)]
    if procs <= 1:
        return [one(j) for j in jobs]
    with Pool(procs) as pool:
        return pool.map(one, jobs, chunksize=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--games", type=int, default=40)
    ap.add_argument("--budget", type=int, nargs=2, default=[400, 400])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--policy", default=None, help="学習した「進め方」のファイル（なければ乱数で進める）")
    ap.add_argument("--out", default=None)
    x = ap.parse_args()
    t0 = time.time()
    rs = run(x.a, x.b, x.games, x.budget, x.seed, x.procs, x.policy)
    n = len(rs)
    w = sum(r["w"] == 0 for r in rs) + 0.5 * sum(r["w"] is None for r in rs)
    wf = sum(r["w"] == r["first"] for r in rs)
    print(f"{x.a}（探索{x.budget[0]}） 対 {x.b}（探索{x.budget[1]}）：{n}戦 {w / n * 100:.0f}% ／先攻の勝ち {wf / n * 100:.0f}%"
          f"／平均{sum(r['turn'] for r in rs) / n:.1f}ターン／{time.time() - t0:.0f}秒")
    how = {}
    for r in rs:
        how[r["how"]] = how.get(r["how"], 0) + 1
    print("  決着：" + "、".join(f"{k}{v}" for k, v in sorted(how.items(), key=lambda kv: -kv[1])))
    if x.out:
        json.dump(rs, open(x.out, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
