"""担当41：DM26-EX2「悪感謝祭 カリスマBEST」の15枚（key は k41_）

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ（https://dmwiki.net/《カード名》）と
      生の wiki ソース（?plugin=template&refer=《カード名》）を別の質問で2回ずつ読み（数字や
      一文の末尾が読めなかった6枚は3回）、コスト・文明・種類・種族・パワー・ブレイク数・
      能力本文が一致することを確かめた。

  この札束に入っている仕組み
    ・**超魂X**（魔誕の悪魔デスモナーク／怒像アゲ）。「これがクリーチャーの下にあれば、そのクリーチャーにも
      以下の能力を与える」。下に潜った状態でも働くので、`atkwatch=`／`loserep=` の中で
      「自分のキーか、自分のキーが u.under にあるか」を見ている。
    ・**パワード・ブレイカー**（デスアポロヌス・ドラゲリオン／ジャオウガ-8／メタル・アポロヌス／
      デス・フェニックス）。dmwiki のキーワードページで確かめたとおり **パワー6000ごとに1枚増える**
      （ブレイク数＝パワー÷6000の小数切り捨て＋1）。`brkx=` で書いた。
    ・**G・リンク**（デスアポロヌス・ドラゲリオン＝中央／エンドレス＝左／メタル・アポロヌス＝右）。
      エンジンの `godlink=` で入れた。つなぐのは追加の手（`x:k41link`。召喚してからリンクする）と、
      S・トリガーや墓地から出た時の `ew_link41`。中央は左か右、左は中央か右、右は中央か左にだけ
      つながり、同じ位置は2枚つなげない。env43 のゴッド（邪眼神オールなど）とも混ざってつながる。
      デス・フェニックスの**トライ・G・リンク**だけは《龍神ヘヴィ》《龍神メタル》限定で、
      その2枚がカードプールに無いので入れていない。
    ・**墓地進化／墓地進化V**（デスアポロヌス・ドラゲリオン／デス・フェニックス）。`evosrc=` で1枚、
      2枚目は `enter=` の中で墓地から下に積む（エンジンの `evosrc` は1枚しか返せない）。
    ・**シンパシー：ゴッド**（デスアポロヌス・ドラゲリオン）＝`costx=`。
    ・**S・バック**（ゲドウ大権現＝闇または火／ジャオウガ-8＝デモニオ）。シールドから手札に加わる1枚を
      捨てて、手札からただで召喚する。ゲドウ大権現は `shieldrep=` で書いたので、ブレイクでも効果でも
      （シールドゾーンの出口はどこでも）誘発する。ジャオウガ-8 はブレイク分だけの `breakrep=` のまま。
    ・**＜鬼エンド＞**（ゲドウ大権現）。シールドが0のプレイヤーがいる間だけブロッカーとスレイヤー。
      スレイヤーは条件つきなので `SLAYER` 集合ではなく `battlefx=` で書いた。
    ・**スター進化＋Zラッシュ＋ハイパーモード**（ジャオウガ-8）。
    ・**召喚時にシールドを選んでコストを下げ、出た時にそれを手札に加える**（グレイテスト・ジャオウガ）。
      `costx=` と `payx=` と `enter=` の3つで組んだ。
    ・**S革命チェンジ：アーマード**（ボルシャック・カクメイジン）＝`changezone=("hand", "shield")` で
      表向きのシールドからも入れ替えられる。**革命チェンジ**（ボルテール・ミラー・ドラゴン）。
    ・**表向きのシールドを参照するコスト軽減**（ゴルギーニ＝-3／ゴルファンタジスタ＝-2）。
    ・**チャージャー**（ミラー・チャージャー）＝`nograve=True` ＋ 呪文の最後で `s.add_mana`。
    ・**「1体をもう1体の下に置く」**（邪眼左神エンドレス）。相手のいちばん大事なクリーチャーを
      いちばん安いクリーチャーの下に押し込む、実質の除去になる。

  調べ直して意外だった点
    ・《ボルシャック・カクメイジン》と《ボルシャック・ゴルギーニ》は、名前から想像する単色の火ではなく
      **光/水/火の3色**で、種族も「マジック・アーマード・ドラゴン／ゲーム・コマンド」
      「メカ・アーマード・ドラゴン」という新しい複合種族だった（カードページと生ソースで2回確認）。
    ・《暗黒破壊神デス・フェニックス》は**コスト4**。墓地から闇または火のクリーチャー2体を使う
      「墓地進化V」なので、この軽さで成立する。
    ・パワード・ブレイカーは5000ごとではなく**6000ごと**。エンジンの `derbande` と同じ式だった。
    ・《「鬼情」の極 ジャオウグリラ》は単体名のページが無く、**ツインパクト**
      《「鬼情」の極 ジャオウグリラ／「自由で欲望のままに生きるのだ！」》でしかページが開けなかった。
    ・《禁鬼機関 ジャオウガ-8》のハイパーモードの一文は、カード本文の語として
      「デモニオ・カードを自分の墓地から**実行**してもよい」と書かれている（「コストを支払わずに」は無い）。
      3回読んでも同じだったので、コストを支払って墓地から使う能力として実装した（note に書いた）。
    ・《ボルテール・ミラー・ドラゴン》と《ミラー・チャージャー》の「自分のシールド1つの上に置く」は
      シールド・プラス（束ねて1つのシールドとして扱う＝シールドの数は増えない）。
      このシミュレーターに束ねたシールドが無いので、**シールドの枚数を変えずに自分のシールド1つを
      表向きにする**形で近似した（`s.flip_shield`。以前は表向きのシールドを1つ増やしていて、
      シールドの枚数＝残り体力がずれていた）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, opp_all, worst_hand
from envcards.env0 import race_like, star_evo_rep

W = "https://dmwiki.net/"
SRC = {
    "k41_desmonarch": W + "《魔誕の悪魔デスモナーク》",
    "k41_deathapollonus": W + "《邪眼破壊神デスアポロヌス・ドラゲリオン》",
    "k41_gedou": W + "《「涅槃」の鬼 ゲドウ大権現》",
    "k41_jaouga8": W + "《禁鬼機関 ジャオウガ-8》",
    "k41_gorgini": W + "《ボルシャック・ゴルギーニ》",
    "k41_kakumeijin": W + "《ボルシャック・カクメイジン》",
    "k41_greatest": W + "《鬼黒皇グレイテスト・ジャオウガ》",
    "k41_parfait": W + "《パルフェ・ルピア／「あとはたのんだぞ」》",
    "k41_endless": W + "《邪眼左神エンドレス》",
    "k41_dozouage": W + "《怒像アゲ》",
    "k41_metalapollonus": W + "《邪眼龍神メタル・アポロヌス》",
    "k41_voltaire": W + "《ボルテール・ミラー・ドラゴン／ミラー・チャージャー》",
    "k41_golfantasista": W + "《ボルシャック・ゴルファンタジスタ》",
    "k41_jaougurira": W + "《「鬼情」の極 ジャオウグリラ／「自由で欲望のままに生きるのだ！」》",
    "k41_deathphoenix": W + "《暗黒破壊神デス・フェニックス》",
}


# ================================================================ 共通の道具
def _top(s, i, n):
    """山札の上から n 枚を取り出す（山札は1枚残す。エンジン共通の決まり）"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    return [p.deck.pop() for _ in range(n)] if n > 0 else []


