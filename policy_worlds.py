#!/usr/bin/env python3
"""「判断＋その判断のもとで進化したデッキ」どうしを戦わせる

policy_duel.py は同じデッキで判断だけを替えた比較。ここでは、デッキもそれぞれの判断に合わせて進化させたものを使う。

  チーム = （どちらの判断のもとで進化したデッキか）×（どちらの判断で動かすか）の4つ
    元デッキ×元の判断 ／ 元デッキ×大会型 ／ 大会デッキ×元の判断 ／ 大会デッキ×大会型

  python policy_worlds.py
"""
import glob
import json
import math
import random

import engine
from cards import BY_KEY
from engine import PRO, Game

GAMES = 16


def tops(pattern, per_run=2):
    out = []
    for p in sorted(glob.glob(pattern)):
        seen = set()
        for d in json.load(open(p, encoding="utf-8"))["final"]:
            if d["signature"] not in seen:
                seen.add(d["signature"])
                out.append(d)
            if len(seen) == per_run:
                break
    return out


def match(da, pa, db, pb, rng, games=GAMES):
    w = n = 0
    for a in da:
        for b in db:
            for g in range(games):
                r = Game((a["counts"], a["aggr"]), (b["counts"], b["aggr"]), rng, first=g % 2, policies=(pa, pb)).play()
                if r:
                    n += 1
                    w += r == "A"
    return w, n


def describe(ds):
    n = len(ds)
    trig = sum(d["triggers"] for d in ds) / n
    clos = sum(len(d["closures"]) for d in ds) / n
    aggr = sum(d["aggr"] for d in ds) / n
    big = sum(sum(v for k, v in d["counts"].items() if BY_KEY[k].kind == "creature" and BY_KEY[k].breaks >= 2) for d in ds) / n
    small = sum(sum(v for k, v in d["counts"].items() if BY_KEY[k].kind == "creature" and BY_KEY[k].breaks == 1) for d in ds) / n
    sa = sum(sum(v for k, v in d["counts"].items() if BY_KEY[k].sa) for d in ds) / n
    return (f"トリガー{trig:.1f}枚｜封殺{clos:.1f}種類｜毎ターン殴る方針{aggr * 100:.0f}%｜2枚以上割るクリーチャー{big:.1f}枚"
            f"｜1枚割るクリーチャー{small:.1f}枚｜出たターンに殴れる{sa:.1f}枚")


def world(title, sim_pat, pro_pat, rng):
    ds, dp = tops(sim_pat), tops(pro_pat)
    if not ds or not dp:
        print(f"{title}：結果がまだない")
        return
    print(f"\n===== {title}（各{len(ds)}デッキ・テンポ2）=====")
    print("  元デッキ（元の判断のもとで進化）：" + describe(ds))
    print("  大会デッキ（大会型の判断のもとで進化）：" + describe(dp))
    teams = [("元デッキ×元の判断", ds, None), ("元デッキ×大会型", ds, PRO),
             ("大会デッキ×元の判断", dp, None), ("大会デッキ×大会型", dp, PRO)]
    print("  行のチームが列のチームに勝つ割合")
    print("  ｜" + "｜".join(t[0] for t in teams) + "｜平均（ほかの3チームに対して）")
    for i, (na, da, pa) in enumerate(teams):
        cells, tot = [], []
        for j, (nb, db, pb) in enumerate(teams):
            if i == j:
                cells.append("—")
                continue
            w, n = match(da, pa, db, pb, rng)
            cells.append(f"{w / n * 100:.0f}%")
            tot.append(w / n)
        print(f"  {na}｜" + "｜".join(cells) + f"｜{sum(tot) / len(tot) * 100:.0f}%")
    w, n = match(ds, None, dp, PRO, rng, games=40)
    p = w / n
    print(f"  本命の比較：元デッキ×元の判断 が 大会デッキ×大会型 に勝つ割合 {p * 100:.1f}%（±{1.96 * math.sqrt(p * (1 - p) / n) * 100:.1f}・{n}戦）")


def main():
    engine.TEMPO = 2
    rng = random.Random(21)
    world("ドギ逆型あり", "runs4/v_t2_s*.json", "runs4/p_t2_s*.json", rng)
    world("ドギ逆型なし", "runs4/v_t2_nolock_s*.json", "runs4/p_t2_nolock_s*.json", rng)
    engine.TEMPO = 0


if __name__ == "__main__":
    main()
