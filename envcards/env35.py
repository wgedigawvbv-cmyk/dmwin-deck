"""担当35：DM26-RP3（逆札篇 第3弾 勝敵！逆転おこせ鬼の∞ディスペクター!!）の未実装カード15枚（63/77〜77/77）

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ
      （https://dmwiki.net/《カード名》）と生の wiki ソース（?plugin=template&refer=《カード名》）を
      別の質問で2回ずつ（あいまいな札は3回）読み、コスト・文明・種類・種族・パワー・
      ブレイク数・能力本文が一致することを確かめた。

  この札束に入っている仕組み
    ・**「◯◯の◯影」サイクル**（バギンの闇影／チュチュリスの爆影／ルグンドドの大影）。
      3枚とも「**タマシード**（パワーを持たない）＋呪文」のツインパクトで、
      タマシード側はコスト2・ササゲール2、呪文側はコスト4・S・トリガー。
      **呪文側の効果は1枚ずつ別**（闇＝アンタップしているクリーチャー1体を破壊、
      火＝パワー6000以下のクリーチャー1体を破壊、自然＝コスト5以下のエレメント1つをマナゾーンへ）。
    ・**ササゲール2**（上の3枚と《大地 ワタン-2》）。自分のディスペクター・クリーチャーの
      召喚コストを2少なくし、そうしたらこのエレメントを破壊する（コストは0以下にならない＝下限1）。
    ・**Jクライム**（ツーキンカイソッQ＝6、ツミタテンカーネン＝4）。攻撃する時、これと自分の
      **墓地**のコスト以下のジョーカーズ・クリーチャーを入れ替える。`atkswap=` で書いた。
    ・**Jチェンジ4**（ホッタレマン）。攻撃する時、これと自分の**マナゾーン**のコスト4以下の
      ジョーカーズ・クリーチャーを入れ替える。Jクライムと違い、入れ替えたこのカードは
      破壊ではなく**マナゾーンに置かれる**。
    ・**ジョーカーズレベル**（SMANAGER＝8、ホッタレマン＝5）。
      「自分のバトルゾーンのジョーカーズ」と「自分のマナゾーンにあるジョーカーズ・カード」の合計。
    ・**J・O・E 1**（どうだいジンセー）。コストを1少なくして召喚してよく、こうして出したら
      そのターンの終わりに山札の下に置いて1枚引く。env31 の《ドラマチック息子》と同じ形
      （`freeacts=`／`actapply=`／`tendall=`）で、自分1枚にだけ与えた。
    ・**Jビッグ1**（光る！流れる!!ベンザマン!!!）。自分の他のジョーカーズの「出た時」の能力を1つ使う。

  エンジンの穴とその回避（詳しくは REQUEST_35.md）
    ・ササゲールの「2少なくしても**よい**」は、engine3 の COSTAURA が常に適用されてしまうので
      `costaura=` では書けない（マナが足りているのに自分のエレメントを失う動きになる）。
      追加の手（`freeacts=`／`actapply=`）として「エレメントをささげて召喚する」を作り、
      **そのままでは払えない時だけ**出すようにした（env32 と同じ考え方）。

  調べ直して意外だった点
    ・《バギンの闇影》《チュチュリスの爆影》《ルグンドドの大影》は**クリーチャーではなくタマシード**
      （パワーの行が無い）。1回目の読みでは「クリーチャー側」と答えが返ってきたので、
      3回目に種類の行だけを聞き直して確かめた。
    ・《緑王双命三速斧》は能力が「スピードアタッカー」と「W・ブレイカー」だけの準バニラ
      （火4コスト・パワー6000）。名前が強そうなので3回読み直したが、他の能力は無かった。
    ・《龍装車 ギギャイア》も準バニラで、**コモン初の無条件Q・ブレイカー**（自然8コスト・23000）。
    ・《龍装医 スティーツ》の「出た時」のハンデスは**相手だけでなく各プレイヤー**（自分も1枚捨てる）。
    ・《ホッタレマン》は《ヤッタレマン》とは別物で、コスト軽減を一切持たない
      （自然1コスト・ジョーカーズレベル5が無いと攻撃できない・Jチェンジ4）。
    ・《邪桃臨界怒刀脚》は呪文。パワーを上げる対象は「クリーチャーを1体」で**相手も選べる**。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, opp_all
from envcards.env0 import discard_choice

W = "https://dmwiki.net/"
SRC = {
    "k35_steets": W + "《龍装医 スティーツ》",
    "k35_tsukin": W + "《ツーキンカイソッQ》",
    "k35_tsumitate": W + "《ツミタテンカーネン》",
    "k35_bagin": W + "《バギンの闇影／卑劣な裏切り》",
    "k35_smanager": W + "《SMANAGER》",
    "k35_ryokuou": W + "《緑王双命三速斧》",
    "k35_prochuris": W + "《龍装者 プロチュリス／「主役を目指すッス！」》",
    "k35_doudai": W + "《どうだいジンセー》",
    "k35_chuchuris": W + "《チュチュリスの爆影／“無我怒”駆乱襲》",
    "k35_gigyaia": W + "《龍装車 ギギャイア》",
    "k35_watan": W + "《大地 ワタン-2》",
    "k35_hottare": W + "《ホッタレマン》",
    "k35_rugundodo": W + "《ルグンドドの大影／マメ・ウィズ・ア・ミッション》",
    "k35_jatou": W + "《邪桃臨界怒刀脚》",
    "k35_benzaman": W + "《光る！流れる!!ベンザマン!!!》",
}

SASAGE = ("k35_bagin", "k35_chuchuris", "k35_watan", "k35_rugundodo")   # ササゲール2を持つ自分のカード
JBIG_NO = ("k35_benzaman",)      # Jビッグ1そのものを含む能力（Jビッグ1の元にはできない）
MAXJB = 3                        # Jビッグ1の連鎖の深さの上限（手順が終わらなくなるのを防ぐ安全装置）


# ================================================================ 共通の道具
def _opp_cre(s, i):
    return opp_all(s, i)


def _best_own(s, i, pred=None):
    """「自分のクリーチャー1体」を選ぶ（アンタップのもの、パワーの高いものを優先）"""
    cs = [z for z in s.P[i].board if z.c.kind == "C" and (pred is None or pred(z))]
    if not cs:
        return None
    return max(cs, key=lambda z: (0 if z.tap else 1, s.power(i, z), E.PRI[z.k]))


def _minus_power(s, i, t, n, who):
    """相手のクリーチャー t のパワーをこのターン -n する（0以下になれば破壊される）"""
    t.pw -= n
    s.ev(f"　{who}：{t.c.name} のパワーをこのターン-{n}")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def _jlevel(s, i):
    """ジョーカーズレベル：自分のバトルゾーンのジョーカーズ＋自分のマナゾーンのジョーカーズ・カードの合計"""
    p = s.P[i]
    n = sum(1 for z in p.board if "jokers" in z.c.races)
    return n + sum(1 for k in p.mana if "jokers" in BY_KEY[k].races)


def _plain_cre(k):
    """進化でないクリーチャー（墓地やマナから出せるもの）"""
    c = BY_KEY[k]
    return c.kind == "C" and not (c.evo and not c.neo)


# ================================================================ ササゲール2（4枚で共通）
# 「2少なくしても**よい**」なので、`costaura=` で常に下げると「マナが足りているのに
# わざわざ自分のエレメントを失う」動きになってしまう。そこで追加の手（freeacts／actapply）として
# 「エレメントをささげて召喚する」を作り、**そのままでは払えない時だけ**出すようにした。
# コストを払う時点でエレメントが破壊されるので、クリーチャーが出る前にささげる。
def _sasage_elems(s, i):
    """自分のササゲール持ちのエレメント（失うのがいちばん安いものから）"""
    out = [z for z in s.P[i].board if z.k in SASAGE]
    out.sort(key=lambda z: (s.val(z), z.uid))
    return out


def fa_sasage(s, i, av, cv):
    """ササゲール2：自分のディスペクター・クリーチャーの召喚コストを2少なくし、
    そのエレメントを破壊して召喚する手を足す（普通に払える時は使わない）"""
    p = s.P[i]
    hs = _sasage_elems(s, i)
    if not hs:
        return []
    out = []
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or "dispector" not in c.races:
            continue
        base = s.ccost(i, k, av)
        if base >= 99 or base <= av:
            continue                       # 普通に召喚する手がもうある
        n, use = base, []
        for z in hs:
            use.append(z.uid)
            n = max(1, base - 2 * len(use))      # コストは0以下にならない
            if n <= av:
                break
        if n > av or not cv.issuperset(c.civ):
            continue
        if s.fate(i, k, "hand", True) != "ok":
            continue
        out.append(("x:k35_sasa", k, n, tuple(use)))
    return out


def ap_sasage(s, a):
    i = s.tp
    p = s.P[i]
    k, n, uids = a[1], a[2], a[3]
    if k not in p.hand or len(p.mana) - p.mused < n:
        return
    hs = [z for z in p.board if z.uid in uids and z.k in SASAGE]
    if len(hs) != len(uids):
        return
    p.hand.remove(k)
    p.mused += n
    s.ev(f"ササゲール2：{BY_KEY[k].name} を{n}マナで召喚（{len(hs)}つをささげる）")
    for z in hs:
        if z in p.board:
            s.leave(i, z, "grave", destroy=True)
    if s.over:
        return
    c = BY_KEY[k]
    on = None
    if c.evo and not c.neo:
        on = s.evo_src(i, k)
        if on is None:                     # 進化元がいなくなっていたら出せない
            p.grave.append(k)
            return
    s.enter(i, k, "hand", True, on=on)


# ================================================================ 63/77 龍装医 スティーツ
def e_steets(s, i, u):
    """出た時、各プレイヤーは自身の手札を1枚選んで捨てる"""
    for j in (i, 1 - i):
        k = discard_choice(s, j)
        if k is not None:
            s.ev(f"　スティーツ：{'自分' if j == i else '相手'}が {BY_KEY[k].name} を捨てる")


add("k35_steets", "龍装医 スティーツ", 4, "D", power=8000, brk=2, races=("dragonguild", "mafigang"),
    pri=6, roles="atk dis", enter=e_steets,
    text="W・ブレイカー。このクリーチャーが出た時、各プレイヤーは自身の手札を1枚選び、捨てる"
         "（自分も1枚捨てる。捨てる札は全デッキ共通の決まりでいちばん要らないものを選ぶ）",
    source=SRC["k35_steets"])


# ================================================================ 64/77 ツーキンカイソッQ
def _jcrime(s, i, u, lim, name):
    """Jクライム：攻撃する時、これと自分の墓地のコスト lim 以下のジョーカーズ・クリーチャー1体を入れ替える
    （入れ替えたこのクリーチャーは破壊として墓地へ、出てきたクリーチャーが攻撃を続ける）"""
    p = s.P[i]
    if u not in p.board:
        return None
    best, bv = None, E.PRI[u.k]
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if not _plain_cre(k) or "jokers" not in c.races or c.cost > lim or E.PRI[k] <= bv:
            continue
        if s.fate(i, k, "grave", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return None
    j = p.board.index(u)
    p.grave.remove(best)
    if not s.leave(i, u, "grave", destroy=True):
        p.grave.append(best)
        return None
    nu = E.U(best)
    nu.tap = True
    nu.sick = False
    p.board.insert(min(j, len(p.board)), nu)
    p.ent += 1
    s.ev(f"　{name}：{u.c.name} と墓地の {nu.c.name} を入れ替える")
    fn = E.ENTER.get(best)
    if fn is not None and not s.over:
        fn(s, i, nu)
    for f in E.ENTERWATCH:
        if not s.over:
            f(s, i, nu)
    return nu if nu in p.board else None


def l_tsukin(s, i, u, dest):
    """離れた時、相手のクリーチャー1体を選ぶ。このターン、そのパワーを-4000する"""
    t = s.target(i)
    if t is None:
        return
    _minus_power(s, i, t, 4000, "ツーキンカイソッQ")


add("k35_tsukin", "ツーキンカイソッQ", 3, "D", power=4000, races=("jokers",), pri=5, roles="rem atk",
    atkswap=lambda s, i, u: _jcrime(s, i, u, 6, "Jクライム6"), left=l_tsukin,
    text="Jクライム6：このクリーチャーが攻撃する時、これと自分の墓地にあるコスト6以下のジョーカーズ・"
         "クリーチャー1体を入れ替えてもよい（入れ替えたこのクリーチャーは破壊として墓地に置かれ、"
         "出てきたクリーチャーが攻撃を続ける）。このクリーチャーが離れた時、相手のクリーチャー1体を選ぶ。"
         "このターン、そのクリーチャーのパワーを-4000する（パワー0以下のクリーチャーは破壊される）",
    source=SRC["k35_tsukin"])


# ================================================================ 65/77 ツミタテンカーネン
def e_tsumitate(s, i, u):
    """出た時、自分の山札の上から2枚を墓地に置く"""
    got = s.mill(i, 2)
    if got:
        s.ev(f"　ツミタテンカーネン：山札の上から{len(got)}枚を墓地へ")


add("k35_tsumitate", "ツミタテンカーネン", 2, "D", power=2000, races=("jokers",), pri=4, roles="atk",
    enter=e_tsumitate, atkswap=lambda s, i, u: _jcrime(s, i, u, 4, "Jクライム4"),
    text="このクリーチャーが出た時、自分の山札の上から2枚を墓地に置く。"
         "Jクライム4：このクリーチャーが攻撃する時、これと自分の墓地にあるコスト4以下のジョーカーズ・"
         "クリーチャー1体を入れ替えてもよい",
    source=SRC["k35_tsumitate"])


# ================================================================ 66/77 バギンの闇影／卑劣な裏切り
def sp_bagin(s, i):
    """相手のアンタップしているクリーチャーを1体選び、破壊する"""
    t = s.target(i, lambda z: not z.tap)
    if t is None:
        return
    s.ev(f"　卑劣な裏切り：{t.c.name} を破壊")
    s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


add("k35_bagin", "バギンの闇影／卑劣な裏切り", 2, "D", kind="T", races=("mafigang", "distas"),
    twin=(4, "D", True), pri=5, roles="acc rem trg",
    spell=sp_bagin,
    actapply={"x:k35_sasa": ap_sasage},
    text="【タマシード】ササゲール2：自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたら、このエレメントを破壊する（コストは0以下にならない）。"
         "【呪文・コスト4】S・トリガー。相手のアンタップしているクリーチャーを1体選び、破壊する",
    note="ササゲール2 は「2少なくしてもよい」という選択なので、常にかかる costaura ではなく"
         "追加の手（freeacts）で表し、そのままでは払えないディスペクターにだけ使う",
    source=SRC["k35_bagin"])


# ================================================================ 67/77 SMANAGER
def e_smanager(s, i, u):
    """出た時、相手のクリーチャーを1体選んでもよい。その選んだクリーチャーとこのクリーチャーをバトルさせる
    （勝てる相手がいる時だけ選ぶ＝任意の選択はこのシミュレーター共通の決まりで決める）"""
    if u not in s.P[i].board:
        return
    ap = s.power(i, u)
    t = s.target(i, lambda z: s.power(1 - i, z) <= ap)
    if t is None:
        return
    s.ev(f"　SMANAGER：{u.c.name} と {t.c.name} をバトルさせる")
    s.battle(i, u, 1 - i, t)


add("k35_smanager", "SMANAGER", 5, "F", power=5000, trig=True, sa=True, races=("jokers",),
    pri=8, roles="trg rem atk", enter=e_smanager,
    powerx=lambda s, i, u, atk: 5000 if _jlevel(s, i) >= 8 else 0,
    brkx=lambda s, i, u: 2 if _jlevel(s, i) >= 8 else None,
    text="S・トリガー。スピードアタッカー。このクリーチャーが出た時、相手のクリーチャーを1体選んでもよい。"
         "その選んだクリーチャーとこのクリーチャーをバトルさせる（勝てる相手がいる時だけ選ぶ）。"
         "自分の、ジョーカーズとマナゾーンにあるジョーカーズ・カードが合計8つ以上なら、"
         "このクリーチャーのパワーを+5000し、「W・ブレイカー」を与える",
    source=SRC["k35_smanager"])


# ================================================================ 68/77 緑王双命三速斧
add("k35_ryokuou", "緑王双命三速斧", 4, "F", power=6000, brk=2, sa=True,
    races=("demonio", "onirexstars"), pri=7, roles="atk",
    text="スピードアタッカー。W・ブレイカー（他の能力は持たない準バニラ）",
    source=SRC["k35_ryokuou"])


# ================================================================ 69/77 龍装者 プロチュリス／「主役を目指すッス！」
def sp_prochuris(s, i):
    """相手のパワー1000以下のクリーチャーをすべて破壊する"""
    ts = [z for z in opp_all(s, i) if s.power(1 - i, z) <= 1000]
    if not ts:
        return
    s.ev(f"　「主役を目指すッス！」：相手のパワー1000以下のクリーチャーを{len(ts)}体破壊")
    for z in ts:
        if z in s.P[1 - i].board:
            s.leave(1 - i, z, "grave", by_opp=True, destroy=True)


add("k35_prochuris", "龍装者 プロチュリス／「主役を目指すッス！」", 3, "F", power=4000, sa=True,
    races=("dragonguild", "beatjockey"), twin=(1, "F", False), pri=5, roles="atk rem",
    spell=sp_prochuris,
    text="【クリーチャー・コスト3】スピードアタッカー。"
         "【呪文・コスト1】相手のパワー1000以下のクリーチャーをすべて破壊する",
    source=SRC["k35_prochuris"])


# ================================================================ 70/77 どうだいジンセー
def e_doudai(s, i, u):
    """出た時、このターン、自分の他のクリーチャー1体に「スピードアタッカー」を与える"""
    z = _best_own(s, i, lambda x: x is not u and not x.sa and not x.c.sa)
    if z is None:
        z = _best_own(s, i, lambda x: x is not u)
    if z is None:
        return
    z.sa = True
    s.ev(f"　どうだいジンセー：{z.c.name} にこのターン「スピードアタッカー」を与える")


def fa_doudai(s, i, av, cv):
    """J・O・E 1：このクリーチャーを、コストを1少なくして召喚してもよい"""
    p = s.P[i]
    if "k35_doudai" not in p.hand:
        return []
    c = BY_KEY["k35_doudai"]
    n = max(0, s.ccost(i, "k35_doudai", av) - 1)
    if n > av or (n > 0 and not cv.issuperset(c.civ)):
        return []
    if s.fate(i, "k35_doudai", "hand", True) != "ok":
        return []
    return [("x:k35_joe", n)]


def ap_doudai(s, a):
    i = s.tp
    p = s.P[i]
    if "k35_doudai" not in p.hand:
        return
    p.hand.remove("k35_doudai")
    p.mused += a[1]
    s.ev(f"J・O・E 1：どうだいジンセー（{a[1]}マナ）")
    u = s.enter(i, "k35_doudai", "hand", True)
    if u is not None:
        u.x["k35_joe"] = s.turn


def te_doudai(s, i, u):
    """J・O・E 1：こうして出したら、このターンの終わりに山札の下に置いて1枚引く"""
    if u.k != "k35_doudai" or u.x.get("k35_joe") != s.turn:
        return
    p = s.P[i]
    if u not in p.board:
        return
    p.board.remove(u)
    p.deck.insert(0, u.k)
    for k in u.under:
        p.deck.insert(0, k)
    s.ev("　J・O・E 1：どうだいジンセー を山札の下に置いて1枚引く")
    s.draw(i)


add("k35_doudai", "どうだいジンセー", 2, "F", power=2000, races=("jokers",), pri=4, roles="atk draw",
    enter=e_doudai, freeacts=fa_doudai, actapply={"x:k35_joe": ap_doudai}, tendall=te_doudai,
    text="J・O・E 1：このクリーチャーを、コストを1少なくして召喚してもよい。こうして出したら、"
         "このターンの終わりに、それを自分の山札の下に置く。そうしたら、カードを1枚引く。"
         "このクリーチャーが出た時、このターン、自分の他のクリーチャー1体に「スピードアタッカー」を与える",
    source=SRC["k35_doudai"])


# ================================================================ 71/77 チュチュリスの爆影／“無我怒”駆乱襲
def sp_chuchuris(s, i):
    """相手のパワー6000以下のクリーチャーを1体選び、破壊する"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 6000)
    if t is None:
        return
    s.ev(f"　“無我怒”駆乱襲：{t.c.name} を破壊")
    s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


