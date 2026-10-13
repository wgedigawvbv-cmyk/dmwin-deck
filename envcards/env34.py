"""担当34：DM26-RP3「逆札篇 第3弾 勝敵！逆転おこせ鬼の∞ディスペクター!!」の未実装カード15枚（48/77〜62/77）

  key は `k34_` で始める。

  出典：dmwiki.net のカード個別ページ（`https://dmwiki.net/《カード名》`）と、
  PukiWiki の生ソース（`?plugin=template&refer=《カード名》`）。
  15枚すべてについて**別の質問で2回以上**読み、コスト・文明・種類・種族・パワー・ブレイク数・
  能力本文が一致することを確かめた。生ソースは行が途中で切れるので、数値や能力文の末尾が
  欠けた8枚（ボイノ・ブサント／スケプ-3／キユリ-2／コオニ-4／ヒミッツキッチ・グローブ／
  祝の瞬き 流終／真・メシアカリバー／覇王になる男 ググッピー／バイナラベーター）は
  同じページに**3回目の質問**をして能力文の全文と数値を確かめ直した。

  この札束に入っている新しい仕組み
    ・ササゲール（自分のディスペクターの召喚コストを減らし、そうしたらこのエレメントを破壊する）
      ……この弾のディスタス／タマシード5枚が持つ。エンジンに「軽減を使った時」の差し込み口が無いので、
      `freeacts` で「ササゲールを使って召喚する」手を足し、実際に使った時だけ破壊するようにした。
    ・ビビッドロー［水/火(2)］（翔天 スケプ-3）……`drawwatch` ＋ `costx`。
    ・バズレンダ［無色(2)］（妖精 キユリ-2）……`freeacts` で「2マナずつ追加して出す」手を足す。
    ・鬼タイム（邪鬼 コオニ-4）……自分と相手のシールドの合計が6つ以下。
    ・Jチェンジ4（マナ）／Jクライム6・4（墓地）……`atkswap`。
    ・「このクリーチャーをアンタップして、攻撃先をこれか自分のタップしているクリーチャーに変更」
      （祝の瞬き 流終）……`guard`。ガードマンそのものではないので `E.GUARDMEN` には入れない。
    ・タマシード側のツインパクト（クリスタの輝影／ザエッサの海影）……`kind="T"` ＋ `twin=`。
      エンジンの `legal_main` は呪文側をクリーチャー側のカードにしか出さないので、`freeacts` で足した
      （シールドからの S・トリガーは `Game.trigger` が `c.twin[2]` を見るのでそのまま働く）。
      → REQUEST_34.md の1番。

  調べ直して意外だった点
    ・《凄虫逆夢 ボイノ・ブサント》は EXライフ を持つが、「EXライフのシールドが離れた時」の誘発は
      持っていなかった（`envcards.env0.EXLOST` への登録は不要だった）。
    ・《妖精 キユリ-2》は《キユリのASMラジオ》とは無関係のスノーフェアリー／ディスタス。
      バズレンダの追加コストは自分の文明ではなく**無色(2)**。
    ・「◯◯の◯影」サイクルの2枚は、どちらもコスト2のタマシード＋ササゲール2だが、
      呪文側のコスト・効果は別（シディアン・ニーラム＝4・シールド化／六奇怪の無＝3・手札に戻す）。
    ・《龍装者 クシュトル》と《龍装者 ドヘブン》は同じ「龍装者」でも能力はまったく別系統
      （クシュトル＝自分のクリーチャーが1体だけなら離れない耐性、ドヘブン＝出た時2枚引く）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, move
from envcards.env0 import SLAYER, exlife_enter, exlife_rep, lock_until_my_turn, own_loss

W = "https://dmwiki.net/"
SRC = {
    "k34_boino": W + "《凄虫逆夢 ボイノ・ブサント》",
    "k34_skep": W + "《翔天 スケプ-3》",
    "k34_kiyuri": W + "《妖精 キユリ-2》",
    "k34_koni": W + "《邪鬼 コオニ-4》",
    "k34_himitsu": W + "《ヒミッツキッチ・グローブ》",
    "k34_rushu": W + "《祝の瞬き 流終》",
    "k34_messiah": W + "《真・メシアカリバー》",
    "k34_monkid": W + "《ヒトリダチ モンキッド》",
    "k34_kushtol": W + "《龍装者 クシュトル》",
    "k34_crysta": W + "《クリスタの輝影／シディアン・ニーラム》",
    "k34_doheven": W + "《龍装者 ドヘブン》",
    "k34_guppy": W + "《覇王になる男 ググッピー》",
    "k34_beach": W + "《ビーチボーイズ・II・メン》",
    "k34_zaessa": W + "《ザエッサの海影／六奇怪の無 〜氾濫する覇王〜》",
    "k34_binara": W + "《バイナラベーター》",
}


# ================================================================ ササゲール（共通）
def _onitime(s, i):
    """鬼タイム：自分と相手のシールドが合計6つ以下か"""
    return len(s.P[i].sh) + len(s.P[1 - i].sh) <= 6


SASAGERU = {
    "k34_skep": lambda s, i, u: 3,
    "k34_kiyuri": lambda s, i, u: 2,
    "k34_koni": lambda s, i, u: 4 if _onitime(s, i) else 0,      # 鬼タイム中だけ
    "k34_crysta": lambda s, i, u: 2,
    "k34_zaessa": lambda s, i, u: 2,
}


def _sas_srcs(s, i):
    """いま使えるササゲールの持ち主：[(下げる数, uid)]（下げる数の大きい順）"""
    out = []
    for z in s.P[i].board:
        f = SASAGERU.get(z.k)
        if f is None:
            continue
        n = f(s, i, z)
        if n > 0:
            out.append((n, z.uid))
    out.sort(reverse=True)
    return out


def acts_sasageru(s, i, av, cv):
    """ササゲール：自分のディスペクター・クリーチャーの召喚コストを減らし、使ったエレメントを破壊する。

    「もよい」なので、**ふつうのコストでは出せない時だけ**使い、足りる分だけのエレメントを使う
    （全デッキ共通の機械的な決め方。エンジンに「軽減を使った時」の差し込み口が無いので、
    こうして追加の手にしておけば、使わなかった時に勝手に自壊することがない）。"""
    p = s.P[i]
    srcs = _sas_srcs(s, i)
    if not srcs:
        return []
    out = []
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or "dispector" not in c.races:
            continue
        base = s.ccost(i, k, av)
        if base <= av or base >= 99 or not cv.issuperset(c.civ):
            continue
        cost, used = base, []
        for n, uid in srcs:
            if cost <= av:
                break
            cost = max(1, cost - n)        # ただしコストは0以下にならない
            used.append(uid)
        if cost > av or not used:
            continue
        if c.evo and not c.neo and s.evo_src(i, k) is None:
            continue
        if s.fate(i, k, "hand", True) != "ok":
            continue
        out.append(("x:k34_sas", k, cost, tuple(used)))
    return out


def ap_sasageru(s, a):
    i = s.tp
    p = s.P[i]
    k, cost, uids = a[1], a[2], a[3]
    if k not in p.hand:
        return
    srcs = [z for z in p.board if z.uid in uids and z.k in SASAGERU]
    if len(srcs) != len(uids):
        return
    c = BY_KEY[k]
    names = "・".join(z.c.name for z in srcs)
    for z in srcs:
        s.leave(i, z, "grave", destroy=True)
    if s.over or k not in p.hand:
        return
    on = s.evo_src(i, k) if c.evo else None
    if c.evo and not c.neo and on is None:
        return
    if s.fate(i, k, "hand", True) != "ok":
        return
    p.hand.remove(k)
    f = E.PAYX.get(k)                    # 召喚の時の追加の支払い（ハイパーエナジーなど）も忘れずに行う
    if f is not None:
        f(s, i, k, cost)
    p.mused += cost
    s.ev(f"ササゲール：{names} を破壊して {c.name} を{cost}マナで召喚")
    s.enter(i, k, "hand", True, on=on)


# ================================================================ タマシード側ツインパクトの呪文側
TWIN_T = ("k34_crysta", "k34_zaessa")


def acts_twin_t(s, i, av, cv):
    """以前は「タマシードのツインパクトの呪文側を唱える手」を自分で足していたが、
    エンジン（legal_main）がツインパクトの呪文側をカードの種類に関係なく出すように直ったので、
    もう何もしない（同じ手が二重に並ばないように空を返す）"""
    return []


def ap_twin_t(s, a):
    i = s.tp
    p = s.P[i]
    k, tc = a[1], a[2]
    if k not in p.hand:
        return
    p.hand.remove(k)
    p.mused += tc
    s.ev(f"呪文：{BY_KEY[k].name}（呪文側）")
    s.cast(i, k, True)


# ================================================================ Jチェンジ／Jクライム（共通）
def _jswap(s, i, u, zone, mx, label):
    """これと〈zone〉にあるコスト mx 以下のジョーカーズ・クリーチャー1体を入れ替える。
    入れ替えたら新しいクリーチャー（攻撃を続ける）を返す"""
    p = s.P[i]
    pool = p.mana if zone == "mana" else p.grave
    best, bv = None, E.PRI[u.k]
    for k in sorted(set(pool)):
        c = BY_KEY[k]
        if c.kind != "C" or "jokers" not in c.races or c.cost > mx:
            continue
        if c.evo and not c.neo:
            continue
        if E.PRI[k] <= bv:
            continue
        if s.fate(i, k, zone, False) != "ok":
            continue
        best, bv = k, E.PRI[k]
    if best is None or u not in p.board:
        return None
    j = p.board.index(u)
    if not s.leave(i, u, zone):          # 攻撃していたこのクリーチャーが〈zone〉へ
        return None
    if best not in pool:
        return None
    if zone == "mana":
        s.take_mana(i, best)
    else:
        pool.remove(best)
    nu = E.U(best)
    nu.tap = True
    nu.sick = False
    p.board.insert(min(j, len(p.board)), nu)
    p.ent += 1
    s.ev(f"　{label}：{u.c.name} と{'マナ' if zone == 'mana' else '墓地'}の {nu.c.name} を入れ替える")
    fn = E.ENTER.get(best)
    if fn is not None:
        fn(s, i, nu)
    for f in E.ENTERWATCH:
        if not s.over:
            f(s, i, nu)
    return nu if nu in p.board else None


# ================================================================ Jビッグ1
JBIG_NO = ("k34_monkid", "k30_jolagang", "k30_kento")      # Jビッグ1そのものを含む能力は元にできない
MAXJB = 3                                                  # 連鎖の深さの上限（手順が終わらなくなるのを防ぐ）


def _jbig1(s, i, src):
    """Jビッグ1：自分の他のジョーカーズの「出た時」の能力を1つ使う（使えたら True）。
    重要度のいちばん高いものを選ぶ（踏み倒し先の選び方と同じ全デッキ共通の決まり）"""
    p = s.P[i]
    cands = [z for z in p.board
             if z is not src and "jokers" in z.c.races and z.k not in JBIG_NO and E.ENTER.get(z.k) is not None]
    if not cands or s.over:
        return False
    d = p.x.get("k34_jb", 0)
    if d >= MAXJB:
        return False
    z = max(cands, key=lambda x: E.PRI[x.k])
    p.x["k34_jb"] = d + 1
    s.ev(f"　Jビッグ1：{z.c.name} の「出た時」の能力を使う")
    E.ENTER[z.k](s, i, z)
    s.P[i].x["k34_jb"] = d
    return True


# ================================================================ 48/77 凄虫逆夢 ボイノ・ブサント
def w_boino(s, i, u):
    """＜アバレチェーン＞自分のクリーチャーが攻撃する時、それがこのターン最初の攻撃なら、
    自分の山札の上から2枚をマナゾーンに置いてもよい。その後、カードを1枚、自分のマナゾーンから手札に戻してもよい"""
    if not s.has(i, "k34_boino"):
        return
    p = s.P[i]
    if p.x.get("k34_abare") == s.turn:
        return
    p.x["k34_abare"] = s.turn
    for z in p.board[:]:
        if z.k != "k34_boino" or s.over:
            continue
        s.ramp(i, 2)
        if p.mana:
            best = max(p.mana, key=E.PRI.get)
            s.take_mana(i, best)
            p.hand.append(best)
            s.ev(f"　アバレチェーン：山札の上2枚をマナへ、マナの {BY_KEY[best].name} を手札へ")
        else:
            s.ev("　アバレチェーン：山札の上2枚をマナへ")


add("k34_boino", "凄虫逆夢 ボイノ・ブサント", 5, "LN", power=6500, brk=2, blocker=True,
    races=("dispector", "beastfolk", "gransect", "boukenoukoku"), pri=9, roles="acc blk draw atk",
    enter=exlife_enter, leaverep=exlife_rep, atkwatch=w_boino,
    text="EXライフ（出た時、山札の上から1枚をこのクリーチャーの下にシールドとして置く。離れる時、"
         "かわりにそのシールドを墓地に置く）。ブロッカー。W・ブレイカー。"
         "＜アバレチェーン＞自分のクリーチャーが攻撃する時、それがこのターン最初の攻撃なら、"
         "自分の山札の上から2枚をマナゾーンに置いてもよい。その後、カードを1枚、自分のマナゾーンから手札に戻してもよい",
    note="アバレチェーンは、マナが2枚増えて手札が1枚増えるので常に使う。マナから手札に戻すのは"
         "重要度のいちばん高いカード（全デッキ共通の決まり）。「このターン最初の攻撃か」は、"
         "このクリーチャーが場にいる間の最初の攻撃で数えるので、1回目の攻撃のあとに"
         "革命チェンジなどでこのクリーチャーが出た場合は2回目の攻撃で誘発する",
    source=SRC["k34_boino"])


# ================================================================ 49/77 翔天 スケプ-3
def dw_skep(s, i, k):
    """ビビッドロー［水/火(2)］：自分のターン中に引いたら、そのターンは2マナで召喚してよい。
    表向きにした枚数を数えておき、2マナで出すたびに1枚ぶん減らす（手札に2枚あっても、引いた分だけ軽くなる）"""
    if k != "k34_skep" or s.tp != i:
        return
    p = s.P[i]
    t, n = p.x.get("k34_vivid", (-1, 0))
    p.x["k34_vivid"] = (s.turn, (n if t == s.turn else 0) + 1)


def _vivid_n(s, i):
    t, n = s.P[i].x.get("k34_vivid", (-1, 0))
    return n if t == s.turn else 0


def cx_skep(s, i, av):
    return 2 if _vivid_n(s, i) > 0 else 4


def px_skep(s, i, k, n):
    """2マナで召喚したら、表向きにしていた1枚ぶんを使い切る"""
    if _vivid_n(s, i) > 0:
        t, c = s.P[i].x["k34_vivid"]
        s.P[i].x["k34_vivid"] = (t, c - 1)


def e_skep(s, i, u):
    """出た時、カードを4枚引く。その後、自分の手札を2枚、好きな順序で山札の上に置く"""
    p = s.P[i]
    s.draw(i, 4)
    back = []
    for _ in range(2):
        if not p.hand:
            break
        k = min(p.hand, key=E.PRI.get)
        p.hand.remove(k)
        back.append(k)
        p.deck.append(k)                 # 山札の上（あとで置いたものが先に引ける）
    if back:
        s.ev(f"　翔天 スケプ-3：4枚引いて {len(back)}枚を山札の上に戻した")


add("k34_skep", "翔天 スケプ-3", 4, "WF", power=4000,
    races=("firebird", "distas", "bikoureioukoku"), pri=7, roles="draw acc",
    enter=e_skep, drawwatch=dw_skep, costx=cx_skep, payx=px_skep,
    freeacts=acts_sasageru, actapply={"x:k34_sas": ap_sasageru},
    text="ビビッドロー［水/火(2)］（自分のターン中、攻撃する前にこのクリーチャーを引いた時、表向きにしてもよい。"
         "そうしたら、このターン、2マナで召喚してもよい）。"
         "このクリーチャーが出た時、カードを4枚引く。その後、自分の手札を2枚、好きな順序で山札の上に置く。"
         "ササゲール3（自分のディスペクター・クリーチャーの召喚コストを3少なくしてもよい。"
         "そうしたら、このエレメントを破壊する。ただしコストは0以下にならない）",
    note="ビビッドローの「攻撃する前に」は、このシミュレーターでは攻撃に入ったあとにクリーチャーを"
         "召喚する手が無いので、自分のターン中に引いたかどうかだけを見ている（表せない差は出ない）。"
         "山札の上に戻す2枚は重要度のいちばん低い2枚（戻す順は、ましな方が先に引けるようにする）",
    source=SRC["k34_skep"])


# ================================================================ 50/77 妖精 キユリ-2
def _br_kiyuri(s, i):
    """BR－自分の山札の上から1枚を見る。そのカードを手札に加えるか、タップしてマナゾーンに置く"""
    p = s.P[i]
    if not p.deck:
        return
    k = p.deck[-1]
    if len(p.mana) <= 3 or E.PRI[k] <= 3:
        s.ramp(i, 1)
        s.ev(f"　BR：{BY_KEY[k].name} をタップしてマナゾーンへ")
    elif len(p.deck) <= 1:
        s.draw(i, 1)                     # 山札が尽きる時はエンジンの引く処理にまかせる
    else:
        p.hand.append(p.deck.pop())
        s.ev(f"　BR：{BY_KEY[k].name} を手札へ")


def e_kiyuri(s, i, u):
    n = 1 + s.P[i].x.get("k34_buzz", 0)
    for _ in range(n):
        if s.over:
            break
        _br_kiyuri(s, i)


def acts_kiyuri(s, i, av, cv):
    """バズレンダ［無色(2)］：コストを支払う時、追加で無色2を好きな回数支払ってよい"""
    p = s.P[i]
    if "k34_kiyuri" not in p.hand:
        return []
    base = s.ccost(i, "k34_kiyuri", av)
    if base >= 99 or not cv.issuperset("WN"):
        return []
    if s.fate(i, "k34_kiyuri", "hand", True) != "ok":
        return []
    out = []
    for n in range(1, 4):
        cost = base + 2 * n
        if cost > av:
            break
        out.append(("x:k34_buzz", cost, n))
    return out


def ap_kiyuri(s, a):
    i = s.tp
    p = s.P[i]
    if "k34_kiyuri" not in p.hand:
        return
    p.hand.remove("k34_kiyuri")
    p.mused += a[1]
    s.ev(f"バズレンダ：妖精 キユリ-2（{a[1]}マナ、追加{a[2]}回）")
    p.x["k34_buzz"] = a[2]
    try:
        s.enter(i, "k34_kiyuri", "hand", True)
    finally:
        p.x.pop("k34_buzz", None)


add("k34_kiyuri", "妖精 キユリ-2", 3, "WN", power=2000,
    races=("snowfu", "snow", "distas", "teamwave"), pri=5, roles="acc draw",
    enter=e_kiyuri, freeacts=acts_kiyuri, actapply={"x:k34_buzz": ap_kiyuri},
    text="バズレンダ［無色(2)］（このクリーチャーのコストを支払う時、追加で無色2を好きな回数支払ってよい。"
         "出た時、BR能力を1回と、追加で支払った回数ぶん使う）。"
         "BR－自分の山札の上から1枚を見る。そのカードを手札に加えるか、タップしてマナゾーンに置く。"
         "ササゲール2（自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたら、このエレメントを破壊する。ただしコストは0以下にならない）",
    note="バズレンダの追加は3回までにしている（手が増えすぎるのを防ぐため）。"
         "BRの選び方は、マナが3枚以下か見たカードの重要度が3以下ならマナゾーン、それ以外は手札（全デッキ共通の決まり）",
    source=SRC["k34_kiyuri"])


# ================================================================ 51/77 邪鬼 コオニ-4
def te_koni(s, i, u):
    """自分のターンの終わりに、自分のシールドを1つ手札に加える（その「S・トリガー」は使えない）"""
    p = s.P[i]
    if not p.sh:
        return
    k, up = p.sh.pop()
    s.shield_left()
    for f in E.SHIELDOUT:
        f(s, i, k, up, "hand")
    p.hand.append(k)
    s.ev(f"　邪鬼 コオニ-4：シールドを1つ手札へ（残り{len(p.sh)}、S・トリガーは使えない）")


add("k34_koni", "邪鬼 コオニ-4", 2, "DF", power=2000,
    races=("demonio", "distas", "onifuda"), pri=5, roles="draw acc rem",
    tend=te_koni,
    text="スレイヤー。"
         "自分のターンの終わりに、自分のシールドを1つ手札に加える。その「S・トリガー」は使えない。"
         "＜鬼タイム＞自分と相手のシールドが合計6つ以下なら、このクリーチャーに「ササゲール4」を与える"
         "（自分のディスペクター・クリーチャーの召喚コストを4少なくしてもよい。"
         "そうしたら、このエレメントを破壊する。ただしコストは0以下にならない）",
    source=SRC["k34_koni"])
SLAYER.add("k34_koni")


# ================================================================ 52/77 ヒミッツキッチ・グローブ
def e_himitsu(s, i, u):
    """出た時、自分の山札の上から3枚を墓地に置く。その後、クリーチャーを1体、自分の墓地からマナゾーンに置いてもよい"""
    p = s.P[i]
    s.mill(i, 3)
    cs = [k for k in set(p.grave) if BY_KEY[k].kind == "C"]
    if not cs:
        return
    k = min(cs, key=E.PRI.get)
    p.grave.remove(k)
    s.add_mana(i, k, True, src="grave")
    s.ev(f"　ヒミッツキッチ・グローブ：墓地の {BY_KEY[k].name} をマナゾーンへ")


def swap_himitsu(s, i, u):
    """Jクライム6（墓地）→ Jチェンジ4（マナ）の順に試す"""
    nu = _jswap(s, i, u, "grave", 6, "Jクライム6")
    if nu is not None:
        return nu
    return _jswap(s, i, u, "mana", 4, "Jチェンジ4")


add("k34_himitsu", "ヒミッツキッチ・グローブ", 3, "DN", power=3000,
    races=("jokers",), pri=5, roles="acc atk",
    enter=e_himitsu, atkswap=swap_himitsu,
    text="このクリーチャーが出た時、自分の山札の上から3枚を墓地に置く。"
         "その後、クリーチャーを1体、自分の墓地からマナゾーンに置いてもよい。"
         "Jチェンジ4（このクリーチャーが攻撃する時、これと自分のマナゾーンにあるコスト4以下の"
         "ジョーカーズ・クリーチャー1体を入れ替えてもよい）。"
         "Jクライム6（このクリーチャーが攻撃する時、これと自分の墓地にあるコスト6以下の"
         "ジョーカーズ・クリーチャー1体を入れ替えてもよい）",
    note="墓地からマナゾーンに置くクリーチャーは、失うのがいちばん安いもの（全デッキ共通の決まり）。"
         "入れ替えは、重要度がより上がる方を墓地（6以下）→マナ（4以下）の順に試す",
    source=SRC["k34_himitsu"])


# ================================================================ 53/77 祝の瞬き 流終
def gd_rushu(s, di, au, tu):
    """このクリーチャーをアンタップして、相手クリーチャーの攻撃先をこのクリーチャーまたは
    自分のタップしているクリーチャーに変更してもよい。

    使うかどうかは全デッキ共通の決まりで決める：バトルに勝てる引き受け先があるか、
    もとの攻撃先のほうが大事な時だけ引き受ける"""
    ap = s.power(1 - di, au, True)
    for z in s.P[di].board:
        if z.k != "k34_rushu" or z.c.kind != "C" or not z.tap or z is tu:
            continue                      # 「アンタップして」が支払えるのはタップしている時だけ
        cands = [z] + [x for x in s.P[di].board
                       if x.c.kind == "C" and x.tap and x is not z and x is not tu]
        win = [x for x in cands if s.power(di, x) > ap]
        if win:
            nt = max(win, key=lambda x: s.power(di, x))
        else:
            nt = min(cands, key=lambda x: own_loss(s, di, x))
            if tu is None or s.val(tu) <= s.val(nt):
                continue                  # 誰も生き残れないなら、守る値打ちがある時だけ引き受ける
        z.tap = False
        s.ev("　祝の瞬き 流終：アンタップして攻撃先を変更")
        return nt
    return None


add("k34_rushu", "祝の瞬き 流終", 6, "L", power=12500, brk=3,
    races=("metallica",), pri=9, roles="blk",
    guard=gd_rushu,
    text="T・ブレイカー。"
         "このクリーチャーをアンタップして、相手クリーチャーの攻撃先をこのクリーチャーまたは"
         "自分のタップしているクリーチャーに変更してもよい",
    note="「アンタップして」を支払えるのはこのクリーチャーがタップしている時だけとした。"
         "引き受けるかどうかは、バトルに勝てる引き受け先があるか、もとの攻撃先のほうが"
         "値打ちが高い時だけ（全デッキ共通の決まり）",
    source=SRC["k34_rushu"])


# ================================================================ 54/77 真・メシアカリバー
def e_messiah(s, i, u):
    """出た時、相手のクリーチャーを3体まで選び、タップする"""
    n = 0
    for _ in range(3):
        t = s.target(i, lambda x: not x.tap)
        if t is None:
            break
        s.tap_cre(1 - i, t)
        n += 1
    if n:
        s.ev(f"　真・メシアカリバー：相手のクリーチャー{n}体をタップ")


add("k34_messiah", "真・メシアカリバー", 5, "L", power=4000, trig=True,
    races=("metallica", "sabakist"), pri=7, roles="trg dis atk",
    enter=e_messiah,
    text="S・トリガー。このクリーチャーが出た時、相手のクリーチャーを3体まで選び、タップする",
    source=SRC["k34_messiah"])


# ================================================================ 55/77 ヒトリダチ モンキッド
def e_monkid(s, i, u):
    """出た時、次の中から1回選ぶ。▶クリーチャーを1体選び、タップまたはアンタップする　▶Jビッグ1する"""
    if _jbig1(s, i, u):
        return
    if s.tp != i:
        z = next((x for x in s.P[i].board if x.c.kind == "C" and x.tap and x.c.blocker), None)
        if z is not None:
            z.tap = False
            s.ev(f"　ヒトリダチ モンキッド：{z.c.name} をアンタップ")
            return
    t = s.target(i, lambda x: not x.tap)
    if t is not None:
        s.tap_cre(1 - i, t)
        s.ev(f"　ヒトリダチ モンキッド：相手の {t.c.name} をタップ")
        return
    cands = [x for x in s.P[i].board if x.c.kind == "C" and x.tap]
    if cands:
        z = max(cands, key=lambda x: s.power(i, x))
        z.tap = False
        s.ev(f"　ヒトリダチ モンキッド：{z.c.name} をアンタップ")


add("k34_monkid", "ヒトリダチ モンキッド", 4, "L", power=4000, trig=True,
    races=("jokers",), pri=6, roles="trg dis",
    enter=e_monkid,
    text="S・トリガー。"
         "このクリーチャーが出た時、次の中から1回選ぶ。"
         "▶クリーチャーを1体選び、タップまたはアンタップする。"
         "▶Jビッグ1する（自分の他のジョーカーズの、Jビッグ1以外の、出た時にトリガーする能力を1つ使う）",
    note="選び方は全デッキ共通の決まり：Jビッグ1に使える相手がいればそれを選ぶ。"
         "いなければ、相手のターン中なら自分のタップしているブロッカーをアンタップし、"
         "そうでなければ相手のいちばん大事なアンタップしているクリーチャーをタップする。"
         "Jビッグ1の元には、Jビッグ1を含む能力を持つカード自身は選ばない。連鎖は深さ3までで止める",
    source=SRC["k34_monkid"])


# ================================================================ 56/77 龍装者 クシュトル
def lr_kushtol(s, i, u, dest, destroy_):
    """自分のクリーチャーがこのクリーチャーだけなら、このクリーチャーは離れない"""
    if u.k != "k34_kushtol":
        return False
    if sum(1 for z in s.P[i].board if z.c.kind == "C") != 1:
        return False
    s.ev("　龍装者 クシュトル：自分のクリーチャーがこれだけなので離れない")
    return True


add("k34_kushtol", "龍装者 クシュトル", 3, "L", power=2500, blocker=True,
    races=("dragonguild", "metallica"), pri=5, roles="blk",
    leaverep=lr_kushtol,
    text="ブロッカー。自分のクリーチャーがこのクリーチャーだけなら、このクリーチャーは離れない",
    source=SRC["k34_kushtol"])


# ================================================================ 57/77 クリスタの輝影／シディアン・ニーラム
def sp_crysta(s, i):
    """シディアン・ニーラム：相手のクリーチャーを1体選び、シールド化する"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　シディアン・ニーラム：相手の {t.c.name} をシールド化")
    s.leave(1 - i, t, "shield", by_opp=True)


