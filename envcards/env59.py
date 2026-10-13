"""担当59：DM26-SD1「ドキドキつよいデッキ 25の王道」の17枚（キーの接頭辞 k59_）

  この箱は25個の構築済みデッキを1つにまとめた再録商品で、担当分はジャイアント（革命チェンジ）、
  アーマード／メカ、鬼札王国、ボルシャックの各デッキの核になる札が中心。

  この担当分で出てきた仕組みと、どう書いたか
    ・革命チェンジ（銀河竜 ゴルファンタジスタ／チアスペース アカネ／鎧機天 シロフェシー）＝ `changex=` と `playrule=`
    ・バトルの差し替え（銀河竜 ゴルファンタジスタの「かわりにこのクリーチャーにバトルさせてもよい」）＝ `battleswap=`
      （スーパーガードマンと違いタップは要らないので、タップせずに引き受ける）
    ・G・ゼロ＋進化（終の怒流牙 ドルゲユキムラ）＝ `freeacts=`／`actapply=` で進化元の上に重ねて召喚
    ・ヨビニオン（悪魔世界の閃光）＝山札の上から1枚ずつめくり、最初に出た軽いクリーチャーを出す
    ・サムライ・メクレイド5（戦術の天才 マロク）＝上3枚からサムライ1枚をただで使い、
      クロスギアならそのままただでクロスする（env0 のクロスギアの仕組みを使う）
    ・エスケープ（戦術の天才 マロク）＝ `leaverep=`
    ・敗北の置き換え（一王二命三眼槍）＝ `loserep=`。鬼エンドは「山札の下から1枚」なので注意
    ・ガチンコ・ジャッジ（特攻の忠剣ハチ公）＝互いに山札の上を見せて下に置き、同コストなら仕掛けた側の勝ち
    ・チャージャー（決闘者・チャージャー）＝ `nograve=True` ＋ 呪文の最後で `s.add_mana`

  調べ直して確かめたこと
    17枚すべて dmwiki.net のカードページを別の質問で2回ずつ読み、コスト・文明・種類・種族・パワー・
    ブレイク数・能力本文が2回とも一致することを確かめた（生の wiki ソース `?plugin=template&refer=…` も併用）。
    1回目で落ちていた記載はなかった。意外だった点：
      ・《一王二命三眼槍》の鬼エンドは「自分の山札の**下**から1枚を墓地に置く」（上ではない）。
      ・《ガチャンコ ガチロボ》の紙版は「3枚すべてが同じコストのクリーチャーなら**すべて出す**」（枚数を選べない）。
      ・《幻緑の双月／母なる星域》の呪文側のコスト制限は「そのクリーチャーのコスト以下」ではなく
        「自分のマナゾーンにあるカードの枚数以下」。
      ・《修羅の死神フミシュナ／「この先は修羅の道ぞ」》（env10 の `e_fumishuna`）と
        《幻緑の双月／母なる星域》（env14 の `e_sougetsu`）は**すでに実装済み**だったので、
        二重登録を避けてこのモジュールでは登録していない（status_59.md に書いた）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, free_play, move, opp_all
from envcards.env0 import gears_on, lock_until_my_turn, race_like

W = "https://dmwiki.net/"
SRC = {
    "k59_chokyu": W + "《超球の超人／父なるタッチダウン》",
    "k59_golfantasista": W + "《銀河竜 ゴルファンタジスタ》",
    "k59_akane": W + "《チアスペース アカネ》",
    "k59_dorugeyukimura": W + "《終の怒流牙 ドルゲユキムラ》",
    "k59_mantis": W + "《輝跡！シャイニングロード・マンティス／輝跡の大地》",
    "k59_cyclil": W + "《学識妖精サイクリル》",
    "k59_walledflash": W + "《悪魔世界の閃光》",
    "k59_maroku": W + "《戦術の天才 マロク》",
    "k59_shirophecy": W + "《鎧機天 シロフェシー》",
    "k59_ichiouni": W + "《一王二命三眼槍》",
    "k59_gachirobo": W + "《ガチャンコ ガチロボ》",
    "k59_hachiko": W + "《特攻の忠剣ハチ公》",
    "k59_naturalgo": W + "《ナ・チュラルゴ・デンジャー／ナチュラル・トラップ》",
    "k59_bolshack": W + "《ボルシャック・ドラゴン／決闘者・チャージャー》",
    "k59_neobolshack": W + "《ネオ・ボルシャック・ドラゴン／ボルシャックゾーン》",
}


# ================================================================ 共通の道具
def _civ(k):
    """そのカードの文明（ツインパクトは両面をまとめたもの）"""
    return E.MCIV[k]


def _summonable(c):
    """進化元なしでも出せるクリーチャーか"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _is_giant(c):
    """ジャイアントの種族カテゴリか（ジャイアント・ドラゴン、ジャイアント・ハンター等も含む）"""
    return any("giant" in r for r in c.races)


def _is_armored(c):
    """アーマードの種族カテゴリか（アーマード・ドラゴン、アーマード・メカ・セレス等も含む）"""
    return any("armored" in r for r in c.races)


def _is_mecha(c):
    """メカの種族カテゴリか（グレートメカオーはメカではないので外す）"""
    return any("mecha" in r and r != "greatmechaoh" for r in c.races)


def _giants(s, i):
    """バトルゾーンにある自分のジャイアント（タマシードも1枚として数える）"""
    return [z for z in s.P[i].board if _is_giant(z.c) and z.c.kind in "CT"]


