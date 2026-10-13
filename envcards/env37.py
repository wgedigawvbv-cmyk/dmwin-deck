"""担当37：DM26-EX1「ますますつよいパック 25の援軍」の15枚（key は k37_）

  調べ方
    dmwiki.net のカード個別ページ（`https://dmwiki.net/《カード名》`）と、PukiWiki の template プラグインで
    取れる生の wiki ソース（`?plugin=template&refer=《カード名》`）を、カードごとに別の質問で2回以上読み、
    コスト・文明・カードの種類・種族・パワー・ブレイク数・能力の本文が一致することを確かめた。
    本文が途中で切れるページは WebFetch の offset をずらして読み直し、cardtable の行と解説文の両方で
    数値（パワー、−1000／−2000、「4体以上」など）を突き合わせた。

  この15枚に入っている仕組み
    ・キング・セル3枚（新世界王の権威／思想／闘気）と、それを合体させて召喚する
      キング・クリーチャー《Volzeos-Balamord》。セルは kind="K"（手札からは実行できないカード）にして、
      G・ストライクとマナチャージ時のアンタップだけを持たせ、合体は追加の手（freeacts/actapply）で作った。
    ・エクストラEXライフ（シールド2枚ぶんの身代わり）＝Volzeos-Balamord
    ・禁断（EXライフ＋ジャストダイバー＋追加ターン）＝禁断竜王 Vol-Val-8
    ・ガチンコ・ジャッジ3回ぶんの踏み倒し＋エターナル・Ω＝超絶奇跡 鬼羅丸
    ・D・D・D[光/火(3)]（自分のクリーチャーの攻撃時に手札からコストを払って出す）＝ボルシャック・デンジャラス・ドラゴン
    ・G城（kind="G"）＝般若真城 マントラ丸。相手の攻撃時に自分を墓地に置いてメカを出す。
    ・スター進化＝ジョパンダ大佐 ＜ケンジ.Star＞（env0 の star_evo_rep を使う）
    ・ガードマン＋破壊置換（マナゾーンへ）＝チアスイート アカネ
    ・罠金乱舞（このターン最初の攻撃で、名前に《トラップ》とある呪文を手札からただで唱える）＝超機動罠 デンジャデオン

  調べ直して意外だった点
    ・《ゲイルマッチ・ビートル》はコスト3でパワー12000。「攻撃できない」かわりに、
      自分の他のパワー12000以上のクリーチャーの破壊を、自分がマナゾーンに行くことで置き換える。
    ・《禁断竜王 Vol-Val-8》のパワーは54321で、追加ターンの条件は「クリーチャーが4体以上破壊されていれば」
      （名前の8ではなく4）。破壊したのが自分か相手かは問わない。
    ・《超機動罠 デンジャデオン》の自分のターンのはじめの能力は「マナゾーンから召喚」ではなく
      「マナゾーンから手札に戻す」（召喚になっているのはデュエプレ版）。
    ・《般若真城 マントラ丸》が出せるのは「コスト5以下のメカ」。いまのカードプールにメカは1枚もないので、
      この部分は条件がそろう場面がない（実装はしてある）。
    ・既実装の《超時空罠 デンジャデオン》とは別のカード（コスト7・パワー13000 ではなくコスト6・パワー6000）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, move
from envcards.env0 import exlife_enter, exlife_rep, guardman, own_loss, star_evo_rep

W = "https://dmwiki.net/"
SRC = {
    "k37_jopanda": W + "《ジョパンダ大佐 ＜ケンジ.Star＞》",
    "k37_grideria": W + "《堕魔 グリデリア／堕呪 フンズヴァイ》",
    "k37_gailmatch": W + "《ゲイルマッチ・ビートル》",
    "k37_akane": W + "《チアスイート アカネ／「ファーーー！甘い甘い!!」》",
    "k37_mantra": W + "《般若真城 マントラ丸》",
    "k37_bolshackdd": W + "《ボルシャック・デンジャラス・ドラゴン》",
    "k37_oxchecker": W + "《芸魔猛牛 オックスチェッカー》",
    "k37_disastertune": W + "《ディザスター・チューン》",
    "k37_kiramaru": W + "《超絶奇跡 鬼羅丸》",
    "k37_kenni": W + "《新世界王の権威》",
    "k37_shiso": W + "《新世界王の思想》",
    "k37_touki": W + "《新世界王の闘気》",
    "k37_volval8": W + "《禁断竜王 Vol-Val-8》",
    "k37_volzeos": W + "《Volzeos-Balamord》",
    "k37_dangerdeon": W + "《超機動罠 デンジャデオン／地獄極楽トラップ黙示録》",
}

CELLS = ("k37_kenni", "k37_shiso", "k37_touki")        # キング・セル3種


# ================================================================ 共通の小道具
def _minus_power(s, i, t, n):
    """i から見た相手のクリーチャー t のパワーを、このターン n 下げる（0以下なら破壊）"""
    if t is None or n <= 0:
        return
    t.pw -= n
    s.ev(f"　{t.c.name} はこのターン パワー-{n}")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.ev(f"　{t.c.name} はパワー0以下で破壊される")
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def _playable_cre(c):
    """進化元なしで、コストを支払わずに出せるクリーチャーか"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _castle_n(s, i, key):
    """key のG城が、i の表向きのシールドとして何枚あるか"""
    return sum(1 for k, up in s.P[i].sh if up and k == key)


