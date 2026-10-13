"""担当48：DM26-SD1「ドキドキつよいデッキ 25の王道」の未実装カード15枚

  key の接頭辞は `k48_`。

  この15枚に入っている仕組み
    ・革命0（閃光の精霊カンビアーレ）＝シールドが1つもない時、シールドから手札に加えたこのカードを
      コストを支払わずに召喚する（`shieldcast=` で受ける）
    ・ガチンコ・ジャッジ（青銅のバンビシカット／「我が力、しかと見よ!」）
    ・マナゾーンから召喚＋ヨビニオン＋破壊置換（ヨビニオン・トライブ）
    ・シンパシー（九番龍 ジゴクバンカー Par459）
    ・「ターンの残りをとばす」（終末の監視者 ジ・ウォッチ）＝`s.stop`
    ・「相手の出た時の能力をトリガーさせない」（終末縫合王 ザ＝キラー・キーナリー）＝`entertriglock=`
    ・ハイパーエナジー＋ガードマン＋「可能ならクリーチャーを攻撃する」＋マナ3枚で離れない
      （哀しみの夜 シンベロム・カタルシス）
    ・墓地から自力で戻ってくる「各ターンの終わり」の能力（死神覇王 ブラックXENARCH）＝`tendp=`
    ・アタック・チャンス（終末王秘伝オリジナルフィナーレ）
    ・SSS級侵略［天災］（SSS級天災 デッドダムド）＝`invade=` ＋ `INVZONE`（バトルゾーンも含む）

  調べ直して確かめたこと（各カードを別の質問で2回以上読んで突き合わせた）
    ・《メヂカラ・コバルト・カイザー》は**単独のカードページが無く**、DM26-SD1 に入っているのは
      ツインパクトの《メヂカラ・コバルト・カイザー／アイド・ワイズ・シャッター》だった
      （収録セットの一覧に DM26-SD1 がある）。クリーチャー側は水7・パワー7000・W・ブレイカー、
      呪文側「アイド・ワイズ・シャッター」は光4・S・トリガー。
    ・《青銅のバンビシカット／「我が力、しかと見よ!」》も同じくツインパクトで、
      クリーチャー側は自然2・パワー1000、呪文側は**火9**（コストが大きく違うので取り違えに注意）。
    ・《死神覇王 ブラックXENARCH》は**殿堂入り（2025年8月12日）**。
    ・《アクアン》は殿堂入り→プレミアム殿堂→再殿堂入りをへて、**2025年3月10日に殿堂解除**されている
      （いまは4枚使える）。
    ・《SSS級天災 デッドダムド》は殿堂入りの表記が無かった。
    ・《九番龍 ジゴクバンカー Par459》のシンパシーは「自分のマナゾーンにあるカード」（枚数ぶん軽くなる）で、
      出た時は「1枚マナに置いて、その後マナから1枚手札に戻してもよい」。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, free_play, worst_hand
from envcards.env0 import (exlife_enter, exlife_rep, guardman, he_costx, he_payx,
                           own_loss, worst_own)

W = "https://dmwiki.net/"
SRC = {
    "k48_cambiare": W + "《閃光の精霊カンビアーレ》",
    "k48_bambicut": W + "《青銅のバンビシカット／「我が力、しかと見よ!」》",
    "k48_medikara": W + "《メヂカラ・コバルト・カイザー／アイド・ワイズ・シャッター》",
    "k48_tribe": W + "《ヨビニオン・トライブ》",
    "k48_jigoku": W + "《九番龍 ジゴクバンカー Par459》",
    "k48_fairylife": W + "《フェアリー・ライフ》",
    "k48_jwatch": W + "《終末の監視者 ジ・ウォッチ》",
    "k48_keenary": W + "《終末縫合王 ザ＝キラー・キーナリー》",
    "k48_shimberom": W + "《哀しみの夜 シンベロム・カタルシス》",
    "k48_xenarch": W + "《死神覇王 ブラックXENARCH》",
    "k48_finale": W + "《終末王秘伝オリジナルフィナーレ》",
    "k48_aquan": W + "《アクアン》",
    "k48_fairymiracle": W + "《フェアリー・ミラクル》",
    "k48_bosukatsu": W + "《漢気の2号 ボスカツ》",
    "k48_deaddamd": W + "《SSS級天災 デッドダムド》",
}


# ================================================================ 共通の小道具
def _playable_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化クリーチャーは進化元が要るので除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _gachinko(s, i):
    """ガチンコ・ジャッジを1回行う（勝ったら True）。

    互いに山札の上から1枚を見せて、そのカードを山札の一番下に置く。
    コストが相手以上なら仕掛けた側（i）の勝ち（引き分けは無い）。"""
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


def _freeze(s, j, u):
    """そのクリーチャーをタップし、次の持ち主のターンのはじめにアンタップしないようにする"""
    s.tap_cre(j, u)
    u.frz = 1


# ================================================================ 1. 閃光の精霊カンビアーレ
def e_cambiare(s, i, u):
    """出た時、相手のクリーチャーをすべてタップする。次の相手のターンのはじめにアンタップしない"""
    o = s.P[1 - i]
    for z in o.board[:]:
        if z.c.kind == "C" and z in o.board:
            _freeze(s, 1 - i, z)


def a_cambiare(s, i, u):
    """攻撃する時、相手のエレメントを1つ選び、シールド化してもよい（重要度のいちばん高いもの）"""
    t = s.target(i, kinds="CTX")
    if t is None:
        return
    s.ev(f"　カンビアーレ：{t.c.name} をシールド化")
    s.leave(1 - i, t, "shield", by_opp=True)


def sc_cambiare(s, i, k, nsh):
    """革命0：このカードを自分のシールドゾーンから手札に加えた時、自分のシールドが1つもなければ、
    コストを支払わずに手札から召喚してもよい（nsh＝その時のシールドの枚数）"""
    p = s.P[i]
    if nsh > 0 or k not in p.hand:
        return False
    if s.fate(i, k, "hand", True) != "ok":
        return False
    p.hand.remove(k)
    s.trig[i] += 1
    s.ev("　革命0：閃光の精霊カンビアーレをコストを支払わずに召喚")
    s.enter(i, k, "hand", True)
    return True


add("k48_cambiare", "閃光の精霊カンビアーレ", 8, "L", power=13000, brk=3, blocker=True,
    races=("angelcommand", "command"), pri=10, roles="blk rem fin trg",
    enter=e_cambiare, attack=a_cambiare, shieldcast=sc_cambiare,
    text="革命0：このカードを自分のシールドゾーンから手札に加えた時、自分のシールドが1つもなければ、"
         "コストを支払わずに手札から召喚してもよい。ブロッカー。T・ブレイカー。"
         "出た時、相手のクリーチャーをすべてタップする。次の相手のターンのはじめに、それらはアンタップしない。"
         "攻撃する時、相手のエレメントを1つ選び、シールド化してもよい"
         "（重要度のいちばん高いものを選ぶ、全デッキ共通の決まり）",
    note="革命0は、エンジンの「シールドから手札に来たカードの受け」（s.trigger／shieldcast）を通る時に働く。"
         "ブレイクされた時と、S・トリガーを使えるようにして手札に加える他のカードの効果では誘発するが、"
         "「そのS・トリガーは使えない」と書かれた効果でシールドを手札に加える時は誘発しない"
         "（カードの決まりどおり）",
    source=SRC["k48_cambiare"])


# ================================================================ 2. 青銅のバンビシカット／「我が力、しかと見よ!」
def e_bambicut(s, i, u):
    """出た時、相手とガチンコ・ジャッジする。勝ったら山札の上から1枚目をマナゾーンに置く"""
    if _gachinko(s, i):
        s.ev("　青銅のバンビシカット：ガチンコ・ジャッジに勝って1枚マナゾーンへ")
        s.ramp(i, 1)
    else:
        s.ev("　青銅のバンビシカット：ガチンコ・ジャッジに負けた")


def sp_bambicut(s, i):
    """「我が力、しかと見よ!」：相手のパワー12000以下のクリーチャー1体を破壊し、
    その後ガチンコ・ジャッジに勝ったら1枚引く"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 12000)
    if t is not None:
        s.ev(f"　我が力、しかと見よ!：{t.c.name} を破壊")
        destroy(s, i, t)
    if _gachinko(s, i):
        s.ev("　我が力、しかと見よ!：ガチンコ・ジャッジに勝って1枚引く")
        s.draw(i, 1)


