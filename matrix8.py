#!/usr/bin/env python3
"""実在の7デッキ＋ネットで調べた5つのデッキタイプを、全デッキ共通の先読み操縦で総当たりさせる

  python matrix8.py --games 6 --budget 200 --procs 2 --out runs8/matrix8.json
  python matrix8.py --official --games 2 --budget 150 --procs 1 --out runs8/matrix9.json   公式の入賞リスト36個
  python matrix8.py --official --pop runs8/pop1.json --games 2 --budget 150 --out runs8/matrix11.json
  python matrix8.py --show runs8/matrix8.json
"""
import argparse
import json
import random
import time
from multiprocessing import Pool

import ai3
import archetypes
import creator
import decks8
from cards3 import DECKS

ALL = dict(DECKS)
for _n, _a in archetypes.ARCHETYPES.items():
    ALL[_n] = _a["deck"]
NAMES = list(ALL)


def use_official():
    """公式カバレージの入賞リスト（decks8.py）を使う"""
    global ALL, NAMES, SHORT
    ALL = dict(decks8.DECKS8)
    NAMES = list(ALL)
    SHORT = {n: decks8.short(n) for n in NAMES}


def add_population(path):
    """population.py が創作したオリジナルデッキを、いまの顔ぶれに足す"""
    global ALL, NAMES, SHORT
    log = json.load(open(path, encoding="utf-8"))
    for i, e in enumerate(log["decks"], 1):
        n = f"創作{i}（{path}）"
        ALL[n] = {k: int(v) for k, v in e["deck"].items()}
        NAMES.append(n)
        SHORT[n] = f"創作{i}"
    print(f"オリジナルデッキ {len(log['decks'])}個を足しました（{path}）")
SHORT = {"4c der'Bande": "der'Bande", "光自然ウィリデ": "ウィリデ", "創世竜ループ": "創世竜", "ドッコイループ": "ドッコイ",
         "ゾロ・ア・スタート": "ゾロ", "水単チェンジサイバー": "サイバー", "火水闇ジャオウガ": "ジャオウガ",
         "青黒デスパペット": "デスパペット", "クローシス モウジャキンガ": "モウジャキンガ", "赤白サムライ": "サムライ",
         "ドロマーロストクルセイダー": "ロスト", "禁断型火自然バイク": "バイク"}


