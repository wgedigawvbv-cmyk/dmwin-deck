#!/usr/bin/env python3
"""人間 vs dmai で1戦する（チャットでも、手元のPowerShellでも打てる）

  盤面はファイルに保存して持ち越すので、1手ずつ別々に呼び出してよい。

    python duel.py --decks                           相手に選べるデッキの一覧
    python duel.py --new --me 赤零 --ai ジャオウガ --level 上級 --first me
    python duel.py --show                            いまの盤面と、打てる手の番号つき一覧
    python duel.py --move 3                          3番の手を打つ（そのあとAIの手番を進める）
    python duel.py --log                             ここまでの出来事を全部見る

  ・自分の手札・マナ・場は全部見える。相手の手札とシールドの中身は見えない（枚数だけ）。
  ・打てる手が1つしかない場面は自動で進める。
  ・カードの効果の中の選択（除去の対象、捨てる札、S・トリガーで何を使うか、ブロックするか等）は
    **エンジンの全デッキ共通の決まり**（重要度PRIと値打ちval）で自動的に決まる。ここは人間も選べない。
    操縦できるのは「どのカードを使うか・誰で誰を攻撃するか・いつターンを終えるか」まで。
  ・AIは「相手（人間）のデッキリストを知っている」前提で読む（このシミュレーターのこれまでの前提と同じ。
    知らない前提にしたいときは --blind を付けると、AIは別のデッキを信じたまま打つ）。
"""
import argparse
import os
import pickle
import random
import sys

import decks8
import dmai
import engine3
from cards3 import BY_KEY

SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "duel_state.pkl")


def nm(k):
    return BY_KEY[k].name


def pick_deck(q):
    """名前の一部からデッキを1つ選ぶ"""
    ns = sorted(decks8.DECKS8)
    hit = [n for n in ns if q in n or q in decks8.short(n)]
    if not hit:
        raise SystemExit(f"『{q}』に合うデッキがありません。--decks で一覧を見てください")
    if len(hit) > 1:
        exact = [n for n in hit if decks8.short(n) == q]
        if exact:
            hit = exact[:1]
    return hit[0], decks8.DECKS8[hit[0]]


def card_line(k, n=None):
    c = BY_KEY[k]
    civ = "".join({"L": "光", "W": "水", "D": "闇", "F": "火", "N": "自然"}[x] for x in c.civ) or "無色"
    kind = {"C": "", "S": "・呪文", "T": "・タマシード", "G": "・城", "X": "・クロスギア"}.get(c.kind, "")
    pw = f" {c.power}" if c.kind == "C" else ""
    br = {2: " W", 3: " T", 99: " ワールド"}.get(c.brk, "")
    return f"{'×' + str(n) + ' ' if n else ''}{c.name}（{c.cost}・{civ}{kind}{pw}{br}）"


def unit_line(u):
    s = nm(u.k)
    tags = []
    if u.tap:
        tags.append("タップ")
    if u.sick:
        tags.append("出たばかり")
    if u.under:
        tags.append(f"下{len(u.under)}枚")
    if getattr(u, "hyper", False):
        tags.append("ハイパー")
    if getattr(u, "jd", False):
        tags.append("ジャストダイバー")
    return s + (f"[{'・'.join(tags)}]" if tags else "")


def show(st, moves=True):
    g, me = st["g"], st["me"]
    you = 1 - me
    P, O = g.P[me], g.P[you]
    print("=" * 66)
    print(f"{st['myturn_label']}　{dmai.PHASE_JA.get(g.phase, g.phase)}フェイズ　"
          f"手番：{'あなた' if g.tp == me else 'AI'}")
    print("-" * 66)
    print(f"【AI】{st['ai_name']}")
    print(f"  シールド {len(O.sh)}　手札 {len(O.hand)}　山札 {len(O.deck)}　"
          f"マナ {len(O.mana)}（使用済 {O.mused}）")
    print(f"  マナの中身：{'・'.join(nm(k) for k in O.mana) or 'なし'}")
    print(f"  バトルゾーン：{'・'.join(unit_line(u) for u in O.board) or 'なし'}")
    print(f"  墓地 {len(O.grave)}枚")
    print("-" * 66)
    print(f"【あなた】{st['my_name']}")
    print(f"  シールド {len(P.sh)}　山札 {len(P.deck)}　マナ {len(P.mana)}（残り {len(P.mana) - P.mused}）")
    print(f"  マナの中身：{'・'.join(nm(k) for k in P.mana) or 'なし'}")
    print(f"  バトルゾーン：{'・'.join(unit_line(u) for u in P.board) or 'なし'}")
    print(f"  墓地 {len(P.grave)}枚")
    print(f"  手札 {len(P.hand)}枚：")
    for k in sorted(set(P.hand), key=lambda x: (BY_KEY[x].cost, nm(x))):
        print("    " + card_line(k, P.hand.count(k)))
    if g.over:
        print("=" * 66)
        w = "引き分け" if g.winner is None else ("あなたの勝ち" if g.winner == me else "AIの勝ち")
        print(f"★ 決着：{w}（{g.how}／{(g.turn + 1) // 2}ターン）")
        return
    if moves and g.tp == me:
        acts = g.legal()
        print("-" * 66)
        print("打てる手：")
        for i, a in enumerate(acts, 1):
            print(f"  {i:2d}. {dmai.move_ja(g, a)}")
        print(f"\n→ python duel.py --move 番号　（1〜{len(acts)}）")
    print("=" * 66)


