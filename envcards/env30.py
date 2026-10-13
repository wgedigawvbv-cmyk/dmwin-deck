"""担当30：DM26-RP2／RP3（逆札篇）の未実装カード15枚（key は k30_）

出典
  DM26-RP2「逆札篇 第2弾 燃えろ禁断！逆転のドギラゴン革命‼」75〜77番の3枚
  DM26-RP3「逆札篇 第3弾 勝敵！逆転おこせ鬼の∞ディスペクター!!」のOR1・S1〜S11のうち未実装分と1/77

この弾で出てきた新しい仕組み（調べて確かめたもの）
  ・シールド・ゴー（破壊された時、表向きのシールドとしてシールドゾーンへ。表向きで
    シールドゾーンを離れる時はかわりに墓地へ）……《清浄のラクシャ インカ》
  ・攻撃誘導＋自分をタップして出す（タップしていないクリーチャーは攻撃されないので、
    誘導を働かせるには自分でタップする必要がある）……《清浄のラクシャ インカ》《完全熱血革命》
  ・マスター・G・ブレイカー（相手のシールドをすべてブレイクし、その攻撃の後、自分のシールドも
    すべてブレイクする。出たターンは1つブレイクするごとに相手のクリーチャー1体を破壊）
    ……《SUPREME-GUN・ザ・ジョニー》
  ・S-MAX進化（進化元が要らない。同じものは1体しか置けない。自分が負ける時、かわりにこれを破壊するか
    手札の同名カードを1枚捨てる）……《SUPREME-GUN・ザ・ジョニー》
  ・Jビッグ1（自分の他のジョーカーズの、Jビッグ1以外の「出た時」の能力を1つ使う）
    ……《ジョット・首魁・ジョラゴン》《ヒトリダチ ケントナーク》
  ・エクストラEXライフ（出る時シールド2枚。離れる時はそのうち1つを墓地に置いて残る）
    ……《「正義と正義と正義と正義」》
  ・輪廻∞（バトルゾーンに置いたまま、このカードの呪文側をコストを払って唱える）
    ……《天地命動 バラギアラ／輪廻虹災》

調べ方
  15枚すべて dmwiki.net のカードページを**別の質問で2回ずつ**読み、コスト・文明・カードの種類・種族・
  パワー・ブレイク数・能力の本文が2回とも一致することを確かめた（curl は403なので WebFetch、4〜6秒間隔）。
  本文が切れる札は生の wiki ソース（?plugin=template&refer=…）も見た。
  新しいキーワード（シールド・ゴー／マスター・G・ブレイカー／S-MAX進化／Jビッグ1）は、
  カードページとキーワードの専用ページの両方で定義を突き合わせた。
  意外だった点：
    ・《清浄のラクシャ インカ》の「このクリーチャーをタップして出してもよい」は損な能力に見えるが、
      デュエマでは**タップしているクリーチャーしか攻撃されない**ので、攻撃誘導を働かせるための能力。
      だから実装では必ずタップして出している（《完全熱血革命》も同じ理由でタップする）。
    ・《Σ龍》はパワー0で、「パワーが0以下の間離れない」のでまったく除去されない。
      そのかわり自分のパワーも0なので、相手のクリーチャーを攻撃することはできない。
    ・《ジョット・首魁・ジョラゴン》は《ジョット・ガン・ジョラゴン》（env19、殿堂入り、無色）とは
      別のカードで、**光文明・コスト7・パワー11500・NEO進化**。無色でもマスター・ドラゴンZでもない。
    ・《“↑↑”ブランド》は《「轟轟轟」ブランド》（火・コスト7・パワー6000）とは別で、
      パワー9000・J・O・E 4・G・G・G持ち。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move
from envcards.env0 import SLAYER, exlife_enter, exlife_rep, worst_own

W = "https://dmwiki.net/"
SRC = {
    "k30_inka": W + "《清浄のラクシャ インカ》",
    "k30_siuba": W + "《熱血の親衛隊シウバ》",
    "k30_kanzen": W + "《完全熱血革命》",
    "k30_sigma": W + "《Σ龍》",
    "k30_supreme": W + "《SUPREME-GUN・ザ・ジョニー》",
    "k30_jolagang": W + "《ジョット・首魁・ジョラゴン》",
    "k30_fujisan": W + "《Dr.富士山ッピング》",
    "k30_ageage": W + "《“↑↑”ブランド》",
    "k30_sandaiteio": W + "《闘帝合体 サンダイテイオー》",
    "k30_seigi4": W + "《「正義と正義と正義と正義」》",
    "k30_kingemp": W + "《キング∞エンペラー》",
    "k30_gorina": W + "《爆龍羅王 ゴリナボルト》",
    "k30_daiju": W + "《祝え！冥帝王 ダイジュ・ディダノス》",
    "k30_baragiara": W + "《天地命動 バラギアラ／輪廻虹災》",
    "k30_kento": W + "《ヒトリダチ ケントナーク》",
}

GOKEYS = ("k30_inka",)              # シールド・ゴーを持つカード
JBIG_NO = ("k30_jolagang", "k30_kento")     # Jビッグ1そのものを含む能力（Jビッグ1の元にはできない）
MAXJB = 4                           # Jビッグ1の連鎖の深さの上限（手順が終わらなくなるのを防ぐ安全装置）
RINNE_COST = 10                     # 輪廻虹災（呪文側）のコスト
RINNE_CIV = "LWDFN"


# ================================================================ 共通の道具
def _jok(k):
    return "jokers" in BY_KEY[k].races


def _plain_cre(c):
    """進化元なしで出せるクリーチャーか"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _after_aura(s, i, k, n):
    """COSTX のあとにかかる全体のコスト変化を当てはめた、実際に払うコスト
    （ほかの担当のコスト軽減があっても「払えるかどうか」を正しく見るため）"""
    for f in E.COSTAURA:
        n = f(s, i, k, n)
    return n


def _owner(s, u):
    for j in (0, 1):
        if u in s.P[j].board:
            return j
    return None


def _jcount(s, i):
    """自分のバトルゾーンのジョーカーズとマナゾーンのジョーカーズ・カードの合計"""
    n = sum(1 for u in s.P[i].board if "jokers" in u.c.races)
    return n + sum(1 for k in s.P[i].mana if _jok(k))


