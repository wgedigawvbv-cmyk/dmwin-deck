#!/usr/bin/env python3
"""第3版エンジンの動作確認：カードの依存関係とメタの効き方を、場面を作って1つずつ確かめる

  python test3.py
"""
import random

from cards3 import DECKS
from engine3 import Game, U

OK = []


def mk(hand=(), mana=(), board=(), grave=(), ohand=(), omana=(), oboard=(), osh=None, sh=None, deck=None, odeck=None,
       phase="M", turn=5):
    """プレイヤー0の番の場面を作る。board は (カード, 出たばかりか) か カード名"""
    g = Game(DECKS["4c der'Bande"], DECKS["4c der'Bande"], random.Random(1), first=0)
    for i, (h, m, b) in enumerate(((hand, mana, board), (ohand, omana, oboard))):
        p = g.P[i]
        p.hand = list(h)
        p.mana = list(m)
        p.mused = 0
        p.grave = []
        p.board = []
        for x in b:
            k, sick = (x, False) if isinstance(x, str) else x
            u = U(k)
            u.sick = sick
            u.jd = False
            p.board.append(u)
    g.P[0].grave = list(grave)
    if sh is not None:
        g.P[0].sh = [(k, False) for k in sh]
    if osh is not None:
        g.P[1].sh = [(k, False) for k in osh]
    if deck is not None:
        g.P[0].deck = list(deck)
    if odeck is not None:
        g.P[1].deck = list(odeck)
    g.phase = phase
    g.turn = turn * 2 - 1
    g.tp = 0
    return g


def has(g, a):
    return a in g.legal()


def kinds(g, t):
    return [a for a in g.legal() if a[0] == t]


def check(name, cond):
    OK.append((name, bool(cond)))
    print(("○ " if cond else "× ") + name)


def unit(g, i, k):
    for u in g.P[i].board:
        if u.k == k:
            return u
    return None


