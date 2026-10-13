"""担当46：DM26-EX2「悪感謝祭 カリスマBEST」の未実装カード18枚

出典：dmwiki.net の各カードページ。18枚すべてについて、カードページ
      （https://dmwiki.net/《カード名》）と生の wiki ソース（?plugin=template&refer=《カード名》）を
      別の質問で2回ずつ読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
      どちらも一致することを確かめた。数字か本文が1回しか読めなかった
      《堕∞魔 ヴォゲンム》《ヴィオラの黒像》《ボルシャック・太陽・ルピア》《邪妃左神 バンバーシュート》
      《ヨミとイズモの計画》《鬼寄せの術》《混沌の獅子デスライガー／カオス・チャージャー》
      《百鬼の邪王門》《ボルシャック・アークゼオスNEX》は3回読み、
      《ボルシャック・アークゼオスNEX》はさらにカードラッシュの商品ページ（23RP33B/22）で
      エスケープの文面まで突き合わせた。《“必駆”蛮触礼亞》の B・A・D・S 2 の括弧内は
      dmwiki の「B・A・D・S」の用語ページで確かめた。

  この札束に入っている仕組み
    ・**ゴッドとG・リンク**が4枚（邪妃左神 バンバーシュート＝左／極限右神ダフトパンク・アライブ＝右／
      邪眼破壊神R・R・R＝中央／ヨミとイズモの計画）。`godlink=` で位置を宣言し、つなぐ操作は
      `freeacts=`／`actapply=` の追加の手（`s.can_link`／`s.god_link`）で出す。位置（左・中央・右）が
      重ならない組み合わせだけつなげられるので、3枚つなぐとパワー16000・ハンデス4枚になる。
      《ヨミとイズモの計画》の「墓地からリンクして出す」は `_gl_from_grave`
      （`s.enter` で出してからつなぐので「出た時」もちゃんと誘発する）。
    ・**墓地進化**（邪眼破壊神R・R・R）。`evosrc=` で墓地の闇のクリーチャーを進化元にする。
      「このクリーチャーに含まれるカード1枚につき」のハンデスは `len(u.under) + 1` 枚。
    ・**パワード・ブレイカー**（邪眼破壊神R・R・R）。`brkx=` で `1 + パワー // 6000`。
    ・**エスケープ**（ボルシャック・アークゼオスNEX）。`leaverep=` で、破壊されるかわりに
      裏向きのシールドを1つ手札に加えて場に残る。
    ・**鬼エンド**（百鬼の邪王門）。`atkwatch=` で、どちらのクリーチャーの攻撃でも、
      シールドが0のプレイヤーがいて自分のマナに闇と火があれば手札からただで唱える。
    ・**B・A・D・S 2**（“必駆”蛮触礼亞）。`spcost=` で、マナが5に足りない時だけ
      コスト3＋手札1枚捨てに切り替える。
    ・**シンパシー**（ヨミとイズモの計画）。墓地のゴッド・カード1枚につきコスト-1。
    ・**チャージャー**（カオス・チャージャー）。`nograve=True` ＋ 呪文の最後で `s.add_mana`。
    ・**シンカライズ**（ヴィオラの黒像）。`engine3.SHINKA` に登録。
    ・**各ターン1回のコスト軽減／次の1体だけのコスト軽減**
      （ボルシャック・太陽・ルピア／鬼寄せの術）。`costaura=` と `enterwatch=` を組にして、
      「軽減が効いた召喚が1回あったら、そのターンはもう効かない」を作っている。

  調べ直して意外だった点
    ・《堕∞魔 ヴォゲンム》はコスト4・パワー13000・T・ブレイカーなのに、
      書いてある能力は**「自分のターンの終わりに山札の上から13枚を墓地に置く」だけ**。
      攻撃制限も召喚制限も無い（3回読んで確かめた）。山札を削るのが利益になるデッキ用の札。
    ・《ヴィオラの黒像》は**クリーチャーではなくタマシード**（コスト7・闇）で、
      S・トリガーとシンカライズを持つ。殿堂入りはしていない（ページの「殿堂入り」は
      《絶望神サガ》の話だった）。
    ・《ルシファー》は**光／水のコスト8の呪文**で、相手ターンなら「残りのターンをとばす」、
      自分のターンなら「光のコスト9以下のクリーチャーを手札から出す」と、効果が入れ替わる。
    ・《ボルシャック・太陽・ルピア》のコスト軽減は**-3**（コッコ・ルピアの-2より大きい）だが
      **各ターン1回だけ**。下限は1。
    ・《“必駆”蛮触礼亞》の B・A・D・S は「コストを2少なくするかわりに手札を1枚捨てる」で、
      ふつうの B・A・D（出したクリーチャーがターンの終わりに壊れる）とは別物だった。
      ターンの終わりに壊れるのは「この呪文で出したビートジョッキー」のほう。
    ・担当18枚に殿堂入り・プレミアム殿堂のカードは1枚も無かった
      （《百鬼の邪王門》も dmwiki のページには殿堂の記載が無い）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, opp_all, worst_hand
from envcards.env0 import discard_choice, race_like, worst_own

W = "https://dmwiki.net/"
SRC = {
    "k46_bambershoot": W + "《邪妃左神 バンバーシュート》",
    "k46_vogenm": W + "《堕∞魔 ヴォゲンム》",
    "k46_viola": W + "《ヴィオラの黒像》",
    "k46_lostresoul": W + "《ロスト・Re：ソウル》",
    "k46_taiyorupia": W + "《ボルシャック・太陽・ルピア》",
    "k46_hikku": W + "《“必駆”蛮触礼亞》",
    "k46_lucifer": W + "《ルシファー》",
    "k46_yomiizumo": W + "《ヨミとイズモの計画》",
    "k46_oniyose": W + "《鬼寄せの術》",
    "k46_deathliger": W + "《混沌の獅子デスライガー／カオス・チャージャー》",
    "k46_daftpunk": W + "《極限右神ダフトパンク・アライブ》",
    "k46_bloodytyphoon": W + "《ブラッディ・タイフーン》",
    "k46_ryutosei": W + "《龍頭星雲人／零誕祭》",
    "k46_jaoumon": W + "《百鬼の邪王門》",
    "k46_nyahan": W + "《策士のシダン ニャハン》",
    "k46_forjun": W + "《豊潤フォージュン》",
    "k46_arkzeosnex": "https://www.cardrush-dm.jp/product/42493",
    "k46_jaganrrr": W + "《邪眼破壊神R・R・R》",
}


# ---------------------------------------------------------------- G・リンク（共通の道具）
# ゴッドを横につないで1体のクリーチャーとして扱う。パワーは合計、能力と文明は併せ持ち、
# 離れる時は構成しているカードのうち1枚だけが離れる（エンジンの `parts`／`god_link` が面倒を見る）。
# つなぐ操作は「自分のメインステップ中の追加の手」として出す（エンジンの決まり）。
# 位置（左 L・中央 C・右 R）が重ならない組み合わせだけつなげられる
# （「左G・リンク」は「中央」か「右」を持つゴッドの左にしか付けない、という決まりをこれで表している）。
_GL_KEYS = frozenset(("k46_bambershoot", "k46_daftpunk", "k46_jaganrrr"))
_GL_ACT = "x:k46_glink"


def _gl_head(s, i, u):
    """u を含んでいるクリーチャー（リンクの頭）。リンクしていなければ u 自身"""
    for z in s.P[i].board:
        if z is u or u in z.link:
            return z
    return u


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


def _gl_from_grave(s, i, base):
    """墓地にあるゴッドを、base にリンクして出す（つなげられるものを重要度の高い順に全部）。

    リンクして出るゴッドもバトルゾーンに出るので、いったん `s.enter` で出してからつなぐ
    （「出た時」の能力はちゃんと誘発する）。《ヨミとイズモの計画》用。"""
    p = s.P[i]
    while not s.over and base in p.board:
        got = None
        for k in sorted(set(p.grave), key=E.PRI.get, reverse=True):
            if k not in E.GODLINK or BY_KEY[k].kind != "C" or BY_KEY[k].evo:
                continue
            pos = {E.GODLINK[z.k][0] for z in s.parts(base) if z.k in E.GODLINK}
            if not pos or E.GODLINK[k][0] in pos:
                continue                     # 相手がゴッドでない／位置が埋まっている
            mates = E.GODLINK[k][1]
            if mates and not any(z.k in mates for z in s.parts(base)):
                continue                     # つなげる相手が決まっているカード
            if s.fate(i, k, "grave", False) != "ok":
                continue
            got = k
            break
        if got is None:
            return
        p.grave.remove(got)
        s.ev(f"　ヨミとイズモの計画：墓地の {BY_KEY[got].name} をリンクして出す")
        u = s.enter(i, got, "grave", False)
        if u is None:
            return                       # 出られなかった（フウジン天などで別のゾーンへ行った）
        if base not in p.board or u not in p.board:
            return
        p.board.remove(u)
        if u.tap:
            base.tap = True
        s.god_link(i, u, base)


# ================================================================ 共通の道具
def _free_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化クリーチャーは進化元が要るので除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _hand_cre(s, i, pred):
    """手札から踏み倒せるクリーチャーのうち、いちばん重要度の高いもの（全デッキ共通の決まり）"""
    best, bv = None, -1
    for k in sorted(set(s.P[i].hand)):
        c = BY_KEY[k]
        if not _free_cre(c) or not pred(c):
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    return best


def _put_from_hand(s, i, pred):
    """手札からコストを支払わずに1体出す。出せたらその U を返す"""
    k = _hand_cre(s, i, pred)
    if k is None:
        return None
    s.P[i].hand.remove(k)
    s.ev(f"　{BY_KEY[k].name} をコストを支払わずに出す")
    return s.enter(i, k, "hand", False)


def _best_face_down(s, i):
    """自分の裏向きのシールドのうち、いちばん重要度の高いものの番号"""
    p = s.P[i]
    js = [j for j, (k, up) in enumerate(p.sh) if not up]
    if not js:
        return None
    return max(js, key=lambda x: E.PRI[p.sh[x][0]])


def _is_god(c):
    """ゴッド（ゴッド／ゴッド・ノヴァ／ゴッド・ノヴァOMG／ゴッド・ガルドをまとめて数える）"""
    return race_like(c, "god")


def _top(s, i, n):
    """山札の上から n 枚を取り出す（山札が尽きて負けないように1枚は残す）"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    return [p.deck.pop() for _ in range(n)] if n > 0 else []


