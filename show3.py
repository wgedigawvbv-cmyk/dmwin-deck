#!/usr/bin/env python3
"""第3版：1戦の流れを文字で見る

  python show3.py "4c der'Bande" "光自然ウィリデ" --seed 1 --budget 200
"""
import argparse
import random

from ai3 import play_game
from cards3 import BY_KEY, DECKS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--budget", type=int, default=200, help="1手あたりに試す回数")
    ap.add_argument("--first", type=int, default=0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    g = play_game(DECKS[a.a], DECKS[a.b], rng, a.first, (a.budget, a.budget), log=True)
    names = (a.a, a.b)
    last = None
    for turn, tp, msg in g.log:
        if (turn, tp) != last:
            last = (turn, tp)
            n = (turn + 1) // 2
            print(f"\n■ {names[tp]} の{n}ターン目")
        print("  " + msg)
    print()
    for i in (0, 1):
        p = g.P[i]
        print(f"{names[i]}：シールド{len(p.sh)} 手札{len(p.hand)} マナ{len(p.mana)} 山札{len(p.deck)} 場 "
              + "・".join(BY_KEY[u.k].name for u in p.board))
    print(f"結果：{names[g.winner] if g.winner is not None else '引き分け'}（{g.how}）／{(g.turn + 1) // 2}ターン目")


if __name__ == "__main__":
    main()
