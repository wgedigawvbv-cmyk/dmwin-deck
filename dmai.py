#!/usr/bin/env python3
"""デュエマのプレイングを担当するAI（dmai）— これまでの知見を1つにまとめたもの

  このファイルだけで「盤面を渡すと手を返す」ところまで完結する。今後のデュエマAIツールは
  `import dmai` して `dmai.Brain(...)` を作るだけでよい（engine3 の中身を知らなくても使える）。

  ■ 何を「知見」としてまとめたか
    1. 手の選び方は**先読み（モンテカルロ探索＋逐次半減）**。デッキごとの作戦は一行も書かない。
       全デッキに同じ方法を当てるのが、このプロジェクトの出発点（デッキの強さを操縦の差と混ぜないため）。
    2. 見えない情報（相手の手札・両者の山札・裏向きのシールド）は、試すたびに**並べ直す**（determinize）。
       どこまで知っている前提にするかは Knowledge.know_opp_list で切り替えられる（下記）。
    3. 「最後まで進める」やり方は2通り：**乱数**と**学習済みの進め方**（learn3.py が探索の記録から作る表）。
       人がデッキごとの手順を書く代わりに、探索が見つけた打ち方を写し取っている。
    4. カードの効果の中の選択（除去の対象、捨てる札、踏み倒す札）は**engine3 側の共通の決まり**。
       重要度 PRI と値打ち val（＝PRI＋下のカード枚数＋ハイパー）で機械的に決める。
       スター進化のクリーチャーは「離れても下が残る」ぶん安く見る（engine3.VALADJ）。
       これにより、自分では退化を狙い、相手には退化をさせない、が1つの決まりから出てくる。
       → つまり「プレイング」は この探索 と engine3 の共通の決まり の2階建てになっている。
    5. 腕の差は**探索回数（budget）**で表す。0なら探索せず進め方の表だけで打つ（＝初級）。
    6. ループが成立する場面では必ず起動する（探索に任せると見つけ損なうため）。

  ■ 前の版（ai3.py）から直したところ
    ・ループの手を「手の並びの最後から2番目」で見つけていた。追加の手（G・ゼロやクロスギアなど
      FREE_ACTS）があるとそこがループでなくなり、**ループを取りこぼしていた**。手の種類で探すようにした。
    ・なぜその手を選んだかを外から読めるようにした（Brain.explain / 手の日本語化 move_ja）。
    ・腕を名前で選べるようにした（LEVELS）。
    ・「相手のデッキリストを知っている前提」を切り替えられるようにした（know_opp_list）。
  ai3.py はそのまま残してある（これまでの測定結果と比べられるように）。dmai は ai3 の上位互換。

  ■ 使い方
      import dmai
      brain = dmai.Brain(level="上級", policy="runs7/policy3_4.json")
      a = brain.choose(g)                 # g＝engine3.Game。打つ手を返す
      print(brain.explain())              # なぜその手にしたか
      g.apply(a)

      dmai.play(deckA, deckB, levels=("上級", "中級"))        # 1戦させる
      dmai.play(deckA, deckB, watch=True)                     # 読み筋を日本語で見ながら1戦

  ■ コマンド
      python dmai.py --demo                 公式入賞デッキ2つで1戦、読み筋つきで見る
      python dmai.py --ladder --games 8     腕の階段が効いているか（上の腕が下の腕に勝つか）を測る
      python dmai.py --vs-ai3 --games 12    前の版 ai3.py と同じ強さか（取りこぼし直しの効果）を測る
      python dmai.py --self 20              同じ腕どうしで回して、判断の内訳を出す
"""
import argparse
import json
import math
import random
import time

import engine3 as _ENG      # 「勘」で打つ時に PRI と civs を見る（engine3 は dmai を読まないので循環しない）

# ------------------------------------------------------------------ 1. エンジンに求める約束
GAME_INTERFACE = """
dmai が盤面（g）に求めるもの。将来エンジンを作り直す時は、これだけ満たせば dmai がそのまま載る。

  g.legal()        -> 打てる手の一覧（空なら終局）
  g.apply(a)       -> 手を1つ進める
  g.clone(rng)     -> 乱数器を差し替えた完全な複製（元を壊さない）
  g.over           -> 終局したか
  g.winner         -> 勝ったプレイヤー（0/1、引き分けは None）
  g.tp             -> 手番のプレイヤー
  g.phase          -> "C" マナチャージ／"M" メイン／"A" 攻撃
  g.turn           -> 両者合わせたターン数
  g.myturn(i)      -> プレイヤー i の自分のターン数
  g.rng            -> 盤面が持っている乱数器
  g.P[i].hand      -> 手札（カードのキーの一覧）
  g.P[i].deck      -> 山札
  g.P[i].sh        -> シールド（(カードのキー, 表向きか) の一覧）
  g.P[i].board     -> バトルゾーン（u.k＝キー、u.c＝カード、u.under＝下のカード）
  g.P[i].mana      -> マナゾーン

手の形（engine3 の語彙。dmai は種類の名前だけを見る）
  ("charge", k) ("skip",) ("play", k, 形) ("spell", k) ("atk", 自分の場の番号, "P"か相手の場の番号, 追加)
  ("end",) ("attack",) ("loop", …) ("gal",) ("zen", k) ("gigan",) ("abyss",) ("x:…", …)
"""


