#!/usr/bin/env python3
"""進化 v2：環境外デッキと、人間のデッキ構築の思い込みを入れる

【環境外デッキ】
  --offmeta 0.4   対戦の4割を環境外デッキと行う
                  （環境外＝純粋な型6種、構築の粗いランダムデッキ6種、少し前の環境のトップ（10世代ごとに保存））
  --unknown       環境外デッキの正体は分からない。プレイヤーは「環境の平均的なデッキ」が相手だと想定して、
                  封殺や除去の使い方を決める（環境デッキ同士は正体が分かる）

【デッキ構築の思い込み】 --bias copy,playset,metaread,flashy,trigmin
  copy     : 新しいデッキの半分は、上位3つのどれかをほぼ丸写し（1枚まで変える）
  playset  : カードは4枚単位で入れたり抜いたりする（1〜3枚の採用を避ける）
  metaread : 前の世代のトップ3を仮想敵に、候補4つを各8戦だけ試して一番よかったものを採用（情報の遅れ＋少ない試行）
  flashy   : 入れるカードを選ぶとき、大型・SA・入れ替え・フィニッシャーを好み、除去や手札破壊を軽く見る
  trigmin  : 「トリガーは8枚は入れないと不安」という思い込み（トリガーを8枚未満にしない）
"""
import argparse
import json
import random
import time
from collections import Counter

from cards import BY_KEY, CLOSURES, PATHS, deck_defense, deck_paths, max_copies
from engine import Game, View, profile_of
from evolve import KEYS, crossover, describe, mutate, random_deck, repair
from seeds import SEEDS

TRIGGER_KEYS = [k for k in KEYS if BY_KEY[k].trig]
FLASHY = {"sa2": 3, "sa3": 3, "swap": 3, "b3": 3, "t_big": 3, "chain_fin": 3,
          "removal": 0.4, "handes_c": 0.4, "handes_s": 0.4, "wipe": 0.4}


# ---------- 思い込みつきの変化 ----------

def pick_add(rng, counts, flashy):
    while True:
        if flashy:
            k = rng.choices(KEYS, [FLASHY.get(x, 1.0) for x in KEYS])[0]
        else:
            k = rng.choice(KEYS)
        if counts.get(k, 0) < max_copies(k):
            return k


def mutate_b(genome, rng, biases):
    if "playset" not in biases and "flashy" not in biases:
        g = mutate(genome, rng)
    else:
        counts, aggr = dict(genome[0]), genome[1]
        steps = rng.choice((1, 1, 2, 2, 3, 4))
        for _ in range(steps):
            if "playset" in biases and rng.random() < 0.7:
                # 4枚単位：1種類を抜き、別の1種類を4枚（入るだけ）入れる
                k = rng.choice(list(counts))
                n = min(4, counts[k])
                counts[k] -= n
                if counts[k] == 0:
                    del counts[k]
                add = pick_add(rng, counts, "flashy" in biases)
                room = max_copies(add) - counts.get(add, 0)
                counts[add] = counts.get(add, 0) + min(n, room)
            else:
                k = rng.choice([k for k, v in counts.items() for _ in range(v)])
                counts[k] -= 1
                if counts[k] == 0:
                    del counts[k]
                add = pick_add(rng, counts, "flashy" in biases)
                counts[add] = counts.get(add, 0) + 1
        if rng.random() < 0.1:
            aggr = 1 - aggr
        g = (repair(counts, rng), aggr)
    return enforce(g, rng, biases)


def enforce(genome, rng, biases):
    if "trigmin" not in biases:
        return genome
    counts = dict(genome[0])
    while sum(counts.get(k, 0) for k in TRIGGER_KEYS) < 8:
        nont = [k for k, v in counts.items() if not BY_KEY[k].trig for _ in range(v)]
        k = rng.choice(nont)
        counts[k] -= 1
        if counts[k] == 0:
            del counts[k]
        t = rng.choice(TRIGGER_KEYS)
        if counts.get(t, 0) < max_copies(t):
            counts[t] = counts.get(t, 0) + 1
        else:
            counts[k] = counts.get(k, 0) + 1
    return (counts, genome[1])