def flush_log(st, mark="AIの手番"):
    """前回見せたところから先の出来事を出す"""
    g = st["g"]
    new = g.log[st["seen"]:]
    st["seen"] = len(g.log)
    if not new:
        return
    print(f"── {mark} ──")
    for _t, _i, msg in new:
        print("  " + msg)
    print()


def advance(st):
    """人間が選ぶ場面か、終局まで進める"""
    g, me = st["g"], st["me"]
    brain = st["brain"]
    while not g.over:
        if g.tp == me:
            acts = g.legal()
            if len(acts) > 1:
                return
            print(f"（あなたの手は1つだけなので自動で進めます：{dmai.move_ja(g, acts[0])}）")
            g.apply(acts[0])
            continue
        acts = g.legal()
        a = brain.choose(g)
        if len(acts) > 1:
            st["ai_moves"].append(dmai.move_ja(g, a))
        g.apply(a)


def new_game(args):
    my_name, my_deck = pick_deck(args.me)
    ai_name, ai_deck = pick_deck(args.ai)
    first_me = (args.first == "me")
    rng = random.Random(args.seed)
    # プレイヤー0＝人間
    g = engine3.Game(my_deck, ai_deck, rng, first=0 if first_me else 1, log=True)
    g.hold = [0, 0]
    g.atkt = [0, 0]
    pol = dmai._load_policy(args.policy) if os.path.exists(args.policy) else {}
    kn = dmai.Knowledge()
    if args.blind:                     # AIは相手（人間）のデッキを読み違えている
        others = [n for n in sorted(decks8.DECKS8) if n != my_name]
        kn = dmai.Knowledge(know_opp_list=False, belief=dict(decks8.DECKS8[random.Random(args.seed).choice(others)]))
    brain = dmai.Brain(level=args.level, policy=pol, knowledge=kn,
                       deck_names=(my_name, ai_name), seed=args.seed + 1, me=1)
    st = {"g": g, "me": 0, "brain": brain, "seen": 0, "ai_moves": [],
          "my_name": decks8.short(my_name), "ai_name": decks8.short(ai_name),
          "level": args.level, "blind": args.blind, "myturn_label": ""}
    print(f"あなた：{st['my_name']}　vs　AI：{st['ai_name']}（腕＝{args.level}"
          + ("・相手のデッキを読み違えている設定" if args.blind else "") + ")")
    print(f"先攻：{'あなた' if first_me else 'AI'}　乱数の種：{args.seed}\n")
    return st


def save(st, path):
    with open(path, "wb") as f:
        pickle.dump(st, f)


def load(path):
    if not os.path.exists(path):
        raise SystemExit("対戦が始まっていません。--new で始めてください")
    with open(path, "rb") as f:
        return pickle.load(f)


def label(st):
    g, me = st["g"], st["me"]
    st["myturn_label"] = f"あなたの{g.myturn(me)}ターン目／AIの{g.myturn(1 - me)}ターン目"


def report_ai(st):
    if st["ai_moves"]:
        print("── AIが打った手 ──")
        for m in st["ai_moves"]:
            print("  ・" + m)
        print()
        st["ai_moves"] = []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", default=SAVE)
    ap.add_argument("--new", action="store_true")
    ap.add_argument("--me", default="赤零")
    ap.add_argument("--ai", default="火水闇ジャオウガ")
    ap.add_argument("--level", default="上級")
    ap.add_argument("--first", choices=("me", "ai"), default="me")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--policy", default="runs7/policy3_4.json")
    ap.add_argument("--blind", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--move", type=int)
    ap.add_argument("--log", action="store_true")
    ap.add_argument("--decks", action="store_true")
    a = ap.parse_args()

    if a.decks:
        for n in sorted(decks8.DECKS8):
            print(f"  {decks8.short(n):26s} {n}")
        return
    if a.new:
        st = new_game(a)
        advance(st)
        label(st)
        flush_log(st, "ここまでの出来事")
        report_ai(st)
        show(st)
        save(st, a.save)
        return
    st = load(a.save)
    if a.log:
        for t, i, msg in st["g"].log:
            print(f"[{t}] P{i} {msg}")
        return
    if a.move is not None:
        g = st["g"]
        if g.over:
            raise SystemExit("この対戦はもう終わっています")
        if g.tp != st["me"]:
            raise SystemExit("いまはAIの手番です（--show で確認してください）")
        acts = g.legal()
        if not (1 <= a.move <= len(acts)):
            raise SystemExit(f"番号は 1〜{len(acts)} です")
        chosen = acts[a.move - 1]
        print(f"あなたの手：{dmai.move_ja(g, chosen)}\n")
        st["seen"] = len(g.log)
        g.apply(chosen)
        advance(st)
        label(st)
        flush_log(st, "起きたこと")
        report_ai(st)
        show(st)
        save(st, a.save)
        return
    label(st)
    show(st)


if __name__ == "__main__":
    main()
