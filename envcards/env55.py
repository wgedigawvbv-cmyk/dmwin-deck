"""担当55：DM26-SD1「ドキドキつよいデッキ 25の王道」の再録カード15枚

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ（https://dmwiki.net/《カード名》）を
      別の質問で2回ずつ読み、数字や能力文が1回しか読み取れなかった7枚は3〜4回読んで突き合わせ、
      コスト・文明・種類・種族・パワー・ブレイク数・能力本文が一致することを確かめた。
      キーワード能力の定義（ガチンコ・ジャッジ／アビスラッシュ／パワード・ブレイカー）は、
      その用語のページも開いて確かめた。
      ツインパクトは正式名（／を含む全体）でページを開いて確かめた。とくに
      《「合体」の頂 アクア・TITAAANS》《「根性」の頂 メチャデ塊ゾウ》は**ツインパクト**で、
      呪文側まで入れて初めて正しいページに当たる（片面の名前だけでは "Spam check failed" になる）。
      《「必勝」の頂 カイザー「刃鬼」》は《「勝利」の頂 カイザー「刃鬼」》とは**別のカード**なので、
      「必勝」の方だけを読んだ。

  この札束に入っている仕組み
    ・**ガチンコ・ジャッジ**（アクア・TITAAANS／カイザー「刃鬼」）。
      互いに山札の上を表向きにし、**仕掛けた側のコストが相手以上なら仕掛けた側の勝ち**
      （同じコストでも仕掛けた側の勝ち。引き分けは無い）。表向きにしたカードは山札の一番下へ。
      エンジンに差し込み口が無いので、この担当分の中の道具（`_gj`）として書いた。
    ・**アビスラッシュ**（邪闘 シス／アビスベル＝ジャシン帝が墓地のアビス全部に与える）。
      墓地からカードのコストを払って召喚し、そのターンは**相手プレイヤーだけ**を攻撃でき、
      ターンの終わりに山札の下へ（`freeacts=`／`u.sa`／`atktargetlock=`／`u.eot`）。
    ・**エターナル・Ω**（カイザー「刃鬼」）。離れる時、行き先を手札に変える（`leavedest=`）。
    ・**敗北の置き換え**（不敗のダイハード・リュウセイ）。負ける時、かわりに自身を破壊し、
      破壊された時はそのターンの終わりまで負けない（`loserep=` と `destroyed=`）。
    ・**シールド焼却**（同じカード）。自分のドラゴンが攻撃する時、相手のシールド1つを墓地へ
      （`atkwatch=` と `s.take_shield`）。
    ・**山札に横向きに刺す特殊敗北**（Q.Q.QX./終葬 5.S.D.）。ブレイクしたシールドを相手の山札の
      4枚目に刺し、相手がそれを手札に加えた時に相手が負ける（`breakrep=` と `drawwatch=`）。
    ・**パワード・ブレイカー**（ストーム・ハイパーXX）。パワー6000ごとに1つ多くブレイク
      （キーワードの定義は env20／env25 と同じ「1 + パワー//6000」）。
    ・**ハイパーエナジー**（同じカード）。`envcards.env0` の `he_costx`／`he_payx`。
    ・**ファイナル革命**（轟く革命 レッドギラゾーン）。「そのターン1回」は `s.P[i].final_turn` で共有。
    ・**アビス・メクレイド／アビス・W・メクレイド**（邪幽 ジャガイスト／邪闘 シス）。
    ・**封印**（フォビドゥン・ハンド）。`s.seal`。

  調べ直して意外だった点
    ・《「必勝」の頂 カイザー「刃鬼」》は**無色**（文明なし）のゼニス。コスト11・パワー14000で、
      登場時にパワー17000と誤植された版があると書かれていた。
    ・《ボルバルザーク・エクス》の「出た時」は**マナをアンタップするだけ**で、
      「山札の上から1枚をマナに置く」は**付いていない**（2回読んで確かめた）。
      2012年8月11日に殿堂入り、2024年3月11日に**殿堂解除**。
    ・《超神龍バイラス・カースド》は古そうな名前だが**DMEX-17が初出**で、
      マッハファイター＋パワー17000＋攻撃誘導＋S・トリガー封じという現代的な作り。
    ・《アビスベル＝ジャシン帝》のコスト軽減は「墓地のアビス」ではなく
      **墓地のクリーチャー全部**（ムゲンクライムやフシギバースにも効く）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all, is_cmd, worst_hand
from envcards.env0 import discard_choice, he_costx, he_payx, lock_until_my_turn

W = "https://dmwiki.net/"
SRC = {
    "k55_redtron": W + "《D2V3 終断のレッドトロン／フォビドゥン・ハンド》",
    "k55_storm": W + "《ストーム・ハイパーXX》",
    "k55_qqq": W + "《Q.Q.QX.／終葬 5.S.D.》",
    "k55_shibire": W + "《シビレアシダケ／インビンシブル・パワー》",
    "k55_redgira": W + "《轟く革命 レッドギラゾーン》",
    "k55_titaaans": W + "《「合体」の頂 アクア・TITAAANS／「必殺！ジェット・カスケード・アタック!!」》",
    "k55_daihard": W + "《不敗のダイハード・リュウセイ》",
    "k55_virus": W + "《超神龍バイラス・カースド》",
    "k55_mechade": W + "《「根性」の頂 メチャデ塊ゾウ／「大親分、ここにあり！」》",
    "k55_baki": W + "《「必勝」の頂 カイザー「刃鬼」》",
    "k55_exs": W + "《ボルバルザーク・エクス》",
    "k55_kaichizu": W + "《ガイアッシュの海地図》",
    "k55_jaga": W + "《邪幽 ジャガイスト》",
    "k55_sis": W + "《邪闘 シス》",
    "k55_jashin": W + "《アビスベル＝ジャシン帝》",
}


# ================================================================ 共通の道具
def _plain_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _gj_cost(k):
    """ガチンコ・ジャッジでめくったカードのコスト（ツインパクトは持ち主が有利な側を選ぶ）"""
    c = BY_KEY[k]
    return max(c.cost, c.twin[0]) if c.twin else c.cost


def _gj(s, i):
    """ガチンコ・ジャッジ（仕掛けるのは i）。互いに山札の上を表向きにして一番下へ。

    仕掛けた側のコストが相手**以上**なら仕掛けた側の勝ち（同じコストでも仕掛けた側の勝ち）。
    山札が見られない（0枚の）側は負けとして扱い、両方0枚なら仕掛けた側の勝ち（公式の裁定どおり）。
    エンジンに差し込み口が無いので、この担当分の道具として書いた。"""
    p, o = s.P[i], s.P[1 - i]
    ca = cb = None
    if p.deck:
        ka = p.deck.pop()
        ca = _gj_cost(ka)
        p.deck.insert(0, ka)
    if o.deck:
        kb = o.deck.pop()
        cb = _gj_cost(kb)
        o.deck.insert(0, kb)
    if ca is None:
        return cb is None
    if cb is None:
        return True
    return ca >= cb


def _meclaid(s, i, n, pred, label, times=1, look=3):
    """メクレイド：山札の上から look 枚を見て、条件に合うコストn以下のカードを times 枚まで
    コストを支払わずに出す。残りは山札の下へ（アビス・W・メクレイドは look=6・times=2）"""
    p = s.P[i]
    m = min(look, len(p.deck))
    if m <= 0:
        return 0
    top = [p.deck.pop() for _ in range(m)]
    got = 0
    for _ in range(times):
        best, bv = None, -1
        for k in top:
            c = BY_KEY[k]
            if c.cost > n or not pred(c):
                continue
            if c.kind == "C" and not _plain_cre(c):
                continue
            if c.kind not in "CT":
                continue
            if E.PRI[k] > bv and (c.kind == "T" or s.fate(i, k, "deck", False) == "ok"):
                best, bv = k, E.PRI[k]
        if best is None:
            break
        top.remove(best)
        s.ev(f"　{label}：{BY_KEY[best].name}")
        if BY_KEY[best].kind == "T":
            s.place_tama(i, best)
        else:
            s.enter(i, best, "deck", False)
        got += 1
        if s.over:
            break
    for k in top:
        p.deck.insert(0, k)
    return got


def _best_shield(s, j):
    """プレイヤー j のシールドのうち、いちばん重要度の高いものの番号（無ければ None）"""
    p = s.P[j]
    if not p.sh:
        return None
    return max(range(len(p.sh)), key=lambda x: E.PRI[p.sh[x][0]])


def _count(s, i, key):
    """自分の場にあるそのカードの枚数（G・リンクした横のカードも数える）"""
    n = 0
    for u in s.P[i].board:
        if u.k == key:
            n += 1
        for z in u.link:
            if z.k == key:
                n += 1
    return n


# ================================================================ 1. D2V3 終断のレッドトロン／フォビドゥン・ハンド
def cx_redtron(s, i, av):
    """召喚する時、手札を1枚捨ててもよい。そうしたら召喚コストを2少なくする
    （足りない時だけ捨てる、という共通の決まりで機械的に決める）"""
    p = s.P[i]
    if av >= 5:
        return 5
    return 3 if len(p.hand) >= 2 else 5          # 自分自身の他に1枚でもあれば捨てられる


def px_redtron(s, i, k, n):
    """軽減を使った時の支払い（この時点でこのカードは手札から取り除かれている）"""
    p = s.P[i]
    if len(p.mana) - p.mused < 5 and p.hand:
        s.ev("　終断のレッドトロン：手札を1枚捨ててコストを2少なくした")
        discard_choice(s, i)


def e_redtron(s, i, u):
    """出た時、相手のクリーチャー1体を選んでもよい。このクリーチャーとそれをバトルさせる"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　終断のレッドトロン：{t.c.name} とバトル")
    s.battle(i, u, 1 - i, t)