# ------------------------------------------------------------------ 2. 打ち方の知見
class Knowledge:
    """プレイングの知見を、名前のついた値として1か所に集めたもの。

    ここを書き換えれば「別の打ち方のAI」になる。何が効いているかを問えるように、
    探索の中に数字を埋め込まず、全部この器に出してある。"""

    def __init__(self, **kw):
        # --- 最後まで進める時の打ち方（乱数のとき）
        self.p_play = 0.85        # カードを使える場面で、使う確率（残りは「攻撃へ進む」）
        self.p_attack = 0.75      # 攻撃できる場面で、攻撃する確率（残りは「ターンを終える」）
        self.p_charge_hold = 0.4  # マナが5枚以上ある時、チャージを見送る確率
        self.charge_hold_from = 5 # 「マナが足りてきた」とみなす枚数
        self.always_loop = True   # ループが成立するなら必ず起動する（探索では見つけ損なうため）

        # --- 「勘」で進める（学習済みの表が無くても、カードの性質だけで打つ）
        #     学習済みの表はデッキごとに作るので、使う人が新しく組んだデッキには存在しない。
        #     そういう時に、でたらめに打つかわりにこちらを使う。どのカードにも同じ式を当てる。
        #     幅（＝探索が同じ筋ばかり見ないこと）は、見えない情報の並べ直し（determinize）が
        #     すでに作っている。だから進め方そのものは**止まらずに打ち切る**ほうが強い。
        #     実測（壁を殴り切るまでのターン、7デッキ）：
        #       乱数 6.0〜10.2 ／ ゆるい勘 6.4〜13.0 ／ きつい勘 5.1〜10.0 ／ greedy 5.0〜9.9
        #     「途中で手を止める確率」を残したままカードの選び方だけ賢くすると、かえって遅くなる。
        self.instinct = True      # True＝表が無い時、乱数ではなくカードの性質で打つ
        self.w_pri = 3.0          # 使う札を選ぶ時、重要度（PRI）をどれだけ重く見るか（指数）
        self.p_charge_rule = 1.0  # チャージを決まりどおりに置く確率
        self.w_atk_player = 12.0  # 相手プレイヤーを攻撃する手の重み（打点1につき）
        self.w_atk_win = 1.0      # バトルで勝てる相手を攻撃する手の重み（相手の値打ち1につき）
        self.w_atk_lose = 0.15    # バトルで負ける相手に攻撃する手の重み（まず選ばないが、0にはしない）
        self.w_end = 0.1          # 「ターンを終える」の重み（薄くするほど打ち切る）
        self.i_play = 1.0         # 「勘」でメインを続ける確率（p_play とは別に持つ）
        self.i_attack = 1.0       # 「勘」で攻撃する確率
        self.i_charge_hold = 0.0  # 「勘」でチャージを見送る確率

        # --- 学習済みの進め方を引く時
        self.turn_cap = 6         # 表のキーに使う自分のターン数の上限（7ターン目以降は6として扱う）
        self.unknown_w = 0.05     # 表に無い手の重み（知らない手を完全に捨てないための下駄）

        # --- 手の選び方（探索）
        self.halving = True      # 見込みの低い手から切り捨てて、残りに回数を回す（逐次半減）
        self.keep = 0.5          # 1回の切り捨てで残す割合
        self.min_per = 1         # 1つの手に最低これだけは回す

        # --- 見えない情報をどう並べ直すか（ここが「どこまで知っている前提か」）
        self.target_threat = None   # 除去の狙いどころ。None＝engine3.TARGET_THREAT のまま／
                                    # True＝危なさで選ぶ／False＝重要度のいちばん高い相手
        self.know_opp_list = True   # True＝相手のデッキリストを知っている前提（大会で中身が知られているのと同じ）
        self.belief = None          # know_opp_list=False の時、相手の未知の札をここから引く（{キー: 枚数}）

        for k, v in kw.items():
            if not hasattr(self, k):
                raise TypeError(f"知らない知見の名前：{k}")
            setattr(self, k, v)

    def copy(self, **kw):
        n = Knowledge()
        n.__dict__.update(self.__dict__)
        n.__dict__.update(kw)
        return n

    def lines(self):
        return [f"{k} = {v}" for k, v in sorted(self.__dict__.items()) if k != "belief"]


# ------------------------------------------------------------------ 3. 手の名前（場面をまたいで数えられる形）
def sig(g, a):
    """手を、場面をまたいで数えられる名前にする（学習済みの進め方の表のキー）"""
    t = a[0]
    if t == "atk":
        return f"a:{g.P[g.tp].board[a[1]].k}:{'P' if a[2] == 'P' else 'C'}:{a[3] or ''}"
    if t == "play":
        return f"p:{a[1]}:{a[2]}"
    if len(a) > 1:
        return f"{t}:{a[1]}"
    return t


def find_loop(acts):
    """ループの手を探す（前の版は「最後から2番目」で見ており、追加の手があると取りこぼしていた）"""
    for a in acts:
        if a[0] == "loop":
            return a
    return None


# ------------------------------------------------------------------ 4. 見えない情報の並べ直し
def determinize(g, me, rng, kn):
    """me から見えない情報を並べ直した複製を作る。

    自分の山札と裏向きのシールドは「自分のデッキの残り」から、
    相手の手札・山札・裏向きのシールドは「相手の残り」から並べ直す。
    kn.know_opp_list=False なら、相手の未知の札は kn.belief（こちらが思っている相手のデッキ）から引く
    ＝読み違えていれば、その読み違えたまま打つ。"""
    h = g.clone(rng)
    for i in (0, 1):
        p = h.P[i]
        down = [j for j, x in enumerate(p.sh) if not x[1]]
        pool = p.deck + [p.sh[j][0] for j in down]
        nh = 0
        if i != me:
            nh = len(p.hand)
            pool += p.hand
            if not kn.know_opp_list and kn.belief:
                pool = _believed(len(pool), kn.belief, rng)
        rng.shuffle(pool)
        if i != me:
            p.hand = pool[:nh]
        k = nh
        for j in down:
            p.sh[j] = (pool[k], False)
            k += 1
        p.deck = pool[k:]
    return h


