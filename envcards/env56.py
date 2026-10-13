#!/usr/bin/env python3
"""担当56：DM26-SD1「ドキドキつよいデッキ 25の王道」の再録カード15枚

  この札束に入っている仕組み
    ・アビス（闇）の一群：シビルカウント3（深淵の壊炉 マーダン＝ロウ）、
      アビスラッシュ（ドミー＝ゾー）、アビス・メクレイド5（「力が欲しいか？」）、
      「このターンアンタップしたクリーチャー1体につき軽減」（深淵の瘴炉 インシネ＝ロウ）、
      ハイパー化＋ハイパーモードだけのW・ブレイカー（超霊淵 ヤバーダン＝ロウ）、
      「相手が手札を1枚捨てた時」の誘発（謀遠 テレスコ＝テレス／インシネ＝ロウ）。
    ・ヴェールアビス（自然）：S・トリガー・プラスの「P能力」（ア：グンテ）、
      メガ・ラスト・バースト（オ：ドユニワ／喰土邪覇）、モード選択の出た時（ア：エヌ：マクア）。
    ・ジョーカーズ：G・ブレイカー（めっちゃ！デンヂャラスG3）とその付与、
      「相手のクリーチャーの能力をすべて無視する」（ケッシング・ゼロ）、
      革命0（プリプリズン）、J・O・E 2（チキン・タッ太）、
      山札の一番下から踏み倒す（カツラデランス）。

  調べ直して確かめたところ
    15枚すべてについて dmwiki.net のカードページを、別の質問で2回以上（ツインパクトと
    ハイパーモード持ちは生 wiki ソース `?plugin=template&refer=…` も）読み、
    コスト・文明・種族・パワー・ブレイク数・能力本文がどちらも一致することを確かめた。
    意外だった点：
      ・《超霊淵 ヤバーダン＝ロウ》は生ソースの区切り（BGCOLOR(#cde):|c|）より下に
        W・ブレイカーがあり、**W・ブレイカーがハイパーモード中だけ**だった
        （1回目の読みでは普通のW・ブレイカーに見えた）。
      ・《深淵の瘴炉 インシネ＝ロウ》の軽減は「このターンアンタップしたクリーチャー」で、
        解説に「相手のクリーチャーのアンタップも含む」と書かれていた（自分だけではない）。
      ・《ドミー＝ゾー／「倒したいか？」》は**クリーチャー側が闇(5)、呪文側が自然(2)**の
        文明ちがいのツインパクト。
      ・《ヘルトッQ》《めっちゃ！デンヂャラスG3》は無色[ジョーカーズ]、
        《カツラデランス》《チキン・タッ太》は火文明[ジョーカーズ]で、同じ弾でも色がちがう。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all, free_play, worst_hand
from envcards.env0 import SLAYER, race_like

W = "https://dmwiki.net/"
SRC = {
    "k56_mardan": W + "《深淵の壊炉 マーダン＝ロウ》",
    "k56_telesco": W + "《謀遠 テレスコ＝テレス》",
    "k56_footless": W + "《フットレス＝トレース／「力が欲しいか？」》",
    "k56_anmakua": W + "《ア：エヌ：マクア》",
    "k56_domyzo": W + "《ドミー＝ゾー／「倒したいか？」》",
    "k56_belladonna": W + "《悪魔妖精ベラドンナ》",
    "k56_yabadan": W + "《超霊淵 ヤバーダン＝ロウ》",
    "k56_insine": W + "《深淵の瘴炉 インシネ＝ロウ》",
    "k56_agunte": W + "《ア：グンテ》",
    "k56_doyuniwa": W + "《オ：ドユニワ／喰土邪覇》",
    "k56_g3": W + "《めっちゃ！デンヂャラスG3／ケッシング・ゼロ》",
    "k56_hertoq": W + "《ヘルトッQ》",
    "k56_katsura": W + "《カツラデランス／「アフロ行きま〜す！！」》",
    "k56_puriprizon": W + "《プリプリズン》",
    "k56_chicken": W + "《チキン・タッ太》",
}


# ================================================================ 共通の道具
def _civil(s, i, civ):
    """シビルカウントN：自分の〈civ〉の、クリーチャーまたはタマシードの合計"""
    return sum(1 for u in s.P[i].board if u.c.kind in ("C", "T") and civ in E.MCIV[u.k])


def _rand_discard(s, j):
    """プレイヤー j の手札を1枚、見ないで選んで捨てさせる（相手の能力による捨て）"""
    p = s.P[j]
    if not p.hand:
        return None
    k = p.hand[s.rng.randrange(len(p.hand))]
    s.discard(j, k, by_opp=True)
    return k


def _playable_cre(c, mx=99):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので除く）"""
    return c.kind == "C" and c.cost <= mx and not (c.evo and not c.neo)


def _mekureido(s, i, n, pred, what):
    """メクレイドX：山札の上3枚を見て、条件に合うカード1枚をただで使う。残りは山札の下へ"""
    p = s.P[i]
    m = min(3, len(p.deck) - 1)
    if m <= 0:
        return
    top = [p.deck.pop() for _ in range(m)]
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.cost <= n and pred(c) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        p.hand.append(best)
        s.ev(f"　{what}：{BY_KEY[best].name} をただで使う")
        if not free_play(s, i, best):
            if best in p.hand:
                p.hand.remove(best)
            top.append(best)
    for k in top:
        p.deck.insert(0, k)


