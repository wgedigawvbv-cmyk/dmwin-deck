#!/usr/bin/env python3
"""第3版：AIオリジナルデッキの使い手（創作者）

  流れ
    1. 実在の7リストに似すぎない（どれとも一致率が MAX_OVERLAP 以下の）デッキを、自由に創作する。
       「そのデッキで出せるか」（playable3.py）を満たすものだけを使う。
    2. 環境の7デッキと対戦して成績をはかり、カードの入れ替えで改良していく（全員と同じ先読み操縦）。
    3. 何回続けても良くならず、成績が目標（既定50%）に届かないと「詰まった」とする。
       詰まったら、どの相手にどう負けるかを調べ、欲しいカードの一覧（wishlist）を作る。
    4. ネットで調べて実装したカード（envcards/*.py。効果はすべてカードどおりに書いてある）を使えるようにする。
       --net claude をつけると、さらに Claude API の検索で新しいカードを探して部品の並びで近似登録する
       （近似なので status は approx。あとで envcards に書き直すためのもの）。
    5. 持ってきたカードを足して、もう一度改良する。
    6. それでも目標に届かなければ、ネットで調べた「新しいデッキタイプ」の40枚（archetypes.py）を試し、
       良ければ乗り換えてもう一度改良する。

  役割の考え方（roles3.py）：1枚で複数の役割をこなす札を優先し、どの役割も担わない／役割の薄い札から先に抜いて、
  いつも40枚にそろえる（入れ替えのたびに40枚を確かめる）。

  python creator.py --seed 1 --out runs8/creator_s1.json
  python creator.py --net none --types none     ネットのカードもデッキタイプも使わない（詰まったらそこで終わり）
  python creator.py --preload                   最初からネットのカードもプールに入れる
"""
import argparse
import json
import random
import statistics
import time
from multiprocessing import Pool

import ai3                       # noqa: F401  （engine3 を通して envcards が登録される）
import archetypes
import envreg
import netcards
import playable3
import roles3
from cards3 import BY_KEY, DECKS, POOL, REAL_USAGE

MAXCOPY = dict(archetypes.LIMIT)          # 殿堂入り・ドリーム・禁断の上限
MAX_OVERLAP = 0.6
NAMES = list(DECKS)
CIV_JA = {"L": "光", "W": "水", "D": "闇", "F": "火", "N": "自然"}
LOADED = []          # 部品の並びで近似登録したカード（子プロセスにも同じ登録をするため）
NETKEYS = sorted(envreg.STATUS)           # ネットで調べて実装したカード（詰まってから使える）
BASEKEYS = sorted(c.key for c in POOL if c.key not in envreg.STATUS)   # もとからあった札束


def cap(k):
    return MAXCOPY.get(k, 4)


def _init(cards):
    """子プロセスの初期化：ネットのカードを同じように登録する（Windows の spawn でも動くように）"""
    if cards:
        netcards.register([dict(c) for c in cards])


def make_pool(procs):
    return Pool(procs, initializer=_init, initargs=([c for c in LOADED],))


def global_policy(path):
    """学習済みの進め方をデッキ共通の1枚にまとめ、ネットのカードにも「中くらいの重み」をつける"""
    if not path:
        return {}
    pol = json.load(open(path, encoding="utf-8"))
    acc = {}
    for tab in pol.values():
        for k, w in tab.items():
            acc.setdefault(k, []).append(w)
    tab = {k: sum(v) / len(v) for k, v in acc.items()}
    return {"*": tab}