def _believed(n, belief, rng):
    """相手の未知の札 n 枚を、こちらが思っている相手のデッキから引く"""
    pool = []
    for k, v in belief.items():
        pool.extend([k] * v)
    if not pool:
        return []
    rng.shuffle(pool)
    while len(pool) < n:
        pool.append(rng.choice(pool))
    return pool[:n]


# ------------------------------------------------------------------ 5. 最後まで進める
def rollout(g, rng, tabs=(None, None), kn=None):
    """終局まで進める。tabs＝(プレイヤー0の進め方の表, プレイヤー1の表)。None なら乱数で進める"""
    kn = kn or DEFAULT
    rnd = rng.random
    cap, unk = kn.turn_cap, kn.unknown_w
    while not g.over:
        acts = g.legal()
        n = len(acts)
        if n == 1:
            g.apply(acts[0])
            continue
        if kn.always_loop and g.phase == "M":
            lp = find_loop(acts)
            if lp is not None:
                g.apply(lp)
                continue
        tab = tabs[g.tp]
        ph = g.phase
        if tab is None and kn.instinct:              # --- 「勘」で進める（学習済みの表が無い時）
            g.apply(instinct_step(g, acts, rng, kn))
            continue
        if tab is None:                              # --- 乱数で進める
            if ph == "C":
                p = g.P[g.tp]
                if len(p.mana) >= kn.charge_hold_from and rnd() < kn.p_charge_hold:
                    g.apply(acts[-1])                # ("skip",)
                else:
                    g.apply(acts[int(rnd() * (n - 1))])
            elif ph == "M":
                if rnd() < kn.p_play:
                    g.apply(acts[int(rnd() * (n - 1))])
                else:
                    g.apply(acts[-1])                # ("attack",)
            else:
                if rnd() < kn.p_attack or not g.P[1 - g.tp].sh:
                    g.apply(acts[int(rnd() * (n - 1))])
                else:
                    g.apply(acts[-1])                # ("end",)
            continue
        t = min(cap, g.myturn(g.tp))                 # --- 学習済みの進め方で進める
        pre = f"{t}|"
        ws, tot, get = [], 0.0, tab.get
        for a in acts:
            x = sig(g, a)
            w = get(pre + x)
            if w is None:
                w = get("0|" + x, unk)
            tot += w
            ws.append(tot)
        r = rnd() * tot
        for j in range(n):
            if r < ws[j]:
                g.apply(acts[j])
                break
        else:
            g.apply(acts[-1])


def _charge_pick(g, i, acts, kn):
    """マナチャージの決まり（solo.py の charge_greedy と同じ考え方を、この中だけで完結させたもの）。

      (1) まだマナに無い文明を足せる札を優先する（色が揃うのが最優先）
      (2) 手札に2枚以上ある札の余りを置く（1枚は使うために残す）
      (3) すぐには使えない重い札（コストがマナ+2より重い）を置く
      (4) どれも無ければ、いちばん重い札を置く
    「重要度のいちばん低い札を置く」にすると、2マナの加速札のような軽くて要の札を
    自分でマナに埋めてしまう（実測でヤッタレマンが7割マナ行きになった）。"""
    from cards3 import BY_KEY
    p = g.P[i]
    ch = [a for a in acts if a[0] == "charge"]
    if not ch:
        return acts[-1]
    have = _ENG.civs(p)
    cand = [a for a in ch if BY_KEY[a[1]].civ and not set(BY_KEY[a[1]].civ) <= have]
    if not cand:
        cand = ch
    cnt = {}
    for k in p.hand:
        cnt[k] = cnt.get(k, 0) + 1
    dup = [a for a in cand if cnt.get(a[1], 0) >= 2]
    if dup:
        return max(dup, key=lambda a: BY_KEY[a[1]].cost)
    av = len(p.mana)
    far = [a for a in cand if BY_KEY[a[1]].cost > av + 2]
    if far:
        return max(far, key=lambda a: BY_KEY[a[1]].cost)
    return max(cand, key=lambda a: BY_KEY[a[1]].cost)


def instinct_step(g, acts, rng, kn):
    """カードの性質だけで1手選ぶ（学習済みの表が要らない「勘」）。

    学習済みの進め方の表はデッキごとに作るので、**使う人がその場で組んだデッキには存在しない**。
    そこを乱数で埋めると、先読みが「最後まで進めた結果」を見る時の中身がでたらめになり、
    どの手を選んでも似たような見積もりになってしまう。
    そこでここでは、どのカードにも同じ式を当てて打つ：

      チャージ：_charge_pick の決まり（色 → 余り → すぐ使えない重い札）
      メイン  ：使える札を、重要度（PRI）の w_pri 乗で重みづけして選ぶ
                PRI は env のカードでは既定がコストなので、これだけで「マナを使い切る方」に寄る
      攻撃    ：相手プレイヤーを攻撃できるならそれを厚く（打点ぶん）、
                クリーチャーしか殴れないならバトルで勝てる相手を、その値打ちぶん厚く

    乱数ではなく重みつきの抽選にしてあるのは、先読みが同じ筋ばかり試して
    幅を失わないようにするため（いちばん良さそうな手だけを打つと、探索が偏る）。"""
    i = g.tp
    ph = g.phase
    rnd = rng.random
    n = len(acts)
    if kn.always_loop and ph == "M":
        lp = find_loop(acts)
        if lp is not None:
            return lp

    if ph == "C":
        p = g.P[i]
        if len(p.mana) >= kn.charge_hold_from and rnd() < kn.i_charge_hold:
            return acts[-1]                       # ("skip",)
        if rnd() >= kn.p_charge_rule:
            return acts[int(rnd() * (n - 1))]     # たまにでたらめに置く（探索の幅）
        return _charge_pick(g, i, acts, kn)

    if ph == "M":
        if kn.i_play < 1.0 and rnd() >= kn.i_play:
            return acts[-1]                       # ("attack",) 攻撃へ進む
        use = acts[:-1]
        if not use:
            return acts[-1]
        pri = _ENG.PRI
        e = kn.w_pri
        ws = []
        for a in use:
            k = a[1] if len(a) > 1 and isinstance(a[1], str) else None
            ws.append((pri.get(k, 1) + 1.0) ** e if k else 1.0)
        return _pick(use, ws, rnd)

    # ---- 攻撃フェイズ
    atk = [a for a in acts if a[0] == "atk"]
    if not atk:
        return acts[-1]                           # ("end",)
    if kn.i_attack < 1.0 and rnd() >= kn.i_attack and g.P[1 - i].sh:
        return acts[-1]
    mine, theirs = g.P[i].board, g.P[1 - i].board
    cand, ws = [], []
    for a in atk:
        u = mine[a[1]]
        if a[2] == "P":
            w = kn.w_atk_player * max(1, g.brk(i, u))
        else:
            t = theirs[a[2]]
            if g.power(i, u, True) >= g.power(1 - i, t):
                w = kn.w_atk_win * max(1.0, g.val(t))
            else:
                w = kn.w_atk_lose
        cand.append(a)
        ws.append(w)
    cand.append(acts[-1])                         # 殴らずに終える手も残す
    ws.append(kn.w_end)
    return _pick(cand, ws, rnd)


