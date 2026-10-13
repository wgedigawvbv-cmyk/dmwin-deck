"""担当29：DM26-RP2（逆札篇 第2弾 燃えろ禁断！逆転のドギラゴン革命‼︎）の未実装カード15枚

出典：dmwiki.net の各カードページ（https://dmwiki.net/DM26-RP2 の 60/77〜74/77）。
      15枚すべてについて、カードページと生の wiki ソース（?plugin=template&refer=…）を
      別の質問で2回ずつ読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
      どちらも一致することを確かめた。

  この札束に入っている新しい仕組み
    ・「熱血の親衛隊」5枚サイクルのうち3枚（ペッパー／ファンク／クラップ）。
      1マナ圏〜2マナ圏の「ハンター／エイリアン」で、それぞれ別のデメリット持ち。
      数値は流用せず1枚ずつ読み直した（ペッパー 水4000・ファンク 闇4000・クラップ 火2000）。
    ・「雪精◯◯。」サイクルのうち2枚（マリニャン。／サエポヨ。）。種族は**スノーフェアリー風**で、
      《エンドレス・フローズン・カーニバル》が数える「スノーフェアリー」とは別の種族。
      どちらも**スーパーガードマン**を持つ。
    ・コモンの呪文サイクル（天災のSSS級計画／狼牙獣鎌拳／FORBIDDEN RAGE ～禁断の怒り～）。
      3枚とも「S・トリガー」＋「このターン、自分のクリーチャー1体のパワーを+4000」＋もう1つの効果。
    ・革命チェンジ3枚（ZEROの革命 ブラックアウト／超革命 マッハ55／風の1号 ハムカツマン逆）。
      どれも文明だけの条件（パワーやコストの下限が無い）。
    ・封印を使い回す《革命α ドルーター》（自分の封印が墓地に置かれた時、それを手札に戻す）。
    ・シールド・ゴー（禁術のラクシャ カレイル）。
    ・アンタップキラー（機神勇者ビクトリーダッシュ・バスター）。エンジンは「アンタップしている
      クリーチャーへの攻撃」をマッハファイター（出たターンだけ）でしか許していないので、
      追加の手（freeacts/actapply）として攻撃そのものを作って表した。

  調べ直して意外だった点
    ・《FORBIDDEN RAGE ～禁断の怒り～》は名前に「禁断」とあるが**禁断の鼓動ではなく、ただのS・トリガー呪文**
      だった（封印も禁断解放も無い）。コモンの呪文サイクルの火文明担当。
    ・《ZEROの革命 ブラックアウト》《超革命 マッハ55》《革命α ドルーター》は名前が「革命」でも中身が別物で、
      ドルーターだけは革命チェンジを持たない（封印を拾う能力だけ）。
    ・《熱血の親衛隊ペッパー》のデメリットは「このターンに自分がカードを2枚以上引いていなければ攻撃できない」で、
      2マナでパワー4000＋ジャストダイバーという強い数値だった。
    ・《熱血の親衛隊クラップ》は能力がパワーアタッカー+3000だけの準バニラ。
    ・《雪精 サエポヨ。》は《完璧妖精サエポヨX》とは全く別のカード（自然7コスト・12000・T・ブレイカー）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add
from envcards.env0 import SLAYER, lock_until_my_turn

W = "https://dmwiki.net/"
SRC = {
    "k29_pepper": W + "《熱血の親衛隊ペッパー》",
    "k29_robert": W + "《アクア秘務官 ロバート・フック》",
    "k29_sssplan": W + "《天災のSSS級計画》",
    "k29_blackout": W + "《ZEROの革命 ブラックアウト》",
    "k29_dorutar": W + "《革命α ドルーター》",
    "k29_funk": W + "《熱血の親衛隊ファンク》",
    "k29_kareiru": W + "《禁術のラクシャ カレイル》",
    "k29_borofsize": W + "《狼牙獣鎌拳》",
    "k29_mach55": W + "《超革命 マッハ55》",
    "k29_marinyan": W + "《雪精 マリニャン。》",
    "k29_vdbuster": W + "《機神勇者ビクトリーダッシュ・バスター》",
    "k29_clap": W + "《熱血の親衛隊クラップ》",
    "k29_forbidrage": W + "《FORBIDDEN RAGE ～禁断の怒り～》",
    "k29_saepoyo": W + "《雪精 サエポヨ。》",
    "k29_hamukatsu": W + "《風の1号 ハムカツマン逆》",
}


# ================================================================ 共通の道具
def _in_deck(s, j, key):
    """プレイヤー j のデッキにそのカードが入っているか（見回りを他の対戦で動かさないための門）"""
    return key in (s.P[j].list or ())


def _best_own(s, i, pred=None):
    """「自分のクリーチャー1体」を選ぶ（パワーを上げる先。アンタップのもの、パワーの高いものを優先）"""
    cs = [z for z in s.P[i].board if z.c.kind == "C" and (pred is None or pred(z))]
    if not cs:
        return None
    return max(cs, key=lambda z: (0 if z.tap else 1, s.power(i, z), E.PRI[z.k]))


def _pump_own(s, i, n, who):
    """このターン、自分のクリーチャー1体のパワーを+n する"""
    z = _best_own(s, i)
    if z is None:
        return None
    z.pw += n
    s.ev(f"　{who}：{z.c.name} のパワーをこのターン+{n}")
    return z


def _minus_power(s, i, t, n, who):
    """相手のクリーチャー t のパワーをこのターン -n する（0以下になれば破壊）"""
    t.pw -= n
    s.ev(f"　{who}：{t.c.name} のパワーをこのターン-{n}")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def _take_shield(s, i, dest="hand"):
    """自分のシールド1つを手札に加える（裏向きを先に。その「S・トリガー」は使えない）。できたら True。

    シールドゾーンの出口は s.take_shield 1か所なので、そこを通す
    （SHIELDDEST＝シールド・ゴーと SHIELDOUT がここで正しく働く）。"""
    p = s.P[i]
    if not p.sh:
        return False
    j = next((x for x in range(len(p.sh) - 1, -1, -1) if not p.sh[x][1]), len(p.sh) - 1)
    return s.take_shield(i, j, dest) is not None


def _grave_to_hand(s, i, pred, who):
    """自分の墓地から条件に合うカード1枚を手札に戻す（いちばん重要度の高いもの）"""
    p = s.P[i]
    cands = [k for k in sorted(set(p.grave)) if pred(BY_KEY[k])]
    if not cands:
        return None
    k = max(cands, key=E.PRI.get)
    p.grave.remove(k)
    p.hand.append(k)
    s.ev(f"　{who}：墓地の {BY_KEY[k].name} を手札に戻す")
    return k


def _change_rule(civ, label):
    """革命チェンジの「そのデッキで出せるか」の判定（元になれるクリーチャーが3体以上いるか）"""
    def f(deck, k):
        n = sum(v for kk, v in deck.items()
                if kk != k and BY_KEY[kk].kind == "C" and set(civ) & set(BY_KEY[kk].civ))
        return None if n >= 3 else f"革命チェンジの元（{label}のクリーチャー）が3体いない"
    return f


# ---------------------------------------------------------------- シールド・ゴー
def sgo_destroyed(s, i, u):
    """シールド・ゴー：このクリーチャーが破壊された時、自分の墓地から表向きでシールド化する"""
    p = s.P[i]
    if u.k not in p.grave:
        return
    p.grave.remove(u.k)
    if not s.add_shield(i, u.k, True):
        p.grave.append(u.k)
        return
    s.ev(f"　シールド・ゴー：{u.c.name} を表向きのシールドとして置く")


def sgo_dest(s, i, k, up, dest):
    """シールド・ゴー：表向きのこのカードが表向きのままシールドゾーンを離れる時は、かわりに墓地に置く
    （SHIELDDEST なのでブレイクでも効果でも通る）"""
    return "grave" if up else dest


# ---------------------------------------------------------------- スーパーガードマン
def super_guardman(key, cond=None):
    """スーパーガードマン：自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーを
    タップしてバトルさせてもよい（BATTLESWAP。ブロックで起きたバトルも効果で起きたバトルも引き受ける。
    攻撃先を変えるわけではないので、攻撃されたクリーチャー自身はシールドをブレイクできる）。

    使うかどうかは共通の決まりで機械的に決める：バトルに勝てるか、守る相手のほうが大事な時だけ引き受ける。
    （どのカードがガードマン系を持つかは engine3.GUARDMEN で引ける）"""
    E.GUARDMEN.add(key)

    def f(s, di, du, ai, au):
        if du is None:
            return None
        ap = s.power(ai, au, True)
        for z in s.P[di].board:
            if z.k != key or z.c.kind != "C" or z.tap or z is du:
                continue
            if cond is not None and not cond(s, di, z):
                continue
            if s.power(di, z) > ap or s.val(du) > s.val(z):
                s.tap_cre(di, z)
                return z
        return None
    return f


# ================================================================ 60/77 熱血の親衛隊ペッパー
def ca_pepper(s, i, u):
    """このターンに自分がカードを2枚以上引いていなければ攻撃できない
    （p.drawn はターンのはじめに0に戻り、そのターンの引いた枚数を数えている）"""
    return s.P[i].drawn < 2


add("k29_pepper", "熱血の親衛隊ペッパー", 2, "W", power=4000, jd=True,
    races=("cyberlord", "hunter", "alien"), pri=3, roles="atk",
    cantatk=ca_pepper,
    text="ジャストダイバー（出た時、次の自分のターンのはじめまで、相手に選ばれず攻撃されない）。"
         "このターンに自分がカードを2枚以上引いていなければ、このクリーチャーは攻撃できない",
    source=SRC["k29_pepper"])


# ================================================================ 61/77 アクア秘務官 ロバート・フック
def brk_powered(s, i, u):
    """パワード・ブレイカー：パワー6000ごとにシールドをもう1つブレイクする"""
    return 1 + s.power(i, u, True) // 6000


def sw_robert(s, i, k):
    """自分が呪文を唱えた時、このターン、このクリーチャーのパワーを+3000する"""
    if not s.has(i, "k29_robert"):
        return
    for u in s.P[i].board:
        if u.k == "k29_robert":
            u.pw += 3000
            s.ev("　ロバート・フック：呪文を唱えたのでパワーをこのターン+3000")


add("k29_robert", "アクア秘務官 ロバート・フック", 2, "W", power=2000,
    races=("liquid",), pri=3, roles="atk",
    brkx=brk_powered, spellwatch=sw_robert,
    text="パワード・ブレイカー（このクリーチャーは、そのパワー6000ごとにシールドをもう1つブレイクする）。"
         "自分が呪文を唱えた時、このターン、このクリーチャーのパワーを+3000する",
    source=SRC["k29_robert"])


# ================================================================ 62/77 天災のSSS級計画
def sp_sssplan(s, i):
    """相手のクリーチャー1体を、次の自分のターンのはじめまで攻撃もブロックもできなくする。
    その後、このターン、自分のクリーチャー1体のパワーを+4000する"""
    t = s.target(i)
    if t is not None:
        lock_until_my_turn(s, i, t)
        s.ev(f"　天災のSSS級計画：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")
    _pump_own(s, i, 4000, "天災のSSS級計画")


add("k29_sssplan", "天災のSSS級計画", 2, "W", kind="S", trig=True, pri=3, roles="dis trg atk",
    spell=sp_sssplan,
    text="S・トリガー。相手のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、そのクリーチャーは"
         "攻撃もブロックもできない。このターン、自分のクリーチャー1体のパワーを+4000する"
         "（相手はいちばん重要なクリーチャー、自分はアンタップしているパワーのいちばん高いクリーチャーを選ぶ）",
    source=SRC["k29_sssplan"])


# ================================================================ 63/77 ZEROの革命 ブラックアウト
def e_blackout(s, i, u):
    """出た時、自分の山札の上から3枚を墓地に置く。その後、クリーチャー1体を自分の墓地から手札に戻す"""
    s.mill(i, 3)
    if s.over:
        return
    _grave_to_hand(s, i, lambda c: c.kind == "C", "ブラックアウト")


SLAYER.add("k29_blackout")

add("k29_blackout", "ZEROの革命 ブラックアウト", 4, "D", power=4000,
    races=("soniccommand", "command", "initialsw"), pri=6, roles="draw rem atk",
    enter=e_blackout, changex=lambda s, i, u: "D" in u.c.civ,
    playrule=_change_rule("D", "闇"),
    text="革命チェンジ：闇のクリーチャー。スレイヤー（バトルした後、相手クリーチャーを破壊する）。"
         "出た時、自分の山札の上から3枚を墓地に置く。その後、クリーチャーを1体、自分の墓地から手札に戻す"
         "（墓地のいちばん重要なクリーチャーを戻す）",
    source=SRC["k29_blackout"])


# ================================================================ 64/77 革命α ドルーター
def _seal_cards(s, j):
    """プレイヤー j の封印として置かれているカードすべて（クリーチャーの封印と禁断の鼓動の封印）"""
    p = s.P[j]
    out = []
    for u, _m in p.sealed:
        out.extend(u.x.get("sealcards") or ())
    for u in p.board:
        if u.c.kind == "K":
            out.extend(u.x.get("sealcards") or ())
    return tuple(sorted(out))


def _dorutar_mark(s, j):
    """いまの封印の状態を覚える（これより減った分が「封印が墓地に置かれた」ぶん）"""
    s.P[j].x["k29_seals"] = _seal_cards(s, j)


def _dorutar_poll(s):
    """自分の封印が墓地に置かれた時、そのカードを自分の墓地から手札に戻す。

    エンジンに「封印が墓地に置かれた時」の差し込み口が無いので、封印の一覧を覚えておいて
    減った分を拾っている（減ったカードのキーまで分かるので、戻すカードは正しい）。"""
    for j in (0, 1):
        p = s.P[j]
        if not _in_deck(s, j, "k29_dorutar"):
            continue
        cur = _seal_cards(s, j)
        prev = p.x.get("k29_seals")
        p.x["k29_seals"] = cur
        if prev is None or prev == cur or s.over:
            continue
        gone = list(prev)
        for k in cur:
            if k in gone:
                gone.remove(k)
        if not gone or not s.has(j, "k29_dorutar"):
            continue
        for k in gone:
            if k in p.grave:
                p.grave.remove(k)
                p.hand.append(k)
                s.ev(f"　革命α ドルーター：墓地に置かれた封印 {BY_KEY[k].name} を手札に戻す")


def e_dorutar(s, i, u):
    """出た時の能力は無い。自分が出たことでコマンドとして外れる封印を拾えるよう、
    この時点の封印の一覧を覚えておく（出た時の処理は ENTERWATCH の封印外しより先に呼ばれる）"""
    _dorutar_mark(s, i)


def ew_dorutar(s, i, u):
    _dorutar_poll(s)


def sw_dorutar(s, i, k):
    _dorutar_poll(s)


def ta_dorutar(s, i, u):
    """ターンの終わりにも封印の一覧を見比べる（取りこぼしを拾う）"""
    if u.k != "k29_dorutar":
        return
    _dorutar_poll(s)


add("k29_dorutar", "革命α ドルーター", 3, "D", power=4000,
    races=("soniccommand", "command", "initialsw"), pri=4, roles="draw",
    enter=e_dorutar, enterwatch=ew_dorutar, spellwatch=sw_dorutar, tendall=ta_dorutar, status="partial",
    note="「自分の封印が墓地に置かれた時」の差し込み口は、いまのエンジンにもまだ無い"
         "（封印のカードは engine3.unseal と env0.remove_seal が p.grave に直接足している）。"
         "そのため封印の一覧を覚えておき、クリーチャーが出た時・呪文を唱えた時・ターンの終わりに"
         "見比べて拾っている（自分が出た時にコマンドとして外す封印はその場で拾える）。"
         "封印が外れてから、この3つのどれも挟まずに次の処理が進む場合だけは拾えない",
    text="自分の封印が墓地に置かれた時、そのカードを自分の墓地から手札に戻してもよい。"
         "このクリーチャー自身がコマンドなので、出た時に自分の封印を1つ外し、それを手札に戻せる",
    source=SRC["k29_dorutar"])


# ================================================================ 65/77 熱血の親衛隊ファンク
def ta_funk(s, i, u):
    """各ターンの終わりに、このクリーチャーがタップしていれば、このクリーチャーを破壊する
    （攻撃・ブロック以外でタップした時も破壊される）"""
    if u.k != "k29_funk" or not u.tap:
        return
    if u not in s.P[i].board:
        return
    s.ev("　熱血の親衛隊ファンク：タップしているので破壊される")
    s.leave(i, u, "grave", destroy=True)


add("k29_funk", "熱血の親衛隊ファンク", 2, "D", power=4000, blocker=True,
    races=("darklord", "hunter", "alien"), pri=3, roles="blk",
    tendall=ta_funk,
    text="ブロッカー。各ターンの終わりに、このクリーチャーがタップしていれば、このクリーチャーを破壊する"
         "（ブロックしたターンだけでなく、効果でタップされた時も破壊される）",
    source=SRC["k29_funk"])


# ================================================================ 66/77 禁術のラクシャ カレイル
def e_kareiru(s, i, u):
    """出た時、自分のシールドを1つ手札に加える。その「S・トリガー」は使えない"""
    if _take_shield(s, i, "hand"):
        s.ev("　禁術のラクシャ カレイル：自分のシールド1つを手札に加えた（S・トリガーは使えない）")


add("k29_kareiru", "禁術のラクシャ カレイル", 2, "D", power=2000,
    races=("oracle", "humanoid"), pri=3, roles="draw shd",
    enter=e_kareiru, destroyed=sgo_destroyed, shielddest=sgo_dest,
    text="出た時、自分のシールドを1つ手札に加える。その「S・トリガー」は使えない。"
         "シールド・ゴー（このクリーチャーが破壊された時、自分の墓地から表向きでシールド化する。"
         "表向きのままシールドゾーンを離れる時は、かわりに墓地に置く）",
    source=SRC["k29_kareiru"])


# ================================================================ 67/77 狼牙獣鎌拳
def sp_borofsize(s, i):
    """相手のクリーチャー1体のパワーをこのターン-4000（0以下なら破壊）。
    その後、このターン、自分のクリーチャー1体のパワーを+4000する"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 4000) or s.target(i)
    if t is not None:
        _minus_power(s, i, t, 4000, "狼牙獣鎌拳")
    if not s.over:
        _pump_own(s, i, 4000, "狼牙獣鎌拳")


