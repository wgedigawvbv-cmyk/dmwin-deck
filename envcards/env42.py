"""担当42：DM26-EX2「悪感謝祭 カリスマBEST」の15枚（key は k42_）

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ
      （https://dmwiki.net/《カード名》）と生の wiki ソース（?plugin=template&refer=《カード名》）を
      別の質問で2回ずつ読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
      どちらの読みでも一致することを確かめた（1枚だけ3回読んだ＝一王伝双三眼槍の鬼タイムの条件文）。

  この札束に入っている仕組み
    ・**「〜の決闘（カリスマ）」サイクル4枚**（覚悟／野望／覇道／孤高）。
      コスト6・3色・S・トリガーの呪文で、全部が
      「このカードを自分の手札からマナゾーンに置いた時、自分の手札にある〈種族〉カードを1枚
        表向きにしてもよい。そうしたら、このカードをアンタップする」を持つ。
      多色カードはマナゾーンにタップして置かれる（エンジンの `add_mana` が `MULTI` を見てそうしている）ので、
      これは `chargex=` で `p.mused` を1戻す形で書けた。**手札を表向きにする所は盤面に影響しない**
      （このシミュレーターに「公開された手札」という状態がない）ので、
      「見せられる札があるならアンタップする」とだけ書いている。
    ・**鬼エンド＋シンカライズ＋「負ける時の置き換え」**（一王二命三眼槍の封）。
      タマシードなので `place_tama` で置く（`enter` ではない）。
    ・**別コストの召喚＋シールドを手札に加える**（一王伝双三眼槍）。`costx=` と `payx=` の組。
    ・**＜鬼タイム＞の負け置き換え**（同）。`loserep=`。条件は「自分のシールドが3つ以下」ではなく
      **「自分と相手のシールドの数が合計6つ以下」**（3回読んで確かめた）。
    ・**マッドネス風の「相手の能力・呪文で手札から捨てられた時、墓地から出る」**（ワダユメ＝縛＝ノミコト）。
      `discardx=`。
    ・**奇数／偶数を選ぶ攻撃・ブロック禁止**（同）。あとから出たクリーチャーにも効くように、
      選んだ側の `p.x` に（偶奇, いつまで）を書いて `atklock=`／`blocklock=` で見ている。
    ・**超魂X**（轟速 ザ・リフル）。クリーチャーの下にあれば、そのクリーチャーにも能力を与える。
      スピードアタッカーの分は `saok=` で書けた（下にこのカードがあるかを見る）。
    ・**侵略ZERO**（「オレたちのZEROの世界を造るまで」）。相手のターンの終わりに、そのターン
      相手がコストを支払わずにクリーチャーを出していたら、手札からただで唱える。
      `enterwatch=`（出来事の記録）と `tendp=`（場が空でも呼ばれるターンの終わり）の組。
    ・**G城**（希望の太陽 マイハマタワー）。自分のアーマードにブロッカーとスピードアタッカーを与え、
      各ターンの終わりに全部アンタップする。表向きでシールドゾーンを離れた時の誘発は `shieldout=`。
    ・**ツインパクト＋クリーチャー側がS・トリガー**（シンクロ・ルピア）。
      呪文側の「シールドを1つ見て1枚を表向きか裏向きにする」は、このエンジンでは
      「表向きのシールドは先に割られる」「表向きのシールドはS・トリガーで使えない」
      「表向きのG城だけが城として働く」の3つに効く操作なので、そのどれかが得になる向きに機械的に選ぶ。
    ・**ゴッド支援**（野望の決闘・プライマル・サーガ・極限龍神ヘヴィ）。
      このシミュレーターの既存カードはゴッドの種族に "god" を必ず入れる作りなので、それで数えている。
    ・**G・リンク**（極限龍神ヘヴィの「左G・リンクOMG」）。`godlink=("L", ())` で位置を宣言し、
      つなぐ操作は `freeacts=`／`actapply=` の追加の手（`s.can_link`／`s.god_link`）で出す。
      リンクしている間だけの「相手のクリーチャーは可能ならこれを攻撃する」は `mustatktgt=`。

  調べ直して意外だった点
    ・《シンクロ・ルピア》は**水文明**で、種族が「アーマード・ドラゴン／ファイアー・バード／スノーフェアリー」。
      名前が「ルピア」なので火だと思い込みそうだが、2回とも水だった。しかも**クリーチャー側がS・トリガー**で、
      呪文側《「D4に敗北は許されない！」》（コスト3・水）にはS・トリガーが**ない**。
    ・《轟速 ザ・リフル》は**侵略を持っていない**。「侵略者」は種族で、このカード自身は
      スピードアタッカーと超魂Xだけ。侵略の**下敷き**になるためのカード。
    ・《極限龍神ヘヴィ》のパワー表記は「5000+」（ゴッドリンクで増えるため）。
      収録はDMEX-17とDM23-EX1が先で、DM26-EX2は再録。
    ・《一王伝双三眼槍》の鬼タイムの条件が**両者のシールドの合計**で書かれている
      （ふつうの鬼タイムは「自分のシールドが3つ以下」なので読み間違えやすい）。
      また、シールドが1枚以下でも[闇/火(3)]での召喚自体はできる（裁定欄）。
    ・《覇道の決闘》だけは除去がなく、マナ加速＋マナからソニック・コマンドを2体出す札だった。
      サイクルで揃っているのは「コスト6・3色・S・トリガー・マナに置いた時のアンタップ」の4点だけ。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move
from envcards.env0 import own_loss, owner_of, worst_own

W = "https://dmwiki.net/"
SRC = {
    "k42_wadayume": W + "《ワダユメ＝縛＝ノミコト》",
    "k42_kakugo": W + "《覚悟の決闘》",
    "k42_yabou": W + "《野望の決闘》",
    "k42_hadou": W + "《覇道の決闘》",
    "k42_baradofu": W + "《一王二命三眼槍の封》",
    "k42_kokou": W + "《孤高の決闘》",
    "k42_dsign": W + "《ドラゴンズ・サイン》",
    "k42_synchro": W + "《シンクロ・ルピア／「D4に敗北は許されない！」》",
    "k42_heavy": W + "《極限龍神ヘヴィ》",
    "k42_kangoku": W + "《カンゴク入道の巻》",
    "k42_primal": W + "《プライマル・サーガ》",
    "k42_rifle": W + "《轟速 ザ・リフル》",
    "k42_zeroworld": W + "《「オレたちのZEROの世界を造るまで」》",
    "k42_maihama": W + "《希望の太陽 マイハマタワー》",
    "k42_baradodouble": W + "《一王伝双三眼槍》",
}


# ---------------------------------------------------------------- G・リンク（共通の道具）
# ゴッドを横につないで1体のクリーチャーとして扱う。パワーは合計、能力と文明は併せ持ち、
# 離れる時は構成しているカードのうち1枚だけが離れる（エンジンの `parts`／`god_link` が面倒を見る）。
# つなぐ操作は「自分のメインステップ中の追加の手」として出す（エンジンの決まり）。
# 位置（左 L・中央 C・右 R）が重ならない組み合わせだけつなげられる
# （「左G・リンク」は「中央」か「右」を持つゴッドの左にしか付けない、という決まりをこれで表している）。
_GL_KEYS = frozenset(("k42_heavy",))
_GL_ACT = "x:k42_glink"


def _gl_ok(s, i, u, base):
    """u を base の横につなげるか（エンジンの可否＋G・リンクの位置が重ならないこと）"""
    if u.link or u.k not in E.GODLINK or not s.can_link(i, u, base):
        return False
    pos = {E.GODLINK[z.k][0] for z in s.parts(base) if z.k in E.GODLINK}
    return bool(pos) and E.GODLINK[u.k][0] not in pos


def _gl_acts(s, i, av, cv):
    """追加の手：このモジュールのゴッドを、自分の場のゴッドの横につなぐ
    （u 側が自分のモジュールのカードの組だけを出すので、ほかのモジュールと重複しない）"""
    out = []
    bd = s.P[i].board
    for u in bd:
        if u.k not in _GL_KEYS:
            continue
        for base in bd:
            if base is not u and _gl_ok(s, i, u, base):
                out.append((_GL_ACT, u.uid, base.uid))
    return out


def _gl_apply(s, a):
    i = s.tp
    p = s.P[i]
    u = next((z for z in p.board if z.uid == a[1] and z.k in _GL_KEYS), None)
    base = next((z for z in p.board if z.uid == a[2]), None)
    if u is None or base is None or not _gl_ok(s, i, u, base):
        return
    p.board.remove(u)
    if u.tap:
        base.tap = True        # つなぐ相手が1体でもタップしていれば、1体のクリーチャーはタップしたまま
    s.god_link(i, u, base)


# ================================================================ 共通の道具
def _top(s, i, n):
    """山札の上からn枚を取り出す（山札は1枚残す）"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    return [p.deck.pop() for _ in range(n)] if n > 0 else []


