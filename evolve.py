#!/usr/bin/env python3
"""デッキを進化させて、シミュレーターの中に「環境」を発生させる

- 集団：デッキ（カード構成＋攻撃方針）の集まり
- 1世代：各デッキが集団内のランダムな相手と対戦し、勝率を適応度とする
- 選択：上位はそのまま残し、残りは上位から親を選んで交叉・突然変異で作る
- 観測：各世代の「経路」「封殺」「守り」の持ち方、混合度、集中度を記録する

  python evolve.py --gens 150 --pop 40 --games 100 --seed 1 --out run1.json
"""
import argparse
import json
import random
import time
from collections import Counter

from cards import POOL, BY_KEY, CLOSURES, PATHS, deck_closures, deck_defense, deck_paths, max_copies
from engine import Game, play_match
from seeds import SEEDS

KEYS = [c.key for c in POOL if c.key != "filler"]


# ---------- 遺伝子の操作 ----------

def repair(counts, rng, prefer=None):
    counts = {k: min(v, max_copies(k)) for k, v in counts.items() if v > 0 and k != "filler"}
    while sum(counts.values()) > 40:
        k = rng.choice([k for k, v in counts.items() for _ in range(v)])
        counts[k] -= 1
        if counts[k] == 0:
            del counts[k]
    pool = prefer or KEYS
    while sum(counts.values()) < 40:
        k = rng.choice(pool)
        if counts.get(k, 0) < max_copies(k):
            counts[k] = counts.get(k, 0) + 1
        elif all(counts.get(x, 0) >= max_copies(x) for x in pool):
            pool = KEYS
    return counts


def mutate(genome, rng):
    counts, aggr = dict(genome[0]), genome[1]
    for _ in range(rng.choice((1, 1, 2, 2, 3, 4))):
        k = rng.choice([k for k, v in counts.items() for _ in range(v)])
        counts[k] -= 1
        if counts[k] == 0:
            del counts[k]
        add = rng.choice(KEYS)
        while counts.get(add, 0) >= max_copies(add):
            add = rng.choice(KEYS)
        counts[add] = counts.get(add, 0) + 1
    if rng.random() < 0.1:
        aggr = 1 - aggr
    return (repair(counts, rng), aggr)