def _execable(s, i, k):
    """コストを支払わずに「実行」できるカードか"""
    c = BY_KEY[k]
    if c.kind == "C":
        return _plain_cre(c) and s.fate(i, k, "deck", False) == "ok"
    if c.kind == "S":
        return s.spell_ok(i, c.cost)
    return c.kind in ("T", "G", "X")


def _free_exec(s, i, k):
    """どのゾーンにも属していないカード1枚を、コストを支払わずに実行する
    （クリーチャー・呪文・タマシード・クロスギア・G城）。できなければ山札の下に戻す"""
    c = BY_KEY[k]
    p = s.P[i]
    if c.kind == "C":
        s.enter(i, k, "deck", False)        # 出られない時は enter が山札へ戻す
    elif c.kind == "S":
        if not s.spell_ok(i, c.cost):
            p.deck.insert(0, k)
            return False
        s.cast(i, k)
    elif c.kind == "T":
        s.place_tama(i, k)
    elif c.kind == "X":
        gu = E.U(k)
        gu.sick = False
        p.board.append(gu)
        fn = E.ENTER.get(k)
        if fn is not None:
            fn(s, i, gu)
    else:
        s.place_castle(i, k)
    return True


def _cast_inplace(s, i, k):
    """ツインパクトの呪文側を、カードをバトルゾーンに置いたまま唱える（墓地には置かない）"""
    c = BY_KEY[k]
    p = s.P[i]
    cost = c.twin[0] if c.twin else c.cost
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


def _jbig1(s, i, src):
    """Jビッグ1：自分の他のジョーカーズ（バトルゾーン）の「出た時」の能力を1つ使う。
    使えたら True。重要度のいちばん高いものを選ぶ（踏み倒し先の選び方と同じ共通の決まり）"""
    p = s.P[i]
    cands = [z for z in p.board
             if z is not src and "jokers" in z.c.races and z.k not in JBIG_NO and E.ENTER.get(z.k) is not None]
    if not cands or s.over:
        return False
    d = p.x.get("k30_jb", 0)
    if d >= MAXJB:
        return False
    z = max(cands, key=lambda x: E.PRI[x.k])
    p.x["k30_jb"] = d + 1
    s.ev(f"　Jビッグ1：{z.c.name} の「出た時」の能力を使う")
    E.ENTER[z.k](s, i, z)
    s.P[i].x["k30_jb"] = d
    return True


# ================================================================ スーパーガードマン
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


# ================================================================ 攻撃誘導（インカ／完全熱血革命 共通）
def _is_taunt(s, u):
    """「相手のクリーチャーが攻撃するなら、可能ならこれを攻撃する」を持っているか"""
    return u.k == "k30_inka" or u.x.get("k30_taunt", -1) >= s.turn


def _can_hit(s, i, au, t):
    """このシミュレーター共通の決まりで、攻撃している au（i のもの）が t を攻撃できるか
    （タップしている・ジャストダイバーでない・パワーが攻撃側以下）"""
    return t.tap and not t.jd and s.power(1 - i, t) <= s.power(i, au, True)


def _taunted(s, i, au):
    for z in s.P[1 - i].board:
        if z.c.kind == "C" and _is_taunt(s, z) and _can_hit(s, i, au, z):
            return True
    return False


def atl_taunt(s, i, u, t):
    """誘導先を攻撃できるなら、それ以外のクリーチャーは攻撃できない"""
    return _taunted(s, i, u) and not _is_taunt(s, t)


def nap_taunt(s, i, u):
    """誘導先を攻撃できるなら、プレイヤーも攻撃できない"""
    return _taunted(s, i, u)


# ================================================================ シールド・ゴー（インカ）
def ld_shieldgo(s, i, u, dest, destroy_):
    """破壊された時、墓地ではなくシールドゾーンへ（このあと si_shieldgo が表向きにする）"""
    if u.k not in GOKEYS or not destroy_:
        return None
    s.P[i].x["k30_go"] = u.k
    return "shield"


def si_shieldgo(s, i, k, up):
    """シールドゾーンに置かれた直後に、シールド・ゴーの1枚だけを表向きにする"""
    p = s.P[i]
    if up or k not in GOKEYS or p.x.get("k30_go") != k:
        return
    p.x["k30_go"] = None
    for j in range(len(p.sh) - 1, -1, -1):
        if p.sh[j][0] == k and not p.sh[j][1]:
            p.sh[j] = (k, True)
            s.ev(f"　シールド・ゴー：{BY_KEY[k].name} が表向きのシールドになった")
            return


def sd_shieldgo(s, i, k, up, dest):
    """シールド・ゴー：表向きのこのカードが表向きのままシールドゾーンを離れる時は、かわりに墓地に置く
    （SHIELDDEST なので、ブレイクでも効果でシールドを動かされた時でも通る）"""
    if not up:
        return dest
    if dest != "grave":
        s.ev(f"　シールド・ゴー：表向きの {BY_KEY[k].name} は墓地へ")
    return "grave"


# ================================================================ 清浄のラクシャ インカ
def e_inka(s, i, u):
    """「このクリーチャーをタップして出してもよい」：タップしていないクリーチャーは攻撃されないので、
    攻撃誘導を働かせるために必ずタップして出す"""
    s.tap_cre(i, u)


add("k30_inka", "清浄のラクシャ インカ", 3, "N", power=5000, races=("oracle", "snowfu", "snow"),
    pri=4, roles="dis shd",
    enter=e_inka, leavedest=ld_shieldgo, shieldin=si_shieldgo, shielddest=sd_shieldgo,
    atktargetlock=atl_taunt, noatkplock=nap_taunt,
    text="このクリーチャーをタップして出してもよい（タップしていないと攻撃を引き受けられないので、必ずタップして出す）。"
         "相手のクリーチャーが攻撃するなら、可能ならこのクリーチャーを攻撃する"
         "（「可能なら」は、このシミュレーター共通の攻撃先の決まり＝タップしていて、"
         "パワーが攻撃側以下のクリーチャー、に当てはまる時）。"
         "シールド・ゴー（このクリーチャーが破壊された時、新しいシールドとして表向きのまま自分のシールドゾーンに置く。"
         "表向きでシールドゾーンを離れる時は、かわりに自分の墓地に置く）",
    source=SRC["k30_inka"])


