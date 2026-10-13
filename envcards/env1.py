"""7つの実在デッキに1枚だけ入っていたカード（これまで近い働きの札に置き換えていたもの）

  出典はカードごとに source に書いた（デュエル・マスターズWiki のカードページ）。
  「どれを選ぶか」「任意効果を使うか」は、このシミュレーター共通の決まりで機械的に決める。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, best_hand, dig2, destroy, move, worst_hand
from envcards.env0 import he_costx, he_payx, lock_until_my_turn, race_like

W = "https://dmwiki.net/"


# ================================================================ 創世竜ループ
def e_greatblue(s, i, u):
    dig2(s, i, 3, [lambda k: BY_KEY[k].kind == "C", lambda k: BY_KEY[k].kind != "C"])


def w_greatblue(s, i, u):
    """超魂X：下にグレートブルーの海幻があるクリーチャーが攻撃する時、
    手札のコスト4以下のクリーチャーでないカードを1枚ただで実行する"""
    if "n_greatblue" not in u.under:
        return
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "C" or c.cost > 4 or p.ban == c.cost:
            continue
        if c.kind == "S" and not s.spell_ok(i, c.cost):
            continue
        if c.kind == "G" and s.has(1 - i, "fujin"):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　超魂X：手札の {BY_KEY[best].name} をただで")
        s.exec_free(i, best)


add("n_greatblue", "グレートブルーの海幻", 3, "W", kind="T", races=("poseidia", "fusioner"), pri=5, roles="draw",
    enter=e_greatblue, atkwatch=w_greatblue,
    text="シンカライズ（このタマシードを進化元にできる）。出た時、山札の上3枚から、クリーチャー1枚とクリーチャーでないカード1枚までを"
         "手札に加え、残りを山札の下へ。超魂X：このカードがクリーチャーの下にあるなら、その上のクリーチャーは"
         "「攻撃する時、手札のコスト4以下のクリーチャーでないカード1枚をただで使ってよい」を得る",
    source=W + "《グレートブルーの海幻》")
E.SHINKA.add("n_greatblue")


# ================================================================ ドッコイループ
def e_eine(s, i, u):
    t = s.target(i)
    if t is not None:
        move(s, i, t, "hand")


add("n_eine", "爆藍月 Eine k'Reine", 5, "W", power=5000, blocker=True, races=("magic",), pri=6, roles="blk rem",
    enter=e_eine, costx=he_costx("n_eine"), payx=he_payx("n_eine"),
    text="ハイパーエナジー（召喚する時、コストが互いに違う自分のクリーチャーを好きな数タップしてよい。1体につきコスト-2）。"
         "ブロッカー。出た時、相手のクリーチャー1体を手札に戻してもよい",
    source=W + "《爆藍月 Eine k'Reine》")


def sp_siren(s, i):
    """マナから1枚手札に戻し、手札から1枚マナに置く"""
    p = s.P[i]
    if p.mana:
        k = max(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        p.hand.append(k)
    k = worst_hand(s, i)
    if k is not None:
        p.hand.remove(k)
        s.add_mana(i, k)


add("n_siren", "セイレーン・コンチェルト", 1, "W", kind="S", trig=True, pri=3, roles="acc trg",
    spell=sp_siren,
    text="S・トリガー。自分のマナゾーンからカード1枚を手札に戻し、その後、自分の手札から1枚をマナゾーンに置く"
         "（単色ならアンタップして置かれる）",
    source=W + "《セイレーン・コンチェルト》")


def sp_naze(s, i):
    """プレイヤー1人を選び、その墓地を山札の下へ。その後2枚引く"""
    j = i if len(s.P[i].deck) <= 10 or s.gc(1 - i) < 3 else 1 - i
    q = s.P[j]
    if q.grave:
        g = q.grave
        q.grave = []
        s.rng.shuffle(g)
        q.deck[0:0] = g
        s.ev(f"　プレイヤー{j}の墓地{len(g)}枚を山札の下へ")
    s.draw(i, 2)


add("n_naze", "♪なぜ離れ どこへ行くのか 君は今", 3, "W", kind="S", pri=4, roles="draw",
    spell=sp_naze,
    text="プレイヤー1人を選ぶ。そのプレイヤーは自分の墓地をシャッフルして山札の下に置く。その後、自分は2枚引く",
    source=W + "《♪なぜ離れ どこへ行くのか 君は今》")


# ================================================================ ゾロ・ア・スタート
def fx_vegeta(s, owner, u, i, k, src, summon, res):
    """相手のエレメントは、相手の手札以外からは出ない／実行以外では出ない"""
    if i == owner:
        return res
    if src != "hand" or not summon:
        return "no"
    return res


def rep_vegeta(s, i, u, dest, destroy_):
    """自分のクリーチャーが離れる時、かわりに自分のマナ3枚を墓地に置いてもよい"""
    p = s.P[i]
    if u.c.kind != "C" or not s.has(i, "n_vegeta") or len(p.mana) < 3:
        return False
    if u.k == "n_vegeta" and dest == "grave" and len(p.mana) < 4:
        return False
    for _ in range(3):
        k = min(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        s.grave_put(i, k)
    s.ev(f"　ミリオンベジータ：マナ3枚を墓地に置いて {u.c.name} を守る")
    return True


def acts_vegeta(s, i, av, cv):
    """マナゾーンからも召喚できる"""
    p = s.P[i]
    if "n_vegeta" not in p.mana or s.manaexec(i):
        return []
    n = BY_KEY["n_vegeta"].cost
    if n <= av and "N" in cv and s.fate(i, "n_vegeta", "mana", True) == "ok":
        return [("x:vegeta", n)]
    return []


def ap_vegeta(s, a):
    i = s.tp
    if "n_vegeta" not in s.P[i].mana:
        return
    s.P[i].mused += a[1]
    s.take_mana(i, "n_vegeta")
    s.ev(f"マナから召喚：暴龍のT ミリオンベジータ（{a[1]}マナ）")
    s.enter(i, "n_vegeta", "mana", True)


add("n_vegeta", "暴龍のT ミリオンベジータ", 9, "N", power=18000, brk=4, mach=True, manaok=True, pri=11,
    roles="fin atk dis", fatex=fx_vegeta, leaverep=rep_vegeta, freeacts=acts_vegeta,
    actapply={"x:vegeta": ap_vegeta},
    text="Q・ブレイカー、マッハファイター。マナゾーンからも召喚できる。相手のエレメントは、相手の手札以外からは出ず、"
         "実行（召喚・唱える等）以外の方法では出ない。自分のクリーチャーが離れる時、かわりに自分のマナ3枚を墓地に置いてもよい",
    source=W + "《暴龍のT ミリオンベジータ》")


def cx_jushoku(s, i, av):
    """手札とマナの他のカードを1枚選ぶごとにコスト-1（必要な分だけ選ぶ）"""
    p = s.P[i]
    tmax = max(0, len(p.hand) - 1) + len(p.mana)
    need = max(0, 8 - av)
    return max(0, 8 - min(tmax, need))


def pay_jushoku(s, i, k, n):
    """選んだカードを覚えておく（出た時に墓地へ）"""
    p = s.P[i]
    t = 8 - n
    picks = []
    cands = [("hand", x) for x in p.hand if x != "n_jushoku"] + [("mana", x) for x in p.mana]
    cands.sort(key=lambda z: E.PRI[z[1]])
    for z, x in cands[:t]:
        picks.append((z, x))
    p.x["jushoku"] = picks


def e_jushoku(s, i, u):
    p = s.P[i]
    for z, k in p.x.pop("jushoku", []):
        if z == "hand" and k in p.hand:
            p.hand.remove(k)
            s.grave_put(i, k)
        elif z == "mana" and k in p.mana:
            s.take_mana(i, k)
            s.grave_put(i, k)


add("n_jushoku", "樹食の超人", 8, "N", power=12000, brk=3, mach=True, races=("giant",), pri=10, roles="fin atk",
    costx=cx_jushoku, payx=pay_jushoku, enter=e_jushoku,
    text="T・ブレイカー、マッハファイター。召喚する時、自分のマナゾーンか手札の他のカードを好きな数選んでよい。"
         "選んだ1枚につきコスト-1。出た時、選んだカードをすべて墓地に置く",
    source=W + "《樹食の超人》")


# ================================================================ 水単チェンジサイバー
def _cyber_count(s, i):
    n = 0
    for k in s.P[i].mana:
        if race_like(BY_KEY[k], "cyber") or race_like(BY_KEY[k], "phoenix"):
            n += 1
    for u in s.P[i].board:
        if race_like(u.c, "cyber") or race_like(u.c, "phoenix"):
            n += 1
    return n


def cx_mercury(s, i, av):
    return 3 if _cyber_count(s, i) >= 5 else 5


def a_mercury(s, i, u):
    """メテオバーン：下のカード1枚を墓地に置き、2枚まで引き、相手のエレメント2つまでを手札に戻す"""
    if not u.under:
        return
    p = s.P[i]
    k = min(u.under, key=E.PRI.get)
    u.under.remove(k)
    s.grave_put(i, k)
    s.ev(f"　メテオバーン：{BY_KEY[k].name} を墓地に置く")
    s.draw(i, 2)
    for _ in range(2):
        t = s.target(i, kinds="CTX")
        if t is None:
            break
        move(s, i, t, "hand")


def acts_mercury(s, i, av, cv):
    """手札進化GV：手札のクリーチャー3体を重ねて出す"""
    p = s.P[i]
    if "n_mercury" not in p.hand:
        return []
    cres = [k for k in p.hand if k != "n_mercury" and BY_KEY[k].kind == "C"]
    if len(cres) < 3:
        return []
    n = cx_mercury(s, i, av)
    if n <= av and "W" in cv and s.fate(i, "n_mercury", "hand", True) == "ok":
        return [("x:merc", n)]
    return []


def ap_mercury(s, a):
    i = s.tp
    p = s.P[i]
    if "n_mercury" not in p.hand:
        return
    cres = sorted((k for k in p.hand if k != "n_mercury" and BY_KEY[k].kind == "C"), key=E.PRI.get)[:3]
    if len(cres) < 3:
        return
    p.mused += a[1]
    p.hand.remove("n_mercury")
    for k in cres:
        p.hand.remove(k)
    s.ev(f"手札進化GV：愛銀河 マーキュリー・スターフォージ（{a[1]}マナ、手札から3体）")
    u = s.enter(i, "n_mercury", "hand", True)
    if u is not None:
        u.under.extend(cres)
    else:
        p.hand.extend(cres)


def pr_mercury(deck, k):
    n = sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C")
    return None if n >= 8 else "手札進化GVの元になるクリーチャーが8体いない"


add("n_mercury", "愛銀河 マーキュリー・スターフォージ", 5, "W", power=15000, brk=3, jd=True,
    races=("cybercommand", "phoenix"), evo="hand", pri=11, roles="fin draw rem atk",
    costx=cx_mercury, attack=a_mercury, freeacts=acts_mercury, actapply={"x:merc": ap_mercury}, playrule=pr_mercury,
    text="手札進化GV（自分の手札のクリーチャー3体を重ねて出す）。T・ブレイカー、ジャストダイバー。"
         "自分のマナとバトルゾーンにサイバーかフェニックスが合計5つ以上あれば、水3マナで召喚してもよい。"
         "攻撃する時、メテオバーン：下のカード1枚を墓地に置いてよい。そうしたら2枚まで引き、相手のエレメント2つまでを手札に戻す",
    source=W + "《愛銀河マーキュリー・スターフォージ》")


def e_michel(s, i, u):
    p = s.P[i]
    if s.add_shield(i, up=True):
        s.ev("　表向きのシールドを1枚追加")
    n = sum(1 for _k, up in p.sh if up)
    if n:
        s.draw(i, n)


add("n_michel", "熱血美刃 ミケランジェロ", 6, "LW", power=9500, brk=2, blocker=True,
    races=("outragecommand", "revolution"), pri=9, roles="blk draw shd",
    enter=e_michel,
    changex=lambda s, i, u: bool(set("LW") & set(u.c.civ)) and s.power(i, u, True) >= 4000,
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
                                         and set("LW") & set(BY_KEY[kk].civ) and BY_KEY[kk].power >= 4000) >= 3
    else "革命チェンジの元が3体いない",
    text="革命チェンジ（光か水のパワー4000以上のクリーチャーが攻撃する時、入れ替えて出せる）。ブロッカー、W・ブレイカー。"
         "出た時、山札の上から1枚を表向きのシールドにしてよい。その後、自分の表向きのシールド1つにつき1枚引いてよい",
    source=W + "《熱血美刃 ミケランジェロ》")


def e_yari(s, i, u):
    """ファイナル革命：革命チェンジで出た時、相手を全部タップし、タップしている相手1体につき1枚引く"""
    p = s.P[i]
    if s.atk is not u or p.x.get("finrev_t") == s.turn:
        return                              # ファイナル革命は、どのカードでも1ターンに1回だけ
    p.x["finrev_t"] = s.turn
    o = s.P[1 - i]
    for x in o.board:
        if x.c.kind == "C":
            x.tap = True
    n = sum(1 for x in o.board if x.c.kind == "C" and x.tap)
    s.ev(f"　ファイナル革命：相手をすべてタップし{n}枚引く")
    if n:
        s.draw(i, n)


def rep_yari(s, i, u, dest, destroy_):
    """エスケープ：破壊される時、かわりにシールド1つを手札に加える"""
    if u.k != "n_yari" or not destroy_:
        return False
    p = s.P[i]
    for j in range(len(p.sh) - 1, -1, -1):
        if not p.sh[j][1]:
            p.hand.append(p.sh.pop(j)[0])
            s.shield_left()
            s.ev("　エスケープ：シールド1つを手札に加えてミラダンテ槍は残る")
            return True
    return False


def w_yari_enter(s, i, u):
    """相手のクリーチャーが出た時、次の（ミラダンテ槍を持つ側の）ターンのはじめまで攻撃できない"""
    if u.c.kind == "C" and s.has(1 - i, "n_yari"):
        lock_until_my_turn(s, 1 - i, u)


def ts_yari(s, i, u):
    """自分のターンのはじめにアンタップした時も同じ（相手がミラダンテ槍を持っていれば）"""
    if u.c.kind == "C" and not u.tap and s.has(1 - i, "n_yari"):
        lock_until_my_turn(s, 1 - i, u)


add("n_yari", "時の団長 ミラダンテ槍", 8, "LW", power=13500, brk=3, races=("angelcommand", "dragon", "revolution"),
    pri=12, roles="fin dis draw",
    enter=e_yari, leaverep=rep_yari, enterwatch=w_yari_enter, tstartall=ts_yari,
    changex=lambda s, i, u: bool(set("LW") & set(u.c.civ)) and s.power(i, u, True) >= 8000,
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
                                         and set("LW") & set(BY_KEY[kk].civ) and BY_KEY[kk].power >= 8000) >= 3
    else "革命チェンジの元が3体いない",
    text="革命チェンジ（光か水のパワー8000以上）。T・ブレイカー。相手のクリーチャーが出た時かアンタップした時、"
         "次の自分のターンのはじめまで攻撃できない。エスケープ（破壊される時、かわりに自分のシールド1つを手札に加えてよい）。"
         "ファイナル革命：革命チェンジで出た時、そのターンに他のファイナル革命を使っていなければ、相手のクリーチャーをすべてタップし、"
         "タップしている相手のクリーチャー1体につき1枚引いてよい",
    source=W + "《時の団長 ミラダンテ槍》")


# ================================================================ 実在の7リストを公式の形に戻す
# これまでは、1枚だけ入っていた上の9枚を「近い働きの採用カード」に置き換えていた。
# 9枚とも実装できたので、超CSⅨ新潟の公式掲載リストどおりの40枚にする。
from cards3 import DECKS           # noqa: E402

_REAL = {
    "創世竜ループ": {"majin": 3, "n_greatblue": 1, "jasmine": 2, "efc": 1},
    "ドッコイループ": {"vt": 1, "n_eine": 1, "clock": 1, "n_siren": 1, "eringi": 3, "n_naze": 1},
    "ゾロ・ア・スタート": {"doom": 3, "n_vegeta": 1, "gigan": 2, "n_jushoku": 1},
    "水単チェンジサイバー": {"mflower": 3, "n_mercury": 1, "tina": 2, "n_michel": 1, "n_yari": 1},
}
for _n, _fix in _REAL.items():
    DECKS[_n].update(_fix)
    assert sum(DECKS[_n].values()) == 40, (_n, sum(DECKS[_n].values()))
