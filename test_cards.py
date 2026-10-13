#!/usr/bin/env python3
"""新しく実装したカードと仕組みの確認：場面を作って1つずつ確かめる

  侵略・S級侵略・禁断と封印・クロスギア・EXライフ・Jクライム・マッドネス・G・ゼロ・シンパシー・
  ハイパーエナジー・フシギバース・D・D・D・革命0トリガー・マナ武装5・シンカライズ など。

  python test_cards.py
"""
import random

import engine3
from cards3 import BY_KEY, DECKS
from engine3 import Game, U
from test3 import check, has, mk, unit, OK


def mk2(**kw):
    """test3.mk と同じだが、deck を長めに用意する（山札が尽きる判定を避ける）"""
    g = mk(**kw)
    for i in (0, 1):
        if len(g.P[i].deck) < 10:
            g.P[i].deck = ["fujin"] * 20
    return g


def main():
    # ---------------------------------------------------------------- 侵略
    g = mk2(hand=["n_redzonez"], mana=["testa"] * 6, board=["n_toring"], osh=["fujin"] * 5, phase="A")
    g.apply(("atk", 0, "P", None))
    u = unit(g, 0, "n_redzonez")
    check("侵略：火のコマンドの攻撃にレッドゾーンZを手札から重ねる",
          u is not None and u.under == ["n_toring"] and "n_redzonez" not in g.P[0].hand)

    g = mk2(hand=[], mana=["testa"] * 3 + ["n_redmad"], board=["n_toring"], phase="A")
    g.apply(("atk", 0, "P", None))
    check("S級侵略：マナゾーンからレッドマッドを重ねる", unit(g, 0, "n_redmad") is not None)

    g = mk2(hand=["n_redzonef"], mana=["testa"] * 6, board=["n_toring"], osh=["fujin"] * 5, phase="A")
    g.apply(("atk", 0, "P", None))
    u = unit(g, 0, "n_toring")
    check("レッドゾーンF：最初の攻撃の終わりに自分を破壊して下のコマンドがアンタップ",
          u is not None and not u.tap and "n_redzonef" in g.P[0].grave)

    g = mk2(hand=["n_redzonez"], mana=["testa"] * 6, board=["n_toring"], osh=["fujin"] * 5, phase="A")
    g.apply(("atk", 0, "P", None))
    check("レッドゾーンZ：進化でないクリーチャーの上に出てシールドを1つ墓地へ",
          len(g.P[1].sh) <= 4 and "fujin" in g.P[1].grave)

    # ---------------------------------------------------------------- 禁断と封印
    d = dict(DECKS["火水闇ジャオウガ"])
    d["fujin"] = 3
    d["n_kindan"] = 1
    g = Game(d, DECKS["4c der'Bande"], random.Random(3), first=0)
    ku = next((u for u in g.P[0].board if u.k == "n_kindan"), None)
    check("禁断：ゲームのはじめから場にあり、封印が6つある", ku is not None and ku.x["seals"] == 6)
    check("禁断：封印のぶん山札が減っている", len(g.P[0].deck) == 40 - 1 - 6 - 10)

    g = mk2(hand=["n_toring"], mana=["testa"] * 4, board=[])
    g.P[0].board.append(U("n_kindan"))
    g.P[0].board[-1].x["seals"] = 2
    g.P[0].board[-1].x["sealcards"] = ["fujin", "fujin"]
    g.apply(("play", "n_toring", 0))
    check("封印：火のコマンドが出ると封印が1つ外れる", unit(g, 0, "n_kindan").x["seals"] == 1)

    g = mk2(hand=["n_toring"], mana=["testa"] * 4, board=[], oboard=["klin", "fujin"])
    g.P[0].board.append(U("n_kindan"))
    g.P[0].board[-1].x["seals"] = 1
    g.P[0].board[-1].x["sealcards"] = ["fujin"]
    g.apply(("play", "n_toring", 0))
    check("禁断解放：封印が0でドキンダムXになる", unit(g, 0, "n_dokindam") is not None)
    check("禁断解放：相手のクリーチャーが封印されて場からいなくなる",
          len(g.P[1].board) == 0 and len(g.P[1].sealed) == 2)
    g.P[1].board.append(U("n_toring"))                     # 相手が火のコマンドを出せば封印が外れる
    engine3.ENTERWATCH and None
    from envcards.env0 import remove_seal
    remove_seal(g, 1, "F")
    check("封印：外れるとクリーチャーが場に戻る", len(g.P[1].sealed) == 1 and len(g.P[1].board) == 2)

    # ---------------------------------------------------------------- クロスギア
    g = mk2(hand=["n_zangeki"], mana=["testa"] * 6, board=["n_buei"])
    check("クロスギア：ジェネレートの手がある", any(a[0] == "x:gen" and a[1] == "n_zangeki" for a in g.legal()))
    g.apply(next(a for a in g.legal() if a[0] == "x:gen"))
    check("クロスギア：場に出る（クロスはまだされていない）", unit(g, 0, "n_zangeki") is not None)
    cross = [a for a in g.legal() if a[0] == "x:cross"]
    check("クロスギア：ただでクロスする手がある（武偉にはコスト0）", bool(cross) and cross[0][3] == 0)
    g.apply(cross[0])
    gu = unit(g, 0, "n_zangeki")
    bu = unit(g, 0, "n_buei")
    check("クロスギア：クロス先が記録される", gu.x.get("on") == bu.uid)
    check("ザンゲキ：クロスしたらサムライのパワー+2000", g.power(0, bu) == 8000)
    check("ザンゲキ：クロスしたらスピードアタッカーを与える", any(f(g, 0, bu) for f in engine3.SAOK))
    g.P[0].board.remove(bu)
    check("クロスギア：クロス先がいなくなっても場に残る", unit(g, 0, "n_zangeki") is not None)

    g = mk2(hand=["n_sengoku"], mana=["testa"] * 6, board=["n_musashi"])
    g.apply(next(a for a in g.legal() if a[0] == "x:gen"))
    g.apply(next(a for a in g.legal() if a[0] == "x:cross"))
    mu = unit(g, 0, "n_musashi")
    check("センゴク：クロスしたらブレイク数が1増える", g.brk(0, mu) == 3)

    # ---------------------------------------------------------------- EXライフ・ドリーム
    g = mk2(hand=["n_mouja"], mana=["vamilia"] * 4 + ["testa"] * 4, osh=["fujin"] * 5, oboard=["klin"], ohand=["fujin"])
    g.apply(("play", "n_mouja", 0))
    u = unit(g, 0, "n_mouja")
    check("EXライフ：出た時にシールドを下に置く", u is not None and u.x.get("ex") == 1)
    check("モウジャキンガ：相手のシールド・クリーチャー・手札を墓地へ",
          len(g.P[1].sh) == 4 and unit(g, 1, "klin") is None and not g.P[1].hand)
    g.leave(0, u, "grave", by_opp=True, destroy=True)
    check("EXライフ：1回目の除去では離れない", unit(g, 0, "n_mouja") is not None and u.x["ex"] == 0)
    g.leave(0, u, "grave", by_opp=True, destroy=True)
    check("EXライフ：2回目の除去で離れる", unit(g, 0, "n_mouja") is None)

    g = mk2(hand=["n_bolrev"], mana=["klin"] * 6, board=["n_bolrev"])
    g.apply(("play", "n_bolrev", 0))
    check("ドリーム・クリーチャー：同じ名前の2体目は出られない",
          sum(1 for u in g.P[0].board if u.k == "n_bolrev") == 1)

    # ---------------------------------------------------------------- Jクライム・マッドネス・G・ゼロ
    g = mk2(hand=[], mana=["vamilia"] * 6, board=["n_aisha"], grave=["n_mouja"], phase="A")
    g.apply(("atk", 0, "P", None))
    check("Jクライム8：攻撃する時に墓地のジョーカーズと入れ替わる",
          unit(g, 0, "n_mouja") is not None and "n_aisha" in g.P[0].grave)

    g = mk2(hand=["n_jenny"], mana=["vamilia"] * 4, board=[], ohand=["n_baiken"], omana=["klin"] * 6)
    g.tp = 0
    g.apply(("play", "n_jenny", 0))
    check("マッドネス：相手のターンに捨てられたバイケンが出る", unit(g, 1, "n_baiken") is not None)

    g = mk2(hand=["n_petpuppet"], mana=[], board=["n_jenny"], ohand=["fujin"])
    check("G・ゼロ：デスパペットがいればペット・パペットは0マナ", has(g, ("play", "n_petpuppet", 0)))
    g = mk2(hand=["n_petpuppet"], mana=[], board=[], ohand=["fujin"])
    check("G・ゼロ：デスパペットがいなければ唱えられない", not has(g, ("play", "n_petpuppet", 0)))

    # ---------------------------------------------------------------- コストの仕組み
    g = mk2(hand=["n_mizuha"], mana=["n_wadachie"] * 3, board=["n_wadachie"] * 4)
    check("シンパシー：ロスト・クルセイダー4体でミヅハは8コスト→マナ3枚では出せない",
          g.ccost(0, "n_mizuha", 3) == 8 and not has(g, ("play", "n_mizuha", 0)))
    g = mk2(hand=["n_mizuha"], mana=["n_wadachie"] * 3, board=["n_wadachie"] * 10)
    check("シンパシー：下限は2コスト", g.ccost(0, "n_mizuha", 3) == 2)

    g = mk2(hand=["n_orugeito"], mana=["klin"] * 3, board=[("n_wadachie", False), ("n_wadaebi", False),
                                                           ("n_fukafuchi", False)])
    check("ハイパーエナジー：コストの違う3体をタップして7→3以下", g.ccost(0, "n_orugeito", 3) <= 3)
    g.apply(("play", "n_orugeito", 0))
    check("ハイパーエナジー：支払いでクリーチャーがタップされる",
          sum(1 for u in g.P[0].board if u.tap and u.k != "n_orugeito") >= 2)

    g = mk2(hand=["n_tigawok"], mana=["klin"] * 5)
    g.P[0].drawn = 3
    check("ティガウォック：このターン3枚引いていればコスト4", g.ccost(0, "n_tigawok", 5) == 4)

    g = mk2(hand=["n_yuuki"], mana=["fujin", "kabocha"], oboard=["artel"])
    check("勇気の絆：手札がこれ1枚なら2マナで唱えられる", has(g, ("play", "n_yuuki", 0)))
    g = mk2(hand=["n_yuuki", "fujin"], mana=["fujin", "kabocha"], oboard=["artel"])
    check("勇気の絆：手札が2枚なら2マナでは唱えられない", not has(g, ("play", "n_yuuki", 0)))

    g = mk2(hand=["kuzen"], mana=["kuzen"] * 8, board=["vamilia"], grave=["kuzen"])
    check("フシギバース：墓地から、クリーチャーをマナに置いて召喚する手がある",
          any(a[0] == "x:kuzen" for a in g.legal()))
    g.apply(next(a for a in g.legal() if a[0] == "x:kuzen"))
    check("フシギバース：クーゼンが場に出て、身代わりがマナに行く",
          unit(g, 0, "kuzen") is not None and "vamilia" in g.P[0].mana)

    # ---------------------------------------------------------------- 出た時・離れた時
    g = mk2(hand=["n_rudezana", "fujin", "fujin", "fujin"], mana=["klin"] * 7, ohand=[],
            oboard=["klin", "artel", "jaouga"])
    g.apply(("play", "n_rudezana", 0))
    check("ルード・ザーナ：引いた後の手札の枚数（4）以下のコストの相手をすべて戻す",
          unit(g, 1, "klin") is None and unit(g, 1, "artel") is not None)

    g = mk2(board=["n_bolshack"], grave=["testa", "fujin", "klin"])
    u = unit(g, 0, "n_bolshack")
    check("ボルシャック・ドラゴン：攻撃中は墓地の火のカードぶん強くなる",
          g.power(0, u, True) == 6000 + 2000 and g.power(0, u) == 6000)

    g = mk2(board=["n_oort"], oboard=["klin"])
    g.leave(0, unit(g, 0, "n_oort"), "hand")
    check("オールトザウルス：離れた時にもパワー3000以下を破壊", unit(g, 1, "klin") is None)

    g = mk2(hand=["n_kernel"], mana=["chakra"] * 5, oboard=["jaouga"])
    g.apply(("play", "n_kernel", 0))
    ju = unit(g, 1, "jaouga")
    check("カーネル：選んだ相手は次の自分のターンのはじめまで攻撃もブロックもできない",
          any(f(g, 1, ju) for f in engine3.ATKLOCK) and not g.can_block(ju))

    g = mk2(board=["fheart"])
    before = len(g.P[0].hand)
    g.leave(0, unit(g, 0, "fheart"), "grave", destroy=True)
    check("フラワー・ハート：墓地に置かれた時に1枚引く", len(g.P[0].hand) == before + 1)

    # ---------------------------------------------------------------- 置き換え・常在
    g = mk2(board=["n_mizuha", "n_wadachie"], oboard=["klin"])
    g.leave(0, unit(g, 0, "n_wadachie"), "hand", by_opp=True)
    check("ミヅハ：自分のロスト・クルセイダーは破壊以外では離れない", unit(g, 0, "n_wadachie") is not None)
    g.leave(0, unit(g, 0, "n_wadachie"), "grave", by_opp=True, destroy=True)
    check("ミヅハ：破壊なら離れる", unit(g, 0, "n_wadachie") is None)

    g = mk2(board=["everlast", "zaze"], mana=["chakra"] * 5, sh=["fujin"] * 3)
    g.leave(0, unit(g, 0, "zaze"), "grave", by_opp=True, destroy=True)
    check("マナ武装5：マナに光5枚ならシールド2つを手札に加えて守る",
          unit(g, 0, "zaze") is not None and len(g.P[0].sh) == 1)

    g = mk2(hand=["tina"], mana=["klin"] * 3, board=["aroma"])
    check("シンカライズ：アロマの海幻の上に進化できる", has(g, ("play", "tina", 1)))

    g = mk2(hand=["n_wadakani"], mana=["klin"] * 3, oboard=[("n_toring", True)])
    g.apply(("play", "n_wadakani", 0))
    tu = unit(g, 1, "n_toring")
    check("ワダカニ：相手は出たターン攻撃できない（マッハファイターも止まる）",
          any(f(g, 1, tu) for f in engine3.ATKLOCK))

    g = mk2(board=["n_wadakani"], ohand=["fujin"] * 3)
    g.tp = 1
    u = unit(g, 0, "n_wadakani")
    g.P[0].hand = ["fujin"] * 3
    check("ワダカニ：相手のターンは手札1枚につき+1000", g.power(0, u) == 1000 + 3000)

    g = mk2(hand=["n_ningyo"], mana=["vamilia"] * 3)
    g.apply(("play", "n_ningyo", 0))
    g.tp = 1
    before = len(g.P[1].mana)
    g.ramp(1, 1)
    check("ニンギョ：相手のターンに相手が山札からマナに置くのを墓地に置き換える",
          len(g.P[1].mana) == before and g.P[1].grave)

    # ---------------------------------------------------------------- D・D・D・革命0トリガー・ストラトバッグ
    g = mk2(hand=[], mana=["shinten", "chakra", "klin", "kabocha", "esmel"], board=["fujin"], phase="A")
    g.apply(("atk", 0, "P", None))
    check("D・D・D：自分のクリーチャーの攻撃時にマナから心転地を唱える", "shinten" in g.P[0].grave)

    g = mk2(hand=["hangyaku"], mana=["klin"] * 6, sh=[], oboard=["jaouga"], deck=["fujin"] * 10 + ["klin"])
    g.tp = 1
    g.phase = "A"
    g.P[1].board = [U("jaouga")]
    g.ninja(0, g.P[1].board[0])
    check("革命0トリガー：シールド0で攻撃された時に叛逆の絆が出る",
          unit(g, 0, "hangyaku") is not None and unit(g, 0, "hangyaku").under == ["klin"])

    g = mk2(board=["strato"], mana=["klin", "fujin"], deck=["testa"] * 10)
    n0 = len(g.P[0].mana)
    g.take_mana(0, "klin")
    check("ストラトバッグ：マナから離れた時に1枚マナを増やす（各ターン1回）", len(g.P[0].mana) == n0)
    g.take_mana(0, "fujin")
    check("ストラトバッグ：同じターンに2回目はない", len(g.P[0].mana) == n0 - 1)
    g = mk2(board=["strato"], oboard=["klin"])
    g.tp = 1
    g.leave(1, unit(g, 1, "klin"), "grave", by_opp=True, destroy=True)
    check("ストラトバッグ：相手のカードが離れる時、かわりにマナゾーンへ", "klin" in g.P[1].mana)

    # ---------------------------------------------------------------- 超魂X・メクレイド
    g = mk2(board=["n_toring"], hand=["tenbin"], mana=["chakra"] * 4, phase="A")
    unit(g, 0, "n_toring").under = ["n_greatblue"]
    g.apply(("atk", 0, "P", None))
    check("超魂X（海幻）：攻撃する時に手札のコスト4以下のクリーチャーでないカードをただで使う",
          "tenbin" in g.P[0].grave)

    g = mk2(hand=["n_arkzeos"], mana=["testa"] * 5, deck=["fujin"] * 10 + ["n_buei"])
    g.apply(("play", "n_arkzeos", 0))
    check("アーマード・メクレイド5：山札の上からアーマードをただで出す", unit(g, 0, "n_buei") is not None)

    g = mk2(board=["n_arkzeos", "n_kottopi"])
    check("アークゼオス：ファイアー・バード1体につき+3000", g.power(0, unit(g, 0, "n_arkzeos")) == 8000)
    check("アークゼオス：パワード・ブレイカー", g.brk(0, unit(g, 0, "n_arkzeos")) == 2)

    # ---------------------------------------------------------------- 直した点の確認
    g = mk2(hand=["n_yari"], mana=["chakra"] * 8, oboard=[])
    g.apply(("play", "n_yari", 0))
    g.P[1].board.append(U("jaouga"))
    for f in engine3.ENTERWATCH:
        f(g, 1, g.P[1].board[-1])
    ju = g.P[1].board[-1]
    check("ミラダンテ槍：出た相手のクリーチャーは攻撃できない", any(f(g, 1, ju) for f in engine3.ATKLOCK))
    g.P[0].board = [u for u in g.P[0].board if u.k != "n_yari"]
    check("ミラダンテ槍：槍が場を離れても、かけた縛りは残る", any(f(g, 1, ju) for f in engine3.ATKLOCK))

    g = mk2(hand=["jaouga"], mana=["testa"], oboard=["n_ningyo", "kabocha"])
    g.P[0].hand.remove("jaouga")
    g.enter(0, "jaouga", "hand", False)          # かぼちゃうちゃうでマナに置き換えられる（手札から）
    check("ニンギョ：手札から出ようとしてマナに置き換えられる分は墓地にならない",
          "jaouga" in g.P[0].mana and "jaouga" not in g.P[0].grave)
    g = mk2(mana=["testa"], oboard=["n_ningyo", "kabocha"], deck=["jaouga"] + ["fujin"] * 10)
    g.enter(0, "jaouga", "deck", False)          # 山札から出ようとした分は墓地になる
    check("ニンギョ：手札以外から出ようとしてマナに置き換えられる分は墓地になる",
          "jaouga" in g.P[0].grave and "jaouga" not in g.P[0].mana)

    g = mk2(board=["n_mary"], ohand=["fujin", "artel"])
    before = len(g.P[0].hand)
    g.leave(0, unit(g, 0, "n_mary"), "grave", by_opp=True, destroy=True)
    check("メアリー・ジェニー：自分が離れた時にも誘発する（引いて相手に捨てさせる）",
          len(g.P[0].hand) == before + 1 and len(g.P[1].hand) == 1)

    # 革命0トリガー：出てきた進化元の能力で叛逆の絆が手札から動いても壊れないか
    g = mk2(hand=["hangyaku", "fujin"], mana=["klin"] * 8, sh=[], oboard=["jaouga"],
            deck=["fujin"] * 10 + ["eringi"])
    g.P[1].board = [U("jaouga")]
    ok = g.ninja(0, g.P[1].board[0])
    hu = unit(g, 0, "hangyaku")
    check("革命0トリガー：進化元の出た時能力で手札が動いても壊れない",
          hu is not None and hu.under == ["eringi"] and "hangyaku" not in g.P[0].hand)

    # ---------------------------------------------------------------- 後から足した差し込み口
    g = mk2(board=["e_korenkoko", "klin"], oboard=["jaouga"])
    g.tp = 1
    g.phase = "A"
    g.apply(("atk", 0, 1, None))                    # 相手がクリン・ラビィを攻撃 → コレンココが引き受ける
    check("ガードマン：攻撃先を引き受ける（引き受けた側がタップされる）",
          unit(g, 0, "klin") is not None and unit(g, 0, "e_korenkoko") is not None
          and unit(g, 0, "e_korenkoko").tap)

    g = mk2(sh=["e_hyouchuu"], grave=[], oboard=["jaouga"], osh=["fujin"] * 5)
    g.tp = 1
    g.break_sh(1, 1)
    check("条件つきS・トリガー：墓地に呪文がなければシールドから使えない", "e_hyouchuu" in g.P[0].hand)
    g = mk2(sh=["e_hyouchuu"], grave=["tenbin", "mirai"], oboard=["jaouga"])
    g.tp = 1
    g.break_sh(1, 1)
    check("条件つきS・トリガー：墓地に呪文が2枚あればシールドから使える", "e_hyouchuu" in g.P[0].grave)

    g = mk2(board=["e_crymax"], sh=[], mana=["vamilia"] * 3)
    g.P[0].sh = [("fujin", True), ("klin", True), ("artel", True)]
    g.win(1, "ダイレクトアタック")
    check("敗北の置き換え（CRYMAX ジャオウガ）：表向きのカード3枚を破壊して負けない", not g.over)

    g = mk2(board=["e_fumishuna"], ohand=["fujin", "artel"])
    before = len(g.P[0].hand)
    g.discard_random(1)
    check("手札を捨てた時：相手が捨てたら引く", len(g.P[0].hand) == before + 1)

    g = mk2(board=["e_dogiodo", "jaouga"], oboard=["klin"])
    tu = unit(g, 0, "jaouga")
    tu.sick = True
    check("マッハファイターを与える：他の多色クリーチャーは出たターンでも相手を攻撃できる",
          any(f(g, 0, tu) for f in engine3.MACHOK))

    g = mk2(board=["e_elborom", "teacher"])
    check("「攻撃できない」を無視する：アクア・ティーチャーが攻撃できるようになる",
          any(f(g, 0, unit(g, 0, "teacher")) for f in engine3.NOATKIGN))

    g = mk2(board=["n_toring"], oboard=[])
    g.P[0].board.append(U("e_blackzone"))
    g.P[0].board[-1].sick = False
    g.phase = "A"
    g.apply(("atk", 0, "P", None))
    u = unit(g, 0, "e_blackzone")
    check("S級侵略（バトルゾーンから）：攻撃しているコマンドの上に重なる",
          u is not None and u.under == ["n_toring"])

    # ---------------------------------------------------------------- スター進化と退化
    from envcards.env0 import STAR, own_loss, worst_own
    check("スター進化の登録：スター進化を持つ3枚すべてが STAR に入っている",
          {"e_momokingdamx", "e_onsoku", "e_katchikomi"} <= STAR)

    g = mk2(board=["n_toring"])
    u = unit(g, 0, "n_toring")
    g.P[0].board[0] = U("e_katchikomi")
    g.P[0].board[0].under = ["jaouga"]
    z = g.P[0].board[0]
    g.leave(0, z, "grave", destroy=True)
    nu = unit(g, 0, "jaouga")
    check("スター進化：離れる時、上のカチコミ入道だけが墓地に行き、下のジャオウガが残る",
          nu is not None and "e_katchikomi" in g.P[0].grave and unit(g, 0, "e_katchikomi") is None)

    g = mk2(board=["klin"])
    g.P[0].board[0] = U("e_onsoku")
    g.P[0].board[0].under = ["jaouga"]
    z = g.P[0].board[0]
    check("退化：スター進化は下の大きいクリーチャーが残るので、失う痛さが安く見える",
          own_loss(g, 0, z) < g.val(U("e_onsoku")) + 1)

    g = mk2(board=["klin"])
    g.P[0].board.append(U("e_onsoku"))
    g.P[0].board[-1].under = ["jaouga"]
    w = worst_own(g, 0)
    check("退化：自分のクリーチャーを失うなら、スター進化のほうを選ぶ（下が残るから）",
          w is not None and w.k == "e_onsoku")

    g = mk2(oboard=["klin"])
    g.P[1].board.append(U("e_onsoku"))
    g.P[1].board[-1].under = ["jaouga"]
    t = g.target(0)
    check("相手に退化をさせない：相手のスター進化より、普通のクリーチャーを選ぶ",
          t is not None and t.k != "e_onsoku")

    g = mk2(board=["klin"], phase="A")
    g.P[0].board[0] = U("e_universe")
    g.P[0].board[0].under = ["e_universe"]      # 下の最後の1枚がフェニックス
    g.P[0].board[0].sick = False
    g.apply(("atk", 0, "P", None))
    check("メテオバーン：下の最後の1枚がフェニックスなら勝つ", g.over and g.winner == 0)

    g = mk2(board=["klin"], phase="A")
    g.P[0].board[0] = U("e_universe")
    g.P[0].board[0].under = ["e_universe", "klin"]
    g.P[0].board[0].sick = False
    g.apply(("atk", 0, "P", None))
    check("メテオバーン：フェニックス以外を先に墓地に置き、まだ勝たない",
          not g.over and unit(g, 0, "e_universe").under == ["e_universe"])

    # ---------------------------------------------------------------- 新しく足した差し込み口
    import engine3 as E

    def _with(lst, fn, body):
        """差し込み口に一時的に登録して確かめる"""
        lst.append(fn)
        try:
            return body()
        finally:
            lst.remove(fn)

    got = []
    g = mk2()
    _with(E.SHIELDIN, lambda s, i, k, up: got.append((i, k, up)),
          lambda: g.add_shield(0, "fujin", False))
    check("SHIELDIN：カードがシールドゾーンに置かれた時に呼ばれる", got == [(0, "fujin", False)])

    got = []
    g = mk2(sh=["fujin"] * 3)
    _with(E.SHIELDOUT, lambda s, i, k, up, dest: got.append((i, k, dest)),
          lambda: g.break_sh(1, 2))
    check("SHIELDOUT：ブレイクで離れたカードごとに呼ばれる",
          len(got) == 2 and all(x[0] == 0 and x[2] == "break" for x in got))

    g = mk2(sh=["fujin"] * 4)
    _with(E.BREAKPRE, lambda s, ai, di, n: n - 1, lambda: g.break_sh(1, 3))
    check("BREAKPRE：ブレイクされる枚数を減らせる", len(g.P[0].sh) == 2)

    g = mk2(sh=["fujin"] * 3)
    _with(E.BREAKPRE, lambda s, ai, di, n: 0, lambda: g.break_sh(1, 2))
    check("BREAKPRE：0を返すと1枚も割られない", len(g.P[0].sh) == 3)

    got = []
    g = mk2(board=["klin"])
    u = unit(g, 0, "klin")
    _with(E.TAPWATCH, lambda s, i, z: got.append((i, z.k)), lambda: g.tap_cre(0, u))
    check("TAPWATCH：クリーチャーがタップした時に呼ばれる", got == [(0, "klin")])

    got = []
    g = mk2(board=["klin"])
    u = unit(g, 0, "klin")
    u.tap = True
    _with(E.TAPWATCH, lambda s, i, z: got.append(z.k), lambda: g.tap_cre(0, u))
    check("TAPWATCH：すでにタップしているなら呼ばれない", got == [])

    got = []
    g = mk2()
    g.P[0].deck = ["fujin", "klin"]
    _with(E.DRAWWATCH, lambda s, i, k: got.append((i, k)), lambda: g.draw(0, 2))
    check("DRAWWATCH：引いたカードごとに呼ばれる", got == [(0, "klin"), (0, "fujin")])

    g = mk2()
    g.P[0].deck = ["fujin"]
    g.put_zone(0, "klin", "decktop")
    check("put_zone の decktop：山札の上（次に引くカード）に置かれる", g.P[0].deck[-1] == "klin")

    got = []
    g = mk2(board=["n_toring"], oboard=["klin"], phase="A")
    E.BLOCKREACT["_t"] = lambda s, di, au, b: got.append((di, au.k, b.k))
    try:
        g.P[1].board[0].c.blocker  # ブロッカーでなければ呼ばれないので、直接 ninja_block を見る
        g.ninja_block(1, g.P[0].board[0], g.P[1].board[0])
    finally:
        del E.BLOCKREACT["_t"]
    check("BLOCKREACT：手札にそのカードが無ければ呼ばれない", got == [])

    got = []
    g = mk2(board=["n_toring"], oboard=["klin"], ohand=["tensai"])
    E.BLOCKREACT["tensai"] = lambda s, di, au, b: got.append((di, au.k, b.k))
    try:
        g.ninja_block(1, g.P[0].board[0], g.P[1].board[0])
    finally:
        del E.BLOCKREACT["tensai"]
    check("BLOCKREACT：手札にあれば、攻撃側とブロックしたカードを受け取る",
          got == [(1, "n_toring", "klin")])

    g = mk2(board=["klin"])
    u = unit(g, 0, "klin")
    u.pw += 3000
    before = g.power(0, u)
    g.end_turn()
    check("「このターンだけのパワー増減」はターンの終わりに戻る（u.pw）",
          before == 3000 + BY_KEY["klin"].power and g.power(0, unit(g, 0, "klin")) == BY_KEY["klin"].power)

    E.HYPER_BRK["klin"] = 3
    E.HYPER_POW.setdefault("klin", 0)
    g = mk2(board=["klin"])
    u = unit(g, 0, "klin")
    u.hyper = True
    b = g.brk(0, u)
    del E.HYPER_BRK["klin"]
    check("HYPER_BRK：ハイパーモード中のブレイク数を指定できる", b == 3)

    got = []
    g = mk2()
    _with(E.MANAIN, lambda s, i, k, src: got.append((i, k, src)),
          lambda: g.add_mana(0, "fujin", src="other"))
    check("MANAIN：自分のマナゾーンにカードが置かれた時に呼ばれる（元のゾーンも分かる）",
          got == [(0, "fujin", "other")])

    got = []
    # 相手のシールドが0で、プレイヤーへの攻撃＝止めないと負けるので、エンジンは必ずブロックする
    g = mk2(board=["n_toring"], oboard=["teacher"], osh=[], phase="A")
    u = unit(g, 0, "n_toring")
    u.sick = False
    g.P[1].board[0].sick = False
    _with(E.BLOCKWATCH, lambda s, i, a, b: got.append((i, a.k, b.k)),
          lambda: g.apply(("atk", 0, "P", None)))
    check("BLOCKWATCH：ブロックされた時、攻撃側に攻撃者とブロッカーが渡る",
          got == [(0, "n_toring", "teacher")])

    got = []
    g = mk2(oboard=["klin", "artel"])
    t = _with(E.CHOSENWATCH, lambda s, own, u, by: got.append((own, u.k, by)),
              lambda: g.target(0))
    check("CHOSENWATCH：相手に選ばれた1体にだけ呼ばれる",
          t is not None and got == [(1, t.k, 0)])

    g = mk2(oboard=["klin", "artel"])
    n = _with(E.CHOSENWATCH, lambda s, own, u, by: None, lambda: len(g.P[1].board))
    check("CHOSENWATCH：候補を数えるだけでは呼ばれない（選ばれた1体だけ）", n == 2)

    g = mk2(board=["n_toring"], osh=["fujin"] * 3, phase="A")
    unit(g, 0, "n_toring").sick = False
    base = [a[0] for a in g.legal()]
    g2 = mk2(board=["n_toring"], osh=["fujin"] * 3, phase="A")
    unit(g2, 0, "n_toring").sick = False
    forced = _with(E.MUSTATK, lambda s, i: True, lambda: [a[0] for a in g2.legal()])
    check("MUSTATK：攻撃できるクリーチャーがいる間は「ターンを終える」が出ない",
          "end" in base and "end" not in forced and "atk" in forced)

    g = mk2(phase="A")
    forced = _with(E.MUSTATK, lambda s, i: True, lambda: [a[0] for a in g.legal()])
    check("MUSTATK：攻撃できるクリーチャーがいなければターンを終えられる", forced == ["end"])

    from envcards.env0 import w_command_seal
    g = mk2(oboard=["artel"])
    z = unit(g, 1, "artel")
    g.seal(1, z, 1)                               # 相手のクリーチャーに封印1つ
    g.P[0].board.append(U("e_dedodamu"))          # 自分のコマンド（闇を含む）が出た
    g.P[0].board[-1].sick = False
    w_command_seal(g, 0, g.P[0].board[-1])
    check("コマンドが出た時に外せるのは自分の封印だけ（相手の封印は外さない）",
          len(g.P[1].sealed) == 1)

    g = mk2(board=["artel"])
    z = unit(g, 0, "artel")
    g.seal(0, z, 1)                               # 自分のクリーチャーに封印1つ
    g.P[0].board.append(U("e_dedodamu"))
    g.P[0].board[-1].sick = False
    w_command_seal(g, 0, g.P[0].board[-1])
    check("コマンドが出た時、自分の封印は外れる", len(g.P[0].sealed) == 0)

    # ---------------------------------------------------------------- 第4版で足した差し込み口
    g = mk2(sh=["fujin", "klin", "artel"])
    r = g.take_shield(0, 1, "hand")
    check("take_shield：シールド1枚を手札へ移せる（ブレイク以外の経路）",
          r == ("klin", False, "hand") and len(g.P[0].sh) == 2 and "klin" in g.P[0].hand)

    E.SHIELDDEST["klin"] = lambda s, i, k, up, dest: "grave"
    g = mk2(sh=["fujin", "klin"])
    try:
        g.take_shield(0, 1, "hand")
    finally:
        del E.SHIELDDEST["klin"]
    check("SHIELDDEST：シールド・ゴー（手札のかわりに墓地へ）",
          "klin" in g.P[0].grave and "klin" not in g.P[0].hand)

    E.SHIELDDEST["klin"] = lambda s, i, k, up, dest: "grave"
    g = mk2(sh=["klin"] * 3)
    try:
        g.break_sh(1, 2)
    finally:
        del E.SHIELDDEST["klin"]
    check("SHIELDDEST：ブレイクされた時も行き先が変わる（1枚ごとに決まる）",
          g.P[0].grave.count("klin") == 2 and g.P[0].hand.count("klin") == 0)

    got = []
    E.SHIELDCAST["klin"] = lambda s, i, k, nsh: got.append(nsh) or True
    g = mk2(sh=["klin"])
    try:
        g.break_sh(1, 1)
    finally:
        del E.SHIELDCAST["klin"]
    check("SHIELDCAST：シールドから手札に加える時、その時のシールドの枚数つきで呼ばれる",
          got == [0])

    g = mk2(sh=["fujin", "artel", "klin"])     # ブレイクは後ろの裏向きから選ばれる
    E.SHIELDCAST["klin"] = lambda s, i, k, nsh: got.append(nsh) or True
    got.clear()
    try:
        g.break_sh(1, 1)
    finally:
        del E.SHIELDCAST["klin"]
    check("SHIELDCAST：シールドが残っていれば、その枚数が渡る", got == [2])

    # n_toring（4000）が klin（2000）を攻撃 → 差し替えなければ klin が死ぬ。
    # artel（6000）に差し替えると、逆に攻撃側の n_toring が死ぬ。
    g = mk2(board=["n_toring"], oboard=["klin", "artel"])
    au, du = unit(g, 0, "n_toring"), unit(g, 1, "klin")
    other = unit(g, 1, "artel")
    _with(E.BATTLESWAP, lambda s, di, d_, ai, a_: other,
          lambda: g.battle(0, au, 1, du))
    check("BATTLESWAP：守る側がバトルする相手を差し替えられる（スーパーガードマン）",
          unit(g, 1, "klin") is not None and unit(g, 1, "artel") is not None
          and unit(g, 0, "n_toring") is None)

    g = mk2(board=["n_toring"], oboard=["klin", "artel"])
    au, du = unit(g, 0, "n_toring"), unit(g, 1, "klin")
    g.battle(0, au, 1, du)
    check("差し替えなければ、攻撃された側（クリン）が死ぬ",
          unit(g, 1, "klin") is None and unit(g, 0, "n_toring") is not None)

    got = []
    g = mk2()
    _with(E.TURNSTART, lambda s, i: got.append(("start", i)), lambda: g.start_turn())
    check("TURNSTART：バトルゾーンに何もなくてもターンのはじめに呼ばれる", got == [("start", g.tp)])

    got = []
    g = mk2()
    _with(E.TENDP, lambda s, i: got.append(i), lambda: g.end_turn())
    check("TENDP：バトルゾーンに何もなくてもターンの終わりに両者について呼ばれる",
          sorted(got) == [0, 1])

    E.EVOSRC["artel"] = lambda s, i: ("hand", "klin") if "klin" in s.P[i].hand else None
    try:
        g = mk2(hand=["artel"], mana=["artel"] * 6)
        acts = [a for a in g.legal_main(0) if a[0] == "play" and a[1] == "artel"]
        check("EVOSRC：手札に進化元がなければ、そのカードは出せる手にならない", not acts)
        g = mk2(hand=["artel", "klin"], mana=["artel"] * 6)
        acts = [a for a in g.legal_main(0) if a[0] == "play" and a[1] == "artel"]
        check("EVOSRC：手札に進化元があれば出せる", acts == [("play", "artel", 1)])
        g = mk2(hand=["artel", "klin"], mana=["artel"] * 6)
        g.apply(("play", "artel", 1))
        u = unit(g, 0, "artel")
        check("EVOSRC：手札進化で、進化元が手札から下に積まれる",
              u is not None and u.under == ["klin"] and "klin" not in g.P[0].hand)
    finally:
        del E.EVOSRC["artel"]

    g = mk2(oboard=["douki", "artel"])
    check("MUSTPICK（同期の妖精）：条件が無ければ必ず選ばされる", g.target(0).k == "douki")
    check("MUSTPICK（同期の妖精）：条件に合わなければ選ばされない（「可能なら」の意味）",
          g.target(0, lambda z: g.power(1, z) >= 5000).k == "artel")

    # ---------------------------------------------------------------- 手を数えるだけで盤面が壊れないこと
    fired = []
    g = mk2(hand=["takkyu"], mana=["takkyu"] * 8, board=["jaouga"], oboard=["artel"])
    _with(E.CHOSENWATCH, lambda s, own, u, by: fired.append(u.k), lambda: g.legal())
    check("打てる手を数えるだけでは「相手に選ばれた時」が誘発しない（盤面を壊さない）", fired == [])

    fired = []
    g = mk2(oboard=["artel"])
    t = _with(E.CHOSENWATCH, lambda s, own, u, by: fired.append(u.k), lambda: g.target(0))
    check("実際に選んだ時は誘発する", fired == ["artel"] and t is not None)

    g = mk2(hand=["takkyu"], mana=["takkyu"] * 8, board=["jaouga"], oboard=["artel"])
    g.legal()
    check("手を数えた後、数えている印は残らない", g.dry == 0)

    bad = [n for n, c in OK if not c]
    print(f"\n{len(OK) - len(bad)}/{len(OK)} 通過" + ("" if not bad else "　失敗：" + "、".join(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
