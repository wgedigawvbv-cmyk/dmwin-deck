"""cardspec0.json の27枚（調べ済みのカード）

  「巨大設計図」（cards3.py の《超七極 Gio》の呪文側）と「樹食の超人」（env1.py の n_jushoku）は実装済みなので入れていない。
  「時の法皇 ミラダンテXII」も env5.py の n_mdante12 として実装済みだった（表記が「ミラダンテⅫ」で名前が一致しなかったため
  cardspec0.json の除外リストから漏れていた）。二重登録でデッキの中身が狂うのを避けるため、こちらでは実装していない。

  調べ直して確かめたところ（dmwiki）
    ・改竄の炎 ボルメテウス・ハック：水文明・コスト2・パワー2000／ハイパーモードはパワー5000。cardspec のとおり。
    ・アイドル・ハート：S・トリガーあり。超魂Xで与えるのは「ブロッカー」だけ。
    ・Q.Q.G.QX.／「この子はさわらせないわ！」：呪文側の後半は「出したクリーチャーを攻撃させる」強制。
    ・煙幕の聖沌 k3mur1：クリーチャー側は攻撃時にメカかシノビ1体をタップしてメカ・メクレイド5。
    ・偽りの月 インターステラ：ブロッカー・ジャストダイバー・W・ブレイカー。超次元ゾーンを使う。
    ・サファイア・ウィズダム：「自分の手札の枚数」はこのカードの持ち主の手札の枚数。
    ・LOVE＆ABYSS：S・トリガーなし。本文は1文だけ。
    ・～輝きは奇跡そのもの～：超魂Xで与えるのは「自分のシールドが離れる時、かわりに下のカードをすべて墓地に置いてよい」。
    ・∞龍 ゲンムエンペラー：「コスト5以下の、クリーチャーの能力と呪文の効果を無視する」（両方コスト5以下が条件）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move
from envcards.env0 import worst_own, lock_until_my_turn, race_like

W = "https://dmwiki.net/"


# ================================================================ 共通の道具
def _mekureido(s, i, n, pred, what):
    """メクレイドX：山札の上3枚を見て、条件に合うカード1枚をコストを支払わずに使う。残りは山札の下へ"""
    p = s.P[i]
    m = min(3, len(p.deck) - 1)
    if m <= 0:
        return
    top = [p.deck.pop() for _ in range(m)]
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.cost <= n and pred(c) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        p.hand.append(best)
        s.ev(f"　{what}：{BY_KEY[best].name} をただで使う")
        if not free_play(s, i, best):
            if best in p.hand:
                p.hand.remove(best)
            top.append(best)
    for k in top:
        p.deck.insert(0, k)


def _cast_free(s, i, k, dest="grave", twin=False):
    """コストを支払わずに呪文を唱える（カードは呼ぶ側がゾーンから取り除いておく）。
    唱えた後の行き先を dest で決める（"grave" / "deck"＝山札の下 / None＝どこにも置かない）"""
    p = s.P[i]
    c = BY_KEY[k]
    cost = c.twin[0] if (twin and c.twin) else c.cost
    p.spl += 1
    s.first_play(i, cost)
    prev = s.spc
    s.spc = cost
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, k)
    fn = E.SPELL.get(k)
    if fn is not None and not s.over:
        fn(s, i)
    s.spc = prev
    if dest == "grave":
        s.grave_put(i, k)
    elif dest == "deck":
        p.deck.insert(0, k)
    if not twin:
        s.noncre(i)


def _cast_inplace(s, i, k):
    """ツインパクトの呪文側を、カードを場に置いたまま唱える（大虹帝 ミノガミ）"""
    _cast_free(s, i, k, dest=None, twin=True)


def _stamp(s, i, u):
    """すべてのクリーチャーに「何ターン目に出たか」を記録する（「このターンに出た」を見るため）"""
    u.x["eturn"] = s.turn


E.ENTERWATCH.append(_stamp)


def _entered_this_turn(s, j):
    return [u for u in s.P[j].board if u.c.kind == "C" and u.x.get("eturn", -1) == s.turn]


def _sick_atklock(key):
    """「相手のクリーチャーは出たターン攻撃できない」"""
    def f(s, i, u):
        return u.sick and any(z.k == key for z in s.P[1 - i].board)
    return f


def _tomana_crowd(key):
    """「相手がそのターンに他のクリーチャーを2体以上出していれば、出るクリーチャーをかわりにマナゾーンへ」"""
    def f(s, owner, u, i, k, src, summon, res):
        if i != owner and res == "ok" and s.P[i].ent >= 2:
            return "mana"
        return res
    return f


# ================================================================ ～世紀末の善悪～
def dw_seikimatsu(s, j, k):
    """相手が手札から呪文を捨てた時、その呪文を相手の墓地からコストを支払わずに唱えてもよい"""
    i = 1 - j
    if not s.has(i, "e_seikimatsu"):
        return
    c = BY_KEY[k]
    tw = c.kind != "S" and bool(c.twin)
    if not (c.kind == "S" or tw):
        return
    o = s.P[j]
    if k not in o.grave or not s.spell_ok(i, c.twin[0] if tw else c.cost):
        return
    if s.P[i].x.get("seiki_busy"):
        return                        # 唱えている途中にさらに捨てられた分は、重ねて唱えない（無限に続くのを防ぐ）
    s.P[i].x["seiki_busy"] = True
    try:
        o.grave.remove(k)
        s.ev(f"　～世紀末の善悪～：相手が捨てた {c.name} を墓地からただで唱える")
        _cast_free(s, i, k, dest="grave", twin=tw)
    finally:
        s.P[i].x["seiki_busy"] = False


def en_seikimatsu(s, i, u):
    p = s.P[i]
    o = s.P[1 - i]
    s.draw(i, 3)
    for _ in range(2):
        if s.over or not p.hand:
            break
        s.discard(i, min(p.hand, key=E.PRI.get))
        if s.over or not o.hand:
            continue
        s.discard(1 - i, o.hand[s.rng.randrange(len(o.hand))])


add("e_seikimatsu", "～世紀末の善悪～", 5, "LWD", power=6500, brk=2, blocker=True,
    races=("god", "steamknight"), evo="LWD", neo=True, gneo=True, pri=8, roles="draw dis blk",
    enter=en_seikimatsu, discardwatch=dw_seikimatsu,
    text="G-NEO進化（光・水・闇のクリーチャー1体の上に置いてもよいし、置かずに出してもよい。離れる時はかわりに下のカードが離れる）。"
         "ブロッカー、W・ブレイカー。出た時、3枚引き、その後自分の手札を2枚まで捨てる。"
         "捨てた1枚につき、相手の手札を見ないで1枚選んで捨てさせる。"
         "相手が手札から呪文を捨てた時、その呪文を相手の墓地からコストを支払わずに唱えてもよい",
    source=W + "《～世紀末の善悪～》")


# ================================================================ 氷柱と炎弧の決断
def sp_hyouchuu(s, i):
    p = s.P[i]
    for _ in range(2):
        if s.over:
            return
        t = s.target(i)
        if t is not None and E.PRI[t.k] >= 4:
            lock_until_my_turn(s, i, t)
            s.ev(f"　{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")
            continue
        best, bv = None, -1
        for k in sorted(set(p.hand)):
            c = BY_KEY[k]
            if c.cost > 2 or c.kind == "S":
                continue
            if c.kind == "C" and ((c.evo and not c.neo) or s.fate(i, k, "hand", False) != "ok"):
                continue
            if E.PRI[k] > bv:
                best, bv = k, E.PRI[k]
        if best is not None:
            s.ev(f"　手札から {BY_KEY[best].name} を出す")
            free_play(s, i, best)
            continue
        if t is not None:
            lock_until_my_turn(s, i, t)
            s.ev(f"　{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")
            continue
        if p.hand:
            s.discard(i, min(p.hand, key=E.PRI.get))
            s.draw(i, 2)


def tg_hyouchuu(s, di, k):
    """自分の墓地に呪文が2枚以上あれば、シールドゾーンにあるこの呪文はS・トリガーを得る"""
    if k != "e_hyouchuu":
        return False
    n = 0
    for x in s.P[di].grave:
        c = BY_KEY[x]
        if c.kind == "S" or c.twin:
            n += 1
            if n >= 2:
                return True
    return False


add("e_hyouchuu", "氷柱と炎弧の決断", 3, "WF", kind="S", pri=5, roles="rem dis draw trg",
    spell=sp_hyouchuu, trigok=tg_hyouchuu,
    text="自分の墓地に呪文が2枚以上あれば、シールドゾーンにあるこの呪文にS・トリガーを与える。"
         "唱えた時、次から2回選ぶ（同じものを2回選んでもよい）："
         "(a)相手のクリーチャー1体を選び、次の自分のターンのはじめまで攻撃もブロックもできなくする／"
         "(b)自分の手札を1枚捨てて2枚引く／(c)コスト2以下のエレメント1つを手札からコストを支払わずに出す",
    source=W + "《氷柱と炎弧の決断》")


# ================================================================ 改竄の炎 ボルメテウス・ハック
def fx_bolhack(s, owner, u, i, k, src, summon, res):
    """相手のクリーチャーは相手の手札以外からは出ない"""
    if i != owner and src != "hand":
        return "no"
    return res


add("e_bolhack", "改竄の炎 ボルメテウス・ハック", 2, "W", power=2000, races=("millionflame", "hyperbeast"),
    zrush=True, pri=5, roles="dis",
    fatex=fx_bolhack, atklock=_sick_atklock("e_bolhack"),
    powerx=lambda s, i, u, atk: 3000 if u.hyper else 0,
    text="相手のクリーチャーは、相手の手札以外からは出られない（山札・マナ・墓地からの踏み倒しを止める）。"
         "Zラッシュ：自分のシールドが離れたら、次の自分のターンのはじめまでハイパーモードを解放する。"
         "ハイパーモード中はパワー5000になり、相手のクリーチャーは出たターンに攻撃できない",
    source=W + "《改竄の炎 ボルメテウス・ハック》")


# ================================================================ ハッター・ルピア
def w_hatter(s, i, u):
    """相手のマナゾーンの枚数よりコストが大きい相手のクリーチャーが出た時、それを破壊する"""
    if u.c.kind != "C" or not s.has(1 - i, "e_hatter"):
        return
    if u.c.cost > len(s.P[i].mana) and u in s.P[i].board:
        s.ev(f"　ハッター・ルピア：{u.c.name} を破壊")
        s.leave(i, u, "grave", by_opp=True, destroy=True)


def at_hatter(s, i, u):
    if u.hyper:
        _mekureido(s, i, 5, lambda c: race_like(c, "firebird"), "ファイアー・バード・メクレイド5")


def fa_hatter(s, i, av, cv):
    """ハイパー化：自分の他のクリーチャーを1体タップしてハイパーモードを解放する"""
    for u in s.P[i].board:
        if u.k == "e_hatter" and not u.hyper:
            if any(z is not u and z.c.kind == "C" and not z.tap for z in s.P[i].board):
                return [("x:hyper_hatter", u.uid)]
    return []


def ap_hatter(s, a):
    i = s.tp
    p = s.P[i]
    u = next((z for z in p.board if z.uid == a[1] and z.k == "e_hatter"), None)
    if u is None or u.hyper:
        return
    oth = [z for z in p.board if z is not u and z.c.kind == "C" and not z.tap]
    if not oth:
        return
    s.tap_cre(i, min(oth, key=s.val))
    u.hyper = True
    s.ev("ハイパー化：ハッター・ルピア（他のクリーチャー1体をタップ）")


add("e_hatter", "ハッター・ルピア", 3, "F", power=3000, races=("armoredfirebird", "firebird", "armored", "hyperbeast"),
    pri=6, roles="rem atk dis",
    attack=at_hatter, enterwatch=w_hatter, freeacts=fa_hatter, actapply={"x:hyper_hatter": ap_hatter},
    saok=lambda s, i, u: u.k == "e_hatter" and u.hyper,
    powerx=lambda s, i, u, atk: 2000 if u.hyper else 0,
    text="相手のマナゾーンの枚数よりコストが大きい相手のクリーチャーが出た時、それを破壊する。"
         "ハイパー化：自分のメインステップ中、自分の他のクリーチャー1体をタップして、"
         "次の自分のターンのはじめまでハイパーモードを解放してよい。"
         "ハイパーモード中はパワー5000・スピードアタッカーになり、攻撃する時ファイアー・バード・メクレイド5をする"
         "（山札の上から3枚を見て、その中のコスト5以下のファイアー・バード1枚をコストを支払わずに使ってよい）",
    source=W + "《ハッター・ルピア》")


# ================================================================ リツイーギョ #桜 #満開
add("e_ritsuigyo", "リツイーギョ #桜 #満開", 2, "N", power=3000, races=("trix", "teamwave"), pri=5, roles="dis blk",
    fatex=_tomana_crowd("e_ritsuigyo"),
    powerx=lambda s, i, u, atk: 4000 if s.tp != i else 0,
    text="相手のクリーチャーが出る時、そのターンに相手が他のクリーチャーを2体以上出していれば、"
         "かわりにそれを相手のマナゾーンに置く。相手のターン中、このクリーチャーのパワーは+4000される",
    source=W + "《リツイーギョ #桜 #満開》")


# ================================================================ 観覧！ホールインランド・ヘラクレス
def en_herakuresu(s, i, u):
    p = s.P[i]
    s.draw(i, 2)
    n = 1 + len(u.under)
    if p.mused:
        p.mused = max(0, p.mused - n)
        s.ev(f"　自分のマナ{n}枚をアンタップ")


add("e_herakuresu", "観覧！ホールインランド・ヘラクレス", 4, "LWN", power=6000, brk=2, blocker=True,
    races=("giant", "insect"), evo="LWN", neo=True, pri=7, roles="draw acc blk",
    enter=en_herakuresu,
    text="NEO進化（光・水・自然のクリーチャー1体の上に置いてもよいし、置かずに出してもよい）。ブロッカー、W・ブレイカー。"
         "出た時、2枚引く。その後、このクリーチャーに含まれるカード1枚につき、自分のマナゾーンのカードを1枚アンタップする",
    source=W + "《観覧！ホールインランド・ヘラクレス》")


# ================================================================ ～輝きは奇跡そのもの～
def en_kagayaki(s, i, u):
    for z in s.P[1 - i].board:
        if z.c.kind == "C":
            s.tap_cre(1 - i, z)
    s.ev("　相手のクリーチャーをすべてタップ")


def bp_kagayaki(s, ai, di, n):
    """超魂：下にこのカードがあるクリーチャーは、自分のシールドが離れるかわりに下のカードをすべて墓地に置ける

    全体に効く差し込み口なので、割られる側の場にこのカードを下に持つクリーチャーがいる時だけ働く。
    ブレイクされる直前に枚数を0にするので、シールドはシールドゾーンを離れない
    （breakrep でいったん離してから戻すと、Zラッシュや「シールドが離れた時」が誤って誘発する）。"""
    if n <= 0:
        return n
    for u in s.P[di].board:
        if u.c.kind == "C" and "e_kagayaki" in u.under:
            for k in u.under:
                s.grave_put(di, k)
            u.under = []
            s.ev("　超魂：下のカードをすべて墓地に置き、シールドを守る")
            return 0
    return n


add("e_kagayaki", "～輝きは奇跡そのもの～", 7, "L", power=4000, trig=True,
    races=("apolloniadragon", "mechadelsol", "steamknight", "fusioner"), pri=8, roles="dis trg shd",
    enter=en_kagayaki, breakpre=bp_kagayaki, status="partial",
    text="S・トリガー。出た時、相手のクリーチャーをすべてタップする。"
         "超魂X：このカードがクリーチャーの下にあれば、そのクリーチャーは"
         "「自分のシールドが離れる時、かわりに自分の下にあるカードをすべて墓地に置いてもよい」を得る",
    note="シールドを守る置き換えは、ブレイクされる時だけ実装した（breakpre はブレイクの直前だけに呼ばれる"
         "差し込み口で、呪文などでシールドがシールドゾーンを離れるのを止める差し込み口はエンジンにない）。"
         "使うかどうかは機械的に決める（下にカードがあれば必ず守る）",
    source=W + "《～輝きは奇跡そのもの～》")
E.SHINKA.add("e_kagayaki")


# ================================================================ LOVE＆ABYSS
def sp_loveabyss(s, i):
    o = s.P[1 - i]
    for u in o.board[:]:
        if u in o.board:
            s.leave(1 - i, u, "deck", by_opp=True)
    o.deck.extend(o.hand)
    del o.hand[:]
    o.deck.extend(o.grave)
    del o.grave[:]
    s.rng.shuffle(o.deck)
    s.ev("　相手のバトルゾーン・手札・墓地のカードをすべて山札に加えてシャッフル")


add("e_loveabyss", "LOVE＆ABYSS", 9, "D", kind="S", pri=10, roles="rem dis fin", spell=sp_loveabyss,
    text="プレイヤーを1人選ぶ。そのプレイヤーは、自分のバトルゾーン・手札・墓地にあるカードをすべて山札に加えてシャッフルする"
         "（選ぶ相手は、このシミュレーター共通の決まりどおり相手プレイヤーにする）",
    source=W + "《LOVE＆ABYSS》")


# ================================================================ トレジャー・マップ
def sp_treasure(s, i):
    s.dig(i, 5, lambda k: BY_KEY[k].kind == "C" and "N" in BY_KEY[k].civ, "bottom")


add("e_treasure", "トレジャー・マップ", 1, "N", kind="S", pri=3, roles="draw", spell=sp_treasure,
    text="自分の山札の上から5枚を見る。その中から自然のクリーチャー1体を選んで手札に加えてもよい。"
         "残りは好きな順序で山札の下に置く",
    source=W + "《トレジャー・マップ》")


# ================================================================ ～進封せし大悪魔～
def en_shinpuu(s, i, u):
    for z in _entered_this_turn(s, 1 - i):
        if z in s.P[1 - i].board:
            move(s, i, z, "hand")


add("e_shinpuu", "～進封せし大悪魔～", 4, "W", power=4000, trig=True, races=("granddevil", "steamknight"),
    evo="LWD", neo=True, pri=6, roles="rem dis trg",
    enter=en_shinpuu, atklock=_sick_atklock("e_shinpuu"),
    text="NEO進化（光・水・闇のクリーチャー1体の上に置いてもよいし、置かずに出してもよい）。S・トリガー。"
         "出た時、このターンに出た相手のクリーチャーをすべて持ち主の手札に戻す。"
         "相手のクリーチャーは、出たターンに攻撃できない",
    source=W + "《～進封せし大悪魔～》")


# ================================================================ ∞龍 ゲンムエンペラー
def _mugen_cands(s, i, skip=None):
    return [u for u in s.P[i].board if u.c.kind == "C" and not u.tap and u is not skip]


def cx_genmu(s, i, av):
    return 4 if len(_mugen_cands(s, i)) >= 4 else 99


def px_genmu(s, i, k, n):
    for u in sorted(_mugen_cands(s, i), key=s.val)[:4]:
        s.tap_cre(i, u)


def _genmu_out(s):
    """∞龍 ゲンムエンペラーがどちらかのバトルゾーンにいるか（この能力は両者に効く）"""
    return any(z.k == "e_genmu" for z in s.P[0].board) or any(z.k == "e_genmu" for z in s.P[1].board)


def sl_genmu(s, i, cost):
    """コスト5以下の呪文の効果を無視する（唱えられないものとして扱う）

    止める条件がコストだけなので、呪文のキー（k）は見なくてよい。"""
    if cost > 5:
        return False
    return _genmu_out(s)


def al_genmu(s, i, u):
    """コスト5以下のクリーチャーの能力をすべて無視する（自分のクリーチャーも対象）

    攻撃を宣言しているクリーチャーだけは外している。engine3.attack は
    `if ABILOCK and not s.abi(i, u): return` で、能力を無視されたクリーチャーの
    攻撃そのもの（ブロック・シールドのブレイクまで）を打ち切ってしまうため、
    そこを含めるとコスト5以下のクリーチャーが一切攻撃できなくなってしまう。
    そのぶん「攻撃する時」の誘発は止まらない（note に書いた）。"""
    if u.c.kind != "C" or u.c.cost > 5 or s.atk is u:
        return False
    return _genmu_out(s)


def fa_genmu(s, i, av, cv):
    """ムゲンクライム4：墓地からも召喚できる"""
    p = s.P[i]
    if "e_genmu" not in p.grave or av < 4 or not cv.issuperset("WD"):
        return []
    if len(_mugen_cands(s, i)) < 4 or s.fate(i, "e_genmu", "grave", True) != "ok":
        return []
    return [("x:mugen_genmu",)]


def ap_genmu(s, a):
    i = s.tp
    p = s.P[i]
    if "e_genmu" not in p.grave or len(p.mana) - p.mused < 4:
        return
    cands = _mugen_cands(s, i)
    if len(cands) < 4:
        return
    for u in sorted(cands, key=s.val)[:4]:
        s.tap_cre(i, u)
    p.mused += 4
    p.grave.remove("e_genmu")
    s.ev("ムゲンクライム4：∞龍 ゲンムエンペラー（墓地から召喚）")
    s.enter(i, "e_genmu", "grave", True)


add("e_genmu", "∞龍 ゲンムエンペラー", 99, "WD", power=99999, brk=99, blocker=True,
    races=("mugenmasterdragon", "teamzero"), pri=13, roles="blk fin dis",
    costx=cx_genmu, payx=px_genmu, spelllock=sl_genmu, abilock=al_genmu,
    freeacts=fa_genmu, actapply={"x:mugen_genmu": ap_genmu},
    status="partial",
    text="コストもパワーも∞（このシミュレーターでは99／99999として扱う）。ブロッカー、∞ブレイカー（シールドをすべてブレイク）。"
         "ムゲンクライム4：自分のクリーチャーを4体タップし、水・闇の4マナを支払って、手札または墓地から召喚してもよい。"
         "コスト5以下の、クリーチャーの能力と呪文の効果を無視する",
    note="「コスト5以下のクリーチャーの能力を無視する」は ABILOCK で実装したが、"
         "「攻撃する時」の誘発だけは止まらない。engine3.attack が ABILOCK で能力を無視された"
         "クリーチャーの攻撃そのものを打ち切ってしまうため、攻撃中のクリーチャーを対象から外している"
         "（入れるとコスト5以下のクリーチャーが攻撃できなくなる。エンジンの修正が必要）。"
         "また、パワーを増減する常在能力（POWERX・AURAP）は ABILOCK を通らないので止まらない。"
         "「コスト5以下の呪文の効果を無視する」は、両者がコスト5以下の呪文を唱えられない形で近似した"
         "（本来は唱えられるが効果が出ないだけなので、マナの使い方が本物と変わる）",
    source=W + "《∞龍 ゲンムエンペラー》")


# ================================================================ ストリエ雷鬼の巻
def en_storie(s, i, u):
    p = s.P[i]
    if p.hand:
        k = min(p.hand, key=E.PRI.get)
        p.hand.remove(k)
        p.deck.insert(0, k)
        s.ev(f"　{BY_KEY[k].name} を山札の下へ")
    s.draw(i)


add("e_storie", "ストリエ雷鬼の巻", 1, "F", kind="T", races=("demonio", "onirexstars"), pri=3, roles="draw",
    enter=en_storie,
    text="タマシード。シンカライズ：このタマシードをクリーチャーとみなして、その上に進化クリーチャーを置いてもよい。"
         "出た時、自分の手札を1枚山札の下に置き、1枚引く",
    source=W + "《ストリエ雷鬼の巻》")
E.SHINKA.add("e_storie")


# ================================================================ 怒りの影ブラック・フェザー
def en_blackfeather(s, i, u):
    mine = [z for z in s.P[i].board if z.c.kind == "C"]
    if not mine:
        return
    t = worst_own(s, i, keep=u) or u
    s.ev(f"　自分の {t.c.name} を破壊")
    s.leave(i, t, "grave", destroy=True)


add("e_blackfeather", "怒りの影ブラック・フェザー", 1, "D", power=3000, races=("ghost",), pri=2, roles="atk",
    enter=en_blackfeather,
    text="出た時、自分のクリーチャー1体を選んで破壊する（強制。他に出せるクリーチャーがいなければ自分を破壊する）",
    source=W + "《怒りの影ブラック・フェザー》")


# ================================================================ 修羅の死神フミシュナ ／「この先は修羅の道ぞ」
def en_fumishuna(s, i, u):
    if s.P[1 - i].hand:
        s.discard_random(1 - i)       # 引く方は dw_fumishuna（手札を捨てた時）が受ける


def dw_fumishuna(s, j, k):
    """各ターン1度、相手が自分の手札を1枚捨てた時、1枚引いてもよい"""
    i = 1 - j
    for u in s.P[i].board:
        if u.k == "e_fumishuna" and u.x.get("fdraw") != s.turn:
            u.x["fdraw"] = s.turn
            s.draw(i)
            return


def sp_fumishuna(s, i):
    for _ in range(2):
        if s.over:
            return
        t = s.target(i)
        if t is not None:
            move(s, i, t, "hand")
        else:
            s.draw(i)


add("e_fumishuna", "修羅の死神フミシュナ", 4, "D", power=4000, blocker=True, races=("demoncommand", "command"),
    twin=(5, "W", True), pri=6, roles="dis blk draw rem trg",
    enter=en_fumishuna, spell=sp_fumishuna, discardwatch=dw_fumishuna,
    text="ブロッカー。出た時、相手の手札を1枚見ないで選んで捨てさせる。"
         "各ターン1度、相手が自分の手札を1枚捨てた時、自分は1枚引いてもよい。"
         "呪文側《「この先は修羅の道ぞ」》（水・コスト5・S・トリガー）：次から2回選ぶ（同じものを2回選んでもよい）："
         "(a)1枚引く／(b)相手のクリーチャー1体を持ち主の手札に戻す",
    source=W + "《修羅の死神フミシュナ／「この先は修羅の道ぞ」》")


# ================================================================ 森仙のJ ロマネスク
def en_romanesque(s, i, u):
    p = s.P[i]
    s.ramp(i, 4)
    if p.mana:
        k = max(p.mana, key=E.PRI.get)
        if E.PRI[k] >= 5:
            s.take_mana(i, k)
            p.hand.append(k)
            s.ev(f"　マナから {BY_KEY[k].name} を手札へ")


def rep_romanesque(s, ai, di, broken):
    """シールド・セイバー：ブレイクされるかわりに自分のクリーチャー1体を破壊してシールドを守る"""
    d = s.P[di]
    if not broken or not any(u.k == "e_romanesque" for u in d.board):
        return False
    if d.sh:
        return False                     # シールドがまだ残っているなら使わない
    cands = [u for u in d.board if u.c.kind == "C" and u.k != "e_romanesque"]
    if not cands:
        cands = [u for u in d.board if u.c.kind == "C"]
    n = 0
    for u in sorted(cands, key=s.val):
        if n >= len(broken) or s.over:
            break
        if u in d.board and s.leave(di, u, "grave", destroy=True):
            n += 1
    if n <= 0:
        return False
    for x in broken[:n]:
        d.sh.append(x)
    del broken[:n]
    s.ev(f"　シールド・セイバー：クリーチャー{n}体を破壊してシールド{n}枚を守る")
    return not broken


add("e_romanesque", "森仙のJ ロマネスク", 8, "LN", power=15000, brk=3, mach=True,
    races=("apolloniadragon", "armoreddragon", "earthdragon", "dragon"), pri=11, roles="acc fin atk shd",
    enter=en_romanesque, breakrep=rep_romanesque, costx=lambda s, i, av: max(0, 8 - s.ncre(i)),
    text="シンパシー：自分のクリーチャー1体につき、このクリーチャーの召喚コストは1少なくなる（0より下がらない）。"
         "マッハファイター、T・ブレイカー。出た時、山札の上から4枚をマナゾーンに置き、"
         "その後マナゾーンから1枚を手札に戻してもよい。"
         "自分のクリーチャーすべてに「シールド・セイバー」を与える"
         "（自分のシールドがブレイクされる時、かわりにそれを持つクリーチャー1体を破壊してもよい）",
    source=W + "《森仙のJ ロマネスク》")


# ================================================================ マジック・A・セミプーロ ／♪閑かさや
def ds_semipuro(s, i, u):
    t = s.target(i)
    if t is not None:
        move(s, i, t, "hand")


def sp_semipuro(s, i):
    p = s.P[i]
    s.draw(i, 3)
    for _ in range(2):
        if not p.hand:
            break
        k = min(p.hand, key=E.PRI.get)
        p.hand.remove(k)
        p.deck.append(k)


add("e_semipuro", "マジック・A・セミプーロ", 6, "W", power=5000, blocker=True, trig=True,
    races=("magiccybercommand", "cybercommand", "command", "magic"), twin=(2, "W", False),
    pri=8, roles="blk rem draw trg",
    destroyed=ds_semipuro, spell=sp_semipuro,
    text="S・トリガー、ブロッカー。破壊された時、相手のクリーチャー1体を選び、持ち主の手札に戻す。"
         "呪文側《♪閑かさや とにかくブレイン 蝉ミンミン》（水・コスト2）：3枚引き、その後自分の手札を2枚、"
         "好きな順序で山札の上に置く",
    source=W + "《マジック・A・セミプーロ／♪閑かさや とにかくブレイン 蝉ミンミン》")


# ================================================================ アイドル・ハート
def lf_idolheart(s, i, u, dest):
    if dest == "grave":
        _mekureido(s, i, 8, lambda c: race_like(c, "cyber"), "サイバー・メクレイド8")


add("e_idolheart", "アイドル・ハート", 5, "W", power=1000, trig=True, races=("cyberv", "fusioner"),
    pri=6, roles="trg blk",
    left=lf_idolheart, blockok=lambda s, u: u.c.kind == "C" and "e_idolheart" in u.under,
    text="S・トリガー。このカードが墓地に置かれた時、その直前にバトルゾーンにあれば、サイバー・メクレイド8をする"
         "（山札の上から3枚を見て、その中のコスト8以下のサイバーを1枚コストを支払わずに使ってよい。残りは山札の下へ）。"
         "超魂X：このカードがクリーチャーの下にあれば、そのクリーチャーはブロッカーを得る",
    source=W + "《アイドル・ハート》")
E.SHINKA.add("e_idolheart")


# ================================================================ Q.Q.G.QX. ／「この子はさわらせないわ！」
def en_qqgqx(s, i, u):
    s.ramp(i, 1)


def sp_qqgqx(s, i):
    p = s.P[i]
    s.rng.shuffle(p.deck)
    if len(p.deck) <= 1:
        return
    k = p.deck[-1]
    c = BY_KEY[k]
    s.ev(f"　山札の上を表向きに：{c.name}")
    if c.kind != "C" or c.power < 12000 or (c.evo and not c.neo):
        return
    if s.fate(i, k, "deck", False) != "ok":
        return
    p.deck.pop()
    z = s.enter(i, k, "deck", False)
    if z is None:
        return
    z.tap = True
    z.x["qqtaunt"] = s.turn + (1 if s.tp == i else 0)
    s.ev(f"　{c.name} をタップして出す（相手はこれを攻撃しなければならない）")


def _qq_taunt(s, i, u, t=None):
    """u（i のクリーチャー）が、相手の出した「攻撃される側」のクリーチャーを攻撃できるか（t は除いて見る）"""
    for z in s.P[1 - i].board:
        if z is t or z.c.kind != "C" or z.jd or z.x.get("qqtaunt", -1) < s.turn:
            continue
        if (z.tap or (u.sick and u.c.mach)) and s.power(1 - i, z) <= s.power(i, u, True):
            return True
    return False


def tl_qqgqx(s, i, u, t):
    """出したクリーチャーを攻撃できるなら、他のクリーチャーは攻撃できない"""
    return _qq_taunt(s, i, u, t)


def np_qqgqx(s, i, u):
    """出したクリーチャーを攻撃できるなら、プレイヤーも攻撃できない"""
    return _qq_taunt(s, i, u)


add("e_qqgqx", "Q.Q.G.QX.", 4, "N", power=12000, noatkp=True, races=("gransect",), twin=(7, "N", True),
    pri=7, roles="blk acc dis trg",
    enter=en_qqgqx, spell=sp_qqgqx, atktargetlock=tl_qqgqx, noatkplock=np_qqgqx, status="partial",
    text="このクリーチャーは相手プレイヤーを攻撃できない。出た時、自分の山札の上から1枚をマナゾーンに置いてもよい。"
         "相手は自分の山札を見ることも、表向きにすることも、順序を変えることもできない。"
         "呪文側《「この子はさわらせないわ！」》（自然・コスト7・S・トリガー）：自分の山札をシャッフルし、上から1枚を表向きにする。"
         "それがパワー12000以上のクリーチャーなら、タップして出してもよい。次の自分のターンのはじめまで、"
         "相手のクリーチャーが攻撃する時、可能ならそのクリーチャーを攻撃する",
    note="「相手は自分の山札を見ることも、表向きにすることも、順序を変えることもできない」は実装していない。"
         "山札を見る処理がエンジンの dig・revive・mill と各カードのサーチに散っていて、"
         "まとめて通す差し込み口（DECKLOOK）がないため",
    source=W + "《Q.Q.G.QX.／「この子はさわらせないわ！」》")


# ================================================================ PP-「P」
def fx_pp(s, owner, u, i, k, src, summon, res):
    if i != owner and res == "ok" and BY_KEY[k].cost > len(s.P[i].mana):
        return "mana"
    return res


def te_pp(s, i, u):
    """超魂X：相手のターンの終わりに、相手のタップしているクリーチャーがなければ、
    山札の上2枚をマナへ置き、マナから1枚手札に戻す"""
    if s.tp == i:
        return                       # 自分のターンの終わりには働かない
    if "e_pp" not in u.under:
        return
    if any(z.c.kind == "C" and z.tap for z in s.P[1 - i].board):
        return
    p = s.P[i]
    if len(p.deck) <= 2:
        return
    s.ramp(i, 2)
    if p.mana:
        k = max(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        p.hand.append(k)
        s.ev(f"　超魂：マナから {BY_KEY[k].name} を手札へ")


add("e_pp", "PP-「P」", 3, "N", power=3000, races=("hunter", "alien", "technosamurai"), pri=5, roles="dis acc",
    fatex=fx_pp, tendall=te_pp,
    text="相手のクリーチャーが出る時、そのコストが相手のマナゾーンの枚数より大きければ、"
         "かわりにそれを持ち主のマナゾーンに置く。"
         "超魂X：このカードがクリーチャーの下にあれば、そのクリーチャーは"
         "「相手のターンの終わりに、相手のタップしているクリーチャーが1体もなければ、山札の上から2枚をマナゾーンに置いてもよい。"
         "そうしたら、マナゾーンから1枚を手札に戻す」を得る",
    source=W + "《PP-「P」》")
E.SHINKA.add("e_pp")


# ================================================================ 魔誕幻獣ボンメェ
def en_bonmee(s, i, u):
    t = s.target(i, lambda z: z.c.cost <= 4, "CTX")
    if t is not None:
        destroy(s, i, t)
    else:
        s.ramp(i, 1)


add("e_bonmee", "魔誕幻獣ボンメェ", 3, "FN", power=2000, trig=True, races=("demoncommand", "command", "dreammate"),
    pri=5, roles="rem acc trg",
    enter=en_bonmee,
    text="S・トリガー。出た時、次から1つ選ぶ：(a)相手のコスト4以下のエレメント1つを破壊する／"
         "(b)自分の山札の上から1枚をマナゾーンに置く（破壊できる相手がいれば破壊を選ぶ）",
    source=W + "《魔誕幻獣ボンメェ》")


# ================================================================ 大虹帝 ミノガミ ／「ミノマルちゃん！…」
def at_minogami(s, i, u):
    p = s.P[i]
    best, bv = None, -1
    for z in p.board:
        if z.c.kind == "C" and z.c.twin and s.spell_ok(i, z.c.twin[0]) and E.PRI[z.k] > bv:
            best, bv = z, E.PRI[z.k]
    if best is None:
        return
    s.ev(f"　{best.c.name} の呪文側を場に置いたままただで唱える")
    _cast_inplace(s, i, best.k)


def ts_minogami(s, i, u):
    """自分のターンのはじめ、パワー12000以上の自分のクリーチャーがいれば、墓地のミノガミを手札に戻す"""
    p = s.P[i]
    if p.x.get("minot") == s.turn or "e_minogami" not in p.grave:
        return
    if u.c.kind == "C" and s.power(i, u) >= 12000:
        p.x["minot"] = s.turn
        p.grave.remove("e_minogami")
        p.hand.append("e_minogami")
        s.ev("　墓地から 大虹帝 ミノガミ を手札へ")


def sp_minogami(s, i):
    s.ramp(i, 1)


add("e_minogami", "大虹帝 ミノガミ", 6, "N", power=12000, brk=3, races=("gransect",), evo="N", neo=True, gneo=True,
    twin=(2, "N", False), pri=9, roles="acc fin atk",
    attack=at_minogami, tstartall=ts_minogami, spell=sp_minogami,
    text="G-NEO進化（自然のクリーチャー1体の上に置いてもよいし、置かずに出してもよい。離れる時はかわりに下のカードが離れる）。"
         "T・ブレイカー。攻撃する時、自分のバトルゾーンにあるツインパクト・クリーチャー1体の呪文側を、"
         "そのカードを場に置いたままコストを支払わずに唱えてもよい（このカード自身の呪文側も選べる）。"
         "自分のターンのはじめ、パワー12000以上の自分のクリーチャーがあれば、このカードを墓地から手札に戻してもよい。"
         "呪文側《「ミノマルちゃん！わたしがついてるわ！」》（自然・コスト2）：自分の山札の上から1枚をマナゾーンに置く",
    source=W + "《大虹帝 ミノガミ／「ミノマルちゃん！わたしがついてるわ！」》")


# ================================================================ 破壊龍神ヘヴィ・デス・メタル GS
def en_hdm(s, i, u):
    if u.x.get("summoned"):
        return
    s.ev("　召喚ではなく出たので、山札に加えてシャッフルする")
    if s.leave(i, u, "deck"):
        s.rng.shuffle(s.P[i].deck)


add("e_hdm", "破壊龍神ヘヴィ・デス・メタル GS", 13, "DF", power=39000, brk=99, sa=True, gs=True,
    races=("god", "phoenix"), pri=13, roles="fin atk trg",
    enter=en_hdm,
    text="スピードアタッカー、ワールド・ブレイカー（相手のシールドをすべてブレイクする）。"
         "召喚ではない方法でバトルゾーンに出た時、このクリーチャーを山札に加えてシャッフルする。"
         "G・ストライク：シールドゾーンから手札に加える時に見せて、相手のクリーチャー1体を選び、"
         "そのクリーチャーはこのターン攻撃できない",
    source=W + "《破壊龍神ヘヴィ・デス・メタル GS》")


# ================================================================ 煙幕の聖沌 k3mur1 ／聖沌忍法 メカくしの術
def at_k3mur1(s, i, u):
    p = s.P[i]
    oth = [z for z in p.board if z is not u and z.c.kind == "C" and not z.tap
           and (race_like(z.c, "mecha") or "shinobi" in z.c.races)]
    if not oth:
        return
    s.tap_cre(i, min(oth, key=s.val))
    _mekureido(s, i, 5, lambda c: race_like(c, "mecha"), "メカ・メクレイド5")


def sp_k3mur1(s, i):
    t = s.target(i, lambda z: not z.tap)
    if t is not None:
        s.tap_cre(1 - i, t)
        s.ev(f"　{t.c.name} をタップ")
    else:
        mine = [z for z in s.P[i].board if z.c.kind == "C" and z.tap]
        if mine:
            z = max(mine, key=lambda x: s.power(i, x))
            z.tap = False
            s.ev(f"　{z.c.name} をアンタップ")
        else:
            t = s.target(i)
            if t is not None:
                s.tap_cre(1 - i, t)
    s.draw(i)


add("e_k3mur1", "煙幕の聖沌 k3mur1", 3, "L", power=4000, races=("mechadelstella", "shinobi"),
    twin=(3, "L", True), pri=5, roles="atk draw dis trg",
    attack=at_k3mur1, spell=sp_k3mur1,
    text="攻撃する時、自分の他のメカまたはシノビのクリーチャー1体をタップしてもよい。"
         "そうしたら、メカ・メクレイド5をする（山札の上から3枚を見て、その中のコスト5以下のメカ1枚を"
         "コストを支払わずに使ってよい。残りは山札の下へ）。"
         "呪文側《聖沌忍法 メカくしの術》（光・コスト3・S・トリガー）：クリーチャー1体を選び、タップするかアンタップする。1枚引く",
    source=W + "《煙幕の聖沌 k3mur1／聖沌忍法 メカくしの術》")


# ================================================================ 忠犬な騎士スゴイワン
def en_sugoiwan(s, i, u):
    s.dig(i, 1, lambda k: BY_KEY[k].kind == "C", "bottom")


add("e_sugoiwan", "忠犬な騎士スゴイワン", 3, "N", power=3000, races=("dreammate",), pri=5, roles="draw dis",
    enter=en_sugoiwan, fatex=_tomana_crowd("e_sugoiwan"),
    text="出た時、自分の山札の上から1枚を表向きにする。それがクリーチャーなら手札に加え、"
         "そうでなければ山札の下に置く。"
         "相手のクリーチャーが出る時、そのターンに相手が他のクリーチャーを2体以上出していれば、"
         "かわりにそれを相手のマナゾーンに置く",
    source=W + "《忠犬な騎士スゴイワン》")


# ================================================================ サファイア・ウィズダム
def w_sapphire_enter(s, i, u):
    if u.c.kind != "C" or not u.x.get("summoned"):
        return
    j = 1 - i
    n = sum(1 for z in s.P[j].board if z.k == "e_sapphire")
    if n:
        s.ev("　サファイア・ウィズダム：2枚引く")
        s.draw(j, 2 * n)


def w_sapphire_spell(s, i, k):
    j = 1 - i
    n = sum(1 for z in s.P[j].board if z.k == "e_sapphire")
    if n:
        s.ev("　サファイア・ウィズダム：2枚引く")
        s.draw(j, 2 * n)


def fx_sapphire(s, owner, u, i, k, src, summon, res):
    if i != owner and summon and BY_KEY[k].cost <= len(s.P[owner].hand):
        return "no"
    return res


def sl_sapphire(s, i, cost):
    j = 1 - i
    return any(z.k == "e_sapphire" for z in s.P[j].board) and cost <= len(s.P[j].hand)


def _pr_sapphire(deck, k):
    n = sum(v for kk, v in deck.items() if kk != k and "angelcommand" in BY_KEY[kk].races)
    return None if n >= 4 else "進化元のエンジェル・コマンドが4体いない"


add("e_sapphire", "サファイア・ウィズダム", 9, "LW", power=15000, brk=3, races=("angelcommand", "starnoid", "command"),
    evo="X", pri=12, roles="draw dis fin",
    evox=lambda s, i, u: "angelcommand" in u.c.races, playrule=_pr_sapphire,
    enterwatch=w_sapphire_enter, spellwatch=w_sapphire_spell, fatex=fx_sapphire, spelllock=sl_sapphire,
    text="進化：エンジェル・コマンド1体の上に置く。T・ブレイカー。"
         "相手がクリーチャーを召喚した時、または呪文を唱えた時、自分は2枚引く。"
         "相手は、自分（このカードの持ち主）の手札の枚数以下のコストを持つクリーチャーを召喚できず、呪文も唱えられない",
    source=W + "《サファイア・ウィズダム》")


# ================================================================ 偽りの月 インターステラ
def en_interstella(s, i, u):
    p = s.P[i]
    best, bz, bv = None, None, -1
    for zn, zone in (("hand", p.hand), ("grave", p.grave)):
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if c.kind != "S" or c.cost > 7 or not (set(c.civ) & set("WD")):
                continue
            if not s.spell_ok(i, c.cost) or E.PRI[k] <= bv:
                continue
            best, bz, bv = k, zn, E.PRI[k]
    if best is None:
        return
    zone = p.hand if bz == "hand" else p.grave
    if best not in zone:
        return
    zone.remove(best)
    s.ev(f"　インターステラ：{BY_KEY[best].name} をただで唱える")
    _cast_free(s, i, best, dest="grave")


def at_interstella(s, i, u):
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if c.kind == "S" and s.spell_ok(i, c.cost) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is None or best not in p.grave:
        return
    p.grave.remove(best)
    s.ev(f"　インターステラ：{BY_KEY[best].name} をただで唱え、山札の下へ")
    _cast_free(s, i, best, dest="deck")


add("e_interstella", "偽りの月 インターステラ", 7, "WD", power=9000, brk=2, blocker=True, jd=True,
    races=("cybermooncommand", "command", "unknown"), pri=10, roles="blk fin rem",
    enter=en_interstella, attack=at_interstella, status="partial",
    text="ブロッカー、ジャストダイバー（出たターン、相手に選ばれず攻撃されない）、W・ブレイカー。"
         "出た時、水または闇のコスト7以下の呪文1枚を手札か墓地からコストを支払わずに唱えてもよい。"
         "攻撃する時、自分の墓地の呪文1枚をコストを支払わずに唱えてもよい。唱えた後、その呪文は山札の下に置く",
    note="超次元ゾーンがこのシミュレーターにないため（ゾーンを作る大きな仕事で、差し込み口では足りない）、"
         "出た時に唱えた呪文は超次元ゾーンではなく墓地に置く。"
         "攻撃する時の「超次元ゾーンから唱える」は、墓地から唱えて山札の下に置く形で近似した",
    source=W + "《偽りの月 インターステラ》")


# ================================================================ 拷問ロスト・マインド
def sp_lostmind(s, i):
    o = s.P[1 - i]
    for k in list(o.hand):
        c = BY_KEY[k]
        if (c.kind == "S" or c.twin) and k in o.hand:
            s.discard(1 - i, k)


add("e_lostmind", "拷問ロスト・マインド", 4, "D", kind="S", pri=5, roles="dis", spell=sp_lostmind,
    text="相手は自分の手札を見せ、その中にある呪文（ツインパクトも呪文として数える）をすべて捨てる",
    source=W + "《拷問ロスト・マインド》")