add("k35_chuchuris", "チュチュリスの爆影／“無我怒”駆乱襲", 2, "F", kind="T",
    races=("beatjockey", "distas"), twin=(4, "F", True), pri=5, roles="acc rem trg",
    spell=sp_chuchuris,
    text="【タマシード】ササゲール2：自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたら、このエレメントを破壊する（コストは0以下にならない）。"
         "【呪文・コスト4】S・トリガー。相手のパワー6000以下のクリーチャーを1体選び、破壊する",
    note="ササゲール2 の仕掛けは《バギンの闇影》と同じ関数を共有している"
         "（そのままでは払えないディスペクターにだけ使う）",
    source=SRC["k35_chuchuris"])


# ================================================================ 72/77 龍装車 ギギャイア
add("k35_gigyaia", "龍装車 ギギャイア", 8, "N", power=23000, brk=4,
    races=("dragonguild", "gransect"), pri=10, roles="atk fin",
    text="Q・ブレイカー（シールドを4つブレイクする。他の能力は持たない準バニラ）",
    source=SRC["k35_gigyaia"])


# ================================================================ 73/77 大地 ワタン-2
def l_watan(s, i, u, dest):
    """離れた時、このターン、自分のクリーチャー1体に「マッハファイター」を与える"""
    z = _best_own(s, i, lambda x: x.sick and not x.tap and not x.c.mach)
    if z is None:
        z = _best_own(s, i, lambda x: not x.c.mach)
    if z is None:
        return
    z.x["k35_mach"] = s.turn
    s.ev(f"　ワタン-2：{z.c.name} にこのターン「マッハファイター」を与える")