def _bottom(s, i, ks):
    for k in ks:
        s.P[i].deck.insert(0, k)


# ================================================================ 1. 邪妃左神 バンバーシュート
def _bamber_shield(s, i):
    """ゴッドを1体、自分の墓地から新しいシールドとして裏向きに加える"""
    p = s.P[i]
    cs = [k for k in p.grave if _is_god(BY_KEY[k])]
    if not cs:
        return
    k = max(cs, key=E.PRI.get)
    p.grave.remove(k)
    if not s.add_shield(i, k, False):
        p.grave.append(k)                      # 置けなかった（フウジン天）ので墓地に戻す
        return
    s.ev(f"　バンバーシュート：墓地の {BY_KEY[k].name} を裏向きのシールドに加えた")


def d_bambershoot(s, i, u):
    """このクリーチャーが破壊された時"""
    _bamber_shield(s, i)


def lw_bambershoot(s, i, u, dest, destroy_):
    """自分の他のクリーチャーが破壊された時（バンバーシュートが場に残っている分だけ誘発）"""
    if not destroy_ or u.c.kind != "C":
        return
    for _ in range(sum(1 for z in s.P[i].board for x in s.parts(z) if x.k == "k46_bambershoot")):
        if s.over:
            return
        _bamber_shield(s, i)


