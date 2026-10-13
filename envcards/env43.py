"""担当43：DM26-EX2「悪感謝祭 カリスマBEST」の未実装カード15枚（key は k43_）

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ（https://dmwiki.net/《カード名》）と
      生の wiki ソース（?plugin=template&refer=《カード名》）を別の質問で2回ずつ（数字や能力の切れ目が
      1回では読めなかった《邪眼神オール》《邪眼右神デリート》は3回）読み、カード名・コスト・文明・種類・
      種族・パワー・ブレイク数・能力本文が一致することを確かめた。
      ツインパクト2枚（レーホウ・衛・デカッチ／轟速 ザ・ダラー）の正式なページ名は、
      収録弾のページ（https://dmwiki.net/DM26-EX2）のカードリストで確かめた。

  この札束に入っている仕組み
    ・**ゴッド・ガルド／ゴッド・ノヴァOMG の G・リンク**（邪眼神オール＝中央、邪眼右神デリート＝右、
      邪眼龍神ヘヴィ・アポロヌス＝左、極限龍神メタル＝右OMG）。エンジンの `godlink=` で入れた。
      つなぐのは追加の手（`x:k43link`。召喚してからリンクする）と、S・トリガーや
      《プロジェクト・ゴッド》のように召喚以外で出た時の `ew_link43`。
      中央は左か右、左は中央か右、右は中央か左にだけつながり、同じ位置は2枚つなげない。
    ・**パワード・ブレイカー**（邪眼神オール・極限龍神メタル）。`brkx=` で「パワー6000ごとに+1」。
    ・**S・バック：デモニオ**（悪霊鬼王ジャオディオス・バクロ法師の封）。デモニオ・カードが自分の
      シールドゾーンから手札に加わる時、そのカードを捨てて、手札のこのカードをただでプレイする。
      `shieldrep=` で書いたので、ブレイクでも効果でも（シールドゾーンの出口はどこでも）誘発する。
    ・**スター進化**（悪霊鬼王ジャオディオス）。`envcards.env0.star_evo_rep` を使って退化が成り立つ形に。
    ・**シンカライズ**（シブキ将鬼の巻・バクロ法師の封）＝`engine3.SHINKA`。
    ・**スマッシュ・バースト**（轟速 ザ・ダラー）＝攻撃する時に呪文側を場に置いたままただで唱える。
    ・**Zラッシュ＋ハイパーモード**（鬼核アトム・ジャオウガ・ボルシャック・マントラ）。
      `zrush=True` は「シールドが離れたらハイパーモードになる」そのものなので、そのまま使った。
    ・**ガードマン**（レーホウ・衛・デカッチ）＝`envcards.env0.guardman`。
    ・**D2フィールド**（Dの侵略 クリム・ゾーン）。無いゾーンなので、場に残るカード＝タマシードで表した
      （env26 の《Dの機動 ヴァイス・ヴァーチュー》と同じ扱い）。
    ・**表向きのシールド**（カイザー・ルピア）。p.sh の表裏を立てて、軽減の条件に使っている。

  調べ直して意外だった点
    ・《カイザー・ルピア》は火ではなく**光文明のコスト2・パワー1000**で、DM26-EX2 が初出の新カード。
      ルピア（アーマード・ファイアー・バード）なのに光、というのは2回読んでも同じだった。
    ・《邪眼右神デリート》の能力は「出た相手クリーチャーの攻撃ロック」だけでなく、
      **コストを支払わずに出ていたら1枚引く**が付く。素のパワー表記は「3000+」だが、
      これは**ゴッドのリンクでパワーが合算される**ことを表す書き方で、パワード・ブレイカーではない
      （生ソースに ''パワード・ブレイカー'' の行が無いことを確かめた）。
      いっぽう《邪眼神オール》（4000+）と《極限龍神メタル》（7000+）には行があり、本当に持っている。
    ・《悪霊鬼王ジャオディオス》はコスト3の**スター進化**で、出た時**と**攻撃する時に
      パワー6000以下を破壊する。S・バックまで付いていて、コスト3としては相当に重い。
    ・《轟速 ザ・ダラー》は「轟速」で種族も**侵略者**なのに、**侵略を持っていない**。
      持っているのは S・トリガー（クリーチャー側）とスマッシュ・バーストで、呪文側は
      「ソニック・コマンド・ワード」という種別だった。
    ・《レーホウ・衛・デカッチ》の呪文側は「呪文：**アーマード・アーツ**」で、S・トリガーは無い。
    ・《プロジェクト・ゴッド》は DM-36（2011年）の古い札で、DM26-EX2 でテキストが更新されている
      （「何体を」リンクするか書かずに「好きな数」になった）。
    ・《ボルシャック・マントラ》の**ブロッカーとW・ブレイカーはハイパーモード中だけ**
      （生ソースの `BGCOLOR(#cde):|c|` の位置で確かめた）。素のパワーは4500。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all, worst_hand
from envcards.env0 import SLAYER, discard_choice, guardman, star_evo_rep

W = "https://dmwiki.net/"
SRC = {
    "k43_jaganall": W + "《邪眼神オール》",
    "k43_dondon": W + "《ドンドン火噴くナウ》",
    "k43_kikaku": W + "《鬼核アトム・ジャオウガ》",
    "k43_kaizerlupia": W + "《カイザー・ルピア》",
    "k43_delete": W + "《邪眼右神デリート》",
    "k43_projectgod": W + "《プロジェクト・ゴッド》",
    "k43_heavyapollonus": W + "《邪眼龍神ヘヴィ・アポロヌス》",
    "k43_dekacchi": W + "《レーホウ・衛・デカッチ／「暴竜爵様のお出ましだッチ!」》",
    "k43_thedollar": W + "《轟速 ザ・ダラー／「イグニッション！ソニックドロォォォ!!」》",
    "k43_jaodios": W + "《悪霊鬼王ジャオディオス》",
    "k43_metal": W + "《極限龍神メタル》",
    "k43_shibuki": W + "《シブキ将鬼の巻》",
    "k43_crimzone": W + "《Dの侵略 クリム・ゾーン》",
    "k43_bakuro": W + "《バクロ法師の封》",
    "k43_mantra": W + "《ボルシャック・マントラ》",
}

# ================================================================ 共通の道具
def _plain_cre(c):
    """コストを支払わずにそのまま出せるクリーチャーか（進化は進化元が要るので別に見る）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _is_god(c):
    """ゴッドか（ゴッド・ガルド、ゴッド・ノヴァOMG なども含む）"""
    return any("god" in r for r in c.races)


