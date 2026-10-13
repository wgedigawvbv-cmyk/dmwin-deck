"""cardspec3.json の26枚（すでに実装済みのバイケン・進化設計図・ジャジーブラッドは除く）

  この札束に入っている新しい仕組み
    ・シンカライズ／超魂X（ウルの天宝・昇カオスマントラ）
    ・D・D・D［無色(8)］＝自分のクリーチャーが攻撃する時、手札からコストを支払って出す（ドギラゴン王道）
    ・鬼S-MAX進化（進化元不要。離れる時、かわりに自分の表向きのカード3枚を破壊）＝CRYMAX ジャオウガ
    ・スター進化（離れる時、かわりに一番上のカードだけが墓地に行き、下のクリーチャーが残る）＝カチコミ入道
    ・メテオバーン（究極銀河ユニバースの特殊勝利）
    ・ファイアー・バード・メクレイド8（クイーン・ルピア）
    ・S・バック［闇］（秩序の意志）／封印
    ・光臨（メイ様）／ハイパー化・ハイパーモード（サエポヨX）／Zラッシュ（アドミラル・アレグル）
    ・エスケープ（昇カオスマントラ、ドギラゴン王道が与えるもの）
    ・ハイパーエナジー（Drache der'Zen）

  調べ直して確かめたところ（cardspec3.json の記述は正しかった）
    究極銀河ユニバース（コスト5・フェニックス1体の上）、ヨビニオン・マルル（各ターン2体目のクリーチャー）、
    若き大長老 アプル（ガードマンと墓地・マナの封じ）、水晶の祈り／クリスタル・ドゥーム、
    Disカルセ・ドニー、昇カオスマントラ（「このクリーチャー以下のコスト」）、逆転の剣スカイソード、
    旋略のS アドミラル・アレグル、剣轟の団長 ドギラゴン王道（D・D・D の意味とドリーム・クリーチャーであること）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move
from envcards.env0 import (guardman, SLAYER, discard_choice, he_costx, he_payx,
                           star_evo_rep)

SRC = {
    "e_urutenpo": "https://dmwiki.net/%E3%80%8A%E3%82%A6%E3%83%AB%E3%81%AE%E5%A4%A9%E5%AE%9D%E3%80%8B",
    "e_dogiodo": "https://dmwiki.net/%E3%80%8A%E5%89%A3%E8%BD%9F%E3%81%AE%E5%9B%A3%E9%95%B7%20%E3%83%89%E3%82%AE%E3%83%A9%E3%82%B4%E3%83%B3%E7%8E%8B%E9%81%93%E3%80%8B",
    "e_crymax": "https://dmwiki.net/%E3%80%8ACRYMAX%20%E3%82%B8%E3%83%A3%E3%82%AA%E3%82%A6%E3%82%AC%E3%80%8B",
    "e_queenrupia": "https://dmwiki.net/%E3%80%8A%E9%BE%8D%E5%90%8E%E5%87%B0%E7%BF%94%E3%82%AF%E3%82%A4%E3%83%BC%E3%83%B3%E3%83%BB%E3%83%AB%E3%83%94%E3%82%A2%E3%80%8B",
    "e_allegre": "https://dmwiki.net/%E3%80%8A%E6%97%8B%E7%95%A5%E3%81%AES%20%E3%82%A2%E3%83%89%E3%83%9F%E3%83%A9%E3%83%AB%E3%83%BB%E3%82%A2%E3%83%AC%E3%82%B0%E3%83%AB%E3%80%8B",
    "e_gaiash": "https://dmwiki.net/%E3%80%8A%E6%B5%81%E6%98%9F%E3%81%AE%E3%82%AC%E3%82%A4%E3%82%A2%E3%83%83%E3%82%B7%E3%83%A5%E3%83%BB%E3%82%AB%E3%82%A4%E3%82%B6%E3%83%BC%E3%80%8B",
    "e_meisama": "https://dmwiki.net/%E3%80%8A%E6%A3%AE%E5%A4%A2%E3%81%AE%E3%82%A4%E3%82%B6%E3%83%8A%E3%82%A4%20%E3%83%A1%E3%82%A4%E6%A7%98%E3%80%8B",
    "e_wakaapul": "https://dmwiki.net/%E3%80%8A%E8%8B%A5%E3%81%8D%E5%A4%A7%E9%95%B7%E8%80%81%20%E3%82%A2%E3%83%97%E3%83%AB%E3%80%8B",
    "e_tachiagaru": "https://dmwiki.net/%E3%80%8A%E2%99%AA%E7%AB%8B%E3%81%A1%E4%B8%8A%E3%81%8C%E3%82%8B%20%E6%82%AA%E9%AD%94%E3%81%AB%E5%A4%A9%E4%BD%BF%20%E5%A0%95%E3%81%A1%E3%82%8B%E3%81%8B%E3%81%AA%E3%80%8B",
    "e_katchikomi": "https://dmwiki.net/%E3%80%8A%E3%82%AB%E3%83%81%E3%82%B3%E3%83%9F%E5%85%A5%E9%81%93+%EF%BC%9C%E3%83%90%E3%83%88%E3%83%A9%E3%82%A4.%E9%AC%BC%EF%BC%9E%E3%80%8B",
    "e_universe": "https://dmwiki.net/%E3%80%8A%E7%A9%B6%E6%A5%B5%E9%8A%80%E6%B2%B3%E3%83%A6%E3%83%8B%E3%83%90%E3%83%BC%E3%82%B9%E3%80%8B",
    "e_karusedoni": "https://dmwiki.net/%E3%80%8ADis%E3%82%AB%E3%83%AB%E3%82%BB%E3%83%BB%E3%83%89%E3%83%8B%E3%83%BC%E3%80%8B",
    "e_aofeshi": "https://dmwiki.net/%E3%80%8A%E5%B7%A8%E9%AD%94%E5%A4%A9%20%E3%82%A2%E3%82%AA%E3%83%95%E3%82%A7%E3%82%B7%E3%83%BC%E3%80%8B",
    "e_shokaos": "https://dmwiki.net/%E3%80%8A%E6%98%87%E3%82%AB%E3%82%AA%E3%82%B9%E3%83%9E%E3%83%B3%E3%83%88%E3%83%A9%E3%80%8B",
    "e_marul": "https://dmwiki.net/%E3%80%8A%E3%83%A8%E3%83%93%E3%83%8B%E3%82%AA%E3%83%B3%E3%83%BB%E3%83%9E%E3%83%AB%E3%83%AB%E3%80%8B",
    "e_rapadaisu": "https://dmwiki.net/%E3%80%8A%E3%82%B8%E3%83%A3%E3%83%B3%E3%83%9C%E3%83%BB%E3%83%A9%E3%83%91%E3%83%80%E3%82%A4%E3%82%B9%E3%80%8B",
    "e_mildias": "https://dmwiki.net/%E3%80%8A%E5%A4%A9%E5%BD%A9%E3%81%AE%E7%B2%BE%E9%9C%8A%E3%83%9F%E3%83%AB%E3%83%87%E3%82%A3%E3%82%A2%E3%82%B9%E3%80%8B",
    "e_sanmad": "https://dmwiki.net/%E3%80%8AS%E7%B4%9A%E5%8E%9F%E5%A7%8B%20%E3%82%B5%E3%83%B3%E3%83%9E%E3%83%83%E3%83%89%E3%80%8B",
    "e_aichoice": "https://dmwiki.net/%E3%80%8ADis%E3%82%A2%E3%82%A4%E3%83%BB%E3%83%81%E3%83%A7%E3%82%A4%E3%82%B9%E3%80%8B",
    "e_saepoyo": "https://dmwiki.net/%E3%80%8A%E5%AE%8C%E7%92%A7%E5%A6%96%E7%B2%BE%E3%82%B5%E3%82%A8%E3%83%9D%E3%83%A8X%E3%80%8B",
    "e_skysword": "https://dmwiki.net/%E3%80%8A%E9%80%86%E8%BB%A2%E3%81%AE%E5%89%A3%E3%82%B9%E3%82%AB%E3%82%A4%E3%82%BD%E3%83%BC%E3%83%89%E3%80%8B",
    "e_chitsujo": "https://dmwiki.net/%E3%80%8A%E7%A7%A9%E5%BA%8F%E3%81%AE%E6%84%8F%E5%BF%97%E3%80%8B",
    "e_akernal": "https://dmwiki.net/%E3%80%8A%E6%98%9F%E9%96%80%E3%81%AE%E7%B2%BE%E9%9C%8A%E3%82%A2%E3%82%B1%E3%83%AB%E3%83%8A%E3%83%AB%EF%BC%8F%E3%82%B9%E3%82%BF%E3%83%BC%E3%82%B2%E3%82%A4%E3%82%BA%E3%83%BB%E3%82%B2%E3%83%BC%E3%83%88%E3%80%8B",
    "e_drachezen": "https://dmwiki.net/%E3%80%8A%E7%88%86%E8%97%8D%E6%9C%88+Drache+der%27Zen%E3%80%8B",
    "e_emeral": "https://dmwiki.net/%E3%80%8A%E3%82%A8%E3%83%A1%E3%83%A9%E3%83%AB%E3%80%8B",
    "e_suisho": "https://dmwiki.net/%E3%80%8A%E6%B0%B4%E6%99%B6%E3%81%AE%E7%A5%88%E3%82%8A%EF%BC%8F%E3%82%AF%E3%83%AA%E3%82%B9%E3%82%BF%E3%83%AB%E3%83%BB%E3%83%89%E3%82%A5%E3%83%BC%E3%83%A0%E3%80%8B",
}


# ================================================================ 共通の道具
def _mek(s, i, n, pred, what):
    """メクレイドX：山札の上から3枚を見て、条件に合うコストn以下のカード1枚をコストを支払わずに使う"""
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


def _put_from_hand(s, i, pred):
    """手札から、条件に合う進化でない（またはNEO進化の）クリーチャー1体をコストを支払わずに出す"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or (c.evo and not c.neo) or not pred(c):
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return None
    p.hand.remove(best)
    s.ev(f"　手札から {BY_KEY[best].name} を出す")
    return s.enter(i, best, "hand", False)