def _cast_free(s, i, k, twin=False):
    """コストを支払わずに呪文を唱える（カードは呼ぶ側がゾーンから取り除いておく）。唱えた後は墓地へ"""
    p = s.P[i]
    c = BY_KEY[k]
    cost = c.twin[0] if (twin and c.twin) else c.cost
    p.spl += 1
    s.first_play(i, cost)
    prev = s.spc
    s.spc = cost
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, k)
    fn = E.SPELL.get(k)
    if fn is not None and not s.over:
        fn(s, i)
    s.spc = prev
    s.grave_put(i, k)
    if not twin:
        s.noncre(i)


def atl_onlyp(s, i, u, t):
    """「このターン、相手プレイヤーを攻撃できる」＝クリーチャーは攻撃できない。

    印は u.x に書くので、この担当のカードが働いた時だけ効く（アビスラッシュのドミー＝ゾー、
    ヤバーダン＝ロウが墓地から出したクリーチャー、ヘルトッQ）。"""
    return u.x.get("k56_onlyp") == s.turn


E.ATKTARGETLOCK.append(atl_onlyp)


# ================================================================ 1 深淵の壊炉 マーダン＝ロウ
def e_mardan(s, i, u):
    """出た時、相手の手札を見てクリーチャーを1体選び、捨てさせる"""
    o = s.P[1 - i]
    cs = [k for k in o.hand if BY_KEY[k].kind == "C"]
    if not cs:
        return
    k = max(cs, key=E.PRI.get)
    s.ev(f"　マーダン＝ロウ：相手の手札の {BY_KEY[k].name} を捨てさせる")
    s.discard(1 - i, k, by_opp=True)


def at_mardan(s, i, u):
    """シビルカウント3：攻撃する時、自分の闇のクリーチャー・タマシードが合計3つ以上あれば、
    相手の墓地のカード1枚の「出た時」の能力を自分が1つ使い、そのカードを持ち主の山札の下に置く"""
    if _civil(s, i, "D") < 3:
        return
    o = s.P[1 - i]
    if not o.grave:
        return
    cands = sorted(set(o.grave))
    withetb = [k for k in cands if E.ENTER.get(k) is not None]
    k = max(withetb or cands, key=E.PRI.get)
    o.grave.remove(k)
    fn = E.ENTER.get(k)
    if fn is not None:
        z = E.U(k)
        z.sick = False
        z.x["summoned"] = False
        z.x["src"] = "grave"
        s.ev(f"　シビルカウント3：相手の墓地の {BY_KEY[k].name} の「出た時」を自分が使う")
        fn(s, i, z)
    else:
        s.ev(f"　シビルカウント3：相手の墓地の {BY_KEY[k].name} を山札の下に置く")
    o.deck.insert(0, k)


SLAYER.add("k56_mardan")
add("k56_mardan", "深淵の壊炉 マーダン＝ロウ", 4, "D", power=4000,
    races=("abyssroyal", "abyss"), pri=7, roles="rem dis atk",
    enter=e_mardan, attack=at_mardan,
    text="スレイヤー（バトルする相手のクリーチャーを、たとえ自分が破壊されても破壊する）。"
         "このクリーチャーが出た時、相手の手札を見てクリーチャーを1体選び、捨てさせる"
         "（重要度のいちばん高いクリーチャーを選ぶ）。"
         "シビルカウント3：このクリーチャーが攻撃する時、自分の、闇のクリーチャーまたは闇のタマシードが"
         "合計3つ以上あれば、相手の墓地にあるカードを1枚選んでもよい。そのカードの「出た時」の能力を"
         "自分が1つ使ってもよい。その後、そのカードを持ち主の山札の下に置く"
         "（「出た時」の能力を持つカードのうち重要度のいちばん高いものを選ぶ）",
    source=SRC["k56_mardan"])


# ================================================================ 2 謀遠 テレスコ＝テレス
def px_telesco(s, i, u, atk):
    """手札が1枚もないプレイヤー1人につき+5000"""
    return 5000 * sum(1 for j in (0, 1) if not s.P[j].hand)


def bx_telesco(s, i, u):
    """パワード・ブレイカー：パワー6000ごとにシールドをもう1つブレイクする"""
    return 1 + s.power(i, u, True) // 6000


def ts_telesco(s, i):
    """相手のターンのはじめに、相手の手札を1枚見ないで選び、捨てさせる

    （i＝そのターンのプレイヤー。テレスコ＝テレスの持ち主は 1-i なので、
      自分のカードが相手の場にいる時だけ働く）"""
    if not s.has(1 - i, "k56_telesco"):
        return
    for u in [z for z in s.P[1 - i].board if z.k == "k56_telesco"]:
        if s.over or not s.P[i].hand or not s.abi(1 - i, u):
            continue
        s.ev("　テレスコ＝テレス：相手のターンのはじめに手札を1枚捨てさせる")
        _rand_discard(s, i)