def _is_god(c):
    """ゴッドかどうか（ゴッド・ノヴァOMG なども含む。既存カードは種族に "god" を必ず入れている）"""
    return any(r.startswith("god") for r in c.races)


def _mf(s, i, u):
    """u はいまマッハファイターとして（アンタップしている相手も）攻撃できるか"""
    if not u.sick:
        return False
    return bool(u.c.mach) or bool(E.MACHOK and any(f(s, i, u) for f in E.MACHOK))


def _is_armored(c):
    """アーマード（アーマード・ドラゴン／アーマード・ファイアー・バードなども含む）"""
    return c.kind == "C" and any("armored" in r for r in c.races)


def _plain_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _until_my_turn(s, i):
    """「次の自分のターンのはじめまで」を表すターン番号（これ以下なら、まだ効いている）"""
    return s.turn + (1 if s.tp == i else 0)


def _grant_blocker(s, i, u, label):
    """次の自分のターンのはじめまで u に「ブロッカー」を与える"""
    u.x["k42_blk"] = _until_my_turn(s, i)
    s.ev(f"　{label}：{u.c.name} に「ブロッカー」を与える")


def bo_granted(s, u):
    """与えられた「ブロッカー」（覇道の決闘・ドラゴンズ・サイン）。

    全体に効く差し込み口なので、与えられていないカードでは必ずすぐ返る。"""
    return u.x.get("k42_blk", -1) >= s.turn


def _keep_face_down(k):
    """表向きにしてはいけないシールドか（G城は表向きだと城として働き、
    《「敬虔なる警官」》は表向きだとターンのはじめにバトルゾーンへ出る）"""
    return BY_KEY[k].kind == "G" or k == "keikan"


def _take_best_shield(s, i, label):
    """自分のシールド1つを手札に加える（S・トリガーは使えない）。
    表向きのG城は、離れると墓地に行ってしまうので最後に選ぶ"""
    p = s.P[i]
    if not p.sh:
        return None
    cands = [j for j in range(len(p.sh)) if not (p.sh[j][1] and BY_KEY[p.sh[j][0]].kind == "G")]
    if not cands:
        return None
    j = max(cands, key=lambda x: E.PRI[p.sh[x][0]])
    r = s.take_shield(i, j, "hand")
    if r is not None:
        s.ev(f"　{label}：シールドの {BY_KEY[r[0]].name} を手札へ（S・トリガーは使えない）")
    return r