def one(job):
    a, b, seed, first, budget, pol = job
    g = ai3.play_game(ALL[a], ALL[b], random.Random(seed), first, (budget, budget), names=("*", "*"), pols=(pol, pol))
    return {"a": a, "b": b, "w": g.winner, "how": g.how, "turn": (g.turn + 1) // 2}


def nash(M):
    """相性表から「釣り合いの取れた使用率」を求める（どのデッキに変えても得をしない配分）"""
    import numpy as np
    from scipy.optimize import linprog
    ns = [n for n in NAMES if n in M]
    k = len(ns)
    A = np.array([[(M[a].get(b, 0.5) if b != a else 0.5) - 0.5 for b in ns] for a in ns])
    c = np.zeros(k + 1)
    c[-1] = -1
    res = linprog(c, A_ub=np.hstack([-A.T, np.ones((k, 1))]), b_ub=np.zeros(k),
                  A_eq=np.hstack([np.ones((1, k)), np.zeros((1, 1))]), b_eq=[1],
                  bounds=[(0, 1)] * k + [(None, None)])
    if not res.success:
        return None
    return {ns[i]: float(res.x[i]) for i in range(k)}


def show(res):
    M = {a: {} for a in NAMES}
    cnt = {a: {} for a in NAMES}
    for r in res:
        a, b = r["a"], r["b"]
        s = M[a].setdefault(b, 0.0)
        M[a][b] = s + (1.0 if r["w"] == 0 else 0.5 if r["w"] is None else 0.0)
        cnt[a][b] = cnt[a].get(b, 0) + 1
    for a in NAMES:
        for b in M[a]:
            M[a][b] /= cnt[a][b]
    rows = []
    for a in NAMES:
        vs = [M[a].get(b) for b in NAMES if b != a]
        got = [v for v in vs if v is not None]
        rows.append((sum(got) / max(1, len(got)), a, len(got)))
    if len(NAMES) <= 14:                      # デッキが少ない時だけ相性表を出す（多いと読めない）
        w = max(len(SHORT.get(n, n)) for n in NAMES)
        print("".ljust(w + 2) + " ".join(SHORT.get(n, n)[:6].rjust(7) for n in NAMES) + "   平均")
        for avg, a, _k in rows:
            cells = " ".join(("  －  " if b == a else f"{M[a].get(b, 0) * 100:5.0f}%").rjust(7) for b in NAMES)
            print(SHORT.get(a, a).ljust(w + 2) + cells + f"  {avg * 100:4.0f}%")
    print("\n平均勝率の順（1デッキあたりの相手の数と、1組の対戦数から誤差を見ること）")
    for avg, a, k in sorted(rows, reverse=True):
        print(f"  {avg * 100:5.1f}%  {SHORT.get(a, a)}")
    pops = [n for n in NAMES if n.startswith("創作")]
    if pops:
        print("\n創作したオリジナルデッキの成績（相手ごと）")
        for a in pops:
            vs = sorted((v, b) for b in NAMES if b != a and (v := M[a].get(b)) is not None)
            if not vs:
                continue
            avg = sum(v for v, _b in vs) / len(vs)
            print(f"  {SHORT.get(a, a)}  平均 {avg * 100:.0f}%（相手{len(vs)}個）")
            print("    得意：" + "、".join(f"{SHORT.get(b, b)} {v * 100:.0f}%" for v, b in vs[::-1][:3]))
            print("    苦手：" + "、".join(f"{SHORT.get(b, b)} {v * 100:.0f}%" for v, b in vs[:3]))
    hows = {}
    for r in res:
        hows[r["how"]] = hows.get(r["how"], 0) + 1
    print("決まり方：" + "、".join(f"{k} {v}" for k, v in sorted(hows.items(), key=lambda kv: -kv[1])))
    print(f"平均の決着ターン：{sum(r['turn'] for r in res) / len(res):.1f}")
    vals = [a for a, _n, _k in rows]
    mid = sum(1 for v in vals if 0.45 <= v <= 0.55)
    print(f"平均勝率のばらつき：最高 {max(vals) * 100:.0f}%／最低 {min(vals) * 100:.0f}%／"
          f"45〜55%に入るデッキ {mid}/{len(vals)}個")
    try:
        mix = nash(M)
    except Exception as e:
        mix = None
        print(f"（釣り合いの取れた使用率は求められませんでした：{e}）")
    if mix:
        use = sorted(((v, n) for n, v in mix.items() if v > 0.005), reverse=True)
        print(f"釣り合いの取れた使用率（0.5%以上のデッキ {len(use)}個／全{len(mix)}個）：")
        for v, n in use:
            print(f"  {v * 100:5.1f}%  {SHORT.get(n, n)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=6, help="1組あたりの対戦数（先攻後攻を半分ずつ）")
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--policy", default="runs7/policy3_4.json")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="runs8/matrix8.json")
    ap.add_argument("--show")
    ap.add_argument("--official", action="store_true", help="公式カバレージの入賞リストで総当たりする")
    ap.add_argument("--pop", help="population.py の結果JSON。創作したオリジナルデッキも顔ぶれに足す")
    args = ap.parse_args()
    if args.official:
        use_official()
    if args.show:
        d = json.load(open(args.show, encoding="utf-8"))
        if d["args"].get("official"):
            use_official()
        if d["args"].get("pop"):
            add_population(d["args"]["pop"])
        show(d["res"])
        return
    if args.pop:
        add_population(args.pop)
    pol = creator.global_policy(args.policy)
    pol = creator.extend_policy(pol, [c for c in creator.NETKEYS])
    rng = random.Random(args.seed)
    jobs = []
    for i, a in enumerate(NAMES):
        for b in NAMES[i + 1:]:
            for g in range(args.games):
                x, y = (a, b) if g % 2 == 0 else (b, a)
                jobs.append((x, y, rng.getrandbits(40), g % 2, args.budget, pol))
    print(f"{len(NAMES)}デッキ、{len(jobs)}戦（1組{args.games}戦、探索{args.budget}回）")
    t0 = time.time()
    res = []
    with Pool(args.procs) as pool:
        for k, r in enumerate(pool.imap_unordered(one, jobs, chunksize=2)):
            res.append(r)
            if (k + 1) % 50 == 0:
                print(f"  {k + 1}/{len(jobs)}（{time.time() - t0:.0f}秒）", flush=True)
    json.dump({"args": vars(args), "res": res}, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"保存：{args.out}（{time.time() - t0:.0f}秒）\n")
    show(res)


if __name__ == "__main__":
    main()