def _look_top(s, i, n):
    """山札の上から n 枚を取り出す（山札は1枚残す。エンジン共通の決まり）"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    if n <= 0:
        return []
    return [p.deck.pop() for _ in range(n)]


def _star_playrule(key, msg):
    """スター進化：進化元になれるレクスターズ／その文明のクリーチャーが4体いるか"""
    def f(deck, k):
        n = 0
        for kk, v in deck.items():
            if kk == k:
                continue
            c = BY_KEY[kk]
            if (c.kind == "C" or kk in E.SHINKA) and msg[1](c):
                n += v
        return None if n >= 4 else msg[0]
    return f


# ================================================================ ジョパンダ大佐 ＜ケンジ.Star＞
def ex_jopanda(s, i, u):
    """スター進化の進化元：レクスターズまたは闇のクリーチャー"""
    return "rexstars" in u.c.races or "D" in u.c.civ


def e_jopanda(s, i, u):
    """出た時、山札の上から3枚を墓地に置く。その後、相手のクリーチャー1体のパワーを
    このターン、自分の墓地にあるカード1枚につき-1000する"""
    s.mill(i, 3)
    if s.over:
        return
    t = s.target(i)
    if t is None:
        return
    _minus_power(s, i, t, 1000 * len(s.P[i].grave))


add("k37_jopanda", "ジョパンダ大佐 ＜ケンジ.Star＞", 3, "D", power=4000, trig=True,
    evo="D", races=("demoncommand", "command", "dreammate", "rexstars"), pri=5, roles="rem trg",
    enter=e_jopanda, evox=ex_jopanda, leaverep=star_evo_rep("k37_jopanda", "ジョパンダ大佐"),
    playrule=_star_playrule("k37_jopanda", ("スター進化の元になるレクスターズか闇のクリーチャーが4体いない",
                                            lambda c: "rexstars" in c.races or "D" in c.civ)),
    text="S・トリガー。スター進化（自分のレクスターズまたは闇のクリーチャー1体の上に置く。離れる時は"
         "一番上のこのカードだけが離れ、下のカードがバトルゾーンに残る）。"
         "出た時、自分の山札の上から3枚を墓地に置く。その後、相手のクリーチャー1体を選んでもよい。"
         "このターン、そのクリーチャーのパワーを自分の墓地にあるカード1枚につき-1000する"
         "（パワー0以下のクリーチャーは破壊される）",
    source=SRC["k37_jopanda"])


# ================================================================ 堕魔 グリデリア／堕呪 フンズヴァイ
def e_grideria(s, i, u):
    """出た時、山札の上から3枚を墓地に置く。その後、相手のクリーチャー1体のパワーを
    このターン、こうして墓地に置いた魔導具カード1枚につき-2000する"""
    got = s.mill(i, 3)
    if s.over:
        return
    n = sum(1 for k in got if "madogu" in BY_KEY[k].races)
    if n <= 0:
        return
    t = s.target(i)
    _minus_power(s, i, t, 2000 * n)


def sp_funzvai(s, i):
    """堕呪 フンズヴァイ：相手のエレメントを2つまで選び、持ち主の手札に戻す"""
    for _ in range(2):
        if s.over:
            return
        t = s.target(i, kinds="CTX")
        if t is None:
            return
        s.ev(f"　堕呪 フンズヴァイ：{t.c.name} を持ち主の手札へ")
        move(s, i, t, "hand")


add("k37_grideria", "堕魔 グリデリア／堕呪 フンズヴァイ", 3, "D", power=2000,
    races=("mafigang", "madogu"), twin=(5, "W", True), pri=4, roles="rem trg",
    enter=e_grideria, spell=sp_funzvai,
    text="クリーチャー側（闇3・マフィ・ギャング／魔導具・パワー2000）：出た時、自分の山札の上から3枚を墓地に置く。"
         "その後、相手のクリーチャー1体を選んでもよい。このターン、そのクリーチャーのパワーを、"
         "こうして墓地に置いた魔導具カード1枚につき-2000する（パワー0以下のクリーチャーは破壊される）。"
         "呪文側《堕呪 フンズヴァイ》（水5・S・トリガー）：相手のエレメントを2つまで選び、持ち主の手札に戻す",
    source=SRC["k37_grideria"])


# ================================================================ ゲイルマッチ・ビートル
def e_gailmatch(s, i, u):
    """出た時、相手のコスト3以下のクリーチャー1体とバトルする"""
    t = s.target(i, lambda z: z.c.cost <= 3)
    if t is None:
        return
    s.ev(f"　ゲイルマッチ・ビートル：{t.c.name} とバトルする")
    s.battle(i, u, 1 - i, t)


def rep_gailmatch(s, i, u, dest, destroy):
    """自分の他の、パワー12000以上のクリーチャーが破壊される時、
    かわりにこのクリーチャー（ゲイルマッチ・ビートル）をマナゾーンに置いてもよい"""
    if not destroy or u.k == "k37_gailmatch" or u.c.kind != "C":
        return False
    if s.power(i, u) < 12000:
        return False
    z = next((x for x in s.P[i].board if x.k == "k37_gailmatch"), None)
    if z is None:
        return False
    if own_loss(s, i, z) > own_loss(s, i, u):
        return False                        # 身代わりのほうが大事なら引き受けない（共通の決まり）
    s.ev(f"　ゲイルマッチ・ビートル：{u.c.name} の破壊のかわりに自分がマナゾーンへ")
    s.leave(i, z, "mana")
    return True


add("k37_gailmatch", "ゲイルマッチ・ビートル", 3, "N", power=12000, noatk=True,
    races=("giant", "insect"), pri=6, roles="rem blk",
    enter=e_gailmatch, leaverep=rep_gailmatch,
    text="このクリーチャーは攻撃できない。"
         "出た時、相手のコスト3以下のクリーチャー1体を選んでもよい。"
         "その選んだクリーチャーとこのクリーチャーをバトルさせる。"
         "自分の他の、パワー12000以上のクリーチャーが破壊される時、"
         "かわりにこのクリーチャーをマナゾーンに置いてもよい",
    source=SRC["k37_gailmatch"])


# ================================================================ チアスイート アカネ／「ファーーー！甘い甘い!!」
def ld_akane(s, i, u, dest, destroy):
    """このクリーチャーが破壊される時、墓地に置くかわりにマナゾーンに置く"""
    if u.k != "k37_akane" or not destroy:
        return None
    return "mana"


def sp_akane(s, i):
    """「ファーーー！甘い甘い!!」：ジャイアントではないクリーチャーをすべて、持ち主のマナゾーンに置く"""
    for j in (1 - i, i):
        for z in list(s.P[j].board):
            if s.over:
                return
            if z.c.kind != "C" or "giant" in z.c.races:
                continue
            if z in s.P[j].board:
                s.ev(f"　「ファーーー！甘い甘い!!」：{z.c.name} を持ち主のマナゾーンへ")
                s.leave(j, z, "mana", by_opp=(j != i))


add("k37_akane", "チアスイート アカネ／「ファーーー！甘い甘い!!」", 2, "N", power=1000, gs=True,
    races=("giant", "snow"), twin=(8, "N", False), pri=3, roles="blk trg acc",
    guard=guardman("k37_akane"), leavedest=ld_akane, spell=sp_akane,
    text="クリーチャー側（自然2・ジャイアント／スノーフェアリー・パワー1000）：G・ストライク。"
         "ガードマン（このクリーチャーをタップして、相手クリーチャーの攻撃先を、"
         "自分の他のクリーチャーからこのクリーチャーに変更してもよい）。"
         "このクリーチャーが破壊される時、墓地に置くかわりにマナゾーンに置く。"
         "呪文側《「ファーーー！甘い甘い!!」》（自然8）：ジャイアントではないクリーチャーをすべて、"
         "持ち主のマナゾーンに置く",
    source=SRC["k37_akane"])


# ================================================================ 般若真城 マントラ丸
def _mantra_mecha(s, i):
    """手札のコスト5以下のメカのうち、いちばん重要度の高いもの"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if not _playable_cre(c) or c.cost > 5 or "mecha" not in c.races:
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    return best


