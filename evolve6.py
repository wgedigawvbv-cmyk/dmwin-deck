#!/usr/bin/env python3
"""第2版のカードプールで、デッキを進化させる

  集団は12種類のデッキタイプから始まる。各デッキは（カード構成, 性質）を持つ。性質＝毎ターン動く(1)／待つ(0)。
  1世代：集団の中どうし（6割）と環境外のデッキ（4割：出発点の12種類・でたらめなデッキ・少し前の上位）と対戦して成績を出す。
  選択：成績の上位1/4はそのまま残り、残りは成績で重みをつけて手本を選び、交叉・変異で作る。

  --force wait / aggr   全員の性質を固定する（比較用）。指定しなければ、性質も進化が選ぶ
  --policy pro          全員が大会型の判断（待つ・メタは1枚・受けを消してから殴る・除去を温存）で動く

  python evolve6.py --seed 1 --out runs6/free_s1.json
"""
import argparse
import json
import math
import random
import time
from collections import Counter

import engine2
from cards2 import BY_KEY, CLOSURES, COMBO, KEYS, PATHS, deck_closures, deck_defense, deck_paths, main_path, max_copies
from engine2 import PRO, Game
from seeds2 import SEEDS


# ---------- 遺伝子の操作 ----------
def repair(counts, rng, prefer=None):
    counts = {k: min(v, max_copies(k)) for k, v in counts.items() if v > 0}
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


