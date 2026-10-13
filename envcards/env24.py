"""担当24：DM26-RP1「逆札篇 第1弾 逆転神VS切札竜」とDM26-RP2の未実装カード15枚

出典：dmwiki.net の各カードページ（日本語のページ名をURLにそのまま入れて開ける）と、
      同じページの生の wiki ソース（`?plugin=template&refer=《カード名》`）。
      生ソースは cardtable の行（文明・コスト・種類・種族・パワー・レアリティ）と、
      ハイパーモード欄の区切り（BGCOLOR(#cde):|c|）が読めるので、
      「どの能力がハイパーモード中だけのものか」の判定に使った。

  この15枚に入っている仕組み
    ・プラスワン・サイクル（S・トリガーの定番除去＋「その後、カードを1枚引く」）3枚
      プラスワン・ハンド（闇5・1体破壊）／プラスワン・フレーム（火4・パワー合計5000以下を好きな数破壊）／
      プラスワン・トラップ（自然4・1体をマナへ）
      ※《プラスワン・ゲート》（n_plusone）と《プラスワン・スパーク》（k23_plusspark）は別の担当が実装済み
    ・「〜の時!!」サイクル（G・ストライク＋シールドを1つブレイクする）2枚
      切り札の時!!（闇4・自分のシールドを割る＝自分のS・トリガーを撃つ／Zラッシュを起こす）／
      逆転の時!!（火2・相手が選んだ相手のシールドを割る）
    ・我竜塔サイクルのG城3枚（第二層 ダルマンディ／第三層 超鯱城／第四層 ポチョムキン）。
      どれも「表向きで自分のシールドゾーンにある間ずっと働く」常在能力で、置かれた時の誘発はない。
    ・セイバー：超化獣（襲撃者ガルゼドライブ）
    ・Zラッシュ＋ハイパーモードでQ・ブレイカーになる超化獣（謎神のQ ギリメノアイル）
    ・ブロック貫通（ノーガルディ・ネギオ＆ガルダンディ・ナスオ：ブロックされた時に相手のシールドを2つブレイク）
    ・コスト3以下のエレメント1つにつき3軽くなる大型呪文（インビンシブル・タワー）
    ・禁断（燃える禁断 ドルマゲドンW）。《禁断 ～封印されしX～》と違って禁断の鼓動から裏返るのではなく、
      ふつうに召喚でき、出た時に自分自身へ封印を4つ付ける。封印はコマンドが出るたびに外れる
      （この仕組みは envcards/env0.py の封印・禁断がそのまま使える）。
    ・墓地進化（魔V王 デスシラズ）／山札の上5枚から「異なるカードタイプ」を抜く（龍V王 Q.E.D.）

  調べ直して確かめたところ
    15枚すべてについて、dmwiki のカードページと生の wiki ソースを別の質問で2回以上読み、
    コスト・文明・種類・種族・パワー・ブレイク数・能力の本文が一致することを確かめた。
    ・《我竜塔第二層 ダルマンディ》は「自分のクリーチャーすべて」か「そのクリーチャー」かが効果の強さを
      大きく変えるので、3回目を読んで「自分のクリーチャーすべてのハイパーモードを解放する」と確かめた。
    ・《切り札の時!!》はコスト4で効果が「自分のシールドを1つブレイクする」だけ。安い《逆転の時!!》（火2）が
      相手のシールドを割るのに、自分のシールドを割るほうが高いのは意外だったが、
      カードページと生ソースの cardtable がどちらもコスト4だったのでそのまま実装した。
      （自分で割ると自分のS・トリガーが撃てて、Zラッシュも起こせるので、効果としては強い側）
    ・《謎神のQ ギリメノアイル》は生ソースのハイパーモード区切りが Zラッシュ行の後にあり、
      18000とQ・ブレイカーがハイパーモード側だと確かめた（通常時はパワー9000・W・ブレイカー）。
    ・《ノーガルディ・ネギオ＆ガルダンディ・ナスオ》はコスト2・パワー3000。
      dmwiki の解説に「ブロック貫通を持つクリーチャーの最小コストを更新した」とあり、安さは正しい。

  近似はもう残っていない。「このクリーチャーがブロックされた時」は `blockwatch=`、
  墓地進化は `evosrc=` で、どちらもエンジンの差し込み口でそのまま書いてある（15枚すべて full）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move
from envcards.env0 import discard_choice

W = "https://dmwiki.net/"
SRC = {
    "k24_plushand": W + "《プラスワン・ハンド》",
    "k24_kirifuda": W + "《切り札の時!!》",
    "k24_potemkin": W + "《我竜塔第四層 ポチョムキン》",
    "k24_galzedrive": W + "《襲撃者ガルゼドライブ》",
    "k24_plusflame": W + "《プラスワン・フレーム》",
    "k24_gyakuten": W + "《逆転の時!!》",
    "k24_chosyachi": W + "《我竜塔第三層 超鯱城》",
    "k24_girimeno": W + "《謎神のQ ギリメノアイル》",
    "k24_negionasuo": W + "《ノーガルディ・ネギオ＆ガルダンディ・ナスオ》",
    "k24_invtower": W + "《インビンシブル・タワー》",
    "k24_plustrap": W + "《プラスワン・トラップ》",
    "k24_darmandi": W + "《我竜塔第二層 ダルマンディ》",
    "k24_dolmageddonw": W + "《燃える禁断 ドルマゲドンW》",
    "k24_qed": W + "《龍V王 Q.E.D.》",
    "k24_deathshirazu": W + "《魔V王 デスシラズ》",
}


# ================================================================ 共通の小道具
def _castle_up(s, i, key):
    """key のG城が、プレイヤー i の表向きのシールドとして置かれているか"""
    for k, up in s.P[i].sh:
        if up and k == key:
            return True
    return False


def _opp_cre(s, i):
    """相手のクリーチャー全部（「すべて」の効果用。選ぶのではないのでジャストダイバーも含む）"""
    return [z for z in s.P[1 - i].board if z.c.kind == "C"]


def _safe_draw(s, i, n=1):
    """「引いてもよい」の任意ドロー。山札を引き切って負けるだけなら引かない（全デッキ共通の決まり）"""
    if len(s.P[i].deck) <= n:
        return False
    s.draw(i, n)
    return True


def _has_hyper(u):
    """ハイパーモードを持つクリーチャーか（持たないクリーチャーは解放しても何も起きない）"""
    return u.k in E.HYPER_POW or "hyperbeast" in u.c.races


def _free_noncre(s, i, mx):
    """手札からコストを支払わずに実行できる「クリーチャーでないカード」（コスト mx 以下）のうち、
    いちばん重要度の高いもの"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "C" or c.cost > mx or E.PRI[k] <= bv:
            continue
        if c.kind == "S":
            if not s.spell_ok(i, c.cost):
                continue
        elif c.kind == "G":
            if s.has(1 - i, "fujin"):
                continue
        if c.kind != "S" and p.ban == c.cost:
            continue
        best, bv = k, E.PRI[k]
    return best


