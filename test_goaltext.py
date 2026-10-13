#!/usr/bin/env python3
"""ゴールを文章で書く仕組み（goaltext.py）の確認

  python test_goaltext.py

  ここで見るのは2つ。
    1. 書いた文が、**狙いどおりの条件**になるか（CASES）
    2. 手で書いた見本のゴール（goals.json）と同じ条件に、文章からも行けるか（HAND）
  読み違えは必ず起きるので、**読み残しを黙って捨てていないか**も毎回見る。
"""
import json

import envcards  # noqa: F401
import goaltext

OK = []


def check(name, cond):
    OK.append((name, bool(cond)))
    print(("○ " if cond else "× ") + name)


# (書いた文, 期待する条件)
CASES = [
    ("ヤッタレマンが場にいる", {"in_play": "ヤッタレマン"}),
    ("ヤッタレマンを2体並べる", {"in_play": "ヤッタレマン", "count": 2}),
    ("ユニバースが表に出る", {"entered": "究極銀河ユニバース"}),
    ("ユニバースを下に仕込む", {"in_play_or_under": "究極銀河ユニバース"}),
    ("一度でもユニバースを下に仕込む", {"ever": {"in_play_or_under": "究極銀河ユニバース"}}),
    ("フェアリー・ライフを使う", {"played": "フェアリー・ライフ"}),
    ("デドダムが墓地にある", {"in_grave": "天災 デドダム"}),
    ("相手の場にとこしえの超人がいる", {"opp_in_play": "とこしえの超人"}),
    ("ユニバースで特殊勝利する", {"special_win": "究極銀河ユニバース"}),
    ("特殊勝利する", {"special_win": True}),
    ("ダイレクトアタックで勝つ", {"direct_attack": True}),
    ("勝つ", {"win": True}),
    ("山札切れにする", {"opp_deck_at_most": 0}),
    ("クリーチャーを5体並べる", {"creatures_at_least": 5}),
    ("進化元を3体並べる", {"creatures_at_least": 3}),
    ("三体並べる", {"creatures_at_least": 3}),
    ("すぐ殴れるクリーチャーが3体以上", {"untapped_at_least": 3}),
    ("打点が6点以上", {"breaks_at_least": 6}),
    ("6打点", {"breaks_at_least": 6}),
    ("パワー合計が20000以上", {"total_power_at_least": 20000}),
    ("マナが8枚以上", {"mana_at_least": 8}),
    ("8マナためる", {"mana_at_least": 8}),
    ("手札を7枚以上", {"hand_at_least": 7}),
    ("相手の盾を割り切る", {"opp_shields_at_most": 0}),
    ("相手の盾が2枚以下", {"opp_shields_at_most": 2}),
    ("自分の盾を3枚以上", {"my_shields_at_least": 3}),
    ("自分の盾を3枚以下", {"my_shields_at_most": 3}),
    ("山札を残り3枚まで削る", {"my_deck_at_most": 3}),
    ("相手のクリーチャーを0体以下", {"opp_creatures_at_most": 0}),
    ("相手の場を空にする", {"opp_creatures_at_most": 0}),
    # まとめ役
    ("5ターン目までに勝つ", {"all": [{"turn_at_most": 5}, {"win": True}]}),
    ("相手の場を空にして8マナためる",
     {"all": [{"opp_creatures_at_most": 0}, {"mana_at_least": 8}]}),
    ("メイ様が場にいてクリーチャーが7体以上",
     {"all": [{"in_play": "お目覚めメイ様"}, {"creatures_at_least": 7}]}),
    ("ヤッタレマンまたはジャスミンの地版が場にいる",
     {"any": [{"in_play": "ヤッタレマン"}, {"in_play": "ジャスミンの地版"}]}),
    ("とこしえの超人がいない", {"not": {"in_play": "とこしえの超人"}}),
    ("とこしえの超人を使わずに勝つ",
     {"all": [{"not": {"played": "とこしえの超人"}}, {"win": True}]}),
]