def aw_mantra(s, i, u):
    """相手のクリーチャーが攻撃する時、このG城を墓地に置いてもよい。
    そうしたら、コスト5以下のメカ1体を自分の手札から出してもよい。
    このターン、こうして出したクリーチャーに「ブロッカー」と「スレイヤー」を与える"""
    if u.c.kind != "C":
        return
    j = 1 - i                                  # G城の持ち主（攻撃しているのは相手）
    if _castle_n(s, j, "k37_mantra") <= 0:
        return
    k = _mantra_mecha(s, j)
    if k is None:
        return                                 # 出すメカがいなければ墓地に置かない
    p = s.P[j]
    idx = next((x for x, (kk, up) in enumerate(p.sh) if up and kk == "k37_mantra"), None)
    if idx is None:
        return
    s.take_shield(j, idx, "grave")
    s.ev("　般若真城 マントラ丸：自分を墓地に置き、手札からメカを出す")
    if k not in p.hand:
        return
    p.hand.remove(k)
    z = s.enter(j, k, "hand", False)
    if z is not None:
        z.x["k37_mgift"] = s.turn              # このターンだけブロッカーとスレイヤー


def tp_mantra(s, j):
    """相手のターンの終わりに、カードを1枚引いてもよい"""
    if s.tp == j:
        return                                 # 自分のターンの終わりには引かない
    n = _castle_n(s, j, "k37_mantra")
    if n <= 0:
        return
    s.ev("　般若真城 マントラ丸：相手のターンの終わりに引く")
    s.draw(j, n)