def main():
    # ---------- メタ ----------
    g = mk(hand=["everlast"], mana=["viride"] * 7, oboard=["kabocha"])
    check("かぼちゃうちゃう：マナ7枚ならコスト7は出せる", has(g, ("play", "everlast", 0)))
    g = mk(hand=["dogigyaku"], mana=["viride"] * 4, board=["viride"], oboard=["kabocha"], phase="A")
    g.apply(("atk", 0, "P", None))
    check("かぼちゃうちゃう：マナ4枚ではドギラゴン逆にチェンジしない", unit(g, 0, "dogigyaku") is None and "dogigyaku" in g.P[0].hand)

    g = mk(hand=["fujin", "fujin", "fujin"], mana=["fujin"] * 6, oboard=["klin"])
    g.apply(("play", "fujin", 0))
    g.apply(("play", "fujin", 0))
    check("クリン・ラビィ：3体目は出せない", not has(g, ("play", "fujin", 0)))

    g = mk(hand=["mirai", "mirai"], mana=["takkyu"] * 6, oboard=["ichion"])
    g.apply(("play", "mirai", 0))
    check("一音の妖精：呪文は1ターンに1回", not has(g, ("play", "mirai", 0)))
    g = mk(hand=["fujin", "fujin"], mana=["fujin"] * 6, oboard=["ichion"])
    unit(g, 1, "ichion").under = ["kohaku"]
    g.apply(("play", "fujin", 0))
    check("一音の妖精（進化）：クリーチャーは1ターンに1体", not has(g, ("play", "fujin", 0)))

    g = mk(hand=[], mana=["tenbin", "kohaku", "kohaku"], board=["derbande"], oboard=["poppi"], phase="A")
    check("ポッピ：der'Bande はマナから呪文を使えない", ("atk", 0, "P", "tenbin") not in g.legal())
    g = mk(hand=[], mana=["tenbin", "kohaku", "kohaku"], board=["derbande"], phase="A")
    check("ポッピがいなければ使える", ("atk", 0, "P", "tenbin") in g.legal())
    g = mk(hand=["leviya"], mana=["leviya", "trap", "parli", "kohaku"], board=["zen"], oboard=["poppi"])
    check("ポッピ：創世竜ループは起動できない", not has(g, ("loop", "z")) and not kinds(g, "zen"))

    g = mk(hand=["radio"], mana=["kohaku"] * 4, oboard=["tokoshie"], deck=["efc", "klin", "klin", "dagra", "efc", "efc"])
    g.apply(("play", "radio", 0))
    check("とこしえの超人：ラジオで山札からは出ない", g.ncre(0) == 0)
    g = mk(hand=["radio"], mana=["kohaku"] * 4, deck=["efc", "klin", "klin", "dagra", "efc", "efc"])
    g.apply(("play", "radio", 0))
    check("いなければ2体出る", g.ncre(0) == 2)

    g = mk(hand=["dogigyaku"], mana=["viride"] * 8, board=["viride"], phase="A")
    g.P[1].sh.append(("hustle", True))
    g.apply(("atk", 0, "P", None))
    check("ハッスル・キャッスル：革命チェンジしない", unit(g, 0, "dogigyaku") is None)
    g = mk(mana=["viride"] * 3, board=["viride"], osh=["clock"], phase="A")
    g.P[0].sh.append(("hustle", True))
    g.apply(("atk", 0, "P", None))
    check("ハッスル・キャッスル：S・トリガー獣は出る（ターンが終わる）", g.tp == 1 and unit(g, 1, "clock") is not None)

    g = mk(mana=["viride"] * 3, board=["viride", "magnum"], osh=["clock", "clock"], phase="A")
    g.apply(("atk", 0, "P", None))
    check("マグナム：S・トリガー獣は使われない", g.tp == 0 and unit(g, 1, "clock") is None and g.trig[1] == 0)

    g = mk(hand=["robin"], mana=["leaf"] * 3, board=["tina"], oboard=["testa"], phase="A")
    g.apply(("atk", 0, "P", None))
    check("テスタ・ロッサ：革命チェンジしない", unit(g, 0, "robin") is None)
    g = mk(hand=["robin"], mana=["leaf"] * 3, board=["tina"], phase="A")
    n = len(g.P[1].hand)
    g.P[1].hand = ["klin", "klin"]
    g.apply(("atk", 0, "P", None))
    check("いなければロビンフッドにチェンジし、相手の手札を1枚捨てさせる", unit(g, 0, "robin") is not None and g.chg[0] == 1)

    g = mk(hand=["saint", "chakra"], mana=["viride"] * 4, oboard=["fujin"])
    check("フウジン天：G城は置けない", not has(g, ("play", "saint", 0)))
    g.apply(("play", "chakra", 0))
    check("フウジン天：チャクラでシールドは増えない", len(g.P[0].sh) == 5)

    g = mk(hand=["vt"], mana=["kerola"] * 8, oboard=["klin", "kabocha", "dagra"], ohand=["kohaku"], omana=["kohaku"] * 4)
    g.apply(("play", "vt", 0))
    check("5000VT：パワー5000以下を全部戻す（かぼちゃは残る）", [u.k for u in g.P[1].board] == ["kabocha"])
    g.apply(("attack",))
    g.apply(("end",))
    g.apply(("skip",))
    check("5000VT：次のターン、相手は小型を出せない", not kinds(g, "play") or all(a[1] != "kohaku" and a[1] != "klin" for a in kinds(g, "play")))

    g = mk(hand=["mirai"], mana=["takkyu"] * 6, oboard=["chakra"])
    unit(g, 1, "chakra").hyper = True
    check("チャクラ（ハイパー中）：コスト5以下の呪文は唱えられない", not has(g, ("play", "mirai", 0)))

    g = mk(hand=["jasmine"], mana=["jasmine"] * 3, oboard=["robin"])
    g.apply(("play", "jasmine", 0))
    check("ロビンフッド：山札からのマナ加速が止まる", len(g.P[0].mana) == 3)
    g = mk(hand=["kuzen"], mana=["kuzen"] * 3, oboard=["robin"])
    g.apply(("spell", "kuzen"))
    check("ロビンフッド：墓地肥やしが止まる", len(g.P[0].grave) == 1 and len(g.P[0].mana) == 3)

    g = mk(hand=["fujin"], mana=["fujin"] * 3, oboard=["zoro"])
    g.apply(("play", "fujin", 0))
    ok = unit(g, 0, "fujin") is None and g.P[0].delayed == ["fujin"]
    g.apply(("attack",))
    g.apply(("end",))
    g.apply(("skip",))
    g.apply(("attack",))
    g.apply(("end",))
    check("ゾロ・ア・スタート：出したクリーチャーは次のターンに遅れて出る", ok and unit(g, 0, "fujin") is not None)

    g = mk(hand=["ops"], mana=["leaf"] * 9, board=["hangyaku"], oboard=["klin", "anti", "katsuemon"], phase="A")
    unit(g, 0, "hangyaku").under = ["mflower"]
    g.P[1].hand = ["kohaku"]
    g.P[1].mana = ["kohaku"] * 5
    g.apply(("atk", 0, "P", None))
    check("オーパーツ銃：指定したコストを全部破壊し、そのコストを使えなくする",
          g.P[1].ban == 3 and all(u.c.cost != 3 for u in g.P[1].board))

    g = mk(board=["viride", "chakra"], oboard=["dogigyaku"], osh=[], phase="A")
    g.P[1].protect = True
    g.apply(("atk", 0, "P", None))
    check("ドギラゴン逆：守られている間はダイレクトアタックで負けない", not g.over)
    g = mk(hand=["trap"], mana=["trap"] * 4, oboard=["klin"])
    g.P[1].protect = True
    g.apply(("play", "trap", 0))
    check("ドギラゴン逆：守られている間、相手の効果で離れない", unit(g, 1, "klin") is not None)

    g = mk(board=["everlast"], phase="A")
    g.P[1].sh.append(("saint", True))
    g.apply(("atk", 0, "P", None))
    check("セイント・キャッスル：3枚ブレイクを1枚で受けて手札に戻る", len(g.P[1].sh) == 5 and "saint" in g.P[1].hand)

    # ---------- デッキの動き ----------
    g = mk(hand=["pon"], mana=["kohaku", "kerola"], board=["teacher", "dokkoi"], turn=2,
           deck=["kerola"] * 10 + ["kohaku"] * 4 + ["eringi"] * 4 + ["efc", "shako", "saitan", "takkyu", "pon", "pon"])
    check("ドッコイループ：ティーチャー＋ドッコイ＋ポンの助で起動できる", has(g, ("loop", "d")))
    g.apply(("loop", "d"))
    check("ドッコイループ：2ターン目は勝てず、凍結をかける", not g.over and g.P[1].frozen and len(g.P[0].mana) == 4)
    g = mk(hand=["pon"], mana=["kohaku", "kerola", "eringi", "eringi", "eringi", "eringi"], board=["teacher", "dokkoi"],
           deck=["kohaku"] * 4 + ["efc", "shako", "saitan", "takkyu", "pon", "pon"] + ["kerola"] * 10)
    g.apply(("loop", "d"))
    check("ドッコイループ：マナ9枚に届けば緊急再誕からシャコガイルで勝つ", g.over and g.winner == 0)
    g = mk(hand=["pon"], mana=["kohaku", "kerola", "eringi", "eringi", "eringi", "eringi"], board=["teacher", "dokkoi"],
           oboard=["klin"])
    check("ドッコイループ：クリン・ラビィがいると起動できない", not has(g, ("loop", "d")))
    g = mk(hand=["pon"], mana=["kohaku", "kerola"], board=["teacher"])
    check("ドッコイループ：ドッコイがいなければ起動できない", not has(g, ("loop", "d")))

    full = ["kohaku"] * 6 + ["valhalla", "wokanna"] + ["jasmine"] * 8
    g = mk(hand=["leviya"], mana=["leviya", "trap", "parli", "kohaku"], board=["zen"], deck=full)
    check("創世竜ループ：創世竜＋レヴィヤ2枚＋トラップ＋パーリで起動できる", has(g, ("loop", "z")))
    g.apply(("loop", "z"))
    check("創世竜ループ：そのまま勝つ", g.over and g.winner == 0)
    g = mk(hand=["leviya"], mana=["leviya", "trap", "kohaku", "kohaku"], board=["zen"], deck=full)
    check("創世竜ループ：パーリがなければ起動できない", not has(g, ("loop", "z")))
    g = mk(hand=["leviya"], mana=["leviya", "trap", "parli", "kohaku"], board=["zen"], deck=full)
    g.P[1].sh.append(("hustle", True))
    g.apply(("loop", "z"))
    check("創世竜ループ：ハッスル・キャッスルがあると勝ちきれない（マナは増える）", not g.over and len(g.P[0].mana) > 8)
    g = mk(hand=["leviya"], mana=["leviya", "trap", "parli", "kohaku"], board=["zen"], oboard=["tokoshie", "testa"], deck=full)
    g.apply(("loop", "z"))
    check("創世竜ループ：コスト4以下のメタはトラップでどかして勝つ", g.over and g.winner == 0)
    g = mk(hand=["leviya"], mana=["leviya", "trap", "parli", "kohaku"], board=["zen"], oboard=[("klin", True)], deck=full)
    unit(g, 1, "klin").jd = True
    g.apply(("loop", "z"))
    check("創世竜ループ：出たばかりのクリン・ラビィ（選べない）は残り、勝ちきれない", not g.over)
    g = mk(hand=["leviya"], mana=["leviya", "trap", "parli", "kohaku"], board=["zen"], deck=["kohaku"] * 12 + ["wokanna"],
           sh=["valhalla", "kohaku"])
    g.apply(("loop", "z"))
    check("創世竜ループ：ヴァルハラが盾に埋まり、エスメルもなければ勝ちきれない", not g.over)

    g = mk(hand=["tenbin"], mana=["tenbin", "shunsen", "radio", "kohaku"], board=["derbande"], phase="A",
           deck=["efc"] * 10, osh=["kabocha"] * 5)
    unit(g, 0, "derbande").under = ["kohaku"]
    g.apply(("atk", 0, "P", "tenbin"))
    d = unit(g, 0, "derbande")
    check("der'Bande：攻撃時にマナの天秤→2枚ブレイクして起きる", len(g.P[1].sh) == 3 and not d.tap)
    g.apply(("atk", 0, "P", "shunsen"))
    check("der'Bande：瞬閃→9000で2枚ブレイク、攻撃の後に起きる", len(g.P[1].sh) == 1 and not d.tap)
    g.apply(("atk", 0, "P", "radio"))
    check("der'Bande：3枚目で12000", g.power(0, d, True) == 12000 and len(g.P[1].sh) == 0)
    g = mk(hand=["anti", "derbande"], mana=["anti", "kohaku", "katsuemon"], deck=["efc"] * 10)
    g.apply(("play", "anti", 0))
    d = unit(g, 0, "derbande")
    g.apply(("attack",))
    check("アンティハムト：der'Bande を出してすぐ攻撃できる", d is not None and any(a[0] == "atk" and a[1] == 1 for a in g.legal()))

    g = mk(hand=["crossfire", "zoro"], mana=["kuzen"] * 3, grave=["lelady"] * 5)
    check("クロスファイア：墓地5体ではただで出せない", not has(g, ("play", "crossfire", 0)))
    g = mk(hand=["crossfire", "zoro"], mana=["kuzen"] * 3, grave=["lelady"] * 5 + ["margani"],
           osh=["kabocha", "kabocha", "klin", "klin", "klin"])
    check("クロスファイア：墓地6体でただで出せる", has(g, ("play", "crossfire", 0)))
    g.apply(("play", "crossfire", 0))
    g.apply(("abyss",))
    g.apply(("attack",))
    g.apply(("atk", 0, "P", None))
    check("ゾロ：クロスファイアからチェンジして全ブレイク", unit(g, 0, "zoro") is not None and len(g.P[1].sh) == 0)
    g.apply(("atk", 1, "P", None))
    check("ゾロ：アビスラッシュのマーガニーでとどめ（3マナ）", g.over and g.winner == 0)

    g = mk(hand=["leaf", "robin"], mana=["leaf", "tina"], board=["mflower"], turn=2, deck=["aroma"] * 10)
    g.apply(("play", "leaf", 1))
    g.apply(("attack",))
    g.apply(("atk", 0, "P", None))
    check("サイバー：2ターン目にリーフ（3枚引く）→ロビンフッドで2枚ブレイク",
          unit(g, 0, "robin") is not None and len(g.P[1].sh) == 3 and "leaf" in g.P[0].hand)

    g = mk(hand=["jaouga"], mana=["shuto", "shuto", "artel", "artel"], board=["fujin", "klin"])
    check("ジャオウガ：コストの違う2体をタップして4マナで出せる", has(g, ("play", "jaouga", 0)))
    g = mk(hand=["jaouga"], mana=["shuto", "shuto", "artel", "artel"], board=["fujin", "testa"])
    check("ジャオウガ：同じコストの2体では足りない", not has(g, ("play", "jaouga", 0)))
    g = mk(hand=["shuto"], mana=["shuto"] * 3, omana=["kohaku"], oboard=["zen"])
    g.apply(("play", "shuto", 0))
    check("終斗：相手のマナに多色があれば3マナ。出た時に創世竜を倒す", unit(g, 1, "zen") is None)

    g = mk(hand=["saint", "viride", "dogigyaku"], mana=["viride", "zaze"], turn=2)
    g.apply(("play", "saint", 0))
    check("ウィリデ：G城でシールドが多ければ2マナ", not has(g, ("play", "viride", 0)))   # 残り1マナなので出せない
    g = mk(hand=["viride", "dogigyaku", "chakra"], mana=["viride", "zaze", "zaze"], board=["zaze"], turn=3, deck=["efc"] * 10)
    unit(g, 0, "zaze").tap = True
    g.apply(("play", "chakra", 0))
    z = unit(g, 0, "zaze")
    check("ザゼ・ゼーン：チャクラでシールドが増えると起きる", not z.tap and len(g.P[0].sh) == 6)
    g.apply(("attack",))
    g.apply(("atk", 0, "P", None))
    check("ウィリデ：3ターン目にザゼ・ゼーンからドギラゴン逆へチェンジ", unit(g, 0, "dogigyaku") is not None and g.P[0].protect)

    # ---------------------------------------------------------------- G・リンク（ゴッドの合体）
    # 実在のゴッドを使わず、既存のカード2枚を仮にゴッドとして登録して、エンジンの仕組みだけを確かめる。
    import engine3 as E
    E.GODLINK["saint"] = ("L", ("zaze",))
    E.GODLINK["zaze"] = ("R", ("saint",))
    try:
        g = mk(board=["zaze"], turn=5)
        base = unit(g, 0, "zaze")
        nu = E.U("saint")
        check("G・リンクできるか判定できる", g.can_link(0, nu, base))
        p0 = g.power(0, base)
        g.god_link(0, nu, base)
        check("リンクしたカードは board に別個では置かれない", len(g.P[0].board) == 1)
        check("パワーは合計になる", g.power(0, base) == p0 + E.CARD["saint"].power)
        check("ブレイク数はいちばん多いカードに合わせる",
              g.brk(0, base) == max(E.CARD["zaze"].brk, E.CARD["saint"].brk))
        check("リンクしたカードも『場にある』と数える", g.has(0, "saint") and g.has(0, "zaze"))
        check("リンクしているクリーチャーは召喚酔いしない", not base.sick)
        check("どちらかがブロッカーならブロックできる",
              g.can_block(base) == (E.CARD["zaze"].blocker or E.CARD["saint"].blocker))
        # 離れる時は1枚だけ
        n0 = len(g.P[0].board)
        g.leave(0, base, "grave", destroy=True)
        left = g.P[0].board
        check("離れる時は構成しているカードのうち1枚だけが離れる", len(left) == n0)
        check("離れたほうは墓地に行く", len(g.P[0].grave) == 1)
        check("残ったほうはリンクが外れて単体になる", left and not left[0].link)
        # 複製しても混ざらない
        g2 = mk(board=["zaze"], turn=5)
        b2 = unit(g2, 0, "zaze")
        g2.god_link(0, E.U("saint"), b2)
        h2 = g2.clone()
        h2.P[0].board[0].link.clear()
        check("盤面を複製しても、もとのリンクは壊れない", len(b2.link) == 1)
    finally:
        del E.GODLINK["saint"], E.GODLINK["zaze"]

    # ---------------------------------------------------------------- 追加ターン
    g = mk(turn=5)
    who, t0 = g.tp, g.turn
    g.P[g.tp].extra = 1
    g.end_turn()
    check("追加ターン：同じプレイヤーの番が続く", g.tp == who)
    check("追加ターン：自分のターン数が1つ進む", g.myturn(who) == (t0 + 2 + 1) // 2 if who == g.first else True)
    g2 = mk(turn=5)
    w2 = g2.tp
    g2.end_turn()
    check("追加ターンが無ければ相手の番になる", g2.tp == 1 - w2)

    # ---------------------------------------------------------------- そのターン破壊された数
    g = mk(board=["zaze"], oboard=["zaze"], turn=5)
    check("破壊の数はターンのはじめに0", g.dcount == [0, 0])
    g.leave(1, g.P[1].board[0], "grave", destroy=True)
    check("相手のクリーチャーが破壊されたら数える", g.dcount[1] == 1 and g.dcount[0] == 0)
    g.leave(0, g.P[0].board[0], "grave", destroy=False)
    check("破壊でなければ数えない", g.dcount[0] == 0)

    # ---------------------------------------------------------------- 能力をすべて無視する
    g = mk(board=["zaze"], turn=5)
    z = unit(g, 0, "zaze")
    check("ふつうは能力が働く", g.abi(0, z))
    f = (lambda st, i, u: u.k == "zaze")
    E.ABILOCK.append(f)
    try:
        check("ABILOCK を登録すると能力が無視される", not g.abi(0, z))
        check("能力を無視されるとブロッカーでもなくなる", not g.can_block(z))
    finally:
        E.ABILOCK.remove(f)

    # ---------------------------------------------------------------- カードを使うコストの全体補正
    g = mk(turn=5)
    from cards3 import BY_KEY as _BK
    tama = next(k for k, c in _BK.items() if c.kind == "T" and c.cost >= 3)
    cas = next((k for k, c in _BK.items() if c.kind == "G" and c.cost >= 3), None)
    twn = next(k for k, c in _BK.items() if c.twin and c.twin[0] >= 3)
    b = (g.ncost(0, tama), g.ncost(0, twn, twin=True), g.ncost(0, cas) if cas else 0)
    f2 = (lambda st, i, k: -2)
    E.SPCOSTAURA.append(f2)
    try:
        check("全体のコスト補正がタマシードに効く", g.ncost(0, tama) == b[0] - 2)
        check("全体のコスト補正がツインパクトの呪文側に効く", g.ncost(0, twn, twin=True) == b[1] - 2)
        if cas:
            check("全体のコスト補正が城に効く", g.ncost(0, cas) == b[2] - 2)
        check("クリーチャーでないカードのコストは1より下がらない", g.ncost(0, tama, 1) == 1)
    finally:
        E.SPCOSTAURA.remove(f2)
    check("補正を外すと元に戻る", g.ncost(0, tama) == b[0])

    # 能力を無視されても攻撃そのものは通る（止まるのは「攻撃する時」の誘発だけ）
    f3 = (lambda st, i, u: True)
    E.ABILOCK.append(f3)
    try:
        n = E.selftest(60)
    finally:
        E.ABILOCK.remove(f3)
    check("能力をすべて無視されても、攻撃そのものは止まらない（ゲームが終わる）", 0 < n < 20000)

    # ---------------------------------------------------------------- シールドの表裏
    g = mk(turn=5)
    check("シールドを表向きにできる", g.flip_shield(0, 0, True) and g.P[0].sh[0][1])
    check("裏向きに戻せる", g.flip_shield(0, 0, False) and not g.P[0].sh[0][1])
    check("範囲外のシールドは何もしない", not g.flip_shield(0, 99, True))

    bad = [n for n, c in OK if not c]
    print(f"\n{len(OK) - len(bad)}/{len(OK)} 通過" + ("" if not bad else "　失敗：" + "、".join(bad)))


if __name__ == "__main__":
    main()
