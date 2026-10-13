#!/usr/bin/env python3
"""大会の行動ロジック 対 シミュレーターの行動ロジック

同じデッキの組み合わせで、片方を「大会型」、もう片方を「シミュレーター型」の判断で動かし、席と先攻後攻を
入れ替えて戦わせる。デッキの強さの差は打ち消されるので、残るのは判断の差だけになる。

大会型の判断（公式カバレージから読み取った型。engine.POLICY_FLAGS）
  hold    : 1ターンで決める（リーサルが見えるまで殴らない）
  onemeta : メタは1枚だけ先置きして、あとは自分の動きを優先する
  clear   : 受けを消してから殴る（リーサルのターンにトリガー封じを出す／ブロッカーを除去する）
  save    : 除去を温存する

  python policy_duel.py            全部（2〜3分）
"""
import glob
import json
import math
import random
from collections import Counter

import engine
from engine import PRO, Game
from seeds import LOCK_SEED, SEEDS

GAMES = 60   # 1つの組み合わせ・1つの席割りあたりの対戦数


def evolved(pattern, per_run=2):
    """進化した環境の上位デッキ（各回から、型の違うものを per_run 個）"""
    out = []
    for p in sorted(glob.glob(pattern)):
        seen = set()
        for d in json.load(open(p, encoding="utf-8"))["final"]:
            if d["signature"] not in seen:
                seen.add(d["signature"])
                out.append((d["counts"], d["aggr"]))
            if len(seen) == per_run:
                break
    return out


def duel(decks, pol_x, pol_y, rng, games=GAMES):
    """すべての組み合わせ（同じデッキどうしを含む）で、方針 X の側の勝率を返す。
    戻り値：(X の勝ち, 決着した対戦数, 攻撃的なデッキを X が持ったときの勝ち/数, 待つデッキを X が持ったときの勝ち/数)"""
    w = n = 0
    by = {1: [0, 0], 0: [0, 0]}
    for i in range(len(decks)):
        for j in range(i, len(decks)):
            for g in range(games):
                # g の偶奇で、X が持つデッキと先攻後攻を入れ替える
                xa = (g // 2) % 2 == 0
                a, b = decks[i], decks[j]
                gm = Game(a, b, rng, first=g % 2, policies=(pol_x, pol_y) if xa else (pol_y, pol_x))
                r = gm.play()
                if r is None:
                    continue
                xwin = (r == "A") == xa
                w += xwin
                n += 1
                aggr = (a if xa else b)[1]
                by[aggr][0] += xwin
                by[aggr][1] += 1
    return w, n, by


def pct(w, n):
    p = w / n
    se = math.sqrt(p * (1 - p) / n)
    return f"{p * 100:.1f}%（±{1.96 * se * 100:.1f}）"


def flow(decks, pol, rng, games=12):
    """同じ方針どうしで戦わせたときの流れ：勝ったターン、4ターン目までの決着、無傷からの1ターンキル、
    3ターン目の終わりに場にある封殺の枚数（1人あたり）、トリガーが発動した回数（1戦あたり）"""
    turns, by4, clean, metas, trig, n = 0, 0, 0, 0, 0, 0
    for i in range(len(decks)):
        for j in range(i, len(decks)):
            for g in range(games):
                log = []
                gm = Game(decks[i], decks[j], rng, first=g % 2, policies=(pol, pol), log=log)
                r = gm.play()
                if r is None:
                    continue
                n += 1
                turns += gm.round
                by4 += gm.round <= 4
                loser = "B" if r == "A" else "A"
                # 最後のターンが始まる前に、負けた側の盾が5枚以上残っていたか
                before = log[-2]["state"][loser]["shields"] if len(log) >= 2 else 5
                clean += (before >= 5 and gm.win_path in ("ATTACK", "SWAP"))
                t3 = [t for t in log if t["round"] == 3]
                if t3:
                    st = t3[-1]["state"]
                    metas += sum(len(u["closes"]) > 0 for side in ("A", "B") for u in st[side]["board"]) / 2
                trig += sum(e["tag"] == "trigger" for t in log for e in t["events"])
    return turns / n, by4 / n, clean / n, metas / n, trig / n


def main():
    engine.TEMPO = 2
    pools = {
        "純粋な型7つ": list(SEEDS.values()) + [LOCK_SEED],
        "進化した上位（ドギ逆型あり）": evolved("runs4/v_t2_s*.json"),
        "進化した上位（ドギ逆型なし）": evolved("runs4/v_t2_nolock_s*.json"),
    }
    variants = [("大会型（4つ全部）", PRO)] + [(f"{k} だけ", frozenset([k])) for k in engine.POLICY_FLAGS] \
        + [(f"{k} 以外の3つ", PRO - {k}) for k in engine.POLICY_FLAGS]
    print("【1】大会型 対 シミュレーター型（テンポ2。同じデッキの組を、席と先攻後攻を入れ替えて対戦）")
    print("    数字は大会型の側の勝率（50%なら互角。±は95%の幅）")
    print("方針｜" + "｜".join(pools) + "｜全体｜うち毎ターン殴るデッキを持ったとき｜とどめまで待つデッキを持ったとき")
    for label, pol in variants:
        rng = random.Random(11)
        cells, W, N = [], 0, 0
        BY = {1: [0, 0], 0: [0, 0]}
        for name, decks in pools.items():
            w, n, by = duel(decks, pol, None, rng)
            cells.append(pct(w, n))
            W += w
            N += n
            for k in by:
                BY[k][0] += by[k][0]
                BY[k][1] += by[k][1]
        print(f"  {label}｜" + "｜".join(cells) + f"｜{pct(W, N)}｜{pct(*BY[1])}｜{pct(*BY[0])}")

    print("\n【2】同じ判断どうしで戦わせたときの流れ（テンポ2）")
    print("デッキ｜判断｜勝ったターンの平均｜4ターン目までに決着｜無傷（盾5枚）からの1ターンキル"
          "｜3ターン目の終わりに場にある封殺（1人あたり）｜トリガーの発動（1戦あたり）")
    for name, decks in pools.items():
        for label, pol in (("シミュレーター型", None), ("大会型", PRO)):
            t, b4, cl, m, tr = flow(decks, pol, random.Random(5))
            print(f"  {name}｜{label}｜{t:.1f}｜{b4 * 100:.0f}%｜{cl * 100:.0f}%｜{m:.1f}枚｜{tr:.1f}回")
    print("  参考（公式カバレージ）：ターンが書かれた25戦のうち4ターン目までに決着が16戦。"
          "先置きのメタは1枚が普通。盾5枚のまま迎えた1ターンキルが多い。")

    print("\n【3】テンポを変えても同じか（大会型4つ全部 対 シミュレーター型。純粋な型7つ）")
    for tempo in (0, 1, 2):
        engine.TEMPO = tempo
        w, n, _ = duel(pools["純粋な型7つ"], PRO, None, random.Random(3))
        print(f"  テンポ{tempo}｜{pct(w, n)}")
    engine.TEMPO = 0


if __name__ == "__main__":
    main()
