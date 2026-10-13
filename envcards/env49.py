"""担当49：DM26-SD1「ドキドキつよいデッキ 25の王道」の15枚（key は k49_）

  この箱は25個の構築済みデッキを1箱にまとめた商品で、中身は過去の強いカードの再録が中心。
  担当分には、殿堂入りの古い札（サイバー・ブレイン＝のちに解除／デビル・ドレーン／
  黒神龍ブライゼナーガ／蒼き団長 ドギラゴン剣／天命龍装 ホーリーエンド）と、
  最近の札（魔誕と光喜と楽識と炎怒と哀樹の決断／魔誕の封殺ディアス Z／深淵の逆転撃）が混ざっている。

  この札束で使った仕組み
    ・パーフェクト呪文（自分のエレメントに5文明そろえば、2回選ぶかわりに5つ全部を1回ずつ）
    ・逆転撃（相手の攻撃時に手札からただで唱え、次の自分のターンのはじめに後払い。払えなければ負け）
    ・バズレンダ（追加の[無色(3)]を好きな回数払い、払った回数ぶんBR能力を増やす）
    ・D・D・D[闇/火/自然(4)]（自分のクリーチャーの攻撃時、4マナで手札から出す。env12 と同じ書き方）
    ・G-NEO進化（進化元なしで召喚でき、離れる時はかわりに下のカードがすべて離れる＝エンジンの gneo=True）
    ・ファイナル革命（革命チェンジで出た時。そのターン1回は s.P[i].final_turn で共有）
    ・革命2（シールドゾーンからS・トリガーを得る）／革命0（シールド0でパワー+10000・SA・T・ブレイカー）
    ・無月の門99（自分のターンの終わり、フィールドの下が4枚以上でゲーム中1度だけ水の呪文をただで唱える）

  調べ直して確かめたところ
    15枚すべてについて dmwiki.net のカードページ（`https://dmwiki.net/《カード名》`）と
    生の wiki ソース（`?plugin=template&refer=…`）を**別の質問で2回ずつ**読み、
    コスト・文明・種類・種族・パワー・ブレイク数・能力本文が一致することを確かめた。
    1回目の読みで間違っていたのは《ナウ・オア・ネバー》で、「手札または墓地から出す」と返ってきたが、
    2回目・3回目は「自分の手札から出してもよい。その後、そのクリーチャーを手札に戻す」で一致した
    （手札限定・即戻しが正しい。出た時の能力を使い回すための札）。
    《覚醒連結 XXDDZ》は名前が「覚醒」なのでサイキック・クリーチャー（超次元）だと思ったが、
    実際は DMRP-20 のディスペクターで超次元は関係なかった。
    《卍 新世壊 卍》はタマシードではなく**無月フィールド**（コスト2・水）だった。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all
from envcards.env0 import exlife_enter, exlife_rep

W = "https://dmwiki.net/"
SRC = {
    "k49_ketsudan": W + "《魔誕と光喜と楽識と炎怒と哀樹の決断》",
    "k49_holyend": W + "《天命龍装 ホーリーエンド／ナウ・オア・ネバー》",
    "k49_xxddz": W + "《覚醒連結 XXDDZ》",
    "k49_social": W + "《ソーシャル・マニフェストII世》",
    "k49_gyakuten": W + "《深淵の逆転撃》",
    "k49_jaouga": W + "《鬼ヶ大王 ジャオウガ》",
    "k49_dogiragoken": W + "《蒼き団長 ドギラゴン剣》",
    "k49_katsuking": W + "《切札勝太＆カツキング -熱血の物語-》",
    "k49_dogiragosen": W + "《蒼き守護神 ドギラゴン閃》",
    "k49_cyberbrain": W + "《サイバー・ブレイン》",
    "k49_devildrain": W + "《デビル・ドレーン》",
    "k49_blizenaga": W + "《黒神龍ブライゼナーガ》",
    "k49_dias": W + "《魔誕の封殺ディアス Z》",
    "k49_shinsekai": W + "《卍 新世壊 卍》",
    "k49_zomenzan": W + "《堕呪 ゾメンザン》",
}


# ================================================================ 共通の道具
def _plain_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化クリーチャーは進化元が要るので除く。NEOは出せる）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _multi(k):
    """多色カードか（ツインパクトは両面の文明をまとめて見る）"""
    return E.MULTI.get(k, False)


def _top(s, i, n):
    """山札の上から n 枚を取り出す（足りなければあるだけ）"""
    p = s.P[i]
    n = min(n, len(p.deck))
    return [p.deck.pop() for _ in range(n)]


def _bottom(s, i, cards):
    for k in cards:
        s.P[i].deck.insert(0, k)


def _mana_to_hand(s, i, keep=1):
    """自分のマナゾーンから重要度のいちばん高いカードを1枚手札に戻す（使えるマナを keep 個は残す）"""
    p = s.P[i]
    if not p.mana or len(p.mana) - p.mused < keep + 1:
        return None
    k = max(p.mana, key=E.PRI.get)
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　マナの {BY_KEY[k].name} を手札に戻した")
    return k


def _ddd_ok(s, i, key, cost, civ):
    """D・D・D：手札のそのカードを、その色のマナ cost 枚で出せるか（env12 と同じ考え方）"""
    p = s.P[i]
    if key not in p.hand or len(p.mana) - p.mused < cost:
        return False
    if not (set(civ) & E.civs(p)):
        return False
    return s.fate(i, key, "hand", True) == "ok"


def _ddd_src(s, i, civ):
    """D・D・D で出す時に進化元にするカード（いま攻撃しているクリーチャーは選べない）"""
    best, bv = None, None
    for z in s.P[i].board:
        if z.c.kind != "C" or z is s.atk or not (set(civ) & set(z.c.civ)):
            continue
        v = (z.tap, E.PRI[z.k] + len(z.under))
        if bv is None or v < bv:
            best, bv = z, v
    return best


def _cast_free(s, i, zones, pred):
    """手札・マナ・墓地からコストを支払わずに呪文1枚を唱える（重要度のいちばん高いもの）"""
    p = s.P[i]
    best, bv, zn, tw = None, -1, None, False
    for zname in zones:
        if zname == "mana" and s.manaexec(i):
            continue
        if zname == "grave" and s.manaexec(i):
            continue
        zone = {"hand": p.hand, "mana": p.mana, "grave": p.grave}[zname]
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            for twin in (False, True):
                if twin and not c.twin:
                    continue
                if not twin and c.kind != "S":
                    continue
                cost = c.twin[0] if twin else c.cost
                if not pred(c, cost) or not s.spell_ok(i, cost):
                    continue
                if E.PRI[k] > bv:
                    best, bv, zn, tw = k, E.PRI[k], zname, twin
    if best is None:
        return False
    if zn == "mana":
        s.take_mana(i, best)
    else:
        (p.hand if zn == "hand" else p.grave).remove(best)
    s.ev(f"　コストを支払わずに {BY_KEY[best].name} を唱える")
    s.cast(i, best, tw)
    return True


def _put_multi(s, i, cards, budget, zone):
    """cards（キーの並び）から、コストの合計が budget 以下になるように進化でない多色クリーチャーを出す。
    出せなかったカードを返す。どれを出すかは重要度の高いものから（全デッキ共通の決まり）"""
    rest = list(cards)
    while budget > 0 and not s.over:
        best, bv = None, -1
        for k in rest:
            c = BY_KEY[k]
            if not _plain_cre(c) or not _multi(k) or c.cost > budget:
                continue
            if E.PRI[k] > bv and s.fate(i, k, zone, False) == "ok":
                best, bv = k, E.PRI[k]
        if best is None:
            break
        rest.remove(best)
        budget -= BY_KEY[best].cost
        s.ev(f"　ファイナル革命：{BY_KEY[best].name} を出す")
        s.enter(i, best, zone, False)
    return rest


# ================================================================ 魔誕と光喜と楽識と炎怒と哀樹の決断
def _kd_shield(s, i):
    s.ev("　決断：自分の山札の上から1枚をシールド化する")
    s.add_shield(i)


def _kd_draw(s, i):
    s.ev("　決断：2枚引く")
    s.draw(i, 2)


def _kd_hand(s, i):
    s.ev("　決断：相手の手札を1枚見ないで捨てさせる")
    s.discard_random(1 - i)


def _kd_dest(s, i):
    t = s.target(i, lambda z: z.c.cost <= 6, kinds="CTX")
    if t is None:
        return
    s.ev(f"　決断：相手の {t.c.name} を破壊する")
    destroy(s, i, t)


def _kd_mana(s, i):
    s.ev("　決断：山札の上から1枚目をマナゾーンに置く")
    s.ramp(i, 1)
    _mana_to_hand(s, i)


def _kd_vals(s, i):
    """5つのモードの効き目（PRI の合計と、残りのシールド・山札で機械的に決める）"""
    p, o = s.P[i], s.P[1 - i]
    t = s.target(i, lambda z: z.c.cost <= 6, kinds="CTX")
    return [
        (3 + (3 if len(p.sh) <= 2 else 0)) if len(p.deck) > 1 else -1,      # シールド化
        5 if len(p.deck) > 2 else -1,                                       # 2枚引く
        3 if o.hand else -1,                                                # ハンデス
        (s.val(t) + 2) if t is not None else -1,                            # 破壊
        (3 if len(p.deck) > 1 else -1),                                     # マナ加速＋回収
    ]


_KD_FNS = (_kd_shield, _kd_draw, _kd_hand, _kd_dest, _kd_mana)


def _kd_all_civ(s, i):
    """自分のエレメント（バトルゾーンのカード）に5文明そろっているか"""
    got = set()
    for z in s.P[i].board:
        got |= set(z.c.civ)
    return set("LWDFN") <= got


def sp_ketsudan(s, i):
    if _kd_all_civ(s, i):
        s.ev("　パーフェクト呪文：自分のエレメントに全文明がそろっているので5つすべてを1回ずつ")
        for f in _KD_FNS:
            if s.over:
                return
            f(s, i)
        return
    for _ in range(2):
        if s.over:
            return
        vals = _kd_vals(s, i)
        j = max(range(5), key=lambda x: vals[x])
        if vals[j] <= 0:
            return
        _KD_FNS[j](s, i)


add("k49_ketsudan", "魔誕と光喜と楽識と炎怒と哀樹の決断", 5, "LWDFN", kind="S", pri=7,
    roles="shd draw dis rem acc", spell=sp_ketsudan,
    text="パーフェクト呪文。次の中から2回選ぶ（同じものを選んでもよい）。"
         "自分のエレメントにすべての文明がそろっていれば、かわりにすべてを1回ずつ使ってもよい。"
         "(1)自分の山札の上から1枚をシールド化する／(2)カードを2枚引く／"
         "(3)相手の手札を1枚見ないで選び、捨てさせる／(4)相手のコスト6以下のエレメント1つを選び、破壊する／"
         "(5)自分の山札の上から1枚目をマナゾーンに置く。その後、自分のマナゾーンからカードを1枚手札に戻してもよい。"
         "どれを選ぶかは、取り除ける相手のカードの重要度と、自分のシールド・山札の残りで機械的に決める",
    note="(5)でマナから手札に戻すのは「そのターンに使えるマナが2つ以上残る時だけ、重要度のいちばん高い1枚」"
         "（マナを削りすぎないための全デッキ共通の決まり）。"
         "(4)のエレメントは、このシミュレーターでバトルゾーンに置かれるもの"
         "（クリーチャー・タマシード・クロスギア）を見る。G城はシールドゾーンにあるので選べない",
    source=SRC["k49_ketsudan"])


# ================================================================ 天命龍装 ホーリーエンド／ナウ・オア・ネバー
def e_holyend(s, i, u):
    """出た時、相手のクリーチャーをすべてタップする。その後、1枚引く"""
    for z in s.P[1 - i].board[:]:
        if z.c.kind == "C":
            s.tap_cre(1 - i, z)
    s.draw(i, 1)


def sp_nowornever(s, i):
    """コスト7以下の進化ではないクリーチャー1体を自分の手札から出し、その後それを手札に戻す"""
    p = s.P[i]
    best, bv = None, None
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if not _plain_cre(c) or c.cost > 7:
            continue
        if s.fate(i, k, "hand", False) != "ok":
            continue
        # すぐ手札に戻るので、「出た時」の能力を持つクリーチャーを優先する（機械的な決まり）
        v = (1 if k in E.ENTER else 0, E.PRI[k])
        if bv is None or v > bv:
            best, bv = k, v
    if best is None:
        return
    p.hand.remove(best)
    s.ev(f"　ナウ・オア・ネバー：{BY_KEY[best].name} を出して手札に戻す")
    z = s.enter(i, best, "hand", False)
    if z is not None and z in p.board:
        s.leave(i, z, "hand")


add("k49_holyend", "天命龍装 ホーリーエンド / ナウ・オア・ネバー", 7, "L", power=9500, brk=2, blocker=True,
    races=("dragonguild", "metallica"), twin=(5, "W", True), pri=9, roles="blk dis draw trg",
    enter=e_holyend, spell=sp_nowornever,
    text="クリーチャー側《天命龍装 ホーリーエンド》（光7・9500）：ブロッカー、W・ブレイカー。"
         "出た時、相手のクリーチャーをすべてタップする。その後、カードを1枚引く。"
         "呪文側《ナウ・オア・ネバー》（水5）：S・トリガー。"
         "コスト7以下の進化ではないクリーチャー1体を自分の手札から出してもよい。"
         "その後、そのクリーチャーを手札に戻す（出すのは「出た時」の能力を持つもののうち重要度のいちばん高いもの）",
    note="2026年10月時点で殿堂入り（デッキに1枚まで）",
    source=SRC["k49_holyend"])


# ================================================================ 覚醒連結 XXDDZ
def e_xxddz(s, i, u):
    exlife_enter(s, i, u)


def sa_xxddz(s, i, u):
    """自分のクリーチャーすべてにスピードアタッカーを与える"""
    return u.c.kind == "C" and s.has(i, "k49_xxddz")


def bf_xxddz(s, ai, au, di, du, a_dies, d_dies):
    """自分のクリーチャーすべてにスレイヤーを与える"""
    if au.c.kind == "C" and s.has(ai, "k49_xxddz"):
        d_dies = True
    if du.c.kind == "C" and s.has(di, "k49_xxddz"):
        a_dies = True
    return a_dies, d_dies


def a_xxddz(s, i, u):
    """攻撃する時、EXライフのシールドを墓地に置いてもよい。
    そうしたら、次の自分のターンのはじめまで相手は呪文を唱えられない"""
    if not u.x.get("ex"):
        return
    u.x["ex"] = 0
    k = u.x.pop("excard", None)
    if k is not None:
        s.grave_put(i, k)
    s.P[1 - i].x["k49_nospell"] = s.turn + 1
    s.ev("　XXDDZ：EXライフのシールドを墓地に置き、次の自分のターンのはじめまで相手は呪文を唱えられない")


def sl_xxddz(s, j, cost):
    """j は呪文を唱えられない（XXDDZ の効果を受けている間）"""
    return s.P[j].x.get("k49_nospell", -1) >= s.turn


add("k49_xxddz", "覚醒連結 XXDDZ", 7, "LDF", power=8000, brk=2,
    races=("dispector", "armoreddragon", "dragon", "worldcommand", "command"), pri=10,
    roles="atk fin dis shd",
    enter=e_xxddz, attack=a_xxddz, leaverep=exlife_rep, saok=sa_xxddz, battlefx=bf_xxddz,
    spelllock=sl_xxddz,
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。W・ブレイカー。"
         "自分のクリーチャーすべてに「スピードアタッカー」と「スレイヤー」を与える。"
         "このクリーチャーが攻撃する時、このクリーチャーの「EXライフ」シールドを墓地に置いてもよい。"
         "そうしたら、次の自分のターンのはじめまで、相手は呪文を唱えられない",
    note="「攻撃する時にEXライフを墓地に置くか」は、置けるなら必ず置く（呪文を止める効き目のほうが大きいという"
         "機械的な決まり）。呪文の封じは一度かけたら XXDDZ が離れても次の自分のターンのはじめまで続く（本文どおり）",
    source=SRC["k49_xxddz"])


# ================================================================ ソーシャル・マニフェストII世
def px_social(s, i, k, n):
    """バズレンダ[無色(3)]：払えるだけ追加で払う（払った回数ぶんBR能力が増える）"""
    p = s.P[i]
    av = len(p.mana) - p.mused - n
    extra = max(0, av // 3)
    if extra:
        p.mused += 3 * extra
        s.ev(f"　バズレンダ：追加で[無色(3)]を{extra}回支払う")
    p.x["k49_social_br"] = extra


def e_social(s, i, u):
    """BR能力：1回＋バズレンダで追加で払った回数。
    BR-山札の上から1枚目をマナゾーンに置き、その後コスト7以下の呪文をマナからただで唱えてもよい"""
    p = s.P[i]
    n = 1
    if u.x.get("summoned"):
        n += max(0, int(p.x.get("k49_social_br") or 0))
    p.x["k49_social_br"] = 0
    for _ in range(n):
        if s.over:
            return
        s.ramp(i, 1)
        _cast_free(s, i, ("mana",), lambda c, cost: cost <= 7)


add("k49_social", "ソーシャル・マニフェストII世", 7, "WN", power=6000, brk=2,
    races=("trix", "cybercommand", "command", "teamwave"), pri=9, roles="acc draw fin",
    enter=e_social, payx=px_social,
    text="バズレンダ[無色(3)]（このクリーチャーのコストを支払う時、追加で[無色(3)]を好きな回数支払ってもよい。"
         "出た時、そのBR能力を1回と、追加で支払った回数ぶん使う）。W・ブレイカー。"
         "BR-自分の山札の上から1枚目をマナゾーンに置く。その後、コスト7以下の呪文を1枚、"
         "コストを支払わずに自分のマナゾーンから唱えてもよい",
    note="バズレンダの追加の支払いは「そのターン残っているマナで払えるだけ払う」（全デッキ共通の機械的な決まり）。"
         "マナから唱える呪文は、重要度のいちばん高いもの（ツインパクトの呪文側も含む）。"
         "召喚以外（踏み倒し）で出た時はBR能力を1回だけ使う",
    source=SRC["k49_social"])


# ================================================================ 深淵の逆転撃
def sp_gyakuten(s, i):
    """相手のクリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを-∞する"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　深淵の逆転撃：{t.c.name} のパワーを-∞（パワー0以下で破壊）")
    destroy(s, i, t)


