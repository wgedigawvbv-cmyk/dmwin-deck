#!/usr/bin/env python3
"""v3 の条件比較：人気・難しさ・封殺によるトリガー抑制が、環境の形をどう変えるか

  python analyze3.py            runs3/ の結果をまとめる
"""
import glob
import json
import statistics as stt
from collections import defaultdict

LABEL = {
    "f_base": "基本",
    "f_pop1": "人気 β=1",
    "f_pop2": "人気 β=2",
    "f_diffR": "難しさ（腕はばらばら）",
    "f_diffF": "難しさ（腕は人に固定）",
    "f_diffF3": "難しさ強め（腕は人に固定）",
    "f_sup4": "トリガー抑制 0.4",
    "f_sup8": "トリガー抑制 0.8",
    "f_pop_diffF": "人気＋難しさ",
    "f_all": "3つ全部",
    "s_base": "基本",
    "s_pop1": "人気 β=1",
    "s_sup4": "トリガー抑制 0.4",
    "s_sup8": "トリガー抑制 0.8",
    "s_diffF": "難しさ（腕は人に固定）",
    "s_all": "3つ全部",
}
LAST = 20


def load():
    rows = defaultdict(list)
    for path in sorted(glob.glob("runs3/*_s*.json")):
        name = path.split("/")[-1].rsplit("_s", 1)[0]
        run = json.load(open(path, encoding="utf-8"))
        h = run["history"][-LAST:]

        def avg(k):
            v = [x[k] for x in h if x.get(k) is not None]
            return sum(v) / len(v) if v else None

        r = {k: avg(k) for k in ("combo_share", "combo_top", "combo_fit", "other_fit", "combo_skill", "triggers_mean",
                                 "triggers_top", "closures_mean", "hybrid_mean", "concentration", "difficulty_mean",
                                 "difficulty_top", "skill_vs_difficulty", "share_vs_strength", "top_type_share",
                                 "top_type_gap")}
        for c in h[0]["closure_share"]:
            r["cl_" + c] = sum(x["closure_share"][c] for x in h) / len(h)
        rows[name].append(r)
    return rows


def f(vals, scale=1, nd=1, suffix="", sign=False):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "-"
    mu = stt.mean(vals) * scale
    sd = stt.stdev(vals) * scale if len(vals) > 1 else 0
    return f"{mu:{'+' if sign else ''}.{nd}f}{suffix}±{sd:.{nd}f}"


def outcome(vals):
    dom = sum(v >= 0.7 for v in vals)
    ext = sum(v < 0.1 for v in vals)
    return f"独占{dom}・共存{len(vals) - dom - ext}・消滅{ext}"


def table(rows, prefix, title):
    print(f"\n===== {title} =====")
    print("（各条件、乱数を変えた回の平均±ばらつき。最後の20世代の平均）")
    print("\n[A] 環境の形")
    print("条件｜回数｜コンボの使用率｜コンボの行方（使用率7割以上＝独占／1割未満＝消滅）｜集中度｜一番人気の使用率"
          "｜一番人気の成績 − ほかの平均｜使用率と成績の順位相関")
    for name, lab in LABEL.items():
        if not name.startswith(prefix) or name not in rows:
            continue
        g = lambda k: [x[k] for x in rows[name]]
        print(f"  {lab}｜{len(rows[name])}｜{f(g('combo_share'), 100, 0, '%')}｜{outcome(g('combo_share'))}｜{f(g('concentration'), 1, 2)}"
              f"｜{f(g('top_type_share'), 100, 0, '%')}｜{f(g('top_type_gap'), 100, 1, 'pt', True)}｜{f(g('share_vs_strength'), 1, 2, '', True)}")
    print("\n[B] 守りの形")
    print("条件｜トリガー枚数（成績上位1/4）｜封殺の種類数｜トリガー封じ｜踏み倒し封じ｜呪文制限｜攻撃制限｜展開制限（持つデッキの割合）")
    for name, lab in LABEL.items():
        if not name.startswith(prefix) or name not in rows:
            continue
        g = lambda k: [x[k] for x in rows[name]]
        cl = "｜".join(f(g("cl_" + c), 100, 0, "%") for c in ("C_TRIG", "C_FREE", "C_SPELL", "C_ATTACK", "C_SUMMON"))
        print(f"  {lab}｜{f(g('triggers_mean'))}（{f(g('triggers_top'))}）｜{f(g('closures_mean'))}｜{cl}")
    print("\n[C] 難しさと腕")
    print("条件｜デッキの難しさの平均（成績上位1/4）｜コンボを使う人の腕の平均（全体は0.5）｜腕と難しさの順位相関"
          "｜コンボの成績｜それ以外の成績")
    for name, lab in LABEL.items():
        if not name.startswith(prefix) or name not in rows:
            continue
        g = lambda k: [x[k] for x in rows[name]]
        print(f"  {lab}｜{f(g('difficulty_mean'), 1, 2)}（{f(g('difficulty_top'), 1, 2)}）｜{f(g('combo_skill'), 1, 2)}"
              f"｜{f(g('skill_vs_difficulty'), 1, 2, '', True)}｜{f(g('combo_fit'), 100, 0, '%')}｜{f(g('other_fit'), 100, 0, '%')}")


def main():
    rows = load()
    table(rows, "f_", "コンボが速い設定（連鎖に必要な数3・ループに必要なマナ4）")
    table(rows, "s_", "コンボが標準の速さ（連鎖4・ループ5）")
    print("\n現実の目安：コンボ系の入賞 約15%／上位のトリガーは少ない／トップの入賞シェア約19%（集中度0.1前後）"
          "／使用の多さと勝ち上がり率の順位相関 約+0.36／一番多い生徒会は勝ち上がり率21%（平均以下）、"
          "少数のドロマーシーザーは43%")


if __name__ == "__main__":
    main()
