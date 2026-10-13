#!/usr/bin/env python3
r"""スマホからデッキを登録して、一人回しを始める — 自分のPCで動かす小さなサーバー

  ■ 何のためのものか
  シミュレーターはPython（このPC）でしか動かない。けれどデッキを組むのは、
  カードを眺めながらスマホでやりたい。そこで**PCをサーバーにして、同じ家のWi-Fiにいる
  スマホのブラウザから操作する**。計算はPCがする。スマホは画面だけ。

  ■ 使い方（PowerShell）
    python serve.py
      → 表示されたURL（http://192.168.x.x:8765/?k=…）をスマホのブラウザで開く。
        同じWi-Fiにつないでいること。URLの k= は合言葉で、これが無いと動かない。

    python serve.py --port 9000      ポートを変える
    python serve.py --local          このPCの中だけ（スマホからは見えない。動作確認用）
    python serve.py --procs 4        計算に使うコアの数（既定はCPUの半分、最大4）
    python serve.py --no-token       合言葉を使わない（自宅の閉じたWi-Fiだけにすること）

  ■ Windows で最初の1回だけ出るもの
  「Windows セキュリティの重要な警告」が出たら、**プライベート ネットワーク**にだけチェックを入れて
  アクセスを許可する。パブリックにはチェックを入れない。

  ■ 安全について
    ・待ち受けるのは同じWi-Fiの中だけ。インターネットには公開されない
      （ルーターのポート開放をしない限り外からは届かない。**開放しないこと**）。
    ・合言葉（起動のたびに作り直す）が合わない要求は全部断る。
    ・書き込むのは、このフォルダの decks\ と mygoals.json だけ。他の場所には触らない。
    ・スマホの画面を閉じてもサーバーは動き続ける。止めるときは PowerShell で Ctrl+C。

  ■ スマホでできること
    ・608枚から検索してデッキを組む（クリックで入れる・±で増減）
    ・デッキを decks\ に保存する／保存したデッキを呼び出す
    ・ゴール（どこに届いたら「できた」とするか）を組み立てて mygoals.json に保存する
    ・戦数・操縦・先攻後攻・壁・ゴール地点を選んで**一人回しを始める**
    ・進み具合を見て、終わったら結果（ゴールの部品ごとの到達・殴り切りの分布・札ごとの働き）を見る
"""
import argparse
import json
import os
import random
import re
import socket
import string
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import runner                      # 回すところは serve.py とウェブ版で共通（runner.py）

HERE = os.path.dirname(os.path.abspath(__file__))
DECKDIR = os.path.join(HERE, "decks")
MAXBODY = 2 << 20          # 2MB より大きい要求は読まない

JOBS = {}                  # {id: {state, done, total, result, error, started}}
JOBLOCK = threading.Lock()
CFG = {"token": "", "procs": 1}
_PAGE = {"html": None, "data": None}


# ------------------------------------------------------------------ 画面
def page_html():
    """デッキを組む画面を、いまのカードプールから作って返す（1回だけ作って使い回す）"""
    if _PAGE["html"] is None:
        import deckui
        d = deckui.card_data()
        _PAGE["data"] = d
        body = deckui.PAGE.replace("/*__DATA__*/", json.dumps(d, ensure_ascii=False,
                                                              separators=(",", ":")))
        # サーバーから配られた時だけ「回す」が使えるようにする目印
        body = (f'<script>window.__SERVER__={{"token":{json.dumps(CFG["token"])}}};</script>\n'
                + body)
        # スマホ向けの宣言を付ける（これが無いと携帯のブラウザは幅980pxの画面として組む）
        _PAGE["html"] = deckui.document(body, d["site"])
    return _PAGE["html"]


# ------------------------------------------------------------------ 仕事（一人回し）
def _run_job(jid, o):
    """用意した要求を回して、進み具合と結果を JOBS に書く（計算そのものは runner.run）"""
    try:
        def prog(done, total):
            with JOBLOCK:
                JOBS[jid]["done"] = done
                JOBS[jid]["total"] = total
        out = runner.run(o, prog)
        with JOBLOCK:
            JOBS[jid].update(state="done", done=o["games"], result=out)
    except Exception as e:                             # noqa: BLE001
        with JOBLOCK:
            JOBS[jid].update(state="error", error=f"{e}")
        print("  × 一人回しが失敗しました：", e)
        traceback.print_exc()