def _pr_change(pred, n=3, what="革命チェンジの元"):
    """革命チェンジ：入れ替え元になるクリーチャーがデッキに n 体以上あるか"""
    def f(deck, k):
        c = sum(v for kk, v in deck.items()
                if kk != k and BY_KEY[kk].kind == "C" and pred(BY_KEY[kk]))
        return None if c >= n else f"{what}になるクリーチャーが{n}体いない"
    return f


def _take_shield_to(s, j, dest):
    """プレイヤー j のシールド1つをシールドゾーンから離して dest へ送る。
    どれを選ぶかは全デッキ共通の決まりで、いちばん重要度の高いカードのシールドを選ぶ。
    シールドゾーンの出口は `s.take_shield` の1か所なので、必ずそれを通す。"""
    p = s.P[j]
    if not p.sh:
        return None
    cand = list(range(len(p.sh)))
    plain = [x for x in cand if not (p.sh[x][1] and BY_KEY[p.sh[x][0]].kind == "G")]
    cand = plain or cand                     # 表向きのG城は離れると墓地なので、ほかにあれば避ける
    x = max(cand, key=lambda y: E.PRI[p.sh[y][0]])
    r = s.take_shield(j, x, dest)
    return None if r is None else r[0]


def _escape(s, i, what):
    """エスケープ：破壊されるかわりに自分のシールド1つを手札に加える（S・トリガーは使えない）"""
    p = s.P[i]
    for x in range(len(p.sh) - 1, -1, -1):
        if p.sh[x][1]:
            continue                         # 表向きのシールド（G城など）は使わない
        r = s.take_shield(i, x, "hand")
        if r is not None:
            s.ev(f"　エスケープ：シールドを1つ手札に加えて {what} は破壊されない")
            return True
    return False


def _gachinko(s, i):
    """ガチンコ・ジャッジ1回（勝ったら True）。互いに山札の上から1枚を見せて一番下に置く。
    同じコストなら仕掛けた側（i）の勝ち"""
    p, o = s.P[i], s.P[1 - i]
    if not p.deck:
        return False
    a = p.deck.pop()
    p.deck.insert(0, a)
    cb = -1
    if o.deck:
        b = o.deck.pop()
        o.deck.insert(0, b)
        cb = BY_KEY[b].cost
    return BY_KEY[a].cost >= cb


# ================================================================ 超球の超人／父なるタッチダウン
def bf_chokyu(s, ai, au, di, du, a_dies, d_dies):
    """バトルに勝った時、相手のシールドを1つ選び、持ち主のマナゾーンに置いてもよい"""
    if au.k == "k59_chokyu" and d_dies and not a_dies:
        if _take_shield_to(s, di, "mana") is not None:
            s.ev("　超球の超人：バトルに勝ったので相手のシールド1つを持ち主のマナゾーンへ")
    elif du.k == "k59_chokyu" and a_dies and not d_dies:
        if _take_shield_to(s, ai, "mana") is not None:
            s.ev("　超球の超人：バトルに勝ったので相手のシールド1つを持ち主のマナゾーンへ")
    return a_dies, d_dies


def sl_chokyu(s, i, cost, k=None):
    """相手はコスト5以下の、クリーチャーではないカードを使えない（呪文の分）。

    ツインパクトは手札などでは両方の種類を持つので、クリーチャーの側があるカードは
    「クリーチャーではないカード」に当たらず、コスト5以下の呪文側でも唱えられる（公式Q&A）。
    クリーチャーの側が無いツインパクト（タマシード／呪文など）は止まる。"""
    if cost > 5 or not s.has(1 - i, "k59_chokyu"):
        return False
    if k is None:
        return True                       # キーが渡らない呼び出しはコストだけで止める（今までどおり）
    return BY_KEY[k].kind != "C"


def sp_chokyu(s, i):
    """父なるタッチダウン：相手1体をマナゾーンに置き、それより軽いクリーチャーをマナから出す"""
    t = s.target(i)
    if t is None:
        return
    cost = t.c.cost
    s.ev(f"　父なるタッチダウン：{t.c.name} を持ち主のマナゾーンへ")
    move(s, i, t, "mana")
    s.revive(i, lambda c: c.cost < cost, "mana")


add("k59_chokyu", "超球の超人 / 父なるタッチダウン", 8, "N", power=12000, brk=3, mach=True,
    races=("giant",), twin=(5, "N", False), pri=11, roles="fin atk rem dis",
    battlefx=bf_chokyu, spelllock=sl_chokyu, spell=sp_chokyu,
    status="partial",
    note="「相手はコスト5以下の、クリーチャーではないカードを使えない」のうち、呪文の分は `spelllock=` で"
         "書けた（クリーチャーの側を持つツインパクトは止めない＝公式の裁定どおり）。"
         "タマシード・クロスギア・G城として使う分は書けなかった（カードを使うこと自体を止める"
         "差し込み口がエンジンになく、タマシード・G城・クロスギアは legal_main の中で"
         "`p.ban`（1つのコストだけを止める仕組み）しか見ていない。REQUEST_59.md 1）。"
         "バトルに勝った時に取るシールドは、重要度のいちばん高いカードのシールドを選ぶ（全デッキ共通の決まり）",
    text="クリーチャー側：マッハファイター、T・ブレイカー。"
         "このクリーチャーがバトルに勝った時、相手のシールドを1つ選び、持ち主のマナゾーンに置いてもよい。"
         "相手はコスト5以下の、クリーチャーではないカードを使えない。"
         "呪文側《父なるタッチダウン》（自然5・ジャイアント・スキル）：相手のクリーチャー1体を選び、"
         "持ち主のマナゾーンに置く。その後、そのクリーチャーよりコストが小さいクリーチャー1体を、"
         "自分のマナゾーンから出してもよい",
    source=SRC["k59_chokyu"])


