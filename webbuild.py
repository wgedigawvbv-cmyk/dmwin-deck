#!/usr/bin/env python3
r"""ウェブで動く形にまとめる — サーバーを置かずに、ブラウザの中でPythonを走らせる

  ■ 何をするものか
  web\ フォルダを作る。その中身をどこかに置けば、**スマホでもPCでも、家の外からでも**
  同じ画面が動く。サーバーはいらない。**計算は見ている人のブラウザの中で走る**
  （Pyodide ＝ ブラウザで動くPython。このシミュレーターのPythonがそのまま動く）。

    serve.py   … PCが計算する。家のWi-Fiの中だけ。速い（複数コアを使える）
    web\       … 見ている端末が計算する。どこからでも。遅い（1コア・2〜4倍）

  ■ 作り方（PowerShell）
    python webbuild.py
      → web\ ができる（約1MB）。Pyodide 本体は CDN から読む形になる。これがいちばん手軽。

    npm i pyodide@0.29.5
    python webbuild.py --pyodide node_modules\pyodide
      → Pyodide 本体（約12MB）も同梱する。**自分が置いたファイルだけで完結する**ので、
        CDN が落ちても、見る人がどこにいても動く。置き場所に12MB入れられるならこちら。

  ■ 置き方
    ・ためす：   python webbuild.py  のあと  python -m http.server 8080 --directory web
                 → http://localhost:8080/ を開く（ファイルを直接開くのは不可。後述）
    ・GitHub Pages：web\ の中身をリポジトリに入れて、Settings → Pages で公開する
    ・そのほか Netlify / Cloudflare Pages など、静的ファイルを置けるところならどこでも

  ■ なぜファイルを直接開いてはいけないか
  ブラウザは file:// で開いたページから別のファイルを読むことを禁じている（Web Worker も作れない）。
  だから必ず http:// で配る必要がある。上の python -m http.server が最短。

  ■ 入っているもの
    index.html   画面（608枚のデータを埋め込み済み。開いた瞬間からデッキは組める）
    worker.js    裏で Pyodide を起こして、一人回しを回す
    dmsrc.zip    このシミュレーターのPython一式（ブラウザの中に展開される）
    pyodide\     Pyodide 本体（--pyodide を使った場合）
    README.txt   置き方の手引き
"""
import argparse
import json
import os
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PYODIDE_VER = "0.29.5"
CDN = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VER}/full/"
# Pyodide 本体のうち、同梱に要るファイル（これだけで動く。科学計算のパッケージは使わない）
PYO_FILES = ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm",
             "python_stdlib.zip", "pyodide-lock.json")

# ブラウザの中に持ち込むPython。runs8\ や cards.md のような、回すのに要らないものは入れない。
SRC_SKIP = {"webbuild.py", "deckui.html", "deckui_artifact.html"}
SRC_JSON = ("env_lists.json", "env_lists_b.json", "env_lists_c.json", "deck_jokers.json",
            "goals.json", "cards_net.json", "cards_net_wishlist.json", "env_missing.json",
            "sets_dm26.json", "site.json")


# 入賞リストのデッキ名には使用者の名前・ハンドルが入っている。
# 出典は公式カバレージなので情報自体は公開されているが、**個人のサイトで
# 「この人はこのデッキを使った」という形にして載せ直すのは別の話**なので、
# 配る版（web と公開リポジトリ）だけ名前を外す。手元のファイルは出典をたどれるように
# そのまま残す。外し方は decks8.anon_one に書いてある。
DECK_LISTS = ("env_lists.json", "env_lists_b.json", "env_lists_c.json", "deck_jokers.json")


def anon_list_bytes(path):
    """デッキリストのJSONを読み、使用者名を外した中身を bytes で返す"""
    import decks8
    d = json.load(open(path, encoding="utf-8"))
    names = [e.get("name", "") for e in d.get("decks", [])]
    m = decks8.anon_map(names)
    for e in d.get("decks", []):
        if e.get("name"):
            e["name"] = m[e["name"]]
    return json.dumps(d, ensure_ascii=False, indent=1).encode("utf-8")


def write_anon_lists(out_dir):
    """配る版のデッキリスト（名前を外したもの）を out_dir に書き出す"""
    n = 0
    for fn in DECK_LISTS:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        with open(os.path.join(out_dir, fn), "wb") as f:
            f.write(anon_list_bytes(p))
        n += 1
    return n