# ================================================================ 65/77 プラスワン・ハンド
def sp_plushand(s, i):
    """相手のクリーチャー1体を選び、破壊する。その後、カードを1枚引く"""
    t = s.target(i)
    if t is not None:
        destroy(s, i, t)
    s.draw(i, 1)


add("k24_plushand", "プラスワン・ハンド", 5, "D", kind="S", trig=True, pri=6, roles="rem trg draw",
    spell=sp_plushand,
    text="S・トリガー。相手のクリーチャー1体を選び、破壊する（重要度のいちばん高いものを選ぶ）。"
         "その後、カードを1枚引く",
    source=SRC["k24_plushand"])


# ================================================================ 66/77 切り札の時!!
def sp_kirifuda(s, i):
    """自分のシールドを1つブレイクする（自分のS・トリガーが撃てて、Zラッシュも起きる）"""
    if not s.P[i].sh:
        return
    s.ev("　切り札の時!!：自分のシールドを1つブレイクする")
    s.break_sh(1 - i, 1)


add("k24_kirifuda", "切り札の時!!", 4, "D", kind="S", gs=True, pri=4, roles="shd dis",
    spell=sp_kirifuda,
    text="G・ストライク。自分のシールドを1つブレイクする"
         "（割れたシールドは自分の手札に加わるので、S・トリガーなら撃てる。"
         "自分のシールドが離れるので、Zラッシュを持つクリーチャーのハイパーモードも解放される）",
    note="「相手は自身のシールドを1つ選ぶ」側ではなく自分のシールドなので、どのシールドが割れるかは"
         "エンジン共通の決まり（表向きのものを先に、次に裏向きの下のほうから）で決まる",
    source=SRC["k24_kirifuda"])