# ================================================================ 銀河竜 ゴルファンタジスタ
def w_golfantasista(s, i, u):
    """相手のクリーチャーが出た時、次の自分のターンのはじめまで、それは攻撃もブロックもできない"""
    if u.c.kind != "C":
        return
    j = 1 - i                                 # ゴルファンタジスタの持ち主
    if not s.has(j, "k59_golfantasista"):
        return
    lock_until_my_turn(s, j, u)
    s.ev(f"　銀河竜 ゴルファンタジスタ：{u.c.name} は次の相手のターンのはじめまで攻撃もブロックもできない")


def bs_golfantasista(s, di, du, ai, au):
    """自分の他のジャイアントが相手のクリーチャーとバトルする時、かわりにこのクリーチャーにバトルさせてもよい
    （タップは要らない。バトルに勝てるか、守る相手のほうが大事な時だけ引き受ける）"""
    if du is None or du.c.kind != "C" or not _is_giant(du.c):
        return None
    ap = s.power(ai, au, True)
    for z in s.P[di].board:
        if z.k != "k59_golfantasista" or z.c.kind != "C" or z is du:
            continue
        if s.power(di, z) > ap or s.val(du) > s.val(z):
            return z
    return None


add("k59_golfantasista", "銀河竜 ゴルファンタジスタ", 7, "WN", power=13000, brk=3,
    races=("giantdragon", "giant", "dragon"), pri=10, roles="fin atk dis blk",
    changex=lambda s, i, u: u.c.cost >= 5 and _is_giant(u.c),
    playrule=_pr_change(lambda c: c.cost >= 5 and _is_giant(c)),
    enterwatch=w_golfantasista, battleswap=bs_golfantasista,
    text="革命チェンジ：コスト5以上のジャイアント（自分のコスト5以上のジャイアントが攻撃する時、"
         "そのクリーチャーと手札にあるこのクリーチャーを入れ替えてもよい）。T・ブレイカー。"
         "相手のクリーチャーが出た時、次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない。"
         "自分の他のジャイアントが相手のクリーチャーとバトルする時、"
         "かわりにこのクリーチャーにバトルさせてもよい（タップは要らない）",
    source=SRC["k59_golfantasista"])


# ================================================================ チアスペース アカネ
def e_akane(s, i, u):
    """出た時、自分の山札の上から2枚を見て、1枚を手札に、もう1枚をマナゾーンに置く"""
    p = s.P[i]
    n = min(2, len(p.deck))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    k = max(top, key=lambda x: E.PRI[x] - 3 * p.hand.count(x))
    top.remove(k)
    p.hand.append(k)
    s.ev(f"　チアスペース アカネ：{BY_KEY[k].name} を手札へ")
    if top:
        s.add_mana(i, top[0], src="deck")
        s.ev(f"　チアスペース アカネ：{BY_KEY[top[0]].name} をマナゾーンへ")


add("k59_akane", "チアスペース アカネ", 5, "WN", power=5000, gs=True, mach=True,
    races=("giant", "snow"), pri=6, roles="acc draw atk trg",
    changex=lambda s, i, u: _is_giant(u.c),
    playrule=_pr_change(lambda c: _is_giant(c)),
    enter=e_akane,
    text="G・ストライク（相手の攻撃中に手札からこのカードを見せ、その攻撃を終わらせてもよい）。"
         "革命チェンジ：ジャイアント（自分のジャイアントが攻撃する時、そのクリーチャーと"
         "手札にあるこのクリーチャーを入れ替えてもよい）。マッハファイター。"
         "このクリーチャーが出た時、自分の山札の上から2枚を見る。"
         "そのうちの1枚を手札に加え、もう1枚をマナゾーンに置く",
    source=SRC["k59_akane"])


# ================================================================ 終の怒流牙 ドルゲユキムラ
def e_dorugeyukimura(s, i, u):
    """出た時、クリーチャーを3体までマナから手札に戻し、その後、手札を3枚までタップしてマナに置く"""
    p = s.P[i]
    back = []
    for _ in range(3):
        cands = [k for k in p.mana if BY_KEY[k].kind == "C" or BY_KEY[k].twin]
        if not cands:
            break
        k = max(cands, key=E.PRI.get)
        s.take_mana(i, k)
        p.hand.append(k)
        back.append(k)
        s.ev(f"　ドルゲユキムラ：マナの {BY_KEY[k].name} を手札へ")
    put = 0
    while put < 3:
        cands = [k for k in p.hand if k not in back and k != "k59_dorugeyukimura"]
        if not cands:
            break
        k = min(cands, key=E.PRI.get)
        p.hand.remove(k)
        s.add_mana(i, k, tapped=True, src="hand")
        s.ev(f"　ドルゲユキムラ：手札の {BY_KEY[k].name} をタップしてマナゾーンへ")
        put += 1


