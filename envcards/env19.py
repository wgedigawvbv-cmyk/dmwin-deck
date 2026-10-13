"""担当19：【赤零ジョーカーズ】（火＋ゼロ文明のジョーカーズ）の40枚ぶん・11種

出典（デッキリスト）
  遊々亭のデッキ紹介記事「【デッキ紹介】旅路ジョーカーズ」（sinigami、2026年6月2日）
  https://yuyu-tei.jp/show/dm/content/26760
  記事は「旅路ジョーカーズ」と呼んでいるが、文明は火12枚＋ゼロ文明（無色）28枚で、
  ネットで【赤零ジョーカーズ】と呼ばれている型（dmwiki の【赤零富士山首魁ジョラゴン】の説明にある
  「オンラインでは【赤零ジョーカーズ】とも呼ばれる」型）と同じ組み方。
  公式テキストカバレージの入賞リスト（超CSⅨ新潟・福岡、DMGP2026-1st 両日、ローグデッキピックアップまで）を
  見たがジョーカーズのリストは1つも載っていなかったので、主流リストとしてこの記事を使った。

このデッキの仕組み
  ・ゼロ文明（無色）のカードはマナに置いても色を出さない。火の3種（ジョギメラゴン＆メラビート／
    メラベンチャー・ザ・ジョニー／アイアン・マンハッタン）を使うには、火のカードをマナに置く必要がある。
  ・「ジョーカーズを手札から捨てた時、その『このクリーチャーが出た時』の能力を1つ使う」
    （ジョット・ガン・ジョラゴンのジョラゴン・ビッグ1、ジョギラゴン＆ジョニーの出た時）が、
    この札束の中心。捨てた札はバトルゾーンにいないので、「このクリーチャー」を指す部分は何も起こらない。
  ・「バトルゾーンとマナゾーンのジョーカーズの合計」が、コスト軽減（ジョギメラゴン）・
    ドロー（ガヨウ神）・G・ゼロ（勝熱と弾丸と自由の決断）・ブロッカー全破壊（メラベンチャー）の条件。

調べ方
  11種すべてについて dmwiki.net のカードページを、別の質問で2回ずつ読み、
  コスト・文明・カードの種類・種族・パワー・ブレイク数・能力の本文が2回とも一致することを確かめた
  （`curl` は 403 で使えないので WebFetch、3〜5秒間隔）。
  《ジョット・ガン・ジョラゴン》のカード枠には「※殿堂入り」の表記があり、記事のリストも1枚。
  《ガヨウ神》は2019年に制限され2022年7月に解除されたので、今は4枚使える（枠に制限の表記なし）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, opp_all

W = "https://dmwiki.net/"
SRC = {
    "ja_yattare": W + "《ヤッタレマン》",
    "ja_pokuchin": W + "《ポクチンちん》",
    "ja_gayou": W + "《ガヨウ神》",
    "ja_jogiragon": W + "《ジョギラゴン＆ジョニー 〜Jの旅路〜》",
    "ja_jogimeragon": W + "《ジョギメラゴン＆メラビート 〜Jの焔舞〜》",
    "ja_meraventure": W + "《メラベンチャー・ザ・ジョニー》",
    "ja_manhattan": W + "《アイアン・マンハッタン》",
    "ja_joragon": W + "《ジョット・ガン・ジョラゴン》",
    "ja_jojojo": W + "《ジョジョジョ・ジョーカーズ》",
    "ja_ketsudan": W + "《勝熱と弾丸と自由の決断》",
    "ja_slotton": W + "《キング・ザ・スロットン7／7777777》",
}
MAXCIP = 6          # 「出た時の能力を使う」連鎖の深さの上限（手順が終わらなくなるのを防ぐ安全装置）


# ================================================================ 共通の道具
def _jok(k):
    """そのカードがジョーカーズか"""
    return "jokers" in BY_KEY[k].races


def jcount(s, i):
    """自分のバトルゾーンとマナゾーンにあるジョーカーズの合計（各カードの条件に使う）"""
    n = sum(1 for u in s.P[i].board if "jokers" in u.c.races)
    return n + sum(1 for k in s.P[i].mana if _jok(k))


def _plain_cre(k):
    """進化元なしで出せるクリーチャーか"""
    c = BY_KEY[k]
    return c.kind == "C" and not (c.evo and not c.neo)


def _cip_ok(k):
    """「このクリーチャーが出た時」で始まる能力を持つジョーカーズ・クリーチャーか"""
    c = BY_KEY[k]
    return c.kind == "C" and "jokers" in c.races and E.ENTER.get(k) is not None


def use_cip(s, i, k):
    """墓地に置いたジョーカーズ・クリーチャーの「このクリーチャーが出た時」の能力を1つ使う。
    カードはバトルゾーンにいないので、「このクリーチャー」を指す部分は何も起こらない"""
    if s.over or not _cip_ok(k):
        return False
    p = s.P[i]
    d = p.x.get("ja_cip", 0)
    if d >= MAXCIP:
        return False
    p.x["ja_cip"] = d + 1
    u = E.U(k)
    u.sick = False
    s.ev(f"　ジョーカーズの「出た時」の能力を使う：{BY_KEY[k].name}")
    E.ENTER[k](s, i, u)
    s.P[i].x["ja_cip"] = d
    return True


def pick_discard(s, i):
    """手札から1枚捨てる時に選ぶカード。「出た時」の能力を使えるジョーカーズ・クリーチャーがあれば、
    その中でいちばん重要度（PRI）の高いものを選ぶ（踏み倒す先はPRIの高いものという全デッキ共通の決まり）。
    なければいちばん重要度の低いカードを捨てる"""
    p = s.P[i]
    if not p.hand:
        return None
    cands = [k for k in p.hand if _cip_ok(k)]
    if cands:
        return max(cands, key=E.PRI.get)
    return min(p.hand, key=E.PRI.get)


def _grant_atkp(s, u):
    """「このターン、相手プレイヤーを攻撃できる」を与える
    （もともとプレイヤーを攻撃できないカードにだけ意味がある文なので、そのカードにだけ印を付ける）"""
    if u is not None and u.c.noatkp and not u.c.noatk:
        u.x["ja_atkp"] = s.turn


def _ja_atkign(s, i, u):
    return u.x.get("ja_atkp") == s.turn


def _ja_noabi(s, i, u):
    """《勝熱と弾丸と自由の決断》で「能力をすべて無視する」と選ばれているか

    攻撃を宣言しているクリーチャーだけ外している。engine3.attack が
    `if ABILOCK and not s.abi(i, u): return` で攻撃そのもの（ブロックもシールドのブレイクも）を
    打ち切ってしまうためで、この呪文は自分のターンにしか唱えられない（S・トリガーを持たない）ので、
    印の付いた相手のクリーチャーがそのターンに攻撃することはない。"""
    return u.x.get("ja_noabi") == s.turn and s.atk is not u


def _is_blocker(s, u):
    """「ブロッカー」を持つクリーチャーか（タップしているかどうかは見ない）"""
    if u.c.kind != "C":
        return False
    return (u.c.blocker or (u.k == "chakra" and u.hyper)
            or bool(E.BLOCKOK and any(f(s, u) for f in E.BLOCKOK)))


# ================================================================ ヤッタレマン
def ca_yattare(s, i, k, cur):
    """自分のジョーカーズ・クリーチャーの召喚コストを1少なくする（0以下にならない）"""
    n = sum(1 for u in s.P[i].board if u.k == "ja_yattare")
    if not n or cur <= 1:
        return cur
    c = BY_KEY[k]
    if c.kind != "C" or "jokers" not in c.races:
        return cur
    return max(1, cur - n)


add("ja_yattare", "ヤッタレマン", 2, "", power=2000, races=("jokers",), pri=4, roles="acc",
    costaura=ca_yattare,
    text="自分のジョーカーズ・クリーチャーの召喚コストを1少なくする。ただし、コストは0以下にならない",
    source=SRC["ja_yattare"])


# ================================================================ ポクチンちん
def e_pokuchin(s, i, u):
    """出た時、プレイヤーを1人選ぶ。そのプレイヤーは自身の墓地をすべて山札に加えてシャッフルする。
    選び方：墓地の重要度の合計が大きい方（相手の墓地が自分より重ければ相手、そうでなければ自分）"""
    mine = sum(E.PRI[k] for k in s.P[i].grave)
    theirs = sum(E.PRI[k] for k in s.P[1 - i].grave)
    if not mine and not theirs:
        return
    j = 1 - i if theirs > mine else i
    p = s.P[j]
    n = len(p.grave)
    p.deck.extend(p.grave)
    p.grave = []
    s.rng.shuffle(p.deck)
    s.ev(f"　ポクチンちん：プレイヤー{j}の墓地{n}枚を山札に加えてシャッフル")


def w_pokuchin(s, i, u):
    """相手のターン中に、相手がコストを支払わずにクリーチャーを出した時、相手はそれを山札の下に置く"""
    if u.c.kind != "C" or s.tp != i or u.x.get("summoned"):
        return
    if not s.has(1 - i, "ja_pokuchin") or u not in s.P[i].board:
        return
    s.ev(f"　ポクチンちん：コストを支払わずに出た {u.c.name} を山札の下へ")
    s.leave(i, u, "deck")


add("ja_pokuchin", "ポクチンちん", 3, "", power=3000, races=("jokers",), pri=6, roles="dis rem",
    enter=e_pokuchin, enterwatch=w_pokuchin,
    text="出た時、プレイヤーを1人選ぶ（墓地の重要度の合計が大きい方）。そのプレイヤーは自身の墓地にあるカードを"
         "すべて山札に加えてシャッフルする。"
         "相手のターン中に、相手がコストを支払わずにクリーチャーを出した時、相手はそれを山札の下に置く"
         "（dmwiki のカードページで、2つめは「出る時」の置き換えではなく「出した時」の誘発能力だと確かめた。"
         "だから、ただで出たクリーチャーの「出た時」の能力は先に働くのが正しい）",
    source=SRC["ja_pokuchin"])


# ================================================================ ガヨウ神
def e_gayou(s, i, u):
    """出た時、バトルゾーンかマナゾーンに自分のジョーカーズが合計5枚以上あれば2枚引く。
    その後、ジョーカーズを1枚手札から捨ててもよく、そうしたら2枚引く"""
    if jcount(s, i) < 5:
        return
    s.draw(i, 2)
    if s.over:
        return
    p = s.P[i]
    cands = [k for k in p.hand if _jok(k)]
    if not cands:
        return
    k = min(cands, key=E.PRI.get)
    if k not in p.hand:
        return
    s.discard(i, k)
    s.draw(i, 2)


add("ja_gayou", "ガヨウ神", 5, "", power=4000, races=("jokers", "specials"), pri=6, roles="draw",
    enter=e_gayou,
    text="出た時、バトルゾーンまたはマナゾーンに自分のジョーカーズが合計5枚以上あれば、カードを2枚引く。"
         "その後、ジョーカーズ1枚（重要度のいちばん低いもの）を自分の手札から捨ててもよい。そうしたら、カードを2枚引く",
    note="2019年に制限され2022年7月に解除された札なので、今は4枚使える",
    source=SRC["ja_gayou"])


# ================================================================ ジョギラゴン＆ジョニー 〜Jの旅路〜
def cx_jogiragon(s, i, au):
    """革命チェンジ：コスト5以上のジョーカーズ"""
    return au.c.kind == "C" and "jokers" in au.c.races and au.c.cost >= 5


def e_jogiragon(s, i, u):
    """出た時、1枚引き、その後、手札を1枚捨てる。捨てたカードがジョーカーズなら、
    その「このクリーチャーが出た時」で始まる能力を1つ使ってもよい"""
    s.draw(i, 1)
    if s.over:
        return
    p = s.P[i]
    k = pick_discard(s, i)
    if k is None or k not in p.hand:
        return
    s.discard(i, k)
    if _jok(k):
        use_cip(s, i, k)


def sl_jogiragon(s, i, cost):
    """相手は、自身のターンに1枚しか呪文を唱えられない"""
    return s.tp == i and s.P[i].spl >= 1 and s.has(1 - i, "ja_jogiragon")


def pr_jogiragon(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and "jokers" in BY_KEY[kk].races and BY_KEY[kk].cost >= 5)
    return None if n >= 3 else "革命チェンジの元（コスト5以上のジョーカーズ）が3体いない"


add("ja_jogiragon", "ジョギラゴン＆ジョニー ～Jの旅路～", 8, "", power=10000, brk=2,
    races=("jokers", "dragon"), pri=11, roles="draw dis atk fin",
    enter=e_jogiragon, changex=cx_jogiragon, spelllock=sl_jogiragon, playrule=pr_jogiragon,
    text="革命チェンジ：コスト5以上のジョーカーズ（自分のコスト5以上のジョーカーズが攻撃する時、"
         "そのクリーチャーと手札のこのクリーチャーを入れ替えてもよい）。W・ブレイカー。"
         "出た時、カードを1枚引き、その後、自分の手札を1枚捨てる（「出た時」の能力を使えるジョーカーズ・"
         "クリーチャーがあれば、その中でいちばん重要度の高いものを捨てる）。こうして捨てたカードがジョーカーズなら、"
         "そのカードの「このクリーチャーが出た時」で始まる能力を1つ使ってもよい。"
         "相手は、自身のターンに1枚しか呪文を唱えられない",
    source=SRC["ja_jogiragon"])


# ================================================================ ジョギメラゴン＆メラビート 〜Jの焔舞〜
def cx_jogimeragon(s, i, av):
    """自分のジョーカーズ（バトルゾーン＋マナゾーン）が合計4つ以上なら召喚コストを3少なくする"""
    return 4 if jcount(s, i) >= 4 else 7


def e_jogimeragon(s, i, u):
    """出た時、山札の上から4枚を見て、ジョーカーズ・カード1枚を手札に加えてもよい。残りは山札の下へ"""
    s.dig(i, 4, _jok, "bottom")


add("ja_jogimeragon", "ジョギメラゴン＆メラビート ～Jの焔舞～", 7, "F", power=10000, brk=2, sa=True, gs=True,
    races=("jokers", "dragon"), pri=10, roles="atk fin draw trg",
    enter=e_jogimeragon, costx=cx_jogimeragon,
    text="G・ストライク。自分の、バトルゾーンのジョーカーズとマナゾーンにあるジョーカーズ・カードが合計4つ以上なら、"
         "このクリーチャーの召喚コストを3少なくする。スピードアタッカー。W・ブレイカー。"
         "出た時、自分の山札の上から4枚を見る。その中からジョーカーズ・カードを1枚（重要度のいちばん高いもの）"
         "手札に加えてもよい。残りを山札の下に置く",
    note="「このクリーチャーの攻撃先は変更されない」は未実装。エンジンのガードマン（GUARD）の差し込み口は"
         "攻撃を受ける側だけが登録するもので、攻撃している側から「変更させない」と言う差し込み口（NOSWAPATK）が"
         "ないため。ガードマンを持つカード（コレンココ・タイシ、トレス、ワカアプルなど）に攻撃先を変えられてしまう",
    status="partial", source=SRC["ja_jogimeragon"])


# ================================================================ メラベンチャー・ザ・ジョニー
def e_meraventure(s, i, u):
    """出た時、ジョーカーズ・クリーチャーを2体まで手札から出し、それらにSAを与える。
    このターンの終わりに、それらを山札の下に置き、1体につき1枚引く"""
    p = s.P[i]
    for _ in range(2):
        if s.over:
            return
        cands = [k for k in p.hand if _plain_cre(k) and _jok(k)]
        if not cands:
            return
        k = max(cands, key=E.PRI.get)
        if s.fate(i, k, "hand", False) != "ok" or k not in p.hand:
            return
        p.hand.remove(k)
        z = s.enter(i, k, "hand", False, sa=True)
        if z is None:
            return
        z.eot = True
        z.x["ja_mera_eot"] = True


def te_meraventure(s, i, u):
    """このターンの終わりに山札の下に置くクリーチャー1体につき、カードを1枚引く
    （山札の下に置くのはエンジンの eot の仕組みが、このあと続けて行う）"""
    if not u.eot or not u.x.pop("ja_mera_eot", False):
        return
    s.draw(i, 1)


def a_meraventure(s, i, u):
    """攻撃する時、自分のジョーカーズが合計7つ以上なら、相手のブロッカーをすべて破壊する"""
    if jcount(s, i) < 7:
        return
    for z in opp_all(s, i, lambda x: _is_blocker(s, x)):
        if z in s.P[1 - i].board:
            s.ev(f"　メラベンチャー：相手のブロッカー {z.c.name} を破壊")
            s.leave(1 - i, z, "grave", by_opp=True, destroy=True)


def pr_meraventure(deck, k):
    n = sum(v for kk, v in deck.items() if kk != k and _plain_cre(kk) and "jokers" in BY_KEY[kk].races)
    return None if n >= 4 else "進化元（ジョーカーズ・クリーチャー）が4体いない"


add("ja_meraventure", "メラベンチャー・ザ・ジョニー", 7, "F", power=10000, brk=2, gs=True,
    evo="jokers", races=("jokers",), pri=11, roles="atk fin rem trg",
    enter=e_meraventure, attack=a_meraventure, tendall=te_meraventure,
    evox=lambda s, i, u: u.c.kind == "C" and "jokers" in u.c.races, playrule=pr_meraventure,
    text="G・ストライク。進化：ジョーカーズ・クリーチャー1体の上に置く。W・ブレイカー。"
         "出た時、ジョーカーズ・クリーチャーを2体まで自分の手札から出し（重要度のいちばん高いものから）、"
         "それらに「スピードアタッカー」を与える。このターンの終わりに、それらを山札の下に置き、"
         "こうして下に置いたクリーチャー1体につき、カードを1枚引く。"
         "このクリーチャーが攻撃する時、自分の、バトルゾーンのジョーカーズとマナゾーンにあるジョーカーズ・カードが"
         "合計7つ以上なら、相手の「ブロッカー」を持つクリーチャーをすべて破壊する",
    note="ブロッカー全破壊は、エンジン共通の決まりでジャストダイバー中のクリーチャーを除く"
         "（このシミュレーターは全体除去でもジャストダイバーを守る）",
    source=SRC["ja_meraventure"])


# ================================================================ アイアン・マンハッタン
def cx_manhattan(s, i, av):
    """J・O・E 2：9マナ払えない時だけ、召喚コストを2少なくする"""
    return 9 if _ja_yred(s, i, 9) <= av else 7


def px_manhattan(s, i, k, n):
    """J・O・E 2を使ったかどうかを、出た時の処理に伝える"""
    s.P[i].x["ja_joe"] = s.turn if n <= 7 else -1


def e_manhattan(s, i, u):
    """J・O・E 2。出た時、相手のシールドを2つ残してあとをすべてブレイクし、
    その後、自分の手札を1枚捨ててもよく、そうしたら次のターン、相手は2体以上クリーチャーを出せない"""
    p = s.P[i]
    o = s.P[1 - i]
    joe = p.x.pop("ja_joe", -1)
    if u.x.get("summoned") and joe == s.turn:
        u.eot = True
        u.x["ja_joe"] = True
        s.ev("　J・O・E 2：このターンの終わりに山札の下へ")
    n = len(o.sh) - 2
    if n > 0:
        s.ev(f"　アイアン・マンハッタン：相手のシールドを2つ残して{n}つブレイク")
        s.break_sh(i, n)
    if s.over:
        return
    if p.hand:
        s.discard(i, min(p.hand, key=E.PRI.get))
        o.x["ja_mh_lim"] = s.turn + 1
        s.ev("　アイアン・マンハッタン：次のターン、相手は2体以上クリーチャーを出せない")


def te_manhattan(s, i, u):
    """J・O・E：山札の下に置いたら、カードを1枚引く（下に置くのはエンジンの eot の仕組み）"""
    if not u.eot or not u.x.pop("ja_joe", False):
        return
    s.draw(i, 1)


def w_manhattan_lim(s, i, u):
    """アイアン・マンハッタンの能力：このターン、相手（＝i）は2体以上クリーチャーを出せない"""
    p = s.P[i]
    if u.c.kind != "C" or s.tp != i or p.x.get("ja_mh_lim") != s.turn or p.ent < 2:
        return
    if u not in p.board:
        return
    s.ev(f"　アイアン・マンハッタンの効果：2体目の {u.c.name} は出していられず山札の下へ")
    s.leave(i, u, "deck")


add("ja_manhattan", "アイアン・マンハッタン", 9, "F", power=8000, brk=2, sa=True,
    races=("jokers",), pri=11, roles="atk fin dis",
    enter=e_manhattan, costx=cx_manhattan, payx=px_manhattan, tendall=te_manhattan,
    enterwatch=w_manhattan_lim,
    text="J・O・E 2（このクリーチャーの召喚コストを2少なくしてもよい。そうしたら、このターンの終わりに、"
         "これを自分の山札の下に置く。下に置いたら、カードを1枚引く。9マナ払えない時だけ使う）。"
         "スピードアタッカー。W・ブレイカー。"
         "出た時、相手のシールドを2つ選ぶ。このクリーチャーは、相手のそれ以外のシールドをすべてブレイクする。"
         "その後、自分の手札を1枚（重要度のいちばん低いもの）捨ててもよい。そうしたら、"
         "次のターン、相手は2体以上クリーチャーを出せない",
    note="「次のターン、相手は2体以上クリーチャーを出せない」は、プレイヤーごとの「このターン出せる数の上限」を"
         "持つ仕組み（ENTLIM）がエンジンになく（fate の LIMIT2 などは相手のバトルゾーンのカードから数えるので、"
         "場を離れる札では表せない）、アイアン・マンハッタン自身は J・O・E でターンの終わりに山札の下へ"
         "行ってしまうため、「2体目以降は出た直後に山札の下に置く」という形で近似した"
         "（出た時の能力は使われてしまう）",
    status="partial", source=SRC["ja_manhattan"])


# ================================================================ ジョット・ガン・ジョラゴン
def _joragon_back(s, i):
    """コストを下げるために手札に戻せる自分のジョーカーズ（失うのが安い順）"""
    return sorted([u for u in s.P[i].board if "jokers" in u.c.races and u.c.kind in ("C", "T")],
                  key=lambda u: s.val(u))


def _ja_yred(s, i, n):
    """ヤッタレマンによる軽減（ccost は COSTX のあとに COSTAURA をかけるので、同じ計算をしておく）"""
    y = sum(1 for u in s.P[i].board if u.k == "ja_yattare")
    return max(1, n - y) if y and n > 1 else n


def _joragon_cost(s, i, av):
    """(払うコスト, 手札に戻すジョーカーズ)。払える分だけ戻す"""
    cands = _joragon_back(s, i)
    for t in range(len(cands) + 1):
        n = max(0, 7 - t)
        if _ja_yred(s, i, n) <= av:
            return n, cands[:t]
    return max(0, 7 - len(cands)), cands


def cx_joragon(s, i, av):
    return _joragon_cost(s, i, av)[0]


def px_joragon(s, i, k, n):
    p = s.P[i]
    for u in _joragon_cost(s, i, len(p.mana) - p.mused)[1]:
        if u in p.board:
            s.ev(f"　ジョラゴン：{u.c.name} を手札に戻して召喚コストを1少なくする")
            s.leave(i, u, "hand")


def a_joragon(s, i, u):
    """攻撃する時、カードを1枚引き、その後、自分の手札を1枚捨てる
    （捨てたジョーカーズは、ジョラゴン・ビッグ1＝w_joragon_big1 が拾う）"""
    s.draw(i, 1)
    if s.over:
        return
    p = s.P[i]
    k = pick_discard(s, i)
    if k is not None and k in p.hand:
        s.discard(i, k)


def w_joragon_big1(s, i, k):
    """ジョラゴン・ビッグ1：ジョーカーズを自分の手札から捨てた時、
    その「このクリーチャーが出た時」で始まる能力を1つ使ってもよい"""
    if not s.has(i, "ja_joragon") or not _jok(k):
        return
    use_cip(s, i, k)


add("ja_joragon", "ジョット・ガン・ジョラゴン", 7, "", power=11000, brk=2, sa=True,
    races=("masterdragon", "dragon", "jokers"), pri=12, roles="atk fin draw",
    attack=a_joragon, costx=cx_joragon, payx=px_joragon, discardwatch=w_joragon_big1,
    text="このクリーチャーを召喚する時、ジョーカーズを好きな数バトルゾーンから自分の手札に戻してもよい"
         "（マナが足りる分だけ、失うのが安いものから戻す）。こうして戻したジョーカーズ1枚につき、"
         "このクリーチャーの召喚コストを1少なくする。スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが攻撃する時、カードを1枚引き、その後、自分の手札を1枚捨てる。"
         "ジョラゴン・ビッグ1：ジョーカーズを自分の手札から捨てた時、そのカードの"
         "「このクリーチャーが出た時」で始まる能力を1つ使ってもよい",
    note="殿堂入り（デッキに1枚まで）。能力の連鎖は深さ6までに止めている（手順が終わらなくなるのを防ぐため）",
    source=SRC["ja_joragon"])


# ================================================================ ジョジョジョ・ジョーカーズ
def sp_jojojo(s, i):
    """山札の上から4枚を見て、ジョーカーズ・クリーチャー1体を手札に加えてもよい。残りは山札の下へ"""
    s.dig(i, 4, lambda k: BY_KEY[k].kind == "C" and _jok(k), "bottom")


add("ja_jojojo", "ジョジョジョ・ジョーカーズ", 1, "", kind="S", races=("jokers",), pri=3, roles="draw",
    spell=sp_jojojo,
    text="自分の山札の上から4枚を見る。その中からジョーカーズ・クリーチャーを1体（重要度のいちばん高いもの）"
         "相手に見せてから手札に加えてもよい。残りを山札の下に置く",
    source=SRC["ja_jojojo"])


# ================================================================ 勝熱と弾丸と自由の決断
def spc_ketsudan(s, i, k):
    """G・ゼロ：自分のジョーカーズが合計7枚以上なら、コストを支払わずに唱えてもよい"""
    return 0 if jcount(s, i) >= 7 else 4


def _ketsudan_one(s, i):
    """3つのモードから1つ。効きめのあるものを上から順に選ぶ（全デッキ共通の機械的な決まり）"""
    t = s.target(i, lambda x: x.c.cost <= 3, kinds="CTX")
    if t is not None:
        s.ev(f"　決断：{t.c.name}（コスト3以下）を持ち主の山札の下へ")
        s.leave(1 - i, t, "deck", by_opp=True)
        return
    t = s.target(i, lambda x: _is_blocker(s, x) or x.jd)
    if t is None:
        mine = [u for u in s.P[i].board if u.c.kind == "C" and u.c.noatkp and not u.c.noatk]
        if mine:
            z = max(mine, key=lambda u: E.PRI[u.k])
            _grant_atkp(s, z)
            s.ev(f"　決断：{z.c.name} はこのターン相手プレイヤーを攻撃できる")
            return
        t = s.target(i)
    if t is None:
        return
    t.jd = False
    t.x["ja_noabi"] = s.turn
    s.ev(f"　決断：{t.c.name} の能力をこのターン無視する")


def sp_ketsudan(s, i):
    for _ in range(2):
        if s.over:
            return
        _ketsudan_one(s, i)


add("ja_ketsudan", "勝熱と弾丸と自由の決断", 4, "", kind="S", races=("jokers",), pri=7, roles="rem dis",
    spell=sp_ketsudan, spcost=spc_ketsudan,
    abilock=_ja_noabi, noatkign=_ja_atkign,
    text="G・ゼロ：バトルゾーンまたはマナゾーンに自分のジョーカーズが合計7枚以上あれば、"
         "この呪文をコストを支払わずに唱えてもよい。次の中から2回選ぶ（同じものを選んでもよい）。"
         "▶バトルゾーンにある、コスト3以下のカードを1枚選び、持ち主の山札の下に置く（相手の重要度の高いものから）。"
         "▶このターン、自分のクリーチャー1体は相手プレイヤーを攻撃できる。"
         "▶相手のクリーチャーを1体選ぶ。このターン、そのクリーチャーの能力をすべて無視する"
         "（ABILOCK で、ブロッカー・ジャストダイバー・出た時・ターンの始め終わり・離れた時の誘発が止まる）",
    source=SRC["ja_ketsudan"])


# ================================================================ キング・ザ・スロットン7／7777777
def e_slotton(s, i, u):
    """出た時、山札の上から3枚を表向きにする。すべてジョーカーズなら、その中からクリーチャー1体を出す
    （そのターン、そのクリーチャーは相手プレイヤーを攻撃できる）。残りは山札の下へ"""
    p = s.P[i]
    n = min(3, len(p.deck))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    s.ev("　スロットン7：山札の上から表向きに（" + "／".join(BY_KEY[k].name for k in top) + "）")
    if all(_jok(k) for k in top):
        cre = [k for k in top if _plain_cre(k)]
        if cre:
            k = max(cre, key=E.PRI.get)
            if s.fate(i, k, "deck", False) == "ok":
                top.remove(k)
                _grant_atkp(s, s.enter(i, k, "deck", False))
    for k in top:
        p.deck.insert(0, k)


def sp_slotton(s, i):
    """相手の山札の上から3枚を表向きにし、その中から1枚を選ぶ。選んだカードとコストが同じ相手のクリーチャー
    すべてと、表向きにした3枚を、相手は山札の下に置く"""
    o = s.P[1 - i]
    n = min(3, len(o.deck))
    if n <= 0:
        return
    top = [o.deck.pop() for _ in range(n)]
    best, bv = top[0], -1
    for k in top:
        c = BY_KEY[k].cost
        v = sum(s.val(z) for z in o.board if z.c.kind == "C" and z.c.cost == c)
        if v > bv:
            best, bv = k, v
    cost = BY_KEY[best].cost
    s.ev(f"　7777777：相手の山札の上から{n}枚のうち {BY_KEY[best].name}（コスト{cost}）を選ぶ")
    for k in top:
        o.deck.insert(0, k)
    for z in [z for z in o.board if z.c.kind == "C" and z.c.cost == cost]:
        if z in o.board:
            s.ev(f"　7777777：{z.c.name} を山札の下へ")
            s.leave(1 - i, z, "deck", by_opp=True)


add("ja_slotton", "キング・ザ・スロットン7 / 7777777", 7, "", power=7777, brk=2,
    races=("jokers",), twin=(3, "", True), pri=9, roles="atk fin rem trg",
    enter=e_slotton, spell=sp_slotton,
    text="【クリーチャー側】W・ブレイカー。出た時、自分の山札の上から3枚を表向きにする。それがすべてジョーカーズなら、"
         "その中からクリーチャーを1体（重要度のいちばん高いもの）出す。そのターン、そのクリーチャーは相手プレイヤーを"
         "攻撃できる。残りを自分の山札の下に置く。"
         "【呪文側 7777777（コスト3・S・トリガー）】相手は自身の山札の上から3枚を表向きにし、自分はその中から1枚を"
         "選ぶ（相手のクリーチャーをいちばん多く巻き込めるコストのもの）。その選んだカードとコストが同じ相手の"
         "クリーチャーすべてと、表向きにした3枚を、相手は山札の下に置く",
    source=SRC["ja_slotton"])