add("k34_crysta", "クリスタの輝影／シディアン・ニーラム", 2, "L", kind="T",
    races=("metallica", "distas"), twin=(4, "L", True), pri=6, roles="rem trg acc",
    spell=sp_crysta, freeacts=acts_twin_t, actapply={"x:k34_tspell": ap_twin_t},
    text="＜タマシード側＞クリスタの輝影（光2・タマシード：メタリカ／ディスタス）。"
         "ササゲール2（自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたら、このエレメントを破壊する。ただしコストは0以下にならない）。"
         "＜呪文側＞シディアン・ニーラム（光4）。S・トリガー。相手のクリーチャーを1体選び、シールド化する",
    source=SRC["k34_crysta"])


# ================================================================ 58/77 龍装者 ドヘブン
add("k34_doheven", "龍装者 ドヘブン", 5, "W", power=8000, brk=2, blocker=True,
    races=("dragonguild", "mutopia"), pri=8, roles="draw blk",
    enter=lambda s, i, u: s.draw(i, 2),
    text="ブロッカー。W・ブレイカー。このクリーチャーが出た時、カードを2枚引く",
    source=SRC["k34_doheven"])


# ================================================================ 59/77 覇王になる男 ググッピー
def e_guppy(s, i, u):
    """出た時、相手のエレメントを1つ選ぶ。相手はそれを山札の上か下に置く"""
    t = s.target(i, kinds="CTX")
    if t is None:
        return
    s.ev(f"　覇王になる男 ググッピー：相手の {t.c.name} を山札の上へ")
    s.leave(1 - i, t, "decktop", by_opp=True)