def bo_mantra(s, u):
    return u.x.get("k37_mgift") == s.turn


def bf_mantra(s, ai, au, di, du, a_dies, d_dies):
    """マントラ丸が与えたスレイヤー"""
    if au.x.get("k37_mgift") == s.turn:
        d_dies = True
    if du.x.get("k37_mgift") == s.turn:
        a_dies = True
    return a_dies, d_dies


add("k37_mantra", "般若真城 マントラ丸", 4, "LD", kind="G", pri=5, roles="blk rem draw",
    atkwatch=aw_mantra, tendp=tp_mantra, blockok=bo_mantra, battlefx=bf_mantra,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時はかわりに墓地へ）。"
         "相手のクリーチャーが攻撃する時、このG城を墓地に置いてもよい。そうしたら、コスト5以下のメカ1体を"
         "自分の手札から出してもよい。このターン、こうして出したクリーチャーに「ブロッカー」と「スレイヤー」を与える。"
         "相手のターンの終わりに、カードを1枚引いてもよい",
    note="いまのカードプールに種族「メカ」のカードが1枚もないので、"
         "「メカを出す」部分が実際に働く場面はまだ作れない（実装はしてある）。"
         "出すメカがいない時は、無駄に墓地に置かないようにしてある",
    source=SRC["k37_mantra"])


# ================================================================ ボルシャック・デンジャラス・ドラゴン
def _ddd_ready(s, i, key, cost, civ):
    """D・D・D：手札のそのカードを、その文明の cost マナで出せるか"""
    p = s.P[i]
    if key not in p.hand or len(p.mana) - p.mused < cost:
        return False
    if not set(civ) <= E.civs(p):
        return False
    return s.fate(i, key, "hand", True) == "ok"


def aw_bolshackdd(s, i, u):
    """D・D・D[光/火(3)]：自分のクリーチャーが攻撃する時、光・火の3マナで手札から出す"""
    if u.c.kind != "C" or s.tp != i:
        return
    if not _ddd_ready(s, i, "k37_bolshackdd", 3, "LF"):
        return
    p = s.P[i]
    p.hand.remove("k37_bolshackdd")
    p.mused += 3
    s.ev("　D・D・D[光/火(3)]：ボルシャック・デンジャラス・ドラゴン")
    s.enter(i, "k37_bolshackdd", "hand", True)


def a_bolshackdd(s, i, u):
    """攻撃する時、他のクリーチャー1体を選び、タップまたはアンタップする"""
    t = s.target(i, lambda z: not z.tap)
    if t is not None:
        s.tap_cre(1 - i, t)
        s.ev(f"　ボルシャック・デンジャラス・ドラゴン：{t.c.name} をタップする")
        return
    z = max((x for x in s.P[i].board if x.c.kind == "C" and x.tap and x is not u),
            key=s.val, default=None)
    if z is not None:
        z.tap = False
        s.ev(f"　ボルシャック・デンジャラス・ドラゴン：{z.c.name} をアンタップする")


add("k37_bolshackdd", "ボルシャック・デンジャラス・ドラゴン", 5, "LF", power=5000, sa=True,
    races=("armoreddragon", "dragon"), pri=7, roles="atk rem dis",
    attack=a_bolshackdd, atkwatch=aw_bolshackdd,
    text="D・D・D[光/火(3)]（自分のクリーチャーが攻撃する時、光・火の3マナを支払って、"
         "このカードを自分の手札から出してもよい）。スピードアタッカー。"
         "このクリーチャーが攻撃する時、他のクリーチャー1体を選び、タップまたはアンタップする"
         "（相手のアンタップしているクリーチャーがいればそれをタップし、いなければ"
         "自分のタップしているクリーチャーのうち重要度のいちばん高いものをアンタップする）",
    source=SRC["k37_bolshackdd"])


# ================================================================ 芸魔猛牛 オックスチェッカー
def cx_oxchecker(s, i, av):
    """召喚コストを、このターン自分が引いたカード1枚につき1少なくする（1より少なくならない）"""
    return max(1, 5 - s.P[i].drawn)


def a_oxchecker(s, i, u):
    """攻撃する時、カードを2枚引き、自分の手札を1枚捨てる"""
    p = s.P[i]
    s.draw(i, 2)
    if s.over or not p.hand:
        return
    s.discard(i, min(p.hand, key=E.PRI.get))


add("k37_oxchecker", "芸魔猛牛 オックスチェッカー", 5, "WF", power=5000, sa=True,
    races=("magicmonster", "gamecommand", "command"), pri=7, roles="draw atk acc",
    costx=cx_oxchecker, attack=a_oxchecker,
    text="このクリーチャーの召喚コストを、このターン自分が引いたカード1枚につき1少なくする。"
         "ただしコストは1より少なくならない。スピードアタッカー。"
         "このクリーチャーが攻撃する時、カードを2枚引き、自分の手札を1枚捨てる",
    source=SRC["k37_oxchecker"])