def _pick(items, ws, rnd):
    """重みつきの抽選（random.choices より軽い。rollout の中で何万回も呼ばれる）"""
    tot = 0.0
    run = []
    for w in ws:
        tot += w
        run.append(tot)
    if tot <= 0:
        return items[-1]
    r = rnd() * tot
    for j, c in enumerate(run):
        if r < c:
            return items[j]
    return items[-1]


def one_step(g, acts, rng, tab, kn=None):
    """探索せずに1手だけ選ぶ（腕の一番下。進め方の表だけで打つ）"""
    kn = kn or DEFAULT
    rnd = rng.random
    n = len(acts)
    ph = g.phase
    if kn.always_loop and ph == "M":
        lp = find_loop(acts)
        if lp is not None:
            return lp
    if tab is None and kn.instinct:
        return instinct_step(g, acts, rng, kn)
    if tab is None:
        if ph == "C":
            p = g.P[g.tp]
            return acts[-1] if (len(p.mana) >= kn.charge_hold_from and rnd() < kn.p_charge_hold) \
                else acts[int(rnd() * (n - 1))]
        if ph == "M":
            return acts[int(rnd() * (n - 1))] if rnd() < kn.p_play else acts[-1]
        return acts[int(rnd() * (n - 1))] if (rnd() < kn.p_attack or not g.P[1 - g.tp].sh) else acts[-1]
    t = min(kn.turn_cap, g.myturn(g.tp))
    ws = []
    for a in acts:
        x = sig(g, a)
        w = tab.get(f"{t}|{x}")
        if w is None:
            w = tab.get("0|" + x, kn.unknown_w)
        ws.append(w)
    return rng.choices(acts, ws)[0]


# ------------------------------------------------------------------ 6. 手を選ぶ（探索）
def search(g, rng, budget, tabs=(None, None), kn=None):
    """いまの局面で打つ手を選ぶ。返り値：(手, 内訳, 決めた理由)

      内訳＝[(手, 勝率の見積もり, 試した回数)]。
      理由＝"only"（打てる手が1つ）／"loop"（ループは必ず起動）／"search"（先読み）"""
    kn = kn or DEFAULT
    acts = g.legal()
    n = len(acts)
    if n == 1:
        return acts[0], None, "only"
    if kn.always_loop and g.phase == "M":
        lp = find_loop(acts)
        if lp is not None:
            return lp, None, "loop"
    me = g.tp
    win = [0.0] * n
    cnt = [0] * n
    alive = list(range(n))
    rounds = max(1, math.ceil(math.log(n, 1 / kn.keep))) if kn.halving else 1
    per = budget / rounds
    while True:
        k = max(kn.min_per, int(per / len(alive)))
        for _ in range(k):
            seed = rng.getrandbits(40)
            base = determinize(g, me, random.Random(seed), kn)
            for a in alive:
                h = base.clone(random.Random(seed + 1))
                h.apply(acts[a])
                rollout(h, h.rng, tabs, kn)
                cnt[a] += 1
                if h.winner == me:
                    win[a] += 1.0
                elif h.winner is None:
                    win[a] += 0.5
        if len(alive) == 1 or not kn.halving:
            break
        alive.sort(key=lambda a: -win[a] / cnt[a])
        alive = alive[:max(1, int(len(alive) * kn.keep))]
        if len(alive) == 1:
            break
    best = max(alive, key=lambda a: win[a] / cnt[a])
    return acts[best], [(acts[a], win[a] / cnt[a] if cnt[a] else None, cnt[a]) for a in range(n)], "search"


# ------------------------------------------------------------------ 7. 腕
LEVELS = {
    #  名前      探索回数   説明
    "初級":   (0,    "探索しない。学習済みの進め方の表だけで打つ（人が覚えた手癖だけで打つ状態）"),
    "中級":   (60,   "1手あたり60回の先読み"),
    "上級":   (150,  "1手あたり150回の先読み"),
    "最上級": (600,  "1手あたり600回の先読み（ここでもまだ頭打ちではない）"),
}


def budget_of(level):
    if isinstance(level, int):
        return level
    if level not in LEVELS:
        raise KeyError(f"知らない腕：{level}（使えるのは {'・'.join(LEVELS)}）")
    return LEVELS[level][0]