def _reveal_untap(race, label):
    """「このカードを自分の手札からマナゾーンに置いた時、自分の手札にある〈race〉カードを1枚
    表向きにしてもよい。そうしたら、このカードをアンタップする」

    多色カードはタップしてマナゾーンに置かれる（add_mana が MULTI を見ている）ので、
    p.mused を1戻すのが「アンタップする」にあたる。"""
    def f(s, i):
        p = s.P[i]
        if not any(race in BY_KEY[k].races for k in p.hand):
            return
        if p.mused <= 0:
            return
        p.mused -= 1
        s.ev(f"　{label}：手札の札を見せて、マナに置いたこのカードをアンタップ")
    return f


def _best_opp_cost(s, i):
    """相手の場でいちばん値打ちのあるクリーチャーのコスト（捨てる札・墓地に置く札を決めるのに使う）"""
    best, bv = 0, -1
    for z in s.P[1 - i].board:
        if z.c.kind == "C" and not z.jd and s.val(z) > bv:
            best, bv = z.c.cost, s.val(z)
    return best


# ================================================================ ワダユメ＝縛＝ノミコト
def _wada_choose(s, i, u):
    """出た時または攻撃する時、奇数か偶数を選ぶ。
    次の自分のターンのはじめまで、選んだコストの相手のクリーチャーは攻撃もブロックもできない"""
    val = [0, 0]
    for z in s.P[1 - i].board:
        if z.c.kind == "C":
            val[z.c.cost % 2] += s.val(z)
    par = 0 if val[0] >= val[1] else 1
    s.P[i].x["k42_wada"] = (par, _until_my_turn(s, i))
    s.ev(f"　ワダユメ＝縛＝ノミコト：{'偶数' if par == 0 else '奇数'}を選ぶ"
         "（そのコストの相手のクリーチャーは攻撃もブロックもできない）")


def _wada_locked(s, i, u):
    """u（持ち主 i）が、相手のワダユメの選んだ偶奇で縛られているか"""
    e = s.P[1 - i].x.get("k42_wada")
    if not e:
        return False
    par, until = e
    return until >= s.turn and u.c.kind == "C" and u.c.cost % 2 == par


def al_wada(s, i, u):
    return _wada_locked(s, i, u)


def bl_wada(s, u):
    return _wada_locked(s, owner_of(s, u), u)


def dx_wadayume(s, i, k):
    """相手のクリーチャーの能力または呪文によって手札から捨てられた時、墓地から出てもよい

    エンジンの discard には「誰の効果で捨てたか」が渡らないので、
    **自分のターン中に捨てた分は自分の効果とみなして誘発させない**という近似にしている。"""
    if s.tp == i or s.over:
        return False
    p = s.P[i]
    if k not in p.hand:
        return False
    p.hand.remove(k)
    s.grave_put(i, k)
    if k not in p.grave:
        return True                                   # 墓地に置かれた時の別の効果で出ていった
    if s.fate(i, k, "grave", False) != "ok":
        return True
    p.grave.remove(k)
    s.ev("　ワダユメ＝縛＝ノミコト：捨てられたので自分の墓地から出る")
    s.enter(i, k, "grave", False)
    return True


add("k42_wadayume", "ワダユメ＝縛＝ノミコト", 7, "LWD", power=11000, brk=2, blocker=True,
    races=("mizugami", "lostcrusader"), pri=10, roles="blk dis atk",
    enter=_wada_choose, attack=_wada_choose, discardx=dx_wadayume, atklock=al_wada, blocklock=bl_wada,
    text="ブロッカー、W・ブレイカー。"
         "相手のクリーチャーの能力または呪文によって、このクリーチャーが自分の手札から捨てられた時、"
         "このクリーチャーを自分の墓地から出してもよい。"
         "このクリーチャーが出た時または攻撃する時、奇数または偶数を選ぶ。"
         "次の自分のターンのはじめまで、選んだコストの相手のクリーチャーは攻撃もブロックもできない"
         "（相手の場で縛れる値打ちの合計が大きい方の偶奇を選ぶ）",
    note="「相手のクリーチャーの能力または呪文によって捨てられた時」の判定。"
         "エンジンの discard（DISCARDX）には「誰の効果で捨てたか」が渡らないので、"
         "自分のターン中に捨てられた分は自分の効果（コストとしての手札を捨てる）とみなして誘発させず、"
         "相手のターン中に捨てられた分だけ誘発する近似にした。"
         "相手が自分のターンにS・トリガー等でハンデスした場合は誘発しない。",
    status="partial", source=SRC["k42_wadayume"])


# ================================================================ 覚悟の決闘
def sp_kakugo(s, i):
    """自分の山札の上から3枚を見る。その中から1枚を表向きでシールド化し、残りを1枚ずつ手札と墓地に置く。
    こうして墓地に置いたカード以下のコストの相手のクリーチャーを1体選び、破壊する"""
    p = s.P[i]
    top = _top(s, i, 3)
    if not top:
        return
    need = _best_opp_cost(s, i)
    # 墓地に置く札：相手のいちばんおいしいクリーチャーを破壊できる中でいちばん安いもの
    # （届くものが無ければ、いちばんコストの大きいものを置いて射程を伸ばす）
    reach = [k for k in top if BY_KEY[k].cost >= need]
    gk = min(reach, key=E.PRI.get) if reach else max(top, key=lambda k: (BY_KEY[k].cost, E.PRI[k]))
    top.remove(gk)
    if top:                                           # 手札に加える札：いちばん値打ちのあるもの
        hk = max(top, key=E.PRI.get)
        top.remove(hk)
        p.hand.append(hk)
        s.ev(f"　覚悟の決闘：{BY_KEY[hk].name} を手札へ")
    if top:                                           # 残りを表向きでシールド化
        sk = top.pop()
        if not s.add_shield(i, sk, True):
            p.hand.append(sk)
        else:
            s.ev(f"　覚悟の決闘：{BY_KEY[sk].name} を表向きでシールド化")
    s.grave_put(i, gk)
    n = BY_KEY[gk].cost
    s.ev(f"　覚悟の決闘：{BY_KEY[gk].name}（コスト{n}）を墓地へ")
    t = s.target(i, lambda z: z.c.cost <= n)
    if t is not None:
        destroy(s, i, t)