def _is_dragonish(c):
    """ドラゴン・カードか（アーマード・ドラゴンなどの複合種族も含む）"""
    return any("dragon" in r for r in c.races)


def _is_firebird(c):
    return any("firebird" in r for r in c.races)


def _demonio(c):
    return "demonio" in c.races


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


def _ncopy(s, i, k):
    """自分のバトルゾーンにあるキー k のカードの枚数（G・リンクしている分も数える）"""
    n = 0
    for z in s.P[i].board:
        for x in s.parts(z):
            if x.k == k:
                n += 1
    return n


def bx_powered(s, i, u):
    """パワード・ブレイカー：パワー6000ごとにシールドをもう1つブレイクする
    （G・リンクしていれば、合計パワーで数える）"""
    return 1 + s.power(i, _unit(s, i, u), True) // 6000


def _face_down(s, i):
    """自分の裏向きのシールドの番号（表向きにしたり手札に加えたりするのに使う）"""
    return [j for j, (k, up) in enumerate(s.P[i].sh) if not up]


def _best_face_down(s, i):
    """手札に加えるならいちばん嬉しい裏向きのシールドの番号（無ければ一番後ろのシールド）"""
    p = s.P[i]
    cands = _face_down(s, i)
    if not cands:
        return len(p.sh) - 1 if p.sh else None
    return max(cands, key=lambda x: E.PRI[p.sh[x][0]])


# ================================================================ G・リンク（ゴッドの合体）
# 位置は左（"L"）・中央（"C"）・右（"R"）の3つ。「中央G・リンク」は左か右を持つゴッドに、
# 「左G・リンク」は中央か右に、「右G・リンク」は中央か左につながる（公式の決まり）。
# 左と右は中央が無くても直につながるので、1体のクリーチャーに同じ位置が2つ無ければよい。

GODS43 = ("k43_jaganall", "k43_delete", "k43_heavyapollonus", "k43_metal")


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


def fa_link43(s, i, av, cv):
    """追加の手「召喚してG・リンクする」（リンクせずに1体で出す手は、もとからある「召喚」のまま）"""
    p = s.P[i]
    out = []
    for k in GODS43:
        if k not in p.hand:
            continue
        mode = _link_mode(s, i, k, av, cv)
        if mode is None:
            continue
        for j, b in enumerate(p.board):
            if _link_ok(s, i, k, b):
                out.append(("x:k43link", k, j, mode))
    return out


def ap_link43(s, a):
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


def ew_link43(s, i, u):
    """G・リンク：召喚以外（S・トリガーや《プロジェクト・ゴッド》で出た分）は、その場でつなぐ

    自分の手札からの召喚は fa_link43 の追加の手で選べるので、ここでは拾わない（二重につながないため）。"""
    if u.k not in GODS43:
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


# ================================================================ S・バック：デモニオ
SBACK = ("k43_jaodios", "k43_bakuro")      # このモジュールの「S・バック：デモニオ」のカード


def _sback_ok(s, j, k):
    """手札のこのS・バックのカードを、いまコストを支払わずにプレイできるか"""
    c = BY_KEY[k]
    p = s.P[j]
    if k not in p.hand:
        return False
    if c.kind == "C":
        if c.evo and not c.neo and s.evo_src(j, k) is None:
            return False
        return s.fate(j, k, "hand", True) == "ok"
    if c.kind == "T":
        return p.ban != c.cost
    return False


def _sback_play(s, j, k):
    """S・バックのカードをコストを支払わずにプレイする"""
    c = BY_KEY[k]
    p = s.P[j]
    if k not in p.hand:
        return False
    if c.kind == "C":
        on = s.evo_src(j, k) if (c.evo and not c.neo) else None
        if c.evo and not c.neo and on is None:
            return False
        if s.fate(j, k, "hand", True) != "ok":
            return False
        p.hand.remove(k)
        s.enter(j, k, "hand", True, on=on)
        return True
    if c.kind == "T":
        p.hand.remove(k)
        s.place_tama(j, k)
        return True
    return False