# ------------------------------------------------------------------ 8. 外から使う入口
class Brain:
    """プレイングを担当するAI。盤面を渡すと手を返す。

      brain = Brain(level="上級", policy="runs7/policy3_4.json", deck_names=("自分のデッキ名", "相手のデッキ名"))
      a = brain.choose(g); print(brain.explain()); g.apply(a)

    deck_names は、学習済みの進め方の表を引くためだけに使う（デッキごとの作戦ではなく、
    「そのデッキでは探索がどんな手を選びがちだったか」の統計）。渡さなければ乱数で最後まで進める。"""

    def __init__(self, level="上級", policy=None, knowledge=None, deck_names=(None, None), seed=None, me=None):
        self.level = level
        self.budget = budget_of(level)
        self.kn = knowledge or Knowledge()
        self.pol = _load_policy(policy)
        self.deck_names = tuple(deck_names)
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self.me = me                      # 自分のプレイヤー番号（分からなければ choose の時の手番）
        self.last = None                  # (手, 内訳, 理由, 盤面)
        self.reasons = {}                 # 理由ごとの回数（"only"/"loop"/"search"/"policy"）
        self.secs = 0.0
        self.calls = 0

    # -- 進め方の表：(プレイヤー0のデッキの表, プレイヤー1のデッキの表)。rollout が g.tp で引く
    def _tabs(self):
        return tuple(self.pol.get(n) if n else None for n in self.deck_names)

    def choose(self, g):
        """この盤面で打つ手を返す"""
        t0 = time.time()
        i = g.tp if self.me is None else self.me
        acts = g.legal()
        tabs = self._tabs()
        if len(acts) == 1:
            a, info, why = acts[0], None, "only"
        elif self.budget <= 0:
            a = one_step(g, acts, self.rng, tabs[i], self.kn)
            info, why = None, ("loop" if a[0] == "loop" else "policy")
        else:
            a, info, why = search(g, self.rng, self.budget, tabs, self.kn)
        self.last = (a, info, why, g)
        self.reasons[why] = self.reasons.get(why, 0) + 1
        self.calls += 1
        self.secs += time.time() - t0
        return a

    def explain(self, top=5):
        """直前の判断を日本語で返す"""
        if self.last is None:
            return "まだ何も判断していない"
        a, info, why, g = self.last
        head = {"only": "打てる手が1つだけ", "loop": "ループが成立するので必ず起動する（知見：always_loop）",
                "policy": f"探索なし（腕＝{self.level}）。学習済みの進め方の表に沿って選んだ",
                "search": f"先読み{self.budget}回で選んだ"}[why]
        out = [f"選んだ手：{move_ja(g, a)}", f"理由：{head}"]
        if info:
            # 逐次半減では、早く切り捨てた手は少ない回数のままなので、見積もりが粗い（当たると高く出る）。
            # 残った手ほど多く試しているので、回数の多い順に並べる。回数を見ずに率だけ比べてはいけない。
            rows = sorted((r for r in info if r[1] is not None), key=lambda r: (-r[2], -r[1]))
            mx = max(r[2] for r in rows)
            shown = rows[:top]
            out.append(f"読み筋（試した回数の多い順に{len(shown)}手／全{len(info)}手）：")
            for m, w, c in shown:
                mark = "→" if m == a else "  "
                tag = "" if c >= mx else "　※早くに切り捨てた手（回数が少なく、率は粗い）"
                out.append(f"  {mark} {w * 100:5.1f}%（{c}回）{move_ja(g, m)}{tag}")
            cut = len(rows) - len(shown)
            if cut > 0:
                out.append(f"  （残り{cut}手は省略）")
        return "\n".join(out)

    def stats(self):
        n = max(1, self.calls)
        return (f"判断{self.calls}回／1回あたり{self.secs / n * 1000:.0f}ミリ秒／"
                + "・".join(f"{k} {v}" for k, v in sorted(self.reasons.items())))


def _load_policy(policy):
    if policy is None:
        return {}
    if isinstance(policy, dict):
        return policy
    return json.load(open(policy, encoding="utf-8"))


def best_move(g, level="上級", policy=None, **kw):
    """1行で使う入口。盤面を渡すと手を返す"""
    return Brain(level=level, policy=policy, **kw).choose(g)


# ------------------------------------------------------------------ 9. 手を日本語にする
PHASE_JA = {"C": "マナチャージ", "M": "メイン", "A": "攻撃"}


def _nm(k):
    try:
        from cards3 import BY_KEY
        return f"《{BY_KEY[k].name}》"
    except Exception:
        return str(k)


def move_ja(g, a):
    """手を人が読める日本語にする（UI・棋譜・コーチ役など、今後のツールで使えるように）"""
    t = a[0]
    if t == "charge":
        return f"{_nm(a[1])}をマナゾーンに置く"
    if t == "skip":
        return "マナチャージを見送る"
    if t == "play":
        k = a[1]
        try:
            from cards3 import BY_KEY
            c = BY_KEY[k]
            kind = {"C": "を召喚", "S": "を唱える", "T": "をタマシードとして出す",
                    "G": "を城として出す", "X": "をジェネレート"}.get(c.kind, "を使う")
        except Exception:
            kind = "を使う"
        if len(a) > 2 and a[2] == 1:
            kind = "を進化（または墓地から）で出す"
        return f"{_nm(k)}{kind}"
    if t == "spell":
        return f"{_nm(a[1])}の呪文側を唱える"
    if t == "atk":
        try:
            u = g.P[g.tp].board[a[1]]
            who = _nm(u.k)
        except Exception:
            who = f"場の{a[1]}番"
        if a[2] == "P":
            tgt = "相手プレイヤー"
        else:
            try:
                tgt = _nm(g.P[1 - g.tp].board[a[2]].k)
            except Exception:
                tgt = f"相手の場の{a[2]}番"
        extra = f"（{_nm(a[3])}を選択）" if len(a) > 3 and a[3] else ""
        return f"{who}で{tgt}を攻撃{extra}"
    if t == "attack":
        return "攻撃に進む"
    if t == "end":
        return "ターンを終える"
    if t == "loop":
        return "ループを起動する"
    if t == "gal":
        return "ガルクライフ（刃極ノ扉）を使う"
    if t == "zen":
        return f"{_nm(a[1])}をマナゾーンから出す（禅）"
    if t == "gigan":
        return "墓地のギガンダイダスを出す"
    if t == "abyss":
        return "墓地のマルガーニを出す（アビスラッシュ）"
    if t.startswith("x:"):
        return f"追加の手「{t[2:]}」" + (f"（{_nm(a[1])}）" if len(a) > 1 and isinstance(a[1], str) else "")
    return str(a)