add("k48_bambicut", "青銅のバンビシカット／「我が力、しかと見よ!」", 2, "N", power=1000,
    races=("dreammate", "hunter"), twin=(9, "F", True), pri=3, roles="acc rem trg draw",
    enter=e_bambicut, spell=sp_bambicut,
    text="クリーチャー側（自然2・パワー1000）：出た時、相手とガチンコ・ジャッジする。"
         "自分が勝ったら、自分の山札の上から1枚目をマナゾーンに置く。"
         "呪文側「我が力、しかと見よ!」（火9・S・トリガー）：相手のパワー12000以下のクリーチャーを1体選び、"
         "破壊する。相手とガチンコ・ジャッジする。自分が勝ったら、カードを1枚引く。"
         "（ガチンコ・ジャッジ＝互いに山札の上から1枚を見せて一番下に置き、"
         "自分のカードのコストが相手以上なら自分の勝ち）",
    source=SRC["k48_bambicut"])


# ================================================================ 3. メヂカラ・コバルト・カイザー／アイド・ワイズ・シャッター
def ew_medikara(s, j, u):
    """相手のクリーチャーが出た時、そのターン、相手のクリーチャーはすべて攻撃できない

    j＝そのクリーチャーを出した側。メヂカラの持ち主は 1-j。"""
    if u.c.kind != "C":
        return
    if not s.has(1 - j, "k48_medikara"):
        return
    s.P[j].x["k48_medikara_t"] = s.turn
    s.ev("　メヂカラ・コバルト・カイザー：このターン、相手のクリーチャーは攻撃できない")