# ================================================================ 67/77 我竜塔第四層 ポチョムキン
def lw_potemkin(s, i, u, dest, destroy_):
    """各ターン、はじめてクリーチャーが破壊された時、自分はカードを1枚引いてもよい
    （どちらのクリーチャーが破壊されても誘発する）"""
    if not destroy_ or u.c.kind != "C":
        return
    for j in (0, 1):
        if s.over or not _castle_up(s, j, "k24_potemkin"):
            continue
        p = s.P[j]
        if p.x.get("k24_poch") == s.turn:
            continue
        p.x["k24_poch"] = s.turn
        if _safe_draw(s, j, 1):
            s.ev("　ポチョムキン：このターンはじめてクリーチャーが破壊された → 1枚引く")


add("k24_potemkin", "我竜塔第四層 ポチョムキン", 1, "D", kind="G", pri=3, roles="draw shd",
    leavewatch=lw_potemkin,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地に置く）。"
         "各ターン、はじめてクリーチャーが破壊された時、自分はカードを1枚引いてもよい"
         "（どちらのプレイヤーのクリーチャーでも誘発する。山札を引き切って負けるだけの時は引かない）",
    source=SRC["k24_potemkin"])


# ================================================================ 68/77 襲撃者ガルゼドライブ
def lr_galzedrive(s, i, u, dest, destroy_):
    """セイバー：超化獣（自分の超化獣が破壊される時、かわりにこのクリーチャーを破壊してもよい）"""
    if not destroy_ or u.k == "k24_galzedrive" or "hyperbeast" not in u.c.races:
        return False
    me = None
    for z in s.P[i].board:
        if z.k == "k24_galzedrive" and z is not u:
            if me is None or s.val(z) < s.val(me):
                me = z
    if me is None or s.val(u) <= s.val(me):
        return False                    # 守る値打ちがなければ使わない（全デッキ共通の決まり）
    s.ev(f"　セイバー：襲撃者ガルゼドライブを破壊して {u.c.name} を守る")
    s.leave(i, me, "grave", destroy=True)
    return True


add("k24_galzedrive", "襲撃者ガルゼドライブ", 3, "F", power=4000, sa=True, races=("dragonoid",),
    pri=4, roles="atk blk", leaverep=lr_galzedrive,
    text="スピードアタッカー。セイバー：超化獣（自分の超化獣が破壊される時、かわりにこのクリーチャーを"
         "破壊してもよい。守る値打ちのある超化獣のときだけ使う）",
    source=SRC["k24_galzedrive"])


# ================================================================ 70/77 プラスワン・フレーム
def sp_plusflame(s, i):
    """相手のクリーチャーを、パワーの合計が5000以下になるように好きな数選び、破壊する。その後1枚引く"""
    budget = 5000
    for _ in range(12):
        if budget <= 0:
            break
        t = s.target(i, lambda z: max(0, s.power(1 - i, z)) <= budget)
        if t is None:
            break
        budget -= max(0, s.power(1 - i, t))
        if not destroy(s, i, t):
            break
    s.draw(i, 1)


