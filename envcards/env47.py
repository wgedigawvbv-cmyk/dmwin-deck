"""担当47：DM26-SD1「ドキドキつよいデッキ 25の王道」の再録カード15枚

出典：dmwiki.net の各カードページ（カードごとに source= に書いた）。
      カクメイジンの「各ブレイクの前に」の範囲だけは https://dmwiki.net/ブレイクの前 、
      鬼丸「覇」のガチンコ・ジャッジの決まりは https://dmwiki.net/ガチンコ・ジャッジ を読んで確かめた。

  この札束に入っている新しい仕組み
    ・追加ターン（`P.extra`）を使う札が2枚ある（《月下卍壊 ガ・リュミーズ 卍》＝確定、
      《勝利宣言 鬼丸「覇」》＝ガチンコ・ジャッジに勝てば）。
    ・「各ブレイクの前に」呪文を踏み倒す（カクメイジン）＝ `breakpre=` で書いた。
    ・「相手のクリーチャーがはじめて攻撃するなら、可能ならこのカードを攻撃する」（覇＝ロード）
      ＝ 攻撃先の強制 `mustatktgt=` で書いた（「はじめての攻撃」は `atkwatch=` で数え、
      数え始めの印は `gamestart=` で付けるので、覇＝ロードの入っていない対戦には一切ふれない）。
    ・「相手は多色ではない呪文を唱えられない」（ドルファディロム）＝ `spelllock=` に
      呪文のキーが渡るようになったので、文明をそのまま見て止めている。
    ・EXライフ2枚（ザーディクリカ・ドルファディロム）。ドルファディロムは
      「EXライフのシールドが離れた時」にも全体除去が誘発するので、env0 の EXLOST に登録した
      （leaverep に自分で書くと、先に登録された側の exlife_rep しか働かない）。
    ・スター進化（ライオネル.Star）＝ env0 の star_evo_rep を使った。
    ・ゲーム中1度の「終極宣言」（ゴルファンタジスタ）。

  調べ直して確かめたところ
    15枚すべて、dmwiki.net のカードページを別の質問で2回ずつ読み、
    コスト・文明・種類・種族・パワー・ブレイク数・能力本文が2回とも一致することを確かめた。
    2回の読みで食い違い、調べ直して直したもの：
      ・《天風のゲイル・ヴェスパー》のコスト。1回目は8と出たが、これはデュエプレ版の値で、
        紙（TCG）版は10。cardtable を見るとTCG版10／デュエプレ版8の2段になっている。**10 を採った。**
      ・《芸魔王将 カクメイジン》が踏み倒せる呪文のコスト上限は「4以下」ではなく
        **「自分のマナゾーンにあるカードの枚数以下」**（ブレイクの前のページの要約でも
        「手札か墓地からマナの枚数以下の呪文を踏み倒し」と書かれている）。
      ・《月下卍壊 ガ・リュミーズ 卍》には無月の門などの別コストは**無い**（素のコスト99の呪文で、
        《卍 新世壊 卍》などの踏み倒しで唱えるカード）。無月の門の札と混同しないこと。
    殿堂の記載があったのは《勝利宣言 鬼丸「覇」》だけ（2014年5月24日に殿堂入り、
    2023年8月11日に殿堂解除＝いまは制限なし）。ほかの14枚はどのページにも殿堂の記載がなかった。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all
from envcards.env0 import EXLOST, exlife_enter, exlife_rep, race_like, star_evo_rep

W = "https://dmwiki.net/"
SRC = {
    "k47_zaadik": W + "《龍風混成 ザーディクリカ》",
    "k47_garumiz": W + "《月下卍壊 ガ・リュミーズ 卍》",
    "k47_gospel": W + "《水晶の王 ゴスペル》",
    "k47_kakumeijin": W + "《芸魔王将 カクメイジン》",
    "k47_hakki": W + "《「勝利」の頂 カイザー「刃鬼」》",
    "k47_haload": W + "《アビスベル＝覇＝ロード》",
    "k47_lionel": W + "《「正義星帝」 ＜ライオネル.Star＞》",
    "k47_vesper": W + "《天風のゲイル・ヴェスパー》",
    "k47_golfan": W + "《超重竜 ゴルファンタジスタ》",
    "k47_kiyonaga": W + "《五輪の求道者 清永》",
    "k47_wakumu": W + "《蒼狼の豊穣 ワクムテラス／オリジナル・ライフ》",
    "k47_dolfa": W + "《聖魔連結王 ドルファディロム》",
    "k47_odokaku": W + "《王道の革命 ドギラゴン》",
    "k47_onimaru": W + "《勝利宣言 鬼丸「覇」》",
    "k47_haikyu": W + "《配球の超人／記録的剛球》",
}


# ================================================================ 共通の道具
def _is_magic(c):
    """マジック（種族のくくり。マジック・ドラゴン、マジック・コマンドなど）"""
    return race_like(c, "magic")


def _is_abyss(c):
    """アビス（アビスロイヤル、アビス・ドラゴンなど）"""
    return race_like(c, "abyss")


def _is_giant(c):
    """ジャイアント（ジャイアント・ドラゴン、ジャイアント・ハンターなど）"""
    return race_like(c, "giant")


def _is_hunter(c):
    """ハンター（ハンター、ジャイアント・ハンターなど）"""
    return race_like(c, "hunter")


def _is_spellcard(k):
    """呪文として扱えるカード（ツインパクトは呪文側があるので呪文としても数える）"""
    c = BY_KEY[k]
    return c.kind == "S" or bool(c.twin)


def _zone(s, i, name):
    p = s.P[i]
    return {"hand": p.hand, "grave": p.grave, "mana": p.mana}[name]


def _best_spell(s, i, zones, maxcost):
    """コストを支払わずに唱えられる呪文のうち、いちばん重要度の高いもの。
    返り値：(ゾーン名, キー, 呪文側として唱えるか) か None"""
    best, bv = None, -1
    for zn in zones:
        for k in sorted(set(_zone(s, i, zn))):
            c = BY_KEY[k]
            opts = []
            if c.kind == "S":
                opts.append((c.cost, False))
            if c.twin:
                opts.append((c.twin[0], True))
            for cost, tw in opts:
                if maxcost is not None and cost > maxcost:
                    continue
                if not s.spell_ok(i, cost):
                    continue
                if E.PRI[k] > bv:
                    best, bv = (zn, k, tw), E.PRI[k]
    return best


def _cast_free(s, i, zones=("grave", "hand"), maxcost=None, bottom=False, tag=""):
    """呪文1枚をコストを支払わずに唱える。bottom＝唱えた後、墓地のかわりに山札の下へ"""
    got = _best_spell(s, i, zones, maxcost)
    if got is None:
        return False
    zn, k, tw = got
    p = s.P[i]
    if k not in _zone(s, i, zn):
        return False
    if zn == "mana":
        s.take_mana(i, k)
    else:
        _zone(s, i, zn).remove(k)
    s.ev(f"　{tag}：{BY_KEY[k].name} を{'墓地' if zn == 'grave' else '手札'}からコストを支払わずに唱える")
    s.cast(i, k, tw)
    if bottom and k in p.grave:
        p.grave.remove(k)
        p.deck.insert(0, k)
        s.ev(f"　{tag}：{BY_KEY[k].name} は墓地のかわりに山札の下へ")
    return True


def _play_elem(s, i, k, src="deck"):
    """エレメント（呪文でないカード）1枚をコストを支払わずに使う。
    カードは呼び出し側が元のゾーンから取り除いておく。使えたら True（使えなければカードは触らない）"""
    c = BY_KEY[k]
    if c.kind == "S":
        return False
    if c.kind == "C":
        on = None
        if c.evo and not c.neo:
            on = s.evo_src(i, k)
            if on is None:
                return False                  # 進化元がいないので出せない
        if s.fate(i, k, src, False) != "ok":
            return False
        s.enter(i, k, src, False, on=on)
        return True
    if c.kind == "T":
        s.place_tama(i, k)
        return True
    if c.kind == E.GEAR:
        gu = E.U(k)
        gu.sick = False
        s.P[i].board.append(gu)
        fn = E.ENTER.get(k)
        if fn is not None:
            fn(s, i, gu)
        return True
    s.place_castle(i, k)                      # G城
    return True


def _use_free(s, i, k, src="deck"):
    """カード1枚をコストを支払わずに「使う」（呪文も含む）。カードは取り除いておく"""
    c = BY_KEY[k]
    if c.kind == "S":
        if not s.spell_ok(i, c.cost):
            return False
        s.cast(i, k)
        return True
    return _play_elem(s, i, k, src)


def _gachinko(s, i):
    """ガチンコ・ジャッジ：互いに山札の上を1枚表向きにし、コストを比べる。
    同じかこちらが大きければ仕掛けた側（i）の勝ち。表向きにしたカードは山札の一番下に置く。
    山札が0枚の側は参照できるコストがないものとして負け（両方0枚なら仕掛けた側の勝ち）"""
    a, b = s.P[i], s.P[1 - i]
    ka = a.deck.pop() if a.deck else None
    kb = b.deck.pop() if b.deck else None

    def cst(k):
        if k is None:
            return -1
        c = BY_KEY[k]
        return max(c.cost, c.twin[0]) if c.twin else c.cost   # ツインパクトは持ち主が有利な側を選ぶ

    win = cst(ka) >= cst(kb)
    s.ev(f"　ガチンコ・ジャッジ：{BY_KEY[ka].name if ka else '（山札なし）'}"
         f" 対 {BY_KEY[kb].name if kb else '（山札なし）'}")
    if ka is not None:
        a.deck.insert(0, ka)
    if kb is not None:
        b.deck.insert(0, kb)
    return win


def _change_rule(pred, why, n=3):
    """革命チェンジの「そのデッキで入れ替えられるか」の判定を作る"""
    def f(deck, k):
        c = sum(v for kk, v in deck.items() if kk != k and pred(BY_KEY[kk]))
        return None if c >= n else why
    return f


# ================================================================ 1 龍風混成 ザーディクリカ
def e_zaadik(s, i, u):
    """EXライフ。出た時、コスト7以下の呪文1枚を手札か墓地からただで唱える（唱えた後は山札の下）"""
    exlife_enter(s, i, u)
    _cast_free(s, i, ("grave", "hand"), maxcost=7, bottom=True, tag="ザーディクリカ")


def t_zaadik(s, i, u):
    """自分のターンの終わりに、そのターン呪文を唱えていれば、相手のパワー5500以下を1体破壊して1枚引く"""
    if s.P[i].spl < 1:
        return
    t = s.target(i, lambda z: s.power(1 - i, z) <= 5500)
    if t is not None:
        s.ev(f"　ザーディクリカ：{t.c.name} を破壊")
        destroy(s, i, t)
    s.draw(i, 1)


add("k47_zaadik", "龍風混成 ザーディクリカ", 7, "LWF", power=6000, brk=2,
    races=("dispector", "crystalcommanddragon", "command", "angelcommand", "meltwarrior", "dragon"),
    pri=10, roles="rem draw fin shd",
    enter=e_zaadik, tend=t_zaadik, leaverep=exlife_rep,
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。W・ブレイカー。"
         "このクリーチャーが出た時、コスト7以下の呪文を1枚、自分の手札または墓地からコストを支払わずに"
         "唱えてもよい。それを唱えた後、墓地に置くかわりに山札の下に置く。"
         "自分のターンの終わりに、そのターン自分が呪文を唱えていれば、"
         "相手のパワー5500以下のクリーチャーを1体選んで破壊し、カードを1枚引いてもよい",
    note="ただで唱える呪文は、手札と墓地のうち重要度のいちばん高いものを選ぶ（全デッキ共通の決まり）",
    source=SRC["k47_zaadik"])


# ================================================================ 2 月下卍壊 ガ・リュミーズ 卍
def sp_garumiz(s, i):
    """ドルスザクを4体まで手札か墓地からただで召喚し、このターンの後に自分のターンを追加する"""
    p = s.P[i]
    done = 0
    while done < 4 and not s.over:
        best, bz = None, None
        for zn in ("hand", "grave"):
            for k in sorted(set(_zone(s, i, zn))):
                c = BY_KEY[k]
                if c.kind != "C" or "dorusuzaku" not in c.races:
                    continue
                if c.evo and not c.neo:
                    continue                  # 進化クリーチャーは進化元が要るので召喚できない
                if s.fate(i, k, zn, True) != "ok":
                    continue
                if best is None or E.PRI[k] > E.PRI[best]:
                    best, bz = k, zn
        if best is None:
            break
        _zone(s, i, bz).remove(best)
        s.ev(f"　ガ・リュミーズ：{BY_KEY[best].name} をコストを支払わずに召喚")
        s.enter(i, best, bz, True)
        done += 1
    p.extra += 1
    s.ev("　ガ・リュミーズ：このターンの後に自分のターンを追加する")


add("k47_garumiz", "月下卍壊 ガ・リュミーズ 卍", 99, "W", kind="S", races=("dorusuzaku",),
    pri=12, roles="fin acc",
    spell=sp_garumiz,
    text="呪文：ドルスザク。コストは99。"
         "ドルスザク・クリーチャーを4体まで、自分の手札または墓地からコストを支払わずに召喚してもよい。"
         "このターンの後に自分のターンを追加する",
    note="素のコストが99なので、通常のマナでは唱えられない（《水晶の王 ゴスペル》の攻撃時のように、"
         "コストの上限なしで呪文を踏み倒す能力から唱えるカード）。"
         "別コスト（無月の門など）は持っていないので、そこは何も足していない",
    source=SRC["k47_garumiz"])


# ================================================================ 3 水晶の王 ゴスペル
def cx_gospel(s, i, av):
    """自分の墓地にある呪文1枚につき召喚コストを1少なくする（1より少なくはならない）"""
    n = sum(1 for k in s.P[i].grave if _is_spellcard(k))
    return max(1, 9 - n)


def e_gospel(s, i, u):
    """出た時、呪文を好きな数、自分の墓地から手札に戻す（全部戻す）"""
    p = s.P[i]
    got = [k for k in p.grave if _is_spellcard(k)]
    for k in got:
        p.grave.remove(k)
        p.hand.append(k)
    if got:
        s.ev(f"　ゴスペル：墓地の呪文{len(got)}枚を手札に戻した")


def a_gospel(s, i, u):
    """攻撃する時、呪文を1枚、自分の手札からコストを支払わずに唱えてもよい"""
    _cast_free(s, i, ("hand",), maxcost=None, tag="ゴスペル")


add("k47_gospel", "水晶の王 ゴスペル", 9, "LW", power=11000, brk=2, blocker=True,
    races=("oracleceres", "kingcommanddragon", "command", "dragon", "unknown"),
    pri=11, roles="blk draw fin",
    costx=cx_gospel, enter=e_gospel, attack=a_gospel,
    text="このクリーチャーの召喚コストを、自分の墓地にある呪文1枚につき1少なくする"
         "（ただしコストは1以下にはならない）。ブロッカー、W・ブレイカー。"
         "このクリーチャーが出た時、呪文を好きな数、自分の墓地から手札に戻す。"
         "このクリーチャーが攻撃する時、呪文を1枚、自分の手札からコストを支払わずに唱えてもよい",
    note="墓地から戻す呪文は「好きな数」なので全部戻す。ツインパクトは呪文側があるので呪文として数える。"
         "攻撃時に唱える呪文は、手札のうち重要度のいちばん高いものを選ぶ（全デッキ共通の決まり）",
    source=SRC["k47_gospel"])


# ================================================================ 4 芸魔王将 カクメイジン
def sa_kakumeijin(s, i, u):
    """自分のマジックすべてに「スピードアタッカー」を与える"""
    return u.c.kind == "C" and _is_magic(u.c) and s.has(i, "k47_kakumeijin")


def bp_kakumeijin(s, ai, di, n):
    """このクリーチャーの各ブレイクの前に、マナの枚数以下のコストの呪文を1枚ただで唱えてもよい"""
    if s.atk is None or s.atk.k != "k47_kakumeijin" or not s.has(ai, "k47_kakumeijin"):
        return n
    for _ in range(max(0, n)):
        if s.over:
            return 0
        if not _cast_free(s, ai, ("hand", "grave"), maxcost=len(s.P[ai].mana),
                          bottom=True, tag="カクメイジン"):
            break
    return 0 if s.over else n


add("k47_kakumeijin", "芸魔王将 カクメイジン", 7, "WF", power=10000, brk=2,
    races=("magicdragon", "gamecommand", "command", "dragon"),
    pri=10, roles="atk acc fin",
    saok=sa_kakumeijin, breakpre=bp_kakumeijin,
    changex=lambda s, i, u: u.c.cost >= 5 and _is_magic(u.c),
    playrule=_change_rule(lambda c: c.kind == "C" and c.cost >= 5 and _is_magic(c),
                          "革命チェンジの元（コスト5以上のマジック）が3枚ない"),
    text="革命チェンジ：コスト5以上のマジック。W・ブレイカー。"
         "自分のマジックすべてに「スピードアタッカー」を与える。"
         "このクリーチャーの各ブレイクの前に、自分のマナゾーンにあるカードの枚数以下のコストを持つ呪文を1枚、"
         "自分の手札または墓地からコストを支払わずに唱えてもよい。"
         "それを唱えた後、墓地に置くかわりに山札の下に置く",
    note="「各ブレイクの前に」は、エンジンがシールドをまとめて割る作りなので、"
         "割る枚数ぶんの呪文を、割る直前にまとめて唱える形にした（唱える回数は同じ。"
         "1枚割るごとに割り込む形ではないので、唱えた呪文で相手のシールドが増減した時だけ順序が違う）",
    source=SRC["k47_kakumeijin"])


# ================================================================ 5 「勝利」の頂 カイザー「刃鬼」
def cx_hakki(s, i, av):
    """シンパシー：ハンター・クリーチャー（1体につきコストを1少なくする。0以下にはならない）"""
    n = sum(1 for z in s.P[i].board if z.c.kind == "C" and _is_hunter(z.c))
    return max(0, 11 - n)


def _mekleid_hunter(s, i):
    """ハンター・W・メクレイド10：山札の上6枚から、コスト10以下のハンターを2枚までただで使う"""
    p = s.P[i]
    n = min(6, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    cands = sorted([k for k in top if _is_hunter(BY_KEY[k]) and BY_KEY[k].cost <= 10],
                   key=lambda x: -E.PRI[x])
    got = 0
    for k in cands:
        if got >= 2 or s.over:
            break
        top.remove(k)
        if _use_free(s, i, k, "deck"):
            s.ev(f"　ハンター・W・メクレイド10：{BY_KEY[k].name} を使う")
            got += 1
        else:
            top.append(k)
    for k in top:
        p.deck.insert(0, k)


def e_hakki(s, i, u):
    if u.x.get("summoned"):
        _mekleid_hunter(s, i)


def sa_hakki(s, i, u):
    """相手のシールドが5つ以上あれば、このクリーチャーに「スピードアタッカー」を与える"""
    return u.k == "k47_hakki" and len(s.P[1 - i].sh) >= 5


add("k47_hakki", "「勝利」の頂 カイザー「刃鬼」", 11, "WFN", power=17000, brk=3, jd=True,
    races=("redcommanddragon", "command", "dragon", "gianthunter", "giant", "hunter", "zenith"),
    pri=13, roles="fin acc atk",
    costx=cx_hakki, enter=e_hakki, attack=lambda s, i, u: _mekleid_hunter(s, i), saok=sa_hakki,
    text="シンパシー：ハンター・クリーチャー（自分のハンター・クリーチャー1体につき、"
         "このクリーチャーの召喚コストを1少なくする。ただしコストは0以下にはならない）。"
         "ジャストダイバー、T・ブレイカー。"
         "このクリーチャーが召喚によって出た時または攻撃する時、ハンター・W・メクレイド10する"
         "（自分の山札の上から6枚を見て、その中からコスト10以下のハンターを2枚まで、"
         "コストを支払わずに使い、残りを山札の下に置く）。"
         "相手のシールドが5つ以上あれば、このクリーチャーに「スピードアタッカー」を与える",
    note="メクレイドで使うカードは重要度の高いものから選ぶ（全デッキ共通の決まり）。"
         "進化クリーチャーは進化元がいる時だけ出す",
    source=SRC["k47_hakki"])


# ================================================================ 6 アビスベル＝覇＝ロード
def mk_haload(s, i, u):
    """自分のアビスすべてに「マッハファイター」を与える"""
    return u.c.kind == "C" and _is_abyss(u.c) and s.has(i, "k47_haload")


def t_haload(s, i, u):
    """自分のターンの終わりに、コスト6以下のアビスを1体、自分の墓地またはマナゾーンから出してもよい"""
    for src in ("grave", "mana"):
        if s.revive(i, lambda c: c.cost <= 6 and _is_abyss(c), src) is not None:
            s.ev("　覇＝ロード：ターンの終わりにアビスを1体出した")
            return


def gs_haload(s, i, cards):
    """このデッキに覇＝ロードが入っている印（攻撃を数えるのを、入っている対戦だけに限るため）"""
    s.P[i].x["k47_hal"] = True


def aw_haload(s, i, u):
    """このターン、そのプレイヤーがもう攻撃したことを書き留める（はじめての攻撃の判定用）"""
    if s.P[1 - i].x.get("k47_hal"):
        s.P[i].x["k47_atk"] = s.turn


def mat_haload(s, i, u, tg):
    """攻撃先の強制：各ターン、相手（i）のクリーチャーがはじめて攻撃するなら、
    可能なら覇＝ロードを攻撃する。候補 tg を絞り終えた後に呼ばれるので、
    攻撃先に選べない時（パワー不足・ジャストダイバーなど）は縛られない"""
    j = 1 - i
    if not s.has(j, "k47_haload"):
        return None
    if s.P[i].x.get("k47_atk") == s.turn:
        return None                          # このターンもう攻撃している
    b = s.P[j].board
    for n in tg:
        if n != "P" and b[n].k == "k47_haload" and b[n].c.kind == "C":
            return n
    return None


add("k47_haload", "アビスベル＝覇＝ロード", 7, "DN", power=11000, brk=2,
    races=("abyssroyal", "abyss"), pri=9, roles="atk rem fin dis",
    machok=mk_haload, tend=t_haload,
    gamestart=gs_haload, atkwatch=aw_haload, mustatktgt=mat_haload,
    changex=lambda s, i, u: u.c.cost >= 5 and _is_abyss(u.c),
    playrule=_change_rule(lambda c: c.kind == "C" and c.cost >= 5 and _is_abyss(c),
                          "革命チェンジの元（コスト5以上のアビス）が3枚ない"),
    text="革命チェンジ：コスト5以上のアビス。W・ブレイカー。"
         "自分のアビスすべてに「マッハファイター」を与える。"
         "自分のターンの終わりに、コスト6以下のアビス・クリーチャーを1体、"
         "自分の墓地またはマナゾーンから出してもよい。"
         "各ターン、相手のクリーチャーがはじめて攻撃するなら、可能ならこのカードを攻撃する",
    source=SRC["k47_haload"])


# ================================================================ 7 「正義星帝」 ＜ライオネル.Star＞
def _lionel_src(c):
    return c.kind == "C" and ("rexstars" in c.races or race_like(c, "rexstars") or "L" in c.civ)


def e_lionel(s, i, u):
    """出た時、1枚引く。その後、光のタマシードを1つ、自分の手札から出してもよい"""
    s.draw(i, 1)
    p = s.P[i]
    cands = [k for k in sorted(set(p.hand)) if BY_KEY[k].kind == "T" and "L" in E.MCIV[k]]
    if not cands:
        return
    k = max(cands, key=E.PRI.get)
    p.hand.remove(k)
    s.ev(f"　正義星帝：手札から {BY_KEY[k].name} を出す")
    s.place_tama(i, k)


def tm_lionel(s, i, u):
    """各ターン1度、自分のタマシードが出た時、コスト6以下の進化クリーチャーを1体、手札から出してもよい"""
    if not s.has(i, "k47_lionel"):
        return
    p = s.P[i]
    if p.x.get("k47_lio") == s.turn:
        return
    best, bon = None, None
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or not c.evo or c.cost > 6:
            continue
        on = s.evo_src(i, k)
        if on is None and not c.neo:
            continue
        if s.fate(i, k, "hand", False) != "ok":
            continue
        if best is None or E.PRI[k] > E.PRI[best]:
            best, bon = k, on
    if best is None:
        return
    p.x["k47_lio"] = s.turn
    p.hand.remove(best)
    s.ev(f"　正義星帝：タマシードが出たので {BY_KEY[best].name} を手札から出す")
    s.enter(i, best, "hand", False, on=bon)


add("k47_lionel", "「正義星帝」 ＜ライオネル.Star＞", 5, "L", power=9500, brk=2, evo="L",
    races=("metallica", "angelcommand", "command", "rexstars"),
    pri=8, roles="draw acc fin",
    enter=e_lionel, tamain=tm_lionel, leaverep=star_evo_rep("k47_lionel", "「正義星帝」 ＜ライオネル.Star＞"),
    evox=lambda s, i, u: _lionel_src(u.c),
    playrule=_change_rule(_lionel_src, "スター進化の下にできるカード（レクスターズか光のクリーチャー）が4枚ない", 4),
    text="スター進化：レクスターズまたは光のクリーチャー1体の上に置く"
         "（離れる時は一番上のこのカードだけが離れ、下のカードがバトルゾーンに残る）。W・ブレイカー。"
         "このクリーチャーが出た時、カードを1枚引く。その後、光のタマシードを1つ、自分の手札から出してもよい。"
         "各ターンに1度、自分のタマシードが出た時、コスト6以下の進化クリーチャーを1体、"
         "自分の手札から出してもよい",
    note="出すタマシード・進化クリーチャーは、手札のうち重要度のいちばん高いものを選ぶ"
         "（全デッキ共通の決まり）。進化元がいない進化クリーチャーは出さない（NEO進化は進化元なしでも出す）",
    source=SRC["k47_lionel"])


# ================================================================ 8 天風のゲイル・ヴェスパー
def _vesper_big(s, i):
    return sum(1 for z in s.P[i].board if z.c.kind == "C" and s.power(i, z) >= 12000)


def cx_vesper(s, i, av):
    """W・シンパシー：パワー12000以上のクリーチャー1体につきコストを2少なくする"""
    return max(0, 10 - 2 * _vesper_big(s, i))


def ca_vesper(s, i, k, cur):
    """自分の手札にあるクリーチャーすべてに、同じ「W・シンパシー」を与える"""
    if cur <= 0 or k == "k47_vesper" or BY_KEY[k].kind != "C":
        return cur
    if not s.has(i, "k47_vesper"):
        return cur
    return max(0, cur - 2 * _vesper_big(s, i))


add("k47_vesper", "天風のゲイル・ヴェスパー", 10, "N", power=12000, brk=3,
    races=("gransect",), pri=11, roles="acc fin",
    costx=cx_vesper, costaura=ca_vesper,
    text="W・シンパシー：パワー12000以上のクリーチャー（自分のパワー12000以上のクリーチャー1体につき、"
         "このクリーチャーの召喚コストを2少なくする。ただしコストは0以下にはならない）。T・ブレイカー。"
         "自分の手札にあるクリーチャーすべてに、「W・シンパシー：パワー12000以上のクリーチャー」を与える",
    note="紙（TCG）版のコスト10で入れてある（デュエプレ版は8）",
    source=SRC["k47_vesper"])


# ================================================================ 9 超重竜 ゴルファンタジスタ
def ub_golfan(s, i, u):
    """自分のジャイアントはブロックされない"""
    return u.c.kind == "C" and _is_giant(u.c) and s.has(i, "k47_golfan")


def e_golfan(s, i, u):
    """出た時、コスト6以下のジャイアントを1体、自分のマナゾーンから出してもよい"""
    if s.revive(i, lambda c: c.cost <= 6 and _is_giant(c), "mana") is not None:
        s.ev("　ゴルファンタジスタ：マナからジャイアントを1体出した")


def ts_golfan(s, i, u):
    """終極宣言（ゲーム中1度）：自分のターンのはじめに、手札と同じ枚数引き、
    その後マナの枚数と同じ枚数を山札の上からマナゾーンに置く"""
    p = s.P[i]
    if p.x.get("k47_golfan_dec"):
        return
    n = min(len(p.hand), max(0, len(p.deck) - 1))
    m = min(len(p.mana), max(0, len(p.deck) - 1 - n))
    if n <= 0 and m <= 0:
        return
    p.x["k47_golfan_dec"] = True
    if n:
        s.draw(i, n)
    if m:
        s.ramp(i, m)
    s.ev(f"　終極宣言：{n}枚引き、{m}枚をマナゾーンに置いた（ゲーム中1度だけ）")


add("k47_golfan", "超重竜 ゴルファンタジスタ", 7, "WN", power=12000, brk=3,
    races=("giantdragon", "giant", "dragon"), pri=10, roles="acc draw fin atk",
    enter=e_golfan, tstart=ts_golfan, unbok=ub_golfan,
    changex=lambda s, i, u: u.c.cost >= 5 and _is_giant(u.c),
    playrule=_change_rule(lambda c: c.kind == "C" and c.cost >= 5 and _is_giant(c),
                          "革命チェンジの元（コスト5以上のジャイアント）が3枚ない"),
    text="革命チェンジ：コスト5以上のジャイアント。T・ブレイカー。"
         "自分のジャイアントはブロックされない。"
         "このクリーチャーが出た時、コスト6以下のジャイアント・クリーチャーを1体、"
         "自分のマナゾーンから出してもよい。"
         "終極宣言：自分のターンのはじめに、自分の手札と同じ枚数のカードを引いてもよい。その後、"
         "自分のマナゾーンにあるカードと同じ枚数のカードを、自分の山札の上からマナゾーンに置いてもよい"
         "（「終極宣言」はゲーム中に一度だけ使える）",
    note="終極宣言は、山札が尽きて負けないように「山札を1枚は残す」ところまでしか引かない／置かない。"
         "ゲーム中1度の印はプレイヤーごとに持つ",
    source=SRC["k47_golfan"])


# ================================================================ 10 五輪の求道者 清永
def a_kiyonaga(s, i, u):
    """攻撃する時、山札の上3枚を表向きにし、すべて違うコストなら、その中のコスト9以下の
    エレメントを好きな数ただで実行してもよい。残りをすべてマナゾーンに置く"""
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    s.ev("　清永：山札の上3枚を表向きにする（"
         + "／".join(BY_KEY[k].name for k in top) + "）")
    if n == 3 and len({BY_KEY[k].cost for k in top}) == 3:
        cands = sorted([k for k in top if BY_KEY[k].kind != "S" and BY_KEY[k].cost <= 9],
                       key=lambda x: -E.PRI[x])
        for k in cands:
            if s.over:
                break
            top.remove(k)
            if _play_elem(s, i, k, "deck"):
                s.ev(f"　清永：{BY_KEY[k].name} をコストを支払わずに実行")
            else:
                top.append(k)
    else:
        s.ev("　清永：同じコストがあったので踏み倒せない")
    for k in top:
        s.add_mana(i, k, src="deck")


add("k47_kiyonaga", "五輪の求道者 清永", 6, "LWN", power=8500, brk=2,
    blocker=True, mach=True, jd=True,
    races=("dreammate", "samurai", "wizard"), pri=9, roles="blk acc rem fin",
    attack=a_kiyonaga,
    text="ブロッカー、マッハファイター、ジャストダイバー、W・ブレイカー。"
         "このクリーチャーが攻撃する時、自分の山札の上から3枚を表向きにする。"
         "それらがすべて異なるコストなら、その中から、コスト9以下のエレメントを好きな数、"
         "コストを支払わずに実行してもよい。残りをすべてマナゾーンに置く",
    note="「好きな数」なので、出せるエレメントは重要度の高い順に全部実行する（全デッキ共通の決まり）。"
         "進化クリーチャーは進化元がいる時だけ出す。呪文はエレメントではないので踏み倒さない",
    source=SRC["k47_kiyonaga"])


# ================================================================ 11 蒼狼の豊穣 ワクムテラス／オリジナル・ライフ
def e_wakumu(s, i, u):
    s.draw(i, 2)


def sp_wakumu(s, i):
    s.ramp(i, 1)


add("k47_wakumu", "蒼狼の豊穣 ワクムテラス／オリジナル・ライフ", 4, "W", power=4000,
    races=("knight", "samurai", "origin"), twin=(2, "N", False), pri=5, roles="draw acc",
    enter=e_wakumu, spell=sp_wakumu,
    text="クリーチャー側《蒼狼の豊穣 ワクムテラス》（コスト4・水・パワー4000・ナイト／サムライ／オリジン）："
         "このクリーチャーが出た時、カードを2枚引く。"
         "呪文側《オリジナル・ライフ》（コスト2・自然）：自分の山札の上から1枚をマナゾーンに置く",
    source=SRC["k47_wakumu"])


# ================================================================ 12 聖魔連結王 ドルファディロム
def _dolfa_wipe(s, i):
    """相手の多色ではないクリーチャーをすべて破壊する"""
    got = 0
    for z in opp_all(s, i, lambda x: not E.MULTI[x.k]):
        if s.over:
            break
        if z in s.P[1 - i].board:
            destroy(s, i, z)
            got += 1
    if got:
        s.ev(f"　ドルファディロム：相手の多色でないクリーチャー{got}体を破壊")


def e_dolfa(s, i, u):
    exlife_enter(s, i, u)
    _dolfa_wipe(s, i)


EXLOST["k47_dolfa"] = lambda s, i, u: _dolfa_wipe(s, i)


def _spell_civ(k, _cost=None):
    """いま唱えようとしている呪文の文明。ツインパクトは呪文側の文明を返す"""
    c = BY_KEY[k]
    if c.kind != "S" and c.twin:
        return c.twin[1]
    return c.civ


def sl_dolfa(s, i, cost, k=None):
    """相手は多色ではない呪文を唱えられない"""
    if k is None:
        return False                         # 呪文が分からない時は止めない
    if not s.has(1 - i, "k47_dolfa"):
        return False
    return len(set(_spell_civ(k, cost))) < 2


add("k47_dolfa", "聖魔連結王 ドルファディロム", 8, "LDF", power=13500, brk=3, sa=True,
    races=("dispector", "angelcommand", "command", "demoncommand"),
    pri=12, roles="rem fin dis shd",
    enter=e_dolfa, leaverep=exlife_rep, spelllock=sl_dolfa,
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。スピードアタッカー、T・ブレイカー。"
         "このクリーチャーが出た時、またはこのクリーチャーの「EXライフ」シールドが離れた時、"
         "相手の多色ではないクリーチャーをすべて破壊する。"
         "相手は多色ではない呪文を唱えられない",
    source=SRC["k47_dolfa"])


# ================================================================ 13 王道の革命 ドギラゴン
def e_odokaku(s, i, u):
    """出た時、山札の上2枚をマナゾーンに置き、その後クリーチャー1体をマナゾーンから手札に戻す"""
    s.ramp(i, 2)
    p = s.P[i]
    cands = [k for k in p.mana if BY_KEY[k].kind == "C"]
    if not cands:
        return
    k = max(cands, key=E.PRI.get)
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　王道の革命：マナの {BY_KEY[k].name} を手札に戻した")


def tg_odokaku(s, di, k):
    """革命2：自分のシールドが2つ以下なら、シールドゾーンから手札に加えるこのカードはS・トリガーを得る"""
    return k == "k47_odokaku" and len(s.P[di].sh) <= 2


def _base_dies(s, ai, au, di, du):
    """エンジンがもともと出すバトルの結果（ほかの差し込み口が足した分を見分けるため）"""
    ap = s.power(ai, au, True) + (2000 if au.k == "testa" else 0)
    dp = s.power(di, du) + (2000 if du.k == "testa" else 0)
    return (ap <= dp or du.k == "kuzen"), (dp <= ap or au.k == "kuzen"), ap, dp


def bf_odokaku(s, ai, au, di, du, a_dies, d_dies):
    """革命0：自分のシールドが1つもなければ、バトル中パワー+10000し、バトルに勝った時アンタップする"""
    if au.k != "k47_odokaku" and du.k != "k47_odokaku":
        return a_dies, d_dies
    ba, bd, ap, dp = _base_dies(s, ai, au, di, du)
    amine = au.k == "k47_odokaku" and not s.P[ai].sh
    dmine = du.k == "k47_odokaku" and not s.P[di].sh
    if not amine and not dmine:
        return a_dies, d_dies
    if amine:
        ap += 10000
    if dmine:
        dp += 10000
    na = (ap <= dp or du.k == "kuzen") or (a_dies and not ba)   # ほかの差し込み口が立てた分は残す
    nd = (dp <= ap or au.k == "kuzen") or (d_dies and not bd)
    if amine and nd and not na:
        au.tap = False
        s.ev("　革命0：王道の革命 ドギラゴンはバトルに勝ってアンタップする")
    if dmine and na and not nd:
        du.tap = False
        s.ev("　革命0：王道の革命 ドギラゴンはバトルに勝ってアンタップする")
    return na, nd


add("k47_odokaku", "王道の革命 ドギラゴン", 5, "LFN", power=5000, blocker=True, sa=True,
    races=("megacommanddragon", "command", "dragon", "kakumeigun"),
    pri=7, roles="acc blk atk trg",
    enter=e_odokaku, trigok=tg_odokaku, battlefx=bf_odokaku,
    text="ブロッカー、スピードアタッカー。"
         "このクリーチャーが出た時、自分の山札の上から2枚をマナゾーンに置く。その後、クリーチャーを1体、"
         "自分のマナゾーンから手札に戻す。"
         "革命2：自分のシールドが2つ以下なら、自分のシールドゾーンから手札に加えるこのクリーチャーに"
         "「S・トリガー」を与える。"
         "革命0：自分のシールドが1つもなければ、バトル中、このクリーチャーのパワーを+10000し、"
         "このクリーチャーがバトルに勝った時、アンタップする",
    note="マナから手札に戻すクリーチャーは、重要度のいちばん高いものを選ぶ（全デッキ共通の決まり）",
    source=SRC["k47_odokaku"])


# ================================================================ 14 勝利宣言 鬼丸「覇」
def px_onimaru(s, i, u, atk):
    """パワーアタッカー+5000"""
    return 5000 if atk else 0


def a_onimaru(s, i, u):
    """攻撃する時、相手とガチンコ・ジャッジする。勝ったら、このターンの後に自分のターンを追加する"""
    if _gachinko(s, i):
        s.P[i].extra += 1
        s.ev("　鬼丸「覇」：ガチンコ・ジャッジに勝った → このターンの後に自分のターンを追加する")
    else:
        s.ev("　鬼丸「覇」：ガチンコ・ジャッジに負けた")


add("k47_onimaru", "勝利宣言 鬼丸「覇」", 10, "F", power=9000, brk=3, sa=True,
    races=("humanoid", "redcommanddragon", "command", "dragon", "hunter", "alien"),
    pri=12, roles="fin atk",
    powerx=px_onimaru, attack=a_onimaru,
    text="スピードアタッカー、パワーアタッカー+5000（攻撃中はパワーが+5000）、T・ブレイカー。"
         "このクリーチャーが攻撃する時、相手とガチンコ・ジャッジする。"
         "自分が勝ったら、このターンの後に自分のターンを追加する"
         "（ガチンコ・ジャッジ：互いに山札の上から1枚を表向きにし、コストが同じかこちらが大きければ"
         "仕掛けた側の勝ち。表向きにしたカードは山札の一番下に置く）",
    note="2014年5月24日に殿堂入りしたが、2023年8月11日に殿堂解除された（いまは枚数の制限なし）。"
         "ガチンコ・ジャッジでツインパクトがめくれた時は、持ち主が有利な（コストの大きい）側で数える",
    source=SRC["k47_onimaru"])


# ================================================================ 15 配球の超人／記録的剛球
def e_haikyu(s, i, u):
    """出た時、相手のクリーチャーを1体選び、持ち主のマナゾーンに置く"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　配球の超人：{t.c.name} を相手のマナゾーンに置く")
    move(s, i, t, "mana")


def sp_haikyu(s, i):
    s.ramp(i, 1)


add("k47_haikyu", "配球の超人／記録的剛球", 8, "N", power=14000, brk=3,
    races=("giant",), twin=(2, "N", False), pri=9, roles="rem acc fin",
    enter=e_haikyu, spell=sp_haikyu,
    text="クリーチャー側《配球の超人》（コスト8・自然・パワー14000・ジャイアント）：T・ブレイカー。"
         "このクリーチャーが出た時、相手のクリーチャーを1体選び、持ち主のマナゾーンに置く。"
         "呪文側《記録的剛球》（コスト2・自然／呪文：ジャイアント・スキル）："
         "自分の山札の上から1枚をマナゾーンに置く",
    source=SRC["k47_haikyu"])