def board_ja(g):
    """盤面を1行で書く（観戦・記録用）"""
    def side(i):
        p = g.P[i]
        cre = "・".join(_nm(u.k) + ("（タップ）" if u.tap else "") for u in p.board) or "なし"
        return f"盾{len(p.sh)} 手{len(p.hand)} マナ{len(p.mana)} 山{len(p.deck)} 場:{cre}"
    return (f"[{g.turn}ターン目／{PHASE_JA.get(g.phase, g.phase)}／手番P{g.tp}]\n"
            f"  P0 {side(0)}\n  P1 {side(1)}")


# ------------------------------------------------------------------ 10. 1戦させる
def play(da, db, levels=("上級", "上級"), policy=None, deck_names=(None, None),
         seed=1, first=0, knowledge=None, watch=False, log=False, record=None):
    """1戦する。返り値：終局した盤面（g.winner が勝者）。

      levels＝(プレイヤー0の腕, プレイヤー1の腕)。watch=True で読み筋を日本語で出しながら進める。
      record にリストを渡すと、探索した場面ごとに (デッキ名, 自分のターン, 打てた手, 選んだ手) を追記する
      （learn3.py が進め方の表を作るのに使う形）。"""
    from engine3 import Game
    rng = random.Random(seed)
    g = Game(da, db, rng, first=first, log=log)
    g.hold = [0, 0]           # 相手プレイヤーを攻撃できたのに1度も攻撃せずに終えたターン数
    g.atkt = [0, 0]           # 相手プレイヤーを攻撃したターン数
    pol = _load_policy(policy)
    # knowledge は1つでも、(プレイヤー0の知見, プレイヤー1の知見) の組でもよい。
    # 組で渡せる形にしてあるのは、**知見を1つだけ変えて勝率を測る**ため
    # （「何が効いているのか」を、同じデッキ・同じ探索回数のまま問えるようにする）。
    kns = knowledge if isinstance(knowledge, (tuple, list)) else (knowledge, knowledge)
    brains = [Brain(level=levels[i], policy=pol, knowledge=kns[i],
                    deck_names=deck_names, seed=seed * 7919 + i, me=i) for i in (0, 1)]
    g.brains = brains
    for i in (0, 1):                      # 除去の狙いどころは engine 側の決まりなので、盤面に書き込む
        if brains[i].kn.target_threat is not None:
            g.tgtmode[i] = brains[i].kn.target_threat
    hit = False
    while not g.over:
        i = g.tp
        acts = g.legal()
        a = brains[i].choose(g)
        if watch and len(acts) > 1:
            print(board_ja(g))
            print(brains[i].explain())
            print()
        if record is not None and deck_names[i] is not None and brains[i].budget > 0 and len(acts) > 1:
            record.append((deck_names[i], min(brains[i].kn.turn_cap, g.myturn(i)),
                           [sig(g, x) for x in acts], sig(g, a)))
        if a[0] == "atk" and a[2] == "P":
            hit = True
        elif a[0] == "end":
            if hit:
                g.atkt[i] += 1
            elif any(x[0] == "atk" and x[2] == "P" for x in acts):
                g.hold[i] += 1
            hit = False
        g.apply(a)
        if g.tp != i:
            hit = False
    if watch:
        print(board_ja(g))
        print(f"決着：{'引き分け' if g.winner is None else f'P{g.winner} の勝ち'}（{g.how}／{(g.turn + 1) // 2}ターン）")
        for i in (0, 1):
            print(f"  P{i}（{levels[i]}）{brains[i].stats()}")
    return g


# ------------------------------------------------------------------ 11. コマンド
def _two_decks():
    import decks8
    ns = sorted(decks8.DECKS8)
    a = next((n for n in ns if decks8.short(n) == "火水闇ジャオウガ"), ns[0])
    b = next((n for n in ns if decks8.short(n) == "光水自然der'Bande"), ns[1])
    return (a, decks8.DECKS8[a]), (b, decks8.DECKS8[b])


def demo(policy, seed):
    (na, da), (nb, db) = _two_decks()
    print(f"P0＝{na}（上級）　vs　P1＝{nb}（上級）\n")
    play(da, db, levels=("上級", "上級"), policy=policy, deck_names=(na, nb), seed=seed, watch=True)


def sides(gno):
    """測る側のプレイヤー番号と、先攻のプレイヤー番号を返す。

    **測り方の落とし穴**：「測る側＝先攻」を交互に入れ替えるだけでは、測る側がいつも先攻になる。
    デュエマは先攻が有利なので、それだと測った差に先攻の有利がまるごと混ざる
    （この取り違えを実際にやって、腕の階段を実際より高く見ていた）。
    測る側と先攻を**別々に**入れ替えること。4戦で4通りがちょうど1回ずつ出る。"""
    return gno % 2, (gno >> 1) % 2


