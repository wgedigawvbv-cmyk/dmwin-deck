#!/usr/bin/env python3
"""第3版：実在の7デッキを、全デッキ共通の先読み操縦で総当たりさせる

  python matrix3.py --games 40 --budget 600 --policy runs7/policy3_4.json --out runs7/matrix.json
  python matrix3.py --show runs7/matrix.json          結果の表示だけ
"""
import argparse
import json
import random
import time
from multiprocessing import Pool

import ai3
from cards3 import DECKS, REAL_USAGE

SHORT = {"4c der'Bande": "der'Bande", "光自然ウィリデ": "ウィリデ", "創世竜ループ": "創世竜", "ドッコイループ": "ドッコイ",
         "ゾロ・ア・スタート": "ゾロ", "水単チェンジサイバー": "サイバー", "火水闇ジャオウガ": "ジャオウガ"}


def one(job):
    a, b, seed, first, budget, pol = job
    ai3.load_policy(pol if pol else {})
    g = ai3.play_game(DECKS[a], DECKS[b], random.Random(seed), first, (budget, budget), names=(a, b))
    return {"a": a, "b": b, "w": g.winner, "how": g.how, "turn": (g.turn + 1) // 2, "first": first, "trig": g.trig,
            "fa": g.fa, "chg": g.chg, "loopt": g.loopt, "hold": g.hold, "atkt": g.atkt}


def nash(M, names):
    """相性表から、釣り合いの取れた使用率（どのデッキを選んでも得をしない配分）を求める"""
    import numpy as np
    from scipy.optimize import linprog
    n = len(names)
    A = np.array([[M[a][b] - 0.5 for b in names] for a in names])
    # 変数：x（n個）と v。最大化 v、条件：すべての相手 j について Σ x_i A[i][j] >= v
    c = np.zeros(n + 1)
    c[-1] = -1
    A_ub = np.hstack([-A.T, np.ones((n, 1))])
    b_ub = np.zeros(n)
    A_eq = np.ones((1, n + 1))
    A_eq[0, -1] = 0
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=[1], bounds=[(0, 1)] * n + [(None, None)])
    return {names[i]: float(res.x[i]) for i in range(n)}


def table(rs):
    names = list(DECKS)
    win = {a: {b: [0.0, 0] for b in names} for a in names}
    for r in rs:
        a, b = r["a"], r["b"]
        s = 1.0 if r["w"] == 0 else (0.5 if r["w"] is None else 0.0)
        win[a][b][0] += s
        win[a][b][1] += 1
        if a != b:
            win[b][a][0] += 1 - s
            win[b][a][1] += 1
    M = {a: {b: (win[a][b][0] / win[a][b][1] if win[a][b][1] else 0.5) for b in names} for a in names}
    for a in names:
        M[a][a] = 0.5
    return M, win