def _escape(s, i, u, what):
    """エスケープ：破壊されるかわりに自分のシールド1つを手札に加える（S・トリガーは使えない）"""
    p = s.P[i]
    for j in range(len(p.sh) - 1, -1, -1):
        if not p.sh[j][1]:
            p.hand.append(p.sh.pop(j)[0])
            s.shield_left()
            s.ev(f"　エスケープ：シールドを1つ手札に加えて {what} は破壊されない")
            return True
    return False


def _cre_count(deck, pred):
    return sum(v for kk, v in deck.items() if BY_KEY[kk].kind == "C" and pred(BY_KEY[kk]))


# ================================================================ ウルの天宝（シンカライズ・超魂X）
def e_urutenpo(s, i, u):
    """シンカライズ：出た時、このタマシードから進化できるコスト6以下のNEOクリーチャーを手札から上に置く"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or not c.neo or not c.evo or c.cost > 6:
            continue
        ex = E.EVOX.get(k)
        ok = ex(s, i, u) if ex is not None else bool(set(c.evo) & set("L"))
        if not ok:
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None or u not in p.board:
        return
    p.hand.remove(best)
    s.ev(f"　シンカライズ：ウルの天宝の上に {BY_KEY[best].name}")
    s.enter(i, best, "hand", False, on=u)


add("e_urutenpo", "ウルの天宝", 4, "L", kind="T", trig=True, races=("angelcommand", "command", "fusioner"),
    blocker=True, pri=5, roles="blk trg",
    enter=e_urutenpo,
    blockok=lambda s, u: u.c.kind == "C" and "e_urutenpo" in u.under,
    text="S・トリガー。タマシード。シンカライズ：このタマシードは進化クリーチャーの進化元にできる。"
         "出た時、自分の手札から、このタマシードから進化できるコスト6以下のNEOクリーチャー1体をこのカードの上に"
         "置いてもよい。超魂X：このカードがクリーチャーの下にある間、そのクリーチャーはブロッカーを得る",
    source=SRC["e_urutenpo"])
E.SHINKA.add("e_urutenpo")


# ================================================================ 剣轟の団長 ドギラゴン王道
def _multi_out(s, i, u):
    """出た時／攻撃する時：コスト7以下の多色クリーチャー1体を手札かマナゾーンから出す"""
    p = s.P[i]
    best, bv, src = None, -1, None
    for zone, zn in ((p.hand, "hand"), (p.mana, "mana")):
        if zn == "mana" and s.manaexec(i):
            continue
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if c.kind != "C" or c.cost > 7 or not c.multi or (c.evo and not c.neo):
                continue
            if E.PRI[k] > bv and s.fate(i, k, zn, False) == "ok":
                best, bv, src = k, E.PRI[k], zn
    if best is None:
        return
    if src == "mana":
        s.take_mana(i, best)
    else:
        p.hand.remove(best)
    s.ev(f"　ドギラゴン王道：{'マナ' if src == 'mana' else '手札'}から {BY_KEY[best].name}")
    s.enter(i, best, src, False)


def _evo_src_but(s, i, k, skip):
    """進化元を選ぶ（攻撃中のクリーチャーは選ばない）"""
    e = BY_KEY[k].evo or ""
    best, bv = None, None
    for z in s.P[i].board:
        if z is skip or (z.c.kind != "C" and z.k not in E.SHINKA):
            continue
        if not (set(z.c.civ) & set(e)):
            continue
        v = (z.tap, bool(z.c.meta), E.PRI[z.k] + len(z.under))
        if bv is None or v < bv:
            best, bv = z, v
    return best


def w_dogiodo_ddd(s, i, u):
    """D・D・D[無色(8)]：自分のクリーチャーが攻撃する時、攻撃中のクリーチャーのコスト分安く手札から召喚する"""
    p = s.P[i]
    if "e_dogiodo" not in p.hand or u.k == "e_dogiodo":
        return
    if not {"L", "F", "N"} <= E.civs(p):
        return
    n = max(0, 8 - u.c.cost)
    if n > len(p.mana) - p.mused:
        return
    if s.fate(i, "e_dogiodo", "hand", True) != "ok":
        return
    p.hand.remove("e_dogiodo")
    p.mused += n
    s.ev(f"　D・D・D[無色(8)]：剣轟の団長 ドギラゴン王道を{n}マナで召喚")
    s.enter(i, "e_dogiodo", "hand", True, on=_evo_src_but(s, i, "e_dogiodo", u))


def _dogiodo_here(s, i):
    return any(z.k == "e_dogiodo" for z in s.P[i].board)


def _dogi_other_multi(s, i, u):
    return u.c.kind == "C" and u.c.multi and u.k != "e_dogiodo" and _dogiodo_here(s, i)


def rep_dogiodo(s, i, u, dest, destroy_):
    """ドギラゴン王道が与えるエスケープ"""
    if not destroy_ or dest != "grave" or not _dogi_other_multi(s, i, u):
        return False
    return _escape(s, i, u, u.c.name)


def fx_dogiodo(s, owner, u, i, k, src, summon, res):
    """ドリーム・クリーチャー：同じ名前のものは2体目は出られない"""
    if i == owner and k == u.k:
        return "no"
    return res


add("e_dogiodo", "剣轟の団長 ドギラゴン王道", 8, "LFN", power=13000, brk=3, evo="LFN", neo=True, gneo=True,
    races=("megacommanddragon", "command", "dragon", "revolution", "hamukatsu", "dream"), pri=12,
    roles="fin atk rem acc",
    enter=_multi_out, attack=_multi_out, atkwatch=w_dogiodo_ddd, leaverep=rep_dogiodo, fatex=fx_dogiodo,
    saok=lambda s, i, u: _dogi_other_multi(s, i, u), machok=lambda s, i, u: _dogi_other_multi(s, i, u),
    text="G-NEO進化（光・火・自然のクリーチャー1体の上に置いてもよい。離れる時、かわりに下のカードがすべて離れる）。"
         "T・ブレイカー。自分のマナゾーンに光・火・自然の各文明があれば、このカードに「D・D・D［無色(8)］」"
         "（自分のクリーチャーが攻撃する時、手札からこのカードを8マナ払って召喚してよい）を与え、"
         "そのコストを攻撃中のクリーチャーのコストの分だけ少なくする（0未満にはならない）。"
         "出た時または攻撃する時、コスト7以下の多色クリーチャー1体を自分の手札またはマナゾーンから出してもよい。"
         "自分の他の多色クリーチャーすべてにスピードアタッカーとマッハファイターとエスケープを与える。"
         "ドリーム・クリーチャー（同じ名前のものは1体しかバトルゾーンに出せない）",
    source=SRC["e_dogiodo"])


# ================================================================ CRYMAX ジャオウガ
def _crymax_cost(s, i, u, why="CRYMAX ジャオウガ は離れない"):
    """鬼S-MAX進化の置き換え：自分の表向きのカード3枚を破壊する。できたら True"""
    p = s.P[i]
    shields = [j for j, (k, up) in enumerate(p.sh) if up]
    boards = [z for z in p.board if z is not u]
    if len(shields) + len(p.mana) + len(boards) < 3:
        return False
    left = 3
    for j in sorted(shields, reverse=True):
        if left <= 0:
            break
        p.grave.append(p.sh.pop(j)[0])
        s.shield_left()
        left -= 1
    while left > 0 and p.mana:
        k = min(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        s.grave_put(i, k)
        left -= 1
    while left > 0:
        cands = [z for z in p.board if z is not u]
        if not cands:
            break
        z = min(cands, key=s.val)
        s.leave(i, z, "grave", destroy=True)
        left -= 1
    s.ev(f"　鬼S-MAX進化：自分の表向きのカード3枚を破壊して{why}")
    return left <= 0


def rep_crymax(s, i, u, dest, destroy_):
    if u.k != "e_crymax":
        return False
    p = s.P[i]
    if p.x.get("crymax_busy"):
        return False
    p.x["crymax_busy"] = True
    try:
        return _crymax_cost(s, i, u)
    finally:
        p.x["crymax_busy"] = False


def lose_crymax(s, i, how):
    """自分が負ける時、かわりに自分の表向きのカード3枚を破壊してもよい（できたら負けない）"""
    p = s.P[i]
    u = None
    for z in p.board:
        if z.k == "e_crymax":
            u = z
            break
    if u is None or p.x.get("crymax_busy"):
        return False
    p.x["crymax_busy"] = True
    try:
        return _crymax_cost(s, i, u, why="負けない")
    finally:
        p.x["crymax_busy"] = False


def e_crymax(s, i, u):
    """出た時：S-MAX進化が2体以上なら1体を残す。その後、各プレイヤーのシールドを3つにする"""
    p = s.P[i]
    smax = [z for z in p.board if z.k == "e_crymax"]
    if len(smax) > 1:
        for z in smax[:-1]:
            if z in p.board:
                p.board.remove(z)
                p.hand.append(z.k)
                for kk in z.under:
                    s.put_zone(i, kk, "grave")
        s.ev("　S-MAX進化クリーチャーが2体以上：1体を残して残りを手札に戻す")
    for j in (0, 1):
        q = s.P[j]
        while len(q.sh) > 3:
            idx, bv = 0, None
            for t, (kk, up) in enumerate(q.sh):
                v = (up, E.PRI[kk])
                if bv is None or v < bv:
                    idx, bv = t, v
            q.grave.append(q.sh.pop(idx)[0])
            s.shield_left()
        s.ev(f"　プレイヤー{j} はシールドを3つ選び、残りを墓地に置いた（残り{len(q.sh)}）")


def a_crymax(s, i, u):
    t = s.target(i)
    if t is not None:
        destroy(s, i, t)
    for _ in range(2):
        s.discard_random(1 - i)


add("e_crymax", "CRYMAX ジャオウガ", 7, "D", power=13000, brk=3, evo="D", neo=True,
    races=("demonio", "rexstars"), pri=12, roles="fin rem dis",
    enter=e_crymax, attack=a_crymax, leaverep=rep_crymax, loserep=lose_crymax, evox=lambda s, i, u: False,
    text="鬼S-MAX進化：進化元なしで召喚できる（進化クリーチャー扱い）。T・ブレイカー。"
         "自分が負ける時、またはこのクリーチャーがバトルゾーンを離れる時、"
         "かわりに自分の表向きのカード3枚を破壊してもよい。"
         "出た時、S-MAX進化クリーチャーが2体以上あれば1体を残して残りを手札に戻し、"
         "その後、各プレイヤーは自分のシールドを3つ選び、残りを自分の墓地に置く。"
         "攻撃する時、相手のクリーチャー1体を破壊し、その後、相手は自分の手札を2枚、見ないで選んで捨てる",
    source=SRC["e_crymax"])


# ================================================================ 龍后凰翔クイーン・ルピア
def _fb_others(s, i, u):
    return [z for z in s.P[i].board if z is not u and "firebird" in z.c.races]


def a_queenrupia(s, i, u):
    """攻撃する時、自分のファイアー・バード1体を破壊して、ファイアー・バード・メクレイド8"""
    oth = _fb_others(s, i, u)
    if not oth:
        return
    z = min(oth, key=s.val)
    s.ev(f"　クイーン・ルピア：{z.c.name} を破壊してファイアー・バード・メクレイド8")
    s.leave(i, z, "grave", destroy=True)
    _mek(s, i, 8, lambda c: "firebird" in c.races, "ファイアー・バード・メクレイド8")


def rep_queenrupia(s, i, u, dest, destroy_):
    """破壊される時、かわりに自分の他のファイアー・バード1体を破壊する"""
    if u.k != "e_queenrupia" or not destroy_:
        return False
    p = s.P[i]
    if p.x.get("qr_busy"):
        return False
    oth = _fb_others(s, i, u)
    if not oth:
        return False
    z = min(oth, key=s.val)
    p.x["qr_busy"] = True
    try:
        s.ev(f"　クイーン・ルピア：かわりに {z.c.name} を破壊")
        s.leave(i, z, "grave", destroy=True)
    finally:
        p.x["qr_busy"] = False
    return True


add("e_queenrupia", "龍后凰翔クイーン・ルピア", 5, "LDF", power=7500, brk=2, blocker=True, sa=True,
    races=("armoredfirebird", "firebird", "dragonbride"), pri=8, roles="blk atk acc fin",
    attack=a_queenrupia, leaverep=rep_queenrupia,
    text="ブロッカー、スピードアタッカー、W・ブレイカー。このクリーチャーが破壊される時、"
         "かわりに自分の他のファイアー・バード1体を破壊してもよい。"
         "攻撃する時、自分のファイアー・バード1体を破壊してもよい。そうしたら、ファイアー・バード・メクレイド8"
         "（山札の上から3枚を見て、その中のコスト8以下のファイアー・バード1枚をコストを支払わずに使う）",
    source=SRC["e_queenrupia"])


# ================================================================ 旋略のS アドミラル・アレグル
def w_allegre(s, i, u):
    """相手のクリーチャーが出た時、自分は1枚引く"""
    if u.c.kind != "C":
        return
    if any(z.k == "e_allegre" for z in s.P[1 - i].board):
        s.draw(1 - i)


def a_allegre(s, i, u):
    """ハイパーモード中、攻撃する時、手札の枚数以下のコストのクリーチャーでないカードを1枚ただで使う"""
    if not u.hyper:
        return
    p = s.P[i]
    n = len(p.hand)
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "C" or c.cost > n:
            continue
        if c.kind == "S" and not s.spell_ok(i, c.cost):
            continue
        if c.kind == "G" and s.has(1 - i, "fujin"):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　アドミラル・アレグル：{BY_KEY[best].name} をただで使う")
        free_play(s, i, best)


add("e_allegre", "旋略のS アドミラル・アレグル", 2, "W", power=1000, blocker=True, zrush=True,
    races=("cybermoon", "hyperbeast"), pri=5, roles="blk draw dis",
    enterwatch=w_allegre, attack=a_allegre,
    text="ブロッカー。相手のクリーチャーが出た時、自分は1枚引いてもよい。"
         "Zラッシュ：自分のシールドが離れたら、次の自分のターンのはじめまでハイパーモードを解放する"
         "（ハイパーモード中はパワー6000・W・ブレイカー）。ハイパーモード中、攻撃する時、"
         "自分の手札の枚数以下のコストを持つクリーチャーでないカード1枚を、手札からコストを支払わずに使ってよい",
    source=SRC["e_allegre"])
E.HYPER_POW["e_allegre"] = 5000


# ================================================================ 流星のガイアッシュ・カイザー
def w_gaiash_mark(s, i, u):
    """相手がコストを支払わずにクリーチャーを出したことを覚えておく"""
    if u.c.kind == "C" and u.x.get("summoned") is False:
        s.P[i].x["freeplay_t"] = s.turn


def w_gaiash_spell(s, i, k):
    """コストを支払わずに呪文を唱えたことを覚えておく（G・ゼロなど、実際のコストが0の呪文）

    s.spcost が 0 を返す呪文＝マナをタップせずに唱えられる呪文。
    他のカードの効果で「コストを支払わずに唱える」分は、払ったコストを知らせる
    差し込み口がないので拾えない（note に書いた）。"""
    if s.spcost(i, k) == 0:
        s.P[i].x["freeplay_t"] = s.turn


def te_gaiash(s, di):
    """相手のターンの終わりに、相手がそのターンコストを支払わずにクリーチャーを出していれば、ただで召喚してよい

    tendp は「ターンの終わり」に両プレイヤーについて1度ずつ呼ばれる（バトルゾーンが空でも呼ばれる）。
    唱える側は「相手のターンの終わり」なので、いまのターンのプレイヤーの側では何もしない。"""
    if di == s.tp:
        return
    p = s.P[di]
    if "e_gaiash" not in p.hand or s.has(di, "e_gaiash"):
        return
    if s.P[s.tp].x.get("freeplay_t") != s.turn:
        return
    if s.fate(di, "e_gaiash", "hand", True) != "ok":
        return
    p.hand.remove("e_gaiash")
    s.ev("　流星のガイアッシュ・カイザー：相手がコストを支払わずに出したので、ただで召喚")
    s.enter(di, "e_gaiash", "hand", True)


def np_gaiash(s, i, u):
    """相手のクリーチャーは、出たターン、自分（プレイヤー）を攻撃できない"""
    return u.sick and s.has(1 - i, "e_gaiash")


add("e_gaiash", "流星のガイアッシュ・カイザー", 6, "WN", power=8000, brk=2,
    races=("bluecommanddragon", "greencommanddragon", "command", "dragon", "hunter"), pri=9,
    roles="draw dis acc fin",
    enter=lambda s, i, u: s.draw(i, 2), tendp=te_gaiash, enterwatch=w_gaiash_mark,
    spellwatch=w_gaiash_spell, noatkplock=np_gaiash,
    costaura=lambda s, i, k, cur: max(0, cur - 4) if BY_KEY[k].kind == "C" and BY_KEY[k].cost >= 10
    and cur > 0 and any(z.k == "e_gaiash" for z in s.P[i].board) else cur,
    text="W・ブレイカー。相手のターンの終わりに、相手がそのターン、コストを支払わずにクリーチャーを出すか"
         "呪文を唱えていて、このクリーチャーが自分のバトルゾーンになければ、"
         "手札からコストを支払わずに召喚してよい。"
         "出た時、2枚引く。自分のコスト10以上のクリーチャーの召喚コストを4少なくする（0未満にはならない）。"
         "相手のクリーチャーは、出たターン、自分（プレイヤー）を攻撃できない",
    note="「コストを支払わずに」の判定は、相手がクリーチャーを踏み倒した分と、"
         "実際のコストが0の呪文（G・ゼロなど）を唱えた分だけを見ている。"
         "他のカードの効果で「コストを支払わずに唱える」呪文は拾えない。"
         "カードを実行した時に「実際に払ったコスト」を知らせる差し込み口（PLAYWATCH）がエンジンになく、"
         "呪文側（spellwatch）からは、ただで唱えさせられた呪文とマナを払って唱えた呪文を見分けられないため",
    status="partial", source=SRC["e_gaiash"])


# ================================================================ 森夢のイザナイ メイ様
def t_meisama(s, i, u):
    """光臨：自分のターンの終わりに、このクリーチャーがタップしていれば山札からドリームメイトを出す"""
    if not u.tap:
        return
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.deck)):
        c = BY_KEY[k]
        if c.kind != "C" or "dreammate" not in c.races or c.cost > 5 or (c.evo and not c.neo):
            continue
        if E.PRI[k] > bv and s.fate(i, k, "deck", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is not None:
        p.deck.remove(best)
        s.ev(f"　光臨：山札から {BY_KEY[best].name}")
        s.enter(i, best, "deck", False)
    s.rng.shuffle(p.deck)


add("e_meisama", "森夢のイザナイ メイ様", 3, "N", power=2000, races=("oracle", "dreammate"), pri=5,
    roles="acc atk",
    tend=t_meisama, changex=lambda s, i, u: "dreammate" in u.c.races,
    text="革命チェンジ（自分のドリームメイトが攻撃する時、そのクリーチャーと手札のこのカードを入れ替えてよい）。"
         "光臨：自分のターンの終わりに、このクリーチャーがタップされていれば、自分の山札から"
         "コスト5以下のドリームメイト1体を出してもよい。その後、山札をシャッフルする",
    source=SRC["e_meisama"])


# ================================================================ 若き大長老 アプル
def fx_wakaapul(s, owner, u, i, k, src, summon, res):
    """相手のカードは墓地・マナゾーンを離れない（＝そこからクリーチャーが出ない）"""
    if i != owner and src in ("grave", "mana"):
        return "no"
    return res


add("e_wakaapul", "若き大長老 アプル", 2, "N", power=3000, gs=True, races=("grandsect",), pri=5,
    roles="trg blk dis",
    fatex=fx_wakaapul, guard=guardman("e_wakaapul"),
    manaexec=lambda s, i: s.has(1 - i, "e_wakaapul"),
    text="G・ストライク。ガードマン：このクリーチャーをタップして、相手のクリーチャーの攻撃先を"
         "自分の他のクリーチャーからこのクリーチャーに変更してもよい。"
         "相手のカードは相手の墓地とマナゾーンを離れない。相手は自分の墓地とマナゾーンから呪文を唱えられない",
    note="「相手のカードは墓地とマナゾーンを離れない」は、相手が墓地・マナからクリーチャーを出すのと"
         "カードを使うのを止める形で実装した。相手が自分のマナ・墓地のカードを手札に戻す分は、"
         "墓地・マナからの持ち出しを止める差し込み口（ZONEMOVEREP）がエンジンになく、"
         "取り出す口も take_mana と各カードの直書きに散っているため省いた",
    status="partial", source=SRC["e_wakaapul"])


# ================================================================ ♪立ち上がる 悪魔に天使 堕ちるかな
def sp_tachiagaru(s, i):
    s.draw(i)
    o = s.P[1 - i]
    cnt = {}
    for z in o.board:
        if z.c.kind == "C":
            cnt[z.c.cost] = cnt.get(z.c.cost, 0) + 1
    if not cnt:
        for k in o.mana:
            cnt[BY_KEY[k].cost] = cnt.get(BY_KEY[k].cost, 0) + 1
    n = max(cnt, key=lambda c: (cnt[c], c)) if cnt else 4
    o.x["ban_num"] = (s.turn + (1 if s.tp == i else 0), n)
    s.ev(f"　数字{n}を選んだ：相手はコスト{n}の呪文を唱えられず、コスト{n}のエレメントの能力は働かない")


def _ban_num(s, j):
    v = s.P[j].x.get("ban_num")
    if v is None or v[0] < s.turn:
        return None
    return v[1]


def al_tachiagaru(s, i, u):
    """選んだ数字と同じコストの相手のエレメントの能力をすべて無視する（i＝そのカードの持ち主）

    攻撃を宣言しているクリーチャーだけ外している。engine3.attack が
    `if ABILOCK and not s.abi(i, u): return` で攻撃そのものを打ち切ってしまい、
    入れると「そのコストのクリーチャーは攻撃できない」になってしまうため。"""
    if s.atk is u:
        return False
    return _ban_num(s, i) == u.c.cost


add("e_tachiagaru", "♪立ち上がる 悪魔に天使 堕ちるかな", 4, "W", kind="S", trig=True, races=("magicsong",),
    pri=5, roles="draw dis trg",
    spell=sp_tachiagaru,
    spelllock=lambda s, i, cost: _ban_num(s, i) == cost,
    abilock=al_tachiagaru,
    text="S・トリガー。1枚引き、数字を1つ選ぶ。次の自分のターンのはじめまで、"
         "その数字と同じコストを持つ相手のエレメントの能力は働かず、相手はその数字と同じコストの呪文を唱えられない",
    note="「相手のエレメントの能力を無視する」は ABILOCK で実装したが、「攻撃する時」の誘発だけは止まらない。"
         "engine3.attack が ABILOCK で能力を無視されたクリーチャーの攻撃そのものを打ち切ってしまうため、"
         "攻撃中のクリーチャーを対象から外している（入れるとそのコストのクリーチャーが攻撃できなくなる）。"
         "パワーを増減する常在能力（POWERX・AURAP）も ABILOCK を通らないので止まらない",
    status="partial", source=SRC["e_tachiagaru"])


# ================================================================ カチコミ入道 <バトライ.鬼>
def e_katchikomi(s, i, u):
    """タマシードから進化していれば、相手のクリーチャー1体とバトルする"""
    if not u.under or BY_KEY[u.under[0]].kind != "T":
        return
    w = s.power(i, u)
    t = s.target(i, lambda z: s.power(1 - i, z) < w)
    if t is None:
        return
    s.ev(f"　カチコミ入道：{t.c.name} とバトル")
    s.battle(i, u, 1 - i, t)


rep_katchikomi = star_evo_rep("e_katchikomi", "カチコミ入道")


add("e_katchikomi", "カチコミ入道 <バトライ.鬼>", 3, "F", power=6000, brk=2, evo="F",
    races=("armoreddragon", "dragon", "flame", "command", "rexstars"), pri=7, roles="atk rem",
    enter=e_katchikomi, leaverep=rep_katchikomi,
    evox=lambda s, i, u: "rexstars" in u.c.races or "F" in u.c.civ,
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items() if kk != k and (
        "rexstars" in BY_KEY[kk].races or (BY_KEY[kk].kind in "CT" and "F" in BY_KEY[kk].civ))) >= 4
    else "スター進化の進化元（レクスターズか火のクリーチャー）が4枚ない",
    text="スター進化：自分のレクスターズまたは火のクリーチャー1体の上に置く（離れる時、かわりに一番上の"
         "このカードだけが墓地に置かれ、下のクリーチャーがバトルゾーンに残る）。W・ブレイカー。"
         "出た時、このクリーチャーがタマシードから進化していれば、相手のクリーチャー1体を選び、バトルしてもよい",
    source=SRC["e_katchikomi"])


# ================================================================ 究極銀河ユニバース
def a_universe(s, i, u):
    """メテオバーン：下のカードを1枚墓地に置く。それが最後の1枚でフェニックスなら勝つ"""
    if not u.under:
        return
    ph = [k for k in u.under if "phoenix" in BY_KEY[k].races]
    if not ph:
        return
    if len(u.under) == 1:
        k = u.under.pop()
        s.grave_put(i, k)
        s.ev("　メテオバーン：最後の1枚がフェニックスだったので勝ち")
        s.win(i, "究極銀河ユニバース")
        return
    k = next((x for x in u.under if "phoenix" not in BY_KEY[x].races), u.under[0])
    u.under.remove(k)
    s.grave_put(i, k)
    s.ev(f"　メテオバーン：{BY_KEY[k].name} を墓地に置く")


add("e_universe", "究極銀河ユニバース", 5, "L", power=17000, brk=3, evo="L", races=("phoenix",), pri=12,
    roles="fin atk",
    attack=a_universe, evox=lambda s, i, u: "phoenix" in u.c.races,
    playrule=lambda deck, k: None if _cre_count(deck, lambda c: "phoenix" in c.races and c.key != k) >= 2
    else "進化元になるフェニックスが2体いない",
    text="進化クリーチャー：自分のフェニックス1体の上に置く。T・ブレイカー。"
         "メテオバーン：攻撃する時、このクリーチャーの下のカードを1枚墓地に置いてもよい。"
         "それがこのクリーチャーの下の最後のカードで、フェニックスであれば、自分はゲームに勝つ",
    source=SRC["e_universe"])


# ================================================================ Disカルセ・ドニー
def bf_karusedoni(s, ai, au, di, du, a_dies, d_dies):
    if au.k == "e_karusedoni" and du.c.cost <= 5:
        d_dies = True
    return a_dies, d_dies


add("e_karusedoni", "Disカルセ・ドニー", 4, "LDN", power=1000, mach=True, races=("spiritquartz", "distas"),
    pri=6, roles="rem atk",
    enter=lambda s, i, u: _put_from_hand(s, i, lambda c: c.cost <= 5), battlefx=bf_karusedoni,
    text="マッハファイター。コスト5以下のクリーチャーを攻撃中、このクリーチャーはスレイヤーを得る"
         "（バトルした相手のクリーチャーを破壊する）。"
         "出た時、コスト5以下のクリーチャー1体を自分の手札から出してもよい",
    source=SRC["e_karusedoni"])


# ================================================================ 巨魔天 アオフェシー
def e_aofeshi(s, i, u):
    if s.atk is u:
        s.draw(i, 2)


add("e_aofeshi", "巨魔天 アオフェシー", 4, "W", power=6000, brk=2, races=("giant", "magic", "seres"), pri=7,
    roles="draw dis atk",
    enter=e_aofeshi, atklock=lambda s, i, u: u.sick and s.has(1 - i, "e_aofeshi"),
    changex=lambda s, i, u: u.c.cost >= 3 and ("giant" in u.c.races or "magic" in u.c.races),
    text="革命チェンジ（自分のコスト3以上のジャイアント、またはコスト3以上のマジックが攻撃する時、"
         "そのクリーチャーと手札のこのカードを入れ替えてよい）。W・ブレイカー。"
         "革命チェンジで出た時、2枚引く。相手のクリーチャーは、出たターン、攻撃できない",
    source=SRC["e_aofeshi"])


# ================================================================ 昇カオスマントラ
def w_shokaos(s, i, u):
    """超魂X：このクリーチャー（または下にこのカードがあるクリーチャー）が攻撃する時、
    それ以下のコストのクリーチャーを手札から出す"""
    if u.k != "e_shokaos" and "e_shokaos" not in u.under:
        return
    n = u.c.cost
    _put_from_hand(s, i, lambda c: c.cost <= n)


def rep_shokaos(s, i, u, dest, destroy_):
    if u.k != "e_shokaos" or not destroy_ or dest != "grave":
        return False
    return _escape(s, i, u, "昇カオスマントラ")


add("e_shokaos", "昇カオスマントラ", 2, "L", power=2500, races=("mechadelstella", "shinobi", "fusioner"),
    pri=5, roles="atk shd",
    atkwatch=w_shokaos, leaverep=rep_shokaos,
    text="エスケープ：このクリーチャーが破壊される時、墓地に置くかわりに自分のシールドを1つ手札に加えてもよい"
         "（そのS・トリガーは使えない）。超魂X：このカードがクリーチャーの下にあれば、そのクリーチャーにも"
         "次の能力を与える。攻撃する時、そのクリーチャー以下のコストのクリーチャー1体を自分の手札から出してもよい",
    source=SRC["e_shokaos"])


# ================================================================ ヨビニオン・マルル
def w_marul(s, i, u):
    """各ターン、自分の2体目のクリーチャーが出た時、山札の上1枚を手札かマナに置く"""
    if u.c.kind != "C":
        return
    p = s.P[i]
    if p.ent != 2 or p.x.get("marul_t") == s.turn:
        return
    if not any(z.k == "e_marul" for z in p.board):
        return
    if len(p.deck) <= 1:
        return
    p.x["marul_t"] = s.turn
    k = p.deck.pop()
    if E.PRI[k] >= 5 or len(p.mana) >= 7:
        p.hand.append(k)
        s.ev(f"　ヨビニオン・マルル：{BY_KEY[k].name} を手札へ")
    else:
        s.add_mana(i, k, True, src="deck")
        s.ev(f"　ヨビニオン・マルル：{BY_KEY[k].name} をタップしてマナへ")


add("e_marul", "ヨビニオン・マルル", 4, "N", power=5000, races=("snow",), pri=6, roles="acc draw",
    enterwatch=w_marul,
    text="各ターン、自分の2体目のクリーチャーが出た時、自分の山札の上から1枚目を見る。"
         "そのカードを手札に加えるか、タップしてマナゾーンに置く",
    source=SRC["e_marul"])


# ================================================================ ジャンボ・ラパダイス
def sp_rapadaisu(s, i):
    p = s.P[i]
    n = min(4, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    got = [k for k in top if BY_KEY[k].kind == "C" and BY_KEY[k].power >= 12000]
    for k in got:
        top.remove(k)
        p.hand.append(k)
    s.ev(f"　ジャンボ・ラパダイス：パワー12000以上のクリーチャー{len(got)}枚を手札へ")
    for k in top:
        p.deck.insert(0, k)


add("e_rapadaisu", "ジャンボ・ラパダイス", 2, "N", kind="S", trig=True, pri=4, roles="draw trg",
    spell=sp_rapadaisu,
    text="S・トリガー。自分の山札の上から4枚を表向きにする。その中のパワー12000以上のクリーチャーを"
         "すべて手札に加え、残りを好きな順序で山札の下に置く",
    source=SRC["e_rapadaisu"])


# ================================================================ 天彩の精霊ミルディアス
def e_mildias(s, i, u):
    s.ramp(i, 1)
    t = s.target(i, kinds="CTX")
    if t is not None:
        move(s, i, t, "hand")


add("e_mildias", "天彩の精霊ミルディアス", 3, "LWN", power=4500, blocker=True,
    races=("angelcommand", "command"), pri=5, roles="acc blk rem",
    enter=e_mildias,
    text="ブロッカー。出た時、自分の山札の上から1枚をマナゾーンに置く。"
         "その後、相手のエレメント1つを選び、持ち主の手札に戻してもよい",
    source=SRC["e_mildias"])


# ================================================================ S級原始 サンマッド
def e_sanmad(s, i, u):
    """出た時、バトルゾーンにクリーチャーが4体以上いれば、1体を持ち主のマナゾーンに置く"""
    if s.ncre(0) + s.ncre(1) < 4:
        return
    t = s.target(i)
    if t is not None:
        move(s, i, t, "mana")
        return
    mine = [z for z in s.P[i].board if z.c.kind == "C" and z is not u]
    if mine:
        z = min(mine, key=s.val)
        s.ev(f"　サンマッド：{z.c.name} をマナゾーンへ")
        s.leave(i, z, "mana")


add("e_sanmad", "S級原始 サンマッド", 3, "N", power=3000, evo="N",
    races=("guerrillacommand", "command", "sinvader"), pri=6, roles="rem atk",
    enter=e_sanmad,
    evox=lambda s, i, u: "N" in u.c.civ and u.c.cost == 3,
    invade=lambda s, i, u: "N" in u.c.civ and u.c.cost == 3,
    brkx=lambda s, i, u: 3 if s.ncre(i) >= 3 else None,
    playrule=lambda deck, k: None if _cre_count(deck, lambda c: c.key != k and "N" in c.civ and c.cost == 3) >= 4
    else "S級侵略の元になる自然のコスト3のクリーチャーが4体いない",
    text="進化：自分の自然のコスト3のクリーチャー1体の上に置く。"
         "S級侵略［原始］：自分の自然のコスト3のクリーチャーが攻撃する時、"
         "手札またはマナゾーンからこのカードをその上に重ねてよい。"
         "自分のクリーチャーが3体以上あれば、このクリーチャーはT・ブレイカーを得る。"
         "出た時、バトルゾーンにクリーチャーが4体以上あれば、そのうち1体を選び、持ち主のマナゾーンに置く",
    source=SRC["e_sanmad"])
E.INVZONE["e_sanmad"] = ("hand", "mana")


# ================================================================ Disアイ・チョイス
def e_aichoice(s, i, u):
    """出た時、自分のマナゾーンのS・トリガーを持つカード1枚をコストを支払わずに使う"""
    if s.manaexec(i):
        return
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if not (c.trig or (c.twin and c.twin[2])):
            continue
        if c.kind == "C" and (c.evo and not c.neo):
            continue
        if c.kind == "S" and not s.spell_ok(i, c.cost):
            continue
        if c.kind == "G" and s.has(1 - i, "fujin"):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　Disアイ・チョイス：マナから {BY_KEY[best].name} をただで使う")
        free_play(s, i, best, "mana")


add("e_aichoice", "Disアイ・チョイス", 6, "WDN", power=3000, blocker=True,
    races=("cybercommand", "command", "distas"), pri=8, roles="blk rem trg",
    enter=e_aichoice,
    text="ブロッカー、スレイヤー（バトルした相手のクリーチャーを破壊する）。"
         "出た時、S・トリガーを持つカード1枚を自分のマナゾーンから選び、コストを支払わずに使ってもよい",
    source=SRC["e_aichoice"])
SLAYER.add("e_aichoice")


# ================================================================ 完璧妖精サエポヨX
def ca_saepoyo(s, i, k, cur):
    """各ターン1度、自分のスノーフェアリーを使うコストを1少なくする"""
    if cur <= 0 or "snow" not in BY_KEY[k].races:
        return cur
    p = s.P[i]
    if p.x.get("saepoyo_t") == s.turn:
        return cur
    if not any(z.k == "e_saepoyo" for z in p.board):
        return cur
    return cur - 1


def w_saepoyo(s, i, u):
    """スノーフェアリーが出たら、そのターンのコスト軽減は使い切ったものとする"""
    if u.c.kind != "C" or "snow" not in u.c.races:
        return
    if any(z.k == "e_saepoyo" and z is not u for z in s.P[i].board):
        s.P[i].x["saepoyo_t"] = s.turn


def ts_saepoyo(s, i, u):
    """ハイパー化：自分の他のクリーチャー1体をタップしてハイパーモードを解放する"""
    if u.hyper:
        return
    p = s.P[i]
    if not any(BY_KEY[k].kind == "C" and not BY_KEY[k].evo for k in p.mana):
        return
    oth = [z for z in p.board if z is not u and z.c.kind == "C" and not z.tap and not z.c.blocker]
    if not oth:
        return
    s.tap_cre(i, min(oth, key=s.val))
    u.hyper = True
    s.ev("　ハイパー化：他のクリーチャーを1体タップしてサエポヨXのハイパーモードを解放")


def acts_saepoyo(s, i, av, cv):
    """ハイパーモード中、各ターン1度、マナゾーンからクリーチャーを1体召喚してよい"""
    p = s.P[i]
    if s.manaexec(i) or p.x.get("saepoyo_cast") == s.turn:
        return []
    if not any(z.k == "e_saepoyo" and z.hyper for z in p.board):
        return []
    out = []
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if c.kind != "C" or (c.evo and not c.neo):
            continue
        n = s.ccost(i, k, av)
        if n <= av and (n == 0 or cv.issuperset(c.civ)) and s.fate(i, k, "mana", True) == "ok":
            out.append(("x:saepoyo", k, n))
    return out


def ap_saepoyo(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.mana:
        return
    p.x["saepoyo_cast"] = s.turn
    p.mused += a[2]
    s.take_mana(i, k)
    s.ev(f"サエポヨXの能力でマナから召喚：{BY_KEY[k].name}（{a[2]}マナ）")
    s.enter(i, k, "mana", True)


add("e_saepoyo", "完璧妖精サエポヨX", 2, "N", power=2000, races=("snow", "hyperbeast"), pri=5,
    roles="acc atk",
    costaura=ca_saepoyo, enterwatch=w_saepoyo, tstart=ts_saepoyo,
    freeacts=acts_saepoyo, actapply={"x:saepoyo": ap_saepoyo},
    brkx=lambda s, i, u: 1,
    text="各ターン1度、自分のスノーフェアリーを使うコストを1少なくしてもよい（0未満にはならない）。"
         "ハイパー化：自分の他のクリーチャー1体をタップして、次の自分のターンのはじめまで"
         "ハイパーモードを解放する（ハイパーモード中はパワー5000）。"
         "ハイパーモード中、各ターン1度、自分のマナゾーンからクリーチャー1体を召喚してもよい",
    source=SRC["e_saepoyo"])
E.HYPER_POW["e_saepoyo"] = 3000


# ================================================================ 逆転の剣スカイソード
def e_skysword(s, i, u):
    t = s.target(i)
    if t is not None:
        move(s, i, t, "mana")
    n = len(s.P[i].mana)
    s.revive(i, lambda c: c.cost < n, "mana")


add("e_skysword", "逆転の剣スカイソード", 10, "N", power=5000, trig=True, races=("beastfolk",), pri=9,
    roles="rem trg acc fin",
    enter=e_skysword,
    text="S・トリガー。出た時、相手のクリーチャー1体を選び、持ち主のマナゾーンに置いてもよい。"
         "その後、自分のマナゾーンにあるカードの枚数よりコストが小さいクリーチャー1体を、"
         "自分のマナゾーンから出してもよい",
    source=SRC["e_skysword"])


# ================================================================ 秩序の意志（S・バック［闇］・封印）
def sp_chitsujo(s, i):
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　{t.c.name} に封印を1つ付ける")
    s.seal(1 - i, t, 1)


def rep_chitsujo(s, ai, di, broken):
    """S・バック［闇］：闇のカードがシールドから手札に加わる時、それを捨てて秩序の意志をただで唱える

    broken（ブレイクしたシールドの並び）から、捨てる1枚だけを取り除いて墓地に置き、False を返す。
    残りはエンジンがそのまま手札に加え、S・トリガーも通常どおり働く。
    """
    d = s.P[di]
    if "e_chitsujo" not in d.hand or not broken:
        return False
    idx = next((j for j, (k, up) in enumerate(broken) if "D" in BY_KEY[k].civ and not up), None)
    if idx is None or not s.spell_ok(di, 4):
        return False
    k = broken.pop(idx)[0]
    s.ev(f"　S・バック［闇］：{BY_KEY[k].name} を捨てて秩序の意志を唱える")
    s.grave_put(di, k)
    d.hand.remove("e_chitsujo")
    s.trig[di] += 1
    s.cast(di, "e_chitsujo")
    return False


add("e_chitsujo", "秩序の意志", 4, "D", kind="S", pri=5, roles="rem dis",
    spell=sp_chitsujo, breakrep=rep_chitsujo,
    text="S・バック［闇］：闇のカードを自分のシールドゾーンから手札に加える時、そのカードを捨てて、"
         "この呪文をコストを支払わずに唱えてもよい。"
         "相手のクリーチャー1体を選び、封印を1つ付ける（封印されたクリーチャーはバトルゾーンにないものとして扱い、"
         "文明の合うコマンドが出ると外れる）",
    source=SRC["e_chitsujo"])


# ================================================================ 星門の精霊アケルナル／スターゲイズ・ゲート
def _light_blocker_out(s, i):
    """光のブロッカーを持つ進化でないクリーチャー1体を手札から出す"""
    return _put_from_hand(s, i, lambda c: c.blocker and "L" in c.civ and not c.evo)


add("e_akernal", "星門の精霊アケルナル / スターゲイズ・ゲート", 9, "L", power=10500, brk=2, blocker=True,
    races=("angelcommand", "command"), twin=(5, "L", False), pri=10, roles="blk fin",
    tend=lambda s, i, u: _light_blocker_out(s, i), spell=lambda s, i: _light_blocker_out(s, i),
    text="クリーチャー側：ブロッカー、W・ブレイカー。自分のターンの終わりに、"
         "光のブロッカーを持つ進化でないクリーチャー1体を自分の手札から出してもよい。"
         "呪文側「スターゲイズ・ゲート」（コスト5・光）：光のブロッカーを持つ進化でないクリーチャー1体を"
         "自分の手札から出す",
    source=SRC["e_akernal"])


# ================================================================ 爆藍月 Drache der'Zen
def e_drachezen(s, i, u):
    """出た時、コスト5以下の呪文1枚を手札か墓地からただで唱える（唱えた後は山札の下へ）"""
    p = s.P[i]
    best, bv, src = None, -1, None
    for zone, zn in ((p.hand, "hand"), (p.grave, "grave")):
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if c.kind != "S" or c.cost > 5 or not s.spell_ok(i, c.cost):
                continue
            if E.PRI[k] > bv:
                best, bv, src = k, E.PRI[k], zn
    if best is None:
        return
    (p.hand if src == "hand" else p.grave).remove(best)
    s.ev(f"　Drache der'Zen：{'墓地' if src == 'grave' else '手札'}の {BY_KEY[best].name} をただで唱える")
    s.cast(i, best)
    if p.grave and p.grave[-1] == best:
        p.grave.pop()
        p.deck.insert(0, best)
        s.ev(f"　{BY_KEY[best].name} は墓地のかわりに山札の下へ")


add("e_drachezen", "爆藍月 Drache der'Zen", 7, "W", power=5000, races=("magic", "command", "dragon"), pri=9,
    roles="rem draw acc",
    enter=e_drachezen, costx=he_costx("e_drachezen"), payx=he_payx("e_drachezen"),
    text="ハイパーエナジー：このクリーチャーを召喚する時、コストが互いに異なる自分のアンタップしている"
         "クリーチャーを好きな数タップしてよい。1体タップするごとに召喚コストが2少なくなる（0未満にはならない）。"
         "出た時、コスト5以下の呪文1枚を自分の手札または墓地からコストを支払わずに唱えてもよい。"
         "その呪文は、唱えた後、墓地に置くかわりに山札の下に置く",
    source=SRC["e_drachezen"])


# ================================================================ エメラル
def e_emeral(s, i, u):
    """出た時、手札を1枚裏向きの新しいシールドにし、そうしたら自分のシールド1つを手札に戻す"""
    p = s.P[i]
    if not p.hand:
        return
    k = min(p.hand, key=E.PRI.get)
    p.hand.remove(k)
    if not s.add_shield(i, k):
        p.hand.append(k)
        return
    s.ev(f"　エメラル：手札の {BY_KEY[k].name} を裏向きのシールドとして置いた")
    new = len(p.sh) - 1                     # いま置いたシールドは戻さない
    cands = [j for j, (kk, up) in enumerate(p.sh) if not up and j != new]
    if not cands:
        return
    j = max(cands, key=lambda j: E.PRI[p.sh[j][0]])
    kk = p.sh.pop(j)[0]
    p.hand.append(kk)
    s.shield_left()
    s.ev(f"　エメラル：シールドの {BY_KEY[kk].name} を手札に戻した（S・トリガーは使えない）")


add("e_emeral", "エメラル", 2, "W", power=1000, races=("cyberlord",), pri=4, roles="shd draw",
    enter=e_emeral,
    text="出た時、自分の手札を1枚、裏向きにして新しいシールドとして置いてもよい。"
         "そうしたら、自分のシールドを1つ選び、持ち主の手札に戻す（そのS・トリガーは使えない）",
    source=SRC["e_emeral"])


# ================================================================ 水晶の祈り／クリスタル・ドゥーム
def sp_suisho(s, i):
    """プレイヤーを1人選ぶ（自分を選ぶ）。3枚引き、手札を2枚選んで捨てる"""
    s.draw(i, 3)
    for _ in range(2):
        if not s.P[i].hand:
            break
        discard_choice(s, i)
    s.ev("　水晶の祈り：3枚引いて手札を2枚捨てた")


def acts_suisho(s, i, av, cv):
    """ゼニス呪文側「クリスタル・ドゥーム」（コスト11）"""
    p = s.P[i]
    if "e_suisho" not in p.hand or av < 11 or "W" not in cv or not s.spell_ok(i, 11):
        return []
    return [("x:crystal", 11)]


def ap_suisho(s, a):
    i = s.tp
    p = s.P[i]
    if "e_suisho" not in p.hand:
        return
    p.hand.remove("e_suisho")
    p.mused += a[1]
    s.ev("呪文：クリスタル・ドゥーム（11マナ）")
    p.spl += 1
    s.first_play(i, 11)
    prev = s.spc
    s.spc = 11
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, "e_suisho")
    s.draw(i, 3)
    for _ in range(8):
        got = None
        for k in sorted(set(p.hand)):
            c = BY_KEY[k]
            if c.kind != "C" or (c.evo and not c.neo):
                continue
            if not ("unknown" in c.races or "zenith" in c.races):
                continue
            if s.fate(i, k, "hand", True) == "ok":
                got = k
                break
        if got is None:
            break
        p.hand.remove(got)
        s.ev(f"　クリスタル・ドゥーム：{BY_KEY[got].name} をただで召喚")
        s.enter(i, got, "hand", True)
    s.spc = prev
    s.grave_put(i, "e_suisho")
    s.noncre(i)


add("e_suisho", "水晶の祈り / クリスタル・ドゥーム", 3, "W", kind="S", pri=5, roles="draw dis fin",
    spell=sp_suisho, freeacts=acts_suisho, actapply={"x:crystal": ap_suisho},
    text="呪文。プレイヤーを1人選ぶ。そのプレイヤーは3枚引き、その後、手札を2枚選んで捨てる。"
         "もう一方の面「クリスタル・ドゥーム」（コスト11・水のゼニス呪文）：3枚引き、"
         "自分の手札からアンノウンまたはゼニスのクリーチャーを好きな数、コストを支払わずに召喚する",
    note="「自分のマナゾーンのカード1枚を裏向きにしてもよい」は、マナゾーンの「裏向き」という状態（MANAFACE）が"
         "エンジンにないため省いた。またカードプールにアンノウン・ゼニスのクリーチャーがないため、"
         "クリスタル・ドゥームの召喚部分は実装してあるが現状は対象がない（エンジンのせいではない）",
    status="partial", source=SRC["e_suisho"])
