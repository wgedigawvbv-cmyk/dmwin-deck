"""共通の仕組み：クロスギア（ジェネレート／クロス）、封印、禁断

  クロスギア（kind="X"）
    ・ジェネレート：手札からコストを払って場に出す（まだ誰にもクロスされていない）。
    ・クロス：場のクロスギアに、もう一度コストを払って自分のクリーチャー1体に付ける。
      「〜にはコストを支払わずにクロスしてよい」はカードごとに FREECROSS に登録する。
    ・クロスしているクリーチャーが離れても、クロスギアは場に残る（クロスされていない状態に戻る）。
    ・どのクリーチャーにクロスするかは、このシミュレーター共通の決まりで機械的に決める
      （ただでクロスできる相手を優先し、次にパワーの高いアンタップのクリーチャー）。

  封印・禁断
    ・禁断の鼓動（kind="K"）はゲームのはじめから場にあり、場を離れない。封印6つを山札の上から置く。
    ・コマンドが出た時、文明が合う封印を1つ外す（強制）。自分の封印を先に外す。
    ・封印が0になると裏返って禁断クリーチャーになる（禁断解放）。
    ・クリーチャーについた封印は、そのクリーチャーをバトルゾーンから外して持つ（封印中は場にないものとして扱う）。
"""
import engine3 as E
from cards3 import BY_KEY

import envreg
from envreg import add, is_cmd

FREECROSS = {}        # クロスギアのキー → fn(s, i, gu, cu) -> True ならただでクロスできる
GEARRED = []          # クロスギアのコストを下げる：fn(s, i, k) -> 下げる数


# ---------------------------------------------------------------- クロスギア
def gcost(s, i, k):
    """クロスギアのジェネレート／クロスのコスト"""
    n = BY_KEY[k].cost
    for f in GEARRED:
        n -= f(s, i, k)
    return max(0, n)


def gears(s, i):
    return [u for u in s.P[i].board if u.c.kind == "X"]


def gears_on(s, i, cu):
    """cu にクロスされているクロスギア"""
    return [g for g in s.P[i].board if g.c.kind == "X" and g.x.get("on") == cu.uid]


def crossed(s, i, gu):
    """gu がクロスされているクリーチャー（なければ None）"""
    on = gu.x.get("on")
    if not on:
        return None
    for u in s.P[i].board:
        if u.uid == on and u.c.kind == "C":
            return u
    return None


def has_gear(s, i, cu, key):
    """cu に key のクロスギアがクロスされているか"""
    return any(g.k == key for g in gears_on(s, i, cu))


def gear_aura(key, pw=0):
    """「クロスされているクリーチャーのパワーを+pw」を作る"""
    def f(s, i, u, atk):
        if u.c.kind != "C" or not pw:
            return 0
        return pw * sum(1 for g in gears_on(s, i, u) if g.k == key)
    return f


def _cross_target(s, i, gu):
    """どのクリーチャーにクロスするか（ただでクロスできる相手を優先、次にパワー）"""
    best, bv = None, None
    for u in s.P[i].board:
        if u.c.kind != "C" or u.uid == gu.x.get("on"):
            continue
        free = FREECROSS.get(gu.k)
        v = (1 if (free is not None and free(s, i, gu, u)) else 0, 0 if u.tap else 1, s.power(i, u))
        if bv is None or v > bv:
            best, bv = u, v
    return best


def gear_acts(s, i, av, cv):
    p = s.P[i]
    out = []
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "X":
            continue
        n = gcost(s, i, k)
        if n <= av and (n == 0 or cv.issuperset(c.civ)):
            out.append(("x:gen", k, n))
    for gu in gears(s, i):
        cu = _cross_target(s, i, gu)
        if cu is None:
            continue
        free = FREECROSS.get(gu.k)
        n = 0 if (free is not None and free(s, i, gu, cu)) else gcost(s, i, gu.k)
        if n <= av and (n == 0 or cv.issuperset(gu.c.civ)):
            out.append(("x:cross", gu.uid, cu.uid, n))
    return out


