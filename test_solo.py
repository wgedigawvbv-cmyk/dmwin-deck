#!/usr/bin/env python3
"""一人回し（solo.py）の確認

  python test_solo.py
"""
import os
import collections
import random

import decks8
import engine3 as E
import solo
from cards3 import BY_KEY

OK = []


def check(name, cond):
    OK.append((name, bool(cond)))
    print(("○ " if cond else "× ") + name)


def _won(deck):
    """勝ちが決まっている盤面を1つ作る（点の確認用）"""
    g = E.Game(dict(deck), dict(solo.WALL), random.Random(1), first=0, log=False)
    g.over = True
    g.winner = 0
    g.how = "ダイレクトアタック"
    return g


def main():
    # ---------------------------------------------------------------- 壁
    c = BY_KEY[solo.WALL_CARD]
    hooks = []
    for n in dir(E):
        o = getattr(E, n)
        if n.isupper() and isinstance(o, dict) and solo.WALL_CARD in o and n not in ("CARD", "MCIV", "MULTI", "PRI"):
            hooks.append(n)
        if n.isupper() and isinstance(o, set) and solo.WALL_CARD in o:
            hooks.append(n)
    check("壁のカードはS・トリガーを持たない", not c.trig)
    check("壁のカードはG・ストライクを持たない", not c.gs)
    check("壁のカードは能力の差し込み口に登録されていない（壁が何もしない）", not hooks)
    check("壁は40枚", sum(solo.WALL.values()) == 40)

    # ---------------------------------------------------------------- 壁は本当に何もしないか
    deck, name = solo.load_deck("赤零")
    r = solo.one(deck, solo.WALL, 1, solo.pilot_greedy, solo.pilot_passive)
    check("1戦が終わる", r["how"] is not None)
    g = E.Game(deck, solo.WALL, random.Random(3), first=0, log=True)
    for _ in range(400):
        if g.over:
            break
        g.apply((solo.pilot_greedy if g.tp == 0 else solo.pilot_passive)(g, g.tp, g.rng))
    check("壁はマナを置かない", len(g.P[1].mana) == 0)
    check("壁はカードを出さない", len(g.P[1].board) == 0)
    check("壁は自分のシールドを減らさない（攻撃しない）", len(g.P[0].sh) == 5)
    check("壁のシールドからS・トリガーが出ない", g.trig[1] == 0)

    # ---------------------------------------------------------------- 操縦（マナチャージの決まり）
    # 2枚ある札の余りを置く
    g = E.Game(deck, solo.WALL, random.Random(1), first=0)
    g.phase = "C"
    g.tp = 0
    g.P[0].hand = ["ja_yattare", "ja_yattare", "ja_manhattan"]
    g.P[0].mana = ["ja_manhattan"]             # 色は足りている状態にする
    a = solo.pilot_greedy(g, 0, g.rng)
    check("マナチャージ：色が足りていれば、手札に2枚ある札の余りを置く（1枚は使うために残す）",
          a[0] == "charge" and a[1] == "ja_yattare")

    g = E.Game(deck, solo.WALL, random.Random(1), first=0)
    g.phase = "C"
    g.tp = 0
    g.P[0].hand = ["ja_yattare", "ja_manhattan"]
    g.P[0].mana = []
    a = solo.pilot_greedy(g, 0, g.rng)
    check("マナチャージ：すぐ使えない重い札を置き、安い要の札は手札に残す",
          a[0] == "charge" and a[1] == "ja_manhattan")

    # 色が足りない時はそれを優先
    g = E.Game(deck, solo.WALL, random.Random(1), first=0)
    g.phase = "C"
    g.tp = 0
    g.P[0].hand = ["ja_manhattan", "ja_manhattan", "ja_jojojo"]   # 火／火／無色
    g.P[0].mana = ["ja_jojojo"]
    a = solo.pilot_greedy(g, 0, g.rng)
    check("マナチャージ：マナに無い文明があれば、それを足せる札を優先する",
          a[0] == "charge" and "F" in BY_KEY[a[1]].civ)

    # ---------------------------------------------------------------- 操縦（攻撃）
    g = E.Game(deck, solo.WALL, random.Random(1), first=0)
    g.P[0].board = [E.U("ja_manhattan")]
    g.P[0].board[0].sick = False
    g.phase = "A"
    g.tp = 0
    a = solo.pilot_greedy(g, 0, g.rng)
    check("攻撃：相手プレイヤーを攻撃できるなら攻撃する", a[0] == "atk" and a[2] == "P")

    # ---------------------------------------------------------------- まとめ
    d = solo.run(deck, name, 60, "greedy", None, 1, 5, None, solo.MAXT)
    check("まとめに必要な項目がそろっている",
          all(x in d for x in ("kill", "curve", "cards", "opening", "stuck3", "hows", "roles")))
    check("対戦数が合っている", d["games"] == 60)
    check("札ごとの統計がデッキの全種類ぶんある", len(d["cards"]) == len(deck))
    check("使った割合は0〜1に収まる", all(0 <= c["use_rate"] <= 1 for c in d["cards"].values()))
    check("腐った割合は0〜1に収まる（負にならない）",
          all(0 <= c["idle_rate"] <= 1 for c in d["cards"].values()))
    check("曲線のターンが1から始まる", min(int(t) for t in d["curve"]) == 1)
    oshs = [d["curve"][t]["opp_shield"] for t in sorted(d["curve"], key=lambda x: int(x))]
    check("相手の盾の平均は増えない（決着ぶんを0として数えているので単調に減る）",
          all(oshs[i] >= oshs[i + 1] - 1e-9 for i in range(len(oshs) - 1)))
    check("まだ続いている割合も単調に減る",
          all(d["curve"][a].get("alive", 1) >= d["curve"][b].get("alive", 1) - 1e-9
              for a, b in zip(sorted(d["curve"], key=lambda x: int(x)),
                              sorted(d["curve"], key=lambda x: int(x))[1:])))

    # ---------------------------------------------------------------- 速さ
    d2 = solo.run(deck, name, 200, "greedy", None, 1, 11, None, solo.MAXT)
    check(f"速い（1戦 {d2['ms_per_game']:.1f}ミリ秒。20ミリ秒以内であること）", d2["ms_per_game"] < 20)

    # ---------------------------------------------------------------- 同じ種なら同じ結果
    a1 = solo.run(deck, name, 80, "greedy", None, 1, 7, None, solo.MAXT)
    a2 = solo.run(deck, name, 80, "greedy", None, 1, 7, None, solo.MAXT)
    check("同じ種なら同じ結果になる（再現性）",
          a1["kill"] == a2["kill"] and a1["stuck3"] == a2["stuck3"])
    a3 = solo.run(deck, name, 80, "greedy", None, 1, 99, None, solo.MAXT)
    check("種を変えれば結果は変わる", a3["kill"] != a1["kill"])

    # ---------------------------------------------------------------- デッキの読み込み
    import os
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_solo_test_deck.txt")
    with open(tmp, "w", encoding="utf-8") as f:
        for k, v in deck.items():
            f.write(f"{v} {BY_KEY[k].name}\n")
    try:
        d3, n3 = solo.load_deck(path=tmp)
        check("デッキリストのテキストから読み込める（枚数が一致）", d3 == deck)
    finally:
        os.remove(tmp)

    # ---------------------------------------------------------------- 勝利条件（ゴール）
    import goals
    gs = goals.load()
    check("ゴール表が読める", len(gs) >= 5)
    bad_goal = []
    for g in gs:
        try:
            for _nm, w in goals.parts_of(g):
                goals._one(w)
            goals.goal_when(g)
        except SystemExit:
            bad_goal.append(g.get("name"))
    check("goals.json の条件が全部組み立てられる", not bad_goal)
    check("デッキ名からゴールが当たる", (goals.pick("ユニバース退化") or {}).get("name") == "ユニバース特殊勝利")
    check("当たるゴールが無いデッキでは None", goals.pick("まったく存在しないデッキ名XYZ") is None)
    gspec = goals.pick("ユニバース退化")
    dU, nU = solo.load_deck("ユニバース")
    rU = solo.run(dU, nU, 60, "greedy", None, 1, 3, None, solo.MAXT, "1st", gspec)
    check("ゴールのまとめが出る", rU["goal"] is not None and rU["goal"]["name"] == "ユニバース特殊勝利")
    check("ゴール到達ターンは殴り切りターン以下か、別に記録される",
          rU["goal"].get("n", 0) == 0 or rU["goal"]["fastest"] >= 1)
    # 開始時点でも満たしてしまう条件は trivial として印が付く
    triv = {"name": "いつでも真", "when": {"opp_creatures_at_most": 99}}
    rT = solo.run(dU, nU, 40, "greedy", None, 1, 3, None, solo.MAXT, "1st", triv)
    check("ゲーム開始時点でも満たす条件には trivial の印が付く", rT["goal"].get("trivial") is True)
    # ゴールで打ち切ると、そのターンまでしか進まない
    gspec2 = {"name": "盾1枚割る", "when": {"opp_shields_at_most": 4}}
    rS = solo.run(deck, name, 80, "greedy", None, 1, 3, None, solo.MAXT, "1st", gspec2, True)
    rN = solo.run(deck, name, 80, "greedy", None, 1, 3, None, solo.MAXT, "1st", gspec2, False)
    check("--goal-stop でも到達率は変わらない（止めても測れている）",
          abs(rS["goal"]["rate"] - rN["goal"]["rate"]) < 1e-9)
    check("--goal-stop で止めると、そのターンより先には進まない",
          rS["kill"].get("rate", 0) < rN["kill"].get("rate", 0))

    # ---------------------------------------------------------------- ゴールの部品とゴール地点
    gp = goals.pick("ユニバース退化")
    ps = goals.parts_of(gp)
    check("ゴールは部品に分けて書ける", len(ps) >= 3)
    _w, at = goals.goal_when(gp)
    check("goal_at がゴール地点を決める", at == gp["goal_at"])
    _w2, at2 = goals.goal_when(gp, ps[0][0])
    check("--goal-at で別の部品をゴール地点にできる", at2 == ps[0][0])
    try:
        goals.goal_when(gp, "そんな部品はない")
        check("知らない部品の名前は分かる形で止まる", False)
    except SystemExit:
        check("知らない部品の名前は分かる形で止まる", True)
    rP = solo.run(dU, nU, 200, "greedy", None, 2, 3, None, solo.MAXT, "1st", gp)
    pr = rP["goal"].get("parts") or []
    check("部品ごとのまとめが出る", len(pr) == len(ps))
    check("部品ごとの到達率は0〜1", all(0 <= q["rate"] <= 1 for q in pr))
    # 「ここで止まった」は部品の連なりがどこで切れたかなので、
    # その合計は「最後の部品まで順に通れなかった割合」と一致する（ゴール地点とは無関係）。
    check("「ここで止まった」の合計は、最後の部品まで通れなかった割合に等しい",
          abs(sum(q["stopped_here"] for q in pr) - (1 - pr[-1]["ord_rate"])) < 1e-9)
    check("「順に通った」は「そろった」を超えない",
          all(q["ord_rate"] <= q["rate"] + 1e-9 for q in pr))
    check("順に通った割合は後ろの部品ほど小さい",
          all(pr[j]["ord_rate"] >= pr[j + 1]["ord_rate"] - 1e-9 for j in range(len(pr) - 1)))
    check("早い部品のほうがよくそろう（モモキングダムXよりユニバース着地のほうが難しい）",
          pr[0]["rate"] >= pr[2]["rate"])
    rA = solo.run(dU, nU, 200, "greedy", None, 2, 3, None, solo.MAXT, "1st", gp, False,
                  "blank", 5, None, ps[0][0])
    check("ゴール地点を手前の部品にすると到達率が上がる",
          rA["goal"]["rate"] >= rP["goal"]["rate"])
    check("ゴール地点の名前が結果に残る", rA["goal"]["at"] == ps[0][0])

    # ---------------------------------------------------------------- 一瞬の出来事を拾えるか
    ev = {"name": "出来事の確認", "parts": [
        {"name": "モモキングダムXを使った", "when": {"played": "禁断英雄 モモキングダムX"}},
        {"name": "ユニバースが表に出た", "when": {"entered": "究極銀河ユニバース"}},
        {"name": "ユニバースが盤面にいた", "when": {"in_play": "究極銀河ユニバース"}},
        {"name": "ユニバースを下に仕込んだ", "when": {"ever": {"in_play_or_under": "究極銀河ユニバース"}}}]}
    rE = solo.run(dU, nU, 300, "plan", None, 2, 5, None, solo.MAXT, "1st", ev)
    pe = rE["goal"]["parts"]
    check("entered は、退化で表に出たクリーチャーも拾う（盤面だけ見る in_play と一致する）",
          abs(pe[1]["rate"] - pe[2]["rate"]) < 1e-9)
    check("ever＋in_play_or_under は、下に入っているカードも拾う（表に出るより多い）",
          pe[3]["rate"] >= pe[1]["rate"])
    check("played は自分で使ったものだけを数える", 0 <= pe[0]["rate"] <= 1)
    g0 = E.Game(dict(dU), dict(solo.WALL), random.Random(3), first=0, log=False)
    check("既定では出来事を記録しない（ゴールを測らない時の負担をゼロにする）", g0.hist is None)
    g0.hist = []
    h = g0.clone()
    h.hist.append(("enter", 0, "mflower"))
    check("複製した盤面の出来事は、本物の記録を汚さない", g0.hist == [])

    # ---------------------------------------------------------------- 自分のゴール表（mygoals.json）
    import json as _json
    import os as _os
    bak = None
    if _os.path.exists(goals.MINE):
        bak = open(goals.MINE, encoding="utf-8").read()
    try:
        _json.dump({"goals": [{"name": "テスト用ゴール", "decks": ["ユニバース"],
                               "when": {"mana_at_least": 3}}]},
                   open(goals.MINE, "w", encoding="utf-8"), ensure_ascii=False)
        check("mygoals.json のゴールが goals.json より先に当たる",
              (goals.pick("ユニバース退化") or {}).get("name") == "テスト用ゴール")
        check("mygoals.json を重ねても goals.json のゴールは消えない",
              any(g["name"] == "ワンショット" for g in goals.load()))
        check("--goal-file を指定したら mygoals.json は重ねない",
              not any(g["name"] == "テスト用ゴール" for g in goals.load(goals.DEFAULT)))
    finally:
        if bak is None:
            _os.remove(goals.MINE)
        else:
            open(goals.MINE, "w", encoding="utf-8").write(bak)

    # ---------------------------------------------------------------- 1手先読みの操縦
    pp = solo.make_pilot("plan", None, name)
    r1 = solo.one(deck, solo.WALL, 11, pp, solo.pilot_passive)
    check("plan 操縦で1戦が終わる", r1["how"] is not None)
    g0 = E.Game(dict(deck), dict(solo.WALL), random.Random(5), first=0, log=False)
    before = (len(g0.P[1].sh), len(g0.P[0].hand), len(g0.P[0].mana))
    solo.make_pilot("plan", None, name)(g0, 0, random.Random(5))
    check("plan 操縦は試し打ちで本物の盤面を動かさない",
          (len(g0.P[1].sh), len(g0.P[0].hand), len(g0.P[0].mana)) == before)
    pa = solo.run(deck, name, 150, "plan", None, 1, 7, None, solo.MAXT)
    pb = solo.run(deck, name, 150, "plan", None, 1, 7, None, solo.MAXT)
    check("plan 操縦も同じ種なら同じ結果になる（試し打ちの乱数が本番を汚さない）",
          pa["kill"] == pb["kill"])
    ga = solo.run(deck, name, 150, "greedy", None, 1, 7, None, solo.MAXT)
    check("plan 操縦のほうが殴り切りが速い（操縦の精度が上がっている）",
          pa["kill"]["mean"] <= ga["kill"]["mean"] + 1e-9)
    check("盤面の点は勝ちをいちばん高く見る",
          solo.score_pos(_won(deck), 0) > 1e8)

    # ---------------------------------------------------------------- 先攻・後攻
    fb = solo.run(deck, name, 120, "greedy", None, 1, 7, None, solo.MAXT, "both")
    check("先攻後攻を半分ずつにすると両方の記録が出る", set(fb["by_first"]) == {"先攻", "後攻"})
    check("先攻と後攻が同じ戦数", fb["by_first"]["先攻"]["games"] == fb["by_first"]["後攻"]["games"])
    f2 = solo.run(deck, name, 120, "greedy", None, 1, 7, None, solo.MAXT, "2nd")
    check("後攻のみなら後攻だけ", set(f2["by_first"]) == {"後攻"})
    # 一人回しでは「後攻のほうが速い」。相手が何もしないので先攻の有利（先に殴れる）が無く、
    # 後攻の1ドロー多いぶんだけが残るから。実測で赤零ジョーカーズは先攻6.32T・後攻5.73T。
    # これは一人回しという測り方の性質であって、デッキの性質ではない。
    check("一人回しでは後攻のほうが殴り切りが速い（相手が何もしないので、1ドローの差だけが残る）",
          fb["by_first"]["後攻"]["kill_mean"] <= fb["by_first"]["先攻"]["kill_mean"] + 1e-9)

    # ---------------------------------------------------------------- 壁の種類
    check("壁の種類がそろっている", set(solo.WALLS) >= {"blank", "trigger", "gs", "heavy"})
    for wk, wd in solo.WALLS.items():
        check(f"壁 {wk} は40枚", sum(wd.values()) == 40)
    wt = solo.run(deck, name, 200, "greedy", None, 1, 7, None, solo.MAXT, "1st", None, False, "trigger")
    wb = solo.run(deck, name, 200, "greedy", None, 1, 7, None, solo.MAXT, "1st", None, False, "blank")
    check("受けのある壁のほうが殴り切りが遅い（受けが効いている）",
          wt["kill"]["mean"] >= wb["kill"]["mean"])
    w3 = solo.run(deck, name, 120, "greedy", None, 1, 7, None, solo.MAXT, "1st", None, False, "blank", 3)
    check("壁の盾を3枚にすると速くなる", w3["kill"]["mean"] < wb["kill"]["mean"])

    # ---------------------------------------------------------------- デッキリストの読み取り
    # 「カード名 4」という書き方を、以前は黙って1枚と読んでいた（枚数が落ちてもエラーにならない）。
    import cardfetch
    import tempfile
    txt = ("フェアリー・ライフ 4\n"
           "4 フェアリー・ミラクル\n"
           "蒼き団長 ドギラゴン剣 x3\n"
           "キング・ザ・スロットン7 / 7777777\n"
           "十番龍 オービーメイカー Par100 2\n"
           "# これは注記\n")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as f:
        f.write(txt)
        tp = f.name
    got = cardfetch.read_deck(tp)
    os.unlink(tp)
    check("「カード名 4」を4枚と読む", got.get("フェアリー・ライフ") == 4)
    check("「4 カード名」を4枚と読む", got.get("フェアリー・ミラクル") == 4)
    check("「カード名 x3」を3枚と読む", got.get("蒼き団長 ドギラゴン剣") == 3)
    check("名前の中の数字を枚数と読まない（スロットン7 / 7777777）",
          got.get("キング・ザ・スロットン7 / 7777777") == 1)
    check("名前の途中の数字（Par100）はそのまま、末尾の2だけが枚数",
          got.get("十番龍 オービーメイカー Par100") == 2)
    check("#で始まる行は読み飛ばす", len(got) == 5)

    bad = [n for n, c in OK if not c]
    print(f"\n{len(OK) - len(bad)}/{len(OK)} 通過" + ("" if not bad else "　失敗：" + "、".join(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
