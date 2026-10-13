#!/usr/bin/env python3
"""難しいデッキ（コンボ）が、上手い人の手に少数だけ残れるか？ を直接はかる

進化の中でコンボが消えたあとの環境（runs3/f_diffF_s*.json の最終世代）に、よくできたコンボデッキを
1つだけ持ち込み、使い手の腕を変えて勝率をはかる。
さらに、環境側のデッキから「踏み倒し封じ」を抜いた場合（＝少数だから狙われない、という状況）も同じようにはかる。

  python ceiling3.py
"""
import glob
import json
import random

import engine
from cards import deck_difficulty
from engine import Game
from evolve3 import pilot_err
from seeds import SEEDS

K = 2.0
GAMES = 30


def unclosed(counts):
    """踏み倒し封じを、同じコストの小型アタッカーに替える"""
    c = dict(counts)
    n = c.pop("m_free", 0) + c.pop("m_free_p", 0)
    if n:
        c["b1"] = c.get("b1", 0) + n
    return c


def winrate(deck, skill, field, rng):
    d = deck_difficulty(deck[0])
    w = n = 0
    for opp in field:
        d_op = deck_difficulty(opp[0])
        for g in range(GAMES):
            errs = (pilot_err(K, d, skill), pilot_err(K, d_op, rng.random()))
            r = Game(deck, opp, rng, first=g % 2, errs=errs).play()
            w += 1 if r == "A" else (0.5 if r is None else 0)
            n += 1
    return w / n


def main():
    engine.CHAIN_NEED, engine.LOOP_MANA = 3, 4
    rng = random.Random(7)
    # 持ち込むコンボ：基本条件の進化で一番成績のよかったコンボデッキ3つ＋純粋な連鎖・ループ
    cands = []
    for p in glob.glob("runs3/f_base_s*.json"):
        for d in json.load(open(p, encoding="utf-8"))["final"]:
            if {"CHAIN", "LOOP"} & set(d["paths"]):
                cands.append((d["fitness"], p, d))
    cands.sort(key=lambda x: -x[0])
    combos, seen = [], set()
    for f, p, d in cands:
        if p not in seen:
            combos.append((f"進化で生まれたコンボ（{'・'.join(d['paths'])}／封殺 {'・'.join(d['closures']) or 'なし'}）",
                           (d["counts"], d["aggr"])))
            seen.add(p)
        if len(combos) == 3:
            break
    combos.append(("純粋な連鎖", SEEDS["連鎖の特殊勝利"]))
    combos.append(("純粋な呪文ループ", SEEDS["呪文ループ"]))

    metas = []
    for p in sorted(glob.glob("runs3/f_diffF_s*.json")):
        metas.append([(d["counts"], d["aggr"]) for d in json.load(open(p, encoding="utf-8"))["final"]])
    print(f"環境：難しさを入れてコンボが消えたあとの最終世代 {len(metas)}つ（各32デッキ）。相手の腕はばらばら。")
    print("持ち込むデッキ｜難しさ｜そのままの環境での勝率：腕0.1／0.5／0.9／1.0｜踏み倒し封じを抜いた環境での勝率：腕0.1／0.5／0.9／1.0")
    for name, deck in combos:
        rows = {False: [], True: []}
        for open_ in (False, True):
            for sk in (0.1, 0.5, 0.9, 1.0):
                v = []
                for m in metas:
                    field = [((unclosed(c) if open_ else c), a) for c, a in m]
                    v.append(winrate(deck, sk, field, rng))
                rows[open_].append(sum(v) / len(v))
        fmt = lambda xs: "／".join(f"{x * 100:.0f}%" for x in xs)
        print(f"  {name}｜{deck_difficulty(deck[0]):.2f}｜{fmt(rows[False])}｜{fmt(rows[True])}")
    # 参考：環境の中のデッキ自身の平均（定義上およそ50%）と上位の成績
    tops = []
    for p in sorted(glob.glob("runs3/f_diffF_s*.json")):
        f = json.load(open(p, encoding="utf-8"))["final"]
        tops.append(sum(d["fitness"] for d in f[:8]) / 8)
    print(f"参考：環境の中の成績上位1/4の平均 {sum(tops) / len(tops) * 100:.0f}%（環境外デッキとの対戦を含む成績）")


if __name__ == "__main__":
    main()