add("k46_bambershoot", "邪妃左神 バンバーシュート", 5, "D", power=5000,
    races=("godnovaomg", "godnova", "god", "angelcommand", "command"), pri=6, roles="shd",
    destroyed=d_bambershoot, leavewatch=lw_bambershoot, godlink=("L", ()),
    freeacts=_gl_acts, actapply={_GL_ACT: _gl_apply},
    text="このクリーチャーまたは自分の他のクリーチャーが破壊された時、ゴッドを1体、"
         "自分の墓地から新しいシールドとして自分のシールドゾーンに裏向きにして加えてもよい"
         "（墓地のゴッドのうち重要度のいちばん高いものを選ぶ）。"
         "パワーの表記は5000+。"
         "左G・リンク（「中央G・リンク」または「右G・リンク」を持つゴッドの左側にリンクしてもよい。"
         "リンクしたゴッドはパワーを合計した1体のクリーチャーになり、能力と文明を併せ持ち、"
         "離れる時はそのうち1枚だけが離れる。つなぐのは自分のメインステップ中の追加の手として行う）。"
         "《邪眼破壊神R・R・R》《極限右神ダフトパンク・アライブ》と3枚つなぐとパワー16000になる",
    source=SRC["k46_bambershoot"])


# ================================================================ 2. 堕∞魔 ヴォゲンム
def te_vogenm(s, i, u):
    """自分のターンの終わりに、自分の山札の上から13枚を墓地に置く（強制）"""
    s.ev("　ヴォゲンム：自分の山札の上から13枚を墓地へ")
    s.mill(i, 13)


add("k46_vogenm", "堕∞魔 ヴォゲンム", 4, "D", power=13000, brk=3,
    races=("mafigang", "demoncommand", "command", "madogu"), pri=9, roles="atk fin",
    tend=te_vogenm,
    text="T・ブレイカー。自分のターンの終わりに、自分の山札の上から13枚を墓地に置く",
    note="エンジンの mill は山札を1枚残す作りなので、この能力だけで山札が0枚になって負けることはない",
    source=SRC["k46_vogenm"])


# ================================================================ 3. ヴィオラの黒像
E.SHINKA.add("k46_viola")


def e_viola(s, i, u):
    """出た時、相手のクリーチャー1体を破壊し、それよりコストの小さいクリーチャーを墓地から出す"""
    t = s.target(i)
    if t is None:
        return
    cost = t.c.cost
    s.ev(f"　ヴィオラの黒像：{t.c.name} を破壊")
    destroy(s, i, t)
    s.revive(i, lambda c: c.cost < cost, "grave")


add("k46_viola", "ヴィオラの黒像", 7, "D", kind="T", trig=True,
    races=("kingcommanddragon", "command", "dragon", "unknown", "rexstars"), pri=8,
    roles="trg rem acc",
    enter=e_viola,
    text="S・トリガー。シンカライズ（このタマシードがクリーチャーであるかのように、"
         "この上に進化クリーチャーを置いてもよい）。"
         "このタマシードが出た時、相手のクリーチャーを1体選び、破壊する。"
         "その選んだクリーチャーよりコストが小さいクリーチャーを1体、自分の墓地から出してもよい"
         "（相手の重要度のいちばん高いクリーチャーを破壊し、墓地からは重要度のいちばん高い"
         "進化でないクリーチャーを出す）",
    source=SRC["k46_viola"])


# ================================================================ 4. ロスト・Re：ソウル
def sp_lostresoul(s, i):
    """相手は自身の手札をすべて捨てる"""
    o = s.P[1 - i]
    n = 0
    for k in list(o.hand):
        if s.over:
            break
        if k in o.hand:
            s.discard(1 - i, k)
            n += 1
    s.ev(f"　ロスト・Re：ソウル：相手の手札{n}枚をすべて捨てさせた")


add("k46_lostresoul", "ロスト・Re：ソウル", 7, "D", kind="S", gs=True, pri=8, roles="dis fin",
    spell=sp_lostresoul,
    text="G・ストライク（このカードを自分のシールドゾーンから手札に加える時、表向きにし、"
         "相手のクリーチャーを1体選んでもよい。このターン、そのクリーチャーは攻撃できない）。"
         "相手は自身の手札をすべて捨てる",
    source=SRC["k46_lostresoul"])


# ================================================================ 5. ボルシャック・太陽・ルピア
def _bolshack(c):
    return "ボルシャック" in c.name