def _sback_pick(s, j, cands):
    """捨てるデモニオ・カードと、そのかわりにプレイするS・バックのカードを選ぶ。

    「捨ててもよい」なので、ただでプレイできるカードのほうが、
    手札に加わるカードより重要度が高い時だけ使う（全デッキ共通の決まり）。"""
    keys = [k for k in SBACK if _sback_ok(s, j, k)]
    if not keys or not cands:
        return None
    k = max(keys, key=lambda x: E.PRI[x])
    pay = min(cands, key=lambda x: E.PRI[x])
    if E.PRI[k] <= E.PRI[pay]:
        return None
    return (pay, k)


def rep_sback(s, i, k, up, dest):
    """S・バック：デモニオ

    デモニオ・カードが自分のシールドゾーンから手札に加わる時、そのカードを捨てて、
    手札のこのカードをコストを支払わずにプレイしてもよい。
    捨てるので、そのカードの行き先を手札から墓地に変える（シールドゾーンの出口はどこでも通る）。"""
    if dest != "hand" or s.over:
        return None
    p = s.P[i]
    if not any(x in p.hand for x in SBACK):
        return None
    if not _demonio(BY_KEY[k]):
        return None
    r = _sback_pick(s, i, [k])
    if r is None:
        return None
    _, sk = r
    s.ev(f"　S・バック：{BY_KEY[k].name} を捨てて {BY_KEY[sk].name} をコストを支払わずにプレイ")
    _sback_play(s, i, sk)
    return "grave"


def _shield_to_hand(s, i, what):
    """自分のシールドを1つ手札に加える（そのS・トリガーは使えない）。

    デモニオ・カードのシールドなら、S・バック（rep_sback）が得な時に自動で割り込む。"""
    p = s.P[i]
    if not p.sh:
        return
    dem = [j for j in _face_down(s, i)
           if _demonio(BY_KEY[p.sh[j][0]]) and _sback_pick(s, i, [p.sh[j][0]]) is not None]
    j = min(dem, key=lambda x: E.PRI[p.sh[x][0]]) if dem else _best_face_down(s, i)
    if j is None:
        return
    nm = BY_KEY[p.sh[j][0]].name
    r = s.take_shield(i, j, "hand")
    if r is not None and r[2] == "hand":
        s.ev(f"　{what}：シールドの {nm} を手札へ（S・トリガーは使えない）")


# ================================================================ 邪眼神オール（49/89）
def e_jaganall(s, i, u):
    """出た時、カードを3枚引き、自分の手札を2枚捨てる"""
    s.draw(i, 3)
    for _ in range(2):
        discard_choice(s, i)


add("k43_jaganall", "邪眼神オール", 3, "WDF", power=4000,
    races=("godgard", "angelcommand", "demoncommand", "command"), pri=5, roles="draw atk",
    enter=e_jaganall, brkx=bx_powered, godlink=("C", ()),
    freeacts=fa_link43, actapply={"x:k43link": ap_link43}, enterwatch=ew_link43,
    text="パワード・ブレイカー（そのパワー6000ごとにシールドをもう1つブレイクする。素のパワー4000なので"
         "ふつうは1つ）。このクリーチャーが出た時、カードを3枚引き、自分の手札を2枚捨てる"
         "（いちばん要らない札から捨てる）。"
         "中央G・リンク（これまたは自分の他のゴッドが出る時、各ゴッドからリンクしているカードを1枚まで外し、"
         "「右G・リンク」または「左G・リンク」を持つゴッドにリンクしてもよい。"
         "リンクしたゴッドはパワーも能力も併せ持つ1体のクリーチャーになり、離れる時は1枚だけが離れる）。"
         "パワーの表記は4000+で、リンクすると合計パワーになる",
    note="", status="full", source=SRC["k43_jaganall"])


# ================================================================ ドンドン火噴くナウ（50/89）
def sp_dondon(s, i):
    """山札の上から3枚を見て、1枚をマナ、1枚を手札、1枚を墓地に置く。
    墓地に置いたカード以下のコストの相手のクリーチャー1体を破壊する"""
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    # どれを墓地に置くか：そのコストで破壊できる相手のクリーチャーがいちばん大事なものを選ぶ
    board = opp_all(s, i)
    best, bv = None, None
    for k in top:
        hit = [z for z in board if z.c.cost <= BY_KEY[k].cost]
        v = (max((s.val(z) for z in hit), default=-1), -E.PRI[k])
        if bv is None or v > bv:
            best, bv = k, v
    top.remove(best)
    s.grave_put(i, best)
    s.ev(f"　ドンドン火噴くナウ：{BY_KEY[best].name} を墓地に置く（コスト{BY_KEY[best].cost}以下を破壊）")
    if top:
        h = max(top, key=lambda k: E.PRI[k])
        top.remove(h)
        p.hand.append(h)
        s.ev(f"　ドンドン火噴くナウ：{BY_KEY[h].name} を手札へ")
    for k in top:
        s.add_mana(i, k, src="deck")
    t = s.target(i, lambda z, c=BY_KEY[best].cost: z.c.cost <= c)
    if t is None:
        return
    destroy(s, i, t)