# ================================================================ 熱血の親衛隊シウバ
add("k30_siuba", "熱血の親衛隊シウバ", 2, "N", power=4000, gs=True,
    races=("beastfolk", "hunter", "alien"), pri=2, roles="trg",
    text="G・ストライク（このカードを自分のシールドゾーンから手札に加える時、相手に見せて、"
         "相手のクリーチャー1体を選んでもよい。このターン、そのクリーチャーは攻撃できない）",
    source=SRC["k30_siuba"])


# ================================================================ 完全熱血革命
def sp_kanzen(s, i):
    """自分のクリーチャーを1体タップしてもよい。次の自分のターンのはじめまで、そのクリーチャーの
    パワーを+4000し、相手のクリーチャーが攻撃するなら可能ならそれを攻撃する"""
    t = worst_own(s, i, lambda z: not z.tap)
    if t is None:
        return
    s.tap_cre(i, t)
    until = s.turn + (1 if s.tp == i else 0)
    t.x["k30_taunt"] = until
    t.x["k30_pump"] = until
    s.ev(f"　完全熱血革命：{t.c.name} をタップして+4000し、攻撃を引き受けさせる")


def ap_kanzen(s, i, u, atk):
    return 4000 if u.x.get("k30_pump", -1) >= s.turn else 0


add("k30_kanzen", "完全熱血革命", 2, "N", kind="S", trig=True, pri=3, roles="trg dis",
    spell=sp_kanzen, aurap=ap_kanzen,
    text="S・トリガー。自分のクリーチャーを1体タップしてもよい（失うのがいちばん安いアンタップのクリーチャーを選ぶ。"
         "タップしていないと攻撃を引き受けられないため）。次の自分のターンのはじめまで、"
         "そのクリーチャーのパワーを+4000し、相手のクリーチャーが攻撃するなら、可能ならそのクリーチャーを攻撃する",
    note="S・トリガーで相手の攻撃中に唱えた時、その攻撃の攻撃先はすでに決まっているので、"
         "引き受けられるのは次の攻撃から。攻撃が始まった後に守る側が攻撃先を決め直す差し込み口"
         "（ATKRETARGET）は、いまのエンジンにもまだ無い（ATKSWAP は攻撃している側の入れ替え、"
         "GUARD は None を返せば次に進む任意の付け替えなので、強制の決め直しには使えない）",
    status="partial", source=SRC["k30_kanzen"])


# ================================================================ Σ龍
def _zero_power(s, j, t):
    """相手のクリーチャー t のパワーをこのターン0にする（0以下なので破壊される）"""
    if t is None:
        return
    o = s.P[1 - j]
    if t not in o.board:
        return
    t.pw -= s.power(1 - j, t)
    s.ev(f"　Σ龍：{t.c.name} のパワーを0にする")
    if s.power(1 - j, t) <= 0 and t in o.board:
        s.leave(1 - j, t, "grave", by_opp=True, destroy=True)


def e_sigma(s, i, u):
    """出た時または攻撃する時、相手のクリーチャー1体のパワーをこのターン0にする"""
    _zero_power(s, i, s.target(i))


def aw_sigma(s, i, u):
    """各ターン、相手のクリーチャーがはじめて攻撃する時、そのターン、そのクリーチャーのパワーを0にする"""
    j = 1 - i
    if not s.has(j, "k30_sigma"):
        return
    p = s.P[j]
    if p.x.get("k30_sigt") == s.turn:
        return
    p.x["k30_sigt"] = s.turn
    _zero_power(s, j, u)


def lr_sigma(s, i, u, dest, destroy_):
    """パワーが0以下の間、このクリーチャーはバトルゾーンを離れない"""
    return u.k == "k30_sigma" and s.power(i, u) <= 0


SLAYER.add("k30_sigma")

add("k30_sigma", "Σ龍", 8, "D", power=0, brk=99,
    races=("masterdragon", "dragon", "jokers"), pri=12, roles="rem fin dis",
    enter=e_sigma, attack=e_sigma, atkwatch=aw_sigma, leaverep=lr_sigma,
    text="スレイヤー。ワールド・ブレイカー（相手のシールドをすべてブレイクする）。"
         "このクリーチャーが出た時または攻撃する時、相手のクリーチャーを1体選ぶ。"
         "このターン、そのクリーチャーのパワーを0にする（パワーが0以下のクリーチャーは破壊される）。"
         "各ターン、相手のクリーチャーがはじめて攻撃する時、そのターン、そのクリーチャーのパワーを0にする。"
         "このクリーチャーは、パワーが0以下の間、バトルゾーンを離れない（パワー0なのでいつも離れない）",
    note="パワー0なので、このシミュレーター共通の決まり（パワーが自分以下のクリーチャーしか攻撃先に選ばない）では"
         "相手のクリーチャーを攻撃できず、プレイヤーへの攻撃だけになる",
    source=SRC["k30_sigma"])


# ================================================================ SUPREME-GUN・ザ・ジョニー
def e_supreme(s, i, u):
    """出た時、相手のクリーチャー1体を持ち主の山札の下に置く。その後、カードを1枚引いてもよい"""
    u.x["k30_born"] = s.turn
    t = s.target(i)
    if t is not None:
        s.ev(f"　SUPREME-GUN：{t.c.name} を山札の下へ")
        move(s, i, t, "deck")
    if len(s.P[i].deck) > 1:
        s.draw(i, 1)


def w_supreme_one(s, i, u):
    """S-MAX進化：自分のS-MAX進化クリーチャーが2体以上あれば、1体を残して残りを手札に戻す"""
    if u.k != "k30_supreme":
        return
    p = s.P[i]
    for z in [z for z in p.board if z.k == "k30_supreme" and z is not u]:
        if z in p.board:
            s.ev("　S-MAX進化：2体目以降は手札に戻る")
            s.leave(i, z, "hand")


def lose_supreme(s, i, how):
    """S-MAX進化：自分が負ける時、かわりにこのクリーチャーを破壊するか、手札の同名カードを1枚捨てる"""
    p = s.P[i]
    for z in p.board:
        if z.k == "k30_supreme":
            if s.leave(i, z, "grave", destroy=True):
                s.ev("　S-MAX進化：かわりに SUPREME-GUN・ザ・ジョニー を破壊して負けない")
                return True
            break
    if "k30_supreme" in p.hand:
        s.discard(i, "k30_supreme")
        s.ev("　S-MAX進化：かわりに手札の SUPREME-GUN・ザ・ジョニー を捨てて負けない")
        return True
    return False