# ================================================================ ディザスター・チューン
def sp_disastertune(s, i):
    """自分の山札の上から4枚を見る。それらを1枚ずつ、手札・マナゾーン・墓地・山札の下に置く"""
    p = s.P[i]
    top = _look_top(s, i, 4)
    if not top:
        return
    top.sort(key=E.PRI.get, reverse=True)
    if top:
        k = top.pop(0)
        p.hand.append(k)
        s.ev(f"　ディザスター・チューン：{BY_KEY[k].name} を手札へ")
    if top:
        k = top.pop(0)
        s.add_mana(i, k, src="deck")
        s.ev(f"　ディザスター・チューン：{BY_KEY[k].name} をマナゾーンへ")
    if top:
        k = top.pop()                       # いちばん要らない1枚を墓地へ
        s.grave_put(i, k)
        s.ev(f"　ディザスター・チューン：{BY_KEY[k].name} を墓地へ")
    for k in top:
        p.deck.insert(0, k)


add("k37_disastertune", "ディザスター・チューン", 3, "WDN", kind="S", pri=4, roles="acc draw",
    spell=sp_disastertune,
    text="自分の山札の上から4枚を見る。それらを1枚ずつ、手札、マナゾーン、墓地、山札の下に置く"
         "（重要度のいちばん高い1枚を手札、次を マナゾーン、いちばん低い1枚を墓地、残りを山札の下に置く）",
    source=SRC["k37_disastertune"])


# ================================================================ 超絶奇跡 鬼羅丸
def _gachi_one(s, i):
    """ガチンコ・ジャッジを1回。勝って表向きにしたのがクリーチャーなら出し、呪文ならただで唱える。
    勝てなければ（または出せなければ）山札の下に置く"""
    p, o = s.P[i], s.P[1 - i]
    if not p.deck:
        return
    a = p.deck.pop()
    cb = -1
    if o.deck:
        b = o.deck.pop()
        o.deck.insert(0, b)
        cb = BY_KEY[b].cost
    c = BY_KEY[a]
    if c.cost >= cb:                        # 同じコストなら仕掛けた側の勝ち
        if _playable_cre(c) and s.fate(i, a, "deck", False) == "ok":
            s.ev(f"　ガチンコ・ジャッジに勝った：{c.name} を出す")
            s.enter(i, a, "deck", False)
            return
        if c.kind == "S" and s.spell_ok(i, c.cost):
            s.ev(f"　ガチンコ・ジャッジに勝った：{c.name} をコストを支払わずに唱える")
            s.cast(i, a)
            return
        if c.twin and s.spell_ok(i, c.twin[0]):
            s.ev(f"　ガチンコ・ジャッジに勝った：{c.name} の呪文側をコストを支払わずに唱える")
            s.cast(i, a, True)
            return
    p.deck.insert(0, a)


def e_kiramaru(s, i, u):
    """召喚によって出た時、相手と3回ガチンコ・ジャッジする"""
    if not u.x.get("summoned"):
        return
    for _ in range(3):
        if s.over:
            return
        _gachi_one(s, i)


def ld_kiramaru(s, i, u, dest, destroy):
    """エターナル・Ω：離れる時、かわりに手札に戻す"""
    if u.k != "k37_kiramaru" or dest == "hand":
        return None
    return "hand"


def sa_kiramaru(s, i, u):
    """自分のクリーチャーすべてに「スピードアタッカー」を与える"""
    return u.c.kind == "C" and s.has(i, "k37_kiramaru")


add("k37_kiramaru", "超絶奇跡 鬼羅丸", 12, "", power=17000, brk=3,
    races=("humanoid", "hunter", "alien", "zenith"), pri=13, roles="fin atk acc",
    enter=e_kiramaru, leavedest=ld_kiramaru, saok=sa_kiramaru,
    text="T・ブレイカー。無色のクリーチャー（どの文明のマナでも召喚できる）。"
         "このクリーチャーが召喚によって出た時、相手と3回ガチンコ・ジャッジする"
         "（互いに山札の上から1枚を表向きにし、コストが大きいほうの勝ち。同じコストなら仕掛けた側の勝ち）。"
         "自分がクリーチャーを表向きにして勝つたび、そのクリーチャーを山札の下に置くかわりに出す。"
         "自分が呪文を表向きにして勝つたび、その呪文を山札の下に置くかわりにコストを支払わずに唱える。"
         "自分のクリーチャーすべてに「スピードアタッカー」を与える。"
         "エターナル・Ω（このクリーチャーが離れる時、かわりに手札に戻す）",
    source=SRC["k37_kiramaru"])