add("k43_dondon", "ドンドン火噴くナウ", 5, "WFN", kind="S", trig=True, pri=6, roles="trg rem acc draw",
    spell=sp_dondon,
    text="S・トリガー。自分の山札の上から3枚を見る。その中から1枚をマナゾーンに置き、1枚を手札に加え、"
         "残りの1枚を墓地に置く。こうして墓地に置いたカード以下のコストの相手のクリーチャーを1体選び、破壊する。"
         "どの1枚を墓地に置くかは、そのコストで取り除ける相手のクリーチャーの重要度がいちばん高くなるように"
         "選び、残りのうち重要度の高いほうを手札に加える（全デッキ共通の決まり）",
    source=SRC["k43_dondon"])


# ================================================================ 鬼核アトム・ジャオウガ（51/89）
def e_kikaku(s, i, u):
    """出た時、自分のシールドを1つ手札に加えてもよい（S・トリガーは使えない）。
    その後、カードを1枚、自分の墓地からマナゾーンに置く"""
    p = s.P[i]
    if len(p.sh) >= 2:                      # シールドは1つは残す（全デッキ共通の決まり）
        _shield_to_hand(s, i, "鬼核アトム・ジャオウガ")
    if s.over or not p.grave:
        return
    k = max(p.grave, key=lambda x: E.PRI[x])
    p.grave.remove(k)
    s.add_mana(i, k, src="grave")
    s.ev(f"　鬼核アトム・ジャオウガ：墓地の {BY_KEY[k].name} をマナゾーンへ")


def gs_kikaku(s, di, k):
    """ハイパーモード中、自分のシールドゾーンにあるデモニオ・カードすべてにG・ストライクを与える"""
    if not _demonio(BY_KEY[k]):
        return False
    return any(z.k == "k43_kikaku" and z.hyper for z in s.P[di].board)


E.HYPER_POW["k43_kikaku"] = 4000           # ハイパーモード 8000
E.HYPER_BRK["k43_kikaku"] = 2              # ハイパーモード中はW・ブレイカー

add("k43_kikaku", "鬼核アトム・ジャオウガ", 3, "DFN", power=4000, sa=True, gs=True, zrush=True,
    races=("demonio", "onirexstars"), pri=6, roles="atk acc trg fin",
    enter=e_kikaku, gsok=gs_kikaku,
    text="G・ストライク。スピードアタッカー。"
         "このクリーチャーが出た時、自分のシールドを1つ手札に加えてもよい（その「S・トリガー」は使えない。"
         "シールドが2つ以上ある時に、重要度のいちばん高い裏向きのシールドを加える）。"
         "その後、カードを1枚、自分の墓地からマナゾーンに置く。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモードを解放する）。"
         "ハイパーモード中はパワー8000、W・ブレイカーになり、"
         "自分のシールドゾーンにあるデモニオ・カードすべてに「G・ストライク」を与える",
    source=SRC["k43_kikaku"])


# ================================================================ カイザー・ルピア（52/89）
def _has_up_shield(s, i):
    return any(up for (_, up) in s.P[i].sh)


def e_kaizerlupia(s, i, u):
    """出た時、自分のシールドゾーンにあるカードを1枚表向きにしてもよい

    表向きのシールドはこのシミュレーターでは先にブレイクされ、ブレイクされてもS・トリガーが
    使えないので、表向きの札がまだ無い時だけ、いちばん惜しくない裏向きのシールドを表にする。"""
    p = s.P[i]
    if _has_up_shield(s, i):
        return                              # もう表向きの札があるので、軽減は増えない
    cands = [j for j in _face_down(s, i) if BY_KEY[p.sh[j][0]].kind != "G"]
    if not cands:
        return
    j = min(cands, key=lambda x: (1 if _trigish(BY_KEY[p.sh[x][0]]) else 0, E.PRI[p.sh[x][0]]))
    k = p.sh[j][0]
    s.flip_shield(i, j, True)
    s.ev(f"　カイザー・ルピア：シールドの {BY_KEY[k].name} を表向きにした")


def _trigish(c):
    """S・トリガーかG・ストライクを持つ札か（表向きにすると損をするので後回しにする）"""
    return c.trig or c.gs or bool(c.twin and c.twin[2])


def _kaizer_cut(s, i, k):
    """カイザー・ルピア1枚あたりの軽減ぶん（アーマード・ドラゴン・カードでなければ0）"""
    n = sum(1 for z in s.P[i].board if z.k == "k43_kaizerlupia")
    if not n or "armoreddragon" not in BY_KEY[k].races:
        return 0
    return n * (2 if _has_up_shield(s, i) else 1)


def ca_kaizerlupia(s, i, k, cur):
    """自分のアーマード・ドラゴン・カードのコストを1少なくする。
    自分のシールドゾーンに表向きのカードがあれば、追加で1少なくする（0以下にはならない）"""
    if cur <= 1:
        return cur
    return max(1, cur - _kaizer_cut(s, i, k))


def sa_kaizerlupia(s, i, k, twin=False):
    """同じ軽減を、呪文・タマシード・城・クロスギア（spcost を通るカード）にも効かせる。
    1より小さくならないよう、減らせるぶんだけを返す。
    ツインパクトの呪文側を使うときは、呪文側のコストで見る。"""
    cut = _kaizer_cut(s, i, k)
    if not cut:
        return 0
    c = BY_KEY[k]
    cost = c.twin[0] if twin else c.cost
    return -min(cut, max(0, cost - 1))