def dw_telesco(s, j, k):
    """相手が自身の手札を1枚捨てた時、自分はカードを1枚引いてもよい（j＝捨てた側）"""
    i = 1 - j
    if s.over or not s.has(i, "k56_telesco"):
        return
    for u in [z for z in s.P[i].board if z.k == "k56_telesco"]:
        if s.over or not s.abi(i, u):
            continue
        s.ev("　テレスコ＝テレス：相手が手札を捨てたので1枚引く")
        s.draw(i, 1)


add("k56_telesco", "謀遠 テレスコ＝テレス", 5, "D", power=5000, blocker=True,
    races=("abyssroyal", "abyss"), pri=8, roles="blk dis draw",
    powerx=px_telesco, brkx=bx_telesco, turnstart=ts_telesco, discardwatch=dw_telesco,
    text="ブロッカー。パワード・ブレイカー（このクリーチャーは、そのパワー6000ごとにシールドをもう1つブレイクする）。"
         "相手のターンのはじめに、相手の手札を1枚見ないで選び、捨てさせる。"
         "相手が自身の手札を1枚捨てた時、自分はカードを1枚引いてもよい。"
         "手札が1枚もないプレイヤー1人につき、このクリーチャーのパワーを+5000する",
    source=SRC["k56_telesco"])


# ================================================================ 3 フットレス＝トレース／「力が欲しいか？」
def te_footless(s, i, u):
    """自分のターンの終わりに、山札の上から1枚を墓地に置く。その後、墓地の闇のカード1枚を手札に戻してもよい"""
    s.mill(i, 1)
    p = s.P[i]
    cs = sorted({k for k in p.grave if "D" in E.MCIV[k]})
    if not cs:
        return
    k = max(cs, key=E.PRI.get)
    p.grave.remove(k)
    p.hand.append(k)
    s.ev(f"　フットレス＝トレース：墓地の {BY_KEY[k].name} を手札に戻す")


def sp_chikara(s, i):
    """アビス・メクレイド5"""
    _mekureido(s, i, 5, lambda c: race_like(c, "abyss"), "アビス・メクレイド5")


add("k56_footless", "フットレス＝トレース／「力が欲しいか？」", 4, "D", power=4000, blocker=True,
    races=("abyssroyal", "abyss"), twin=(4, "D", False), pri=6, roles="blk draw acc",
    tend=te_footless, spell=sp_chikara,
    text="【クリーチャー側】ブロッカー。自分のターンの終わりに、自分の山札の上から1枚目を墓地に置く。"
         "その後、闇のカードを1枚、自分の墓地から手札に戻してもよい（重要度のいちばん高いものを戻す）。"
         "【呪文側・コスト4／闇】アビス・メクレイド5（自分の山札の上から3枚を見て、"
         "その中からコスト5以下のアビスを1枚、コストを支払わずに使ってもよい。残りは山札の下に置く）",
    source=SRC["k56_footless"])


