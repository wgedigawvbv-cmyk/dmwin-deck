"""cardspec2.json の29枚（《グレートブルーの海幻》は env1 に実装済みなので除く）

  能力は省かずに1枚ずつ書いた。エンジンに差し込み口がなくて表せなかったところだけ status="partial" にして note に書いた。
  調べ直したところ：《斬隠将撃龍ニバイケン》と《「GG」-001》は dmwiki の本文を読んで cardspec の内容が正しいことを確かめた。

  この版で新しく書いた仕組み
    ・D・D・D（自分のクリーチャーの攻撃時、手札からコストを払って出す）＝ atkwatch で実装（env6 の心転地と同じ考え方）
    ・デッキ進化GV（山札の上3枚を下に置いて出す）＝ freeacts ＋ actapply
    ・スター進化（離れる時、一番上の1枚だけが離れる）＝ leaverep で下のカードを場に戻す
    ・チャージャー（唱えた後マナゾーンへ）＝ nograve=True ＋ 呪文の最後で s.add_mana

  envtest で △（使えた場面0）になる2枚について
    ・愛銀河マーズ・シンギュラリティ：デッキ進化GVは freeacts の手（("x:mars", コスト)）で出すため、
      envtest の「手の2番目がカードのキーか」という見分け方に引っかからない。実戦（game_smoke）では使われている。
      既に実装済みの《愛銀河 マーキュリー・スターフォージ》や侵略の札も同じ理由で △ になる。
    ・オンソク童子 ＜ターボ.鬼＞：スター進化なので進化元が要るが、envtest の決まった場面には
      レクスターズも火のクリーチャーもいない（場にいるのは同期の妖精だけ）。実戦では使われている。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move, opp_all
from envcards.env0 import (guardman, SLAYER, exlife_enter, exlife_rep, fx_dream, race_like,
                           star_evo_rep)

SRC = {
    "e_shinkiro":
        "https://dmwiki.net/%E3%80%8A%E7%9C%9F%E6%B0%97%E6%A5%BC%E3%81%A8%E8%AA%A0%E5%81%BD%E6%84%9F%E3%81%AE%E6%B1%BA%E6%96%AD%E3%80%8B",
    "e_rodzojia":
        "https://dmwiki.net/%E3%80%8A%E9%A0%82%E4%B8%8A%E9%80%A3%E7%B5%90%20%E3%83%AD%E3%83%83%E3%83%89%E3%83%BB%E3%82%BE%E3%83%BC%E3%82%B8%E3%82%A25th%E3%80%8B",
    "e_jadoredzone":
        "https://dmwiki.net/%E3%80%8A%E8%BD%9F%E3%81%8F%E9%82%AA%E9%81%93%20%E3%83%AC%E3%83%83%E3%83%89%E3%82%BE%E3%83%BC%E3%83%B3%E3%80%8B",
    "e_marssing":
        "https://dmwiki.net/%E3%80%8A%E6%84%9B%E9%8A%80%E6%B2%B3%E3%83%9E%E3%83%BC%E3%82%BA%E3%83%BB%E3%82%B7%E3%83%B3%E3%82%AE%E3%83%A5%E3%83%A9%E3%83%AA%E3%83%86%E3%82%A3%E3%80%8B",
    "e_nibaiken":
        "https://dmwiki.net/%E3%80%8A%E6%96%AC%E9%9A%A0%E5%B0%86%E6%92%83%E9%BE%8D%E3%83%8B%E3%83%90%E3%82%A4%E3%82%B1%E3%83%B3%E3%80%8B",
    "e_golgieoja":
        "https://dmwiki.net/%E3%80%8A%E8%BD%9F%E4%A1%9B%E5%90%88%E4%BD%93%20%E3%82%B4%E3%83%AB%E3%82%AE%E3%83%BC%E3%82%AA%E3%83%BC%E3%82%B8%E3%83%A3%E3%83%BC%E3%80%8B",
    "e_mendels":
        "https://dmwiki.net/%E3%80%8A%E3%83%A1%E3%83%B3%E3%83%87%E3%83%AB%E3%82%B9%E3%82%BE%E3%83%BC%E3%83%B3%E3%80%8B",
    "e_tores":
        "https://dmwiki.net/%E3%80%8A%E9%85%8D%E8%86%B3%E7%8A%AC%E3%81%AE%E3%83%88%E3%83%AC%E3%82%B9%E3%80%8B",
    "e_perfect":
        "https://dmwiki.net/%E3%80%8A%E6%94%AF%E9%85%8D%E3%81%AE%E7%B2%BE%E9%9C%8A%E3%83%9A%E3%83%AB%E3%83%95%E3%82%A7%E3%82%AF%E3%83%88%EF%BC%8F%E3%82%AE%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%B7%E3%83%BC%E3%83%BB%E3%83%81%E3%83%A3%E3%83%BC%E3%82%B8%E3%83%A3%E3%83%BC%E3%80%8B",
    "e_aqnetwork":
        "https://dmwiki.net/%E3%80%8AAQ%20NETWORK%E3%80%8B",
    "e_onsoku":
        "https://dmwiki.net/%E3%80%8A%E3%82%AA%E3%83%B3%E3%82%BD%E3%82%AF%E7%AB%A5%E5%AD%90%20%EF%BC%9C%E3%82%BF%E3%83%BC%E3%83%9C.%E9%AC%BC%EF%BC%9E%E3%80%8B",
    "e_evoegg":
        "https://dmwiki.net/%E3%80%8A%E3%82%A8%E3%83%9C%E3%83%AA%E3%83%A5%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3%E3%83%BB%E3%82%A8%E3%83%83%E3%82%B0%E3%80%8B",
    "e_timechanger":
        "https://dmwiki.net/%E3%80%8A%E6%99%82%E7%A9%BA%E5%B7%A5%E5%85%B5%E3%82%BF%E3%82%A4%E3%83%A0%E3%83%81%E3%82%A7%E3%83%B3%E3%82%B8%E3%83%A3%E3%83%BC%E3%80%8B",
    "e_tranky":
        "https://dmwiki.net/%E3%80%8A%E5%A5%87%E7%9F%B3%20%E3%83%88%E3%83%A9%E3%83%B3%E3%82%AD%E3%83%BC%EF%BC%8F%E3%82%A2%E3%82%A4%E3%83%BB%E3%82%AA%E3%83%96%E3%83%BB%E3%82%B6%E3%83%BB%E3%82%BF%E3%82%A4%E3%82%AC%E3%83%BC%E3%80%8B",
    "e_takasugi":
        "https://dmwiki.net/%E3%80%8ATAKASUGI-%E6%AD%BB%E5%90%88%E4%B9%B1%E9%97%983000%E3%80%8B",
    "e_astralheart":
        "https://dmwiki.net/%E3%80%8A%E3%82%A2%E3%82%B9%E3%83%88%E3%83%A9%E3%83%AB%E3%83%BB%E3%83%8F%E3%83%BC%E3%83%88%E3%80%8B",
    "e_astralkaigen":
        "https://dmwiki.net/%E3%80%8A%E3%82%A2%E3%82%B9%E3%83%88%E3%83%A9%E3%83%AB%E3%81%AE%E6%B5%B7%E5%B9%BB%E3%80%8B",
    "e_cabbage":
        "https://dmwiki.net/%E3%80%8A%E3%82%AD%E3%83%A3%E3%83%99%E3%83%83%E3%82%B8%E3%83%BB%E3%82%BB%E3%83%83%E3%82%B7%E3%83%A7%E3%83%B3%E3%82%BA%EF%BC%8F%E3%82%BD%E3%82%A4%E3%83%AB%E3%83%94%E3%83%B3%E3%83%97%E3%83%BB%E3%82%AD%E3%83%A3%E3%83%99%E3%83%83%E3%82%B8%E3%80%8B",
    "e_golgienext":
        "https://dmwiki.net/%E3%80%8A%E5%89%B5%E4%B8%96%E7%AB%9C%20%E3%82%B4%E3%83%AB%E3%82%AE%E3%83%BC%E3%83%8D%E3%82%AF%E3%82%B9%E3%83%88%E3%80%8B",
    "e_ellnadonna":
        "https://dmwiki.net/%E3%80%8A%E6%98%9F%E5%A7%AB%E6%A2%B0%20%E3%82%A8%E3%83%AB%E3%83%8A%E3%83%89%E3%83%B3%E3%83%8A%E3%80%8B",
    "e_cyclopedia":
        "https://dmwiki.net/%E3%80%8A%E9%BE%8D%E7%B4%A0%E8%A8%98%E5%8F%B7wD%20%E3%82%B5%E3%82%A4%E3%82%AF%E3%83%AB%E3%83%9A%E3%83%87%E3%82%A3%E3%82%A2%E3%80%8B",
    "e_alicetotsu":
        "https://dmwiki.net/%E3%80%8A%E3%82%A2%E3%83%AA%E3%82%B9%E3%81%AE%E7%AA%81%E6%92%83%E3%82%A4%E3%83%B3%E3%82%BF%E3%83%93%E3%83%A5%E3%83%BC%E3%80%8B",
    "e_bolmebius":
        "https://dmwiki.net/%E3%80%8A%E9%80%86%E8%BB%A2%E3%81%AE%E7%81%AB%E7%84%94%20%E3%83%9C%E3%83%AB%E3%82%B7%E3%83%A3%E3%83%83%E3%82%AF%E3%83%BB%E3%83%A1%E3%83%93%E3%82%A6%E3%82%B9%E3%80%8B",
    "e_gg001":
        "https://dmwiki.net/%E3%80%8A%E3%80%8CGG%E3%80%8D-001%E3%80%8B",
    "e_alicerupia":
        "https://dmwiki.net/%E3%80%8A%E3%82%A2%E3%83%AA%E3%82%B9%E3%83%BB%E3%83%AB%E3%83%94%E3%82%A2%E3%80%8B",
    "e_takeuma":
        "https://dmwiki.net/%E3%80%8A%E7%AB%B9%E9%A6%AC%E3%81%AE%E8%B6%85%E4%BA%BA%EF%BC%8F%E3%83%86%E3%82%A4%E3%82%AF%E3%83%90%E3%83%83%E3%82%AF%E3%83%BB%E3%83%81%E3%83%A3%E3%83%BC%E3%82%B8%E3%83%A3%E3%83%BC%E3%80%8B",
    "e_marchrupia":
        "https://dmwiki.net/%E3%80%8A%E5%87%B0%E7%BF%94%E7%AB%9C%E6%A9%9F%E3%83%9E%E3%83%BC%E3%83%81%E3%83%BB%E3%83%AB%E3%83%94%E3%82%A2%E3%80%8B",
    "e_escalden":
        "https://dmwiki.net/%E3%80%8A%E9%BE%8D%E7%BD%A0%20%E3%82%A8%E3%82%B9%E3%82%AB%E3%83%AB%E3%83%87%E3%83%B3%EF%BC%8F%E3%83%9E%E3%82%AF%E3%82%B9%E3%82%AB%E3%83%AB%E3%82%B4%E3%83%BB%E3%83%88%E3%83%A9%E3%83%83%E3%83%97%E3%80%8B",
    "e_grasper":
        "https://dmwiki.net/%E3%80%8A%E3%82%B0%E3%83%AC%E3%83%BC%E3%83%88%E3%83%BB%E3%82%B0%E3%83%A9%E3%82%B9%E3%83%91%E3%83%BC%E3%80%8B",
}


# ================================================================ 共通の小道具
def _worst(s, i):
    """自分の手札でいちばん要らないカード"""
    p = s.P[i]
    return min(p.hand, key=E.PRI.get) if p.hand else None


def _top(s, i, n):
    """山札の上から n 枚を取り出す（山札を切らさないよう1枚は残す）"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    return [p.deck.pop() for _ in range(n)] if n > 0 else []


