"""担当26：DM26-RP2（逆札篇 第2弾 燃えろ禁断！逆転のドギラゴン革命‼︎）の未実装カード15枚

出典：dmwiki.net の各カードページ（本文が切れる時は ?plugin=template&refer=《カード名》 の生ソース）。
      15枚すべて、別の質問で2回ずつ読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
      どちらの読みでも一致することを確かめた。食い違った時は3回目を読んで決めている。

  この札束で出てくる新しい仕組み
    ・「〜ナウ」5枚のサイクル（ポプポプ守る／スラスラ吸い込む／ごくごく掘る／ドファドファ叩く／サクサク打つべし）。
      どれも「S・トリガー」＋「軽い手札・マナ・墓地の整え」＋「その過程でパワー6000以上のクリーチャーを
      めくった／捨てた／戻したら、文明ごとの除去がおまけで付く」という形。
    ・D2フィールド（Dの機動 ヴァイス・ヴァーチュー）。バトルゾーンに出て残るカードなので、
      既存の《DG-パルテノン》と同じく**タマシード（kind="T"）**として実装した。
      「他のD2フィールドが出た時、このD2フィールドを破壊する」も入れてある。
    ・パワー・ガチンコ・ジャッジ（カチスギル・スキル、ガチ＝ザ＝デッドマン）。
      コストではなくパワーを比べる。パワーのないカードは0。同じなら仕掛けた側の勝ち。
    ・「自分のマナゾーンにあるカードは、すべての文明を持つ」（ガチ＝ザ＝デッドマン）。
      このエンジンは「マナに必要な文明があるか」で使える札を決めているので、engine3.civs を
      自分のモジュールから包んで（engine3.py は書き換えずに）効かせている。
    ・スーパーガードマン＋「自分のガードマンにスピードアタッカーとパワード・ブレイカーを与える」
      （グローバル・ステージ）。パワード・ブレイカーは「パワー6000ごとにブレイク数+1」。
    ・スペース・チャージ（鎧亜寄生パラス・キューピッド）。`manain=`（自分のマナゾーンに
      カードが置かれた時）で、置かれたその場で誘発させている。

  調べ直して意外だった点
    ・《革命の轟速 レッドゾーンW》は侵略ではなく**革命チェンジ**（闇か火のパワー4000以上）だった。
      出た時に相手のクリーチャー1体に封印1つを付ける。
    ・《Dの機動 ヴァイス・ヴァーチュー》は城（G）ではなく**D2フィールド**。G・ストライク持ち。
    ・《熱血の名 カチスギル・スキル》はブロッカーを持つ（1回目の読みでも2回目でも「ブロッカー」があった）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move, opp_all
from envcards.env0 import discard_choice

W = "https://dmwiki.net/"
SRC = {
    "k26_popupo": W + "《ポプポプ守るナウ》",
    "k26_surasura": W + "《スラスラ吸い込むナウ》",
    "k26_vaisu": W + "《Dの機動 ヴァイス・ヴァーチュー》",
    "k26_kachisugiru": W + "《熱血の名 カチスギル・スキル》",
    "k26_gokugoku": W + "《ごくごく掘るナウ》",
    "k26_ukon": W + "《流星の使者 ウコン＆サコン》",
    "k26_dofadofa": W + "《ドファドファ叩くナウ》",
    "k26_gachideadman": W + "《虹暴の面 ガチ＝ザ＝デッドマン》",
    "k26_sakusaku": W + "《サクサク打つべしナウ》",
    "k26_bosukatsu": W + "《漢の2号 ボスカツ逆》",
    "k26_redzonew": W + "《革命の轟速 レッドゾーンW》",
    "k26_katsuking": W + "《V闘将軍 カツキング》",
    "k26_globalstage": W + "《獣音類武士目 グローバル・ステージ》",
    "k26_tapdoreiyu": W + "《護英雄 タップ・ド・レイユ》",
    "k26_paraskyupido": W + "《鎧亜寄生パラス・キューピッド》",
}


# ================================================================ 共通の道具
def _big(k):
    """「パワー6000以上のクリーチャー」か（〜ナウ5枚のおまけの条件）"""
    c = BY_KEY[k]
    return c.kind == "C" and c.power >= 6000


def _pgj(s, i):
    """パワー・ガチンコ・ジャッジを1回行う（勝ったら True）。
    互いに山札の上から1枚を表向きにして山札の下へ。パワーが相手以上なら仕掛けた側の勝ち。
    パワーのないカードは0として扱う"""
    p, o = s.P[i], s.P[1 - i]
    if not p.deck:
        return False
    a = p.deck.pop()
    p.deck.insert(0, a)
    pa = BY_KEY[a].power if BY_KEY[a].kind == "C" else 0
    pb = 0
    if o.deck:
        b = o.deck.pop()
        o.deck.insert(0, b)
        pb = BY_KEY[b].power if BY_KEY[b].kind == "C" else 0
    return pa >= pb


def _look_take(s, i, n, prefer_big):
    """山札の上n枚を見て1枚を手札に加え、残りを山札の下へ。加えたカードを返す。
    prefer_big が True なら、パワー6000以上のクリーチャーを優先して取る（おまけの条件を満たすため）"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    if n <= 0:
        return None
    top = [p.deck.pop() for _ in range(n)]
    pick = None
    if prefer_big:
        bigs = [k for k in top if _big(k)]
        if bigs:
            pick = max(bigs, key=lambda k: E.PRI[k] - 3 * p.hand.count(k))
    if pick is None:
        pick = max(top, key=lambda k: E.PRI[k] - 3 * p.hand.count(k))
    top.remove(pick)
    p.hand.append(pick)
    for k in top:
        p.deck.insert(0, k)
    return pick