def make_src_zip(path):
    """このシミュレーターのPythonとデータを1つのzipにまとめる（デッキ名は配る版＝名前なし）"""
    n = 0
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for fn in sorted(os.listdir(HERE)):
            if fn.endswith(".py") and fn not in SRC_SKIP:
                z.write(os.path.join(HERE, fn), fn)
                n += 1
        envd = os.path.join(HERE, "envcards")
        for fn in sorted(os.listdir(envd)):
            if fn.endswith(".py"):
                z.write(os.path.join(envd, fn), "envcards/" + fn)
                n += 1
        for fn in SRC_JSON:
            p = os.path.join(HERE, fn)
            if not os.path.exists(p):
                continue
            if fn in DECK_LISTS:                    # 使用者の名前を外してから入れる
                z.writestr(fn, anon_list_bytes(p))
            else:
                z.write(p, fn)
            n += 1
    return n, os.path.getsize(path)


WORKER = r'''/* 裏方：ブラウザの中で Python（Pyodide）を起こして、一人回しを回す。
   画面（index.html）はこのファイルに頼むだけで、計算そのものには触らない。
   重い計算をここ（Web Worker）でやるので、回している間も画面は動く。 */
let py = null, booting = null;

function say(msg) { postMessage({ t: "status", msg }); }

async function boot() {
  if (py) return py;
  if (booting) return booting;
  booting = (async () => {
    say("Python を起こしています…（はじめの1回だけ時間がかかります）");
    importScripts(PYODIDE_URL + "pyodide.js");
    py = await loadPyodide({ indexURL: PYODIDE_URL });
    say("カードを読み込んでいます…");
    const r = await fetch("dmsrc.zip");
    if (!r.ok) throw new Error("dmsrc.zip が読めません（" + r.status + "）");
    const buf = await r.arrayBuffer();
    py.FS.mkdirTree("/dmwin");
    py.unpackArchive(buf, "zip", { extractDir: "/dmwin" });
    py.runPython(`
import sys
sys.path.insert(0, "/dmwin")
import webrun
`);
    const info = JSON.parse(py.runPython("webrun.ready()"));
    say(`用意できました（カード${info.cards}枚）`);
    postMessage({ t: "ready", info });
    return py;
  })();
  return booting;
}

onmessage = async (e) => {
  const m = e.data || {};
  try {
    if (m.t === "boot") { await boot(); return; }
    if (m.t === "run") {
      await boot();
      py.globals.set("__req", JSON.stringify(m.req));
      py.globals.set("__prog", (done, total) => postMessage({ t: "prog", done, total }));
      const out = py.runPython("webrun.go(__req, __prog)");
      postMessage({ t: "done", result: JSON.parse(out) });
      return;
    }
    if (m.t === "checkgoal") {
      await boot();
      py.globals.set("__g", JSON.stringify(m.goal));
      postMessage({ t: "goalcheck", msg: py.runPython("webrun.check_goal(__g)") });
      return;
    }
  } catch (err) {
    postMessage({ t: "error", msg: String(err && err.message || err) });
  }
};
'''

README = """デュエマ デッキ工房（ウェブ版）

このフォルダの中身をそのまま、静的ファイルを置ける場所に上げれば動きます。
サーバーのプログラムは要りません。計算は、見ている人のブラウザの中で走ります。

■ 手元でためす
    python -m http.server 8080 --directory web
    → ブラウザで http://localhost:8080/

  ※ index.html をダブルクリックして file:// で開いても動きません。
     ブラウザが file:// のページに別ファイルの読み込みと Web Worker を許していないためです。

■ GitHub Pages に置く
  1. GitHub に新しいリポジトリを作る（公開でも非公開でもよい。Pages は公開が要る）
  2. このフォルダの中身をそのまま入れて push する
  3. Settings → Pages → Source を「Deploy from a branch」、ブランチを main、フォルダを / (root)
  4. 数分待つと https://<ユーザー名>.github.io/<リポジトリ名>/ で開ける

■ 入っているもの
  index.html    画面（カードのデータを埋め込み済み。開いた瞬間からデッキは組める）
  worker.js     裏で Pyodide を起こして一人回しを回す
  dmsrc.zip     シミュレーターのPython一式
  pyodide/      Pyodide 本体（同梱した場合のみ）

■ 速さ
  ブラウザの中のPythonは、PCで直接動かすより約2倍遅く、コアも1つしか使えません。
  300戦で3秒、1000戦で10秒ほどが目安です。大きな測定は PC で solo.py / serve.py を使ってください。

■ 共有リンク
  画面の「共有リンク」を押すと、いま組んでいるデッキとゴールがURLの中に入ったリンクができます。
  そのリンクを開いた人は、同じデッキとゴールが入った状態で始められます。
  サーバーに何も保存しないので、渡した相手の端末の中だけで完結します。

■ 公開する前に一度考えること
  このページには、カード名・コスト・パワー・種族と、効果を自分の言葉で要約した文、
  それに公式カバレージから書き取った入賞デッキのリストが入っています。
  自分と友人で使うぶんには問題になりにくいものですが、**誰でも見られる形で公開する**のは
  別の話です。迷うなら、リンクを知っている人だけが開ける置き方（非公開リポジトリ＋
  Netlify/Cloudflare のプレビューURLなど）から始めるか、公式のファンコンテンツの決まりを
  確かめてからにしてください。
"""