def rc_gyakuten(s, di, au):
    """逆転撃[闇(3)]：クリーチャーが自分を攻撃する時、手札からコストを支払わずに唱える"""
    p = s.P[di]
    if "k49_gyakutengeki" not in p.hand or s.over:
        return False
    if not s.spell_ok(di, 4) or s.target(di) is None:
        return False
    if len(p.mana) < 3 or "D" not in E.civs(p):
        return False                      # 次のターンに[闇(3)]を払えない見込みなら使わない（負けてしまう）
    p.hand.remove("k49_gyakutengeki")
    p.x["k49_gt_owe"] = p.x.get("k49_gt_owe", 0) + 1
    s.trig[di] += 1
    s.ev("　逆転撃[闇(3)]：深淵の逆転撃")
    s.cast(di, "k49_gyakutengeki")
    return True


def tsp_gyakuten(s, i):
    """次の自分のターンのはじめに[闇(3)]を支払う。支払えなければ負け"""
    p = s.P[i]
    n = p.x.get("k49_gt_owe", 0)
    if not n:
        return
    p.x["k49_gt_owe"] = 0
    need = 3 * n
    if len(p.mana) - p.mused >= need and "D" in E.civs(p):
        p.mused += need
        s.ev(f"　逆転撃の後払い：[闇(3)]×{n} を支払った")
    else:
        s.ev("　逆転撃の後払いができない")
        s.win(1 - i, "逆転撃の支払い")