add("k29_borofsize", "狼牙獣鎌拳", 3, "D", kind="S", trig=True, pri=4, roles="rem trg atk",
    spell=sp_borofsize,
    text="S・トリガー。相手のクリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを-4000する"
         "（パワーが0以下のクリーチャーは破壊される。倒せる相手を優先して選ぶ）。"
         "このターン、自分のクリーチャー1体のパワーを+4000する",
    source=SRC["k29_borofsize"])


# ================================================================ 68/77 超革命 マッハ55
def ew_mach55(s, i, u):
    """自分のターンに相手のクリーチャーが召喚以外の方法で出た時、そのクリーチャーを破壊する"""
    j = 1 - i
    if u.c.kind != "C" or s.tp != j or u.x.get("summoned"):
        return
    if not s.has(j, "k29_mach55") or u not in s.P[i].board:
        return
    s.ev(f"　超革命 マッハ55：召喚以外で出た {u.c.name} を破壊する")
    s.leave(i, u, "grave", by_opp=True, destroy=True)


add("k29_mach55", "超革命 マッハ55", 4, "F", power=4000, sa=True,
    races=("soniccommand", "command", "initialsw"), pri=6, roles="atk dis rem",
    changex=lambda s, i, u: "F" in u.c.civ, enterwatch=ew_mach55,
    playrule=_change_rule("F", "火"),
    text="革命チェンジ：火のクリーチャー。スピードアタッカー。"
         "自分のターンに相手のクリーチャーが召喚以外の方法で出た時、そのクリーチャーを破壊する",
    source=SRC["k29_mach55"])


