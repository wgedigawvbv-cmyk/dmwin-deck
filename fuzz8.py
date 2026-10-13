#!/usr/bin/env python3
"""でたらめなデッキを大量に作って対戦させ、例外が出ないかを確かめる（創作者が壊れないかの事前確認）

  python fuzz8.py 400 1        対戦数とseed
"""
import random
import sys
import traceback

import creator
import engine3
import playable3
from archetypes import ARCHETYPES
from cards3 import BY_KEY, DECKS


def random_deck(rng, keys):
    for _ in range(80):
        d = creator.concept(rng, keys)
        if d:
            return d
    return None


def main(n=400, seed=1):
    rng = random.Random(seed)
    keys = sorted(set(creator.BASEKEYS) | set(creator.NETKEYS))
    pool = [ARCHETYPES[k]["deck"] for k in ARCHETYPES] + list(DECKS.values())
    made = 0
    for _ in range(14):
        d = random_deck(rng, keys)
        if d:
            pool.append(d)
            made += 1
    print(f"デッキ {len(pool)}個（うちでたらめに作ったもの {made}個）で {n}戦")
    bad = 0
    moves = 0
    for t in range(n):
        a, b = rng.choice(pool), rng.choice(pool)
        g = engine3.Game(a, b, rng, first=t % 2)
        try:
            while not g.over:
                g.apply(rng.choice(g.legal()))
                moves += 1
        except Exception:
            bad += 1
            print(f"--- {t}戦目で例外 ---")
            traceback.print_exc()
            if bad >= 3:
                break
    print(f"{n - bad}/{n} 戦が例外なしで終わった（{moves}手）")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 400,
                          int(sys.argv[2]) if len(sys.argv) > 2 else 1))


def _deck_with(k, rng):
    """既知の12デッキを土台にして、カード k を入れた40枚を作る（色と「出せるか」を満たすもの）"""
    base = [("実在:" + n, d) for n, d in DECKS.items()] + [("タイプ:" + n, a["deck"]) for n, a in ARCHETYPES.items()]
    rng.shuffle(base)
    want = set(BY_KEY[k].civ)
    for nm, d0 in base:
        cols = set("".join(BY_KEY[x].civ for x in d0))
        if not want <= cols and want:
            continue
        d = dict(d0)
        need = min(4, creator.cap(k))
        if playable3.PLAYRULE.get(k) and playable3.PLAYRULE[k]({k: 4}, k):
            need = 1                                    # 1枚制限のカード
        for _ in range(need):
            ks = [x for x in sorted(d) if x != k]
            if not ks:
                break
            w = min(ks, key=lambda x: (engine3.PRI[x], x))
            d[w] -= 1
            if not d[w]:
                del d[w]
        d[k] = d.get(k, 0) + need
        while sum(d.values()) > 40:
            ks = [x for x in sorted(d) if x != k]
            w = min(ks, key=lambda x: (engine3.PRI[x], x))
            d[w] -= 1
            if not d[w]:
                del d[w]
        while sum(d.values()) < 40:
            x = max(sorted(d0), key=lambda y: (engine3.PRI[y], y) if d.get(y, 0) < creator.cap(y) else (-99, y))
            d[x] = d.get(x, 0) + 1
        if sum(d.values()) == 40 and not playable3.dead(d):
            return nm, d
    return None, None


def cover(seed=1, games_per=2):
    """カード1枚ずつについて、それを含むデッキを作って対戦させる（全カードを一度は通す）"""
    rng = random.Random(seed)
    keys = sorted(set(creator.BASEKEYS) | set(creator.NETKEYS))
    opp = list(DECKS.values()) + [ARCHETYPES[k]["deck"] for k in ARCHETYPES]
    miss, bad, done = [], 0, 0
    for k in keys:
        nm, d = _deck_with(k, rng)
        if d is None:
            miss.append(k)
            continue
        for t in range(games_per):
            g = engine3.Game(d, rng.choice(opp), rng, first=t % 2)
            try:
                while not g.over:
                    g.apply(rng.choice(g.legal()))
                done += 1
            except Exception:
                bad += 1
                print(f"--- {BY_KEY[k].name} を入れたデッキ（土台 {nm}）で例外 ---")
                traceback.print_exc()
                if bad >= 5:
                    return 1
    print(f"{done}戦が例外なしで終わった（{len(keys) - len(miss)}/{len(keys)}枚を試した）")
    if miss:
        print("デッキに入れられなかったカード：" + "、".join(BY_KEY[k].name for k in miss))
    return 1 if bad else 0


def _deck_force(k, rng):
    """カード k の色だけで40枚を組む（既知デッキを土台にできないカード用）"""
    from cards3 import POOL
    want = set(BY_KEY[k].civ)
    keys = [c.key for c in POOL if set(c.civ) <= want or not c.civ]
    if len(keys) < 12:
        return None
    for try_n in range(60):
        want_n = (4, 2, 1)[min(2, try_n // 20)]        # 1枚制限のカードもあるので枚数を減らして試す
        d = {k: min(want_n, creator.cap(k))}
        for _ in range(500):
            if sum(d.values()) >= 40:
                break
            x = rng.choice(keys)
            if d.get(x, 0) < creator.cap(x) and rng.random() < 1 / (1 + max(0, BY_KEY[x].cost - 4) * 0.4):
                d[x] = d.get(x, 0) + 1
        if sum(d.values()) != 40:
            continue
        for _ in range(30):
            bad = {b for b in playable3.dead(d) if b != k}
            if not bad:
                break
            for b in bad:
                d.pop(b, None)
            while sum(d.values()) < 40:
                x = rng.choice(keys)
                if d.get(x, 0) < creator.cap(x):
                    d[x] = d.get(x, 0) + 1
        if sum(d.values()) == 40 and not playable3.dead(d) and d.get(k):
            return d
    return None


def cover2(seed=1, games_per=3, only=None):
    """既知デッキを土台にできないカードも、色だけで組んだデッキで試す"""
    rng = random.Random(seed)
    keys = only or [c.key for c in __import__("cards3").POOL]
    opp = list(DECKS.values()) + [ARCHETYPES[k]["deck"] for k in ARCHETYPES]
    miss, bad, done = [], 0, 0
    for k in keys:
        nm, d = _deck_with(k, rng)
        if d is None:
            d = _deck_force(k, rng)
            nm = "色だけで組んだデッキ"
        if d is None:
            miss.append(k)
            continue
        for t in range(games_per):
            g = engine3.Game(d, rng.choice(opp), rng, first=t % 2)
            try:
                while not g.over:
                    g.apply(rng.choice(g.legal()))
                done += 1
            except Exception:
                bad += 1
                print(f"--- {BY_KEY[k].name} を入れたデッキ（土台 {nm}）で例外 ---")
                traceback.print_exc()
                if bad >= 5:
                    return 1
    print(f"{done}戦が例外なしで終わった（{len(keys) - len(miss)}/{len(keys)}枚を試した）")
    if miss:
        print("デッキに入れられなかったカード：" + "、".join(BY_KEY[k].name for k in miss))
    return 1 if bad else 0
