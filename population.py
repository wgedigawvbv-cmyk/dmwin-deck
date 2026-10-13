#!/usr/bin/env python3
"""オリジナルデッキを何個もまとめて創作する（シミュレーションに並べる「創作者の群れ」を作る）

  creator.py は1個の最良デッキを作って終わるが、環境の構造を問うには「1つの正解」より
  「互いに違う複数の答え」のほうが情報が多い。ここでは
    ・相手は公式カバレージの入賞リスト（decks8.py）＝実際の環境
    ・すでに創作したデッキに似すぎたものは作り直す（creator.EXTRA_REF／EXTRA_MAX）
  という2つの決まりだけを置いて、同じ手続きを n 回まわす。デッキごとの作戦は書いていない。

  python population.py --n 6 --seed 31 --procs 4 --out runs8/pop1.json
  python population.py --show runs8/pop1.json
"""
import argparse
import json
import random
import time
from multiprocessing import Pool

import ai3                        # noqa: F401  （engine3 を通して envcards が登録される）
import creator
import decks8
import playable3
import roles3
from cards3 import BY_KEY

OPP = {}          # {相手の名前: デッキ}　子プロセスにも initializer で渡す


def _init(opp, cards):
    global OPP
    OPP = opp
    creator._init(cards)


def one(job):
    idx, deck, oname, seed, first, budget, pol = job
    g = ai3.play_game(deck, OPP[oname], random.Random(seed), first,
                      (budget, budget), names=("*", "*"), pols=(pol, pol))
    return idx, oname, g.winner, g.how, (g.turn + 1) // 2


def evaluate(pool, decks, opps, games, budget, pol, rng):
    """各デッキを opps の各デッキと games 戦ずつ戦わせる。返り値：[(平均勝率, {相手: 勝率})]"""
    jobs = []
    for i, d in enumerate(decks):
        for o in opps:
            for g in range(games):
                jobs.append((i, d, o, rng.getrandbits(40), g % 2, budget, pol))
    res = {}
    for i, o, w, _how, _t in pool.imap_unordered(one, jobs, chunksize=4):
        s = res.setdefault((i, o), [0.0, 0])
        s[0] += 1.0 if w == 0 else 0.5 if w is None else 0.0
        s[1] += 1
    out = []
    for i in range(len(decks)):
        per = {o: res[(i, o)][0] / res[(i, o)][1] for o in opps}
        out.append((sum(per.values()) / len(per), per))
    return out


def climb(pool, deck, fit, opps, rng, args, pol, favor=None, tag=""):
    """入れ替えで改良する（creator.climb と同じ考え方。相手だけが公式の入賞リストに変わる）"""
    hist, stale, rnd = [], 0, 0
    keys = args._keys
    while stale < args.stuck and rnd < args.rounds:
        rnd += 1
        kids = []
        for n in range(args.children):
            k = (creator.prune_refill(deck, rng, keys, favor) if n % 4 == 3
                 else creator.mutate(deck, rng, keys, favor))
            if k:
                kids.append(k)
        if not kids:
            break
        ev = evaluate(pool, kids, opps, args.games, args.budget, pol, rng)
        j = max(range(len(kids)), key=lambda i: ev[i][0])
        better = ev[j][0] > fit + 0.01
        if better:
            # 運で良く見えただけかもしれないので、倍の戦数で、いまのデッキと同時に測り直す
            chk, cur = evaluate(pool, [kids[j], deck], opps, args.games * 2, args.budget, pol, rng)
            better = chk[0] > cur[0]
            if better:
                deck, fit = kids[j], (chk[0] + ev[j][0]) / 2
        hist.append({"round": rnd, "best_child": round(ev[j][0], 3), "adopted": bool(better),
                     "fit": round(fit, 3), "tag": tag})
        stale = 0 if better else stale + 1
        print(f"    {tag}[{rnd}] 子の最高 {ev[j][0] * 100:.0f}% → {'採用' if better else '見送り'}"
              f"（いま {fit * 100:.0f}%）", flush=True)
    return deck, fit, hist