# ================================================================ 69/77 雪精 マリニャン。
def aw_marinyan(s, i, u):
    """このターンに攻撃したクリーチャーを覚えておく（マリニャン。の攻撃条件を見るため）"""
    p = s.P[i]
    if not _in_deck(s, i, "k29_marinyan"):
        return
    if p.x.get("k29_atkt") != s.turn:
        p.x["k29_atkt"] = s.turn
        p.x["k29_atku"] = ()
    if u.uid not in p.x["k29_atku"]:
        p.x["k29_atku"] = p.x["k29_atku"] + (u.uid,)


def ca_marinyan(s, i, u):
    """このターンに他のクリーチャーが攻撃していなければ、このクリーチャーは攻撃できない"""
    p = s.P[i]
    if p.x.get("k29_atkt") != s.turn:
        return True
    return not any(x != u.uid for x in p.x.get("k29_atku", ()))


add("k29_marinyan", "雪精 マリニャン。", 3, "F", power=8000, brk=2,
    races=("snowfu",), pri=6, roles="blk atk",
    battleswap=super_guardman("k29_marinyan"), atkwatch=aw_marinyan, cantatk=ca_marinyan,
    text="スーパーガードマン（自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーをタップして"
         "バトルさせてもよい）。W・ブレイカー。"
         "このターンに他のクリーチャーが攻撃していなければ、このクリーチャーは攻撃できない",
    source=SRC["k29_marinyan"])