def al_medikara(s, i, u):
    """上の印が立っているターンは、そのプレイヤーのクリーチャーは攻撃できない。

    この印は ew_medikara（メヂカラが場にいる時だけ動く）しか立てないので、
    メヂカラが1枚も入っていない対戦では必ず None のままになる。"""
    return s.P[i].x.get("k48_medikara_t") == s.turn


def sw_medikara(s, i, k):
    """相手が呪文を唱えた時、自分はカードを2枚引いてもよい（i＝唱えた側）"""
    j = 1 - i
    if not s.has(j, "k48_medikara"):
        return
    if len(s.P[j].deck) <= 2:
        return                               # 山札を切らしてまでは引かない
    s.ev("　メヂカラ・コバルト・カイザー：相手が呪文を唱えたので2枚引く")
    s.draw(j, 2)


def sp_medikara(s, i):
    """アイド・ワイズ・シャッター：相手のクリーチャーを2体まで選び、タップする。
    次の相手のターンのはじめに、それらはアンタップしない

    アンタップしているクリーチャー（ブロッカーを外せる）を先に、足りない分はタップしている
    クリーチャー（次のターンも動けなくなる）から、重要度の高い順に選ぶ。"""
    done = 0
    for pred in (lambda z: not z.tap, lambda z: z.frz == 0):
        while done < 2:
            t = s.target(i, pred)
            if t is None:
                break
            s.ev(f"　アイド・ワイズ・シャッター：{t.c.name} をタップして次のターンもアンタップさせない")
            _freeze(s, 1 - i, t)
            done += 1
        if done >= 2:
            return


add("k48_medikara", "メヂカラ・コバルト・カイザー／アイド・ワイズ・シャッター", 7, "W", power=7000, brk=2,
    races=("bluecommanddragon", "command", "dragon", "hunter"), twin=(4, "L", True),
    pri=8, roles="dis draw rem trg",
    enterwatch=ew_medikara, atklock=al_medikara, spellwatch=sw_medikara, spell=sp_medikara,
    text="クリーチャー側（水7・パワー7000）：W・ブレイカー。"
         "相手のクリーチャーが出た時、そのターン、相手のクリーチャーはすべて攻撃できない。"
         "相手が呪文を唱えた時、自分はカードを2枚引いてもよい（山札が残っている時だけ引く）。"
         "呪文側「アイド・ワイズ・シャッター」（光4・S・トリガー）：相手のクリーチャーを2体まで選び、"
         "タップする。次の相手のターンのはじめに、それらはアンタップしない",
    note="DM26-SD1 に入っているのはこのツインパクトで、《メヂカラ・コバルト・カイザー》という"
         "単独のカードは存在しない（dmwiki にも単独ページが無い）",
    source=SRC["k48_medikara"])


# ================================================================ 4. ヨビニオン・トライブ
def e_tribe(s, i, u):
    """ヨビニオン：召喚で出た時、山札の上から、これよりコストの小さいクリーチャーが出るまで表向きにする"""
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
            flipped.append(got)              # 進化クリーチャーは進化元がなく出せない
    for k in flipped:
        p.deck.insert(0, k)


def fa_tribe(s, i, av, cv):
    """このクリーチャーを自分のマナゾーンから召喚してもよい（コストは支払う）"""
    p = s.P[i]
    if "k48_tribe" not in p.mana or s.manaexec(i):
        return []
    n = s.ccost(i, "k48_tribe", av)
    if n > av - 1:                           # このカード自身はマナとして使えない
        return []
    if n > 0 and not cv.issuperset(BY_KEY["k48_tribe"].civ):
        return []
    if s.fate(i, "k48_tribe", "mana", True) != "ok":
        return []
    return [("x:k48_tribe", n)]


def ap_tribe(s, a):
    i = s.tp
    p = s.P[i]
    if "k48_tribe" not in p.mana:
        return
    n = a[1]
    if len(p.mana) - p.mused - 1 < n:
        return
    p.mused += n
    s.take_mana(i, "k48_tribe")
    s.ev(f"ヨビニオン・トライブ：マナゾーンから召喚（{n}マナ）")
    s.enter(i, "k48_tribe", "mana", True)


def ld_tribe(s, i, u, dest, destroy_):
    """破壊される時、墓地に置くかわりにマナゾーンに置く"""
    if u.k != "k48_tribe" or not destroy_ or dest != "grave":
        return None
    return "mana"