def _bottom(s, i, cards):
    for k in cards:
        s.P[i].deck.insert(0, k)


def _owner(s, u):
    """そのカードを持っているプレイヤー（持ち主が渡されない差し込み口で使う）"""
    for j in (0, 1):
        if u in s.P[j].board:
            return j
    return 0


def _ddd_ok(s, i, key, cost, civ):
    """D・D・D：手札のそのカードを、その色のマナ cost 枚で出せるか"""
    p = s.P[i]
    if key not in p.hand or len(p.mana) - p.mused < cost:
        return False
    if not (set(civ) & E.civs(p)):
        return False
    return s.fate(i, key, "hand", True) == "ok"


def _ddd_src(s, i, key, civ):
    """D・D・D で出す時に進化元にするカード（いま攻撃しているクリーチャーは選ばない）"""
    best, bv = None, None
    for z in s.P[i].board:
        if z.c.kind != "C" or z is s.atk or not (set(civ) & set(z.c.civ)):
            continue
        v = (z.tap, E.PRI[z.k] + len(z.under))
        if bv is None or v < bv:
            best, bv = z, v
    return best


def _grave_cast(s, i, k, twin=False):
    """自分の墓地から呪文を唱える（唱えた後は墓地ではなく山札の下に置く）"""
    p = s.P[i]
    if k not in p.grave:
        return False
    c = BY_KEY[k]
    if not s.spell_ok(i, c.twin[0] if twin else c.cost):
        return False
    p.grave.remove(k)
    s.ev(f"　墓地から {c.name} を唱える")
    p.x["gcast"] = p.x.get("gcast", 0) + 1
    s.cast(i, k, twin)
    p.x["gcast"] = max(0, p.x.get("gcast", 1) - 1)
    if k in p.grave:
        p.grave.remove(k)
        p.deck.insert(0, k)
    return True


# ================================================================ 真気楼と誠偽感の決断
def _trig_from_grave(s, i):
    """墓地のS・トリガーを持つカード1枚をコストを支払わずに実行する"""
    p = s.P[i]
    best, bv, tw = None, -1, False
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        side = False
        if c.trig:
            if c.kind == "C":
                if (c.evo and not c.neo) or s.fate(i, k, "grave", True) != "ok":
                    continue
            elif c.kind == "S":
                if not s.spell_ok(i, c.cost):
                    continue
            elif c.kind == "T":
                if p.ban == c.cost:
                    continue
            elif s.has(1 - i, "fujin"):
                continue
        elif c.twin is not None and c.twin[2]:
            if not s.spell_ok(i, c.twin[0]):
                continue
            side = True
        else:
            continue
        if E.PRI[k] > bv:
            best, bv, tw = k, E.PRI[k], side
    if best is None:
        return False
    c = BY_KEY[best]
    if tw:
        return _grave_cast(s, i, best, True)
    if c.kind == "S":
        return _grave_cast(s, i, best)
    p.grave.remove(best)
    s.ev(f"　墓地の {c.name} をコストを支払わずに実行")
    if c.kind == "C":
        s.enter(i, best, "grave", True)
    elif c.kind == "T":
        s.place_tama(i, best)
    else:
        s.place_castle(i, best)
    return True


def _shinkiro_one(s, i):
    """3つの選択肢から1つ（相手の重い札をシールドに→墓地のS・トリガー→引いて捨てる）"""
    t = s.target(i)
    if t is not None and E.PRI[t.k] >= 5:
        s.ev(f"　{t.c.name} をシールドにする")
        s.leave(1 - i, t, "shield", by_opp=True)
        return
    if _trig_from_grave(s, i):
        return
    if t is not None:
        s.ev(f"　{t.c.name} をシールドにする")
        s.leave(1 - i, t, "shield", by_opp=True)
        return
    s.draw(i, 2)
    k = _worst(s, i)
    if k is not None:
        s.discard(i, k)


def sp_shinkiro(s, i):
    for _ in range(2):
        if s.over:
            return
        _shinkiro_one(s, i)


def te_shinkiro(s, di):
    """相手のターンの終わりに、そのターンにクリーチャーが合計3体以上出ていれば、手札からただで唱える

    tendp は「ターンの終わり」に両プレイヤーについて1度ずつ呼ばれる（バトルゾーンが空でも呼ばれる）。
    唱えるのは「相手のターンの終わり」なので、いまのターンのプレイヤーの側では何もしない。"""
    if di == s.tp:
        return
    p = s.P[di]
    if "e_shinkiro" not in p.hand or s.P[0].ent + s.P[1].ent < 3 or not s.spell_ok(di, 5):
        return
    p.hand.remove("e_shinkiro")
    s.ev("　真気楼と誠偽感の決断をコストを支払わずに唱える")
    s.cast(di, "e_shinkiro")


add("e_shinkiro", "真気楼と誠偽感の決断", 5, "LWD", kind="S", pri=6, roles="draw rem shd",
    spell=sp_shinkiro, tendp=te_shinkiro,
    text="相手のターンの終わりに、そのターン、クリーチャーが合計3体以上出ていれば、"
         "手札からコストを支払わずに唱えてもよい。"
         "唱えた時、次から2回選ぶ（同じものを選んでもよい）：①2枚引いて手札を1枚捨てる　"
         "②自分の墓地にあるS・トリガーを持つカード1枚をコストを支払わずに実行する（呪文なら唱えた後に山札の下へ）　"
         "③クリーチャー1体を選び、持ち主のシールドにする",
    source=SRC["e_shinkiro"])