add("k35_watan", "大地 ワタン-2", 3, "N", power=3000, mach=True, races=("gransect", "distas"),
    pri=5, roles="acc rem atk", left=l_watan,
    machok=lambda s, i, u: u.x.get("k35_mach") == s.turn,
    freeacts=fa_sasage,                       # ← ササゲールの手は env35 に1回だけ登録する
    text="マッハファイター。ササゲール2：自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたら、このエレメントを破壊する（コストは0以下にならない）。"
         "このクリーチャーが離れた時、このターン、自分のクリーチャー1体に「マッハファイター」を与える",
    source=SRC["k35_watan"])


# ================================================================ 74/77 ホッタレマン
def swap_hottare(s, i, u):
    """Jチェンジ4：攻撃する時、これと自分のマナゾーンのコスト4以下のジョーカーズ・クリーチャー1体を入れ替える"""
    p = s.P[i]
    if u not in p.board:
        return None
    best, bv = None, E.PRI[u.k]
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if not _plain_cre(k) or "jokers" not in c.races or c.cost > 4 or E.PRI[k] <= bv:
            continue
        if s.fate(i, k, "mana", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return None
    j = p.board.index(u)
    if not s.leave(i, u, "mana"):
        return None
    if best not in p.mana:                    # 自分自身がマナに置かれて並びが変わった場合の保険
        return None
    s.take_mana(i, best)
    nu = E.U(best)
    nu.tap = True
    nu.sick = False
    p.board.insert(min(j, len(p.board)), nu)
    p.ent += 1
    s.ev(f"　Jチェンジ4：{u.c.name} をマナゾーンに置き、マナの {nu.c.name} と入れ替える")
    fn = E.ENTER.get(best)
    if fn is not None and not s.over:
        fn(s, i, nu)
    for f in E.ENTERWATCH:
        if not s.over:
            f(s, i, nu)
    return nu if nu in p.board else None


add("k35_hottare", "ホッタレマン", 1, "N", power=1000, races=("jokers",), pri=3, roles="atk",
    cantatk=lambda s, i, u: _jlevel(s, i) < 5, atkswap=swap_hottare,
    text="自分の、ジョーカーズとマナゾーンにあるジョーカーズ・カードが合計5つ以上なければ、"
         "このクリーチャーは攻撃できない。"
         "Jチェンジ4：このクリーチャーが攻撃する時、これと自分のマナゾーンにあるコスト4以下の"
         "ジョーカーズ・クリーチャー1体を入れ替えてもよい（このカードはマナゾーンに置かれ、"
         "出てきたクリーチャーが攻撃を続ける）",
    source=SRC["k35_hottare"])


# ================================================================ 75/77 ルグンドドの大影／マメ・ウィズ・ア・ミッション
def _worst_own_elem(s, i, pred=None):
    """自分のエレメントのうち、失うのがいちばん安いもの"""
    cs = [z for z in s.P[i].board if z.c.kind in "CTXG" and (pred is None or pred(z))]
    if not cs:
        return None
    return min(cs, key=s.val)


def sp_rugundodo(s, i):
    """コスト5以下のエレメントを1つ選び、持ち主のマナゾーンに置く"""
    t = s.target(i, lambda z: z.c.cost <= 5, kinds="CTX")
    if t is not None:
        s.ev(f"　マメ・ウィズ・ア・ミッション：{t.c.name} を相手のマナゾーンへ")
        s.leave(1 - i, t, "mana", by_opp=True)
        return
    z = _worst_own_elem(s, i, lambda x: x.c.cost <= 5)       # 相手に対象がいなければ強制で自分のものを置く
    if z is None:
        return
    s.ev(f"　マメ・ウィズ・ア・ミッション：選べる相手のエレメントが無いので {z.c.name} を自分のマナゾーンへ")
    s.leave(i, z, "mana")


add("k35_rugundodo", "ルグンドドの大影／マメ・ウィズ・ア・ミッション", 2, "N", kind="T",
    races=("gransect", "distas"), twin=(4, "N", True), pri=5, roles="acc rem trg",
    spell=sp_rugundodo,
    status="partial",
    text="【タマシード】ササゲール2：自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたら、このエレメントを破壊する（コストは0以下にならない）。"
         "【呪文・コスト4】S・トリガー。コスト5以下のエレメントを1つ選び、持ち主のマナゾーンに置く"
         "（相手のいちばん重要なものを選ぶ。相手に対象が無ければ強制なので自分のいちばん安いものを置く）",
    note="「エレメント」のうち城（kind=\"G\"）は、このシミュレーターでは表向きのシールドとして"
         "シールドゾーンに置かれ、バトルゾーンには無いので選べない"
         "（クリーチャー・タマシード・クロスギアだけを対象にした）",
    source=SRC["k35_rugundodo"])


# ================================================================ 76/77 邪桃臨界怒刀脚
def sp_jatou(s, i):
    """クリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを+2000する。
    自分と相手のクリーチャーを1体ずつ選ぶ。その2体をバトルさせる"""
    z = _best_own(s, i)
    if z is None:                              # 自分にクリーチャーがいなければ、強制なので相手のいちばん安いものを上げる
        ts = _opp_cre(s, i)
        if ts:
            t = min(ts, key=s.val)
            t.pw += 2000
            s.ev(f"　邪桃臨界怒刀脚：選べる自分のクリーチャーが無いので {t.c.name} のパワーを+2000")
        return
    z.pw += 2000
    s.ev(f"　邪桃臨界怒刀脚：{z.c.name} のパワーをこのターン+2000")
    if s.over or z not in s.P[i].board:
        return
    ap = s.power(i, z)
    t = s.target(i, lambda x: s.power(1 - i, x) <= ap)
    if t is None:
        return
    s.ev(f"　邪桃臨界怒刀脚：{z.c.name} と {t.c.name} をバトルさせる")
    s.battle(i, z, 1 - i, t)


add("k35_jatou", "邪桃臨界怒刀脚", 2, "N", kind="S", trig=True, pri=3, roles="rem trg atk",
    spell=sp_jatou,
    text="S・トリガー。クリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを+2000する。"
         "自分と相手のクリーチャーを1体ずつ選ぶ。その2体をバトルさせる"
         "（パワーを上げるのは自分のいちばん強いクリーチャー、バトルは勝てる相手がいる時だけ選ぶ）",
    source=SRC["k35_jatou"])


# ================================================================ 77/77 光る！流れる!!ベンザマン!!!
def _jbig_cands(s, i, u):
    return [z for z in s.P[i].board
            if z is not u and z.c.kind == "C" and "jokers" in z.c.races
            and z.k not in JBIG_NO and E.ENTER.get(z.k) is not None]


def _jbig(s, i, u):
    """Jビッグ1：自分の他のジョーカーズの、Jビッグ1以外の、出た時にトリガーする能力を1つ使う"""
    p = s.P[i]
    cands = _jbig_cands(s, i, u)
    d = p.x.get("k35_jbig", 0)
    if not cands or d >= MAXJB or s.over:
        return False
    z = max(cands, key=lambda x: E.PRI[x.k])
    p.x["k35_jbig"] = d + 1
    s.ev(f"　Jビッグ1：{z.c.name} の「出た時」の能力を使う")
    E.ENTER[z.k](s, i, z)
    s.P[i].x["k35_jbig"] = d
    return True


def e_benzaman(s, i, u):
    """出た時、次の中から1回選ぶ。▶カードを1枚引く ▶Jビッグ1する
    （使い回せる「出た時」がそれなりに重いものなら Jビッグ1、そうでなければ1枚引く）"""
    cands = _jbig_cands(s, i, u)
    if cands and max(E.PRI[z.k] for z in cands) >= 4 and _jbig(s, i, u):
        return
    s.draw(i)
    s.ev("　ベンザマン!!!：カードを1枚引く")


add("k35_benzaman", "光る！流れる!!ベンザマン!!!", 2, "LW", power=2000, races=("jokers",),
    pri=4, roles="draw", enter=e_benzaman,
    text="このクリーチャーが出た時、次の中から1回選ぶ。▶カードを1枚引く。"
         "▶Jビッグ1する（自分の他のジョーカーズの、Jビッグ1以外の、出た時にトリガーする能力を1つ使う）。"
         "使い回せる「出た時」の重要度が4以上あれば Jビッグ1、そうでなければ1枚引く",
    source=SRC["k35_benzaman"])