# ---------- 相手の想定 ----------

def known_signatures(pop):
    """環境デッキとして「正体が知られている」署名：2つ以上あり、集団の上位を占めるもの"""
    sig = Counter(describe(g)["signature"] for g in pop)
    out, covered = set(), 0
    for s, n in sig.most_common():
        if n < 2:
            break
        out.add(s)
        covered += n
        if covered >= 0.8 * len(pop):
            break
    return out


def meta_view(pop):
    """「環境の平均的なデッキ」：半分以上のデッキが持つ経路と、守りの平均"""
    profs = [profile_of(g[0]) for g in pop]
    n = len(profs)
    paths = {p for p in PATHS if sum(p in x.paths for x in profs) >= n / 2}
    keys = profs[0].defense.keys()
    defense = {k: sum(x.defense[k] for x in profs) / n for k in keys}
    return View(paths, defense, sum(x.sa for x in profs) / n)


# ---------- 評価 ----------

def evaluate(pop, outside, games, rng, cfg, mview, known):
    n = len(pop)
    sigs = [describe(g)["signature"] for g in pop]
    out_sigs = [describe(g)["signature"] for g in outside]
    wins = [0.0] * n
    played = [0] * n
    off_w = off_n = 0
    for i in range(n):
        for g in range(games):
            if outside and rng.random() < cfg["offmeta"]:
                k = rng.randrange(len(outside))
                opp = outside[k]
                va = mview if (cfg["unknown"] and out_sigs[k] not in known) else None
                game = Game(pop[i], opp, rng, first=g % 2, views=(va, None))
                r = game.play()
                s = 1.0 if r == "A" else (0.5 if r is None else 0.0)
                wins[i] += s
                played[i] += 1
                off_w += s
                off_n += 1
            else:
                j = rng.randrange(n - 1)
                j = j + 1 if j >= i else j
                va = mview if (cfg["unknown"] and sigs[j] not in known) else None
                vb = mview if (cfg["unknown"] and sigs[i] not in known) else None
                game = Game(pop[i], pop[j], rng, first=g % 2, views=(va, vb))
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
    return [wins[i] / played[i] for i in range(n)], (off_w / off_n if off_n else None)