def extend_policy(pol, keys):
    """知らないカードの重みを、同じターンの「カードを出す手」の中央値にそろえる（ネットのカードが不利にならないように）"""
    if not pol:
        return pol
    tab = pol["*"]
    for t in range(0, 7):
        vals = sorted(w for k, w in tab.items() if k.startswith(f"{t}|p:"))
        mid = vals[len(vals) // 2] if vals else 0.3
        for k in keys:
            for form in (f"{t}|p:{k}:0", f"{t}|p:{k}:1", f"{t}|spell:{k}"):
                tab.setdefault(form, mid)
    return pol


# ---------------------------------------------------------------- デッキの組み立て
def overlap(d, e):
    return sum(min(v, e.get(k, 0)) for k, v in d.items()) / 40


def max_overlap(d):
    return max(overlap(d, DECKS[n]) for n in NAMES)


EXTRA_REF = []            # すでに創作したデッキ（population.py が入れる。これにも似すぎないようにする）
EXTRA_MAX = MAX_OVERLAP   # 創作ずみのデッキとの一致率の上限


def over_ref(d):
    """実在リストにも、すでに創作したデッキにも、似すぎていないか（似すぎなら True）"""
    if max_overlap(d) > MAX_OVERLAP:
        return True
    return any(overlap(d, e) > EXTRA_MAX for e in EXTRA_REF)


def addable(deck, k):
    """k を1枚足しても、そのデッキで出せるか（出せない札が増えないか）"""
    if deck.get(k, 0) >= cap(k):
        return False
    deck[k] = deck.get(k, 0) + 1
    ok = not playable3.dead(deck)
    deck[k] -= 1
    if not deck[k]:
        del deck[k]
    return ok


def pick_card(deck, rng, keys, prefer=None, power=1.0):
    """デッキに足せる札を1つ選ぶ。役割がまだ足りないほど・複数の役割を持つほど・安いほど選ばれやすい
    （power を上げるほど役割の価値を重く見る）。prefer があればその中から"""
    pool = prefer if prefer else keys
    cov = roles3.coverage(deck)
    w = [(roles3.value(k, cov) ** power) / (1 + max(0, BY_KEY[k].cost - 4) * 0.5) for k in pool]
    for k in rng.choices(pool, weights=w, k=40):
        if addable(deck, k):
            return k
    return None


def concept(rng, keys):
    """創作の出発点：主な色を1〜3つ選び、その色で出せる札だけでデッキを作る"""
    for _ in range(200):
        n = rng.choice((1, 2, 2, 3))
        cols = set(rng.sample("LWDFN", n))
        pool = [k for k in keys if set(BY_KEY[k].civ) <= cols and BY_KEY[k].kind in ("C", "S")]
        if len(pool) < 18:
            continue
        deck = {}
        for _ in range(400):
            if sum(deck.values()) >= 40:
                break
            k = rng.choice(pool)
            if deck.get(k, 0) < cap(k) and rng.random() < 1 / (1 + max(0, BY_KEY[k].cost - 4) * 0.5):
                deck[k] = deck.get(k, 0) + 1
        if sum(deck.values()) != 40:
            continue
        if playable3.dead(deck) or over_ref(deck):
            deck = settle(deck, rng, keys)
            if deck is None:
                continue
        return deck
    return None


def settle(deck, rng, keys):
    """出せない札を除き、足せる札で埋める。実在リストに似すぎたら None"""
    deck = dict(deck)
    for _ in range(40):
        bad = playable3.dead(deck)
        if not bad:
            break
        for k in bad:
            del deck[k]
    for _ in range(400):
        if sum(deck.values()) >= 40:
            break
        k = pick_card(deck, rng, keys)
        if k:
            deck[k] = deck.get(k, 0) + 1
    if sum(deck.values()) != 40 or playable3.dead(deck) or over_ref(deck):
        return None
    return deck


def check40(d):
    assert sum(d.values()) == 40, f"40枚でない：{sum(d.values())}"
    return d


def ok_deck(d, deck):
    return sum(d.values()) == 40 and not playable3.dead(d) and not over_ref(d) and d != deck


def remove_thin(d, rng, n, sharp=1.0):
    """役割の薄い札ほど選ばれやすく、n枚を抜く（抜いたあとの役割の数で測り直しながら）"""
    for _ in range(n):
        th = roles3.thinness(d)
        ks = sorted(d)
        k = rng.choices(ks, weights=[(1.0 / (0.3 + th[x])) ** (2 * sharp) * d[x] for x in ks], k=1)[0]
        d[k] -= 1
        if not d[k]:
            del d[k]


def mutate(deck, rng, keys, favor=None):
    """入れ替えを1〜4枚。抜くのは役割の薄い札、足すのは役割が足りず複数の役割をもつ札。
    favor（ネットの複数役割カード）があれば、足す札の4割をそこから選ぶ"""
    for _ in range(20):
        d = dict(deck)
        for _ in range(rng.choice((1, 1, 2, 2, 3, 4))):
            remove_thin(d, rng, 1)
            a = pick_card(d, rng, keys, prefer=favor if favor and rng.random() < 0.4 else None, power=2.0)
            if a is None:
                return None
            d[a] = d.get(a, 0) + 1
        if ok_deck(d, deck):
            return check40(d)
    return None


def prune_refill(deck, rng, keys, favor=None):
    """役割の薄い札を3〜6枚まとめて抜き、役割の多い札で埋める（デッキの無駄を一気に減らす）"""
    for _ in range(20):
        d = dict(deck)
        remove_thin(d, rng, rng.choice((3, 4, 5, 6)), sharp=1.5)
        for _ in range(40 - sum(d.values())):
            a = pick_card(d, rng, keys, prefer=favor if favor and rng.random() < 0.5 else None, power=3.0)
            if a is None:
                break
            d[a] = d.get(a, 0) + 1
        if ok_deck(d, deck):
            return check40(d)
    return None


# ---------------------------------------------------------------- 対戦
def one(job):
    idx, deck, opp, seed, first, budget, pol = job
    g = ai3.play_game(deck, DECKS[opp], random.Random(seed), first, (budget, budget), names=("*", "*"), pols=(pol, pol))
    return idx, opp, g.winner, g.how, (g.turn + 1) // 2


def evaluate(pool, decks, games, budget, pol, rng):
    """各デッキを、7つの実在リストと games 戦ずつ戦わせる。返り値：[(使用数で重みづけた勝率, {相手: 勝率})]"""
    jobs = []
    for i, d in enumerate(decks):
        for o in NAMES:
            for g in range(games):
                jobs.append((i, d, o, rng.getrandbits(40), g % 2, budget, pol))
    res = {}
    for i, o, w, how, turn in pool.imap_unordered(one, jobs, chunksize=4):
        s = res.setdefault((i, o), [0.0, 0])
        s[0] += 1.0 if w == 0 else 0.5 if w is None else 0.0
        s[1] += 1
    out = []
    tot = sum(REAL_USAGE.values())
    for i in range(len(decks)):
        per = {o: res[(i, o)][0] / res[(i, o)][1] for o in NAMES}
        out.append((sum(per[o] * REAL_USAGE[o] for o in NAMES) / tot, per))
    return out


def diagnose(pool, deck, games, budget, pol, rng):
    """どの相手に、どう負けるかを調べる"""
    jobs = [(0, deck, o, rng.getrandbits(40), g % 2, budget, pol) for o in NAMES for g in range(games)]
    rs = pool.map(one, jobs, chunksize=4)
    per = {}
    for _, o, w, how, turn in rs:
        p = per.setdefault(o, {"n": 0, "win": 0.0, "fast": 0, "loop": 0, "slow": 0, "loss": 0})
        p["n"] += 1
        p["win"] += 1.0 if w == 0 else 0.5 if w is None else 0.0
        if w == 1:
            p["loss"] += 1
            if how in ("ループ", "シャコガイル", "山札切れ"):
                p["loop"] += 1
            elif turn <= 5:
                p["fast"] += 1
            elif turn >= 7:
                p["slow"] += 1
    return per


def deck_colors(deck):
    cnt = {}
    for k, v in deck.items():
        for x in BY_KEY[k].civ:
            cnt[x] = cnt.get(x, 0) + v
    return [x for x, n in sorted(cnt.items(), key=lambda kv: -kv[1]) if n >= 6]


def wishlist(deck, per):
    """負け方から、欲しいカードの一覧を作る"""
    cols = deck_colors(deck)
    colja = "・".join(CIV_JA[c] for c in cols)
    loss = sum(p["loss"] for p in per.values()) or 1
    fast = sum(p["fast"] for p in per.values()) / loss
    loop = sum(p["loop"] for p in per.values()) / loss
    slow = sum(p["slow"] for p in per.values()) / loss
    worst = sorted(per, key=lambda o: per[o]["win"] / per[o]["n"])[:3]
    weak = [{"vs": o, "winrate": round(per[o]["win"] / per[o]["n"], 2)} for o in worst]
    wants = []
    if fast >= 0.3:
        wants.append({"role": "守り", "why": f"負けの{fast * 100:.0f}%が5ターン目までの速い決着",
                      "need": "ブロッカー、S・トリガーの除去・タップ、シールドを増やす札など。コスト2〜5",
                      "civs": cols, "max_cost": 5})
    if loop >= 0.2:
        wants.append({"role": "ループ対策", "why": f"負けの{loop * 100:.0f}%がループ（殴らない勝ち）",
                      "need": "相手のクリーチャーを手札やマナに戻す、手札を捨てさせる、出せる数を縛る札。コスト2〜5",
                      "civs": cols, "max_cost": 5})
    if slow >= 0.25:
        wants.append({"role": "長引いたときの強さ", "why": f"負けの{slow * 100:.0f}%が7ターン目以降",
                      "need": "手札を増やす、マナを増やす、大きなブレイク数のクリーチャー",
                      "civs": cols, "max_cost": 8})
    wants.append({"role": "低コストの強い動き", "why": "どの相手にも先に動くため",
                  "need": "コスト2〜4で、出た時に何かが起きる（引く・除去・加速）クリーチャーや呪文",
                  "civs": cols, "max_cost": 4})
    return {"deck_colors": colja, "weak_against": weak, "loss_shape": {"fast": round(fast, 2), "loop": round(loop, 2),
                                                                      "slow": round(slow, 2)}, "wants": wants}


def show_deck(deck):
    return "、".join(f"{BY_KEY[k].name}×{v}" for k, v in sorted(deck.items(), key=lambda kv: (BY_KEY[kv[0]].cost, kv[0])))


def role_line(deck):
    cov, multi, zero = roles3.stats(deck)
    return ("役割の枚数 " + "・".join(f"{r}{cov[r]}" for r in roles3.ROLES) +
            f"／2役割以上の札 {multi}枚／役割のない札 {zero}枚")


def load_types(path=None):
    """ネットで調べたデッキタイプ（archetypes.py の40枚）。--types-file を指定すればそのJSONも足す"""
    out = [dict(a, name=n) for n, a in archetypes.ARCHETYPES.items()]
    if path and __import__("os").path.exists(path):
        try:
            out += json.load(open(path, encoding="utf-8")).get("types", [])
        except (ValueError, KeyError):
            pass
    return out


def build_type(arch, rng, keys):
    """デッキタイプの40枚を作る。リストがそろっていればそのまま使い、核だけなら残りを役割の価値で埋める"""
    full = arch.get("deck")
    if full and sum(full.values()) == 40 and all(k in BY_KEY for k in full):
        d = dict(full)
        if not playable3.dead(d):
            return d
    core = {k: n for k, n in (arch.get("core") or full or {}).items() if k in BY_KEY}
    if len(core) < 2:
        return None
    cols = set("".join(BY_KEY[k].civ for k in core))
    allowed = [k for k in keys if set(BY_KEY[k].civ) <= cols and BY_KEY[k].kind in ("C", "S")]
    for _ in range(30):
        d = dict(core)
        for _ in range(600):
            if sum(d.values()) >= 40:
                break
            cov = roles3.coverage(d)
            k = rng.choices(allowed, weights=[roles3.value(x, cov) ** 2 / (1 + max(0, BY_KEY[x].cost - 4) * .5)
                                              for x in allowed], k=1)[0]
            if d.get(k, 0) < cap(k):
                d[k] = d.get(k, 0) + 1
        for _ in range(20):
            bad = [k for k in playable3.dead(d) if k not in core] or list(playable3.dead(d))
            if not bad:
                break
            for k in bad:
                d.pop(k, None)
            for _ in range(300):
                if sum(d.values()) >= 40:
                    break
                k = pick_card(d, rng, allowed, power=2.0)
                if k:
                    d[k] = d.get(k, 0) + 1
                else:
                    cov = roles3.coverage(d)
                    k = rng.choices(allowed, weights=[roles3.value(x, cov) for x in allowed], k=1)[0]
                    if d.get(k, 0) < cap(k):
                        d[k] = d.get(k, 0) + 1
        if sum(d.values()) == 40 and not playable3.dead(d) and max_overlap(d) <= MAX_OVERLAP:
            return d
    return None


def measure(pool, deck, args, pol, rng, mult=6):
    """決め手になる測定（戦数を増やして測り直す）。返り値：(勝率, 相手別)"""
    return evaluate(pool, [deck], max(8, args.games * mult), args.budget, pol, rng)[0]


def climb(pool, deck, fit, rng, args, pol, favor=None, tag=""):
    """入れ替えで改良する。args.stuck 回続けて良くならなければやめる。返り値：(デッキ, 成績, 履歴)"""
    hist = []
    stale = 0
    keys = [c.key for c in POOL]
    rnd = 0
    while stale < args.stuck and rnd < args.rounds:
        rnd += 1
        kids = []
        for n in range(args.children):
            k = prune_refill(deck, rng, keys, favor) if n % 4 == 3 else mutate(deck, rng, keys, favor)
            if k:
                kids.append(k)
        if not kids:
            break
        ev = evaluate(pool, kids, args.games, args.budget, pol, rng)
        j = max(range(len(kids)), key=lambda i: ev[i][0])
        better = ev[j][0] > fit + 0.01
        if better:
            # 運で良く見えただけかもしれないので、倍の戦数で測り直してから採用する
            chk = evaluate(pool, [kids[j]], args.games * 2, args.budget, pol, rng)[0][0]
            cur = evaluate(pool, [deck], args.games * 2, args.budget, pol, rng)[0][0]
            better = chk > cur
            if better:
                deck, fit = kids[j], (chk + ev[j][0]) / 2
        hist.append({"round": rnd, "best_child": round(ev[j][0], 3), "adopted": bool(better), "fit": round(fit, 3), "tag": tag})
        stale = 0 if better else stale + 1
        print(f"  {tag}[{rnd}] 子の最高 {ev[j][0] * 100:.0f}% → {'採用' if better else '見送り'}（いま {fit * 100:.0f}%）", flush=True)
    return deck, fit, hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--policy", default="runs7/policy3_4.json")
    ap.add_argument("--budget", type=int, default=100)
    ap.add_argument("--games", type=int, default=3, help="実在の1リストあたりの対戦数（子の評価）")
    ap.add_argument("--children", type=int, default=8)
    ap.add_argument("--rounds", type=int, default=12, help="1段階あたりの改良の最大回数")
    ap.add_argument("--stuck", type=int, default=3, help="続けて良くならなかったら詰まったとみなす回数")
    ap.add_argument("--target", type=float, default=0.5, help="この勝率（使用数で重みづけ）に届けば満足")
    ap.add_argument("--starts", type=int, default=6, help="最初に創作して比べるデッキの数")
    ap.add_argument("--net", choices=("none", "file", "claude"), default="file")
    ap.add_argument("--net-file", default="cards_net.json")
    ap.add_argument("--types", choices=("none", "file", "claude"), default="file",
                    help="それでも詰まったとき、新しいデッキタイプを探す（file＝archetypes_net.json、claude＝API検索）")
    ap.add_argument("--types-file", default="archetypes_net.json", help="--types claude で探した結果を書き足すJSON")
    ap.add_argument("--preload", action="store_true", help="最初から cards_net.json のカードをプールに入れる（詰まる前から使う）")
    ap.add_argument("--net-rounds", type=int, default=1, help="ネットに探しに行く回数の上限")
    ap.add_argument("--out", default="runs7/creator.json")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    pol = global_policy(args.policy)
    log = {"args": vars(args), "stages": []}
    t0 = time.time()
    keys = list(BASEKEYS)
    if args.preload:
        keys = sorted(set(keys) | set(NETKEYS))
        pol = extend_policy(pol, NETKEYS)
        print(f"（最初からネットで調べたカード {len(NETKEYS)}枚もプールに入れました）")
    pool = make_pool(args.procs)

    print(f"【1】自由に創作（{args.starts}案）")
    starts = []
    while len(starts) < args.starts:
        d = concept(rng, keys)
        if d:
            starts.append(d)
    ev = evaluate(pool, starts, args.games * 2, args.budget, pol, rng)
    for d, (f, _) in zip(starts, ev):
        print(f"  案：{'・'.join(CIV_JA[c] for c in deck_colors(d))}　{f * 100:.0f}%　実在リストとの一致率 {max_overlap(d) * 100:.0f}%")
    j = max(range(len(starts)), key=lambda i: ev[i][0])
    deck, fit = starts[j], ev[j][0]
    log["stages"].append({"stage": "創作", "fit": fit, "deck": deck, "starts": [e[0] for e in ev]})

    print(f"【2】改良（実在の7デッキと対戦）")
    deck, fit, hist = climb(pool, deck, fit, rng, args, pol, tag="")
    final = measure(pool, deck, args, pol, rng)
    print(f"  → 測り直し {final[0] * 100:.0f}%")
    fit = final[0]
    log["stages"].append({"stage": "改良", "fit": fit, "deck": deck, "per": final[1], "hist": hist})

    net_round = 0
    while fit < args.target and args.net != "none" and net_round < args.net_rounds:
        net_round += 1
        print(f"【3】詰まりました（{fit * 100:.0f}% ＜ 目標{args.target * 100:.0f}%）。負け方を調べます")
        per = diagnose(pool, deck, 6, args.budget, pol, rng)
        wl = wishlist(deck, per)
        for w in wl["weak_against"]:
            print(f"  苦手：{w['vs']}（{w['winrate'] * 100:.0f}%）")
        print(f"  負け方：速い決着 {wl['loss_shape']['fast'] * 100:.0f}%／ループ {wl['loss_shape']['loop'] * 100:.0f}%"
              f"／長引く {wl['loss_shape']['slow'] * 100:.0f}%")
        for w in wl["wants"]:
            print(f"  欲しい札：{w['role']}（{w['why']}）")
        json.dump(wl, open(args.net_file.replace(".json", "_wishlist.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"【4】ネットで調べたカードを使えるようにします（{args.net}）")
        ok = [k for k in NETKEYS if k not in keys]
        if args.net == "claude":                       # さらに API の検索で探す（部品の並びでの近似登録）
            import fetch_cards
            got = fetch_cards.fetch(wl, args.net_file)
            new = [c for c in got if c["key"] not in BY_KEY]
            ok2, bad = netcards.register(new)
            for k, w in bad:
                print(f"  × {k}：{w}")
            LOADED.extend(c for c in new if c["key"] in ok2)
            ok += ok2
        if not ok:
            log["stages"].append({"stage": "ネット", "wishlist": wl, "loaded": []})
            break
        keys = sorted(set(keys) | set(ok))
        print(f"  使えるようになった札：{len(ok)}枚")
        pool.terminate()
        pol = extend_policy(pol, ok)
        pool = make_pool(args.procs)
        print(f"【5】ネットのカードを足して再び改良")
        before = fit
        multi = [k for k in ok if len(roles3.roles(k)) >= 2] or ok
        deck2, fit2, hist2 = climb(pool, deck, fit, rng, args, pol, favor=multi, tag="ネット後 ")
        final = measure(pool, deck2, args, pol, rng)
        if deck2 is not deck:                      # 同じ戦数で測り直した値どうしで比べる
            before = measure(pool, deck, args, pol, rng)[0]
        print(f"  → 測り直し {final[0] * 100:.0f}%（ネットのカードを足す前を同じ戦数で測り直すと {before * 100:.0f}%）")
        if final[0] < before:
            print("  → ネットのカードを足したほうが良くなかったので、元のデッキのままにします")
            deck2, final = deck, (before, final[1])
        used = {BY_KEY[k].name: v for k, v in deck2.items() if k in ok}
        print("  ネットのカードの採用：" + ("、".join(f"{n}×{v}" for n, v in used.items()) or "なし"))
        log["stages"].append({"stage": "ネット", "wishlist": wl, "loaded": ok, "fit": final[0], "before": before,
                              "deck": deck2, "per": final[1], "hist": hist2, "net_used": used})
        deck, fit = deck2, final[0]

    # 【6】新しいデッキタイプ
    if fit < args.target and args.types != "none":
        print(f"【6】まだ届きません（{fit * 100:.0f}% ＜ 目標{args.target * 100:.0f}%）。新しいデッキタイプを探します（{args.types}）")
        if args.types == "claude":
            import fetch_cards
            fetch_cards.fetch_types(log["stages"][-1].get("wishlist") or {}, args.types_file, args.net_file)
            got = json.load(open(args.net_file, encoding="utf-8")).get("cards", [])
            new = [c for c in got if c["key"] not in BY_KEY]
            ok2, bad2 = netcards.register(new)
            LOADED.extend(c for c in new if c["key"] in ok2)
            if ok2:
                pool.terminate()
                pol = extend_policy(pol, ok2)
                pool = make_pool(args.procs)
        if set(NETKEYS) - set(keys):        # デッキタイプの札を使えるようにする
            keys = sorted(set(keys) | set(NETKEYS))
            pool.terminate()
            pol = extend_policy(pol, NETKEYS)
            pool = make_pool(args.procs)
        cands, names = [], []
        for arch in load_types(args.types_file if args.types == "claude" else None):
            d = build_type(arch, rng, keys)
            if d:
                cands.append(d)
                names.append(arch["name"])
            else:
                print(f"  {arch['name']}：このカードプールでは組めませんでした")
        if cands:
            ev = evaluate(pool, cands, args.games * 4, args.budget, pol, rng)
            for n, d, (f, _) in zip(names, cands, ev):
                print(f"  タイプ案「{n}」{f * 100:.0f}%（一致率 {max_overlap(d) * 100:.0f}%）")
            j = max(range(len(cands)), key=lambda i: ev[i][0])
            curm = measure(pool, deck, args, pol, rng)
            cur = curm[0]
            fit, per0 = cur, curm[1]                  # いまのデッキの成績も、同じ戦数で測り直した値にそろえる
            log["stages"].append({"stage": "測り直し", "fit": cur, "deck": deck, "per": per0})
            print(f"  いまのデッキ（測り直し）{cur * 100:.0f}% ／最良のタイプ案「{names[j]}」{ev[j][0] * 100:.0f}%")
            before = cur
            if ev[j][0] > cur:
                print(f"  → 「{names[j]}」に乗り換えて改良します")
                favor2 = [k for k in keys if k in envreg.STATUS and len(roles3.roles(k)) >= 2]
                deck3, fit3, hist3 = climb(pool, cands[j], ev[j][0], rng, args, pol, favor=favor2, tag="タイプ後 ")
                final = measure(pool, deck3, args, pol, rng)
                print(f"  → 測り直し {final[0] * 100:.0f}%（乗り換え前を同じ戦数で測り直すと {before * 100:.0f}%）")
                log["stages"].append({"stage": "デッキタイプ", "type": names[j], "fit": final[0], "before": before,
                                      "deck": deck3, "per": final[1], "hist": hist3,
                                      "candidates": {n: e[0] for n, e in zip(names, ev)}})
                if final[0] >= before:
                    deck, fit = deck3, final[0]
                else:
                    print("  → 乗り換えたほうが良くなかったので、元のデッキのままにします")
            else:
                print("  → どのタイプ案も、いまのデッキを上回らなかったので乗り換えません")
                log["stages"].append({"stage": "デッキタイプ", "type": None, "before": cur,
                                      "candidates": {n: e[0] for n, e in zip(names, ev)}})

    pool.terminate()
    print("\n【結果】")
    print(f"  勝率（実在の7デッキ、使用数で重みづけ）{fit * 100:.0f}%")
    print(f"  実在リストとの一致率（最大）{max_overlap(deck) * 100:.0f}%　色：{'・'.join(CIV_JA[c] for c in deck_colors(deck))}")
    print("  デッキ：" + show_deck(deck))
    print("  " + role_line(deck))
    assert sum(deck.values()) == 40
    per = None
    for st in reversed(log["stages"]):
        if st.get("deck") == deck and st.get("per"):
            per = st["per"]
            break
    if per:
        print("  相手別：" + "、".join(f"{o} {w * 100:.0f}%" for o, w in per.items()))
    log["final"] = {"roles": roles3.coverage(deck), "deck": deck, "fit": fit, "names": {k: BY_KEY[k].name for k in deck}}
    json.dump(log, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"保存：{args.out}（{time.time() - t0:.0f}秒）")


if __name__ == "__main__":
    main()