def fa_dorugeyukimura(s, i, av, cv):
    """G・ゼロ：バトルゾーンに自分のジャイアントが4枚以上あれば、コストを支払わずに召喚してもよい"""
    p = s.P[i]
    if "k59_dorugeyukimura" not in p.hand or len(_giants(s, i)) < 4:
        return []
    if s.evo_src(i, "k59_dorugeyukimura") is None:
        return []
    if s.fate(i, "k59_dorugeyukimura", "hand", True) != "ok":
        return []
    return [("x:k59_gzero",)]


def ap_dorugeyukimura(s, a):
    i = s.tp
    p = s.P[i]
    k = "k59_dorugeyukimura"
    if k not in p.hand or len(_giants(s, i)) < 4:
        return
    src = s.evo_src(i, k)
    if src is None:
        return
    p.hand.remove(k)
    s.ev("G・ゼロ：終の怒流牙 ドルゲユキムラ（コストを支払わずに召喚）")
    s.enter(i, k, "hand", True, on=src)


add("k59_dorugeyukimura", "終の怒流牙 ドルゲユキムラ", 8, "WN", power=17000, brk=3, evo="WN",
    races=("giant", "eartheater", "shinobi"), pri=11, roles="fin acc atk",
    evox=lambda s, i, u: _is_giant(u.c),
    playrule=_pr_change(_is_giant, 3, "進化元"),
    enter=e_dorugeyukimura, freeacts=fa_dorugeyukimura, actapply={"x:k59_gzero": ap_dorugeyukimura},
    text="G・ゼロ：バトルゾーンに自分のジャイアントが4枚以上あれば、このクリーチャーを"
         "コストを支払わずに召喚してもよい。進化：自分のジャイアント1体の上に置く。T・ブレイカー。"
         "このクリーチャーが出た時、クリーチャーを3体まで、自分のマナゾーンから手札に戻す。"
         "その後、自分の手札を3枚まで、タップしてマナゾーンに置く",
    note="マナから戻すのは重要度のいちばん高いクリーチャー、マナに置くのは手札のうち重要度のいちばん低い"
         "カード（いま戻したカードは置き直さない）という全デッキ共通の決まりで決めている。"
         "envtest の effect_smoke は場にジャイアントを置かない場面なので「使えた場面 0」になるが、"
         "進化元のジャイアントがいる場面では進化召喚もG・ゼロも動く（実際の対戦では使われている）",
    source=SRC["k59_dorugeyukimura"])


# ================================================================ 輝跡！シャイニングロード・マンティス／輝跡の大地
def e_mantis(s, i, u):
    """出た時、相手は自身のクリーチャーを2体選び、残りをすべてマナゾーンに置く"""
    o = s.P[1 - i]
    cre = [z for z in o.board if z.c.kind == "C"]
    if len(cre) <= 2:
        return
    keep = sorted(cre, key=s.val, reverse=True)[:2]       # 相手が選ぶので、相手の大事な2体が残る
    n = 0
    for z in cre:
        if z in keep or s.over:
            continue
        if move(s, i, z, "mana"):
            n += 1
    if n:
        s.ev(f"　シャイニングロード・マンティス：相手のクリーチャー{n}体を持ち主のマナゾーンへ")


def ts_mantis(s, i, u):
    """自分のターンのはじめに、カードを1枚、自分のマナゾーンから手札に戻してもよい"""
    p = s.P[i]
    if len(p.mana) < 5 or not p.mana:
        return                                 # マナ基盤を壊さない範囲でだけ戻す
    k = max(p.mana, key=E.PRI.get)
    if E.PRI[k] < 5:
        return
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　シャイニングロード・マンティス：マナの {BY_KEY[k].name} を手札へ")


def sp_mantis(s, i):
    """輝跡の大地：コスト8以下の進化ではないジャイアント1枚をマナから出し、クリーチャーならバトルさせる"""
    p = s.P[i]
    if s.manaexec(i):
        return
    best, bv = None, -1
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if c.cost > 8 or not _is_giant(c) or c.evo:
            continue
        if c.kind == "C":
            if s.fate(i, k, "mana", False) != "ok":
                continue
        elif c.kind != "T":
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is None:
        return
    s.take_mana(i, best)
    s.ev(f"　輝跡の大地：マナから {BY_KEY[best].name} を出す")
    if BY_KEY[best].kind == "T":
        s.place_tama(i, best)
        return
    z = s.enter(i, best, "mana", False)
    if z is None or z not in p.board:
        return
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　輝跡の大地：{z.c.name} と {t.c.name} をバトルさせる")
    s.battle(i, z, 1 - i, t)


add("k59_mantis", "輝跡！シャイニングロード・マンティス / 輝跡の大地", 8, "N", power=13000, brk=3,
    races=("giant", "insect"), twin=(7, "N", True), pri=11, roles="fin rem trg acc",
    enter=e_mantis, tstart=ts_mantis, spell=sp_mantis,
    text="クリーチャー側：T・ブレイカー。"
         "このクリーチャーが出た時、相手は自身のクリーチャーを2体選び、"
         "残りの自身のクリーチャーをすべてマナゾーンに置く。"
         "自分のターンのはじめに、カードを1枚、自分のマナゾーンから手札に戻してもよい。"
         "呪文側《輝跡の大地》（自然7・ジャイアント・スキル、S・トリガー）："
         "コスト8以下の、進化ではないジャイアントを1枚、自分のマナゾーンから出す。その後、"
         "このようにして出したのがクリーチャーなら、相手のクリーチャーを1体選んでもよい。その2体をバトルさせる",
    note="相手が残す2体は重要度のいちばん高い2体（相手が選ぶ側なので相手に有利な選び方）。"
         "ターンのはじめのマナ回収は、マナが5枚以上あり重要度5以上のカードがある時だけ行う",
    source=SRC["k59_mantis"])