add("k49_gyakutengeki", "深淵の逆転撃", 4, "D", kind="S", pri=6, roles="rem trg dis",
    spell=sp_gyakuten, react=rc_gyakuten, turnstart=tsp_gyakuten,
    text="逆転撃[闇(3)]：クリーチャーが自分を攻撃する時、その攻撃中に「逆転撃」を使っていなければ、"
         "この呪文を自分の手札からコストを支払わずに唱えてもよい。そうしたら、"
         "次の自分のターンのはじめに[闇(3)]を支払う。支払えなければ、自分はゲームに負ける。"
         "相手のクリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを-∞する"
         "（パワー0以下のクリーチャーは破壊される）",
    note="「パワーを-∞」は、エンジンにパワーを下限なく下げる書き方がないので、"
         "結果が同じになる「破壊」で書いた（パワー0以下での破壊なので、破壊の置き換え＝EXライフ等は正しく働く）。"
         "逆転撃を使うのは「マナが3枚以上あって闇が出せる（次のターンに払える見込みがある）」時だけ"
         "（払えずに負けるのを避けるための機械的な決まり）",
    source=SRC["k49_gyakuten"])


# ================================================================ 鬼ヶ大王 ジャオウガ
def e_jaouga49(s, i, u):
    """出た時、自分のシールドをすべて手札に加えてもよい（そのS・トリガーは使えない）"""
    p = s.P[i]
    if not p.sh or len(p.sh) > 2:
        return                            # シールドを3つ以上は手放さない（全デッキ共通の決まり）
    n = len(p.sh)
    for j in range(n - 1, -1, -1):
        s.take_shield(i, j, "hand")
    s.ev(f"　鬼ヶ大王 ジャオウガ：自分のシールド{n}枚を手札に加えた（S・トリガーは使えない）")