def build(out_dir, pyodide_dir=None, use_cdn=False):
    os.makedirs(out_dir, exist_ok=True)
    import deckui
    d = deckui.card_data()
    pyurl = CDN if use_cdn else "pyodide/"
    body = deckui.PAGE.replace("/*__DATA__*/", json.dumps(d, ensure_ascii=False,
                                                          separators=(",", ":")))
    body = (f'<script>window.__WEB__={{"pyodide":{json.dumps(pyurl)},'
            f'"version":{json.dumps(PYODIDE_VER)}}};</script>\n' + body)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(deckui.document(body, d["site"]))
    with open(os.path.join(out_dir, "worker.js"), "w", encoding="utf-8") as f:
        f.write(f'const PYODIDE_URL = {json.dumps(pyurl)};\n' + WORKER)
    nsrc, zsize = make_src_zip(os.path.join(out_dir, "dmsrc.zip"))
    with open(os.path.join(out_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(README)

    copied = 0
    if pyodide_dir:
        dst = os.path.join(out_dir, "pyodide")
        os.makedirs(dst, exist_ok=True)
        miss = []
        for fn in PYO_FILES:
            src = os.path.join(pyodide_dir, fn)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(dst, fn))
                copied += 1
            else:
                miss.append(fn)
        if miss:
            raise SystemExit(f"Pyodide のファイルが足りません：{'、'.join(miss)}\n"
                             f"  {pyodide_dir} を確かめてください"
                             f"（npm i pyodide@{PYODIDE_VER} で入ります）")
    return {"cards": len(d["cards"]), "src": nsrc, "zip": zsize, "pyo": copied, "cdn": use_cdn}


def main():
    ap = argparse.ArgumentParser(description="ウェブで動く形（web\\ フォルダ）を作る")
    ap.add_argument("--out", default=os.path.join(HERE, "web"))
    ap.add_argument("--pyodide", help="Pyodide のファイルがあるフォルダ（node_modules\\pyodide）")
    ap.add_argument("--cdn", action="store_true",
                    help="Pyodide を同梱せず、CDN から読む（見る人がネットにつながっている必要がある）")
    ap.add_argument("--list-src", action="store_true",
                    help="dmsrc.zip に入れるファイルの名前だけを並べて終わる（publish.ps1 が使う）")
    ap.add_argument("--anon-lists", metavar="DIR",
                    help="入賞リストから使用者名を外した版を DIR に書き出して終わる（publish.ps1 が使う）")
    a = ap.parse_args()
    if a.anon_lists:
        k = write_anon_lists(a.anon_lists)
        print(f"使用者名を外したデッキリストを {k}個 書き出しました：{a.anon_lists}")
        return
    if a.list_src:
        for fn in sorted(os.listdir(HERE)):
            if fn.endswith(".py") and fn not in SRC_SKIP:
                print(fn)
        envd = os.path.join(HERE, "envcards")
        for fn in sorted(os.listdir(envd)):
            if fn.endswith(".py"):
                print("envcards/" + fn)
        for fn in SRC_JSON:
            if os.path.exists(os.path.join(HERE, fn)):
                print(fn)
        print("webbuild.py")     # 作る側そのもの（リポジトリには必要）
        return
    pyo = a.pyodide
    if not pyo and not a.cdn:
        for g in (os.path.join(HERE, "node_modules", "pyodide"),
                  os.path.join(HERE, "pyodide")):
            if os.path.isdir(g):
                pyo = g
                break
    if not pyo and not a.cdn:
        a.cdn = True
        print("（Pyodide 本体が手元に無いので、CDN から読む形で作ります）")
        print(f"  自分のものだけで完結させたいときは： npm i pyodide@{PYODIDE_VER} のあと")
        print("    python webbuild.py --pyodide node_modules\\pyodide\n")
    r = build(a.out, pyo, a.cdn)
    print(f"できました：{a.out}")
    print(f"  画面（カード{r['cards']}枚を埋め込み）／Python {r['src']}ファイル"
          f"（dmsrc.zip {r['zip'] / 1024:.0f}KB）")
    print("  Pyodide " + (f"同梱 {r['pyo']}ファイル" if r["pyo"] else "はCDNから読む"))
    tot = sum(os.path.getsize(os.path.join(dp, f))
              for dp, _dn, fs in os.walk(a.out) for f in fs)
    print(f"  合計 {tot / 1024 / 1024:.1f}MB")
    print()
    print("  ためす：   python -m http.server 8080 --directory " + os.path.relpath(a.out, HERE))
    print("             → http://localhost:8080/")
    print("  ※ index.html を直接ダブルクリックしても動きません（http:// で配る必要があります）")
    print("  置き方は " + os.path.join(a.out, "README.txt"))


if __name__ == "__main__":
    main()