# ================================================================ 70/77 機神勇者ビクトリーダッシュ・バスター
def _can_attack_now(s, i, u):
    """そのクリーチャーがいま攻撃できるか（エンジンの legal_attack と同じ判定）"""
    c = u.c
    ign = bool(E.NOATKIGN) and any(f(s, i, u) for f in E.NOATKIGN)
    if c.kind != "C" or u.tap or (c.noatk and not ign) or (u.lock == s.turn and not ign):
        return False
    if u.k in E.CANTATK and E.CANTATK[u.k](s, i, u):
        return False
    if any(f(s, i, u) for f in E.ATKLOCK):
        return False
    return ((not u.sick) or u.sa or c.sa or s.has(i, "jaouga") or bool(c.evo and u.under)
            or bool(E.SAOK and any(f(s, i, u) for f in E.SAOK)))


def fa_vdbuster(s, i, av, cv):
    """アンタップキラー：アンタップしているクリーチャーへの攻撃を、追加の手として作る
    （エンジンはアンタップしているクリーチャーへの攻撃をマッハファイターにしか許していない）"""
    if not s.has(i, "k29_vdbuster"):
        return []
    out, seen = [], set()
    o = s.P[1 - i]
    for u in s.P[i].board:
        if u.k != "k29_vdbuster" or not _can_attack_now(s, i, u):
            continue
        ap = s.power(i, u, True)
        for t in o.board:
            if t.c.kind != "C" or t.jd or t.tap or t.k in seen:
                continue
            if E.ATKTARGETLOCK and any(f(s, i, u, t) for f in E.ATKTARGETLOCK):
                continue
            if s.power(1 - i, t) > ap:
                continue
            seen.add(t.k)
            out.append(("x:k29_vdb", u.uid, t.uid))
        break                               # 1体ぶんの手を出せば足りる（同名の2体目は同じ手になる）
    return out


