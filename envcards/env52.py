"""担当52：DM26-SD1「ドキドキつよいデッキ 25の王道」の未実装カード15枚

出典：dmwiki.net の各カードページ（本文が切れる分は生の wiki ソース
      `?plugin=template&refer=《カード名》` で cardtable 行と能力行の並びを突き合わせた）。
      15枚すべて、別の質問で2回ずつ読んで、コスト・文明・種類・種族・パワー・
      ブレイク数・能力の並びがどちらも一致することを確かめた。

  この担当分に入っている新しい仕組み
    ・アーマード（種族名に「アーマード」を含む）のサポート一式
      ＝アシスター・コッピ（各ターン1度のコスト軽減）／ボルシャック・サイン（手札からの踏み倒し）／
        革命チェンジ：アーマード（ヴァル・ボルシャック／ボルシャック・フレア／ボルシャック・ヴォルジャアク）
    ・「召喚コストを1少なくしてもよい。そうしたら〜」という、**支払った額で誘発が変わる**書き方
      （ボルザード・ゴールド・ドラゴン＝自分のシールドを1つブレイク、
        頂上印鑑 パラキン8th＝このターンの終わりに自身を破壊）。
      `costx=`（必要な時だけ下げる）と `payx=`（下げたら「待ち」を1つ積む）と `enter=`（待ちを1つ消費）の3つで書いた。
    ・終極宣言（ボルシャック・ヴォルジャアク）＝1ゲームに1度、自分のシールドをすべて自分でブレイクして、
      次の自分のターンのはじめまで負けない（`tstart=` と `loserep=`）。
    ・ドラゴン以外のクリーチャーが出るのを置き換える（龍世界 ドラゴ大王）＝`fatex=` で "grave" を返す。
    ・ドラゴン・W・ブレイカー（煌龍 サッヴァーク）＝ブレイクの直前にシールドを増やす（`breakpre=`）。
    ・表向きのシールドを墓地に置いて自分のクリーチャーを守る（煌龍 サッヴァーク、`leaverep=`）。

  調べ直して意外だった点
    ・《GENJI・ハイパーXX》は名前に「ハイパー」とあるがハイパーモードは持たない
      （wiki の生ソースにハイパーモード欄の区切り `BGCOLOR(#cde):|c|` が無い）。
      能力はハイパーエナジーとスピードアタッカーの2つだけ。
    ・《ボルシャック・サイン》には S・トリガーが無く、踏み倒した後に
      「自分のエレメントを1つ破壊する」という強制のデメリットが付く。
    ・《頂上印鑑 パラキン8th》の2つめの種族は「アーマードン」で、
      種族名に「アーマード」を含むのでアーマードのサポートを受けられる。
    ・《煌龍 サッヴァーク》の2つの能力は「シールドの上に重ねる」（シールド・プラス）で、
      この仕組みはエンジンに無い。そこだけ近似した（note に理由）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all
from envcards.env0 import discard_choice, he_costx, he_payx, race_like

W = "https://dmwiki.net/"
SRC = {
    "k52_genji": W + "《GENJI・ハイパーXX》",
    "k52_coppi": W + "《アシスター・コッピ》",
    "k52_vorjaak": W + "《ボルシャック・ヴォルジャアク》",
    "k52_flare": W + "《輝く革命 ボルシャック・フレア》",
    "k52_valbol": W + "《飛ぶ革命 ヴァル・ボルシャック》",
    "k52_parakin": W + "《頂上印鑑 パラキン8th／「魔物が居るな……」》",
    "k52_bolsign": W + "《ボルシャック・サイン》",
    "k52_superhero": W + "《ボルシャック・スーパーヒーロー／超英雄タイム》",
    "k52_bolzard": W + "《ボルザード・ゴールド・ドラゴン》",
    "k52_savvark": W + "《煌龍 サッヴァーク》",
    "k52_zeos": W + "《サーヴァ・K・ゼオス》",
    "k52_triclub": W + "《蒼神龍トライクラブ・トライショット》",
    "k52_suzu": W + "《熊田すず》",
    "k52_dragodaio": W + "《龍世界 ドラゴ大王》",
    "k52_megumega": W + "《真久間メガ》",
}

ARMORED_CHANGE = "革命チェンジの元になるコスト5以上のアーマード・クリーチャーが3体いない"


# ================================================================ 共通の道具
def _armored(c):
    """アーマード（種族名に「アーマード」を含む）か"""
    return race_like(c, "armored")


def _dragon(c):
    """ドラゴン（種族名に「ドラゴン」を含む）か"""
    return race_like(c, "dragon")


def _bolshack(c):
    return "ボルシャック" in c.name


def _playable_cre(c):
    """進化元が要らない（コストを支払わずに出せる）クリーチャーか"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _pick_from_hand(s, i, pred):
    """手札から pred に合う、重要度のいちばん高いクリーチャー1体を出す（出せたらそのキー）"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if not _playable_cre(c) or not pred(c):
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    return best


def _self_break(s, i, n=1):
    """自分のシールドを n つブレイクする（自分のS・トリガーは使える）"""
    if s.P[i].sh and n > 0:
        s.break_sh(1 - i, n)


def _worst_element(s, i, skip=None):
    """自分のエレメント（バトルゾーンのカード）のうち、失うのがいちばん安いもの"""
    best, bv = None, None
    for z in s.P[i].board:
        if z.c.kind not in "CTX" or z is skip:
            continue
        v = s.val(z) if z.c.kind == "C" else E.PRI[z.k]
        if bv is None or v < bv:
            best, bv = z, v
    return best


def _need_disc(s, i, k, base, av):
    """「召喚コストを1少なくしてもよい」を使う必要があるか。

    どちらのカードも「下げると損になる誘発（自分のシールドをブレイク／ターンの終わりに破壊）」が
    付くので、**ほかの軽減（アシスター・コッピなど）を effect させても払えない時だけ**下げる。
    エンジンの ccost は COSTX のあとに COSTAURA をかけるので、ここでも同じ順で計算して比べる
    （COSTAURA の関数はどれも値を返すだけで、盤面を変えない）。"""
    n = base
    for f in E.COSTAURA:
        n = f(s, i, k, n)
    return n > av


def _cheap_disc(key, base):
    """「召喚コストを1少なくしてもよい」：損になる誘発が付くので、**足りない時だけ**下げる"""
    def f(s, i, av):
        return base - 1 if _need_disc(s, i, key, base, av) else base
    return f


def _disc_pay(key, base):
    """下げて払ったら「待ち」を1つ積む（出た時の誘発の判定に使う）。
    turn を一緒に持つので、出られなかった時に次のターンへ持ち越さない。

    判定は `_cheap_disc` と同じ `_need_disc` で見る。
    払った額（n）で見ると、アシスター・コッピのような**別のカードの軽減**で安くなった時に
    「自分で1下げた」と誤判定してしまう。"""
    def f(s, i, k, n):
        p = s.P[i]
        if not _need_disc(s, i, k, base, len(p.mana) - p.mused):
            return None                   # 自分の軽減は使っていない
        t, c = p.x.get(key, (-1, 0))
        p.x[key] = (s.turn, (c if t == s.turn else 0) + 1)
        return None
    return f


def _disc_take(s, i, key):
    """積んである「待ち」を1つ消費する（下げて召喚されたか）"""
    p = s.P[i]
    t, c = p.x.get(key, (-1, 0))
    if t != s.turn or c <= 0:
        return False
    p.x[key] = (s.turn, c - 1)
    return True


# ================================================================ 1. GENJI・ハイパーXX
add("k52_genji", "GENJI・ハイパーXX", 5, "F", power=5000, sa=True,
    races=("armoreddragon", "armored", "dragon", "flame", "command", "samurai"), pri=6, roles="atk",
    costx=he_costx("k52_genji"), payx=he_payx("k52_genji"),
    text="ハイパーエナジー（このクリーチャーを召喚する時、コストが異なる自分のクリーチャーを好きな数タップしてよい。"
         "タップした1体につき、召喚コストを2少なくする。ただし0以下にはならない）。"
         "スピードアタッカー。"
         "（名前に「ハイパー」とあるが、ハイパーモードは持たない）",
    source=SRC["k52_genji"])


# ================================================================ 2. アシスター・コッピ
def px_coppi(s, i, u, atk):
    """パワーアタッカー+2000"""
    return 2000 if atk else 0


def ca_coppi(s, i, k, cur):
    """各ターンに1度、自分のアーマード・カードを使うコストを1少なくする（0以下にはならない）"""
    if cur <= 1 or not _armored(BY_KEY[k]):
        return cur
    p = s.P[i]
    if not any(z.k == "k52_coppi" for z in p.board):
        return cur
    if p.x.get("k52_coppi_t") == s.turn:
        return cur
    return max(1, cur - 1)


def ew_coppi(s, i, u):
    """軽減が効いたアーマードの召喚が1回あったら、そのターンはもう軽減しない"""
    if u.c.kind != "C" or not u.x.get("summoned") or not _armored(u.c):
        return
    p = s.P[i]
    if not any(z.k == "k52_coppi" and z is not u for z in p.board):
        return
    if p.x.get("k52_coppi_t") == s.turn:
        return
    p.x["k52_coppi_t"] = s.turn


def sa_coppi(s, i, k, twin=False):
    """各ターンに1度、自分のアーマード呪文を使うコストを1少なくする（0以下にはならない）。

    `spcostaura=` は呪文全体にかかるので、コッピが場にある持ち主のアーマード呪文だけに
    効くよう必ず確かめる。各ターン1度なので、重ねずに1だけ下げる。"""
    c = BY_KEY[k]
    cost = c.twin[0] if twin else c.cost
    if not (c.kind == "S" or c.kind == "T" or c.kind == "X" or twin) or cost <= 1 or not _armored(c):
        return 0
    p = s.P[i]
    if not any(z.k == "k52_coppi" for z in p.board):
        return 0
    if p.x.get("k52_coppi_t") == s.turn:
        return 0
    return -1


def sw_coppi(s, i, k):
    """アーマード呪文に軽減が効いた分も、そのターンの1回として数える"""
    if not _armored(BY_KEY[k]) or not s.has(i, "k52_coppi"):
        return
    p = s.P[i]
    if p.x.get("k52_coppi_t") == s.turn:
        return
    p.x["k52_coppi_t"] = s.turn


add("k52_coppi", "アシスター・コッピ", 2, "F", power=3000,
    races=("armoredfirebird", "armored", "firebird"), pri=3, roles="acc",
    powerx=px_coppi, costaura=ca_coppi, spcostaura=sa_coppi,
    enterwatch=ew_coppi, spellwatch=sw_coppi,
    text="パワーアタッカー+2000（攻撃中、このクリーチャーのパワーは+2000）。"
         "各ターンに1度、自分のアーマード・カードを使うコストを1少なくしてもよい"
         "（ただしコストは0以下にはならない）",
    status="full", source=SRC["k52_coppi"])


# ================================================================ 3. ボルシャック・ヴォルジャアク
def ew_vorjaak(s, i, u):
    """各ターンに1度、クリーチャーが出た時（どちらのでも）、自分の山札の上から1枚をシールド化してもよい"""
    if u.c.kind != "C":
        return
    for j in (0, 1):
        if not s.has(j, "k52_vorjaak"):
            continue
        p = s.P[j]
        if p.x.get("k52_vorjaak_t") == s.turn:
            continue
        p.x["k52_vorjaak_t"] = s.turn
        if s.add_shield(j):
            s.ev("　ボルシャック・ヴォルジャアク：山札の上から1枚をシールド化")


def d_vorjaak(s, i, u):
    """破壊された時、名前に《ボルシャック》とあるコスト7以下のクリーチャーを1体、自分の手札から出してもよい"""
    k = _pick_from_hand(s, i, lambda c: c.cost <= 7 and _bolshack(c))
    if k is None:
        return
    s.P[i].hand.remove(k)
    s.ev(f"　ボルシャック・ヴォルジャアク：手札から {BY_KEY[k].name} を出す")
    s.enter(i, k, "hand", False)


def ts_vorjaak(s, i, u):
    """終極宣言（1ゲームに1度）：自分のターンのはじめに、自分のシールドをすべてブレイクしてもよい。
    そうしたら、次の自分のターンのはじめまで、自分はゲームに負けない。

    「してもよい」の決め方：相手のバトルゾーンのクリーチャーのブレイク数の合計が自分のシールドの数以上
    （＝次の相手のターンに負けうる）時だけ使う。"""
    p = s.P[i]
    if p.x.get("k52_ult_used"):
        return
    thr = sum(s.brk(1 - i, z) for z in s.P[1 - i].board if z.c.kind == "C")
    if thr <= 0 or thr < len(p.sh):
        return
    p.x["k52_ult_used"] = True
    p.x["k52_ult_until"] = s.turn + 2
    s.ev("　終極宣言：自分のシールドをすべてブレイクし、次の自分のターンのはじめまで負けない")
    _self_break(s, i, len(p.sh))


def lose_vorjaak(s, i, how):
    """終極宣言を使ったあとは、次の自分のターンのはじめまで負けない"""
    return s.P[i].x.get("k52_ult_until", -1) > s.turn


def _pr_armored5(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and _armored(BY_KEY[kk]) and BY_KEY[kk].cost >= 5)
    return None if n >= 3 else ARMORED_CHANGE


add("k52_vorjaak", "ボルシャック・ヴォルジャアク", 7, "LF", power=11000, brk=2, sa=True,
    races=("armoreddragon", "armored", "dragon"), pri=11, roles="atk fin shd",
    changex=lambda s, i, u: _armored(u.c) and u.c.cost >= 5, playrule=_pr_armored5,
    enterwatch=ew_vorjaak, destroyed=d_vorjaak, tstart=ts_vorjaak, loserep=lose_vorjaak,
    text="革命チェンジ：コスト5以上のアーマード（それが攻撃する時、手札のこのカードと入れ替えてもよい）。"
         "スピードアタッカー、W・ブレイカー。"
         "各ターンに1度、クリーチャーが出た時、自分の山札の上から1枚をシールド化してもよい。"
         "このクリーチャーが破壊された時、名前に《ボルシャック》とあるコスト7以下のクリーチャーを1体、"
         "自分の手札から出してもよい。"
         "終極宣言（1ゲームに1度）：自分のターンのはじめに、自分のシールドをすべてブレイクしてもよい。"
         "そうしたら、次の自分のターンのはじめまで、自分はゲームに負けない"
         "（相手の攻め手が自分のシールドを割りきれる時だけ使う）",
    source=SRC["k52_vorjaak"])


# ================================================================ 4. 輝く革命 ボルシャック・フレア
def bf_flare(s, ai, au, di, du, a_dies, d_dies):
    """各ターン、はじめて自分のクリーチャーがバトルする時、そのバトルに勝つ"""
    for j in (0, 1):
        if not s.has(j, "k52_flare"):
            continue
        p = s.P[j]
        if p.x.get("k52_flare_t") == s.turn:
            continue
        if ai == j:
            p.x["k52_flare_t"] = s.turn
            s.ev("　ボルシャック・フレア：このバトルに勝つ")
            return False, True
        if di == j:
            p.x["k52_flare_t"] = s.turn
            s.ev("　ボルシャック・フレア：このバトルに勝つ")
            return True, False
    return a_dies, d_dies


def ew_flare(s, i, u):
    """各ターン、はじめて出る相手のクリーチャーは、タップして出る"""
    if u.c.kind != "C":
        return
    if not s.has(1 - i, "k52_flare"):
        return
    if s.P[i].ent != 1:
        return
    s.tap_cre(i, u)
    s.ev(f"　ボルシャック・フレア：{u.c.name} はタップして出る")


def t_flare(s, i, u):
    """自分のターンの終わりに、このクリーチャーをアンタップする"""
    u.tap = False


add("k52_flare", "輝く革命 ボルシャック・フレア", 7, "LF", power=10500, brk=2, blocker=True, sa=True,
    races=("armoreddragon", "armored", "dragon"), pri=11, roles="atk blk fin dis",
    changex=lambda s, i, u: _armored(u.c) and u.c.cost >= 5, playrule=_pr_armored5,
    battlefx=bf_flare, enterwatch=ew_flare, tend=t_flare,
    text="革命チェンジ：コスト5以上のアーマード（それが攻撃する時、手札のこのカードと入れ替えてもよい）。"
         "ブロッカー、スピードアタッカー、W・ブレイカー。"
         "各ターン、はじめて自分のクリーチャーがバトルする時、そのバトルに勝つ。"
         "各ターン、はじめて出る相手のクリーチャーは、タップして出る。"
         "自分のターンの終わりに、このクリーチャーをアンタップする",
    source=SRC["k52_flare"])


# ================================================================ 5. 飛ぶ革命 ヴァル・ボルシャック
def e_valbol(s, i, u):
    """出た時、他のクリーチャーを2体まで選び、それぞれタップまたはアンタップする

    どれを選ぶかは全デッキ共通の決まりで機械的に：
    「相手のアンタップしているクリーチャーをタップする」か「自分のタップしているクリーチャーを
    アンタップする」のうち、重要度の高いほうを2回。"""
    for _ in range(2):
        t = s.target(i, lambda z: not z.tap)
        mine = [z for z in s.P[i].board if z.c.kind == "C" and z.tap and z is not u]
        best = max(mine, key=s.val) if mine else None
        if t is not None and (best is None or s.val(t) >= s.val(best)):
            s.tap_cre(1 - i, t)
            s.ev(f"　ヴァル・ボルシャック：{t.c.name} をタップ")
        elif best is not None:
            best.tap = False
            s.ev(f"　ヴァル・ボルシャック：{best.c.name} をアンタップ")
        else:
            return


def _pr_armored(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and _armored(BY_KEY[kk]))
    return None if n >= 3 else "革命チェンジの元になるアーマード・クリーチャーが3体いない"


add("k52_valbol", "飛ぶ革命 ヴァル・ボルシャック", 5, "LF", power=5500, sa=True,
    races=("armoreddragon", "armored", "dragon"), pri=7, roles="atk dis",
    changex=lambda s, i, u: _armored(u.c), playrule=_pr_armored, enter=e_valbol,
    text="革命チェンジ：アーマード（自分のアーマードが攻撃する時、手札のこのカードと入れ替えてもよい）。"
         "スピードアタッカー。"
         "このクリーチャーが出た時、他のクリーチャーを2体まで選び、それぞれタップまたはアンタップする"
         "（相手のアンタップしているクリーチャーをタップするか、自分のタップしているクリーチャーを"
         "アンタップするかを、重要度で機械的に決める）",
    source=SRC["k52_valbol"])


# ================================================================ 6. 頂上印鑑 パラキン8th／「魔物が居るな……」
def e_parakin(s, i, u):
    """召喚コストを1少なくして召喚していたら、このターンの終わりに自身を破壊する"""
    if _disc_take(s, i, "k52_parakin_d"):
        u.x["k52_parakin_die"] = 1
        s.ev("　パラキン8th：コストを1少なくしたので、このターンの終わりに破壊される")


def t_parakin(s, i, u):
    if u.x.get("k52_parakin_die"):
        s.ev("　パラキン8th：ターンの終わりに破壊される")
        s.leave(i, u, "grave", destroy=True)


def a_parakin(s, i, u):
    """攻撃する時、自分の手札が1枚以下なら、このクリーチャーをアンタップし、カードを2枚引く"""
    if len(s.P[i].hand) <= 1:
        u.re = True                      # 攻撃の終わりにアンタップする
        s.ev("　パラキン8th：手札が1枚以下なのでアンタップして2枚引く")
        s.draw(i, 2)


def sp_parakin(s, i):
    """「魔物が居るな……」：相手は自身のアンタップしているクリーチャーを2体選んでタップする。
    カードを1枚引き、自分の手札を1枚マナゾーンに置く"""
    o = s.P[1 - i]
    for _ in range(2):
        cands = [z for z in o.board if z.c.kind == "C" and not z.tap]
        if not cands:
            break
        z = min(cands, key=s.val)        # 相手が選ぶので、相手にとっていちばん安いもの
        s.tap_cre(1 - i, z)
        s.ev(f"　魔物が居るな……：相手は {z.c.name} をタップ")
    s.draw(i, 1)
    p = s.P[i]
    if p.hand:
        k = min(p.hand, key=E.PRI.get)
        p.hand.remove(k)
        s.add_mana(i, k, src="hand")
        s.ev(f"　魔物が居るな……：手札の {BY_KEY[k].name} をマナゾーンへ")


add("k52_parakin", "頂上印鑑 パラキン8th／「魔物が居るな……」", 5, "F", power=5000, sa=True,
    races=("jurassiccommanddragon", "command", "dragon", "armordon", "armored"),
    twin=(4, "LN", True), pri=6, roles="atk draw acc trg",
    costx=_cheap_disc("k52_parakin", 5), payx=_disc_pay("k52_parakin_d", 5),
    enter=e_parakin, tend=t_parakin, attack=a_parakin, spell=sp_parakin,
    text="クリーチャー側（火・コスト5・ジュラシック・コマンド・ドラゴン／アーマードン・5000）："
         "このクリーチャーの召喚コストを1少なくしてもよい。そうしたら、このターンの終わりに、これを破壊する"
         "（マナが足りない時だけ少なくする）。スピードアタッカー。"
         "このクリーチャーが攻撃する時、自分の手札が1枚以下なら、このクリーチャーをアンタップし、カードを2枚引く。"
         "呪文側「魔物が居るな……」（光／自然・コスト4）：S・トリガー。"
         "相手は、自身のアンタップしているクリーチャーを2体選び、タップする。"
         "カードを1枚引き、自分の手札を1枚マナゾーンに置く",
    source=SRC["k52_parakin"])


# ================================================================ 7. ボルシャック・サイン
def sp_bolsign(s, i):
    """コスト7以下の進化ではないアーマード・クリーチャーを1体、自分の手札から出す。
    そのクリーチャーは「スピードアタッカー」を得る。その後、自分のエレメントを1つ破壊する"""
    k = _pick_from_hand(s, i, lambda c: c.cost <= 7 and _armored(c))
    got = None
    if k is not None:
        s.P[i].hand.remove(k)
        s.ev(f"　ボルシャック・サイン：手札から {BY_KEY[k].name} を出す（スピードアタッカー）")
        got = s.enter(i, k, "hand", False, sa=True)
    z = _worst_element(s, i)
    if z is None:
        return
    if got is not None and z is got:
        s.ev("　ボルシャック・サイン：ほかにエレメントがないので、出したクリーチャーを破壊する")
    s.leave(i, z, "grave", destroy=True)


add("k52_bolsign", "ボルシャック・サイン", 5, "F", kind="S", races=("armoredarts", "armored"),
    pri=7, roles="acc atk",
    spell=sp_bolsign,
    text="コスト7以下の進化ではないアーマード・クリーチャーを1体、自分の手札から出す。"
         "そのクリーチャーはこのターン「スピードアタッカー」を得る。"
         "その後、自分のエレメントを1つ破壊する（失うのがいちばん安いものを選ぶ）",
    note="S・トリガーは持たない。「自分のエレメントを1つ破壊する」は強制なので、"
         "ほかにエレメントが無ければ、出したクリーチャーがそのまま破壊される",
    source=SRC["k52_bolsign"])


# ================================================================ 8. ボルシャック・スーパーヒーロー／超英雄タイム
def e_superhero(s, i, u):
    """出た時、パワー3000以下のサイキックではないクリーチャーをすべて破壊する"""
    for j in (0, 1):
        for z in list(s.P[j].board):
            if z.c.kind != "C" or z not in s.P[j].board:
                continue
            if s.power(j, z) <= 3000:
                s.leave(j, z, "grave", by_opp=(j != i), destroy=True)


def sp_superhero(s, i):
    """「超英雄タイム」：バトルゾーンにある相手のコスト3以下のカードを1枚選び、破壊する"""
    t = s.target(i, lambda z: z.c.cost <= 3, kinds="CTX")
    if t is None:
        return
    destroy(s, i, t)


add("k52_superhero", "ボルシャック・スーパーヒーロー／超英雄タイム", 6, "F", power=6000, brk=2,
    races=("armoreddragon", "armored", "dragon", "hunter"), twin=(2, "F", False), pri=9, roles="rem atk",
    enter=e_superhero, spell=sp_superhero,
    text="クリーチャー側（火・コスト6・アーマード・ドラゴン／ハンター・6000）：W・ブレイカー。"
         "出た時、パワー3000以下のサイキックではないクリーチャーをすべて破壊する。"
         "その後、パワー5000以下のサイキック・クリーチャーをすべて破壊する。"
         "呪文側「超英雄タイム」（火・コスト2）："
         "バトルゾーンにある相手のコスト3以下のカードを1枚選び、破壊する",
    note="「パワー5000以下のサイキック・クリーチャーをすべて破壊する」は、"
         "超次元ゾーン（サイキック・クリーチャー）がこのシミュレーターに無いので何も起きない",
    status="partial", source=SRC["k52_superhero"])


# ================================================================ 9. ボルザード・ゴールド・ドラゴン
def e_bolzard(s, i, u):
    """召喚コストを1少なくして召喚していたら、出た時、自分のシールドを1つブレイクする"""
    if _disc_take(s, i, "k52_bolzard_d"):
        s.ev("　ボルザード・ゴールド・ドラゴン：コストを1少なくしたので自分のシールドを1つブレイク")
        _self_break(s, i, 1)


add("k52_bolzard", "ボルザード・ゴールド・ドラゴン", 5, "F", power=5000, sa=True,
    races=("armoreddragon", "armored", "dragon"), pri=6, roles="atk",
    costx=_cheap_disc("k52_bolzard", 5), payx=_disc_pay("k52_bolzard_d", 5), enter=e_bolzard,
    text="このクリーチャーの召喚コストを1少なくしてもよい。そうしたら、このクリーチャーが出た時、"
         "このクリーチャーは自分のシールドを1つブレイクする（マナが足りない時だけ少なくする）。"
         "スピードアタッカー",
    source=SRC["k52_bolzard"])


# ================================================================ 10. 煌龍 サッヴァーク
def e_savvark(s, i, u):
    """出た時、バトルゾーンにある相手のカードを1枚選び、表向きで持ち主のシールドゾーンに置く"""
    t = s.target(i, kinds="CTX")
    if t is None:
        return
    o = s.P[1 - i]
    nm = t.c.name
    if not s.leave(1 - i, t, "shield", by_opp=True):
        return
    if o.sh:
        s.flip_shield(1 - i, len(o.sh) - 1, True)
    s.ev(f"　煌龍 サッヴァーク：{nm} を表向きで相手のシールドゾーンへ")


def bp_savvark(s, ai, di, n):
    """ドラゴン・W・ブレイカー：各ブレイクの前に、自分の山札の上から1枚をシールド化する"""
    u = s.atk
    if u is None or n <= 0:
        return n
    if not any(z.k == "k52_savvark" for z in s.parts(u)):
        return n
    if not s.has(ai, "k52_savvark"):
        return n
    for _ in range(n):
        if s.add_shield(ai):
            s.ev("　ドラゴン・W・ブレイカー：ブレイクの前に山札の上から1枚をシールド化")
            continue
        j = next((x for x, (_, up) in enumerate(s.P[ai].sh) if not up), None)
        if j is None:
            break
        s.flip_shield(ai, j, True)           # 山札から置けない時は、もう一方の選択肢（表向き）に寄せる
        s.ev("　ドラゴン・W・ブレイカー：ブレイクの前に自分のシールド1つを表向きにした")
    return n


def _faceup_shield(s, i):
    """墓地に置く表向きのシールドを選ぶ。(持ち主, 番号) か None。
    相手の表向きのカードを剥がせるならそちらを優先、無ければ自分のいちばん安いもの"""
    o = 1 - i
    best = None
    for j, (k, up) in enumerate(s.P[o].sh):
        if up and (best is None or E.PRI[k] > E.PRI[s.P[o].sh[best][0]]):
            best = j
    if best is not None:
        return o, best
    best = None
    for j, (k, up) in enumerate(s.P[i].sh):
        if up and (best is None or E.PRI[k] < E.PRI[s.P[i].sh[best][0]]):
            best = j
    if best is not None:
        return i, best
    return None


def lr_savvark(s, i, u, dest, destroy_):
    """自分のクリーチャーが離れる時、かわりにいずれかのシールドゾーンにある表向きのカードを1枚選び、
    持ち主の墓地に置いてもよい"""
    if u.c.kind != "C" or not s.has(i, "k52_savvark"):
        return False
    r = _faceup_shield(s, i)
    if r is None:
        return False
    j, idx = r
    k = s.P[j].sh[idx][0]
    if j == i and s.val(u) < E.PRI[k]:
        return False                      # 自分の表向きのシールドのほうが大事なら守らない
    s.take_shield(j, idx, "grave")
    s.ev(f"　煌龍 サッヴァーク：表向きのシールド {BY_KEY[k].name} を墓地に置いて {u.c.name} を守る")
    return True


add("k52_savvark", "煌龍 サッヴァーク", 7, "L", power=11000, brk=2,
    races=("masterdragon", "dragon", "metallica"), pri=11, roles="rem fin shd blk",
    enter=e_savvark, breakpre=bp_savvark, leaverep=lr_savvark,
    text="ドラゴン・W・ブレイカー（このクリーチャーはシールドを2つブレイクする。各ブレイクの前に、"
         "自分の山札の上から1枚目をシールド化するか、表向きにして自分のシールド1つの上に置く。"
         "ここではシールド化するほうを選ぶ）。"
         "このクリーチャーが出た時、バトルゾーンにある相手のカードを1枚選び、"
         "表向きで持ち主のシールド1つの上に置く。"
         "自分のクリーチャーが離れる時、かわりにいずれかのシールドゾーンにある表向きのカードを1枚選び、"
         "持ち主の墓地に置いてもよい（相手の表向きのカードを優先して剥がす）",
    note="2つの能力の「表向きにして（自分の）シールド1つの上に置く」（シールドを重ねる）が"
         "エンジンに無いので近似した。"
         "(1)ドラゴン・W・ブレイカーは、もう一方の選択肢「山札の上から1枚をシールド化する」を選ぶ"
         "（山札が足りず置けない時だけ、自分のシールド1つを表向きにして代わりにする）。"
         "(2)出た時の能力は、重ねるかわりに「表向きの新しいシールドとして置く」ことにしたので、"
         "本来は増えない相手のシールドが1つ増える",
    status="partial", source=SRC["k52_savvark"])


# ================================================================ 11. サーヴァ・K・ゼオス
def e_zeos(s, i, u):
    """出た時、相手のエレメントを1つ選び、シールド化してもよい"""
    t = s.target(i, kinds="CTX")
    if t is None:
        return
    nm = t.c.name
    if s.leave(1 - i, t, "shield", by_opp=True):
        s.ev(f"　サーヴァ・K・ゼオス：{nm} をシールド化")


add("k52_zeos", "サーヴァ・K・ゼオス", 8, "L", power=5000, trig=True, blocker=True,
    races=("masterdragon", "dragon", "metallica"), pri=9, roles="trg blk rem",
    enter=e_zeos,
    text="S・トリガー。ブロッカー。"
         "このクリーチャーが出た時、相手のエレメントを1つ選び、シールド化してもよい",
    source=SRC["k52_zeos"])


# ================================================================ 12. 蒼神龍トライクラブ・トライショット
def e_triclub(s, i, u):
    """出た時、相手のクリーチャーを2体まで選び、持ち主の手札に戻す。
    相手のターンに出た時、このターンに2つ以上自分のシールドがブレイクされていなければ、自身を破壊する"""
    for _ in range(2):
        t = s.target(i)
        if t is None:
            break
        move(s, i, t, "hand")
    if s.tp != i and s.P[i].brk_t < 2 and u in s.P[i].board:
        s.ev("　トライクラブ・トライショット：自分のシールドが2つブレイクされていないので破壊される")
        s.leave(i, u, "grave", destroy=True)


add("k52_triclub", "蒼神龍トライクラブ・トライショット", 6, "W", power=7000, brk=2, trig=True, blocker=True,
    races=("giantposeidiadragon", "giant", "poseidia", "dragon"), pri=8, roles="trg blk rem",
    enter=e_triclub,
    text="S・トリガー。ブロッカー。W・ブレイカー。"
         "このクリーチャーが出た時、相手のクリーチャーを2体まで選び、持ち主の手札に戻す。"
         "相手のターンにこのクリーチャーが出た時、このターンに2つ以上自分のシールドが"
         "ブレイクされていなければ、このクリーチャーを破壊する",
    source=SRC["k52_triclub"])


# ================================================================ 13. 熊田すず
def e_suzu(s, i, u):
    t = s.target(i)
    if t is None:
        return
    destroy(s, i, t)


def lw_suzu(s, j, u, dest, destroy_):
    """相手のクリーチャーが破壊された時、相手は自身の手札を1枚選んで捨てる"""
    if not destroy_ or u.c.kind != "C":
        return
    i = 1 - j
    n = sum(1 for z in s.P[i].board for x in s.parts(z) if x.k == "k52_suzu")
    for _ in range(n):
        if s.over:
            return
        discard_choice(s, j)


add("k52_suzu", "熊田すず", 7, "D", power=4000, trig=True,
    races=("demoncommanddragon", "demoncommand", "command", "dragon"), pri=8, roles="trg rem dis",
    enter=e_suzu, leavewatch=lw_suzu,
    text="S・トリガー。"
         "このクリーチャーが出た時、相手のクリーチャーを1体選び、破壊する。"
         "相手のクリーチャーが破壊された時、相手は自身の手札を1枚選んで捨てる",
    source=SRC["k52_suzu"])


# ================================================================ 14. 龍世界 ドラゴ大王
def e_dragodaio(s, i, u):
    """出た時、自分と相手のクリーチャーを1体ずつ選び、バトルする"""
    mine = [z for z in s.P[i].board if z.c.kind == "C"]
    if not mine or not opp_all(s, i):
        return
    best = max(mine, key=lambda z: s.power(i, z, True))
    ap = s.power(i, best, True)
    t, bv = None, -1
    for z in opp_all(s, i):
        if s.power(1 - i, z) <= ap and s.val(z) > bv:
            t, bv = z, s.val(z)
    if t is None:                            # 勝てる相手がいないなら、失うのがいちばん安い自分のクリーチャーで
        best = min(mine, key=s.val)
        cs = opp_all(s, i)
        t = min(cs, key=s.val)
    s.ev(f"　龍世界 ドラゴ大王：{best.c.name} と {t.c.name} をバトルさせる")
    s.battle(i, best, 1 - i, t)


def fx_dragodaio(s, owner, u, i, k, src, summon, res):
    """ドラゴンではないクリーチャーが出る時、かわりにそれを持ち主の墓地に置く"""
    c = BY_KEY[k]
    if c.kind == "C" and not _dragon(c) and res == "ok":
        return "grave"
    return res


add("k52_dragodaio", "龍世界 ドラゴ大王", 10, "F", power=13000, brk=3,
    races=("redcommanddragon", "command", "dragon"), pri=13, roles="fin rem dis",
    enter=e_dragodaio, fatex=fx_dragodaio,
    text="T・ブレイカー。"
         "このクリーチャーが出た時、自分と相手のクリーチャーを1体ずつ選び、バトルする"
         "（勝てるうちでいちばん重要度の高い相手を選ぶ）。"
         "ドラゴンではないクリーチャーが出る時、かわりにそれを持ち主の墓地に置く"
         "（自分のクリーチャーにも効く）",
    source=SRC["k52_dragodaio"])


# ================================================================ 15. 真久間メガ
def cx_megumega(s, i, av):
    """召喚コストを、相手のクリーチャー1体につき1少なくする（0以下にはならない）"""
    return max(1, 13 - s.ncre(1 - i))


def e_megumega(s, i, u):
    """出た時、相手のパワー13000以下のクリーチャーをすべて破壊する"""
    for z in opp_all(s, i, lambda x: s.power(1 - i, x) <= 13000):
        if z in s.P[1 - i].board:
            destroy(s, i, z)


add("k52_megumega", "真久間メガ", 13, "F", power=13000, brk=3, sa=True,
    races=("megacommanddragon", "command", "dragon", "revolution"), pri=13, roles="fin rem atk",
    costx=cx_megumega, enter=e_megumega,
    text="このクリーチャーの召喚コストを、相手のクリーチャー1体につき1少なくする"
         "（ただしコストは0以下にはならない）。"
         "スピードアタッカー、T・ブレイカー。"
         "このクリーチャーが出た時、相手のパワー13000以下のクリーチャーをすべて破壊する",
    source=SRC["k52_megumega"])