def bp_supreme(s, ai, di, n):
    """マスター・G・ブレイカー：出たターンは、シールドを1つブレイクするごとに
    相手のクリーチャー1体を選んで破壊する（ブレイクする枚数は変えない）"""
    u = s.atk
    if u is None or u.k != "k30_supreme" or u.x.get("k30_born") != s.turn:
        return n
    own = _owner(s, u)
    if own is None:
        return n
    for _ in range(min(n, len(s.P[di].sh))):
        if s.over:
            break
        t = s.target(own)
        if t is None:
            break
        s.ev(f"　マスター・G・ブレイカー：ブレイクの前に {t.c.name} を破壊")
        destroy(s, own, t)
    return n


def ae_supreme(s, i, u):
    """マスター・G・ブレイカー：その攻撃の後、自分のシールドをすべてブレイクする"""
    if u.k != "k30_supreme":
        return
    n = len(s.P[i].sh)
    if n and not s.over:
        s.ev("　マスター・G・ブレイカー：その攻撃の後、自分のシールドをすべてブレイク")
        s.break_sh(1 - i, n)


add("k30_supreme", "SUPREME-GUN・ザ・ジョニー", 7, "", power=10000, brk=99,
    evo="smax", neo=True, evox=lambda s, i, u: False,
    races=("jokers", "rexstars", "spriggan"), pri=13, roles="fin atk rem draw",
    enter=e_supreme, enterwatch=w_supreme_one, loserep=lose_supreme, breakpre=bp_supreme, atkend=ae_supreme,
    playrule=lambda deck, k: None,
    text="S-MAX進化（このクリーチャーは進化元を必要としない。自分のS-MAX進化クリーチャーが2体以上あれば、"
         "1体を残して残りをすべて手札に戻す。自分がゲームに負ける時、かわりにこのクリーチャーを破壊するか、"
         "自分の手札から《SUPREME-GUN・ザ・ジョニー》を1枚捨てる）。"
         "マスター・G・ブレイカー（このクリーチャーは相手のシールドをすべてブレイクし、その攻撃の後、"
         "自分のシールドをすべてブレイクする。このクリーチャーが出たターン、各ブレイクの前に、"
         "相手のクリーチャーを1体選び、破壊する）。"
         "このクリーチャーが出た時、相手のクリーチャーを1体選び、持ち主の山札の下に置く。その後、カードを1枚引いてもよい",
    note="進化元が要らないので「出せるデッキか」の判定（playrule）は何も求めていない",
    source=SRC["k30_supreme"])


# ================================================================ ジョット・首魁・ジョラゴン
def _jolagang_out(s, i):
    """コスト5以下のジョーカーズで、手札から出せるもののうち重要度のいちばん高いもの"""
    cands = [k for k in s.P[i].hand
             if _jok(k) and BY_KEY[k].cost <= 5 and (_plain_cre(BY_KEY[k]) or BY_KEY[k].kind == "T")]
    return max(cands, key=E.PRI.get) if cands else None


def e_jolagang(s, i, u):
    """出た時または攻撃する時、次の中から1回選ぶ。
    ▶コスト5以下のジョーカーズを1つ、自分の手札から出す　▶Jビッグ1する"""
    p = s.P[i]
    k = _jolagang_out(s, i)
    big = [z for z in p.board
           if z is not u and "jokers" in z.c.races and z.k not in JBIG_NO and E.ENTER.get(z.k) is not None]
    bigv = max((E.PRI[z.k] for z in big), default=-1)
    if k is not None and E.PRI[k] >= bigv:
        c = BY_KEY[k]
        if c.kind == "T":
            p.hand.remove(k)
            s.ev(f"　ジョット・首魁・ジョラゴン：{c.name} を手札から出す")
            s.place_tama(i, k)
            return
        if s.fate(i, k, "hand", False) == "ok" and k in p.hand:
            p.hand.remove(k)
            s.ev(f"　ジョット・首魁・ジョラゴン：{c.name} を手札から出す")
            s.enter(i, k, "hand", False)
            return
    _jbig1(s, i, u)


def cx_jolagang(s, i, av):
    """NEO進化クリーチャーとして召喚するなら、召喚コストを2少なくする"""
    return 5 if s.evo_src(i, "k30_jolagang") is not None else 7


add("k30_jolagang", "ジョット・首魁・ジョラゴン", 7, "L", power=11500, brk=2,
    evo="jokers", neo=True, races=("masterdragon", "dragon", "jokers"), pri=11, roles="atk fin rem",
    enter=e_jolagang, attack=e_jolagang, costx=cx_jolagang,
    evox=lambda s, i, u: u.c.kind == "C" and ("jokers" in u.c.races or "rexstars" in u.c.races),
    playrule=lambda deck, k: None,
    text="NEO進化クリーチャーとして召喚するなら、このクリーチャーの召喚コストを2少なくする。"
         "NEO進化：ジョーカーズまたはレクスターズのクリーチャー1体の上に置いてもよい（置かずに召喚してもよい）。"
         "W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、次の中から1回選ぶ。"
         "▶コスト5以下のジョーカーズを1つ、自分の手札から出す（重要度のいちばん高いもの）。"
         "▶Jビッグ1する（自分の他のジョーカーズの、Jビッグ1以外の、出た時にトリガーする能力を1つ使う）",
    note="コスト軽減は「NEO進化として召喚するなら」だが、COSTX に渡されるのは fn(s, i, av) だけで"
         "「NEO進化で出すか、置かずに出すか」が渡らない（手が作られるのはコストを決めた後）ため、"
         "進化元にできるジョーカーズ／レクスターズがバトルゾーンにいれば5として扱っている"
         "（進化元を置かずに出す手を選ぶと2少ないままになる）。"
         "Jビッグ1の元には、Jビッグ1を含む能力を持つカード自身（このカードとヒトリダチ ケントナーク）は選ばない。"
         "進化元なしでも召喚できるので playrule は何も求めていない",
    status="partial", source=SRC["k30_jolagang"])


# ================================================================ Dr.富士山ッピング
def e_fujisan(s, i, u):
    """出た時、自分の山札の上から3枚を表向きにし、その中のジョーカーズを好きな数手札に加える。
    残りを好きな順番で山札の下に置く"""
    p = s.P[i]
    n = min(3, max(0, len(p.deck) - 1))
    if n <= 0:
        return
    rest = []
    for k in [p.deck.pop() for _ in range(n)]:
        if _jok(k):
            p.hand.append(k)
            s.ev(f"　Dr.富士山ッピング：{BY_KEY[k].name} を手札に加える")
        else:
            rest.append(k)
    for k in rest:
        p.deck.insert(0, k)


