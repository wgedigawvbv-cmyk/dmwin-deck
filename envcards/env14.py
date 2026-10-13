"""cardspec4.json の27枚（「覇帝なき侵略 レッドゾーンF」「セイレーン・コンチェルト」は既に実装済みなので除く）

  カードに書かれている能力を1つずつそのまま実装した。どれを選ぶか・任意効果を使うかは、
  このシミュレーター共通の決まり（相手からは重要度PRIの高いもの、自分からは低いもの）で機械的に決めている。
  dmwiki で本文を確かめたカード：アシステスト・インコッピ（光のアーマード・ファイアー・バードで合っていた）、
  聖カオスマントラ（ニンジャ・チェンジ5）、地龍仙ロマネアース（ガードマン・T・ブレイカー）、～邪眼帝～（G-NEO進化）、
  コッコ・武・ルピア（選んだ枚数以下のコスト）、マクスハト（サイバー・メクレイド5）。
  cardspec4.json の記述は、この6枚についてはどれも正しかった。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, opp_all
from envcards.env0 import guardman, race_like

W = "https://dmwiki.net/"
U_RELIFE = W + ("%E3%80%8A%E3%83%95%E3%82%A7%E3%82%A2%E3%83%AA%E3%83%BC%E3%83%BB"
                "Re%EF%BC%9A%E3%83%A9%E3%82%A4%E3%83%95%E3%80%8B")
U_SOUGETSU = W + ("%E3%80%8A%E5%B9%BB%E7%B7%91%E3%81%AE%E5%8F%8C%E6%9C%88%EF%BC%8F"
                  "%E6%AF%8D%E3%81%AA%E3%82%8B%E6%98%9F%E5%9F%9F%E3%80%8B")
U_ROMANE = W + ("%E3%80%8A%E5%9C%B0%E9%BE%8D%E4%BB%99%E3%83%AD%E3%83%9E%E3%83%8D%E3%82%A2%E3%83%BC%E3%82%B9%EF%BC%8F"
                "%E4%BB%99%E3%81%AA%E3%82%8B%E5%A4%A7%E5%9C%B0%E3%80%8B")


# ================================================================ 共通の小道具
def _top(s, i, n):
    """山札の上から n 枚を取り出す（山札を切らさないように1枚は残す）"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    if n <= 0:
        return []
    return [p.deck.pop() for _ in range(n)]


def _pick(cards, p):
    """手の内で一番うれしい1枚（同じ札がすでに手札にあれば下げる）"""
    return max(cards, key=lambda k: E.PRI[k] - 3 * p.hand.count(k))