def concept4(rng, keys):
    """出発点を作る：色を1〜3つ選び、役割の足りない札を「4枚ずつ」入れて40枚にする。

    creator.concept は1枚ずつ足すので、出発点が1枚差し40種類の山になりやすい。
    公式カバレージの入賞リストはどれも11〜18種類（＝多くの札が4枚）で、構造がまるで違う。
    ここで合わせているのは「枚数の形」だけで、どの札を入れるかは役割の決まり（roles3）に任せている。"""
    kinds = ("C", "S", "T", "G", "X")
    for _ in range(200):
        cols = set(rng.sample("LWDFN", rng.choice((1, 2, 2, 3))))
        pool = [k for k in keys if set(BY_KEY[k].civ) <= cols and BY_KEY[k].kind in kinds]
        if len(pool) < 18:
            continue
        deck = {}
        for _ in range(60):
            room = 40 - sum(deck.values())
            if room <= 0:
                break
            k = creator.pick_card(deck, rng, pool, power=1.5)
            if k is None:
                break
            n = min(creator.cap(k), 4, room)
            if rng.random() < 0.15:                    # 1枚差し・2枚差しも少しは混ぜる
                n = min(n, rng.choice((1, 2)))
            deck[k] = deck.get(k, 0) + n
        if sum(deck.values()) != 40:
            continue
        if playable3.dead(deck) or creator.over_ref(deck):
            deck = creator.settle(deck, rng, keys)
            if deck is None:
                continue
        return deck
    return None