# ================================================================ 新世界王の権威／思想／闘気（キング・セル）
def cx_cell(s, i):
    """このカードを自分の手札からマナゾーンに置いた時、アンタップする
    （多色なのでエンジンはタップして置く。その1枚ぶんを戻す）"""
    p = s.P[i]
    if p.mused > 0:
        p.mused -= 1


def _cell_text(name, civ, others):
    return (f"キング・セル（{civ}の多色カード。マナコストがなく、手札からは実行できない）。G・ストライク。"
            f"このカードを自分の手札からマナゾーンに置いた時、アンタップする。"
            f"{others}と合体すると《Volzeos-Balamord》になる")


add("k37_kenni", "新世界王の権威", 0, "LDF", kind="K", gs=True, pri=2, roles="trg",
    chargex=cx_cell,
    text=_cell_text("新世界王の権威", "光/闇/火", "《新世界王の思想》《新世界王の闘気》"),
    source=SRC["k37_kenni"])

add("k37_shiso", "新世界王の思想", 0, "WFN", kind="K", gs=True, pri=2, roles="trg",
    chargex=cx_cell,
    text=_cell_text("新世界王の思想", "水/火/自然", "《新世界王の権威》《新世界王の闘気》"),
    source=SRC["k37_shiso"])

add("k37_touki", "新世界王の闘気", 0, "LDN", kind="K", gs=True, pri=2, roles="trg",
    chargex=cx_cell,
    text=_cell_text("新世界王の闘気", "光/闇/自然", "《新世界王の権威》《新世界王の思想》"),
    source=SRC["k37_touki"])


# ================================================================ Volzeos-Balamord
def _cells_where(s, i):
    """キング・セル3種がどこにあるか（{キー: "hand"/"mana"}）。3種そろっていなければ None"""
    p = s.P[i]
    out = {}
    for k in CELLS:
        if k in p.hand:
            out[k] = "hand"
        elif k in p.mana:
            out[k] = "mana"
        else:
            return None
    return out


def fa_volzeos(s, i, av, cv):
    """合体召喚：手札またはマナゾーンにキング・セル3種がそろっていれば、コスト9を支払って召喚してもよい"""
    p = s.P[i]
    if s.has(i, "k37_volzeos"):
        return []
    w = _cells_where(s, i)
    if w is None:
        return []
    inmana = sum(1 for z in w.values() if z == "mana")
    if len(p.mana) - p.mused - inmana < 9:
        return []
    if not set("LWDFN") <= cv:
        return []
    if s.fate(i, "k37_volzeos", "hand", True) != "ok":
        return []
    return [("x:k37_volz", "k37_volzeos")]


def ap_volzeos(s, a):
    i = s.tp
    p = s.P[i]
    w = _cells_where(s, i)
    if w is None:
        return
    inmana = sum(1 for z in w.values() if z == "mana")
    if len(p.mana) - p.mused - inmana < 9:
        return
    for k, zone in sorted(w.items()):
        if zone == "mana":
            s.take_mana(i, k)
        else:
            p.hand.remove(k)
    p.mused += 9
    s.ev("合体召喚：キング・セル3枚から Volzeos-Balamord（9マナ）")
    u = s.enter(i, "k37_volzeos", "hand", True)
    if u is not None:
        u.under = list(CELLS)                # 離れる時、合体していたキング・セルも一緒に離れる
    else:
        for k in sorted(w):
            p.grave.append(k)


def e_volzeos(s, i, u):
    """エクストラEXライフ：出す時、自分の山札の上から2枚をシールド化する。
    出たターンの間はブロックされない"""
    p = s.P[i]
    got = []
    for _ in range(2):
        if len(p.deck) <= 1:
            break
        k = p.deck.pop()
        if s.add_shield(i, k, False):
            got.append(k)
        else:
            p.deck.append(k)
            break
    u.x["k37_ex"] = tuple(got)
    u.x["k37_ent"] = s.turn
    if got:
        s.ev(f"　エクストラEXライフ：シールドを{len(got)}枚置いた")


def rep_volzeos(s, i, u, dest, destroy):
    """離れる時、かわりにエクストラEXライフのシールド1つを墓地に置く"""
    if u.k != "k37_volzeos":
        return False
    got = u.x.get("k37_ex") or ()
    p = s.P[i]
    for n, k in enumerate(got):
        j = next((x for x, (kk, up) in enumerate(p.sh) if kk == k and not up), None)
        if j is None:
            continue
        u.x["k37_ex"] = got[:n] + got[n + 1:]
        s.take_shield(i, j, "grave")
        s.ev("　エクストラEXライフ：シールド1つを墓地に置いて Volzeos-Balamord は残る")
        return True
    u.x["k37_ex"] = ()
    return False


def a_volzeos(s, i, u):
    """攻撃する時、相手は自身の手札をすべて捨てる"""
    o = s.P[1 - i]
    if not o.hand:
        return
    s.ev("　Volzeos-Balamord：相手は手札をすべて捨てる")
    for k in list(o.hand):
        if s.over:
            return
        if k in o.hand:
            s.discard(1 - i, k)