def quick_score(cand, rivals, rng, games=8):
    w = 0.0
    for r in rivals:
        for g in range(games // len(rivals) or 1):
            res = Game(cand, r, rng, first=g % 2).play()
            w += 1 if res == "A" else (0.5 if res is None else 0)
    return w


# ---------- 観測 ----------

def stats(pop, fit, off_wr):
    desc = [describe(g) for g in pop]
    n = len(pop)
    top = sorted(range(n), key=lambda i: -fit[i])[: max(1, n // 4)]
    sig = Counter(x["signature"] for x in desc)
    combo = lambda x: bool({"CHAIN", "LOOP"} & set(x["paths"]))
    return {
        "fit_top": max(fit),
        "path_share": {p: sum(p in x["paths"] for x in desc) / n for p in PATHS},
        "closure_share": {c: sum(c in x["closures"] for x in desc) / n for c in CLOSURES},
        "combo_share": sum(combo(x) for x in desc) / n,
        "combo_top": sum(combo(desc[i]) for i in top) / len(top),
        "hybrid_mean": sum(x["hybrid"] for x in desc) / n,
        "triggers_mean": sum(x["triggers"] for x in desc) / n,
        "triggers_top": sum(desc[i]["triggers"] for i in top) / len(top),
        "removal_mean": sum(x["removal"] for x in desc) / n,
        "concentration": sum((v / n) ** 2 for v in sig.values()),
        "offmeta_wr": off_wr,
    }


# ---------- 進化 ----------

def run(cfg, gens, pop_size, games, seed, log=print):
    rng = random.Random(seed)
    biases = set(cfg["bias"])
    seeds = list(SEEDS.values())
    pop = [seeds[i % len(seeds)] if i < len(seeds) else mutate(seeds[i % len(seeds)], rng) for i in range(pop_size)]
    pop = [enforce(g, rng, biases) for g in pop]
    outside_fixed = seeds + [random_deck(rng) for _ in range(6)]
    snapshots = []
    history = []
    prev_top = pop[:3]
    t0 = time.time()
    for gen in range(gens):
        outside = outside_fixed + snapshots if cfg["offmeta"] > 0 else []
        known = known_signatures(pop)
        mview = meta_view(pop)
        fit, off_wr = evaluate(pop, outside, games, rng, cfg, mview, known)
        st = stats(pop, fit, off_wr)
        st["gen"] = gen
        history.append(st)
        order = sorted(range(pop_size), key=lambda i: -fit[i])
        if gen % 10 == 0:
            snapshots = (snapshots + [pop[order[0]]])[-6:]   # 少し前の環境のトップを環境外に残す
        if gen % 20 == 0 or gen == gens - 1:
            log(f"[{gen:3d}] 混合{st['hybrid_mean']:.1f} 集中{st['concentration']:.2f} コンボ{st['combo_share'] * 100:.0f}%"
                f"(上位{st['combo_top'] * 100:.0f}%) トリガー{st['triggers_mean']:.1f}(上位{st['triggers_top']:.1f})"
                f" 環境外への勝率{(off_wr or 0) * 100:.0f}% ({time.time() - t0:.0f}s)")
        elite_n = max(2, pop_size // 4)
        elite = [pop[i] for i in order[:elite_n]]
        parents = [pop[i] for i in order[: pop_size // 2]]
        top3 = [pop[i] for i in order[:3]]
        new = list(elite)
        while len(new) < pop_size:
            if "copy" in biases and rng.random() < 0.5:
                child = rng.choice(top3)
                if rng.random() < 0.5:
                    c = dict(child[0])
                    k = rng.choice(list(c))
                    c[k] -= 1
                    c = {a: b for a, b in c.items() if b}
                    child = enforce((repair(c, rng), child[1]), rng, biases)
            elif "metaread" in biases:
                base = rng.choice(parents)
                cands = []
                for _ in range(4):
                    c = crossover(base, rng.choice(parents), rng) if rng.random() < 0.5 else base
                    cands.append(mutate_b(c, rng, biases))
                child = max(cands, key=lambda c: quick_score(c, prev_top, rng))
            else:
                if rng.random() < 0.5:
                    child = crossover(rng.choice(parents), rng.choice(parents), rng)
                    child = enforce(child, rng, biases)
                    if rng.random() < 0.5:
                        child = mutate_b(child, rng, biases)
                else:
                    child = mutate_b(rng.choice(parents), rng, biases)
            new.append(child)
        prev_top = top3
        pop = new
    fit, off_wr = evaluate(pop, (outside_fixed + snapshots) if cfg["offmeta"] > 0 else [], games, rng, cfg,
                           meta_view(pop), known_signatures(pop))
    return pop, fit, history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", type=int, default=80)
    ap.add_argument("--pop", type=int, default=32)
    ap.add_argument("--games", type=int, default=80)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--offmeta", type=float, default=0.0)
    ap.add_argument("--unknown", action="store_true")
    ap.add_argument("--bias", default="")
    ap.add_argument("--out", default="run2.json")
    a = ap.parse_args()
    cfg = {"offmeta": a.offmeta, "unknown": a.unknown, "bias": [b for b in a.bias.split(",") if b]}
    pop, fit, hist = run(cfg, a.gens, a.pop, a.games, a.seed)
    order = sorted(range(len(pop)), key=lambda i: -fit[i])
    final = [{"counts": pop[i][0], "aggr": pop[i][1], "fitness": fit[i], **describe(pop[i])} for i in order]
    json.dump({"args": vars(a), "cfg": cfg, "history": hist, "final": final},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"保存しました：{a.out}")


if __name__ == "__main__":
    main()
