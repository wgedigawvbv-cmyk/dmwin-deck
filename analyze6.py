#!/usr/bin/env python3
"""第2版（カードプールとデッキタイプを増やした世界）の条件比較

  python analyze6.py            runs6/ の結果をまとめる
"""
import glob
import json
import os
import statistics as stt
from collections import Counter, defaultdict

from cards2 import BY_KEY, COLOR_JA, PATH_JA, deck_colors

LABEL = {
    "free_t1": "性質は進化が選ぶ（テンポ1）",
    "free_t0": "性質は進化が選ぶ（テンポ0）",
    "wait_t1": "全員「待つ」に固定（テンポ1）",
    "aggr_t1": "全員「毎ターン動く」に固定（テンポ1）",
    "pro_t1": "全員が大会型の判断（テンポ1）",
}
LAST = 20


def load():
    rows = defaultdict(list)
    for path in sorted(glob.glob("runs6/*_s*.json")):
        name = os.path.basename(path).rsplit("_s", 1)[0]
        run = json.load(open(path, encoding="utf-8"))
        h = run["history"][-LAST:]
        avg = lambda k: sum(x[k] for x in h) / len(h)
        r = {k: avg(k) for k in ("wait_share", "wait_top", "combo_share", "closures_mean", "types", "top_type", "triggers",
                                 "gstrike", "handdef", "multi", "win_turn", "by3", "by4", "clean", "trig", "hand", "meta3",
                                 "wait_win")}
        for p in h[0]["main_share"]:
            r["m_" + p] = sum(x["main_share"][p] for x in h) / len(h)
        for p in h[0]["win_path"]:
            r["w_" + p] = sum(x["win_path"][p] for x in h) / len(h)
        final = run["final"]
        r["ncol"] = sum(len(deck_colors(d["counts"])) for d in final) / len(final)
        r["main_final"] = Counter(d["main"] for d in final).most_common(1)[0][0]
        r["cards"] = Counter()
        for d in final:
            for k, v in d["counts"].items():
                r["cards"][k] += v / len(final)
        rows[name].append(r)
    return rows


def f(vals, scale=1, nd=1, suffix=""):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "-"
    mu = stt.mean(vals) * scale
    sd = stt.stdev(vals) * scale if len(vals) > 1 else 0
    return f"{mu:.{nd}f}{suffix}±{sd:.{nd}f}"


def main():
    rows = load()
    print("各条件、乱数を変えた回の平均±ばらつき。最後の20世代の平均（対戦の数字は、環境の中のデッキどうしの対戦）")
    print("\n[A] 進化は「待つ」を選ぶか／デッキタイプは分かれるか")
    print("条件｜回数｜待つデッキの割合（成績上位1/4）｜1割以上いるデッキタイプの数｜一番多いタイプの割合"
          "｜最終世代で一番多かったタイプ（回数）｜殴らずに勝つ経路を持つ割合｜デッキの色の数")
    for name, lab in LABEL.items():
        if name not in rows:
            continue
        g = lambda k: [x[k] for x in rows[name]]
        mains = Counter(g("main_final"))
        mtxt = "、".join(f"{PATH_JA.get(k, k)}{v}" for k, v in mains.most_common())
        print(f"  {lab}｜{len(rows[name])}｜{f(g('wait_share'), 100, 0, '%')}（{f(g('wait_top'), 100, 0, '%')}）｜{f(g('types'))}"
              f"｜{f(g('top_type'), 100, 0, '%')}｜{mtxt}｜{f(g('combo_share'), 100, 0, '%')}｜{f(g('ncol'))}")
    print("\n[B] 対戦の流れ")
    print("条件｜勝ったターンの平均｜3ターン目までに決着｜4ターン目までに決着｜盾5枚からの1ターンキル"
          "｜盾からの受けが効いた対戦｜手札からの受けが効いた対戦｜3ターン目の終わりの封殺（1人あたり）")
    for name, lab in LABEL.items():
        if name not in rows:
            continue
        g = lambda k: [x[k] for x in rows[name]]
        print(f"  {lab}｜{f(g('win_turn'))}｜{f(g('by3'), 100, 0, '%')}｜{f(g('by4'), 100, 0, '%')}｜{f(g('clean'), 100, 0, '%')}"
              f"｜{f(g('trig'), 100, 0, '%')}｜{f(g('hand'), 100, 0, '%')}｜{f(g('meta3'), 1, 1, '枚')}")
    print("  参考（公式カバレージ約47戦）：ターンが書かれた25戦のうち3ターン目8・4ターン目8・5〜6ターン目4・7ターン目以降5。"
          "トリガーが勝敗か延命に関わったのは9戦前後。先置きのメタは1枚が普通。")
    print("\n[C] デッキの中身（1デッキあたりの平均枚数・種類数）")
    print("条件｜S・トリガー｜G・ストライク｜手札からの受け｜封殺の種類数｜複数の働きを持つメタ")
    for name, lab in LABEL.items():
        if name not in rows:
            continue
        g = lambda k: [x[k] for x in rows[name]]
        print(f"  {lab}｜{f(g('triggers'))}｜{f(g('gstrike'))}｜{f(g('handdef'))}｜{f(g('closures_mean'))}｜{f(g('multi'))}")
    print("\n[D] よく使われたカード（最終世代・全回の平均で1デッキ2枚以上）")
    for name, lab in LABEL.items():
        if name not in rows:
            continue
        tot = Counter()
        for x in rows[name]:
            for k, v in x["cards"].items():
                tot[k] += v / len(rows[name])
        top = [(k, v) for k, v in tot.most_common() if v >= 2.0]
        print(f"  {lab}｜" + "、".join(f"{BY_KEY[k].name}（{COLOR_JA[BY_KEY[k].color]}）{v:.1f}" for k, v in top))


if __name__ == "__main__":
    main()