# ================================================================ 学識妖精サイクリル
def e_cyclil(s, i, u):
    """出た時、自分の山札の上から1枚目をタップしてマナゾーンに置く"""
    s.ramp(i, 1, tapped=True)


def aw_cyclil(s, i, u):
    """各ターンに1度、自分のスノーフェアリーが攻撃する時、コスト4以下の呪文を墓地から手札に戻してもよい"""
    if u.c.kind != "C" or not race_like(u.c, "snow"):
        return
    p = s.P[i]
    for z in p.board:
        if z.k != "k59_cyclil" or z.x.get("k59_back") == s.turn:
            continue
        cands = [k for k in p.grave
                 if (BY_KEY[k].kind == "S" and BY_KEY[k].cost <= 4)
                 or (BY_KEY[k].twin and BY_KEY[k].twin[0] <= 4)]
        if not cands:
            return
        z.x["k59_back"] = s.turn
        k = max(cands, key=E.PRI.get)
        p.grave.remove(k)
        p.hand.append(k)
        s.ev(f"　学識妖精サイクリル：墓地の {BY_KEY[k].name} を手札へ")


add("k59_cyclil", "学識妖精サイクリル", 3, "WN", power=3000, mach=True,
    races=("giant", "snow"), pri=4, roles="acc draw atk",
    enter=e_cyclil, atkwatch=aw_cyclil,
    text="マッハファイター。このクリーチャーが出た時、自分の山札の上から1枚目をタップしてマナゾーンに置く。"
         "各ターンに1度、自分のスノーフェアリー・クリーチャーが攻撃する時、"
         "コスト4以下の呪文を1枚、自分の墓地から手札に戻してもよい",
    note="ツインパクトは呪文側のコストが4以下なら戻せる札として数えている",
    source=SRC["k59_cyclil"])


# ================================================================ 悪魔世界の閃光
def _yobinion(s, i, mx, what):
    """ヨビニオン：山札の上から1枚ずつ表向きにし、最初に出たコスト mx 未満のクリーチャーを出す"""
    p = s.P[i]
    flip, got = [], None
    while p.deck:
        k = p.deck.pop()
        c = BY_KEY[k]
        if c.kind == "C" and c.cost < mx:
            got = k
            break
        flip.append(k)
    if got is not None:
        if _summonable(BY_KEY[got]) and s.fate(i, got, "deck", False) == "ok":
            s.ev(f"　{what}：{BY_KEY[got].name} を出す")
            s.enter(i, got, "deck", False)
        else:
            flip.append(got)                   # 進化クリーチャーは進化元がなく出せない
    for k in flip:
        p.deck.insert(0, k)


def sp_walledflash(s, i):
    """ヨビニオンの後、自分のクリーチャーをすべてアンタップし、すべてにブロッカーを与える"""
    _yobinion(s, i, 6, "ヨビニオン")
    p = s.P[i]
    lim = s.turn + (1 if s.tp == i else 0)
    n = 0
    for z in p.board:
        if z.c.kind != "C":
            continue
        z.tap = False
        z.x["k59_blk"] = lim
        n += 1
    s.ev(f"　悪魔世界の閃光：自分のクリーチャー{n}体をアンタップし、次の自分のターンのはじめまでブロッカーを与える")


add("k59_walledflash", "悪魔世界の閃光", 6, "L", kind="S", trig=True, pri=7, roles="trg blk acc",
    spell=sp_walledflash,
    blockok=lambda s, u: u.x.get("k59_blk", -1) >= s.turn,
    text="S・トリガー。ヨビニオン（自分の山札の上から、この呪文よりコストが小さいクリーチャーが出るまで"
         "1枚ずつ表向きにしてもよい。そのクリーチャーを出し、残りを山札の下に置く）。"
         "自分のクリーチャーをすべてアンタップする。"
         "次の自分のターンのはじめまで、自分のクリーチャーすべてに「ブロッカー」を与える",
    source=SRC["k59_walledflash"])


# ================================================================ 戦術の天才 マロク
def _cross_free(s, i, k):
    """こうして出したクロスギアを、自分のクリーチャー1体にコストを支払わずにクロスする"""
    gu = None
    for z in reversed(s.P[i].board):
        if z.k == k and z.c.kind == "X" and not z.x.get("on"):
            gu = z
            break
    if gu is None:
        return
    cands = [z for z in s.P[i].board if z.c.kind == "C"]
    if not cands:
        return
    cu = max(cands, key=lambda z: (0 if z.tap else 1, s.power(i, z)))
    gu.x["on"] = cu.uid
    s.ev(f"　ただでクロス：{gu.c.name} → {cu.c.name}")


def _samurai_mek5(s, i):
    """サムライ・メクレイド5：山札の上3枚から、コスト5以下のサムライ1枚をコストを支払わずに使う"""
    p = s.P[i]
    m = min(3, len(p.deck))
    if m <= 0:
        return
    top = [p.deck.pop() for _ in range(m)]
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.cost > 5 or not race_like(c, "samurai") or c.kind not in "CX":
            continue
        if c.kind == "C" and not _summonable(c):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        p.hand.append(best)
        kind = BY_KEY[best].kind
        s.ev(f"　サムライ・メクレイド5：{BY_KEY[best].name} をコストを支払わずに使う")
        if free_play(s, i, best):
            if kind == "X":
                _cross_free(s, i, best)
        else:
            if best in p.hand:
                p.hand.remove(best)
            top.append(best)
    for k in top:
        p.deck.insert(0, k)