def te_fujisan(s, i, u):
    """自分のターンの終わりに、このカードが手札にあれば、自分のジョーカーズを合計コスト7以上になるよう
    手札に戻して、このクリーチャーを出せる（バトルゾーンのカード1つずつについて呼ばれるので、
    1ターンに1度しか動かないようにしている）"""
    j = s.tp
    p = s.P[j]
    if "k30_fujisan" not in p.hand or p.x.get("k30_fjend") == s.turn or s.over:
        return
    tot, back = 0, []
    for z in sorted([z for z in p.board if z.c.kind == "C" and "jokers" in z.c.races], key=lambda z: s.val(z)):
        if tot >= 7:
            break
        back.append(z)
        tot += z.c.cost
    if tot < 7 or s.fate(j, "k30_fujisan", "hand", False) != "ok":
        return
    p.x["k30_fjend"] = s.turn
    for z in back:
        if z in p.board:
            s.leave(j, z, "hand")
    if "k30_fujisan" not in p.hand:
        return
    p.hand.remove("k30_fujisan")
    s.ev("　Dr.富士山ッピング：ジョーカーズを手札に戻してバトルゾーンに出る")
    s.enter(j, "k30_fujisan", "hand", False)


def lw_fujisan(s, i, u, dest, destroy_):
    """各ターンに1度、自分の他のジョーカーズが離れた時、その「出た時」の能力を1つ使ってもよい"""
    if u.k == "k30_fujisan" or "jokers" not in u.c.races or not s.has(i, "k30_fujisan"):
        return
    fn = E.ENTER.get(u.k)
    if fn is None or s.over:
        return
    p = s.P[i]
    if p.x.get("k30_fjuse") == s.turn:
        return
    p.x["k30_fjuse"] = s.turn
    z = E.U(u.k)
    z.sick = False
    s.ev(f"　Dr.富士山ッピング：離れた {u.c.name} の「出た時」の能力を使う")
    fn(s, i, z)


add("k30_fujisan", "Dr.富士山ッピング", 5, "W", power=6000, brk=2, blocker=True, jd=True,
    races=("jokers",), pri=9, roles="blk draw acc",
    enter=e_fujisan, tendall=te_fujisan, leavewatch=lw_fujisan,
    text="自分のターンの終わりに、このカードが手札にあれば、自分のジョーカーズを好きな数バトルゾーンから手札に戻し、"
         "こうして戻したクリーチャーのコストの合計が7以上なら、このクリーチャーを手札から出す"
         "（失うのが安いものから戻す）。ブロッカー。ジャストダイバー。W・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から3枚を表向きにする。その中からジョーカーズを好きな数、"
         "手札に加える。残りを好きな順番で山札の下に置く。"
         "各ターンに1度、自分の他のジョーカーズが離れた時、そのジョーカーズの「出た時」の能力を1つ使ってもよい",
    source=SRC["k30_fujisan"])


# ================================================================ “↑↑”ブランド
def cx_ageage(s, i, av):
    """J・O・E 4：7マナ払えない時だけ、召喚コストを4少なくする"""
    return 7 if _after_aura(s, i, "k30_ageage", 7) <= av else 3


def px_ageage(s, i, k, n):
    """J・O・E 4を使ったかどうかを、出た時の処理に伝える"""
    s.P[i].x["k30_joe"] = s.turn if n <= 3 else -1


def e_ageage(s, i, u):
    """J・O・E 4。出た時、自分の手札を好きな数捨ててもよい。
    こうして捨てたカード1枚につき、相手のパワー6000以下のクリーチャーを1体選び、破壊する"""
    p = s.P[i]
    if u.x.get("summoned") and p.x.pop("k30_joe", -1) == s.turn:
        u.eot = True
        u.x["k30_joe"] = True
        s.ev("　J・O・E 4：このターンの終わりに山札の下へ")
    while p.hand and not s.over:
        t = s.target(i, lambda x: s.power(1 - i, x) <= 6000)
        if t is None:
            return
        s.discard(i, min(p.hand, key=E.PRI.get))
        if t in s.P[1 - i].board:
            s.ev(f"　“↑↑”ブランド：手札を1枚捨てて {t.c.name} を破壊")
            destroy(s, i, t)


def te_ageage(s, i, u):
    """J・O・E：山札の下に置いたら、カードを1枚引く（下に置くのはエンジンの eot の仕組み）"""
    if not u.eot or not u.x.pop("k30_joe", False):
        return
    s.draw(i, 1)


def _ggg(s, i, u):
    """G・G・G：自分の手札が1枚以下なら、自分の他のクリーチャーに効く（効いている“↑↑”ブランドの数）"""
    if u.c.kind != "C" or len(s.P[i].hand) > 1:
        return 0
    n = sum(1 for z in s.P[i].board if z.k == "k30_ageage")
    if u.k == "k30_ageage":
        n -= 1
    return max(0, n)


def ap_ageage(s, i, u, atk):
    return 4000 * _ggg(s, i, u)