add("k48_tribe", "ヨビニオン・トライブ", 4, "N", power=4000, races=("beastfolk",),
    pri=5, roles="acc atk", enter=e_tribe, leavedest=ld_tribe,
    freeacts=fa_tribe, actapply={"x:k48_tribe": ap_tribe},
    text="このクリーチャーを自分のマナゾーンから召喚してもよい（コストは支払う。"
         "このカード自身はそのコストに使えない）。"
         "ヨビニオン：召喚によって出た時、自分の山札の上から1枚ずつ表向きにし、"
         "最初に出た、これよりコストの小さいクリーチャーを出す。残りは山札の下に置く。"
         "このクリーチャーが破壊される時、墓地に置くかわりにマナゾーンに置く",
    source=SRC["k48_tribe"])


# ================================================================ 5. 九番龍 ジゴクバンカー Par459
def cx_jigoku(s, i, av):
    """シンパシー：自分のマナゾーンにあるカード1枚につきコストを1少なくする（0以下にはならない）"""
    return max(1, BY_KEY["k48_jigoku"].cost - len(s.P[i].mana))


def e_jigoku(s, i, u):
    """出た時、山札の上から1枚目をマナゾーンに置く。その後、マナから1枚手札に戻してもよい"""
    p = s.P[i]
    s.ramp(i, 1)
    if not p.mana:
        return
    k = max(p.mana, key=E.PRI.get)
    if E.PRI[k] < 4:
        return                               # 戻す値打ちのある札が無ければ戻さない
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　ジゴクバンカー：マナの {BY_KEY[k].name} を手札に戻す")


add("k48_jigoku", "九番龍 ジゴクバンカー Par459", 12, "N", power=10000, brk=2, mach=True,
    races=("giantdragon", "giant", "dragon"), pri=10, roles="acc draw atk fin",
    costx=cx_jigoku, enter=e_jigoku,
    text="シンパシー：自分のマナゾーンにあるカード（このカードの召喚コストを、自分のマナゾーンにある"
         "カード1枚につき1少なくする。ただし1より少なくはならない）。マッハファイター。W・ブレイカー。"
         "出た時、自分の山札の上から1枚目をマナゾーンに置く。その後、カードを1枚、"
         "自分のマナゾーンから手札に戻してもよい（重要度4以上のいちばん高い札を戻す）",
    source=SRC["k48_jigoku"])


# ================================================================ 6. フェアリー・ライフ
def sp_fairylife(s, i):
    s.ramp(i, 1)


add("k48_fairylife", "フェアリー・ライフ", 2, "N", kind="S", trig=True, pri=2, roles="acc trg",
    spell=sp_fairylife,
    text="S・トリガー。自分の山札の上から1枚をマナゾーンに置く",
    source=SRC["k48_fairylife"])


# ================================================================ 7. 終末の監視者 ジ・ウォッチ
def _jwatch_bounce(s, i):
    """クリーチャーを2体まで選び、持ち主の手札に戻す（相手の重要度の高い2体を選ぶ）"""
    for _ in range(2):
        if s.over:
            return
        t = s.target(i)
        if t is None:
            return
        s.ev(f"　ジ・ウォッチ：{t.c.name} を手札に戻す")
        move(s, i, t, "hand")


def e_jwatch(s, i, u):
    if u.x.get("summoned"):
        _jwatch_bounce(s, i)


def a_jwatch(s, i, u):
    _jwatch_bounce(s, i)


def _jwatch_stop(s, j):
    """ジ・ウォッチの持ち主から見て「相手（j）の手番」なら、ターンの残りをとばす。

    自分の手番の出来事（相手のS・トリガーなど）でとばすと自分のターンを失うので使わない。"""
    if not s.has(1 - j, "k48_jwatch"):
        return
    if s.tp != j:
        return
    s.ev("　ジ・ウォッチ：ターンの残りをとばす")
    s.stop = True


def ew_jwatch(s, j, u):
    if u.c.kind == "C":
        _jwatch_stop(s, j)


def sw_jwatch(s, j, k):
    _jwatch_stop(s, j)


add("k48_jwatch", "終末の監視者 ジ・ウォッチ", 10, "W", power=12000, brk=3,
    races=("outragemax",), pri=11, roles="rem dis fin atk",
    enter=e_jwatch, attack=a_jwatch, enterwatch=ew_jwatch, spellwatch=sw_jwatch,
    text="T・ブレイカー。召喚によって出た時または攻撃する時、クリーチャーを2体まで選び、"
         "持ち主の手札に戻す（相手の重要度の高いクリーチャーから選ぶ）。"
         "相手のクリーチャーが出た時または相手が呪文を唱えた時、ターンの残りをとばしてもよい"
         "（相手の手番の時だけ使う）",
    source=SRC["k48_jwatch"])


# ================================================================ 8. 終末縫合王 ザ＝キラー・キーナリー
def e_keenary(s, i, u):
    """EXライフ。出た時、相手のクリーチャー1体を選び、手札に戻してもよい。
    その後、その選んだクリーチャー以下のコストのクリーチャーを1体、自分の墓地から出す"""
    exlife_enter(s, i, u)
    t = s.target(i)
    if t is None:
        return
    n = t.c.cost
    s.ev(f"　キーナリー：{t.c.name} を手札に戻す")
    move(s, i, t, "hand")
    s.revive(i, lambda c: c.cost <= n, "grave")