add("k49_jaouga", "鬼ヶ大王 ジャオウガ", 5, "DF", power=7000, brk=2, sa=True,
    races=("demonio", "onifudaoukoku"), pri=7, roles="atk draw fin",
    enter=e_jaouga49,
    text="スピードアタッカー、W・ブレイカー。"
         "このクリーチャーが出た時、自分のシールドをすべて手札に加えてもよい"
         "（ただし、その「S・トリガー」は使えない）",
    note="シールドを手札に加えるのは「自分のシールドが2つ以下の時」だけ（失うものが小さい時に手札に換える、"
         "という全デッキ共通の決まり。既にあるカードの「シールドは2つまでは減らさない」と同じ考え方）",
    source=SRC["k49_jaouga"])


# ================================================================ 蒼き団長 ドギラゴン剣
def cx_dogiragoken(s, i, u):
    """革命チェンジ：火または自然のコスト5以上のドラゴン"""
    return (u.c.kind == "C" and "dragon" in u.c.races and bool(set("FN") & set(u.c.civ))
            and u.c.cost >= 5)


def sa_dogiragoken(s, i, u):
    """自分の多色クリーチャーすべてにスピードアタッカーを与える"""
    return u.c.kind == "C" and _multi(u.k) and s.has(i, "k49_dogiragoken")