def _pairs(n, seed):
    """公式入賞リストから、同じデッキ同士の対戦になる組を n 個作る
    （同じデッキ同士なら、勝率の差はまるごと腕の差になる）"""
    import decks8
    rng = random.Random(seed)
    ns = sorted(decks8.DECKS8)
    picks = rng.sample(ns, min(n, len(ns)))
    return [(x, decks8.DECKS8[x]) for x in picks]


def ladder(policy, games, seed, pairs=4):
    """腕の階段が効いているか：上の腕が下の腕に勝つかを測る。

    **同じデッキ同士**で戦わせる（デッキの差を消して、腕の差だけを見るため）。
    デッキを何個か変えて、どのデッキでも階段になっているかを見る。"""
    ds = _pairs(pairs, seed)
    order = list(LEVELS)
    print(f"同じデッキ同士・{len(ds)}デッキ×各{games}戦（測る側と先攻を別々に入れ替え）")
    print("使うデッキ：" + "、".join(__import__("decks8").short(n) for n, _d in ds) + "\n")
    print("　上の腕 → 下の腕 の勝率（50%なら腕の差が出ていない）")
    for x in range(len(order) - 1):
        hi, lo = order[x + 1], order[x]
        tot, per = 0.0, []
        for n, d in ds:
            w = 0.0
            for gno in range(games):
                me, first = sides(gno)
                lv = (hi, lo) if me == 0 else (lo, hi)
                g = play(d, d, levels=lv, policy=policy, deck_names=(n, n),
                         seed=seed + gno * 13, first=first)
                w += 1.0 if g.winner == me else 0.5 if g.winner is None else 0.0
            per.append(w / games)
            tot += w
        print(f"  {hi}（{budget_of(hi)}回）→ {lo}（{budget_of(lo)}回）："
              f"{tot / (games * len(ds)) * 100:.0f}%　デッキ別 "
              + "・".join(f"{v * 100:.0f}%" for v in per), flush=True)


def loopcheck(policy, games, seed):
    """前の版のループの取りこぼしが、実戦でどれだけ起きていたかを数える。

    前の版 ai3 は「手の並びの最後から2番目がループなら起動」という見つけ方だった。
    追加の手（FREE_ACTS）がその後ろに並ぶとそこがループでなくなるので、取りこぼす。"""
    from engine3 import Game
    import cards3
    import decks8
    pol = _load_policy(policy)
    # ループが起きうる側（ドッコイ＝teacher+dokkoi+pon／創世竜＝zen+leviya+trap+parli）を必ず片方に置く
    allD = dict(cards3.DECKS)
    allD.update(decks8.DECKS8)
    loopers = [n for n, d in allD.items()
               if ({"teacher", "dokkoi", "pon"} <= set(d)) or ({"zen", "leviya", "trap", "parli"} <= set(d))]
    others = sorted(allD)
    tot = {"場面": 0, "ループが打てた場面": 0, "前の版が取りこぼす並び": 0}
    rng = random.Random(seed)
    print("ループ側に使うデッキ：" + "、".join(loopers[:6]) + (" ほか" if len(loopers) > 6 else ""))
    for gno in range(games):
        a = loopers[gno % len(loopers)] if loopers else rng.choice(others)
        b = rng.choice(others)
        g = Game(allD[a], allD[b], random.Random(seed + gno), first=gno % 2)
        brains = [Brain(level="中級", policy=pol, deck_names=(a, b), seed=seed + gno * 7 + i, me=i)
                  for i in (0, 1)]
        g.hold = [0, 0]
        g.atkt = [0, 0]
        while not g.over:
            acts = g.legal()
            if g.phase == "M" and len(acts) > 1:
                tot["場面"] += 1
                lp = find_loop(acts)
                if lp is not None:
                    tot["ループが打てた場面"] += 1
                    if acts[-2][0] != "loop":
                        tot["前の版が取りこぼす並び"] += 1
            g.apply(brains[g.tp].choose(g))
    print(f"{games}戦（片方はループが起きうるデッキ、相手は無作為）")
    for k, v in tot.items():
        print(f"  {k}：{v}")
    if tot["ループが打てた場面"]:
        r = tot["前の版が取りこぼす並び"] / tot["ループが打てた場面"]
        print(f"  → ループが打てた場面のうち {r * 100:.1f}% を前の版は取りこぼしていた")
    else:
        print("  → この回ではループが打てる場面が出なかった（ループデッキを含む組を増やすこと）")


def vs_ai3(policy, games, seed, budget=150):
    """前の版 ai3.py と比べる（ループの取りこぼし直しが効いているか）"""
    import ai3
    (na, da), (nb, db) = _two_decks()
    pol = _load_policy(policy)
    ai3.load_policy(pol)
    w = 0.0
    for gno in range(games):
        me, first = sides(gno)
        rng = random.Random(seed + gno * 101)
        from engine3 import Game
        g = Game(da, db, rng, first=first)
        g.hold = [0, 0]
        g.atkt = [0, 0]
        brain = Brain(level=budget, policy=pol, deck_names=(na, nb), seed=seed + gno, me=me)
        tabs = (pol.get(na), pol.get(nb))
        while not g.over:
            i = g.tp
            if i == me:
                a = brain.choose(g)
            else:
                acts = g.legal()
                a = acts[0] if len(acts) == 1 else ai3.search(g, rng, budget, tabs)[0]
            g.apply(a)
        w += 1.0 if g.winner == me else 0.5 if g.winner is None else 0.0
        print(f"  {gno + 1}/{games}　dmai {w}勝", flush=True)
    print(f"dmai（新） vs ai3（旧）：{w / games * 100:.0f}%（{games}戦、どちらも探索{budget}回）")
    print("  同じ探索方法なので50%前後が正しい。大きく上なら、ループの取りこぼし直しが効いている")