def bk_ageage(s, i, u):
    """G・G・G でパワード・ブレイカー（パワー6000ごとに1つ多くブレイク）を与える"""
    if not _ggg(s, i, u):
        return 0
    return max(0, 1 + s.power(i, u, True) // 6000 - u.c.brk)


add("k30_ageage", "“↑↑”ブランド", 7, "F", power=9000, brk=2, sa=True,
    races=("beatjockey", "jokers"), pri=11, roles="atk rem fin",
    enter=e_ageage, costx=cx_ageage, payx=px_ageage, tend=te_ageage, aurap=ap_ageage, brkplus=bk_ageage,
    text="J・O・E 4（このクリーチャーを、コストを4少なくして召喚してもよい。こうして出したら、このターンの終わりに、"
         "それを自分の山札の下に置く。そうしたら、カードを1枚引く。7マナ払えない時だけ使う）。"
         "スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが出た時、自分の手札を好きな数捨ててもよい（重要度のいちばん低いものから）。"
         "こうして捨てたカード1枚につき、相手のパワー6000以下のクリーチャーを1体選び、破壊する。"
         "G・G・G：自分の手札が1枚以下なら、自分の他のクリーチャーすべてのパワーを+4000し、"
         "「パワード・ブレイカー」を与える",
    source=SRC["k30_ageage"])


# ================================================================ 闘帝合体 サンダイテイオー
def e_sandaiteio(s, i, u):
    """出た時、次の中から3回選ぶ（同じものを選んでもよい）。
    ▶相手のクリーチャー1体を持ち主のマナゾーンに置く　▶山札の上から1枚をマナゾーンに置く
    ▶自分のマナゾーンからクリーチャー1体を手札に戻す"""
    p = s.P[i]
    for _ in range(3):
        if s.over:
            return
        t = s.target(i)
        if t is not None:
            s.ev(f"　サンダイテイオー：{t.c.name} をマナゾーンへ")
            move(s, i, t, "mana")
            continue
        if len(p.deck) > 1:
            s.ramp(i, 1)
            continue
        cands = [k for k in p.mana if BY_KEY[k].kind == "C"]
        if cands:
            k = max(cands, key=E.PRI.get)
            s.take_mana(i, k)
            p.hand.append(k)
            s.ev(f"　サンダイテイオー：マナの {BY_KEY[k].name} を手札へ")


def tg_sandaiteio(s, di, k):
    """自分のジョーカーズとマナのジョーカーズが合計7つ以上なら、シールドゾーンのこのカードにS・トリガーを与える"""
    return k == "k30_sandaiteio" and _jcount(s, di) >= 7


add("k30_sandaiteio", "闘帝合体 サンダイテイオー", 8, "N", power=13000, brk=3, mach=True,
    races=("jokers",), pri=11, roles="rem acc fin atk trg",
    enter=e_sandaiteio, trigok=tg_sandaiteio,
    text="自分の、バトルゾーンのジョーカーズとマナゾーンにあるジョーカーズ・カードが合計7つ以上なら、"
         "自分のシールドゾーンにあるこのクリーチャーに「S・トリガー」を与える。"
         "マッハファイター。T・ブレイカー。"
         "このクリーチャーが出た時、次の中から3回選ぶ（同じものを選んでもよい）。"
         "▶相手のクリーチャーを1体選び、持ち主のマナゾーンに置く。"
         "▶自分の山札の上から1枚をマナゾーンに置く。"
         "▶クリーチャーを1体、自分のマナゾーンから手札に戻す。"
         "（相手のクリーチャーがいる限り1つめ、いなければ2つめ、山札が尽きていれば3つめを選ぶ）",
    source=SRC["k30_sandaiteio"])


# ================================================================ 「正義と正義と正義と正義」
def e_seigi4(s, i, u):
    """エクストラEXライフ：出る時、自分の山札の上から2枚をシールド化する"""
    p = s.P[i]
    ks = []
    for _ in range(2):
        if len(p.deck) <= 1:
            break
        k = p.deck[-1]
        if not s.add_shield(i):
            break
        ks.append(k)
    u.x["k30_ex"] = tuple(ks)
    if ks:
        s.ev(f"　エクストラEXライフ：山札の上から{len(ks)}枚をシールド化")


def lr_seigi4(s, i, u, dest, destroy_):
    """エクストラEXライフ：離れる時、かわりにそのシールドの中から1つを墓地に置く"""
    if u.k != "k30_seigi4":
        return False
    ks = u.x.get("k30_ex") or ()
    if not ks:
        return False
    p = s.P[i]
    k = ks[0]
    u.x["k30_ex"] = ks[1:]
    for j in range(len(p.sh) - 1, -1, -1):
        if p.sh[j][0] == k:
            s.take_shield(i, j, "grave")       # シールドゾーンの出口はここ1か所
            break
    s.ev(f"　エクストラEXライフ：シールドを1つ失って {u.c.name} は残る")
    return True


def tg_seigi4(s, di, k):
    """自分の「EXライフ」シールドすべてにS・トリガーを与える"""
    for z in s.P[di].board:
        if z.k == "k30_seigi4" and k in (z.x.get("k30_ex") or ()):
            return True
    return False


def tw_seigi4(s, i, u):
    """このクリーチャーがタップした時、シールドを1つブレイクしてもよい"""
    if u.k != "k30_seigi4" or s.over:
        return
    if s.P[1 - i].sh:
        s.ev("　「正義と正義と正義と正義」：タップしたので相手のシールドを1つブレイク")
        s.break_sh(i, 1)


def te_seigi4(s, i, u):
    """自分のターンの終わりに、このクリーチャーをアンタップする。その後、カードを1枚引いてもよい"""
    u.tap = False
    u.frz = 0
    s.draw(i, 1)


add("k30_seigi4", "「正義と正義と正義と正義」", 7, "LWD", power=13500, brk=3, blocker=True,
    races=("dispector", "metallica", "demoncommand", "command", "teamgalaxy", "gekkououkoku"),
    pri=11, roles="blk atk fin shd trg",
    enter=e_seigi4, leaverep=lr_seigi4, trigok=tg_seigi4, tapwatch=tw_seigi4, tend=te_seigi4,
    text="エクストラEXライフ（このクリーチャーを出す時、自分の山札の上から2枚をシールド化する。"
         "このクリーチャーが離れる時、かわりにそのシールドの中から1つを墓地に置く）。"
         "ブロッカー。T・ブレイカー。"
         "自分の「EXライフ」シールドすべてに「S・トリガー」を与える。"
         "このクリーチャーがタップした時、このクリーチャーは相手のシールドを1つブレイクしてもよい。"
         "自分のターンの終わりに、このクリーチャーをアンタップする。その後、カードを1枚引いてもよい",
    note="「シールドを1つブレイクしてもよい」は誰のシールドか本文に書かれていないので、"
         "ブレイクの標準の扱い（相手のシールド）にした。"
         "また「EXライフ」シールドの覚え方はカードの名前で見ているので、同じ名前のカードが"
         "ふつうのシールドにもある時は、そちらにもS・トリガーが付くことがある",
    status="partial", source=SRC["k30_seigi4"])


# ================================================================ キング∞エンペラー
def bf_kingemp(s, ai, au, di, du, a_dies, d_dies):
    """このクリーチャーはすべてのバトルに勝つ"""
    if au.k == "k30_kingemp":
        a_dies, d_dies = False, True
    if du.k == "k30_kingemp":
        a_dies, d_dies = True, False
    return a_dies, d_dies


def te_kingemp(s, i, u):
    """自分のターンの終わりに、自分の山札をシャッフルし、上から自分のエレメントの数だけ見る。
    その中からカードを1枚、コストを支払わずに実行してもよい。残りを好きな順序で山札の下に置く"""
    p = s.P[i]
    n = min(len(p.board), max(0, len(p.deck) - 1))
    if n <= 0 or s.over:
        return
    s.rng.shuffle(p.deck)
    top = [p.deck.pop() for _ in range(n)]
    best, bv = None, -1
    for k in top:
        if _execable(s, i, k) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        s.ev(f"　キング∞エンペラー：{BY_KEY[best].name} をコストを支払わずに実行")
        _free_exec(s, i, best)
    for k in top:
        s.P[i].deck.insert(0, k)


add("k30_kingemp", "キング∞エンペラー", 8, "LWN", power=8888, brk=2, blocker=True, mach=True,
    races=("exdreamer", "dispector", "trix", "mugenmasterdragon", "dragon", "teamwave", "teamzero"),
    pri=12, roles="blk rem fin acc",
    enter=exlife_enter, leaverep=exlife_rep, battlefx=bf_kingemp, tend=te_kingemp,
    text="EXライフ（このクリーチャーを出す時、自分の山札の上から1枚をシールド化する。離れる時はかわりに"
         "そのシールドを墓地に置いて残る）。ブロッカー。マッハファイター。W・ブレイカー。"
         "このクリーチャーはすべてのバトルに勝つ。"
         "自分のターンの終わりに、自分の山札をシャッフルし、上から自分のエレメントの数だけ見る。"
         "その中からカードを1枚（重要度のいちばん高いもの）、コストを支払わずに実行してもよい。"
         "残りを好きな順序で山札の下に置く",
    note="エレメントの数は、バトルゾーンにある自分のカード（クリーチャー・タマシード・クロスギアなど）の数で数えている。"
         "表向きのG城はシールドゾーンにあるので数に入らない",
    source=SRC["k30_kingemp"])


# ================================================================ 爆龍羅王 ゴリナボルト
def cx_gorina(s, i, av):
    """シンパシー：自分のクリーチャー1体につき召喚コストを1少なくする（1より少なくならない）"""
    return max(1, 8 - s.ncre(i))


def a_gorina(s, i, u):
    """各ターン、このクリーチャーがはじめて攻撃する時、このクリーチャーをアンタップする"""
    if u.x.get("k30_gori") == s.turn:
        return
    u.x["k30_gori"] = s.turn
    u.re = True
    s.ev("　ゴリナボルト：このターンはじめての攻撃なのでアンタップする")


def aw_gorina(s, i, u):
    """自分のクリーチャーが攻撃する時、カードを1枚引いてもよい。その後、攻撃しているクリーチャーより
    コストが小さいクリーチャーを1体、自分の手札から出してもよい"""
    n = sum(1 for z in s.P[i].board if z.k == "k30_gorina")
    if not n:
        return
    p = s.P[i]
    for _ in range(n):
        if s.over:
            return
        s.draw(i, 1)
        if s.over:
            return
        cands = [k for k in p.hand if _plain_cre(BY_KEY[k]) and BY_KEY[k].cost < u.c.cost]
        if not cands:
            continue
        k = max(cands, key=E.PRI.get)
        if s.fate(i, k, "hand", False) != "ok" or k not in p.hand:
            continue
        p.hand.remove(k)
        s.ev(f"　ゴリナボルト：{BY_KEY[k].name} を手札から出す")
        s.enter(i, k, "hand", False)


add("k30_gorina", "爆龍羅王 ゴリナボルト", 8, "LFN", power=11000, brk=2, sa=True,
    races=("dispector", "dynamitedragon", "dragon", "beastfolk", "teambomber", "boukenoukoku"),
    pri=11, roles="atk draw blk fin acc",
    enter=exlife_enter, leaverep=exlife_rep, costx=cx_gorina, attack=a_gorina, atkwatch=aw_gorina,
    battleswap=super_guardman("k30_gorina"),
    text="シンパシー：自分のクリーチャー（このクリーチャーを召喚する時、バトルゾーンにある自分のクリーチャー1体につき、"
         "召喚コストを1少なくする。ただし1より少なくならない）。"
         "EXライフ（出す時に山札の上から1枚をシールド化し、離れる時はかわりにそのシールドを墓地に置いて残る）。"
         "スピードアタッカー。W・ブレイカー。"
         "スーパーガードマン（自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーをタップしてバトルさせてもよい）。"
         "各ターン、このクリーチャーがはじめて攻撃する時、このクリーチャーをアンタップする。"
         "自分のクリーチャーが攻撃する時、カードを1枚引いてもよい。その後、攻撃しているクリーチャーより"
         "コストが小さいクリーチャーを1体、自分の手札から出してもよい（重要度のいちばん高いもの）",
    source=SRC["k30_gorina"])


# ================================================================ 祝え！冥帝王 ダイジュ・ディダノス
def e_daiju(s, i, u):
    u.x["k30_born"] = s.turn
    exlife_enter(s, i, u)


def a_daiju(s, i, u):
    """このクリーチャーが出たターンに攻撃する時、相手は自身の手札をすべて捨てる"""
    if u.x.get("k30_born") != s.turn:
        return
    o = s.P[1 - i]
    if not o.hand:
        return
    s.ev("　ダイジュ・ディダノス：相手は手札をすべて捨てる")
    for k in list(o.hand):
        if s.over:
            return
        if k in o.hand:
            s.discard(1 - i, k)


def fx_daiju(s, owner, u, i, k, src, summon, res):
    """このクリーチャーの攻撃中、相手はクリーチャーを出せない"""
    if i != owner and s.atk is u:
        return "no"
    return res


def nap_daiju(s, i, u):
    """相手のクリーチャーは自分（このカードの持ち主）を攻撃できない"""
    return s.has(1 - i, "k30_daiju")


add("k30_daiju", "祝え！冥帝王 ダイジュ・ディダノス", 12, "DFN", power=50000, brk=99, sa=True, gs=True,
    races=("dispector", "giantdragon", "dragon", "phoenix", "fujijuoukoku", "bikoureioukoku"),
    pri=13, roles="fin atk dis trg",
    enter=e_daiju, leaverep=exlife_rep, attack=a_daiju, fatex=fx_daiju, noatkplock=nap_daiju,
    text="G・ストライク。EXライフ（出す時に山札の上から1枚をシールド化し、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。スピードアタッカー。ワールド・ブレイカー（相手のシールドをすべてブレイクする）。"
         "このクリーチャーが出たターンに攻撃する時、相手は自身の手札をすべて捨てる。"
         "このクリーチャーの攻撃中、相手はクリーチャーを出せない。"
         "相手のクリーチャーは自分を攻撃できない（相手はプレイヤーを攻撃できない）",
    source=SRC["k30_daiju"])


# ================================================================ 天地命動 バラギアラ／輪廻虹災
def e_baragiara(s, i, u):
    """召喚によって出た時、自分のマナゾーンにあるカードをすべてアンタップする"""
    if u.x.get("summoned"):
        s.P[i].mused = 0
        s.ev("　バラギアラ：自分のマナをすべてアンタップ")


def sp_baragiara(s, i):
    """輪廻虹災：山札の上から5枚を表向きにし、その中からコスト9以下の各文明のカードを1枚ずつ、
    コストを支払わずに実行してもよい。残りを好きな順序で山札の下に置く"""
    p = s.P[i]
    n = min(5, max(0, len(p.deck) - 1))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    d = p.x.get("k30_rin", 0)
    if d < 2:
        p.x["k30_rin"] = d + 1
        for civ in RINNE_CIV:
            if s.over:
                break
            best, bv = None, -1
            for k in top:
                if BY_KEY[k].cost <= 9 and civ in E.MCIV[k] and _execable(s, i, k) and E.PRI[k] > bv:
                    best, bv = k, E.PRI[k]
            if best is not None:
                top.remove(best)
                s.ev(f"　輪廻虹災：{BY_KEY[best].name}（{civ}）をコストを支払わずに実行")
                _free_exec(s, i, best)
        s.P[i].x["k30_rin"] = d
    for k in top:
        s.P[i].deck.insert(0, k)


def fa_baragiara(s, i, av, cv):
    """輪廻∞：バトルゾーンに置いたまま、このカードの呪文側を唱える（コストは支払う）"""
    if not s.has(i, "k30_baragiara"):
        return []
    if av < RINNE_COST or not cv.issuperset(set(RINNE_CIV)) or not s.spell_ok(i, RINNE_COST):
        return []
    return [("x:k30_rinne",)]


def ap_rinne(s, a):
    i = s.tp
    p = s.P[i]
    n = sum(1 for z in p.board if z.k == "k30_baragiara")
    if not n or len(p.mana) - p.mused < RINNE_COST or not s.spell_ok(i, RINNE_COST):
        return
    p.mused += RINNE_COST
    s.ev(f"　輪廻∞：輪廻虹災を場に置いたまま唱える（{RINNE_COST}マナ）")
    s.ramp(i, n)
    _cast_inplace(s, i, "k30_baragiara")


add("k30_baragiara", "天地命動 バラギアラ／輪廻虹災", 9, "N", power=17000, brk=3,
    twin=(RINNE_COST, RINNE_CIV, False), races=("masterhazard", "gransect"), pri=11, roles="acc fin atk",
    enter=e_baragiara, spell=sp_baragiara, freeacts=fa_baragiara, actapply={"x:k30_rinne": ap_rinne},
    text="このクリーチャーが召喚によって出た時、自分のマナゾーンにあるカードをすべてアンタップする。"
         "輪廻∞：このカードの呪文側を、バトルゾーンに置いたまま唱えてもよい（コストは支払う）。"
         "そうした時、自分の《天地命動 バラギアラ》1体につき、自分の山札の上から1枚をマナゾーンに置く。"
         "T・ブレイカー。"
         "呪文側《輪廻虹災》（光水闇火自然・コスト10）：自分の山札の上から5枚を表向きにする。"
         "その中からコスト9以下の各文明のカードを1枚ずつ（文明ごとに重要度のいちばん高いもの）、"
         "コストを支払わずに実行してもよい。残りを好きな順序で山札の下に置く",
    note="輪廻虹災の連鎖は深さ2までに止めている（手順が終わらなくなるのを防ぐため）。"
         "多色カードはどの文明の枠にも使えるものとして扱い、1枚は1つの文明の枠だけに使う",
    source=SRC["k30_baragiara"])


# ================================================================ ヒトリダチ ケントナーク
def e_kento(s, i, u):
    """出た時、次の中から1回選ぶ。▶山札の上から1枚をシールド化する　▶Jビッグ1する"""
    if _jbig1(s, i, u):
        return
    s.add_shield(i)
    s.ev("　ヒトリダチ ケントナーク：山札の上から1枚をシールド化")


def lr_kento(s, i, u, dest, destroy_):
    """各ターンに1度、自分のジョーカーズが離れる時、かわりに自分のシールドを1つ手札に加えてもよい
    （そのシールドのS・トリガーは使えない）"""
    if "jokers" not in u.c.races or not s.has(i, "k30_kento"):
        return False
    if not destroy_ and dest == "hand":
        return False                       # 自分から手札に戻す効果は置き換えない
    p = s.P[i]
    if p.x.get("k30_kent") == s.turn or not p.sh:
        return False
    p.x["k30_kent"] = s.turn
    s.take_shield(i, len(p.sh) - 1, "hand")        # シールドゾーンの出口はここ1か所
    s.ev(f"　ケントナーク：{u.c.name} が離れるかわりにシールドを1つ手札へ（S・トリガーは使えない）")
    return True


add("k30_kento", "ヒトリダチ ケントナーク", 4, "L", power=4500, blocker=True,
    races=("jokers",), pri=6, roles="blk shd",
    enter=e_kento, leaverep=lr_kento,
    text="ブロッカー。"
         "このクリーチャーが出た時、次の中から1回選ぶ。"
         "▶自分の山札の上から1枚を新しいシールドとして置く。"
         "▶Jビッグ1する（自分の他のジョーカーズの、Jビッグ1以外の、出た時にトリガーする能力を1つ使う。"
         "使える相手がいればこちらを選ぶ）。"
         "各ターンに1度、自分のジョーカーズが離れる時、かわりに自分のシールドを1つ手札に加えてもよい。"
         "その「S・トリガー」は使えない",
    note="自分から手札に戻す効果（コストを下げるために戻すなど）は置き換えない（置き換えると損になるため）。"
         "Jビッグ1の元には、Jビッグ1を含む能力を持つカード自身（このカードとジョット・首魁・ジョラゴン）は選ばない",
    source=SRC["k30_kento"])
