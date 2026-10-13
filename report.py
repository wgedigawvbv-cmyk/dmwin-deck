#!/usr/bin/env python3
"""進化の結果を、現実で見えた3つの特徴と照らす

  1. 上位デッキが、複数の経路と封殺を混ぜた形になるか（混合）
  2. 上位同士の相性が50%近くに縮むか（圧縮）  ※最初の純粋なデッキ同士と比べる
  3. 勝ち筋が封殺と重なるデッキほど成績が悪いか（窓の重なり）

  python report.py run1.json [run2.json ...]
"""
import json
import sys

from cards import CLOSURE_JA, PATH_JA
from engine import play_match
from evolve import matchup_spread
from seeds import SEEDS

MATCH_GAMES = 400


def pick_distinct(final, k=8):
    """署名（経路＋封殺）が違うものを優先して、上位から k 個選ぶ"""
    out, seen = [], set()
    for d in final:
        if d["signature"] not in seen:
            out.append(d)
            seen.add(d["signature"])
        if len(out) == k:
            return out
    for d in final:
        if d not in out:
            out.append(d)
        if len(out) == k:
            break
    return out


def show(path):
    run = json.load(open(path, encoding="utf-8"))
    h = run["history"]
    print(f"\n======== {path}（{run['args']}）")
    print("世代｜平均の混合度（上位1/4）｜集中度｜経路を持つデッキの割合｜封殺を持つデッキの割合｜平均トリガー枚数")
    step = max(1, len(h) // 8)
    for st in h[::step] + ([h[-1]] if (len(h) - 1) % step else []):
        ps = " ".join(f"{PATH_JA[p]}{v * 100:.0f}" for p, v in st["path_share"].items() if v > 0)
        cs = " ".join(f"{CLOSURE_JA[c]}{v * 100:.0f}" for c, v in st["closure_share"].items() if v > 0)
        print(f"  {st['gen']:3d}｜{st['hybrid_mean']:.1f}（{st['hybrid_top']:.1f}）｜{st['concentration']:.2f}｜{ps or '-'}｜{cs or '-'}"
              f"｜{st['triggers_mean']:.1f}")

    top = pick_distinct(run["final"], 8)
    print("\n最終世代の上位デッキ（署名が違うもの）:")
    for d in top:
        ps = "・".join(PATH_JA[p] for p in d["paths"]) or "-"
        cs = "・".join(CLOSURE_JA[c] for c in d["closures"]) or "-"
        print(f"  適応度 {d['fitness']:.2f}｜経路 {ps}｜封殺 {cs}｜トリガー{d['triggers']} 除去{d['removal']} 手札破壊{d['handes']}"
              f"｜{'毎ターン攻撃' if d['aggr'] else 'とどめまで待つ'}")

    decks = [(d["counts"], d["aggr"]) for d in top]
    _, spread_final, max_final = matchup_spread(decks, MATCH_GAMES, seed=77)
    seed_decks = list(SEEDS.values())
    _, spread_seed, max_seed = matchup_spread(seed_decks, MATCH_GAMES, seed=77)
    print(f"\n相性の50%からのずれ（平均／最大）：最初の純粋なデッキ {spread_seed * 100:.1f}／{max_seed * 100:.1f}ポイント"
          f" → 進化後の上位 {spread_final * 100:.1f}／{max_final * 100:.1f}ポイント")
    print("（現実の上位デッキ同士は、決勝の戦い方別成績でおよそ43〜57%＝ずれ7ポイント以内）")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        show(p)
