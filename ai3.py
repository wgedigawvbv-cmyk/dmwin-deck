"""全デッキ共通の操縦：先読み（モンテカルロ探索）

  ・打てる手それぞれについて、「その手を打ったあと、最後まで進めたらどれくらい勝つか」を何度も試し、
    いちばん勝った手を選ぶ。デッキごとの作戦は書かない。どのデッキも同じこの方法で動かす。
  ・見えない情報（相手の手札・山札・シールドの中身、自分の山札・シールドの中身）は、試すたびに並べ直す。
    相手のデッキリストは知っている前提（大会で主要なデッキの中身が知られているのと同じ）。
  ・強さは budget（1手あたりに試す回数）で決まる。増やしても結果が変わらなくなれば、それがこの方法の上限。
  ・見込みの低い手から順に切り捨てて、残った手に回数を回す（逐次半減）。

  「最後まで進める」やり方（rollout）は2通り。
    乱数：カードを使える時は85%で使い、攻撃できる時は75%で攻撃する。ループが成立するなら必ず起動する。
    学習済み：探索が実際に選んだ手の記録から、「このデッキは、この場面でこの手をどれくらい選ぶか」を数え、
              その割合に沿って進める（learn3.py が作る）。デッキごとの癖を、人が書かずに探索から写し取る。
"""
import json
import math
import random

POLICY = {}          # デッキ名 → {"ターン|手": 重み}


def load_policy(path):
    global POLICY
    if isinstance(path, dict):
        POLICY = path
    else:
        POLICY = json.load(open(path, encoding="utf-8"))
    return POLICY


def sig(g, a):
    """手を、場面をまたいで数えられる名前にする"""
    t = a[0]
    if t == "atk":
        return f"a:{g.P[g.tp].board[a[1]].k}:{'P' if a[2] == 'P' else 'C'}:{a[3] or ''}"
    if t == "play":
        return f"p:{a[1]}:{a[2]}"
    if len(a) > 1:
        return f"{t}:{a[1]}"
    return t


def rollout(g, rng, tabs=(None, None)):
    """最後まで進める。tabs＝(プレイヤー0の進め方, プレイヤー1の進め方)。None なら乱数"""
    rnd = rng.random
    while not g.over:
        acts = g.legal()
        n = len(acts)
        if n == 1:
            g.apply(acts[0])
            continue
        tab = tabs[g.tp]
        ph = g.phase
        if tab is None:
            if ph == "C":
                p = g.P[g.tp]
                if len(p.mana) >= 5 and rnd() < 0.4:
                    g.apply(acts[-1])
                else:
                    g.apply(acts[int(rnd() * (n - 1))])
            elif ph == "M":
                a = acts[-2]
                if a[0] == "loop":
                    g.apply(a)
                elif rnd() < 0.85:
                    g.apply(acts[int(rnd() * (n - 1))])
                else:
                    g.apply(acts[-1])
            else:
                if rnd() < 0.75 or not g.P[1 - g.tp].sh:
                    g.apply(acts[int(rnd() * (n - 1))])
                else:
                    g.apply(acts[-1])
            continue
        if ph == "M" and acts[-2][0] == "loop":
            g.apply(acts[-2])
            continue
        t = g.myturn(g.tp)
        if t > 6:
            t = 6
        pre = f"{t}|"
        ws = []
        tot = 0.0
        get = tab.get
        for a in acts:
            x = sig(g, a)
            w = get(pre + x)
            if w is None:
                w = get("0|" + x, 0.05)
            tot += w
            ws.append(tot)
        r = rnd() * tot
        for j in range(n):
            if r < ws[j]:
                g.apply(acts[j])
                break
        else:
            g.apply(acts[-1])


def determinize(g, me, rng):
    """me から見えない情報を並べ直した複製を作る"""
    h = g.clone(rng)
    for i in (0, 1):
        p = h.P[i]
        down = [j for j, x in enumerate(p.sh) if not x[1]]
        pool = p.deck + [p.sh[j][0] for j in down]
        nh = 0
        if i != me:
            nh = len(p.hand)
            pool += p.hand
        rng.shuffle(pool)
        if i != me:
            p.hand = pool[:nh]
        k = nh
        for j in down:
            p.sh[j] = (pool[k], False)
            k += 1
        p.deck = pool[k:]
    return h