def starts_for(rng, keys, n, types):
    """出発点を集める：自由な創作と、調べたデッキタイプからの組み立てを混ぜる
    （すでに創作したデッキに似すぎるものは creator 側ではじかれる）"""
    out, src = [], []
    for arch in types:
        d = creator.build_type(arch, rng, keys)
        if d and not creator.over_ref(d) and not playable3.dead(d):
            out.append(d)
            src.append("型:" + arch["name"])
        if len(out) >= max(1, n // 2):
            break
    tries = 0
    while len(out) < n and tries < 80:
        tries += 1
        d = concept4(rng, keys) if tries % 4 else creator.concept(rng, keys)
        if d:
            out.append(d)
            src.append("自由(4枚ずつ)" if tries % 4 else "自由(1枚ずつ)")
    return out, src


def show(log):
    print(f"\n【創作したデッキ {len(log['decks'])}個】相手＝公式カバレージの入賞リスト{log['n_opp']}個")
    for i, e in enumerate(log["decks"], 1):
        d = {k: v for k, v in e["deck"].items()}
        print(f"\n({i}) 勝率 {e['fit'] * 100:.0f}%　色：{'・'.join(creator.CIV_JA[c] for c in creator.deck_colors(d))}"
              f"　出発点：{e['start']}")
        print("    " + creator.show_deck(d))
        print("    " + creator.role_line(d))
        print(f"    実在リストとの一致率（最大）{e['overlap'] * 100:.0f}%"
              f"／ほかの創作デッキとの一致率（最大）{e['overlap_pop'] * 100:.0f}%")
        if e.get("per"):
            top = sorted(e["per"].items(), key=lambda kv: -kv[1])[:3]
            bot = sorted(e["per"].items(), key=lambda kv: kv[1])[:3]
            print("    得意：" + "、".join(f"{decks8.short(o)} {w * 100:.0f}%" for o, w in top))
            print("    苦手：" + "、".join(f"{decks8.short(o)} {w * 100:.0f}%" for o, w in bot))
    if len(log["decks"]) >= 2:
        print("\n創作デッキどうしの一致率")
        ds = [e["deck"] for e in log["decks"]]
        for i in range(len(ds)):
            print("  " + " ".join(("  －  " if i == j else f"{creator.overlap(ds[i], ds[j]) * 100:4.0f}%")
                                  for j in range(len(ds))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6, help="創作するデッキの数")
    ap.add_argument("--seed", type=int, default=31)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--policy", default="runs7/policy3_4.json")
    ap.add_argument("--budget", type=int, default=100)
    ap.add_argument("--games", type=int, default=1, help="改良中、相手1つあたりの対戦数")
    ap.add_argument("--final-games", type=int, default=2, help="仕上げに測り直す時の、相手1つあたりの対戦数")
    ap.add_argument("--children", type=int, default=6)
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--stuck", type=int, default=3)
    ap.add_argument("--starts", type=int, default=4, help="1個あたり、最初に比べる案の数")
    ap.add_argument("--opp", type=int, default=12, help="改良中に相手にする入賞リストの数（0＝全部）")
    ap.add_argument("--div", type=float, default=0.45, help="創作デッキどうしの一致率の上限")
    ap.add_argument("--out", default="runs8/pop1.json")
    ap.add_argument("--show")
    args = ap.parse_args()
    if args.show:
        show(json.load(open(args.show, encoding="utf-8")))
        return

    rng = random.Random(args.seed)
    allopp = dict(decks8.DECKS8)
    names = sorted(allopp)
    sample = names if args.opp <= 0 or args.opp >= len(names) else sorted(rng.sample(names, args.opp))
    creator.EXTRA_MAX = args.div
    creator.EXTRA_REF = []
    keys = sorted(set(creator.BASEKEYS) | set(creator.NETKEYS))   # カードプール全部
    args._keys = keys
    pol = creator.extend_policy(creator.global_policy(args.policy), creator.NETKEYS)
    types = creator.load_types()
    favor = [k for k in keys if len(roles3.roles(k)) >= 2]

    print(f"カードプール {len(keys)}枚／相手にする入賞リスト {len(sample)}個（全{len(names)}個のうち）"
          f"／創作するデッキ {args.n}個")
    print("改良中の相手：" + "、".join(decks8.short(o) for o in sample))
    t0 = time.time()
    log = {"args": {k: v for k, v in vars(args).items() if not k.startswith("_")},
           "n_opp": len(names), "opp_sample": sample, "pool": len(keys), "decks": []}
    pool = Pool(args.procs, initializer=_init, initargs=(allopp, list(creator.LOADED)))
    try:
        for slot in range(1, args.n + 1):
            print(f"\n=== {slot}個目 ===", flush=True)
            cands, src = starts_for(rng, keys, args.starts, types)
            if not cands:
                print("  これ以上、ほかと違うデッキが作れませんでした")
                break
            ev = evaluate(pool, cands, sample, max(1, args.games), args.budget, pol, rng)
            for s, (f, _p) in zip(src, ev):
                print(f"  案（{s}）{f * 100:.0f}%")
            j = max(range(len(cands)), key=lambda i: ev[i][0])
            deck, fit, hist = climb(pool, cands[j], ev[j][0], sample, rng, args, pol, favor=favor)
            fin = evaluate(pool, [deck], names, args.final_games, args.budget, pol, rng)[0]
            opop = max([creator.overlap(deck, e) for e in creator.EXTRA_REF] or [0.0])
            print(f"  → 全{len(names)}個で測り直し {fin[0] * 100:.0f}%"
                  f"（実在リスト一致率 {creator.max_overlap(deck) * 100:.0f}%／創作ずみ {opop * 100:.0f}%）")
            print("  " + creator.show_deck(deck))
            creator.EXTRA_REF.append(deck)
            log["decks"].append({"deck": deck, "fit": fin[0], "per": fin[1], "start": src[j],
                                 "overlap": creator.max_overlap(deck), "overlap_pop": opop,
                                 "roles": roles3.coverage(deck), "hist": hist,
                                 "names": {k: BY_KEY[k].name for k in deck}})
            json.dump(log, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    finally:
        pool.terminate()
    log["secs"] = time.time() - t0
    json.dump(log, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    show(log)
    print(f"\n保存：{args.out}（{log['secs']:.0f}秒）")


if __name__ == "__main__":
    main()
