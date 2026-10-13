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