add("k34_guppy", "覇王になる男 ググッピー", 5, "W", power=4000, trig=True,
    races=("mutopia",), pri=7, roles="rem trg",
    enter=e_guppy,
    text="S・トリガー。このクリーチャーが出た時、相手のエレメントを1つ選ぶ。相手はそれを山札の上か下に置く",
    note="どちらに置くかは持ち主（相手）が決めるので、カードが残る山札の上を選ぶものとして扱っている",
    source=SRC["k34_guppy"])


# ================================================================ 60/77 ビーチボーイズ・II・メン
def _beach(s, i):
    t = s.target(i)
    if t is None:
        return
    lock_until_my_turn(s, i, t)
    s.ev(f"　ビーチボーイズ・II・メン：相手の {t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k34_beach", "ビーチボーイズ・II・メン", 2, "W", power=1000,
    races=("jokers",), pri=4, roles="dis",
    enter=lambda s, i, u: _beach(s, i), left=lambda s, i, u, dest: _beach(s, i),
    text="このクリーチャーが出た時または離れた時、相手のクリーチャーを1体選ぶ。"
         "次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない",
    source=SRC["k34_beach"])


# ================================================================ 61/77 ザエッサの海影／六奇怪の無 〜氾濫する覇王〜
def sp_zaessa(s, i):
    """六奇怪の無 〜氾濫する覇王〜：相手のエレメントを1つ選び、持ち主の手札に戻す"""
    t = s.target(i, kinds="CTX")
    if t is None:
        return
    s.ev(f"　六奇怪の無：相手の {t.c.name} を手札に戻す")
    move(s, i, t, "hand")