def e_dogiragoken(s, i, u):
    """ファイナル革命：革命チェンジで出た時、コストの合計が6以下になるように、
    進化ではない多色クリーチャーを好きな数、自分の手札またはマナゾーンから出す"""
    if "src" in u.x:
        return                            # 召喚・踏み倒しで出た時は働かない（革命チェンジ限定）
    p = s.P[i]
    if p.final_turn == s.turn:
        return                            # そのターンに他のファイナル革命を使っている
    p.final_turn = s.turn
    s.ev("　ファイナル革命：手札とマナから多色クリーチャーを出す（コストの合計6以下）")
    budget = 6
    while budget > 0 and not s.over:
        best, bv, zn = None, None, None
        for zname, zone in (("hand", p.hand), ("mana", p.mana)):
            for k in sorted(set(zone)):
                c = BY_KEY[k]
                if not _plain_cre(c) or not _multi(k) or c.cost > budget:
                    continue
                v = (E.PRI[k], 1 if zname == "hand" else 0)      # 手札のほうを先に使う
                if (bv is None or v > bv) and s.fate(i, k, zname, False) == "ok":
                    best, bv, zn = k, v, zname
        if best is None:
            break
        if zn == "mana":
            s.take_mana(i, best)
        else:
            p.hand.remove(best)
        budget -= BY_KEY[best].cost
        s.ev(f"　　{BY_KEY[best].name} を{'手札' if zn == 'hand' else 'マナ'}から出す")
        s.enter(i, best, zn, False)


def _pr_change(civ, need, label):
    def f(deck, k):
        n = sum(v for kk, v in deck.items()
                if kk != k and BY_KEY[kk].kind == "C" and "dragon" in BY_KEY[kk].races
                and set(civ) & set(BY_KEY[kk].civ) and BY_KEY[kk].cost >= need)
        return None if n >= 3 else f"革命チェンジの元（{label}）が3体いない"
    return f


add("k49_dogiragoken", "蒼き団長 ドギラゴン剣", 8, "FN", power=13000, brk=3,
    races=("megacommanddragon", "command", "dragon", "revolution", "hamukatsudan"), pri=13,
    roles="fin atk acc",
    enter=e_dogiragoken, changex=cx_dogiragoken, saok=sa_dogiragoken,
    playrule=_pr_change("FN", 5, "火か自然のコスト5以上のドラゴン"),
    text="革命チェンジ：火または自然の、コスト5以上のドラゴン"
         "（自分のそのクリーチャーが攻撃する時、そのクリーチャーと手札にあるこのクリーチャーを入れ替えてもよい）。"
         "T・ブレイカー。自分の多色クリーチャーすべてに「スピードアタッカー」を与える。"
         "ファイナル革命：このクリーチャーが「革命チェンジ」によって出た時、"
         "そのターンに他の「ファイナル革命」を使っていなければ、コストの合計が6以下になるように、"
         "進化ではない多色クリーチャーを好きな数、自分の手札またはマナゾーンから出す",
    note="2026年10月時点で殿堂入り（デッキに1枚まで。プレミアム殿堂ではない）。"
         "ファイナル革命で出す組み合わせは「重要度のいちばん高いものから、手札を先に使う」"
         "（コストの合計を使い切る最良の組み合わせを探すのではなく、全デッキ共通の機械的な決まり）",
    source=SRC["k49_dogiragoken"])


# ================================================================ 切札勝太＆カツキング -熱血の物語-
def e_katsuking(s, i, u):
    """出た時、山札の上から5枚を見て1枚を表向きにして手札に加え、残りを山札の下に置く。
    表向きにしたカードが火または自然なら、クリーチャー1体を選び持ち主の手札に戻してもよい"""
    p = s.P[i]
    top = _top(s, i, 5)
    if not top:
        return
    fn = [k for k in top if set("FN") & set(E.MCIV[k])]
    k = max(fn, key=E.PRI.get) if fn else max(top, key=E.PRI.get)
    top.remove(k)
    p.hand.append(k)
    _bottom(s, i, top)
    s.ev(f"　カツキング：{BY_KEY[k].name} を表向きにして手札に加えた")
    if not (set("FN") & set(E.MCIV[k])):
        return
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　カツキング：{t.c.name} を持ち主の手札に戻す")
    move(s, i, t, "hand")


def tg_katsuking(s, di, k):
    """革命2：自分のシールドが2つ以下なら、シールドゾーンから手札に加えるこのクリーチャーにS・トリガーを与える"""
    return k == "k49_katsuking" and len(s.P[di].sh) <= 2