def crossover(a, b, rng):
    keys = set(a[0]) | set(b[0])
    child = {}
    for k in keys:
        x, y = a[0].get(k, 0), b[0].get(k, 0)
        child[k] = rng.choice((x, y, (x + y) // 2, (x + y + 1) // 2))
    return (repair(child, rng, prefer=list(keys)), rng.choice((a[1], b[1])))


def random_deck(rng):
    return (repair({}, rng), rng.randint(0, 1))


# ---------- 観測 ----------

def describe(genome):
    counts = genome[0]
    paths = deck_paths(counts)
    clos = deck_closures(counts)
    d = deck_defense(counts)
    return {
        "paths": sorted(paths),
        "closures": sorted(clos),
        "hybrid": len(paths) + len(clos),
        "triggers": d["triggers"],
        "removal": d["removal"],
        "handes": d["handes"],
        "signature": "+".join(sorted(paths)) + "|" + "+".join(sorted(clos)),
    }


def population_stats(pop, fit):
    desc = [describe(g) for g in pop]
    n = len(pop)
    sig = Counter(x["signature"] for x in desc)
    hhi = sum((v / n) ** 2 for v in sig.values())
    top = sorted(range(n), key=lambda i: -fit[i])[: max(1, n // 4)]
    return {
        "fit_mean": sum(fit) / n,
        "fit_top": max(fit),
        "path_share": {p: sum(p in x["paths"] for x in desc) / n for p in PATHS},
        "closure_share": {c: sum(c in x["closures"] for x in desc) / n for c in CLOSURES},
        "hybrid_mean": sum(x["hybrid"] for x in desc) / n,
        "hybrid_top": sum(desc[i]["hybrid"] for i in top) / len(top),
        "triggers_mean": sum(x["triggers"] for x in desc) / n,
        "removal_mean": sum(x["removal"] for x in desc) / n,
        "handes_mean": sum(x["handes"] for x in desc) / n,
        "concentration": hhi,
        "aggr_share": sum(g[1] for g in pop) / n,
        "top_signatures": sig.most_common(5),
    }


def matchup_spread(decks, games, seed):
    """デッキ同士の総当たり相性と、50%からのずれの大きさ"""
    k = len(decks)
    m = [[0.5] * k for _ in range(k)]
    for i in range(k):
        for j in range(i + 1, k):
            w, _, _ = play_match(decks[i], decks[j], games, seed=seed + i * 31 + j)
            m[i][j], m[j][i] = w, 1 - w
    offs = [abs(m[i][j] - 0.5) for i in range(k) for j in range(k) if i < j]
    return m, (sum(offs) / len(offs) if offs else 0), (max(offs) if offs else 0)


# ---------- 進化 ----------

def evaluate(pop, games, rng):
    n = len(pop)
    wins = [0.0] * n
    played = [0] * n
    for i in range(n):
        for g in range(games):
            j = rng.randrange(n - 1)
            j = j + 1 if j >= i else j
            game = Game(pop[i], pop[j], rng, first=g % 2)
            r = game.play()
            if r == "A":
                wins[i] += 1
            elif r == "B":
                wins[j] += 1
            else:
                wins[i] += 0.5
                wins[j] += 0.5
            played[i] += 1
            played[j] += 1
    return [wins[i] / played[i] for i in range(n)]


def initial_population(n, rng, mode):
    pop = []
    seeds = list(SEEDS.values())
    if mode in ("seeds", "mixed"):
        while len(pop) < (n if mode == "seeds" else n // 2):
            base = seeds[len(pop) % len(seeds)]
            pop.append(base if len(pop) < len(seeds) else mutate(base, rng))
    while len(pop) < n:
        pop.append(random_deck(rng))
    return pop


def evolve(gens=150, pop_size=40, games=100, seed=1, init="seeds", elite_frac=0.25, log=print):
    rng = random.Random(seed)
    pop = initial_population(pop_size, rng, init)
    history = []
    t0 = time.time()
    for gen in range(gens):
        fit = evaluate(pop, games, rng)
        st = population_stats(pop, fit)
        st["gen"] = gen
        history.append(st)
        if gen % 10 == 0 or gen == gens - 1:
            ps = " ".join(f"{p}:{v * 100:.0f}" for p, v in st["path_share"].items())
            cs = " ".join(f"{c[2:]}:{v * 100:.0f}" for c, v in st["closure_share"].items())
            log(f"[{gen:3d}] 適応度 平均{st['fit_mean']:.2f}/最高{st['fit_top']:.2f}｜混合度 {st['hybrid_mean']:.1f}"
                f"（上位{st['hybrid_top']:.1f}）｜集中度 {st['concentration']:.2f}｜経路% {ps}｜封殺% {cs}"
                f"｜トリガー{st['triggers_mean']:.1f} 除去{st['removal_mean']:.1f} ({time.time() - t0:.0f}s)")
        order = sorted(range(pop_size), key=lambda i: -fit[i])
        elite_n = max(2, int(pop_size * elite_frac))
        elite = [pop[i] for i in order[:elite_n]]
        parents = [pop[i] for i in order[: pop_size // 2]]
        new = list(elite)
        while len(new) < pop_size:
            if rng.random() < 0.5:
                child = crossover(rng.choice(parents), rng.choice(parents), rng)
                if rng.random() < 0.5:
                    child = mutate(child, rng)
            else:
                child = mutate(rng.choice(parents), rng)
            new.append(child)
        pop = new
    final_fit = evaluate(pop, games, rng)
    return pop, final_fit, history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", type=int, default=150)
    ap.add_argument("--pop", type=int, default=40)
    ap.add_argument("--games", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--init", default="seeds", choices=["seeds", "random", "mixed"])
    ap.add_argument("--out", default="run.json")
    a = ap.parse_args()
    pop, fit, hist = evolve(a.gens, a.pop, a.games, a.seed, a.init)
    order = sorted(range(len(pop)), key=lambda i: -fit[i])
    final = [{"counts": pop[i][0], "aggr": pop[i][1], "fitness": fit[i], **describe(pop[i])} for i in order]
    json.dump({"args": vars(a), "history": hist, "final": final}, open(a.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"保存しました：{a.out}")


if __name__ == "__main__":
    main()