def ca_taiyorupia(s, i, k, cur):
    """各ターンに一度、名前に《ボルシャック》とある自分のクリーチャーの召喚コストを3少なくする"""
    if cur <= 1 or BY_KEY[k].kind != "C" or not _bolshack(BY_KEY[k]):
        return cur
    p = s.P[i]
    if not any(z.k == "k46_taiyorupia" for z in p.board):
        return cur
    if p.x.get("k46_taiyo_t") == s.turn:
        return cur
    return max(1, cur - 3)


def ew_taiyorupia(s, i, u):
    """軽減が効いた《ボルシャック》の召喚が1回あったら、そのターンはもう軽減しない"""
    if u.c.kind != "C" or not u.x.get("summoned") or not _bolshack(u.c):
        return
    p = s.P[i]
    if not any(z.k == "k46_taiyorupia" and z is not u for z in p.board):
        return                                 # 軽減してくれる太陽・ルピアが（自分以外に）いなかった
    if p.x.get("k46_taiyo_t") == s.turn:
        return
    p.x["k46_taiyo_t"] = s.turn


add("k46_taiyorupia", "ボルシャック・太陽・ルピア", 3, "F", power=4000, gs=True,
    races=("firebird", "armoreddragon", "armored", "dragon"), pri=5, roles="acc trg",
    costaura=ca_taiyorupia, enterwatch=ew_taiyorupia,
    text="G・ストライク（このカードを自分のシールドゾーンから手札に加える時、表向きにし、"
         "相手のクリーチャーを1体選んでもよい。このターン、そのクリーチャーは攻撃できない）。"
         "各ターンに一度、名前に《ボルシャック》とある自分のクリーチャーの召喚コストを3少なくしてもよい。"
         "ただし、コストは1以下にはならない"
         "（軽減が効いた召喚が1回あったら、そのターンはもう効かない）",
    source=SRC["k46_taiyorupia"])


# ================================================================ 6. “必駆”蛮触礼亞
def _bj(c):
    return race_like(c, "beatjockey")


def spc_hikku(s, i, k):
    """B・A・D・S 2：コストを2少なくするかわりに手札を1枚捨てる（マナが5に足りない時だけ使う）"""
    p = s.P[i]
    av = len(p.mana) - p.mused
    cost = 5
    if av < 5 and len(p.hand) >= 2:
        cost = 3
    if not s.dry:
        p.x["k46_hikku_pay"] = cost
    return cost


def ta_hikku(s, i, u):
    """この呪文で出したビートジョッキーを、そのターンの終わりに破壊する"""
    if u.x.get("k46_hikku_eot") != s.turn:
        return
    s.ev(f"　“必駆”蛮触礼亞：ターンの終わりに {u.c.name} を破壊")
    s.leave(i, u, "grave", destroy=True)


def sp_hikku(s, i):
    p = s.P[i]
    if p.x.pop("k46_hikku_pay", 5) == 3:
        k = worst_hand(s, i)
        if k is not None:
            s.ev(f"　B・A・D・S 2：手札の {BY_KEY[k].name} を捨てて2コスト軽くした")
            s.discard(i, k)
    k = _hand_cre(s, i, _bj)
    if k is None:
        return
    pw = BY_KEY[k].power
    win = [z for z in opp_all(s, i) if s.power(1 - i, z) < pw]
    if not win and k not in E.ENTER:
        return                                 # バトルで勝てる相手も、出た時の効果も無いなら出さない
    p.hand.remove(k)
    s.ev(f"　“必駆”蛮触礼亞：手札から {BY_KEY[k].name} を出す")
    u = s.enter(i, k, "hand", False)
    if u is None or u not in p.board:
        return
    u.x["k46_hikku_eot"] = s.turn
    t = s.target(i, lambda z: s.power(1 - i, z) < s.power(i, u, True))
    if t is not None:
        s.ev(f"　“必駆”蛮触礼亞：{u.c.name} と {t.c.name} をバトルさせる")
        s.battle(i, u, 1 - i, t)


add("k46_hikku", "“必駆”蛮触礼亞", 5, "F", kind="S", pri=6, roles="rem acc",
    spell=sp_hikku, spcost=spc_hikku, tendall=ta_hikku,
    text="B・A・D・S 2（この呪文を唱えるコストを2少なくしてもよい。そうしたら、自分の手札を1枚捨てる。"
         "使えるマナが5に足りず、捨てられる手札がある時だけ使う）。"
         "ビートジョッキーを1体、自分の手札から出してもよい。そうしたら、相手のクリーチャーを1体選ぶ。"
         "その2体をバトルさせる。そのターンの終わりに、そのビートジョッキーを破壊する"
         "（バトルで勝てる相手がいるか、出た時の効果を持つビートジョッキーがいる時だけ出す）",
    source=SRC["k46_hikku"])


# ================================================================ 7. ルシファー
def sp_lucifer(s, i):
    """相手のターンなら残りのターンをとばす。自分のターンなら光のコスト9以下を手札から出す"""
    if s.tp != i:
        s.stop = True
        s.ev("　ルシファー：相手のターンの残りをとばす")
        return
    u = _put_from_hand(s, i, lambda c: "L" in c.civ and c.cost <= 9)
    if u is not None:
        s.ev("　ルシファー：自分のターンなので光のクリーチャーを手札から出した")


add("k46_lucifer", "ルシファー", 8, "LW", kind="S", trig=True, pri=9, roles="trg fin",
    spell=sp_lucifer,
    text="S・トリガー。今のターンが相手のターンなら、残りのターンをとばす。"
         "今のターンが自分のターンなら、光のコスト9以下のクリーチャーを1体、自分の手札から出してもよい"
         "（手札の条件に合うクリーチャーのうち、重要度のいちばん高いものを出す）",
    source=SRC["k46_lucifer"])


