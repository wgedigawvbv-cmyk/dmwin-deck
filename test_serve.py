#!/usr/bin/env python3
"""スマホ用サーバー（serve.py）の確認

  ブラウザを使わずに、サーバーに直接要求を出して確かめる。
  python test_serve.py
"""
import json
import os
import shutil
import socket
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import serve

OK = []


def check(name, cond):
    OK.append((name, bool(cond)))
    print(("○ " if cond else "× ") + name)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def req(url, body=None, key=None, expect=200):
    from urllib.parse import quote
    if key is not None:
        url += ("&" if "?" in url else "?") + "k=" + quote(key, safe="")
    url = quote(url, safe=":/?&=%")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(url, data=data,
                               headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(r, timeout=30) as f:
            return f.status, f.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def main():
    import goals
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    serve.CFG["token"] = "testtoken123"
    serve.CFG["procs"] = 1
    # 本物の mygoals.json と decks\ を壊さないように、よけておく
    bak_goals = goals.MINE + ".testbak"
    bak_decks = serve.DECKDIR + "_testbak"
    had_goals = os.path.exists(goals.MINE)
    had_decks = os.path.isdir(serve.DECKDIR)
    if had_goals:
        shutil.copy2(goals.MINE, bak_goals)
    if had_decks:
        shutil.move(serve.DECKDIR, bak_decks)

    srv = ThreadingHTTPServer(("127.0.0.1", port), serve.H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        # ---------------------------------------------------------- 合言葉
        st, _b = req(base + "/api/ping", expect=403)
        check("合言葉が無い要求は断る", st == 403)
        st, _b = req(base + "/api/ping", key="ちがう")
        check("合言葉が違う要求は断る", st == 403)
        st, b = req(base + "/api/ping", key="testtoken123")
        j = json.loads(b)
        check("合言葉が合えば答える", st == 200 and j["ok"])
        check("カードの枚数を返す", j["cards"] > 500)

        # ---------------------------------------------------------- 画面
        st, b = req(base + "/", key="testtoken123")
        check("画面を配る", st == 200 and "<!doctype html>" in b)
        check("スマホ向けの宣言が入っている（これが無いと携帯で豆粒になる）",
              'name="viewport"' in b and "width=device-width" in b)
        check("サーバーから配られた印が入っている", "__SERVER__" in b)
        check("合言葉が画面に埋め込まれている（スマホでそのまま使える）", "testtoken123" in b)

        # ---------------------------------------------------------- デッキの検査
        st, b = req(base + "/api/run", {"deck": {"そんなカードはない": 4}}, "testtoken123")
        check("知らないカードは断る", st == 400 and "知らないカード" in b)
        st, b = req(base + "/api/run", {"deck": {}}, "testtoken123")
        check("空のデッキは断る", st == 400)
        st, b = req(base + "/api/run", {"deck": {"ヤッタレマン": 9}}, "testtoken123")
        check("5枚以上のカードは断る", st == 400)

        # ---------------------------------------------------------- 一人回し
        import decks8
        from cards3 import BY_KEY
        nm = next(n for n in sorted(decks8.DECKS8) if "赤零" in decks8.short(n))
        deck = {BY_KEY[k].name: v for k, v in decks8.DECKS8[nm].items()}
        goal = {"name": "テスト", "goal_at": "殴れる形",
                "parts": [{"name": "並べる", "when": {"creatures_at_least": 2}},
                          {"name": "殴れる形", "when": {"breaks_at_least": 6}},
                          {"name": "勝つ", "when": {"win": True}}]}
        st, b = req(base + "/api/run",
                    {"deck": deck, "name": "赤零ジョーカーズ", "games": 60, "pilot": "greedy",
                     "first": "both", "wall": "blank", "wall_shields": 5,
                     "goal": goal, "goal_at": "殴れる形"}, "testtoken123")
        check("一人回しを始められる", st == 200 and "job" in b)
        jid = json.loads(b)["job"]
        res, t0 = None, time.time()
        while time.time() - t0 < 90:
            st, b = req(base + "/api/job?id=" + jid, key="testtoken123")
            j = json.loads(b)
            if j["state"] == "done":
                res = j["result"]
                break
            if j["state"] == "error":
                print("   error:", j["error"])
                break
            time.sleep(0.3)
        check("終わって結果が返る", res is not None)
        if res:
            check("戦数が合っている", res["games"] == 60)
            check("ゴールのまとめが入っている", res.get("goal") and res["goal"]["name"] == "テスト")
            check("ゴール地点が指定どおり", res["goal"]["at"] == "殴れる形")
            check("部品ごとのまとめが入っている", len(res["goal"]["parts"]) == 3)
            check("殴り切りのまとめが入っている", res["kill"].get("n", 0) > 0)
            check("札ごとのまとめが入っている", len(res["cards"]) == len(decks8.DECKS8[nm]))
            check("先攻後攻の両方がある", set(res["by_first"]) == {"先攻", "後攻"})
        st, b = req(base + "/api/job?id=ないしごと", key="testtoken123")
        check("知らない仕事は404", st == 404)

        # ---------------------------------------------------------- 保存
        st, b = req(base + "/api/save-deck",
                    {"name": "テスト用デッキ", "text": "4 ヤッタレマン\n"}, "testtoken123")
        check("デッキを保存できる", st == 200)
        check("保存先はこのフォルダの decks\\ の中", os.path.exists(
            os.path.join(serve.DECKDIR, "テスト用デッキ.txt")))
        st, b = req(base + "/api/save-deck",
                    {"name": "../../abunai", "text": "4 ヤッタレマン\n"}, "testtoken123")
        check("あぶない名前でも decks\\ の外には書かない",
              st == 200 and not os.path.exists(os.path.join(serve.HERE, "..", "abunai.txt")))
        st, b = req(base + "/api/saved", key="testtoken123")
        check("保存したデッキを読み出せる", "テスト用デッキ" in b)
        st, b = req(base + "/api/save-goals",
                    {"goals": [{"name": "保存テスト", "when": {"mana_at_least": 5}}]}, "testtoken123")
        check("ゴールを保存できる", st == 200)
        check("保存したゴールが読み込める",
              any(g["name"] == "保存テスト" for g in goals.load()))
        st, b = req(base + "/api/save-goals",
                    {"goals": [{"name": "だめ", "when": {"そんな条件": 1}}]}, "testtoken123")
        check("書き方のおかしいゴールは断る（保存前に確かめている）", st == 400)
        st, b = req(base + "/api/save-goals", {"goals": []}, "testtoken123")
        check("空のゴールは断る", st == 400)
        # ---------------------------------------------------------------- 文章で書いたゴールを読む
        st, body = req(base + "/api/parse-goal",
                       {"text": "ユニバースが表に出る\nユニバースで特殊勝利する", "deck": []},
                       key="testtoken123")
        r = json.loads(body) if st == 200 else {}
        check("文章からゴールを作る道がサーバーにもある", st == 200 and bool(r.get("goal")))
        check("1行＝1部品になる", len((r.get("goal") or {}).get("parts", [])) == 2)
        check("読み返しが返る", all(n.get("read") for n in r.get("notes", [])))
        st2, b2 = req(base + "/api/goal-text", {"goal": r["goal"]}, key="testtoken123")
        r2 = json.loads(b2) if st2 == 200 else {}
        check("ゴールを文章に戻す道もある", st2 == 200 and bool(r2.get("text")))
        st3, b3 = req(base + "/api/parse-goal", {"text": "そらをとぶピカチュウを出す", "deck": []},
                      key="testtoken123")
        r3 = json.loads(b3) if st3 == 200 else {}
        check("読めない行は、読めなかったと返す（黙って捨てない）",
              st3 == 200 and any((not n["ok"]) or n.get("miss") for n in r3.get("notes", [])))

        st, _b = req(base + "/api/nothing", key="testtoken123")
        check("知らない道は404", st == 404)
    finally:
        srv.shutdown()
        srv.server_close()
        shutil.rmtree(serve.DECKDIR, ignore_errors=True)
        if had_decks:
            shutil.move(bak_decks, serve.DECKDIR)
        if had_goals:
            shutil.move(bak_goals, goals.MINE)
        elif os.path.exists(goals.MINE):
            os.remove(goals.MINE)


    bad = [n for n, c in OK if not c]
    print(f"\n{len(OK) - len(bad)}/{len(OK)} 通過" + ("" if not bad else "　失敗：" + "、".join(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