def blind(policy, games, seed, level="上級", pairs=3):
    """「相手のデッキリストを知っている前提」が、どれだけの強さを生んでいたかを測る。

    このプロジェクトはずっと「相手のリストは知っている（大会で中身が知られているのと同じ）」として
    見えない札を並べ直してきた。実際のツールでは相手のリストは分からないので、ここを測っておく。

      知っている側（know_opp_list=True）  vs  読み違えている側（別のデッキのリストを信じている）
    同じデッキ同士で戦わせるので、勝率の差はまるごと「リストを知っていること」の価値になる。"""
    import decks8
    ds = _pairs(pairs + 1, seed)
    pol = _load_policy(policy)
    print(f"同じデッキ同士・{pairs}デッキ×各{games}戦（腕＝{level}、測る側と先攻を別々に入れ替え）")
    print("　知っている側 → 読み違えている側 の勝率（50%ならリストを知る価値がない）\n")
    tot = 0.0
    for x in range(pairs):
        n, d = ds[x]
        wrong = ds[x + 1][1]                      # 別のデッキのリストを信じてしまっている
        kn_know = Knowledge()
        kn_blind = Knowledge(know_opp_list=False, belief=dict(wrong))
        w = 0.0
        for gno in range(games):
            me, first = sides(gno)
            g = _duel(d, d, (n, n), pol, level, me, kn_know, kn_blind, seed + gno * 17, first)
            w += 1.0 if g.winner == me else 0.5 if g.winner is None else 0.0
        tot += w
        print(f"  {decks8.short(n)}：{w / games * 100:.0f}%（{games}戦。読み違えの中身は"
              f"{decks8.short(ds[x + 1][0])}）", flush=True)
    print(f"\n  合計：{tot / (games * pairs) * 100:.0f}%")


def _duel(da, db, names, pol, level, me, kn_me, kn_opp, seed, first):
    """知見だけを左右で変えて1戦させる（腕・デッキ・進め方の表は同じ）"""
    from engine3 import Game
    g = Game(da, db, random.Random(seed), first=first)
    g.hold = [0, 0]
    g.atkt = [0, 0]
    brains = [Brain(level=level, policy=pol, deck_names=names, seed=seed * 7919 + i, me=i,
                    knowledge=(kn_me if i == me else kn_opp)) for i in (0, 1)]
    g.brains = brains
    for i in (0, 1):
        if brains[i].kn.target_threat is not None:
            g.tgtmode[i] = brains[i].kn.target_threat
    while not g.over:
        g.apply(brains[g.tp].choose(g))
    return g


def selfplay(policy, games, seed, level="上級"):
    (na, da), (nb, db) = _two_decks()
    wins = [0.0, 0.0]
    rs = {}
    t0 = time.time()
    for gno in range(games):
        g = play(da, db, levels=(level, level), policy=policy, deck_names=(na, nb),
                 seed=seed + gno * 31, first=gno % 2)
        if g.winner is not None:
            wins[g.winner] += 1
        else:
            wins[0] += 0.5
            wins[1] += 0.5
        for b in g.brains:
            for k, v in b.reasons.items():
                rs[k] = rs.get(k, 0) + v
    tot = sum(rs.values()) or 1
    print(f"{games}戦（腕＝{level}）{time.time() - t0:.0f}秒　P0 {wins[0]}勝／P1 {wins[1]}勝")
    print("判断の内訳：" + "、".join(f"{k} {v}回（{v / tot * 100:.0f}%）" for k, v in sorted(rs.items())))
    print("  only＝打てる手が1つ／loop＝ループを必ず起動／search＝先読み／policy＝探索なし")


def main():
    ap = argparse.ArgumentParser(description="デュエマのプレイングを担当するAI（dmai）")
    ap.add_argument("--policy", default="runs7/policy3_4.json", help="学習済みの進め方の表")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--games", type=int, default=8)
    ap.add_argument("--demo", action="store_true", help="1戦を読み筋つきで見る")
    ap.add_argument("--ladder", action="store_true", help="腕の階段を測る")
    ap.add_argument("--vs-ai3", action="store_true", help="前の版と比べる")
    ap.add_argument("--self", type=int, default=0, help="同じ腕どうしで指定回数回す")
    ap.add_argument("--pairs", type=int, default=4, help="--ladder で使うデッキの数")
    ap.add_argument("--loopcheck", action="store_true", help="前の版のループ取りこぼしが実戦で何%起きていたかを数える")
    ap.add_argument("--blind", action="store_true", help="相手のデッキリストを知っていることの価値を測る")
    ap.add_argument("--knowledge", action="store_true", help="知見の一覧を出す")
    a = ap.parse_args()
    if a.knowledge:
        print("【dmai がもっている打ち方の知見】")
        for ln in Knowledge().lines():
            print("  " + ln)
        print("\n【腕】")
        for n, (b, d) in LEVELS.items():
            print(f"  {n}：探索{b}回　{d}")
        print(GAME_INTERFACE)
        return
    if a.demo:
        demo(a.policy, a.seed)
    if a.ladder:
        ladder(a.policy, a.games, a.seed, a.pairs)
    if a.vs_ai3:
        vs_ai3(a.policy, a.games, a.seed)
    if a.loopcheck:
        loopcheck(a.policy, a.games, a.seed)
    if a.blind:
        blind(a.policy, a.games, a.seed, pairs=a.pairs)
    if a.self:
        selfplay(a.policy, a.self, a.seed)
    if not (a.demo or a.ladder or a.vs_ai3 or a.self or a.loopcheck or a.blind):
        ap.print_help()


DEFAULT = Knowledge()

if __name__ == "__main__":
    main()