# ================================================================ 8. ヨミとイズモの計画
def spc_yomiizumo(s, i, k):
    """シンパシー：自分の墓地にあるゴッド・カード1枚につきコストを1少なくする"""
    n = sum(1 for x in s.P[i].grave if _is_god(BY_KEY[x]))
    return max(1, 9 - n)


def sp_yomiizumo(s, i):
    s.mill(i, 4)
    u = s.revive(i, lambda c: True, "grave")
    if u is None or s.over:
        return
    _gl_from_grave(s, i, u)


add("k46_yomiizumo", "ヨミとイズモの計画", 9, "WD", kind="S", races=("god",), pri=8,
    roles="acc fin",
    spell=sp_yomiizumo, spcost=spc_yomiizumo,
    text="シンパシー：自分の墓地にあるゴッド・カード（この呪文を唱えるコストを、"
         "自分の墓地にあるゴッド・カード1枚につき1少なくする。ただし1より少なくはならない）。"
         "自分の山札の上から4枚を墓地に置く。"
         "クリーチャーを1体、自分の墓地から出してもよい（重要度のいちばん高い進化でないクリーチャー）。"
         "その後、それにリンクできる好きな数のゴッドを、自分の墓地からリンクして出してもよい"
         "（出したクリーチャーがゴッドなら、墓地のゴッドのうちリンクの位置が空いているものを、"
         "重要度の高い順に全部つなげる）",
    source=SRC["k46_yomiizumo"])


# ================================================================ 9. 鬼寄せの術
def _oni_n(p, turn):
    v = p.x.get("k46_oniyose")
    return v[1] if (v is not None and v[0] == turn) else 0


def ca_oniyose(s, i, k, cur):
    """このターン、次に召喚する自分の闇または火のクリーチャーのコストを4少なくする（1より下げない）"""
    if cur <= 1 or BY_KEY[k].kind != "C":
        return cur
    n = _oni_n(s.P[i], s.turn)
    if not n or not (set(BY_KEY[k].civ) & set("DF")):
        return cur
    return max(1, cur - 4 * n)


def ew_oniyose(s, i, u):
    """軽減が効いた1体が出たら、その効果は使い切る"""
    if u.c.kind != "C" or not u.x.get("summoned"):
        return
    p = s.P[i]
    if not _oni_n(p, s.turn) or not (set(u.c.civ) & set("DF")):
        return
    p.x["k46_oniyose"] = (s.turn, 0)


def sp_oniyose(s, i):
    p = s.P[i]
    j = _best_face_down(s, i)
    if j is not None:
        r = s.take_shield(i, j, "hand")
        if r is not None:
            s.ev(f"　鬼寄せの術：自分のシールドの {BY_KEY[r[0]].name} を手札に加えた"
                 "（S・トリガーは使えない）")
    p.x["k46_oniyose"] = (s.turn, _oni_n(p, s.turn) + 1)
    s.ev("　鬼寄せの術：このターン、次に召喚する闇か火のクリーチャーのコストが4少なくなる")


add("k46_oniyose", "鬼寄せの術", 2, "DF", kind="S", races=("onifuda",), pri=4, roles="acc draw",
    spell=sp_oniyose, costaura=ca_oniyose, enterwatch=ew_oniyose,
    text="自分のシールドを1つ手札に加える。ただし、その「S・トリガー」は使えない"
         "（裏向きのシールドのうち重要度のいちばん高いものを選ぶ）。"
         "このターン、次に召喚する自分の闇または火のクリーチャーのコストを4少なくする。"
         "ただし、コストは0以下にはならない（1まで）",
    source=SRC["k46_oniyose"])


# ================================================================ 10. 混沌の獅子デスライガー／カオス・チャージャー
def sp_deathliger(s, i):
    """カオス・チャージャー：上4枚からデーモン・コマンドを2枚まで手札へ。唱えた後マナゾーンへ"""
    p = s.P[i]
    top = _top(s, i, 4)
    got, rest = 0, []
    for k in sorted(top, key=E.PRI.get, reverse=True):
        if got < 2 and race_like(BY_KEY[k], "demoncommand"):
            p.hand.append(k)
            got += 1
            s.ev(f"　カオス・チャージャー：{BY_KEY[k].name} を手札へ")
        else:
            rest.append(k)
    _bottom(s, i, rest)
    s.add_mana(i, "k46_deathliger")
    s.ev("　チャージャー：カオス・チャージャーをマナゾーンへ")


add("k46_deathliger", "混沌の獅子デスライガー / カオス・チャージャー", 7, "D", power=9000, brk=2,
    races=("demoncommand", "command"), twin=(3, "D", False), nograve=True, pri=8,
    roles="atk draw acc",
    spell=sp_deathliger,
    text="クリーチャー側《混沌の獅子デスライガー》（闇7・デーモン・コマンド・9000）：W・ブレイカー。"
         "呪文側《カオス・チャージャー》（闇3）：自分の山札の上から4枚を見る。その中から、"
         "デーモン・コマンド・カードを2枚まで、表向きにしてから手札に加える。"
         "残りを好きな順序で山札の下に置く。"
         "チャージャー（唱えた後、墓地に置くかわりにマナゾーンに置く）",
    source=SRC["k46_deathliger"])