add("k24_plusflame", "プラスワン・フレーム", 4, "F", kind="S", trig=True, pri=6, roles="rem trg draw",
    spell=sp_plusflame,
    text="S・トリガー。相手のクリーチャーを、パワーの合計が5000以下になるように好きな数選び、破壊する"
         "（パワーの合計が残りの枠に収まるもののうち、重要度のいちばん高いものから順に選ぶ）。"
         "その後、カードを1枚引く",
    source=SRC["k24_plusflame"])


# ================================================================ 71/77 逆転の時!!
def sp_gyakuten(s, i):
    """相手は自身のシールドを1つ選ぶ。そのシールドをブレイクする"""
    if not s.P[1 - i].sh:
        return
    s.ev("　逆転の時!!：相手のシールドを1つブレイクする")
    s.break_sh(i, 1)


add("k24_gyakuten", "逆転の時!!", 2, "F", kind="S", gs=True, pri=3, roles="atk dis",
    spell=sp_gyakuten,
    text="G・ストライク。相手は自身のシールドを1つ選ぶ。そのシールドをブレイクする"
         "（ブロッカーや攻撃先の変更を越えてシールドを減らせる。相手のシールドが離れるので、"
         "Zラッシュを持つクリーチャーのハイパーモードも解放される）",
    note="「相手が自分のシールドを1つ選ぶ」ところは、どのシールドが割れるかをエンジン共通の決まり"
         "（表向きのものを先に、次に裏向きの下のほうから）で決めている",
    source=SRC["k24_gyakuten"])


# ================================================================ 72/77 我竜塔第三層 超鯱城
def ew_chosyachi(s, i, u):
    """相手のマナゾーンにあるカードの枚数よりコストが大きい相手のクリーチャーが出た時、それを破壊する"""
    if u.c.kind != "C" or s.over:
        return
    if not _castle_up(s, 1 - i, "k24_chosyachi"):
        return
    if u.c.cost <= len(s.P[i].mana):
        return
    if u not in s.P[i].board:
        return
    s.ev(f"　超鯱城：マナの枚数({len(s.P[i].mana)})よりコストが大きい {u.c.name} を破壊")
    s.leave(i, u, "grave", by_opp=True, destroy=True)


add("k24_chosyachi", "我竜塔第三層 超鯱城", 2, "F", kind="G", pri=5, roles="rem dis shd",
    enterwatch=ew_chosyachi,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地に置く）。"
         "相手のマナゾーンにあるカードの枚数よりコストが大きい相手のクリーチャーが出た時、そのクリーチャーを破壊する",
    source=SRC["k24_chosyachi"])


# ================================================================ 73/77 謎神のQ ギリメノアイル
add("k24_girimeno", "謎神のQ ギリメノアイル", 5, "N", power=9000, brk=2, zrush=True,
    races=("god", "hyperbeast"), pri=8, roles="atk fin",
    text="W・ブレイカー。Zラッシュ（シールドが離れたら、次の自分のターンのはじめまで、"
         "このクリーチャーのハイパーモードを解放する）。"
         "ハイパーモード中はパワー18000になり、Q・ブレイカー（シールドを4つブレイクする）になる",
    source=SRC["k24_girimeno"])
E.HYPER_POW["k24_girimeno"] = 9000
E.HYPER_BRK["k24_girimeno"] = 4


# ================================================================ 74/77 ノーガルディ・ネギオ＆ガルダンディ・ナスオ
def bw_negionasuo(s, i, u, b):
    """このクリーチャーがブロックされた時、相手のシールドを2つブレイクする（ブロック貫通）"""
    if u.k != "k24_negionasuo":
        return
    s.ev("　ネギオ＆ナスオ：ブロックされた → 相手のシールドを2つブレイク")
    s.break_sh(i, 2)