# ================================================================ 頂上連結 ロッド・ゾージア5th
def cx_rodzojia(s, i, av):
    n = sum(1 for k in s.P[i].mana if "L" in E.MCIV[k] or "F" in E.MCIV[k])
    return 4 if n >= 5 else 7


def e_rodzojia(s, i, u):
    exlife_enter(s, i, u)
    w = s.power(i, u)
    t = s.target(i, lambda z: s.power(1 - i, z) < w)
    if t is not None:
        destroy(s, i, t)
    u.x["lim1"] = s.turn + 1


def fx_rodzojia(s, owner, u, i, k, src, summon, res):
    """次の相手のターン中、相手はクリーチャーを1体までしか出せない"""
    if i == owner or u.x.get("lim1") != s.turn:
        return res
    return "no" if s.P[i].ent >= 1 else res


add("e_rodzojia", "頂上連結 ロッド・ゾージア5th", 7, "LF", power=11000, brk=2, sa=True, pri=11,
    races=("dispector", "angelcommanddragon", "command", "dragon", "soniccommand"), roles="rem atk fin dis",
    enter=e_rodzojia, costx=cx_rodzojia, fatex=fx_rodzojia, leaverep=exlife_rep,
    text="W・ブレイカー、スピードアタッカー。自分のマナゾーンに光または火のカードが合計5枚以上あれば、召喚コストが3少なくなる。"
         "EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを墓地に置いて残る）。"
         "出た時、このクリーチャーよりパワーの小さい相手のクリーチャー1体を破壊し、"
         "次の相手のターン中、相手はクリーチャーを1体しか出せない",
    source=SRC["e_rodzojia"])


# ================================================================ 轟く邪道 レッドゾーン
def _kill_weakest(s, i):
    """相手の、パワーがいちばん小さいクリーチャーをすべて破壊する"""
    zs = opp_all(s, i)
    if not zs:
        return
    m = min(s.power(1 - i, z) for z in zs)
    for z in zs:
        if z in s.P[1 - i].board and s.power(1 - i, z) == m:
            destroy(s, i, z)


def e_jadoredzone(s, i, u):
    u.tap = False
    _kill_weakest(s, i)


def a_jadoredzone(s, i, u):
    _kill_weakest(s, i)


def ign_jadoredzone(s, i, u):
    """自分のクリーチャーは「攻撃できない」を無視して攻撃できる"""
    return u.c.kind == "C" and s.has(i, "e_jadoredzone")


def w_jadoredzone(s, i, u):
    """D・D・D[火(4)]：自分のクリーチャーの攻撃時、手札から4マナで出す"""
    if not _ddd_ok(s, i, "e_jadoredzone", 4, "F"):
        return
    p = s.P[i]
    on = _ddd_src(s, i, "e_jadoredzone", "DFN")
    p.hand.remove("e_jadoredzone")
    p.mused += 4
    s.ev("　D・D・D[火(4)]：轟く邪道 レッドゾーン")
    s.enter(i, "e_jadoredzone", "hand", True, on=on)


add("e_jadoredzone", "轟く邪道 レッドゾーン", 6, "F", power=12000, brk=3, evo="DFN", neo=True, gneo=True, pri=11,
    races=("soniccommand", "command", "invader"), roles="rem atk fin",
    enter=e_jadoredzone, attack=a_jadoredzone, noatkign=ign_jadoredzone,
    atkwatch=w_jadoredzone, fatex=fx_dream,
    # ドリーム・クリーチャーは「バトルゾーンに1体まで」で、デッキに入れる枚数の制限ではない
    # （全国大会2025 関東Aブロック 入賞リストに2枚積みが実在した）。場の制限は fatex=fx_dream。
    text="ドリーム・クリーチャー（バトルゾーンに1体まで）。T・ブレイカー。"
         "G-NEO進化（自分の闇・火・自然のクリーチャー1体の上に置いてもよいし、そのまま召喚してもよい。"
         "進化元がある間は離れるかわりに下のカードが離れる）。"
         "D・D・D[火(4)]：自分のクリーチャーが攻撃する時、火4マナを支払って手札から出してもよい。"
         "出た時、このクリーチャーをアンタップする。出た時と攻撃する時、相手のパワーがいちばん小さいクリーチャーをすべて破壊する。"
         "自分のクリーチャーは、相手のカードによる「攻撃できない」を無視して攻撃できる",
    note="エンジンの noatkign は、カードに書かれた「攻撃できない」（c.noatk）と"
         "「このターン攻撃できない」（u.lock）をまとめて無視するところまでで、"
         "相手のカードが条件つきでかけ続ける型（cantatk／atklock。"
         "「次の自分のターンのはじめまで攻撃できない」などの類）には効かない"
         "（無視する対象を選べる差し込み口 NOATKIGN2 がエンジンにない）",
    status="partial", source=SRC["e_jadoredzone"])


# ================================================================ 愛銀河マーズ・シンギュラリティ
def _bird(c):
    return "firebird" in c.races or "phoenix" in c.races


def cx_marssing(s, i, av):
    p = s.P[i]
    n = sum(1 for k in p.mana if _bird(BY_KEY[k])) + sum(1 for z in p.board if _bird(z.c))
    return 3 if n >= 5 else 5


def acts_marssing(s, i, av, cv):
    """デッキ進化GV：山札の上3枚を下に置いて出す"""
    p = s.P[i]
    if "e_marssing" not in p.hand or len(p.deck) < 4:
        return []
    n = cx_marssing(s, i, av)
    if n <= av and "F" in cv and s.fate(i, "e_marssing", "hand", True) == "ok":
        return [("x:mars", n)]
    return []


def ap_marssing(s, a):
    i = s.tp
    p = s.P[i]
    if "e_marssing" not in p.hand or len(p.deck) < 4:
        return
    p.mused += a[1]
    p.hand.remove("e_marssing")
    under = [p.deck.pop() for _ in range(3)]
    s.ev(f"デッキ進化GV：愛銀河マーズ・シンギュラリティ（{a[1]}マナ、山札の上3枚の上に）")
    u = s.enter(i, "e_marssing", "hand", True)
    if u is not None:
        u.under.extend(under)
    else:
        for k in reversed(under):
            p.deck.append(k)


def a_marssing(s, i, u):
    """メテオバーン：下のカードを相手に見ずに選ばせて墓地に置く。火のクリーチャーなら墓地から出す"""
    if not u.under:
        return
    p = s.P[i]
    k = u.under[s.rng.randrange(len(u.under))]
    u.under.remove(k)
    c = BY_KEY[k]
    s.ev(f"　メテオバーン：{c.name} を墓地に置く")
    s.grave_put(i, k)
    if c.kind != "C" or "F" not in c.civ or k not in p.grave or (c.evo and not c.neo):
        return
    if s.fate(i, k, "grave", False) == "ok":
        p.grave.remove(k)
        s.ev(f"　墓地から {c.name} を出す")
        s.enter(i, k, "grave", False)


add("e_marssing", "愛銀河マーズ・シンギュラリティ", 5, "F", power=13000, brk=3, evo="deck", pri=11,
    races=("firebird", "phoenix"), roles="atk fin",
    costx=cx_marssing, attack=a_marssing, freeacts=acts_marssing, actapply={"x:mars": ap_marssing},
    saok=lambda s, i, u: s.has(i, "e_marssing"),
    playrule=lambda deck, k: None,
    text="デッキ進化GV（自分の山札の上から3枚を裏向きのまま下に置いて出す）。T・ブレイカー。"
         "自分のマナゾーンとバトルゾーンに、ファイアー・バードまたはフェニックスを持つものが合計5つ以上あれば、"
         "火3マナで召喚してもよい。自分のクリーチャーすべてにスピードアタッカーを与える。"
         "攻撃する時、メテオバーン：下のカードを1枚、相手に見ないで選ばせて墓地に置いてもよい。"
         "それが火のクリーチャーなら、そのまま墓地から出す",
    source=SRC["e_marssing"])


# ================================================================ 斬隠将撃龍ニバイケン
def _nibai_battle(s, i, u):
    if u not in s.P[i].board:
        return
    t = s.target(i)
    if t is not None:
        s.battle(i, u, 1 - i, t)


def _nibai_draw(s, i, u):
    """タップした時：2枚引いて1枚捨てる（山札が少ない時はしない）"""
    p = s.P[i]
    if len(p.deck) <= 2:
        return
    s.draw(i, 2)
    k = _worst(s, i)
    if k is not None:
        s.discard(i, k)


def e_nibaiken(s, i, u):
    _nibai_battle(s, i, u)


