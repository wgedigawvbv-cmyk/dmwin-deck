#!/usr/bin/env python3
"""進化 v3：人気・デッキの難しさ・封殺によるトリガー抑制

すべての条件で「環境外デッキ4割・環境外の正体は分からない」を入れる（v2 の現実寄りの設定）。

集団は「プレイヤー」の集まり。各プレイヤーがデッキを1つ持つ。

  --pop-beta 1.0   人気：次に使うデッキを選ぶ重み ∝ exp(成績) × (そのデッキタイプの使用率)^β
  --difficulty 2.0 難しさ：ミス率 = 係数 × デッキの難しさ × (1 − 使い手の腕)（上限0.9）
  --skill random   腕は対戦ごとにばらばら（デッキと使い手に関係がない）
  --skill fixed    腕はプレイヤーごとに決まっている（0〜1 に均等）。成績のよかった上位1/4は同じデッキを使い続け、
                   残りは成績と人気を見て乗り換える → 「難しいデッキは上手い人の手にだけ残る」が起きうる
  --suppress 0.4   封殺によるトリガー抑制：場の封殺1種類ごとに、相手のトリガーをこの確率で不発にする
  --combo-fast     コンボの速さを攻撃と拮抗させる（連鎖に必要な数3・ループに必要なマナ4）
"""
import argparse
import json
import math
import random
import time
from collections import Counter, defaultdict

import engine
from cards import CLOSURES, PATHS, deck_difficulty
from engine import Game
from evolve import crossover, describe, mutate, random_deck
from evolve2 import known_signatures, meta_view
from seeds import SEEDS


def pilot_err(k, d, skill):
    return min(0.9, k * d * (1 - skill)) if k else 0.0