def unb_volzeos(s, i, u):
    return u.k == "k37_volzeos" and u.x.get("k37_ent") == s.turn


def gs_volzeos(s, di, k):
    """自分が「G・ストライク」を使った時、自分の山札の上から1枚目をマナゾーンに置き、
    相手のクリーチャー1体を選んでタップしてもよい（両方するか、どちらもしないかのどちらか）"""
    if not s.has(di, "k37_volzeos"):
        return
    s.ramp(di, 1)
    t = s.target(di, lambda x: not x.tap and x.c.kind == "C")
    if t is not None:
        s.tap_cre(1 - di, t)
        s.ev(f"　Volzeos-Balamord：マナを1枚増やし、{t.c.name} をタップする")
    else:
        s.ev("　Volzeos-Balamord：マナを1枚増やす")


add("k37_volzeos", "Volzeos-Balamord", 9, "LWDFN", power=555555, brk=99, sa=True,
    races=("dispector", "newworlddragon"), pri=15, roles="fin atk dis shd",
    enter=e_volzeos, attack=a_volzeos, leaverep=rep_volzeos, unbok=unb_volzeos,
    freeacts=fa_volzeos, actapply={"x:k37_volz": ap_volzeos}, gswatch=gs_volzeos,
    costx=lambda s, i, av: 99,              # 手札から普通に召喚するカードではない（合体召喚だけ）
    playrule=lambda deck, k: "キング・セル3枚を合体させて出すキング・クリーチャーで、デッキには入らない",
    text="キング・クリーチャー（デッキには入らず、自分の手札またはマナゾーンにキング・セル"
         "《新世界王の権威》《新世界王の思想》《新世界王の闘気》の3種がそろっていれば、合体させ、"
         "コスト9を支払って召喚してもよい）。"
         "エクストラEXライフ（出す時、自分の山札の上から2枚をシールド化する。離れる時、"
         "かわりにそのシールドのうち1つを墓地に置く）。スピードアタッカー。"
         "ワールド・ブレイカー（相手のシールドをすべてブレイクする）。"
         "このクリーチャーは、出たターンの間ブロックされない。"
         "このクリーチャーが攻撃する時、相手は自身の手札をすべて捨てる。"
         "自分が「G・ストライク」を使った時、自分の山札の上から1枚目をマナゾーンに置き、"
         "相手のクリーチャー1体を選んでタップしてもよい",
    note="エクストラEXライフのシールドは本物のシールドとして置いているが、"
         "「そのシールド」の見分けはカードのキーでしているので、同じカードが別のシールドにもある時は"
         "そちらを墓地に置くことがある。"
         "合体召喚は「キング・セルをマナゾーンから取り除いたうえで、残りのマナ9枚を支払う」形にした",
    status="full", source=SRC["k37_volzeos"])


# ================================================================ 禁断竜王 Vol-Val-8
def a_volval8(s, i, u):
    """攻撃する時、山札の上から5枚を見て2枚まで手札に加え、残りを山札の下に置く。
    その後、パワー6000以下のクリーチャーをすべて破壊してもよい"""
    p, o = s.P[i], s.P[1 - i]
    top = _look_top(s, i, 5)
    if top:
        top.sort(key=E.PRI.get, reverse=True)
        for k in top[:2]:
            p.hand.append(k)
        s.ev(f"　Vol-Val-8：上5枚から{len(top[:2])}枚を手札へ")
        for k in top[2:]:
            p.deck.insert(0, k)
    if s.over:
        return
    mine = [z for z in p.board if z.c.kind == "C" and s.power(i, z) <= 6000]
    theirs = [z for z in o.board if z.c.kind == "C" and s.power(1 - i, z) <= 6000]
    if not theirs:
        return
    if sum(s.val(z) for z in theirs) <= sum(own_loss(s, i, z) for z in mine):
        return                              # 自分のほうが損なら使わない（共通の決まり）
    s.ev("　Vol-Val-8：パワー6000以下のクリーチャーをすべて破壊する")
    for z in theirs:
        if z in o.board and not s.over:
            s.leave(1 - i, z, "grave", by_opp=True, destroy=True)
    for z in mine:
        if z in p.board and not s.over:
            s.leave(i, z, "grave", destroy=True)


def t_volval8(s, i, u):
    """自分のターンの終わりに、このターン、クリーチャーが4体以上破壊されていれば、
    このターンの後に自分のターンを追加する（どちらのクリーチャーでも数える）"""
    if s.dcount[0] + s.dcount[1] < 4:
        return
    s.P[i].extra += 1
    s.ev("　Vol-Val-8：このターンの後に自分のターンを追加する")