def _best_grave_cre(s, i, prefer_big):
    """墓地のクリーチャーのうち、手札に戻したいもの（prefer_big ならパワー6000以上を優先）"""
    p = s.P[i]
    cs = [k for k in p.grave if BY_KEY[k].kind == "C"]
    if not cs:
        return None
    if prefer_big:
        bigs = [k for k in cs if _big(k)]
        if bigs:
            return max(bigs, key=E.PRI.get)
    return max(cs, key=E.PRI.get)


def _sum_pick(s, i, limit, pred=None):
    """相手のエレメントから、コストの合計が limit 以下になるように、値打ちの高い順に選ぶ"""
    out, rest = [], limit
    for t in sorted(opp_all(s, i, pred, kinds="CTX"), key=lambda u: -s.val(u)):
        if t.c.cost <= rest:
            out.append(t)
            rest -= t.c.cost
    return out


def _opp_elem(s, i, limit=None):
    """相手のエレメント（クリーチャー・タマシード・クロスギア）に、取り除く値打ちのあるものがあるか"""
    return bool(opp_all(s, i, (lambda u: u.c.cost <= limit) if limit is not None else None, kinds="CTX"))


def _base_brk(s, i, u):
    """パワード・ブレイカーを足す前のブレイク数（W・ブレイカー等と重ねて数えないため）"""
    f = E.BRKX.get(u.k)
    if f is not None:
        r = f(s, i, u)
        if r is not None:
            return r
    if u.hyper and u.k in E.HYPER_POW:
        return E.HYPER_BRK.get(u.k, 2)
    return u.c.brk