def ts_maroku(s, i, u):
    """自分のターンのはじめに、クロスギアがクロスされていればサムライ・メクレイド5をする"""
    if not gears_on(s, i, u):
        return
    _samurai_mek5(s, i)


def rep_maroku(s, i, u, dest, destroy_):
    """エスケープ：破壊される時、墓地に置くかわりに自分のシールド1つを手札に加えてもよい"""
    if u.k != "k59_maroku" or not destroy_:
        return False
    return _escape(s, i, "戦術の天才 マロク")


add("k59_maroku", "戦術の天才 マロク", 2, "L", power=2500,
    races=("starnoid", "machineeater", "armoredsamurai", "armored", "samurai"),
    pri=3, roles="acc blk",
    tstart=ts_maroku, leaverep=rep_maroku,
    text="自分のターンのはじめに、このクリーチャーにクロスギアがクロスされていれば、サムライ・メクレイド5する"
         "（山札の上から3枚を見て、その中のコスト5以下のサムライ1枚をコストを支払わずに使い、"
         "残りを山札の下に置く）。こうしてクロスギアを出したなら、"
         "それを自分のクリーチャー1体にコストを支払わずにクロスしてもよい。"
         "エスケープ（このクリーチャーが破壊される時、墓地に置くかわりに自分のシールドを1つ"
         "手札に加えてもよい。ただしその「S・トリガー」は使えない）",
    source=SRC["k59_maroku"])


# ================================================================ 鎧機天 シロフェシー
def e_shirophecy(s, i, u):
    """革命チェンジで出た時、次の自分のターンのはじめまで、相手はコスト5以下の呪文を唱えられない"""
    if s.atk is not u:
        return                                 # 革命チェンジ（攻撃の途中の入れ替え）で出た時だけ
    s.P[i].x["k59_shiro_lock"] = s.turn + 1
    s.ev("　鎧機天 シロフェシー：次の自分のターンのはじめまで、相手はコスト5以下の呪文を唱えられない")


def sl_shirophecy(s, i, cost):
    """i＝唱えようとしている側。シロフェシーの持ち主が掛けたロックが残っているか"""
    return cost <= 5 and s.P[1 - i].x.get("k59_shiro_lock", -1) >= s.turn


def t_shirophecy(s, i, u):
    """自分のターンの終わりに、このクリーチャーをアンタップする"""
    u.tap = False


add("k59_shirophecy", "鎧機天 シロフェシー", 4, "L", power=6500, brk=2, blocker=True,
    races=("armoredmechaseres", "armored", "mecha", "seres"), pri=6, roles="blk dis atk",
    changex=lambda s, i, u: u.c.cost >= 3 and (_is_armored(u.c) or _is_mecha(u.c)),
    playrule=_pr_change(lambda c: c.cost >= 3 and (_is_armored(c) or _is_mecha(c))),
    enter=e_shirophecy, spelllock=sl_shirophecy, tend=t_shirophecy,
    text="革命チェンジ：コスト3以上のアーマードまたはコスト3以上のメカ（それが攻撃する時、"
         "そのクリーチャーと手札にあるこのクリーチャーを入れ替えてもよい）。ブロッカー、W・ブレイカー。"
         "このクリーチャーが「革命チェンジ」によって出た時、次の自分のターンのはじめまで、"
         "相手はコスト5以下の呪文を唱えられない。自分のターンの終わりに、このクリーチャーをアンタップする",
    source=SRC["k59_shirophecy"])


# ================================================================ 一王二命三眼槍
def lose_ichiouni(s, i, how):
    """相手のターン中に負ける時、マナに闇と火があれば、手札のこのカードを表向きにし山札の下に置く"""
    p = s.P[i]
    if s.tp == i or "k59_ichiouni" not in p.hand:
        return False
    cv = set()
    for k in p.mana:
        cv |= set(_civ(k))
    if not {"D", "F"} <= cv:
        return False
    p.hand.remove("k59_ichiouni")
    p.deck.insert(0, "k59_ichiouni")
    s.ev("　一王二命三眼槍：手札から表向きにし山札の下に置いて、負けを置き換えた")
    return True


def e_ichiouni(s, i, u):
    """鬼エンド：出た時、シールドが1つもないプレイヤーがいれば、山札の下から1枚を墓地に置く。
    それがコスト5以下のクリーチャーなら出してもよい"""
    p = s.P[i]
    if s.P[0].sh and s.P[1].sh:
        return
    if not p.deck:
        return
    k = p.deck.pop(0)                          # 山札の下（deck は末尾が上）
    c = BY_KEY[k]
    s.ev(f"　鬼エンド：山札の下から {c.name} を墓地に置く")
    s.grave_put(i, k)
    if not (_summonable(c) and c.cost <= 5) or k not in p.grave or s.over:
        return
    if s.fate(i, k, "grave", False) != "ok":
        return
    p.grave.remove(k)
    s.ev(f"　鬼エンド：{c.name} を出す")
    s.enter(i, k, "grave", False)