add("k24_negionasuo", "ノーガルディ・ネギオ＆ガルダンディ・ナスオ", 2, "N", power=3000,
    races=("wildvegies",), pri=4, roles="atk",
    blockwatch=bw_negionasuo,
    text="このクリーチャーがブロックされた時、このクリーチャーは相手のシールドを2つブレイクする"
         "（ブロック貫通。ブロックされてもシールドが2つ割れる）",
    source=SRC["k24_negionasuo"])


# ================================================================ 75/77 インビンシブル・タワー
def _elem3(s, i):
    """自分のコスト3以下のエレメント（バトルゾーンのカード）の数。
    G城はシールドゾーンのカードなのでエレメントではなく、数えない"""
    return sum(1 for u in s.P[i].board if u.c.cost <= 3)


def sc_invtower(s, i, k):
    """唱えるコストを、自分のコスト3以下のエレメント1つにつき3少なくする（0以下にならない）"""
    return max(1, 13 - 3 * _elem3(s, i))


def sp_invtower(s, i):
    """このターン、自分のクリーチャーすべてのパワーを+9000し、T・ブレイカーを与える"""
    n = 0
    for u in s.P[i].board:
        if u.c.kind != "C":
            continue
        u.pw += 9000
        u.x["k24_tower"] = s.turn
        n += 1
    if n:
        s.ev(f"　インビンシブル・タワー：自分のクリーチャー{n}体に+9000とT・ブレイカー")


def bp_invtower(s, i, u):
    """T・ブレイカーを与える（すでに3つ以上ブレイクするなら増やさない）"""
    if u.x.get("k24_tower") != s.turn:
        return 0
    base = u.c.brk
    if u.hyper and u.k in E.HYPER_POW:
        base = E.HYPER_BRK.get(u.k, 2)
    return max(0, 3 - base)


add("k24_invtower", "インビンシブル・タワー", 13, "N", kind="S", pri=8, roles="atk fin",
    spell=sp_invtower, spcost=sc_invtower, brkplus=bp_invtower,
    text="この呪文を唱えるコストを、自分のコスト3以下のエレメント1つにつき3少なくする"
         "（ただしコストは1より少なくならない）。このターン、自分のクリーチャーすべてのパワーを+9000し、"
         "「T・ブレイカー」を与える（すでに3つ以上ブレイクするクリーチャーのブレイク数は減らさない）",
    note="コスト軽減が数えるエレメントは、バトルゾーンにあるカード（クリーチャー・タマシード・クロスギア・"
         "禁断の鼓動）のうちコスト3以下のもの。G城は表向きのシールドなのでエレメントに数えていない",
    source=SRC["k24_invtower"])


# ================================================================ 76/77 プラスワン・トラップ
def sp_plustrap(s, i):
    """相手のクリーチャー1体を選び、持ち主のマナゾーンに置く。その後、カードを1枚引く"""
    t = s.target(i)
    if t is not None:
        move(s, i, t, "mana")
    s.draw(i, 1)


add("k24_plustrap", "プラスワン・トラップ", 4, "N", kind="S", trig=True, pri=6, roles="rem trg draw",
    spell=sp_plustrap,
    text="S・トリガー。相手のクリーチャー1体を選び、持ち主のマナゾーンに置く"
         "（重要度のいちばん高いものを選ぶ）。その後、カードを1枚引く。"
         "《プラスワン・ゲート》（手札に戻す）とは別のカード",
    source=SRC["k24_plustrap"])


# ================================================================ 77/77 我竜塔第二層 ダルマンディ
def ew_darmandi(s, i, u):
    """自分のクリーチャーが出た時、次の自分のターンのはじめまで、自分のクリーチャーすべての
    ハイパーモードを解放する"""
    if u.c.kind != "C" or s.over:
        return
    if not _castle_up(s, i, "k24_darmandi"):
        return
    n = 0
    for z in s.P[i].board:
        if z.c.kind == "C" and not z.hyper and _has_hyper(z):
            z.hyper = True
            n += 1
    if n:
        s.ev(f"　ダルマンディ：自分のクリーチャー{n}体のハイパーモードを解放")