# ================================================================ 11. 極限右神ダフトパンク・アライブ
def e_daftpunk(s, i, u):
    """出た時、山札の上から1枚を墓地に置き、コスト4以下のゴッド・ノヴァを墓地から出す"""
    s.mill(i, 1)
    s.revive(i, lambda c: c.cost <= 4 and race_like(c, "godnova"), "grave")


add("k46_daftpunk", "極限右神ダフトパンク・アライブ", 5, "D", power=3000,
    races=("godnovaomg", "godnova", "god", "demoncommand", "command"), pri=6, roles="acc",
    enter=e_daftpunk, godlink=("R", ()),
    freeacts=_gl_acts, actapply={_GL_ACT: _gl_apply},
    text="このクリーチャーが出た時、自分の山札の上から1枚目を墓地に置く。その後、"
         "コスト4以下のゴッド・ノヴァを1体、自分の墓地から出してもよい。"
         "パワーの表記は3000+。"
         "右G・リンク（「中央G・リンク」または「左G・リンク」を持つゴッドの右側にリンクしてもよい。"
         "リンクしたゴッドはパワーを合計した1体のクリーチャーになり、能力と文明を併せ持ち、"
         "離れる時はそのうち1枚だけが離れる。つなぐのは自分のメインステップ中の追加の手として行う）"
         "※コスト4以下のゴッド・ノヴァはいまのカードプールにほとんどいないので、"
         "墓地から出す能力はめったに働かない（カードの文面どおりに実装はしてある）",
    source=SRC["k46_daftpunk"])


# ================================================================ 12. ブラッディ・タイフーン
def sp_bloodytyphoon(s, i):
    """山札の上から3枚を見て1枚を手札に加え、残りを墓地に置く"""
    k = s.dig(i, 3, lambda x: True, rest="grave")
    if k is not None:
        s.ev(f"　ブラッディ・タイフーン：{BY_KEY[k].name} を手札へ（残りは墓地）")


add("k46_bloodytyphoon", "ブラッディ・タイフーン", 2, "WD", kind="S", pri=4, roles="draw acc",
    spell=sp_bloodytyphoon,
    text="自分の山札の上から3枚を見る。そのうちの1枚を自分の手札に加え、残りを墓地に置く"
         "（見た中で重要度のいちばん高い1枚を手札に加える）",
    source=SRC["k46_bloodytyphoon"])


# ================================================================ 13. 龍頭星雲人／零誕祭
def cx_ryutosei(s, i, av):
    """自分の墓地にある水または闇のカード1枚につき召喚コストを1少なくする（1より下げない）"""
    n = sum(1 for k in s.P[i].grave if set(E.MCIV[k]) & set("WD"))
    return max(1, 10 - n)


def _ryutosei_hand(s, i, u):
    """出た時または攻撃する時、相手は自身の手札を2枚選んで捨てる"""
    for _ in range(2):
        if s.over:
            return
        discard_choice(s, 1 - i)


def sp_ryutosei(s, i):
    """零誕祭：自分のクリーチャーを1体破壊し、その後、相手のクリーチャーを1体破壊する"""
    z = worst_own(s, i)
    if z is not None:
        s.ev(f"　零誕祭：自分の {z.c.name} を破壊")
        s.leave(i, z, "grave", destroy=True)
    t = s.target(i)
    if t is not None:
        s.ev(f"　零誕祭：相手の {t.c.name} を破壊")
        destroy(s, i, t)


add("k46_ryutosei", "龍頭星雲人 / 零誕祭", 10, "D", power=12000, brk=3,
    races=("demoncommand", "command", "zerolist"), twin=(4, "D", True), pri=11,
    roles="fin dis rem trg",
    costx=cx_ryutosei, enter=_ryutosei_hand, attack=_ryutosei_hand, spell=sp_ryutosei,
    text="クリーチャー側《龍頭星雲人》（闇10・デーモン・コマンド／ゼロリスト・12000）："
         "自分の墓地にある水または闇のカード1枚につき、このクリーチャーの召喚コストを1少なくする。"
         "ただし、コストは0以下にはならない（1まで）。T・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、相手は自身の手札を2枚選んで捨てる。"
         "呪文側《零誕祭》（闇4）：S・トリガー。自分のクリーチャーを1体破壊する。"
         "その後、相手のクリーチャーを1体破壊する"
         "（自分は失うのがいちばん安いクリーチャー、相手は重要度のいちばん高いクリーチャーを選ぶ）",
    source=SRC["k46_ryutosei"])


# ================================================================ 14. 百鬼の邪王門
def sp_jaoumon(s, i):
    """山札の上4枚を墓地に置き、その中の闇か火のコスト6以下の進化でないクリーチャーを出してバトル"""
    p = s.P[i]
    got = s.mill(i, 4)
    cands = [k for k in got
             if k in p.grave and _free_cre(BY_KEY[k]) and BY_KEY[k].cost <= 6
             and (set(BY_KEY[k].civ) & set("DF"))]
    if not cands:
        return
    k = max(cands, key=E.PRI.get)
    if s.fate(i, k, "grave", False) != "ok":
        return
    p.grave.remove(k)
    s.ev(f"　百鬼の邪王門：墓地に置いた {BY_KEY[k].name} を出す")
    u = s.enter(i, k, "grave", False)
    if u is None or u not in p.board:
        return
    pw = s.power(i, u, True)
    if not [z for z in opp_all(s, i) if s.power(1 - i, z) < pw]:
        return                                 # 勝てる相手がいないならバトルさせない（任意）
    t = s.target(i, lambda z: s.power(1 - i, z) < pw)
    if t is not None:
        s.ev(f"　百鬼の邪王門：{u.c.name} と {t.c.name} をバトルさせる")
        s.battle(i, u, 1 - i, t)