add("k59_ichiouni", "一王二命三眼槍", 5, "DF", power=6000, brk=2, sa=True,
    races=("demonio", "onifuda"), pri=7, roles="atk fin acc",
    enter=e_ichiouni, loserep=lose_ichiouni,
    text="相手のターン中に自分がゲームに負ける時、自分のマナゾーンに闇と火の文明があれば、"
         "かわりに自分の手札にあるこのカードを表向きにし、山札の下に置いてもよい。"
         "スピードアタッカー、W・ブレイカー。"
         "鬼エンド：このクリーチャーが出た時、シールドが1つもないプレイヤーがいれば、"
         "自分の山札の下から1枚を墓地に置く。それがコスト5以下のクリーチャーなら、出してもよい",
    source=SRC["k59_ichiouni"])


# ================================================================ ガチャンコ ガチロボ
def _gachirobo_go(s, i, u):
    """出た時または攻撃する時、山札の上から3枚を表向きにし、すべて同じコストのクリーチャーなら出す"""
    p = s.P[i]
    n = min(3, len(p.deck))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    cs = {BY_KEY[k].cost for k in top}
    allc = all(BY_KEY[k].kind == "C" for k in top)
    if allc and len(cs) == 1:
        s.ev(f"　ガチャンコ ガチロボ：上{n}枚がすべてコスト{cs.pop()}のクリーチャー → すべて出す")
        rest = []
        for k in top:
            if s.over:
                rest.append(k)
            elif _summonable(BY_KEY[k]) and s.fate(i, k, "deck", False) == "ok":
                s.enter(i, k, "deck", False)
            else:
                rest.append(k)                 # 進化クリーチャーは進化元がなく出せない
        top = rest
    for k in top:
        p.deck.insert(0, k)


def unb_gachirobo(s, i, u):
    """相手のシールドが2つ以下なら、自分の水のクリーチャーはブロックされない"""
    return (u.c.kind == "C" and "W" in u.c.civ and s.has(i, "k59_gachirobo")
            and len(s.P[1 - i].sh) <= 2)


def atl_gachirobo(s, i, u, t):
    """相手のシールドが2つ以下なら、自分の水のクリーチャーは攻撃されない（i＝攻める側）"""
    return (t.c.kind == "C" and "W" in t.c.civ and s.has(1 - i, "k59_gachirobo")
            and len(s.P[i].sh) <= 2)


add("k59_gachirobo", "ガチャンコ ガチロボ", 6, "W", power=6000, brk=2,
    races=("greatmechaoh", "invader"), pri=8, roles="acc atk fin",
    enter=_gachirobo_go, attack=_gachirobo_go,
    unbok=unb_gachirobo, atktargetlock=atl_gachirobo,
    text="W・ブレイカー。このクリーチャーが出た時または攻撃する時、自分の山札の上から3枚を表向きにする。"
         "それがすべて同じコストのクリーチャーなら、そのクリーチャーをすべて出す。"
         "そうでなければ、好きな順序で山札の下に置く。"
         "相手のシールドが2つ以下なら、自分の水のクリーチャーは攻撃もブロックもされない",
    source=SRC["k59_gachirobo"])


# ================================================================ 特攻の忠剣ハチ公
def ae_hachiko(s, i, u):
    """攻撃の終わりに、相手とガチンコ・ジャッジ。勝ったら山札からハチ公を1体出してもよい"""
    if u.k != "k59_hachiko":
        return
    p = s.P[i]
    if not _gachinko(s, i):
        s.ev("　特攻の忠剣ハチ公：ガチンコ・ジャッジに負けた")
        return
    cands = [k for k in set(p.deck)
             if "特攻の忠剣ハチ公" in BY_KEY[k].name and _summonable(BY_KEY[k])]
    if not cands:
        s.ev("　特攻の忠剣ハチ公：ガチンコ・ジャッジに勝ったが、山札にハチ公がいない")
        return
    k = max(cands, key=E.PRI.get)
    if s.fate(i, k, "deck", False) != "ok":
        return
    p.deck.remove(k)
    s.ev(f"　特攻の忠剣ハチ公：ガチンコ・ジャッジに勝って {BY_KEY[k].name} を出す")
    s.enter(i, k, "deck", False)


add("k59_hachiko", "特攻の忠剣ハチ公", 4, "F", power=3000, sa=True,
    races=("flame", "command", "flamemonster", "hunter"), pri=4, roles="atk",
    atkend=ae_hachiko,
    text="このカードをデッキに何枚入れてもよい。スピードアタッカー。"
         "このクリーチャーの攻撃の終わりに、相手とガチンコ・ジャッジする。自分が勝ったら、自分の山札を見る。"
         "その中から、名前に《特攻の忠剣ハチ公》とあるクリーチャーを1体、出してもよい。その後、山札をシャッフルする"
         "（ガチンコ・ジャッジ：各プレイヤーは自身の山札の上から1枚目を見せ、それを一番下に置く。"
         "そのカードのコストが相手以上であれば、自分の勝ち）",
    note="「デッキに何枚入れてもよい」は、デッキの枚数の決まりが archetypes.py 側にあり担当外のため、"
         "カード側には書いていない（4枚までの扱いになる）。"
         "名前に《特攻の忠剣ハチ公》とあるクリーチャーは《愛羅特攻の忠剣ハチ公》も拾う",
    source=SRC["k59_hachiko"])