def start_job(o):
    jid = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    with JOBLOCK:
        for k, v in list(JOBS.items()):                # 古いものは捨てる（溜めない）
            if v["state"] != "running" and time.time() - v["started"] > 1800:
                del JOBS[k]
        JOBS[jid] = {"state": "running", "done": 0, "total": o["games"], "result": None,
                     "error": "", "started": time.time()}
    threading.Thread(target=_run_job, args=(jid, o), daemon=True).start()
    return jid


# ------------------------------------------------------------------ 保存
def _safe_name(s):
    s = re.sub(r"[^\w぀-ヿ一-鿿 ー－・-]", "", str(s)).strip()
    return (s or "deck")[:40]


def save_deck(name, text):
    os.makedirs(DECKDIR, exist_ok=True)
    p = os.path.join(DECKDIR, _safe_name(name) + ".txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def list_decks():
    if not os.path.isdir(DECKDIR):
        return []
    out = []
    for fn in sorted(os.listdir(DECKDIR)):
        if fn.endswith(".txt"):
            out.append({"name": fn[:-4],
                        "text": open(os.path.join(DECKDIR, fn), encoding="utf-8").read()[:8000]})
    return out


def save_goals(obj):
    import goals
    gs = obj.get("goals") if isinstance(obj, dict) else None
    if not gs:
        raise ValueError("ゴールが入っていません")
    for g in gs:                                       # 書き方を確かめてから保存する
        for _nm, w in goals.parts_of(g):
            goals._one(w)
        goals.goal_when(g)
    with open(goals.MINE, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return goals.MINE


# ------------------------------------------------------------------ サーバー
class H(BaseHTTPRequestHandler):
    server_version = "dmwin"

    def log_message(s, fmt, *a):                       # 既定の1行ログは出さない（うるさいので）
        pass

    def _ok(s, obj, ctype="application/json; charset=utf-8"):
        body = (obj if isinstance(obj, bytes)
                else json.dumps(obj, ensure_ascii=False).encode("utf-8"))
        s.send_response(200)
        s.send_header("Content-Type", ctype)
        s.send_header("Content-Length", str(len(body)))
        s.send_header("Cache-Control", "no-store")
        s.send_header("X-Content-Type-Options", "nosniff")
        s.end_headers()
        s.wfile.write(body)

    def _err(s, code, msg):
        body = json.dumps({"error": msg}, ensure_ascii=False).encode("utf-8")
        s.send_response(code)
        s.send_header("Content-Type", "application/json; charset=utf-8")
        s.send_header("Content-Length", str(len(body)))
        s.end_headers()
        s.wfile.write(body)

    def _auth(s, q):
        if not CFG["token"]:
            return True
        k = (q.get("k") or [""])[0] or s.headers.get("X-Key", "")
        return k == CFG["token"]

    def _body(s):
        n = int(s.headers.get("Content-Length") or 0)
        if n <= 0 or n > MAXBODY:
            raise ValueError("要求の大きさがおかしい")
        return json.loads(s.rfile.read(n).decode("utf-8"))

    def do_GET(s):
        u = urlparse(s.path)
        q = parse_qs(u.query)
        if u.path == "/favicon.ico":               # ブラウザが勝手に取りに来るので、黙って返す
            s.send_response(204)
            s.send_header("Content-Length", "0")
            s.end_headers()
            return
        if not s._auth(q):
            return s._err(403, "合言葉が違います。PCの画面に出ているURLをそのまま開いてください")
        if u.path in ("/", "/index.html"):
            return s._ok(page_html().encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/api/ping":
            page_html()                            # まだなら、ここでカードを読み込む
            d = _PAGE["data"] or {}
            return s._ok({"ok": True, "cards": len(d.get("cards", [])),
                          "procs": CFG["procs"], "decks": len(list_decks())})
        if u.path == "/api/job":
            jid = (q.get("id") or [""])[0]
            with JOBLOCK:
                j = JOBS.get(jid)
                if not j:
                    return s._err(404, "その仕事はありません（サーバーを入れ直すと消えます）")
                return s._ok({k: v for k, v in j.items() if k != "started"})
        if u.path == "/api/saved":
            return s._ok({"decks": list_decks()})
        return s._err(404, "ありません")

    def do_POST(s):
        u = urlparse(s.path)
        q = parse_qs(u.query)
        if not s._auth(q):
            return s._err(403, "合言葉が違います")
        try:
            b = s._body()
        except Exception as e:                         # noqa: BLE001
            return s._err(400, f"読めませんでした：{e}")
        try:
            if u.path == "/api/run":
                return s._ok({"job": start_job(runner.prepare(b))})
            if u.path == "/api/save-deck":
                p = save_deck(b.get("name", "deck"), str(b.get("text", ""))[:20000])
                print(f"  ・デッキを保存しました：{p}")
                return s._ok({"path": os.path.basename(p)})
            if u.path == "/api/save-goals":
                p = save_goals(b)
                print(f"  ・ゴールを保存しました：{p}")
                return s._ok({"path": os.path.basename(p)})
            if u.path == "/api/parse-goal":
                # 文章で書いたゴールを読む（画面の「文章で書く」欄）。
                # 読み方は goaltext.py の1か所だけ。画面側では読まない。
                import goaltext
                g, notes = goaltext.parse(str(b.get("text", ""))[:4000], b.get("deck") or None)
                return s._ok({"goal": g, "notes": notes})
            if u.path == "/api/goal-text":
                import goaltext
                return s._ok({"text": goaltext.explain(b.get("goal") or {})})
        except SystemExit as e:
            return s._err(400, str(e))
        except Exception as e:                         # noqa: BLE001
            return s._err(400, f"{e}")
        return s._err(404, "ありません")


def lan_ip():
    """同じWi-Fiの中から見えるこのPCのアドレスを調べる（どこにも通信はしない）"""
    sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sk.connect(("192.0.2.1", 9))                   # 例示用アドレス。届かなくてよい
        return sk.getsockname()[0]
    except Exception:                                  # noqa: BLE001
        return "127.0.0.1"
    finally:
        sk.close()


def main():
    ap = argparse.ArgumentParser(description="スマホからデッキ登録と一人回しをするための小さなサーバー")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default=None, help="待ち受けるアドレス（既定は同じWi-Fiの中すべて）")
    ap.add_argument("--local", action="store_true", help="このPCの中だけ（スマホからは見えない）")
    ap.add_argument("--procs", type=int, default=0, help="計算に使うコアの数（既定はCPUの半分、最大4）")
    ap.add_argument("--no-token", action="store_true", help="合言葉を使わない（閉じたWi-Fiだけにすること）")
    a = ap.parse_args()

    if a.procs > 0:
        CFG["procs"] = max(1, min(16, a.procs))
    else:
        CFG["procs"] = max(1, min(4, (os.cpu_count() or 2) // 2))
    runner.PROCS[0] = CFG["procs"]
    CFG["token"] = "" if a.no_token else "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(12))

    host = a.host or ("127.0.0.1" if a.local else "0.0.0.0")
    print("カードを読み込んでいます…", flush=True)
    t0 = time.time()
    page_html()
    n = len(_PAGE["data"]["cards"])
    print(f"  {n}枚（{time.time() - t0:.1f}秒）\n")

    srv = ThreadingHTTPServer((host, a.port), H)
    ip = "127.0.0.1" if a.local else lan_ip()
    url = f"http://{ip}:{a.port}/" + (f"?k={CFG['token']}" if CFG["token"] else "")
    print("=" * 64)
    print("  スマホのブラウザで、このURLを開いてください（同じWi-Fiにつないだまま）")
    print()
    print("    " + url)
    print()
    if not a.local:
        print("  ・Windowsの警告が出たら「プライベート ネットワーク」だけ許可してください")
        print("  ・このURLは同じWi-Fiの中だけで届きます。ルーターのポート開放はしないこと")
    if CFG["token"]:
        print(f"  ・合言葉 k={CFG['token']} は起動のたびに変わります")
    print(f"  ・計算に使うコア {CFG['procs']}　　止めるときは Ctrl+C")
    print("=" * 64, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n止めました")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