def tw_nibaiken(s, i, u):
    """このクリーチャーがタップした時（攻撃・ブロック・効果のタップのすべて）、2枚引いて1枚捨てる"""
    if u.k != "e_nibaiken":
        return
    _nibai_draw(s, i, u)


def dx_nibaiken(s, i, k):
    """マッドネス：相手のターンに手札から捨てられる時、墓地に置くかわりに出す"""
    if s.tp == i or k not in s.P[i].hand:
        return False
    if s.fate(i, k, "hand", False) != "ok":
        return False
    s.P[i].hand.remove(k)
    s.ev("　マッドネス：斬隠将撃龍ニバイケンが出る")
    s.enter(i, k, "hand", False)
    return True


add("e_nibaiken", "斬隠将撃龍ニバイケン", 6, "WF", power=6000, brk=2, blocker=True, sa=True, pri=8,
    races=("poseidia", "armoreddragon", "dragon", "shinobi"), roles="blk atk draw rem",
    enter=e_nibaiken, discardx=dx_nibaiken, tapwatch=tw_nibaiken,
    text="W・ブレイカー、ブロッカー、スピードアタッカー。"
         "相手のターン中にこのカードが自分の手札から捨てられる時、墓地に置くかわりにバトルゾーンに出してもよい（マッドネス）。"
         "出た時、相手のクリーチャー1体を選んでもよい。選んだクリーチャーとこのクリーチャーをバトルさせる。"
         "このクリーチャーがタップした時、2枚引いてもよい。そうしたら手札を1枚捨てる",
    source=SRC["e_nibaiken"])


# ================================================================ 轟䡛合体 ゴルギーオージャー
def cx_golgieoja(s, i, av):
    z = s.evo_src(i, "e_golgieoja")
    n = 1 + len(z.under) if z is not None else 0
    return max(3, 9 - 2 * n)


def e_golgieoja(s, i, u):
    p = s.P[i]
    n = len(u.under) + 1
    s.ramp(i, n)
    for _ in range(3):
        cands = [k for k in p.mana if E.PRI[k] >= 5]
        if not cands:
            break
        k = max(cands, key=E.PRI.get)
        s.take_mana(i, k)
        p.hand.append(k)
        s.ev(f"　マナから {BY_KEY[k].name} を手札へ")


def a_golgieoja(s, i, u):
    if len(u.under) + 1 >= 10:
        s.win(i, "轟䡛合体 ゴルギーオージャー")


add("e_golgieoja", "轟䡛合体 ゴルギーオージャー", 9, "LWN", power=14500, brk=3, blocker=True, mach=True,
    evo="LWN", neo=True, gneo=True, pri=12, races=("mecadeldinero", "supercardragon", "dragon"),
    roles="acc blk fin", enter=e_golgieoja, attack=a_golgieoja, costx=cx_golgieoja,
    text="G-NEO進化（自分の光・水・自然のクリーチャー1体の上に置いてもよいし、そのまま召喚してもよい）。"
         "T・ブレイカー、ブロッカー、マッハファイター。召喚コストは、進化元になるカード1枚につき2少なくなる（3より下がらない）。"
         "出た時、このクリーチャーに含まれるカードの枚数まで山札の上からマナゾーンに置き、"
         "その後、自分のマナゾーンから3枚までを手札に戻す。"
         "攻撃する時、このクリーチャーに含まれるカードが10枚以上あれば、自分はゲームに勝つ",
    source=SRC["e_golgieoja"])


# ================================================================ メンデルスゾーン
def sp_mendels(s, i):
    for k in _top(s, i, 2):
        if "dragon" in BY_KEY[k].races:
            s.add_mana(i, k, True, src="deck")
            s.ev(f"　{BY_KEY[k].name} をタップしてマナゾーンへ")
        else:
            s.grave_put(i, k)


add("e_mendels", "メンデルスゾーン", 2, "FN", kind="S", pri=4, roles="acc", spell=sp_mendels,
    text="自分の山札の上から2枚を表向きにする。その中のドラゴンをすべてタップしてマナゾーンに置き、残りを墓地に置く",
    source=SRC["e_mendels"])


# ================================================================ 配膳犬のトレス
def e_tores(s, i, u):
    s.dig(i, 3, lambda k: "dreammate" in BY_KEY[k].races)


def acts_tores(s, i, av, cv):
    """ハイパー化：自分の他のクリーチャー1体をタップしてハイパーモードを解放する"""
    for z in s.P[i].board:
        if z.k == "e_tores" and not z.hyper:
            if any(x is not z and x.c.kind == "C" and not x.tap for x in s.P[i].board):
                return [("x:tores", z.uid)]
    return []


def ap_tores(s, a):
    i = s.tp
    p = s.P[i]
    z = next((x for x in p.board if x.uid == a[1] and x.k == "e_tores" and not x.hyper), None)
    if z is None:
        return
    oth = [x for x in p.board if x is not z and x.c.kind == "C" and not x.tap]
    if not oth:
        return
    s.tap_cre(i, min(oth, key=s.val))
    z.hyper = True
    s.ev("　ハイパー化：配膳犬のトレス")


add("e_tores", "配膳犬のトレス", 2, "N", power=3000, noatkp=True, pri=4, races=("dreammate", "hyperbeast"),
    roles="draw blk", enter=e_tores, freeacts=acts_tores, actapply={"x:tores": ap_tores},
    guard=guardman("e_tores", cond=lambda s, di, z: z.hyper),
    gsok=lambda s, di, k: "dreammate" in BY_KEY[k].races and any(z.k == "e_tores" for z in s.P[di].board),
    text="このクリーチャーは相手プレイヤーを攻撃できない。"
         "出た時、山札の上から3枚を表向きにし、その中のドリームメイト1枚を手札に加え、残りを好きな順序で山札の下に置く。"
         "ハイパー化：自分のメインステップ中、自分の他のクリーチャー1体をタップして、"
         "次の自分のターンのはじめまでハイパーモードになる。ハイパーモード中はパワー6000になり、ガードマンを持つ",
    source=SRC["e_tores"])
E.HYPER_POW["e_tores"] = 3000


# ================================================================ 支配の精霊ペルフェクト／ギャラクシー・チャージャー
def _perf_n(s, i):
    x = s.P[i].x
    return x.get("perfn", 0) if x.get("perft") == s.turn else 0


def w_perfect(s, i, u):
    """そのターンに召喚したクリーチャーの数を数える"""
    if u.c.kind != "C" or not u.x.get("summoned"):
        return
    x = s.P[i].x
    if x.get("perft") != s.turn:
        x["perft"], x["perfn"] = s.turn, 0
    x["perfn"] = x.get("perfn", 0) + 1


def fx_perfect(s, owner, u, i, k, src, summon, res):
    if i == owner or not summon:
        return res
    return "no" if _perf_n(s, i) + s.P[i].spl >= 3 else res


def lk_perfect(s, i, cost):
    return s.has(1 - i, "e_perfect") and _perf_n(s, i) + s.P[i].spl >= 3


def rep_perfect(s, i, u, dest, destroy_):
    """パワーが0より大きければ、離れるかわりにバトルゾーンにとどまる"""
    return u.k == "e_perfect" and s.power(i, u) > 0


def sp_perfect(s, i):
    """ギャラクシー・チャージャー（呪文側）"""
    p = s.P[i]
    rest = []
    for k in _top(s, i, 3):
        if "angelcommand" in BY_KEY[k].races:
            p.hand.append(k)
            s.ev(f"　{BY_KEY[k].name} を手札へ")
        else:
            rest.append(k)
    _bottom(s, i, rest)
    s.add_mana(i, "e_perfect")
    s.ev("　チャージャー：ギャラクシー・チャージャーをマナゾーンへ")


add("e_perfect", "支配の精霊ペルフェクト / ギャラクシー・チャージャー", 7, "L", power=9000, brk=2, blocker=True,
    twin=(3, "L", False), pri=10, races=("angelcommand", "command"), roles="blk dis acc draw",
    spell=sp_perfect, nograve=True, enterwatch=w_perfect, fatex=fx_perfect, spelllock=lk_perfect,
    leaverep=rep_perfect,
    text="W・ブレイカー、ブロッカー。相手は各ターン、クリーチャーの召喚と呪文を唱えるのを合計3回までしかできない。"
         "このクリーチャーが離れる時、そのパワーが0より大きければ、かわりにバトルゾーンにとどまる。"
         "呪文側《ギャラクシー・チャージャー》（光3）：山札の上から3枚を表向きにし、"
         "その中のエンジェル・コマンドをすべて手札に加え、残りを好きな順序で山札の下に置く。"
         "チャージャー（唱えた後、墓地ではなくマナゾーンに置く）",
    source=SRC["e_perfect"])