def search(g, rng, budget, tabs=(None, None)):
    """いまの局面で打つ手を選ぶ。返り値：(手, 各手の勝率の見積もり)"""
    acts = g.legal()
    n = len(acts)
    if n == 1:
        return acts[0], None
    me = g.tp
    win = [0.0] * n
    cnt = [0] * n
    alive = list(range(n))
    rounds = max(1, math.ceil(math.log2(n)))
    per = budget / rounds
    while True:
        k = max(1, int(per / len(alive)))
        for _ in range(k):
            seed = rng.getrandbits(40)
            base = determinize(g, me, random.Random(seed))
            for a in alive:
                h = base.clone(random.Random(seed + 1))
                h.apply(acts[a])
                rollout(h, h.rng, tabs)
                cnt[a] += 1
                if h.winner == me:
                    win[a] += 1.0
                elif h.winner is None:
                    win[a] += 0.5
        if len(alive) == 1:
            break
        alive.sort(key=lambda a: -win[a] / cnt[a])
        alive = alive[:max(1, len(alive) // 2)]
        if len(alive) == 1:
            break
    best = alive[0]
    return acts[best], [(acts[a], win[a] / cnt[a] if cnt[a] else None, cnt[a]) for a in range(n)]


def play_game(da, db, rng, first, budgets, log=False, names=(None, None), record=None, pols=None, watch=None):
    """1戦する。
      budgets＝(プレイヤー0の探索回数, プレイヤー1の探索回数)。0 なら探索せず「進め方」だけで動く
      names＝デッキ名（学習済みの進め方を引くのに使う）
      pols＝(プレイヤー0が使う進め方の表, プレイヤー1が使う進め方の表)。省くと読み込み済みの POLICY を両者が使う
      record＝リストを渡すと、探索した場面ごとに (デッキ名, ターン, 打てた手, 選んだ手) を追記する"""
    from engine3 import Game
    g = Game(da, db, rng, first=first, log=log)
    g.hold = [0, 0]        # 相手プレイヤーを攻撃できたのに、1度も攻撃せずに終えたターンの数
    g.atkt = [0, 0]        # 相手プレイヤーを攻撃したターンの数
    if pols is None:
        pols = (POLICY, POLICY)
    tabs = [(pols[i].get(names[0]), pols[i].get(names[1])) for i in (0, 1)]
    hit = False
    while not g.over:
        i = g.tp
        acts = g.legal()
        if len(acts) == 1:
            a = acts[0]
        elif budgets[i] <= 0:
            h = g.clone(rng)
            a = None
            before = (g.turn, g.phase, len(acts))
            # 探索なし：進め方だけで1手選ぶ
            a = _one_step(g, acts, rng, tabs[i][i])
            del h, before
        else:
            a, info = search(g, rng, budgets[i], tabs[i])
            if record is not None and names[i] is not None:
                record.append((names[i], min(6, g.myturn(i)), [sig(g, x) for x in acts], sig(g, a)))
            if watch is not None:
                watch(g, a, info)
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
    return g


def _one_step(g, acts, rng, tab):
    rnd = rng.random
    n = len(acts)
    ph = g.phase
    if ph == "M" and acts[-2][0] == "loop":
        return acts[-2]
    if tab is None:
        if ph == "C":
            p = g.P[g.tp]
            return acts[-1] if (len(p.mana) >= 5 and rnd() < 0.4) else acts[int(rnd() * (n - 1))]
        if ph == "M":
            return acts[int(rnd() * (n - 1))] if rnd() < 0.85 else acts[-1]
        return acts[int(rnd() * (n - 1))] if (rnd() < 0.75 or not g.P[1 - g.tp].sh) else acts[-1]
    t = min(6, g.myturn(g.tp))
    ws = []
    for a in acts:
        x = sig(g, a)
        w = tab.get(f"{t}|{x}")
        if w is None:
            w = tab.get("0|" + x, 0.05)
        ws.append(w)
    return rng.choices(acts, ws)[0]