add("k24_darmandi", "我竜塔第二層 ダルマンディ", 3, "N", kind="G", pri=5, roles="atk shd",
    enterwatch=ew_darmandi,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地に置く）。"
         "自分のクリーチャーが出た時、次の自分のターンのはじめまで、自分のクリーチャーすべての"
         "ハイパーモードを解放する（ハイパーモードを持たないクリーチャーには何も起きない）",
    source=SRC["k24_darmandi"])


# ================================================================ RP2 OR1/OR1 燃える禁断 ドルマゲドンW
def e_dolmageddonw(s, i, u):
    """出た時、自分の手札を1枚捨て、カードを2枚引く（封印4つは ew_dolmageddonw で付ける）"""
    discard_choice(s, i)
    s.draw(i, 2)


def ew_dolmageddonw(s, i, u):
    """出た時の後半：このクリーチャーに封印を4つ付ける。
    「コマンドが出た時に封印を1つ外す」（env0 の enterwatch）より後に処理するために、
    こちら側（env0 より後に登録される enterwatch）で封印を付けている。
    ドルマゲドンW 自身がソニック・コマンドなので、同時に誘発する封印外しのほうを先に解決する形になる"""
    if u.k != "k24_dolmageddonw" or s.over:
        return
    if u not in s.P[i].board or u.x.get("k24_sealed"):
        return
    u.x["k24_sealed"] = 1
    s.seal(i, u, 4)


