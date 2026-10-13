#!/usr/bin/env python3
r"""一人回し（ひとりまわし）— あなたのデッキを高速で何千回も回して、デッキのデータを取る

  このシミュレーターの本題。「このデッキは何ターン目に目的を達成するのか」「どの札が腐るのか」
  「初手はどれくらい動けるのか」を、**相手の妨害抜きでデッキ自身の性能として**測る。

  ■ 一人回しとは
  相手は「シールドの壁」で、何もしない（マナも置かず、カードも使わず、攻撃もしない）。
  既定の壁は能力を1つも持たないカード（マリン・フラワー）だけなので、**S・トリガーも出ない**。
  つまり測るのは**あなたのデッキの素の速さと安定性**だけ。
  受けのある相手でどうなるかは --wall trigger などで足せる（下の【壁の種類】）。
  相手の妨害を含めた強さを測りたい時は、総当たり（matrix8.py）や dmai を使う。

  ■ 測るもの＝デッキごとの勝利条件（ゴール）
  既定では「相手の盾を割り切ってダイレクトアタックするまでのターン数」を測るが、
  **デッキの目的がそれではない**デッキでは意味を持たない（ユニバースの特殊勝利、ループ、コントロール）。
  goals.json に「このデッキが目指している状態」を書くと、それに届いたターンも一緒に測る。
  デッキ名から自動で当たる（python goals.py --list / --check デッキ名）。書き方は goals.py の説明。

  ■ 先攻・後攻（測り方のくせ）
  一人回しでは **後攻のほうが速い**。相手が何もしないので「先に殴れる」という先攻の有利が無く、
  後攻が1枚多く引けるぶんだけが残るから（実測で赤零ジョーカーズは先攻6.32T・後攻5.73T）。
  これは一人回しという測り方の性質で、デッキの性質ではない。既定は先攻のみ。
  --first both で半分ずつにすると、この偏りが打ち消されてデッキ同士の比較が素直になる。

  ■ 速さ
  探索（先読み）を使わないので **1戦あたり約5ミリ秒**。5000戦で30秒ほど（1コア）。
  --pilot plan（1手先読み）は1戦あたり数十ミリ秒かかるが、操縦の腕が上がるぶん数字が実戦に近づく。
  操縦は「どのデッキにも同じ」決まりで動く（下の pilot を参照）。デッキごとの作戦は書かない。

  ■ 使い方（PowerShell）
    # 実装済みのデッキ名で（名前の一部でよい）
    python solo.py --deck 赤零 --games 3000

    # 自分のデッキリストのファイルで（「4 カード名」の行が並んだテキスト、または decks8 形式のJSON）
    python solo.py --deck-file mydeck.txt --games 3000 --out runs8\solo_mydeck.json

    # 先攻・後攻を半分ずつにする（既定は先攻だけ。実戦に近づけるならこちら）
    python solo.py --deck 赤零 --first both --games 3000

    # 1手先読みの操縦で測る（精度が上がる。遅くなる）
    python solo.py --deck 赤零 --pilot plan --games 1000

    # 受けのある壁を相手にする
    python solo.py --deck 赤零 --wall trigger --games 2000

    # ゴールを指定する／自動で当たったゴールを使わない
    python solo.py --deck 赤零 --goal ワンショット --games 2000
    python solo.py --deck ユニバース --no-goal --games 2000

    # 2つのデッキを比べる
    python solo.py --deck 赤零 --compare 火水闇ジャオウガ --games 3000

    # 1枚入れ替えると何が変わるかを測る（抜く札→入れる札）
    python solo.py --deck 赤零 --swap "ジョジョジョ・ジョーカーズ=ヤッタレマン" --games 3000

    # 操縦を変える／相手を壁でなく本物にする
    python solo.py --deck 赤零 --pilot policy --games 2000
    python solo.py --deck 赤零 --vs 火水闇ジャオウガ --games 300

    python solo.py --show runs8\solo_mydeck.json      保存した結果を読み直す
    python solo.py --pilot-ab 赤零 --games 600         操縦のちがいを測る（greedy と plan の比べ）

  ■ 壁の種類（--wall）
    blank    （既定）能力を1つも持たない壁。S・トリガーもG・ストライクも無い＝素の速さを測る
    trigger  40枚のうち8枚が《終末の時計 ザ・クロック》。5枚の盾に平均1枚の受けが混ざる
    gs       40枚のうち8枚がG・ストライク持ち。攻撃を1回止められる受け
    heavy    S・トリガーとG・ストライクを両方多めに。受けの厚い相手に押し切れるかを見る
    --wall-shields N で壁の盾の枚数も変えられる（既定5）

  ■ 取れるデータ
    ・ゴールに届くターン（分布・中央値・Nターン目までに届く割合）／殴り切るターン
    ・ターンごとの相手のシールドの残り枚数（一人回しの曲線）
    ・ターンごとの自分のマナ・手札・バトルゾーンの数
    ・初手の質（マナを置けるか、2〜3ターン目に動けるか、使える札が何枚あるか）
    ・札ごとの統計（使われた割合／平均で何ターン目に使われたか／手札で腐った割合／マナに置かれた割合）
    ・事故率（3ターン目まで何も出せなかった割合、色が足りなくて使えなかった回数）
    ・決まり方の内訳（ダイレクトアタック・特殊勝利・山札切れ・時間切れ）
    ・先攻／後攻ごとの差
    ・役割の充足（roles3）
"""
import argparse
import collections
import json
import os
import random
import statistics
import sys
import time

import engine3 as E
from cards3 import BY_KEY

HERE = os.path.dirname(os.path.abspath(__file__))
WALL_CARD = "mflower"      # 壁に使うカード（能力を1つも持たない。S・トリガーもG・ストライクも無い）
WALL = {WALL_CARD: 40}

# 壁の種類。受けの量を変えて「押し切れるか」を見るため。
#   clock  《終末の時計 ザ・クロック》 S・トリガー。出るとターンの残りをとばす（攻撃が止まる）
#   fujin  《鬼星の絆 フウジン天＆ライジン天》 G・ストライク。攻撃を1回止める
WALLS = {
    "blank":   {WALL_CARD: 40},
    "trigger": {WALL_CARD: 32, "clock": 8},
    "gs":      {WALL_CARD: 32, "fujin": 8},
    "heavy":   {WALL_CARD: 24, "clock": 8, "fujin": 8},
}


# ------------------------------------------------------------------ デッキを読む
def load_deck(name=None, path=None):
    """{カードのキー: 枚数} と表示名を返す"""
    import decks8
    if path:
        import cardfetch
        raw = cardfetch.read_deck(path)
        idx = decks8._index()
        deck, miss = {}, []
        for nm, v in raw.items():
            k = decks8.find(nm, idx)
            if k is None:
                miss.append(nm)
            else:
                deck[k] = deck.get(k, 0) + v
        if miss:
            raise SystemExit("未実装のカードがあります：" + "、".join(miss)
                             + "\n  python cardfetch.py --missing-text " + path + " で調べてください")
        return deck, os.path.basename(path)
    ns = sorted(decks8.DECKS8)
    hit = [n for n in ns if name in n or name in decks8.short(n)]
    if not hit:
        import archetypes
        from cards3 import DECKS
        for src in (DECKS, {k: v["deck"] for k, v in archetypes.ARCHETYPES.items()}):
            h = [n for n in src if name in n]
            if h:
                return dict(src[h[0]]), h[0]
        raise SystemExit(f"『{name}』に合うデッキがありません（python solo.py --decks で一覧）")
    exact = [n for n in hit if decks8.short(n) == name]
    n = (exact or hit)[0]
    return dict(decks8.DECKS8[n]), decks8.short(n)


