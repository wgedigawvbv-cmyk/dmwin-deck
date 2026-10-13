"""担当16：DMGP2025-2nd Day2 オリジナルの入賞デッキに入っていた未実装カード13枚

出典：公式テキストカバレージの入賞デッキリスト
      https://dm.takaratomy.co.jp/coverage/dmgp2025-2ndb_deck
      （順位表記の無い大会の4リスト。「闇王ゼーロ＋不死鳥縫合 ブラック・ビッグバン」系）

  この札束に入っている新しい仕組み
    ・闇王ゼーロの別のコスト（手札の闇3枚を捨て、自分の闇のクリーチャー3体を破壊して、ただで唱える）
    ・「山札が0枚でも負けない」＋「引く時に山札が0枚なら、かわりに墓地からクリーチャーを出す」
      （不死鳥縫合 ブラック・ビッグバン）。これと《サイバー・J・イレブン》の特殊勝利（水のクリーチャー11体）
      が、このデッキの勝ち筋。
    ・「カードが自分のシールドゾーンに置かれた時」の誘発（DARK MEMORY CONTAINER）
    ・EXライフ／ディスペクター・ディスタスのコスト軽減（戦国接続 ギャラクテスト・シデンシーザー）
    ・ムゲンクライム1（罪無 ターボ兆）／ヨビニオン（ティンパニ＝シンバリー）
    ・革命2でS・トリガーを得る呪文（理想と平和の決断）／2回選ぶモード呪文
    ・「シールド化」による除去（理想と平和の決断の3つめのモード）

  調べ直して確かめたところ
    13枚すべてについて dmwiki.net のカードページを2回ずつ（別の質問で）読み、コスト・文明・種族・パワー・
    ブレイク数・能力の本文がどちらも一致することを確かめた。
    《サイバー・J・イレブン / 「みんなと戦えてよかった♥」》だけは dmwiki のツインパクト名のページが
    短縮形URLでしか開けなかったので、カードラッシュの商品ページ（型番 25EX1 21/89）の本文と
    突き合わせて確かめた（呪文側はコスト1・水、1枚引いて唱えた後は山札の下）。
    cardspec と食い違っていた点はなし（この担当分に cardspec ファイルはなく、デッキリストから調べた）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, move, opp_all
from envcards.env0 import discard_choice, exlife_enter, exlife_rep

W = "https://dmwiki.net/"
SRC = {
    "ea_jigokugaeri": W + "《～地獄帰りの騎士～》",
    "ea_darkmemory": W + "《DARK MEMORY CONTAINER》",
    "ea_galactest": W + "《戦国接続 ギャラクテスト・シデンシーザー》",
    "ea_bigbang": W + "《不死鳥縫合 ブラック・ビッグバン》",
    "ea_yamiouzero": W + "《闇王ゼーロ》",
    "ea_rrr": W + "《R・R・R》",
    "ea_turbocho": W + "《罪無 ターボ兆》",
    "ea_viljaberin": W + "《偽槍縫合 ヴィルジャベリン》",
    "ea_jeleven": "https://www.cardrush-dm.jp/product/51703",
    "ea_timpani": W + "《ティンパニ＝シンバリー》",
    "ea_gigagedo": W + "《魔獣星樹ギガゲドー》",
    "ea_shikumi": W + "《影世界のシクミ》",
    "ea_risoheiwa": W + "《理想と平和の決断》",
}


# ================================================================ 共通の道具
def _civs(k):
    """そのカードの文明（ツインパクトは両面の文明をまとめたもの）"""
    return E.MCIV[k]


def _draw(s, i, n):
    """カードを引く。山札が0枚で不死鳥縫合 ブラック・ビッグバンがいれば、かわりに墓地からクリーチャーを出す"""
    p = s.P[i]
    for _ in range(n):
        if s.over:
            return
        if not p.deck:
            if not s.has(i, "ea_bigbang"):
                return
            if s.revive(i, lambda c: True, "grave") is None:
                return
            s.ev("　ブラック・ビッグバン：山札が0枚なので、引くかわりに墓地からクリーチャーを出す")
            continue
        s.draw(i, 1)


def _add_shield(s, i, k=None, up=False):
    """シールドを1つ増やす（「シールドゾーンに置かれた時」はエンジンの shieldin= が見るので、ここでは何もしない）"""
    return s.add_shield(i, k, up)


def _playable_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化クリーチャーは進化元が要るので除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


# ================================================================ ～地獄帰りの騎士～
def e_jigokugaeri(s, i, u):
    """出た時、3枚引いてもよい。そうしたら手札を2枚捨て、山札の上から1枚をシールド化する"""
    p = s.P[i]
    if len(p.deck) < 3 and not s.has(i, "ea_bigbang"):
        return                                  # 引ききって山札切れで負けるだけなら引かない
    _draw(s, i, 3)
    for _ in range(2):
        discard_choice(s, i)
    _add_shield(s, i)


add("ea_jigokugaeri", "～地獄帰りの騎士～", 3, "LWD", power=3000, evo="LWD", neo=True,
    races=("arkseraphim", "steamknight"), pri=5, roles="draw shd",
    enter=e_jigokugaeri,
    text="NEO進化：光・水・闇のどれかのクリーチャー1体の上に置いてもよい（進化元なしで召喚してもよい）。"
         "出た時、3枚引いてもよい。引いたなら、自分の手札を2枚捨てて、"
         "自分の山札の上から1枚を新しいシールドとして置く",
    source=SRC["ea_jigokugaeri"])


# ================================================================ DARK MEMORY CONTAINER
def e_darkmemory(s, i, u):
    _draw(s, i, 2)


def si_darkmemory(s, j, k, up):
    """カードが自分のシールドゾーンに置かれた時、このクリーチャーを自分の墓地から出してもよい

    全体に効く差し込み口なので、墓地にこのカードがある時だけ働く（1枚につき1体ずつ出す）。"""
    p = s.P[j]
    if "ea_darkmemory" not in p.grave or s.over:
        return
    for _ in range(p.grave.count("ea_darkmemory")):
        if s.over or "ea_darkmemory" not in p.grave:
            break
        if s.fate(j, "ea_darkmemory", "grave", False) != "ok":
            break
        p.grave.remove("ea_darkmemory")
        s.ev("　DARK MEMORY CONTAINER：シールドが置かれたので墓地から出る")
        s.enter(j, "ea_darkmemory", "grave", False)


add("ea_darkmemory", "DARK MEMORY CONTAINER", 5, "LWD", power=5500, blocker=True,
    races=("steamknight",), pri=6, roles="draw blk",
    enter=e_darkmemory, shieldin=si_darkmemory,
    text="ブロッカー。出た時、2枚引く。"
         "カードが自分のシールドゾーンに置かれた時、このクリーチャーを自分の墓地から出してもよい。"
         "（公式の種族表記は「？？？／スチーム・ナイト」で、？？？の側は何とも組み合わない）",
    source=SRC["ea_darkmemory"])


# ================================================================ 戦国接続 ギャラクテスト・シデンシーザー
def e_galactest(s, i, u):
    """EXライフ。出た時、自分のマナゾーンか墓地からカードを3枚まで手札に戻す"""
    exlife_enter(s, i, u)
    p = s.P[i]
    got = 0
    while got < 3 and p.grave:
        k = max(p.grave, key=E.PRI.get)
        p.grave.remove(k)
        p.hand.append(k)
        s.ev(f"　ギャラクテスト：墓地の {BY_KEY[k].name} を手札へ")
        got += 1
    while got < 3 and len(p.mana) > p.mused + 2:
        k = max(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        p.hand.append(k)
        s.ev(f"　ギャラクテスト：マナの {BY_KEY[k].name} を手札へ")
        got += 1


def ca_galactest(s, i, k, cur):
    """自分のディスタスとディスペクターの召喚コストを2少なくする（1より少なくはならない）"""
    if cur <= 1 or not any(z.k == "ea_galactest" for z in s.P[i].board):
        return cur
    r = BY_KEY[k].races
    if "distas" in r or "dispector" in r:
        return max(1, cur - 2)
    return cur


add("ea_galactest", "戦国接続 ギャラクテスト・シデンシーザー", 8, "LDN", power=14000, brk=2,
    races=("dispector", "knight", "samurai"), pri=10, roles="draw acc shd fin",
    enter=e_galactest, leaverep=exlife_rep, costaura=ca_galactest,
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。W・ブレイカー。"
         "出た時、自分のマナゾーンまたは墓地からカードを3枚まで選び、手札に戻す"
         "（墓地の重要度の高いカードから取り、足りない分だけマナからも取る。"
         "ただしそのターンに使うマナを2つは残す）。"
         "自分のディスタスとディスペクターの召喚コストを2少なくする（1より少なくはならない）",
    source=SRC["ea_galactest"])


# ================================================================ 不死鳥縫合 ブラック・ビッグバン
def _bb_fill(s, i, u):
    """出た時または攻撃する時、山札の上から2枚を墓地に置き、その後2枚引く"""
    s.mill(i, 2)
    _draw(s, i, 2)


def e_bigbang(s, i, u):
    exlife_enter(s, i, u)
    _bb_fill(s, i, u)


def lose_bigbang(s, i, how):
    """自分の山札が0枚でも負けない"""
    return how == "山札切れ" and s.has(i, "ea_bigbang")


add("ea_bigbang", "不死鳥縫合 ブラック・ビッグバン", 8, "WDN", power=13000, brk=3, blocker=True,
    races=("dispector", "phoenix"), pri=12, roles="fin blk draw shd",
    enter=e_bigbang, attack=_bb_fill, leaverep=exlife_rep, loserep=lose_bigbang,
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。ブロッカー、T・ブレイカー。"
         "出た時または攻撃する時、自分の山札の上から2枚を墓地に置き、その後2枚引く。"
         "自分の山札が0枚でも、自分はゲームに負けない。"
         "自分がカードを引く時、自分の山札が0枚なら、かわりにクリーチャー1体を自分の墓地から出してもよい",
    note="「引く時に山札が0枚なら、かわりに墓地からクリーチャーを出す」は、"
         "引く1枚ぶんを置き換える差し込み口（DRAWREP）がエンジンにないため"
         "（`drawwatch=` は引けた後の見張りなので置き換えには使えない）、"
         "この担当のカードが引かせる分（ブラック・ビッグバン自身・DARK MEMORY CONTAINER・地獄帰りの騎士・"
         "ヴィルジャベリン・みんなと戦えてよかった♥）にだけ効くようにした。"
         "ターンのはじめの1枚や、ほかの担当のカードのドローでは置き換わらない。"
         "また、エンジンの mill（山札の上から墓地に置く）は山札を1枚残す作りなので、"
         "この能力だけで山札を0枚にすることはできない（引いて0枚にする必要がある）",
    status="partial", source=SRC["ea_bigbang"])


# ================================================================ 闇王ゼーロ
def sp_yamiouzero(s, i):
    """自分の山札の上から4枚を墓地に置き、その後、闇のクリーチャー1体を自分の墓地から出す"""
    s.mill(i, 4)
    s.revive(i, lambda c: "D" in c.civ, "grave")


def _zeero_ready(s, i):
    """ゼーロの別のコストを払えるか：手札の闇3枚（この呪文以外）と、自分の闇のクリーチャー3体"""
    p = s.P[i]
    rest = list(p.hand)
    rest.remove("ea_yamiouzero")
    dark = sum(1 for k in rest if "D" in _civs(k))
    cre = sum(1 for z in p.board if z.c.kind == "C" and "D" in z.c.civ)
    return dark >= 3 and cre >= 3


def fa_yamiouzero(s, i, av, cv):
    p = s.P[i]
    if "ea_yamiouzero" not in p.hand or not s.spell_ok(i, 8):
        return []
    if not _zeero_ready(s, i):
        return []
    return [("x:zeero",)]


def ap_yamiouzero(s, a):
    i = s.tp
    p = s.P[i]
    if "ea_yamiouzero" not in p.hand or not _zeero_ready(s, i):
        return
    p.hand.remove("ea_yamiouzero")
    for _ in range(3):
        cands = [k for k in p.hand if "D" in _civs(k)]
        if not cands:
            break
        s.discard(i, min(cands, key=E.PRI.get))
    for _ in range(3):
        mine = [z for z in p.board if z.c.kind == "C" and "D" in z.c.civ]
        if not mine:
            break
        s.leave(i, min(mine, key=s.val), "grave", destroy=True)
    s.ev("呪文：闇王ゼーロ（手札の闇3枚を捨て、自分の闇のクリーチャー3体を破壊して、コストを支払わずに）")
    s.cast(i, "ea_yamiouzero")


add("ea_yamiouzero", "闇王ゼーロ", 8, "D", kind="S", pri=10, roles="fin acc rem",
    spell=sp_yamiouzero, freeacts=fa_yamiouzero, actapply={"x:zeero": ap_yamiouzero},
    text="闇王ゼーロ：コストを支払うかわりに、自分の手札から闇のカード3枚を捨て、"
         "自分の闇のクリーチャー3体を破壊して、この呪文を唱えてもよい。"
         "自分の山札の上から4枚を墓地に置く。その後、闇のクリーチャー1体を自分の墓地から出す",
    note="2026年3月16日から殿堂入り（デッキに1枚まで）。"
         "捨てる3枚は手札のうち重要度の低い闇のカード、破壊する3体は自分の闇のクリーチャーのうち"
         "失うのがいちばん安い3体を選ぶ（全デッキ共通の決まり）",
    source=SRC["ea_yamiouzero"])


# ================================================================ R・R・R
def sp_rrr(s, i):
    """次のうちいずれか1つを選ぶ（効き目のいちばん大きいものを選ぶ）"""
    p = s.P[i]
    unt = opp_all(s, i, lambda z: not z.tap)
    tapd = opp_all(s, i, lambda z: z.tap)
    va = sum(s.val(z) for z in unt)
    vc = sum(s.val(z) for z in tapd)
    vb = (3 if len(p.deck) > 1 else -1) * (2 if len(p.sh) <= 1 else 1)
    if unt and va >= vc and va >= vb:
        s.ev("　R・R・R：相手のアンタップしているクリーチャーをすべて手札に戻す")
        for z in unt:
            move(s, i, z, "hand")
    elif tapd and vc >= vb:
        s.ev("　R・R・R：相手のタップしているクリーチャーをすべてマナゾーンに置く")
        for z in tapd:
            move(s, i, z, "mana")
    else:
        s.ev("　R・R・R：自分の山札の上をシールド化する")
        _add_shield(s, i)
        if len(p.sh) <= 2:
            _add_shield(s, i)


add("ea_rrr", "R・R・R", 6, "LWN", kind="S", trig=True, pri=7, roles="rem trg shd",
    spell=sp_rrr,
    text="S・トリガー。次のうちいずれか1つを選ぶ。"
         "(1)相手のアンタップしているクリーチャーをすべて、持ち主の手札に戻す／"
         "(2)自分の山札の上から1枚をシールド化する。その後、自分のシールドが2つ以下なら、もう1枚シールド化する／"
         "(3)相手のタップしているクリーチャーをすべて、持ち主のマナゾーンに置く。"
         "どれを選ぶかは、取り除ける相手のカードの重要度の合計がいちばん大きいものを選ぶ（全デッキ共通の決まり）",
    source=SRC["ea_rrr"])


# ================================================================ 罪無 ターボ兆
def _mugen_cands(s, i):
    return [z for z in s.P[i].board if z.c.kind == "C" and not z.tap]


def fa_turbocho(s, i, av, cv):
    """ムゲンクライム1：自分のクリーチャー1体をタップし、闇の1マナで手札または墓地から召喚する"""
    p = s.P[i]
    if av < 1 or "D" not in cv or not _mugen_cands(s, i):
        return []
    out = []
    for zn, zone in (("hand", p.hand), ("grave", p.grave)):
        if "ea_turbocho" in zone and s.fate(i, "ea_turbocho", zn, True) == "ok":
            out.append(("x:mugen_turbo", zn))
    return out


def ap_turbocho(s, a):
    i = s.tp
    p = s.P[i]
    zn = a[1]
    zone = p.hand if zn == "hand" else p.grave
    if "ea_turbocho" not in zone or len(p.mana) - p.mused < 1:
        return
    cands = _mugen_cands(s, i)
    if not cands:
        return
    s.tap_cre(i, min(cands, key=s.val))
    p.mused += 1
    zone.remove("ea_turbocho")
    s.ev(f"ムゲンクライム1：罪無 ターボ兆（{'手札' if zn == 'hand' else '墓地'}から召喚）")
    s.enter(i, "ea_turbocho", zn, True)


def bf_turbocho(s, ai, au, di, du, a_dies, d_dies):
    """バトルに勝った時、このクリーチャーを破壊する"""
    if au.k == "ea_turbocho" and d_dies and not a_dies:
        a_dies = True
    if du.k == "ea_turbocho" and a_dies and not d_dies:
        d_dies = True
    return a_dies, d_dies


add("ea_turbocho", "罪無 ターボ兆", 3, "D", power=3000, blocker=True, noatk=True,
    races=("mafigang", "teamzero"), pri=3, roles="blk",
    freeacts=fa_turbocho, actapply={"x:mugen_turbo": ap_turbocho}, battlefx=bf_turbocho,
    text="ムゲンクライム1：自分のクリーチャー1体をタップし、闇の1マナを支払って、"
         "このクリーチャーを自分の手札または墓地から召喚してもよい。"
         "ブロッカー。このクリーチャーは攻撃できない。"
         "このクリーチャーがバトルに勝った時、このクリーチャーを破壊する",
    source=SRC["ea_turbocho"])


# ================================================================ 偽槍縫合 ヴィルジャベリン
def e_viljaberin(s, i, u):
    """EXライフ。出た時、相手のバトルゾーン・マナゾーン・手札から1枚ずつ、相手の墓地に置かせる"""
    exlife_enter(s, i, u)
    o = s.P[1 - i]
    t = s.target(i)
    if t is not None:
        move(s, i, t, "grave")
    if o.mana:
        k = max(o.mana, key=E.PRI.get)
        s.take_mana(1 - i, k)
        s.grave_put(1 - i, k)
        s.ev(f"　ヴィルジャベリン：相手のマナの {BY_KEY[k].name} を墓地へ")
    s.discard_random(1 - i)


def t_viljaberin(s, i, u):
    """自分のターンの終わりに、プレイヤーを1人選ぶ（自分を選ぶ）。そのプレイヤーは2枚引く"""
    _draw(s, i, 2)


add("ea_viljaberin", "偽槍縫合 ヴィルジャベリン", 10, "WDN", power=15000, brk=3,
    races=("dispector", "kingcommanddragon", "command", "dragon", "liquid"), pri=12,
    roles="fin rem dis draw",
    enter=e_viljaberin, tend=t_viljaberin, leaverep=exlife_rep,
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。T・ブレイカー。"
         "出た時、相手のカードをバトルゾーンから1枚、マナゾーンから1枚、さらに相手の手札から見ないで1枚選び、"
         "相手はそれらを自身の墓地に置く。"
         "自分のターンの終わりに、プレイヤーを1人選ぶ（自分を選ぶ）。そのプレイヤーは2枚引く",
    source=SRC["ea_viljaberin"])


# ================================================================ サイバー・J・イレブン／「みんなと戦えてよかった♥」
def _water_cre(s, i):
    return sum(1 for z in s.P[i].board if z.c.kind == "C" and "W" in z.c.civ)


def _jeleven_win(s):
    for j in (0, 1):
        if s.has(j, "ea_jeleven") and _water_cre(s, j) >= 11:
            s.win(j, "サイバー・J・イレブン")
            return


def sp_jeleven(s, i):
    """呪文側「みんなと戦えてよかった♥」：1枚引く。唱えた後は墓地ではなく山札の下へ"""
    _draw(s, i, 1)
    s.P[i].deck.insert(0, "ea_jeleven")


add("ea_jeleven", "サイバー・J・イレブン / 「みんなと戦えてよかった♥」", 11, "W", power=11000, brk=2,
    races=("cybercommand",), twin=(1, "W", False), nograve=True, pri=10, roles="fin draw",
    spell=sp_jeleven,
    enterwatch=lambda s, i, u: _jeleven_win(s),
    tstartall=lambda s, i, u: _jeleven_win(s),
    text="クリーチャー側：M・ソウル、W・ブレイカー。自分の水のクリーチャーが11体以上あれば、自分はゲームに勝つ。"
         "呪文側「みんなと戦えてよかった♥」（コスト1・水）：1枚引く。"
         "この呪文を唱えた後、墓地に置くかわりに山札の下に置く",
    note="M・ソウルは、このシミュレーターに種族をまたぐ合体の仕組みがないので、何とも組み合わない印だけ。"
         "特殊勝利の判定は、クリーチャーが出た時と自分のターンのはじめに見る",
    source=SRC["ea_jeleven"])


# ================================================================ ティンパニ＝シンバリー
def e_timpani(s, i, u):
    """ヨビニオン：召喚した時、山札の上から、これよりコストの小さいクリーチャーが出るまで表向きにする"""
    if not u.x.get("summoned"):
        return
    p = s.P[i]
    flipped, got = [], None
    while len(p.deck) > 1:
        k = p.deck.pop()
        c = BY_KEY[k]
        if c.kind == "C" and c.cost < u.c.cost:
            got = k
            break
        flipped.append(k)
    if got is not None:
        if _playable_cre(BY_KEY[got]):
            s.ev(f"　ヨビニオン：{BY_KEY[got].name} を出す")
            s.enter(i, got, "deck", False)
        else:
            flipped.append(got)             # 進化クリーチャーは進化元がなく出せない
    for k in flipped:
        p.deck.insert(0, k)


def w_timpani(s, i, u):
    """各ターン、自分の2体目のクリーチャーが出た時、自身を破壊して、相手に自分のクリーチャー1体を破壊させる"""
    if u.c.kind != "C":
        return
    p = s.P[i]
    if p.ent != 2 or p.x.get("ea_timpani_t") == s.turn:
        return
    z = next((x for x in p.board if x.k == "ea_timpani"), None)
    if z is None:
        return
    cands = [x for x in s.P[1 - i].board if x.c.kind == "C"]
    if not cands:
        return
    t = min(cands, key=s.val)               # 相手が選ぶので、相手のいちばん安いクリーチャー
    if s.val(t) + 1 < s.val(z):
        return                              # 損な取り引きならしない（重要度で決める共通の決まり）
    p.x["ea_timpani_t"] = s.turn
    s.ev("　ティンパニ＝シンバリー：自身を破壊し、相手は自分のクリーチャー1体を破壊する")
    s.leave(i, z, "grave", destroy=True)
    if t in s.P[1 - i].board:
        s.leave(1 - i, t, "grave", destroy=True)


add("ea_timpani", "ティンパニ＝シンバリー", 4, "D", power=4000, blocker=True,
    races=("abyssroyal", "abyss"), pri=6, roles="blk rem acc",
    enter=e_timpani, enterwatch=w_timpani,
    text="ヨビニオン：このクリーチャーを召喚した後、自分の山札の上から1枚ずつ表向きにする。"
         "こうして最初に出た、このクリーチャーよりコストの小さいクリーチャーを出し、残りを山札の下に置く。"
         "ブロッカー。"
         "各ターン、自分の2体目のクリーチャーが出た時、このクリーチャーを破壊してもよい。"
         "そうしたら、相手は自分のクリーチャー1体を選んで破壊する",
    source=SRC["ea_timpani"])


# ================================================================ 魔獣星樹ギガゲドー
def w_gigagedo(s, i, u):
    """自分のクリーチャーが出た時、自分のシールドを1つ手札に戻してもよい（S・トリガーは使えない）"""
    if u.c.kind != "C":
        return
    p = s.P[i]
    for _ in range(sum(1 for z in p.board if z.k == "ea_gigagedo")):
        if len(p.sh) < 3:
            return                          # シールドは2つまでは減らさない（革命2の条件にも合う）
        cands = [j for j, (kk, up) in enumerate(p.sh) if not up]
        if not cands:
            return
        j = max(cands, key=lambda x: E.PRI[p.sh[x][0]])
        k = p.sh.pop(j)[0]
        p.hand.append(k)
        s.shield_left()
        s.ev(f"　ギガゲドー：シールドの {BY_KEY[k].name} を手札に戻した（S・トリガーは使えない）")


def d_gigagedo(s, i, u):
    """破壊された時、自分の山札の上から1枚をシールド化してもよい"""
    _add_shield(s, i)


add("ea_gigagedo", "魔獣星樹ギガゲドー", 3, "LD", power=5000, blocker=True, noatkp=True,
    races=("chimera", "starlighttree"), pri=5, roles="blk draw shd",
    enterwatch=w_gigagedo, destroyed=d_gigagedo,
    text="ブロッカー。このクリーチャーはプレイヤーを攻撃できない。"
         "自分のクリーチャーが出た時、自分のシールドを1つ選び、持ち主の手札に戻してもよい"
         "（そのS・トリガーは使えない）。"
         "このクリーチャーが破壊された時、自分の山札の上から1枚をシールド化してもよい。"
         "戻すシールドは重要度のいちばん高い裏向きのシールドを選び、シールドが3つ以上ある時だけ戻す",
    source=SRC["ea_gigagedo"])


# ================================================================ 影世界のシクミ
def sp_shikumi(s, i):
    """自分の山札の上から3枚を墓地に置き、コスト3以下のクリーチャー1体を墓地か手札から出す"""
    s.mill(i, 3)
    p = s.P[i]
    best, bv, src = None, -1, None
    for zn, zone in (("grave", p.grave), ("hand", p.hand)):
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if not _playable_cre(c) or c.cost > 3:
                continue
            if E.PRI[k] > bv and s.fate(i, k, zn, False) == "ok":
                best, bv, src = k, E.PRI[k], zn
    if best is None:
        return
    (p.grave if src == "grave" else p.hand).remove(best)
    s.ev(f"　影世界のシクミ：{'墓地' if src == 'grave' else '手札'}から {BY_KEY[best].name} を出す")
    z = s.enter(i, best, src, False)
    if z is not None:
        z.x["ea_blk"] = s.turn + (1 if s.tp == i else 0)


add("ea_shikumi", "影世界のシクミ", 4, "LD", kind="S", trig=True, pri=5, roles="trg acc blk",
    spell=sp_shikumi,
    blockok=lambda s, u: u.x.get("ea_blk", -1) >= s.turn,
    text="S・トリガー。自分の山札の上から3枚を墓地に置く。その後、コスト3以下のクリーチャー1体を"
         "自分の墓地または手札から出してもよい。次の自分のターンのはじめまで、"
         "そのクリーチャーは「ブロッカー」を得る",
    source=SRC["ea_shikumi"])


# ================================================================ 理想と平和の決断
def tg_risoheiwa(s, di, k):
    """革命2：自分のシールドが2つ以下なら、シールドゾーンにあるこの呪文はS・トリガーを得る"""
    return k == "ea_risoheiwa" and len(s.P[di].sh) <= 2


def _rh_mode1(s, i):
    """山札の上2枚を表向きにし、光と水のカードすべてを手札に加え、残りを山札の下に置く"""
    p = s.P[i]
    n = min(2, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    got = [k for k in top if set(_civs(k)) & set("LW")]
    for k in got:
        top.remove(k)
        p.hand.append(k)
    s.ev(f"　理想と平和の決断：上2枚から光・水のカード{len(got)}枚を手札へ")
    for k in top:
        p.deck.insert(0, k)


def _rh_one(s, i):
    p = s.P[i]
    t = s.target(i, lambda z: z.c.cost <= 3, kinds="CTX")
    v3 = s.val(t) if t is not None else -1
    v1 = 4 if len(p.deck) > 1 else -1
    v2 = (3 + (3 if len(p.sh) <= 2 else 0)) if len(p.deck) > 1 else -1
    if t is not None and v3 >= v1 and v3 >= v2:
        s.ev(f"　理想と平和の決断：{t.c.name} をシールド化する")
        s.leave(1 - i, t, "shield", by_opp=True)
    elif v1 >= v2 and v1 > 0:
        _rh_mode1(s, i)
    elif v2 > 0:
        s.ev("　理想と平和の決断：自分の山札の上をシールド化する")
        _add_shield(s, i)


def sp_risoheiwa(s, i):
    for _ in range(2):
        if s.over:
            return
        _rh_one(s, i)


add("ea_risoheiwa", "理想と平和の決断", 4, "LW", kind="S", pri=6, roles="trg rem shd draw",
    spell=sp_risoheiwa, trigok=tg_risoheiwa,
    text="革命2：自分のシールドが2つ以下なら、シールドゾーンから手札に加えるこの呪文にS・トリガーを与える。"
         "次の中から2回選ぶ（同じものを選んでもよい）。"
         "(1)自分の山札の上から2枚を表向きにし、その中の光と水のカードをすべて手札に加え、"
         "残りを好きな順序で山札の下に置く／"
         "(2)自分の山札の上から1枚をシールド化する／"
         "(3)コスト3以下のエレメント1つを選び、シールド化する。"
         "どれを選ぶかは、取り除ける相手のエレメントの重要度と、シールドの残りの枚数で機械的に決める",
    source=SRC["ea_risoheiwa"])