# ================================================================ ナ・チュラルゴ・デンジャー／ナチュラル・トラップ
def _naturalgo_put(s, i):
    """自然のコスト6以下のクリーチャー1体を、自分の手札またはマナゾーンから出してもよい"""
    p = s.P[i]
    zones = [("hand", p.hand)]
    if not s.manaexec(i):
        zones.append(("mana", p.mana))
    best, bv, src = None, -1, None
    for zn, zone in zones:
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if c.cost > 6 or "N" not in _civ(k) or not _summonable(c):
                continue
            if E.PRI[k] > bv and s.fate(i, k, zn, False) == "ok":
                best, bv, src = k, E.PRI[k], zn
    if best is None:
        return
    if src == "hand":
        p.hand.remove(best)
    else:
        s.take_mana(i, best)
    s.ev(f"　ナ・チュラルゴ・デンジャー：{'手札' if src == 'hand' else 'マナ'}から {BY_KEY[best].name} を出す")
    s.enter(i, best, src, False)


def e_naturalgo(s, i, u):
    _naturalgo_put(s, i)


def sw_naturalgo(s, i, k):
    """自分が名前に《トラップ》とある呪文を唱えた時も同じ効果"""
    if "トラップ" not in BY_KEY[k].name:
        return
    for _ in range(sum(1 for z in s.P[i].board if z.k == "k59_naturalgo")):
        if s.over:
            return
        _naturalgo_put(s, i)


def sp_naturalgo(s, i):
    """ナチュラル・トラップ：相手のクリーチャー1体を持ち主のマナゾーンに置く"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　ナチュラル・トラップ：{t.c.name} を持ち主のマナゾーンへ")
    move(s, i, t, "mana")


add("k59_naturalgo", "ナ・チュラルゴ・デンジャー / ナチュラル・トラップ", 7, "N", power=12000, brk=3,
    mach=True, races=("gransect", "giant"), twin=(6, "N", True), pri=10,
    roles="fin rem trg acc atk",
    enter=e_naturalgo, spellwatch=sw_naturalgo, spell=sp_naturalgo,
    text="クリーチャー側：マッハファイター、T・ブレイカー。"
         "このクリーチャーが出た時または自分が名前に《トラップ》とある呪文を唱えた時、"
         "自然のコスト6以下のクリーチャー1体を、自分の手札またはマナゾーンから出してもよい。"
         "呪文側《ナチュラル・トラップ》（自然6・S・トリガー）："
         "相手のクリーチャーを1体選び、持ち主のマナゾーンに置く",
    source=SRC["k59_naturalgo"])


# ================================================================ ボルシャック・ドラゴン／決闘者・チャージャー
def px_bolshack(s, i, u, atk):
    """攻撃中、自分の墓地にある火のカード1枚につき+1000"""
    if not atk:
        return 0
    return 1000 * sum(1 for k in s.P[i].grave if "F" in _civ(k))


def sp_bolshack(s, i):
    """決闘者・チャージャー：上3枚からボルシャックをすべて手札に。チャージャー：唱えた後マナゾーンへ"""
    p = s.P[i]
    n = min(3, len(p.deck))
    top = [p.deck.pop() for _ in range(n)]
    got = [k for k in top if "ボルシャック" in BY_KEY[k].name]
    for k in got:
        top.remove(k)
        p.hand.append(k)
    s.ev(f"　決闘者・チャージャー：上{n}枚からボルシャック{len(got)}枚を手札へ")
    for k in top:
        p.deck.insert(0, k)
    s.add_mana(i, "k59_bolshack")
    s.ev("　チャージャー：決闘者・チャージャーをマナゾーンへ")


add("k59_bolshack", "ボルシャック・ドラゴン / 決闘者・チャージャー", 6, "F", power=6000, brk=2,
    races=("armoreddragon", "dragon"), twin=(3, "F", False), nograve=True, pri=8,
    roles="atk draw acc",
    powerx=px_bolshack, spell=sp_bolshack,
    text="クリーチャー側：W・ブレイカー。"
         "攻撃中、このクリーチャーのパワーを、自分の墓地にある火のカード1枚につき+1000する。"
         "呪文側《決闘者・チャージャー》（火3）：自分の山札の上から3枚を表向きにする。"
         "その中から、名前に《ボルシャック》とあるカードをすべて手札に加え、残りを好きな順序で山札の下に置く。"
         "チャージャー（この呪文を唱えた後、墓地に置くかわりにマナゾーンに置く）",
    note="《ボルシャック・ドラゴン》（単面・cards3 の n_bolshack）とは別のカード。"
         "墓地の火のカードは、ツインパクトの片面が火ならそれも数える",
    source=SRC["k59_bolshack"])


# ================================================================ ネオ・ボルシャック・ドラゴン／ボルシャックゾーン
def px_neobolshack(s, i, u, atk):
    """パワーアタッカー+4000"""
    return 4000 if atk else 0


def sp_neobolshack(s, i):
    """ボルシャックゾーン：自分の山札の上から1枚をマナゾーンに置く"""
    s.ramp(i, 1, tapped=False)


add("k59_neobolshack", "ネオ・ボルシャック・ドラゴン / ボルシャックゾーン", 8, "F", power=11000, brk=3,
    races=("armoreddragon", "dragon"), twin=(2, "N", False), pri=9, roles="fin atk acc",
    powerx=px_neobolshack, spell=sp_neobolshack,
    text="クリーチャー側：パワーアタッカー+4000（攻撃中、このクリーチャーのパワーを+4000する）、T・ブレイカー。"
         "呪文側《ボルシャックゾーン》（自然2）：自分の山札の上から1枚をマナゾーンに置く",
    source=SRC["k59_neobolshack"])