# ================================================================ AQ NETWORK
def _sybil3(s, i):
    return sum(1 for z in s.P[i].board if z.c.kind in "CT" and "W" in z.c.civ) >= 3


def e_aqnetwork(s, i, u):
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind not in ("S", "T") or c.cost > 5 or p.ban == c.cost:
            continue
        if c.kind == "S" and not s.spell_ok(i, c.cost):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　AQ NETWORK：手札の {BY_KEY[best].name} をコストを支払わずに実行")
        free_play(s, i, best)


def ld_aqnetwork(s, i, u, dest, destroy_):
    if u.k == "e_aqnetwork" and destroy_ and _sybil3(s, i):
        return "hand"
    return None


add("e_aqnetwork", "AQ NETWORK", 5, "W", power=5000, trig=True, pri=6, races=("magic", "liquid"),
    roles="trg blk draw", enter=e_aqnetwork, leavedest=ld_aqnetwork,
    blockok=lambda s, u: u.k == "e_aqnetwork" and _sybil3(s, _owner(s, u)),
    text="S・トリガー。出た時、コスト5以下のタマシードまたは呪文を1つ、自分の手札からコストを支払わずに実行してもよい。"
         "シビルカウント3：自分の水のクリーチャーまたはタマシードが合計3つ以上あれば、このクリーチャーはブロッカーを得て、"
         "破壊される時は墓地に置くかわりに手札に戻る",
    source=SRC["e_aqnetwork"])



# ================================================================ オンソク童子 ＜ターボ.鬼＞
def ex_onsoku(s, i, u):
    return "rexstars" in u.c.races or "F" in u.c.civ


def e_onsoku(s, i, u):
    k = _worst(s, i)
    if k is not None:
        s.discard(i, k)
    s.draw(i)
    if u.under and BY_KEY[u.under[0]].kind == "T":
        s.draw(i)


rep_onsoku = star_evo_rep("e_onsoku", "オンソク童子")


def pr_onsoku(deck, k):
    n = 0
    for kk, v in deck.items():
        if kk == k:
            continue
        c = BY_KEY[kk]
        if (c.kind == "C" or kk in E.SHINKA) and ("rexstars" in c.races or "F" in c.civ):
            n += v
    return None if n >= 4 else "スター進化の元になるレクスターズか火のクリーチャーが4体いない"


add("e_onsoku", "オンソク童子 ＜ターボ.鬼＞", 2, "F", power=4000, evo="F", pri=5,
    races=("soniccommand", "command", "onirexstars", "rexstars"), roles="draw atk",
    enter=e_onsoku, evox=ex_onsoku, leaverep=rep_onsoku, playrule=pr_onsoku,
    text="スター進化（自分のレクスターズまたは火のクリーチャー1体の上に置く。離れる時は一番上のカード1枚だけが離れ、"
         "下のカードはバトルゾーンに残る）。出た時、自分の手札を1枚捨て、カードを1枚引く。"
         "タマシードから進化していれば、さらにもう1枚引く",
    source=SRC["e_onsoku"])


# ================================================================ エボリューション・エッグ
def sp_evoegg(s, i):
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    best, bv = None, -99
    for k in sorted(set(p.deck)):
        c = BY_KEY[k]
        if c.kind != "C" or not c.evo:
            continue
        v = E.PRI[k] - 3 * p.hand.count(k)
        if v > bv:
            best, bv = k, v
    if best is not None:
        p.deck.remove(best)
        p.hand.append(best)
        s.ev(f"　山札から {BY_KEY[best].name} を手札へ")
    s.rng.shuffle(p.deck)


add("e_evoegg", "エボリューション・エッグ", 2, "N", kind="S", trig=True, pri=4, roles="draw trg", spell=sp_evoegg,
    text="S・トリガー。自分の山札を見て、進化クリーチャー1体を選び、表向きにして手札に加えてもよい。その後、山札をシャッフルする",
    source=SRC["e_evoegg"])


# ================================================================ 時空工兵タイムチェンジャー
def e_timechanger(s, i, u):
    p = s.P[i]
    tgt, tv = None, -1
    for z in p.board:
        if z.c.kind == "C" and z.c.evo and E.PRI[z.k] > tv:
            tgt, tv = z, E.PRI[z.k]
    if tgt is None:
        return
    got = []
    for _ in range(2):
        if len(p.deck) <= 1:
            break
        cands = [k for k in sorted(set(p.deck)) if BY_KEY[k].kind == "C"]
        if not cands:
            break
        k = min(cands, key=E.PRI.get)
        p.deck.remove(k)
        got.append(k)
    for k in got:
        tgt.under.append(k)
    if got:
        s.ev(f"　{tgt.c.name} の下に山札から{len(got)}枚置く")
    s.rng.shuffle(p.deck)


add("e_timechanger", "時空工兵タイムチェンジャー", 3, "W", power=2000, pri=3, races=("greatmechaoh",), roles="",
    enter=e_timechanger,
    text="出た時、自分の進化クリーチャー1体を選んでもよい。そうしたら自分の山札を見てクリーチャーを2体表向きにし、"
         "選んだ進化クリーチャーの下に置く。その後、山札をシャッフルする",
    source=SRC["e_timechanger"])


# ================================================================ 奇石 トランキー／アイ・オブ・ザ・タイガー
def _is_blocker(s, u):
    return u.c.kind == "C" and (u.c.blocker or any(f(s, u) for f in E.BLOCKOK))


def ign_tranky(s, i, u):
    """自分のブロッカーを持つクリーチャーの「攻撃できない」能力を無効にする（召喚酔いは無効にならない）"""
    return _is_blocker(s, u) and s.has(i, "e_tranky")


def te_tranky(s, i, u):
    """自分のターンの終わりに、自分のブロッカーをすべてアンタップする"""
    for z in s.P[i].board:
        if _is_blocker(s, z):
            z.tap = False


def sp_tranky(s, i):
    """アイ・オブ・ザ・タイガー（呪文側）"""
    s.draw(i)
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or not c.blocker or c.cost > 5 or (c.evo and not c.neo):
            continue
        if s.fate(i, k, "hand", False) != "ok":
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        p.hand.remove(best)
        s.ev(f"　手札から {BY_KEY[best].name} を出す")
        s.enter(i, best, "hand", False)


add("e_tranky", "奇石 トランキー / アイ・オブ・ザ・タイガー", 7, "L", power=6500, brk=2, twin=(4, "L", False),
    pri=8, races=("metallica",), roles="blk draw", tend=te_tranky, spell=sp_tranky, noatkign=ign_tranky,
    text="W・ブレイカー。自分のブロッカーを持つクリーチャーの「攻撃できない」能力を無効にする。"
         "自分のターンの終わりに、自分のブロッカーを持つクリーチャーをすべてアンタップする。"
         "呪文側《アイ・オブ・ザ・タイガー》（光4）：1枚引く。その後、コスト5以下のブロッカーを持つクリーチャー1体を"
         "自分の手札から出してもよい",
    source=SRC["e_tranky"])


# ================================================================ TAKASUGI-死合乱闘3000
def _takasugi_dig(s, i):
    s.dig(i, 4, lambda k: BY_KEY[k].kind == "C")


def e_takasugi(s, i, u):
    if u.under:
        _takasugi_dig(s, i)


def w_takasugi_src(s, i, u):
    """進化元になった時も同じ効果"""
    if u.under and u.under[0] == "e_takasugi":
        _takasugi_dig(s, i)


def w_takasugi_ddd(s, i, u):
    """D・D・D[自然(2)]"""
    if not _ddd_ok(s, i, "e_takasugi", 2, "N"):
        return
    p = s.P[i]
    on = _ddd_src(s, i, "e_takasugi", "LFN")
    p.hand.remove("e_takasugi")
    p.mused += 2
    s.ev("　D・D・D[自然(2)]：TAKASUGI-死合乱闘3000")
    s.enter(i, "e_takasugi", "hand", True, on=on)


add("e_takasugi", "TAKASUGI-死合乱闘3000", 3, "N", power=4000, evo="LFN", neo=True, pri=5,
    races=("giant", "technosamurai"), roles="draw atk",
    enter=e_takasugi, enterwatch=w_takasugi_src, atkwatch=w_takasugi_ddd,
    text="NEO進化（自分の光・火・自然のクリーチャー1体の上に置いてもよいし、そのまま召喚してもよい）。"
         "D・D・D[自然(2)]：自分のクリーチャーが攻撃する時、自然2マナを支払って手札から出してもよい。"
         "進化して出た時、または他の進化クリーチャーの進化元になった時、自分の山札の上から4枚を見て、"
         "その中のクリーチャー1体を手札に加えてもよい。残りは好きな順序で山札の下に置く",
    source=SRC["e_takasugi"])