add("k42_kakugo", "覚悟の決闘", 6, "LWF", kind="S", trig=True, pri=7, roles="trg rem draw shd",
    spell=sp_kakugo, chargex=_reveal_untap("armoreddragon", "覚悟の決闘"),
    text="S・トリガー。自分の山札の上から3枚を見る。その中から1枚を表向きでシールド化し、"
         "残りを1枚ずつ、手札と墓地に置く。こうして墓地に置いたカード以下のコストの"
         "相手のクリーチャーを1体選び、破壊する"
         "（墓地に置く札は、相手のいちばん値打ちのあるクリーチャーに届く中でいちばん安いもの。"
         "届く札が無ければコストがいちばん大きい札を置く）。"
         "このカードを自分の手札からマナゾーンに置いた時、自分の手札にあるアーマード・ドラゴン・カードを"
         "1枚、表向きにしてもよい。そうしたら、このカードをアンタップする"
         "（多色なのでマナゾーンにはタップして置かれる）",
    note="山札が3枚に足りない時は、墓地→手札→シールドの順に置ける分だけ置く"
         "（公式のテキストはシールド化が先だが、墓地に置いた札で破壊の射程が決まるので、"
         "枚数が足りない時は墓地を先に埋める形にした）",
    source=SRC["k42_kakugo"])


# ================================================================ 野望の決闘
def sp_yabou(s, i):
    """相手のクリーチャーを1体選び、破壊する。その選んだクリーチャーよりもコストが小さいゴッドを1つ、
    自分の墓地から出してもよい。こうして出さなければ、カードを2枚引いてもよい"""
    t = s.target(i)
    got = None
    if t is not None:
        n = t.c.cost
        destroy(s, i, t)
        got = s.revive(i, lambda c: _is_god(c) and c.cost < n, "grave")
    if got is None:
        s.draw(i, 2)


add("k42_yabou", "野望の決闘", 6, "WDF", kind="S", trig=True, pri=7, roles="trg rem draw",
    spell=sp_yabou, chargex=_reveal_untap("god", "野望の決闘"),
    text="S・トリガー。相手のクリーチャーを1体選び、破壊する。"
         "その選んだクリーチャーよりもコストが小さいゴッドを1つ、自分の墓地から出してもよい。"
         "こうして出さなければ、カードを2枚引いてもよい。"
         "このカードを自分の手札からマナゾーンに置いた時、自分の手札にあるゴッド・カードを1枚、"
         "表向きにしてもよい。そうしたら、このカードをアンタップする"
         "（多色なのでマナゾーンにはタップして置かれる）",
    source=SRC["k42_yabou"])


# ================================================================ 覇道の決闘
def sp_hadou(s, i):
    """自分の山札の上から1枚目をマナゾーンに置く。その後、コストの合計が8以下になるように、
    ソニック・コマンドを2つまで自分のマナゾーンから出す。
    次の自分のターンのはじめまで、それらに「ブロッカー」を与える"""
    p = s.P[i]
    s.ramp(i, 1)
    budget = 8
    for _ in range(2):
        best, bv = None, -1
        for k in sorted(set(p.mana)):
            c = BY_KEY[k]
            if not _plain_cre(c) or "soniccommand" not in c.races or c.cost > budget:
                continue
            if s.fate(i, k, "mana", False) != "ok":
                continue
            if E.PRI[k] > bv:
                best, bv = k, E.PRI[k]
        if best is None:
            return
        budget -= BY_KEY[best].cost
        s.take_mana(i, best)
        s.ev(f"　覇道の決闘：マナから {BY_KEY[best].name} を出す")
        u = s.enter(i, best, "mana", False)
        if u is None:
            return
        _grant_blocker(s, i, u, "覇道の決闘")


add("k42_hadou", "覇道の決闘", 6, "WFN", kind="S", trig=True, pri=7, roles="trg acc blk",
    spell=sp_hadou, chargex=_reveal_untap("soniccommand", "覇道の決闘"), blockok=bo_granted,
    text="S・トリガー。自分の山札の上から1枚目をマナゾーンに置く。その後、コストの合計が8以下になるように、"
         "ソニック・コマンドを2つまで自分のマナゾーンから出す。"
         "次の自分のターンのはじめまで、それらに「ブロッカー」を与える"
         "（マナからは重要度の高いソニック・コマンドを順に出す）。"
         "このカードを自分の手札からマナゾーンに置いた時、自分の手札にあるソニック・コマンド・カードを"
         "1枚、表向きにしてもよい。そうしたら、このカードをアンタップする"
         "（多色なのでマナゾーンにはタップして置かれる）",
    source=SRC["k42_hadou"])


# ================================================================ 一王二命三眼槍の封
def e_baradofu(s, i, u):
    """このタマシードが出た時、相手のクリーチャーを1体選び、破壊する"""
    t = s.target(i)
    if t is None:
        return
    destroy(s, i, t)


def aw_baradofu(s, i, u):
    """＜鬼エンド＞クリーチャーが攻撃する時、シールドが1つもないプレイヤーがいて、
    自分のマナゾーンに火・闇・自然文明があれば、手札からコストを支払わずに置いてもよい

    自分の攻撃でも相手の攻撃でも誘発するので、両方のプレイヤーの手札を見る。"""
    if u.c.kind != "C":
        return
    if s.P[0].sh and s.P[1].sh:
        return
    for j in (0, 1):
        p = s.P[j]
        if s.over or "k42_baradofu" not in p.hand or p.ban == 5:
            continue
        cv = set("".join(E.MCIV[k] for k in p.mana))
        if not {"D", "F", "N"} <= cv:
            continue
        p.hand.remove("k42_baradofu")
        s.ev("　鬼エンド：一王二命三眼槍の封をコストを支払わずに置く")
        s.place_tama(j, "k42_baradofu")