def make_wall(kind="blank", shields=5):
    """壁のデッキを返す。kind は WALLS のどれか、または実装済みのデッキ名"""
    if kind in WALLS:
        return dict(WALLS[kind]), f"壁（{kind}／盾{shields}）"
    d, nm = load_deck(kind)
    return d, f"{nm}（何もしない／盾{shields}）"


# ------------------------------------------------------------------ 操縦（どのデッキにも同じ決まり）
def charge_greedy(g, i, acts):
    """マナチャージの決まり。plan 操縦でもここを共用する。

      (1) まだマナに無い文明があれば、それを足せる札から選ぶ（色が揃うのが最優先）。
      (2) 手札に2枚以上ある札があれば、その余りを置く（1枚は使うために残す）。
      (3) それも無ければ、**いま使えず・すぐにも使えない札**（コストがマナ＋2より重い札）のうち
          いちばん重い札を置く。
      (4) どれも当てはまらなければ、いちばん重い札を置く。
      ※「重要度のいちばん低い札を置く」という単純な規則にすると、**2マナの加速札のような
         安くて軽い要の札を自分でマナに埋めてしまう**（実測でヤッタレマンが7割マナ行きになった）。
      ※先読み（plan）はチャージには効かない。1手先ではどのカードを置いても盤面の点がほぼ同じで、
        差が出るのは数ターン後だから。だからチャージだけは人が書いた決まりを使う。"""
    p = g.P[i]
    ch = [a for a in acts if a[0] == "charge"]
    if not ch:
        return acts[-1]
    have = E.civs(p)
    cand = [a for a in ch if not set(BY_KEY[a[1]].civ) <= have and BY_KEY[a[1]].civ]
    if not cand:                               # 色は足りている
        cand = ch
    cnt = collections.Counter(p.hand)
    dup = [a for a in cand if cnt[a[1]] >= 2]  # 2枚以上ある札の余りから置く
    if dup:
        return max(dup, key=lambda a: BY_KEY[a[1]].cost)
    av = len(p.mana)                           # このターンの後のマナの枚数
    far = [a for a in cand if BY_KEY[a[1]].cost > av + 2]   # すぐには使えない重い札
    if far:
        return max(far, key=lambda a: BY_KEY[a[1]].cost)
    return max(cand, key=lambda a: BY_KEY[a[1]].cost)


def pilot_greedy(g, i, rng):
    """探索しない操縦。デッキごとの作戦は書かず、次の決まりだけで動く。

      マナチャージ：charge_greedy（上）
      メイン      ：使える札のうち、重要度のいちばん高いものを使う。使えなくなるまで繰り返す。
      攻撃        ：相手プレイヤーを攻撃できるものは全部攻撃する。
                    クリーチャーしか攻撃できないものは、倒せる相手がいれば攻撃する。

    これは「人が考える最善手」ではない。**どのデッキにも同じやり方を当てる**ための決まりで、
    デッキ間の比較が操縦の差で狂わないようにするためのもの。"""
    acts = g.legal()
    if len(acts) == 1:
        return acts[0]
    ph = g.phase
    if ph == "C":
        return charge_greedy(g, i, acts)
    if ph == "M":
        lp = next((a for a in acts if a[0] == "loop"), None)
        if lp is not None:
            return lp
        use = [a for a in acts if a[0] in ("play", "spell", "gal", "zen", "gigan", "abyss")
               or str(a[0]).startswith("x:")]
        if use:
            def w(a):
                k = a[1] if len(a) > 1 and isinstance(a[1], str) else None
                return E.PRI.get(k, 0) if k else 0
            return max(use, key=w)
        return acts[-1]                            # ("attack",)
    # 攻撃フェイズ
    atk = [a for a in acts if a[0] == "atk"]
    if not atk:
        return acts[-1]
    pl = [a for a in atk if a[2] == "P"]
    if pl:
        return pl[0]
    best, bv = None, None
    for a in atk:                                  # クリーチャーを殴るなら、倒せる相手のうち重要度が高いもの
        t = g.P[1 - i].board[a[2]]
        u = g.P[i].board[a[1]]
        if g.power(i, u, True) < g.power(1 - i, t):
            continue
        v = g.val(t)
        if bv is None or v > bv:
            best, bv = a, v
    return best if best is not None else acts[-1]


# ------------------------------------------------------------------ 1手先読みの操縦（精度を上げる）
# 盤面の点の重み。plan 操縦の「良い盤面」の決め方。どのデッキにも同じ重みを当てる。
#   osh    相手の盾1枚（負）        盾を減らすのが目的に最も近いので、いちばん重い
#   msh    自分の盾1枚
#   cre    自分のクリーチャー1体
#   pw     自分のパワー1000あたり
#   brk    自分の打点（割れる盾）1枚
#   ready  すぐ殴れる面（タップしていない・出たターンでない）
#   atkp   相手プレイヤーを殴れる面（打点ぶんを重ねて数える）
#   under  下に敷かれたカード1枚（進化元・マナドライブなど）
#   seed   自分のタマシード・城など1枚
#   ocre   相手のクリーチャー1体（負）
#   opw    相手のパワー1000あたり（負）
#   hand   手札1枚               ※大きすぎると「打たずに抱える」のが得になる（実測で動かなくなった）
#   mana   マナの総枚数
#   idle   使わずに余ったマナ1枚（負）  ※マナを使い切る方へ押す。手札を減らす損を打ち消す役
#   goal   ゴールに届いた盤面
W = {"osh": -300.0, "msh": 40.0, "cre": 90.0, "pw": 1 / 170.0, "brk": 25.0, "ready": 20.0,
     "atkp": 35.0, "under": 8.0, "seed": 40.0, "ocre": -70.0, "opw": -1 / 220.0,
     "hand": 10.0, "mana": 10.0, "idle": -3.0, "goal": 5000.0}


def hits_player(g, i, u):
    """このクリーチャーは今このターン、相手プレイヤーを攻撃できるか（engine の判定を軽く写したもの）

    これが無いと、1手先しか見ない操縦は「このターン相手プレイヤーを攻撃できる」を与える札の
    値打ちが見えない。実測で《勝熱と弾丸と自由の決断》（本来プレイヤーを攻撃できない
    《ポクチンちん》に攻撃を許す呪文）の使用率が0%に落ちていた。"""
    c = u.c
    if c.kind != "C" or u.tap:
        return False
    ign = bool(E.NOATKIGN) and any(f(g, i, u) for f in E.NOATKIGN)
    if (c.noatk and not ign) or (u.lock == g.turn and not ign):
        return False
    if u.k in E.CANTATK and E.CANTATK[u.k](g, i, u):
        return False
    if any(f(g, i, u) for f in E.ATKLOCK):
        return False
    full = ((not u.sick) or u.sa or c.sa or g.has(i, "jaouga") or bool(c.evo and u.under)
            or bool(E.SAOK and any(f(g, i, u) for f in E.SAOK)))
    if not full:
        return False
    if (c.noatkp and not ign) or (E.NOATKPX and any(f(g, i, u) for f in E.NOATKPX)):
        return False
    return True


