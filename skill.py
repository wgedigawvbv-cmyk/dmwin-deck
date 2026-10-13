#!/usr/bin/env python3
"""操縦の腕（デュエマのプレイングの質）を測る道具

  カードプールが増えるたびに、操縦が置いていかれていないかを確かめるためのもの。
  「このAIは強くなったのか」を言葉ではなく数字で出すところまでを1つにまとめてある。

  測り方は3つ。

    1. 腕くらべ（--ladder）
       相手が何もしない壁を、何ターンで殴り切れるか。低いほど上手い。
       相手との読み合いが無いぶん、**操縦そのものの質**だけが出る。いちばんばらつきが小さい。

    2. 直接対決（--ab）
       同じデッキ・同じ探索回数で、進め方だけを変えて戦わせる。
       座席と先攻後攻を入れ替えるので、デッキの有利不利と先攻の有利は打ち消える。

    3. 表の行き届き（--coverage）
       学習済みの進め方の表（runs7/policy3_4.json）が、いまのカードプールの
       どれだけを知っているか。ここが0%なら、その表は仕事をしていない。

  使い方
      python skill.py --coverage
      python skill.py --ladder --deck 赤零 --games 600
      python skill.py --ab --budget 0 --games 60
      python skill.py --ab --budget 60 --games 40 --procs 2
      python skill.py --knobs --deck 赤零 --games 400
"""
import argparse
import json
import math
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DEFAULT_DECKS = ["赤零", "火水闇ジャオウガ", "der'Ba", "サイバー", "邪眼帝", "アポロヌス"]


# ------------------------------------------------------------------ 1. 腕くらべ
def ladder(deck_name, games):
    """壁を殴り切るまでのターン数で、操縦を並べる（低いほど上手い）"""
    import solo
    import dmai
    deck, name = solo.load_deck(deck_name)

    def kill(pilot, label, **kn):
        for k, v in kn.items():
            setattr(dmai.DEFAULT, k, v)
        r = solo.run(deck, name, games, pilot, None, 1, 7, None, solo.MAXT, "both", None, True, "blank")
        k2 = r["kill"]
        print(f"  {label:<36} 平均 {k2['mean']:5.2f}T　中央値 {k2['median']:.0f}")
        return k2["mean"]

    print(f"【腕くらべ】{name}／{games}戦／先攻後攻を半分ずつ／壁は受けなし")
    out = {}
    out["random"] = kill("random", "でたらめ（打てる手から一様に選ぶ）")
    out["dmai_rand"] = kill("policy", "dmai の乱数モード（instinct=False）", instinct=False)
    out["instinct"] = kill("policy", "dmai の「勘」（instinct=True）", instinct=True)
    out["greedy"] = kill("greedy", "greedy（決まりだけ・決め打ち）")
    out["plan"] = kill("plan", "plan（1手先読み）")
    print()
    print(f"  乱数モード → 勘：{out['dmai_rand'] - out['instinct']:+.2f}T 速くなった"
          f"（プラスなら勘のほうが上手い。greedy との差は {out['instinct'] - out['greedy']:+.2f}T）")
    return out


# ------------------------------------------------------------------ 2. 直接対決
# 何を比べるか。(A側の知見, B側の知見) を返す
CONTESTS = {
    "instinct": ("勘（instinct）", "乱数",
                 lambda d: (d(instinct=True), d(instinct=False))),
    "target":   ("除去＝危なさ", "除去＝重要度",
                 lambda d: (d(target_threat=True), d(target_threat=False))),
    "control":  ("まったく同じ設定", "まったく同じ設定",
                 lambda d: (d(), d())),
}