def _bottom(s, i, ks):
    for k in ks:
        s.P[i].deck.insert(0, k)


def _unit(s, i, u):
    """u を含むクリーチャー（G・リンクしているなら、その先頭のカード）。
    リンクしたゴッドは1体のクリーチャーなので、パワーを見る時はこちらを使う"""
    for z in s.P[i].board:
        if z is u:
            return z
        for x in z.link:
            if x is u:
                return z
    return u


def _powered_brk(s, i, u):
    """パワード・ブレイカー：パワー6000ごとにブレイクするシールドが1枚増える
    （G・リンクしていれば、合計パワーで数える）"""
    return 1 + s.power(i, _unit(s, i, u), True) // 6000


def _plain_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _faceup(s, i):
    """自分のシールドゾーンに表向きのカードがあるか"""
    return any(up for _k, up in s.P[i].sh)


def _worst_shield(s, i):
    """自分のシールドのうち、失っていちばん痛くないもの（裏向きを先に、重要度の低いものから）"""
    p = s.P[i]
    if not p.sh:
        return None
    return min(range(len(p.sh)), key=lambda j: (p.sh[j][1], E.PRI[p.sh[j][0]]))


def _best_shield(s, i):
    """自分のシールドのうち、手札に加えていちばん得なもの（重要度の高い裏向きから）"""
    p = s.P[i]
    if not p.sh:
        return None
    return max(range(len(p.sh)), key=lambda j: (not p.sh[j][1], E.PRI[p.sh[j][0]]))


def _df_cre(c):
    return c.kind == "C" and bool(set("DF") & set(c.civ))


def _pr_cre(msg, pred, n=4):
    """「出せるデッキか」：進化元になれるクリーチャーが n 体以上いるか"""
    def f(deck, k):
        c = 0
        for kk, v in deck.items():
            if kk == k:
                continue
            cc = BY_KEY[kk]
            if (cc.kind == "C" or kk in E.SHINKA) and pred(cc):
                c += v
        return None if c >= n else msg
    return f