def score_pos(g, i, goal=None):
    """盤面の点。i から見て高いほど良い。**どのデッキにも同じ式**を当てる（重みは W）。

    一人回しの目的は「このデッキが自分の目的にどれだけ速く届くか」なので、
    相手の盾を減らすことにいちばん重い点を置き、次に盤面の面と打点、手札とマナを足す。
    ゴール（goals.json）が指定されていれば、届いた盤面に大きな点を足す。

    ※手札の点を高くしすぎると、1手先しか見ない操縦は**何も打たずに抱える**のが得になる。
      実測で hand=25 にしたら赤零ジョーカーズの《勝熱と弾丸と自由の決断》の使用率が
      65%から0%に落ち、3ターン目まで何も出せない割合が2.7%から21%に悪化した。
      そこで手札は軽くし、「余ったマナ」に負の点を置いて使い切る方へ押している。"""
    if g.over:
        return 1e9 if g.winner == i else -1e9
    p, q = g.P[i], g.P[1 - i]
    sc = W["osh"] * len(q.sh) + W["msh"] * len(p.sh)
    for u in p.board:
        if u.c.kind == "C":
            sc += W["cre"] + g.power(i, u) * W["pw"] + W["brk"] * g.brk(i, u)
            if not u.tap and not u.sick:
                sc += W["ready"]
            if hits_player(g, i, u):               # 相手プレイヤーを殴れる面（これが勝ちに直結する）
                sc += W["atkp"] + W["brk"] * g.brk(i, u)
            sc += W["under"] * len(u.under)
        else:
            sc += W["seed"]
    for u in q.board:
        if u.c.kind == "C":
            sc += W["ocre"] + g.power(1 - i, u) * W["opw"]
        else:
            sc -= 30
    sc += W["hand"] * len(p.hand)
    sc += W["mana"] * len(p.mana) + W["idle"] * (len(p.mana) - p.mused)
    if goal is not None:
        try:
            if goal(g, i):
                sc += W["goal"]
        except Exception:                          # noqa: BLE001
            pass
    return sc


def make_plan_pilot(goal=None, seed=0):
    """1手先読みの操縦を返す。

    手を1つずつ実際に試して（盤面を複製して打つ）、できた盤面の点がいちばん高い手を選ぶ。
    greedy の決まりが取りこぼすものを拾える。
      ・出た時の効果（引く・壊す・マナを増やす）が、コストの重さと別に評価される
        → greedy は「重要度＝コスト」で並べるので、軽くて強い札を後回しにしていた
      ・攻撃がブロッカーで止まる・相打ちで損をする、という結果が見える
      ・S・トリガーを踏んで損をする手（--wall trigger の時）を避けられる
    チャージだけは先読みが効かない（1手先では差が出ない）ので charge_greedy を使う。

    複製した盤面は**別の乱数**で回す。そうしないと試し打ちが本番の乱数を進めてしまい、
    同じ種をまいても結果が変わる（再現できなくなる）。"""
    probe = random.Random(seed)

    def f(g, i, rng):
        acts = g.legal()
        if len(acts) == 1:
            return acts[0]
        if g.phase == "C":
            return charge_greedy(g, i, acts)
        lp = next((a for a in acts if a[0] == "loop"), None)
        if lp is not None:
            return lp
        best, bv = acts[0], None
        for a in acts:
            h = g.clone(probe)
            try:
                h.apply(a)
            except Exception:                      # noqa: BLE001  試し打ちで壊れた手は選ばない
                continue
            v = score_pos(h, i, goal)
            if bv is None or v > bv:
                best, bv = a, v
        return best
    return f


def pilot_passive(g, i, rng):
    """壁：何もしない（マナも置かず、カードも使わず、攻撃もしない）"""
    acts = g.legal()
    if len(acts) == 1:
        return acts[0]
    if g.phase == "C":
        return next((a for a in acts if a[0] == "skip"), acts[-1])
    if g.phase == "M":
        return next((a for a in acts if a[0] == "attack"), acts[-1])
    return next((a for a in acts if a[0] == "end"), acts[-1])


def make_pilot(kind, policy, deck_name, goal=None):
    """操縦を返す。
       greedy （既定）決まりだけで動く／plan 1手先読み／policy 学習済みの進め方／random でたらめ"""
    if kind == "greedy":
        return pilot_greedy
    if kind == "plan":
        return make_plan_pilot(goal)
    if kind == "random":
        return lambda g, i, rng: rng.choice(g.legal())
    if kind == "policy":
        import dmai
        pol = dmai._load_policy(policy) if policy and os.path.exists(policy) else {}
        tab = pol.get(deck_name)

        def f(g, i, rng):
            acts = g.legal()
            return acts[0] if len(acts) == 1 else dmai.one_step(g, acts, rng, tab)
        return f
    raise SystemExit(f"知らない操縦：{kind}")


# ------------------------------------------------------------------ 1戦まわして記録を取る
MAXT = 20          # これより長引いたら「決まらなかった」として打ち切る（自分のターン数）


def one(deck, opp, seed, pilot, opp_pilot, maxt=MAXT, first=0, goal_spec=None,
        goal_stop=False, wall_shields=5, goal_at=None):
    """1戦して記録を返す。自分はプレイヤー0。first=0 なら自分が先攻、1 なら後攻"""
    import goals
    rng = random.Random(seed)
    g = E.Game(deck, opp, rng, first=first, log=False)
    if goal_spec is not None:
        g.hist = []            # ゴールの entered / played を測るため、出来事を書き留める
    if wall_shields != 5:                          # 壁の盾の枚数を変える
        q = g.P[1]
        while len(q.sh) > wall_shields:
            q.deck.append(q.sh.pop()[0])
        while len(q.sh) < wall_shields and q.deck:
            q.sh.append((q.deck.pop(), False))
    g.hold = [0, 0]
    g.atkt = [0, 0]
    tr = goals.Tracker(goal_spec, goal_at) if goal_spec else None
    r = {"played": [], "turns": [], "opening": None, "dead_civ": 0, "first": first}
    seen_hand = set()
    while not g.over and g.myturn(0) <= maxt:
        i = g.tp
        if g.phase == "C" and i == 0:              # 自分のターンのはじめの状態を記録
            if r["opening"] is None:
                r["opening"] = sorted(g.P[0].hand)
            r["turns"].append({"t": g.myturn(0), "mana": len(g.P[0].mana), "hand": len(g.P[0].hand),
                               "board": sum(1 for u in g.P[0].board if u.c.kind == "C"),
                               "osh": len(g.P[1].sh)})
            seen_hand |= set(g.P[0].hand)
        a = (pilot if i == 0 else opp_pilot)(g, i, rng)
        if i == 0 and a[0] in ("play", "spell") and isinstance(a[1], str):
            r["played"].append((a[1], g.myturn(0)))
        g.apply(a)
        if tr is not None and tr.check(g, 0) and goal_stop:
            break
    r["win"] = (g.winner == 0)
    r["how"] = g.how if g.over else "決まらなかった"
    r["kill_turn"] = g.myturn(0) if (g.winner == 0) else None
    r["goal_turn"] = tr.turn if tr is not None else None
    r["goal_parts"] = tr.parts() if tr is not None else None
    r["last_turn"] = g.myturn(0)
    r["osh_end"] = len(g.P[1].sh)
    r["left_hand"] = sorted(g.P[0].hand)
    r["in_mana"] = sorted(g.P[0].mana)
    r["seen"] = sorted(seen_hand)
    r["decked"] = (g.how == "山札切れ")
    return r


def job(args):
    deck, opp, seed, kind, policy, name, maxt, first, goal_spec, goal_stop, wsh, gat = args
    gf = None
    if goal_spec and kind == "plan":
        import goals
        gf = goals._one(goals.goal_when(goal_spec, gat)[0])
    pilot = make_pilot(kind, policy, name, gf)
    return one(deck, opp, seed, pilot, pilot_passive, maxt, first, goal_spec, goal_stop, wsh, gat)


# ------------------------------------------------------------------ まとめる
def _turnstats(vals, n, maxt=MAXT):
    """ターンの一覧から、中央値・分布・Nターン目までに届く割合をまとめる"""
    out = {"n": len(vals)}
    if not vals:
        return out
    ks = sorted(vals)
    out.update({
        "rate": len(ks) / n,
        "mean": sum(ks) / len(ks), "median": statistics.median(ks),
        "fastest": ks[0], "slowest": ks[-1],
        "sd": statistics.pstdev(ks) if len(ks) > 1 else 0.0,
        "by_turn": {t: sum(1 for x in ks if x <= t) / n for t in range(1, maxt + 1)},
        "hist": dict(sorted(collections.Counter(ks).items())),
    })
    return out