def ap_vdbuster(s, a):
    i = s.tp
    p, o = s.P[i], s.P[1 - i]
    idx = next((j for j, u in enumerate(p.board) if u.uid == a[1]), None)
    tgt = next((j for j, u in enumerate(o.board) if u.uid == a[2]), None)
    if idx is None or tgt is None:
        return
    s.phase = "A"
    s.ev("アンタップキラー：機神勇者ビクトリーダッシュ・バスターがアンタップしているクリーチャーを攻撃")
    s.attack(idx, tgt)


add("k29_vdbuster", "機神勇者ビクトリーダッシュ・バスター", 3, "F", power=4000,
    races=("humanoid", "beastfolk"), pri=4, roles="rem atk",
    freeacts=fa_vdbuster, actapply={"x:k29_vdb": ap_vdbuster}, status="partial",
    note="アンタップキラー（アンタップしているクリーチャーを攻撃できる）の差し込み口は、いまのエンジンにも無い。"
         "engine3.legal_attack はアンタップしているクリーチャーへの攻撃を mf（そのターンに出た"
         "マッハファイター）にしか許しておらず、MACHOK も u.sick の時だけ効くので、"
         "出たターン以外のアンタップキラーは表せない。そこで追加の手（freeacts）として攻撃そのものを作った。"
         "そのため、この攻撃は「攻撃に移る」前（メインステップ）からしか宣言できず、"
         "ほかのクリーチャーで攻撃し始めた後には選べない",
    text="このクリーチャーは、アンタップしているクリーチャーを攻撃できる",
    source=SRC["k29_vdbuster"])


