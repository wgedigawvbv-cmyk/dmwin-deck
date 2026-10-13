#!/usr/bin/env python3
"""第3版：実在の7デッキから出発して、デッキを進化させる（型の境界は保たれるか）

  ・集団は、実在の7リストとその小変更から始める。
  ・成績＝実在の7リストとの対戦の勝率（どのリストとも同じ数だけ戦う）。操縦は全員同じ先読み。
  ・上位はそのまま残り、残りは上位を手本にした交叉（別のデッキとの混ぜ合わせ）と変異（カードの入れ替え）で作る。
  ・観測：成績の上位が、出発点のリストとどれくらい同じカードでできているか（一致率）。
    型をまたいだ混ぜ合わせが勝つなら一致率が下がり、型の中の調整しか勝てないなら高いまま残る。

  python evolve7.py --gens 10 --pop 21 --games 4 --budget 100 --policy runs7/policy3_5.json --out runs7/evo_s1.json
"""
import argparse
import json
import random
import time
from multiprocessing import Pool

import ai3
from cards3 import BY_KEY, DECKS, POOL
from playable3 import dead, dead_copies

MAXCOPY = {"shunsen": 1, "magnum": 1, "saitan": 1, "gio": 1}      # 大会当時の殿堂入り（1枚制限）
KEYS = [c.key for c in POOL]
NAMES = list(DECKS)


PLAYABLE = True       # True：そのデッキでは出せないカード（色が足りない・チェンジ元がいない等）を残さない


def cap(k):
    return MAXCOPY.get(k, 4)


def fix(d, rng):
    """出せないカードを、出せるカードに入れ替える（出せない枚数が減る入れ替えだけを受け入れる）"""
    d = dict(d)
    for _ in range(400):
        dd = dead(d)
        if not dd:
            return d
        k = rng.choice(sorted(dd))
        a = rng.choice(KEYS)
        if a == k or d.get(a, 0) >= cap(a):
            continue
        e = dict(d)
        e[k] -= 1
        if not e[k]:
            del e[k]
        e[a] = e.get(a, 0) + 1
        if dead_copies(e) < dead_copies(d):
            d = e
    return d


def repair(d, rng, prefer=None):
    d = {k: min(v, cap(k)) for k, v in d.items() if v > 0}
    while sum(d.values()) > 40:
        k = rng.choice([k for k in sorted(d) for _ in range(d[k])])
        d[k] -= 1
        if not d[k]:
            del d[k]
    pool = prefer or KEYS
    while sum(d.values()) < 40:
        k = rng.choice(pool)
        if d.get(k, 0) < cap(k):
            d[k] = d.get(k, 0) + 1
        elif all(d.get(x, 0) >= cap(x) for x in pool):
            pool = KEYS
    return fix(d, rng) if PLAYABLE else d


def mutate(d, rng):
    d = dict(d)
    for _ in range(rng.choice((1, 1, 2, 2, 3, 4))):
        k = rng.choice([k for k in sorted(d) for _ in range(d[k])])
        d[k] -= 1
        if not d[k]:
            del d[k]
        a = rng.choice(KEYS)
        while d.get(a, 0) >= cap(a):
            a = rng.choice(KEYS)
        d[a] = d.get(a, 0) + 1
    return repair(d, rng)


