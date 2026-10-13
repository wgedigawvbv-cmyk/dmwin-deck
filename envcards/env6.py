"""cards3.py の7デッキで「省いていた能力」を実装する

  これまで note に「省いた」「簡略化」と書いていた能力を、調べ直して全部実装した。
  調べ直して分かった取り違え：
    ・俳句爵 der'Bande に D・D・D はない（D・D・D を持っているのは 心転地と透幻郷の決断）。
    ・チャクラ・デル・フィンに マナ武装5 はない（マナ武装5 を持っているのは 天V王 エバーラスト）。
    ・超七極 Gio は「能力なし」ではなく、コスト9・光・パワー11500・ブロッカー・進化（光のクリーチャーの上）で、
      召喚する時に手札の他のコスト9のカードを見せた枚数ぶんコストが下がる（cards3.py 側を直した）。
  実装しきれない点はカードごとに note に書いてある。
"""
import engine3 as E
from cards3 import BY_KEY

import envreg
from envreg import destroy, free_play, move
from envcards.env0 import SLAYER

# ---------------------------------------------------------------- アロマの海幻（シンカライズ）
E.SHINKA.add("aroma")          # タマシードだが進化元になれる（cards3 の note どおり）
SLAYER.add("kuzen")            # 雷撃の冥将クーゼンのスレイヤー


# ---------------------------------------------------------------- 心転地と透幻郷の決断：D・D・D
def _shinten_one(s, i):
    """選択肢を1回選ぶ（engine3 の sp_shinten と同じ決め方。エレメントにクロスギアも含める）"""
    p = s.P[i]
    o = s.P[1 - i]
    mid = s.tp == i and s.atk is not None
    if mid:
        k = None
        if "tenbin" in p.hand and s.spell_ok(i, 3):
            k = "tenbin"
        elif "shunsen" in p.hand and s.spell_ok(i, 3) and not s.atk.re:
            k = "shunsen"
        if k is not None:
            p.hand.remove(k)
            s.ev(f"　心転地：手札の {BY_KEY[k].name} をただで")
            s.cast(i, k)
            return
    t = None if o.protect else s.target(i, lambda x: x.c.cost <= 6, "CTX")
    if t is not None and (E.PRI[t.k] >= 5 or (mid and s.can_block(t))):
        s.ev(f"　心転地：{t.c.name} をマナへ")
        move(s, i, t, "mana")
        return
    best, bv = None, 0
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.cost > 3 or p.ban == c.cost:
            continue
        if c.kind == "C":
            if c.evo and not c.neo or s.fate(i, k, "hand", True) != "ok":
                continue
        elif c.kind == "S":
            continue
        elif c.kind == "G" and s.tp == i and s.has(1 - i, "fujin"):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　心転地：手札の {BY_KEY[best].name} をただで")
        free_play(s, i, best)
        return
    s.draw(i, 2)
    if p.hand:
        k = min(p.hand, key=E.PRI.get)
        p.hand.remove(k)
        p.deck.insert(0, k)


def sp_shinten(s, i):
    """2回選ぶ。D・D・D で唱えたなら3回選ぶ"""
    n = 3 if s.P[i].x.pop("shinten_ddd", False) else 2
    for _ in range(n):
        if s.over:
            return
        _shinten_one(s, i)


E.SPELL["shinten"] = sp_shinten


def w_shinten_ddd(s, i, u):
    """D・D・D[光/水/自然(5)]：自分のクリーチャーが攻撃する時、手札かマナゾーンから5マナで唱える"""
    p = s.P[i]
    if len(p.mana) - p.mused < 5 or not set("LWN") <= E.civs(p) or not s.spell_ok(i, 4):
        return
    src = "hand" if "shinten" in p.hand else ("mana" if "shinten" in p.mana and not s.manaexec(i) else None)
    if src is None:
        return
    if src == "hand":
        p.hand.remove("shinten")
    else:
        s.take_mana(i, "shinten")
    p.mused += 5
    p.x["shinten_ddd"] = True
    s.ev(f"　D・D・D：{'手札' if src == 'hand' else 'マナ'}から心転地と透幻郷の決断を5マナで唱える")
    s.cast(i, "shinten")


E.ATKWATCH.append(w_shinten_ddd)


# ---------------------------------------------------------------- 天V王 エバーラスト：マナ武装5
def rep_everlast(s, i, u, dest, destroy_):
    """自分のクリーチャーが離れる時、マナに光が5枚以上あれば、かわりに自分のシールド2つを手札に加えてよい"""
    p = s.P[i]
    if u.c.kind != "C" or not s.has(i, "everlast"):
        return False
    if sum(1 for x in p.mana if "L" in E.MCIV[x]) < 5:
        return False
    dn = [j for j in range(len(p.sh) - 1, -1, -1) if not p.sh[j][1]]
    if len(dn) < 2:
        return False
    for j in dn[:2]:
        p.hand.append(p.sh.pop(j)[0])
    s.shield_left()
    s.ev(f"　マナ武装5：シールド2つを手札に加えて {u.c.name} を守る")
    return True