add("k34_zaessa", "ザエッサの海影／六奇怪の無 〜氾濫する覇王〜", 2, "W", kind="T",
    races=("mutopia", "distas"), twin=(3, "W", True), pri=6, roles="rem trg acc",
    spell=sp_zaessa,
    text="＜タマシード側＞ザエッサの海影（水2・タマシード：ムートピア／ディスタス）。"
         "ササゲール2（自分のディスペクター・クリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたら、このエレメントを破壊する。ただしコストは0以下にならない）。"
         "＜呪文側＞六奇怪の無 〜氾濫する覇王〜（水3）。S・トリガー。"
         "相手のエレメントを1つ選び、持ち主の手札に戻す",
    source=SRC["k34_zaessa"])


# ================================================================ 62/77 バイナラベーター
def e_binara(s, i, u):
    """出た時、相手のクリーチャーを1体選び、持ち主の山札の下に置く"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　バイナラベーター：相手の {t.c.name} を山札の下へ")
    s.leave(1 - i, t, "deck", by_opp=True)


add("k34_binara", "バイナラベーター", 6, "D", power=3000, trig=True,
    races=("jokers",), pri=8, roles="rem trg atk",
    enter=e_binara, atkswap=lambda s, i, u: _jswap(s, i, u, "grave", 4, "Jクライム4"),
    text="S・トリガー。"
         "このクリーチャーが出た時、相手のクリーチャーを1体選び、持ち主の山札の下に置く。"
         "Jクライム4（このクリーチャーが攻撃する時、これと自分の墓地にあるコスト4以下の"
         "ジョーカーズ・クリーチャー1体を入れ替えてもよい）",
    source=SRC["k34_binara"])