def _has_field(s, i):
    """自分のフィールド（D2フィールド）があるか。

    D2フィールドはこのシミュレーターに無いカード種別なので、この判定は常に False になる。
    それでも書いてあるとおりの形で残しておく（status は partial、理由は note に書いた）。"""
    return any(z.c.kind == "F" for z in s.P[i].board)


def sp_redtron(s, i):
    """フォビドゥン・ハンド：相手のパワー9999以下のクリーチャー1体を破壊する。
    自分のフィールドがあれば、相手のクリーチャー1体に封印を1つ付ける"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 9999)
    if t is not None:
        s.ev(f"　フォビドゥン・ハンド：{t.c.name} を破壊")
        destroy(s, i, t)
    if not _has_field(s, i):
        return
    t = s.target(i)
    if t is not None:
        s.ev(f"　フォビドゥン・ハンド：{t.c.name} に封印1つ")
        s.seal(1 - i, t, 1)


add("k55_redtron", "D2V3 終断のレッドトロン／フォビドゥン・ハンド", 5, "F", power=5000,
    races=("soniccommand", "command", "masterinitialsx"), twin=(9, "F", True), pri=6,
    roles="rem trg",
    enter=e_redtron, spell=sp_redtron, costx=cx_redtron, payx=px_redtron,
    text="クリーチャー側：このクリーチャーを召喚する時、自分の手札を1枚捨ててもよい。"
         "そうしたら、このクリーチャーの召喚コストを2少なくする。"
         "このクリーチャーが出た時、相手のクリーチャーを1体選んでもよい。"
         "そうしたら、このクリーチャーとそのクリーチャーをバトルさせる。"
         "呪文側「フォビドゥン・ハンド」（コスト9・火・S・トリガー）："
         "相手のパワー9999以下のクリーチャーを1体選び、破壊する。"
         "その後、自分のフィールドがあれば、相手のクリーチャーを1体選び、相手はそれに封印を1つ付ける",
    note="呪文側の2つめ「自分のフィールドがあれば」は、D2フィールド（フィールドというカード種別）が"
         "このシミュレーターに無いため、判定が常に成り立たず、封印を付ける部分は実際には働かない"
         "（封印そのものは s.seal で書いてある）。"
         "手札を1枚捨てる軽減は、マナが5に足りない時だけ使い、捨てるのは手札のうち重要度のいちばん低い札"
         "（全デッキ共通の決まり）",
    status="partial", source=SRC["k55_redtron"])


# ================================================================ 2. ストーム・ハイパーXX
def _diff_costs(s, i):
    """コストが互いに違う自分のクリーチャーの数（＝自分のクリーチャーのコストの種類の数）"""
    return len({z.c.cost for z in s.P[i].board if z.c.kind == "C"})


def px_storm(s, i, u, atk):
    """コストが異なる自分のクリーチャー1体につき、このクリーチャーのパワーを+3000する"""
    return 3000 * _diff_costs(s, i)


def e_storm(s, i, u):
    """出た時、これよりパワーが小さい相手のクリーチャーをすべて破壊する"""
    w = s.power(i, u)
    s.ev(f"　ストーム・ハイパーXX：パワー{w}より小さい相手のクリーチャーをすべて破壊")
    for z in opp_all(s, i):
        if z in s.P[1 - i].board and s.power(1 - i, z) < w:
            destroy(s, i, z)


add("k55_storm", "ストーム・ハイパーXX", 11, "F", power=0, trig=True,
    races=("armoreddragon", "flamecommand", "command", "dragon"), pri=11, roles="rem trg fin atk",
    enter=e_storm, powerx=px_storm, costx=he_costx("k55_storm"), payx=he_payx("k55_storm"),
    brkx=lambda s, i, u: 1 + s.power(i, u, True) // 6000,
    text="S・トリガー。ハイパーエナジー（このクリーチャーを召喚する時、コストが異なる自分のクリーチャーを"
         "好きな数タップしてもよい。そのクリーチャー1体につき、召喚コストを2少なくする。"
         "ただしコストは0より少なくならない）。"
         "パワード・ブレイカー（パワー6000ごとにシールドをもう1つブレイクする）。"
         "コストが異なる自分のクリーチャー1体につき、このクリーチャーのパワーを+3000する。"
         "このクリーチャーが出た時、これよりパワーが小さい相手のクリーチャーをすべて破壊する",
    note="「コストが異なる自分のクリーチャー1体につき」は、自分のクリーチャーのコストの種類の数で数える"
         "（このクリーチャー自身も含む）。パワード・ブレイカーの刻みは、キーワードの定義どおり6000ごと",
    source=SRC["k55_storm"])


# ================================================================ 3. Q.Q.QX.／終葬 5.S.D.
def _stab(s, j, k):
    """プレイヤー j の山札の上から4枚目の位置に、カード k を横向きに刺す
    （山札が2枚以下なら一番下。横向きのカードは p.x に覚えておく）"""
    p = s.P[j]
    if k in p.deck:
        p.deck.remove(k)
    pos = max(0, len(p.deck) - 3)
    p.deck.insert(pos, k)
    p.x["k55_side"] = p.x.get("k55_side", ()) + (k,)
    s.ev(f"　5.S.D.：{BY_KEY[k].name} を相手の山札の4枚目に横向きに刺した")


def br_qqq(s, ai, di, broken):
    """5.S.D.：このクリーチャーがシールドをブレイクする時、相手はそのシールドのカードを
    手札に加えるかわりに、自身の山札の上から4枚目の位置に横向きに刺す"""
    if s.atk is None or s.atk.k != "k55_qqq":
        return False
    for k, up in broken:
        _stab(s, di, k)
    return True


def dw_qqq(s, i, k):
    """相手は、自身の山札の横向きのカードを手札に加えた時、ゲームに負ける"""
    side = s.P[i].x.get("k55_side")
    if not side or k not in side:
        return
    rest = list(side)
    rest.remove(k)
    s.P[i].x["k55_side"] = tuple(rest)
    s.ev("　5.S.D.：横向きのカードを手札に加えたのでゲームに負ける")
    s.win(1 - i, "5.S.D.")


def l_qqq(s, i, u, dest):
    """このクリーチャーが離れた時、相手は自身の山札をシャッフルする"""
    o = s.P[1 - i]
    if o.deck:
        s.rng.shuffle(o.deck)
        s.ev("　5.S.D.：相手は山札をシャッフルする")


def sp_qqq(s, i):
    """終葬 5.S.D.：相手のクリーチャー1体を山札の4枚目に横向きに刺す。その後、このカードを出す"""
    t = s.target(i)
    if t is not None:
        k = t.k
        if s.leave(1 - i, t, "deck", by_opp=True):
            _stab(s, 1 - i, k)
    if s.fate(i, "k55_qqq", "hand", False) == "ok":
        s.ev("　終葬 5.S.D.：このカードをバトルゾーンに出す")
        s.enter(i, "k55_qqq", "hand", False)
    else:
        s.grave_put(i, "k55_qqq")


add("k55_qqq", "Q.Q.QX.／終葬 5.S.D.", 4, "N", power=4000,
    races=("grandsect",), twin=(8, "N", False), nograve=True, pri=7, roles="fin rem",
    spell=sp_qqq, breakrep=br_qqq, drawwatch=dw_qqq, left=l_qqq,
    text="クリーチャー側：5.S.D.（このクリーチャーがシールドをブレイクする時、相手はそのシールドの"
         "カードを手札に加えるかわりに、自身の山札の上から4枚目の位置に横向きに刺す）。"
         "相手は、自身の山札の横向きのカードを手札に加えた時、ゲームに負ける。"
         "相手は、自身の山札を見たり、順番を入れ替えたりできない。"
         "このクリーチャーが離れた時、相手は自身の山札をシャッフルする。"
         "呪文側「終葬 5.S.D.」（コスト8・自然）：相手のクリーチャーを1体選ぶ。"
         "相手はそれを、自身の山札の上から4枚目の位置に横向きに刺す。その後、このカードをバトルゾーンに出す",
    note="「横向きのカード」を1枚ずつ見分ける仕組みがエンジンに無いので、刺したカードのキーを覚えておき、"
         "同じキーのカードを引いた時に負ける形にした（同じカードが山札に他にもある場合、"
         "そちらを引いても負ける）。また「相手は自身の山札を見たり順番を入れ替えたりできない」は、"
         "山札を見る・並べ替えるのを止める差し込み口が無いため実装していない（REQUEST_55.md に書いた）",
    status="partial", source=SRC["k55_qqq"])


# ================================================================ 4. シビレアシダケ／インビンシブル・パワー
def e_shibire(s, i, u):
    """出た時、自分の手札を1枚マナゾーンに置いてもよい"""
    p = s.P[i]
    if len(p.hand) < 2:
        return                                   # 手札を使い切ってしまう時は置かない
    k = worst_hand(s, i)
    if k is None:
        return
    p.hand.remove(k)
    s.add_mana(i, k, src="hand")
    s.ev(f"　シビレアシダケ：手札の {BY_KEY[k].name} をマナゾーンへ")


def sp_shibire(s, i):
    """インビンシブル・パワー：このターン、自分のクリーチャーすべてのパワーを+8000し、
    「T・ブレイカー」を与える"""
    n = 0
    for z in s.P[i].board:
        if z.c.kind != "C":
            continue
        z.pw += 8000
        z.x["k55_inv"] = s.turn
        n += 1
    s.ev(f"　インビンシブル・パワー：自分のクリーチャー{n}体に+8000とT・ブレイカー")


def bp_shibire(s, i, u):
    """インビンシブル・パワーで与えたT・ブレイカー（そのターンだけ）"""
    if u.x.get("k55_inv") != s.turn:
        return 0
    return max(0, 3 - u.c.brk)


add("k55_shibire", "シビレアシダケ／インビンシブル・パワー", 2, "N", power=1000,
    races=("balloonmushroom",), twin=(13, "N", False), pri=3, roles="acc fin",
    enter=e_shibire, spell=sp_shibire, brkplus=bp_shibire,
    text="クリーチャー側：このクリーチャーが出た時、自分の手札を1枚、マナゾーンに置いてもよい。"
         "呪文側「インビンシブル・パワー」（コスト13・自然）：このターン、自分のクリーチャーすべての"
         "パワーを+8000し、「T・ブレイカー」を与える",
    note="マナに置くのは手札のうち重要度のいちばん低い札で、手札が2枚以上ある時だけ置く"
         "（全デッキ共通の決まり）。与えるT・ブレイカーは、もとのブレイク数が3に届かない分だけ増やす形で"
         "書いた（ブレイク数を書き換える差し込み口が無く、増やす差し込み口しかないため）",
    source=SRC["k55_shibire"])


# ================================================================ 5. 轟く革命 レッドギラゾーン
def cx_redgira(s, i, u):
    """革命チェンジ：水、火または自然のコマンド"""
    return is_cmd(u.c) and bool(set(u.c.civ) & set("WFN"))


def _redgira_cmd(s, i, u):
    """自分のコマンドすべてに与える（このカードが場にある時だけ）"""
    return u.c.kind == "C" and is_cmd(u.c) and s.has(i, "k55_redgira")


def e_redgira(s, i, u):
    """ファイナル革命：「革命チェンジ」によって出た時、そのターンに他の「ファイナル革命」を
    使っていなければ、自分の他のクリーチャーをすべてアンタップする"""
    if "src" in u.x:
        return                                   # 召喚・踏み倒しで出た時は働かない（革命チェンジ限定）
    p = s.P[i]
    if p.final_turn == s.turn:
        return
    p.final_turn = s.turn
    n = 0
    for z in p.board:
        if z is u or z.c.kind != "C" or not z.tap:
            continue
        z.tap = False
        n += 1
    s.ev(f"　ファイナル革命：自分の他のクリーチャー{n}体をアンタップ")


def pr_redgira(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and is_cmd(BY_KEY[kk])
            and set(BY_KEY[kk].civ) & set("WFN"))
    return None if n >= 3 else "革命チェンジの元（水・火・自然のコマンド）が3体いない"


add("k55_redgira", "轟く革命 レッドギラゾーン", 7, "WFN", power=11000, brk=2,
    races=("soniccommanddragon", "command", "dragon", "revolution"), pri=11, roles="atk fin rem",
    enter=e_redgira, changex=cx_redgira, playrule=pr_redgira,
    saok=_redgira_cmd, machok=_redgira_cmd, unbok=_redgira_cmd,
    text="革命チェンジ：水、火または自然のコマンド"
         "（自分のそのクリーチャーが攻撃する時、そのクリーチャーと手札にあるこのクリーチャーを"
         "入れ替えてもよい）。W・ブレイカー。"
         "自分のコマンドすべてに「スピードアタッカー」と「マッハファイター」を与え、"
         "それらはブロックされない。"
         "ファイナル革命：このクリーチャーが「革命チェンジ」によって出た時、"
         "そのターンに他の「ファイナル革命」を使っていなければ、自分の他のクリーチャーをすべてアンタップする",
    source=SRC["k55_redgira"])


# ================================================================ 6. 「合体」の頂 アクア・TITAAANS
def ew_titaaans(s, i, u):
    """相手のクリーチャーが出た時、相手とガチンコ・ジャッジをする。自分が勝ったら1枚引き、
    そのターン、相手のクリーチャーはすべて攻撃できない（ガチンコ・ジャッジもドローも強制）"""
    if u.c.kind != "C":
        return
    j = 1 - i                                    # TITAAANS を持っている側
    n = _count(s, j, "k55_titaaans")
    if not n:
        return
    for _ in range(n):
        if s.over:
            return
        won = _gj(s, j)
        s.ev(f"　アクア・TITAAANS：ガチンコ・ジャッジ（{'勝ち' if won else '負け'}）")
        if not won:
            continue
        s.draw(j, 1)
        s.P[i].x["k55_tit_lock"] = s.turn
        s.ev("　アクア・TITAAANS：このターン、相手のクリーチャーはすべて攻撃できない")


def al_titaaans(s, i, u):
    """TITAAANS のガチンコ・ジャッジに負けた側は、そのターン攻撃できない"""
    return s.P[i].x.get("k55_tit_lock") == s.turn


def sp_titaaans(s, i):
    """「必殺！ジェット・カスケード・アタック!!」：このゲームに参加しているプレイヤー1人につき1枚引く
    （1対1なので2枚）"""
    s.ev("　必殺！ジェット・カスケード・アタック!!：2枚引く")
    s.draw(i, 2)


add("k55_titaaans", "「合体」の頂 アクア・TITAAANS／「必殺！ジェット・カスケード・アタック!!」", 10, "W",
    power=12000, brk=3, blocker=True, gs=True,
    races=("liquid", "gianthunter", "zenith"), twin=(3, "W", False), pri=11,
    roles="blk dis draw fin",
    spell=sp_titaaans, enterwatch=ew_titaaans, atklock=al_titaaans,
    text="クリーチャー側：G・ストライク、ブロッカー、T・ブレイカー。"
         "相手のクリーチャーが出た時、相手とガチンコ・ジャッジをする"
         "（互いに山札の上を表向きにし、自分のコストが相手以上なら自分の勝ち。その後、下に置く）。"
         "自分が勝ったら、1枚引く。そのターン、相手のクリーチャーはすべて攻撃できない。"
         "呪文側「必殺！ジェット・カスケード・アタック!!」（コスト3・水）："
         "このゲームに参加しているプレイヤー1人につき、カードを1枚引く",
    note="ガチンコ・ジャッジとドローは強制なので、相手がクリーチャーを並べると自分の山札が減る"
         "（公式でもデッキ切れに注意と書かれている）。"
         "参加プレイヤー数は、このシミュレーターが1対1しか扱わないので常に2枚",
    source=SRC["k55_titaaans"])


# ================================================================ 7. 不敗のダイハード・リュウセイ
def aw_daihard(s, i, u):
    """自分のドラゴンが攻撃する時、相手のシールドを1つ選び、持ち主の墓地に置く"""
    if u.c.kind != "C" or "dragon" not in u.c.races:
        return
    n = _count(s, i, "k55_daihard")
    if not n:
        return
    for _ in range(n):
        if s.over:
            return
        j = _best_shield(s, 1 - i)
        if j is None:
            return
        r = s.take_shield(1 - i, j, "grave")
        if r is None:
            return
        s.ev(f"　ダイハード・リュウセイ：相手のシールド（{BY_KEY[r[0]].name}）を墓地へ")


def d_daihard(s, i, u):
    """このクリーチャーが破壊された時、そのターンの終わりまで自分はゲームに負けない"""
    s.P[i].x["k55_dh_safe"] = s.turn
    s.ev("　ダイハード・リュウセイ：このターンの終わりまで自分はゲームに負けない")


def lose_daihard(s, i, how):
    """自分がゲームに負ける時、かわりにこのクリーチャーを破壊する"""
    p = s.P[i]
    if p.x.get("k55_dh_safe") == s.turn:
        return True
    z = None
    for u in p.board:
        for x in s.parts(u):
            if x.k == "k55_daihard":
                z = u
                break
        if z is not None:
            break
    if z is None:
        return False
    s.ev("　ダイハード・リュウセイ：負けるかわりに自身を破壊する")
    s.leave(i, z, "grave", destroy=True)
    return True


def tp_daihard(s, i):
    """「そのターンの終わりまで」が切れた時、山札が0枚ならそこで負ける。

    エンジンは山札切れを「山札が0枚になったその瞬間」にしか見ないので、
    いったん負けを置き換えると二度と見に来ない。そのままでは
    「そのターンの終わりまで」が永久の山札切れ無効になってしまうため、ここで見直している。"""
    p = s.P[i]
    if p.x.get("k55_dh_safe") != s.turn:
        return
    p.x["k55_dh_safe"] = -1
    if not p.deck and not s.over:
        s.ev("　ダイハード・リュウセイ：ターンが終わり、山札が0枚なので負ける")
        s.win(1 - i, "山札切れ")


add("k55_daihard", "不敗のダイハード・リュウセイ", 8, "F", power=8000, brk=2,
    races=("redcommanddragon", "command", "dragon", "hunter"), pri=10, roles="fin atk shd",
    atkwatch=aw_daihard, destroyed=d_daihard, loserep=lose_daihard, tendp=tp_daihard,
    text="W・ブレイカー。自分のドラゴンが攻撃する時、相手のシールドを1つ選び、持ち主の墓地に置く。"
         "自分がゲームに負ける時、かわりにこのクリーチャーを破壊する。"
         "このクリーチャーが破壊された時、そのターンの終わりまで、自分はゲームに負けない",
    note="墓地に置くシールドは、相手のシールドのうち重要度のいちばん高いものを選ぶ（全デッキ共通の決まり）。"
         "シールドを墓地に置くのはブレイクではないので、S・トリガーは使われない",
    source=SRC["k55_daihard"])


# ================================================================ 8. 超神龍バイラス・カースド
def _virus_tapped(s, j):
    """プレイヤー j のバイラス・カースドがタップしているか"""
    for u in s.P[j].board:
        for z in s.parts(u):
            if z.k == "k55_virus" and (z.tap or u.tap):
                return True
    return False


def _trig_card(s, i, k):
    """そのカードがS・トリガーとして使えるか（S・トリガーを与える効果も見る）"""
    c = BY_KEY[k]
    if c.trig or (c.twin and c.twin[2]):
        return True
    return bool(E.TRIGOK) and any(f(s, i, k) for f in E.TRIGOK)


def sl_virus(s, i, cost, k=None):
    """このクリーチャーがタップしていれば、相手は自身のS・トリガーを使えない（呪文の分）。

    止まるのは「S・トリガー」の使用だけで、S・トリガーを持つカードをふつうに唱えるのは
    止まらない（公式Q&A）。そこで、相手のターン中に自分でない側が唱える場面
    （＝シールドからの受け）で、**S・トリガーとして使えるカードだけ**を止める。
    呪文のキーが渡らない呼び出しでは止めない。"""
    if k is None or i == s.tp or not _virus_tapped(s, 1 - i):
        return False
    return _trig_card(s, i, k)


def fx_virus(s, owner, u, i, k, src, summon, res):
    """同じく、S・トリガーのクリーチャー（とタマシード）を止める"""
    if u.k != "k55_virus" or not u.tap or i == owner or i == s.tp or src != "hand" or not summon:
        return res
    c = BY_KEY[k]
    if c.trig or (E.TRIGOK and any(f(s, i, k) for f in E.TRIGOK)):
        return "no"
    return res


def mat_virus(s, i, u, tg):
    """相手のクリーチャーが攻撃するなら、可能ならこのクリーチャーを攻撃する。

    i＝攻める側（バイラス・カースドの持ち主は 1-i）。tg はエンジンが攻撃先の候補を
    絞り終えた並び（"P"＝プレイヤー、数＝相手の場の番号）なので、
    この中にバイラス・カースドがいる時だけ縛る＝「可能なら」がそのまま出る。"""
    o = s.P[1 - i]
    for j in tg:
        if j == "P":
            continue
        t = o.board[j]
        if any(z.k == "k55_virus" for z in s.parts(t)) and s.abi(1 - i, t):
            return j
    return None


add("k55_virus", "超神龍バイラス・カースド", 10, "N", power=17000, brk=3, mach=True,
    races=("earthdragon", "mysterytotem", "dragon", "hunter"), pri=12, roles="blk dis rem fin",
    spelllock=sl_virus, fatex=fx_virus, mustatktgt=mat_virus,
    text="マッハファイター、T・ブレイカー。"
         "このクリーチャーがタップしていれば、相手は自身のS・トリガーを使えない。"
         "相手のクリーチャーが攻撃するなら、可能ならこのクリーチャーを攻撃する",
    note="「S・トリガーを使えない」そのものを止める差し込み口がエンジンに無いので、"
         "呪文は spelllock（相手のターン中に自分でない側が唱える＝シールドからの受けの場面で、"
         "S・トリガーとして使えるカードだけを止める）、クリーチャーは fatex で止めている。"
         "そのため**タマシードのS・トリガーだけは止まらない**"
         "（エンジンのタマシードのS・トリガーはコスト1つを封じる p.ban しか見ていない。"
         "REQUEST_55.md に差し込み口の要望を書いた）",
    status="partial", source=SRC["k55_virus"])


# ================================================================ 9. 「根性」の頂 メチャデ塊ゾウ
def _mechade_go(s, j):
    """自分のマナゾーンから、コストが自分のマナゾーンのカードの枚数以下のハンター1体を
    コストを支払わずに召喚してもよい"""
    p = s.P[j]
    lim = len(p.mana)
    best, bv = None, -1
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if not _plain_cre(c) or "hunter" not in c.races or c.cost > lim:
            continue
        if E.PRI[k] > bv and s.fate(j, k, "mana", True) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return
    s.take_mana(j, best)
    s.ev(f"　メチャデ塊ゾウ：マナゾーンから {BY_KEY[best].name} を召喚")
    s.enter(j, best, "mana", True)


def bf_mechade(s, ai, au, di, du, a_dies, d_dies):
    """このクリーチャーがバトルに勝った時に働く"""
    if s.over:
        return a_dies, d_dies
    if au.k == "k55_mechade" and d_dies and not a_dies:
        _mechade_go(s, ai)
    elif du.k == "k55_mechade" and a_dies and not d_dies:
        _mechade_go(s, di)
    return a_dies, d_dies


def sp_mechade(s, i):
    """「大親分、ここにあり！」：自分の山札の上から2枚を見て、1枚をマナゾーンに置き、
    残りを山札の上か下に置く"""
    p = s.P[i]
    n = min(2, len(p.deck))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    k = max(top, key=E.PRI.get)
    top.remove(k)
    s.add_mana(i, k, src="deck")
    s.ev(f"　大親分、ここにあり！：{BY_KEY[k].name} をマナゾーンへ")
    for x in top:
        p.deck.append(x)                         # 残りは山札の上（引けるので上に戻す）


add("k55_mechade", "「根性」の頂 メチャデ塊ゾウ／「大親分、ここにあり！」", 10, "N",
    power=14000, brk=3, mach=True, gs=True,
    races=("beastfolk", "gianthunter", "zenith"), twin=(3, "N", False), pri=11,
    roles="acc atk fin",
    spell=sp_mechade, battlefx=bf_mechade,
    text="クリーチャー側：G・ストライク、マッハファイター、T・ブレイカー。"
         "このクリーチャーがバトルに勝った時、コストが自分のマナゾーンにあるカードの枚数以下の"
         "ハンター1体を、自分のマナゾーンからコストを支払わずに召喚してもよい。"
         "呪文側「大親分、ここにあり！」（コスト3・自然）：自分の山札の上から2枚を見て、"
         "1枚をマナゾーンに置き、残りを山札の上か下に置く",
    note="召喚するハンターは重要度のいちばん高いもの、マナに置くのは見た2枚のうち重要度の高い方、"
         "残りは山札の上に戻す（全デッキ共通の決まり）。"
         "進化クリーチャーは進化元の置き方を表せないので、進化でないハンターから選ぶ",
    source=SRC["k55_mechade"])


# ================================================================ 10. 「必勝」の頂 カイザー「刃鬼」
def _baki_put(s, i):
    """ハンター1体を自分の手札・マナゾーン・墓地のどこかから出す（出せたら True）。

    進化ハンターも出せる（公式Q&A「はい、重ねられます」）。進化元は全デッキ共通の決まりで
    エンジンに選ばせる（アンタップしている・重要度のいちばん低いもの）。"""
    p = s.P[i]
    best, bv, zn, bon = None, None, None, None
    for zname, zone in (("grave", p.grave), ("mana", p.mana), ("hand", p.hand)):
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if c.kind != "C" or "hunter" not in c.races:
                continue
            on = None
            if c.evo and not c.neo:
                on = s.evo_src(i, k)
                if on is None:                               # 進化元になれるクリーチャーがいない
                    continue
            v = (E.PRI[k], 0 if zname == "hand" else 1)      # 同じなら手札は残す
            if (bv is None or v > bv) and s.fate(i, k, zname, False) == "ok":
                best, bv, zn, bon = k, v, zname, on
    if best is None:
        return False
    if zn == "mana":
        s.take_mana(i, best)
    elif zn == "grave":
        p.grave.remove(best)
    else:
        p.hand.remove(best)
    s.ev(f"　カイザー「刃鬼」：{BY_KEY[best].name} を{'墓地' if zn == 'grave' else ('マナ' if zn == 'mana' else '手札')}から出す")
    s.enter(i, best, zn, False, on=bon)
    return True


def e_baki(s, i, u):
    """召喚した時、相手のシールド1つにつき1回、相手とガチンコ・ジャッジをする。
    その後、自分が勝った数だけハンターを手札・マナゾーン・墓地から1体ずつ出す"""
    if not u.x.get("summoned"):
        return
    n = len(s.P[1 - i].sh)
    wins = 0
    for _ in range(n):
        if s.over:
            return
        if _gj(s, i):
            wins += 1
    s.ev(f"　カイザー「刃鬼」：ガチンコ・ジャッジ{n}回のうち{wins}回勝った")
    for _ in range(wins):
        if s.over or not _baki_put(s, i):
            break


def ld_baki(s, i, u, dest, destroy_):
    """エターナル・Ω：このクリーチャーが離れる時、かわりに手札に戻す"""
    if u.k != "k55_baki":
        return None
    return "hand"


add("k55_baki", "「必勝」の頂 カイザー「刃鬼」", 11, "", power=14000, brk=3,
    races=("redcommanddragon", "command", "dragon", "hunter", "zenith"), pri=13, roles="fin atk acc",
    enter=e_baki, leavedest=ld_baki,
    text="無色のクリーチャー。T・ブレイカー。"
         "エターナル・Ω（このクリーチャーが離れる時、かわりに手札に戻す）。"
         "このクリーチャーを召喚した時、相手のシールド1つにつき1回、相手とガチンコ・ジャッジをする"
         "（互いに山札の上を表向きにし、自分のコストが相手以上なら自分の勝ち。その後、下に置く）。"
         "その後、自分がガチンコ・ジャッジに勝った数だけ、ハンターを1体ずつ、"
         "自分の手札・マナゾーン・墓地から出す",
    note="出すハンターは重要度のいちばん高いもので、同じなら墓地とマナを先に使う（全デッキ共通の決まり）。"
         "進化ハンターも出せる（進化元はアンタップしている・重要度のいちばん低い自分のクリーチャー）",
    source=SRC["k55_baki"])


# ================================================================ 11. ボルバルザーク・エクス
def e_exs(s, i, u):
    """出た時、自分のマナゾーンにあるカードをすべてアンタップする"""
    p = s.P[i]
    if p.mused:
        s.ev(f"　ボルバルザーク・エクス：マナを{p.mused}枚アンタップ")
        p.mused = 0


add("k55_exs", "ボルバルザーク・エクス", 7, "FN", power=6000, brk=2, sa=True,
    races=("armoreddragon", "earthdragon", "dragon", "hunter"), pri=9, roles="acc atk fin",
    enter=e_exs,
    text="スピードアタッカー、W・ブレイカー。"
         "このクリーチャーが出た時、自分のマナゾーンにあるカードをすべてアンタップする",
    note="2012年8月11日に殿堂入りしたが、2024年3月11日付で殿堂解除されており、"
         "いまはデッキに4枚入れられる",
    source=SRC["k55_exs"])


# ================================================================ 12. ガイアッシュの海地図
def e_kaichizu(s, i, u):
    """出た時、1枚引く。その後、相手のクリーチャー1体を選び、次の自分のターンのはじめまで
    攻撃もブロックもできなくする"""
    s.draw(i, 1)
    t = s.target(i)
    if t is None:
        return
    lock_until_my_turn(s, i, t)
    s.ev(f"　ガイアッシュの海地図：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


def ca_kaichizu(s, i, k, cur):
    """自分のコスト8以上のクリーチャーの召喚コストを2少なくする（0以下にはならない）"""
    if cur <= 1 or not s.has(i, "k55_kaichizu"):
        return cur
    c = BY_KEY[k]
    if c.kind == "C" and c.cost >= 8:
        return max(1, cur - 2)
    return cur


E.SHINKA.add("k55_kaichizu")        # シンカライズ：クリーチャーでなくても進化元にできる

add("k55_kaichizu", "ガイアッシュの海地図", 5, "WN", kind="T", trig=True,
    races=("bluecommanddragon", "greencommanddragon", "command", "dragon", "hunter", "rexstars"),
    pri=7, roles="draw dis trg acc",
    enter=e_kaichizu, costaura=ca_kaichizu,
    text="タマシード。S・トリガー。シンカライズ（このタマシードがクリーチャーであるかのように、"
         "この上に進化クリーチャーを置いてもよい）。"
         "このタマシードが出た時、1枚引く。その後、相手のクリーチャーを1体選ぶ。"
         "次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない。"
         "自分のコスト8以上のクリーチャーの召喚コストを2少なくする。ただしコストは0以下にならない",
    source=SRC["k55_kaichizu"])


# ================================================================ 13. 邪幽 ジャガイスト
def _is_abyss(c):
    return "abyss" in c.races


def e_jaga(s, i, u):
    """出た時、自分の手札を2枚捨ててもよい。そうしたら、アビス・メクレイド5をする"""
    p = s.P[i]
    if len(p.hand) < 2:
        return
    for _ in range(2):
        discard_choice(s, i)
    s.ev("　邪幽 ジャガイスト：手札を2枚捨ててアビス・メクレイド5")
    _meclaid(s, i, 5, _is_abyss, "アビス・メクレイド5")


def ew_jaga(s, i, u):
    """各ターン1回、自分の山札からクリーチャーが出た時、そのクリーチャーのコスト以下の
    アビス・クリーチャー1体を自分の墓地から出してもよい。そのクリーチャーはこのターン攻撃でき、
    攻撃していればこのターンの終わりに山札の下に置かれる"""
    if u.c.kind != "C" or u.x.get("src") != "deck":
        return
    p = s.P[i]
    if p.x.get("k55_jaga_t") == s.turn or not s.has(i, "k55_jaga"):
        return
    lim = u.c.cost
    best, bv = None, -1
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if not _plain_cre(c) or not _is_abyss(c) or c.cost > lim:
            continue
        if E.PRI[k] > bv and s.fate(i, k, "grave", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return
    p.x["k55_jaga_t"] = s.turn
    p.grave.remove(best)
    s.ev(f"　邪幽 ジャガイスト：墓地から {BY_KEY[best].name} を出す")
    z = s.enter(i, best, "grave", False, sa=True)
    if z is not None:
        z.x["k55_jaga_rev"] = s.turn


def aw_jaga(s, i, u):
    """ジャガイストで出したクリーチャーが攻撃したら、このターンの終わりに山札の下へ"""
    if u.x.get("k55_jaga_rev") != s.turn:
        return
    u.eot = True


add("k55_jaga", "邪幽 ジャガイスト", 5, "D", power=9000, brk=2, blocker=True,
    races=("abyssdragon", "abyss", "dragon"), pri=8, roles="blk acc rem atk",
    enter=e_jaga, enterwatch=ew_jaga, atkwatch=aw_jaga,
    text="ブロッカー、W・ブレイカー。"
         "このクリーチャーが出た時、自分の手札を2枚捨ててもよい。そうしたら、アビス・メクレイド5をする"
         "（自分の山札の上から3枚を見て、その中のコスト5以下のアビス1枚をコストを支払わずに出し、"
         "残りを山札の下に置く）。"
         "各ターン1回、自分の山札からクリーチャーが出た時、そのクリーチャーのコスト以下の"
         "アビス・クリーチャー1体を、自分の墓地から出してもよい。そのクリーチャーはこのターン、"
         "相手プレイヤーを攻撃でき、このターン攻撃していれば、ターンの終わりに山札の下に置かれる",
    note="2024年8月17日から殿堂入り（デッキに1枚まで）。アビスからの殿堂入り第1号。"
         "出した後に「攻撃したか」を見分けるため、attack の見張り（atkwatch）で山札の下に置く印を付けている",
    source=SRC["k55_jaga"])


# ================================================================ 14・15 アビスラッシュ（シス／ジャシン帝）
def ca_jashin(s, i, k, n):
    """アビスベル＝ジャシン帝：自分の墓地にあるクリーチャーの召喚コストを2少なくする
    （コストは1より少なくならない）。

    エンジンの ccost は「どのゾーンから召喚するか」を渡さないので、
    **そのカードが墓地にだけある時**に軽減する。こうすると、この担当分のアビスラッシュだけでなく、
    ほかの担当のムゲンクライムやフシギバース（どれも ccost で墓地からの召喚コストを出している）にも
    軽減がかかる。同じカードが手札やマナにもある時は、どのゾーンから召喚するのか見分けられないので
    軽減しない（note に書いた）。"""
    if n >= 99 or not s.has(i, "k55_jashin"):
        return n
    p = s.P[i]
    if k not in p.grave or k in p.hand or k in p.mana:
        return n
    return max(1, n - 2)


def fa_abyssrush(s, i, av, cv):
    """アビスラッシュ：このクリーチャー（と、ジャシン帝がいれば墓地のアビス全部）を
    自分の墓地から召喚してもよい"""
    p = s.P[i]
    sis = "k55_sis" in p.grave
    jas = s.has(i, "k55_jashin")
    if not sis and not jas:
        return []
    keys = ["k55_sis"] if sis else []
    if jas:
        for k in sorted(set(p.grave)):
            if k in keys:
                continue
            c = BY_KEY[k]
            if _plain_cre(c) and _is_abyss(c):
                keys.append(k)
    if not keys or s.manaexec(i):
        return []
    out = []
    for k in keys:
        c = BY_KEY[k]
        n = s.ccost(i, k, av)                    # 軽減はジャシン帝の costaura（ca_jashin）がかける
        if n > av or (n > 0 and not cv.issuperset(c.civ)):
            continue
        if s.fate(i, k, "grave", True) != "ok":
            continue
        out.append(("x:k55rush", k, n))
    return out


def ap_abyssrush(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.grave:
        return
    p.mused += a[2]
    p.grave.remove(k)
    s.ev(f"アビスラッシュ：{BY_KEY[k].name}（墓地から召喚・{a[2]}マナ）")
    z = s.enter(i, k, "grave", True)
    if z is not None:
        z.sa = True                              # そのターン攻撃できる
        z.x["k55_onlyp"] = s.turn                # ただし相手プレイヤーだけ
        z.eot = True                             # ターンの終わりに山札の下へ


def atl_rush(s, i, u, t):
    """アビスラッシュで出たクリーチャーは、そのターン相手のクリーチャーを攻撃できない"""
    return u.x.get("k55_onlyp") == s.turn


# ================================================================ 14. 邪闘 シス
def e_sis(s, i, u):
    """出た時、相手のクリーチャー1体を選び、そのターン、パワーを-∞する"""
    t = s.target(i)
    if t is None:
        return
    t.pw -= 999999
    s.ev(f"　邪闘 シス：{t.c.name} のパワーを-∞（パワー0以下で破壊）")
    if t in s.P[1 - i].board:
        destroy(s, i, t)


def a_sis(s, i, u):
    """攻撃する時、アビス・W・メクレイド5をしてもよい"""
    s.ev("　邪闘 シス：アビス・W・メクレイド5")
    _meclaid(s, i, 5, _is_abyss, "アビス・W・メクレイド5", times=2, look=6)


add("k55_sis", "邪闘 シス", 6, "D", power=9000, brk=2,
    races=("abysschimera", "abyss", "chimera"), pri=9, roles="rem acc atk fin",
    enter=e_sis, attack=a_sis, freeacts=fa_abyssrush, actapply={"x:k55rush": ap_abyssrush},
    atktargetlock=atl_rush,
    text="アビスラッシュ（このクリーチャーを自分の墓地から召喚してもよい。そうしたら、このターン、"
         "このクリーチャーは相手プレイヤーを攻撃でき、このターンの終わりに山札の下に置かれる）。"
         "W・ブレイカー。"
         "このクリーチャーが出た時、相手のクリーチャーを1体選ぶ。このターン、そのパワーを-∞する。"
         "このクリーチャーが攻撃する時、アビス・W・メクレイド5をしてもよい"
         "（自分の山札の上から6枚を見て、その中のコスト5以下のアビスを2枚までコストを支払わずに出し、"
         "残りを好きな順序で山札の下に置く）",
    note="パワー-∞は、パワーが0以下になったクリーチャーが破壊されるルールどおり、"
         "その場で破壊として処理している",
    source=SRC["k55_sis"])


# ================================================================ 15. アビスベル＝ジャシン帝
def lr_jashin(s, i, u, dest, destroy_):
    """このクリーチャーが離れる時、かわりに自分の手札を2枚捨ててもよい"""
    if u.k != "k55_jashin":
        return False
    p = s.P[i]
    if len(p.hand) < 2:
        return False
    for _ in range(2):
        discard_choice(s, i)
    s.ev("　アビスベル＝ジャシン帝：離れるかわりに手札を2枚捨てて残る")
    return True


add("k55_jashin", "アビスベル＝ジャシン帝", 4, "D", power=7000, brk=2, blocker=True,
    races=("abyssroyal", "abyss"), pri=8, roles="blk acc fin",
    leaverep=lr_jashin, costaura=ca_jashin,
    text="ブロッカー、W・ブレイカー。"
         "自分の墓地にあるアビス・クリーチャーはすべて「アビスラッシュ」を得る"
         "（そのクリーチャーを自分の墓地から召喚してもよい。そうしたら、このターン、"
         "そのクリーチャーは相手プレイヤーを攻撃でき、このターンの終わりに山札の下に置かれる）。"
         "このクリーチャーがバトルゾーンを離れる時、かわりに自分の手札を2枚捨ててもよい。"
         "自分の墓地にあるクリーチャーの召喚コストを2少なくする。ただしコストは1より少なくならない",
    note="墓地からの召喚コストを2少なくする部分は、全体のコスト変化（costaura）で書いたので、"
         "この担当分のアビスラッシュだけでなく、ほかの担当のムゲンクライム・フシギバースなど"
         "ccost で墓地からの召喚コストを出しているものにも効く。"
         "ただしエンジンの ccost は召喚するゾーンを渡さないため、"
         "**同じカードが墓地と手札（かマナ）の両方にある時は軽減しない**"
         "（どちらから召喚するのか見分けられないので、安全側に倒した）。"
         "離れるかわりに手札を2枚捨てるのは、手札が2枚以上あれば必ず使う（全デッキ共通の決まり）",
    status="partial", source=SRC["k55_jashin"])