def mutate(g, rng):
    counts, aggr = dict(g[0]), g[1]
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
    keys = sorted(set(a[0]) | set(b[0]))
    child = {}
    for k in keys:
        x, y = a[0].get(k, 0), b[0].get(k, 0)
        child[k] = rng.choice((x, y, (x + y) // 2, (x + y + 1) // 2))
    return (repair(child, rng, prefer=keys), rng.choice((a[1], b[1])))


def random_deck(rng):
    return (repair({}, rng), rng.randint(0, 1))


def describe(g):
    c = g[0]
    d = deck_defense(c)
    paths = sorted(deck_paths(c))
    clos = sorted(deck_closures(c))
    return {"paths": paths, "closures": clos, "main": main_path(c), "triggers": d["triggers"], "gstrike": d["gstrike"],
            "hand": d["hand"], "signature": "+".join(paths) + "|" + "+".join(clos),
            "multi": c.get("chakra", 0) + c.get("rod", 0) + c.get("vt", 0)}


# ---------- 評価 ----------
def evaluate(pop, outside, games, rng, cfg, tally):
    n = len(pop)
    pol = cfg["_pol"]
    wins, played = [0.0] * n, [0] * n
    for i in range(n):
        for g in range(games):
            if outside and rng.random() < 0.4:
                o = rng.randrange(len(outside))
                r = Game(pop[i], outside[o], rng, first=g % 2, policies=pol).play()
                wins[i] += 1.0 if r == "A" else (0.5 if r is None else 0.0)
                played[i] += 1
                continue
            j = rng.randrange(n - 1)
            j = j + 1 if j >= i else j
            gm = Game(pop[i], pop[j], rng, first=g % 2, policies=pol)
            r = gm.play()
            tally["n"] += 1
            if r == "A":
                wins[i] += 1
            elif r == "B":
                wins[j] += 1
            else:
                wins[i] += 0.5
                wins[j] += 0.5
            played[i] += 1
            played[j] += 1
            if r:
                st = gm.stats
                tally["won"] += 1
                tally["turn"] += gm.round
                tally["by3"] += gm.round <= 3
                tally["by4"] += gm.round <= 4
                tally["clean"] += st["clean"]
                tally["trig"] += st["trig"] > 0
                tally["hand"] += st["hand"] > 0
                tally["meta3"] += st["meta3"]
                tally["lock4"] += st["lock"].get(r, 99) <= 4
                tally["dec4"] += min(gm.round, st["lock"].get(r, 99)) <= 4
                tally["path_" + gm.win_path] += 1
                w = pop[i] if r == "A" else pop[j]
                tally["wait_win"] += (not w[1])
    return [wins[i] / played[i] for i in range(n)]


def stats(pop, fit, tally, cfg):
    n = len(pop)
    desc = [describe(g) for g in pop]
    top = sorted(range(n), key=lambda i: -fit[i])[: max(1, n // 4)]
    won = max(1, tally["won"])
    mains = Counter(x["main"] for x in desc)
    sig = Counter(x["signature"] for x in desc)
    aggr = [(1 if cfg["force"] == "aggr" else 0 if cfg["force"] == "wait" else g[1]) for g in pop]
    return {
        "wait_share": sum(1 - a for a in aggr) / n,
        "wait_top": sum(1 - aggr[i] for i in top) / len(top),
        "main_share": {p: mains.get(p, 0) / n for p in list(PATHS) + ["なし"]},
        "path_share": {p: sum(p in x["paths"] for x in desc) / n for p in PATHS},
        "combo_share": sum(bool(COMBO & set(x["paths"])) for x in desc) / n,
        "closure_share": {c: sum(c in x["closures"] for x in desc) / n for c in CLOSURES},
        "closures_mean": sum(len(x["closures"]) for x in desc) / n,
        "types": sum(1 for v in mains.values() if v / n >= 0.1),            # 1割以上いるデッキタイプの数
        "top_type": max(mains.values()) / n,
        "conc_main": sum((v / n) ** 2 for v in mains.values()),
        "concentration": sum((v / n) ** 2 for v in sig.values()),
        "triggers": sum(x["triggers"] for x in desc) / n,
        "gstrike": sum(x["gstrike"] for x in desc) / n,
        "handdef": sum(x["hand"] for x in desc) / n,
        "multi": sum(x["multi"] for x in desc) / n,
        "win_turn": tally["turn"] / won,
        **{k: tally[k] / won for k in ("by3", "by4", "dec4", "clean", "trig", "hand", "meta3", "lock4", "wait_win")},
        "win_path": {p: tally["path_" + p] / won for p in list(PATHS) + ["DECKOUT"]},
    }


def force(g, cfg):
    if cfg["force"] == "wait":
        return (g[0], 0)
    if cfg["force"] == "aggr":
        return (g[0], 1)
    return g


def run(cfg, gens, pop_size, games, seed, log=print):
    rng = random.Random(seed)
    engine2.TEMPO = cfg["tempo"]
    cfg["_pol"] = (PRO, PRO) if cfg["policy"] == "pro" else (None, None)
    seeds = [force(g, cfg) for g in SEEDS.values()]
    pop = [seeds[i % len(seeds)] if i < len(seeds) else force(mutate(seeds[i % len(seeds)], rng), cfg) for i in range(pop_size)]
    outside_fixed = seeds + [force(random_deck(rng), cfg) for _ in range(6)]
    snapshots, history = [], []
    t0 = time.time()
    for gen in range(gens):
        tally = Counter()
        fit = evaluate(pop, outside_fixed + snapshots, games, rng, cfg, tally)
        st = stats(pop, fit, tally, cfg)
        st["gen"] = gen
        history.append(st)
        order = sorted(range(pop_size), key=lambda i: -fit[i])
        if gen % 10 == 0:
            snapshots = (snapshots + [pop[order[0]]])[-6:]
        if gen % 20 == 0 or gen == gens - 1:
            mains = "・".join(f"{k}{v * 100:.0f}" for k, v in st["main_share"].items() if v >= 0.1)
            log(f"[{gen:3d}] 待つ{st['wait_share'] * 100:.0f}% {mains} 勝ちT{st['win_turn']:.1f} 4T決着{st['by4'] * 100:.0f}%"
                f" 1ターンキル{st['clean'] * 100:.0f}% ({time.time() - t0:.0f}s)")
        mu = sum(fit) / pop_size
        w = [math.exp(6 * (f - mu)) for f in fit]
        new = list(pop)
        for i in order[pop_size // 4:]:
            if rng.random() < 0.5:
                a, b = rng.choices(pop, w, k=2)
                c = crossover(a, b, rng)
                c = mutate(c, rng) if rng.random() < 0.5 else c
            else:
                c = mutate(rng.choices(pop, w, k=1)[0], rng)
            new[i] = force(c, cfg)
        pop = new
    tally = Counter()
    fit = evaluate(pop, outside_fixed + snapshots, games, rng, cfg, tally)
    return pop, fit, history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", type=int, default=80)
    ap.add_argument("--pop", type=int, default=36)
    ap.add_argument("--games", type=int, default=70)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tempo", type=int, default=0)
    ap.add_argument("--force", choices=("", "wait", "aggr"), default="", help="全員の性質を固定する（wait＝待つ、aggr＝毎ターン動く）")
    ap.add_argument("--policy", choices=("sim", "pro"), default="sim", help="pro＝全員が大会型の判断で動く")
    ap.add_argument("--out", default="run6.json")
    a = ap.parse_args()
    cfg = {"tempo": a.tempo, "force": a.force, "policy": a.policy}
    pop, fit, hist = run(cfg, a.gens, a.pop, a.games, a.seed)
    cfg.pop("_pol", None)
    order = sorted(range(len(pop)), key=lambda i: -fit[i])
    final = [{"counts": pop[i][0], "aggr": pop[i][1], "fitness": fit[i], **describe(pop[i])} for i in order]
    json.dump({"args": vars(a), "cfg": cfg, "history": hist, "final": final}, open(a.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"保存しました：{a.out}")


if __name__ == "__main__":
    main()
