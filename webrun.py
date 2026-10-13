#!/usr/bin/env python3
r"""ブラウザの中で動くPython（Pyodide）から一人回しを呼ぶための入口

  ウェブ版（webbuild.py が作る web\ フォルダ）は、サーバーを置かない。
  **計算はその端末のブラウザの中で、このPythonがそのまま走る**。
  だから数字はPCで回したものと同じ（通る道は runner.py の1本きり）。

  JavaScript 側からはこの2つだけを呼ぶ。
    ready()                 カードを読み込む（はじめの1回。数秒かかる）
    go(要求のJSON, 進み具合) 回して、まとめのJSONを返す

  ブラウザの中では複数のコアを使えないので、runner.PROCS は 1 のまま。
  そのぶん遅い（PCの2〜4倍）。戦数を控えめにするか、待つこと。
"""
import json

import runner


def ready():
    """カードとデッキを読み込む。はじめの1回だけ時間がかかるので、先に呼んでおく"""
    import decks8
    import goals                      # noqa: F401
    import solo                       # noqa: F401
    from cards3 import BY_KEY
    return json.dumps({"cards": len(BY_KEY), "decks": len(decks8.DECKS8)})


def go(req_json, progress=None):
    """要求（JSONの文字列）を回して、まとめ（JSONの文字列）を返す。

    progress は JavaScript の関数。(いくつ終わったか, 全部で何戦) を受け取る。"""
    o = runner.prepare(json.loads(req_json))

    def p(done, total):
        if progress is not None:
            progress(done, total)
    return json.dumps(runner.run(o, p), ensure_ascii=False)


def parse_goal_text(text, deck_json="[]"):
    """文章で書いたゴールを読む。画面の「文章で書く」欄が1文字ごとに呼ぶ。

    返すのは {"goal": ゴールの辞書, "notes": 読み取りの記録}。
    読めなかった行も notes に入れて返す（黙って捨てない）。"""
    import goaltext
    try:
        deck = json.loads(deck_json) if deck_json else []
    except Exception:                               # noqa: BLE001
        deck = []
    goal, notes = goaltext.parse(text, deck or None)
    return json.dumps({"goal": goal, "notes": notes}, ensure_ascii=False)


def goal_to_text(goal_json):
    """ゴールの辞書を文章に戻す（画面で「いまのゴールを文章にする」を押した時）"""
    import goaltext
    try:
        return goaltext.explain(json.loads(goal_json))
    except Exception as e:                          # noqa: BLE001
        return ""


def check_goal(goal_json):
    """ゴールの書き方だけを確かめる（回さない）。おかしければ理由を返す"""
    import goals
    try:
        g = json.loads(goal_json)
        for _nm, w in goals.parts_of(g):
            goals._one(w)
        goals.goal_when(g)
        return ""
    except SystemExit as e:
        return str(e)
    except Exception as e:                          # noqa: BLE001
        return str(e)