add("k43_kaizerlupia", "カイザー・ルピア", 2, "L", power=1000,
    races=("armoredfirebird", "firebird", "armored"), pri=3, roles="acc",
    enter=e_kaizerlupia, costaura=ca_kaizerlupia, spcostaura=sa_kaizerlupia,
    text="このクリーチャーが出た時、自分のシールドゾーンにあるカードを1枚表向きにしてもよい"
         "（表向きの札がまだ無い時に、S・トリガーを持たない、いちばん惜しくない裏向きのシールドを表にする）。"
         "自分のアーマード・ドラゴン・カードのコストを1少なくする。"
         "自分のシールドゾーンに表向きのカードがあれば、追加で1少なくする。"
         "ただし、コストは0以下にはならない",
    status="full", source=SRC["k43_kaizerlupia"])


# ================================================================ 邪眼右神デリート（53/89）
def w_delete(s, i, u):
    """相手のクリーチャーが出た時、そのターン、そのクリーチャーは攻撃できない。
    コストを支払わずに出ていたら、自分はカードを1枚引いてもよい"""
    if u.c.kind != "C":
        return
    d = 1 - i                               # デリートの持ち主
    n = _ncopy(s, d, "k43_delete")
    if not n:
        return
    u.x["k43_noatk"] = s.turn
    s.ev(f"　邪眼右神デリート：{u.c.name} はこのターン攻撃できない")
    if not u.x.get("summoned"):
        s.draw(d, n)


add("k43_delete", "邪眼右神デリート", 3, "W", power=3000,
    races=("godgard", "poseidia", "dragon"), pri=4, roles="dis draw",
    enterwatch=w_delete, atklock=lambda s, i, u: u.x.get("k43_noatk", -1) == s.turn,
    godlink=("R", ()),
    text="相手のクリーチャーが出た時、そのターン、そのクリーチャーは攻撃できない。"
         "そのクリーチャーがコストを支払わずに出ていたら、自分はカードを1枚引いてもよい（引く）。"
         "右G・リンク（「中央G・リンク」または「左G・リンク」を持つゴッドの右側にリンクしてもよい）。"
         "パワーの表記は3000+で、リンクすると合計パワーになる",
    note="「コストを支払わずに出ていたら」は、エンジンに「コストを支払ったか」を持つ場所が無いので、"
         "**召喚ではなく効果で出た**クリーチャー（踏み倒し）を、支払っていないものとして見ている。"
         "ムゲンクライムやアビスラッシュのように「召喚だがコストが軽い」ものは引けない",
    status="partial", source=SRC["k43_delete"])


# ================================================================ プロジェクト・ゴッド（54/89）
def sp_projectgod(s, i):
    """山札の上から5枚を墓地に置く。その中から、バトルゾーンにある自分のゴッドとリンクできる
    ゴッドを好きな数リンクして出す（リンクできないゴッドは出せない）"""
    p = s.P[i]
    got = s.mill(i, 5)
    if not got:
        return
    for k in sorted(got, key=lambda x: -E.PRI[x]):
        if s.over or k not in p.grave:
            continue
        c = BY_KEY[k]
        if not (_plain_cre(c) and _is_god(c)):
            continue
        if _link_base(s, i, k) is None:
            continue                        # リンクできる相手のゴッドがいない
        if s.fate(i, k, "grave", False) != "ok":
            continue
        p.grave.remove(k)
        s.ev(f"　プロジェクト・ゴッド：{c.name} を出してリンクする")
        s.enter(i, k, "grave", False)       # 出た時に ew_link43 がリンクする


add("k43_projectgod", "プロジェクト・ゴッド", 4, "W", kind="S", pri=5, roles="acc fin",
    spell=sp_projectgod,
    text="自分の山札の上から5枚を墓地に置く。その中から、バトルゾーンにある自分のゴッドとリンクできる"
         "ゴッドを、好きな数リンクして出してもよい（出せるゴッドは重要度の高いものから全部出す）",
    note="進化ゴッドは進化元が要るので、この効果では出せない",
    status="full", source=SRC["k43_projectgod"])


# ================================================================ 邪眼龍神ヘヴィ・アポロヌス（58/89）
SLAYER.add("k43_heavyapollonus")

add("k43_heavyapollonus", "邪眼龍神ヘヴィ・アポロヌス", 5, "D", power=5000, trig=True, blocker=True,
    races=("godgard", "dragonzombie", "tyranodrake"), pri=7, roles="trg blk rem",
    godlink=("L", ()),
    text="S・トリガー。ブロッカー。スレイヤー（バトルする時、バトルの後、相手クリーチャーを破壊する）。"
         "左G・リンク・ガルド（《龍神メタル》《破壊神デス》、または「中央G・リンク」か「右G・リンク」を"
         "持つゴッドの左側にリンクしてもよい。リンクしたゴッドはパワーも能力も併せ持つ1体のクリーチャーになる）。"
         "パワーの表記は5000+で、リンクすると合計パワーになる",
    note="リンク相手の《龍神メタル》《破壊神デス》はこのカードプールに無いので、"
         "「中央G・リンク」「右G・リンク」を持つゴッドにだけリンクする",
    status="full", source=SRC["k43_heavyapollonus"])


# ================================================================ レーホウ・衛・デカッチ（59/89）
def sp_dekacchi(s, i):
    """呪文側「暴竜爵様のお出ましだッチ!」：山札の上から4枚を見て、ドラゴンかファイアー・バードの
    カード1枚を手札に加えてもよい。残りを好きな順序で山札の上か下に置く"""
    s.dig(i, 4, lambda k: _is_dragonish(BY_KEY[k]) or _is_firebird(BY_KEY[k]))