def evaluate(pop, skills, outside, games, rng, cfg, mview, known):
    n = len(pop)
    k = cfg["difficulty"]
    fixed = cfg["skill"] == "fixed"
    sigs = [describe(g)["signature"] for g in pop]
    diffs = [deck_difficulty(g[0]) for g in pop]
    out_sigs = [describe(g)["signature"] for g in outside]
    out_diffs = [deck_difficulty(g[0]) for g in outside]
    sk = (lambda i: skills[i]) if fixed else (lambda i: rng.random())
    wins = [0.0] * n
    played = [0] * n
    for i in range(n):
        for g in range(games):
            if outside and rng.random() < cfg["offmeta"]:
                o = rng.randrange(len(outside))
                va = mview if (cfg["unknown"] and out_sigs[o] not in known) else None
                errs = (pilot_err(k, diffs[i], sk(i)), pilot_err(k, out_diffs[o], rng.random()))
                r = Game(pop[i], outside[o], rng, first=g % 2, views=(va, None), errs=errs).play()
                wins[i] += 1.0 if r == "A" else (0.5 if r is None else 0.0)
                played[i] += 1
            else:
                j = rng.randrange(n - 1)
                j = j + 1 if j >= i else j
                va = mview if (cfg["unknown"] and sigs[j] not in known) else None
                vb = mview if (cfg["unknown"] and sigs[i] not in known) else None
                errs = (pilot_err(k, diffs[i], sk(i)), pilot_err(k, diffs[j], sk(j)))
                r = Game(pop[i], pop[j], rng, first=g % 2, views=(va, vb), errs=errs).play()
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


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for q in range(i, j + 1):
                r[order[q]] = (i + j) / 2
            i = j + 1
        return r
    if len(xs) < 3:
        return None
    rx, ry = rank(xs), rank(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    vy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return cov / (vx * vy) if vx and vy else None


def mean(v):
    return sum(v) / len(v) if v else None


def stats(pop, skills, fit):
    desc = [describe(g) for g in pop]
    n = len(pop)
    diffs = [deck_difficulty(g[0]) for g in pop]
    top = sorted(range(n), key=lambda i: -fit[i])[: max(1, n // 4)]
    sig = Counter(x["signature"] for x in desc)
    is_combo = [bool({"CHAIN", "LOOP"} & set(x["paths"])) for x in desc]
    by = defaultdict(list)
    for x, f in zip(desc, fit):
        by[x["signature"]].append(f)
    types = [(len(v) / n, sum(v) / len(v)) for v in by.values() if len(v) >= 2]
    top_sig, top_n = sig.most_common(1)[0]
    rest = [f for x, f in zip(desc, fit) if x["signature"] != top_sig]
    return {
        "combo_share": sum(is_combo) / n,
        "combo_top": sum(is_combo[i] for i in top) / len(top),
        "combo_fit": mean([f for f, c in zip(fit, is_combo) if c]),
        "other_fit": mean([f for f, c in zip(fit, is_combo) if not c]),
        "combo_skill": mean([s for s, c in zip(skills, is_combo) if c]),
        "triggers_mean": sum(x["triggers"] for x in desc) / n,
        "triggers_top": sum(desc[i]["triggers"] for i in top) / len(top),
        "closures_mean": sum(len(x["closures"]) for x in desc) / n,
        "hybrid_mean": sum(x["hybrid"] for x in desc) / n,
        "concentration": sum((v / n) ** 2 for v in sig.values()),
        "closure_share": {c: sum(c in x["closures"] for x in desc) / n for c in CLOSURES},
        "path_share": {p: sum(p in x["paths"] for x in desc) / n for p in PATHS},
        "difficulty_mean": sum(diffs) / n,
        "difficulty_top": sum(diffs[i] for i in top) / len(top),
        "skill_vs_difficulty": spearman(skills, diffs),
        "share_vs_strength": spearman([t[0] for t in types], [t[1] for t in types]),
        "n_types": len(types),
        "top_type_share": top_n / n,
        "top_type_gap": (mean(by[top_sig]) - mean(rest)) if rest else None,
    }


def run(cfg, gens, pop_size, games, seed, log=print):
    rng = random.Random(seed)
    engine.SUPPRESS = {k: cfg["suppress"] for k in engine.SUPPRESS}
    if cfg["combo_fast"]:
        engine.CHAIN_NEED, engine.LOOP_MANA = 3, 4
    seeds = list(SEEDS.values())
    pop = [seeds[i % len(seeds)] if i < len(seeds) else mutate(seeds[i % len(seeds)], rng) for i in range(pop_size)]
    skills = [(i + 0.5) / pop_size for i in range(pop_size)]
    rng.shuffle(skills)
    outside_fixed = seeds + [random_deck(rng) for _ in range(6)]
    snapshots, history = [], []
    t0 = time.time()
    for gen in range(gens):
        outside = outside_fixed + snapshots
        fit = evaluate(pop, skills, outside, games, rng, cfg, meta_view(pop), known_signatures(pop))
        st = stats(pop, skills, fit)
        st["gen"] = gen
        history.append(st)
        order = sorted(range(pop_size), key=lambda i: -fit[i])
        if gen % 10 == 0:
            snapshots = (snapshots + [pop[order[0]]])[-6:]
        if gen % 25 == 0 or gen == gens - 1:
            log(f"[{gen:3d}] コンボ{st['combo_share'] * 100:.0f}% トリガー{st['triggers_mean']:.1f} 集中{st['concentration']:.2f}"
                f" 難しさ{st['difficulty_mean']:.2f} ({time.time() - t0:.0f}s)")
        # 成績のよかった上位1/4のプレイヤーは同じデッキを使い続ける。
        # 残りのプレイヤーは「成績 × 人気」の重みで手本を選び、少し変えて使う
        sigs = [describe(g)["signature"] for g in pop]
        share = Counter(sigs)
        mu = sum(fit) / pop_size
        w = [math.exp(6 * (fit[i] - mu)) * ((share[sigs[i]] / pop_size) ** cfg["pop_beta"]) for i in range(pop_size)]
        new = list(pop)
        for i in order[pop_size // 4:]:
            if rng.random() < 0.5:
                a, b = rng.choices(pop, w, k=2)
                child = crossover(a, b, rng)
                if rng.random() < 0.5:
                    child = mutate(child, rng)
            else:
                child = mutate(rng.choices(pop, w, k=1)[0], rng)
            new[i] = child
        pop = new
    fit = evaluate(pop, skills, outside_fixed + snapshots, games, rng, cfg, meta_view(pop), known_signatures(pop))
    return pop, skills, fit, history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", type=int, default=100)
    ap.add_argument("--pop", type=int, default=32)
    ap.add_argument("--games", type=int, default=80)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--pop-beta", type=float, default=0.0)
    ap.add_argument("--difficulty", type=float, default=0.0)
    ap.add_argument("--skill", choices=("random", "fixed"), default="random")
    ap.add_argument("--suppress", type=float, default=0.0)
    ap.add_argument("--combo-fast", action="store_true")
    ap.add_argument("--out", default="run3.json")
    a = ap.parse_args()
    cfg = {"offmeta": 0.4, "unknown": True, "pop_beta": a.pop_beta, "difficulty": a.difficulty,
           "skill": a.skill, "suppress": a.suppress, "combo_fast": a.combo_fast}
    pop, skills, fit, hist = run(cfg, a.gens, a.pop, a.games, a.seed)
    order = sorted(range(len(pop)), key=lambda i: -fit[i])
    final = [{"counts": pop[i][0], "aggr": pop[i][1], "fitness": fit[i], "difficulty": deck_difficulty(pop[i][0]),
              "skill": skills[i], **describe(pop[i])} for i in order]
    json.dump({"args": vars(a), "cfg": cfg, "history": hist, "final": final},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"保存しました：{a.out}")


if __name__ == "__main__":
    main()