def _revive_element(s, i, pred):
    """自分の墓地から、条件に合うエレメント（進化でないクリーチャー1体かタマシード1つ）を出す"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if not pred(c) or E.PRI[k] <= bv:
            continue
        if c.kind == "C":
            if not _plain_cre(c) or s.fate(i, k, "grave", False) != "ok":
                continue
        elif c.kind == "T":
            if p.ban == c.cost:
                continue
        else:
            continue
        best, bv = k, E.PRI[k]
    if best is None:
        return None
    c = BY_KEY[best]
    p.grave.remove(best)
    s.ev(f"　墓地から {c.name}")
    if c.kind == "C":
        return s.enter(i, best, "grave", False)
    s.place_tama(i, best)
    return best


def _sink(s, j, base, sunk):
    """プレイヤー j のクリーチャー sunk を base の下に置く（sunk はバトルゾーンのクリーチャーでなくなる）"""
    p = s.P[j]
    if base is sunk or base not in p.board or sunk not in p.board:
        return False
    p.board.remove(sunk)
    base.under = [sunk.k] + sunk.under + base.under
    s.ev(f"　{sunk.c.name} を {base.c.name} の下に置いた")
    return True


# ================================================================ G・リンク（ゴッドの合体）
_RYUJIN = ("龍神ヘヴィ", "龍神メタル")

# 位置は左（"L"）・中央（"C"）・右（"R"）の3つ。「中央G・リンク」は左か右を持つゴッドに、
# 「左G・リンク」は中央か右に、「右G・リンク」は中央か左につながる（公式の決まり）。
# 左と右は中央が無くても直につながるので、1体のクリーチャーに同じ位置が2つ無ければよい。

GODS41 = ("k41_deathapollonus", "k41_endless", "k41_metalapollonus")   # このモジュールのG・リンク持ち


def _link_pos(s, u):
    """u を構成しているゴッドの (キー, 位置) の並び。ゴッドでないカードが混じっていれば None

    G・リンクしたゴッドは1体のクリーチャーなので、u 自身がすでにリンクしていることもある。"""
    if u.c.kind != "C":
        return None
    out = []
    for z in s.parts(u):
        h = E.GODLINK.get(z.k)
        if h is None:
            return None
        out.append((z.k, h[0]))
    return out


def _link_join_ok(s, ups, base):
    """(キー, 位置) の並び ups を base につなげるか。

    左・中央・右はそれぞれ1枚までで、同じカードは2枚つなげない（engine3 の can_link は
    「相手のキーの組」しか見ないので、位置の決まりはここで見る）。
    左と右は中央が無くても直につながるので、位置が重なっていなければつなげる。"""
    bps = _link_pos(s, base)
    if not bps or not ups:
        return False
    ks = {k for k, _ in bps}
    ps = {x for _, x in bps}
    for k, x in ups:
        if k in ks or x in ps:
            return False
        ks.add(k)
        ps.add(x)
    return True


def _link_ok(s, i, k, base):
    """手札や墓地のゴッド k（1枚）を、バトルゾーンの base にG・リンクできるか"""
    g = E.GODLINK.get(k)
    if g is None:
        return False
    return _link_join_ok(s, [(k, g[0])], base)


def _do_link(s, i, u, base):
    """u を base の横につなぐ。u にすでに別のゴッドがつながっていれば、それも base に移す
    （engine3 の parts は1段しか見ないので、入れ子にすると下のゴッドが消える）"""
    p = s.P[i]
    extra = list(u.link)
    u.link = []
    if u in p.board:
        p.board.remove(u)
    s.god_link(i, u, base)
    for z in extra:
        s.god_link(i, z, base)


def _link_base(s, i, k):
    """k をつなぐ相手として、いちばん大きくなるクリーチャーを選ぶ（全デッキ共通の決まり）"""
    cands = [b for b in s.P[i].board if _link_ok(s, i, k, b)]
    if not cands:
        return None
    return max(cands, key=lambda b: (len(s.parts(b)), E.PRI[b.k]))


def _link_mode(s, i, k, av, cv):
    """このゴッドをいま手札から召喚できるか（legal_main と同じ条件）。play に渡す mode か None"""
    c = BY_KEY[k]
    n = s.ccost(i, k, av)
    if n > av or (n > 0 and not cv.issuperset(c.civ)):
        return None
    if s.fate(i, k, "hand", True) != "ok":
        return None
    ez = E.EVOSRC.get(k)
    if ez is not None:
        return 1 if ez(s, i) is not None else None
    if not c.evo:
        return 0
    if s.evo_src(i, k) is not None:
        return 1
    return 0 if c.neo else None


def fa_link41(s, i, av, cv):
    """追加の手「召喚してG・リンクする」（リンクせずに1体で出す手は、もとからある「召喚」のまま）"""
    p = s.P[i]
    out = []
    for k in GODS41:
        if k not in p.hand:
            continue
        mode = _link_mode(s, i, k, av, cv)
        if mode is None:
            continue
        for j, b in enumerate(p.board):
            if _link_ok(s, i, k, b):
                out.append(("x:k41link", k, j, mode))
    return out


def ap_link41(s, a):
    """召喚してから、出たゴッドを base の横につなぐ"""
    i = s.tp
    p = s.P[i]
    k, j, mode = a[1], a[2], a[3]
    if k not in p.hand or not (0 <= j < len(p.board)):
        return
    base = p.board[j]
    before = list(p.board)
    s.play(i, k, mode)
    if base not in p.board:
        return
    u = next((z for z in p.board if z.k == k and all(z is not y for y in before)), None)
    if u is None or u is base:
        return
    ups = _link_pos(s, u)
    if ups is not None and _link_join_ok(s, ups, base) and s.can_link(i, u, base):
        _do_link(s, i, u, base)


def ew_link41(s, i, u):
    """G・リンク：召喚以外（S・トリガーや墓地から出た分）で出たゴッドは、その場でつなぐ

    自分の手札からの召喚は fa_link41 の追加の手で選べるので、ここでは拾わない（二重につながないため）。"""
    if u.k not in GODS41:
        return
    if s.tp == i and u.x.get("src") == "hand":
        return
    p = s.P[i]
    if u not in p.board:
        return
    b = _link_base(s, i, u.k)
    if b is None or b is u or not s.can_link(i, u, b):
        return
    _do_link(s, i, u, b)


def _linked_names(s, u):
    """このクリーチャーを構成しているカードの名前の集合（リンクしているゴッドを調べるのに使う）"""
    return {z.c.name for z in s.parts(u)}


# ================================================================ 魔誕の悪魔デスモナーク
def e_desmonarch(s, i, u):
    """出た時、山札の上から4枚を見て、NEOクリーチャーか進化クリーチャー1体を手札に加えてもよい"""
    p = s.P[i]
    top = _top(s, i, 4)
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.kind == "C" and (c.neo or c.evo) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        p.hand.append(best)
        s.ev(f"　デスモナーク：{BY_KEY[best].name} を手札に加えた")
    _bottom(s, i, top)


def aw_desmonarch(s, i, u):
    """超魂X：各ターン、このクリーチャーの最初の攻撃の終わりにアンタップする
    （下に潜っている時は、上のクリーチャーにもこの能力を与える）"""
    if u.k != "k41_desmonarch" and "k41_desmonarch" not in u.under:
        return
    if u.x.get("k41_dm") == s.turn:
        return
    u.x["k41_dm"] = s.turn
    u.re = True               # エンジンが攻撃の終わりにアンタップする


add("k41_desmonarch", "魔誕の悪魔デスモナーク", 3, "F", power=3000,
    races=("demoncommand", "command", "fusioner"), pri=5, roles="draw atk",
    enter=e_desmonarch, atkwatch=aw_desmonarch,
    text="出た時、自分の山札の上から4枚を見る。その中からNEOクリーチャーまたは進化クリーチャーを1体、"
         "手札に加えてもよい（重要度のいちばん高いものを選ぶ）。残りを山札の下に置く。"
         "超魂X（このカードがクリーチャーの下にあれば、そのクリーチャーにも次の能力を与える）："
         "各ターン、このクリーチャーの最初の攻撃の終わりに、このクリーチャーをアンタップする",
    source=SRC["k41_desmonarch"])


# ================================================================ 邪眼破壊神デスアポロヌス・ドラゲリオン
def _is_god41(c):
    """ゴッドかどうか（ゴッド・ガルド／ゴッド・ノヴァOMG なども数える）"""
    return any(r.startswith("god") for r in c.races)


def _gods_in_grave(s, i):
    return sum(1 for k in s.P[i].grave if _is_god41(BY_KEY[k]))


def cx_deathapollonus(s, i, av):
    """シンパシー：自分の墓地にあるゴッド・カード1枚につきコスト-1（1より小さくならない）"""
    return max(1, 13 - _gods_in_grave(s, i))


def es_deathapollonus(s, i):
    """墓地進化：自分の墓地にある闇または火のクリーチャー1体の上に重ねる"""
    cs = [k for k in s.P[i].grave if _df_cre(BY_KEY[k])]
    if not cs:
        return None
    return ("grave", min(cs, key=E.PRI.get))


def e_deathapollonus(s, i, u):
    """出た時、コスト7以下のゴッドを2つまで、自分の墓地から出す。
    そのあと、《龍神ヘヴィ》と《龍神メタル》の両方とG・リンクしていれば、相手のクリーチャーをすべて破壊する

    進化元にする1枚（エンジンが「出た時」のあとで下に積む）は、ここで墓地から取り置いておく。
    そうしないと、この効果が進化元のゴッドを先に出してしまい、下に何も積まれなくなる。"""
    p = s.P[i]
    res = es_deathapollonus(s, i)
    keep = res[1] if res is not None and res[1] in p.grave else None
    if keep is not None:
        p.grave.remove(keep)
    try:
        for _ in range(2):
            if s.over:
                return
            if _revive_element(s, i, lambda c: c.cost <= 7 and _is_god41(c)) is None:
                break
    finally:
        if keep is not None:
            p.grave.append(keep)
    if s.over or u not in p.board:
        return
    if set(_RYUJIN) <= _linked_names(s, u):
        s.ev("　デスアポロヌス：《龍神ヘヴィ》と《龍神メタル》とリンクしているので相手を全滅")
        for z in opp_all(s, i):
            destroy(s, i, z)


add("k41_deathapollonus", "邪眼破壊神デスアポロヌス・ドラゲリオン", 13, "DF", power=13000, brk=3, gs=True,
    evo="DF", races=("godgard", "god", "tyranodrake"), pri=13, roles="fin rem trg acc",
    enter=e_deathapollonus, costx=cx_deathapollonus, evosrc=es_deathapollonus,
    brkx=_powered_brk, godlink=("C", ()),
    freeacts=fa_link41, actapply={"x:k41link": ap_link41}, enterwatch=ew_link41,
    playrule=_pr_cre("墓地進化の元になる闇か火のクリーチャーが4体いない", lambda c: bool(set("DF") & set(c.civ))),
    text="G・ストライク。シンパシー：自分の墓地にあるゴッド・カード（1枚につき召喚コストを1少なくする。"
         "1より小さくはならない）。墓地進化：自分の墓地にある、闇または火のクリーチャー1体の上に重ねつつ出す。"
         "パワード・ブレイカー（パワー6000ごとにブレイクするシールドが1枚増える）。"
         "中央G・リンク（これまたは自分の他のゴッドが出る時、「右G・リンク」または「左G・リンク」を"
         "持つゴッドにリンクしてもよい。リンクしたゴッドはパワーも能力も併せ持つ1体のクリーチャーになる）。"
         "出た時、コスト7以下のゴッドを2つまで、自分の墓地から出す。"
         "そのあと、このクリーチャーが《龍神ヘヴィ》と《龍神メタル》の両方とリンクしていれば、"
         "相手のクリーチャーをすべて破壊する",
    note="墓地から出すゴッドは重要度の高いものから選ぶ。"
         "「《龍神ヘヴィ》と《龍神メタル》とリンクしていれば相手を全滅」は名前で見る形で入れてあるが、"
         "その2枚はこのカードプールに無いので実際には働かない",
    status="full", source=SRC["k41_deathapollonus"])


# ================================================================ 「涅槃」の鬼 ゲドウ大権現
def _oni_end(s):
    """＜鬼エンド＞：シールドが1つもないプレイヤーがいるか"""
    return not s.P[0].sh or not s.P[1].sh


def rep_gedou(s, i, k, up, dest):
    """S・バック：闇または火

    闇または火のカードが自分のシールドゾーンから手札に加わる時、そのカードを捨てて、
    手札のこのクリーチャーをコストを支払わずに召喚してもよい（捨てるので行き先を墓地に変える）。
    捨てるのは「そのカード」なので、ゲドウ大権現より重要度の低い札の時だけ使う。"""
    if dest != "hand" or s.over:
        return None
    d = s.P[i]
    if "k41_gedou" not in d.hand:
        return None
    if not (set("DF") & set(E.MCIV[k])):
        return None
    if E.PRI["k41_gedou"] <= E.PRI[k]:
        return None
    if s.fate(i, "k41_gedou", "hand", True) != "ok":
        return None
    d.hand.remove("k41_gedou")
    s.ev(f"　S・バック：{BY_KEY[k].name} を捨てて「涅槃」の鬼 ゲドウ大権現を召喚")
    s.enter(i, "k41_gedou", "hand", True)
    return "grave"


def w_gedou(s, i, u):
    """相手のターン中に、相手のクリーチャーが召喚以外の方法で出た時、そのクリーチャーを破壊する"""
    if u.c.kind != "C" or u.x.get("summoned") or s.tp != i:
        return
    j = 1 - i
    if not s.has(j, "k41_gedou") or u not in s.P[i].board:
        return
    s.ev(f"　ゲドウ大権現：召喚以外で出た {u.c.name} を破壊")
    s.leave(i, u, "grave", by_opp=True, destroy=True)


def bf_gedou(s, ai, au, di, du, a_dies, d_dies):
    """＜鬼エンド＞：スレイヤーを得る"""
    if not _oni_end(s):
        return a_dies, d_dies
    if au.k == "k41_gedou":
        d_dies = True
    if du.k == "k41_gedou":
        a_dies = True
    return a_dies, d_dies


add("k41_gedou", "「涅槃」の鬼 ゲドウ大権現", 6, "DF", power=7000, brk=2,
    races=("demonio",), pri=8, roles="blk rem dis trg",
    shieldrep=rep_gedou, enterwatch=w_gedou, battlefx=bf_gedou,
    blockok=lambda s, u: u.k == "k41_gedou" and _oni_end(s),
    text="S・バック：闇または火（闇または火のカードを自分のシールドゾーンから手札に加える時、"
         "そのカードを捨てて、このクリーチャーをコストを支払わずに召喚してもよい）。W・ブレイカー。"
         "相手のターン中に、相手のクリーチャーが召喚以外の方法で出た時、そのクリーチャーを破壊する。"
         "＜鬼エンド＞シールドが1つもないプレイヤーがいれば、このクリーチャーに"
         "「ブロッカー」と「スレイヤー」を与える",
    note="S・バックで捨てるのは手札に加わるはずだったそのカードなので、"
         "そのカードより ゲドウ大権現 の重要度が高い時だけ使う（全デッキ共通の決まり）",
    status="full", source=SRC["k41_gedou"])


# ================================================================ 禁鬼機関 ジャオウガ-8
E.HYPER_POW["k41_jaouga8"] = 3000          # 9000 → 12000


def ex_jaouga8(s, i, u):
    """スター進化の進化元：デモニオ、闇、または自然のクリーチャー"""
    return "demonio" in u.c.races or bool(set("DN") & set(u.c.civ))


def e_jaouga8(s, i, u):
    """召喚によって出た時、自分のシールドを1つ墓地に置いてもよい。
    そうしたら、自分のマナゾーンにあるカードをすべてアンタップする"""
    if not u.x.get("summoned"):
        return
    p = s.P[i]
    if p.mused < 2 or not p.sh:
        return                              # 起こすマナが無いなら、シールドを損するだけなのでしない
    j = _worst_shield(s, i)
    if j is None:
        return
    s.take_shield(i, j, "grave")
    p.mused = 0
    s.ev("　ジャオウガ-8：シールドを1つ墓地に置き、マナをすべてアンタップ")


def rep_jaouga8(s, ai, di, broken):
    """S・バック：デモニオ（割れたシールドのデモニオ1枚を捨てて、手札からただで召喚する）"""
    d = s.P[di]
    if "k41_jaouga8" not in d.hand or not broken or s.over:
        return False
    base = s.evo_src(di, "k41_jaouga8")
    if base is None:
        return False                        # スター進化なので進化元が要る
    idx = next((j for j, (k, _up) in enumerate(broken) if "demonio" in BY_KEY[k].races), None)
    if idx is None or s.fate(di, "k41_jaouga8", "hand", True) != "ok":
        return False
    k = broken.pop(idx)[0]
    s.grave_put(di, k)
    d.hand.remove("k41_jaouga8")
    s.ev(f"　S・バック：{BY_KEY[k].name} を捨てて禁鬼機関 ジャオウガ-8を召喚")
    s.enter(di, "k41_jaouga8", "hand", True, on=base)
    return False


def fa_jaouga8(s, i, av, cv):
    """ハイパーモード：自分のターンに1度、デモニオ・カードを自分の墓地から使ってもよい"""
    p = s.P[i]
    if p.x.get("k41_j8t") == s.turn or s.manaexec(i):
        return []
    if not any(z.k == "k41_jaouga8" and z.hyper for z in p.board):
        return []
    out = []
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if "demonio" not in c.races:
            continue
        if c.kind == "C":
            if not _plain_cre(c):
                continue
            n = s.ccost(i, k, av)
            if n <= av and (n == 0 or cv.issuperset(c.civ)) and s.fate(i, k, "grave", True) == "ok":
                out.append(("x:k41_j8", k, n))
        elif c.kind == "S":
            n = s.spcost(i, k)
            if n <= av and (n == 0 or cv.issuperset(c.civ)) and s.spell_ok(i, c.cost):
                out.append(("x:k41_j8", k, n))
        elif c.kind == "T":
            if c.cost <= av and cv.issuperset(c.civ) and p.ban != c.cost:
                out.append(("x:k41_j8", k, c.cost))
    return out


def ap_jaouga8(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.grave or p.x.get("k41_j8t") == s.turn:
        return
    c = BY_KEY[k]
    p.x["k41_j8t"] = s.turn
    p.mused += a[2]
    p.grave.remove(k)
    s.ev(f"ハイパーモード（ジャオウガ-8）：墓地の {c.name} を使う（{a[2]}マナ）")
    if c.kind == "C":
        s.enter(i, k, "grave", True)
    elif c.kind == "S":
        s.cast(i, k)
    else:
        s.place_tama(i, k)


add("k41_jaouga8", "禁鬼機関 ジャオウガ-8", 4, "DN", power=9000, brk=2, blocker=True, zrush=True,
    evo="DN", races=("demonio", "onirexstars", "choukaju"), pri=8, roles="blk acc atk fin",
    enter=e_jaouga8, evox=ex_jaouga8, brkx=_powered_brk,
    leaverep=star_evo_rep("k41_jaouga8", "禁鬼機関 ジャオウガ-8"),
    breakrep=rep_jaouga8, freeacts=fa_jaouga8, actapply={"x:k41_j8": ap_jaouga8},
    playrule=_pr_cre("スター進化の元になるデモニオか闇・自然のクリーチャーが4体いない",
                     lambda c: "demonio" in c.races or bool(set("DN") & set(c.civ))),
    text="S・バック：デモニオ（デモニオ・カードを自分のシールドゾーンから手札に加える時、そのカードを捨てて、"
         "このクリーチャーをコストを支払わずに召喚してもよい）。"
         "スター進化（自分のデモニオ、闇、または自然のクリーチャー1体の上に置く。離れる時は一番上のこのカードだけが"
         "離れ、下のカードがバトルゾーンに残る）。ブロッカー。"
         "パワード・ブレイカー（パワー6000ごとにブレイクするシールドが1枚増える。素のパワー9000なら2枚、"
         "ハイパーモードの12000なら3枚）。"
         "このクリーチャーが召喚によって出た時、自分のシールドを1つ墓地に置いてもよい。そうしたら、"
         "自分のマナゾーンにあるカードをすべてアンタップする（起こせるマナが2つ以上ある時だけ使う）。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモード）。"
         "ハイパーモード12000：自分のターンに1度、デモニオ・カードを自分の墓地から使ってもよい",
    note="ハイパーモードの一文は、カード本文に「デモニオ・カードを自分の墓地から実行してもよい」と書かれていて、"
         "「コストを支払わずに」とは書かれていない（dmwiki を3回読んで確かめた）。"
         "そのため、コストを支払って墓地から使う（召喚・唱える・タマシードを置く）能力として実装した。"
         "墓地から出すのは進化でないクリーチャーだけ（進化は進化元が別に要るため）。"
         "このカードはスター進化なので、envtest の effect_smoke（自分の場に水のクリーチャー1体だけ）では"
         "進化元が作れず「使えた場面 0」になる。実戦（game_smoke）では使われている",
    source=SRC["k41_jaouga8"])


# ================================================================ ボルシャック・ゴルギーニ
def cx_gorgini(s, i, av):
    """自分のシールドゾーンに表向きのカードがあれば、召喚コストを3少なくする"""
    return 4 if _faceup(s, i) else 7


def w_gorgini(s, i, u):
    """自分のアーマード・ドラゴンが出た時、相手のクリーチャー1体をタップする。
    次の自分のターンのはじめまで、それはアンタップしない"""
    if u.c.kind != "C" or not race_like(u.c, "armoreddragon"):
        return
    for _ in range(sum(1 for z in s.P[i].board if z.k == "k41_gorgini")):
        if s.over:
            return
        t = s.target(i, lambda x: not x.tap) or s.target(i)
        if t is None:
            return
        s.tap_cre(1 - i, t)
        t.frz = 1
        s.ev(f"　ゴルギーニ：{t.c.name} をタップし、次の自分のターンまでアンタップしない")


def a_gorgini(s, i, u):
    """攻撃する時、カードを2枚引いてもよい"""
    if len(s.P[i].deck) >= 3:
        s.draw(i, 2)


add("k41_gorgini", "ボルシャック・ゴルギーニ", 7, "LWF", power=9500, brk=2, sa=True,
    races=("mechaarmoreddragon", "armoreddragon", "dragon"), pri=10, roles="atk draw rem dis",
    costx=cx_gorgini, enterwatch=w_gorgini, attack=a_gorgini,
    text="自分のシールドゾーンに表向きのカードがあれば、このクリーチャーの召喚コストを3少なくする。"
         "スピードアタッカー。W・ブレイカー。"
         "自分のアーマード・ドラゴンが出た時、相手のクリーチャーを1体選び、タップする。"
         "次の自分のターンのはじめまで、それはアンタップしない"
         "（アンタップしている重要度のいちばん高いクリーチャーを選ぶ）。"
         "このクリーチャーが攻撃する時、カードを2枚引いてもよい（山札が3枚以上ある時だけ引く）",
    source=SRC["k41_gorgini"])


# ================================================================ ボルシャック・カクメイジン
def ch_kakumeijin(s, i, u):
    """S革命チェンジ：アーマード"""
    return race_like(u.c, "armored")


def e_kakumeijin(s, i, u):
    """出た時、自分の山札の上から1枚を表向きでシールド化する"""
    s.add_shield(i, None, True)


def lr_kakumeijin(s, i, u, dest, destroy_):
    """自分のアーマード・ドラゴンが離れる時、かわりに自分のシールドゾーンにある
    表向きのカードを1枚、裏向きにしてもよい"""
    if u.c.kind != "C" or not race_like(u.c, "armoreddragon"):
        return False
    if not s.has(i, "k41_kakumeijin"):
        return False
    p = s.P[i]
    j = next((x for x, (_k, up) in enumerate(p.sh) if up), None)
    if j is None:
        return False
    s.flip_shield(i, j, False)
    s.ev(f"　カクメイジン：表向きのシールドを裏向きにして {u.c.name} は離れない")
    return True


add("k41_kakumeijin", "ボルシャック・カクメイジン", 5, "LWF", power=6000, brk=2, sa=True,
    races=("magicarmoreddragon", "armoreddragon", "dragon", "gamecommand", "command"),
    pri=8, roles="atk shd dis",
    enter=e_kakumeijin, changex=ch_kakumeijin, leaverep=lr_kakumeijin,
    changezone=("hand", "shield"),
    playrule=_pr_cre("S革命チェンジの元になるアーマードが3体いない", lambda c: race_like(c, "armored"), n=3),
    text="S革命チェンジ：アーマード（自分のアーマードが攻撃する時、そのクリーチャーと、"
         "手札または表向きのシールドにあるこのクリーチャーを入れ替えてもよい）。"
         "スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から1枚を表向きでシールド化する。"
         "自分のアーマード・ドラゴンが離れる時、かわりに自分のシールドゾーンにある表向きのカードを1枚、"
         "裏向きにしてもよい（表向きのシールドがあれば必ず使う）",
    note="", status="full", source=SRC["k41_kakumeijin"])


# ================================================================ 鬼黒皇グレイテスト・ジャオウガ
def cx_greatest(s, i, av):
    """召喚する時、自分のシールドを2つまで選ぶ。選んだ1つにつき召喚コストを1少なくする"""
    return max(1, 5 - min(2, len(s.P[i].sh)))


def px_greatest(s, i, k, n):
    """選んだシールドの数を覚えておく（出た時に手札に加えるため）"""
    s.P[i].x["k41_gr"] = (s.turn, min(2, len(s.P[i].sh)))
    return None


def ex_greatest(s, i, u):
    """スター進化の進化元：デモニオ、闇、火、または自然のクリーチャー"""
    return "demonio" in u.c.races or bool(set("DFN") & set(u.c.civ))


def e_greatest(s, i, u):
    """出た時、選んだシールドを手札に加える（そのS・トリガーは使えない）"""
    p = s.P[i]
    t, n = p.x.get("k41_gr", (-1, 0))
    if not u.x.get("summoned") or t != s.turn:
        return
    p.x["k41_gr"] = (-1, 0)
    for _ in range(n):
        j = _best_shield(s, i)
        if j is None:
            break
        r = s.take_shield(i, j, "hand")
        if r is None:
            break
        s.ev(f"　グレイテスト・ジャオウガ：シールドの {BY_KEY[r[0]].name} を手札へ（S・トリガーは使えない）")


def a_greatest(s, i, u):
    """攻撃する時、自分の手札を1枚捨ててもよい。そうしたら、カードを2枚引き、
    コスト5以下のデモニオを1つ、自分の墓地から出す"""
    p = s.P[i]
    if not p.hand or len(p.deck) < 3:
        return
    k = worst_hand(s, i)
    if k is None:
        return
    s.discard(i, k)
    s.draw(i, 2)
    if not s.over:
        _revive_element(s, i, lambda c: c.cost <= 5 and "demonio" in c.races)


add("k41_greatest", "鬼黒皇グレイテスト・ジャオウガ", 5, "DFN", power=7000, brk=2, mach=True,
    evo="DFN", races=("demonio", "onirexstars"), pri=8, roles="atk draw rem acc",
    enter=e_greatest, attack=a_greatest, costx=cx_greatest, payx=px_greatest, evox=ex_greatest,
    leaverep=star_evo_rep("k41_greatest", "鬼黒皇グレイテスト・ジャオウガ"),
    playrule=_pr_cre("スター進化の元になるデモニオか闇・火・自然のクリーチャーが4体いない",
                     lambda c: "demonio" in c.races or bool(set("DFN") & set(c.civ))),
    text="このクリーチャーを召喚する時、自分のシールドを2つまで選ぶ。選んだシールド1つにつき、"
         "このクリーチャーの召喚コストを1少なくする。このクリーチャーが出た時、選んだシールドを手札に加える"
         "（その「S・トリガー」は使えない。重要度の高い裏向きのシールドから選ぶ）。"
         "スター進化（自分のデモニオ、闇、火、または自然のクリーチャー1体の上に置く。離れる時は一番上の"
         "このカードだけが離れ、下のカードがバトルゾーンに残る）。マッハファイター。W・ブレイカー。"
         "このクリーチャーが攻撃する時、自分の手札を1枚捨ててもよい。そうしたら、カードを2枚引き、"
         "コスト5以下のデモニオを1つ、自分の墓地から出す",
    note="このカードはスター進化なので、envtest の effect_smoke（自分の場に水のクリーチャー1体だけ）では"
         "進化元が作れず「使えた場面 0」になる。実戦（game_smoke）では使われている。"
         "墓地から出すデモニオは、進化でないクリーチャーかタマシード（コスト5以下）のうち重要度のいちばん高いもの",
    source=SRC["k41_greatest"])


# ================================================================ パルフェ・ルピア／「あとはたのんだぞ」
def si_parfait(s, i, k, up):
    """カードが自分のシールドゾーンに表向きで置かれた時、自分のマナゾーンにあるカードが2枚以上なら、
    このクリーチャーを自分の手札から出してもよい"""
    if not up or s.over:
        return
    p = s.P[i]
    if "k41_parfait" not in p.hand or len(p.mana) < 2:
        return
    if s.fate(i, "k41_parfait", "hand", False) != "ok":
        return
    p.hand.remove("k41_parfait")
    s.ev("　パルフェ・ルピア：表向きのシールドが置かれたので手札から出る")
    s.enter(i, "k41_parfait", "hand", False)


def sp_parfait(s, i):
    """「あとはたのんだぞ」：次の中から1回選ぶ"""
    t = s.target(i, lambda z: z.c.cost <= 3)
    if t is not None and s.val(t) >= 3:
        s.ev(f"　あとはたのんだぞ：{t.c.name} をシールド化")
        s.leave(1 - i, t, "shield", by_opp=True)
        return
    s.ev("　あとはたのんだぞ：自分の山札の上から1枚を表向きでシールド化")
    s.add_shield(i, None, True)


add("k41_parfait", "パルフェ・ルピア / 「あとはたのんだぞ」", 5, "L", power=5500, blocker=True, gs=True,
    races=("armoreddragon", "dragon", "firebird", "mecadeldinero"), twin=(3, "L", False),
    pri=6, roles="blk trg shd rem",
    spell=sp_parfait, shieldin=si_parfait,
    text="クリーチャー側：G・ストライク。ブロッカー。"
         "カードが自分のシールドゾーンに表向きで置かれた時、自分のマナゾーンにあるカードが2枚以上なら、"
         "このクリーチャーを自分の手札から出してもよい。"
         "呪文側「あとはたのんだぞ」（コスト3・光）：次の中から1回選ぶ。"
         "(1)相手のコスト3以下のクリーチャーを1体選び、シールド化する／"
         "(2)自分の山札の上から1枚を表向きでシールド化する。"
         "取り除ける相手のクリーチャーの重要度が3以上ならそれを選び、なければシールドを増やす",
    source=SRC["k41_parfait"])


# ================================================================ 邪眼左神エンドレス
def e_endless(s, i, u):
    """出た時、各プレイヤー1人につき、そのプレイヤーのクリーチャーを2体選び、
    そのうち1体をもう1体の下に置いてもよい"""
    o = s.P[1 - i]
    cands = [z for z in o.board if z.c.kind == "C" and not z.jd]
    if len(cands) < 2:
        return
    sunk = s.target(i)
    if sunk is None or sunk not in cands:
        return
    rest = [z for z in cands if z is not sunk]
    if not rest:
        return
    base = min(rest, key=lambda z: E.PRI[z.k])
    s.ev("　エンドレス：相手のクリーチャー2体のうち1体を、もう1体の下に置く")
    _sink(s, 1 - i, base, sunk)
    # 自分の側は、クリーチャー1体を失う取り引きになるので、全デッキ共通の決まりでは使わない


add("k41_endless", "邪眼左神エンドレス", 4, "W", power=3000, trig=True,
    races=("godgard", "god", "cybercommand", "command"), pri=6, roles="trg rem",
    enter=e_endless, godlink=("L", ()),
    text="S・トリガー。"
         "左G・リンク（「中央G・リンク」か「右G・リンク」を持つゴッドの左にリンクしてもよい。"
         "リンクしたゴッドはパワーも能力も併せ持つ1体のクリーチャーになり、離れる時は1枚だけが離れる）。"
         "このクリーチャーが出た時、各プレイヤー1人につき、そのプレイヤーのクリーチャーを2体選び、"
         "そのうち1体をもう1体の下に置いてもよい"
         "（相手については、重要度のいちばん高いクリーチャーを、いちばん安いクリーチャーの下に押し込む）",
    note="「下に置く」は自分の側については、クリーチャーを1体失うだけなので使わない（全デッキ共通の決まり）",
    status="full", source=SRC["k41_endless"])


# ================================================================ 怒像アゲ
def e_dozouage(s, i, u):
    """出た時、コストの合計が9以下になるように、相手のクリーチャーを2体まで選び、破壊する"""
    left = 9
    for _ in range(2):
        if s.over:
            return
        cap = left
        t = s.target(i, lambda z: z.c.cost <= cap)
        if t is None:
            return
        left -= t.c.cost
        destroy(s, i, t)


def lose_dozouage(s, i, how):
    """超魂X：自分がゲームに負ける時、これが進化クリーチャーなら、かわりにこのクリーチャーの下にある
    カードをすべて墓地に置いてもよい"""
    for z in s.P[i].board:
        if z.k != "k41_dozouage" and "k41_dozouage" not in z.under:
            continue
        if not z.under:
            continue
        for k in z.under:
            s.grave_put(i, k)
        z.under = []
        s.ev(f"　怒像アゲ（超魂X）：{z.c.name} の下のカードをすべて墓地に置いて、負けを置き換えた")
        return True
    return False


add("k41_dozouage", "怒像アゲ", 7, "F", power=5000, trig=True,
    races=("demoncommand", "command", "demonslegacy", "fusioner"), pri=8, roles="trg rem fin",
    enter=e_dozouage, loserep=lose_dozouage,
    text="S・トリガー。"
         "このクリーチャーが出た時、コストの合計が9以下になるように、相手のクリーチャーを2体まで選び、破壊する"
         "（重要度の高いものから、合計が9を超えないように選ぶ）。"
         "超魂X（このカードがクリーチャーの下にあれば、そのクリーチャーにも次の能力を与える）："
         "自分がゲームに負ける時、これが進化クリーチャーなら、かわりにこのクリーチャーの下にある"
         "カードをすべて墓地に置いてもよい",
    source=SRC["k41_dozouage"])


# ================================================================ 邪眼龍神メタル・アポロヌス
def w_metalapollonus(s, i, u):
    """相手のクリーチャーがコストを支払わずに出た時、それを破壊する"""
    if u.c.kind != "C" or u.x.get("summoned"):
        return
    j = 1 - i
    if not s.has(j, "k41_metalapollonus") or u not in s.P[i].board:
        return
    s.ev(f"　メタル・アポロヌス：コストを支払わずに出た {u.c.name} を破壊")
    s.leave(i, u, "grave", by_opp=True, destroy=True)


add("k41_metalapollonus", "邪眼龍神メタル・アポロヌス", 6, "F", power=7000, brk=2,
    races=("godgard", "god", "armoreddragon", "dragon", "tyranodrake"), pri=8, roles="rem dis atk",
    enterwatch=w_metalapollonus, brkx=_powered_brk, godlink=("R", ()),
    text="パワード・ブレイカー（パワー6000ごとにブレイクするシールドが1枚増える。パワー7000なので2枚）。"
         "右G・リンク・ガルド（《龍神ヘヴィ》《破壊神デス》や「中央G・リンク」「左G・リンク」を持つゴッドの"
         "右にリンクしてもよい。リンクしたゴッドはパワーも能力も併せ持つ1体のクリーチャーになる）。"
         "相手のクリーチャーがコストを支払わずに出た時、それを破壊する",
    note="リンク相手の《龍神ヘヴィ》《破壊神デス》はこのカードプールに無いので、"
         "「中央G・リンク」「左G・リンク」を持つゴッドにだけリンクする",
    status="full", source=SRC["k41_metalapollonus"])


# ================================================================ ボルテール・ミラー・ドラゴン／ミラー・チャージャー
def _shield_plus(s, i):
    """山札の上から1枚目を表向きにし、自分のシールド1つの上に置く

    近似：シールドを束ねる仕組み（シールド・プラス）がこのシミュレーターに無いので、
    「シールドの枚数は増えず、表向きのシールドが1つできる」という結果だけを再現し、
    自分のシールド1つを表向きにする（山札の上の1枚は山札に残る）。"""
    p = s.P[i]
    if not p.sh:
        return False
    cands = [j for j, (_k, up) in enumerate(p.sh) if not up]
    if not cands:
        return True                   # もう全部表向き：結果は変わらない
    j = min(cands, key=lambda x: E.PRI[p.sh[x][0]])
    s.flip_shield(i, j, True)
    s.ev(f"　シールドの {BY_KEY[p.sh[j][0]].name} が表向きになった")
    return True


def e_voltaire(s, i, u):
    _shield_plus(s, i)


def sp_voltaire(s, i):
    """ミラー・チャージャー：シールドの上に1枚置き、チャージャーでこの呪文をマナゾーンへ"""
    _shield_plus(s, i)
    s.add_mana(i, "k41_voltaire")
    s.ev("　チャージャー：ミラー・チャージャーをマナゾーンへ")


add("k41_voltaire", "ボルテール・ミラー・ドラゴン / ミラー・チャージャー", 5, "LF", power=5000, sa=True,
    races=("armoreddragon", "dragon"), twin=(3, "LF", False), nograve=True,
    pri=6, roles="shd atk acc",
    enter=e_voltaire, spell=sp_voltaire,
    changex=lambda s, i, u: bool(set("LF") & set(u.c.civ)),
    playrule=_pr_cre("革命チェンジの元になる光か火のクリーチャーが3体いない",
                     lambda c: bool(set("LF") & set(c.civ)) and not c.noatk, n=3),
    text="クリーチャー側：革命チェンジ：光または火のクリーチャー（自分の光か火のクリーチャーが攻撃する時、"
         "そのクリーチャーと手札のこのクリーチャーを入れ替えてもよい）。スピードアタッカー。"
         "このクリーチャーが出た時、自分の山札の上から1枚目を表向きにし、自分のシールド1つの上に置いてもよい。"
         "呪文側「ミラー・チャージャー」（コスト3・光/火）：自分の山札の上から1枚目を表向きにし、"
         "自分のシールド1つの上に置く。チャージャー（唱えた後、この呪文をマナゾーンに置く）",
    note="「自分のシールド1つの上に置く」はシールド・プラス（束ねて1つのシールドとして扱うので、"
         "シールドの数は増えず、そのシールドが割れると束ねたカードがまとめて手札に入る）。"
         "シールドを束ねる仕組みがこのシミュレーターに無いため、"
         "「シールドの枚数は増えないまま、表向きのシールドが1つできる」結果だけを再現し、"
         "自分のシールド1つを表向きにする形で近似した（山札の上の1枚は山札に残るので、"
         "そのシールドが割れた時に1枚多く手札に入る分は再現されない）。"
         "シールドが0枚の時は置く先が無いので何も起きない",
    status="partial", source=SRC["k41_voltaire"])


# ================================================================ ボルシャック・ゴルファンタジスタ
def cx_golfantasista(s, i, av):
    """自分のシールドゾーンに表向きのカードがあれば、召喚コストを2少なくする"""
    return 3 if _faceup(s, i) else 5


def e_golfantasista(s, i, u):
    """出た時、相手のクリーチャー1体を選んでもよい。その選んだクリーチャーとこのクリーチャーをバトルさせる"""
    mine = s.power(i, u, True)
    t = s.target(i, lambda z: s.power(1 - i, z) < mine)
    if t is None:
        return
    s.ev(f"　ゴルファンタジスタ：{t.c.name} とバトルする")
    s.battle(i, u, 1 - i, t)


add("k41_golfantasista", "ボルシャック・ゴルファンタジスタ", 5, "LF", power=5000, brk=2, sa=True,
    races=("giantarmoreddragon", "armoreddragon", "giant", "dragon"), pri=7, roles="atk rem",
    enter=e_golfantasista, costx=cx_golfantasista,
    powerx=lambda s, i, u, atk: 5000 if s.tp == i else 0,
    text="自分のシールドゾーンに表向きのカードがあれば、このクリーチャーの召喚コストを2少なくする。"
         "スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが出た時、相手のクリーチャーを1体選んでもよい。"
         "その選んだクリーチャーとこのクリーチャーをバトルさせる"
         "（勝てる相手のうち重要度のいちばん高いものを選び、勝てる相手がいなければ選ばない）。"
         "自分のターン中、このクリーチャーのパワーを+5000する",
    source=SRC["k41_golfantasista"])


# ================================================================ 「鬼情」の極 ジャオウグリラ／「自由で欲望のままに生きるのだ！」
def ex_jaougurira(s, i, u):
    """スター進化の進化元：デモニオ、闇、または火のクリーチャー"""
    return "demonio" in u.c.races or bool(set("DF") & set(u.c.civ))


def fa_jaougurira(s, i, av, cv):
    """このクリーチャーを自分の墓地から召喚してもよい"""
    p = s.P[i]
    if "k41_jaougurira" not in p.grave or s.manaexec(i):
        return []
    n = s.ccost(i, "k41_jaougurira", av)
    if n > av or (n > 0 and not cv.issuperset("DF")):
        return []
    if s.evo_src(i, "k41_jaougurira") is None:
        return []
    if s.fate(i, "k41_jaougurira", "grave", True) != "ok":
        return []
    return [("x:k41_jg", n)]


def ap_jaougurira(s, a):
    i = s.tp
    p = s.P[i]
    if "k41_jaougurira" not in p.grave:
        return
    base = s.evo_src(i, "k41_jaougurira")
    if base is None:
        return
    p.mused += a[1]
    p.grave.remove("k41_jaougurira")
    s.ev(f"召喚：「鬼情」の極 ジャオウグリラ（墓地から・{a[1]}マナ）")
    s.enter(i, "k41_jaougurira", "grave", True, on=base)


def a_jaougurira(s, i, u):
    """攻撃する時、自分の墓地にあるカードの枚数以下のコストを持つ相手のクリーチャーを1体選び、破壊してもよい"""
    n = len(s.P[i].grave)
    t = s.target(i, lambda z: z.c.cost <= n)
    if t is None:
        return
    destroy(s, i, t)


def sp_jaougurira(s, i):
    """「自由で欲望のままに生きるのだ！」：次の中から1回選ぶ"""
    t = s.target(i, lambda z: z.c.cost <= 3, kinds="CTX")
    if t is not None and s.val(t) >= 3:
        s.ev(f"　自由で欲望のままに生きるのだ！：{t.c.name} を破壊")
        destroy(s, i, t)
        return
    s.ev("　自由で欲望のままに生きるのだ！：自分の山札の上から3枚を墓地に置く")
    s.mill(i, 3)


add("k41_jaougurira", "「鬼情」の極 ジャオウグリラ / 「自由で欲望のままに生きるのだ！」", 4, "DF",
    power=7000, brk=2, evo="DF", races=("demonio", "onirexstars"), twin=(2, "DF", False),
    pri=7, roles="atk rem acc fin",
    attack=a_jaougurira, spell=sp_jaougurira, evox=ex_jaougurira,
    leaverep=star_evo_rep("k41_jaougurira", "「鬼情」の極 ジャオウグリラ"),
    freeacts=fa_jaougurira, actapply={"x:k41_jg": ap_jaougurira},
    playrule=_pr_cre("スター進化の元になるデモニオか闇・火のクリーチャーが4体いない",
                     lambda c: "demonio" in c.races or bool(set("DF") & set(c.civ))),
    text="クリーチャー側：このクリーチャーを自分の墓地から召喚してもよい（コストは支払う）。"
         "スター進化（自分のデモニオ、闇、または火のクリーチャー1体の上に置く。離れる時は一番上のこのカードだけが"
         "離れ、下のカードがバトルゾーンに残る）。W・ブレイカー。"
         "このクリーチャーが攻撃する時、自分の墓地にあるカードの枚数以下のコストを持つ相手のクリーチャーを"
         "1体選び、破壊してもよい。"
         "呪文側「自由で欲望のままに生きるのだ！」（コスト2・闇/火）：次の中から1回選ぶ。"
         "(1)自分の山札の上から3枚を墓地に置く／(2)相手のコスト3以下のエレメントを1つ選び、破壊する",
    source=SRC["k41_jaougurira"])


# ================================================================ 暗黒破壊神デス・フェニックス
def es_deathphoenix(s, i):
    """墓地進化V：闇または火のクリーチャーを2体墓地から選び、その上に重ねつつ出す（1体目）"""
    cs = sorted((k for k in s.P[i].grave if _df_cre(BY_KEY[k])), key=E.PRI.get)
    if len(cs) < 2:
        return None
    return ("grave", cs[0])


def e_deathphoenix(s, i, u):
    """墓地進化V の2体目（エンジンの evosrc は1枚しか返せないので、ここで下に積む）"""
    p = s.P[i]
    if u.under:
        return
    cs = sorted((k for k in p.grave if _df_cre(BY_KEY[k])), key=E.PRI.get)
    if len(cs) < 2:
        return
    k = cs[1]                        # 1体目（cs[0]）はエンジンが後で下に積む
    p.grave.remove(k)
    u.under.append(k)
    s.ev(f"　墓地進化V：{BY_KEY[k].name} も下に置く")


def a_deathphoenix(s, i, u):
    """メテオバーン：攻撃する時、下に重ねたカードを1枚墓地に置いてもよい。
    そうしたら、《龍神ヘヴィ》または《龍神メタル》を1体自分の墓地から出す"""
    p = s.P[i]
    if not u.under:
        return
    cs = [k for k in p.grave if BY_KEY[k].name in _RYUJIN and _plain_cre(BY_KEY[k])]
    if not cs:
        return
    k = max(cs, key=E.PRI.get)
    if s.fate(i, k, "grave", False) != "ok":
        return
    s.grave_put(i, u.under.pop(0))
    p.grave.remove(k)
    s.ev(f"　メテオバーン：墓地から {BY_KEY[k].name} を出す")
    s.enter(i, k, "grave", False)


add("k41_deathphoenix", "暗黒破壊神デス・フェニックス", 4, "DF", power=9000, brk=2,
    evo="DF", races=("god", "phoenix"), pri=9, roles="fin atk",
    enter=e_deathphoenix, attack=a_deathphoenix, evosrc=es_deathphoenix, brkx=_powered_brk,
    playrule=_pr_cre("墓地進化Vの元になる闇か火のクリーチャーが4体いない",
                     lambda c: bool(set("DF") & set(c.civ))),
    text="墓地進化V（闇または火のクリーチャーを2体、自分の墓地から選び、このクリーチャーをその上に重ねつつ出す）。"
         "パワード・ブレイカー（パワー6000ごとにブレイクするシールドが1枚増える。パワー9000なので2枚）。"
         "メテオバーン：このクリーチャーが攻撃する時、このクリーチャーの下に重ねたカードを1枚、"
         "墓地に置いてもよい。そうしたら、《龍神ヘヴィ》または《龍神メタル》を1体、自分の墓地から出す",
    note="トライ・G・リンクは《龍神ヘヴィ》の右横・《龍神メタル》の左横・その2枚の間にだけリンクできる"
         "能力で、その2枚がこのカードプールに無いため、リンクを登録していない"
         "（ほかのゴッドにはリンクできない）。メテオバーンも同じ2枚を墓地から出す能力なので、"
         "名前が一致するカードが墓地にある時だけ動く形で入れてあるが、実際には働かない",
    status="partial", source=SRC["k41_deathphoenix"])