def summarize(deck, name, rs, meta):
    n = len(rs)
    kills = [r["kill_turn"] for r in rs if r["kill_turn"] is not None]
    out = {"name": name, "games": n, "deck": deck,
           "names": {k: BY_KEY[k].name for k in deck}, **meta}
    out["win_rate"] = sum(1 for r in rs if r["win"]) / n
    out["kill"] = _turnstats(kills, n)
    gts = [r["goal_turn"] for r in rs if r.get("goal_turn") is not None]
    if meta.get("goal_name"):
        out["goal"] = _turnstats(gts, n)
        out["goal"]["name"] = meta["goal_name"]
        out["goal"]["label"] = meta.get("goal_label", "")
        out["goal"]["at"] = meta.get("goal_at", "")
        # 部品ごと：何割の対戦でそろったか・平均で何ターン目か・どこで崩れたか
        pn = [p0[0] for p0 in (rs[0].get("goal_parts") or [])]
        parts = []
        for j, nm in enumerate(pn):
            ts = [r["goal_parts"][j][1] for r in rs
                  if r.get("goal_parts") and r["goal_parts"][j][1] is not None]
            os_ = [r["goal_parts"][j][2] for r in rs
                   if r.get("goal_parts") and r["goal_parts"][j][2] is not None]
            parts.append({"name": nm, "rate": len(ts) / n,
                          "mean": (sum(ts) / len(ts)) if ts else None,
                          "median": statistics.median(ts) if ts else None,
                          "ord_rate": len(os_) / n,
                          "ord_mean": (sum(os_) / len(os_)) if os_ else None,
                          "skipped": (len(ts) - len(os_)) / n,
                          "by_turn": {t: sum(1 for x in ts if x <= t) / n for t in range(1, MAXT + 1)}})
        # 「どこで止まったか」は**順に通った**ほうで数える（道筋として正しいのはこちら）
        stop = collections.Counter()
        for r in rs:
            gp = r.get("goal_parts") or []
            last = -1
            for j, t3 in enumerate(gp):
                if t3[2] is not None:
                    last = j
                else:
                    break
            if last + 1 < len(pn):
                stop[pn[last + 1]] += 1
        for q in parts:
            q["stopped_here"] = stop.get(q["name"], 0) / n
        out["goal"]["parts"] = parts
        out["goal"]["ordered"] = bool(meta.get("goal_ordered", True))
        # ゲーム開始時点でも満たしてしまう条件は、測っても意味がない。気づけるようにしておく。
        out["goal"]["trivial"] = bool(gts) and len(gts) / n > 0.9 and statistics.median(gts) <= 1
    else:
        out["goal"] = None
    # 先攻／後攻ごとの差
    fs = {}
    for f in (0, 1):
        sub = [r for r in rs if r.get("first", 0) == f]
        if not sub:
            continue
        kk = [r["kill_turn"] for r in sub if r["kill_turn"] is not None]
        gg = [r["goal_turn"] for r in sub if r.get("goal_turn") is not None]
        fs["先攻" if f == 0 else "後攻"] = {
            "games": len(sub),
            "win_rate": sum(1 for r in sub if r["win"]) / len(sub),
            "kill_mean": (sum(kk) / len(kk)) if kk else None,
            "kill_rate": len(kk) / len(sub),
            "goal_mean": (sum(gg) / len(gg)) if gg else None,
            "goal_rate": len(gg) / len(sub),
            "stuck3": sum(1 for r in sub if not any(t <= 3 for _k, t in r["played"])) / len(sub),
        }
    out["by_first"] = fs
    # ターンごとの平均。
    # 決着した対戦は「そのターン以降も相手の盾は0」として数える（そうしないと
    # 速いデッキで決着した分が平均から抜けて、盾が増えたように見える＝生存バイアス）。
    per = collections.defaultdict(list)
    osh = collections.defaultdict(list)
    for r in rs:
        for t in r["turns"]:
            per[t["t"]].append(t)
            osh[t["t"]].append(t["osh"])
        end = r["last_turn"]
        rest = 0 if r["win"] else r["osh_end"]
        for t in range(end + 1, MAXT + 1):
            osh[t].append(rest)
    out["curve"] = {t: {"mana": sum(x["mana"] for x in v) / len(v),
                        "hand": sum(x["hand"] for x in v) / len(v),
                        "board": sum(x["board"] for x in v) / len(v),
                        "opp_shield": sum(osh[t]) / len(osh[t]),
                        "alive": len(v) / n}
                    for t, v in sorted(per.items()) if t <= MAXT}
    # 札ごとの統計
    cs = {}
    for k, v in deck.items():
        cs[k] = {"copies": v, "name": BY_KEY[k].name, "cost": BY_KEY[k].cost,
                 "used": 0, "turns": [], "left": 0, "mana": 0, "seen": 0, "idle": 0}
    for r in rs:
        done = {k for k, _t in r["played"]}
        for k, t in r["played"]:
            if k in cs:
                cs[k]["turns"].append(t)
        for k in done:
            if k in cs:
                cs[k]["used"] += 1
        for k in set(r["left_hand"]):
            if k in cs:
                cs[k]["left"] += 1
        for k in set(r["in_mana"]):
            if k in cs:
                cs[k]["mana"] += 1
        for k in r["seen"]:
            if k in cs:
                cs[k]["seen"] += 1
                if k not in done:                  # 手札に来たのに一度も使わなかった
                    cs[k]["idle"] += 1
    for k, c in cs.items():
        c["use_rate"] = c["used"] / n
        c["avg_turn"] = (sum(c["turns"]) / len(c["turns"])) if c["turns"] else None
        c["left_rate"] = c["left"] / n
        c["mana_rate"] = c["mana"] / n
        c["seen_rate"] = c["seen"] / n
        c["idle_rate"] = c["idle"] / n             # 手札に来たのに使えなかった対戦の割合
        del c["turns"]
    out["cards"] = cs
    # 初手の質
    opens = [r["opening"] or [] for r in rs]
    out["opening"] = {
        "avg_castable_t3": sum(sum(1 for k in o if BY_KEY[k].cost <= 3) for o in opens) / n,
        "no_1or2": sum(1 for o in opens if not any(BY_KEY[k].cost <= 2 for k in o)) / n,
        "all_heavy": sum(1 for o in opens if all(BY_KEY[k].cost >= 5 for k in o) and o) / n,
    }
    # 事故率
    out["stuck3"] = sum(1 for r in rs if not any(t <= 3 for _k, t in r["played"])) / n
    out["decked"] = sum(1 for r in rs if r["decked"]) / n
    out["hows"] = dict(collections.Counter(r["how"] for r in rs).most_common())
    out["unused"] = sorted((cs[k]["name"] for k in cs if cs[k]["use_rate"] < 0.02))
    try:
        import roles3
        out["roles"] = roles3.coverage(deck)
    except Exception:                              # noqa: BLE001
        out["roles"] = None
    return out


# ------------------------------------------------------------------ 画面に出す
def bar(x, width=28, top=1.0):
    k = int(round(min(1.0, max(0.0, x) / top) * width))
    return "█" * k + "·" * (width - k)


def _by_turn(k, t):
    return k.get("by_turn", {}).get(t, k.get("by_turn", {}).get(str(t), 0)) or 0