def d_dekacchi(s, i, u):
    """破壊された時、自分のドラゴンをすべてアンタップする"""
    n = 0
    for z in s.P[i].board:
        if z.c.kind == "C" and z.tap and _is_dragonish(z.c):
            z.tap = False
            n += 1
    if n:
        s.ev(f"　レーホウ・衛・デカッチ：自分のドラゴン{n}体をアンタップ")


add("k43_dekacchi", "レーホウ・衛・デカッチ / 「暴竜爵様のお出ましだッチ!」", 3, "F", power=4000,
    races=("armoredfirebird", "firebird", "armored"), twin=(2, "F", False), pri=4, roles="blk draw",
    spell=sp_dekacchi, destroyed=d_dekacchi, guard=guardman("k43_dekacchi"),
    text="クリーチャー側：ガードマン（このクリーチャーをタップして、相手クリーチャーの攻撃先を、"
         "自分の他のクリーチャーからこのクリーチャーに変更してもよい）。"
         "このクリーチャーが破壊された時、自分のドラゴンをすべてアンタップする。"
         "呪文側「暴竜爵様のお出ましだッチ!」（コスト2・火・アーマード・アーツ）："
         "自分の山札の上から4枚を見る。その中から、ドラゴン・カードまたはファイアー・バード・カードを1枚、"
         "表向きにしてから手札に加えてもよい。残りを好きな順序で山札の上か下に置く（山札の下に置く）",
    source=SRC["k43_dekacchi"])


# ================================================================ 轟速 ザ・ダラー（60/89）
def sp_thedollar(s, i):
    """呪文側：自分の手札を1枚捨て、次の中から1回選ぶ。
    (1)カードを2枚引く／(2)相手のパワー7000以下のクリーチャー1体を破壊する"""
    p = s.P[i]
    k = worst_hand(s, i, skip=("k43_thedollar",))
    if k is not None:
        s.discard(i, k)
    t = s.target(i, lambda z: s.power(1 - i, z) <= 7000)
    vd = 4 if len(p.deck) > 2 else -1
    if t is not None and s.val(t) >= vd:
        s.ev(f"　「イグニッション！ソニックドロォォォ!!」：{t.c.name} を破壊")
        destroy(s, i, t)
    elif len(p.deck) > 1:
        s.ev("　「イグニッション！ソニックドロォォォ!!」：2枚引く")
        s.draw(i, 2)
    elif t is not None:
        destroy(s, i, t)


def a_thedollar(s, i, u):
    """スマッシュ・バースト：攻撃する時、呪文側を場に置いたままコストを支払わずに唱えてもよい"""
    if not s.spell_ok(i, 2):
        return
    p = s.P[i]
    p.spl += 1
    s.first_play(i, 2)
    prev = s.spc
    s.spc = 2
    s.ev("　スマッシュ・バースト：「イグニッション！ソニックドロォォォ!!」をコストを支払わずに唱える")
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, "k43_thedollar")
    if not s.over:
        sp_thedollar(s, i)
    s.spc = prev


add("k43_thedollar", "轟速 ザ・ダラー / 「イグニッション！ソニックドロォォォ!!」", 3, "F", power=3000,
    trig=True, races=("soniccommand", "command", "invader"), twin=(2, "F", False),
    pri=5, roles="trg rem draw atk",
    spell=sp_thedollar, attack=a_thedollar,
    text="クリーチャー側：S・トリガー。"
         "スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱えてもよい）。"
         "呪文側「イグニッション！ソニックドロォォォ!!」（コスト2・火・ソニック・コマンド・ワード）："
         "自分の手札を1枚捨て、次の中から1回選ぶ。"
         "(1)カードを2枚引く／(2)相手のパワー7000以下のクリーチャーを1体選び、破壊する。"
         "どちらを選ぶかは、取り除ける相手のクリーチャーの重要度で機械的に決める（全デッキ共通の決まり）",
    note="種族に侵略者を持つが、侵略の能力は持っていない（dmwiki のカードページを2回読んで確かめた）",
    source=SRC["k43_thedollar"])


