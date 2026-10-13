"""担当22：DM26-RP1「逆札篇 第1弾 逆転神VS切札竜」の未実装カード15枚（31/77〜46/77）

出典：dmwiki.net の各カードページ（日本語のページ名でそのまま開ける）と、
      カードラッシュ（cardrush-dm.jp）の商品ページ（能力テキストの本文が載っている）

  この15枚に入っている新しい仕組み
    ・「我竜塔」の上層サイクル（G城＝kind="G"。実行すると表向きのシールドになる）
      我竜塔第六層 シルヴァー・グローリー（光2）／究極我竜塔 ティーツー（水3）／我竜塔最高層 ローズ・キャッスル（闇3）
      ※ 我竜塔第七層 ハッスル・キャッスル（hustle）と第八層 バルザーク（e_barzark）は既に実装済み
    ・「ウラ・ニンジャ・ストライク」（相手のクリーチャーが攻撃またはブロックした時、マナの枚数と文明が条件を満たせば
      手札からただで召喚し、そのターンの終わりに山札の下へ）。《裏斬隠 テンサイ・ハート》と同じ仕組み
    ・「超化獣」＋Zラッシュ＋ハイパーモード（シールドが離れたら次の自分のターンのはじめまでパワーが上がり、
      ハイパーモード側の能力を得る）。源神のH エレクトロン／撃滅神オブリ＆レイト／朱神のC ガリョウ／
      護神のP エメラルド・ファラオ の4枚
    ・コスト踏み倒しへの逆襲（オブリ＆レイト＝マナをタップせずに実行されたら相手が自分のクリーチャーを破壊、
      ガリョウ＝相手がコストを支払わずに出したら自分も山札の上から踏み倒す）
    ・シールド・セイバー（マッハ・ガルピア）／攻撃誘導（エメラルド・ファラオ）／
      ブレイク数を1つに制限する（ローズ・キャッスル）

  調べ直して確かめたところ
    15枚すべてについて dmwiki のカードページを別の質問で2回ずつ読み、さらに9枚はカードラッシュの商品ページで
    能力テキストの本文を突き合わせた（コスト・文明・種類・種族・パワー・ブレイク数・能力の本文）。
    ・《フェイト・ガルペンター》だけ、dmwiki のカード枠は「水文明 (5)」なのにページ下部のタグが「コスト4」で
      食い違っている。カード枠（カードそのものの写し）を採ってコスト5にした。カードラッシュの商品ページには
      能力テキストだけがあり、コストは載っていなかった。
    ・《ガルド・ライフ》は dmwiki のカードページで収録番号が「48/77」と読めたが、DM26-RP1 のカードリストと
      カードラッシュの商品名（26RP146/77）では46/77だった。カード名は同じなので、そのまま実装した。
    ・4枚の超化獣は、カードラッシュの商品ページで能力テキストが段落で区切られており、
      「W・ブレイカー」とその下の能力がハイパーモード側だと確かめられた（通常時は1ブレイク）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, opp_all
from envcards.env0 import discard_choice, lock_until_my_turn, worst_own

W = "https://dmwiki.net/"
SRC = {
    "k22_glory": W + "《我竜塔第六層 シルヴァー・グローリー》",
    "k22_galpenter": W + "《フェイト・ガルペンター》",
    "k22_suiton": W + "《スイトン・クロウラー》",
    "k22_electron": W + "《源神のH エレクトロン》",
    "k22_tiitsu": W + "《究極我竜塔 ティーツー》",
    "k22_neodvo": W + "《黒神龍ネオ・ドボルザーク》",
    "k22_deathproof": W + "《死神の影遁デスプルーフ》",
    "k22_oburi": W + "《撃滅神オブリ＆レイト》",
    "k22_rose": W + "《我竜塔最高層 ローズ・キャッスル》",
    "k22_galpia": W + "《マッハ・ガルピア》",
    "k22_basil": W + "《破壊の神遁バジル》",
    "k22_garyou": W + "《朱神のC ガリョウ》",
    "k22_kamiarashi": W + "《神嵐の超人》",
    "k22_pharaoh": W + "《護神のP エメラルド・ファラオ》",
    "k22_galdlife": W + "《ガルド・ライフ》",
}


# ================================================================ 共通の道具
def _castle_up(s, i, key):
    """key のG城が、プレイヤー i の表向きのシールドとして置かれているか"""
    for k, up in s.P[i].sh:
        if up and k == key:
            return True
    return False


def _ncastle_up(s, i, key):
    """key のG城が、表向きのシールドとして何枚置かれているか"""
    return sum(1 for k, up in s.P[i].sh if up and k == key)


def _onboard(s, i, key):
    """プレイヤー i の場にある key のカード（繰り返しの途中で場が変わっても安全なように写しを返す）"""
    return [u for u in s.P[i].board if u.k == key]


def _revive_self(s, i, key):
    """自分の墓地にある key を1枚、コストを支払わずに出す"""
    p = s.P[i]
    if key not in p.grave or s.fate(i, key, "grave", False) != "ok":
        return False
    p.grave.remove(key)
    s.enter(i, key, "grave", False)
    return True


def ura_ninja(key, need, civ):
    """ウラ・ニンジャ・ストライク：相手のクリーチャーが攻撃した時（react=）またはブロックした時（blockreact=）、
    自分のマナが need 枚以上で civ があれば、手札のこれをコストを支払わずに召喚する。
    そのターンの終わりに山札の下へ。
    「その攻撃中にニンジャ能力を使っていなければ」は、攻撃した時とブロックした時で二重に使えてしまわないよう、
    攻撃しているクリーチャーごとに印を付けて見ている"""
    def f(s, di, au):
        d = s.P[di]
        if key not in d.hand or len(d.mana) < need or civ not in E.civs(d):
            return False
        if d.x.get("k22_ninja") == (s.turn, au.uid):
            return False
        ok = _NINJA_OK.get(key)
        if ok is not None and not ok(s, di, au):
            return False
        if s.fate(di, key, "hand", True) != "ok":
            return False
        d.hand.remove(key)
        s.ev(f"　ウラ・ニンジャ・ストライク{need}：{BY_KEY[key].name}")
        s.trig[di] += 1
        d.x["k22_ninja"] = (s.turn, au.uid)
        u = s.enter(di, key, "hand", True)
        if u is not None:
            u.eot = True
        return True
    return f


def ura_ninja_block(key, need, civ):
    """同じものの「相手がブロックした時」版（blockreact= の形）"""
    base = ura_ninja(key, need, civ)

    def f(s, di, au, b):
        return base(s, di, au)
    return f


_NINJA_OK = {}        # key -> fn(s, di, au)：ただ撃ちにならないかの見極め（全デッキ共通）


# ---------------------------------------------------------------- マナをタップせずに実行したかの見分け
def _mu_rec(s, i, av, cv):
    """オブリ＆レイトかガリョウが相手の場にいる間だけ、手を選ぶ直前のマナの使用量を覚えておく
    （このあと実行されるカードが、マナをタップしたかどうかを見るため）"""
    if s.has(1 - i, "k22_oburi") or s.has(1 - i, "k22_garyou"):
        s.P[i].x["k22_mu"] = (s.turn, s.P[i].mused)
    return []


def _paid_mana(s, j):
    """いま実行したカードのために、プレイヤー j がマナをタップしたか"""
    rec = s.P[j].x.get("k22_mu")
    prev = rec[1] if (rec is not None and rec[0] == s.turn) else 0
    return s.P[j].mused > prev


def _no_cost_entry(s, j, u):
    """プレイヤー j のクリーチャー u が、コストを支払わずにバトルゾーンに出たか"""
    if not u.x.get("summoned"):
        return True                       # 効果で出た（踏み倒し）
    if s.tp != j:
        return True                       # 相手のターン中の召喚（S・トリガー、ニンジャ・ストライクなど）
    return not _paid_mana(s, j)


# ================================================================ 31/77 我竜塔第六層 シルヴァー・グローリー
def ap_glory(s, i, u, atk):
    """相手のターン中、自分のクリーチャーすべてのパワーを+2000する"""
    if u.c.kind != "C" or s.tp == i:
        return 0
    return 2000 * _ncastle_up(s, i, "k22_glory")


def lw_glory(s, i, u, dest, destroy_):
    """自分のクリーチャーが破壊された時、そのクリーチャーを墓地から裏向きでこのシールドの下に置いてもよい
    （シールドの下に置いたカードは、このシールドがシールドゾーンを離れた時に出てくる＝so_glory）"""
    p = s.P[i]
    if not _castle_up(s, i, "k22_glory"):
        return
    if not destroy_ or u.c.kind != "C" or dest != "grave":
        return
    if u.k not in p.grave:
        return
    p.grave.remove(u.k)
    p.x["k22_glory_under"] = tuple(p.x.get("k22_glory_under") or ()) + (u.k,)
    s.ev(f"　シルヴァー・グローリー：{u.c.name} を裏向きでこのシールドの下に置く")


def so_glory(s, i, k, up, dest):
    """シルヴァー・グローリーのシールドがシールドゾーンを離れた：下に置いていたカードも同じ行き先へ
    （ブレイクなら手札に加えて、S・トリガーを使えるようにする＝bw_22 でまとめて使う）"""
    if not (up and k == "k22_glory") or s.over:
        return
    p = s.P[i]
    stored = tuple(p.x.get("k22_glory_under") or ())
    if not stored:
        return
    p.x["k22_glory_under"] = ()
    if dest in ("break", "hand"):
        p.hand.extend(stored)
        if dest == "break":
            p.x["k22_glory_q"] = tuple(p.x.get("k22_glory_q") or ()) + stored
        s.ev(f"　シルヴァー・グローリー：下に置いていた{len(stored)}枚が手札に加わる")
        return
    for x in stored:
        s.put_zone(i, x, dest if dest in ("grave", "mana", "deck", "decktop") else "grave")
    s.ev(f"　シルヴァー・グローリー：下に置いていた{len(stored)}枚も同じ行き先へ")


def bw_22(s, ai, di, n):
    """ブレイクの後：シルヴァー・グローリーの下から手札に加わったカードのS・トリガーを使う"""
    for j in (ai, di):
        q = s.P[j].x.get("k22_glory_q")
        if not q:
            continue
        s.P[j].x["k22_glory_q"] = ()
        for k in q:
            if s.over or s.stop:
                break
            if k in s.P[j].hand:
                s.trigger(j, k)


def bp_galpia(s, ai, di, n):
    """シールド・セイバー（マッハ・ガルピア）：シールドがブレイクされる直前に、
    かわりに自分のクリーチャーを破壊してシールドを守る。
    ほかにシールドが残らない時だけ使う（無駄に減らさない全デッキ共通の決まり）"""
    d = s.P[di]
    if n <= 0 or n < len(d.sh):
        return n
    for z in sorted(_onboard(s, di, "k22_galpia"), key=s.val):
        if n <= 0 or s.over:
            break
        if z in d.board and s.leave(di, z, "grave", destroy=True):
            n -= 1
            s.ev("　シールド・セイバー：マッハ・ガルピアを破壊してシールド1枚を守る")
    return n


add("k22_glory", "我竜塔第六層 シルヴァー・グローリー", 2, "L", kind="G", pri=3, roles="blk trg shd",
    aurap=ap_glory, leavewatch=lw_glory, shieldout=so_glory, breakwatch=bw_22, status="partial",
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地に置く）。"
         "相手のターン中、自分のクリーチャーすべてのパワーを+2000する。"
         "自分のクリーチャーが破壊された時、そのクリーチャーを自分の墓地から裏向きでこのシールドの下に置いてもよい"
         "（破壊されたクリーチャーは必ず下に置く。このシールドがブレイクされると、"
         "下のカードもまとめて手札に加わり、S・トリガーなら使える）",
    note="このシミュレーターのシールドは（カード, 表向きか）の並びで、「シールドの下」というゾーンがない。"
         "そのため下に置いたカードはプレイヤーごとの置き場（p.x）で持っており、"
         "（a）同じ名前のG城を2枚置いた場合、下のカードはまとめて1つの置き場になり、"
         "どちらのシールドが割れても全部まとめて出てくる、"
         "（b）そのカードは墓地でもシールドでもないので、墓地やシールドの枚数を数える効果からは見えない、"
         "という2点がカードとずれる。シールドゾーンを離れた時は、"
         "ブレイクなら手札（S・トリガーが使える）、それ以外ならシールドと同じ行き先へ送っている",
    source=SRC["k22_glory"])


# ================================================================ 32/77 フェイト・ガルペンター
def e_galpenter(s, i, u):
    """出た時、カードを3枚引き、自分の手札を3枚捨てる"""
    s.draw(i, 3)
    for _ in range(3):
        discard_choice(s, i)


add("k22_galpenter", "フェイト・ガルペンター", 5, "W", power=3000, races=("marfolk",), trig=True,
    pri=5, roles="draw trg", enter=e_galpenter,
    text="S・トリガー。出た時、カードを3枚引き、自分の手札を3枚捨てる（捨てるのは重要度のいちばん低い札から）",
    note="dmwiki のカード枠はコスト5、ページ下部のタグはコスト4で食い違っている。"
         "カード枠（カードそのものの写し）を採ってコスト5にした",
    source=SRC["k22_galpenter"])


# ================================================================ 33/77 スイトン・クロウラー
add("k22_suiton", "スイトン・クロウラー", 4, "W", power=4000, blocker=True, jd=True,
    races=("eartheater", "origin", "shinobi"), pri=5, roles="blk dis",
    react=ura_ninja("k22_suiton", 4, "W"), blockreact=ura_ninja_block("k22_suiton", 4, "W"),
    text="ウラ・ニンジャ・ストライク4（水）（相手のクリーチャーが攻撃またはブロックした時、自分のマナゾーンの"
         "カードが4枚以上で水文明のカードがあり、その攻撃中にニンジャ能力を使っていなければ、"
         "手札のこれをコストを支払わずに召喚してもよい。そのターンの終わりに山札の下に置く）。"
         "ブロッカー。ジャストダイバー（出た時、次の自分のターンのはじめまで相手に選ばれず攻撃されない）",
    source=SRC["k22_suiton"])


# ================================================================ 34/77 源神のH エレクトロン
def a_electron(s, i, u):
    """攻撃する時、カードを2枚引き、自分の手札を1枚捨てる"""
    s.draw(i, 2)
    discard_choice(s, i)


# ハイパーモード：自分がカードを引く時、かわりにカードを2枚引いてもよい
#   「引いた時」の差し込み口（drawwatch=）で、1枚引くごとにもう1枚引く形にした（合わせて2倍になる）。
#   入れ子にならないように _ELEC で止め、山札を引ききってしまう時は倍にしない
#   （「〜してもよい」の機械的な決め方）
_ELEC = [False]


def dw_electron(s, i, k):
    p = s.P[i]
    if _ELEC[0] or s.over or len(p.deck) <= 1:
        return
    for u in p.board:
        if u.k == "k22_electron" and u.hyper:
            break
    else:
        return
    _ELEC[0] = True
    try:
        s.draw(i, 1)
    finally:
        _ELEC[0] = False


E.HYPER_POW["k22_electron"] = 3000        # パワー4000 → ハイパーモード7000

add("k22_electron", "源神のH エレクトロン", 3, "W", power=4000, zrush=True, races=("god", "hyperbeast"),
    pri=4, roles="draw atk", attack=a_electron, drawwatch=dw_electron,
    text="このクリーチャーが攻撃する時、カードを2枚引き、自分の手札を1枚捨てる。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまで、このクリーチャーのハイパーモードを解放する）。"
         "ハイパーモード：パワー7000。W・ブレイカー。"
         "自分がカードを引く時、かわりにカードを2枚引いてもよい（山札を引ききってしまう時は倍にしない）",
    source=SRC["k22_electron"])


# ================================================================ 35/77 究極我竜塔 ティーツー
def _tiitsu_lock(s, i):
    """相手のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない
    （すでに止まっているクリーチャーを選び直さないように、止まっていないものから先に選ぶ）"""
    t = s.target(i, lambda z: z.x.get("lockuntil", -1) < s.turn) or s.target(i)
    if t is None:
        return
    lock_until_my_turn(s, i, t)
    s.ev(f"　ティーツー：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


def si_tiitsu(s, i, k, up):
    """このG城が表向きで自分のシールドゾーンに置かれた時"""
    if k != "k22_tiitsu" or not up or s.over:
        return
    s.ev("　ティーツー：表向きのシールドとして置かれた")
    _tiitsu_lock(s, i)


def aw_tiitsu(s, i, u):
    """各ターンはじめて自分のクリーチャーが攻撃する時にも誘発する"""
    if s.over or u.c.kind != "C" or not _castle_up(s, i, "k22_tiitsu"):
        return
    p = s.P[i]
    if p.x.get("k22_t2a") == s.turn:
        return
    p.x["k22_t2a"] = s.turn
    for _ in range(_ncastle_up(s, i, "k22_tiitsu")):
        if s.over:
            break
        s.ev("　ティーツー：このターンはじめて自分のクリーチャーが攻撃した")
        _tiitsu_lock(s, i)


def ca_tiitsu(s, i, k, cur):
    """自分の「ブロッカー」を持つクリーチャーの召喚コストを1少なくする（0以下にはならない）"""
    if cur <= 1 or not BY_KEY[k].blocker:
        return cur
    n = _ncastle_up(s, i, "k22_tiitsu")
    return max(1, cur - n) if n else cur


add("k22_tiitsu", "究極我竜塔 ティーツー", 3, "W", kind="G", pri=4, roles="dis acc",
    atkwatch=aw_tiitsu, costaura=ca_tiitsu, shieldin=si_tiitsu,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地に置く）。"
         "このG城が表向きで自分のシールドゾーンに置かれた時、または各ターンはじめて自分のクリーチャーが攻撃する時、"
         "相手のクリーチャーを1体選ぶ（まだ止まっていないもののうち重要度のいちばん高いもの）。"
         "次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない。"
         "自分の「ブロッカー」を持つクリーチャーの召喚コストを1少なくする（0以下にはならない）",
    source=SRC["k22_tiitsu"])


# ================================================================ 36/77 黒神龍ネオ・ドボルザーク
def lw_neodvo(s, i, u, dest, destroy_):
    """自分のコスト5以上のクリーチャーが破壊された時、このクリーチャーを自分の墓地から出してもよい"""
    if not destroy_ or u.c.kind != "C" or u.c.cost < 5 or s.over:
        return
    if "k22_neodvo" not in s.P[i].grave:
        return
    s.ev("　ネオ・ドボルザーク：コスト5以上が破壊されたので墓地から出る")
    _revive_self(s, i, "k22_neodvo")


add("k22_neodvo", "黒神龍ネオ・ドボルザーク", 4, "D", power=4000, blocker=True, trig=True,
    races=("dragonzombie", "dragon"), pri=5, roles="blk trg",
    leavewatch=lw_neodvo,
    text="S・トリガー。ブロッカー。"
         "自分のコスト5以上のクリーチャーが破壊された時、このクリーチャーを自分の墓地から出してもよい（必ず出す）",
    source=SRC["k22_neodvo"])


# ================================================================ 37/77 死神の影遁デスプルーフ
def e_deathproof(s, i, u):
    """出た時、このターン、自分のクリーチャー1体に「スレイヤー」を与える。
    このターン、そのクリーチャーが破壊された時、自分はカードを2枚引く
    （ブロックできるクリーチャーのうちいちばん安いものに与える。いなければいちばん安いクリーチャー。
      スレイヤーはバトルして相打ちになる時に効くので、ブロックできるものを優先する。全デッキ共通の決まり）"""
    cs = [z for z in s.P[i].board if z.c.kind == "C" and s.can_block(z)]
    t = min(cs, key=s.val) if cs else worst_own(s, i)
    if t is None:
        return
    t.x["k22_slay"] = s.turn
    s.ev(f"　デスプルーフ：このターン {t.c.name} はスレイヤーになり、破壊されたら2枚引く")


def bfx_deathproof(s, ai, au, di, du, a_dies, d_dies):
    """デスプルーフが与えたスレイヤー（このターンだけ）"""
    if au.x.get("k22_slay") == s.turn:
        d_dies = True
    if du.x.get("k22_slay") == s.turn:
        a_dies = True
    return a_dies, d_dies


def lw_deathproof(s, i, u, dest, destroy_):
    """スレイヤーを与えたクリーチャーが、そのターンに破壊された時、2枚引く"""
    if destroy_ and u.x.get("k22_slay") == s.turn and not s.over:
        s.ev("　デスプルーフ：スレイヤーを与えたクリーチャーが破壊された → 2枚引く")
        s.draw(i, 2)


_NINJA_OK["k22_deathproof"] = lambda s, di, au: any(z.c.kind == "C" for z in s.P[di].board)

add("k22_deathproof", "死神の影遁デスプルーフ", 2, "D", power=3000,
    races=("ghost", "origin", "shinobi"), pri=3, roles="rem draw",
    enter=e_deathproof, battlefx=bfx_deathproof, leavewatch=lw_deathproof,
    react=ura_ninja("k22_deathproof", 2, "D"),
    blockreact=ura_ninja_block("k22_deathproof", 2, "D"),
    text="ウラ・ニンジャ・ストライク2（闇）（相手のクリーチャーが攻撃またはブロックした時、自分のマナゾーンの"
         "カードが2枚以上で闇文明のカードがあり、その攻撃中にニンジャ能力を使っていなければ、"
         "手札のこれをコストを支払わずに召喚してもよい。そのターンの終わりに山札の下に置く）。"
         "出た時、このターン、自分のクリーチャー1体に「スレイヤー」を与える"
         "（ブロックできるクリーチャーのうちいちばん安いもの。いなければいちばん安いクリーチャー）。"
         "このターン、そのクリーチャーが破壊された時、自分はカードを2枚引く"
         "（自分のクリーチャーが場に1体もいない時はただ撃ちになるので使わない＝無駄撃ちを省く共通の決まり）",
    source=SRC["k22_deathproof"])


# ================================================================ 38/77 撃滅神オブリ＆レイト
def _oburi_fire(s, j):
    """相手（j）が、自分のマナゾーンのカードをタップせずにカードを実行した
    → 相手は自身のクリーチャーを1体選び、破壊する（相手が選ぶので、いちばん安いものになる）"""
    i = 1 - j
    for z in _onboard(s, i, "k22_oburi"):
        if s.over or z not in s.P[i].board:
            break
        t = worst_own(s, j)
        if t is None:
            break
        s.ev("　オブリ＆レイト：マナをタップせずに実行したので、相手は自身のクリーチャー1体を破壊する")
        s.leave(j, t, "grave", destroy=True)


def ew_oburi(s, j, u):
    if u.c.kind == "C" and u.x.get("summoned") and s.tp == j and not _paid_mana(s, j):
        _oburi_fire(s, j)


def sw_oburi(s, j, k):
    if s.tp == j and not _paid_mana(s, j):
        _oburi_fire(s, j)


def aw_oburi(s, i, u):
    """ブロックされたかを見分けるため、攻撃を宣言した時点でタップしている相手のクリーチャーを覚えておく
    （オブリ＆レイトはマッハファイターを持たないので、アンタップしているクリーチャーは攻撃先になれない。
      つまり、アンタップだったクリーチャーとバトルになったらブロックされたということ）"""
    if u.k == "k22_oburi" and u.hyper:
        u.x["k22_tapped"] = tuple(z.uid for z in s.P[1 - i].board if z.tap)


def bfx_oburi(s, ai, au, di, du, a_dies, d_dies):
    """ハイパーモード：このクリーチャーがブロックされた時、相手は自身の手札を3枚選び、捨てる"""
    if au.k == "k22_oburi" and au.hyper and au is s.atk:
        if du.uid not in (au.x.get("k22_tapped") or ()):
            s.ev("　オブリ＆レイト：ブロックされた → 相手は手札を3枚捨てる")
            for _ in range(3):
                if not discard_choice(s, di):
                    break
    return a_dies, d_dies


E.HYPER_POW["k22_oburi"] = 4000           # パワー2000 → ハイパーモード6000

add("k22_oburi", "撃滅神オブリ＆レイト", 2, "D", power=2000, zrush=True,
    races=("god", "dragonzombie", "hyperbeast"), pri=4, roles="dis atk",
    enterwatch=ew_oburi, spellwatch=sw_oburi, atkwatch=aw_oburi, battlefx=bfx_oburi, freeacts=_mu_rec,
    status="partial",
    text="相手のターンに、相手が自身のマナゾーンのカードをタップせずにカードを実行した時、"
         "相手は自身のクリーチャーを1体選び、破壊する（相手が選ぶので、いちばん安いものになる）。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまで、このクリーチャーのハイパーモードを解放する）。"
         "ハイパーモード：パワー6000。W・ブレイカー。"
         "このクリーチャーがブロックされた時、相手は自身の手札を3枚選び、捨てる",
    note="「マナをタップせずに実行した時」は、クリーチャーの召喚と呪文を唱えた時だけ見ている"
         "（手を選ぶ直前のマナの使用量と比べて、増えていなければタップしていないと見なす）。"
         "タマシードやG城を実行した時、および効果でただで使ったクリーチャー"
         "（エンジンでは「召喚」でなく「出す」扱いになるもの）は見ていない。"
         "相手がそのターン中に多色カードをマナゾーンに置いていた場合、"
         "そのターン最初の実行だけ、マナをタップしたと見誤ることがある",
    source=SRC["k22_oburi"])


# ================================================================ 39/77 我竜塔最高層 ローズ・キャッスル
def bfx_rose(s, ai, au, di, du, a_dies, d_dies):
    """自分のクリーチャーがバトルする時、そのバトルの終わりまで、
    バトルしている相手クリーチャーのパワーを-4000する（パワー0以下のクリーチャーは破壊される）"""
    ra = _ncastle_up(s, ai, "k22_rose")
    rd = _ncastle_up(s, di, "k22_rose")
    if not ra and not rd:
        return a_dies, d_dies
    ap = s.power(ai, au, True) + (2000 if au.k == "testa" else 0)
    dp = s.power(di, du) + (2000 if du.k == "testa" else 0)
    base_a = ap <= dp or du.k == "kuzen"
    base_d = dp <= ap or au.k == "kuzen"
    forced_a = a_dies and not base_a      # ほかの効果（スレイヤーなど）が決めた破壊は残す
    forced_d = d_dies and not base_d
    dp -= 4000 * ra
    ap -= 4000 * rd
    a_dies = ap <= dp or ap <= 0 or du.k == "kuzen" or forced_a
    d_dies = dp <= ap or dp <= 0 or au.k == "kuzen" or forced_d
    return a_dies, d_dies


def bp_rose(s, i, u):
    """相手のクリーチャーは、1度につき最大1つしかシールドをブレイクできない"""
    if u.c.kind != "C" or not _castle_up(s, 1 - i, "k22_rose"):
        return 0
    b = None
    f = E.BRKX.get(u.k)
    if f is not None:
        b = f(s, i, u)
    if b is None:
        if u.k == "derbande" or u.k == "koori":
            b = 1 + s.power(i, u, True) // 6000
        elif u.hyper and u.k in E.HYPER_POW:
            b = 2
        else:
            b = u.c.brk
    for g in E.BRKPLUS:
        if g is not bp_rose:
            b += g(s, i, u)
    return 1 - b if b > 1 else 0


add("k22_rose", "我竜塔最高層 ローズ・キャッスル", 3, "D", kind="G", pri=4, roles="rem blk",
    battlefx=bfx_rose, brkplus=bp_rose,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地に置く）。"
         "自分のクリーチャーがバトルする時、そのバトルの終わりまで、"
         "バトルしている相手クリーチャーのパワーを-4000する（パワー0以下のクリーチャーは破壊される）。"
         "相手のクリーチャーは、1度につき最大1つしかシールドをブレイクできない",
    source=SRC["k22_rose"])


# ================================================================ 40/77 マッハ・ガルピア
add("k22_galpia", "マッハ・ガルピア", 5, "F", power=5000, sa=True, trig=True, races=("firebird",),
    pri=6, roles="trg blk atk", breakpre=bp_galpia,
    text="S・トリガー。スピードアタッカー。"
         "シールド・セイバー（自分のシールドがブレイクされる時、かわりにこのクリーチャーを破壊してもよい。"
         "ほかにシールドが残っていない時だけ使う）",
    source=SRC["k22_galpia"])


# ================================================================ 41/77 破壊の神遁バジル
def e_basil(s, i, u):
    """出た時、相手の「ブロッカー」を持つクリーチャーまたはパワー2000以下のクリーチャーを1体選び、破壊する"""
    t = s.target(i, lambda z: z.c.blocker or s.power(1 - i, z) <= 2000)
    if t is None:
        return
    s.ev(f"　バジル：{t.c.name} を破壊する")
    destroy(s, i, t)


_NINJA_OK["k22_basil"] = lambda s, di, au: bool(
    [z for z in opp_all(s, di) if z.c.blocker or s.power(1 - di, z) <= 2000])

add("k22_basil", "破壊の神遁バジル", 3, "F", power=3000,
    races=("granddevil", "xenoparts", "shinobi"), pri=4, roles="rem",
    enter=e_basil, react=ura_ninja("k22_basil", 3, "F"),
    blockreact=ura_ninja_block("k22_basil", 3, "F"),
    text="ウラ・ニンジャ・ストライク3（火）（相手のクリーチャーが攻撃またはブロックした時、自分のマナゾーンの"
         "カードが3枚以上で火文明のカードがあり、その攻撃中にニンジャ能力を使っていなければ、"
         "手札のこれをコストを支払わずに召喚してもよい。そのターンの終わりに山札の下に置く）。"
         "出た時、相手の「ブロッカー」を持つクリーチャーまたはパワー2000以下のクリーチャーを1体選び、破壊する"
         "（重要度のいちばん高いものを選ぶ。破壊できる相手がいない時はただ撃ちになるので使わない"
         "＝無駄撃ちを省く共通の決まり）",
    source=SRC["k22_basil"])


# ================================================================ 42/77 朱神のC ガリョウ
def _garyou_fire(s, i):
    """自分の山札の上から1枚を表向きにする。それがコスト5以下のクリーチャーなら出す。それ以外なら山札の下に置く"""
    p = s.P[i]
    if not p.deck:
        return
    k = p.deck.pop()
    c = BY_KEY[k]
    s.ev(f"　ガリョウ：山札の上の {c.name} を表向きにする")
    if c.kind == "C" and c.cost <= 5 and not (c.evo and not c.neo) and s.fate(i, k, "deck", False) == "ok":
        s.enter(i, k, "deck", False)
    else:
        p.deck.insert(0, k)


def ew_garyou(s, j, u):
    """相手のクリーチャーがコストを支払わずに出た時（ハイパーモード）"""
    if u.c.kind != "C" or s.over:
        return
    i = 1 - j
    if not any(z.k == "k22_garyou" and z.hyper for z in s.P[i].board):
        return
    if not _no_cost_entry(s, j, u):
        return
    for z in _onboard(s, i, "k22_garyou"):
        if s.over or z not in s.P[i].board or not z.hyper:
            continue
        _garyou_fire(s, i)


E.HYPER_POW["k22_garyou"] = 4000          # パワー3000 → ハイパーモード7000

add("k22_garyou", "朱神のC ガリョウ", 3, "F", power=3000, sa=True, zrush=True,
    races=("god", "samurai", "hyperbeast"), pri=4, roles="atk dis",
    enterwatch=ew_garyou, status="partial",
    text="スピードアタッカー。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまで、このクリーチャーのハイパーモードを解放する）。"
         "ハイパーモード：パワー7000。W・ブレイカー。"
         "相手のクリーチャーがコストを支払わずに出た時、自分の山札の上から1枚を表向きにする。"
         "それがコスト5以下のクリーチャーなら出す。それ以外なら山札の下に置く",
    note="「コストを支払わずに出た」は、効果で出た場合と、相手のターン中の召喚（S・トリガーなど）、"
         "および自分のターンにマナをタップせずに召喚した場合で見ている。"
         "相手がそのターン中に多色カードをマナゾーンに置いていた場合、"
         "そのターン最初の召喚だけ、マナをタップしたと見誤ることがある。"
         "表向きにしたカードが進化クリーチャーの場合は出せないので山札の下に置く",
    source=SRC["k22_garyou"])


# ================================================================ 44/77 神嵐の超人
add("k22_kamiarashi", "神嵐の超人", 4, "N", power=20000, brk=4, mach=True, races=("giant",),
    pri=8, roles="atk fin", costx=lambda s, i, av: 7,
    text="手札から召喚するなら、このクリーチャーの召喚コストを3多くする（手札からは7マナ）。"
         "マッハファイター。Q・ブレイカー",
    source=SRC["k22_kamiarashi"])


# ================================================================ 45/77 護神のP エメラルド・ファラオ
def bfx_pharaoh(s, ai, au, di, du, a_dies, d_dies):
    """このクリーチャーがバトルに勝った時、相手のシールドを1つブレイクしてもよい（必ずブレイクする）"""
    if au.k == "k22_pharaoh" and d_dies and not a_dies:
        s.ev("　エメラルド・ファラオ：バトルに勝った → 相手のシールドを1つブレイク")
        if s.P[di].sh:
            s.break_sh(ai, 1)
    elif du.k == "k22_pharaoh" and a_dies and not d_dies:
        s.ev("　エメラルド・ファラオ：バトルに勝った → 相手のシールドを1つブレイク")
        if s.P[ai].sh:
            s.break_sh(di, 1)
    return a_dies, d_dies


def mat_pharaoh(s, i, u, tg):
    """ハイパーモード：「相手のクリーチャーが攻撃するなら、可能ならこのクリーチャーを攻撃する」。

    攻撃先の強制の差し込み口（mustatktgt=）は、エンジンが攻撃先の候補を絞り終えた後に呼ばれる。
    だから「可能なら」の判定（タップしているか・マッハファイターか・パワーが足りるか）は
    エンジンに任せきりでよく、候補にファラオが入っていない時は何も縛らない。
    i＝攻める側、tg＝攻撃先の候補（相手の場の番号と、プレイヤーを表す "P"）"""
    o = s.P[1 - i]
    if not any(z.k == "k22_pharaoh" and z.hyper for z in o.board):
        return None
    for j in tg:
        if j == "P":
            continue
        t = o.board[j]
        if t.k == "k22_pharaoh" and t.hyper:
            return j
    return None


E.HYPER_POW["k22_pharaoh"] = 2000         # パワー4000 → ハイパーモード6000

add("k22_pharaoh", "護神のP エメラルド・ファラオ", 3, "N", power=4000, mach=True, zrush=True,
    races=("god", "hyperbeast"), pri=4, roles="atk rem blk",
    battlefx=bfx_pharaoh, mustatktgt=mat_pharaoh,
    status="partial",
    text="マッハファイター。"
         "このクリーチャーがバトルに勝った時、このクリーチャーは相手のシールドを1つブレイクしてもよい"
         "（必ずブレイクする）。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまで、このクリーチャーのハイパーモードを解放する）。"
         "ハイパーモード：パワー6000。W・ブレイカー。"
         "相手のクリーチャーが攻撃するなら、可能ならこのクリーチャーを攻撃する",
    note="「バトルに勝った時」の差し込み口がエンジンにない（あるのはバトルの結果を直す battlefx= だけ）ため、"
         "ブレイクはバトルの結果が決まった時点で行っている。"
         "そのため、負けたクリーチャーが墓地に置かれる前にシールドが割れ、"
         "ブレイクで出たS・トリガーのクリーチャーから見ると、負けたクリーチャーがまだ場にいる",
    source=SRC["k22_pharaoh"])


# ================================================================ 46/77 ガルド・ライフ
def sp_galdlife(s, i):
    """クリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを+6000し、
    そのクリーチャーは相手プレイヤーを攻撃できない。その後、自分の山札の上から1枚をマナゾーンに置く。
    （相手プレイヤーを攻撃できなくなるのが大きいので、相手のクリーチャーのうち重要度のいちばん高い、
      プレイヤーを攻撃できるものを選ぶ。それがいなければ自分のいちばんパワーの高いクリーチャーを選ぶ）"""
    t = s.target(i, lambda z: not z.c.noatkp)
    mine = False
    if t is None:
        cs = [z for z in s.P[i].board if z.c.kind == "C"]
        if cs:
            t = max(cs, key=lambda z: s.power(i, z))
            mine = True
    if t is not None:
        t.pw += 6000
        t.x["k22_nap"] = s.turn
        s.ev(f"　ガルド・ライフ：{t.c.name} は+6000され、このターン相手プレイヤーを攻撃できない"
             f"（{'自分' if mine else '相手'}のクリーチャー）")
    s.ramp(i, 1, tapped=False)


add("k22_galdlife", "ガルド・ライフ", 3, "N", kind="S", trig=True, pri=3, roles="acc trg dis",
    spell=sp_galdlife,
    noatkplock=lambda s, i, u: u.x.get("k22_nap") == s.turn,
    text="S・トリガー。クリーチャーを1体選ぶ（自分のでも相手のでもよい）。"
         "このターン、そのクリーチャーのパワーを+6000し、そのクリーチャーは相手プレイヤーを攻撃できない。"
         "自分の山札の上から1枚をマナゾーンに置く",
    source=SRC["k22_galdlife"])
