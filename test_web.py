#!/usr/bin/env python3
"""ウェブ版（webbuild.py が作る web\\ フォルダ）の確認

  ブラウザを立てずに、できあがったファイルの中身だけを確かめる。
  python test_web.py
"""
import json
import os
import shutil
import tempfile
import zipfile

import webbuild

OK = []


def check(name, cond):
    OK.append((name, bool(cond)))
    print(("○ " if cond else "× ") + name)


def main():
    out = tempfile.mkdtemp(prefix="dmweb")
    try:
        r = webbuild.build(out, None, use_cdn=True)
        idx = os.path.join(out, "index.html")
        html = open(idx, encoding="utf-8").read()
        check("index.html ができる", os.path.exists(idx))
        check("スマホ向けの宣言が入っている（無いと携帯で豆粒になる）",
              'name="viewport"' in html and "width=device-width" in html)
        check("外側のHTMLがある（ブラウザでそのまま開ける）", html.lstrip().startswith("<!doctype html>"))
        check("ウェブ版の印が入っている", "__WEB__" in html)
        check("サーバー版の印は入っていない（ウェブ版はサーバーに話しかけない）",
              "window.__SERVER__={" not in html.replace(" ", ""))
        check("カードのデータが埋め込まれている（開いた瞬間からデッキを組める）",
              '"cards":[' in html.replace(" ", "") and len(html) > 200000)
        check("ゴールの条件の表が入っている", '"conds"' in html.replace(" ", ""))
        check("SNSに貼ったときの見え方（OGP）が入っている",
              'property="og:title"' in html and 'name="description"' in html)
        check("非公式であることの注記が入っている（公開するなら必須）",
              "非公式" in html and "タカラトミー" in html)
        check("site.json の設定が画面に渡っている", '"site":{' in html.replace(" ", ""))
        import deckui as _d
        st = _d.site()
        check("site.json が読める", st["name"] and st["unofficial"])
        check("既定では支援リンクも広告も入れない（自分で決めるもの）",
              not st["support"] and not st["ad_html"])

        w = open(os.path.join(out, "worker.js"), encoding="utf-8").read()
        check("worker.js ができる", bool(w))
        check("--cdn なら Pyodide を CDN から読む", webbuild.CDN in w)
        check("worker は dmsrc.zip を読む", "dmsrc.zip" in w)
        check("worker は webrun を呼ぶ", "webrun.go" in w and "webrun.ready" in w)

        zp = os.path.join(out, "dmsrc.zip")
        with zipfile.ZipFile(zp) as z:
            names = set(z.namelist())
        need = ["engine3.py", "cards3.py", "solo.py", "goals.py", "runner.py", "webrun.py",
                "decks8.py", "roles3.py", "archetypes.py", "playable3.py", "envreg.py",
                "cardfetch.py", "netcards.py", "envcards/__init__.py", "envcards/env0.py",
                "env_lists.json", "deck_jokers.json", "goals.json"]
        miss = [n for n in need if n not in names]
        check("回すのに要るPythonとデータが全部入っている（足りない：" + "、".join(miss) + "）", not miss)
        nenv = sum(1 for n in names if n.startswith("envcards/env") and n.endswith(".py"))
        import glob
        have = len(glob.glob(os.path.join(webbuild.HERE, "envcards", "env*.py")))
        check(f"カードの実装が全部入っている（envcards {nenv}/{have}個）", nenv == have)
        check("回すのに要らない大きなものは入れていない",
              "cards.md" not in names and not any(n.startswith("runs8") for n in names))
        check("dmsrc.zip は 2MB 未満（通信を軽くする）", os.path.getsize(zp) < 2 << 20)

        check("置き方の手引きがある", os.path.exists(os.path.join(out, "README.txt")))
        check("--cdn では Pyodide を同梱しない", not os.path.isdir(os.path.join(out, "pyodide")))

        # 同梱する指定で、ファイルが足りなければ分かる形で止まる
        try:
            webbuild.build(out, tempfile.mkdtemp(prefix="nopyo"), use_cdn=False)
            check("Pyodide が足りなければ分かる形で止まる", False)
        except SystemExit as e:
            check("Pyodide が足りなければ分かる形で止まる", "足りません" in str(e))

        # 本物の Pyodide があるなら、同梱の形も確かめる
        cand = [os.path.join(webbuild.HERE, "node_modules", "pyodide"),
                os.path.join(webbuild.HERE, "pyodide")]
        src = next((c for c in cand if os.path.isdir(c)), None)
        if src:
            out2 = tempfile.mkdtemp(prefix="dmweb2")
            try:
                r2 = webbuild.build(out2, src, use_cdn=False)
                check("同梱すると Pyodide のファイルが揃う", r2["pyo"] == len(webbuild.PYO_FILES))
                w2 = open(os.path.join(out2, "worker.js"), encoding="utf-8").read()
                check("同梱版は自分のフォルダから読む（CDNを見に行かない）",
                      '"pyodide/"' in w2 and webbuild.CDN not in w2)
                check("Pyodide 本体（wasm）が入っている",
                      os.path.getsize(os.path.join(out2, "pyodide", "pyodide.asm.wasm")) > 5 << 20)
            finally:
                shutil.rmtree(out2, ignore_errors=True)
        else:
            print("  （Pyodide 本体が無いので、同梱の確認はとばしました"
                  f"：npm i pyodide@{webbuild.PYODIDE_VER}）")

        # 画面と同じ道を通る runner が、ウェブからの要求を受けられるか
        import runner
        import decks8
        from cards3 import BY_KEY
        nm = next(n for n in sorted(decks8.DECKS8) if "赤零" in decks8.short(n))
        deck = {BY_KEY[k].name: v for k, v in decks8.DECKS8[nm].items()}
        import webrun
        res = json.loads(webrun.go(json.dumps(
            {"deck": deck, "name": "赤零", "games": 40, "pilot": "greedy", "first": "both"})))
        check("webrun.go がウェブからの要求をそのまま回せる", res["games"] == 40)
        check("webrun と serve は同じ道を通る（runner.run）",
              "runner" in dir(webrun) and hasattr(runner, "run"))
        check("ゴールの書き方の確認がウェブからもできる",
              webrun.check_goal(json.dumps({"when": {"そんな条件": 1}})) != ""
              and webrun.check_goal(json.dumps({"when": {"mana_at_least": 5}})) == "")
    finally:
        shutil.rmtree(out, ignore_errors=True)

    # ---------------------------------------------------------------- 配る版に使用者名を載せない
    # 名前そのものをこのファイルに書くと、**この検査ファイル自体が公開されて名前が漏れる**
    # （実際に1度そうなった）。なので名前は書かず、もとの名前と配る版の差分から
    # 「外されたはずの文字列」を機械的に取り出して、それが配る版に残っていないかを見る。
    import decks8
    import difflib
    import json as _json
    import zipfile as _zip

    names = sorted(decks8.DECKS8)
    m = decks8.anon_map(names)
    check("配る版のデッキ名は全部ちがう（名前を外しても見分けられる）",
          len(set(m.values())) == len(names))
    check("大会と順位は残る",
          all(("位" in m[n] or "優勝" in m[n]) for n in names if ("位" in n or "優勝" in n)))

    removed = set()
    for n in names:
        sm = difflib.SequenceMatcher(None, n, m[n], autojunk=False)
        for tag, i1, i2, _j1, _j2 in sm.get_opcodes():
            if tag in ("delete", "replace"):
                frag = n[i1:i2].strip(" 　()（）・-－")
                if len(frag) >= 3:          # 2文字は「イム」のような誤当たりが多い
                    removed.add(frag)
    # この検査は2つの場所で回る。手元（名前つきのファイル）と、公開リポジトリ（名前を外した版）。
    # 「もとのファイルには名前が残っているはず」と決めつけると、公開リポジトリ側で必ず落ちる
    # （実際に GitHub Actions で落ちた）。どちらでも成り立つ形は「**もう一度外しても変わらない**」。
    check("配る版の名前は、もう一度外しても変わらない（外し切れている）",
          all(m[n] == decks8.anon_one(m[n]) for n in names))
    check("配る版のデッキ名に、外されたはずの文字列が残っていない",
          not any(r in v for v in m.values() for r in removed))
    check("画面に出す短い名前にも残っていない",
          not any(r in decks8.short(m[n]) for n in names for r in removed))
    if removed:
        # 名前つきのファイルから回した時だけ見られること
        check("手元のファイルには名前が残っている（出典をたどれる）",
              any(r in n for n in names for r in removed))
        check("外された文字列が1つ以上ある（そもそも匿名化が働いている）", len(removed) >= 5)

    here = os.path.dirname(os.path.abspath(__file__))
    zp = os.path.join(here, "web", "dmsrc.zip")
    if os.path.exists(zp):
        z = _zip.ZipFile(zp)
        left = []
        for f in webbuild.DECK_LISTS:
            if f not in z.namelist():
                continue
            for e in _json.loads(z.read(f).decode("utf-8")).get("decks", []):
                if any(r in e.get("name", "") for r in removed):
                    left.append(e["name"])
        check("配る dmsrc.zip の中のデッキリストにも名前が残っていない", not left)
        # ゴールの当たり先にも名前を書かない（goals.json は配る zip に入る）
        if "goals.json" in z.namelist():
            gj = z.read("goals.json").decode("utf-8")
            check("goals.json の当たり先にも名前が残っていない",
                  not any(r in gj for r in removed))

    bad = [n for n, c in OK if not c]
    print(f"\n{len(OK) - len(bad)}/{len(OK)} 通過" + ("" if not bad else "　失敗：" + "、".join(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
