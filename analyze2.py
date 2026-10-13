#!/usr/bin/env python3
"""条件ごとの比較：現実で見えた特徴にどこまで近づいたか"""
import glob
import json
import statistics as stt
from collections import defaultdict

from engine import play_match
from report import pick_distinct

LABEL = {
    "base": "基本（前回と同じ）",
    "off": "環境外デッキあり",
    "offunk": "環境外あり＋正体が分からない",
    "bias": "思い込み5つ（環境外なし）",
    "all": "全部入り",
    "ou_copy": "環境外＋不明＋模倣",
    "ou_playset": "環境外＋不明＋4枚積み",
    "ou_metaread": "環境外＋不明＋前週メタ読み",
    "ou_flashy": "環境外＋不明＋派手なカード偏重",
    "ou_trigmin": "環境外＋不明＋トリガー最低8枚",
}


def dist(a, b):
    keys = set(a) | set(b)
    return sum(abs(a.get(k, 0) - b.get(k, 0)) for k in keys) / 80


def compression(final, games=300, seed=5):
    top = pick_distinct(final, 8)
    decks = [(d["counts"], d["aggr"]) for d in top]
    far, near, ds = [], [], []
    for i in range(len(decks)):
        for j in range(i + 1, len(decks)):
            w, _, _ = play_match(decks[i], decks[j], games, seed=seed + i * 17 + j)
            dd = dist(decks[i][0], decks[j][0])
            ds.append(dd)
            (far if dd >= 0.4 else near).append(abs(w - 0.5))
    m = lambda x: (sum(x) / len(x)) if x else None
    return m(far + near), m(far), len(far), m(ds)


def summarize():
    rows = defaultdict(list)
    for path in sorted(glob.glob("runs/*_s*.json")):
        name = path.split("/")[-1].rsplit("_s", 1)[0]
        run = json.load(open(path, encoding="utf-8"))
        h = run["history"][-20:]
        avg = lambda k: sum(x[k] for x in h) / len(h)
        comp_all, comp_far, n_far, mdist = compression(run["final"])
        rows[name].append({
            "combo": avg("combo_share"), "combo_top": avg("combo_top"),
            "trig": avg("triggers_mean"), "trig_top": avg("triggers_top"),
            "hybrid": avg("hybrid_mean"), "conc": avg("concentration"),
            "off_wr": avg("offmeta_wr") if h[0]["offmeta_wr"] is not None else None,
            "comp": comp_all, "comp_far": comp_far, "n_far": n_far, "dist": mdist,
        })
    return rows


def fmt(vals, scale=1, nd=0, suffix=""):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "-"
    mu = stt.mean(vals) * scale
    sd = (stt.stdev(vals) * scale) if len(vals) > 1 else 0
    return f"{mu:.{nd}f}{suffix}±{sd:.{nd}f}"


def main():
    rows = summarize()
    print("各条件 3回（乱数違い）の平均±ばらつき。最後の20世代の平均と、最終世代の上位8デッキの総当たり（各300戦）")
    print("条件｜コンボ経路を持つ割合（上位1/4）｜トリガー枚数（上位1/4）｜混合度｜集中度｜環境外への勝率｜"
          "相性のずれ（似ていない組み合わせ）｜上位8の平均の違い")
    for name in LABEL:
        if name not in rows:
            continue
        r = rows[name]
        g = lambda k: [x[k] for x in r]
        print(f"{LABEL[name]}｜{fmt(g('combo'), 100, 0, '%')}（{fmt(g('combo_top'), 100, 0, '%')}）"
              f"｜{fmt(g('trig'), 1, 1)}（{fmt(g('trig_top'), 1, 1)}）｜{fmt(g('hybrid'), 1, 1)}｜{fmt(g('conc'), 1, 2)}"
              f"｜{fmt(g('off_wr'), 100, 0, '%')}｜{fmt(g('comp'), 100, 1)}（{fmt(g('comp_far'), 100, 1)}・{sum(g('n_far'))}組）"
              f"｜{fmt(g('dist'), 1, 2)}")
    print("\n現実の目安：コンボ系の入賞 約15%／上位のトリガーは少ない（ザゼゼーン等はほぼ0）／上位は経路と封殺の混合"
          "／トップデッキの入賞シェア約19%・上位7で約6割（集中度0.1前後に相当）／上位同士の相性のずれ 7ポイント以内")


if __name__ == "__main__":
    main()