add("k37_volval8", "禁断竜王 Vol-Val-8", 9, "WFN", power=54321, brk=3, sa=True, jd=True,
    races=("dispector", "armoreddragon", "earthdragon", "kindan"), pri=13,
    roles="fin atk rem draw shd",
    enter=exlife_enter, attack=a_volval8, tend=t_volval8,
    leaverep=exlife_rep,
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。スピードアタッカー。ジャストダイバー（出たターン、相手に選ばれず攻撃されない）。"
         "T・ブレイカー。"
         "このクリーチャーが攻撃する時、自分の山札の上から5枚を見て、その中から2枚まで手札に加える。"
         "残りを好きな順序で山札の下に置く。その後、パワー6000以下のクリーチャーをすべて破壊してもよい。"
         "自分のターンの終わりに、このターン、クリーチャーが4体以上破壊されていれば、"
         "このターンの後に自分のターンを追加する",
    note="",
    status="full", source=SRC["k37_volval8"])


# ================================================================ 超機動罠 デンジャデオン／地獄極楽トラップ黙示録
def ts_dangerdeon(s, i):
    """自分のターンのはじめに、このクリーチャーを自分のマナゾーンから手札に戻してもよい
    （マナが減りすぎない時だけ戻す＝全デッキ共通の機械的な決まり）"""
    p = s.P[i]
    if "k37_dangerdeon" not in p.mana or len(p.mana) < 7:
        return
    s.take_mana(i, "k37_dangerdeon")
    p.hand.append("k37_dangerdeon")
    s.ev("　超機動罠 デンジャデオン：マナゾーンから手札に戻る")


def _trap_free_cast(s, j):
    """名前に《トラップ》とある呪文を1枚、手札からコストを支払わずに唱える"""
    p = s.P[j]
    best, bv, bt = None, -1, False
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if "トラップ" not in c.name:
            continue
        if c.kind == "S" and s.spell_ok(j, c.cost):
            v, tw = E.PRI[k], False
        elif c.twin and s.spell_ok(j, c.twin[0]):
            v, tw = c.twin[0], True
        else:
            continue
        if v > bv:
            best, bv, bt = k, v, tw
    if best is None:
        return
    p.hand.remove(best)
    s.ev(f"　罠金乱舞：{BY_KEY[best].name} をコストを支払わずに唱える")
    s.cast(j, best, bt)


def aw_dangerdeon(s, i, u):
    """罠金乱舞：クリーチャーが攻撃する時、それがこのターン最初の攻撃なら、
    名前に《トラップ》とある呪文を1枚、自分の手札からコストを支払わずに唱えてもよい"""
    if u.c.kind != "C":
        return
    for j in (0, 1):
        if not s.has(j, "k37_dangerdeon"):
            continue
        p = s.P[j]
        if p.x.get("k37_dd_t") == s.turn:
            continue                        # このターン最初の攻撃ではない
        p.x["k37_dd_t"] = s.turn
        _trap_free_cast(s, j)


def sp_dangerdeon(s, i):
    """地獄極楽トラップ黙示録：相手のクリーチャー1体またはシールド1つを、持ち主のマナゾーンに置く"""
    o = s.P[1 - i]
    t = s.target(i)
    if t is not None:
        s.ev(f"　地獄極楽トラップ黙示録：{t.c.name} を持ち主のマナゾーンへ")
        move(s, i, t, "mana")
        return
    if not o.sh:
        return
    j = next((x for x in range(len(o.sh) - 1, -1, -1) if not o.sh[x][1]), len(o.sh) - 1)
    s.ev("　地獄極楽トラップ黙示録：相手のシールド1つを持ち主のマナゾーンへ")
    s.take_shield(1 - i, j, "mana")


add("k37_dangerdeon", "超機動罠 デンジャデオン／地獄極楽トラップ黙示録", 6, "N", power=6000, brk=2,
    races=("grandsect",), twin=(8, "N", True), pri=8, roles="rem acc trg fin",
    turnstart=ts_dangerdeon, atkwatch=aw_dangerdeon, spell=sp_dangerdeon,
    text="クリーチャー側（自然6・グランセクト・パワー6000）：W・ブレイカー。"
         "自分のターンのはじめに、このクリーチャーを自分のマナゾーンから手札に戻してもよい"
         "（マナが7枚以上ある時だけ戻す）。"
         "罠金乱舞：クリーチャーが攻撃する時、それがこのターン最初の攻撃なら、"
         "名前に《トラップ》とある呪文を1枚、自分の手札からコストを支払わずに唱えてもよい。"
         "呪文側《地獄極楽トラップ黙示録》（自然8・S・トリガー）：相手のクリーチャー1体またはシールド1つを選び、"
         "持ち主のマナゾーンに置く（相手のクリーチャーがいればそれを、いなければシールドを選ぶ）",
    note="罠金乱舞の「このターン最初の攻撃なら」は、このクリーチャーがバトルゾーンにいる間の"
         "最初の攻撃で判定している。そのターンの最初の攻撃より後にこのクリーチャーが出た場合、"
         "その次の攻撃を「最初の攻撃」として扱ってしまう（攻撃の回数をエンジンが数えていないため）",
    source=SRC["k37_dangerdeon"])