def pw_katsuking(s, i, u, atk):
    """革命0：自分のシールドが1つもなければパワー+10000"""
    return 10000 if (u.k == "k49_katsuking" and not s.P[i].sh) else 0


def brk_katsuking(s, i, u):
    """革命0：T・ブレイカー"""
    return 3 if not s.P[i].sh else None


def sa_katsuking(s, i, u):
    """革命0：スピードアタッカー"""
    return u.k == "k49_katsuking" and not s.P[i].sh


add("k49_katsuking", "切札勝太＆カツキング -熱血の物語-", 5, "WFN", power=5000, mach=True,
    races=("outragedragon", "dragon", "humanoid"), pri=8, roles="draw rem trg atk",
    enter=e_katsuking, trigok=tg_katsuking, powerx=pw_katsuking, brkx=brk_katsuking, saok=sa_katsuking,
    text="マッハファイター（相手のタップしているクリーチャーを、出たターンでも攻撃できる）。"
         "このクリーチャーが出た時、自分の山札の上から5枚を見る。その中から1枚を表向きにして手札に加え、"
         "残りを好きな順序で山札の下に置く。こうして表向きにしたカードが火または自然なら、"
         "クリーチャー1体を選び、持ち主の手札に戻してもよい。"
         "革命2：自分のシールドが2つ以下なら、自分のシールドゾーンから手札に加えるこのクリーチャーに"
         "「S・トリガー」を与える。"
         "革命0：自分のシールドが1つもなければ、このクリーチャーのパワーを+10000し、"
         "「スピードアタッカー」と「T・ブレイカー」を与える",
    note="表向きにする1枚は「火か自然のカードがあればその中でいちばん重要度の高いもの、"
         "無ければ全体でいちばん重要度の高いもの」（除去が付く条件を満たすほうを選ぶ機械的な決まり）。"
         "手札に戻すクリーチャーは相手の重要度のいちばん高いもの",
    source=SRC["k49_katsuking"])


# ================================================================ 蒼き守護神 ドギラゴン閃
def cx_dogiragosen(s, i, u):
    """革命チェンジ：光または火のコスト5以上のドラゴン"""
    return (u.c.kind == "C" and "dragon" in u.c.races and bool(set("LF") & set(u.c.civ))
            and u.c.cost >= 5)


def e_dogiragosen(s, i, u):
    """ファイナル革命：革命チェンジで出た時、山札の上から4枚を表向きにし、その中から
    コストの合計が6以下になるように進化ではない多色クリーチャーを好きな数出す。残りは山札の下へ"""
    if "src" in u.x:
        return
    p = s.P[i]
    if p.final_turn == s.turn:
        return
    p.final_turn = s.turn
    top = _top(s, i, 4)
    if not top:
        return
    s.ev("　ファイナル革命：山札の上から4枚を表向きにする")
    rest = _put_multi(s, i, top, 6, "deck")
    _bottom(s, i, rest)


def t_dogiragosen(s, i, u):
    """自分のターンの終わりに、自分の多色クリーチャーをすべてアンタップする"""
    for z in s.P[i].board:
        if z.c.kind == "C" and _multi(z.k) and z.tap:
            z.tap = False


add("k49_dogiragosen", "蒼き守護神 ドギラゴン閃", 8, "LF", power=13000, brk=3, blocker=True,
    races=("megacommanddragon", "command", "dragon", "revolution", "hamukatsudan"), pri=12,
    roles="fin blk atk acc",
    enter=e_dogiragosen, tend=t_dogiragosen, changex=cx_dogiragosen,
    playrule=_pr_change("LF", 5, "光か火のコスト5以上のドラゴン"),
    text="革命チェンジ：光または火の、コスト5以上のドラゴン。ブロッカー、T・ブレイカー。"
         "自分のターンの終わりに、自分の多色クリーチャーをすべてアンタップする。"
         "ファイナル革命：このクリーチャーが「革命チェンジ」によって出た時、"
         "そのターンに他の「ファイナル革命」を使っていなければ、自分の山札の上から4枚を表向きにする。"
         "その中から、コストの合計が6以下になるように進化ではない多色クリーチャーを好きな数出し、"
         "残りを好きな順序で山札の下に置く",
    note="出す組み合わせは重要度のいちばん高いものから（コストの合計を使い切る最良の組み合わせは探さない）",
    source=SRC["k49_dogiragosen"])


# ================================================================ サイバー・ブレイン
def sp_cyberbrain(s, i):
    """カードを3枚まで引く（山札を切らさない枚数だけ引く）"""
    p = s.P[i]
    n = 3 if len(p.deck) > 3 else max(0, len(p.deck) - 1)
    if n:
        s.draw(i, n)


add("k49_cyberbrain", "サイバー・ブレイン", 4, "W", kind="S", trig=True, pri=5, roles="draw trg",
    spell=sp_cyberbrain,
    text="S・トリガー。カードを3枚まで引く（山札が切れて負けないように、引ける枚数だけ引く）",
    note="2004年3月に最初の殿堂入り5種の1枚、2011年1月15日にプレミアム殿堂、2021年7月1日に殿堂入りへ降格、"
         "2022年7月1日に殿堂解除。いまは4枚使える",
    source=SRC["k49_cyberbrain"])


# ================================================================ デビル・ドレーン
def sp_devildrain(s, i):
    """自分のシールドを好きな数、手札に加える（そのS・トリガーは使えない）"""
    p = s.P[i]
    n = len(p.sh) - 2
    if n <= 0:
        return
    got = 0
    for _ in range(n):
        if not p.sh:
            break
        j = max(range(len(p.sh)), key=lambda x: E.PRI[p.sh[x][0]])
        s.take_shield(i, j, "hand")
        got += 1
    s.ev(f"　デビル・ドレーン：自分のシールド{got}枚を手札に加えた（S・トリガーは使えない）")