# ================================================================ 71/77 熱血の親衛隊クラップ
add("k29_clap", "熱血の親衛隊クラップ", 2, "F", power=2000,
    races=("firebird", "hunter", "alien"), pri=3, roles="atk",
    powerx=lambda s, i, u, atk: 3000 if atk else 0,
    text="パワーアタッカー+3000（このクリーチャーが攻撃する時、このクリーチャーのパワーは+3000される）",
    source=SRC["k29_clap"])


# ================================================================ 72/77 FORBIDDEN RAGE ～禁断の怒り～
def sp_forbidrage(s, i):
    """このターン、自分のクリーチャー1体のパワーを+4000する。
    その後、相手のクリーチャーを1体選んでもよい。その2体をバトルさせる
    （勝てる相手がいる時だけバトルさせる＝任意の選択はこのシミュレーター共通の決まりで決める）"""
    z = _pump_own(s, i, 4000, "FORBIDDEN RAGE")
    if z is None or s.over or z not in s.P[i].board:
        return
    ap = s.power(i, z, True)
    t = s.target(i, lambda x: s.power(1 - i, x) <= ap)
    if t is None:
        return
    s.ev(f"　FORBIDDEN RAGE：{z.c.name} と {t.c.name} をバトルさせる")
    s.battle(i, z, 1 - i, t)