def show(rs, title=""):
    names = list(DECKS)
    M, win = table(rs)
    n = len(rs)
    per = win[names[0]][names[1]][1]
    print(f"【総当たり】{title}各組{per}戦（先攻・後攻は半分ずつ）。行のデッキが列のデッキに勝つ割合（%）")
    print("　｜" + "｜".join(SHORT[b] for b in names) + "｜平均｜現実の使用数で重みづけ")
    tot = sum(REAL_USAGE.values())
    for a in names:
        avg = sum(M[a][b] for b in names if b != a) / (len(names) - 1)
        wr = sum(M[a][b] * REAL_USAGE[b] for b in names) / tot
        print(f"{SHORT[a]}｜" + "｜".join("—" if a == b else f"{M[a][b] * 100:.0f}" for b in names) + f"｜{avg * 100:.0f}｜{wr * 100:.0f}")
    eq = nash(M, names)
    print("\n【使用率】釣り合いの取れた配分（シミュレーション）と、超CSⅨ新潟の予選突破者の使用数（7デッキ内の割合）")
    for a in names:
        print(f"  {SHORT[a]}｜釣り合い {eq[a] * 100:.0f}%｜現実 {REAL_USAGE[a] / tot * 100:.0f}%（{REAL_USAGE[a]}人）")
    wf = sum(r["w"] == r["first"] for r in rs) / n
    turns = {}
    for r in rs:
        t = min(r["turn"], 8)
        turns[t] = turns.get(t, 0) + 1
    how = {}
    for r in rs:
        how[r["how"]] = how.get(r["how"], 0) + 1
    print(f"\n【流れ】{n}戦")
    print(f"  先攻の勝率 {wf * 100:.0f}%／決着の平均 {sum(r['turn'] for r in rs) / n:.1f}ターン目")
    print("  決着ターン：" + "、".join(f"{t}{'以降' if t == 8 else ''}ターン目 {turns[t] / n * 100:.0f}%" for t in sorted(turns)))
    print("  決着の形：" + "、".join(f"{k} {v / n * 100:.0f}%" for k, v in sorted(how.items(), key=lambda kv: -kv[1])))
    print(f"  盾からの受けが1回以上あった対戦 {sum(1 for r in rs if sum(r['trig']) > 0) / n * 100:.0f}%"
          f"／負けた側の受けが出た対戦 {sum(1 for r in rs if r['w'] is not None and r['trig'][1 - r['w']] > 0) / n * 100:.0f}%")
    print("\n【デッキごと】勝った対戦の決着ターン／はじめて相手プレイヤーを攻撃したターン／攻撃できたのに攻撃しなかったターンの割合")
    for a in names:
        wt, fa, hold, att, wn = [], [], 0, 0, 0
        loops = 0
        for r in rs:
            for i, d in enumerate((r["a"], r["b"])):
                if d != a:
                    continue
                if r["w"] == i:
                    wt.append(r["turn"])
                    wn += 1
                    loops += r["how"] in ("ループ", "シャコガイル", "山札切れ")
                if r["fa"][i]:
                    fa.append(r["fa"][i])
                hold += r["hold"][i]
                att += r["atkt"][i]
        d3 = sum(1 for t in wt if t <= 3) / max(1, len(wt))
        d4 = sum(1 for t in wt if t <= 4) / max(1, len(wt))
        print(f"  {SHORT[a]}｜勝ちの平均 {sum(wt) / max(1, len(wt)):.1f}ターン目（3ターン目まで {d3 * 100:.0f}%、4ターン目まで {d4 * 100:.0f}%）"
              f"｜初攻撃 {sum(fa) / max(1, len(fa)):.1f}ターン目｜見送り {hold / max(1, hold + att) * 100:.0f}%"
              f"｜殴らない勝ち {loops / max(1, wn) * 100:.0f}%")
    return M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=40)
    ap.add_argument("--budget", type=int, default=600)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--policy", default=None)
    ap.add_argument("--mirror", action="store_true", help="同じデッキどうしも打つ")
    ap.add_argument("--out", default="matrix3.json")
    ap.add_argument("--show", default=None)
    x = ap.parse_args()
    if x.show:
        d = json.load(open(x.show, encoding="utf-8"))
        show(d["games"], f"探索{d['budget']}回・")
        return
    names = list(DECKS)
    pol = json.load(open(x.policy, encoding="utf-8")) if x.policy else {}
    jobs = []
    for ia, a in enumerate(names):
        for ib, b in enumerate(names):
            if ib < ia or (ib == ia and not x.mirror):
                continue
            for g in range(x.games):
                jobs.append((a, b, x.seed * 1000003 + (ia * 7 + ib) * 1009 + g, g % 2, x.budget, pol))
    t0 = time.time()
    with Pool(x.procs) as pool:
        rs = pool.map(one, jobs, chunksize=1)
    json.dump({"budget": x.budget, "policy": x.policy, "games": rs}, open(x.out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(jobs)}戦 {time.time() - t0:.0f}秒 → {x.out}\n")
    show(rs, f"探索{x.budget}回・")


if __name__ == "__main__":
    main()