def _put_cre(s, i, src, pred):
    """手札・墓地・マナから、条件に合う（進化でない）クリーチャーを1体コストを支払わずに出す"""
    p = s.P[i]
    zone = {"hand": p.hand, "grave": p.grave, "mana": p.mana}[src]
    best, bv = None, -1
    for k in sorted(set(zone)):
        c = BY_KEY[k]
        if c.kind != "C" or (c.evo and not c.neo) or not pred(c):
            continue
        if E.PRI[k] > bv and s.fate(i, k, src, False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None or best not in zone:
        return False
    if src == "mana":
        s.take_mana(i, best)
    else:
        zone.remove(best)
    s.ev(f"　{BY_KEY[best].name} を出す")
    s.enter(i, best, src, False)
    return True


def _battle_best(s, i):
    """自分のクリーチャー1体と相手のクリーチャー1体をバトルさせる（勝てる相手がいる時だけ）"""
    mine = [z for z in s.P[i].board if z.c.kind == "C"]
    if not mine:
        return False
    au = max(mine, key=lambda z: s.power(i, z, True))
    ap = s.power(i, au, True)
    best, bv = None, -1
    for t in opp_all(s, i):
        if s.power(1 - i, t) <= ap and E.PRI[t.k] > bv:
            best, bv = t, E.PRI[t.k]
    if best is None:
        return False
    s.ev(f"　{au.c.name} と {best.c.name} をバトルさせる")
    s.battle(i, au, 1 - i, best)
    return True


def _self_break(s, i, n=1):
    """自分のシールドを n つブレイクする（S・トリガーは使える）"""
    if s.P[i].sh:
        s.break_sh(1 - i, n)


# ================================================================ 天災 デドダム
def e_dedodamu(s, i, u):
    p = s.P[i]
    top = _top(s, i, 3)
    if not top:
        return
    k = _pick(top, p)
    top.remove(k)
    p.hand.append(k)
    if top:
        k2 = max(top, key=E.PRI.get)        # 残り2枚のうち使えるほうをマナへ、もう1枚は墓地へ
        top.remove(k2)
        s.add_mana(i, k2, src="deck")
    for x in top:
        s.grave_put(i, x)


add("e_dedodamu", "天災 デドダム", 3, "WDN", power=3000, races=("trinitycommand", "command", "invader"),
    pri=6, roles="draw acc", enter=e_dedodamu,
    text="出た時、自分の山札の上から3枚を見る。そのうち1枚を手札に、1枚をマナゾーンに、残り1枚を墓地に置く",
    source=W + "天災 デドダム")


# ================================================================ ブレイン・スラッシュ
def sp_brainslash(s, i):
    p = s.P[i]
    civ = set()
    for z in p.board:
        if z.c.kind in "CT":
            civ |= set(z.c.civ)
    both = {"W", "D"} <= civ                # 自分のクリーチャー・タマシードに水と闇がそろえば両方選べる
    can = any(BY_KEY[k].kind == "C" and not BY_KEY[k].evo and BY_KEY[k].cost <= 8 for k in p.grave)
    if both or not can:
        s.draw(i, 3)
        if p.hand:
            s.discard(i, min(p.hand, key=E.PRI.get))
    if both or can:
        s.revive(i, lambda c: c.cost <= 8)


add("e_brainslash", "ブレイン・スラッシュ", 6, "WD", kind="S", trig=True, pri=7, roles="draw trg",
    spell=sp_brainslash,
    text="S・トリガー。唱えた時、次のうち1つを選ぶ。自分のクリーチャーとタマシードに水と闇の両方があれば、両方選ぶ。"
         "(1)3枚引いて、手札を1枚捨てる (2)自分の墓地からコスト8以下のクリーチャー1体を出す",
    source=W + "ブレイン・スラッシュ")


# ================================================================ マジシャン・ルピア
def e_magicianlupia(s, i, u):
    p = s.P[i]
    if not p.hand:
        s.draw(i)
        return
    k = min(p.hand, key=lambda x: E.PRI[x] - (3 if "firebird" in BY_KEY[x].races else 0))
    fb = "firebird" in BY_KEY[k].races
    s.discard(i, k)
    s.draw(i, 2 if fb else 1)


add("e_magicianlupia", "マジシャン・ルピア", 2, "F", power=1000, races=("armored", "firebird"), pri=4,
    roles="draw", enter=e_magicianlupia,
    text="出た時、自分の手札を1枚捨てる。その後1枚引く。捨てたカードがファイアー・バードなら、もう1枚引く",
    source=W + "マジシャン・ルピア")


# ================================================================ 宝魂剣と獄門盾の決断
def tg_houkonken(s, di, k):
    """自分のパワー5000以上のクリーチャーがあれば、シールドゾーンにあるこの呪文はS・トリガーを得る"""
    return k == "e_houkonken" and any(z.c.kind == "C" and s.power(di, z) >= 5000 for z in s.P[di].board)


def sp_houkonken(s, i):
    for _ in range(2):                      # 次のうちから2回選ぶ（同じものを選んでもよい）
        if s.over or s.stop:
            return
        if _battle_best(s, i):
            continue
        if _put_cre(s, i, "hand", lambda c: c.cost <= 3) or _put_cre(s, i, "grave", lambda c: c.cost <= 3):
            continue
        _opp_break(s, i)


def _opp_break(s, i):
    if s.P[1 - i].sh:
        s.break_sh(i, 1)


add("e_houkonken", "宝魂剣と獄門盾の決断", 3, "LDF", kind="S", pri=5, roles="rem atk trg",
    spell=sp_houkonken, trigok=tg_houkonken,
    text="自分のパワー5000以上のクリーチャーがあれば、この呪文はシールドゾーンにある時S・トリガーを得る。"
         "唱えた時、次のうちから2回選ぶ（同じものを選んでもよい）。(1)コスト3以下のクリーチャー1体を手札か墓地から出す "
         "(2)クリーチャー2体を選び、バトルさせる (3)相手のシールドを1つブレイクする",
    source=W + "宝魂剣と獄門盾の決断")


# ================================================================ 虚ト成リシ古ノ蛇神ノ咆哮
def sp_jashinhoukou(s, i):
    p = s.P[i]
    if p.hand:
        s.discard(i, min(p.hand, key=E.PRI.get))
    t = s.target(i, lambda z: s.power(1 - i, z) <= 9000)
    if t is not None:
        destroy(s, i, t)
    else:
        s.draw(i, 2)


add("e_jashinhoukou", "虚ト成リシ古ノ蛇神ノ咆哮", 2, "F", kind="S", trig=True, pri=4, roles="rem draw trg",
    spell=sp_jashinhoukou,
    text="S・トリガー。唱えた時、自分の手札を1枚捨てる。その後、次のうち1つを選ぶ。"
         "(1)2枚引く (2)相手のパワー9000以下のクリーチャー1体を破壊する",
    source=W + "虚ト成リシ古ノ蛇神ノ咆哮")


# ================================================================ ～邪眼帝～
def e_jagantei(s, i, u):
    s.mill(i, 2)
    s.revive(i, lambda c: c.cost <= 5)


def t_jagantei(s, i, u):
    """自分のターンの終わりに、タップしていれば自分の他のクリーチャー1体を手札に戻し、同名のものを手札から出せる"""
    if not u.tap:
        return
    p = s.P[i]
    oth = [z for z in p.board if z is not u and z.c.kind == "C"]
    if not oth:
        return
    z = min(oth, key=lambda x: E.PRI[x.k] + len(x.under))
    k = z.k
    if not s.leave(i, z, "hand"):
        return
    s.ev(f"　～邪眼帝～：{BY_KEY[k].name} を手札に戻す")
    if k in p.hand and s.fate(i, k, "hand", False) == "ok":
        p.hand.remove(k)
        s.enter(i, k, "hand", False)


add("e_jagantei", "～邪眼帝～", 6, "LWD", power=7500, brk=2, blocker=True, evo="LWD", neo=True, gneo=True,
    races=("dragonzombie", "darklord", "steamknight"), pri=9, roles="blk atk",
    enter=e_jagantei, tend=t_jagantei,
    text="G・NEO進化（自分の光・水・闇のクリーチャー1体の上に置いてもよいし、普通に召喚してもよい）。"
         "ブロッカー、W・ブレイカー。出た時、自分の山札の上から2枚を墓地に置き、その後、自分の墓地から"
         "コスト5以下のクリーチャー1体を出してもよい。自分のターンの終わりに、このクリーチャーがタップしていれば、"
         "自分の他のクリーチャー1体を手札に戻してもよい。そうしたら、それと同じ名前のクリーチャー1体を手札から出してもよい",
    source=W + "～邪眼帝～")


# ================================================================ ～そして覚醒へ…～
def _kakusei_ok(k):
    """～そして覚醒へ…～がS・トリガーを与えるカードか（コスト9以下の呪文、またはナイト）"""
    c = BY_KEY[k]
    return (c.kind == "S" and c.cost <= 9) or "knight" in c.races


def _kakusei_use(s, di, k):
    """与えられたS・トリガーで使う"""
    d = s.P[di]
    c = BY_KEY[k]
    if c.kind == "S":
        if not s.spell_ok(di, c.cost):
            return
        d.hand.remove(k)
        s.trig[di] += 1
        s.ev(f"　S・トリガー（～そして覚醒へ…～）：{c.name}")
        s.cast(di, k)
    elif c.kind == "C":
        if s.fate(di, k, "hand", True) != "ok":
            return
        d.hand.remove(k)
        s.trig[di] += 1
        s.ev(f"　S・トリガー（～そして覚醒へ…～）：{c.name}")
        s.enter(di, k, "hand", True)
    elif c.kind == "T":
        if d.ban == c.cost:
            return
        d.hand.remove(k)
        s.trig[di] += 1
        s.ev(f"　S・トリガー（～そして覚醒へ…～）：{c.name}")
        s.place_tama(di, k)


def rep_kakusei(s, ai, di, broken):
    """自分のシールドゾーンのコスト9以下の呪文とナイトにS・トリガーを与える（ブレイクの処理を引き受ける）"""
    if not s.has(di, "e_kakuseihe"):
        return False
    d = s.P[di]
    for k, up in broken:
        if up and BY_KEY[k].kind == "G":
            s.grave_put(di, k)
        else:
            d.hand.append(k)
    for k, up in broken:
        if s.over or s.stop:
            break
        if up or k not in d.hand:
            continue
        s.trigger(di, k)                      # もともと持っているS・トリガー・G・ストライク
        if k in d.hand and _kakusei_ok(k) and s.has(di, "e_kakuseihe"):
            _kakusei_use(s, di, k)
    return True


def e_kakuseihe(s, i, u):
    """出た時または攻撃する時：山札の上1枚をシールドにし、その後自分のシールドを1つブレイクしてもよい"""
    s.add_shield(i)
    if len(s.P[i].sh) >= 3:                   # シールドが3つ以上あるなら割って手札とS・トリガーに変える
        s.ev("　～そして覚醒へ…～：自分のシールドを1つブレイクする")
        _self_break(s, i, 1)


add("e_kakuseihe", "～そして覚醒へ…～", 6, "LWD", power=8500, brk=2, evo="LWD", neo=True, gneo=True,
    races=("armoreddragon", "dragonzombie", "steamknight"), pri=9, roles="shd atk trg",
    enter=e_kakuseihe, attack=e_kakuseihe, breakrep=rep_kakusei,
    text="G・NEO進化（自分の光・水・闇のクリーチャー1体の上に置いてもよいし、普通に召喚してもよい）。W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、自分の山札の上から1枚を新しいシールドとして置く。"
         "その後、このクリーチャーは自分のシールドを1つブレイクしてもよい。"
         "自分のシールドゾーンにあるコスト9以下の呪文とナイトのカードすべてにS・トリガーを与える",
    source=W + "～そして覚醒へ…～")


# ================================================================ 激烈元気モーニンジョー
def e_morninjo(s, i, u):
    _put_cre(s, i, "hand", lambda c: "dreammate" in c.races)


add("e_morninjo", "激烈元気モーニンジョー", 5, "N", power=1000, trig=True, races=("dreammate",), pri=6,
    roles="trg atk", enter=e_morninjo,
    text="S・トリガー。出た時、自分の手札からドリームメイト・クリーチャー1体を出してもよい",
    source=W + "激烈元気モーニンジョー")


# ================================================================ ベイB セガーレ
def fx_segare(s, owner, u, i, k, src, summon, res):
    """相手が、自分のマナゾーンの枚数より大きいコストのクリーチャーを出す時、かわりにマナゾーンに置かせる"""
    if i == owner or res != "ok":
        return res
    c = BY_KEY[k]
    if c.kind == "C" and c.cost > len(s.P[i].mana):
        u.x["fired"] = 1
        return "mana"
    return res


def t_segare(s, i, u):
    if u.x.get("fired"):
        u.x["fired"] = 0
        s.ev("　ベイB セガーレ：自分をマナゾーンに置く")
        s.leave(i, u, "mana")


add("e_segare", "ベイB セガーレ", 1, "N", power=6000, noatk=True, races=("milkboy",), pri=4, roles="dis",
    fatex=fx_segare, tstart=t_segare, status="partial",
    text="このクリーチャーは攻撃できない。相手が、相手自身のマナゾーンのカードの枚数より大きいコストを持つ"
         "クリーチャーを出す時、かわりにそれを相手のマナゾーンに置く。その後、このクリーチャーを自分のマナゾーンに置く",
    note="「その後、このクリーチャーを自分のマナゾーンに置く」は、エンジンの置き換えの差し込み口（fatex）が"
         "打てる手を数える時の試し打ちでも呼ばれ、本番と試し打ちを区別する引数（FATESPEC）がないため、"
         "その場では動かせない。置き換えが起きた次の自分のターンのはじめに自分をマナゾーンに置く形にした"
         "（1回しか止められない点は同じ）。この代用のため、相手が実際には出さずに「出せるか」を数えただけでも"
         "印が立ち、マナゾーンに行ってしまうことがある",
    source=W + "ベイB セガーレ")


# ================================================================ 料理犬のヴィヤンドゥ
def _viandu_win(s, i):
    """バトルに勝った時：山札の上1枚をマナに置き、それがドリームメイトなら出してもよい"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    k = p.deck.pop()
    s.add_mana(i, k, src="deck")
    c = BY_KEY[k]
    s.ev(f"　料理犬のヴィヤンドゥ：{c.name} をマナゾーンへ")
    if c.kind == "C" and "dreammate" in c.races and not (c.evo and not c.neo) and k in p.mana:
        if s.fate(i, k, "mana", False) == "ok":
            s.take_mana(i, k)
            s.enter(i, k, "mana", False)


def bf_viandu(s, ai, au, di, du, a_dies, d_dies):
    if au.k == "e_viandu" and d_dies and not a_dies:
        _viandu_win(s, ai)
    if du.k == "e_viandu" and a_dies and not d_dies:
        _viandu_win(s, di)
    return a_dies, d_dies


def acts_viandu(s, i, av, cv):
    """ハイパー化：メインステップ中に自分の他のクリーチャー1体をタップしてハイパーモードにする"""
    for u in s.P[i].board:
        if u.k == "e_viandu" and not u.hyper:
            if any(z is not u and z.c.kind == "C" and not z.tap for z in s.P[i].board):
                return [("x:hypvia", u.uid)]
    return []


def ap_viandu(s, a):
    i = s.tp
    p = s.P[i]
    u = next((z for z in p.board if z.uid == a[1] and z.k == "e_viandu"), None)
    if u is None or u.hyper:
        return
    oth = [z for z in p.board if z is not u and z.c.kind == "C" and not z.tap]
    if not oth:
        return
    s.tap_cre(i, min(oth, key=s.val))
    u.hyper = True
    s.ev("ハイパー化：料理犬のヴィヤンドゥ（パワー6000・W・ブレイカー）")


add("e_viandu", "料理犬のヴィヤンドゥ", 3, "N", power=4000, mach=True, races=("dreammate", "hyperbeast"), pri=5,
    roles="acc atk", battlefx=bf_viandu, freeacts=acts_viandu, actapply={"x:hypvia": ap_viandu},
    text="マッハファイター。ハイパー化（自分のメインステップ中、自分の他のクリーチャー1体をタップして、"
         "次の自分のターンのはじめまでハイパーモードになれる。ハイパーモード中はパワー6000でW・ブレイカー）。"
         "このクリーチャーがバトルに勝った時、自分の山札の上から1枚をマナゾーンに置く。"
         "そのカードがドリームメイトなら、マナゾーンから出してもよい",
    source=W + "料理犬のヴィヤンドゥ")
E.HYPER_POW["e_viandu"] = 2000


# ================================================================ アシステスト・インコッピ
def e_incoppi(s, i, u):
    if any(z is not u and race_like(z.c, "armored") for z in s.P[i].board):
        s.draw(i)


def ca_incoppi(s, i, k, cur):
    if cur > 0 and race_like(BY_KEY[k], "armored") and s.has(i, "e_incoppi"):
        return max(0, cur - 1)
    return cur


def lr_incoppi(s, i, u, dest, destroy_):
    """ウルトラ・セイバー：アーマード。自分のアーマードが破壊される時、かわりにこれを破壊してもよい"""
    if not destroy_ or not race_like(u.c, "armored"):
        return False
    me = next((z for z in s.P[i].board if z.k == "e_incoppi" and z is not u and not z.x.get("usav")), None)
    if me is None or E.PRI[u.k] < E.PRI["e_incoppi"]:
        return False
    me.x["usav"] = 1
    s.ev(f"　ウルトラ・セイバー：アシステスト・インコッピを破壊して {u.c.name} を守る")
    s.leave(i, me, "grave", destroy=True)
    return True


add("e_incoppi", "アシステスト・インコッピ", 3, "L", power=2000, races=("armored", "firebird"), pri=4,
    roles="draw acc", enter=e_incoppi, costaura=ca_incoppi, leaverep=lr_incoppi,
    text="出た時、自分の他のアーマードがあれば1枚引く。自分のアーマードを召喚するコストを1少なくする"
         "（0より少なくはならない）。ウルトラ・セイバー：アーマード（自分のアーマードが破壊される時、"
         "かわりにこのクリーチャーを破壊してもよい。守る値打ちのあるものだけ守る）",
    source=W + "アシステスト・インコッピ")


# ================================================================ バッドドッグ・マニアクス
def sp_baddog(s, i):
    mine = [z for z in s.P[i].board if z.c.kind == "C"]
    if mine:
        z = min(mine, key=lambda x: E.PRI[x.k] + len(x.under))
        s.leave(i, z, "grave", destroy=True)
    t = s.target(i, lambda z: s.power(1 - i, z) <= 5000)
    if t is not None:
        destroy(s, i, t)


add("e_baddog", "バッドドッグ・マニアクス", 1, "F", kind="S", trig=True, pri=3, roles="rem trg", spell=sp_baddog,
    text="S・トリガー。唱えた時、自分のクリーチャー1体を選んで破壊する。"
         "その後、相手のパワー5000以下のクリーチャー1体を選んで破壊する",
    source=W + "バッドドッグ・マニアクス")


# ================================================================ 無頼BEN-K1000
def e_benk1000(s, i, u):
    p = s.P[i]
    top = _top(s, i, 3)
    if not top:
        return
    k = max(top, key=E.PRI.get)
    top.remove(k)
    if not s.add_shield(i, k):
        s.add_mana(i, k, src="deck")
    if top:
        k2 = max(top, key=E.PRI.get)
        top.remove(k2)
        s.add_mana(i, k2, True, src="deck")
    for x in top:
        u.under.append(x)


add("e_benk1000", "無頼BEN-K1000", 3, "LFN", power=3000, evo="LFN", neo=True, races=("dreammate", "technosamurai"),
    pri=5, roles="shd acc", enter=e_benk1000,
    text="NEO進化（自分の光・火・自然のクリーチャー1体の上に置いてもよいし、普通に召喚してもよい）。"
         "出た時、自分の山札の上から3枚を見て、1枚を新しいシールドとして置き、"
         "1枚をタップしてマナゾーンに置き、残り1枚をこのクリーチャーの下に置く",
    source=W + "無頼BEN-K1000")


# ================================================================ 友情地龍 ルピア・ターン
def e_lupiaturn(s, i, u):
    p = s.P[i]
    s.ramp(i, 2, True)
    if p.mana:
        k = min(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        p.deck.append(k)
        s.ev(f"　友情地龍 ルピア・ターン：マナから {BY_KEY[k].name} を山札の上へ")


add("e_lupiaturn", "友情地龍 ルピア・ターン", 3, "FN", power=4000, races=("firebird", "greencommanddragon", "command", "dragon"),
    pri=5, roles="acc", enter=e_lupiaturn,
    text="出た時、自分の山札の上から2枚をタップしてマナゾーンに置く。その後、自分のマナゾーンから1枚を山札の上に置く",
    source=W + "友情地龍 ルピア・ターン")


# ================================================================ マクスハト
def e_makusuhato(s, i, u):
    """出た時、自分の他のエレメント1つを手札に戻してよい。そうしたらサイバー・メクレイド5"""
    p = s.P[i]
    oth = [z for z in p.board if z is not u and z.c.kind in "CTXG"]
    if not oth:
        return
    z = min(oth, key=lambda x: E.PRI[x.k] + len(x.under))
    if not s.leave(i, z, "hand"):
        return
    s.ev(f"　マクスハト：{z.c.name} を手札に戻す → サイバー・メクレイド5")
    top = _top(s, i, 3)
    if not top:
        return
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.cost <= 5 and race_like(c, "cyber") and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        p.hand.append(best)
        if not free_play(s, i, best, "hand") and best in p.hand:
            p.hand.remove(best)
            top.append(best)
    for x in top:
        p.deck.insert(0, x)


add("e_makusuhato", "マクスハト", 3, "W", power=4000, races=("cyberlord",), pri=5, roles="acc draw",
    enter=e_makusuhato,
    text="出た時、自分の他のエレメント（クリーチャー・タマシードなど）1つを手札に戻してもよい。"
         "そうしたら、サイバー・メクレイド5（自分の山札の上から3枚を見て、その中からコスト5以下のサイバー・カード1枚を"
         "コストを支払わずに使ってもよい。残りを山札の下に置く）",
    source=W + "マクスハト")


# ================================================================ フェアリー・Re:ライフ
def sp_relife(s, i):
    s.ramp(i, 1, True)


add("e_relife", "フェアリー・Re:ライフ", 2, "N", kind="S", gs=True, pri=3, roles="acc trg", spell=sp_relife,
    text="G・ストライク（相手の攻撃時に手札から見せて、その攻撃をなかったことにできる）。"
         "唱えた時、自分の山札の上から1枚をタップしてマナゾーンに置く",
    source=U_RELIFE)


# ================================================================ 光開の精霊サイフォゲート
def e_saifogate(s, i, u):
    _put_cre(s, i, "hand", lambda c: c.blocker and "L" in c.civ and not c.evo)


add("e_saifogate", "光開の精霊サイフォゲート", 6, "L", power=3500, trig=True, blocker=True,
    races=("angelcommand", "command"), pri=7, roles="blk trg", enter=e_saifogate,
    text="S・トリガー、ブロッカー。出た時、自分の手札から、ブロッカーを持つ光の進化ではないクリーチャー1体を出してもよい",
    source=W + "光開の精霊サイフォゲート")


# ================================================================ コッコ・武・ルピア
def e_kokkobu(s, i, u):
    """出た時または攻撃する時：プレイヤー1人の墓地のカードを好きな数、山札の下へ。その枚数以下のコストの相手1体を破壊"""
    p, o = s.P[i], s.P[1 - i]
    best = s.target(i)
    need = best.c.cost if best is not None else 0
    j = 1 - i if (len(o.grave) >= need or len(o.grave) >= len(p.grave)) else i
    z = s.P[j]
    n = len(z.grave)
    if n:
        cards = sorted(z.grave, key=E.PRI.get)
        del z.grave[:]
        for k in cards:
            z.deck.insert(0, k)
        s.ev(f"　コッコ・武・ルピア：プレイヤー{j} の墓地{n}枚を山札の下へ")
    t = s.target(i, lambda x: x.c.cost <= n)
    if t is not None:
        destroy(s, i, t)


add("e_kokkobu", "コッコ・武・ルピア", 3, "F", power=3000, races=("armored", "firebird"), pri=5, roles="rem atk dis",
    enter=e_kokkobu, attack=e_kokkobu,
    text="出た時または攻撃する時、プレイヤー1人の墓地にあるカードを好きな数選ぶ。その持ち主は選ばれたカードを"
         "好きな順序で山札の下に置く。その後、選ばれたカードの枚数以下のコストを持つ相手のクリーチャー1体を"
         "選んで破壊してもよい（墓地の枚数が多いほうのプレイヤーを選び、全部選ぶ）",
    source=W + "コッコ・武・ルピア")


# ================================================================ 光器アメリア
def e_ameria(s, i, u):
    s.add_shield(i)
    u.x["ame"] = s.turn


def t_ameria(s, i, u):
    """次の自分のターンのはじめに、自分のシールドを1つ手札に加える（S・トリガーは使えない）"""
    if not u.x.get("ame") or u.x["ame"] >= s.turn:
        return
    u.x["ame"] = 0
    p = s.P[i]
    j = next((j for j in range(len(p.sh) - 1, -1, -1) if not p.sh[j][1]), None)
    if j is None:
        return
    p.hand.append(p.sh.pop(j)[0])
    s.shield_left()
    s.ev("　光器アメリア：シールドを1つ手札に加えた（S・トリガーは使えない）")


add("e_ameria", "光器アメリア", 2, "L", power=500, races=("mechadelsol",), pri=3, roles="shd draw",
    enter=e_ameria, tstart=t_ameria,
    text="出た時、自分の山札の上から1枚を新しいシールドとして置く。"
         "次の自分のターンのはじめに、自分のシールドを1つ選んで手札に加える（そのS・トリガーは使えない）",
    source=W + "光器アメリア")


# ================================================================ クイーン・アマテラス
def e_amaterasu(s, i, u):
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.deck)):
        c = BY_KEY[k]
        if c.kind in "STGX" and c.cost <= 6 and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is None:
        return
    p.deck.remove(best)
    s.rng.shuffle(p.deck)
    p.hand.append(best)
    s.ev(f"　クイーン・アマテラス：山札から {BY_KEY[best].name} を手札に加えてただで使う")
    free_play(s, i, best, "hand")


add("e_amaterasu", "クイーン・アマテラス", 8, "W", power=7000, brk=2, races=("knight", "samurai", "origin"),
    pri=10, roles="draw fin", enter=e_amaterasu,
    text="W・ブレイカー。出た時、自分の山札を見て、その中からコスト6以下のクリーチャーでないカード1枚を手札に加え、"
         "山札をシャッフルする。その後、そのカードをコストを支払わずに使う",
    source=W + "クイーン・アマテラス")


# ================================================================ 幻緑の双月／母なる星域
def e_sougetsu(s, i, u):
    p = s.P[i]
    if not p.hand:
        return
    k = min(p.hand, key=E.PRI.get)
    p.hand.remove(k)
    s.add_mana(i, k, src="hand")
    s.ev(f"　幻緑の双月：手札から {BY_KEY[k].name} をマナゾーンへ")


def sp_hoshiiki(s, i):
    """母なる星域：自分の進化でないクリーチャー1体をマナに置き、マナの枚数以下のコストの進化クリーチャーをマナから出す"""
    p = s.P[i]
    cands = [z for z in p.board if z.c.kind == "C" and not z.c.evo]
    if not cands:
        return
    z = min(cands, key=lambda x: E.PRI[x.k] + len(x.under))
    if not s.leave(i, z, "mana"):
        return
    n = len(p.mana)
    best, bv = None, -1
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if c.kind == "C" and c.evo and c.cost <= n and E.PRI[k] > bv and s.fate(i, k, "mana", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None or best not in p.mana:
        return
    s.take_mana(i, best)
    s.ev(f"　母なる星域：マナから {BY_KEY[best].name} を出す")
    s.enter(i, best, "mana", False, on=s.evo_src(i, best))


add("e_sougetsu", "幻緑の双月", 2, "N", power=1000, races=("beastfolk",), twin=(3, "N", False), pri=4,
    roles="acc fin", enter=e_sougetsu, spell=sp_hoshiiki,
    text="【クリーチャー側 幻緑の双月】出た時、自分の手札を1枚マナゾーンに置いてもよい。"
         "【呪文側 母なる星域（コスト3・自然）】自分の進化ではないクリーチャー1体を選び、マナゾーンに置く。"
         "そうしたら、コストが自分のマナゾーンのカードの枚数以下の進化クリーチャー1体を、自分のマナゾーンから出す",
    note="母なる星域は殿堂入り（デッキに1枚）。マナから出す進化クリーチャーは、進化元があれば重ね、なければ単体で出す。"
         "デッキ1枚の上限は archetypes.LIMIT に書く必要があるが、そのファイルは担当外のため登録していない",
    source=U_SOUGETSU)


# ================================================================ 聖カオスマントラ
def e_chaosmantra(s, i, u):
    for z in s.P[1 - i].board:
        if z.c.kind == "C":
            s.tap_cre(1 - i, z)
    s.ev("　聖カオスマントラ：相手のクリーチャーをすべてタップ")


def w_chaosmantra(s, i, u):
    """相手のクリーチャーは出たターン攻撃できない"""
    if u.c.kind == "C" and any(z.k == "e_chaosmantra" for z in s.P[1 - i].board):
        u.lock = s.turn


def _ninja_change(s, di):
    """ニンジャ・チェンジ5：手札のこれと、自分のコスト5以上のメカかシノビ1体を入れ替える"""
    d = s.P[di]
    if "e_chaosmantra" not in d.hand:
        return False
    cands = [z for z in d.board if z.c.kind == "C" and z.c.cost >= 5
             and (race_like(z.c, "mecha") or "shinobi" in z.c.races)]
    if not cands or s.fate(di, "e_chaosmantra", "hand", False) != "ok":
        return False
    z = min(cands, key=lambda x: E.PRI[x.k] + len(x.under))
    j = d.board.index(z)
    d.hand.remove("e_chaosmantra")
    d.hand.append(z.k)
    d.hand.extend(z.under)
    nu = E.U("e_chaosmantra")
    nu.sick = False
    d.board[j] = nu
    d.ent += 1
    s.note("surface", di, nu.k)
    s.ev(f"　ニンジャ・チェンジ5：{z.c.name} と 聖カオスマントラ を入れ替える")
    s.trig[di] += 1
    e_chaosmantra(s, di, nu)
    for f in E.ENTERWATCH:
        if not s.over:
            f(s, di, nu)
    return True


def react_chaosmantra(s, di, au):
    """相手のクリーチャーが攻撃した時（react＝攻撃される側の誘発）"""
    return _ninja_change(s, di)


def bw_chaosmantra(s, i, u, b):
    """相手のクリーチャーがブロックした時（blockwatch＝攻撃している側の誘発）

    全体に効く差し込み口なので、手札にこのカードがある時だけ働く。
    「この攻撃中にニンジャ能力を使っていなければ」は、使うと手札から離れるので自然に満たされる
    （攻撃する時に react で入れ替わっていれば、ここでは手札にない）。"""
    if "e_chaosmantra" not in s.P[i].hand:
        return
    _ninja_change(s, i)


add("e_chaosmantra", "聖カオスマントラ", 7, "L", power=9500, brk=2, races=("mechadelstella", "shinobi"),
    pri=9, roles="dis atk fin", enter=e_chaosmantra, attack=e_chaosmantra, enterwatch=w_chaosmantra,
    react=react_chaosmantra, blockwatch=bw_chaosmantra,
    text="W・ブレイカー。ニンジャ・チェンジ5（相手のクリーチャーが攻撃またはブロックした時、"
         "この攻撃中に自分がニンジャ能力を使っていなければ、"
         "手札のこのクリーチャーと、自分のコスト5以上のメカまたはシノビのクリーチャー1体を"
         "入れ替えてもよい）。出た時または攻撃する時、相手のクリーチャーをすべてタップする。"
         "相手のクリーチャーは、出たターン攻撃できない",
    source=W + "聖カオスマントラ")


# ================================================================ 逆転の影ガレック
def e_gareck(s, i, u):
    """次のうちから3回選ぶ（同じものを選んでもよい）"""
    for left in range(3, 0, -1):
        if s.over:
            return
        t = s.target(i, lambda z: s.power(1 - i, z) <= 3000)
        if t is None and left >= 2:
            t = s.target(i, lambda z: s.power(1 - i, z) <= 3000 * left)
        if t is not None:
            t.pw -= 3000
            s.ev(f"　{t.c.name} はこのターン パワー-3000")
            if s.power(1 - i, t) <= 0:
                s.leave(1 - i, t, "grave", by_opp=True, destroy=True)
            continue
        if s.revive(i, lambda c: c.cost <= 3) is not None:
            continue
        s.mill(i, 3)


add("e_gareck", "逆転の影ガレック", 10, "D", power=5000, trig=True, races=("ghost",), pri=10,
    roles="rem trg fin", enter=e_gareck,
    text="S・トリガー。出た時、次のうちから3回選ぶ（同じものを選んでもよい）。"
         "(1)相手のクリーチャー1体のパワーをこのターン-3000する（パワー0以下になれば破壊される） "
         "(2)自分の山札の上から3枚を墓地に置く (3)自分の墓地からコスト3以下のクリーチャー1体を出す",
    note="殿堂入り（デッキに1枚）。デッキ1枚の上限は archetypes.LIMIT に書く必要があるが、そのファイルは担当外のため登録していない",
    source=W + "逆転の影ガレック")


# ================================================================ 地龍仙ロマネアース／仙なる大地
def e_romaneearth(s, i, u):
    s.ramp(i, 4, True)


def sp_sennaru(s, i):
    """仙なる大地：自分のクリーチャー1体をマナに置き、マナの枚数以下のコストのクリーチャーを手札から出す"""
    p = s.P[i]
    cands = [z for z in p.board if z.c.kind == "C"]
    if not cands:
        return
    z = min(cands, key=lambda x: E.PRI[x.k] + len(x.under))
    if not s.leave(i, z, "mana"):
        return
    s.ev(f"　仙なる大地：{z.c.name} をマナゾーンへ")
    _put_cre(s, i, "hand", lambda c: c.cost <= len(p.mana))


def t_romaneearth(s, i, u):
    """自分のターンの終わりに、呪文側をバトルゾーンに置いたままコストを支払わずに唱えてもよい"""
    if not s.spell_ok(i, 6):
        return
    p = s.P[i]
    p.spl += 1
    prev = s.spc
    s.spc = 6
    s.ev("　地龍仙ロマネアース：仙なる大地をコストを支払わずに唱える")
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, "e_romaneearth")
    sp_sennaru(s, i)
    s.spc = prev


add("e_romaneearth", "地龍仙ロマネアース", 8, "N", power=12000, brk=3, races=("earthdragon", "dragon"),
    twin=(6, "N", False), pri=11, roles="acc blk atk fin",
    enter=e_romaneearth, spell=sp_sennaru, tend=t_romaneearth, guard=guardman("e_romaneearth"),
    text="【クリーチャー側 地龍仙ロマネアース】ガードマン、T・ブレイカー。出た時、自分の山札の上から4枚までを"
         "タップしてマナゾーンに置く。自分のターンの終わりに、このカードの呪文側をバトルゾーンに置いたまま、"
         "コストを支払わずに唱えてもよい。"
         "【呪文側 仙なる大地（コスト6・自然）】自分のクリーチャー1体を選び、マナゾーンに置く。そうしたら、"
         "コストが自分のマナゾーンのカードの枚数以下のクリーチャー1体を自分の手札から出す",
    source=U_ROMANE)


# ================================================================ 超神羅星アポロヌス・ドラゲリオン
def e_apollonus(s, i, u):
    """メテオバーン：下のカード3枚を墓地に置いてもよい。そうしたら相手のシールドをすべてブレイクする"""
    if len(u.under) < 3:
        return
    for _ in range(3):
        s.grave_put(i, u.under.pop(0))
    s.ev("　メテオバーン：相手のシールドをすべてブレイクする")
    o = s.P[1 - i]
    if o.sh:
        s.break_sh(i, len(o.sh))


def cw_apollonus(s, i, u, by):
    """相手がこのクリーチャーを選んだ時、相手のマナゾーンのカード2枚を墓地に置く

    注意（エンジン側の不具合。2026-10-08 に見つけた）：`Game.legal_main` が《タッ・キュー》の
    無駄撃ち判定（`Game.takkyu_ok`）で `s.target()` を呼ぶため、**打てる手を数えるだけでも
    CHOSENWATCH が誘発する**（chosenwatch= を使う全カードに共通）。
    直すには `takkyu_ok` が `s.target()` を使わずに候補を数える形にする必要がある
    （engine3.py は担当外）。"""
    if u.k != "e_apollonus" or s.over:
        return
    o = s.P[by]
    for _ in range(2):
        if not o.mana:
            return
        k = max(o.mana, key=E.PRI.get)
        s.take_mana(by, k)
        s.grave_put(by, k)
        s.ev(f"　アポロヌス・ドラゲリオン：選ばれたので相手のマナの {BY_KEY[k].name} を墓地へ")


def pr_apollonus(deck, k):
    n = sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C" and BY_KEY[kk].evo)
    return None if n >= 4 else "進化元になる進化クリーチャーが4体いない"


add("e_apollonus", "超神羅星アポロヌス・ドラゲリオン", 6, "F", power=15000, brk=3, evo="X", races=("phoenix",),
    pri=12, roles="atk fin", enter=e_apollonus, playrule=pr_apollonus, chosenwatch=cw_apollonus,
    evox=lambda s, i, u: bool(u.c.evo),
    invade=lambda s, i, u: "F" in u.c.civ and bool(u.c.evo) and "dragon" in u.c.races,
    text="究極進化（自分の進化クリーチャー1体の上に置く）。T・ブレイカー。"
         "侵略［火の進化ドラゴン］（自分の火の進化ドラゴンが攻撃する時、手札のこのカードをその上に重ねて出せる）。"
         "出た時、メテオバーン：このクリーチャーの下のカードを3枚墓地に置いてもよい。"
         "そうしたら、このクリーチャーは相手のシールドをすべてブレイクする。"
         "相手がこのクリーチャーを選んだ時、相手のマナゾーンのカード2枚を墓地に置く。"
         "殿堂入り（デッキに1枚まで。枚数の上限は archetypes.LIMIT に書くもので、そのファイルは担当外のため未登録）",
    note="",
    source=W + "超神羅星アポロヌス・ドラゲリオン")


# ================================================================ シュトラ
def e_shutora(s, i, u):
    for j in (i, 1 - i):
        p = s.P[j]
        if not p.mana:
            continue
        k = max(p.mana, key=E.PRI.get)
        s.take_mana(j, k)
        p.hand.append(k)
        s.ev(f"　シュトラ：プレイヤー{j} はマナから {BY_KEY[k].name} を手札へ")


add("e_shutora", "シュトラ", 4, "W", power=2000, races=("cyberlord",), pri=5, roles="dis", enter=e_shutora,
    text="出た時、各プレイヤーは自分のマナゾーンからカード1枚を選び、手札に戻す（相手のマナを1枚減らせる）",
    source=W + "シュトラ")


# ================================================================ 神秘の石柱
def sp_sekichu(s, i):
    p = s.P[i]
    s.ramp(i, 2, True)
    if p.mana:
        k = min(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        s.grave_put(i, k)
        s.ev(f"　神秘の石柱：マナから {BY_KEY[k].name} を墓地へ")


add("e_sekichu", "神秘の石柱", 3, "N", kind="S", pri=4, roles="acc", spell=sp_sekichu,
    text="唱えた時、自分の山札の上から2枚をタップしてマナゾーンに置く。"
         "その後、自分のマナゾーンからカード1枚を選び、墓地に置く",
    source=W + "神秘の石柱")