add("k29_forbidrage", "FORBIDDEN RAGE ～禁断の怒り～", 2, "F", kind="S", trig=True, pri=3, roles="rem trg atk",
    spell=sp_forbidrage,
    text="S・トリガー。このターン、自分のクリーチャー1体のパワーを+4000する。"
         "その後、相手のクリーチャーを1体選んでもよい。その2体をバトルさせる"
         "（バトルで勝てる相手のうち、いちばん重要なクリーチャーを選ぶ）",
    source=SRC["k29_forbidrage"])


# ================================================================ 73/77 雪精 サエポヨ。
add("k29_saepoyo", "雪精 サエポヨ。", 7, "N", power=12000, brk=3,
    races=("snowfu",), pri=9, roles="blk atk fin",
    costx=lambda s, i, av: max(0, 7 - s.ncre(i)), battleswap=super_guardman("k29_saepoyo"),
    text="シンパシー：自分のクリーチャー（このカードの召喚コストを、自分のクリーチャー1体につき1少なくする。"
         "ただしコストは0以下にならない）。"
         "スーパーガードマン（自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーをタップして"
         "バトルさせてもよい）。T・ブレイカー",
    source=SRC["k29_saepoyo"])


# ================================================================ 74/77 風の1号 ハムカツマン逆
def e_hamukatsu(s, i, u):
    """出た時、自分の山札の上から3枚を表向きにする。その中からパワー6000以上のクリーチャーを1体
    手札に加え、残りを好きな順序で山札の下に置く"""
    k = s.dig(i, 3, lambda x: BY_KEY[x].kind == "C" and BY_KEY[x].power >= 6000, "bottom")
    if k is not None:
        s.ev(f"　ハムカツマン逆：{BY_KEY[k].name} を手札に加えた")


add("k29_hamukatsu", "風の1号 ハムカツマン逆", 4, "N", power=4000, mach=True,
    races=("megacommanddragon", "command", "revolution", "hamukatsu"), pri=6, roles="draw atk",
    enter=e_hamukatsu, changex=lambda s, i, u: "N" in u.c.civ,
    playrule=_change_rule("N", "自然"),
    text="革命チェンジ：自然のクリーチャー。マッハファイター。"
         "出た時、自分の山札の上から3枚を表向きにする。その中からパワー6000以上のクリーチャーを1体手札に加え、"
         "残りを好きな順序で山札の下に置く",
    source=SRC["k29_hamukatsu"])