def atk_dolmageddonw(s, i, u):
    """攻撃する時、相手のクリーチャーを1体選び、相手はそれに封印を1つ付ける"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　ドルマゲドンW：{t.c.name} に封印を1つ付ける")
    s.seal(1 - i, t, 1)


add("k24_dolmageddonw", "燃える禁断 ドルマゲドンW", 2, "DF", power=999999, brk=3,
    races=("kindan", "soniccommand", "command"), pri=12, roles="fin atk rem draw",
    enter=e_dolmageddonw, enterwatch=ew_dolmageddonw, attack=atk_dolmageddonw,
    text="T・ブレイカー。このクリーチャーが出た時、自分の手札を1枚捨て、カードを2枚引く。"
         "その後、このクリーチャーに封印を4つ付ける（封印されている間はバトルゾーンにないものとして扱う。"
         "コマンドが出るたびに、その持ち主は文明の合う封印を1つ墓地に置く）。"
         "このクリーチャーが攻撃する時、相手のクリーチャーを1体選び、相手はそれに封印を1つ付ける"
         "（重要度のいちばん高いものを選ぶ）",
    source=SRC["k24_dolmageddonw"])


# ================================================================ RP2 S3/S11 龍V王 Q.E.D.
def e_qed(s, i, u):
    """出た時、山札の上から5枚を表向きにする。その中から異なるカードタイプを持つカードを好きな数選び、
    手札に加える。残りを好きな順序で山札の下に置く"""
    p = s.P[i]
    n = min(5, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    pick = {}
    for k in top:
        kd = BY_KEY[k].kind
        cur = pick.get(kd)
        if cur is None or E.PRI[k] > E.PRI[cur]:
            pick[kd] = k
    got = []
    for kd in sorted(pick):
        k = pick[kd]
        top.remove(k)
        p.hand.append(k)
        got.append(BY_KEY[k].name)
    for k in top:
        p.deck.insert(0, k)
    if got:
        s.ev(f"　Q.E.D.：{'／'.join(got)} を手札に加えた")


def lf_qed(s, i, u, dest):
    """離れた時、コスト6以下のクリーチャーでないカード1枚を、手札からコストを支払わずに実行してもよい"""
    if s.over:
        return
    k = _free_noncre(s, i, 6)
    if k is None:
        return
    s.ev(f"　Q.E.D.：手札の {BY_KEY[k].name} をコストを支払わずに実行")
    free_play(s, i, k, "hand")


add("k24_qed", "龍V王 Q.E.D.", 5, "W", power=8000, brk=2, blocker=True, jd=True,
    races=("crystalcommanddragon", "command", "dragon", "revolution", "hamukatsu"),
    pri=9, roles="blk draw rem fin", enter=e_qed, left=lf_qed,
    text="ブロッカー。ジャストダイバー（出たターン、相手に選ばれず、攻撃もブロックもされない）。"
         "W・ブレイカー。出た時、自分の山札の上から5枚を表向きにし、その中から異なるカードタイプを持つ"
         "カードを好きな数選んで手札に加える（カードタイプごとに重要度のいちばん高い1枚を取る）。"
         "残りは山札の下に置く。このクリーチャーが離れた時、コスト6以下のクリーチャーでないカード1枚を、"
         "自分の手札からコストを支払わずに実行してもよい（重要度のいちばん高いものを実行する）",
    source=SRC["k24_qed"])


# ================================================================ RP2 S4/S11 魔V王 デスシラズ
def _grave_dark_cre(s, i):
    """自分の墓地にある闇のクリーチャーのうち、いちばん安いもの（進化元にして使い切る側）"""
    cs = [k for k in s.P[i].grave if BY_KEY[k].kind == "C" and "D" in E.MCIV[k]]
    return min(cs, key=E.PRI.get) if cs else None


def es_deathshirazu(s, i):
    """墓地進化：自分の墓地にある闇のクリーチャー1体を進化元にする（evosrc）

    進化元が墓地にいなければ None を返し、エンジンが召喚の手を出さない。"""
    k = _grave_dark_cre(s, i)
    return ("grave", k) if k is not None else None


def ts_deathshirazu(s, i, u):
    """自分のターンのはじめに、自分の山札の上から2枚を墓地に置いてもよい
    （このカード自身が見ている「墓地13枚」に届いていない間だけ置く）"""
    if len(s.P[i].grave) >= 13:
        return
    s.mill(i, 2)


def lf_deathshirazu(s, i, u, dest):
    """離れた時、自分の墓地にカードが13枚以上あれば、相手のクリーチャーをすべて破壊する"""
    if len(s.P[i].grave) < 13:
        return
    s.ev("　デスシラズ：墓地が13枚以上 → 相手のクリーチャーをすべて破壊")
    for z in _opp_cre(s, i):
        if s.over:
            return
        if z in s.P[1 - i].board:
            s.leave(1 - i, z, "grave", by_opp=True, destroy=True)


def pr_deathshirazu(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and "D" in E.MCIV[kk] and not (BY_KEY[kk].evo and not BY_KEY[kk].neo))
    return None if n >= 6 else "墓地進化の元になる闇のクリーチャーが6体いない"


add("k24_deathshirazu", "魔V王 デスシラズ", 3, "D", power=8000, brk=2, evo="grave",
    races=("demoncommand", "command", "dragon", "revolution", "hamukatsu"),
    pri=9, roles="fin rem atk", evosrc=es_deathshirazu,
    evox=lambda s, i, u: False, tstart=ts_deathshirazu, left=lf_deathshirazu,
    playrule=pr_deathshirazu,
    text="墓地進化：自分の墓地にある闇のクリーチャー1体の上に重ねつつ出す（墓地にそれがなければ召喚できない。"
         "いちばん安い闇のクリーチャーを進化元にする）。W・ブレイカー。"
         "自分のターンのはじめに、自分の山札の上から2枚を墓地に置いてもよい（墓地が13枚に届くまで置く）。"
         "このクリーチャーが離れた時、自分の墓地にカードが13枚以上あれば、相手のクリーチャーをすべて破壊する",
    source=SRC["k24_deathshirazu"])