E.LEAVEREP.append(rep_everlast)


# ---------------------------------------------------------------- 超七極 Gio：召喚コストの軽減
def cx_gio(s, i, av):
    n = sum(1 for k in s.P[i].hand if k != "gio" and BY_KEY[k].cost == 9)
    return max(1, 9 - n)


E.COSTX["gio"] = cx_gio


# ---------------------------------------------------------------- ストラトバッグ：本来の2つの能力
def ml_strato(s, i, k):
    """各ターンはじめて自分のマナゾーンからカードが離れた時、山札の上1枚をマナゾーンに置いてよい"""
    p = s.P[i]
    if p.x.get("strato_turn") == s.turn or not s.has(i, "strato"):
        return
    p.x["strato_turn"] = s.turn
    s.ramp(i, 1)


def ld_strato(s, i, u, dest, destroy_):
    """バトルゾーンの相手のカードが離れる時、かわりに持ち主のマナゾーンに置いてもよい"""
    if dest == "mana" or not s.has(1 - i, "strato"):
        return None
    if s.tp == i:                      # 自分のカードが自分の都合で離れる時は置き換えない（相手の任意効果）
        return "mana" if dest == "grave" else None
    return "mana"


E.MANALEAVE.append(ml_strato)
E.LEAVEDEST.append(ld_strato)


# ---------------------------------------------------------------- クーゼン：フシギバースとラスト・バースト
def acts_kuzen(s, i, av, cv):
    """フシギバース[闇/自然(8)]：墓地から、自分のクリーチャー1体をタップしてマナに置いて召喚する"""
    p = s.P[i]
    if "kuzen" not in p.grave or not set("DN") <= cv or s.manaexec(i):
        return []
    cands = [u for u in p.board if u.c.kind == "C" and not u.tap]
    if not cands:
        return []
    best = min(cands, key=s.val)
    n = max(0, 8 - best.c.cost)
    if n <= av and s.fate(i, "kuzen", "grave", True) == "ok":
        return [("x:kuzen", n, best.uid)]
    return []


def ap_kuzen(s, a):
    i = s.tp
    p = s.P[i]
    u = next((z for z in p.board if z.uid == a[2]), None)
    if u is None or "kuzen" not in p.grave:
        return
    p.mused += a[1]
    p.board.remove(u)
    s.add_mana(i, u.k, True)
    for k in u.under:
        s.add_mana(i, k, True)
    p.grave.remove("kuzen")
    s.ev(f"フシギバース：{u.c.name} をマナに置いて雷撃の冥将クーゼン（{a[1]}マナ）")
    s.enter(i, "kuzen", "grave", True)


def d_kuzen(s, i, u):
    """ラスト・バースト：破壊された時、呪文側をただで唱えてよい"""
    if "kuzen" in s.P[i].grave and s.spell_ok(i, 2):
        s.P[i].grave.remove("kuzen")
        s.ev("　ラスト・バースト：ダーク・ライフをただで唱える")
        s.cast(i, "kuzen", True)


E.FREE_ACTS.append(acts_kuzen)
E.ACTAPPLY["x:kuzen"] = ap_kuzen
E.DESTROYED["kuzen"] = d_kuzen


# ---------------------------------------------------------------- デンジャデオン：マナゾーンからの召喚
def acts_dangerdeon(s, i, av, cv):
    """各ターン1度、自分のマナゾーンからクリーチャーを召喚してよい"""
    p = s.P[i]
    if not s.has(i, "dangerdeon") or p.x.get("dd_turn") == s.turn or s.manaexec(i):
        return []
    out = []
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if c.kind != "C" or (c.evo and not c.neo):
            continue
        n = s.ccost(i, k, av)
        if n <= av and cv.issuperset(c.civ) and s.fate(i, k, "mana", True) == "ok":
            out.append(("x:ddmana", k, n))
    return out


