"""担当32：DM26-RP3「逆札篇 第3弾 勝敵！逆転おこせ鬼の∞ディスペクター!!」の未実装カード15枚（17/77〜31/77・key は `k32_`）

  出典：dmwiki.net のカード個別ページ（`https://dmwiki.net/《カード名》`）を、カードごとに
        **別の質問で2回ずつ**読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
        2回とも一致することを確かめた（curl は403なので WebFetch、4〜6秒間隔）。
        生の wiki ソース（`?plugin=template&refer=《カード名》`）は cardtable の行が「…」で
        切れてしまい本文が読めないので、通常ページ側を2回読む形にした。
        キーワード（マジボンバー・ササゲール・エスケープ・フシギバース・ギャラクシールド・
        ムゲンクライム・キリフダッシュ・スマッシュ・バースト・スーパー・S・トリガー）は
        カードページとキーワードの専用ページの両方で定義を突き合わせた。

  内訳（番号は DM26-RP3 の通し番号）
    ・17/77 冥王の顎（闇4・呪文・スーパー・S・トリガー）
    ・18/77 キング・ザ・ベスト（火7・ジョーカーズ・山札の下から踏み倒し）
    ・19/77 ドドンガ轟キャイエス（火5・呪文・スーパー・S・トリガー）
    ・20/77 大地 コンダマ-2（自然3・ディスタス・ササゲールを配る）
    ・21/77 コクーン・ツェッペリン（自然3・呪文・スーパー・S・トリガー）
    ・22/77 輝晶 エヴァ-3（光水3・ギャラクシールド[光/水(2)]）
    ・23/77 冥運逆夢 ハミデスナスカ（光闇6・EXライフ・オシオキムーン）
    ・24/77 雷星逆夢 ヴァリ-我-ラウザス（光火6・EXライフ・マジボンバー6）
    ・25/77 魔具 ヴァイポイズ-4（水闇5・ムゲンクライム2・ササゲール4）
    ・26/77 昆怪逆夢 アンダステリオン（闇自然7・EXライフ・フシギバース[闇/自然(9)]）
    ・27/77 罰空逆夢 ブラゴチャーンド（火自然7・EXライフ・キリフダッシュ[火/自然(4)]）
    ・28/77 銃初逆夢 ザ・ウィニー／ジョリー・ザ・スパーク（光5/3・ツインパクト・スマッシュ・バースト）
    ・29/77 輝晶 シンプ-2（光3・離れた時にブロッカーを配る）
    ・30/77 ヒトリダチ キャンベロ（光2・Jビッグ1・コスト大きい相手を山札の下へ）
    ・31/77 輝晶 マルハヴ-2（光2・相手のターン中ディスタスにエスケープ）

  この弾の仕組みと、このファイルでの書き方
    ・**ササゲール**N（20/77・22/77・25/77・29/77・31/77 の5枚）
      「自分のディスペクター・クリーチャーの召喚コストをN少なくしてもよい。そうしたらこのエレメントを破壊する」。
      `costaura` で常に安くすると「払えるのにわざわざ自分のクリーチャーを失う」手になってしまうので、
      env31 の J・O・E 2 と同じく `freeacts=`／`actapply=` で
      「ササゲールを使ってディスペクターを召喚する手」を別に足した（普通の召喚の手はそのまま残る）。
      同じ召喚で複数のササゲールを重ねられる（公式Q&A）ので、必要な数だけ、
      失うのがいちばん安いエレメントから順にささげる。
    ・**ギャラクシールド**[光/水(2)]（22/77）……手札から2マナで表向きのシールドとして置き、
      自分のターンのはじめにコストを支払ったものとして召喚する。置く手は `freeacts=`、
      「表向きでシールドゾーンに置かれた時」は `shieldin=` で拾える。
      ターンのはじめの召喚は `turnstart=`（バトルゾーンに何もなくても呼ばれる）1本。
    ・**マジボンバー6**（24/77）……攻撃する時、山札の上から1枚を見て、
      コスト6以下のクリーチャーを手札か**その見た1枚**から出す（召喚ではない）。
    ・**フシギバース**[闇/自然(9)]（26/77）……自分のクリーチャー1体をマナゾーンに置き、
      9からそのクリーチャーのコストを引いた数（最低2）を支払って墓地から召喚する。
    ・**キリフダッシュ**[火/自然(4)]（27/77）……自分のクリーチャーの攻撃の終わりに、
      **その攻撃中にシールドをブレイクしていれば**手札から4マナで召喚してよい。
      「その攻撃でブレイクしたか」は `breakwatch=` で攻撃中のクリーチャーの uid を覚えて `atkend=` で見る。
    ・**エスケープ**（31/77）……破壊される時、かわりに自分のシールドを1つ手札に加える（S・トリガーは使えない）。
      `leaverep=` で置き換える。
    ・**スーパー・S・トリガー**（17/77・19/77・21/77）……S・トリガーと同じに唱えられ、
      「その時自分のシールドが1つもなければ」追加で「S-」の能力も使う。env31 と同じやり方
      （`shieldcast=`。`fn(s, i, k, nsh)` の nsh＝その時のシールドの枚数を見る）にし、
      env31 の `SUPER_S` にも登録して《七王を統べる者 魔王ザダン》から使えるようにした。

  調べ直して意外だった点
    ・「◯◯逆夢 ◯◯」は**EXライフ以外まるで共通点が無い**。この5枚でもコストは 6・6・7・7・5、
      パワーは 7000・7500・7000・10000・5500、ブレイク数も W が4枚と無しが1枚、
      文明も 光闇・光火・闇自然・火自然・光とばらばらで、持っている仕組みも
      オシオキムーン／マジボンバー／フシギバース／キリフダッシュ／スマッシュ・バーストと全部違う。
      サイクルだと思って数値や能力を流用すると全部間違う。
    ・《キング・ザ・ベスト》は《キング・ザ・スロットン7／7777777》（env19）とは別のカードで、
      コスト7・パワー7000・火単色のジョーカーズ。踏み倒すのは**山札の下から3枚**（上ではない）。
    ・《マジボンバー》は名前から「出た時に手札から出す」能力だと思い込みやすいが、
      実際は「**攻撃する時**、山札の上から1枚を見て、手札か**その1枚**から出す」。
      キーワードの専用ページで定義を確かめ直した。
    ・《輝晶 エヴァ-3》の「ササゲール3」は注釈文なしで能力欄の最後に1行だけ書かれている
      （ほかのササゲール持ちは注釈文つき）。見落としやすい。
    ・《ドドンガ轟キャイエス》の破壊は「相手のクリーチャーを**2体まで**」で、
      元ネタの《ドンドン火噴くナウ》の「好きな数」より狭い。
    ・《ヒトリダチ キャンベロ》は《奇石 ミクセル／ジャミング・チャフ》のジョーカーズ版で、
      置き換え（かわりにマナへ）ではなく「出た時、相手が**山札の下に置く**」。
      《クイーン&かぼちゃうちゃう》とは誘発の仕方が違う。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, opp_all
from envcards.env0 import EXLOST, exlife_enter, exlife_rep, worst_own

try:                                   # 闇のスーパー・S・トリガーは《魔王ザダン》（env31）から参照される
    from envcards.env31 import SUPER_S
except Exception:                      # env31 が無くても動くように
    SUPER_S = {}

W = "https://dmwiki.net/"
SRC = {
    "k32_meiou": W + "《冥王の顎》",
    "k32_kingbest": W + "《キング・ザ・ベスト》",
    "k32_dodonga": W + "《ドドンガ轟キャイエス》",
    "k32_kondama": W + "《大地 コンダマ-2》",
    "k32_cocoon": W + "《コクーン・ツェッペリン》",
    "k32_eva": W + "《輝晶 エヴァ-3》",
    "k32_hamides": W + "《冥運逆夢 ハミデスナスカ》",
    "k32_valirauza": W + "《雷星逆夢 ヴァリ-我-ラウザス》",
    "k32_vaipoi": W + "《魔具 ヴァイポイズ-4》",
    "k32_andaste": W + "《昆怪逆夢 アンダステリオン》",
    "k32_blago": W + "《罰空逆夢 ブラゴチャーンド》",
    "k32_thewinny": W + "《銃初逆夢 ザ・ウィニー／ジョリー・ザ・スパーク》",
    "k32_shimp": W + "《輝晶 シンプ-2》",
    "k32_canbero": W + "《ヒトリダチ キャンベロ》",
    "k32_maruhavu": W + "《輝晶 マルハヴ-2》",
}

ELEM = "CTX"                 # エレメント（バトルゾーンのクリーチャー・タマシード・クロスギア）
SASAGEL = {}                 # ササゲール：key -> 少なくするコスト
JBIG_NO = ("k30_kento", "k30_jolagang", "k31_niyani", "k32_canbero")   # Jビッグ1を含む能力（Jビッグ1の元にできない）
SST = "スーパー・S・トリガー"


# ================================================================ 共通の小道具
def _evo_on(s, i, k):
    """踏み倒す時に重ねる進化元（進化でなければ None、進化元が無ければ "x"＝出せない）"""
    c = BY_KEY[k]
    if not c.evo or c.neo:
        return None
    return s.evo_src(i, k) or "x"


def _minus_power(s, i, t, n):
    """相手のクリーチャー t のパワーを n 下げる（0以下になれば破壊される）"""
    t.pw -= n
    s.ev(f"　{t.c.name} のパワーを-{n}")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def _take_shield(s, j, dest):
    """プレイヤー j のシールドを1つ（裏向きを優先して）選び、dest に置く。置いたカードか None。
    S・トリガーは使わない（「手札に加える」「墓地に置く」どちらも、この効果では受けを使えない）。

    シールドゾーンの出口は s.take_shield 1か所なので、そこを通す
    （SHIELDDEST＝シールド・ゴーと SHIELDOUT がここで正しく働く）"""
    p = s.P[j]
    if not p.sh:
        return None
    idx = next((x for x in range(len(p.sh) - 1, -1, -1) if not p.sh[x][1]), len(p.sh) - 1)
    got = s.take_shield(j, idx, dest)
    return got[0] if got is not None else None


def _depth(s, i, key, cap=2):
    """入れ子の深さを数える（効果が互いを呼び合って止まらなくなるのを防ぐ）。
    使えるなら元の深さを返し、深すぎるなら None"""
    p = s.P[i]
    d = p.x.get(key, 0)
    if d >= cap:
        return None
    p.x[key] = d + 1
    return d


def _undepth(s, i, key, d):
    s.P[i].x[key] = d


def _jbig_cands(s, i, u):
    """Jビッグ1の元にできる、自分の他のジョーカーズ（Jビッグ1を含む能力のカードは除く）"""
    return [z for z in s.P[i].board
            if z is not u and z.c.kind == "C" and "jokers" in z.c.races
            and z.k not in JBIG_NO and E.ENTER.get(z.k) is not None]


def _jbig(s, i, u):
    """Jビッグ1：自分の他のジョーカーズの、出た時にトリガーする能力を1つ使う（重要度のいちばん高いもの）"""
    cands = _jbig_cands(s, i, u)
    if not cands or s.over:
        return False
    d = _depth(s, i, "k32_jbig")
    if d is None:
        return False
    try:
        z = max(cands, key=lambda x: (E.PRI[x.k], x.uid))
        s.ev(f"　Jビッグ1：{z.c.name} の「出た時」の能力を使う")
        E.ENTER[z.k](s, i, z)
    finally:
        _undepth(s, i, "k32_jbig", d)
    return True


# ---------------------------------------------------------------- スーパー・S・トリガー
def _sst_cast(key, sfn):
    """スーパー・S・トリガー：このカードを自分のシールドゾーンから手札に加える時、
    コストを支払わずにすぐ唱える。その時自分のシールドが1つもなければ（nsh==0）、S能力も使う。

    SHIELDCAST なので、ブレイクでも効果でシールドから手札に加わる時でも通り、
    「手札に来たのに唱えず、同じターンに手札から唱えた」時にS能力が付くこともない。
    S能力を呪文のどこで使うかはカードごとに違う（《ドドンガ轟キャイエス》は破壊より先に働かせる）ので、
    印を立てて `spell=` の中の `_sst_used` で見る形にしている"""
    def f(s, i, k, nsh):
        p = s.P[i]
        if k not in p.hand or not s.spell_ok(i, BY_KEY[k].cost):
            return False                       # 唱えられないなら、ふつうに手札に加えたままにする
        p.hand.remove(k)
        s.trig[i] += 1
        s.ev(f"　{SST}：{BY_KEY[k].name}")
        if nsh <= 0:
            p.x["k32_sst"] = key               # シールドが1つもないのでS能力も使える
        try:
            s.cast(i, k)
        finally:
            if s.P[i].x.get("k32_sst") == key:
                s.P[i].x["k32_sst"] = None
        return True
    return f


def _sst_used(s, i, key):
    """この呪文が、自分のシールドが1つもない状態でシールドゾーンから唱えられたか（S能力を使えるか）"""
    p = s.P[i]
    if p.x.get("k32_sst") == key:
        p.x["k32_sst"] = None
        return True
    return False


def _super_s(key, sfn):
    """スーパー・S・トリガーを1か所で登録する。
    SUPER_S は env31 の《七王を統べる者 魔王ザダン》が
    「シールドがないものとしてS能力も使う」ために引く表（env31 と持ち合っている）"""
    SUPER_S[key] = sfn
    return _sst_cast(key, sfn)


# ---------------------------------------------------------------- ササゲール（共通）
def _sasa_n(s, u):
    """u が今もっているササゲールの数（コンダマ-2 がこのターンだけ与えた分も足す）"""
    n = SASAGEL.get(u.k, 0)
    g = u.x.get("k32_sasa")
    if g is not None and g[0] == s.turn:
        n += g[1]
    return n


def _sasa_holders(s, i):
    """自分のササゲール持ちのエレメント（失うのがいちばん安いものから）"""
    out = [u for u in s.P[i].board if u.c.kind in ELEM and _sasa_n(s, u) > 0]
    out.sort(key=lambda u: (s.val(u), u.uid))
    return out


def fa_sasagel(s, i, av, cv):
    """ササゲール：自分のディスペクター・クリーチャーの召喚コストを少なくし、
    そのぶんのエレメントを破壊して召喚する手を足す。
    普通に召喚できる時はササゲールを使わない（払えるのに自分のエレメントを失うのは損なので）"""
    p = s.P[i]
    hs = _sasa_holders(s, i)
    if not hs:
        return []
    out = []
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or "dispector" not in c.races:
            continue
        base = s.ccost(i, k, av)
        if base >= 99 or base <= av:
            continue                       # 普通の召喚の手がもうある
        red, use, n = 0, [], base
        for z in hs:
            red += _sasa_n(s, z)
            use.append(z.uid)
            n = max(0, base - red)
            if n <= av:
                break
        if n > av or (n > 0 and not cv.issuperset(c.civ)):
            continue
        if s.fate(i, k, "hand", True) != "ok":
            continue
        out.append(("x:k32_sasa", k, n, tuple(use)))
    return out


def ap_sasagel(s, a):
    i = s.tp
    p = s.P[i]
    k, n, uids = a[1], a[2], a[3]
    if k not in p.hand or len(p.mana) - p.mused < n:
        return
    hs = [z for z in p.board if z.uid in uids]
    if len(hs) != len(uids):
        return
    p.hand.remove(k)
    p.mused += n
    s.ev(f"ササゲール：{BY_KEY[k].name} を{n}マナで召喚（{len(hs)}つをささげる）")
    for z in hs:                           # ディスペクターが出る前にササゲール持ちが破壊される
        if z in p.board:
            s.leave(i, z, "grave", destroy=True)
    if s.over:
        return
    on = _evo_on(s, i, k)
    if on == "x":
        p.grave.append(k)
        return
    s.enter(i, k, "hand", True, on=on)


# ================================================================ 17/77 冥王の顎
def _meiou_s(s, i):
    """S-コストの合計が8以下になるようにクリーチャーを好きな数、自分の墓地から出す"""
    p = s.P[i]
    left = 8
    for _ in range(8):
        best, bv, bon = None, -1, None
        for k in sorted(set(p.grave)):
            c = BY_KEY[k]
            if c.kind != "C" or c.cost > left or E.PRI[k] <= bv:
                continue
            on = _evo_on(s, i, k)
            if on == "x" or s.fate(i, k, "grave", False) != "ok":
                continue
            best, bv, bon = k, E.PRI[k], on
        if best is None:
            return
        p.grave.remove(best)
        left -= BY_KEY[best].cost
        s.ev(f"　S能力：墓地の {BY_KEY[best].name} を出す（残り{left}）")
        s.enter(i, best, "grave", False, on=bon)
        if s.over:
            return


def sp_meiou(s, i):
    """自分の山札の上から3枚を墓地に置く。相手のクリーチャー1体のパワーを、自分の墓地1枚につき-1000"""
    s.mill(i, 3)
    t = s.target(i)
    if t is not None:
        _minus_power(s, i, t, 1000 * len(s.P[i].grave))
    if _sst_used(s, i, "k32_meiou") and not s.over:
        _meiou_s(s, i)


add("k32_meiou", "冥王の顎", 4, "D", kind="S", trig=True, pri=7, roles="trg rem fin",
    spell=sp_meiou, shieldcast=_super_s("k32_meiou", _meiou_s),
    text=f"{SST}（このカードを自分のシールドゾーンから手札に加える時、コストを支払わずにすぐ唱えてもよい。"
         "その時自分のシールドが1つもなければ、このカードにS能力を与える）。"
         "自分の山札の上から3枚を墓地に置く。"
         "相手のクリーチャーを1体選ぶ（重要度のいちばん高いもの）。このターン、そのクリーチャーのパワーを、"
         "自分の墓地にあるカード1枚につき-1000する（パワーが0以下になれば破壊される）。"
         "S-コストの合計が8以下になるようにクリーチャーを好きな数、自分の墓地から出す"
         "（重要度の高いものから順に、入るだけ出す）",
    source=SRC["k32_meiou"])


# ================================================================ 18/77 キング・ザ・ベスト
def a_kingbest(s, i, u):
    """攻撃する時、自分の山札の下から3枚を表向きにする。その中からコスト8以下のジョーカーズ・クリーチャーを
    1体出してもよい。残りを好きな順序で山札の上に置く"""
    p = s.P[i]
    n = min(3, len(p.deck))
    if n <= 0:
        return
    seen = [p.deck.pop(0) for _ in range(n)]
    s.ev(f"　キング・ザ・ベスト：山札の下から{n}枚を表向きに")
    best, bv, bon = None, -1, None
    for k in seen:
        c = BY_KEY[k]
        if c.kind != "C" or c.cost > 8 or "jokers" not in c.races or E.PRI[k] <= bv:
            continue
        on = _evo_on(s, i, k)
        if on == "x" or s.fate(i, k, "deck", False) != "ok":
            continue
        best, bv, bon = k, E.PRI[k], on
    if best is not None:
        seen.remove(best)
    for k in sorted(seen, key=lambda x: (E.PRI[x], x)):     # 重要度の高いものが山札の上になるように
        p.deck.append(k)
    if best is not None:
        s.ev(f"　キング・ザ・ベスト：{BY_KEY[best].name} を出す")
        s.enter(i, best, "deck", False, on=bon)


add("k32_kingbest", "キング・ザ・ベスト", 7, "F", power=7000, brk=2, sa=True, gs=True, races=("jokers",),
    pri=9, roles="atk fin trg",
    attack=a_kingbest,
    text="G・ストライク（このカードを自分のシールドゾーンから手札に加える時、表向きにし、"
         "相手のクリーチャーを1体選んでもよい。このターン、それは攻撃できない）。"
         "スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが攻撃する時、自分の山札の下から3枚を表向きにする。"
         "その中からコスト8以下のジョーカーズ・クリーチャーを1体、出してもよい"
         "（重要度のいちばん高いもの）。残りを好きな順序で山札の上に置く（重要度の高いものを上に）",
    source=SRC["k32_kingbest"])


# ================================================================ 19/77 ドドンガ轟キャイエス
def _dodonga_s(s, i):
    """S-このターン、相手のクリーチャーが破壊された時、シールドを1つ選び、持ち主の墓地に置いてもよい"""
    s.P[i].x["k32_dodonga"] = s.turn
    s.ev("　S能力：このターン、相手のクリーチャーが破壊されるたびに相手のシールド1つを墓地に置く")


def lw_dodonga(s, j, u, dest, destroy):
    """ドドンガ轟キャイエスのS能力（このターンのあいだ働く遅れた誘発）"""
    if not destroy or u.c.kind != "C":
        return
    i = 1 - j
    if s.P[i].x.get("k32_dodonga") != s.turn or s.over:
        return
    d = _depth(s, i, "k32_dod_d")
    if d is None:
        return
    try:
        k = _take_shield(s, j, "grave")
        if k is not None:
            s.ev(f"　S能力：{u.c.name} が破壊されたので相手のシールド1つを墓地に置く")
    finally:
        _undepth(s, i, "k32_dod_d", d)


def _best_kill(s, i, budget):
    """コストの合計が budget 以下になるように相手のクリーチャーを2体まで選ぶ（値打ちの合計がいちばん大きい組）"""
    cands = sorted(opp_all(s, i), key=lambda z: (-s.val(z), z.uid))
    best, bv = (), 0
    for a in range(len(cands)):
        for b in range(a, len(cands)):
            pick = (cands[a],) if a == b else (cands[a], cands[b])
            if sum(z.c.cost for z in pick) > budget:
                continue
            v = sum(s.val(z) for z in pick)
            if v > bv:
                best, bv = pick, v
    return best, bv


def sp_dodonga(s, i):
    """自分の手札を1枚捨てる。その後、コストの合計がその捨てたカードのコスト以下になるように、
    相手のクリーチャーを2体まで選び、破壊する。カードを2枚引く"""
    p = s.P[i]
    if _sst_used(s, i, "k32_dodonga"):
        _dodonga_s(s, i)                   # 破壊より先に働かせる（破壊のたびにシールドを落とすため）
    if p.hand:
        bk, bpick, bsc = None, (), None
        for k in sorted(set(p.hand)):
            pick, v = _best_kill(s, i, BY_KEY[k].cost)
            sc = (v, -E.PRI[k], k)
            if bsc is None or sc > bsc:
                bk, bpick, bsc = k, pick, sc
        if bk is not None:
            s.discard(i, bk)
            s.ev(f"　ドドンガ轟キャイエス：{BY_KEY[bk].name}（コスト{BY_KEY[bk].cost}）を捨てた")
            for z in bpick:
                if s.over:
                    break
                if z in s.P[1 - i].board:
                    s.leave(1 - i, z, "grave", by_opp=True, destroy=True)
    if not s.over:
        s.draw(i, 2)


add("k32_dodonga", "ドドンガ轟キャイエス", 5, "F", kind="S", trig=True, pri=7, roles="trg rem draw",
    spell=sp_dodonga, shieldcast=_super_s("k32_dodonga", _dodonga_s), leavewatch=lw_dodonga,
    text=f"{SST}（このカードを自分のシールドゾーンから手札に加える時、コストを支払わずにすぐ唱えてもよい。"
         "その時自分のシールドが1つもなければ、このカードにS能力を与える）。"
         "S-このターン、相手のクリーチャーが破壊された時、シールドを1つ選び、持ち主の墓地に置いてもよい"
         "（相手のシールドを、裏向きのものから選ぶ）。"
         "自分の手札を1枚捨てる。その後、コストの合計がその捨てたカードのコスト以下になるように、"
         "相手のクリーチャーを2体まで選び、破壊する（倒せる相手の値打ちの合計がいちばん大きくなる捨て札を選び、"
         "同じなら重要度のいちばん低い札を捨てる）。カードを2枚引く",
    source=SRC["k32_dodonga"])


# ================================================================ 20/77 大地 コンダマ-2
def mi_kondama(s, i, k, src):
    """ディスタス・カードまたはディスペクター・カードを自分のマナゾーンに置いた時、そのカードをアンタップする"""
    if not s.has(i, "k32_kondama"):
        return
    r = BY_KEY[k].races
    if "distas" not in r and "dispector" not in r:
        return
    p = s.P[i]
    if p.mused > 0:
        p.mused -= 1
        s.ev(f"　大地 コンダマ-2：マナに置いた {BY_KEY[k].name} をアンタップ")


def ts_kondama(s, i, u):
    """自分のターンのはじめに、このターン、自分のエレメント1つに「ササゲール2」を与える"""
    els = [z for z in s.P[i].board if z.c.kind in ELEM]
    free = [z for z in els if _sasa_n(s, z) == 0]
    cands = free or els
    if not cands:
        return
    z = min(cands, key=lambda x: (s.val(x), x.uid))
    z.x["k32_sasa"] = (s.turn, 2)
    s.ev(f"　大地 コンダマ-2：{z.c.name} にこのターン「ササゲール2」を与える")


add("k32_kondama", "大地 コンダマ-2", 3, "N", power=4000, gs=True, races=("gransect", "distas"),
    pri=5, roles="acc trg",
    manain=mi_kondama, tstart=ts_kondama,
    freeacts=fa_sasagel, actapply={"x:k32_sasa": ap_sasagel},      # ← ササゲール5枚ぶんの手をここでまとめて登録
    text="G・ストライク（このカードを自分のシールドゾーンから手札に加える時、表向きにし、"
         "相手のクリーチャーを1体選んでもよい。このターン、それは攻撃できない）。"
         "ディスタス・カードまたはディスペクター・カードを自分のマナゾーンに置いた時、そのカードをアンタップする。"
         "ササゲール2（自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたらこのエレメントを破壊する。ただしコストは0以下にならない）。"
         "自分のターンのはじめに、このターン、自分のエレメント1つに「ササゲール2」を与える"
         "（ササゲールを持っていないエレメントのうち、失うのがいちばん安いものに与える）",
    source=SRC["k32_kondama"])
SASAGEL["k32_kondama"] = 2


# ================================================================ 21/77 コクーン・ツェッペリン
def _cocoon_s(s, i):
    """S-自分のマナゾーンにあるカードの枚数以下のコストのクリーチャーを1体、自分のマナゾーンから出してもよい"""
    n = len(s.P[i].mana)
    u = s.revive(i, lambda c: c.cost <= n, src="mana")
    if u is not None:
        s.ev("　S能力：マナゾーンからクリーチャーを出した")


def _cocoon_pick(s, i):
    """墓地を山札の下に戻すプレイヤーを選ぶ。自分の山札が10枚以下なら自分（山札の回復）、
    そうでなければ相手の墓地が5枚以上の時だけ相手（墓地を使うデッキへの妨害）"""
    p, o = s.P[i], s.P[1 - i]
    if len(p.deck) <= 10 and p.grave:
        return i
    if len(o.grave) >= 5:
        return 1 - i
    return None


def sp_cocoon(s, i):
    """自分の山札の上から1枚をマナゾーンに置く。プレイヤーを1人選んでもよい。
    そのプレイヤーは自身の墓地をシャッフルし、山札の下に置く"""
    s.ramp(i, 1, tapped=False)            # 「マナゾーンに置く」なのでアンタップのまま（多色はタップして入る）
    j = _cocoon_pick(s, i)
    if j is not None:
        q = s.P[j]
        g = list(q.grave)
        del q.grave[:]
        s.rng.shuffle(g)
        for k in g:
            q.deck.insert(0, k)
        s.ev(f"　コクーン・ツェッペリン：{'自分' if j == i else '相手'}の墓地{len(g)}枚を山札の下へ")
    if _sst_used(s, i, "k32_cocoon") and not s.over:
        _cocoon_s(s, i)


add("k32_cocoon", "コクーン・ツェッペリン", 3, "N", kind="S", trig=True, pri=5, roles="trg acc dis",
    spell=sp_cocoon, shieldcast=_super_s("k32_cocoon", _cocoon_s),
    text=f"{SST}（このカードを自分のシールドゾーンから手札に加える時、コストを支払わずにすぐ唱えてもよい。"
         "その時自分のシールドが1つもなければ、このカードにS能力を与える）。"
         "自分の山札の上から1枚をマナゾーンに置く。"
         "プレイヤーを1人選んでもよい。そのプレイヤーは自身の墓地をシャッフルし、山札の下に置く"
         "（自分の山札が10枚以下なら自分を、そうでなければ相手の墓地が5枚以上の時だけ相手を選ぶ）。"
         "S-自分のマナゾーンにあるカードの枚数以下のコストのクリーチャーを1体、自分のマナゾーンから出してもよい"
         "（進化クリーチャーは進化元が必要なので選ばない）",
    source=SRC["k32_cocoon"])


# ================================================================ 22/77 輝晶 エヴァ-3
def _eva_tap(s, i):
    """相手のクリーチャーを1体選び、タップする。次の自分のターンのはじめまでアンタップしない"""
    t = s.target(i, lambda x: not x.tap) or s.target(i)
    if t is None:
        return
    s.tap_cre(1 - i, t)
    t.frz = 1
    s.ev(f"　輝晶 エヴァ-3：{t.c.name} をタップし、次の自分のターンのはじめまでアンタップさせない")


def e_eva(s, i, u):
    _eva_tap(s, i)


def si_eva(s, i, k, up):
    """このカードが表向きで自分のシールドゾーンに置かれた時"""
    if k != "k32_eva" or not up:
        return
    _eva_tap(s, i)


def _eva_summon(s, i):
    """表向きで自分のシールドゾーンにあるエヴァ-3を、コストを支払ったものとして召喚する"""
    p = s.P[i]
    done = 0
    for _ in range(4):
        j = next((x for x in range(len(p.sh)) if p.sh[x][1] and p.sh[x][0] == "k32_eva"), None)
        if j is None or s.over:
            break
        if s.fate(i, "k32_eva", "shield", True) != "ok":
            break
        s.take_shield(i, j, "zone")        # シールドゾーンの出口はここ1か所（行き先はバトルゾーン）
        s.ev("ギャラクシールド：輝晶 エヴァ-3 をコストを支払ったものとして召喚")
        s.enter(i, "k32_eva", "shield", True)
        done += 1
    return done


def ts_eva(s, i):
    """自分のターンのはじめに、表向きで自分のシールドゾーンにあればコストを支払ったものとして召喚する
    （TURNSTART はバトルゾーンに何もなくても呼ばれるので、これ1本で足りる）"""
    if not any(up and k == "k32_eva" for k, up in s.P[i].sh):
        return
    _eva_summon(s, i)


def fa_eva(s, i, av, cv):
    p = s.P[i]
    if "k32_eva" in p.hand and av >= 2 and {"L", "W"} <= cv and p.ban != 3 and not s.has(1 - i, "fujin"):
        return [("x:k32_gal",)]
    return []


def ap_eva_gal(s, a):
    i = s.tp
    p = s.P[i]
    if "k32_eva" not in p.hand or len(p.mana) - p.mused < 2:
        return
    p.hand.remove("k32_eva")
    p.mused += 2
    s.ev("ギャラクシールド[光/水(2)]：輝晶 エヴァ-3 を表向きのシールドに")
    if not s.add_shield(i, "k32_eva", True):
        p.hand.append("k32_eva")
        p.mused -= 2


add("k32_eva", "輝晶 エヴァ-3", 3, "LW", power=3000,
    races=("metallica", "angelcommand", "command", "distas", "teamgalaxy"), pri=5, roles="dis shd",
    enter=e_eva, shieldin=si_eva, turnstart=ts_eva, freeacts=fa_eva,
    actapply={"x:k32_gal": ap_eva_gal},
    text="ギャラクシールド[光/水(2)]（このカードを実行するコストのかわりに、[光/水(2)]を支払って"
         "このカードを表向きでシールド化してもよい）。"
         "自分のターンのはじめに、このクリーチャーが表向きで自分のシールドゾーンにあれば、"
         "コストを支払ったものとして召喚する。"
         "このカードが表向きで自分のシールドゾーンに置かれた時またはこのクリーチャーが出た時、"
         "相手のクリーチャーを1体選び、タップする（アンタップしているもの、重要度の高いもの）。"
         "次の自分のターンのはじめまで、それはアンタップしない。"
         "ササゲール3（自分のディスペクター・クリーチャーの召喚コストを3少なくしてもよい。"
         "そうしたらこのエレメントを破壊する。ただしコストは0以下にならない）",
    source=SRC["k32_eva"])
SASAGEL["k32_eva"] = 3


# ================================================================ 23/77 冥運逆夢 ハミデスナスカ
def _oshioki(s, i):
    """＜オシオキムーン＞カードが自分のシールドゾーンを離れた時、
    相手は自身のアンタップしているクリーチャーを1体選び、破壊する"""
    if not s.has(i, "k32_hamides") or s.over:
        return
    d = _depth(s, i, "k32_osh_d", 3)
    if d is None:
        return
    try:
        z = worst_own(s, 1 - i, lambda x: not x.tap)
        if z is None:
            return
        s.ev(f"　オシオキムーン：相手は {z.c.name} を選んで破壊する")
        s.leave(1 - i, z, "grave", destroy=True)
    finally:
        _undepth(s, i, "k32_osh_d", d)


def so_hamides(s, i, k, up, dest):
    _oshioki(s, i)


EXLOST["k32_hamides"] = lambda s, i, u: _oshioki(s, i)


def a_hamides(s, i, u):
    """攻撃する時、自分の山札の上から1枚をシールド化してもよい"""
    if s.add_shield(i):
        s.ev("　冥運逆夢 ハミデスナスカ：山札の上から1枚をシールド化")


add("k32_hamides", "冥運逆夢 ハミデスナスカ", 6, "LD", power=7000, brk=2, blocker=True,
    races=("dispector", "demoncommand", "command", "metallica", "gekkououkoku"), pri=9, roles="blk rem shd fin",
    enter=exlife_enter, leaverep=exlife_rep, attack=a_hamides, shieldout=so_hamides,
    text="EXライフ（このクリーチャーを出す時、自分の山札の上から1枚をシールド化する。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。ブロッカー。W・ブレイカー。"
         "このクリーチャーが攻撃する時、自分の山札の上から1枚をシールド化してもよい。"
         "＜オシオキムーン＞カードが自分のシールドゾーンを離れた時、"
         "相手は自身のアンタップしているクリーチャーを1体選び、破壊する（相手は失うのがいちばん安いものを選ぶ）",
    note="オシオキムーンは、ブレイク・効果でシールドが離れた時・このカード自身のEXライフのシールドが"
         "離れた時には誘発するが、**自分の他のクリーチャーのEXライフのシールドが離れた時**には誘発しない。"
         "EXライフのシールドはこのシミュレーターではシールドゾーン（p.sh）に入らずクリーチャーが抱えていて、"
         "それが離れる時に呼ばれるのは envcards.env0 の EXLOST のうち**そのクリーチャー自身のキーの分だけ**"
         "なので、他のカードのEXライフを見る差し込み口がいまのエンジンにも無い",
    status="partial", source=SRC["k32_hamides"])


# ================================================================ 24/77 雷星逆夢 ヴァリ-我-ラウザス
def a_valirauza(s, i, u):
    """マジボンバー6：攻撃する時、自分の山札の上から1枚を見る。その後、コスト6以下のクリーチャーを1体、
    自分の手札またはその1枚から出してもよい"""
    p = s.P[i]
    top = p.deck[-1] if p.deck else None
    cands = [("hand", k) for k in sorted(set(p.hand))]
    if top is not None:
        cands.append(("deck", top))
    best, bv, bsrc, bon = None, -1, None, None
    for src, k in cands:
        c = BY_KEY[k]
        if c.kind != "C" or c.cost > 6 or E.PRI[k] <= bv:
            continue
        on = _evo_on(s, i, k)
        if on == "x" or s.fate(i, k, src, False) != "ok":
            continue
        best, bv, bsrc, bon = k, E.PRI[k], src, on
    if best is None:
        return
    if bsrc == "hand":
        p.hand.remove(best)
    else:
        p.deck.pop()
    s.ev(f"　マジボンバー6：{'手札' if bsrc == 'hand' else '山札の上'}の {BY_KEY[best].name} を出す")
    s.enter(i, best, bsrc, False, on=bon)


add("k32_valirauza", "雷星逆夢 ヴァリ-我-ラウザス", 6, "LF", power=7500, brk=2, sa=True,
    races=("dispector", "nitrodragon", "dragon", "beatjockey", "teambomber"), pri=9, roles="atk fin",
    enter=exlife_enter, leaverep=exlife_rep, attack=a_valirauza,
    text="EXライフ（このクリーチャーを出す時、自分の山札の上から1枚をシールド化する。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。"
         "スピードアタッカー。W・ブレイカー。"
         "マジボンバー6（このクリーチャーが攻撃する時、自分の山札の上から1枚を見る。その後、"
         "コスト6以下のクリーチャーを1体、自分の手札または山札の上から出してもよい。"
         "重要度のいちばん高いものを出す）",
    source=SRC["k32_valirauza"])


# ================================================================ 25/77 魔具 ヴァイポイズ-4
def e_vaipoi(s, i, u):
    """出た時、相手は自身のクリーチャーを1体選び、破壊する"""
    z = worst_own(s, 1 - i)
    if z is None:
        return
    s.ev(f"　魔具 ヴァイポイズ-4：相手は {z.c.name} を選んで破壊する")
    s.leave(1 - i, z, "grave", destroy=True)


def fa_vaipoi(s, i, av, cv):
    """ムゲンクライム2：自分のクリーチャーを2体タップし、[水/闇(2)]支払って手札または墓地から召喚する"""
    p = s.P[i]
    if av < 2 or not {"W", "D"} <= cv:
        return []
    if len([z for z in p.board if z.c.kind == "C" and not z.tap]) < 2:
        return []
    out = []
    for zn, zone in (("hand", p.hand), ("grave", p.grave)):
        if "k32_vaipoi" in zone and s.fate(i, "k32_vaipoi", zn, True) == "ok":
            out.append(("x:k32_mugen", zn))
    return out


def ap_vaipoi(s, a):
    i = s.tp
    p = s.P[i]
    zn = a[1]
    zone = p.hand if zn == "hand" else p.grave
    if "k32_vaipoi" not in zone or len(p.mana) - p.mused < 2:
        return
    cands = sorted((z for z in p.board if z.c.kind == "C" and not z.tap), key=lambda z: (s.val(z), z.uid))
    if len(cands) < 2:
        return
    for z in cands[:2]:
        s.tap_cre(i, z)
    p.mused += 2
    zone.remove("k32_vaipoi")
    s.ev(f"ムゲンクライム2：魔具 ヴァイポイズ-4（{'手札' if zn == 'hand' else '墓地'}から召喚）")
    s.enter(i, "k32_vaipoi", zn, True)


add("k32_vaipoi", "魔具 ヴァイポイズ-4", 5, "WD", power=5000,
    races=("mafigang", "madogu", "distas", "teamzero"), pri=7, roles="rem atk",
    enter=e_vaipoi, unbok=lambda s, i, u: u.k == "k32_vaipoi",
    freeacts=fa_vaipoi, actapply={"x:k32_mugen": ap_vaipoi},
    text="＜ムゲンクライム＞2（自分のクリーチャーを2体タップし、[水/闇(2)]支払って、"
         "このカードを自分の手札または墓地から召喚してもよい。タップするのは失うのが安い2体）。"
         "このクリーチャーが出た時、相手は自身のクリーチャーを1体選び、破壊する"
         "（相手は失うのがいちばん安いものを選ぶ）。"
         "このクリーチャーはブロックされない。"
         "ササゲール4（自分のディスペクター・クリーチャーの召喚コストを4少なくしてもよい。"
         "そうしたらこのエレメントを破壊する。ただしコストは0以下にならない）",
    source=SRC["k32_vaipoi"])
SASAGEL["k32_vaipoi"] = 4


# ================================================================ 26/77 昆怪逆夢 アンダステリオン
def a_andaste(s, i, u):
    """攻撃する時、ディスタスを1つ、自分の墓地から出してもよい"""
    p = s.P[i]
    best, bv, bon = None, -1, None
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if c.kind not in ELEM or "distas" not in c.races or E.PRI[k] <= bv:
            continue
        if c.kind == "C":
            on = _evo_on(s, i, k)
            if on == "x" or s.fate(i, k, "grave", False) != "ok":
                continue
        else:
            on = None
        best, bv, bon = k, E.PRI[k], on
    if best is None:
        return
    p.grave.remove(best)
    s.ev(f"　昆怪逆夢 アンダステリオン：墓地の {BY_KEY[best].name} を出す")
    if BY_KEY[best].kind == "C":
        s.enter(i, best, "grave", False, on=bon)
    else:
        s.place_tama(i, best)


def fa_andaste(s, i, av, cv):
    """フシギバース[闇/自然(9)]：自分のクリーチャー1体をマナゾーンに置き、
    9からそのクリーチャーのコストを引いた数（最低2）を支払って墓地から召喚する"""
    p = s.P[i]
    if "k32_andaste" not in p.grave or not {"D", "N"} <= cv:
        return []
    if s.fate(i, "k32_andaste", "grave", True) != "ok":
        return []
    cands = [z for z in p.board if z.c.kind == "C" and max(2, 9 - z.c.cost) <= av]
    if not cands:
        return []
    cheap = min(cands, key=lambda z: (s.val(z), z.uid))          # 失うのがいちばん安い
    light = min(cands, key=lambda z: (max(2, 9 - z.c.cost), s.val(z), z.uid))   # マナがいちばん安い
    out, seen = [], set()
    for z in (cheap, light):
        if z.uid in seen:
            continue
        seen.add(z.uid)
        out.append(("x:k32_fushigi", z.uid, max(2, 9 - z.c.cost)))
    return out


def ap_andaste(s, a):
    i = s.tp
    p = s.P[i]
    z = next((x for x in p.board if x.uid == a[1] and x.c.kind == "C"), None)
    if z is None or "k32_andaste" not in p.grave or len(p.mana) - p.mused < a[2]:
        return
    k = z.k
    if not s.leave(i, z, "mana"):
        return
    if k in p.mana and not E.MULTI[k]:                 # タップしてマナゾーンに置く
        p.mused = min(len(p.mana), p.mused + 1)
    if "k32_andaste" not in p.grave or len(p.mana) - p.mused < a[2]:
        return
    p.mused += a[2]
    p.grave.remove("k32_andaste")
    s.ev(f"フシギバース[闇/自然(9)]：{BY_KEY[k].name} をマナに置いて 昆怪逆夢 アンダステリオン を{a[2]}マナで召喚")
    s.enter(i, "k32_andaste", "grave", True)


add("k32_andaste", "昆怪逆夢 アンダステリオン", 7, "DN", power=7000, brk=2, mach=True,
    races=("dispector", "devilmask", "gransect", "fujijuoukoku"), pri=10, roles="rem atk fin",
    enter=exlife_enter, leaverep=exlife_rep, attack=a_andaste,
    freeacts=fa_andaste, actapply={"x:k32_fushigi": ap_andaste},
    text="EXライフ（このクリーチャーを出す時、自分の山札の上から1枚をシールド化する。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。"
         "マッハファイター。W・ブレイカー。"
         "このクリーチャーが攻撃する時、ディスタスを1つ、自分の墓地から出してもよい"
         "（重要度のいちばん高いもの）。"
         "＜フシギバース＞[闇/自然(9)]（自分のクリーチャーを1体タップしてマナゾーンに置き、"
         "[闇/自然(9)]からそのクリーチャーのコストを引いた数のコストを支払って、"
         "このクリーチャーを自分の墓地から召喚してもよい。ただしコストは[闇/自然(2)]より少なくならない。"
         "マナに置くのは、失うのがいちばん安いクリーチャーと、支払いがいちばん軽くなるクリーチャーの2通りから選ぶ）",
    source=SRC["k32_andaste"])


# ================================================================ 27/77 罰空逆夢 ブラゴチャーンド
def bw_blago(s, ai, di, n):
    """キリフダッシュの条件：いま攻撃しているクリーチャーがこの攻撃中にシールドをブレイクしたことを覚える"""
    if "k32_blago" not in s.P[ai].hand:
        return
    u = s.atk
    if u is not None:
        s.P[ai].x["k32_brk"] = (s.turn, u.uid)


def ae_blago(s, i, u):
    """キリフダッシュ[火/自然(4)]：自分のクリーチャーの攻撃の終わりに、
    そのクリーチャーがその攻撃中にシールドをブレイクしていれば、手札から4マナで召喚してもよい"""
    p = s.P[i]
    if "k32_blago" not in p.hand:
        return
    if p.x.get("k32_brk") != (s.turn, u.uid):
        return
    if len(p.mana) - p.mused < 4 or not {"F", "N"} <= E.civs(p):
        return
    if s.fate(i, "k32_blago", "hand", True) != "ok":
        return
    p.hand.remove("k32_blago")
    p.mused += 4
    s.ev("　キリフダッシュ[火/自然(4)]：罰空逆夢 ブラゴチャーンド を4マナで召喚")
    s.enter(i, "k32_blago", "hand", True)


add("k32_blago", "罰空逆夢 ブラゴチャーンド", 7, "FN", power=10000, brk=2, sa=True, mach=True,
    races=("dispector", "beatjockey", "jokers", "teamkirifuda"), pri=11, roles="atk fin rem",
    enter=exlife_enter, leaverep=exlife_rep, breakwatch=bw_blago, atkend=ae_blago,
    text="＜キリフダッシュ＞[火/自然(4)]（自分のクリーチャーの攻撃の終わりに、そのクリーチャーが"
         "その攻撃中にシールドをブレイクしていれば、このクリーチャーを[火/自然(4)]支払って"
         "手札から召喚してもよい。払えるなら召喚する）。"
         "EXライフ（このクリーチャーを出す時、自分の山札の上から1枚をシールド化する。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。"
         "スピードアタッカー。マッハファイター。W・ブレイカー",
    source=SRC["k32_blago"])


# ================================================================ 28/77 銃初逆夢 ザ・ウィニー／ジョリー・ザ・スパーク
def sp_thewinny(s, i):
    """ジョリー・ザ・スパーク：カードを1枚引く。その後、コスト2以下の、クリーチャーまたはタマシードを1つ、
    自分の手札から出してもよい"""
    p = s.P[i]
    s.draw(i)
    best, bv, bon = None, -1, None
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.cost > 2 or c.kind not in ("C", "T") or E.PRI[k] <= bv:
            continue
        if c.kind == "C":
            on = _evo_on(s, i, k)
            if on == "x" or s.fate(i, k, "hand", False) != "ok":
                continue
        else:
            on = None
        best, bv, bon = k, E.PRI[k], on
    if best is None:
        return
    p.hand.remove(best)
    s.ev(f"　ジョリー・ザ・スパーク：手札の {BY_KEY[best].name} を出す")
    if BY_KEY[best].kind == "T":
        s.place_tama(i, best)
    else:
        s.enter(i, best, "hand", False, on=bon)


def a_thewinny(s, i, u):
    """スマッシュ・バースト：攻撃する時、このカードの呪文側を、バトルゾーンに置いたまま
    コストを支払わずに唱えてもよい"""
    p = s.P[i]
    cost = BY_KEY["k32_thewinny"].twin[0]
    if not s.spell_ok(i, cost) or s.over:
        return
    d = _depth(s, i, "k32_smash")
    if d is None:
        return
    try:
        p.spl += 1
        s.first_play(i, cost)
        prev = s.spc
        s.spc = cost
        s.ev("　スマッシュ・バースト：ジョリー・ザ・スパーク をコストを支払わずに唱える")
        for f in E.SPELLWATCH:
            if not s.over:
                f(s, i, "k32_thewinny")
        if not s.over:
            sp_thewinny(s, i)
        s.spc = prev
    finally:
        _undepth(s, i, "k32_smash", d)


add("k32_thewinny", "銃初逆夢 ザ・ウィニー／ジョリー・ザ・スパーク", 5, "L", power=5500,
    races=("dispector", "metallica", "jokers"), twin=(3, "L", False), pri=7, roles="draw shd atk",
    enter=exlife_enter, leaverep=exlife_rep, attack=a_thewinny, spell=sp_thewinny,
    text="【クリーチャー側：銃初逆夢 ザ・ウィニー（光5・パワー5500）】"
         "EXライフ（このクリーチャーを出す時、自分の山札の上から1枚をシールド化する。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。"
         "スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱えてもよい）。"
         "【呪文側：ジョリー・ザ・スパーク（光3）】"
         "カードを1枚引く。その後、コスト2以下の、クリーチャーまたはタマシードを1つ、"
         "自分の手札から出してもよい（重要度のいちばん高いもの）",
    source=SRC["k32_thewinny"])


# ================================================================ 29/77 輝晶 シンプ-2
def e_shimp(s, i, u):
    """出た時、自分の山札の上から1枚をシールド化する"""
    if s.add_shield(i):
        s.ev("　輝晶 シンプ-2：山札の上から1枚をシールド化")


def lf_shimp(s, i, u, dest):
    """離れた時、次の自分のターンのはじめまで、自分のクリーチャー1体に「ブロッカー」を与える"""
    cres = [z for z in s.P[i].board if z.c.kind == "C"]
    cands = [z for z in cres if not z.c.blocker] or cres
    if not cands:
        return
    z = max(cands, key=lambda x: (s.power(i, x), x.uid))
    z.x["k32_blk"] = s.turn + (1 if s.tp == i else 0)
    s.ev(f"　輝晶 シンプ-2：{z.c.name} に次の自分のターンのはじめまで「ブロッカー」を与える")


def bo_shimp(s, u):
    return u.x.get("k32_blk", -1) >= s.turn


add("k32_shimp", "輝晶 シンプ-2", 3, "L", power=2500, races=("metallica", "distas"), pri=4, roles="shd blk",
    enter=e_shimp, left=lf_shimp, blockok=bo_shimp,
    text="このクリーチャーが出た時、自分の山札の上から1枚をシールド化する。"
         "このクリーチャーが離れた時、次の自分のターンのはじめまで、自分のクリーチャー1体に「ブロッカー」を与える"
         "（ブロッカーを持っていないクリーチャーのうち、いちばんパワーの高いものに与える）。"
         "ササゲール2（自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたらこのエレメントを破壊する。ただしコストは0以下にならない）",
    source=SRC["k32_shimp"])
SASAGEL["k32_shimp"] = 2


# ================================================================ 30/77 ヒトリダチ キャンベロ
def e_canbero(s, i, u):
    """出た時、次の中から1回選ぶ。
    ▶自分のクリーチャー1体は、次の自分のターンのはじめまでバトル中破壊されない　▶Jビッグ1する"""
    if _jbig(s, i, u):
        return
    cands = [z for z in s.P[i].board if z.c.kind == "C"]
    if not cands:
        return
    z = max(cands, key=lambda x: (s.val(x), s.power(i, x), x.uid))
    z.x["k32_prot"] = s.turn + (1 if s.tp == i else 0)
    s.ev(f"　ヒトリダチ キャンベロ：{z.c.name} は次の自分のターンのはじめまでバトル中破壊されない")


def bf_canbero(s, ai, au, di, du, a_dies, d_dies):
    if a_dies and au.x.get("k32_prot", -1) >= s.turn:
        a_dies = False
    if d_dies and du.x.get("k32_prot", -1) >= s.turn:
        d_dies = False
    return a_dies, d_dies


def w_canbero(s, i, u):
    """相手のマナゾーンにあるカードの枚数よりコストが大きい相手のクリーチャーが出た時、
    相手はそれを山札の下に置く"""
    if u.c.kind != "C" or not any(z.k == "k32_canbero" for z in s.P[1 - i].board):
        return
    if u.c.cost > len(s.P[i].mana) and u in s.P[i].board:
        s.ev(f"　ヒトリダチ キャンベロ：{u.c.name} を山札の下へ")
        s.leave(i, u, "deck", by_opp=True)


add("k32_canbero", "ヒトリダチ キャンベロ", 2, "L", power=2000, races=("jokers",), pri=5, roles="dis",
    enter=e_canbero, battlefx=bf_canbero, enterwatch=w_canbero,
    text="このクリーチャーが出た時、次の中から1回選ぶ。"
         "▶自分のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、そのクリーチャーはバトル中破壊されない"
         "（いちばん大事な、同じならパワーの高いクリーチャーを選ぶ）。"
         "▶Jビッグ1する（自分の他のジョーカーズの、Jビッグ1以外の、出た時にトリガーする能力を1つ使う。"
         "使える相手がいればこちらを選ぶ）。"
         "相手のマナゾーンにあるカードの枚数よりコストが大きい相手のクリーチャーが出た時、"
         "相手はそれを山札の下に置く",
    source=SRC["k32_canbero"])


# ================================================================ 31/77 輝晶 マルハヴ-2
def lr_maruhavu(s, i, u, dest, destroy):
    """相手のターン中、自分のディスタス・クリーチャーすべてに「エスケープ」を与える
    （破壊される時、かわりに自分のシールドを1つ手札に加えてもよい。そのS・トリガーは使えない）"""
    if not destroy or u.c.kind != "C" or "distas" not in u.c.races:
        return False
    if s.tp == i or not s.has(i, "k32_maruhavu") or not s.P[i].sh:
        return False
    if _take_shield(s, i, "hand") is None:
        return False
    s.ev(f"　エスケープ：{u.c.name} は破壊されず、自分のシールドを1つ手札に加える")
    return True


add("k32_maruhavu", "輝晶 マルハヴ-2", 2, "L", power=2000, races=("metallica", "distas"), pri=5, roles="dis",
    leaverep=lr_maruhavu,
    text="相手のターン中、自分のディスタス・クリーチャーすべてに「エスケープ」を与える"
         "（「エスケープ」を持つクリーチャーが破壊される時、かわりに自分のシールドを1つ手札に加えてもよい。"
         "その「S・トリガー」は使えない。裏向きのシールドから加える）。"
         "ササゲール2（自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたらこのエレメントを破壊する。ただしコストは0以下にならない）",
    source=SRC["k32_maruhavu"])
SASAGEL["k32_maruhavu"] = 2