def _one(args):
    import dmai
    import decks8
    name, t, budget, seed, what = args
    A, B = CONTESTS[what][2](dmai.Knowledge)
    side = t % 2                     # A がどちらの座席か（毎回入れ替える）
    first = (t // 2) % 2             # 先攻も入れ替える
    kns = (A, B) if side == 0 else (B, A)
    d = dict(decks8.DECKS8[name])
    g = dmai.play(d, dict(d), levels=(budget, budget), knowledge=kns,
                  seed=seed * 1000 + t, first=first)
    return name, (1 if g.winner == side else 0), (0 if g.winner is None else 1)


def ab(decks, games, budget, procs=1, seed=1, what="instinct"):
    """同じデッキ・同じ探索回数で、知見を1つだけ変えて戦わせる。

    `--what control` は**測り方そのものの点検**。まったく同じ設定どうしなので 50% に
    なるはずで、ならなければ座席か先攻の入れ替えが偏っている
    （実測 1799戦で 49.53%±2.3。偏っていない）。"""
    import decks8
    jobs = []
    for nm in decks:
        hit = [n for n in decks8.DECKS8 if nm in n]
        if not hit:
            print(f"  （{nm} に合うデッキがありません）")
            continue
        jobs += [(hit[0], t, budget, seed, what) for t in range(games)]
    if not jobs:
        return {}
    la, lb, _ = CONTESTS[what]
    print(f"【直接対決】{la} vs {lb}／探索回数 {budget}／デッキごとに {games} 戦／"
          f"座席も先攻も入れ替え（{len(jobs)}戦）")
    t0 = time.time()
    res = {}
    if procs > 1:
        with Pool(procs) as pool:
            for name, w, n in pool.imap_unordered(_one, jobs, chunksize=1):
                a = res.setdefault(name, [0, 0])
                a[0] += w
                a[1] += n
    else:
        for j in jobs:
            name, w, n = _one(j)
            a = res.setdefault(name, [0, 0])
            a[0] += w
            a[1] += n
    tw = tn = 0
    for name, (w, n) in sorted(res.items()):
        tw += w
        tn += n
        print(f"  {decks8.short(name):<26} {la}の勝率 {w / n * 100:5.1f}%　（{w}/{n}）")
    half = 1.96 * math.sqrt(0.25 / tn) * 100 if tn else 0
    print(f"  {'合計':<26} {la}の勝率 {tw / tn * 100:5.1f}%　（{tw}/{tn}）　±{half:.1f}ポイント")
    print(f"  （{time.time() - t0:.0f}秒）")
    if tw / tn - 0.5 > half / 100:
        print(f"  → {la} のほうが強い（ばらつきの幅を超えている）")
    elif 0.5 - tw / tn > half / 100:
        print(f"  → {lb} のほうが強い")
    else:
        print("  → 差は、このばらつきの幅の中。戦数を増やさないと言えない")
    return res


# ------------------------------------------------------------------ 3. 表の行き届き
def coverage(path="runs7/policy3_4.json"):
    """学習済みの進め方の表が、いまのカードプールのどれだけを知っているか"""
    import envcards  # noqa: F401
    import decks8
    from cards3 import BY_KEY, POOL
    p = os.path.join(HERE, path)
    if not os.path.exists(p):
        print(f"  表がありません：{p}")
        return
    pol = json.load(open(p, encoding="utf-8"))
    sigs = set()
    for tab in pol.values():
        for k in tab:
            sigs.add(k.split("|", 1)[1])
    keys = {x.split(":")[1] for x in sigs if len(x.split(":")) >= 2 and x.split(":")[1] in BY_KEY}
    names = sorted(decks8.DECKS8)
    known = sum(1 for n in names if n in pol)
    print(f"【表の行き届き】{path}")
    print(f"  表にあるデッキ　　　　：{len(pol)}個（{'・'.join(list(pol)[:3])} …）")
    print(f"  いま配っているデッキ　：{len(names)}個　うち表にあるのは {known}個")
    print(f"  表が知っているカード　：{len(keys)}枚 ／ カードプール {len(POOL)}枚")
    print(f"  表が知らないカード　　：{len(POOL) - len(keys)}枚")
    if known == 0:
        print()
        print("  → この表はいま配っているデッキに1つも当たらない。")
        print("     先読みの中の「最後まで進める」は、表ではなく instinct（勘）が動かしている。")
        print("     使う人がその場で組んだデッキにも表は無いので、勘のほうが本番の道。")


# ------------------------------------------------------------------ 4. つまみを1つずつ振る
def knobs(deck_name, games):
    """「勘」のつまみを1つずつ動かして、腕がどう変わるかを見る"""
    import solo
    import dmai
    deck, name = solo.load_deck(deck_name)
    base = {k: v for k, v in dmai.Knowledge().__dict__.items() if k != "belief"}

    def kill(**kw):
        for k, v in base.items():
            setattr(dmai.DEFAULT, k, v)
        for k, v in kw.items():
            setattr(dmai.DEFAULT, k, v)
        return solo.run(deck, name, games, "policy", None, 1, 7, None, solo.MAXT,
                        "both", None, True, "blank")["kill"]["mean"]

    print(f"【つまみ】{name}／{games}戦。平均ターンが小さいほど上手い")
    b = kill()
    print(f"  {'いまの既定':<40} {b:5.2f}T")
    trials = [("instinct を切る（乱数に戻す）", dict(instinct=False)),
              ("メインを途中でやめる（i_play 0.85）", dict(i_play=0.85)),
              ("攻撃を途中でやめる（i_attack 0.75）", dict(i_attack=0.75)),
              ("マナを見送る（i_charge_hold 0.4）", dict(i_charge_hold=0.4)),
              ("チャージを1割でたらめに（rule 0.9）", dict(p_charge_rule=0.9)),
              ("重要度を軽く見る（w_pri 1.0）", dict(w_pri=1.0)),
              ("重要度を重く見る（w_pri 5.0）", dict(w_pri=5.0)),
              ("プレイヤー攻撃を薄く（w_atk_player 3）", dict(w_atk_player=3.0)),
              ("終える手を厚く（w_end 1.0）", dict(w_end=1.0)),
              ("負けるバトルも辞さない（w_atk_lose 1.0）", dict(w_atk_lose=1.0))]
    for label, kw in trials:
        v = kill(**kw)
        print(f"  {label:<40} {v:5.2f}T　（{v - b:+.2f}）")
    for k, v in base.items():
        setattr(dmai.DEFAULT, k, v)


def main():
    ap = argparse.ArgumentParser(description="操縦の腕を測る")
    ap.add_argument("--ladder", action="store_true", help="壁を殴り切る速さで操縦を並べる")
    ap.add_argument("--ab", action="store_true", help="勘と乱数を直接戦わせる")
    ap.add_argument("--coverage", action="store_true", help="学習済みの表の行き届きを見る")
    ap.add_argument("--knobs", action="store_true", help="つまみを1つずつ振る")
    ap.add_argument("--deck", default="赤零")
    ap.add_argument("--decks", default=",".join(DEFAULT_DECKS))
    ap.add_argument("--games", type=int, default=400)
    ap.add_argument("--budget", type=int, default=0)
    ap.add_argument("--what", default="instinct", choices=sorted(CONTESTS),
                    help="何を比べるか：instinct（勘 vs 乱数）／target（除去の狙いどころ）／"
                         "control（測り方そのものの点検。50%%になるはず）")
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args()
    if not (a.ladder or a.ab or a.coverage or a.knobs):
        a.coverage = a.ladder = True
    if a.coverage:
        coverage()
        print()
    if a.ladder:
        ladder(a.deck, a.games)
        print()
    if a.knobs:
        knobs(a.deck, a.games)
        print()
    if a.ab:
        ab(a.decks.split(","), a.games, a.budget, a.procs, what=a.what)


if __name__ == "__main__":
    main()