# ================================================================ 4 ア：エヌ：マクア
def e_anmakua(s, i, u):
    """出た時、次のうちいずれか1つを選ぶ
      ▶山札の上から2枚をタップしてマナゾーンに置き、その後マナから1枚を手札に戻す
      ▶プレイヤーを1人選ぶ。そのプレイヤーは墓地をシャッフルして山札の下に置く
      ▶相手の、コスト5以下のクリーチャーでないエレメントをすべてマナゾーンに置く"""
    p, o = s.P[i], s.P[1 - i]
    ts = opp_all(s, i, lambda z: z.c.cost <= 5, kinds="TX")
    if ts:
        s.ev("　ア：エヌ：マクア：相手のコスト5以下の、クリーチャーでないエレメントをすべてマナゾーンへ")
        for t in ts:
            if t in o.board:
                move(s, i, t, "mana")
        return
    tgt = None
    if len(o.grave) >= 6:
        tgt = 1 - i
    elif len(p.deck) <= 5 and len(p.grave) >= 5:
        tgt = i
    if tgt is not None:
        q = s.P[tgt]
        g = q.grave[:]
        s.rng.shuffle(g)
        q.grave = []
        q.deck[:0] = g                       # 山札の下（末尾が上なので先頭が下）
        s.ev(f"　ア：エヌ：マクア：プレイヤー{tgt} の墓地 {len(g)} 枚をシャッフルして山札の下へ")
        return
    s.ramp(i, 2)
    if p.mana:
        k = max(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        p.hand.append(k)
        s.ev(f"　ア：エヌ：マクア：山札の上2枚をマナへ、マナの {BY_KEY[k].name} を手札へ")


add("k56_anmakua", "ア：エヌ：マクア", 5, "N", power=6000, brk=2, mach=True,
    races=("veilabyss", "abyss"), pri=8, roles="acc rem dis",
    enter=e_anmakua,
    text="マッハファイター（このクリーチャーは、出たターンでも相手のタップしているクリーチャーを攻撃できる）。"
         "W・ブレイカー。このクリーチャーが出た時、次のうちいずれか1つを選ぶ。"
         "▶自分の山札の上から2枚を、タップしてマナゾーンに置く。その後、カードを1枚、自分のマナゾーンから手札に戻す。"
         "▶プレイヤーを1人選ぶ。そのプレイヤーは、自身の墓地をシャッフルし、山札の下に置く。"
         "▶相手は、自身のコスト5以下の、クリーチャーではないエレメントをすべてマナゾーンに置く。"
         "（相手のコスト5以下のタマシード等があればそれを、無ければ墓地が6枚以上のプレイヤーの墓地を山札の下へ、"
         "どちらも無ければマナを増やす、という決まりで選ぶ）",
    source=SRC["k56_anmakua"])


# ================================================================ 5 ドミー＝ゾー／「倒したいか？」
def e_domyzo(s, i, u):
    """出た時、自分の山札の上から5枚を墓地に置いてもよい"""
    s.mill(i, 5)


def fa_domyzo(s, i, av, cv):
    """アビスラッシュ：このクリーチャーを自分の墓地から召喚してもよい"""
    p = s.P[i]
    if "k56_domyzo" not in p.grave or s.manaexec(i):
        return []
    n = s.ccost(i, "k56_domyzo", av)
    if n > av or (n > 0 and "D" not in cv):
        return []
    if s.fate(i, "k56_domyzo", "grave", True) != "ok":
        return []
    return [("x:k56_abyssrush", n)]


def ap_domyzo(s, a):
    i = s.tp
    p = s.P[i]
    if "k56_domyzo" not in p.grave:
        return
    p.mused += a[1]
    p.grave.remove("k56_domyzo")
    s.ev(f"アビスラッシュ：ドミー＝ゾー（墓地から召喚・{a[1]}マナ）")
    z = s.enter(i, "k56_domyzo", "grave", True)
    if z is not None:
        z.sa = True                          # 召喚酔いしない
        z.x["k56_onlyp"] = s.turn            # ただし相手プレイヤーだけを攻撃できる
        z.eot = True                         # ターンの終わりに山札の下へ


def sp_taoshitai(s, i):
    """自分の山札の上から1枚目をマナゾーンに置く"""
    s.ramp(i, 1)


add("k56_domyzo", "ドミー＝ゾー／「倒したいか？」", 5, "D", power=6000, brk=2,
    races=("abyssroyal", "abyss"), twin=(2, "N", False), pri=7, roles="atk acc",
    enter=e_domyzo, spell=sp_taoshitai, freeacts=fa_domyzo, actapply={"x:k56_abyssrush": ap_domyzo},
    playrule=lambda deck, k: None,
    text="【クリーチャー側】アビスラッシュ（このクリーチャーを自分の墓地から召喚してもよい。そうしたら、"
         "このターン、このクリーチャーは相手プレイヤーを攻撃でき、ターンの終わりに山札の下に置かれる）。"
         "W・ブレイカー。このクリーチャーが出た時、自分の山札の上から5枚を墓地に置いてもよい。"
         "【呪文側・コスト2／自然】自分の山札の上から1枚目をマナゾーンに置く",
    source=SRC["k56_domyzo"])


# ================================================================ 6 悪魔妖精ベラドンナ
def e_belladonna(s, i, u):
    """出た時、このクリーチャーを破壊してもよい。そうしたら次のうちいずれか1つを選ぶ
      ▶相手の手札を1枚見ないで選び、捨てさせる　▶自分の山札の上から1枚目をマナゾーンに置く"""
    p, o = s.P[i], s.P[1 - i]
    mode = None
    if len(p.mana) < 7 and len(p.deck) > 1:
        mode = "mana"
    elif o.hand:
        mode = "hand"
    if mode is None or u not in p.board:
        return
    if not s.leave(i, u, "grave", destroy=True):
        return
    s.ev("　悪魔妖精ベラドンナ：自身を破壊する")
    if mode == "mana":
        s.ramp(i, 1)
        s.ev("　　山札の上から1枚目をマナゾーンへ")
    else:
        s.ev("　　相手の手札を1枚捨てさせる")
        _rand_discard(s, 1 - i)


add("k56_belladonna", "悪魔妖精ベラドンナ", 2, "DN", power=2000,
    races=("snow", "funkynightmare"), pri=4, roles="acc dis",
    enter=e_belladonna,
    text="このクリーチャーが出た時、このクリーチャーを破壊してもよい。そうしたら、次のうちいずれか1つを選ぶ。"
         "▶相手の手札を1枚見ないで選び、捨てさせる。▶自分の山札の上から1枚目をマナゾーンに置く。"
         "（マナが7枚未満ならマナを増やし、そうでなければ相手の手札を捨てさせる。"
         "どちらも意味がなければ破壊しない）",
    source=SRC["k56_belladonna"])


# ================================================================ 7 超霊淵 ヤバーダン＝ロウ
def e_yabadan(s, i, u):
    """出た時、相手のクリーチャーを1体選んで破壊する。その後、そのクリーチャーのコストと同じ枚数まで、
    自分の山札の上から墓地に置いてもよい"""
    t = s.target(i)
    if t is None:
        return
    cost = t.c.cost
    s.ev(f"　ヤバーダン＝ロウ：{t.c.name} を破壊する")
    destroy(s, i, t)
    if cost > 0 and not s.over:
        s.mill(i, cost)


def at_yabadan(s, i, u):
    """ハイパーモード中、攻撃する時：コスト8以下のクリーチャーを1体、自分の墓地から出してもよい。
    そのクリーチャーはこのターン、相手プレイヤーを攻撃できる"""
    if not u.hyper:
        return
    z = s.revive(i, lambda c: c.cost <= 8, "grave")
    if z is None:
        return
    z.sa = True
    z.x["k56_onlyp"] = s.turn
    s.ev(f"　ヤバーダン＝ロウ：墓地から {z.c.name}（このターン相手プレイヤーを攻撃できる）")


def fa_yabadan(s, i, av, cv):
    """ハイパー化：自分の他のクリーチャーを1体タップする"""
    for u in s.P[i].board:
        if u.k == "k56_yabadan" and not u.hyper:
            if any(z is not u and z.c.kind == "C" and not z.tap for z in s.P[i].board):
                return [("x:k56_hyper", u.uid)]
    return []


def ap_yabadan(s, a):
    i = s.tp
    p = s.P[i]
    u = next((z for z in p.board if z.uid == a[1] and z.k == "k56_yabadan"), None)
    if u is None or u.hyper:
        return
    oth = [z for z in p.board if z is not u and z.c.kind == "C" and not z.tap]
    if not oth:
        return
    s.tap_cre(i, min(oth, key=s.val))
    u.hyper = True
    s.ev("ハイパー化：超霊淵 ヤバーダン＝ロウ（他のクリーチャー1体をタップ）")


E.HYPER_POW["k56_yabadan"] = 4000          # ハイパーモード 9000
E.HYPER_BRK["k56_yabadan"] = 2             # W・ブレイカーはハイパーモード中だけ
add("k56_yabadan", "超霊淵 ヤバーダン＝ロウ", 5, "D", power=5000, brk=1,
    races=("abyssroyal", "superbeast", "abyss"), pri=9, roles="rem atk fin",
    enter=e_yabadan, attack=at_yabadan, freeacts=fa_yabadan, actapply={"x:k56_hyper": ap_yabadan},
    text="このクリーチャーが出た時、相手のクリーチャーを1体選び、破壊する。その後、そのクリーチャーのコストと"
         "同じ枚数まで、自分の山札の上から墓地に置いてもよい。"
         "ハイパー化：自分のメインステップ中、自分の他のクリーチャー1体をタップして、ハイパーモードにする。"
         "【ハイパーモード：パワー9000】W・ブレイカー。"
         "このクリーチャーが攻撃する時、コスト8以下のクリーチャーを1体、自分の墓地から出してもよい。"
         "そのクリーチャーはこのターン、相手プレイヤーを攻撃できる",
    source=SRC["k56_yabadan"])


# ================================================================ 8 深淵の瘴炉 インシネ＝ロウ
def tp_insine(s, i):
    """ターンの終わりに、そのプレイヤーのタップしているクリーチャーの数を書き留める。

    次にそのプレイヤーのターンが来た時、その数だけクリーチャーがアンタップする
    （インシネ＝ロウの軽減を数えるため。盤面は一切変えないので、他のデッキの対戦には影響しない）。"""
    p = s.P[i]
    n = sum(1 for u in p.board if u.c.kind == "C" and u.tap)
    p.x["k56_untap"] = (s.turn + 1, n)


def cx_insine(s, i, av):
    """このターンアンタップしたクリーチャー1体につき、召喚コストを2少なくする（1より少なくならない）"""
    rec = s.P[i].x.get("k56_untap")
    n = rec[1] if rec is not None and rec[0] == s.turn else 0
    return max(1, 5 - 2 * n)


def e_insine(s, i, u):
    """出た時、相手の手札を1枚見ないで選び、捨てさせる"""
    if s.P[1 - i].hand:
        s.ev("　インシネ＝ロウ：相手の手札を1枚捨てさせる")
        _rand_discard(s, 1 - i)


def dw_insine(s, j, k):
    """相手が自身の手札を1枚捨てた時、相手のクリーチャー1体をこのターン-3000する（j＝捨てた側）"""
    i = 1 - j
    if s.over or not s.has(i, "k56_insine"):
        return
    for u in [z for z in s.P[i].board if z.k == "k56_insine"]:
        if s.over or not s.abi(i, u):
            continue
        t = s.target(i)
        if t is None:
            return
        t.pw -= 3000
        s.ev(f"　インシネ＝ロウ：{t.c.name} をこのターン-3000")
        if s.power(j, t) <= 0:
            s.leave(j, t, "grave", by_opp=True, destroy=True)


add("k56_insine", "深淵の瘴炉 インシネ＝ロウ", 5, "D", power=6000, brk=2,
    races=("abyssroyal", "abyss"), pri=8, roles="rem dis",
    costx=cx_insine, enter=e_insine, discardwatch=dw_insine, tendp=tp_insine,
    text="このターンアンタップしたクリーチャー1体につき、このクリーチャーの召喚コストを2少なくする"
         "（ただし1より少なくはならない）。W・ブレイカー。"
         "このクリーチャーが出た時、相手の手札を1枚見ないで選び、捨てさせる。"
         "相手が自身の手札を1枚捨てた時、相手のクリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを-3000する"
         "（パワー0以下になったら破壊される）",
    status="partial",
    note="本来は相手のクリーチャーのアンタップも数えるが、エンジンに「アンタップした時」の差し込み口が"
         "無いので、数えているのは「ターンのはじめのアンタップ」だけ（ターンの終わりにタップしている"
         "クリーチャーの数を書き留めて、次のそのプレイヤーのターンにその数を使う）。"
         "そのため、ターン中に効果でアンタップしたクリーチャーは数に入らない（REQUEST_56.md に要望）",
    source=SRC["k56_insine"])


# ================================================================ 9 ア：グンテ
def e_agunte(s, i, u):
    """出た時、相手のコスト5以下のエレメントを1つ選び、持ち主のマナゾーンに置いてもよい。
    S・トリガー・プラスのP能力：相手のターンで、そのターンに自分のシールドが2つ以上ブレイクされていれば、
    相手のクリーチャーを2体まで選び、持ち主のマナゾーンに置く"""
    t = s.target(i, lambda z: z.c.cost <= 5, kinds="CTX")
    if t is not None:
        s.ev(f"　ア：グンテ：{t.c.name} を持ち主のマナゾーンに置く")
        move(s, i, t, "mana")
    if s.tp != i and s.P[i].brk_t >= 2:
        for _ in range(2):
            if s.over:
                return
            t = s.target(i)
            if t is None:
                return
            s.ev(f"　ア：グンテのP能力：{t.c.name} を持ち主のマナゾーンに置く")
            move(s, i, t, "mana")


add("k56_agunte", "ア：グンテ", 4, "N", power=4000, trig=True,
    races=("veilabyss", "abyss"), pri=6, roles="rem trg",
    enter=e_agunte,
    text="S・トリガー・プラス（このクリーチャーを自分のシールドゾーンから手札に加える時、コストを支払わずに"
         "すぐ召喚してもよい。それが相手のターンで、そのターン中に自分のシールドが2つ以上ブレイクされていれば、"
         "このクリーチャーにP能力を与える）。"
         "P−このクリーチャーが出た時、相手のクリーチャーを2体まで選び、持ち主のマナゾーンに置く。"
         "このクリーチャーが出た時、相手のコスト5以下のエレメントを1つ選び、持ち主のマナゾーンに置いてもよい",
    source=SRC["k56_agunte"])


# ================================================================ 10 オ：ドユニワ／喰土邪覇
def sp_kuudojaha(s, i):
    """カードを1枚、自分のマナゾーンから墓地に置く。その後、自分の山札の上から2枚をタップしてマナゾーンに置く"""
    p = s.P[i]
    if p.mana:
        k = min(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        s.grave_put(i, k)
        s.ev(f"　喰土邪覇：マナの {BY_KEY[k].name} を墓地に置く")
    s.ramp(i, 2)


def lf_doyuniwa(s, i, u, dest):
    """メガ・ラスト・バースト：離れて手札・マナゾーン・墓地に置かれた時、呪文側をただで唱えてもよい"""
    if dest not in ("hand", "mana", "grave") or s.over:
        return
    if not s.spell_ok(i, 3):
        return
    p = s.P[i]
    if dest == "mana":
        if "k56_doyuniwa" not in p.mana:
            return
        s.take_mana(i, "k56_doyuniwa")
    else:
        zone = p.hand if dest == "hand" else p.grave
        if "k56_doyuniwa" not in zone:
            return
        zone.remove("k56_doyuniwa")
    s.ev("　メガ・ラスト・バースト：喰土邪覇をコストを支払わずに唱える")
    _cast_free(s, i, "k56_doyuniwa", twin=True)


add("k56_doyuniwa", "オ：ドユニワ／喰土邪覇", 5, "N", power=6000, brk=2, gs=True,
    races=("veilabyss", "abyss"), twin=(3, "N", False), pri=7, roles="acc shd",
    spell=sp_kuudojaha, left=lf_doyuniwa,
    text="【クリーチャー側】G・ストライク（このクリーチャーを自分のシールドゾーンから手札に加える時、相手に見せ、"
         "相手のクリーチャーを1体選んでもよい。このターン、そのクリーチャーは攻撃できない）。W・ブレイカー。"
         "メガ・ラスト・バースト（このクリーチャーが離れて、手札、マナゾーン、または墓地に置かれた時、"
         "このカードの呪文側をコストを支払わずに唱えてもよい）。"
         "【呪文側・コスト3／自然】カードを1枚、自分のマナゾーンから墓地に置く。その後、自分の山札の上から2枚を"
         "タップしてマナゾーンに置く（マナからは重要度のいちばん低いカードを墓地に置く）",
    source=SRC["k56_doyuniwa"])


# ================================================================ 11 めっちゃ！デンヂャラスG3／ケッシング・ゼロ
def bx_g3(s, i, u):
    """G・ブレイカー：相手のシールドをすべてブレイクする"""
    return max(1, len(s.P[1 - i].sh))


def bp_gbreaker(s, i, u):
    """デンヂャラスG3がG・ブレイカーを与えたクリーチャーも、相手のシールドをすべてブレイクする"""
    if u.k == "k56_g3" or u.x.get("k56_gb") != s.turn:
        return 0
    return max(0, len(s.P[1 - i].sh) - u.c.brk)


def ae_gbreaker(s, i, u):
    """G・ブレイカー：その攻撃の後、自分のシールドをすべてブレイクする"""
    if u.k != "k56_g3" and u.x.get("k56_gb") != s.turn:
        return
    n = len(s.P[i].sh)
    if n <= 0 or s.over:
        return
    s.ev(f"　G・ブレイカー：{u.c.name} の攻撃の後、自分のシールド{n}枚をすべてブレイク")
    s.break_sh(1 - i, n)


def e_g3(s, i, u):
    """出た時、「シールドいらねえー!」と言ってもよい。そうしたら、そのターン、自分のクリーチャー3体に
    「G・ブレイカー」を与える"""
    if not s.P[1 - i].sh:
        return                                   # 相手のシールドが0なら、自分の盾だけ割れて損なので言わない
    cs = [z for z in s.P[i].board if z.c.kind == "C" and z is not u and z.x.get("k56_gb") != s.turn]
    if not cs:
        return
    s.ev("　めっちゃ！デンヂャラスG3：「シールドいらねえー!」")
    for z in sorted(cs, key=s.val, reverse=True)[:3]:
        z.x["k56_gb"] = s.turn
        s.ev(f"　　{z.c.name} に G・ブレイカー を与える")


def sp_kesshing(s, i):
    """「気に入らねぇやつは消す」と言ってもよい。そうしたら、このターン、相手のクリーチャーの能力をすべて無視する"""
    s.P[i].x["k56_kes"] = s.turn
    s.ev("　ケッシング・ゼロ：「気に入らねぇやつは消す」（このターン、相手のクリーチャーの能力をすべて無視する）")


def ab_kesshing(s, j, u):
    """ケッシング・ゼロを唱えた側から見た相手のクリーチャーは、このターン能力をすべて無視される"""
    if u.c.kind != "C":
        return False
    return s.P[1 - j].x.get("k56_kes") == s.turn


add("k56_g3", "めっちゃ！デンヂャラスG3／ケッシング・ゼロ", 10, "", power=21300, brk=1,
    races=("jokers",), twin=(5, "", True), pri=13, roles="fin atk trg dis",
    enter=e_g3, spell=sp_kesshing, brkx=bx_g3, brkplus=bp_gbreaker, atkend=ae_gbreaker, abilock=ab_kesshing,
    text="【クリーチャー側・無色[ジョーカーズ]】G・ブレイカー（このクリーチャーは、相手のシールドをすべてブレイクし、"
         "その攻撃の後、自分のシールドをすべてブレイクする）。"
         "このクリーチャーが出た時、「シールドいらねえー!」と言ってもよい。そうしたら、そのターン、"
         "自分のクリーチャー3体に「G・ブレイカー」を与える（重要度の高い3体に与える。"
         "相手のシールドが0枚の時は言わない）。"
         "【呪文側・コスト5／無色】S・トリガー。「気に入らねぇやつは消す」と言ってもよい。そうしたら、このターン、"
         "相手のクリーチャーの能力すべてを無視する",
    source=SRC["k56_g3"])


# ================================================================ 12 ヘルトッQ
def e_hertoq(s, i, u):
    """出た時、自分のジョーカーズ・クリーチャー1体につき1枚、カードを引いてもよい"""
    u.x["k56_onlyp"] = s.turn               # 出たターン、相手プレイヤーを攻撃できる
    p = s.P[i]
    n = sum(1 for z in p.board if z.c.kind == "C" and "jokers" in z.c.races)
    n = min(n, max(0, len(p.deck) - 1))
    if n > 0:
        s.ev(f"　ヘルトッQ：自分のジョーカーズ {n} 体ぶん引く")
        s.draw(i, n)


add("k56_hertoq", "ヘルトッQ", 5, "", power=5050, sa=True,
    races=("jokers",), pri=7, roles="draw atk",
    enter=e_hertoq,
    text="このクリーチャーは、出たターン、相手プレイヤーを攻撃できる（クリーチャーは攻撃できない）。"
         "このクリーチャーが出た時、自分のジョーカーズ・クリーチャー1体につき1枚、カードを引いてもよい"
         "（山札が尽きない範囲で引く）",
    source=SRC["k56_hertoq"])


# ================================================================ 13 カツラデランス／「アフロ行きま〜す！！」
def e_katsura(s, i, u):
    """出た時、自分の山札の一番下のカードを墓地に置く。それがコスト6以下のジョーカーズ・クリーチャーなら出す"""
    p = s.P[i]
    if not p.deck:
        return
    k = p.deck.pop(0)                        # 山札は末尾が上なので、先頭が一番下
    s.grave_put(i, k)
    c = BY_KEY[k]
    s.ev(f"　カツラデランス：山札の一番下の {c.name} を墓地に置く")
    if not (_playable_cre(c, 6) and "jokers" in c.races) or k not in p.grave or s.over:
        return
    if s.fate(i, k, "grave", False) != "ok":
        return
    p.grave.remove(k)
    s.ev(f"　　{c.name} を出す")
    s.enter(i, k, "grave", False)


def sp_afro(s, i):
    """自分の手札を1枚捨て、その後、カードを2枚引く"""
    k = worst_hand(s, i)
    if k is not None:
        s.discard(i, k)
    s.draw(i, 2)


add("k56_katsura", "カツラデランス／「アフロ行きま〜す！！」", 7, "F", power=7000, brk=2,
    races=("jokers",), twin=(2, "F", False), pri=9, roles="atk draw",
    enter=e_katsura, spell=sp_afro,
    text="【クリーチャー側・火文明[ジョーカーズ]】W・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の一番下のカードを墓地に置く。"
         "それがコスト6以下のジョーカーズ・クリーチャーなら出す。"
         "【呪文側・コスト2／火】自分の手札を1枚捨て、その後、カードを2枚引く"
         "（重要度のいちばん低い手札を捨てる）",
    source=SRC["k56_katsura"])


# ================================================================ 14 プリプリズン
def e_puriprizon(s, i, u):
    """出た時、山札の上から4枚を見て、その中からジョーカーズ・クリーチャー1体を手札に加えてもよい。
    革命0：自分のシールドが1つもなければ、コスト7以下のジョーカーズ・クリーチャーを1体、手札から出してもよい"""
    s.dig(i, 4, lambda k: BY_KEY[k].kind == "C" and "jokers" in BY_KEY[k].races, "bottom")
    p = s.P[i]
    if p.sh or s.over:
        return
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if _playable_cre(c, 7) and "jokers" in c.races and E.PRI[k] > bv:
            if s.fate(i, k, "hand", False) == "ok":
                best, bv = k, E.PRI[k]
    if best is None:
        return
    s.ev(f"　革命0：手札から {BY_KEY[best].name} を出す")
    free_play(s, i, best)


add("k56_puriprizon", "プリプリズン", 5, "F", power=1000, trig=True,
    races=("jokers",), pri=6, roles="trg draw atk",
    enter=e_puriprizon,
    text="S・トリガー。このクリーチャーが出た時、自分の山札の上から4枚を見る。"
         "その中からジョーカーズ・クリーチャーを1体表向きにし、手札に加えてもよい。"
         "残りを好きな順序で山札の下に置く。"
         "革命0：このクリーチャーが出た時、自分のシールドが1つもなければ、"
         "コスト7以下のジョーカーズ・クリーチャーを1体、自分の手札から出してもよい",
    source=SRC["k56_puriprizon"])


# ================================================================ 15 チキン・タッ太
def e_chicken(s, i, u):
    """出た時、相手の「ブロッカー」を持つクリーチャーを1体破壊する"""
    t = s.target(i, lambda z: s.kw(z, "blocker") or any(f(s, z) for f in E.BLOCKOK))
    if t is None:
        return
    s.ev(f"　チキン・タッ太：ブロッカーの {t.c.name} を破壊する")
    destroy(s, i, t)


def fa_chicken(s, i, av, cv):
    """J・O・E 2：コストを2少なくして召喚してもよい"""
    p = s.P[i]
    if "k56_chicken" not in p.hand:
        return []
    n = max(0, s.ccost(i, "k56_chicken", av) - 2)
    if n > av or (n > 0 and "F" not in cv):
        return []
    if s.fate(i, "k56_chicken", "hand", True) != "ok":
        return []
    return [("x:k56_joe", n)]


def ap_chicken(s, a):
    i = s.tp
    p = s.P[i]
    if "k56_chicken" not in p.hand:
        return
    p.mused += a[1]
    p.hand.remove("k56_chicken")
    s.ev(f"J・O・E 2：チキン・タッ太（コストを2少なくして召喚・{a[1]}マナ）")
    z = s.enter(i, "k56_chicken", "hand", True)
    if z is not None:
        z.eot = True                         # ターンの終わりに山札の下へ
        z.x["k56_joe"] = True


def te_chicken(s, i, u):
    """J・O・E 2 で召喚したなら、ターンの終わりに山札の下に置いて1枚引く
    （山札の下に置くのはエンジンが u.eot で行う）"""
    if not u.x.get("k56_joe"):
        return
    s.ev("　J・O・E 2：チキン・タッ太を山札の下に置いて1枚引く")
    s.draw(i, 1)


add("k56_chicken", "チキン・タッ太", 6, "F", power=5000, sa=True,
    races=("jokers",), pri=7, roles="rem atk draw",
    enter=e_chicken, tend=te_chicken, freeacts=fa_chicken, actapply={"x:k56_joe": ap_chicken},
    text="J・O・E 2（このクリーチャーを、コストを2少なくして召喚してもよい。そうしたら、このターンの終わりに、"
         "これを山札の下に置く。下に置いたら、カードを1枚引く）。"
         "スピードアタッカー。"
         "このクリーチャーが出た時、相手の「ブロッカー」を持つクリーチャーを1体破壊する",
    source=SRC["k56_chicken"])