def aw_jaoumon(s, i, u):
    """鬼エンド：クリーチャーが攻撃する時、シールドが1つもないプレイヤーがいて、
    自分のマナゾーンに闇と火文明があれば、この呪文を手札からコストを支払わずに唱えてもよい

    自分の攻撃でも相手の攻撃でも誘発するので、両方のプレイヤーの手札を見る。"""
    if u.c.kind != "C":
        return
    if s.P[0].sh and s.P[1].sh:
        return
    for j in (0, 1):
        p = s.P[j]
        while "k46_jaoumon" in p.hand and not s.over:
            cv = set("".join(E.MCIV[k] for k in p.mana))
            if not {"D", "F"} <= cv:
                break
            if not s.spell_ok(j, 6) or len(p.deck) <= 5:
                break
            p.hand.remove("k46_jaoumon")
            s.ev("　鬼エンド：百鬼の邪王門をコストを支払わずに唱える")
            s.cast(j, "k46_jaoumon")


add("k46_jaoumon", "百鬼の邪王門", 6, "DF", kind="S", races=("onifuda",), pri=8,
    roles="trg rem fin",
    spell=sp_jaoumon, atkwatch=aw_jaoumon,
    text="＜鬼エンド＞クリーチャーが攻撃する時、シールドが1つもないプレイヤーがいて、"
         "自分のマナゾーンに闇と火文明があれば、この呪文を自分の手札からコストを支払わずに唱えてもよい"
         "（山札が6枚以上ある間だけ唱える）。"
         "自分の山札の上から4枚を墓地に置く。こうして墓地に置いたカードの中から、闇または火の、"
         "コスト6以下の、進化ではないクリーチャーを1体出す。その後、相手のクリーチャーを1体選んでもよい。"
         "その2体をバトルさせる（バトルで勝てる相手がいる時だけ選ぶ）",
    source=SRC["k46_jaoumon"])


# ================================================================ 15. 策士のシダン ニャハン
def _oracle_like(c):
    """種族にオラクル、アンノウン、またはゼニスを持つか"""
    return race_like(c, "oracle") or race_like(c, "unknown") or race_like(c, "zenith")


def e_nyahan(s, i, u):
    """出た時、自分の手札を1枚裏向きにしてマナゾーンに置いてもよい"""
    p = s.P[i]
    k = worst_hand(s, i)
    if k is None:
        return
    p.hand.remove(k)
    s.add_mana(i, k, src="hand")
    s.ev(f"　ニャハン：手札の {BY_KEY[k].name} を裏向きにしてマナゾーンへ")


def lf_nyahan(s, i, u, dest):
    """離れた時、オラクル・アンノウン・ゼニスを1枚、自分のマナゾーンから手札に戻してもよい"""
    p = s.P[i]
    if len(p.mana) < 4:
        return                                 # マナが細い時は崩さない
    cs = [k for k in p.mana if _oracle_like(BY_KEY[k])]
    if not cs:
        return
    k = max(cs, key=E.PRI.get)
    if E.PRI[k] < 4:
        return
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　ニャハン：マナの {BY_KEY[k].name} を手札へ")


add("k46_nyahan", "策士のシダン ニャハン", 2, "", power=2222, gs=True,
    races=("oracleceres",), pri=4, roles="acc trg draw",
    enter=e_nyahan, left=lf_nyahan,
    text="無色のクリーチャー。G・ストライク（このカードを自分のシールドゾーンから手札に加える時、"
         "表向きにし、相手のクリーチャーを1体選んでもよい。このターン、そのクリーチャーは攻撃できない）。"
         "このクリーチャーが出た時、自分の手札を1枚裏向きにしてマナゾーンに置いてもよい"
         "（手札でいちばん要らない1枚を置く）。"
         "このクリーチャーが離れた時、種族にオラクル、アンノウン、またはゼニスを持つカードを1枚、"
         "自分のマナゾーンから手札に戻してもよい（マナが4枚以上あり、重要度4以上のカードがある時）",
    note="「裏向きにしてマナゾーンに置く」の裏向き（文明を持たないマナになる）は、"
         "このシミュレーターのマナゾーンに表裏の区別が無いため、ふつうにマナに置くのと同じ扱いにした",
    source=SRC["k46_nyahan"])


# ================================================================ 16. 豊潤フォージュン
def sp_forjun(s, i):
    """山札の上から1枚をマナゾーンに置き、その後マナが5枚以下なら1枚引く"""
    s.ramp(i, 1, tapped=False)
    if len(s.P[i].mana) <= 5:
        s.draw(i, 1)


add("k46_forjun", "豊潤フォージュン", 3, "N", kind="S", pri=4, roles="acc draw",
    spell=sp_forjun,
    text="自分の山札の上から1枚をマナゾーンに置く。その後、自分のマナゾーンのカードが5枚以下なら、"
         "カードを1枚引く",
    source=SRC["k46_forjun"])


# ================================================================ 17. ボルシャック・アークゼオスNEX
def _armored(c):
    return c.kind == "C" and race_like(c, "armored")


def cx_arkzeosnex(s, i, av):
    """自分のアーマード・クリーチャーがあれば、召喚コストを1少なくする"""
    if any(_armored(z.c) for z in s.P[i].board):
        return 4
    return 5