def main():
    cards = goaltext.Cards()

    # ---------------------------------------------------------------- 1. 文 → 条件
    bad = []
    for text, want in CASES:
        got, miss = goaltext.parse_line(text, cards)
        same = json.dumps(got, ensure_ascii=False, sort_keys=True) == \
            json.dumps(want, ensure_ascii=False, sort_keys=True)
        if not same:
            bad.append((text, want, got))
        if miss:
            bad.append((text, "読み残しなし", f"読み残し {miss}"))
    for text, want, got in bad:
        print(f"   × 『{text}』")
        print(f"       ほしい：{want}")
        print(f"       出たの：{got}")
    check(f"書いた文が狙いどおりの条件になる（{len(CASES)}通り）", not bad)

    # ---------------------------------------------------------------- 2. 読み返し
    for text, want in CASES:
        got, _ = goaltext.parse_line(text, cards)
        s = goaltext.say(got)
        if not s or s.startswith("（") or "=" in s:
            check(f"読み返しが日本語になる：{text}", False)
            break
    else:
        check("どの条件も日本語に戻せる（読み返しが出せる）", True)

    # ---------------------------------------------------------------- 3. 読めない文は黙って捨てない
    got, miss = goaltext.parse_line("そらをとぶピカチュウが光臨する", cards)
    check("読めない文は、読めなかったと返す", got is None or bool(miss))
    got2, miss2 = goaltext.parse_line("存在しないカード名を出す", cards)
    check("当たらないカード名は、どの言葉が当たらなかったかを返す",
          got2 is None or any(m[0] for m in miss2))

    # ---------------------------------------------------------------- 4. 文章ぜんぶ
    text = ("モモキングダムXが出る\n"
            "一度でもユニバースを下に仕込む\n"
            "ユニバースが表に出る\n"
            "ユニバースで特殊勝利する")
    goal, notes = goaltext.parse(text, name="ためし")
    check("1行＝1部品になる", len(goal["parts"]) == 4)
    check("最後の部品がゴール地点になる", goal["goal_at"] == goal["parts"][-1]["name"])
    check("どの行も読めた", all(n["ok"] for n in notes))
    import goals
    try:
        for _nm, w in goals.parts_of(goal):
            goals._one(w)
        okbuild = True
    except SystemExit:
        okbuild = False
    check("組み立てたゴールが goals.py で実際に使える形になっている", okbuild)

    # ---------------------------------------------------------------- 5. 見本のゴールを文章にして読み直す
    tab = goals.load()
    if isinstance(tab, tuple):
        tab = tab[0]
    items = tab.items() if isinstance(tab, dict) else [(g.get("name"), g) for g in tab]
    n_exp = 0
    for nm, g in items:
        if goaltext.explain(g).strip():
            n_exp += 1
    check(f"見本のゴールを全部そのまま文章にできる（{n_exp}個）", n_exp >= 5)

    # 文章にしたものを読み直すと、同じ条件に戻る部品が十分あること
    same = tot = 0
    for nm, g in items:
        for p in (g.get("parts") or []):
            tot += 1
            back, _ = goaltext.parse_line(goaltext.say(p["when"]), cards)
            if json.dumps(back, ensure_ascii=False, sort_keys=True) == \
               json.dumps(p["when"], ensure_ascii=False, sort_keys=True):
                same += 1
    print(f"   （読み返しの文をもう一度読ませると {same}/{tot} が同じ条件に戻る）")
    check("読み返しの文を読み直して、半分以上が同じ条件に戻る", tot == 0 or same * 2 >= tot)

    bad2 = [n for n, c in OK if not c]
    print(f"\n{len(OK) - len(bad2)}/{len(OK)} 通過" + ("" if not bad2 else "　失敗：" + "、".join(bad2)))
    return 1 if bad2 else 0


if __name__ == "__main__":
    raise SystemExit(main())