def lose_baradofu(s, i, how):
    """自分がゲームに負ける時、かわりにこのタマシードから進化できるコスト5以下のデモニオ・クリーチャーを
    1体、自分の手札からこの上に置いてもよい"""
    p = s.P[i]
    u = None
    for z in p.board:
        if z.k == "k42_baradofu":
            u = z
            break
    if u is None:
        return False
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "C" and c.evo and c.cost <= 5 and "demonio" in c.races and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is None:
        return False
    p.hand.remove(best)
    s.ev(f"　一王二命三眼槍の封：負けるかわりに {BY_KEY[best].name} をこの上に置く")
    s.enter(i, best, "hand", False, on=u)
    return True


E.SHINKA.add("k42_baradofu")

add("k42_baradofu", "一王二命三眼槍の封", 5, "DFN", kind="T", races=("demonio", "onirexstars"),
    pri=7, roles="rem fin",
    enter=e_baradofu, atkwatch=aw_baradofu, loserep=lose_baradofu,
    text="＜鬼エンド＞クリーチャーが攻撃する時、シールドが1つもないプレイヤーがいて、"
         "自分のマナゾーンに火、闇、自然文明があれば、このタマシードを自分の手札から"
         "コストを支払わずに出してもよい。"
         "シンカライズ（このタマシードがクリーチャーであるかのように、この上に進化クリーチャーを置いてもよい）。"
         "このタマシードが出た時、相手のクリーチャーを1体選び、破壊する。"
         "自分がゲームに負ける時、かわりにこのタマシードから進化できるコスト5以下の"
         "デモニオ・クリーチャーを1体、自分の手札からこの上に置いてもよい",
    source=SRC["k42_baradofu"])


# ================================================================ 孤高の決闘
def sp_kokou(s, i):
    """自分の手札を1枚捨てる。こうして捨てたカード以下のコストの相手のクリーチャーを1体選び、破壊する。
    コスト5以下の、タマシードとデモニオを最大1つずつ、自分のマナゾーンまたは墓地から出す"""
    p = s.P[i]
    if p.hand:
        need = _best_opp_cost(s, i)
        reach = [k for k in p.hand if BY_KEY[k].cost >= need]
        k = min(reach, key=E.PRI.get) if reach else min(p.hand, key=E.PRI.get)
        n = BY_KEY[k].cost
        s.discard(i, k)
        s.ev(f"　孤高の決闘：{BY_KEY[k].name}（コスト{n}）を捨てる")
        t = s.target(i, lambda z: z.c.cost <= n)
        if t is not None:
            destroy(s, i, t)
    # タマシード1つ
    best, bv, src = None, -1, None
    for zn, zone in (("grave", p.grave), ("mana", p.mana)):
        for kk in sorted(set(zone)):
            c = BY_KEY[kk]
            if c.kind == "T" and c.cost <= 5 and E.PRI[kk] > bv and p.ban != c.cost:
                best, bv, src = kk, E.PRI[kk], zn
    if best is not None:
        if src == "grave":
            p.grave.remove(best)
        else:
            s.take_mana(i, best)
        s.ev(f"　孤高の決闘：{'墓地' if src == 'grave' else 'マナ'}から {BY_KEY[best].name} を出す")
        s.place_tama(i, best)
    # デモニオ1体
    if s.revive(i, lambda c: c.cost <= 5 and "demonio" in c.races, "grave") is None:
        s.revive(i, lambda c: c.cost <= 5 and "demonio" in c.races, "mana")


add("k42_kokou", "孤高の決闘", 6, "DFN", kind="S", trig=True, pri=7, roles="trg rem atk",
    spell=sp_kokou, chargex=_reveal_untap("demonio", "孤高の決闘"),
    text="S・トリガー。自分の手札を1枚捨てる。こうして捨てたカード以下のコストの相手のクリーチャーを"
         "1体選び、破壊する（相手のいちばん値打ちのあるクリーチャーに届く中でいちばん安い札を捨てる）。"
         "コスト5以下の、タマシードとデモニオを最大1つずつ、自分のマナゾーンまたは墓地から出す",
    source=SRC["k42_kokou"])