def ap_dangerdeon(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.mana:
        return
    p.x["dd_turn"] = s.turn
    p.mused += a[2]
    s.take_mana(i, k)
    s.ev(f"デンジャデオン：マナゾーンから {BY_KEY[k].name} を召喚（{a[2]}マナ）")
    s.enter(i, k, "mana", True)


def sp_dangerdeon(s, i):
    """呪文側：相手のエレメント2つまでを持ち主のマナゾーンに置く"""
    o = s.P[1 - i]
    if o.protect:
        return
    for _ in range(2):
        t = s.target(i, kinds="CTX")
        if t is None:
            break
        move(s, i, t, "mana")


E.FREE_ACTS.append(acts_dangerdeon)
E.ACTAPPLY["x:ddmana"] = ap_dangerdeon
E.SPELL["dangerdeon"] = sp_dangerdeon


# ---------------------------------------------------------------- フラワー・ハート：墓地ドローと超魂X
def l_fheart(s, i, u, dest):
    if dest == "grave":
        s.draw(i)


def w_fheart(s, i, u):
    """超魂X：下にフラワー・ハートがあるクリーチャーが攻撃する時、1枚引いて手札を1枚捨てる"""
    if "fheart" not in u.under:
        return
    p = s.P[i]
    before = len(p.hand)
    s.draw(i)
    if len(p.hand) > before and p.hand:
        k = min(p.hand, key=E.PRI.get)
        s.discard(i, k)


E.LEFT["fheart"] = l_fheart
E.ATKWATCH.append(w_fheart)


# ---------------------------------------------------------------- 叛逆の絆：山札の上下と革命0トリガー
def e_hangyaku(s, i, u):
    """出た時・攻撃する時：相手のクリーチャー1体を選び、相手がそれを山札の上か下に置く"""
    t = s.target(i)
    if t is None:
        return
    o = s.P[1 - i]
    k = t.k
    top = E.PRI[k] >= 5                  # 相手が選ぶ：大事なクリーチャーなら引き直せる山札の上
    if s.leave(1 - i, t, "deck", by_opp=True) and top and o.deck and o.deck[0] == k:
        o.deck.remove(k)
        o.deck.append(k)
        s.ev(f"　{BY_KEY[k].name} は山札の上に置かれた")


def react_hangyaku(s, di, au):
    """革命0トリガー：自分のシールドが0枚で攻撃された時、手札から表向きにし、
    山札の上が水の進化でないクリーチャーならそれを出して、叛逆の絆をその上に置く"""
    d = s.P[di]
    if d.sh or "hangyaku" not in d.hand or len(d.deck) <= 1:
        return False
    k = d.deck[-1]
    c = BY_KEY[k]
    if c.kind != "C" or "W" not in c.civ or c.evo:
        return False
    if s.fate(di, k, "deck", False) != "ok" or s.fate(di, "hangyaku", "hand", False) != "ok":
        return False
    d.deck.pop()
    d.hand.remove("hangyaku")                   # 先に手札から表向きにする
    s.ev(f"　革命0トリガー：{c.name} を出して叛逆の絆を重ねる")
    base = s.enter(di, k, "deck", False)
    if base is None or base not in d.board:
        d.hand.append("hangyaku")               # 進化元が出なければ叛逆の絆は手札に戻る
        return False
    u = s.enter(di, "hangyaku", "hand", False, on=base)
    return u is not None


E.ENTER["hangyaku"] = e_hangyaku
E.ATTACK["hangyaku"] = e_hangyaku
E.REACT["hangyaku"] = react_hangyaku


# ---------------------------------------------------------------- エバーラスト・アーテル：エレメントとして扱う
def everlast(s, i):
    """出た時・攻撃する時：エレメント1つをシールドにする。そうしなければ山札の上1枚をシールドにする"""
    o = s.P[1 - i]
    t = None if o.protect else s.target(i, kinds="CTX")
    if t is not None and t.k != "douki" and E.PRI[t.k] >= 5:
        s.ev(f"　エバーラスト：{t.c.name} をシールドに")
        move(s, i, t, "shield")
    else:
        s.add_shield(i)


E.Game.everlast = lambda s, i: everlast(s, i)


_ARTEL_BUSY = []


def rep_artel(s, i, u, dest, destroy_):
    """アーテル・ゴルギーニ：離れる時、かわりに自分の他のクリーチャー1体を破壊してもよい

    身代わりで破壊するクリーチャーの破壊は、さらに別のアーテルで置き換えない
    （同じできごとに置き換えを重ねて無限に続くのを防ぐ。ルール上も無限ループは作れない）"""
    if u.k != "artel" or _ARTEL_BUSY:
        return False
    oth = [z for z in s.P[i].board if z is not u and z.c.kind == "C"]
    if not oth:
        return False
    z = min(oth, key=s.val)
    s.ev(f"　アーテル・ゴルギーニ：かわりに {z.c.name} を破壊")
    _ARTEL_BUSY.append(1)
    try:
        s.leave(i, z, "grave", destroy=True)
    finally:
        _ARTEL_BUSY.pop()
    return True


E.LEAVEREP.append(rep_artel)


# ---------------------------------------------------------------- 巨大設計図（単体のカード）
# 超七極 Gio のツインパクトとは別に、同じ名前の呪文単体のカードがある（殿堂入りではなく4枚使える）。
def sp_kyodai(s, i):
    """山札の上から4枚を見て、その中のコスト7以上のクリーチャーをすべて手札に加える。残りは山札の下へ"""
    p = s.P[i]
    n = min(4, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    got = [k for k in top if BY_KEY[k].kind == "C" and BY_KEY[k].cost >= 7]
    for k in got:
        top.remove(k)
        p.hand.append(k)
    s.ev(f"　巨大設計図：コスト7以上のクリーチャー{len(got)}枚を手札へ")
    for k in top:
        p.deck.insert(0, k)


envreg.add("e_kyodai", "巨大設計図", 2, "N", kind="S", pri=4, roles="draw", spell=sp_kyodai,
           text="自分の山札の上から4枚を表向きにする。その中のコスト7以上のクリーチャーをすべて手札に加え、"
                "残りを好きな順序で山札の下に置く",
           source="https://dmwiki.net/《巨大設計図》")