# ================================================================ アストラル・ハート
def e_astralheart(s, i, u):
    p = s.P[i]
    s.draw(i, 3)
    if u.under and race_like(BY_KEY[u.under[0]], "cyber"):
        return
    n = 0
    for _ in range(3):
        k = _worst(s, i)
        if k is None:
            break
        p.hand.remove(k)
        p.deck.append(k)
        n += 1
    if n:
        s.ev(f"　手札{n}枚を好きな順序で山札の上に置く")


add("e_astralheart", "アストラル・ハート", 2, "W", power=3000, evo="W", neo=True, pri=4, races=("cyberv",),
    roles="draw", enter=e_astralheart,
    text="NEO進化（自分の水のクリーチャー1体の上に置いてもよいし、そのまま召喚してもよい）。"
         "出た時、カードを3枚引く。その後、サイバー・カードから進化していなければ、"
         "自分の手札を3枚、好きな順序で山札の上に置く",
    source=SRC["e_astralheart"])


# ================================================================ アストラルの海幻
def e_astralkaigen(s, i, u):
    s.draw(i, 2)
    k = _worst(s, i)
    if k is not None:
        s.discard(i, k)


add("e_astralkaigen", "アストラルの海幻", 2, "W", kind="T", pri=4, races=("cyberv", "rexstars"), roles="draw",
    enter=e_astralkaigen,
    text="シンカライズ（このタマシードをクリーチャーであるかのように扱い、この上に進化クリーチャーを置いてもよい）。"
         "出た時、カードを2枚引き、自分の手札を1枚捨てる",
    source=SRC["e_astralkaigen"])
E.SHINKA.add("e_astralkaigen")


# ================================================================ キャベッジ・セッションズ／ソイルピンプ・キャベッジ
def w_cabbage(s, i, u):
    """自分のクリーチャーが出た時、1つ軽い自然のパワー12000以上をマナゾーンから出す"""
    if u.c.kind != "C" or not s.has(i, "e_cabbage") or s.manaexec(i):
        return
    need = u.c.cost - 1
    if need < 0:
        return
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if c.kind != "C" or c.cost != need or "N" not in c.civ or c.power < 12000:
            continue
        if c.evo and not c.neo:
            continue
        if s.fate(i, k, "mana", False) != "ok":
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is None:
        return
    s.take_mana(i, best)
    s.ev(f"　キャベッジ・セッションズ：マナゾーンから {BY_KEY[best].name}")
    s.enter(i, best, "mana", False)


def w_cabbage_used(s, i, u):
    """ソイルピンプ・キャベッジの軽減は、次に召喚した1体だけに働く"""
    p = s.P[i]
    if p.x.get("cab") == s.turn and u.x.get("summoned") and "N" in u.c.civ and u.c.power >= 12000:
        p.x["cab"] = -1


def w_cabbage_all(s, i, u):
    w_cabbage_used(s, i, u)
    w_cabbage(s, i, u)


def ca_cabbage(s, i, k, cur):
    if s.P[i].x.get("cab") != s.turn:
        return cur
    c = BY_KEY[k]
    if c.kind == "C" and "N" in c.civ and c.power >= 12000:
        return max(1, cur - 8)
    return cur


def sp_cabbage(s, i):
    """ソイルピンプ・キャベッジ（呪文側）"""
    s.P[i].x["cab"] = s.turn
    s.ev("　このターン、次に召喚する自然のパワー12000以上のクリーチャーのコストが8少なくなる")


add("e_cabbage", "キャベッジ・セッションズ / ソイルピンプ・キャベッジ", 9, "N", power=12000, brk=3, evo="N", neo=True,
    twin=(5, "N", False), pri=12, races=("gransect",), roles="fin acc",
    enterwatch=w_cabbage_all, costaura=ca_cabbage, spell=sp_cabbage,
    text="NEO進化（自分の自然のクリーチャー1体の上に置いてもよいし、そのまま召喚してもよい）。T・ブレイカー。"
         "自分のクリーチャーが出た時、そのクリーチャーよりコストが1小さい、自然のパワー12000以上のクリーチャー1体を"
         "自分のマナゾーンから出してもよい。"
         "呪文側《ソイルピンプ・キャベッジ》（自然5）：このターン、次に召喚する自分の自然のパワー12000以上の"
         "クリーチャーのコストを8少なくする（1より下がらない）",
    source=SRC["e_cabbage"])


# ================================================================ 創世竜 ゴルギーネクスト
def e_golgienext(s, i, u):
    """D・D・D で出た時だけ働く"""
    p = s.P[i]
    if not p.x.pop("gnddd", False) or len(p.deck) <= 1:
        return
    s.rng.shuffle(p.deck)
    k = p.deck.pop()
    c = BY_KEY[k]
    s.ev(f"　山札の上から {c.name} を表向きにする")
    p.hand.append(k)
    if free_play(s, i, k):
        return
    if k in p.hand and E.PRI[k] < 5:
        p.hand.remove(k)
        s.add_mana(i, k)
        s.ev(f"　{c.name} をマナゾーンへ")


def rep_golgienext(s, i, u, dest, destroy_):
    """エスケープ：破壊される時、かわりに自分のシールド1つを手札に加える"""
    if u.k != "e_golgienext" or not destroy_:
        return False
    p = s.P[i]
    for j in range(len(p.sh) - 1, -1, -1):
        if not p.sh[j][1]:
            p.hand.append(p.sh.pop(j)[0])
            s.shield_left()
            s.ev("　エスケープ：シールド1つを手札に加えて創世竜 ゴルギーネクストは残る")
            return True
    return False


def w_golgienext_ddd(s, i, u):
    """D・D・D[光/水/自然(4)]"""
    if not _ddd_ok(s, i, "e_golgienext", 4, "LWN"):
        return
    p = s.P[i]
    p.hand.remove("e_golgienext")
    p.mused += 4
    p.x["gnddd"] = True
    s.ev("　D・D・D[光/水/自然(4)]：創世竜 ゴルギーネクスト")
    s.enter(i, "e_golgienext", "hand", True)
    p.x.pop("gnddd", None)


add("e_golgienext", "創世竜 ゴルギーネクスト", 3, "L", power=4000, pri=6, meta=("LIMIT2",),
    races=("mecadeldinero", "supercardragon", "dragon"), roles="dis acc draw",
    enter=e_golgienext, leaverep=rep_golgienext, atkwatch=w_golgienext_ddd,
    text="相手は各ターン、クリーチャーを2体までしか出せない。"
         "D・D・D[光/水/自然(4)]：自分のクリーチャーが攻撃する時、光・水・自然の4マナを支払って手札から出してもよい。"
         "D・D・Dで出た時、自分の山札をシャッフルして上から1枚を表向きにし、コストを支払わずに実行してもよい。"
         "実行しなければ手札に加えるかマナゾーンに置く。"
         "エスケープ：このクリーチャーが破壊される時、墓地に置くかわりに自分のシールド1つを手札に加えてもよい"
         "（そのシールドのS・トリガーは使えない）",
    source=SRC["e_golgienext"])


# ================================================================ 星姫械 エルナドンナ
def rep_ellnadonna(s, i, u, dest, destroy_):
    """各ターン1度、自分の他のクリーチャーが離れる時、かわりに自分のシールド1つを手札に加える"""
    if u.c.kind != "C":
        return False
    p = s.P[i]
    z = next((x for x in p.board if x.k == "e_ellnadonna" and x is not u and x.x.get("ell") != s.turn), None)
    if z is None:
        return False
    for j in range(len(p.sh) - 1, -1, -1):
        if not p.sh[j][1]:
            z.x["ell"] = s.turn
            p.hand.append(p.sh.pop(j)[0])
            s.shield_left()
            s.ev(f"　エルナドンナ：シールド1つを手札に加えて {u.c.name} は残る")
            return True
    return False


add("e_ellnadonna", "星姫械 エルナドンナ", 2, "L", power=2500, blocker=True, pri=4, races=("mecadelstella",),
    roles="blk", leaverep=rep_ellnadonna,
    text="ブロッカー。各ターンに一度、自分の他のクリーチャーが離れる時、かわりに自分のシールド1つを手札に加えてもよい"
         "（そのシールドのS・トリガーは使えない）。そうしたら、そのクリーチャーはバトルゾーンに残る",
    source=SRC["e_ellnadonna"])


# ================================================================ 龍素記号wD サイクルペディア
def e_cyclopedia(s, i, u):
    best, bv = None, -1
    for k in sorted(set(s.P[i].grave)):
        c = BY_KEY[k]
        if c.kind != "S" or c.cost > 4 or not s.spell_ok(i, c.cost):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        _grave_cast(s, i, best)


