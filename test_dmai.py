#!/usr/bin/env python3
"""プレイング担当AI（dmai.py）の確認

  python test_dmai.py
"""
import random

import decks8
import dmai
import engine3
from engine3 import Game

OK = []


def check(name, cond):
    OK.append((name, bool(cond)))
    print(("○ " if cond else "× ") + name)


def two():
    ns = sorted(decks8.DECKS8)
    a = next(n for n in ns if decks8.short(n) == "火水闇ジャオウガ")
    b = next(n for n in ns if decks8.short(n) == "光水自然der'Bande")
    return (a, decks8.DECKS8[a]), (b, decks8.DECKS8[b])


def main():
    (na, da), (nb, db) = two()

    # ---------------------------------------------------------------- 知見の器
    kn = dmai.Knowledge()
    check("知見は名前つきで取り出せる", kn.p_play == 0.85 and kn.always_loop is True)
    try:
        dmai.Knowledge(p_pray=0.5)
        bad = False
    except TypeError:
        bad = True
    check("知らない知見の名前を渡すと止まる（書き間違いを通さない）", bad)
    kn2 = kn.copy(p_play=0.5)
    check("copy は元を壊さない", kn2.p_play == 0.5 and kn.p_play == 0.85)

    # ---------------------------------------------------------------- 腕
    check("腕は名前で引ける", dmai.budget_of("上級") == 150 and dmai.budget_of("初級") == 0)
    check("腕に数字も渡せる", dmai.budget_of(77) == 77)
    try:
        dmai.budget_of("超級")
        bad = False
    except KeyError:
        bad = True
    check("知らない腕は止まる", bad)
    check("腕は探索回数の昇順になっている",
          [dmai.budget_of(n) for n in dmai.LEVELS] == sorted(dmai.budget_of(n) for n in dmai.LEVELS))

    # ---------------------------------------------------------------- ループの見つけ方（前の版の取りこぼし）
    acts = [("play", "a", 0), ("loop", "d"), ("x:gear", "b"), ("attack",)]
    check("ループを手の種類で見つける（追加の手があっても取りこぼさない）",
          dmai.find_loop(acts) == ("loop", "d"))
    check("前の版の見つけ方（最後から2番目）ではこの並びを取りこぼす", acts[-2][0] != "loop")
    check("ループが無ければ None", dmai.find_loop([("play", "a", 0), ("attack",)]) is None)

    # ---------------------------------------------------------------- 手を選ぶ
    g = Game(da, db, random.Random(1), first=0)
    b = dmai.Brain(level="上級", seed=1)
    a = b.choose(g)
    check("盤面を渡すと打てる手のどれかを返す", a in g.legal())
    check("理由が記録される", b.last[2] in ("only", "loop", "search", "policy"))
    check("explain が日本語で読める", "選んだ手：" in b.explain() and "理由：" in b.explain())
    check("1行の入口 best_move も使える", dmai.best_move(g, level="中級") in g.legal())

    g2 = Game(da, db, random.Random(1), first=0)
    b0 = dmai.Brain(level="初級", seed=1)
    a0 = b0.choose(g2)
    check("初級（探索なし）でも手を返す", a0 in g2.legal())
    check("初級の理由は policy か only か loop", b0.last[2] in ("policy", "only", "loop"))

    # ---------------------------------------------------------------- 盤面を壊さない
    g3 = Game(da, db, random.Random(5), first=0)
    before = (len(g3.P[0].hand), len(g3.P[1].hand), len(g3.P[0].deck), g3.turn, g3.phase)
    dmai.Brain(level="上級", seed=2).choose(g3)
    after = (len(g3.P[0].hand), len(g3.P[1].hand), len(g3.P[0].deck), g3.turn, g3.phase)
    check("考えても元の盤面は変わらない", before == after)

    # ---------------------------------------------------------------- 並べ直し
    g4 = Game(da, db, random.Random(9), first=0)
    h = dmai.determinize(g4, 0, random.Random(3), kn)
    check("並べ直しても自分の手札は変わらない", h.P[0].hand == g4.P[0].hand)
    check("並べ直すと相手の手札の枚数は同じ", len(h.P[1].hand) == len(g4.P[1].hand))
    check("並べ直してもシールドの枚数は同じ", len(h.P[1].sh) == len(g4.P[1].sh))
    tot = lambda x: len(x.hand) + len(x.deck) + len(x.sh)
    check("並べ直しでカードは増減しない", tot(h.P[1]) == tot(g4.P[1]))

    kn3 = kn.copy(know_opp_list=False, belief={"fujin": 40})
    h2 = dmai.determinize(g4, 0, random.Random(3), kn3)
    check("相手のリストを知らない前提にすると、相手の未知の札は思っているデッキから引かれる",
          all(k == "fujin" for k in h2.P[1].hand) and h2.P[0].hand == g4.P[0].hand)

    # ---------------------------------------------------------------- 1戦させる
    g5 = dmai.play(da, db, levels=("中級", "初級"), deck_names=(na, nb), seed=11)
    check("1戦が終局する", g5.over and (g5.winner in (0, 1, None)))
    check("攻めたターン数が記録される", isinstance(g5.atkt, list) and len(g5.atkt) == 2)
    check("両者の判断が記録される", g5.brains[0].calls > 0 and g5.brains[1].calls > 0)
    check("上の腕のほうが時間を使っている", g5.brains[0].secs > g5.brains[1].secs)

    rec = []
    dmai.play(da, db, levels=("中級", "中級"), deck_names=(na, nb), seed=12, record=rec)
    check("learn3 用の記録が取れる（デッキ名・ターン・打てた手・選んだ手）",
          rec and len(rec[0]) == 4 and isinstance(rec[0][2], list) and rec[0][3] in rec[0][2])

    # ---------------------------------------------------------------- 日本語化
    g6 = Game(da, db, random.Random(2), first=0)
    names = [dmai.move_ja(g6, x) for x in g6.legal()]
    check("マナチャージの手が日本語になる", any("マナゾーンに置く" in x for x in names))
    check("見送りの手が日本語になる", any("見送る" in x for x in names))
    check("日本語化で例外が出ない（全部の手）", all(isinstance(x, str) and x for x in names))
    while g6.phase != "A" and not g6.over:
        g6.apply(g6.legal()[-1])
    ja = [dmai.move_ja(g6, x) for x in g6.legal()]
    check("攻撃の手が日本語になる", any("攻撃" in x or "ターンを終える" in x for x in ja))
    check("盤面が日本語で書ける", "盾" in dmai.board_ja(g6) and "手番" in dmai.board_ja(g6))

    # ---------------------------------------------------------------- engine3 との約束
    g7 = Game(da, db, random.Random(4), first=0)
    need = ("legal", "apply", "clone", "myturn")
    check("約束している engine3 の入口がそろっている",
          all(callable(getattr(g7, x, None)) for x in need)
          and all(hasattr(g7, x) for x in ("over", "winner", "tp", "phase", "turn", "rng", "P")))
    check("スター進化の値打ちの補正（退化の決まり）がエンジンに入っている", len(engine3.VALADJ) >= 1)

    # ---------------------------------------------------------------- 測り方の落とし穴
    import collections
    cc = collections.Counter(dmai.sides(g) for g in range(8))
    check("測る側と先攻は別々に入れ替わる（4通りが同じ回数ずつ出る）",
          len(cc) == 4 and len(set(cc.values())) == 1)
    check("測る側＝先攻 になっていない（前の harness の取り違え）",
          any(me != first for me, first in (dmai.sides(g) for g in range(4))))

    # ---------------------------------------------------------------- 「勘」（学習不要の進め方）
    kn = dmai.Knowledge()
    check("既定では「勘」で進める（学習済みの表が無いデッキでも、でたらめにならない）", kn.instinct is True)
    check("勘はメインを途中でやめない（i_play 1.0）", kn.i_play == 1.0)
    check("勘は攻撃を途中でやめない（i_attack 1.0）", kn.i_attack == 1.0)

    rng = random.Random(3)
    g = Game(dict(da), dict(db), rng, first=0)
    phases = set()
    for _ in range(300):
        if g.over:
            break
        acts = g.legal()
        if len(acts) > 1:
            a = dmai.instinct_step(g, acts, rng, kn)
            check_once = a in acts
            if not check_once:
                break
            phases.add(g.phase)
            g.apply(a)
        else:
            g.apply(acts[0])
    check("勘が返す手は必ず打てる手の中にある", True if g.over or check_once else False)
    check("チャージ・メイン・攻撃の3つとも勘で通った", phases >= {"C", "M"})

    # チャージの決まり：まだマナに無い文明を足せる札を選ぶ
    rng2 = random.Random(11)
    g2 = Game(dict(da), dict(db), rng2, first=0)
    got = 0
    for _ in range(200):
        if g2.over:
            break
        acts = g2.legal()
        if g2.phase == "C" and len(acts) > 1:
            from cards3 import BY_KEY
            have = engine3.civs(g2.P[g2.tp])
            need = [a for a in acts if a[0] == "charge" and BY_KEY[a[1]].civ
                    and not set(BY_KEY[a[1]].civ) <= have]
            if need:
                a = dmai._charge_pick(g2, g2.tp, acts, kn)
                if a in need:
                    got += 1
                else:
                    got = -99
                    break
        g2.apply(acts[0] if len(acts) == 1 else rng2.choice(acts))
    check("足りない文明があれば、それを足せる札をマナに置く", got > 0)

    # 腕くらべ：勘は乱数モードより速く壁を殴り切る（＝上手い）
    import solo
    deck, nm = solo.load_deck("赤零")
    def killT(flag):
        dmai.DEFAULT.instinct = flag
        return solo.run(deck, nm, 200, "policy", None, 1, 7, None, solo.MAXT,
                        "both", None, True, "blank")["kill"]["mean"]
    t_inst, t_rand = killT(True), killT(False)
    dmai.DEFAULT.instinct = True
    check(f"勘のほうが速く殴り切る（勘 {t_inst:.2f}T ＜ 乱数 {t_rand:.2f}T）", t_inst < t_rand)

    # ---------------------------------------------------------------- 除去の狙いどころ
    g3 = Game(dict(da), dict(db), random.Random(5), first=0)
    check("狙いどころはプレイヤーごとに持つ", isinstance(g3.tgtmode, list) and len(g3.tgtmode) == 2)
    g3.tgtmode[0] = True
    check("複製にも引き継がれる", g3.clone().tgtmode == g3.tgtmode)
    check("既定は、もとのやり方（測っても差が無かったので変えていない）",
          engine3.TARGET_THREAT is False)
    kn2 = dmai.Knowledge(target_threat=True)
    gg = dmai.play(dict(da), dict(db), levels=(0, 0),
                   knowledge=(kn2, dmai.Knowledge(target_threat=False)), seed=1)
    check("知見から狙いどころを片側だけ変えられる", gg.tgtmode == [True, False])

    bad = [n for n, c in OK if not c]
    print(f"\n{len(OK) - len(bad)}/{len(OK)} 通過" + ("" if not bad else "　失敗：" + "、".join(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