# ================================================================ ドラゴンズ・サイン
def sp_dsign(s, i):
    """光のコスト7以下の、進化ではないドラゴン・クリーチャーを1体、自分の手札から出す。
    次の自分のターンのはじめまで、そのクリーチャーに「ブロッカー」を与える"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or c.evo or c.cost > 7 or "L" not in c.civ:
            continue
        if "dragon" not in c.races:
            continue
        if s.fate(i, k, "hand", False) != "ok":
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is None:
        return
    p.hand.remove(best)
    s.ev(f"　ドラゴンズ・サイン：手札から {BY_KEY[best].name} を出す")
    u = s.enter(i, best, "hand", False)
    if u is not None:
        _grant_blocker(s, i, u, "ドラゴンズ・サイン")


add("k42_dsign", "ドラゴンズ・サイン", 5, "L", kind="S", trig=True, pri=6, roles="trg blk atk",
    spell=sp_dsign, blockok=bo_granted,
    text="S・トリガー。光のコスト7以下の、進化ではないドラゴン・クリーチャーを1体、自分の手札から出す。"
         "次の自分のターンのはじめまで、そのクリーチャーに「ブロッカー」を与える"
         "（手札の中でいちばん重要度の高いものを出す）",
    source=SRC["k42_dsign"])


# ================================================================ シンクロ・ルピア／「D4に敗北は許されない！」
def e_synchro(s, i, u):
    """このクリーチャーが出た時、相手のクリーチャーを1体選び、持ち主の手札に戻してもよい"""
    t = s.target(i)
    if t is None:
        return
    move(s, i, t, "hand")


def _flip_one(s, i):
    """シールドを1つ見て、そこに含まれるカードを1枚、表向きまたは裏向きにする。

    このエンジンでシールドの表裏が効くのは次の3つ。得になる向きを順に探す。
      ・表向きのG城だけが城として働く　→ 相手の城は裏向きにすると止まる
      ・表向きのシールドはブレイクされてもS・トリガーで使えない　→ 相手の受け札は表向きにする
      ・表向きのシールドは先にブレイクされる　→ 自分の表向きのシールドは裏向きにする"""
    o, p = s.P[1 - i], s.P[i]
    for j, (k, up) in enumerate(o.sh):
        if up and BY_KEY[k].kind == "G":
            o.sh[j] = (k, False)
            return f"相手の {BY_KEY[k].name} を裏向きにする（城の効果が止まる）"
    best = None
    for j, (k, up) in enumerate(o.sh):
        c = BY_KEY[k]
        if up or _keep_face_down(k):
            continue
        if not (c.trig or c.gs or (c.twin and c.twin[2])):
            continue
        if best is None or E.PRI[k] > E.PRI[o.sh[best][0]]:
            best = j
    if best is not None:
        k = o.sh[best][0]
        o.sh[best] = (k, True)
        return f"相手の {BY_KEY[k].name} を表向きにする（S・トリガーで使えなくなる）"
    for j, (k, up) in enumerate(p.sh):
        if up and BY_KEY[k].kind != "G":
            p.sh[j] = (k, False)
            return f"自分の {BY_KEY[k].name} を裏向きにする（先に割られないように）"
    return None


def sp_synchro(s, i):
    msg = _flip_one(s, i)
    if msg is not None:
        s.ev(f"　D4に敗北は許されない！：{msg}")
    s.draw(i, 2)


add("k42_synchro", "シンクロ・ルピア／「D4に敗北は許されない！」", 5, "W", power=4000, trig=True,
    races=("armoreddragon", "dragon", "firebird", "snowfu"), twin=(3, "W", False),
    pri=6, roles="trg rem draw dis",
    enter=e_synchro, spell=sp_synchro,
    text="【クリーチャー側】S・トリガー。出た時、相手のクリーチャーを1体選び、持ち主の手札に戻してもよい。"
         "【呪文側《「D4に敗北は許されない！」》コスト3・水】シールドを1つ見る。"
         "そのシールドに含まれるカードを1枚、表向きまたは裏向きにしてもよい。その後、カードを2枚引く"
         "（相手の表向きのG城を裏向きにする→相手の裏向きの受け札を表向きにする→"
         "自分の表向きのシールドを裏向きにする、の順で得になる向きを選ぶ）",
    source=SRC["k42_synchro"])


# ================================================================ 極限龍神ヘヴィ
def e_heavy(s, i, u):
    """出た時、自分のクリーチャーを1体破壊してもよい。そうしたら、カードを1枚引き、
    その後、相手は自身のクリーチャーを1体選んで破壊する"""
    z = worst_own(s, i, pred=lambda x: x is not u)
    if z is None:
        return                                        # 自分自身を破壊するだけになるなら使わない
    o = worst_own(s, 1 - i)
    if o is None:
        return                                        # 相手が何も失わないなら、自分だけ損をしない
    if own_loss(s, i, z) > own_loss(s, 1 - i, o) + 2:
        return                                        # 損な取引はしない
    s.ev(f"　極限龍神ヘヴィ：自分の {z.c.name} を破壊")
    s.leave(i, z, "grave", destroy=True)
    s.draw(i)
    o2 = worst_own(s, 1 - i)
    if o2 is not None:
        s.ev(f"　極限龍神ヘヴィ：相手は自身の {o2.c.name} を破壊")
        s.leave(1 - i, o2, "grave", destroy=True)


def _heavy_force(s, i, u):
    """i（攻める側）のクリーチャー u が、いま相手のリンクした極限龍神ヘヴィを攻撃できるなら、それを返す

    「可能なら」は、ヘヴィ側がタップしているか、u がマッハファイターとして攻撃できるかで決める
    （パワーの大小は見ない）。リンクしていない間は働かない能力なので、頭のリンクも確かめる。"""
    mf = None
    for z in s.P[1 - i].board:
        if z.c.kind != "C" or z.jd or not z.link:
            continue
        if not any(x.k == "k42_heavy" for x in s.parts(z)) or not s.abi(1 - i, z):
            continue
        if not z.tap:
            if mf is None:
                mf = _mf(s, i, u)
            if not mf:
                continue
        return z
    return None


def mt_heavy(s, i, u, tg):
    """リンクしていれば、相手のクリーチャーは可能ならこのクリーチャーを攻撃しなければならない"""
    z = _heavy_force(s, i, u)
    if z is None:
        return None
    o = s.P[1 - i]
    for j in tg:
        if j != "P" and o.board[j] is z:
            return j
    return None


def atl_heavy(s, i, u, t):
    """同じ能力の続き：リンクしたヘヴィのパワーが高くて攻撃先に選べない時は、
    ほかのクリーチャーへの攻撃を止める（エンジンは自分より強いクリーチャーへの攻撃を手に出さないので、
    「攻撃しなければならない」を『ほかを攻撃できない』の形で表す）"""
    z = _heavy_force(s, i, u)
    return z is not None and t is not z and s.power(1 - i, z) > s.power(i, u, True)


def nap_heavy(s, i, u):
    """同じく、プレイヤーへの攻撃も止める"""
    z = _heavy_force(s, i, u)
    return z is not None and s.power(1 - i, z) > s.power(i, u, True)


add("k42_heavy", "極限龍神ヘヴィ", 4, "D", power=5000, races=("god", "godnova", "dragonzombie", "dragon"),
    pri=5, roles="rem draw blk",
    enter=e_heavy, godlink=("L", ()),
    mustatktgt=mt_heavy, atktargetlock=atl_heavy, noatkplock=nap_heavy,
    freeacts=_gl_acts, actapply={_GL_ACT: _gl_apply},
    text="このクリーチャーが出た時、自分のクリーチャーを1体破壊してもよい。そうしたら、カードを1枚引き、"
         "その後、相手は自身のクリーチャーを1体選んで破壊する"
         "（自分はこのクリーチャー以外でいちばん失って痛くないものを破壊し、"
         "相手が失うものより損な時や、自分にほかのクリーチャーがいない時は使わない）。"
         "左G・リンクOMG（《龍神メタル》《破壊神デス》や、「中央G・リンク」「右G・リンク」を持つ"
         "ゴッドの左側にリンクしてもよい。リンクしたゴッドはパワーを合計した1体のクリーチャーになり、"
         "能力と文明を併せ持ち、離れる時はそのうち1枚だけが離れる）。"
         "リンクしていれば、相手のクリーチャーは可能ならこのクリーチャーを攻撃しなければならない"
         "（つなぐのは自分のメインステップ中の追加の手として行う）",
    note="エンジンは「パワーで負ける相手のクリーチャーへの攻撃」を手の一覧の段階で外している。"
         "そのため、リンクしたヘヴィより弱い相手のクリーチャーは、本物のカードのように"
         "『攻撃させられて返り討ちになる』のではなく、そのターン攻撃できないという形になる"
         "（守る力はほぼ同じだが、相手のクリーチャーは死なない）",
    status="partial", source=SRC["k42_heavy"])


# ================================================================ カンゴク入道の巻
def ts_kangoku(s, i, u):
    """自分のターンのはじめに、自分のシールドを1つ手札に加える。その「S・トリガー」は使えない"""
    _take_best_shield(s, i, "カンゴク入道の巻")


E.SHINKA.add("k42_kangoku")

add("k42_kangoku", "カンゴク入道の巻", 2, "D", kind="T", races=("demonio", "onirexstars"),
    pri=3, roles="draw",
    tstart=ts_kangoku,
    text="シンカライズ（このタマシードがクリーチャーであるかのように、この上に進化クリーチャーを置いてもよい）。"
         "自分のターンのはじめに、自分のシールドを1つ手札に加える。その「S・トリガー」は使えない"
         "（重要度のいちばん高いシールドを選ぶ。表向きのG城は、離れると墓地に行ってしまうので選ばない）",
    source=SRC["k42_kangoku"])


# ================================================================ プライマル・サーガ
def sp_primal(s, i):
    """自分の山札の上から4枚を墓地に置く。その後、コスト5以下のゴッドを1つ、自分の墓地から出す"""
    s.mill(i, 4)
    s.revive(i, lambda c: _is_god(c) and c.cost <= 5, "grave")


add("k42_primal", "プライマル・サーガ", 4, "D", kind="S", trig=True, pri=5, roles="trg atk",
    spell=sp_primal,
    text="S・トリガー。自分の山札の上から4枚を墓地に置く。"
         "その後、コスト5以下のゴッドを1つ、自分の墓地から出す",
    source=SRC["k42_primal"])


# ================================================================ 轟速 ザ・リフル
def sa_rifle(s, i, u):
    """超魂X：このカードがクリーチャーの下にあれば、そのクリーチャーにもスピードアタッカーを与える"""
    return "k42_rifle" in u.under


def nogs_rifle(s, i, u):
    """超魂X：下にこのカードがあるクリーチャーの攻撃中も、相手は「G・ストライク」を使えない"""
    return "k42_rifle" in u.under


E.NOGS.add("k42_rifle")

add("k42_rifle", "轟速 ザ・リフル", 4, "F", power=4000, sa=True,
    races=("soniccommand", "command", "invader", "fusioner"), pri=5, roles="atk",
    saok=sa_rifle, nogsx=nogs_rifle,
    text="スピードアタッカー。このクリーチャーの攻撃中、相手は「G・ストライク」を使えない。"
         "超魂X（このカードがクリーチャーの下にあれば、そのクリーチャーにも上の能力を与える。"
         "スピードアタッカーも、攻撃中に相手のG・ストライクを使えなくする分も与える）",
    source=SRC["k42_rifle"])


# ================================================================ 「オレたちのZEROの世界を造るまで」
def ew_zero(s, i, u):
    """侵略ZEROの前半：相手がコストを支払わずにクリーチャーを出したターンを書き留める

    全体に効く差し込み口なので、相手がこの呪文を持っているデッキの時だけ書き留める。"""
    if u.c.kind != "C" or u.x.get("summoned"):
        return
    o = s.P[1 - i]
    if "k42_zeroworld" not in (o.list or {}) and "k42_zeroworld" not in o.hand:
        return
    s.P[i].x["k42_zero"] = s.turn


def tp_zero(s, j):
    """侵略ZERO：相手のターンの終わりに、そのターン、相手のクリーチャーがコストを支払わずに出ていたら、
    この呪文を自分の手札からコストを支払わずに唱えてもよい"""
    if s.over or s.tp == j:
        return
    p = s.P[j]
    if "k42_zeroworld" not in p.hand:
        return
    if s.P[1 - j].x.get("k42_zero") != s.turn:
        return
    if not s.spell_ok(j, 6):
        return
    p.hand.remove("k42_zeroworld")
    s.ev("　侵略ZERO：「オレたちのZEROの世界を造るまで」をコストを支払わずに唱える")
    s.cast(j, "k42_zeroworld")


def sp_zeroworld(s, i):
    """相手のパワー5000以下のクリーチャーをすべて破壊する"""
    o = s.P[1 - i]
    n = 0
    for z in o.board[:]:
        if z.c.kind != "C" or z not in o.board:
            continue
        if s.power(1 - i, z) <= 5000:
            if s.leave(1 - i, z, "grave", by_opp=True, destroy=True):
                n += 1
    s.ev(f"　オレたちのZEROの世界を造るまで：相手のパワー5000以下を{n}体破壊")


add("k42_zeroworld", "「オレたちのZEROの世界を造るまで」", 6, "F", kind="S", pri=7, roles="rem dis",
    spell=sp_zeroworld, enterwatch=ew_zero, tendp=tp_zero,
    text="侵略ZERO：相手のターンの終わりに、そのターン、相手のクリーチャーがコストを支払わずに出ていたら、"
         "この呪文を自分の手札からコストを支払わずに唱えてもよい。"
         "相手のパワー5000以下のクリーチャーをすべて破壊する",
    source=SRC["k42_zeroworld"])


# ================================================================ 希望の太陽 マイハマタワー
def _maihama_up(s, i):
    """このG城が、表向きで自分のシールドゾーンにあるか"""
    for k, up in s.P[i].sh:
        if up and k == "k42_maihama":
            return True
    return False


def bo_maihama(s, u):
    """自分のアーマードすべてに「ブロッカー」を与える"""
    if not _is_armored(u.c):
        return False
    return _maihama_up(s, owner_of(s, u))


def sa_maihama(s, i, u):
    """自分のアーマードすべてに「スピードアタッカー」を与える"""
    return _is_armored(u.c) and _maihama_up(s, i)


def tp_maihama(s, j):
    """各ターンの終わりに、自分のアーマードをすべてアンタップする"""
    if s.over or not _maihama_up(s, j):
        return
    n = 0
    for u in s.P[j].board:
        if _is_armored(u.c) and u.tap:
            u.tap = False
            n += 1
    if n:
        s.ev(f"　希望の太陽 マイハマタワー：自分のアーマード{n}体をアンタップ")


def so_maihama(s, i, k, up, dest):
    """このG城が表向きで自分のシールドゾーンを離れた時、自分の山札の上から1枚を表向きでシールド化する"""
    if k != "k42_maihama" or not up:
        return
    if s.add_shield(i, None, True):
        s.ev("　希望の太陽 マイハマタワー：山札の上から1枚を表向きでシールド化")


add("k42_maihama", "希望の太陽 マイハマタワー", 2, "LF", kind="G", pri=4, roles="blk atk shd",
    blockok=bo_maihama, saok=sa_maihama, tendp=tp_maihama, shieldout=so_maihama,
    text="G城（実行したら表向きでシールド化される。このカードが表向きで自分のシールドゾーンを離れる時、"
         "かわりに墓地に置く）。"
         "自分のアーマードすべてに「ブロッカー」と「スピードアタッカー」を与える。"
         "各ターンの終わりに、自分のアーマードをすべてアンタップする。"
         "このG城が表向きで自分のシールドゾーンを離れた時、自分の山札の上から1枚を表向きでシールド化する",
    source=SRC["k42_maihama"])


# ================================================================ 一王伝双三眼槍
def cx_baradodouble(s, i, av):
    """このクリーチャーを[闇/火(3)]を支払って召喚してもよい（そうしたらシールドを2つ手札に加える）

    シールドを手札に加えるのは、このシミュレーターでは「盾を2枚失う」という重い代償なので、
    コスト5を払えない時か、失う盾がほとんど無い時だけ別コストを使う。"""
    return 3 if (av < 5 or len(s.P[i].sh) <= 1) else 5


def px_baradodouble(s, i, k, n):
    """別コストで召喚したなら、自分のシールドを2つ手札に加える（S・トリガーは使えない）"""
    if n >= 5:
        return
    for _ in range(2):
        if _take_best_shield(s, i, "一王伝双三眼槍") is None:
            return


def lose_baradodouble(s, i, how):
    """＜鬼タイム＞自分がゲームに負ける時、自分と相手のシールドの数が合計6つ以下なら、
    かわりにこのクリーチャーを破壊してもよい"""
    if len(s.P[0].sh) + len(s.P[1].sh) > 6:
        return False
    p = s.P[i]
    u = None
    for z in p.board:
        if z.k == "k42_baradodouble":
            u = z
            break
    if u is None:
        return False
    s.ev("　＜鬼タイム＞一王伝双三眼槍を破壊して、負けるのを置き換える")
    s.leave(i, u, "grave", destroy=True)
    return True


add("k42_baradodouble", "一王伝双三眼槍", 5, "DF", power=6000, brk=2,
    races=("demonio", "onifuda"), pri=7, roles="atk draw fin",
    costx=cx_baradodouble, payx=px_baradodouble, loserep=lose_baradodouble,
    text="このクリーチャーを[闇/火(3)]を支払って召喚してもよい。そうしたら、自分のシールドを2つ"
         "手札に加える。ただし、その「S・トリガー」は使えない。W・ブレイカー。"
         "＜鬼タイム＞自分がゲームに負ける時、自分と相手のシールドの数が合計6つ以下なら、"
         "かわりにこのクリーチャーを破壊してもよい",
    note="別コスト[闇/火(3)]を使うかどうかは、このシミュレーター共通の決まりで機械的に決めている"
         "（コスト5を払えない時か、自分のシールドが1枚以下で失うものがほとんど無い時だけ3マナで召喚する）。"
         "能力自体はどちらのコストでも全部実装してある。",
    source=SRC["k42_baradodouble"])