def w_cyclopedia(s, i, k):
    """各ターン1度、自分が呪文を唱えた時、その呪文を墓地からもう一度唱える"""
    if BY_KEY[k].kind != "S":
        return
    p = s.P[i]
    if p.x.get("gcast"):            # 墓地から唱えた呪文には働かない（手札から唱えた時だけ）
        return
    z = next((x for x in p.board if x.k == "e_cyclopedia" and x.x.get("cyc") != s.turn), None)
    if z is None or not s.spell_ok(i, BY_KEY[k].cost):
        return
    z.x["cyc"] = s.turn
    if k in p.grave:
        p.grave.remove(k)
    s.ev(f"　サイクルペディア：{BY_KEY[k].name} を墓地からもう一度唱える")
    p.x["gcast"] = p.x.get("gcast", 0) + 1
    s.cast(i, k)
    p.x["gcast"] = max(0, p.x.get("gcast", 1) - 1)
    if k in p.grave:
        p.grave.remove(k)
        p.deck.insert(0, k)


add("e_cyclopedia", "龍素記号wD サイクルペディア", 5, "WD", power=5000, blocker=True, jd=True, pri=7,
    races=("crystalcommanddragon", "command", "dragon", "darklord"), roles="blk draw",
    enter=e_cyclopedia, spellwatch=w_cyclopedia,
    text="ブロッカー。出た時、ジャストダイバー（次の自分のターンのはじめまで相手に選ばれず、攻撃もされない）。"
         "出た時、コスト4以下の呪文1枚を自分の墓地からコストを支払わずに唱えてもよい。"
         "各ターン1度、自分が手札から呪文を唱えた時、その呪文を自分の墓地からコストを支払わずに唱えてもよい。"
         "自分の墓地から呪文を唱えた後は、墓地ではなく山札の下に置く",
    source=SRC["e_cyclopedia"])


# ================================================================ アリスの突撃インタビュー
def _alice_kills(s, i, zs, budget):
    got, tot = 0, 0
    for z in zs:
        if got >= 2:
            break
        if tot + z.c.cost <= budget:
            tot += z.c.cost
            got += 1
    return got


def sp_alicetotsu(s, i):
    p = s.P[i]
    if not p.hand:
        return
    zs = sorted(opp_all(s, i), key=lambda z: -E.PRI[z.k])
    best, bv = None, None
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        v = (_alice_kills(s, i, zs, c.cost), 1 if "firebird" in c.races else 0, -E.PRI[k])
        if bv is None or v > bv:
            best, bv = k, v
    c = BY_KEY[best]
    s.ev(f"　手札の {c.name} を捨てる（コスト{c.cost}まで破壊できる）")
    s.discard(i, best)
    budget, n = c.cost, 0
    for z in zs:
        if n >= 2:
            break
        if z in s.P[1 - i].board and z.c.cost <= budget:
            budget -= z.c.cost
            n += 1
            destroy(s, i, z)
    if "firebird" in c.races:
        s.revive(i, lambda cc: cc.cost <= 5)


add("e_alicetotsu", "アリスの突撃インタビュー", 4, "LDF", kind="S", trig=True, pri=6, roles="rem trg dis",
    spell=sp_alicetotsu,
    playrule=lambda deck, k: None if deck.get(k, 0) <= 1 else "殿堂入りなのでデッキに1枚まで",
    text="S・トリガー。自分の手札を1枚捨てる。その後、コストの合計がその捨てたカードのコスト以下になるように、"
         "相手のクリーチャーを2体まで選んで破壊する。捨てたカードがファイアー・バードだったら、"
         "コスト5以下のクリーチャー1体を自分の墓地から出してもよい。殿堂入り（デッキに1枚まで）",
    source=SRC["e_alicetotsu"])


# ================================================================ 逆転の火焔 ボルシャック・メビウス
def e_bolmebius(s, i, u):
    if u not in s.P[i].board:
        return
    t = s.target(i)
    if t is not None:
        s.battle(i, u, 1 - i, t)


def a_bolmebius(s, i, u):
    """ハイパーモード中、攻撃する時に自分の他のクリーチャー1体をアンタップする"""
    if not u.hyper:
        return
    cands = [z for z in s.P[i].board if z is not u and z.c.kind == "C" and z.tap]
    if cands:
        z = max(cands, key=lambda x: s.power(i, x))
        z.tap = False
        s.ev(f"　{z.c.name} をアンタップする")


def cw_bolmebius(s, i, u, by):
    """ハイパーモード中、相手にこのクリーチャーが選ばれた時、相手のシールドを3つブレイクしてもよい

    注意（エンジン側の不具合。2026-10-08 に見つけた）：`Game.legal_main` が《タッ・キュー》の
    無駄撃ち判定（`Game.takkyu_ok`）で `s.target()` を呼ぶため、**打てる手を数えるだけでも
    CHOSENWATCH が誘発する**。そのため、相手が《タッ・キュー》を手札に持っていて、
    このクリーチャーが `power < 自分の最大パワー` の条件に合う時だけ、手を数えるたびに
    このブレイクが起きてしまう。直すには `takkyu_ok` が `s.target()` を使わずに
    候補を数える形にする必要がある（engine3.py は担当外）。"""
    if u.k != "e_bolmebius" or not u.hyper or s.over:
        return
    s.ev("　ボルシャック・メビウス：相手に選ばれたので相手のシールドを3つブレイク")
    s.break_sh(i, 3)


def fx_bolmebius(s, ai, au, di, du, a_dies, d_dies):
    """バトルに勝った時、相手のシールドを1つブレイクする"""
    if s.over:
        return a_dies, d_dies
    if au.k == "e_bolmebius" and d_dies and not a_dies:
        s.break_sh(ai, 1)
    elif du.k == "e_bolmebius" and a_dies and not d_dies:
        s.break_sh(di, 1)
    return a_dies, d_dies


add("e_bolmebius", "逆転の火焔 ボルシャック・メビウス", 5, "F", power=7000, brk=2, sa=True, zrush=True, pri=8,
    races=("armoreddragon", "dragon", "hyperbeast"), roles="atk rem fin",
    enter=e_bolmebius, attack=a_bolmebius, battlefx=fx_bolmebius, chosenwatch=cw_bolmebius,
    brkx=lambda s, i, u: 3 if u.hyper else None,
    text="W・ブレイカー、スピードアタッカー。出た時、相手のクリーチャー1体を選んでもよい。"
         "選んだクリーチャーとこのクリーチャーをバトルさせる。このクリーチャーがバトルに勝った時、相手のシールドを1つブレイクしてもよい。"
         "Zラッシュ：シールドが1つでも離れたら、次の自分のターンのはじめまでハイパーモードになる。"
         "ハイパーモード中はパワー12000・T・ブレイカーになり、攻撃する時に自分の他のクリーチャー1体をアンタップする。"
         "ハイパーモード中、相手がこのクリーチャーを選んだ時、相手のシールドを3つブレイクしてもよい",
    source=SRC["e_bolmebius"])
E.HYPER_POW["e_bolmebius"] = 5000


# ================================================================ 「GG」-001
def w_gg001_ddd(s, i, u):
    """D・D・D[光/火/自然(7)]"""
    if not _ddd_ok(s, i, "e_gg001", 7, "LFN"):
        return
    p = s.P[i]
    on = _ddd_src(s, i, "e_gg001", "LFN")
    p.hand.remove("e_gg001")
    p.mused += 7
    s.ev("　D・D・D[光/火/自然(7)]：「GG」-001")
    s.enter(i, "e_gg001", "hand", True, on=on)


def etl_gg001(s, i, u):
    """これが進化クリーチャーなら、相手のクリーチャーが出たことによる「出た時」を誘発させない

    i＝そのクリーチャーを出した側なので、止めるのは「GG」-001 の持ち主から見た相手の分だけ。
    NEO進化はそのまま召喚もできるので、下にカードがある（＝進化クリーチャーである）時だけ働く。"""
    if u.c.kind != "C":
        return False
    return any(z.k == "e_gg001" and z.under for z in s.P[1 - i].board)


