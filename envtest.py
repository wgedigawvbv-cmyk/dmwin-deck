#!/usr/bin/env python3
"""新カード（envcards）の動作確認の道具

  effect_smoke(key)  そのカードを手札に持ち、全色のマナがある場面で、使える手をすべて試して例外が出ないかを調べる。
                     返り値：そのカードを使う手を実行できた回数（0なら、どの場面でも使えなかった）
  game_smoke(key, n) そのカードを6枚入れたデッキで、実在デッキと n 戦して、例外が出ないか・そのカードが実際に使われたかを調べる。
                     返り値：(使われた戦の数, 戦数)
  python envtest.py env0        envcards/env0.py の全カードを調べる
"""
import random
import sys
import traceback

import ai3
import engine3
from cards3 import BY_KEY, DECKS

MANA = ["chakra", "chakra", "chakra", "klin", "klin", "klin", "margani", "margani", "margani", "fujin", "fujin", "fujin",
        "dagra", "dagra", "dagra", "kabocha", "klin", "chakra", "margani", "fujin"]


def _setup(key, seed, opp_name=None):
    rng = random.Random(seed)
    names = list(DECKS)
    da = dict(DECKS[names[seed % len(names)]])
    db = dict(DECKS[opp_name or names[(seed + 3) % len(names)]])
    g = engine3.Game(da, db, rng, first=0)
    p, o = g.P[0], g.P[1]
    p.mana = list(MANA)
    p.mused = 0
    p.hand = [key, key] + p.hand[:3]
    o.board = [engine3.U(k) for k in ("klin", "zaze", "dagra")[: 1 + seed % 3]]
    for u in o.board:
        u.sick = False
    p.board = [engine3.U("douki")]
    p.board[0].sick = False
    p.grave = ["artel", "klin", "margani", "dagra", "vamilia", "fujin", "chakra", "jaouga"]
    g.phase = "M"
    return g


def effect_smoke(key, tries=12):
    ok = 0
    for seed in range(tries):
        g = _setup(key, seed)
        for a in g.legal():
            if key in a[1:2] or (len(a) > 1 and a[1] == key):
                h = g.clone()
                h.apply(a)
                ok += 1
                # 続けて最後まで少し進める（攻撃・ターン終了で例外が出ないか）
                for _ in range(40):
                    if h.over:
                        break
                    acts = h.legal()
                    h.apply(acts[min(len(acts) - 1, seed % 3)])
                break
    return ok


def game_smoke(key, n=4, budget=0):
    used = 0
    names = list(DECKS)
    for j in range(n):
        rng = random.Random(100 + j)
        da = dict(DECKS[names[j % len(names)]])
        # 一番多い札を6枚ぶん置き換える
        out = 0
        for k in sorted(da, key=lambda x: -da[x]):
            if out >= 6:
                break
            take = min(da[k], 6 - out)
            da[k] -= take
            out += take
            if not da[k]:
                del da[k]
        da[key] = da.get(key, 0) + 6
        g = ai3.play_game(da, DECKS[names[(j + 2) % len(names)]], rng, j % 2, (budget, budget), log=True,
                          names=("*", "*"), pols=({}, {}))
        nm = BY_KEY[key].name
        if any(nm in m for (_, _, m) in g.log):
            used += 1
    return used, n


def check_module(mod):
    import envcards  # noqa: F401
    import envreg
    import importlib
    m = importlib.import_module(f"envcards.{mod}")
    keys = [k for k in envreg.STATUS if getattr(BY_KEY[k], "key", None) == k]
    bad = 0
    for k in keys:
        try:
            e = effect_smoke(k)
            u, n = game_smoke(k, 3)
            print(f"{'○' if e and u else '△'} {BY_KEY[k].name}：使えた場面 {e}／使われた戦 {u}/{n}　[{envreg.STATUS[k][0]}]")
        except Exception:
            bad += 1
            print(f"× {BY_KEY[k].name}")
            traceback.print_exc()
    return bad


if __name__ == "__main__":
    sys.exit(1 if check_module(sys.argv[1]) else 0)
