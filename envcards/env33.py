"""担当33：DM26-RP3（逆札篇 第3弾 勝敵！逆転おこせ鬼の∞ディスペクター!!）の未実装カード15枚

  出典：dmwiki.net の各カードページ。通常ページ `https://dmwiki.net/《カード名》` と
        生の wiki ソース `?plugin=template&refer=《カード名》` を、カードごとに**別の質問で2回以上**読み、
        コスト・文明・種類・種族・パワー・ブレイク数・能力本文がどちらでも一致することを確かめた。
        片方の読みで数値が「...」で切れていた4枚（ザ・ゲオニー／ザ・マグニー／ザ・デンニー／アアルカイト）は
        3回目の質問（パワーだけ／その能力行だけ）で確かめ直した。15枚いずれもハイパーモード欄は無い。

  内訳（番号は DM26-RP3 の通し番号）
    ・32/77 銃宮逆夢 ザ・ネオニー／ジョリー・ザ・ブレイン（水5／水4・ツインパクト）
    ・33/77 スイドー・ド・デショー（水4・S・トリガー）
    ・34/77 The 淡口ラー漢 極（水3・ジョーカーズのコスト-1）
    ・35/77 アアルカイトの電影（水3・タマシード・ササゲール3）
    ・36/77 銃毒逆夢 ザ・ゲオニー／ジョリー・ザ・ハンド（闇5／闇1・ツインパクト）
    ・37/77 ワーク騎士（闇4・Jクライム6）
    ・38/77 ×マドギワ親父（闇3・墓地から召喚・Jクライム4）
    ・39/77 闇影 ヘモグロ-2（闇3・ササゲール2・自己リアニメイト）
    ・40/77 ア・ストラ・ゼーレの電影（闇3・タマシード・ササゲール3・墓地からディスペクター召喚）
    ・41/77 ケツカッちん（火6・J・O・E 2・スーパーガードマン）
    ・42/77 銃車逆夢 ザ・マグニー／ジョリー・ザ・スクラッパー（火5／火2・ツインパクト）
    ・43/77 爆衆 ランブル-2（火3・ササゲール2）
    ・45/77 メモッタルド・デカスギオ／メモメモ・ジョーカーズ（自然6／自然1・ツインパクト）
    ・46/77 銃蝸逆夢 ザ・デンニー／ジョリー・ザ・トラップ（自然5／自然2・ツインパクト）
    ・47/77 Q字工事（自然3・Jチェンジ6）

  この弾の新しい（このシミュレーターに無かった）仕組みと、その書き方
    ・**スマッシュ・バースト**（銃◯逆夢の4枚）：攻撃する時、このカードの呪文側を、
      カードをバトルゾーンに置いたままコストを支払わずに唱えてもよい。
      `attack=` から `_cast_inplace()`（呪文側だけを実行し、墓地には送らない）を呼んでいる。
    ・**ササゲール**（アアルカイト3／ア・ストラ・ゼーレ3／ヘモグロ2／ランブル2）：
      「自分のディスペクター・クリーチャーの召喚コストを N 少なくしてもよい。そうしたらこのエレメントを破壊する」。
      エンジンの `PAYX` はカードのキーごとなので、**他の担当のディスペクターには付けられない**。
      そこで `costaura=`（下げる）と `enterwatch=`（下げたぶんの捧げたカードを破壊する）の2つで書いた。
      `costaura` は「そのままでは払えない時だけ」必要な枚数だけ下げ、下げた相手と捧げるカードの uid を
      `s.P[i].x["k33sas"]`（tuple）に書き残す。`ccost` は召喚の直前にもう一度呼ばれるので、
      この記録は必ずその召喚のものになる（env0 のハイパーエナジーと同じ「必要な分だけ」の考え方）。
      この2つは4枚で共通の全体フックなので、**モジュールの中で1度だけ**登録している
      （カードごとに add() へ渡すと COSTAURA に4つ積まれ、同じ軽減が4回かかる）。
    ・**Jクライム N**（ワーク騎士6／×マドギワ親父4）：攻撃する時、これと自分の**墓地**の
      コストN以下のジョーカーズ・クリーチャー1体を入れ替えてもよい（`atkswap=`）。
    ・**Jチェンジ N**（メモッタルド8／Q字工事6）：攻撃する時、これと自分の**マナゾーン**の
      コストN以下のジョーカーズ・クリーチャー1体を入れ替えてもよい（`atkswap=`）。
      入れ替えは移動なので、このカードは「破壊」ではなくそのままマナゾーン（Jクライムは墓地）へ置いている。
    ・**Jトルネード**（スイドー・ド・デショー）：自分の他のジョーカーズ・クリーチャー1体を手札に戻す。
    ・**J・O・E 2**（ケツカッちん）：env31 と同じく `freeacts=`／`actapply=` で
      「コスト-2で召喚する手」を別に足した（普通のコストで召喚する手も残る）。
    ・**スーパーガードマン**（ケツカッちん／Q字工事）：`battleswap=`（BATTLESWAP）で書いた。
      ブロックで起きたバトルも効果で起きたバトルも引き受ける。

  調べ直して意外だった点
    ・「銃◯逆夢 ザ・◯◯／ジョリー・ザ・◯◯」は5枚サイクルだが、**共通なのは
      クリーチャー側の「EXライフ＋スマッシュ・バースト」とコスト5だけ**。
      パワーは 4000／4000／5000／5000（env32 のザ・ウィニーは5500）とそろっておらず、
      呪文側のコストも 4／1／2／2 でばらばら。W・ブレイカーは**どれも持たない**（brk=1）。
    ・呪文側の名前が《ジョリー・ザ・ジョニー》系なので S・トリガーを疑ったが、
      **5枚とも呪文側に S・トリガーは無い**（env32 担当のザ・ウィニー／ジョリー・ザ・スパークも無し）。
      dmwiki の解説にも「ハンドの名称カテゴリは本来破壊されない能力を持つが、
      このサイクルはブレイン以外それを持たない」とあり、名前だけの引用である。
    ・「◯◯の電影」は2枚とも**タマシード：トリックス/ディスタス**で、ツインパクトではない。
      env34/env35 が担当する「◯◯の輝影／◯◯の海影／◯◯の闇影／◯◯の爆影／◯◯の大影」は
      セット一覧では名前に「／」が入っているツインパクトなので、**同じ仕組みではない**。
      「電影」2枚に共通なのは **ササゲール3** だけで、残りの能力はまるで違う。
    ・《闇影 ヘモグロ-2》の「闇影」は、上の「◯◯の闇影」（ツインパクト）とは別物で、
      《爆衆 ランブル-2》と同じ「〈種族名〉 ◯◯-数字」のディスタス・サイクル（ササゲール持ち）。
      手本にした《爆衆 マキシ-2》（env4）とは、ササゲールの書き方だけが同じ。
    ・《×マドギワ親父》は「×」まで含めて正式名。能力でも何でもなく名前の一部。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, worst_hand
from envcards.env0 import discard_choice, exlife_enter, exlife_rep, lock_until_my_turn, own_loss

W = "https://dmwiki.net/"
SRC = {
    "k33_neony": W + "《銃宮逆夢 ザ・ネオニー／ジョリー・ザ・ブレイン》",
    "k33_suido": W + "《スイドー・ド・デショー》",
    "k33_rahan": W + "《The 淡口ラー漢 極》",
    "k33_aarkite": W + "《アアルカイトの電影》",
    "k33_geony": W + "《銃毒逆夢 ザ・ゲオニー／ジョリー・ザ・ハンド》",
    "k33_work": W + "《ワーク騎士》",
    "k33_madogiwa": W + "《×マドギワ親父》",
    "k33_hemoglo": W + "《闇影 ヘモグロ-2》",
    "k33_astrazele": W + "《ア・ストラ・ゼーレの電影》",
    "k33_ketsu": W + "《ケツカッちん》",
    "k33_magny": W + "《銃車逆夢 ザ・マグニー／ジョリー・ザ・スクラッパー》",
    "k33_rumble": W + "《爆衆 ランブル-2》",
    "k33_memotta": W + "《メモッタルド・デカスギオ／メモメモ・ジョーカーズ》",
    "k33_denny": W + "《銃蝸逆夢 ザ・デンニー／ジョリー・ザ・トラップ》",
    "k33_qji": W + "《Q字工事》",
}

SGUARD_TEXT = ("スーパーガードマン（自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーをタップして"
               "バトルさせてもよい）。")


def super_guardman(key, cond=None):
    """スーパーガードマン：自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーを
    タップしてバトルさせてもよい（BATTLESWAP。ブロックで起きたバトルも効果で起きたバトルも引き受ける。
    攻撃先を変えるわけではないので、攻撃されたクリーチャー自身はシールドをブレイクできる）。

    使うかどうかは共通の決まりで機械的に決める：バトルに勝てるか、守る相手のほうが大事な時だけ引き受ける。
    （どのカードがガードマン系を持つかは engine3.GUARDMEN で引ける）"""
    E.GUARDMEN.add(key)

    def f(s, di, du, ai, au):
        if du is None:
            return None
        ap = s.power(ai, au, True)
        for z in s.P[di].board:
            if z.k != key or z.c.kind != "C" or z.tap or z is du:
                continue
            if cond is not None and not cond(s, di, z):
                continue
            if s.power(di, z) > ap or s.val(du) > s.val(z):
                s.tap_cre(di, z)
                return z
        return None
    return f


# ================================================================ 共通の道具
def _plain_cre(k):
    """進化でない普通のクリーチャー（墓地・マナから出せるもの）"""
    c = BY_KEY[k]
    return c.kind == "C" and not (c.evo and not c.neo)


def _jok_cre(k):
    return _plain_cre(k) and "jokers" in BY_KEY[k].races


def _cast_inplace(s, i, k, cost, fn):
    """ツインパクトの呪文側を、カードをバトルゾーンに置いたままコストを支払わずに唱える（墓地には行かない）"""
    if not s.spell_ok(i, cost):
        return
    s.P[i].spl += 1
    s.first_play(i, cost)
    prev = s.spc
    s.spc = cost
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, k)
    if not s.over:
        fn(s, i)
    s.spc = prev


def smash_burst(key, cost, fn):
    """スマッシュ・バースト：攻撃する時、このカードの呪文側を場に置いたままただで唱えてもよい"""
    def f(s, i, u):
        if u.k != key:
            return
        s.ev(f"　スマッシュ・バースト：{BY_KEY[key].name} の呪文側をただで唱える")
        _cast_inplace(s, i, key, cost, fn)
    return f


def _targets(s, i, n, pred=None, kinds="C"):
    """相手のカードを最大n個選ぶ（重要度の高いものから。選ばれない効果はエンジンが見る）"""
    out = []
    for _ in range(n):
        seen = tuple(z.uid for z in out)
        t = s.target(i, lambda x: x.uid not in seen and (pred is None or pred(x)), kinds)
        if t is None:
            break
        out.append(t)
    return out


def jclimb(key, lim):
    """Jクライム：攻撃する時、これと自分の墓地のコストlim以下のジョーカーズ・クリーチャー1体を入れ替えてもよい"""
    def f(s, i, u):
        if u.k != key:
            return None
        return _swap(s, i, u, "grave", lim)
    return f


def jchange(key, lim):
    """Jチェンジ：攻撃する時、これとマナゾーンのコストlim以下のジョーカーズ・クリーチャー1体を入れ替えてもよい"""
    def f(s, i, u):
        if u.k != key:
            return None
        return _swap(s, i, u, "mana", lim)
    return f


def _swap(s, i, u, zone, lim):
    """攻撃しているクリーチャー u と、zone（墓地かマナ）のジョーカーズ・クリーチャーを入れ替える"""
    p = s.P[i]
    if s.manaexec(i):
        return None
    src = p.grave if zone == "grave" else p.mana
    best, bv = None, E.PRI[u.k]
    for k in sorted(set(src)):
        c = BY_KEY[k]
        if not _jok_cre(k) or c.cost > lim or E.PRI[k] <= bv:
            continue
        if s.fate(i, k, zone, False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return None
    j = p.board.index(u)
    if zone == "grave":
        src.remove(best)
    else:
        s.take_mana(i, best)
    if not s.leave(i, u, zone):          # 入れ替えは移動（破壊ではない）
        if zone == "grave":
            src.append(best)
        else:
            s.add_mana(i, best)
        return None
    nu = E.U(best)
    nu.tap = True
    nu.sick = False
    p.board.insert(min(j, len(p.board)), nu)
    p.ent += 1
    s.ev(f"　{'Jクライム' if zone == 'grave' else 'Jチェンジ'}{lim}："
         f"{u.c.name} と{'墓地' if zone == 'grave' else 'マナ'}の {nu.c.name} を入れ替える")
    fn = E.ENTER.get(best)
    if fn is not None and not s.over:
        fn(s, i, nu)
    for g in E.ENTERWATCH:
        if not s.over:
            g(s, i, nu)
    return nu if nu in p.board else None


# ================================================================ ササゲール（4枚で共通）
SAS = {"k33_aarkite": 3, "k33_astrazele": 3, "k33_hemoglo": 2, "k33_rumble": 2}


def ca_sas(s, i, k, cur):
    """ササゲール：自分のディスペクター・クリーチャーの召喚コストを少なくする（0以下にはならない）。

    「〜してもよい」なので、そのままでは払えない時だけ、必要な枚数だけ捧げる。
    捧げる相手と捧げるカードを s.P[i].x["k33sas"] に書き残し、enterwatch（w_sas）が破壊する。"""
    p = s.P[i]
    srcs = [z for z in p.board if z.k in SAS]
    if not srcs:
        return cur                      # この効果を出しているカードが無い対戦では何もしない
    c = BY_KEY[k]
    av = len(p.mana) - p.mused
    if c.kind != "C" or "dispector" not in c.races or cur <= 1 or cur <= av:
        p.x.pop("k33sas", None)
        return cur
    srcs.sort(key=lambda z: (-SAS[z.k], own_loss(s, i, z)))
    used, n = [], cur
    for z in srcs:
        if n <= av or n <= 1:
            break
        n = max(1, n - SAS[z.k])
        used.append(z.uid)
    if used:
        p.x["k33sas"] = (k, s.turn, tuple(used))
    else:
        p.x.pop("k33sas", None)
    return n


def w_sas(s, i, u):
    """ササゲールでコストを下げて召喚されたら、捧げたカードを破壊する"""
    p = s.P[i]
    rec = p.x.get("k33sas")
    if not rec:
        return                          # 記録は ca_sas だけが作る（この担当のカードが無い対戦では空）
    if u.c.kind != "C" or u.k != rec[0] or rec[1] != s.turn or not u.x.get("summoned"):
        return
    p.x.pop("k33sas", None)
    for uid in rec[2]:
        for z in p.board[:]:
            if z.uid == uid and z.k in SAS:
                s.ev(f"　ササゲール{SAS[z.k]}：{z.c.name} を破壊して {u.c.name} のコストを下げた")
                s.leave(i, z, "grave", destroy=True)
                break


# ササゲールは4枚が同じ仕組みなので、全体にかかる差し込み口はモジュールで**1度だけ**登録する
# （カードごとに add() へ渡すと COSTAURA に4つ積まれ、同じ軽減が4回かかってしまう）
if ca_sas not in E.COSTAURA:
    E.COSTAURA.append(ca_sas)
if w_sas not in E.ENTERWATCH:
    E.ENTERWATCH.append(w_sas)


SAS_TEXT = "（自分のディスペクター・クリーチャーの召喚コストを{0}少なくしてもよい。そうしたら、このエレメントを破壊する。" \
           "ただしコストは0以下にならない。そのままでは払えない時だけ、必要な数だけ捧げる）"


# ================================================================ 32/77 銃宮逆夢 ザ・ネオニー／ジョリー・ザ・ブレイン
def sp_neony(s, i):
    """ジョリー・ザ・ブレイン：カードを2枚引く。相手のクリーチャー1体を選び、
    次の自分のターンのはじめまで攻撃もブロックもできなくする"""
    s.draw(i, 2)
    t = s.target(i)
    if t is None:
        return
    lock_until_my_turn(s, i, t)
    s.ev(f"　ジョリー・ザ・ブレイン：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k33_neony", "銃宮逆夢 ザ・ネオニー／ジョリー・ザ・ブレイン", 5, "W", power=4000,
    races=("dispector", "mutopia", "jokers"), twin=(4, "W", False), pri=8, roles="draw dis shd",
    enter=exlife_enter, leaverep=exlife_rep, attack=smash_burst("k33_neony", 4, sp_neony), spell=sp_neony,
    text="クリーチャー側：EXライフ（出た時、自分の山札の上から1枚を自分の下にシールドとして置く。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。"
         "スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱えてもよい）。"
         "呪文側《ジョリー・ザ・ブレイン》（水・コスト4・S・トリガーは無い）：カードを2枚引く。"
         "相手のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、それは攻撃もブロックもできない",
    source=SRC["k33_neony"])


# ================================================================ 33/77 スイドー・ド・デショー
def e_suido(s, i, u):
    """出た時、相手のクリーチャーを2体まで選び、次の自分のターンのはじめまで攻撃もブロックもできなくする"""
    for t in _targets(s, i, 2):
        lock_until_my_turn(s, i, t)
        s.ev(f"　スイドー・ド・デショー：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


def a_suido(s, i, u):
    """攻撃する時、Jトルネード（自分の他のジョーカーズ・クリーチャー1体を手札に戻す）してもよい。
    そうしたら、カードを3枚引き、自分の手札を1枚捨てる"""
    p = s.P[i]
    cands = [z for z in p.board if z.c.kind == "C" and z is not u and "jokers" in z.c.races]
    if not cands:
        return
    z = min(cands, key=lambda x: own_loss(s, i, x))
    if not s.leave(i, z, "hand"):
        return
    s.ev(f"　Jトルネード：{z.c.name} を手札に戻し、3枚引いて1枚捨てる")
    s.draw(i, 3)
    k = worst_hand(s, i)
    if k is not None:
        s.discard(i, k)


add("k33_suido", "スイドー・ド・デショー", 4, "W", power=3000, trig=True, races=("jokers",),
    pri=7, roles="trg dis draw",
    enter=e_suido, attack=a_suido,
    text="S・トリガー。出た時、相手のクリーチャーを2体まで選ぶ。次の自分のターンのはじめまで、"
         "それらは攻撃もブロックもできない。"
         "このクリーチャーが攻撃する時、Jトルネードしてもよい（自分の他のジョーカーズ・クリーチャー1体を手札に戻す）。"
         "そうしたら、カードを3枚引き、自分の手札を1枚捨てる",
    source=SRC["k33_suido"])


# ================================================================ 34/77 The 淡口ラー漢 極
def ca_rahan(s, i, k, cur):
    """自分のジョーカーズ・クリーチャーの召喚コストを1少なくする（0以下にはならない）"""
    n = sum(1 for z in s.P[i].board if z.k == "k33_rahan")
    if not n or cur <= 1:
        return cur
    c = BY_KEY[k]
    if c.kind != "C" or "jokers" not in c.races:
        return cur
    return max(1, cur - n)


add("k33_rahan", "The 淡口ラー漢 極", 3, "W", power=3000, gs=True, races=("jokers",),
    pri=5, roles="acc draw trg",
    enter=lambda s, i, u: s.draw(i), costaura=ca_rahan,
    text="G・ストライク（相手のクリーチャーを1体選び、このターン攻撃できなくする）。出た時、カードを1枚引く。"
         "自分のジョーカーズ・クリーチャーの召喚コストを1少なくする。ただし、コストは0以下にならない",
    source=SRC["k33_rahan"])


# ================================================================ 35/77 アアルカイトの電影
def e_aarkite(s, i, u):
    """出た時、山札の上から4枚を見て1枚を手札に加え、残りを山札の下に置く"""
    s.dig(i, 4, lambda k: True)


def d_aarkite(s, i, u):
    """破壊された時、次の自分のターンのはじめまで、自分のクリーチャー1体は呪文によって相手に選ばれない"""
    cs = [z for z in s.P[i].board if z.c.kind == "C"]
    if not cs:
        return
    z = max(cs, key=s.val)
    z.x["k33_spsafe"] = s.turn + (1 if s.tp == i else 0)
    s.ev(f"　アアルカイトの電影：{z.c.name} は次の自分のターンのはじめまで呪文で相手に選ばれない")


def tl_aarkite(s, by, u):
    """呪文によって相手に選ばれない（s.spc＝いま唱えている呪文のコスト）"""
    return s.spc is not None and u.x.get("k33_spsafe", -1) >= s.turn


add("k33_aarkite", "アアルカイトの電影", 3, "W", kind="T", races=("trix", "distas"),
    pri=5, roles="draw acc dis",
    enter=e_aarkite, destroyed=d_aarkite, tgtlock=tl_aarkite,
    text="出た時、自分の山札の上から4枚を見る。その中から1枚を手札に加え、残りを好きな順序で山札の下に置く。"
         "ササゲール3" + SAS_TEXT.format(3) + "。"
         "このタマシードが破壊された時、次の自分のターンのはじめまで、"
         "自分のクリーチャー1体は呪文によって相手に選ばれない",
    source=SRC["k33_aarkite"])


# ================================================================ 36/77 銃毒逆夢 ザ・ゲオニー／ジョリー・ザ・ハンド
def sp_geony(s, i):
    """ジョリー・ザ・ハンド：相手のクリーチャー1体を選び、このターン、そのパワーを-3000する"""
    t = s.target(i, lambda x: s.power(1 - i, x) <= 3000) or s.target(i)
    if t is None:
        return
    t.pw -= 3000
    s.ev(f"　ジョリー・ザ・ハンド：{t.c.name} のパワーを-3000")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


add("k33_geony", "銃毒逆夢 ザ・ゲオニー／ジョリー・ザ・ハンド", 5, "D", power=4000,
    races=("dispector", "mafigang", "jokers"), twin=(1, "D", False), pri=7, roles="rem shd",
    enter=exlife_enter, leaverep=exlife_rep, attack=smash_burst("k33_geony", 1, sp_geony), spell=sp_geony,
    text="クリーチャー側：EXライフ（出た時、自分の山札の上から1枚を自分の下にシールドとして置く。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。"
         "スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱えてもよい）。"
         "呪文側《ジョリー・ザ・ハンド》（闇・コスト1・S・トリガーは無い）：相手のクリーチャーを1体選ぶ。"
         "このターン、そのクリーチャーのパワーを-3000する（パワーが0以下になったクリーチャーは破壊される）",
    source=SRC["k33_geony"])


# ================================================================ 37/77 ワーク騎士
def e_work(s, i, u):
    """出た時、山札の上から4枚を墓地に置いてもよい。その後、ジョーカーズ・カード1枚を墓地から手札に戻してもよい"""
    p = s.P[i]
    if len(p.deck) > 6:                 # 山札切れが近い時は置かない（「置いてもよい」の選択）
        s.mill(i, 4)
    cands = [k for k in sorted(set(p.grave)) if "jokers" in BY_KEY[k].races]
    if not cands:
        return
    k = max(cands, key=E.PRI.get)
    p.grave.remove(k)
    p.hand.append(k)
    s.ev(f"　ワーク騎士：墓地の {BY_KEY[k].name} を手札に戻す")


add("k33_work", "ワーク騎士", 4, "D", power=4000, races=("jokers",), pri=7, roles="draw acc",
    enter=e_work, atkswap=jclimb("k33_work", 6),
    text="出た時、自分の山札の上から4枚を墓地に置いてもよい。"
         "その後、ジョーカーズ・カードを1枚、自分の墓地から手札に戻してもよい。"
         "Jクライム6（このクリーチャーが攻撃する時、これと自分の墓地にあるコスト6以下の"
         "ジョーカーズ・クリーチャー1体を入れ替えてもよい。入れ替えたこのクリーチャーは墓地に置かれ、"
         "出てきたクリーチャーが攻撃を続ける）",
    source=SRC["k33_work"])


# ================================================================ 38/77 ×マドギワ親父
def e_madogiwa(s, i, u):
    """出た時、相手は自身の手札を1枚選び、捨てる"""
    discard_choice(s, 1 - i)


def fa_madogiwa(s, i, av, cv):
    """このクリーチャーを自分の墓地から召喚してもよい（コストは支払う）"""
    p = s.P[i]
    if "k33_madogiwa" not in p.grave or s.manaexec(i):
        return []
    n = s.ccost(i, "k33_madogiwa", av)
    if n > av or (n > 0 and not cv.issuperset(BY_KEY["k33_madogiwa"].civ)):
        return []
    if s.fate(i, "k33_madogiwa", "grave", True) != "ok":
        return []
    return [("x:k33_madogiwa", n)]


def ap_madogiwa(s, a):
    i = s.tp
    p = s.P[i]
    if "k33_madogiwa" not in p.grave:
        return
    n = s.ccost(i, "k33_madogiwa", len(p.mana) - p.mused)   # 召喚の直前にもう一度（軽減の記録を新しくする）
    p.grave.remove("k33_madogiwa")
    p.mused += n
    s.ev(f"墓地から召喚：×マドギワ親父（{n}マナ）")
    s.enter(i, "k33_madogiwa", "grave", True)


add("k33_madogiwa", "×マドギワ親父", 3, "D", power=3000, races=("jokers",), pri=5, roles="dis",
    enter=e_madogiwa, atkswap=jclimb("k33_madogiwa", 4),
    freeacts=fa_madogiwa, actapply={"x:k33_madogiwa": ap_madogiwa},
    text="このクリーチャーを自分の墓地から召喚してもよい。"
         "出た時、相手は自身の手札を1枚選び、捨てる。"
         "Jクライム4（このクリーチャーが攻撃する時、これと自分の墓地にあるコスト4以下の"
         "ジョーカーズ・クリーチャー1体を入れ替えてもよい）",
    source=SRC["k33_madogiwa"])


# ================================================================ 39/77 闇影 ヘモグロ-2
def d_hemoglo(s, i, u):
    """自分のターン中に破壊された時、そのターンの終わりに、自分の墓地から出す（枚数を数えておく）"""
    if s.tp != i:
        return
    p = s.P[i]
    rec = p.x.get("k33_hemo")
    n = rec[1] + 1 if rec and rec[0] == s.turn else 1
    p.x["k33_hemo"] = (s.turn, n)
    s.ev("　闇影 ヘモグロ-2：このターンの終わりに墓地から出る")


def tp_hemoglo(s, i):
    """ターンの終わりに墓地から出す（TENDP はバトルゾーンに何もなくても、両プレイヤーについて呼ばれる）"""
    p = s.P[i]
    rec = p.x.get("k33_hemo")
    if not rec or rec[0] != s.turn:
        return
    p.x.pop("k33_hemo", None)
    for _ in range(rec[1]):
        if "k33_hemoglo" not in p.grave or s.over:
            break
        p.grave.remove("k33_hemoglo")
        s.ev("　闇影 ヘモグロ-2：墓地からバトルゾーンに出る")
        s.enter(i, "k33_hemoglo", "grave", False)


add("k33_hemoglo", "闇影 ヘモグロ-2", 3, "D", power=2000, races=("mafigang", "distas"),
    pri=5, roles="acc",
    destroyed=d_hemoglo, tendp=tp_hemoglo,
    text="自分のターン中にこのクリーチャーが破壊された時、そのターンの終わりに、"
         "このクリーチャーを自分の墓地からバトルゾーンに出す。"
         "ササゲール2" + SAS_TEXT.format(2),
    source=SRC["k33_hemoglo"])


# ================================================================ 40/77 ア・ストラ・ゼーレの電影
def e_astrazele(s, i, u):
    """出た時、各プレイヤーは自分の手札を1枚捨てる"""
    for j in (i, 1 - i):
        discard_choice(s, j)


def fa_astrazele(s, i, av, cv):
    """自分のターンに1度、ディスペクター・クリーチャーを自分の墓地から召喚してもよい"""
    p = s.P[i]
    if not s.has(i, "k33_astrazele") or s.manaexec(i) or p.x.get("k33_az") == s.turn:
        return []
    out = []
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if not _plain_cre(k) or "dispector" not in c.races:
            continue
        n = s.ccost(i, k, av)
        if n > av or (n > 0 and not cv.issuperset(c.civ)):
            continue
        if s.fate(i, k, "grave", True) != "ok":
            continue
        out.append(("x:k33_az", k, n))
    return out


def ap_astrazele(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.grave:
        return
    # 召喚の直前にもう一度コストを計算する（ササゲールの記録を、この召喚のものに更新するため）
    n = s.ccost(i, k, len(p.mana) - p.mused)
    p.grave.remove(k)
    p.mused += n
    p.x["k33_az"] = s.turn
    s.ev(f"ア・ストラ・ゼーレの電影：墓地から召喚 {BY_KEY[k].name}（{n}マナ）")
    s.enter(i, k, "grave", True)


add("k33_astrazele", "ア・ストラ・ゼーレの電影", 3, "D", kind="T", races=("trix", "distas"),
    pri=6, roles="dis acc",
    enter=e_astrazele,
    freeacts=fa_astrazele, actapply={"x:k33_az": ap_astrazele},
    text="出た時、各プレイヤーは自分の手札を1枚捨てる。"
         "自分のターンに1度、ディスペクター・クリーチャーを自分の墓地から召喚してもよい。"
         "ササゲール3" + SAS_TEXT.format(3),
    source=SRC["k33_astrazele"])


# ================================================================ 41/77 ケツカッちん
def e_ketsu(s, i, u):
    """出た時、このクリーチャーはシールドを1つブレイクする"""
    s.break_sh(i, 1)


def fa_ketsu(s, i, av, cv):
    """J・O・E 2：コストを2少なくして召喚してもよい（普通のコストで召喚する手はもとからある）"""
    p = s.P[i]
    if "k33_ketsu" not in p.hand:
        return []
    n = max(0, s.ccost(i, "k33_ketsu", av) - 2)
    if n > av or (n > 0 and not cv.issuperset(BY_KEY["k33_ketsu"].civ)):
        return []
    if s.fate(i, "k33_ketsu", "hand", True) != "ok":
        return []
    return [("x:k33_joe", n)]


def ap_ketsu(s, a):
    i = s.tp
    p = s.P[i]
    if "k33_ketsu" not in p.hand:
        return
    n = max(0, s.ccost(i, "k33_ketsu", len(p.mana) - p.mused) - 2)
    p.hand.remove("k33_ketsu")
    p.mused += n
    s.ev(f"J・O・E 2：ケツカッちん（{n}マナ）")
    u = s.enter(i, "k33_ketsu", "hand", True)
    if u is not None:
        u.x["k33_joe"] = s.turn


def te_ketsu(s, i, u):
    """J・O・E：こうして出したら、このターンの終わりに山札の下に置き、1枚引く"""
    if u.x.get("k33_joe") != s.turn:
        return
    p = s.P[i]
    if u not in p.board:
        return
    p.board.remove(u)
    p.deck.insert(0, u.k)
    for k in u.under:
        p.deck.insert(0, k)
    s.ev("　J・O・E 2：ケツカッちん を山札の下に置いて1枚引く")
    s.draw(i)


add("k33_ketsu", "ケツカッちん", 6, "F", power=8000, brk=2, races=("jokers",),
    pri=8, roles="atk blk fin",
    enter=e_ketsu, battleswap=super_guardman("k33_ketsu"), tendall=te_ketsu,
    freeacts=fa_ketsu, actapply={"x:k33_joe": ap_ketsu},
    text="J・O・E 2（このクリーチャーを、コストを2少なくして召喚してもよい。こうして出したら、"
         "このターンの終わりに、それを自分の山札の下に置く。そうしたら、カードを1枚引く）。"
         + SGUARD_TEXT +
         "W・ブレイカー。出た時、このクリーチャーはシールドを1つブレイクする",
    source=SRC["k33_ketsu"])


# ================================================================ 42/77 銃車逆夢 ザ・マグニー／ジョリー・ザ・スクラッパー
def sp_magny(s, i):
    """ジョリー・ザ・スクラッパー：相手のコスト3以下のエレメントを1つ選び、破壊する"""
    t = s.target(i, lambda x: x.c.cost <= 3, kinds="CTX")
    if t is None:
        return
    s.ev(f"　ジョリー・ザ・スクラッパー：{t.c.name} を破壊")
    destroy(s, i, t)


add("k33_magny", "銃車逆夢 ザ・マグニー／ジョリー・ザ・スクラッパー", 5, "F", power=5000,
    races=("dispector", "beatjockey", "jokers"), twin=(2, "F", False), pri=7, roles="rem shd",
    enter=exlife_enter, leaverep=exlife_rep, attack=smash_burst("k33_magny", 2, sp_magny), spell=sp_magny,
    text="クリーチャー側：EXライフ（出た時、自分の山札の上から1枚を自分の下にシールドとして置く。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。"
         "スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱えてもよい）。"
         "呪文側《ジョリー・ザ・スクラッパー》（火・コスト2・S・トリガーは無い）："
         "相手のコスト3以下のエレメントを1つ選び、破壊する",
    source=SRC["k33_magny"])


# ================================================================ 43/77 爆衆 ランブル-2
def e_rumble(s, i, u):
    """出た時、自分の手札を1枚捨て、カードを2枚引く"""
    k = worst_hand(s, i)
    if k is not None:
        s.discard(i, k)
    s.draw(i, 2)


def l_rumble(s, i, u, dest):
    """離れた時、このターン、自分のクリーチャー1体に「スピードアタッカー」を与える"""
    cs = [z for z in s.P[i].board if z.c.kind == "C" and not z.sa and not z.c.sa]
    if not cs:
        return
    # 召喚酔いで攻撃できないものを先に、その中でパワーの高いものを選ぶ（全デッキ共通の決まり）
    z = max(cs, key=lambda x: (1 if x.sick else 0, s.power(i, x)))
    z.sa = True
    s.ev(f"　爆衆 ランブル-2：{z.c.name} にスピードアタッカーを与える")


add("k33_rumble", "爆衆 ランブル-2", 3, "F", power=3000, races=("beatjockey", "distas"),
    pri=5, roles="draw acc atk",
    enter=e_rumble, left=l_rumble,
    text="出た時、自分の手札を1枚捨て、カードを2枚引く。"
         "このクリーチャーが離れた時、このターン、自分のクリーチャー1体に「スピードアタッカー」を与える。"
         "ササゲール2" + SAS_TEXT.format(2),
    source=SRC["k33_rumble"])


# ================================================================ 45/77 メモッタルド・デカスギオ／メモメモ・ジョーカーズ
def sp_memotta(s, i):
    """メモメモ・ジョーカーズ：山札の上から3枚を見て、ジョーカーズ・カード1枚を手札に加え、残りを山札の下へ"""
    s.dig(i, 3, lambda k: "jokers" in BY_KEY[k].races)


add("k33_memotta", "メモッタルド・デカスギオ／メモメモ・ジョーカーズ", 6, "N", power=8000, brk=2,
    mach=True, gs=True, races=("unknown", "jokers"), twin=(1, "N", False), pri=9,
    roles="atk rem draw trg",
    spell=sp_memotta, atkswap=jchange("k33_memotta", 8),
    text="クリーチャー側：G・ストライク（相手のクリーチャーを1体選び、このターン攻撃できなくする）。"
         "マッハファイター。W・ブレイカー。"
         "Jチェンジ8（このクリーチャーが攻撃する時、これと自分のマナゾーンにあるコスト8以下の"
         "ジョーカーズ・クリーチャー1体を入れ替えてもよい。入れ替えたこのクリーチャーはマナゾーンに置かれ、"
         "出てきたクリーチャーが攻撃を続ける）。"
         "呪文側《メモメモ・ジョーカーズ》（自然・コスト1・ジョーカーズ呪文・S・トリガーは無い）："
         "自分の山札の上から3枚を見る。その中からジョーカーズ・カードを1枚表向きにし、手札に加えてもよい。"
         "残りを好きな順序で山札の下に置く",
    source=SRC["k33_memotta"])


# ================================================================ 46/77 銃蝸逆夢 ザ・デンニー／ジョリー・ザ・トラップ
def sp_denny(s, i):
    """ジョリー・ザ・トラップ：自分の山札の上から1枚をマナゾーンに置く"""
    s.ramp(i, 1)


add("k33_denny", "銃蝸逆夢 ザ・デンニー／ジョリー・ザ・トラップ", 5, "N", power=5000,
    races=("dispector", "gransect", "jokers"), twin=(2, "N", False), pri=7, roles="acc shd",
    enter=exlife_enter, leaverep=exlife_rep, attack=smash_burst("k33_denny", 2, sp_denny), spell=sp_denny,
    text="クリーチャー側：EXライフ（出た時、自分の山札の上から1枚を自分の下にシールドとして置く。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。"
         "スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱えてもよい）。"
         "呪文側《ジョリー・ザ・トラップ》（自然・コスト2・S・トリガーは無い）："
         "自分の山札の上から1枚をマナゾーンに置く",
    source=SRC["k33_denny"])


# ================================================================ 47/77 Q字工事
def ld_qji(s, i, u, dest, destroy_):
    """破壊される時、墓地のかわりにマナゾーンに置く"""
    if u.k != "k33_qji" or not destroy_ or dest != "grave":
        return None
    s.ev("　Q字工事：破壊されるかわりにマナゾーンへ")
    return "mana"


add("k33_qji", "Q字工事", 3, "N", power=5000, races=("jokers",), pri=5, roles="blk acc atk",
    battleswap=super_guardman("k33_qji"), leavedest=ld_qji, atkswap=jchange("k33_qji", 6),
    text=SGUARD_TEXT +
         "このクリーチャーが破壊される時、墓地のかわりにマナゾーンに置く。"
         "Jチェンジ6（このクリーチャーが攻撃する時、これと自分のマナゾーンにあるコスト6以下の"
         "ジョーカーズ・クリーチャー1体を入れ替えてもよい）",
    source=SRC["k33_qji"])