def _powered(s, i, u):
    """パワード・ブレイカー：パワー6000ごとにブレイク数が1つ増える（増える分だけを返す）"""
    return max(0, 1 + s.power(i, u, True) // 6000 - _base_brk(s, i, u))


def _take_shield(s, i, dest="hand"):
    """自分のシールド1つを手札に加える（裏向きを先に。S・トリガーは使えない）。できたら True"""
    p = s.P[i]
    if not p.sh:
        return False
    j = next((x for x in range(len(p.sh) - 1, -1, -1) if not p.sh[x][1]), len(p.sh) - 1)
    k, up = p.sh.pop(j)
    if dest == "hand":
        p.hand.append(k)
    else:
        s.grave_put(i, k)
    s.shield_left()
    for f in E.SHIELDOUT:
        f(s, i, k, up, dest)
    return True


# ================================================================ ポプポプ守るナウ（13/77）
def sp_popupo(s, i):
    """自分の山札の上から1枚を表向きでシールド化する。
    こうしてパワー6000以上のクリーチャーをシールド化したら、相手のクリーチャー1体をシールド化してもよい"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    if s.has(1 - i, "robin"):                 # ロビンフッド：シールドは増えず山札の下へ
        p.deck.insert(0, p.deck.pop())
        return
    k = p.deck.pop()
    if not s.add_shield(i, k, True):          # フウジン天：増やせない
        p.deck.append(k)
        return
    s.ev(f"　ポプポプ守るナウ：{BY_KEY[k].name} を表向きのシールドに")
    if not _big(k) or s.over:
        return
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　ポプポプ守るナウ：{t.c.name} をシールド化")
    s.leave(1 - i, t, "shield", by_opp=True)


add("k26_popupo", "ポプポプ守るナウ", 5, "L", kind="S", trig=True, pri=5, roles="shd trg rem",
    spell=sp_popupo,
    text="S・トリガー。自分の山札の上から1枚を表向きでシールド化する。"
         "こうしてパワー6000以上のクリーチャーをシールド化したら、相手のクリーチャー1体を選んでシールド化してもよい",
    source=SRC["k26_popupo"])


# ================================================================ スラスラ吸い込むナウ（14/77）
def sp_surasura(s, i):
    """山札の上から4枚を見て1枚を手札に加え、残りを山札の下へ。
    こうしてパワー6000以上のクリーチャーを表向きにしたら、相手のクリーチャー1体を手札に戻してもよい"""
    want = s.target(i) is not None
    k = _look_take(s, i, 4, want)
    if k is None or not _big(k) or s.over:
        return
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　スラスラ吸い込むナウ：{t.c.name} を手札へ")
    move(s, i, t, "hand")


add("k26_surasura", "スラスラ吸い込むナウ", 3, "W", kind="S", trig=True, pri=4, roles="draw trg rem",
    spell=sp_surasura,
    text="S・トリガー。自分の山札の上から4枚を見て、その中から1枚を表向きにして手札に加え、残りを山札の下に置く。"
         "こうしてパワー6000以上のクリーチャーを表向きにしたら、相手のクリーチャー1体を持ち主の手札に戻してもよい",
    source=SRC["k26_surasura"])


# ================================================================ Dの機動 ヴァイス・ヴァーチュー（15/77）
D2 = ("k26_vaisu",)          # このモジュールで実装したD2フィールド


def e_vaisu(s, i, u):
    """D2フィールドの決まり：他のD2フィールドが出た時、先にあったD2フィールドは破壊される"""
    p = s.P[i]
    for z in p.board[:]:
        if z is not u and z.k in D2:
            s.ev(f"　D2フィールドの決まり：{z.c.name} を破壊")
            s.leave(i, z, "grave", destroy=True)


def t_vaisu(s, i, u):
    """自分のターンの終わりに、カードを1枚引いてもよい"""
    if len(s.P[i].deck) > 1:
        s.draw(i)


def _dsw_pick(s, i):
    """Dスイッチでただで使える札（コスト5以下、クリーチャーでない、その文明がすべて自分のマナゾーンにある）"""
    p = s.P[i]
    cv = E.civs(p)
    best, bv = None, -99
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "C" or c.twin or c.cost > 5 or not c.civ:
            continue                           # ツインパクトとクリーチャーと無色は使えない
        if not cv.issuperset(c.civ):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    return best


def w_vaisu(s, i, au):
    """Dスイッチ：クリーチャーが自分（プレイヤー）を攻撃する時、ゲーム中1度だけこのD2フィールドを
    上下逆さまにして、手札からコスト5以下のクリーチャーでないカード1枚をただで使う。

    「プレイヤーを攻撃する時」は `s.atktgt is None` で見る（クリーチャーへの攻撃では誘発しない）"""
    if s.atktgt is not None:
        return
    d = 1 - i
    for z in s.P[d].board:
        if z.k != "k26_vaisu" or z.x.get("k26_dsw"):
            continue
        k = _dsw_pick(s, d)
        if k is None:
            continue
        z.x["k26_dsw"] = 1
        s.ev(f"　Dスイッチ：ヴァイス・ヴァーチューを裏返して {BY_KEY[k].name} をただで使う")
        free_play(s, d, k, "hand")
        return


add("k26_vaisu", "Dの機動 ヴァイス・ヴァーチュー", 4, "W", kind="T", gs=True, pri=4, roles="draw trg",
    enter=e_vaisu, tend=t_vaisu, atkwatch=w_vaisu, status="partial",
    note="D2フィールドはこのシミュレーターに無いゾーンなので、場に残るカードとしてタマシードで表している"
         "（他のD2フィールドが出た時に破壊される決まりは書いてあるが、"
         "「クリーチャーでもタマシードでもない」ことによる差は表せない）",
    text="D2フィールド（バトルゾーンに出て残るカード。このシミュレーターではタマシードとして扱う）。G・ストライク。"
         "自分のターンの終わりに、カードを1枚引いてもよい。他のD2フィールドが出た時、このD2フィールドを破壊する。"
         "Dスイッチ：クリーチャーが自分を攻撃する時、ゲーム中1度だけこのカードを上下逆さまにして、"
         "コスト5以下で、その文明がすべて自分のマナゾーンにある、クリーチャーでないカード1枚を手札からただで使ってもよい",
    source=SRC["k26_vaisu"])
E.STAY.add("k26_vaisu")


# ================================================================ 熱血の名 カチスギル・スキル（16/77）
def e_kachisugiru(s, i, u):
    """出た時、相手は自身の手札を3枚選んで捨てる"""
    for _ in range(3):
        if s.over or not s.P[1 - i].hand:
            break
        discard_choice(s, 1 - i)


def d_kachisugiru(s, i, u):
    """破壊された時、パワー・ガチンコ・ジャッジに勝てば、このクリーチャーを墓地からタップして出す"""
    p = s.P[i]
    if "k26_kachisugiru" not in p.grave or s.over:
        return
    if not _pgj(s, i):
        s.ev("　カチスギル・スキル：パワー・ガチンコ・ジャッジに負けた")
        return
    if s.fate(i, "k26_kachisugiru", "grave", False) != "ok":
        return
    p.grave.remove("k26_kachisugiru")
    s.ev("　カチスギル・スキル：ジャッジに勝って墓地からタップして出る")
    nu = s.enter(i, "k26_kachisugiru", "grave", False)
    if nu is not None and nu in p.board:
        nu.tap = True            # 「タップして出す」＝タップ状態で出る（タップした時の誘発はしない）


add("k26_kachisugiru", "熱血の名 カチスギル・スキル", 6, "D", power=9000, brk=2, blocker=True,
    races=("dragonzombie", "unknown"), pri=9, roles="blk dis rem fin",
    enter=e_kachisugiru, destroyed=d_kachisugiru,
    text="ブロッカー、W・ブレイカー。出た時、相手は自身の手札を3枚選んで捨てる。"
         "破壊された時、相手とパワー・ガチンコ・ジャッジしてもよい（互いに山札の上から1枚を表向きにして下に置き、"
         "パワーが相手以上なら勝ち。パワーのないカードは0）。勝ったら、このクリーチャーを自分の墓地からタップして出す",
    source=SRC["k26_kachisugiru"])


# ================================================================ ごくごく掘るナウ（17/77）
def sp_gokugoku(s, i):
    """山札の上から3枚を墓地に置き、その後クリーチャー1体を墓地から手札に戻す。
    こうしてパワー6000以上のクリーチャーを戻したら、相手のクリーチャー1体を破壊する"""
    p = s.P[i]
    s.mill(i, 3)
    want = s.target(i) is not None
    k = _best_grave_cre(s, i, want)
    if k is None:
        return
    p.grave.remove(k)
    p.hand.append(k)
    s.ev(f"　ごくごく掘るナウ：{BY_KEY[k].name} を墓地から手札へ")
    if not _big(k) or s.over:
        return
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　ごくごく掘るナウ：{t.c.name} を破壊")
    destroy(s, i, t)


add("k26_gokugoku", "ごくごく掘るナウ", 4, "D", kind="S", trig=True, pri=4, roles="draw trg rem",
    spell=sp_gokugoku,
    text="S・トリガー。自分の山札の上から3枚を墓地に置く。その後、クリーチャー1体を自分の墓地から手札に戻す。"
         "こうしてパワー6000以上のクリーチャーを手札に戻したら、相手のクリーチャー1体を選んで破壊する",
    source=SRC["k26_gokugoku"])


# ================================================================ 流星の使者 ウコン＆サコン（18/77）
def w_ukon(s, i, u):
    """各ターン1度、自分の他のクリーチャーが出た時、パワー+4000と「スピードアタッカー」「パワード・ブレイカー」を与える
    （終わりの時が書かれていないので、ずっと続く＝u.x に残す）"""
    if u.c.kind != "C":
        return
    p = s.P[i]
    if not any(z.k == "k26_ukon" and z is not u for z in p.board):
        return                                 # 「自分の他のクリーチャー」なので、自分自身には与えられない
    if p.x.get("k26_ukon_t") == s.turn:
        return
    p.x["k26_ukon_t"] = s.turn
    u.x["k26_boost"] = 1
    s.ev(f"　ウコン＆サコン：{u.c.name} にパワー+4000とスピードアタッカー・パワード・ブレイカー")


def ap_ukon(s, i, u, atk):
    return 4000 if u.x.get("k26_boost") else 0


def sa_ukon(s, i, u):
    return bool(u.x.get("k26_boost"))


def bp_ukon(s, i, u):
    """パワード・ブレイカー：パワー6000ごとにブレイク数が1つ増える"""
    if not u.x.get("k26_boost"):
        return 0
    return _powered(s, i, u)


add("k26_ukon", "流星の使者 ウコン＆サコン", 3, "F", power=3000, races=("firebird", "hunter"),
    pri=5, roles="atk fin",
    enterwatch=w_ukon, aurap=ap_ukon, saok=sa_ukon, brkplus=bp_ukon,
    text="各ターン1度、自分の他のクリーチャーが出た時、そのクリーチャーのパワーを+4000し、"
         "「スピードアタッカー」と「パワード・ブレイカー」（パワー6000ごとにシールドを1つ多くブレイクする）を与えてもよい。"
         "終わりの時が書かれていないので、与えた効果はそのままずっと続く",
    source=SRC["k26_ukon"])


# ================================================================ ドファドファ叩くナウ（19/77）
def sp_dofadofa(s, i):
    """自分の手札を1枚捨て、カードを2枚引く。
    こうしてパワー6000以上のクリーチャーを捨てたら、コストの合計が6以下になるように相手のエレメントを選んで破壊する"""
    p = s.P[i]
    if not p.hand:
        s.draw(i, 2)
        return
    k = None
    if _opp_elem(s, i, 6):
        bigs = [x for x in p.hand if _big(x)]
        if bigs:
            k = min(bigs, key=E.PRI.get)       # おまけを使うため、いちばん軽い6000以上を捨てる
    if k is None:
        k = min(p.hand, key=E.PRI.get)
    had = p.hand.count(k)
    s.discard(i, k)
    done = p.hand.count(k) < had          # マッドネスで捨てずにすんだ場合はおまけも付かない
    s.draw(i, 2)
    if not done or not _big(k) or s.over:
        return
    ts = _sum_pick(s, i, 6)
    for t in ts:
        if s.over:
            break
        if t in s.P[1 - i].board:
            s.ev(f"　ドファドファ叩くナウ：{t.c.name} を破壊")
            destroy(s, i, t)


add("k26_dofadofa", "ドファドファ叩くナウ", 3, "F", kind="S", trig=True, pri=4, roles="draw trg rem",
    spell=sp_dofadofa,
    text="S・トリガー。自分の手札を1枚捨て、カードを2枚引く。"
         "こうしてパワー6000以上のクリーチャーを捨てたら、コストの合計が6以下になるように相手のエレメントを"
         "好きな数選んで破壊する",
    source=SRC["k26_dofadofa"])


# ================================================================ 虹暴の面 ガチ＝ザ＝デッドマン（20/77）
_ORIG_CIVS = E.civs


def _civs_all(p):
    """自分のマナゾーンにあるカードは、すべての文明を持つ（ガチ＝ザ＝デッドマンがバトルゾーンにいる間）"""
    for u in p.board:
        if u.k == "k26_gachideadman":
            return set("LWDFN")
    return _ORIG_CIVS(p)


if not getattr(E.civs, "_k26", False):
    _civs_all._k26 = True
    E.civs = _civs_all


def t_gachideadman(s, i, u):
    """自分のターンのはじめに、パワー・ガチンコ・ジャッジに勝てば山札の上から1枚をマナゾーンに置く"""
    if _pgj(s, i):
        s.ev("　ガチ＝ザ＝デッドマン：ジャッジに勝って1枚マナへ")
        s.ramp(i, 1)


add("k26_gachideadman", "虹暴の面 ガチ＝ザ＝デッドマン", 2, "N", power=3000,
    races=("beastfolk", "revolution", "hamukatsu"), pri=4, roles="acc",
    tstart=t_gachideadman,
    note="効果そのものは全部入っているが、書き方が例外的：「自分のマナゾーンにあるカードはすべての文明を持つ」は"
         "文明そのものを書き換える効果で、エンジンにそれを与える差し込み口（CIVAURA）がまだ無いため、"
         "このモジュールから engine3.civs を包んで（engine3.py は書き換えずに）効かせている。"
         "エンジン側に CIVAURA が入ったら、この包みを外して差し込み口に移すこと",
    text="自分のマナゾーンにあるカードは、すべての文明を持つ。"
         "自分のターンのはじめに、相手とパワー・ガチンコ・ジャッジしてもよい（互いに山札の上から1枚を表向きにして"
         "下に置き、パワーが相手以上なら勝ち。パワーのないカードは0）。勝ったら、自分の山札の上から1枚をマナゾーンに置く",
    source=SRC["k26_gachideadman"])


# ================================================================ サクサク打つべしナウ（21/77）
def sp_sakusaku(s, i):
    """山札の上から2枚をタップしてマナゾーンに置き、その後カード1枚をマナゾーンから手札に戻す。
    こうしてパワー6000以上のクリーチャーを戻したら、相手のコスト6以下のエレメント1つを持ち主のマナゾーンに置いてもよい"""
    p = s.P[i]
    s.ramp(i, 2, tapped=True)
    if not p.mana:
        return
    want = _opp_elem(s, i, 6)
    k = None
    if want:
        bigs = [x for x in p.mana if _big(x)]
        if bigs:
            k = max(bigs, key=E.PRI.get)
    if k is None:
        k = max(p.mana, key=E.PRI.get)
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　サクサク打つべしナウ：{BY_KEY[k].name} をマナから手札へ")
    if not _big(k) or s.over:
        return
    t = s.target(i, lambda u: u.c.cost <= 6, kinds="CTX")
    if t is None:
        return
    s.ev(f"　サクサク打つべしナウ：{t.c.name} を持ち主のマナゾーンへ")
    move(s, i, t, "mana")


add("k26_sakusaku", "サクサク打つべしナウ", 4, "N", kind="S", trig=True, pri=5, roles="acc trg rem",
    spell=sp_sakusaku,
    text="S・トリガー。自分の山札の上から2枚をタップしてマナゾーンに置く。その後、カード1枚を自分のマナゾーンから"
         "手札に戻す。こうしてパワー6000以上のクリーチャーを手札に戻したら、相手のコスト6以下のエレメント1つを選び、"
         "持ち主のマナゾーンに置いてもよい",
    source=SRC["k26_sakusaku"])


# ================================================================ 漢の2号 ボスカツ逆（23/77）
def ca_bosukatsu(s, i, k, n):
    """自分のクリーチャーの召喚コストを2少なくする（0以下にはならない）"""
    if n <= 1 or BY_KEY[k].kind != "C" or not s.has(i, "k26_bosukatsu"):
        return n
    return max(1, n - 2)


def rep_bosukatsu(s, i, u, dest, destroy_):
    """エスケープ：破壊される時、墓地に置くかわりに自分のシールド1つを手札に加えてもよい（S・トリガーは使えない）"""
    if not destroy_ or u.k != "k26_bosukatsu" or not s.P[i].sh:
        return False
    if not _take_shield(s, i, "hand"):
        return False
    s.ev("　エスケープ：シールド1つを手札に加えて ボスカツ逆 は残る")
    return True


def pr_bosukatsu(deck, k):
    n = sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
            and set("LN") & set(BY_KEY[kk].civ) and BY_KEY[kk].power >= 4000)
    return None if n >= 3 else "革命チェンジの元（光か自然のパワー4000以上）が3体いない"


add("k26_bosukatsu", "漢の2号 ボスカツ逆", 6, "LN", power=8500, brk=2, gs=True,
    races=("megacommanddragon", "command", "revolution", "hamukatsu"), pri=9, roles="acc atk fin trg",
    changex=lambda s, i, u: bool(set("LN") & set(u.c.civ)) and s.power(i, u, True) >= 4000,
    costaura=ca_bosukatsu, leaverep=rep_bosukatsu, playrule=pr_bosukatsu,
    text="G・ストライク。革命チェンジ：光または自然の、パワー4000以上のクリーチャー。W・ブレイカー。"
         "自分のクリーチャーの召喚コストを2少なくする（0以下にはならない）。"
         "エスケープ（破壊される時、墓地に置くかわりに自分のシールド1つを手札に加えてもよい。その「S・トリガー」は使えない）",
    source=SRC["k26_bosukatsu"])


# ================================================================ 革命の轟速 レッドゾーンW（25/77）
def e_redzonew(s, i, u):
    """出た時、相手のクリーチャー1体を選び、相手はそれに封印を1つ付ける"""
    t = s.target(i)
    if t is None:
        return
    s.seal(1 - i, t, 1)
    u.x["k26_seal"] = t.uid       # 下の w_redzonew で付け直せるように覚えておく


def w_redzonew(s, i, u):
    """env0 の「コマンドが出た時、封印を1つ外す」は、自分の封印が無いと相手の封印まで外してしまう。
    このクリーチャー自身もソニック・コマンドなので、出た時に付けた封印が同じ誘発でいきなり外れてしまう。
    ENTERWATCH は env0 より後に呼ばれるので、ここで付け直す（REQUEST_26.md）"""
    uid = u.x.pop("k26_seal", None)
    if uid is None or s.over:
        return
    o = s.P[1 - i]
    if any(z.uid == uid for z, _ in o.sealed):
        return
    t = next((z for z in o.board if z.uid == uid), None)
    if t is not None:
        s.ev("　レッドゾーンW：外れた封印を付け直す")
        s.seal(1 - i, t, 1)


def pr_redzonew(deck, k):
    n = sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
            and set("DF") & set(BY_KEY[kk].civ) and BY_KEY[kk].power >= 4000)
    return None if n >= 3 else "革命チェンジの元（闇か火のパワー4000以上）が3体いない"


add("k26_redzonew", "革命の轟速 レッドゾーンW", 6, "DF", power=9000, brk=2, sa=True,
    races=("soniccommand", "command", "initialsw"), pri=9, roles="atk rem fin",
    enter=e_redzonew, enterwatch=w_redzonew,
    changex=lambda s, i, u: bool(set("DF") & set(u.c.civ)) and s.power(i, u, True) >= 4000,
    playrule=pr_redzonew,
    text="革命チェンジ：闇または火の、パワー4000以上のクリーチャー。スピードアタッカー、W・ブレイカー。"
         "出た時、相手のクリーチャー1体を選び、相手はそれに封印を1つ付ける",
    source=SRC["k26_redzonew"])


# ================================================================ V闘将軍 カツキング（26/77）
def e_katsuking(s, i, u):
    """出た時、相手の「ブロッカー」を持つクリーチャー1体を持ち主のマナゾーンに置く"""
    t = s.target(i, lambda z: z.c.blocker)
    if t is None:
        return
    s.ev(f"　V闘将軍 カツキング：ブロッカーの {t.c.name} をマナへ")
    move(s, i, t, "mana")


def ae_katsuking(s, i, u):
    """攻撃の終わりに、山札の上から3枚を表向きにし、その中からクリーチャー1体を手札に加えてもよい。残りは山札の下へ"""
    if u.k != "k26_katsuking":
        return
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    cs = [k for k in top if BY_KEY[k].kind == "C"]
    if cs:
        pick = max(cs, key=lambda k: E.PRI[k] - 3 * p.hand.count(k))
        top.remove(pick)
        p.hand.append(pick)
        s.ev(f"　V闘将軍 カツキング：{BY_KEY[pick].name} を手札に加える")
    for k in top:
        p.deck.insert(0, k)


def pr_katsuking(deck, k):
    n = sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
            and set("FN") & set(BY_KEY[kk].civ) and BY_KEY[kk].power >= 4000)
    return None if n >= 3 else "革命チェンジの元（火か自然のパワー4000以上）が3体いない"


add("k26_katsuking", "V闘将軍 カツキング", 6, "FN", power=9000, brk=2, sa=True,
    races=("outragecommand", "command", "revolution", "hamukatsu"), pri=9, roles="atk rem draw fin",
    enter=e_katsuking, atkend=ae_katsuking,
    changex=lambda s, i, u: bool(set("FN") & set(u.c.civ)) and s.power(i, u, True) >= 4000,
    playrule=pr_katsuking,
    text="革命チェンジ：火または自然の、パワー4000以上のクリーチャー。スピードアタッカー、W・ブレイカー。"
         "出た時、相手の「ブロッカー」を持つクリーチャー1体を選び、持ち主のマナゾーンに置く。"
         "このクリーチャーの攻撃の終わりに、自分の山札の上から3枚を表向きにし、その中からクリーチャー1体を"
         "手札に加えてもよい。残りを山札の下に置く",
    source=SRC["k26_katsuking"])


# ================================================================ 獣音類武士目 グローバル・ステージ（27/77）
_GUARD_EXTRA = ("e_tores",)                  # テキストから拾えないガードマン持ち
_GUARD_PAT = ("ガードマン。", "ガードマン、", "ガードマン：", "「ガードマン」")
_GCACHE = {"n": -1, "set": frozenset()}


def _guard_keys():
    """バトルゾーンで「ガードマン」を持つカードのキー。

    engine3.GUARDMEN（env0.guardman を使ったカードが自動で入る）を正とし、
    そこに入らない書き方のものだけ効果文から拾う。
    以前は効果文の字面だけで判定していたため、「スーパーガードマン（…」と書いた札
    （雪精サエポヨ。など）が拾えていなかった。"""
    if _GCACHE["n"] != len(BY_KEY) + len(E.GUARDMEN):
        ks = set(_GUARD_EXTRA) | set(E.GUARDMEN)
        ks.add("k26_globalstage")
        for k, c in BY_KEY.items():
            n = c.note or ""
            if any(pt in n for pt in _GUARD_PAT):
                ks.add(k)
        _GCACHE["n"] = len(BY_KEY) + len(E.GUARDMEN)
        _GCACHE["set"] = frozenset(ks)
    return _GCACHE["set"]


def bs_globalstage(s, di, du, ai, au):
    """スーパーガードマン：自分の他のクリーチャーがバトルする時、かわりにこれをタップしてバトルさせる

    引き受けるかどうかは全デッキ共通の決まりで決める：バトルに勝てるか、守る相手のほうが大事な時だけ。
    攻撃先は変えないので、攻撃されたクリーチャーのほうは本物どおりそのまま残る。"""
    if du.k == "k26_globalstage":
        return None
    ap = s.power(ai, au, True)
    for z in s.P[di].board:
        if z.k != "k26_globalstage" or z.c.kind != "C" or z.tap or z is du:
            continue
        if s.power(di, z) > ap or s.val(du) > s.val(z):
            s.tap_cre(di, z)
            return z
    return None


E.GUARDMEN.add("k26_globalstage")            # 「ガードマンを持つクリーチャー」の判定に入れる


def _globalstage_on(s, i, u):
    return u.c.kind == "C" and u.k in _guard_keys() and s.has(i, "k26_globalstage")


def sa_globalstage(s, i, u):
    return _globalstage_on(s, i, u)


def bp_globalstage(s, i, u):
    """パワード・ブレイカー：パワー6000ごとにブレイク数が1つ増える
    （ウコン＆サコンのパワード・ブレイカーとは重ねない）"""
    if not _globalstage_on(s, i, u) or u.x.get("k26_boost"):
        return 0
    return _powered(s, i, u)


def ign_globalstage(s, i, u):
    return _globalstage_on(s, i, u)


def al_globalstage(s, i, u):
    """無視するのは「そのクリーチャー自身が持つ攻撃できない能力」だけ。

    エンジンの NOATKIGN は、カード自身の noatk／noatkp と一緒に、外からかけられた
    「このターン攻撃できない」（`u.lock`。G・ストライクなど）まで無視してしまうので、
    そこだけ攻撃できないように縛り直す"""
    if u.lock != s.turn:
        return False
    return _globalstage_on(s, i, u)


add("k26_globalstage", "獣音類武士目 グローバル・ステージ", 4, "FN", power=8000,
    races=("jurassiccommanddragon", "command", "snowfu"), pri=7, roles="blk atk fin",
    battleswap=bs_globalstage, saok=sa_globalstage, brkplus=bp_globalstage, noatkign=ign_globalstage,
    atklock=al_globalstage, status="partial",
    note="「それらが持つ攻撃できない能力を無視する」は NOATKIGN で書いている。"
         "NOATKIGN は外からかけられた「このターン攻撃できない」（G・ストライクなど）まで無視してしまうので、"
         "そのぶんは atklock= で縛り直した。ただし、カード自身の「攻撃できない」を "
         "cantatk=（条件つきで攻撃できない）で書いている札、たとえば《雪精 マリニャン。》の"
         "「このターンに他のクリーチャーが攻撃していなければ攻撃できない」は、"
         "エンジンが CANTATK を NOATKIGN の対象にしていないため無視できない。"
         "スーパーガードマンは battleswap で書いてあり、ブロックのバトルも効果のバトルも引き受ける。"
         "「ガードマンを持つクリーチャー」の判定は engine3.GUARDMEN を正とし、"
         "そこに入らない書き方の札だけ効果文から拾っている",
    text="スーパーガードマン（自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーをタップしてバトルさせてもよい）。"
         "自分の「ガードマン」を持つクリーチャーすべてに「スピードアタッカー」と「パワード・ブレイカー」"
         "（パワー6000ごとにシールドをもう1つブレイクする）を与え、それらが持つ攻撃できない能力を無視する",
    source=SRC["k26_globalstage"])


# ================================================================ 護英雄 タップ・ド・レイユ（28/77）
def _mana3(s, i):
    """マナ武装3：自分のマナゾーンに光のカードが3枚以上あるか"""
    return sum(1 for x in s.P[i].mana if "L" in E.MCIV[x]) >= 3


def e_tapdoreiyu(s, i, u):
    """出た時、相手のクリーチャーを2体選んでタップする"""
    for _ in range(2):
        if s.over:
            break
        t = s.target(i, lambda z: not z.tap)
        if t is None:
            break
        s.ev(f"　タップ・ド・レイユ：{t.c.name} をタップ")
        s.tap_cre(1 - i, t)


def px_tapdoreiyu(s, i, u, atk):
    return 4000 if _mana3(s, i) else 0


def bx_tapdoreiyu(s, i, u):
    return 2 if _mana3(s, i) else None


add("k26_tapdoreiyu", "護英雄 タップ・ド・レイユ", 4, "L", power=3000, blocker=True, trig=True,
    races=("angelcommanddragon", "command"), pri=5, roles="blk trg dis",
    enter=e_tapdoreiyu, powerx=px_tapdoreiyu, brkx=bx_tapdoreiyu,
    text="S・トリガー、ブロッカー。出た時、相手のクリーチャーを2体選んでタップする。"
         "マナ武装3：自分のマナゾーンに光のカードが3枚以上あれば、このクリーチャーのパワーを+4000し、"
         "「W・ブレイカー」を与える",
    source=SRC["k26_tapdoreiyu"])


# ================================================================ 鎧亜寄生パラス・キューピッド（29/77）
def e_paras(s, i, u):
    """出た時、相手のクリーチャー1体をタップし、次の自分のターンのはじめまでアンタップしない（フリーズ）"""
    t = s.target(i)
    if t is None:
        return
    s.tap_cre(1 - i, t)
    t.frz = 1
    s.ev(f"　パラス・キューピッド：{t.c.name} をタップして起こさない")


def mi_paras(s, i, k, src):
    """スペース・チャージ SC-闇：自分のマナゾーンに闇のカードが置かれた時（manain）

    相手のクリーチャー1体のパワーをこのターン-2000する（0以下なら破壊）。"""
    if "D" not in E.MCIV.get(k, "") or not s.has(i, "k26_paraskyupido"):
        return
    t = s.target(i)
    if t is None:
        return
    t.pw -= 2000
    s.ev(f"　SC-闇：{t.c.name} のパワーを-2000")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.ev(f"　{t.c.name} はパワー0以下で破壊される")
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


add("k26_paraskyupido", "鎧亜寄生パラス・キューピッド", 3, "L", power=4000,
    races=("lostcrusader", "alien"), pri=4, roles="dis rem",
    enter=e_paras, manain=mi_paras,
    text="出た時、相手のクリーチャー1体を選んでタップする。次の自分のターンのはじめまで、それはアンタップしない。"
         "スペース・チャージ（自分のマナゾーンにカードが置かれた時、その文明に合うSC能力を使ってもよい）。"
         "SC-闇：相手のクリーチャー1体を選び、このターン、そのクリーチャーのパワーを-2000する"
         "（パワーが0以下のクリーチャーは破壊される）",
    source=SRC["k26_paraskyupido"])