def etl_keenary(s, j, u):
    """相手のクリーチャーが出て、その能力がトリガーする時、かわりにその能力はトリガーしない

    j＝そのクリーチャーを出した側。キーナリーの持ち主（1-j）から見て相手のものだけ止める。"""
    return s.has(1 - j, "k48_keenary")


add("k48_keenary", "終末縫合王 ザ＝キラー・キーナリー", 10, "WDN", power=15000, brk=3,
    races=("dispector", "jurassiccommanddragon", "command", "dragon", "dragonzombie"),
    pri=12, roles="rem dis fin shd",
    enter=e_keenary, leaverep=exlife_rep, entertriglock=etl_keenary,
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりに"
         "そのシールドを墓地に置いて残る）。T・ブレイカー。"
         "出た時、相手のクリーチャーを1体選ぶ。そのクリーチャーを持ち主の手札に戻してもよい。"
         "その後、その選んだクリーチャー以下のコストのクリーチャーを1体、自分の墓地から出す。"
         "相手のクリーチャーが出て、その能力がトリガーする時、かわりにその能力はトリガーしない",
    source=SRC["k48_keenary"])


# ================================================================ 9. 哀しみの夜 シンベロム・カタルシス
def nap_shimberom(s, i, u):
    """相手のクリーチャーが攻撃する時、可能ならクリーチャーを攻撃する

    （攻撃できる自分のクリーチャーが1体でもいる間、相手はプレイヤーを攻撃できない）。
    i＝攻撃する側、u＝攻撃するクリーチャー。シンベロムの持ち主は 1-i。"""
    di = 1 - i
    if not s.has(di, "k48_shimberom"):
        return False
    ap = s.power(i, u, True)
    mf = u.sick and (s.kw(u, "mach") or bool(E.MACHOK and any(f(s, i, u) for f in E.MACHOK)))
    for t in s.P[di].board:
        if t.c.kind != "C" or t.jd:
            continue
        if not t.tap and not mf:
            continue
        if E.ATKTARGETLOCK and any(f(s, i, u, t) for f in E.ATKTARGETLOCK):
            continue
        if s.power(di, t) > ap:
            continue
        return True
    return False


