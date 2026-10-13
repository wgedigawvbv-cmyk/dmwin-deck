#!/usr/bin/env python3
"""v4 の条件比較：テンポ（速さ）と「封殺の完了」を入れた世界

  python analyze4.py            runs4/ の結果をまとめる
"""
import glob
import json
import os
import statistics as stt
from collections import defaultdict

LABEL = {
    "v_t0": "テンポ0（これまでの速さ）",
    "v_t1": "テンポ1",
    "v_t2": "テンポ2",
    "v_t1_nolock": "テンポ1・一手封殺なし",
    "v_t2_nolock": "テンポ2・一手封殺なし",
    "v_t2_sup8": "テンポ2＋トリガー抑制0.8",
    "v_t2_fast": "テンポ2＋コンボ速い",
    "v_t2_fast_diff": "テンポ2＋コンボ速い＋難しさ・慣れ・試し回し",
}
LAST = 20
GRP = {"t_stop": "g_ins", "t_tap": "g_ins", "t_remove": "g_dual", "t_wipe": "g_dual", "t_block": "g_tcre",
       "t_big": "g_tcre", "removal": "g_rem", "wipe": "g_rem", "counter0": "g_c0", "blocker": "g_blk"}


def load():
    rows = defaultdict(list)
    for path in sorted(glob.glob("runs4/*_s*.json")):
        name = os.path.basename(path).rsplit("_s", 1)[0]
        run = json.load(open(path, encoding="utf-8"))
        h = run["history"][-LAST:]

        def avg(k):
            v = [x[k] for x in h if x.get(k) is not None]
            return sum(v) / len(v) if v else None

        r = {k: avg(k) for k in ("win_turn", "win3", "win4", "dec3", "dec4", "lock_win", "lock4", "lock_decks",
                                 "combo_share", "triggers_mean", "triggers_top", "closures_mean", "concentration",
                                 "top_type_share", "combo_skill")}
        for c in h[0]["closure_share"]:
            r["cl_" + c] = sum(x["closure_share"][c] for x in h) / len(h)
        for p in h[0]["win_path"]:
            r["wp_" + p] = sum(x["win_path"][p] for x in h) / len(h)
        final = run["final"]
        comp = defaultdict(float)
        for d in final:
            for k, v in d["counts"].items():
                if k in GRP:
                    comp[GRP[k]] += v / len(final)
        for g in set(GRP.values()):
            r[g] = comp[g]
        r["aggr"] = sum(d["aggr"] for d in final) / len(final)
        rows[name].append(r)
    return rows


def f(vals, scale=1, nd=1, suffix=""):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "-"
    mu = stt.mean(vals) * scale
    sd = stt.stdev(vals) * scale if len(vals) > 1 else 0
    return f"{mu:.{nd}f}{suffix}±{sd:.{nd}f}"


def outcome(vals):
    dom = sum(v >= 0.7 for v in vals)
    ext = sum(v < 0.1 for v in vals)
    return f"独占{dom}・共存{len(vals) - dom - ext}・消滅{ext}"


def main():
    rows = load()
    print("各条件、乱数を変えた回の平均±ばらつき。最後の20世代の平均（環境の中のデッキどうしの対戦）")
    print("\n[A] 決着の速さ")
    print("条件｜回数｜勝ったターンの平均｜3ターン目までに決着｜4ターン目までに決着｜うち4ターン目までに勝ち"
          "｜うち4ターン目までに封殺完了｜勝者が封殺を完了させていた割合")
    for name, lab in LABEL.items():
        if name not in rows:
            continue
        g = lambda k: [x[k] for x in rows[name]]
        print(f"  {lab}｜{len(rows[name])}｜{f(g('win_turn'))}｜{f(g('dec3'), 100, 0, '%')}｜{f(g('dec4'), 100, 0, '%')}"
              f"｜{f(g('win4'), 100, 0, '%')}｜{f(g('lock4'), 100, 0, '%')}｜{f(g('lock_win'), 100, 0, '%')}")
    print("\n[B] 環境の形")
    print("条件｜一手封殺を持つデッキ｜毎ターン殴るデッキの割合（最終世代）｜コンボの使用率（行方）｜集中度｜一番人気の使用率"
          "｜勝ち筋の内訳：攻撃／入れ替え／連鎖／ループ")
    for name, lab in LABEL.items():
        if name not in rows:
            continue
        g = lambda k: [x[k] for x in rows[name]]
        wp = "／".join(f(g("wp_" + p), 100, 0, "%") for p in ("ATTACK", "SWAP", "CHAIN", "LOOP"))
        print(f"  {lab}｜{f(g('lock_decks'), 100, 0, '%')}｜{f(g('aggr'), 100, 0, '%')}｜{f(g('combo_share'), 100, 0, '%')}（{outcome(g('combo_share'))}）"
              f"｜{f(g('concentration'), 1, 2)}｜{f(g('top_type_share'), 100, 0, '%')}｜{wp}")
    print("\n[C] 守りの形")
    print("条件｜トリガー枚数｜純粋な保険のトリガー｜除去を兼ねるトリガー呪文｜クリーチャーが出るトリガー｜0コスト受け｜ブロッカー"
          "｜封殺の種類数｜トリガー封じ｜踏み倒し封じ｜呪文制限｜展開制限（持つデッキの割合）")
    for name, lab in LABEL.items():
        if name not in rows:
            continue
        g = lambda k: [x[k] for x in rows[name]]
        cl = "｜".join(f(g("cl_" + c), 100, 0, "%") for c in ("C_TRIG", "C_FREE", "C_SPELL", "C_SUMMON"))
        print(f"  {lab}｜{f(g('triggers_mean'))}｜" + "｜".join(f(g(k)) for k in ("g_ins", "g_dual", "g_tcre", "g_c0", "g_blk"))
              + f"｜{f(g('closures_mean'))}｜{cl}")
    print("\n目標（現実）：3〜4ターン目には、勝っているか封殺が完了している")


if __name__ == "__main__":
    main()