def ap_gen(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.hand:
        return
    p.hand.remove(k)
    p.mused += a[2]
    gu = E.U(k)
    gu.sick = False
    p.board.append(gu)
    s.ev(f"ジェネレート：{BY_KEY[k].name}（{a[2]}マナ）")
    s.first_play(i, BY_KEY[k].cost)
    s.noncre(i)
    fn = E.ENTER.get(k)
    if fn is not None:
        fn(s, i, gu)


def ap_cross(s, a):
    i = s.tp
    p = s.P[i]
    gu = cu = None
    for u in p.board:
        if u.uid == a[1] and u.c.kind == "X":
            gu = u
        elif u.uid == a[2] and u.c.kind == "C":
            cu = u
    if gu is None or cu is None:
        return
    p.mused += a[3]
    gu.x["on"] = cu.uid
    s.ev(f"クロス：{gu.c.name} → {cu.c.name}（{a[3]}マナ）")


E.FREE_ACTS.append(gear_acts)
E.ACTAPPLY["x:gen"] = ap_gen
E.ACTAPPLY["x:cross"] = ap_cross


# ---------------------------------------------------------------- 封印・禁断
def remove_seal(s, j, civ):
    """プレイヤー j の封印のうち、文明が合うものを1つ外す。外したら True"""
    p = s.P[j]
    for u in p.board:
        if u.c.kind == "K" and u.x.get("seals", 0) > 0 and (set(civ) & set(u.c.civ)):
            cs = u.x.get("sealcards") or []
            if cs:
                p.grave.append(cs.pop())
            u.x["seals"] -= 1
            s.ev(f"　封印が1つ外れた（残り{u.x['seals']}）")
            if u.x["seals"] <= 0:
                FLIP[u.k](s, j, u)
            return True
    return s.unseal(j, civ)


def w_command_seal(s, i, u):
    """コマンドが出た時、自分の封印を1つ外す。

    以前は「自分の封印が無ければ相手の封印を外す」と書いていたが、これは誤り。
    公式の封印は**自分のカードに付いた封印を自分のコマンドで外す**もので、相手の封印には触れない。
    この誤りのせいで、自分自身に封印を付けて出るコマンド（《燃える禁断 ドルマゲドンW》）が、
    同じ「出た時」で相手の封印を外してしまっていた。"""
    if u.c.kind != "C" or not is_cmd(u.c):
        return
    remove_seal(s, i, u.c.civ)


FLIP = {}        # 禁断の鼓動のキー → fn(s, i, u)（裏返す）


def no_leave(s, i, u, dest, destroy):
    """禁断の鼓動はバトルゾーンを離れない"""
    return u.c.kind == "K"


def gs_kindan(s, i, cards):
    """ゲームのはじめ：禁断の鼓動を場に置き、山札の上から封印6つ"""
    if "n_kindan" not in cards:
        return
    cards.remove("n_kindan")
    u = E.U("n_kindan")
    u.sick = False
    n = max(0, min(6, len(cards) - 11))
    u.x["sealcards"] = [cards.pop() for _ in range(n)]
    u.x["seals"] = n
    s.P[i].board.append(u)


def flip_kindan(s, i, u):
    p = s.P[i]
    if u not in p.board:
        return
    j = p.board.index(u)
    nu = E.U("n_dokindam")
    nu.sick = False
    p.board[j] = nu
    s.note("surface", i, nu.k)
    s.ev("　禁断解放：伝説の禁断 ドキンダムX")
    for x in s.P[1 - i].board[:]:
        if x.c.kind == "C" and x in s.P[1 - i].board:
            s.seal(1 - i, x, 1)


FLIP["n_kindan"] = flip_kindan

add("n_kindan", "禁断 ～封印されしX～", 0, "F", kind="K", pri=0, roles="fin",
    gamestart=gs_kindan, enterwatch=w_command_seal, leaverep=no_leave,
    text="ゲームのはじめからバトルゾーンにあり、封印6つが置かれる。場を離れない。コマンドが出るたびに文明の合う封印が1つ外れ、"
         "すべて外れると裏返って《伝説の禁断 ドキンダムX》になる",
    source="https://dmwiki.net/《禁断 ～封印されしX～》")

add("n_dokindam", "伝説の禁断 ドキンダムX", 99, "F", power=99999, brk=3, pri=12, roles="fin atk",
    tgtlock=lambda s, by, u: u.k == "n_dokindam" and s.spc is not None and s.spc <= 4,
    enter=lambda s, i, u: None,
    text="T・ブレイカー。禁断解放した時、相手のクリーチャーすべてに封印を1つずつ置く。相手のコスト4以下の呪文では選ばれない",
    source="https://dmwiki.net/《伝説の禁断 ドキンダムX》")


# ---------------------------------------------------------------- コストを下げる共通の仕組み
def distinct_untapped(s, i, skip=None):
    """コストが互いに違う、自分のアンタップしているクリーチャー（ハイパーエナジー用）"""
    seen, out = set(), []
    for u in sorted(s.P[i].board, key=lambda u: (s.power(i, u), u.c.cost)):
        if u.c.kind != "C" or u.tap or u is skip or u.c.cost in seen:
            continue
        seen.add(u.c.cost)
        out.append(u)
    return out


def hyper_energy(s, i, k, av, per=2):
    """ハイパーエナジー：必要な分だけクリーチャーをタップしてコストを下げる。(コスト, タップするクリーチャー)"""
    cost = BY_KEY[k].cost
    cands = distinct_untapped(s, i)
    need = 0 if cost <= av else -(-(cost - av) // per)
    t = min(len(cands), need)
    return max(0, cost - per * t), cands[:t]


def he_costx(k, per=2):
    return lambda s, i, av: hyper_energy(s, i, k, av, per)[0]


def he_payx(k, per=2):
    def f(s, i, kk, n):
        av = len(s.P[i].mana) - s.P[i].mused
        for u in hyper_energy(s, i, k, av, per)[1]:
            u.tap = True
        return None
    return f


def race_like(c, sub):
    """種族名に sub を含むか（サイバー・コマンドとサイバー・ウイルスをまとめて数えるため）"""
    return any(sub in r for r in c.races)


# ---------------------------------------------------------------- スレイヤー・一時的な攻撃ロック
SLAYER = set()        # スレイヤーを持つカードのキー


def _slayer(s, ai, au, di, du, a_dies, d_dies):
    if au.k in SLAYER:
        d_dies = True
    if du.k in SLAYER:
        a_dies = True
    return a_dies, d_dies


E.BATTLEFX.append(_slayer)


def lock_until_my_turn(s, i, u):
    """「次の自分のターンのはじめまで攻撃もブロックもできない」を u にかける（i＝かけた側）"""
    u.x["lockuntil"] = s.turn + (1 if s.tp == i else 0)


def _locked(u):
    return u.x.get("lockuntil", -1)


E.ATKLOCK.append(lambda s, i, u: _locked(u) >= s.turn)
E.BLOCKLOCK.append(lambda s, u: _locked(u) >= s.turn)


def owner_of(s, u):
    """u を持っているプレイヤー（BLOCKOK などで持ち主が渡されない時に使う）"""
    for j in (0, 1):
        if u in s.P[j].board:
            return j
    return 0


def discard_choice(s, j):
    """プレイヤー j が自分で選んで手札を1枚捨てる（いちばん要らない札を捨てる）"""
    p = s.P[j]
    if not p.hand:
        return None
    k = min(p.hand, key=E.PRI.get)
    s.discard(j, k)
    return k


# ---------------------------------------------------------------- EXライフ・ドリーム・コストを下げる
def exlife_enter(s, i, u):
    """EXライフ：出た時、山札の上から1枚を自分の下にシールドとして置く"""
    p = s.P[i]
    if len(p.deck) > 1:
        u.x["excard"] = p.deck.pop()
        u.x["ex"] = 1


EXLOST = {}      # EXライフのシールドを失った時：キー → fn(s, i, u)


def exlife_rep(s, i, u, dest, destroy_):
    """EXライフ：離れる時、かわりにそのシールドを墓地に置く。

    LEAVEREP は「どれか1つが True を返したら離れない」ので、各モジュールが同じ中身の
    exlife_rep を登録すると**先に登録された側だけが働く**。そのため
    「EXライフのシールドが離れた時」に何かするカードは、自分の leaverep に書くのではなく
    `envcards.env0.EXLOST[自分のキー] = fn` に登録すること（ここから必ず呼ばれる）。"""
    if not u.x.get("ex"):
        return False
    u.x["ex"] = 0
    k = u.x.pop("excard", None)
    if k is not None:
        s.grave_put(i, k)
    s.ev(f"　EXライフ：シールドを失って {u.c.name} は残る")
    f = EXLOST.get(u.k)
    if f is not None and not s.over:
        f(s, i, u)
    return True


def fx_dream(s, owner, u, i, k, src, summon, res):
    """ドリーム・クリーチャー：同じ名前のものは2体目は出られない"""
    if i == owner and k == u.k:
        return "no"
    return res


def race_cost_down(race, n=1, src=None, floor=0):
    """「自分の〈race〉のコストを n 少なくする」（src＝この効果を出しているカードが場にある時だけ働く）"""
    def f(s, i, k, cur):
        if src is not None and not any(z.k == src for z in s.P[i].board):
            return cur
        if race in BY_KEY[k].races and cur > floor:
            return max(floor, cur - n)
        return cur
    return f


def guardman(key, cond=None):
    """ガードマン：相手のクリーチャーの攻撃先を、自分の他のクリーチャーからこのクリーチャーに変更する
    （このクリーチャーをタップする。プレイヤーへの攻撃は引き受けられない）。
    使うかどうかは共通の決まりで機械的に決める：バトルに勝てるか、守る相手のほうが大事な時だけ引き受ける
    （どのカードがガードマンを持つかは engine3.GUARDMEN で引ける）"""
    E.GUARDMEN.add(key)

    def f(s, di, au, tu):
        if tu is None:
            return None
        ap = s.power(1 - di, au, True)
        for z in s.P[di].board:
            if z.k != key or z.c.kind != "C" or z.tap or z is tu:
                continue
            if cond is not None and not cond(s, di, z):
                continue
            if s.power(di, z) > ap or s.val(tu) > s.val(z):
                z.tap = True
                return z
        return None
    return f


STAR = set()          # スター進化を持つカード（離れる時、一番上の1枚だけが離れる）


def _star_valadj(s, u):
    """スター進化のクリーチャーは、離れても下のカードがバトルゾーンに残る。
    だから「失う痛さ」も「相手から取り除く値打ち」も、その分だけ安く見る。
    自分側ではこれが「退化」（上をわざと外して下の大きいクリーチャーを出す）を生み、
    相手側では「相手に退化をさせてやる手」を避ける働きになる。デッキごとの作戦は書いていない。"""
    if u.k in STAR and u.under:
        return -E.PRI.get(u.under[0], 0)
    return 0


E.VALADJ.append(_star_valadj)


def own_loss(s, i, z):
    """自分のクリーチャー z を失う痛さ（スター進化の補正は s.val に入っている）"""
    return s.val(z)


def worst_own(s, i, pred=None, keep=None):
    """自分のクリーチャーのうち、失うのがいちばん安いもの（keep は最後に選ぶ）"""
    cs = [z for z in s.P[i].board if z.c.kind == "C" and (pred is None or pred(z))]
    if not cs:
        return None
    return min(cs, key=lambda z: (own_loss(s, i, z), 0 if z is not keep else 1))


def star_evo_rep(key, name=None):
    """スター進化：離れる時、一番上のカード（このカード）だけが離れ、下のカードがバトルゾーンに残る
    （いわゆる「退化」。下に置いたクリーチャーを、コストを支払わずに場に出す形になる）"""
    STAR.add(key)

    def f(s, i, u, dest, destroy_):
        if u.k != key or not u.under:
            return False
        p = s.P[i]
        if u not in p.board:
            return False
        j = p.board.index(u)
        nu = E.U(u.under[0])
        nu.under = u.under[1:]
        nu.tap = u.tap
        nu.sick = u.sick
        nu.frz = u.frz
        p.board[j] = nu
        s.note("surface", i, nu.k)
        s.put_zone(i, key, dest)
        s.ev(f"　スター進化：{name or BY_KEY[key].name} だけが離れ、{nu.c.name} が残る")
        return True
    return f
