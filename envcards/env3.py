"""青黒デスパペット（遊々亭のデッキ紹介記事の採用リストから）

  ツインパクト、マッドネス、ドリーム・クリーチャー、シールドを山札の下に送るブレイクの置き換えなど、
  カードに書かれている効果をそのまま実装した。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all
from envcards.env0 import discard_choice, lock_until_my_turn, owner_of

W = "https://dmwiki.net/"
PUP = ("puppet",)


def _is_pup(c):
    return "puppet" in c.races


# ================================================================ ジェニー系
def e_jenny(s, i, u):
    """出た時、自分でこのクリーチャーを破壊してもよい。破壊したら相手の手札をランダムに1枚捨てさせる"""
    if not s.P[1 - i].hand or u not in s.P[i].board:
        return
    s.leave(i, u, "grave", destroy=True)
    s.discard_random(1 - i)


add("n_jenny", "特攻人形ジェニー", 2, "D", power=1000, races=PUP, pri=4, roles="dis", enter=e_jenny,
    text="出た時、自分でこのクリーチャーを破壊してもよい。そうしたら、相手の手札を1枚ランダムに捨てさせる",
    source=W + "《特攻人形ジェニー》")


def e_mary(s, i, u):
    """出た時、山札の上2枚を墓地に置いてもよい。その後、墓地からコスト4以下のデスパペットを1つ出してもよい"""
    s.mill(i, 2)
    s.revive(i, lambda c: c.cost <= 4 and _is_pup(c))


def w_mary_leave(s, i, u, dest, destroy_):
    """自分のデスパペットが離れた時、1枚引いてもよい。その後、相手は自分の手札を1枚選んで捨てる"""
    if not _is_pup(u.c) or not (u.k == "n_mary" or s.has(i, "n_mary")):
        return                      # メアリー自身が離れた時も誘発する（離れるできごとを見ている）
    s.draw(i)
    discard_choice(s, 1 - i)


add("n_mary", "龍后人形メアリー・ジェニー", 5, "WD", power=6000, brk=2, jd=True, races=("puppet", "dragon"), pri=8,
    roles="blk draw dis", enter=e_mary, leavewatch=w_mary_leave,
    blockok=lambda s, u: _is_pup(u.c) and s.has(owner_of(s, u), "n_mary"),
    text="ジャストダイバー、W・ブレイカー。自分のデスパペットすべてにブロッカーを与える。"
         "出た時、山札の上2枚を墓地に置いてもよく、その後、自分の墓地からコスト4以下のデスパペットを1つ出してもよい。"
         "自分のデスパペットが離れた時、1枚引いてもよく、その後、相手は自分の手札を1枚選んで捨てる",
    source=W + "《龍后人形メアリー・ジェニー》")


def e_jenimoon(s, i, u):
    discard_choice(s, 1 - i)


def sp_jenimoon(s, i):
    t = s.target(i)
    if t is not None:
        destroy(s, i, t)


add("n_jenimoon", "弾手人形ジェニムーン / 月のダンスを見においで", 2, "D", power=1000, blocker=True, noatk=True,
    races=PUP, twin=(5, "D", True), pri=5, roles="blk dis rem trg", enter=e_jenimoon, spell=sp_jenimoon, nograve=True,
    text="クリーチャー側：ブロッカー。攻撃できない。出た時、相手は自分の手札を1枚選んで捨てる。"
         "呪文側《月のダンスを見においで》（コスト5・S・トリガー）：相手のクリーチャー1体を破壊する。"
         "唱えた後、この呪文は墓地ではなく自分の超次元ゾーンに置かれる",
    source=W + "《弾手人形ジェニムーン／月のダンスを見においで》")


def sp_ochakai(s, i):
    """3枚引き、手札を3枚捨て、その後コスト3以下のデスパペットを3つまで墓地から出す"""
    p = s.P[i]
    s.draw(i, 3)
    for _ in range(3):
        if not p.hand:
            break
        k = min(p.hand, key=E.PRI.get)
        s.discard(i, k)
    for _ in range(3):
        if s.revive(i, lambda c: c.cost <= 3 and _is_pup(c)) is None:
            break


add("n_ochakai", "メアリー・ジェニーのお茶会", 5, "WD", kind="S", trig=True, pri=7, roles="draw rem dis trg",
    spell=sp_ochakai,
    text="S・トリガー。3枚引く。その後、自分の手札を3枚捨てる。その後、自分の墓地からコスト3以下のデスパペットを"
         "3つまで出す（引いてから捨てるので、引いたデスパペットを墓地に落として出すことができる）",
    source=W + "《メアリー・ジェニーのお茶会》")


def sc_petpuppet(s, i, k):
    """G・ゼロ：自分のデスパペットがあれば0マナ"""
    return 0 if any(_is_pup(u.c) for u in s.P[i].board) else 3


add("n_petpuppet", "人形の裏技ペット・パペット", 3, "D", kind="S", pri=4, roles="dis", spell=lambda s, i: s.discard_random(1 - i),
    spcost=sc_petpuppet,
    text="G・ゼロ：自分のデスパペットが1つでもあれば、コストを支払わずに唱えてよい。相手の手札を1枚ランダムに捨てさせる",
    source=W + "《人形の裏技ペット・パペット》")


# ================================================================ そのほか
def e_cobra(s, i, u):
    """出た時、山札の上2枚を墓地に置き、墓地からコスト5以下のクリーチャーを1体出す。
    相手のターンに出て、そのターン自分のシールドが2つ以上ブレイクされていなければ自壊する"""
    s.mill(i, 2)
    s.revive(i, lambda c: c.cost <= 5)
    if s.tp != i and s.P[i].brk_t < 2 and u in s.P[i].board:
        s.ev("　c0br4：シールドが2つ以上ブレイクされていないので自壊")
        s.leave(i, u, "grave", destroy=True)


add("n_cobra", "忍蛇の聖沌 c0br4", 6, "D", power=5000, trig=True, blocker=True, races=("mechadelstella", "shinobi"),
    pri=8, roles="blk trg", enter=e_cobra,
    text="S・トリガー、ブロッカー。出た時、自分の山札の上から2枚を墓地に置き、その後、自分の墓地からコスト5以下の"
         "クリーチャーを1体出す。相手のターンに出た時、そのターンに自分のシールドが2つ以上ブレイクされていなければ、"
         "このクリーチャーを破壊する", source=W + "《忍蛇の聖沌 c0br4》")


def e_bolrev(s, i, u):
    """出た時、次の自分のターンのはじめまで、相手のクリーチャーはすべて攻撃もブロックもできない"""
    for z in s.P[1 - i].board:
        if z.c.kind == "C":
            lock_until_my_turn(s, i, z)
    s.ev("　相手のクリーチャーはすべて攻撃もブロックもできない")


def rep_bolrev(s, ai, di, broken):
    """ブレイクしたシールドを手札に加えるかわりに山札の下へ。その後、各プレイヤーがその枚数引く"""
    if s.atk is None or s.atk.k != "n_bolrev":
        return False
    d = s.P[di]
    for k, _up in broken:
        d.deck.insert(0, k)
    n = len(broken)
    s.ev(f"　ブレイクしたシールド{n}枚を山札の下へ。各プレイヤーが{n}枚引く")
    s.draw(ai, n)
    s.draw(di, n)
    return True


def fx_dream(s, owner, u, i, k, src, summon, res):
    """ドリーム・クリーチャー：同じ名前のものは2つ目は出られない"""
    if i == owner and k == u.k:
        return "no"
    return res


add("n_bolrev", "切札竜 ボルメテウス・リバース・ドラゴン", 5, "W", power=7000, brk=2, blocker=True, zrush=True,
    races=("exdreamer", "armoreddragon", "dragon", "hyperbeast"), pri=10, roles="blk fin dis draw",
    enter=e_bolrev, breakrep=rep_bolrev, fatex=fx_dream,
    brkx=lambda s, i, u: 3 if u.hyper else None,
    tgtlock=lambda s, by, u: u.k == "n_bolrev" and by != owner_of(s, u),
    unbok=lambda s, i, u: u.k == "n_bolrev",
    text="ブロッカー、ブロックされない、アンタッチャブル（相手に選ばれない）、W・ブレイカー。"
         "Zラッシュ：自分のシールドが離れたら、次の自分のターンのはじめまでハイパーモード（パワー12000・T・ブレイカー）。"
         "出た時、次の自分のターンのはじめまで、相手のクリーチャーはすべて攻撃もブロックもできない。"
         "シールドをブレイクする時、そのシールドを持ち主の手札に加えるかわりに山札の下に置き、各プレイヤーはその枚数引く。"
         "ドリーム・クリーチャー（同じ名前のものは場に1体まで。デッキに入れる枚数の制限はない）",
    source=W + "《切札竜 ボルメテウス・リバース・ドラゴン》")
E.HYPER_POW["n_bolrev"] = 5000


def dx_baiken(s, i, k):
    """マッドネス：相手のターンに手札から捨てられる時、墓地に置くかわりに場に出す"""
    if s.tp == i or k not in s.P[i].hand:
        return False
    if s.fate(i, k, "hand", False) != "ok":
        return False
    s.P[i].hand.remove(k)
    s.ev("　マッドネス：斬隠蒼頭龍バイケンが出る")
    u = s.enter(i, k, "hand", False)
    if u is not None:
        t = s.target(i)
        if t is not None:
            move(s, i, t, "hand")
    return True


add("n_baiken", "斬隠蒼頭龍バイケン", 6, "W", power=6000, brk=2, races=("poseidia", "dragon", "shinobi"), pri=8,
    roles="rem atk", discardx=dx_baiken,
    text="W・ブレイカー。マッドネス：相手のターン中にこのカードが自分の手札から捨てられる時、墓地に置くかわりに"
         "バトルゾーンに出してよい。そうしたら、クリーチャー1体を選び、持ち主の手札に戻してもよい",
    note="「自分のシノビがニンジャ・ストライクを使った時に1枚引く」能力は実装していない。"
         "エンジンの REACT（ニンジャ・ストライク）はカードごとの dict で、"
         "「ニンジャ能力が使われた」ことを外から見る差し込み口がないため"
         "（ほかの担当のモジュールの REACT を包むと、モジュールの読み込み順に結果が左右される）。"
         "あわせて、この札束にはニンジャ・ストライクを持つシノビがないので、働く機会もない", status="partial",
    source=W + "《斬隠蒼頭龍バイケン》")