add("k49_devildrain", "デビル・ドレーン", 3, "D", kind="S", pri=4, roles="draw",
    spell=sp_devildrain,
    text="自分のシールドを好きな数、自分の手札に加える（ただし、その「S・トリガー」は使えない）",
    note="2014年5月24日から殿堂入り（デッキに1枚まで）。"
         "加える枚数は「シールドを2つ残す」（重要度のいちばん高いシールドから加える）。"
         "シールドが2つ以下の時は1枚も加えない（全デッキ共通の決まり）",
    source=SRC["k49_devildrain"])


# ================================================================ 黒神龍ブライゼナーガ
def e_blizenaga(s, i, u):
    """出た時、このクリーチャーは自分のシールドをすべてブレイクする（強制。自分のS・トリガーは働く）"""
    n = len(s.P[i].sh)
    if not n:
        return
    s.ev(f"　黒神龍ブライゼナーガ：自分のシールド{n}枚をすべてブレイクする")
    s.break_sh(1 - i, n)


add("k49_blizenaga", "黒神龍ブライゼナーガ", 6, "D", power=9000, brk=2,
    races=("dragonzombie",), pri=7, roles="draw trg atk",
    enter=e_blizenaga,
    text="W・ブレイカー。このクリーチャーが出た時、このクリーチャーは自分のシールドをすべてブレイクする"
         "（強制。自分のシールドが割れるので、自分のS・トリガーが働く）",
    note="2019年3月1日から殿堂入り（デッキに1枚まで）",
    source=SRC["k49_blizenaga"])


# ================================================================ 魔誕の封殺ディアス Z
def w_dias(s, i, u):
    """D・D・D[闇/火/自然(4)]：自分のクリーチャーが攻撃する時、4マナを支払って手札から出す"""
    if not _ddd_ok(s, i, "k49_dias", 4, "DFN"):
        return
    p = s.P[i]
    on = _ddd_src(s, i, "DFN")
    p.hand.remove("k49_dias")
    p.mused += 4
    s.ev("　D・D・D[闇/火/自然(4)]：魔誕の封殺ディアス Z")
    s.enter(i, "k49_dias", "hand", True, on=on)


def ae_dias(s, i, u):
    """このクリーチャーの攻撃の終わりに、コスト5以下のクリーチャー1体を自分の墓地またはマナゾーンから出す。
    このターン、そのクリーチャーにスピードアタッカーを与える"""
    if u.k != "k49_dias":
        return
    p = s.P[i]
    best, bv, zn = None, None, None
    for zname, zone in (("grave", p.grave), ("mana", p.mana)):
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if not _plain_cre(c) or c.cost > 5:
                continue
            v = (E.PRI[k], 1 if zname == "grave" else 0)      # マナより墓地から先に使う
            if (bv is None or v > bv) and s.fate(i, k, zname, False) == "ok":
                best, bv, zn = k, v, zname
    if best is None:
        return
    if zn == "mana":
        s.take_mana(i, best)
    else:
        p.grave.remove(best)
    s.ev(f"　ディアス Z：{'墓地' if zn == 'grave' else 'マナ'}から {BY_KEY[best].name} を出す（SA）")
    s.enter(i, best, zn, False, sa=True)


add("k49_dias", "魔誕の封殺ディアス Z", 6, "DFN", power=10000, brk=2, mach=True,
    evo="DFN", neo=True, gneo=True, races=("demoncommand", "command"), pri=10,
    roles="atk rem acc fin",
    atkwatch=w_dias, atkend=ae_dias,
    evox=lambda s, i, u: bool(set("DFN") & set(u.c.civ)),
    playrule=lambda deck, k: None,
    text="D・D・D[闇/火/自然(4)]：自分のクリーチャーが攻撃する時、闇・火・自然のマナ4つを支払って、"
         "このカードを自分の手札から出してもよい。"
         "G-NEO進化：闇、火、または自然のクリーチャー1体の上に置いてもよい"
         "（進化元なしで召喚してもよい。下にカードがある間は、離れるかわりに下のカードがすべて離れる）。"
         "マッハファイター、W・ブレイカー。"
         "このクリーチャーの攻撃の終わりに、コスト5以下のクリーチャー1体を自分の墓地またはマナゾーンから出す。"
         "このターン、そのクリーチャーに「スピードアタッカー」を与える",
    note="D・D・Dで出す時、進化元にできるのは「いま攻撃しているクリーチャー以外」。"
         "エンジンは攻撃しているクリーチャーを別のカードに差し替える道（侵略）にコストの支払いを持たないため、"
         "既にある D・D・D のカード（env12）と同じ書き方にした。"
         "G-NEO進化は進化元なしで召喚できるので、playrule は進化元の枚数を問わない",
    status="partial", source=SRC["k49_dias"])


# ================================================================ 卍 新世壊 卍
def _is_madogu(k):
    """魔導具呪文か。種族「魔導具」の印は "madogu"（以前この担当は "madougu" と書き間違えていて、
    ほかの担当の堕呪（env50 など）がまったく数えられていなかった）"""
    return "madogu" in BY_KEY[k].races


def _lockfree(k):
    """呪文ロックを無視して唱えられる呪文（魔導具呪文またはドルスザク呪文）か"""
    r = BY_KEY[k].races
    return "madogu" in r or "dorusuzaku" in r