# ================================================================ 悪霊鬼王ジャオディオス（61/89）
def _jaodios_hit(s, i, u):
    """出た時または攻撃する時、相手のパワー6000以下のクリーチャー1体を破壊する"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 6000)
    if t is None:
        return
    s.ev(f"　悪霊鬼王ジャオディオス：{t.c.name} を破壊")
    destroy(s, i, t)


def ex_jaodios(s, i, u):
    """スター進化：デモニオまたは火の、クリーチャー1体の上に置く"""
    return _demonio(u.c) or "F" in u.c.civ


def pr_jaodios(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and (BY_KEY[kk].kind == "C" or kk in E.SHINKA)
            and (_demonio(BY_KEY[kk]) or "F" in BY_KEY[kk].civ))
    return None if n >= 4 else "進化元になるデモニオか火のクリーチャーが4体いない"


add("k43_jaodios", "悪霊鬼王ジャオディオス", 3, "F", power=6000, brk=2, evo="F",
    races=("demonio", "onirexstars"), pri=6, roles="rem atk fin",
    enter=_jaodios_hit, attack=_jaodios_hit, evox=ex_jaodios,
    leaverep=star_evo_rep("k43_jaodios"), shieldrep=rep_sback, playrule=pr_jaodios,
    text="S・バック：デモニオ（デモニオ・カードを自分のシールドゾーンから手札に加える時、"
         "そのカードを捨ててもよい。そうしたら、コストを支払わずにこのカードをプレイする）。"
         "スター進化：デモニオまたは火の、クリーチャー1体の上に置く"
         "（離れる時は、一番上のこのカードだけが離れ、下のカードがバトルゾーンに残る）。"
         "W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、相手のパワー6000以下のクリーチャーを1体選び、破壊する",
    note="S・バックで捨てるのは手札に加わるはずだったそのカードなので、"
         "そのカードよりこのカードの重要度が高い時だけ使う（全デッキ共通の決まり）。"
         "envtest の effect_smoke は「使えた場面 0」になるが、これは試験の決まった場面に"
         "進化元になるデモニオか火のクリーチャーが1体もいないためで、"
         "進化元を置いた場面では進化・退化・出た時の破壊・S・バックのすべてが動くことを確かめた",
    status="full", source=SRC["k43_jaodios"])


# ================================================================ 極限龍神メタル（62/89）
def e_metal(s, i, u):
    """出た時、相手のマナゾーンからカードを1枚と、バトルゾーンにある相手のクリーチャーではない
    カードを1枚選び、持ち主の墓地に置いてもよい"""
    o = s.P[1 - i]
    if o.mana:
        k = max(o.mana, key=lambda x: E.PRI[x])
        s.take_mana(1 - i, k)
        s.grave_put(1 - i, k)
        s.ev(f"　極限龍神メタル：相手のマナの {BY_KEY[k].name} を墓地へ")
    t = s.target(i, kinds="TX")
    if t is None:
        return
    s.ev(f"　極限龍神メタル：相手の {t.c.name} を墓地へ")
    move(s, i, t, "grave")


add("k43_metal", "極限龍神メタル", 6, "F", power=7000,
    races=("godnovaomg", "armoreddragon", "armored", "dragon"), pri=8, roles="rem dis fin",
    enter=e_metal, brkx=bx_powered, godlink=("R", ()),
    text="パワード・ブレイカー（そのパワー6000ごとにシールドをもう1つブレイクする。"
         "素のパワー7000なので2つ）。"
         "このクリーチャーが出た時、相手のマナゾーンからカードを1枚と、"
         "バトルゾーンにある相手の、クリーチャーではないカードを1枚選び、持ち主の墓地に置いてもよい"
         "（それぞれ重要度のいちばん高いものを選ぶ）。"
         "右G・リンクOMG（《龍神ヘヴィ》《破壊神デス》、または「中央G・リンク」か「左G・リンク」を"
         "持つゴッドの右側にリンクしてもよい。リンクしたゴッドはパワーも能力も併せ持つ1体のクリーチャーになる）。"
         "パワーの表記は7000+で、リンクすると合計パワーになる",
    note="リンク相手の《龍神ヘヴィ》《破壊神デス》はこのカードプールに無いので、"
         "「中央G・リンク」「左G・リンク」を持つゴッドにだけリンクする",
    status="full", source=SRC["k43_metal"])


# ================================================================ シブキ将鬼の巻（63/89）
def e_shibuki(s, i, u):
    """出た時、自分のシールドを1つ手札に加える（S・トリガーは使えない）"""
    _shield_to_hand(s, i, "シブキ将鬼の巻")


E.SHINKA.add("k43_shibuki")
E.STAY.add("k43_shibuki")

add("k43_shibuki", "シブキ将鬼の巻", 2, "F", kind="T", races=("demonio", "onirexstars"),
    pri=3, roles="draw acc",
    enter=e_shibuki,
    text="シンカライズ（このタマシードがクリーチャーであるかのように、この上に進化クリーチャーを置いてもよい）。"
         "このタマシードが出た時、自分のシールドを1つ手札に加える"
         "（ただし、その「S・トリガー」は使えない。重要度のいちばん高い裏向きのシールドを加える）",
    source=SRC["k43_shibuki"])


# ================================================================ Dの侵略 クリム・ゾーン（64/89）
D2 = ("k43_crimzone",)         # このモジュールで実装したD2フィールド


def e_crimzone(s, i, u):
    """D2フィールドの決まり：他のD2フィールドが出た時、先にあったD2フィールドは墓地に置かれる"""
    p = s.P[i]
    for z in p.board[:]:
        if z is not u and z.k in D2:
            s.ev(f"　D2フィールドの決まり：{z.c.name} を自分の墓地に置く")
            s.leave(i, z, "grave")


def t_crimzone(s, i, u):
    """自分のターンのはじめに、自分の手札からソニック・コマンドを1体出してもよい"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or "soniccommand" not in c.races:
            continue
        if c.evo and not c.neo and s.evo_src(i, k) is None:
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return
    c = BY_KEY[best]
    on = s.evo_src(i, best) if (c.evo and not c.neo) else None
    p.hand.remove(best)
    s.ev(f"　Dの侵略 クリム・ゾーン：手札から {c.name} を出す")
    s.enter(i, best, "hand", False, on=on)