add("e_gg001", "「GG」-001", 10, "LFN", power=18000, brk=4, evo="LFN", neo=True, pri=13,
    races=("gaialcommanddragon", "command", "dragon", "humanoidbomb", "technosamurai"), roles="fin atk dis",
    atkwatch=w_gg001_ddd, entertriglock=etl_gg001,
    text="NEO進化（自分の光・火・自然のクリーチャー1体の上に置いてもよいし、そのまま召喚してもよい）。Q・ブレイカー。"
         "D・D・D[光/火/自然(7)]：自分のクリーチャーが攻撃する時、光・火・自然の7マナを支払って手札から出してもよい。"
         "相手のクリーチャーが出るか攻撃することによって能力がトリガーする時、これが進化クリーチャーなら、"
         "かわりにその能力はトリガーしない",
    note="「出ることによってトリガーする能力」は ENTERTRIGLOCK で止めたが、2点残っている。"
         "（1）「攻撃することによってトリガーする能力」を止める差し込み口がエンジンになく、"
         "ABILOCK を使うと engine3.attack が攻撃そのものを打ち切ってしまうため、こちらは止められない。"
         "（2）ENTERTRIGLOCK は ENTER（そのクリーチャー自身の「出た時」）と同時に ENTERWATCH"
         "（他のカードの「クリーチャーが出た時」）もまとめて止めるため、"
         "本来は不発にならない「相手のクリーチャーが出た時」の誘発（自分の分も含む）まで止まる",
    status="partial", source=SRC["e_gg001"])


# ================================================================ アリス・ルピア
def e_alicerupia(s, i, u):
    p = s.P[i]
    top = _top(s, i, 3)
    for k in sorted(top, key=E.PRI.get, reverse=True):
        c = BY_KEY[k]
        if c.kind != "C" or "firebird" not in c.races or k == "e_alicerupia" or (c.evo and not c.neo):
            continue
        if s.fate(i, k, "deck", False) != "ok":
            continue
        top.remove(k)
        s.ev(f"　アリス・ルピア：{c.name} を出す")
        nu = s.enter(i, k, "deck", False, sa=True)
        if nu is not None:
            nu.x["aeot"] = s.turn
    for k in top:
        s.grave_put(i, k)


def te_alicerupia(s, i, u):
    """このターンの終わりに、出したクリーチャーを破壊する"""
    for z in s.P[i].board[:]:
        if z.x.get("aeot") == s.turn and z in s.P[i].board:
            s.leave(i, z, "grave", destroy=True)


def ts_alicerupia(s, i, u):
    """アリス・ルピアが先に離れていた時の取りこぼしを、次の自分のターンのはじめに片づける"""
    if u.x.get("aeot") and u.x["aeot"] < s.turn and u in s.P[i].board:
        s.leave(i, u, "grave", destroy=True)


add("e_alicerupia", "アリス・ルピア", 8, "F", power=8000, brk=2, gs=True, pri=10, races=("armoredfirebird", "firebird"),
    roles="atk fin", enter=e_alicerupia, tend=te_alicerupia, tstartall=ts_alicerupia,
    text="W・ブレイカー、G・ストライク。出た時、自分の山札の上から3枚を表向きにし、"
         "その中の《アリス・ルピア》以外のファイアー・バード・クリーチャーを好きな数バトルゾーンに出し、残りを墓地に置く。"
         "出したクリーチャーはスピードアタッカーを得て、このターンの終わりに破壊される",
    source=SRC["e_alicerupia"])


# ================================================================ 竹馬の超人／テイクバック・チャージャー
def e_takeuma(s, i, u):
    s.ramp(i, 2)


def sp_takeuma(s, i):
    """テイクバック・チャージャー（呪文側）"""
    o = s.P[1 - i]
    t = s.target(i, lambda z: z.c.cost <= 3, "CTX")
    if t is not None:
        before = o.mused
        s.ev(f"　{t.c.name} をタップして持ち主のマナゾーンへ")
        move(s, i, t, "mana")
        if o.mused == before and o.mused < len(o.mana):
            o.mused += 1
    s.add_mana(i, "e_takeuma")
    s.ev("　チャージャー：テイクバック・チャージャーをマナゾーンへ")


add("e_takeuma", "竹馬の超人 / テイクバック・チャージャー", 7, "N", power=11000, brk=2, twin=(3, "N", False),
    pri=9, races=("giant",), roles="acc rem", enter=e_takeuma, spell=sp_takeuma, nograve=True,
    text="W・ブレイカー。出た時、自分の山札の上から2枚をタップしてマナゾーンに置く。"
         "呪文側《テイクバック・チャージャー》（自然3・ジャイアント・スキル）：コスト3以下のエレメント1つを選び、"
         "タップして持ち主のマナゾーンに置いてもよい。チャージャー（唱えた後、墓地ではなくマナゾーンに置く）",
    source=SRC["e_takeuma"])


# ================================================================ 凰翔竜機マーチ・ルピア
def w_marchrupia(s, i, u, dest, destroy_):
    """自分のファイアー・バードが破壊された時、それより軽いファイアー・バードを墓地から出す"""
    if not destroy_ or u.c.kind != "C" or "firebird" not in u.c.races:
        return
    if not s.has(i, "e_marchrupia"):
        return
    s.revive(i, lambda c: "firebird" in c.races and c.cost < u.c.cost)


add("e_marchrupia", "凰翔竜機マーチ・ルピア", 6, "DF", power=6000, brk=2, sa=True, pri=8,
    races=("armoreddragon", "dragon", "firebird"), roles="atk rem", leavewatch=w_marchrupia,
    changex=lambda s, i, u: "firebird" in u.c.races and u.c.cost >= 3,
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
                                        and "firebird" in BY_KEY[kk].races and BY_KEY[kk].cost >= 3) >= 3
    else "革命チェンジの元になるコスト3以上のファイアー・バードが3体いない",
    text="W・ブレイカー、スピードアタッカー、スレイヤー（バトルした相手のクリーチャーを破壊する）。"
         "革命チェンジ：コスト3以上のファイアー・バード（それが攻撃する時、手札のこのカードと入れ替えてもよい）。"
         "自分のファイアー・バード・クリーチャーが破壊された時、それよりコストが小さいファイアー・バード・クリーチャー1体を"
         "自分の墓地から出してもよい",
    source=SRC["e_marchrupia"])
SLAYER.add("e_marchrupia")


# ================================================================ 龍罠 エスカルデン／マクスカルゴ・トラップ
def e_escalden(s, i, u):
    p = s.P[i]
    top = _top(s, i, 2)
    cs = [k for k in top if BY_KEY[k].kind == "C"]
    if cs:
        k = max(cs, key=lambda x: E.PRI[x] - 3 * p.hand.count(x))
        top.remove(k)
        p.hand.append(k)
        s.ev(f"　{BY_KEY[k].name} を手札へ")
    for k in top:
        s.add_mana(i, k, src="deck")


def sp_escalden(s, i):
    """マクスカルゴ・トラップ（呪文側）"""
    t = s.target(i)
    if t is not None:
        s.ev(f"　{t.c.name} を持ち主のマナゾーンへ")
        move(s, i, t, "mana")
    s.revive(i, lambda c: c.cost <= 6, "mana")


add("e_escalden", "龍罠 エスカルデン / マクスカルゴ・トラップ", 5, "N", power=5000, twin=(7, "N", False), pri=7,
    races=("dragonguild", "dragon", "gransect"), roles="acc draw rem", enter=e_escalden, spell=sp_escalden,
    text="出た時、自分の山札の上から2枚を表向きにし、その中のクリーチャー1体を手札に加えてもよい。残りをマナゾーンに置く。"
         "呪文側《マクスカルゴ・トラップ》（自然7）：相手のクリーチャー1体を選び、持ち主のマナゾーンに置く。"
         "その後、コスト6以下のクリーチャー1体を自分のマナゾーンから出す",
    source=SRC["e_escalden"])


# ================================================================ グレート・グラスパー
def e_grasper(s, i, u):
    t = s.target(i)
    if t is not None:
        s.ev(f"　{t.c.name} を持ち主のマナゾーンへ")
        move(s, i, t, "mana")


def w_grasper(s, i, u):
    """自分のNEOクリーチャーが攻撃する時、それより小さいクリーチャーをマナゾーンから出す"""
    if not u.c.neo or not s.has(i, "e_grasper") or s.manaexec(i):
        return
    w = s.power(i, u, True)
    s.revive(i, lambda c: c.power < w, "mana")


add("e_grasper", "グレート・グラスパー", 8, "N", power=14000, brk=3, evo="N", neo=True, pri=11, races=("gransect",),
    roles="rem fin acc", enter=e_grasper, atkwatch=w_grasper,
    text="NEO進化（自分の自然のクリーチャー1体の上に置いてもよいし、そのまま召喚してもよい）。T・ブレイカー。"
         "出た時、クリーチャー1体を選び、持ち主のマナゾーンに置いてもよい。"
         "自分のNEOクリーチャーが攻撃する時、それよりパワーが小さいクリーチャー1体を自分のマナゾーンから出してもよい",
    source=SRC["e_grasper"])