def _sin_flush(s):
    """唱え終わった魔導具呪文を、墓地から新世壊の下へ移す（唱えている最中はまだ墓地にないため後でまとめる）"""
    for j in (0, 1):
        p = s.P[j]
        pend = p.x.get("k49_sinpend")
        if not pend:
            continue
        p.x["k49_sinpend"] = ()
        u = next((z for z in p.board if z.k == "k49_shinsekai"), None)
        if u is None:
            continue
        for k in pend:
            if k in p.grave:
                p.grave.remove(k)
                u.under = u.under + [k]


def sw_shinsekai(s, i, k):
    """自分の魔導具呪文を唱えた後、墓地のかわりにこのフィールドの下に置いて、1枚引いてもよい"""
    _sin_flush(s)
    if not _is_madogu(k) or not s.has(i, "k49_shinsekai"):
        return
    p = s.P[i]
    p.x["k49_sinpend"] = tuple(p.x.get("k49_sinpend") or ()) + (k,)
    s.ev(f"　卍 新世壊 卍：{BY_KEY[k].name} を下に置いて1枚引く")
    s.draw(i, 1)


def ts_shinsekai(s, i):
    _sin_flush(s)


def fa_shinsekai(s, i, av, cv):
    """自分は、呪文を唱えられなくする効果を無視して、魔導具呪文またはドルスザク呪文を唱えてもよい。

    追加の手として出す（エンジンの呪文ロックは「止める」側しかないので、
    止められている呪文を唱える手をこちらから足して飛び越える）。
    ついでに、唱え終わって墓地に行った魔導具呪文をフィールドの下へ移す（下の説明を参照）。"""
    if s.P[0].x.get("k49_sinpend") or s.P[1].x.get("k49_sinpend"):
        _sin_flush(s)
    if not s.has(i, "k49_shinsekai"):
        return []
    p = s.P[i]
    out = []
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "S" or not _lockfree(k):
            continue
        n = s.spcost(i, k)
        if n > av or (n and not cv.issuperset(c.civ)):
            continue
        if s.spell_ok(i, c.cost, k):
            continue                         # 止められていないなら、普通の手でそのまま唱えられる
        out.append(("x:k49_sinfree", k))
    return out


def ap_shinsekai(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.hand or not s.has(i, "k49_shinsekai"):
        return
    n = s.spcost(i, k)
    if len(p.mana) - p.mused < n:
        return
    p.mused += n
    p.hand.remove(k)
    s.ev(f"卍 新世壊 卍：呪文ロックを無視して {BY_KEY[k].name} を唱える")
    s.cast(i, k)


def t_shinsekai(s, i, u):
    """無月の門99：自分のターンの終わりに、下に4枚以上あれば、ゲーム中に1度、
    水のコスト99以下の呪文1枚を手札か墓地からコストを支払わずに唱える"""
    _sin_flush(s)
    p = s.P[i]
    if len(u.under) < 4 or p.x.get("k49_mugetsu_used"):
        return
    if not _cast_free(s, i, ("hand", "grave"), lambda c, cost: "W" in c.civ and cost <= 99):
        return
    p.x["k49_mugetsu_used"] = True
    s.ev("　無月の門99：卍 新世壊 卍（ゲーム中1度）")


add("k49_shinsekai", "卍 新世壊 卍", 2, "W", kind="T", races=("mugetsufield",), pri=4,
    roles="draw acc fin",
    spellwatch=sw_shinsekai, turnstart=ts_shinsekai, tend=t_shinsekai,
    freeacts=fa_shinsekai, actapply={"x:k49_sinfree": ap_shinsekai},
    text="自分の魔導具呪文を唱えた後、墓地のかわりにこのフィールドの下に置いて、カードを1枚引いてもよい。"
         "自分は、呪文を唱えられなくする効果を無視して、魔導具呪文またはドルスザク呪文を唱えてもよい。"
         "無月の門99：自分のターンの終わりに、このフィールドの下に4枚以上カードがあれば、ゲーム中に1度、"
         "水のコスト99以下の呪文を1枚、自分の手札または墓地からコストを支払わずに唱えてもよい",
    note="このカードの種類は本当は「無月フィールド」だが、このシミュレーターにフィールドの仕組みがないので、"
         "バトルゾーンに残る非クリーチャーのカード＝タマシード（kind=\"T\"）として置いた"
         "（置くコストと、下にカードを置ける点、エレメントとして選べる点は同じになる）。"
         "「呪文を唱えられなくする効果を無視して魔導具呪文またはドルスザク呪文を唱えてもよい」は、"
         "止められている呪文を唱える手を freeacts で足して表した（自分の手番の手としてだけ足すので、"
         "S・トリガーで唱える時は呪文ロックを飛び越えられない）。"
         "また、唱えた魔導具呪文を下に置くのは「呪文が墓地に置かれた後」になるため、"
         "唱えた直後ではなく、次に手を選ぶ時（または次の呪文・ターンのはじめ・自分のターンの終わり）に"
         "まとめて動かしている。1枚引くのは本文どおり唱えた時に行う",
    status="partial", source=SRC["k49_shinsekai"])


# ================================================================ 堕呪 ゾメンザン
add("k49_zomenzan", "堕呪 ゾメンザン", 1, "W", kind="S", races=("madogu",), pri=1, roles="draw",
    text="能力を持たない呪文（魔導具）。《卍 新世壊 卍》などの「自分の魔導具呪文を唱えた時」の条件を満たすための1枚",
    note="カード単体では何も起こらない（公式にも能力の記載がないバニラ呪文）。"
         "roles に draw を入れているのは、新世壊があれば唱えるたびに1枚引けるため",
    source=SRC["k49_zomenzan"])