def _show_parts(g):
    """ゴールの部品ごとの到達率と、どこで崩れたかを出す。

    「届いたか／届かなかったか」だけでは、**何が足りなくて崩れたのか**が分からない。
    部品に分けて書いておけば、関門がどこかが数字で出る。"""
    ps = g.get("parts")
    if not ps or len(ps) < 2:
        return
    at = g.get("at", "")
    ordered = g.get("ordered", True)
    print("\n  【部品ごと】そろった割合／順に通った割合と、平均で何ターン目にそろったか")
    print(f"    {'':2} {'部品':<24}{'そろう':>8}{'順に':>8}{'平均T':>7}  {'':22}{'ここで止まった':>8}")
    for n, q in enumerate(ps, 1):
        mk = "←ゴール地点" if q["name"] == at else ""
        mean = f"{q['mean']:.2f}" if q["mean"] else "  －"
        print(f"    {n}. {q['name'][:23]:<24}{q['rate'] * 100:7.1f}%{q.get('ord_rate', 0) * 100:7.1f}%"
              f"{mean:>7}  {bar(q.get('ord_rate', 0), 22)}{q['stopped_here'] * 100:7.1f}%{mk}")
    worst = max(ps, key=lambda q: q["stopped_here"])
    if worst["stopped_here"] > 0.05:
        print(f"    → いちばんの関門は「{worst['name']}」"
              f"（そこまで順に通った対戦の多くが、ここで止まっている）")
    sk = [q for q in ps if q.get("skipped", 0) >= 0.01]
    if ordered and sk:
        print("    ※「そろう」より「順に」が低い部品があります＝前の部品を飛ばして成立しています。"
              "\n      " + "、".join(f"{q['name']}（{q['skipped'] * 100:.1f}%が順番を飛ばした）" for q in sk[:3])
              + "\n      部品の並びが、このデッキの実際の道筋と合っていない可能性があります"
                "（goals.py の entered／played／ever で書き直せることがあります）。")


def show(d, cards=True):
    print("=" * 74)
    print(f"一人回し：{d['name']}　{d['games']}戦　操縦＝{d.get('pilot')}　相手＝{d.get('vs')}"
          f"　{d.get('first_label', '先攻')}")
    print("=" * 74)
    g = d.get("goal")
    if g and g.get("n"):
        print(f"\n【このデッキのゴール】{g['name']}　{g.get('label', '')}")
        print(f"  届いた {g['n']}戦（{g['rate'] * 100:.1f}%）　中央値 {g['median']:.0f}ターン"
              f"　平均 {g['mean']:.2f}　最速 {g['fastest']}　ばらつき±{g['sd']:.2f}")
        print("\n  ターン目までにゴールに届く割合")
        for t in range(2, min(12, MAXT) + 1):
            v = _by_turn(g, t)
            print(f"   {t:2d}T  {bar(v)} {v * 100:5.1f}%")
        if g.get("trivial"):
            print("  ※ほぼ全戦が1ターン目で満たしています。ゲーム開始時点でも成り立つ条件を"
                  "書いていませんか（goals.json を見直してください）")
        _show_parts(g)
    elif g:
        print(f"\n【このデッキのゴール】{g['name']}　— 1戦も届きませんでした")
        _show_parts(g)
    k = d["kill"]
    if k.get("n"):
        print(f"\n【殴り切るまでのターン数】{k['n']}戦で決着（{k['n'] / d['games'] * 100:.0f}%）")
        print(f"  中央値 {k['median']:.0f}ターン　平均 {k['mean']:.2f}　最速 {k['fastest']}　最遅 {k['slowest']}"
              f"　ばらつき±{k['sd']:.2f}")
        print("\n  ターン目までに決まる割合")
        for t in range(2, min(12, MAXT) + 1):
            v = _by_turn(k, t)
            print(f"   {t:2d}T  {bar(v)} {v * 100:5.1f}%")
    else:
        print("\n【殴り切るまでのターン数】1戦も決着しませんでした")
    bf = d.get("by_first") or {}
    if len(bf) > 1:
        print("\n【先攻・後攻】一人回しでは後攻のほうが速い（相手が何もしないので、"
              "先攻の「先に殴れる」有利が無く、後攻の1ドロー多いぶんだけが残る）")
        print(f"  {'':6}{'戦数':>6}{'勝率':>8}{'決着率':>8}{'殴り切り平均':>12}{'3T事故':>8}")
        for lab, v in bf.items():
            km = f"{v['kill_mean']:.2f}T" if v["kill_mean"] else "－"
            print(f"  {lab:6}{v['games']:>6}{v['win_rate'] * 100:7.1f}%{v['kill_rate'] * 100:7.1f}%"
                  f"{km:>12}{v['stuck3'] * 100:7.1f}%")
    print("\n【一人回しの曲線】自分のターンごとの平均（マナ・手札・場は決着していない対戦の平均。"
          "相手の盾は決着ぶんを0として数えた全体の平均）")
    print("   T   マナ   手札   場    相手の盾        まだ続いている")
    for t, c in sorted(d["curve"].items(), key=lambda x: int(x[0])):
        if int(t) > 12:
            break
        print(f"  {int(t):2d}  {c['mana']:5.2f} {c['hand']:6.2f} {c['board']:5.2f}   "
              f"{c['opp_shield']:4.2f}  {bar(1 - c['opp_shield'] / 5, 14)}  {c.get('alive', 1) * 100:5.1f}%")
    o = d["opening"]
    print(f"\n【初手の質】3コスト以下の札が平均 {o['avg_castable_t3']:.2f}枚"
          f"／2コスト以下が1枚も無い初手 {o['no_1or2'] * 100:.1f}%"
          f"／全部5コスト以上 {o['all_heavy'] * 100:.1f}%")
    print(f"【事故】3ターン目までに1枚も使えなかった {d['stuck3'] * 100:.1f}%"
          f"／山札切れ {d['decked'] * 100:.1f}%")
    print("【決まり方】" + "、".join(f"{a} {b}" for a, b in d["hows"].items()))
    if d.get("roles"):
        print("【役割の枚数】" + "・".join(f"{a}{b}" for a, b in d["roles"].items()))
    if cards:
        print("\n【札ごとの働き】use＝使えた対戦の割合／T＝平均で何ターン目に／腐り＝引いたのに使えなかった割合")
        print(f"  {'枚':>2} {'カード':<34}{'コスト':>4} {'use':>6} {'T':>5} {'腐り':>6} {'マナ行き':>7}")
        rows = sorted(d["cards"].values(), key=lambda c: (-c["use_rate"], c["cost"]))
        for c in rows:
            t = f"{c['avg_turn']:.1f}" if c["avg_turn"] else "  －"
            print(f"  {c['copies']:>2} {c['name'][:33]:<34}{c['cost']:>4} {c['use_rate'] * 100:5.0f}% "
                  f"{t:>5} {c['idle_rate'] * 100:5.0f}% {c['mana_rate'] * 100:6.0f}%")
        if d.get("pilot") == "greedy":
            print("  ※操縦は「使える札のうち重要度のいちばん高いものを使う」固定の決まりなので、"
                  "数枚の組み合わせで初めて働く札（踏み倒しの元になる札など）は、"
                  "実際より腐って見えることがあります（--pilot plan で先読みすると改善します）。")
    if d.get("unused"):
        print("\n【ほとんど使われない札】" + "、".join(d["unused"]))
        print("  （一人回しで出番が無い＝相手の妨害とは無関係に腐っている。抜く候補）")
    print("=" * 74)


def compare(a, b):
    print("\n" + "=" * 74)
    print(f"比べる：{a['name']}  vs  {b['name']}（各{a['games']}戦）")
    print("=" * 74)
    rows = [
        ("決着した割合", a["kill"].get("n", 0) / a["games"], b["kill"].get("n", 0) / b["games"], "%"),
        ("殴り切る中央値", a["kill"].get("median"), b["kill"].get("median"), "T"),
        ("殴り切る平均", a["kill"].get("mean"), b["kill"].get("mean"), "T"),
        ("最速", a["kill"].get("fastest"), b["kill"].get("fastest"), "T"),
        ("5T までに決まる", _by_turn(a["kill"], 5), _by_turn(b["kill"], 5), "%"),
        ("6T までに決まる", _by_turn(a["kill"], 6), _by_turn(b["kill"], 6), "%"),
        ("3Tまで何も出せない", a["stuck3"], b["stuck3"], "%"),
        ("2コスト以下が無い初手", a["opening"]["no_1or2"], b["opening"]["no_1or2"], "%"),
        ("山札切れ", a["decked"], b["decked"], "%"),
    ]
    if a.get("goal") and b.get("goal"):
        rows = [("ゴール到達率", a["goal"].get("rate", 0), b["goal"].get("rate", 0), "%"),
                ("ゴール到達の平均", a["goal"].get("mean"), b["goal"].get("mean"), "T")] + rows
    print(f"  {'':24}{a['name'][:14]:>16}{b['name'][:14]:>16}   差")
    for lab, x, y, unit in rows:
        if x is None or y is None:
            continue
        f = (lambda v: f"{v * 100:.1f}%") if unit == "%" else (lambda v: f"{v:.2f}")
        d = y - x
        sign = "＋" if d > 0 else "－" if d < 0 else "±"
        print(f"  {lab:24}{f(x):>16}{f(y):>16}   {sign}{abs(d) * (100 if unit == '%' else 1):.1f}")
    print("=" * 74)