def at_arkzeosnex(s, i, u):
    """攻撃する時、コスト5以下のアーマード・クリーチャーを1体、手札から出してもよい"""
    _put_from_hand(s, i, lambda c: c.cost <= 5 and race_like(c, "armored"))


def lf_arkzeosnex(s, i, u, dest):
    """離れた時、自分の山札の上から1枚をシールド化してもよい"""
    if s.add_shield(i):
        s.ev("　アークゼオスNEX：山札の上から1枚をシールド化")


def rep_arkzeosnex(s, i, u, dest, destroy_):
    """エスケープ：破壊される時、墓地に置くかわりに自分のシールドを1つ手札に加えてもよい"""
    if u.k != "k46_arkzeosnex" or not destroy_:
        return False
    j = _best_face_down(s, i)
    if j is None:
        return False
    r = s.take_shield(i, j, "hand")
    if r is None:
        return False
    s.ev(f"　エスケープ：シールドの {BY_KEY[r[0]].name} を手札に加えて {u.c.name} は残る")
    return True


add("k46_arkzeosnex", "ボルシャック・アークゼオスNEX", 5, "L", power=6500, brk=2, blocker=True,
    races=("armoreddragon", "armored", "dragon"), pri=8, roles="blk atk shd acc",
    costx=cx_arkzeosnex, attack=at_arkzeosnex, left=lf_arkzeosnex, leaverep=rep_arkzeosnex,
    text="自分のアーマード・クリーチャーがあれば、このクリーチャーの召喚コストを1少なくする。"
         "ブロッカー、W・ブレイカー。"
         "このクリーチャーが攻撃する時、コスト5以下のアーマード・クリーチャーを1体、"
         "自分の手札から出してもよい。"
         "このクリーチャーが離れた時、自分の山札の上から1枚をシールド化してもよい。"
         "エスケープ（このクリーチャーが破壊される時、墓地に置くかわりに自分のシールドを1つ"
         "手札に加えてもよい。そのシールドのS・トリガーは使えない。"
         "裏向きのシールドが1つでもあれば必ず使う）",
    source=SRC["k46_arkzeosnex"])


# ================================================================ 18. 邪眼破壊神R・R・R
def _grave_dark_cre(s, i):
    """自分の墓地にある闇のクリーチャーのうち、いちばん安いもの（進化元にして使い切る側）"""
    cs = [k for k in s.P[i].grave if BY_KEY[k].kind == "C" and "D" in E.MCIV[k]]
    return min(cs, key=E.PRI.get) if cs else None


def es_jaganrrr(s, i):
    """墓地進化：自分の墓地にある闇のクリーチャー1体を進化元にする"""
    k = _grave_dark_cre(s, i)
    return ("grave", k) if k is not None else None


def bx_jaganrrr(s, i, u):
    """パワード・ブレイカー（パワー6000ごとに1枚多くブレイクする）。

    リンクしている時は、合計パワー（リンクの頭で数えたパワー）で数える。"""
    return 1 + s.power(i, _gl_head(s, i, u), True) // 6000


def at_jaganrrr(s, i, u):
    """攻撃する時、このクリーチャーに含まれるカード1枚につき、相手の手札を1枚見ないで捨てさせる

    「含まれるカード」は、進化元（下のカード）とリンクしているゴッドの両方を数える。
    リンクしている時、エンジンは攻撃する能力をリンクの頭の u で呼ぶので、u から数えればよい。"""
    n = sum(1 + len(z.under) for z in s.parts(u))
    s.ev(f"　邪眼破壊神R・R・R：相手の手札を{n}枚、見ないで捨てさせる")
    for _ in range(n):
        if s.over:
            return
        s.discard_random(1 - i)


def pr_jaganrrr(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and "D" in E.MCIV[kk]
            and not (BY_KEY[kk].evo and not BY_KEY[kk].neo))
    return None if n >= 6 else "墓地進化の元になる闇のクリーチャーが6体いない"


add("k46_jaganrrr", "邪眼破壊神R・R・R", 5, "D", power=8000, evo="grave",
    races=("godgard", "god", "darklord", "knight"), pri=10, roles="fin dis atk",
    evosrc=es_jaganrrr, evox=lambda s, i, u: False, brkx=bx_jaganrrr, attack=at_jaganrrr,
    playrule=pr_jaganrrr, godlink=("C", ()),
    freeacts=_gl_acts, actapply={_GL_ACT: _gl_apply},
    text="墓地進化：自分の墓地にある闇のクリーチャー1体の上に重ねつつ出す"
         "（墓地にそれがなければ召喚できない。いちばん安い闇のクリーチャーを進化元にする）。"
         "パワード・ブレイカー（パワー6000ごとにシールドを1枚多くブレイクする）。"
         "このクリーチャーが攻撃する時、このクリーチャーに含まれるカード1枚につき、"
         "相手の手札を1枚見ないで選び、捨てさせる"
         "（進化元とリンクしているゴッドを数える。墓地進化しているので通常は2枚）。"
         "パワーの表記は8000+。"
         "中央G・リンク（「右G・リンク」または「左G・リンク」を持つゴッドとつなげてもよい。"
         "リンクしたゴッドはパワーを合計した1体のクリーチャーになり、能力と文明を併せ持ち、"
         "離れる時はそのうち1枚だけが離れる。つなぐのは自分のメインステップ中の追加の手として行う）。"
         "《邪妃左神 バンバーシュート》《極限右神ダフトパンク・アライブ》と3枚つなぐと"
         "パワー16000（T・ブレイカー）・ハンデス4枚になる",
    source=SRC["k46_jaganrrr"])