def rep_shimberom(s, i, u, dest, destroy_):
    """離れる時、かわりに自分のマナゾーンにあるカードを3枚、山札の下に置いてもよい"""
    if u.k != "k48_shimberom":
        return False
    p = s.P[i]
    if len(p.mana) < 3:
        return False
    for _ in range(3):
        k = min(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        p.deck.insert(0, k)
    s.ev("　シンベロム・カタルシス：マナ3枚を山札の下に置いて離れない")
    return True


def aw_shimberom(s, i, u):
    """自分の他のクリーチャーが相手プレイヤーを攻撃する時、
    このターン、そのクリーチャーのパワーを+6000し「パワード・ブレイカー」を与える"""
    if u.c.kind != "C" or u.k == "k48_shimberom":
        return
    if s.atktgt is not None:
        return                               # プレイヤーへの攻撃でなければ何もしない
    n = sum(1 for z in s.P[i].board if z.k == "k48_shimberom")
    if not n:
        return
    u.pw += 6000 * n
    u.x["k48_pb"] = s.turn
    s.ev(f"　シンベロム・カタルシス：{u.c.name} に+{6000 * n}とパワード・ブレイカー")


def bp_shimberom(s, i, u):
    """上で与えたパワード・ブレイカー（パワー6000ごとにシールドをもう1つブレイクする）"""
    if u.x.get("k48_pb", -1) != s.turn:
        return 0
    return max(0, 1 + s.power(i, u, True) // 6000 - u.c.brk)


add("k48_shimberom", "哀しみの夜 シンベロム・カタルシス", 11, "N", power=17000, brk=3,
    races=("demoncommand", "command"), pri=12, roles="blk rem atk fin dis",
    costx=he_costx("k48_shimberom"), payx=he_payx("k48_shimberom"),
    guard=guardman("k48_shimberom"), noatkplock=nap_shimberom,
    leaverep=rep_shimberom, atkwatch=aw_shimberom, brkplus=bp_shimberom,
    text="ハイパーエナジー（自分のコストの違うクリーチャーを好きな数タップして、"
         "そのクリーチャー1体につきこのクリーチャーの召喚コストを2少なくする）。"
         "ガードマン（相手のクリーチャーが自分の他のクリーチャーを攻撃する時、"
         "このクリーチャーをタップして攻撃先をこのクリーチャーに変更してもよい）。T・ブレイカー。"
         "相手のクリーチャーが攻撃する時、可能ならクリーチャーを攻撃する。"
         "このクリーチャーが離れる時、かわりに自分のマナゾーンにあるカードを3枚、"
         "好きな順序で山札の下に置いてもよい。"
         "自分の他のクリーチャーが相手プレイヤーを攻撃する時、このターン、そのクリーチャーの"
         "パワーを+6000し「パワード・ブレイカー」を与える",
    source=SRC["k48_shimberom"])


# ================================================================ 10. 死神覇王 ブラックXENARCH
_XEN_BUSY = [0]


def _xen_choose(s, j):
    """相手（j）は自身のクリーチャー1体を選んで破壊する。そうしなければ手札を1枚選んで捨てる

    どちらにするかは相手が選ぶので、失うのが軽いほうを選ぶ（全デッキ共通の決まり）。"""
    z = worst_own(s, j)
    hk = worst_hand(s, j)
    lz = own_loss(s, j, z) if z is not None else None
    lh = E.PRI[hk] if hk is not None else None
    if z is not None and (lh is None or lz <= lh):
        s.ev(f"　ブラックXENARCH：相手は自分の {z.c.name} を破壊")
        s.leave(j, z, "grave", destroy=True)
    elif hk is not None:
        s.ev(f"　ブラックXENARCH：相手は手札の {BY_KEY[hk].name} を捨てる")
        s.discard(j, hk, by_opp=True)


def _xen_fire(s, j, n):
    """n 回ぶん誘発させる（両者が持っていると誘発がつながるので、深さを4までに抑える）"""
    if n <= 0 or _XEN_BUSY[0] >= 4:
        return
    _XEN_BUSY[0] += 1
    try:
        for _ in range(n):
            if s.over:
                return
            _xen_choose(s, j)
    finally:
        _XEN_BUSY[0] -= 1


def ew_xenarch(s, i, u):
    """自分のクリーチャーが出た時"""
    if u.c.kind != "C":
        return
    _xen_fire(s, 1 - i, sum(1 for z in s.P[i].board if z.k == "k48_xenarch"))


def lw_xenarch(s, i, u, dest, destroy_):
    """自分のクリーチャーが離れた時（このクリーチャー自身が離れた時も含む）"""
    if u.c.kind != "C":
        return
    n = sum(1 for z in s.P[i].board if z.k == "k48_xenarch")
    if u.k == "k48_xenarch":
        n += 1
    _xen_fire(s, 1 - i, n)


def tp_xenarch(s, j):
    """各ターンの終わりに、このクリーチャーが自分の墓地にあり、自分のマナゾーンに闇のカードがあれば、
    自分のタップしているクリーチャーを3体破壊してもよい。そうしたら、このクリーチャーを墓地から出す"""
    p = s.P[j]
    for _ in range(3):
        if s.over or "k48_xenarch" not in p.grave:
            return
        if not any("D" in E.MCIV[k] for k in p.mana):
            return
        tapped = sorted((z for z in p.board if z.c.kind == "C" and z.tap),
                        key=lambda z: own_loss(s, j, z))
        if len(tapped) < 3:
            return
        pick = tapped[:3]
        loss = sum(own_loss(s, j, z) for z in pick)
        gain = E.PRI["k48_xenarch"]
        cs = [z for z in s.P[1 - j].board if z.c.kind == "C"]
        if cs:
            gain += min(own_loss(s, 1 - j, z) for z in cs)   # 出た時に相手が1体失うぶん
        if loss > gain:
            return
        if s.fate(j, "k48_xenarch", "grave", False) != "ok":
            return
        s.ev("　ブラックXENARCH：タップしているクリーチャー3体を破壊して墓地から出る")
        for z in pick:
            if z in p.board:
                s.leave(j, z, "grave", destroy=True)
        if s.over or "k48_xenarch" not in p.grave:
            return
        p.grave.remove("k48_xenarch")
        s.enter(j, "k48_xenarch", "grave", False)


add("k48_xenarch", "死神覇王 ブラックXENARCH", 6, "D", power=9000, brk=2, blocker=True,
    races=("darklord",), pri=8, roles="blk rem dis fin",
    enterwatch=ew_xenarch, leavewatch=lw_xenarch, tendp=tp_xenarch,
    text="各ターンの終わりに、このクリーチャーが自分の墓地にあり、自分のマナゾーンに闇のカードがあれば、"
         "自分のタップしているクリーチャーを3体破壊してもよい。そうしたら、このクリーチャーを"
         "自分の墓地から出す（失う3体のほうが軽い時だけ使う、全デッキ共通の決まり）。"
         "ブロッカー。W・ブレイカー。"
         "自分のクリーチャーが出た時または離れた時、相手は自身のクリーチャーを1体選び、破壊する。"
         "そうしなければ、相手は自身の手札を1枚選び、捨てる",
    note="2025年8月12日から殿堂入り（デッキに1枚まで）。"
         "「出た時または離れた時」の誘発は、両方のプレイヤーがこのカードを持っていると"
         "誘発がつながって終わらなくなるので、つながりの深さを4回までに抑えている",
    source=SRC["k48_xenarch"])


# ================================================================ 11. 終末王秘伝オリジナルフィナーレ
def sp_finale(s, i):
    """山札の上から3枚を見て、2枚をマナゾーンに置き、残りの1枚を手札に加える。
    その後、相手のクリーチャー1体のパワーを、自分のマナゾーンのカード1枚につき-1000する"""
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n > 0:
        top = [p.deck.pop() for _ in range(n)]
        keep = max(top, key=E.PRI.get)       # 手札に加えるのは重要度のいちばん高い1枚
        top.remove(keep)
        p.hand.append(keep)
        for k in top:
            s.add_mana(i, k, tapped=True, src="deck")
        s.ev(f"　オリジナルフィナーレ：{BY_KEY[keep].name} を手札へ、{len(top)}枚をマナゾーンへ")
    t = s.target(i)
    if t is None:
        return
    d = 1000 * len(p.mana)
    t.pw -= d
    s.ev(f"　オリジナルフィナーレ：{t.c.name} のパワーを-{d}")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        destroy(s, i, t)


def aw_finale(s, i, u):
    """アタック・チャンス：自分の水と闇と自然を持つディスペクターが攻撃する時、
    手札のこの呪文をコストを支払わずに唱えてもよい"""
    p = s.P[i]
    if "k48_finale" not in p.hand:
        return
    if u.c.kind != "C" or "dispector" not in u.c.races:
        return
    if not set("WDN").issubset(set(u.c.civ)):
        return
    for _ in range(4):
        if s.over or s.stop or "k48_finale" not in p.hand:
            return
        if not s.spell_ok(i, BY_KEY["k48_finale"].cost):
            return
        s.ev("　アタック・チャンス：終末王秘伝オリジナルフィナーレをコストを支払わずに唱える")
        free_play(s, i, "k48_finale", "hand")


add("k48_finale", "終末王秘伝オリジナルフィナーレ", 5, "WDN", kind="S", pri=6, roles="acc draw rem",
    spell=sp_finale, atkwatch=aw_finale,
    text="アタック・チャンス：水と闇と自然を持つディスペクター"
         "（自分のその条件のクリーチャーが攻撃する時、この呪文をコストを支払わずに唱えてもよい）。"
         "自分の山札の上から3枚を見る。その中から2枚をマナゾーンに置き、残りの1枚を手札に加える"
         "（手札に加えるのは重要度のいちばん高い1枚）。"
         "相手のクリーチャーを1体選ぶ。このターン、自分のマナゾーンのカード1枚につき、"
         "そのクリーチャーのパワーを-1000する（パワーが0以下になったクリーチャーは破壊される）",
    source=SRC["k48_finale"])


# ================================================================ 12. アクアン
def e_aquan(s, i, u):
    """出た時、山札の上から5枚を表向きにしてもよい。光のカードと闇のカードをすべて手札に加え、
    残りを墓地に置く"""
    p = s.P[i]
    n = min(5, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    got = [k for k in top if set("LD") & set(E.MCIV[k])]
    for k in got:
        top.remove(k)
        p.hand.append(k)
    for k in top:
        s.grave_put(i, k)
    s.ev(f"　アクアン：上から{n}枚のうち光・闇の{len(got)}枚を手札へ、{len(top)}枚を墓地へ")


add("k48_aquan", "アクアン", 4, "W", power=2000, races=("cyberlord",), pri=5, roles="draw",
    enter=e_aquan,
    text="出た時、自分の山札の上から5枚を表向きにしてもよい。その中から光のカードと闇のカードを"
         "すべて手札に加え、残りを墓地に置く",
    note="殿堂入り（2005年3月15日）→プレミアム殿堂（2011年1月15日）→再殿堂入り（2022年7月1日）を"
         "へて、2025年3月10日に殿堂解除された。いまは枚数の制限なしで使える",
    source=SRC["k48_aquan"])


# ================================================================ 13. フェアリー・ミラクル
def sp_fairymiracle(s, i):
    """山札の上から1枚をマナゾーンに置く。マナゾーンにすべての文明が揃っていれば、もう1枚置く"""
    s.ramp(i, 1)
    civ = set()
    for k in s.P[i].mana:
        civ |= set(E.MCIV[k])
    if set("LWDFN").issubset(civ):
        s.ev("　フェアリー・ミラクル：すべての文明が揃っているのでもう1枚マナゾーンへ")
        s.ramp(i, 1)


add("k48_fairymiracle", "フェアリー・ミラクル", 3, "N", kind="S", pri=3, roles="acc",
    spell=sp_fairymiracle,
    text="自分の山札の上から1枚をマナゾーンに置く。自分のマナゾーンに光・水・闇・火・自然の"
         "すべての文明が揃っていれば、自分の山札の上からもう1枚、マナゾーンに置く",
    source=SRC["k48_fairymiracle"])


# ================================================================ 14. 漢気の2号 ボスカツ
def e_bosukatsu(s, i, u):
    """出た時、相手の手札を1枚見ないで選び、捨てさせる。
    その捨てたカードと同じ文明を持つ、コスト8以下の多色クリーチャーを1体、自分の手札から出してもよい"""
    p, o = s.P[i], s.P[1 - i]
    if not o.hand:
        return
    k = o.hand[s.rng.randrange(len(o.hand))]
    s.ev(f"　ボスカツ：相手の手札を見ないで1枚（{BY_KEY[k].name}）捨てさせる")
    s.discard(1 - i, k, by_opp=True)
    civ = set(E.MCIV[k])
    best, bv = None, -1
    for x in sorted(set(p.hand)):
        c = BY_KEY[x]
        if c.kind != "C" or c.cost > 8 or not E.MULTI[x]:
            continue
        if not (set(E.MCIV[x]) & civ):
            continue
        if c.evo and not c.neo and s.evo_src(i, x) is None:
            continue
        if E.PRI[x] > bv and s.fate(i, x, "hand", False) == "ok":
            best, bv = x, E.PRI[x]
    if best is None:
        return
    p.hand.remove(best)
    on = s.evo_src(i, best) if BY_KEY[best].evo else None
    s.ev(f"　ボスカツ：手札から {BY_KEY[best].name} を出す")
    s.enter(i, best, "hand", False, on=on)


add("k48_bosukatsu", "漢気の2号 ボスカツ", 5, "LDF", power=4000, sa=True,
    races=("megacommanddragon", "command", "dragon", "revolution", "hamukatsu"),
    pri=7, roles="dis atk acc",
    enter=e_bosukatsu,
    text="スピードアタッカー。"
         "出た時、相手の手札を1枚見ないで選び、捨てさせる。その捨てたカードと同じ文明を持つ、"
         "コスト8以下の多色クリーチャーを1体、自分の手札から出してもよい"
         "（重要度のいちばん高いものを出す、全デッキ共通の決まり）",
    source=SRC["k48_bosukatsu"])


# ================================================================ 15. SSS級天災 デッドダムド
def e_deaddamd(s, i, u):
    """他のクリーチャーの上に重ねた時、相手のクリーチャー1体を選び、
    破壊する／マナゾーンに置く／手札に戻す のどれかを行う"""
    if not u.under:
        return                               # 重ねていない（タマシードからの進化など）なら誘発しない
    t = s.target(i)
    if t is None:
        return
    o = s.P[1 - i]
    v = s.val(t)
    # どれを選ぶかは機械的に決める：ふつうは破壊。破壊されると得をする相手（「破壊された時」の能力を持つ）
    # ならマナゾーンへ。相手がコストを払い直せない大きいクリーチャーなら手札へ戻す。
    sdes = v - (3 if t.k in E.DESTROYED else 0)
    smana = v - 1                            # 相手のマナが1枚増える
    shand = v - 2 + (2 if t.c.cost > len(o.mana) else 0)
    if sdes >= smana and sdes >= shand:
        s.ev(f"　デッドダムド：{t.c.name} を破壊")
        destroy(s, i, t)
    elif smana >= shand:
        s.ev(f"　デッドダムド：{t.c.name} をマナゾーンに置く")
        move(s, i, t, "mana")
    else:
        s.ev(f"　デッドダムド：{t.c.name} を手札に戻す")
        move(s, i, t, "hand")


def pr_deaddamd(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and not (BY_KEY[kk].evo and not BY_KEY[kk].neo)
            and set("WDN") & set(BY_KEY[kk].civ))
    return None if n >= 6 else "進化元になる水・闇・自然のクリーチャーが6体いない"


add("k48_deaddamd", "SSS級天災 デッドダムド", 8, "WDN", power=11000, brk=2, evo="WDN",
    races=("trinitycommand", "command", "sinvader"), pri=11, roles="rem atk fin",
    enter=e_deaddamd, playrule=pr_deaddamd,
    invade=lambda s, i, u: ("command" in u.c.races) and bool(set("WDN") & set(u.c.civ)),
    text="進化：水、闇、または自然のクリーチャー1体の上に置く。"
         "SSS級侵略［天災］：水、闇、または自然のコマンドが攻撃する時、バトルゾーン・手札・墓地・"
         "マナゾーンにあるこのカードを、その攻撃しているクリーチャーの上に重ねてもよい。W・ブレイカー。"
         "このクリーチャーを他のクリーチャーの上に重ねた時、相手のクリーチャーを1体選び、"
         "破壊する、持ち主のマナゾーンに置く、持ち主の手札に戻す のうち1つを行う"
         "（相手が破壊で得をするならマナゾーンへ、コストを払い直せない大きいクリーチャーなら手札へ、"
         "それ以外は破壊、という全デッキ共通の決まりで機械的に決める）",
    source=SRC["k48_deaddamd"])
E.INVZONE["k48_deaddamd"] = ("hand", "grave", "mana", "board")