# ------------------------------------------------------------------ 入口
def run(deck, name, games, kind, policy, procs, seed, vs_deck, maxt,
        first="1st", goal_spec=None, goal_stop=False, wall="blank", wall_shields=5,
        vs_label=None, goal_at=None):
    if vs_deck:
        opp, olab = vs_deck, (vs_label or "本物のデッキ")
    else:
        opp, olab = make_wall(wall, wall_shields)
    firsts = {"1st": [0], "2nd": [1], "both": [0, 1]}[first]
    jobs = [(deck, opp, seed + i * 7919, kind, policy, name, maxt,
             firsts[i % len(firsts)], goal_spec, goal_stop, wall_shields, goal_at)
            for i in range(games)]
    t0 = time.time()
    if procs > 1:
        from multiprocessing import Pool
        with Pool(procs) as pool:
            rs = pool.map(job, jobs, chunksize=max(1, games // (procs * 8)))
    else:
        rs = [job(x) for x in jobs]
    secs = time.time() - t0
    meta = {"pilot": kind, "vs": olab, "secs": secs, "ms_per_game": secs / games * 1000,
            "seed": seed, "wall": wall, "wall_shields": wall_shields,
            "first_label": {"1st": "先攻のみ", "2nd": "後攻のみ", "both": "先攻後攻を半分ずつ"}[first]}
    if goal_spec:
        import goals
        meta["goal_name"] = goal_spec.get("name", "")
        meta["goal_label"] = goal_spec.get("label", "")
        meta["goal_at"] = goals.goal_when(goal_spec, goal_at)[1]
        meta["goal_ordered"] = bool(goal_spec.get("ordered", True))
    return summarize(deck, name, rs, meta)


def run_all(games, kind, policy, procs, seed, maxt, out=None, first="1st",
            wall="blank", wall_shields=5, use_goals=True, goal_file=None, goal_at=None):
    """公式入賞リスト全部を一人回しして、速さの順に並べる。

    これが「この環境の基準表」になる。自分のデッキを測った時、どのあたりの速さなのかを比べられる。
    ゴールが当たるデッキは、ゴールに届くターンも一緒に出す。"""
    import decks8
    import goals
    ns = sorted(decks8.DECKS8)
    print(f"{len(ns)}デッキ × 各{games}戦（操縦＝{kind}／壁＝{wall}／{first}）\n")
    rows = []
    t0 = time.time()
    for n in ns:
        nm = decks8.short(n)
        gs = goals.pick(nm, None, goal_file) if use_goals else None
        d = run(dict(decks8.DECKS8[n]), nm, games, kind, policy, procs, seed, None, maxt,
                first, gs, False, wall, wall_shields, None, goal_at)
        k = d["kill"]
        rows.append((k.get("median") or 99, k.get("mean") or 99, d))
        gt = ""
        if d.get("goal") and d["goal"].get("n"):
            gt = f"  ゴール{d['goal']['name'][:10]} {d['goal']['mean']:.2f}T {d['goal']['rate'] * 100:.0f}%"
        print(f"  {nm:26s} 中央{k.get('median', 0):.0f}T 平均{k.get('mean', 0):5.2f}T"
              f" 最速{k.get('fastest', 0):2.0f}T  5Tまで{_by_turn(k, 5) * 100:5.1f}%"
              f"  3T事故{d['stuck3'] * 100:4.1f}%{gt}", flush=True)
    rows.sort(key=lambda r: (r[1], r[0]))
    print(f"\n（{time.time() - t0:.0f}秒）\n")
    print("=" * 86)
    print("【速さの順】一人回しで何ターン目に殴り切るか（妨害なしの素の速さ）")
    print("=" * 86)
    print(f"  {'順':>2} {'デッキ':<26}{'平均':>6}{'中央':>5}{'最速':>5}{'5Tまで':>8}{'6Tまで':>8}{'3T事故':>7}"
          f"  {'ゴール':<12}{'到達':>6}{'到達T':>7}")
    for r, (_m, _mean, d) in enumerate(rows, 1):
        k = d["kill"]
        gg = d.get("goal") or {}
        gl = f"  {gg.get('name', '')[:11]:<12}{(gg.get('rate') or 0) * 100:5.0f}%" \
             f"{(gg.get('mean') or 0):6.2f}T" if gg.get("n") else ""
        print(f"  {r:>2} {d['name'][:25]:<26}{k.get('mean', 0):6.2f}{k.get('median', 0):5.0f}"
              f"{k.get('fastest', 0):5.0f}{_by_turn(k, 5) * 100:7.1f}%"
              f"{_by_turn(k, 6) * 100:7.1f}%{d['stuck3'] * 100:6.1f}%{gl}")
    print("=" * 86)
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        json.dump({"games": games, "pilot": kind, "wall": wall, "first": first,
                   "decks": [d for _m, _x, d in rows]},
                  open(out, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"保存：{out}")


def pilot_ab(deck_name, games, procs, seed, maxt, wall, wall_shields, first, goal_file,
             goal_at=None):
    """操縦を変えると数字がどう動くかを測る。「一人回しの精度」を確かめるための道具。

    操縦が下手なら、デッキの本当の性能より遅く・腐って見える。greedy（決まりだけ）と
    plan（1手先読み）で同じデッキを同じ種で回して、差を出す。"""
    import goals
    deck, name = load_deck(deck_name)
    gs = goals.pick(name, None, goal_file)
    outs = {}
    for kind in ("greedy", "plan"):
        d = run(deck, name, games, kind, None, procs, seed, None, maxt, first, gs, False,
                wall, wall_shields, None, goal_at)
        outs[kind] = d
        print(f"  {kind:7s} 完了（{d['secs']:.1f}秒／1戦 {d['ms_per_game']:.1f}ミリ秒）", flush=True)
    a, b = outs["greedy"], outs["plan"]
    print("\n" + "=" * 74)
    print(f"操縦の比べ：{name}　各{games}戦（壁＝{wall}／{a['first_label']}）")
    print("=" * 74)
    rows = [("勝率", a["win_rate"], b["win_rate"], "%"),
            ("決着率", a["kill"].get("rate", 0), b["kill"].get("rate", 0), "%"),
            ("殴り切り平均", a["kill"].get("mean"), b["kill"].get("mean"), "T"),
            ("殴り切り中央値", a["kill"].get("median"), b["kill"].get("median"), "T"),
            ("5Tまでに決まる", _by_turn(a["kill"], 5), _by_turn(b["kill"], 5), "%"),
            ("3Tまで何も出せない", a["stuck3"], b["stuck3"], "%"),
            ("1戦あたりの時間", a["ms_per_game"], b["ms_per_game"], "ms")]
    if a.get("goal") and b.get("goal"):
        rows = [("ゴール到達率", a["goal"].get("rate", 0), b["goal"].get("rate", 0), "%"),
                ("ゴール到達平均", a["goal"].get("mean"), b["goal"].get("mean"), "T")] + rows
    print(f"  {'':22}{'greedy':>12}{'plan':>12}   差")
    for lab, x, y, unit in rows:
        if x is None or y is None:
            continue
        if unit == "%":
            fx, fy, dd = f"{x * 100:.1f}%", f"{y * 100:.1f}%", (y - x) * 100
        elif unit == "ms":
            fx, fy, dd = f"{x:.1f}ms", f"{y:.1f}ms", y - x
        else:
            fx, fy, dd = f"{x:.2f}T", f"{y:.2f}T", y - x
        sign = "＋" if dd > 0 else "－" if dd < 0 else "±"
        print(f"  {lab:22}{fx:>12}{fy:>12}   {sign}{abs(dd):.2f}")
    # 腐り率がいちばん動いた札（先読みで使えるようになった／逆に使われなくなった札）
    diffs = []
    for k, c in a["cards"].items():
        if k in b["cards"]:
            diffs.append((b["cards"][k]["use_rate"] - c["use_rate"], c["name"],
                          c["use_rate"], b["cards"][k]["use_rate"]))
    diffs.sort(key=lambda x: -abs(x[0]))
    print("\n  使われ方がいちばん動いた札（先読みで評価が変わった＝greedy が取りこぼしていた札）")
    for dd, nm, x, y in diffs[:8]:
        print(f"    {nm[:28]:30} {x * 100:5.1f}% → {y * 100:5.1f}%  （{dd * 100:+.1f}）")
    print("=" * 74)
    return outs


def ab_files(pa, pb, la="A", lb="B"):
    """--all で作った2つの基準表を突き合わせて、操縦（や壁・先後）のちがいを全デッキで測る。

    一人回しの「精度」は、総当たりの勝率との相関では測れない（相関の残りは相手との相互作用で、
    操縦の腕とは別のもの）。測れるのは**同じデッキで、より良い手順を見つけられたか**。
    同じ種・同じデッキで殴り切りが速くなったなら、それは前の操縦が本当の動きを取りこぼしていた
    ということ（下限が真の値に近づく）。"""
    a = json.load(open(pa, encoding="utf-8"))
    b = json.load(open(pb, encoding="utf-8"))
    la = a.get("pilot", la)
    lb = b.get("pilot", lb)
    A = {d["name"]: d for d in a["decks"]}
    B = {d["name"]: d for d in b["decks"]}
    rows = []
    for n, x in A.items():
        y = B.get(n)
        if not y or not (x["kill"].get("mean") and y["kill"].get("mean")):
            continue
        rows.append((y["kill"]["mean"] - x["kill"]["mean"], n, x, y))
    if not rows:
        raise SystemExit("突き合わせられるデッキがありません")
    d = [r[0] for r in rows]
    av = lambda f: sum(f(r) for r in rows) / len(rows)          # noqa: E731
    print("=" * 78)
    print(f"操縦の比べ（全{len(rows)}デッキ）　{la}  →  {lb}")
    print("=" * 78)
    print(f"  殴り切り平均の変化    平均 {sum(d) / len(d):+.3f}T   中央 {statistics.median(d):+.3f}T"
          f"   いちばん良くなった {min(d):+.2f}T   悪くなった {max(d):+.2f}T")
    print(f"  速くなったデッキ {sum(1 for x in d if x < -0.02)} / "
          f"遅くなった {sum(1 for x in d if x > 0.02)} / 変わらず {sum(1 for x in d if abs(x) <= 0.02)}")
    print(f"  決着率   {av(lambda r: r[2]['kill'].get('rate', 0)) * 100:5.1f}% → "
          f"{av(lambda r: r[3]['kill'].get('rate', 0)) * 100:5.1f}%")
    print(f"  5Tまで   {av(lambda r: _by_turn(r[2]['kill'], 5)) * 100:5.1f}% → "
          f"{av(lambda r: _by_turn(r[3]['kill'], 5)) * 100:5.1f}%")
    print(f"  3T事故   {av(lambda r: r[2]['stuck3']) * 100:5.1f}% → {av(lambda r: r[3]['stuck3']) * 100:5.1f}%")
    nu = lambda d_: sum(1 for c in d_["cards"].values() if c["use_rate"] < 0.02)   # noqa: E731
    print(f"  ほとんど使われない札の数（平均）  {av(lambda r: nu(r[2])):.2f} → {av(lambda r: nu(r[3])):.2f}")
    print("   ※この数は増えることがある。先読みは「打っても盤面が良くならない札」を打たなくなるので、")
    print("     前の操縦が“とりあえず打っていた”札が、正しく「出番が無い」側に回る。")
    gs = [r for r in rows if (r[2].get("goal") or {}).get("rate") is not None
          and (r[3].get("goal") or {}).get("rate") is not None]
    if gs:
        print(f"  ゴール到達率（{len(gs)}デッキ）  "
              f"{sum(r[2]['goal']['rate'] for r in gs) / len(gs) * 100:5.1f}% → "
              f"{sum(r[3]['goal']['rate'] for r in gs) / len(gs) * 100:5.1f}%")
    rows.sort(key=lambda r: r[0])
    print(f"\n  ■ 速くなった上位（前の操縦が本当の動きを取りこぼしていたデッキ）")
    for dd, n, x, y in rows[:8]:
        print(f"     {n[:26]:28} {x['kill']['mean']:5.2f}T → {y['kill']['mean']:5.2f}T  （{dd:+.2f}）")
    print(f"\n  ■ 遅くなった側（1手先の点取りに釣られて組み立てを崩した疑い）")
    for dd, n, x, y in rows[-5:]:
        print(f"     {n[:26]:28} {x['kill']['mean']:5.2f}T → {y['kill']['mean']:5.2f}T  （{dd:+.2f}）")
    print("=" * 78)


def vs_matrix(solo_path, matrix_path):
    """一人回しの速さと、総当たりの勝率を突き合わせる。

    一人回しは「相手の妨害抜きのデッキ自身の速さ」なので、これだけで強さが決まるなら
    速いデッキほど勝つはず。実際にどれだけ説明できるのかを見る。"""
    import decks8
    so = json.load(open(solo_path, encoding="utf-8"))
    mx = json.load(open(matrix_path, encoding="utf-8"))
    W = collections.defaultdict(lambda: [0.0, 0])
    for r in mx["res"]:
        for who, win in ((r["a"], 1.0 if r["w"] == 0 else 0.5 if r["w"] is None else 0.0),
                         (r["b"], 1.0 if r["w"] == 1 else 0.5 if r["w"] is None else 0.0)):
            W[who][0] += win
            W[who][1] += 1
    short = {n: decks8.short(n) for n in decks8.DECKS8}
    mwin = {short.get(n, n): w / c for n, (w, c) in W.items()}
    rows = [(d["kill"]["mean"], mwin[d["name"]], d["name"], d["stuck3"])
            for d in so["decks"] if d["name"] in mwin and d["kill"].get("mean")]
    if len(rows) < 3:
        raise SystemExit("突き合わせられるデッキが足りません")

    def corr(xs, ys):
        mx_, my = sum(xs) / len(xs), sum(ys) / len(ys)
        num = sum((a - mx_) * (b - my) for a, b in zip(xs, ys))
        den = (sum((a - mx_) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5
        return num / den if den else 0.0

    ks = [r[0] for r in rows]
    ws = [r[1] for r in rows]
    st = [r[3] for r in rows]
    rk = corr(ks, ws)
    rs2 = corr(st, ws)
    print("=" * 78)
    print(f"一人回しの速さ と 総当たりの勝率（{len(rows)}デッキ）")
    print("=" * 78)
    print(f"  殴り切る平均ターン × 勝率の相関   r = {rk:+.3f}（r²={rk * rk:.2f}）")
    print(f"  3ターン事故率      × 勝率の相関   r = {rs2:+.3f}（r²={rs2 * rs2:.2f}）")
    print(f"\n  → 一人回しの速さは、勝率のばらつきの {rk * rk * 100:.0f}% しか説明しない。")
    print("     残りは「相手に何をするか・されるか」。一人回しはデッキの土台を測る道具で、")
    print("     強さそのものではない（強さは matrix8.py の総当たりで測る）。")
    rows.sort(key=lambda r: -r[1])
    print("\n  勝率の高い順（上位6）と、その一人回しの速さ")
    for mean, w, nm, s3 in rows[:6]:
        print(f"    勝率{w * 100:5.1f}%  キル{mean:5.2f}T  3T事故{s3 * 100:4.1f}%  {nm}")
    rows.sort(key=lambda r: r[0])
    print("\n  一人回しが速い順（上位6）と、その勝率")
    for mean, w, nm, s3 in rows[:6]:
        print(f"    キル{mean:5.2f}T  勝率{w * 100:5.1f}%  3T事故{s3 * 100:4.1f}%  {nm}")
    gap = sorted(rows, key=lambda r: r[0] - (1 - r[1]) * 6)
    print("\n  速いのに勝てないデッキ（速さを活かせていない＝妨害に弱い）")
    for mean, w, nm, s3 in gap[:4]:
        print(f"    キル{mean:5.2f}T  勝率{w * 100:5.1f}%  {nm}")
    print("=" * 78)


def main():
    ap = argparse.ArgumentParser(description="一人回し：デッキを高速で回してデータを取る")
    ap.add_argument("--deck", help="実装済みのデッキ名（一部でよい）")
    ap.add_argument("--deck-file", help="自分のデッキリスト（テキストかJSON）")
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--pilot", default="greedy", choices=("greedy", "plan", "policy", "random"),
                    help="greedy＝決まりだけ（速い）／plan＝1手先読み（精度が高い。遅い）")
    ap.add_argument("--policy", default="runs7/policy3_4.json")
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--maxturn", type=int, default=MAXT, help="これより長引いたら打ち切る（自分のターン数）")
    ap.add_argument("--first", default="1st", choices=("1st", "2nd", "both"),
                    help="1st＝先攻のみ（既定）／2nd＝後攻のみ／both＝半分ずつ")
    ap.add_argument("--wall", default="blank",
                    help="壁の種類 blank／trigger／gs／heavy、または実装済みのデッキ名")
    ap.add_argument("--wall-shields", type=int, default=5, help="壁の盾の枚数（既定5）")
    ap.add_argument("--goal", help="使うゴールの名前（既定はデッキ名から自動で当てる）")
    ap.add_argument("--goal-file", help="ゴール表のJSON（既定 goals.json ＋ mygoals.json）")
    ap.add_argument("--goal-at", help="ゴール地点にする部品の名前（python goals.py --check デッキ名 で一覧）")
    ap.add_argument("--no-goal", action="store_true", help="ゴールを測らない")
    ap.add_argument("--goal-stop", action="store_true",
                    help="ゴールに届いたらそこで打ち切る（速いが、殴り切りターンは取れなくなる）")
    ap.add_argument("--vs", help="壁でなく、本物のデッキを相手にする（遅くなる）")
    ap.add_argument("--compare", help="もう1つのデッキと比べる")
    ap.add_argument("--swap", help="1枚入れ替えて比べる（例 --swap \"抜く札=入れる札\"）")
    ap.add_argument("--out", help="結果を書き出すJSON")
    ap.add_argument("--show", help="保存した結果を読み直す")
    ap.add_argument("--no-cards", action="store_true", help="札ごとの表を出さない")
    ap.add_argument("--decks", action="store_true", help="使えるデッキの一覧")
    ap.add_argument("--all", action="store_true",
                    help="公式入賞リスト全部を一人回しして、速さの順に並べる（基準表を作る）")
    ap.add_argument("--pilot-ab", help="このデッキで greedy と plan の操縦を比べる（精度の確認）")
    ap.add_argument("--ab-files", nargs=2, metavar=("A_JSON", "B_JSON"),
                    help="--all で作った2つの基準表を突き合わせる（操縦・壁・先後のちがいを全デッキで測る）")
    ap.add_argument("--vs-matrix", nargs=2, metavar=("SOLO_JSON", "MATRIX_JSON"),
                    help="一人回しの速さと総当たりの勝率を突き合わせる（速さが強さをどれだけ説明するか）")
    a = ap.parse_args()

    if a.decks:
        import decks8
        for n in sorted(decks8.DECKS8):
            print(f"  {decks8.short(n):26s} {n}")
        return
    if a.show:
        d = json.load(open(a.show, encoding="utf-8"))
        show(d, not a.no_cards)
        return
    if a.ab_files:
        ab_files(*a.ab_files)
        return
    if a.vs_matrix:
        vs_matrix(*a.vs_matrix)
        return
    if a.pilot_ab:
        pilot_ab(a.pilot_ab, a.games, a.procs, a.seed, a.maxturn, a.wall, a.wall_shields,
                 a.first, a.goal_file, a.goal_at)
        return
    if a.all:
        run_all(a.games, a.pilot, a.policy, a.procs, a.seed, a.maxturn, a.out, a.first,
                a.wall, a.wall_shields, not a.no_goal, a.goal_file, a.goal_at)
        return
    if not (a.deck or a.deck_file):
        ap.print_help()
        return
    deck, name = load_deck(a.deck, a.deck_file)
    if sum(deck.values()) != 40:
        print(f"（注意）{sum(deck.values())}枚のデッキです（40枚ではありません）", file=sys.stderr)
    import goals
    gs = None if a.no_goal else goals.pick(name, a.goal, a.goal_file)
    if gs:
        _w, _at = goals.goal_when(gs, a.goal_at)
        print(f"ゴール「{gs['name']}」で測ります：{gs.get('label', '')}")
        if len(goals.parts_of(gs)) > 1:
            print(f"  ゴール地点＝「{_at}」"
                  "（--goal-at で変えられます。python goals.py --check デッキ名 で部品の一覧）")
    vs = None
    if a.vs:
        vs, _vn = load_deck(a.vs)
    d = run(deck, name, a.games, a.pilot, a.policy, a.procs, a.seed, vs, a.maxturn,
            a.first, gs, a.goal_stop, a.wall, a.wall_shields, None, a.goal_at)
    show(d, not a.no_cards)
    print(f"（{d['secs']:.1f}秒／1戦 {d['ms_per_game']:.1f}ミリ秒）")
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(d, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"保存：{a.out}")

    other = None
    if a.compare:
        d2, n2 = load_deck(a.compare)
        g2 = None if a.no_goal else goals.pick(n2, a.goal, a.goal_file)
        other = run(d2, n2, a.games, a.pilot, a.policy, a.procs, a.seed, vs, a.maxturn,
                    a.first, g2, a.goal_stop, a.wall, a.wall_shields, None, a.goal_at)
    elif a.swap:
        import decks8
        idx = decks8._index()
        outk, ink = a.swap.split("=", 1)
        ko, ki = decks8.find(outk.strip(), idx), decks8.find(ink.strip(), idx)
        if ko is None or ki is None:
            raise SystemExit(f"カードが見つかりません：{outk if ko is None else ink}")
        if deck.get(ko, 0) < 1:
            raise SystemExit(f"{BY_KEY[ko].name} はこのデッキに入っていません")
        d2 = dict(deck)
        d2[ko] -= 1
        if not d2[ko]:
            del d2[ko]
        d2[ki] = d2.get(ki, 0) + 1
        other = run(d2, f"{name}（{BY_KEY[ko].name}→{BY_KEY[ki].name}）",
                    a.games, a.pilot, a.policy, a.procs, a.seed, vs, a.maxturn,
                    a.first, gs, a.goal_stop, a.wall, a.wall_shields, None, a.goal_at)
        show(other, False)
    if other is not None:
        compare(d, other)


if __name__ == "__main__":
    main()
