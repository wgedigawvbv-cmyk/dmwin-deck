"""相手側の「退化をさせてやらない」決まりが、【ユニバース退化】の勝率をどれだけ下げるかを測る

  A（いまの版）  ：VALADJ で s.val / s.target の両方にスター進化の補正が効く
                   → 自分では退化を狙い、相手には退化をさせない
  B（前の版）    ：補正を自分のクリーチャーを捨てる選択（own_loss）だけに限る
                   → 相手は無防備にスター進化を壊してくれる＝無料で退化が起きる
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai3
import engine3 as E
import decks8
import envcards.env0 as env0
from envcards.env0 import STAR

ME = [n for n in decks8.DECKS8 if "ユニバース" in n][0]
OPPS = ["火水闇ジャオウガ", "光自然ロマネスク", "光水自然der'Bande", "GP7 4c ガイアッシュ/ジャオウガ"]
OPPS = [n for n in decks8.DECKS8 if decks8.short(n) in
        ("火水闇ジャオウガ", "光自然ロマネスク", "光水自然der'Bande", "GP7 4c ガイアッシュ/ジ",
         "火光自然「終斗」", "サイバー系", "ジャオウガ系", "4c善悪")]


def run(tag, games, budget):
    w = 0.0
    n = 0
    for i, o in enumerate(OPPS):
        for g in range(games):
            gm = ai3.play_game(decks8.DECKS8[ME], decks8.DECKS8[o], random.Random(1000 + i * 97 + g),
                               g % 2, (budget, budget), names=("*", "*"))
            w += 1.0 if gm.winner == 0 else 0.5 if gm.winner is None else 0.0
            n += 1
    print(f"  {tag}: {w}/{n} = {w / n * 100:.1f}%", flush=True)
    return w / n


games, budget = int(sys.argv[1]), int(sys.argv[2])
print(f"【ユニバース退化】× 相手{len(OPPS)}デッキ × {games}戦（探索{budget}回）")
a = run("A いまの版（相手も退化をさせない）", games, budget)

# B：補正を自分の捨てる選択だけに限る
E.VALADJ.clear()
env0.own_loss = lambda s, i, z: s.val(z) - (E.PRI.get(z.under[0], 0) if z.k in STAR and z.under else 0)
import envcards.env10 as env10
env10.worst_own = env0.worst_own = lambda s, i, pred=None, keep=None: (
    min([z for z in s.P[i].board if z.c.kind == "C" and (pred is None or pred(z))],
        key=lambda z: (env0.own_loss(s, i, z), 0 if z is not keep else 1), default=None))
b = run("B 前の版（相手は無防備に壊す）", games, budget)
print(f"差：{(a - b) * 100:+.1f} ポイント（A − B）")
