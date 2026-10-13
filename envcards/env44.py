"""担当44：DM26-EX2「悪感謝祭 カリスマBEST」の未実装カード15枚

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ
      （https://dmwiki.net/《カード名》）と生の wiki ソース（?plugin=template&refer=《カード名》）を
      別の質問で2回ずつ（《ワダゲコノミコト》《鶏と蛙 ケローラ＆ルピア》《樹界の守護車 アイオン・ユピテル》は
      数字か本文が1回しか読めなかったので3回）読み、コスト・文明・種類・種族・パワー・ブレイク数・
      能力本文が2回とも一致することを確かめた。

  この札束に入っている仕組み
    ・**ミズガミ／ロスト・クルセイダー**の3枚（ワダウザ／ワダフミ／ワダゲコ）。
      env4 の《ワダチエノミコト》たちと同じ族で、《ワダシストノミコト》のコスト軽減が
      代替コストにもかかる（`costaura` を自分で通して計算している）。
    ・**マナ進化**（超轟速 レッドランチャー）。`evosrc=` でマナゾーンの火／自然のクリーチャーを
      進化元にする。破壊される時は墓地ではなくマナゾーンへ（`leavedest=`）。
    ・**Zラッシュ＋ハイパーモード**（鶏と蛙 ケローラ＆ルピア／鬼覇 ザ＝デッドジャオウガ）。
      生の wiki ソースの `BGCOLOR(#cde):|c|` の位置で「どこからがハイパーモード中だけか」を確かめた。
      どちらも**W・ブレイカーがハイパーモード中だけ**なので、素の brk は1。
    ・**「可能ならこのクリーチャーを攻撃しなければならない」**（鬼覇 ザ＝デッドジャオウガのハイパーモード）。
      `mustatktgt=` で攻撃先をその1体に縛る。エンジンが「自分より強いクリーチャーへの攻撃」を
      手の一覧に出さないぶんは、`atktargetlock=`／`noatkplock=` で「ほかを攻撃できない」の形に落としている。
      「可能なら」は、鬼覇がタップしているか相手がマッハファイターで攻撃できる時だけ縛る
      （パワーの大小は見ない）。
    ・**墓地からの回収＋同じ種族の進化クリーチャーの踏み倒し**（魔光蟲ヴィルジニア卿）。
    ・**G・リンク**（邪眼右神C・ロマノフ＝右／邪眼左神M・ロマノフ＝左）。`godlink=` で位置を宣言し、
      つなぐ操作は `freeacts=`／`actapply=` の追加の手（`s.can_link`／`s.god_link`）で出す。
      位置（左・中央・右）が重ならない組み合わせだけつなげられる。2枚つなぐとパワー5000の1体になる。
    ・**シールドを自分で減らす**（鬼火の守護者ジャオウガ・メルキス／鬼覇 ザ＝デッドジャオウガ）。
      `s.take_shield` を通すので、シールドが離れたことで Zラッシュがちゃんと誘発する。

  調べ直して意外だった点
    ・《ワダゲコノミコト》は**コスト1なのに「水(3)支払って召喚してもよい」という“高い”代替コスト**を持つ。
      高く払うと「出た時、自分のクリーチャー1体を手札に戻す」が付き、自分自身を戻せば
      「離れた時」（相手1体を凍らせる）を使い回せる、という使い方のための能力だった（2回の読みとも同じ）。
    ・《轟速 ザ・ジオ》は火ではなく**自然**（ソニック・コマンド／侵略者、パワー7000）。
      呪文側《「キサマのデュエマは周回遅れだ！」》はコスト1で、山札の上5枚から**進化クリーチャー**を回収する。
    ・《超轟速 レッドランチャー》は侵略ではなく**マナ進化**のクリーチャー。
    ・《魔光蟲ヴィルジニア卿》は2011年に殿堂入りしたが**2020年1月1日に殿堂解除**されていて、
      いまは枚数制限なし（note に書いた）。この弾の15枚に殿堂入りのカードは1枚も無かった。
    ・《鶏と蛙 ケローラ＆ルピア》の素のパワーは4000で、**W・ブレイカーも除去もハイパーモード中だけ**。
      素の状態はただのコスト3スピードアタッカー（火単色なので革命チェンジ元に向く）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy
from envcards.env0 import lock_until_my_turn, worst_own

W = "https://dmwiki.net/"
LOST = "lostcrusader"
SRC = {
    "k44_wadauza": W + "《ワダウザノミコト》",
    "k44_redlauncher": W + "《超轟速 レッドランチャー》",
    "k44_logic": W + "《ロジック・サークル》",
    "k44_leopold": W + "《氷牙レオポル・ディーネ公》",
    "k44_hakofu": W + "《水面護り ハコフ／蓄積された魔力の縛り》",
    "k44_wadafumi": W + "《ワダフミノミコト》",
    "k44_wadageko": W + "《ワダゲコノミコト》",
    "k44_virginia": W + "《魔光蟲ヴィルジニア卿》",
    "k44_cromanov": W + "《邪眼右神C・ロマノフ》",
    "k44_melkis": W + "《鬼火の守護者ジャオウガ・メルキス》",
    "k44_kerola": W + "《鶏と蛙 ケローラ＆ルピア》",
    "k44_mromanov": W + "《邪眼左神M・ロマノフ》",
    "k44_thegio": W + "《轟速 ザ・ジオ／「キサマのデュエマは周回遅れだ！」》",
    "k44_deadjaouga": W + "《鬼覇 ザ＝デッドジャオウガ》",
    "k44_aionjupiter": W + "《樹界の守護車 アイオン・ユピテル》",
}


# ---------------------------------------------------------------- G・リンク（共通の道具）
# ゴッドを横につないで1体のクリーチャーとして扱う。パワーは合計、能力と文明は併せ持ち、
# 離れる時は構成しているカードのうち1枚だけが離れる（エンジンの `parts`／`god_link` が面倒を見る）。
# つなぐ操作は「自分のメインステップ中の追加の手」として出す（エンジンの決まり）。
# 位置（左 L・中央 C・右 R）が重ならない組み合わせだけつなげられる
# （「左G・リンク」は「中央」か「右」を持つゴッドの左にしか付けない、という決まりをこれで表している）。
_GL_KEYS = frozenset(("k44_cromanov", "k44_mromanov"))
_GL_ACT = "x:k44_glink"


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
def _worst_face_down(s, i):
    """自分のシールドのうち、自分で減らすならいちばん惜しくない裏向きのシールドの番号"""
    p = s.P[i]
    cands = [j for j, (k, up) in enumerate(p.sh) if not up]
    if not cands:
        return len(p.sh) - 1 if p.sh else None
    return min(cands, key=lambda x: E.PRI[p.sh[x][0]])


def _best_face_down(s, i):
    """自分のシールドのうち、手札に加えるならいちばん嬉しい裏向きのシールドの番号"""
    p = s.P[i]
    cands = [j for j, (k, up) in enumerate(p.sh) if not up]
    if not cands:
        return len(p.sh) - 1 if p.sh else None
    return max(cands, key=lambda x: E.PRI[p.sh[x][0]])


def _mf(s, i, u):
    """u はいまマッハファイターとして（アンタップしている相手も）攻撃できるか"""
    if not u.sick:
        return False
    return bool(u.c.mach) or bool(E.MACHOK and any(f(s, i, u) for f in E.MACHOK))


# ================================================================ 1. ワダウザノミコト
def bd_wadauza(s, i, b, a):
    """このクリーチャーがブロックした時、このクリーチャーと攻撃しているクリーチャーを、
    それぞれ持ち主の手札に戻す（バトルする前に両方とも戻る）"""
    if a not in s.P[1 - i].board:
        return
    s.ev("　ワダウザノミコト：ブロックしたので、攻撃クリーチャーと自身をそれぞれ持ち主の手札に戻す")
    s.leave(1 - i, a, "hand", by_opp=True)
    if b in s.P[i].board:
        s.leave(i, b, "hand")


def lf_wadauza(s, i, u, dest):
    """離れた時、自分の山札の上から4枚を見て1枚を手札に加え、残りは山札の下に置く"""
    s.dig(i, 4, lambda k: True, "bottom")


add("k44_wadauza", "ワダウザノミコト", 4, "LW", power=1000, blocker=True, trig=True,
    races=("mizugami", LOST), pri=6, roles="blk trg rem draw",
    blockdone=bd_wadauza, left=lf_wadauza,
    text="S・トリガー。ブロッカー。"
         "このクリーチャーがブロックした時、このクリーチャーと攻撃しているクリーチャーを、"
         "それぞれ持ち主の手札に戻す（バトルする前に両方とも戻る）。"
         "このクリーチャーが離れた時、自分の山札の上から4枚を見て、その中から1枚を手札に加え、"
         "残りを好きな順序で山札の上か下に置く"
         "（残る3枚は、全デッキ共通の決まりで山札の下に置く）",
    source=SRC["k44_wadauza"])


# ================================================================ 2. 超轟速 レッドランチャー
def es_redlauncher(s, i):
    """マナ進化：自分のマナゾーンの火または自然のクリーチャー1体を進化元にする"""
    cands = [k for k in s.P[i].mana
             if BY_KEY[k].kind == "C" and (set("FN") & set(BY_KEY[k].civ))]
    if not cands:
        return None
    return ("mana", min(cands, key=E.PRI.get))      # いちばん安いマナを進化元にする


def ld_redlauncher(s, i, u, dest, destroy_):
    """このクリーチャーが破壊される時、墓地に置くかわりにマナゾーンに置く"""
    if u.k != "k44_redlauncher" or not destroy_ or dest != "grave":
        return None
    return "mana"


def pr_redlauncher(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and (set("FN") & set(BY_KEY[kk].civ)))
    return None if n >= 6 else "マナ進化の元になる火か自然のクリーチャーが6体いない"


add("k44_redlauncher", "超轟速 レッドランチャー", 4, "FN", power=8000, brk=2, mach=True, evo="mana",
    races=("soniccommand", "command", "invader"), pri=9, roles="rem atk fin",
    evosrc=es_redlauncher, evox=lambda s, i, u: False, leavedest=ld_redlauncher,
    playrule=pr_redlauncher,
    text="マナ進化：自分のマナゾーンにある火または自然のクリーチャー1体の上に重ねつつ出す"
         "（マナにそれがなければ召喚できない。いちばん安いものを進化元にする）。"
         "マッハファイター。W・ブレイカー。"
         "このクリーチャーが破壊される時、墓地に置くかわりにマナゾーンに置く",
    note="破壊をマナ置きに差し替えると、エンジンは下に敷いた進化元もいっしょにマナゾーンへ送る"
         "（本来は進化元だけ墓地に行くと解釈できる）。マナの枚数が1枚ぶん多くなるだけの差",
    source=SRC["k44_redlauncher"])


# ================================================================ 3. ロジック・サークル
def sp_logic(s, i):
    """自分の山札を見て、呪文を1枚選び山札の一番上に置く（シャッフルは山札の順が関係ないので省く）"""
    p = s.P[i]
    cands = [k for k in p.deck if BY_KEY[k].kind == "S" or BY_KEY[k].twin]
    if not cands:
        return
    k = max(cands, key=E.PRI.get)
    p.deck.remove(k)
    s.put_zone(i, k, "decktop")
    s.ev(f"　ロジック・サークル：{BY_KEY[k].name} を山札の一番上に置いた")


add("k44_logic", "ロジック・サークル", 1, "L", kind="S", trig=True, pri=4, roles="trg draw",
    spell=sp_logic,
    text="S・トリガー。自分の山札を見て、その中から呪文を1枚選び、相手に見せる。"
         "その後、山札をシャッフルして、選んだ呪文を山札の一番上に置く"
         "（重要度のいちばん高い呪文を選ぶ。ツインパクトのカードも呪文として選べる）",
    source=SRC["k44_logic"])


# ================================================================ 4. 氷牙レオポル・ディーネ公
def sw_leopold(s, i, k):
    """自分が呪文を唱えた時、1枚引いてもよい（場にいる数だけ引く）"""
    n = sum(1 for z in s.P[i].board if z.k == "k44_leopold")
    for _ in range(n):
        if s.over:
            return
        s.draw(i)


add("k44_leopold", "氷牙レオポル・ディーネ公", 4, "W", power=2000, races=("cyberv", "knight"),
    pri=6, roles="draw", spellwatch=sw_leopold,
    text="自分が呪文を唱えた時、カードを1枚引いてもよい"
         "（唱えた時点でバトルゾーンにいる数だけ引く。引けるなら必ず引く）",
    source=SRC["k44_leopold"])


# ================================================================ 5. 水面護り ハコフ／蓄積された魔力の縛り
def sp_hakofu(s, i):
    """相手のクリーチャーを2体まで選び、次の自分のターンのはじめまで攻撃もブロックもできなくする"""
    got = []
    for _ in range(2):
        t = s.target(i, lambda z: all(z is not x for x in got))
        if t is None:
            return
        got.append(t)
        lock_until_my_turn(s, i, t)
        s.ev(f"　蓄積された魔力の縛り：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k44_hakofu", "水面護り ハコフ / 蓄積された魔力の縛り", 1, "W", power=2000, blocker=True, noatk=True,
    races=("mutopia",), twin=(5, "W", True), pri=4, roles="blk trg dis",
    spell=sp_hakofu,
    text="クリーチャー側《水面護り ハコフ》（コスト1・水・パワー2000）：ブロッカー。"
         "このクリーチャーは攻撃できない。"
         "呪文側《蓄積された魔力の縛り》（コスト5・水）：S・トリガー。"
         "相手のクリーチャーを2体まで選ぶ。次の自分のターンのはじめまで、"
         "それらは攻撃もブロックもできない（重要度の高い2体を選ぶ）",
    source=SRC["k44_hakofu"])


# ================================================================ 6. ワダフミノミコト
def e_wadafumi(s, i, u):
    """出た時、カードを3枚引き、その後、自分の手札を1枚選び山札の上に置く"""
    s.draw(i, 3)
    p = s.P[i]
    if s.over or not p.hand:
        return
    k = min(p.hand, key=E.PRI.get)
    p.hand.remove(k)
    s.put_zone(i, k, "decktop")
    s.ev(f"　ワダフミノミコト：手札の {BY_KEY[k].name} を山札の上に置いた")


add("k44_wadafumi", "ワダフミノミコト", 4, "W", power=4000, gs=True, races=("mizugami", LOST),
    pri=6, roles="draw trg",
    enter=e_wadafumi,
    text="G・ストライク。"
         "このクリーチャーが出た時、カードを3枚引き、その後、自分の手札を1枚選んで山札の上に置く"
         "（重要度のいちばん低い手札を置く）",
    source=SRC["k44_wadafumi"])


# ================================================================ 7. ワダゲコノミコト
def _geko_alt_cost(s, i):
    """代替コスト［水(3)］。全体のコスト軽減（ワダシストノミコトなど）はこちらにもかかる"""
    n = 3
    for f in E.COSTAURA:
        n = f(s, i, "k44_wadageko", n)
    return max(0, n)


def fa_wadageko(s, i, av, cv):
    """手札のワダゲコノミコトを、水(3)を支払って召喚する手を足す"""
    p = s.P[i]
    if "k44_wadageko" not in p.hand:
        return []
    n = _geko_alt_cost(s, i)
    if n > av or (n > 0 and "W" not in cv):
        return []
    if s.fate(i, "k44_wadageko", "hand", True) != "ok":
        return []
    return [("x:k44_geko3", n)]


def ap_wadageko(s, a):
    i = s.tp
    p = s.P[i]
    if "k44_wadageko" not in p.hand or len(p.mana) - p.mused < a[1]:
        return
    p.hand.remove("k44_wadageko")
    p.mused += a[1]
    p.x["k44_geko_alt"] = True
    s.ev(f"召喚：ワダゲコノミコト（代替コスト 水{a[1]}マナ）")
    s.enter(i, "k44_wadageko", "hand", True)
    p.x.pop("k44_geko_alt", None)


def e_wadageko(s, i, u):
    """代替コストで召喚していたら、出た時に自分のクリーチャー1体を手札に戻す"""
    p = s.P[i]
    if not p.x.pop("k44_geko_alt", False):
        return
    z = worst_own(s, i)
    if z is None:
        return
    s.ev(f"　ワダゲコノミコト：代替コストの代償に {z.c.name} を手札に戻す")
    s.leave(i, z, "hand")


def lf_wadageko(s, i, u, dest):
    """離れた時、相手のクリーチャー1体は次の自分のターンのはじめまで攻撃もブロックもできない"""
    t = s.target(i)
    if t is None:
        return
    lock_until_my_turn(s, i, t)
    s.ev(f"　ワダゲコノミコト：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k44_wadageko", "ワダゲコノミコト", 1, "W", power=2000, blocker=True, noatk=True,
    races=("mizugami", LOST), pri=5, roles="blk dis",
    enter=e_wadageko, left=lf_wadageko,
    freeacts=fa_wadageko, actapply={"x:k44_geko3": ap_wadageko},
    text="このクリーチャーを［水(3)］支払って召喚してもよい。そうしたら、このクリーチャーが出た時、"
         "自分のクリーチャーを1体選び、手札に戻す（失うのがいちばん安い自分のクリーチャーを選ぶので、"
         "多くの場合は自分自身を戻して「離れた時」を使い回す形になる）。"
         "ブロッカー。このクリーチャーは攻撃できない。"
         "このクリーチャーが離れた時、相手のクリーチャーを1体選ぶ。"
         "次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない",
    note="代替コストの［水(3)］にも全体のコスト軽減（《ワダシストノミコト》など）をかけている"
         "（dmwiki のページにもそう書いてある）",
    source=SRC["k44_wadageko"])


# ================================================================ 8. 魔光蟲ヴィルジニア卿
def e_virginia(s, i, u):
    """出た時、自分の墓地からクリーチャー1体を手札に戻す。それがこのクリーチャーと同じ種族を持つ
    進化クリーチャーなら、自分の手札からコストを支払わずに出してもよい"""
    p = s.P[i]
    cres = [k for k in sorted(set(p.grave)) if BY_KEY[k].kind == "C"]
    if not cres:
        return
    mine = set(u.c.races)

    def _same_evo(k):
        c = BY_KEY[k]
        return bool(c.evo) and bool(mine & set(c.races))

    same = [k for k in cres if _same_evo(k)]
    k = max(same, key=E.PRI.get) if same else max(cres, key=E.PRI.get)
    p.grave.remove(k)
    p.hand.append(k)
    s.ev(f"　ヴィルジニア卿：墓地の {BY_KEY[k].name} を手札に戻す")
    if not _same_evo(k) or k not in p.hand or s.over:
        return
    if s.fate(i, k, "hand", False) != "ok":
        return
    p.hand.remove(k)
    s.ev(f"　ヴィルジニア卿：同じ種族の進化クリーチャー {BY_KEY[k].name} をコストを支払わずに出す")
    s.enter(i, k, "hand", False)


add("k44_virginia", "魔光蟲ヴィルジニア卿", 5, "D", power=3000, races=("parasiteworm", "knight"),
    pri=7, roles="acc fin",
    enter=e_virginia,
    text="このクリーチャーが出た時、クリーチャー1体を自分の墓地から手札に戻す。"
         "そのクリーチャーがこのクリーチャーと同じ種族（パラサイトワームかナイト）を持つ"
         "進化クリーチャーであれば、自分の手札からコストを支払わずにバトルゾーンに出してもよい"
         "（出せる進化クリーチャーがあればそれを優先して戻し、なければ重要度のいちばん高い"
         "クリーチャーを戻す）",
    note="2011年1月15日から殿堂入りだったが、2020年1月1日に殿堂解除されたので、"
         "いまはデッキに4枚まで入れられる",
    source=SRC["k44_virginia"])


# ================================================================ 9. 邪眼右神C・ロマノフ
def e_cromanov(s, i, u):
    """出た時、自分の山札の上から2枚を墓地に置いてもよい（山札切れで負けない時だけ置く）"""
    if len(s.P[i].deck) > 3:
        s.mill(i, 2)


add("k44_cromanov", "邪眼右神C・ロマノフ", 2, "D", power=2000, gs=True,
    races=("godgard", "darklord", "knight"), pri=4, roles="trg acc",
    enter=e_cromanov, godlink=("R", ()),
    freeacts=_gl_acts, actapply={_GL_ACT: _gl_apply},
    text="G・ストライク。"
         "このクリーチャーが出た時、自分の山札の上から2枚を墓地に置いてもよい"
         "（山札が4枚以上あれば置く）。"
         "右G・リンク（「中央G・リンク」または「左G・リンク」を持つゴッドの右側にリンクしてもよい。"
         "リンクしたゴッドはパワーを合計した1体のクリーチャーになり、能力と文明を併せ持ち、"
         "離れる時はそのうち1枚だけが離れる。つなぐのは自分のメインステップ中の追加の手として行う）。"
         "パワーの表記は2000+で、《邪眼左神M・ロマノフ》とつなぐとパワー5000になる",
    source=SRC["k44_cromanov"])


# ================================================================ 10. 鬼火の守護者ジャオウガ・メルキス
def e_melkis(s, i, u):
    """出た時、自分のシールドを1つ手札に加える（そのS・トリガーは使えない）"""
    j = _best_face_down(s, i)
    if j is None:
        return
    r = s.take_shield(i, j, "hand")
    if r is not None:
        s.ev(f"　ジャオウガ・メルキス：自分のシールドの {BY_KEY[r[0]].name} を手札に加えた"
             "（S・トリガーは使えない）")


add("k44_melkis", "鬼火の守護者ジャオウガ・メルキス", 2, "D", power=1000, gs=True,
    races=("demonio", "onirexstars"), pri=4, roles="trg draw",
    enter=e_melkis,
    text="G・ストライク。"
         "このクリーチャーが出た時、自分のシールドを1つ選び、手札に加える"
         "（そのシールドのS・トリガーは使えない。重要度のいちばん高い裏向きのシールドを選ぶ）",
    source=SRC["k44_melkis"])


# ================================================================ 11. 鶏と蛙 ケローラ＆ルピア
E.HYPER_POW["k44_kerola"] = 4000          # ハイパーモード 8000／W・ブレイカー（HYPER_BRK の既定は2）


def at_kerola(s, i, u):
    """ハイパーモード中、攻撃する時、相手のコスト3以下のクリーチャー1体を選び破壊する"""
    if not u.hyper:
        return
    t = s.target(i, lambda z: z.c.cost <= 3)
    if t is None:
        return
    s.ev(f"　ケローラ＆ルピア（ハイパーモード）：{t.c.name} を破壊")
    destroy(s, i, t)


add("k44_kerola", "鶏と蛙 ケローラ＆ルピア", 3, "F", power=4000, sa=True, zrush=True,
    races=("armoreddragon", "firebird", "magicoutrage", "hyperbeast"), pri=7, roles="atk rem",
    attack=at_kerola,
    text="スピードアタッカー。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモードになる）。"
         "ハイパーモード中はパワー8000でW・ブレイカーを持ち、"
         "攻撃する時、相手のコスト3以下のクリーチャー1体を選んで破壊する"
         "（素のパワーは4000で、W・ブレイカーも破壊もハイパーモード中だけ）",
    source=SRC["k44_kerola"])


# ================================================================ 12. 邪眼左神M・ロマノフ
def e_mromanov(s, i, u):
    """出た時、相手のクリーチャー1体を選んでもよい。そのクリーチャーとこのクリーチャーをバトルする"""
    ap = s.power(i, u, True)
    t = s.target(i, lambda z: s.power(1 - i, z) < ap)       # 勝てる相手だけ選ぶ（任意の能力）
    if t is None:
        return
    s.ev(f"　M・ロマノフ：{t.c.name} とバトルする")
    s.battle(i, u, 1 - i, t)


add("k44_mromanov", "邪眼左神M・ロマノフ", 3, "F", power=3000, sa=True,
    races=("godgard", "darklord", "knight"), pri=6, roles="rem atk",
    enter=e_mromanov, godlink=("L", ()),
    freeacts=_gl_acts, actapply={_GL_ACT: _gl_apply},
    text="スピードアタッカー。"
         "このクリーチャーが出た時、相手のクリーチャーを1体選んでもよい。"
         "そのクリーチャーとこのクリーチャーをバトルする"
         "（自分が勝てる相手のうち重要度のいちばん高いクリーチャーを選び、"
         "勝てる相手がいなければバトルしない）。"
         "左G・リンク（「中央G・リンク」または「右G・リンク」を持つゴッドの左側にリンクしてもよい。"
         "リンクしたゴッドはパワーを合計した1体のクリーチャーになり、能力と文明を併せ持ち、"
         "離れる時はそのうち1枚だけが離れる。つなぐのは自分のメインステップ中の追加の手として行う）。"
         "パワーの表記は3000+で、《邪眼右神C・ロマノフ》とつなぐとパワー5000になる",
    source=SRC["k44_mromanov"])


# ================================================================ 13. 轟速 ザ・ジオ／「キサマのデュエマは周回遅れだ！」
def sp_thegio(s, i):
    """自分の山札の上から5枚を表向きにし、その中から進化クリーチャー1体を手札に加える。
    残りは好きな順序で山札の下に置く"""
    got = s.dig(i, 5, lambda k: BY_KEY[k].kind == "C" and bool(BY_KEY[k].evo), "bottom")
    if got is not None:
        s.ev(f"　キサマのデュエマは周回遅れだ！：{BY_KEY[got].name} を手札に加えた")


add("k44_thegio", "轟速 ザ・ジオ / 「キサマのデュエマは周回遅れだ！」", 4, "N", power=7000, brk=2,
    mach=True, gs=True, races=("soniccommand", "command", "invader"), twin=(1, "N", False),
    pri=8, roles="atk rem draw",
    spell=sp_thegio,
    text="クリーチャー側《轟速 ザ・ジオ》（コスト4・自然・パワー7000）：G・ストライク。"
         "マッハファイター。W・ブレイカー。"
         "呪文側《「キサマのデュエマは周回遅れだ！」》（コスト1・自然）："
         "自分の山札の上から5枚を表向きにする。その中から進化クリーチャー1体を手札に加え、"
         "残りを好きな順序で山札の下に置く（重要度のいちばん高い進化クリーチャーを選ぶ）",
    source=SRC["k44_thegio"])


# ================================================================ 14. 鬼覇 ザ＝デッドジャオウガ
E.HYPER_POW["k44_deadjaouga"] = 5000      # ハイパーモード 9000／W・ブレイカー（HYPER_BRK の既定は2）


def at_deadjaouga(s, i, u):
    """攻撃する時、自分のシールドを1つマナゾーンに置いてもよい
    （シールドが離れるので Zラッシュでハイパーモードになる。ハイパーでない時だけ払う）"""
    p = s.P[i]
    if u.hyper or len(p.sh) < 2:
        return
    j = _worst_face_down(s, i)
    if j is None:
        return
    r = s.take_shield(i, j, "mana")
    if r is not None:
        s.ev(f"　鬼覇 ザ＝デッドジャオウガ：自分のシールドの {BY_KEY[r[0]].name} をマナゾーンに置いた")


def _dj_force(s, i, u):
    """i の攻撃クリーチャー u が、いま相手のハイパーモードの鬼覇を攻撃「できる」なら、その鬼覇を返す

    「できる」は、鬼覇がタップしているか、u がマッハファイターとして攻撃できるか、で決める。
    パワーの大小は見ない（本物のカードは、負けるとわかっていても攻撃させられる）。"""
    o = s.P[1 - i]
    mf = None
    for z in o.board:
        if z.k != "k44_deadjaouga" or z.c.kind != "C" or not z.hyper or z.jd:
            continue
        if not z.tap:
            if mf is None:
                mf = _mf(s, i, u)
            if not mf:
                continue
        return z
    return None


def mt_deadjaouga(s, i, u, t_cands):
    """ハイパーモード中、相手のクリーチャーは可能ならこのクリーチャーを攻撃しなければならない"""
    z = _dj_force(s, i, u)
    if z is None:
        return None
    o = s.P[1 - i]
    for j in t_cands:
        if j != "P" and o.board[j] is z:
            return j
    return None


def atl_deadjaouga(s, i, u, t):
    """同じ能力の続き：鬼覇のパワーが高くて攻撃先に選べない時は、ほかのクリーチャーへの攻撃を止める
    （エンジンは自分より強いクリーチャーへの攻撃を手の一覧に出さないので、
    「攻撃しなければならない」を『ほかを攻撃できない』の形で表す）"""
    z = _dj_force(s, i, u)
    return z is not None and t is not z and s.power(1 - i, z) > s.power(i, u, True)


def nap_deadjaouga(s, i, u):
    """同じく、プレイヤーへの攻撃も止める"""
    z = _dj_force(s, i, u)
    return z is not None and s.power(1 - i, z) > s.power(i, u, True)


add("k44_deadjaouga", "鬼覇 ザ＝デッドジャオウガ", 4, "N", power=4000, mach=True, zrush=True,
    races=("demonio", "onirexstars", "hyperbeast"), pri=8, roles="atk acc blk fin",
    attack=at_deadjaouga, mustatktgt=mt_deadjaouga,
    atktargetlock=atl_deadjaouga, noatkplock=nap_deadjaouga,
    text="マッハファイター。"
         "このクリーチャーが攻撃する時、自分のシールドを1つマナゾーンに置いてもよい"
         "（ハイパーモードでなく、シールドが2つ以上ある時に、いちばん惜しくない裏向きのシールドを置く。"
         "シールドが離れるのでZラッシュが誘発する）。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモードになる）。"
         "ハイパーモード中はパワー9000でW・ブレイカーを持ち、"
         "相手のクリーチャーが攻撃するなら、可能ならこのクリーチャーを攻撃しなければならない"
         "（このクリーチャーがタップしているか、相手がマッハファイターで攻撃できる時だけ縛る）",
    note="エンジンは「パワーで負ける相手には攻撃しない」を手の一覧の段階で外している。"
         "そのため、ハイパーモードの鬼覇（パワー9000）より弱い相手のクリーチャーは、"
         "本物のカードのように『攻撃させられて返り討ちになる』のではなく、"
         "そのターン攻撃できないという形になる（守る力はほぼ同じだが、相手のクリーチャーは死なない）",
    status="partial", source=SRC["k44_deadjaouga"])


# ================================================================ 15. 樹界の守護車 アイオン・ユピテル
add("k44_aionjupiter", "樹界の守護車 アイオン・ユピテル", 2, "N", power=4000, mach=True, noatkp=True,
    races=("fionaguardian", "soniccommand", "command"), pri=5, roles="rem atk",
    text="マッハファイター。このクリーチャーは相手プレイヤーを攻撃できない",
    source=SRC["k44_aionjupiter"])