def crossover(a, b, rng):
    keys = sorted(set(a) | set(b))
    c = {}
    for k in keys:
        x, y = a.get(k, 0), b.get(k, 0)
        c[k] = rng.choice((x, y, (x + y) // 2, (x + y + 1) // 2))
    return repair(c, rng, prefer=keys)


def overlap(d, e):
    return sum(min(v, e.get(k, 0)) for k, v in d.items()) / 40


def nearest(d):
    best = max(NAMES, key=lambda n: overlap(d, DECKS[n]))
    return best, overlap(d, DECKS[best])


def one(job):
    idx, deck, opp, seed, first, budget, pol = job
    g = ai3.play_game(deck, DECKS[opp], random.Random(seed), first, (budget, budget), names=("*", "*"), pols=(pol, pol))
    return idx, opp, (1.0 if g.winner == 0 else 0.5 if g.winner is None else 0.0)


def global_policy(pol):
    """デッキごとの進め方を1つにまとめる（どのリストにも同じ表を使うため）"""
    acc = {}
    for tab in pol.values():
        for k, w in tab.items():
            acc.setdefault(k, []).append(w)
    return {"*": {k: sum(v) / len(v) for k, v in acc.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", type=int, default=10)
    ap.add_argument("--pop", type=int, default=21)
    ap.add_argument("--games", type=int, default=4, help="実在のリスト1つあたりの対戦数（1世代）")
    ap.add_argument("--budget", type=int, default=100)
    ap.add_argument("--policy", default=None)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--out", default="evo7.json")
    ap.add_argument("--no-playable", action="store_true", help="出せないカードを残したままにする（前回までの条件）")
    x = ap.parse_args()
    global PLAYABLE
    PLAYABLE = not x.no_playable
    rng = random.Random(x.seed)
    pol = global_policy(json.load(open(x.policy, encoding="utf-8"))) if x.policy else {}
    pop = [dict(DECKS[n]) for n in NAMES]
    while len(pop) < x.pop:
        pop.append(mutate(DECKS[NAMES[len(pop) % 7]], rng))
    score = [[0.0, 0] for _ in pop]            # これまでの通算（生き残った個体は持ち越す）
    hist = []
    t0 = time.time()
    with Pool(x.procs) as pool:
        for gen in range(x.gens):
            jobs = []
            for i, d in enumerate(pop):
                for o in NAMES:
                    for g in range(x.games):
                        jobs.append((i, d, o, rng.getrandbits(40), g % 2, x.budget, pol))
            for i, o, s in pool.imap_unordered(one, jobs, chunksize=4):
                score[i][0] += s
                score[i][1] += 1
            fit = [s[0] / s[1] for s in score]
            order = sorted(range(len(pop)), key=lambda i: -fit[i])
            top = order[:max(1, len(pop) // 3)]
            near = [nearest(pop[i]) for i in range(len(pop))]
            st = {"gen": gen, "best": fit[order[0]], "mean": sum(fit) / len(fit),
                  "top_overlap": sum(near[i][1] for i in top) / len(top),
                  "top_dead": sum(dead_copies(pop[i]) for i in top) / len(top),
                  "all_overlap": sum(n[1] for n in near) / len(near),
                  "top_types": sorted({near[i][0] for i in top}),
                  "top": [(near[i][0], round(near[i][1], 3), round(fit[i], 3), score[i][1]) for i in top]}
            hist.append(st)
            print(f"[{gen}] 最高{st['best'] * 100:.0f}% 平均{st['mean'] * 100:.0f}% 上位の一致率{st['top_overlap'] * 100:.0f}%"
                  f" 上位の型{len(st['top_types'])}種 出せない札{st['top_dead']:.1f}枚 ({time.time() - t0:.0f}s)", flush=True)
            if gen == x.gens - 1:
                break
            new, nscore = [], []
            for i in top:
                new.append(pop[i])
                nscore.append(score[i])
            w = [max(0.01, fit[i] - 0.3) for i in range(len(pop))]
            while len(new) < len(pop):
                r = rng.random()
                if r < 0.4:
                    a, b = rng.choices(range(len(pop)), w, k=2)
                    c = crossover(pop[a], pop[b], rng)
                    if rng.random() < 0.3:
                        c = mutate(c, rng)
                else:
                    c = mutate(pop[rng.choices(range(len(pop)), w, k=1)[0]], rng)
                new.append(c)
                nscore.append([0.0, 0])
            pop, score = new, nscore
    fit = [s[0] / s[1] for s in score]
    order = sorted(range(len(pop)), key=lambda i: -fit[i])
    final = []
    for i in order:
        n, ov = nearest(pop[i])
        base = DECKS[n]
        add = {k: v - base.get(k, 0) for k, v in pop[i].items() if v > base.get(k, 0)}
        cut = {k: v - pop[i].get(k, 0) for k, v in base.items() if v > pop[i].get(k, 0)}
        final.append({"deck": pop[i], "fit": fit[i], "n": score[i][1], "near": n, "overlap": ov,
                      "dead": dead_copies(pop[i]),
                      "add": {BY_KEY[k].name: v for k, v in add.items()}, "cut": {BY_KEY[k].name: v for k, v in cut.items()}})
    json.dump({"args": vars(x), "history": hist, "final": final}, open(x.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"保存しました：{x.out}")


if __name__ == "__main__":
    main()