def rep_crimzone(s, i, u, dest, destroy_):
    """自分のソニック・コマンドはバトルゾーンから手札に戻らない"""
    if dest != "hand" or u.c.kind != "C" or "soniccommand" not in u.c.races:
        return False
    return s.has(i, "k43_crimzone")


E.STAY.add("k43_crimzone")

add("k43_crimzone", "Dの侵略 クリム・ゾーン", 3, "F", kind="T", pri=4, roles="acc dis",
    enter=e_crimzone, tstart=t_crimzone, leaverep=rep_crimzone,
    text="D2フィールド（バトルゾーンに出て残るカード。このシミュレーターではタマシードとして扱う）。"
         "自分のターンのはじめに、自分の手札からソニック・コマンドを1体出してもよい"
         "（重要度のいちばん高いものを出す）。"
         "自分のソニック・コマンドはバトルゾーンから手札に戻らない。"
         "他のD2フィールドが出た時、このD2フィールドを自分の墓地に置く",
    note="D2フィールドはこのシミュレーターに無いゾーンなので、"
         "場に残るカード＝タマシードで表している（env26 の《Dの機動 ヴァイス・ヴァーチュー》と同じ）。"
         "そのため、タマシードを対象にする効果で取り除かれてしまう",
    status="partial", source=SRC["k43_crimzone"])


# ================================================================ バクロ法師の封（65/89）
def e_bakuro(s, i, u):
    """出た時、自分のシールドゾーンにあるカードを1枚マナゾーンに置く。そうしたら、自分のマナゾーンに
    あるカードの枚数以下のコストの進化デモニオ・クリーチャーを1体、自分のマナゾーンから出す"""
    p = s.P[i]
    if not p.sh:
        return
    cands = _face_down(s, i)
    j = (min(cands, key=lambda x: E.PRI[p.sh[x][0]]) if cands else len(p.sh) - 1)
    r = s.take_shield(i, j, "mana")
    if r is None:
        return
    s.ev(f"　バクロ法師の封：シールドの {BY_KEY[r[0]].name} をマナゾーンへ")
    n = len(p.mana)
    best, bv = None, -1
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if c.kind != "C" or not c.evo or c.cost > n or not _demonio(c):
            continue
        if not c.neo and s.evo_src(i, k) is None:
            continue
        if E.PRI[k] > bv and s.fate(i, k, "mana", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return
    c = BY_KEY[best]
    on = s.evo_src(i, best) if not c.neo else None
    s.take_mana(i, best)
    s.ev(f"　バクロ法師の封：マナから {c.name} を出す")
    s.enter(i, best, "mana", False, on=on)


E.SHINKA.add("k43_bakuro")
E.STAY.add("k43_bakuro")

add("k43_bakuro", "バクロ法師の封", 4, "N", kind="T", races=("demonio", "onirexstars"),
    pri=5, roles="acc fin",
    enter=e_bakuro, shieldrep=rep_sback,
    text="S・バック：デモニオ（デモニオ・カードを自分のシールドゾーンから手札に加える時、"
         "そのカードを捨ててもよい。そうしたら、コストを支払わずにこのカードをプレイする）。"
         "シンカライズ（このタマシードがクリーチャーであるかのように、この上に進化クリーチャーを置いてもよい）。"
         "このタマシードが出た時、自分のシールドゾーンにあるカードを1枚マナゾーンに置く"
         "（いちばん惜しくない裏向きのシールドを置く）。そうしたら、自分のマナゾーンにあるカードの枚数以下の"
         "コストの進化デモニオ・クリーチャーを1体、自分のマナゾーンから出す",
    note="S・バックで捨てるのは手札に加わるはずだったそのカードなので、"
         "そのカードよりこのタマシードの重要度が高い時だけ使う（全デッキ共通の決まり）",
    status="full", source=SRC["k43_bakuro"])


# ================================================================ ボルシャック・マントラ（67/89）
def e_mantra(s, i, u):
    """出た時、クリーチャーを3体まで選び、タップする。
    その後、相手のタップしているクリーチャー1体につき、カードを1枚引く"""
    o = s.P[1 - i]
    for _ in range(3):
        t = s.target(i, lambda z: not z.tap)
        if t is None:
            break
        s.ev(f"　ボルシャック・マントラ：{t.c.name} をタップ")
        s.tap_cre(1 - i, t)
    n = sum(1 for z in o.board if z.c.kind == "C" and z.tap)
    if n:
        s.draw(i, n)


E.HYPER_POW["k43_mantra"] = 4000           # ハイパーモード 8500
E.HYPER_BRK["k43_mantra"] = 2              # ハイパーモード中はW・ブレイカー

add("k43_mantra", "ボルシャック・マントラ", 7, "LW", power=4500, trig=True, zrush=True,
    races=("mecha", "armoreddragon", "armored", "dragon", "shinobi", "hyperbeast"),
    pri=8, roles="trg draw dis blk",
    enter=e_mantra,
    blockok=lambda s, u: u.k == "k43_mantra" and u.hyper,
    text="S・トリガー。"
         "このクリーチャーが出た時、クリーチャーを3体まで選び、タップする"
         "（相手のアンタップしているクリーチャーのうち重要度の高いものから選ぶ）。"
         "その後、相手のタップしているクリーチャー1体につき、カードを1枚引く。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモードを解放する）。"
         "ハイパーモード中はパワー8500になり、ブロッカーとW・ブレイカーを得る",
    source=SRC["k43_mantra"])
