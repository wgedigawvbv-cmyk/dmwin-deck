"""対戦エンジン第3版：実在のカードを参考にしたカードプール（cards3.py）用

考え方
  ・対戦は「いまの番のプレイヤーが、打てる手の一覧（legal）から1つ選ぶ（apply）」のくり返しで進む。
    手＝マナに置く／カードを使う／攻撃に移る／どれでどこを攻撃する／ターンを終える。
  ・操縦する側（ai3.py）は、この一覧から選ぶだけ。デッキごとの作戦は、このファイルにも操縦側にも書かない。
  ・対象の選び方、任意効果を使うかどうか、守る側の対応（ブロック・S・トリガー・ニンジャ・ストライク）は、
    全デッキ共通の決まり（カードの重要度 PRI など）で機械的に決める。
  ・ループ（創世竜ループ・ドッコイループ）は手順を1つずつ回さず、「部品がそろい、止めるメタがいなければ成立」で扱う。

ゾーンの持ち方：山札は末尾が上。シールドは (カード, 表向きか) の並び。
"""
import random

from cards3 import BY_KEY as CARD

MCIV, MULTI = {}, {}
for _k, _c in CARD.items():
    _civ = set(_c.civ) | (set(_c.twin[1]) if _c.twin else set())
    MCIV[_k] = "".join(sorted(_civ))
    MULTI[_k] = len(_civ) >= 2

# カードの重要度（全デッキ共通）。除去の対象、捨てるカード、山札から選ぶカード、踏み倒すカードを決めるのに使う
PRI = {k: c.cost for k, c in CARD.items()}
PRI.update({
    "kohaku": 5, "chakra": 6, "kabocha": 5, "klin": 6, "douki": 3, "fujin": 3, "vt": 7, "clock": 3, "eringi": 4, "keikan": 4,
    "tensai": 3, "efc": 2,
    "derbande": 9, "anti": 6, "dagra": 5, "katsuemon": 4, "magnum": 5, "tenbin": 5, "shunsen": 5, "radio": 5, "shinten": 5,
    "tokoshie": 5, "zaze": 6, "ichion": 5, "poppi": 6, "viride": 8, "everlast": 7, "dogigyaku": 10, "saint": 3, "gcross": 3,
    "hustle": 4,
    "zen": 9, "leviya": 8, "trap": 6, "parli": 7, "jasmine": 3, "majin": 2, "manhattan": 5, "valhalla": 6, "wokanna": 6,
    "esmel": 2, "strato": 3,
    "pon": 7, "teacher": 8, "dokkoi": 9, "shako": 6, "princess": 4, "kerola": 3, "takkyu": 3, "mirai": 2, "saitan": 6,
    "crossfire": 9, "zoro": 10, "doom": 7, "gigan": 7, "margani": 4, "kuzen": 4, "dangerdeon": 5, "lelady": 3, "apul": 4,
    "obza": 4, "gio": 3,
    "fheart": 2, "mflower": 2, "aroma": 2, "tina": 4, "leaf": 7, "koori": 4, "hangyaku": 6, "robin": 8, "ops": 9,
    "testa": 5, "vamilia": 6, "venom": 6, "artel": 7, "shuto": 7, "jaouga": 9, "scarlet": 8,
})
STAY = {"manhattan", "valhalla", "strato", "aroma"}        # 場に残して働くタマシード（創世竜の下に置かない）
SNOW = {k for k, c in CARD.items() if "snow" in c.races and c.kind == "C"}
HYPER_POW = {"chakra": 3500, "dagra": 3000, "dokkoi": 5000, "venom": 4000, "vamilia": 3000}
CHANGE_ORDER = ("zoro", "ops", "dogigyaku", "scarlet", "robin")
from cards3 import CHANGE  # noqa: E402

MAXTURN = 60          # これを超えたら引き分け（両者合わせたターン数）
# ---- 新カード用の差し込み口（envcards/*.py が登録する。キー＝カードのキー）----
ATTACK, DESTROYED, LEFT, TSTART, TEND = {}, {}, {}, {}, {}     # fn(s, i, u) ／ LEFT は fn(s, i, u, dest)
POWERX = {}        # fn(s, i, u, atk) -> パワーの加算
BRKX = {}          # fn(s, i, u) -> ブレイク数（None なら通常）
COSTX = {}         # fn(s, i, av) -> 手札から召喚するコスト
CANTATK = {}       # fn(s, i, u) -> True なら攻撃できない
EVOX = {}          # fn(s, i, u) -> u を進化元にできるか
CHANGEX = {}       # 革命チェンジ：fn(s, i, attacker_u) -> 手札のそのカードに入れ替えられるか
REACT = {}         # 相手の攻撃に反応して手札から出る（ニンジャ・ストライク等）：fn(s, di, attacker_u) -> 使ったら True
FATEX = {}         # 場にいる間の出現制限：fn(s, owner, u, i, k, src, summon, res) -> res（"ok"/"no"/"mana"/"grave"/"delay"）
ACTAPPLY = {}      # 追加の手の実行：名前（"x:..."）-> fn(s, action)
FREE_ACTS = []     # 追加の手の一覧：fn(s, i, av, cv) -> [("x:...", ...)]
AURAP = []         # 他のカードのパワーへの加算：fn(s, i, u, atk) -> 加算値
COSTAURA = []      # 全体のコスト変化：fn(s, i, k, n) -> n
ATKLOCK = []       # fn(s, i, u) -> True なら u は攻撃できない
BLOCKLOCK = []     # fn(s, u) -> True なら u はブロックできない
ATKTARGETLOCK = [] # fn(s, i, u, t) -> True なら u は t を攻撃できない
ATKWATCH = []      # 攻撃を宣言した時：fn(s, i, u)
LEAVEWATCH = []    # カードが場を離れた時：fn(s, i, u, dest, destroy)
ENTERWATCH = []    # クリーチャーが出た時：fn(s, i, u)
BREAKWATCH = []    # シールドがブレイクされた時：fn(s, ai, di, n)
BATTLEFX = []      # バトル結果の補正：fn(s, ai, au, di, du, a_dies, d_dies) -> (a_dies, d_dies)
INVADEX = {}       # 侵略：fn(s, i, 攻撃しているu) -> 手札のそのカードをその上に重ねられるか
GAMESTART = {}     # ゲームのはじめの用意（禁断など）：fn(s, i, cards)（cards＝山札になる前の並び。ここから取り出す）
PAYX = {}          # 召喚の時の追加の支払い（ハイパーエナジー、ジャオウガ式のタップ）：fn(s, i, k, n)
SPCOST = {}        # 呪文・クロスギアの実際のコスト（G・ゼロ、別コスト）：fn(s, i, k) -> コスト
DISCARDX = {}      # 手札から捨てられる時（マッドネス）：fn(s, i, k) -> True なら捨てずにすんだ
LEAVEREP = []      # 離れるのを別のことで置き換える（EXライフ、セイバー、エスケープ）：fn(s, i, u, dest, destroy) -> True なら離れない
BREAKREP = []      # ブレイクしたシールドの行き先を変える：fn(s, ai, di, broken) -> True なら手札に加えない
NOGRAVE = set()    # 唱えた後に墓地へ行かない呪文（超次元ゾーンへ）
BRKPLUS = []       # ブレイク数を増やす（クロスギア等）：fn(s, i, u) -> 増やす数
BLOCKOK = []       # ブロッカーを与える：fn(s, u) -> True ならブロックできる
SAOK = []          # スピードアタッカーを与える：fn(s, i, u) -> True なら出たターンに攻撃できる
UNBOK = []         # ブロックされない：fn(s, i, u) -> True
SPELLLOCK = []     # 呪文を唱えられない：fn(s, i, cost) -> True なら唱えられない
MANAEXEC = []      # 相手はマナ・墓地からカードを使えない：fn(s, i) -> True（i＝使おうとしている側）
GSOK = []          # G・ストライクを与える：fn(s, di, k) -> True
GUARD = []         # ガードマン：fn(s, di, 攻撃しているu, 本来の攻撃先tu) -> 新しい攻撃先(U) か None
DISCARDWATCH = []  # 手札からカードが捨てられた時：fn(s, i, k)
TENDALL = []       # どちらのターンの終わりにも、場のカード1つずつについて：fn(s, i, u)（i＝持ち主）
NOATKPX = []       # 相手プレイヤーを攻撃できない（与える側）：fn(s, i, u) -> True
NOATKIGN = []      # 「攻撃できない」を無視する：fn(s, i, u) -> True
TRIGOK = []        # シールドから使える（S・トリガーを得る）：fn(s, di, k) -> True
MACHOK = []        # マッハファイターを与える：fn(s, i, u) -> True
LOSEREP = []       # 負けるのを置き換える：fn(s, i, how) -> True なら負けない
INVZONE = {}       # 侵略をどのゾーンから使えるか（既定は手札のみ）：key -> ("hand", "mana", "grave")
NOGS = set()       # このカードの攻撃中は相手のG・ストライクが使えない
ATKEND = []        # 攻撃の終わりに：fn(s, i, u)
ATKSWAP = {}       # 攻撃しているクリーチャーを入れ替える（Jクライム等）：fn(s, i, u) -> 新しいU（しなければ None）
MANALEAVE = []     # 自分のマナゾーンからカードが離れた時：fn(s, i, k)
LEAVEDEST = []     # 離れる先を変える：fn(s, i, u, dest, destroy) -> 新しい行き先（変えないなら None）
MANAREP = []       # 手札以外からマナゾーンに置かれるのを墓地に変える：fn(s, i, k, src) -> True なら墓地へ
SPELLWATCH = []    # 呪文を唱えた時：fn(s, i, k)
TSTARTALL = []     # 自分のターンのはじめに、場のカード1つずつについて：fn(s, i, u)
CHARGEX = {}       # マナゾーンに置いた時：fn(s, i)
SHINKA = set()     # シンカライズ：クリーチャーでなくても進化元にできるカード
TGTLOCK = []       # 相手に選ばれない：fn(s, 選ぶ側, u) -> True なら選べない（s.spc＝いま唱えている呪文のコスト）
VALADJ = []        # クリーチャーの値打ちの補正：fn(s, u) -> 増減（スター進化は離れても下が残るので安い）

# 除去などで「相手のどれを選ぶか」の決め方。
#   True  ＝ 危なさ（Game.threat）で選ぶ＝自分を殴ってくる面・ブロッカーを優先して消す
#   False ＝ もとのやり方。重要度（val）のいちばん高い相手を選ぶ（既定）
#
# 既定を False にしてあるのは、**測ったら差が無かった**から（2026-10-11）。
#   同じデッキ・同じ探索回数・座席と先攻を入れ替えて 480〜720戦：勝率 47.5〜49.0%、
#   重みを0倍〜2倍に振っても動かず、まったく同じ設定どうしの点検が 49.5% だったので、
#   いずれもばらつきの中。理由も数えた：「相手のどれを選ぶか」の呼び出しのうち
#   **62.9% は候補が0〜1つで選ぶ余地が無く**、2つ以上あった場合も 61.5% は同じ相手を選ぶ。
#   2つの決め方が食い違うのは **1戦あたり0.8回**しかないので、勝率が動くはずがない。
# 仕組みは残してある（プレイヤーごとに g.tgtmode[i] で切り替えられる）。
# 除去の多いカードが増えて分かれ目が増えたら、skill.py で測り直すとよい。
TARGET_THREAT = False
THREAT_W = {"atkp": 4.0,      # 次のターン自分を殴れる面
            "brk": 2.0,       # その打点1つにつき
            "blk": 2.0,       # ブロッカー（自分の攻めを止める）
            "ready": 1.5,     # 立っている（タップしていない）
            "power": 1 / 2000.0}
SHIELDIN = []      # カードがシールドゾーンに置かれた時：fn(s, i, k, up)（i＝持ち主、up＝表向きか）
SHIELDOUT = []     # カードがシールドゾーンを離れた時：fn(s, i, k, up, dest)（dest＝"hand"/"grave"/"break"…）
CASTLEX = {}       # G城が表向きで置かれた時：fn(s, i, k)（キーごと）
BREAKPRE = []      # シールドがブレイクされる直前：fn(s, 攻める側, 割られる側, n) -> 新しい枚数（減らせる）
TAPWATCH = []      # クリーチャーがタップした時：fn(s, i, u)（i＝持ち主）
DRAWWATCH = []     # カードを引いた時：fn(s, i, k)
BLOCKREACT = {}    # 相手がブロックした時に手札から出る（ウラ・ニンジャ・ストライク）：fn(s, di, 攻撃側u, ブロックしたu) -> True なら使った
HYPER_BRK = {}     # ハイパーモード中のブレイク数（既定は2）
SPCOSTAURA = []    # 呪文・タマシードなどのコストを全体で変える：fn(s, i, k) -> 増減（マイナスで軽く）
MUSTATKTGT = []    # 攻撃先の強制：fn(s, 攻める側, u, 候補の並び) -> 選ばせたい相手の番号か None
ABILOCK = []       # 能力をすべて無視する：fn(s, 持ち主, u) -> True なら u の能力は一切働かない
SHIELDREP = []     # シールドゾーンのカードの行き先を変える（S・バック）：fn(s, i, k, up, dest) -> 新しい dest か None
CHANGEZONE = {}    # 革命チェンジで探すゾーン：キー -> ("hand", "shield") など（既定は手札だけ）
GSWATCH = []       # G・ストライクを使った時：fn(s, 使った側, k)
BLOCKDONE = {}     # ブロックした時（ブロックした側のカード）：fn(s, ブロック側, b, 攻撃しているu)
ENTERTRIGLOCK = [] # 出た時の能力を誘発させない：fn(s, 出した側, u) -> True なら「出た時」が働かない
TAMAIN = []        # タマシードが置かれた時：fn(s, i, u)
NOGSX = []         # この攻撃ではG・ストライクを使えない：fn(s, 攻める側, 攻撃しているu) -> True
GODLINK = {}       # G・リンク：キー -> (位置, つなげる相手のキーの組)。相手が空なら「どのゴッドでも」
                   #   位置は "L"（左）／"R"（右）／"C"（中央）。いまの実装は位置を記録するだけで、
                   #   並び順の制約（中央は左右の間）までは見ていない。
MANAIN = []        # 自分のマナゾーンにカードが置かれた時（スペース・チャージ）：fn(s, i, k, src)
BLOCKWATCH = []    # 攻撃がブロックされた時（攻撃側の誘発）：fn(s, i, 攻撃しているu, ブロックしたu)
CHOSENWATCH = []   # 相手に1つ選ばれた時（target が返す1つについて）：fn(s, 持ち主, u, 選んだ側)
MUSTATK = []       # 攻撃の強制：fn(s, i) -> True なら、攻撃できるクリーチャーがいる間ターンを終えられない
GUARDMEN = set()   # ガードマンを持つカード（env0.guardman が入れる）
SHIELDDEST = {}    # シールドゾーンを離れる時の行き先を変える（シールド・ゴー）：fn(s, i, k, up, dest) -> 新しい dest
SHIELDCAST = {}    # シールドゾーンから手札に加える時の受け（スーパー・S・トリガー）：
                   #   fn(s, i, k, nsh) -> True なら、そのカードはここで処理済み（手札に残さない）。nsh＝その時のシールドの枚数
BATTLESWAP = []    # バトルするクリーチャーを守る側で差し替える（スーパーガードマン）：
                   #   fn(s, di, du, ai, au) -> 新しい du か None（タップはカード側でやる）
TURNSTART = []     # 自分のターンのはじめ（バトルゾーンに何もなくても呼ばれる）：fn(s, i)
TENDP = []         # ターンの終わり（バトルゾーンに何もなくても、両プレイヤーについて呼ばれる）：fn(s, i)
EVOSRC = {}        # バトルゾーン以外からの進化元（手札進化・墓地進化・マナ進化）：
                   #   fn(s, i) -> (ゾーン名"hand"/"grave"/"mana", キー) か None
MUSTPICK = []      # 「相手が選ぶなら、可能ならこれを選ぶ」：fn(s, 選ぶ側, 候補の一覧) -> 選ばせたい U か None


def _mustpick_douki(s, by, cands):
    """《同期の妖精》：相手がクリーチャーを選ぶ時、可能ならこれを選ばせる
    （以前は Game.target にカード名で直書きしてあり、しかも条件（pred）で絞る前に
      横取りしていたため、「パワー3000以下を選ぶ」のような条件つきの効果でも選ばれていた）"""
    for u in cands:
        if u.k == "douki":
            return u
    return None


MUSTPICK.append(_mustpick_douki)
GEAR = "X"         # クロスギアの kind
_UID = [0]
MAXENT = 12           # 1ターンに出せるクリーチャーの上限（手順が終わらなくなるのを防ぐ安全装置）


class U:
    """バトルゾーンのカード1枚（クリーチャーかタマシード）"""
    __slots__ = ("k", "c", "tap", "sick", "under", "hyper", "frz", "sa", "pw", "lock", "eot", "re", "unb", "jd", "x", "uid", "link")

    def __init__(s, k):
        _UID[0] += 1
        s.uid = _UID[0]
        s.k = k
        s.c = CARD[k]
        s.tap = False
        s.sick = True        # このターンに出た
        s.under = []         # 下にあるカード
        s.hyper = False
        s.frz = 0            # 次のアンタップをとばす
        s.sa = False         # このターンだけスピードアタッカー
        s.pw = 0             # このターンだけのパワー増減
        s.lock = -1          # このターン番号の間、攻撃もブロックもできない
        s.eot = False        # ターンの終わりに山札の下へ
        s.re = False         # 最初の攻撃の後アンタップ
        s.unb = False        # このターンブロックされない
        s.jd = s.c.jd        # ジャストダイバー中
        s.x = {}             # 新カード用の状態
        s.link = []          # G・リンク：横につないだゴッド（この U と合わせて「1体のクリーチャー」）

    def copy(s):
        n = U.__new__(U)
        n.uid = s.uid
        n.k = s.k
        n.c = s.c
        n.tap = s.tap
        n.sick = s.sick
        n.under = s.under[:]
        n.hyper = s.hyper
        n.frz = s.frz
        n.sa = s.sa
        n.pw = s.pw
        n.lock = s.lock
        n.eot = s.eot
        n.re = s.re
        n.unb = s.unb
        n.jd = s.jd
        n.x = dict(s.x)
        n.link = [z.copy() for z in s.link]
        return n


class P:
    __slots__ = ("deck", "hand", "mana", "mused", "grave", "sh", "board", "ent", "spl", "drawn", "fp", "zen_used", "gc_used",
                 "final_used", "final_turn", "protect", "nosmall", "nolow", "ban", "delayed", "brk_t", "sc_used", "klin_used", "frozen",
                 "looped", "jao_used", "ven_used", "list", "x", "sealed", "extra")

    def __init__(s):
        s.deck, s.hand, s.mana, s.grave, s.sh, s.board, s.delayed = [], [], [], [], [], [], []
        s.mused = 0          # タップしているマナの枚数
        s.ent = s.spl = s.drawn = 0
        s.fp = s.zen_used = s.gc_used = s.final_used = s.protect = s.sc_used = s.klin_used = False
        s.final_turn = -1      # ファイナル革命を使ったターン番号（「そのターン1回」の判定用）
        s.frozen = s.looped = s.jao_used = s.ven_used = False
        s.nosmall = s.nolow = 0
        s.ban = -1
        s.brk_t = 0
        s.list = None
        s.x = {}
        s.sealed = []        # 封印されてバトルゾーンから外れたカード：[(U, 封印の数)]
        s.extra = 0          # もらった追加ターンの数

    def copy(s):
        n = P.__new__(P)
        n.deck = s.deck[:]
        n.hand = s.hand[:]
        n.mana = s.mana[:]
        n.grave = s.grave[:]
        n.sh = s.sh[:]
        n.board = [u.copy() for u in s.board]
        n.delayed = s.delayed[:]
        n.mused = s.mused
        n.ent = s.ent
        n.spl = s.spl
        n.drawn = s.drawn
        n.fp = s.fp
        n.zen_used = s.zen_used
        n.gc_used = s.gc_used
        n.final_used = s.final_used
        n.final_turn = s.final_turn
        n.protect = s.protect
        n.sc_used = s.sc_used
        n.klin_used = s.klin_used
        n.frozen = s.frozen
        n.looped = s.looped
        n.jao_used = s.jao_used
        n.ven_used = s.ven_used
        n.nosmall = s.nosmall
        n.nolow = s.nolow
        n.ban = s.ban
        n.brk_t = s.brk_t
        n.list = s.list
        n.x = dict(s.x)
        n.sealed = [(u.copy(), m) for u, m in s.sealed]
        n.extra = s.extra
        return n


def civs(p):
    return set("".join([MCIV[k] for k in p.mana]))


class Game:
    def __init__(s, da, db, rng, first=0, log=False):
        s.rng = rng
        s.P = [P(), P()]
        for pi, (p, d) in enumerate(zip(s.P, (da, db))):
            cards = [k for k in sorted(d) for _ in range(d[k])]
            rng.shuffle(cards)
            p.list = d
            for gk in sorted(GAMESTART):          # 禁断など、はじめから場に置くカード
                if gk in d:
                    GAMESTART[gk](s, pi, cards)
            p.sh = [(cards.pop(), False) for _ in range(5)]
            p.hand = [cards.pop() for _ in range(5)]
            p.deck = cards
        s.first = first
        # 除去などで相手のどれを選ぶか。プレイヤーごとに持つ（片方だけ変えて勝率を測れるように）
        s.tgtmode = [TARGET_THREAT, TARGET_THREAT]
        s.tp = first
        s.turn = 0
        s.phase = "C"
        s.over = False
        s.winner = None
        s.how = ""
        s.stop = False
        s.atk = None
        s.spc = None        # いま唱えている呪文のコスト（「コストN以下の呪文では選ばれない」の判定用）
        s.log = [] if log else None
        s.dry = 0              # >0 の間は「打てる手を数えているだけ」（観測だけの誘発を止める）
        s.trig = [0, 0]        # 盾から使えた受けの回数
        s.fa = [0, 0]          # 相手プレイヤーをはじめて攻撃したターン（自分の何ターン目か）
        s.chg = [0, 0]         # 革命チェンジの回数
        s.loopt = [0, 0]       # ループを起動したターン
        s.hist = None          # None 以外なら、出来事を (何が, 誰が, カード) で書き留める
        s.dcount = [0, 0]      # このターン、各プレイヤーのクリーチャーが破壊された数（ターンのはじめに0）
        s.dcby = False         # 直前の「手札を捨てる」が相手の能力によるものか（マッドネスの判定用）
        s.atktgt = None        # いま攻撃している相手（プレイヤーへの攻撃なら None）
        s.start_turn()         # ※盤面を見るだけでは取りこぼす「一瞬の出来事」を測るため（goals.py の entered / played）

    def clone(s, rng=None):
        g = Game.__new__(Game)
        g.rng = rng or s.rng
        g.P = [s.P[0].copy(), s.P[1].copy()]
        g.first = s.first
        g.tgtmode = s.tgtmode[:]
        g.tp = s.tp
        g.turn = s.turn
        g.phase = s.phase
        g.over = s.over
        g.winner = s.winner
        g.how = s.how
        g.stop = False
        g.atk = None
        g.spc = None
        g.dry = 0              # 複製した盤面では、手を数えている途中ではない
        g.log = None
        g.trig = s.trig[:]
        g.fa = s.fa[:]
        g.chg = s.chg[:]
        g.loopt = s.loopt[:]
        # 出来事の記録は**写して**持たせる。共有すると試し打ちが本番の記録を汚し、
        # None にすると試し打ちの盤面から「この試合で出た」が見えなくなる（先読みが効かなくなる）。
        g.hist = None if s.hist is None else s.hist[:]
        g.dcount = s.dcount[:]
        g.dcby = s.dcby
        g.atktgt = None
        return g

    # ------------------------------------------------------------------ 補助
    def ev(s, msg):
        if s.log is not None:
            s.log.append((s.turn, s.tp, msg))

    def tap_cre(s, i, u):
        """クリーチャーをタップする（「タップした時」の誘発をここ1か所で見る）"""
        if u.tap:
            return
        u.tap = True
        if TAPWATCH:
            for f in TAPWATCH:
                f(s, i, u)

    def note(s, what, i, k):
        """出来事を書き留める（s.hist が有効な時だけ）。

        盤面を見るだけでは測れない「一瞬の出来事」のため。
        what は enter（場に出た）／surface（進化元や下のカードが表に出た＝退化・侵略・革命チェンジなど）／
        cast（呪文を唱えた）。goals.py の entered／played がこれを読む。"""
        if s.hist is not None:
            s.hist.append((what, i, k))

    def myturn(s, i):
        return (s.turn + 1) // 2 if i == s.first else s.turn // 2

    def abi(s, i, u):
        """このカードの能力が働くか（《あたりポンの助》のように能力をすべて無視された状態でないか）"""
        return not (ABILOCK and any(f(s, i, u) for f in ABILOCK))

    # ------------------------------------------------------------------ G・リンク
    def parts(s, u):
        """このクリーチャーを構成しているカード。G・リンクしていなければ自分1枚だけ。

        G・リンクしたゴッドは**1体のクリーチャー**として扱い、パワーとコストは合計、
        能力と文明は併せ持つ（公式の決まり）。離れる時は、**そのうち1枚だけ**が離れる。"""
        return (u,) if not u.link else (u, *u.link)

    def kw(s, u, name):
        """キーワード（blocker／sa／mach／noatk など）を、リンクしたカードの**どれかが持てば持つ**"""
        if not u.link:
            return getattr(u.c, name)
        return any(getattr(z.c, name) for z in s.parts(u))

    def can_link(s, i, u, base):
        """u を base にG・リンクできるか"""
        g = GODLINK.get(u.k)
        if g is None or base.c.kind != "C":
            return False
        pos, mates = g
        if base.k == u.k or any(z.k == u.k for z in base.link):
            return False                        # 同じカードは2枚つなげない
        if mates and not any(z.k in mates for z in s.parts(base)):
            return False
        if GODLINK.get(base.k) is None and not any(GODLINK.get(z.k) for z in s.parts(base)):
            return False                        # 相手もゴッドであること
        return base in s.P[i].board

    def god_link(s, i, u, base):
        """u を base の横につなぐ（u はバトルゾーンに単体では置かない）。

        u がすでに別のゴッドとリンクしていたら、その仲間も base に移す（平らにする）。
        入れ子にすると内側のリンクが見えなくなる。"""
        inner = u.link
        u.link = []
        base.link.append(u)
        base.link.extend(inner)
        base.sick = False                       # リンクしているクリーチャーは召喚酔いしない
        for z in base.link:
            z.sick = False
        s.ev(f"　G・リンク：{base.c.name} ＋ {u.c.name}")
        s.note("surface", i, u.k)

    def has(s, i, k):
        for u in s.P[i].board:
            if u.k == k:
                return True
            for z in u.link:
                if z.k == k:
                    return True
        return False

    def ncre(s, i):
        return sum(1 for u in s.P[i].board if u.c.kind == "C")

    def gc(s, i):
        return sum(1 for k in s.P[i].grave if CARD[k].kind == "C")

    def win(s, i, how):
        if s.over:
            return
        for f in LOSEREP:                    # 負ける側が、負けを別のことで置き換えられるか
            if f(s, 1 - i, how):
                s.ev(f"　{how} を置き換えて負けなかった")
                return
        s.over = True
        s.winner = i
        s.how = how
        s.ev(f"★ プレイヤー{i}の勝ち（{how}）")

    def deckout(s, i):
        """山札が0枚になった"""
        p = s.P[i]
        if p.protect or s.has(i, "valhalla"):
            return
        s.win(1 - i, "山札切れ")

    def power(s, i, u, atk=False):
        if u.link:                               # G・リンク：パワーは合計
            return sum(s._power1(i, z, atk) for z in s.parts(u))
        return s._power1(i, u, atk)

    def _power1(s, i, u, atk=False):
        k = u.k
        w = u.c.power + u.pw
        if u.hyper and k in HYPER_POW:
            w += HYPER_POW[k]
        if k == "crossfire":
            if atk:
                w += 1000000
        elif k == "shuto":
            if s.tp == i:
                w += 4000
        elif k == "koori":
            if u.under:
                w += 1000 * len(s.P[i].hand)
        f = POWERX.get(k)
        if f is not None:
            w += f(s, i, u, atk)
        for f in AURAP:
            w += f(s, i, u, atk)
        return w

    def brk(s, i, u):
        if u.link:                               # G・リンク：いちばん多く割れるカードに合わせる
            return max(s._brk1(i, z) for z in s.parts(u))
        return s._brk1(i, u)

    def _brk1(s, i, u):
        k = u.k
        f = BRKX.get(k)
        if f is not None:
            r = f(s, i, u)
            if r is not None:
                return r
        if k == "derbande" or k == "koori":
            b = 1 + s.power(i, u, True) // 6000
        elif u.hyper and k in HYPER_POW:
            b = HYPER_BRK.get(k, 2)
        else:
            b = u.c.brk
        for f in BRKPLUS:
            b += f(s, i, u)
        return b

    def val(s, u):
        v = PRI[u.k] + len(u.under) + (3 if u.hyper else 0)
        for f in VALADJ:
            v += f(s, u)
        return v

    def threat(s, by, u):
        """by から見た、相手のクリーチャー u の「危なさ」。

        もとは除去の相手を `max(val)` ＝ **いちばんコスト（重要度）の高い相手**で選んでいた。
        それはデュエマのプレイングとしては粗い。本当に消したいのは「自分を殴ってくる面」で、
        重いだけで寝ている・殴ってこないクリーチャーは後回しでよい。
        そこで、重要度に「自分に向かってくる力」を足したものを使う。

          ・次の相手のターンに自分（プレイヤー）を殴れるなら、打点ぶん重く見る
          ・ブロッカーは自分の攻めを止めるので重く見る
          ・パワーも少しだけ見る（バトルで勝てない面が残る）

        `g.tgtmode[by] = False` にすると、その人だけ もとの「いちばん重要度の高い相手」に戻る。
        プレイヤーごとに持たせてあるので、**同じ対戦の中で片方だけ変えて勝率を測れる**
        （skill.py --target）。既定は engine3.TARGET_THREAT。"""
        v = s.val(u)
        if u.c.kind != "C":
            return v
        o = 1 - by
        w = THREAT_W
        v += w["power"] * s.power(o, u)
        if s.kw(u, "blocker"):
            v += w["blk"]
        if not u.tap:
            v += w["ready"]
            ign = bool(NOATKIGN) and any(f(s, o, u) for f in NOATKIGN)
            nop = (s.kw(u, "noatkp") and not ign) or bool(NOATKPX and any(f(s, o, u) for f in NOATKPX))
            if not (s.kw(u, "noatk") and not ign) and not nop:
                v += w["atkp"] + w["brk"] * s.brk(o, u)
        return v

    def target(s, by, pred=None, kinds="C"):
        """プレイヤー by が相手のカードを1つ選ぶ。ジャストダイバーは選べない。

        「可能ならこれを選ぶ」（同期の妖精など）は、**条件（pred）で絞り終えた候補**に対して
        MUSTPICK で決める。条件に合わないなら選ばされないのが「可能なら」の意味なので、
        候補を絞る前に横取りしてはいけない。"""
        cands = []
        for u in s.P[1 - by].board:
            if u.jd or u.c.kind not in kinds:
                continue
            if TGTLOCK and any(f(s, by, u) for f in TGTLOCK):
                continue
            if pred is not None and not pred(u):
                continue
            cands.append(u)
        if not cands:
            return None
        best = None
        for f in MUSTPICK:                         # 可能なら選ばされるもの
            best = f(s, by, cands)
            if best is not None:
                break
        if best is None:
            best = max(cands, key=(lambda u: s.threat(by, u)) if s.tgtmode[by] else s.val)
        if CHOSENWATCH and not s.dry:              # 選ばれた1つだけに「選ばれた時」を通す
            for f in CHOSENWATCH:                  # （手を数えているだけの時は誘発させない）
                f(s, 1 - by, best, by)
        return best

    # ------------------------------------------------------------------ カードの移動
    def draw(s, i, n=1):
        p = s.P[i]
        for _ in range(n):
            if s.over or not p.deck:
                return
            if len(p.deck) == 1 and s.has(i, "shako"):
                s.win(i, "シャコガイル")
                return
            p.hand.append(p.deck.pop())
            p.drawn += 1
            if DRAWWATCH:
                for f in DRAWWATCH:
                    f(s, i, p.hand[-1])
            if p.drawn >= 2 and p.hand:
                for u in s.P[1 - i].board:
                    if u.k == "vamilia" and u.hyper:
                        k = min(p.hand, key=PRI.get)
                        p.hand.remove(k)
                        s.grave_put(i, k)
                        break
            if not p.deck:
                s.deckout(i)

    def add_mana(s, i, k, tapped=False, src="other"):
        if src != "hand" and MANAREP and any(f(s, i, k, src) for f in MANAREP):
            s.ev(f"　{CARD[k].name} はマナゾーンのかわりに墓地へ")
            s.grave_put(i, k)
            return
        p = s.P[i]
        p.mana.append(k)
        if tapped or MULTI[k]:
            p.mused += 1
        for f in MANAIN:
            if not s.over:
                f(s, i, k, src)

    def take_mana(s, i, k):
        p = s.P[i]
        p.mana.remove(k)
        if p.mused > len(p.mana):
            p.mused = len(p.mana)
        for f in MANALEAVE:
            if not s.over:
                f(s, i, k)

    def ramp(s, i, n=1, tapped=True):
        """山札の上からマナへ。相手にロビンフッドがいると、かわりに山札の下へ"""
        p = s.P[i]
        robin = s.has(1 - i, "robin")
        for _ in range(n):
            if len(p.deck) <= 1:
                return
            k = p.deck.pop()
            if robin:
                p.deck.insert(0, k)
            else:
                s.add_mana(i, k, tapped, src="deck")

    def mill(s, i, n):
        """山札の上から墓地へ。戻り値は置かれたカード"""
        p = s.P[i]
        robin = s.has(1 - i, "robin")
        out = []
        for _ in range(n):
            if len(p.deck) <= 1:
                break
            k = p.deck.pop()
            if robin:
                p.deck.insert(0, k)
            else:
                out.append(k)
                s.grave_put(i, k)
        return out

    def grave_put(s, i, k):
        p = s.P[i]
        c = CARD[k]
        if not p.sc_used and c.kind == "C" and c.cost <= 5 and not (c.evo and not c.neo) and s.has(i, "scarlet"):
            if s.fate(i, k, "grave", False) == "ok":       # スカーレッドゾーン：墓地に置かれたコスト5以下を出す（各ターン1度）
                p.sc_used = True
                s.enter(i, k, "grave", False)
                return
        p.grave.append(k)

    def put_zone(s, i, k, dest):
        p = s.P[i]
        if dest == "hand":
            p.hand.append(k)
        elif dest == "mana":
            s.add_mana(i, k)
        elif dest == "grave":
            s.grave_put(i, k)
        elif dest == "deck":
            p.deck.insert(0, k)
        elif dest == "decktop":
            p.deck.append(k)                 # 山札の上（draw は末尾から取る）
        else:
            p.sh.append((k, False))
            s.shield_added(i)
            for f in SHIELDIN:
                f(s, i, k, False)

    def discard(s, i, k, by_opp=False):
        """手札を1枚捨てる。by_opp＝相手の能力で捨てさせられたか（自分で払うコストと区別する）"""
        s.dcby = by_opp
        f = DISCARDX.get(k)
        if f is not None and f(s, i, k):
            return
        s.P[i].hand.remove(k)
        s.grave_put(i, k)
        for g in DISCARDWATCH:
            if not s.over:
                g(s, i, k)

    def discard_random(s, i, by_opp=True):
        """手札からでたらめに1枚捨てさせる。by_opp＝相手の能力によるもの（マッドネスの判定用）。
        いまのところ呼び出しは全部「相手に捨てさせる」なので既定を True にしている。"""
        p = s.P[i]
        if p.hand:
            k = p.hand[s.rng.randrange(len(p.hand))]
            s.discard(i, k, by_opp)

    def dig(s, i, n, pred, rest="bottom"):
        """山札の上n枚から、条件に合う1枚を手札へ。残りは山札の下か墓地へ"""
        p = s.P[i]
        n = min(n, len(p.deck) - 1)
        if n <= 0:
            return None
        top = [p.deck.pop() for _ in range(n)]
        best, bv = None, -99
        for k in top:
            if pred(k):
                v = PRI[k] - 3 * p.hand.count(k)
                if v > bv:
                    best, bv = k, v
        if best is not None:
            top.remove(best)
            p.hand.append(best)
        if rest == "grave" and not s.has(1 - i, "robin"):
            for k in top:
                s.grave_put(i, k)
        else:
            for k in top:
                p.deck.insert(0, k)
        return best

    # ------------------------------------------------------------------ シールド
    def add_shield(s, i, k=None, up=False):
        """シールドを増やす。自分のターン中、相手にフウジン天がいると置けない"""
        p = s.P[i]
        if s.tp == i and s.has(1 - i, "fujin"):
            return False
        if k is None:
            if len(p.deck) <= 1:
                return False
            if s.has(1 - i, "robin"):
                p.deck.insert(0, p.deck.pop())
                return False
            k = p.deck.pop()
        p.sh.append((k, up))
        s.shield_added(i)
        for f in SHIELDIN:
            f(s, i, k, up)
        return True

    def shield_added(s, i):
        p = s.P[i]
        for u in p.board[:]:
            if u.k == "zaze":
                u.tap = False
                t = s.target(i, lambda x: not x.tap and not x.c.noatk)
                if t is not None:
                    s.tap_cre(1 - i, t)
                    t.frz = 1
                else:
                    s.draw(i)
            elif u.k == "chakra":
                t = s.target(i, lambda x: not x.tap) or s.target(i)
                if t is not None:
                    s.tap_cre(1 - i, t)
                    t.frz = 1

    def shield_left(s):
        """どちらかのシールドが離れた：Zラッシュ持ちがハイパーになる"""
        for p in s.P:
            for u in p.board:
                if u.c.zrush:
                    u.hyper = True

    def shield_out(s, i, j, how="effect"):
        """シールド j 枚目をシールドゾーンから取り除くだけ（行き先はまだ決めない）。

        **番号を使うので、取り除きは必ず先にやる**。
        誘発（SHIELDOUT や BREAKREP）の中で `p.sh` が動くため、あとで番号を使うと範囲外になる
        （実際に `_self_break` が IndexError で落ちた）。
        返り値：(カードのキー, 表向きだったか)。j が範囲外なら None。"""
        p = s.P[i]
        if not (0 <= j < len(p.sh)):
            return None
        k, up = p.sh[j]
        del p.sh[j]
        s.shield_left()
        for g in SHIELDOUT:
            g(s, i, k, up, how)
        return (k, up)

    def flip_shield(s, i, j, up):
        """シールドの表裏を変える（表向きにする・裏向きに戻す）。範囲外なら何もしない"""
        p = s.P[i]
        if 0 <= j < len(p.sh):
            p.sh[j] = (p.sh[j][0], bool(up))
            return True
        return False

    def shield_to(s, i, k, up, dest):
        """シールドゾーンから離れたカードを dest へ送る。SHIELDDEST（シールド・ゴー）が行き先を変える。
        返り値：実際の行き先"""
        p = s.P[i]
        f = SHIELDDEST.get(k)
        if f is not None:
            dest = f(s, i, k, up, dest) or dest
        for g in SHIELDREP:                      # S・バック：手札に加えるかわりに捨てて別のことをする
            nd = g(s, i, k, up, dest)
            if nd is not None:
                dest = nd
                break
        if dest == "hand":
            p.hand.append(k)
        elif dest == "grave":
            s.grave_put(i, k)
        elif dest == "mana":
            s.add_mana(i, k)
        elif dest == "deck":
            p.deck.insert(0, k)
        elif dest == "decktop":
            p.deck.append(k)
        return dest

    def take_shield(s, i, j, dest, by_break=False):
        """シールド j 枚目をシールドゾーンから離して dest へ送る（取り除き＋行き先をまとめたもの）。

        シールドゾーンの出口はここ1か所にまとめてある。`p.sh` を直接いじらずこれを使うこと
        （そうしないと SHIELDOUT と SHIELDDEST が通らない）。
        返り値：(カードのキー, 表向きだったか, 実際の行き先)。j が範囲外なら None。"""
        r = s.shield_out(i, j, "break" if by_break else dest)
        if r is None:
            return None
        k, up = r
        return (k, up, s.shield_to(i, k, up, dest))

    def break_sh(s, ai, n):
        di = 1 - ai
        d = s.P[di]
        for j, (k, up) in enumerate(d.sh):
            if up and k == "saint":                 # セイント・キャッスル：この1枚だけが割れて手札に戻る
                del d.sh[j]
                d.hand.append("saint")
                s.shield_left()
                s.ev("　セイント・キャッスルが身代わり")
                return
        for f in BREAKPRE:                     # シールド・セイバー等：割られる枚数を減らせる
            n = f(s, ai, di, n)
            if n <= 0:
                return
        n = min(n, len(d.sh))
        up_i = [j for j, x in enumerate(d.sh) if x[1]][:n]
        dn_i = [j for j, x in enumerate(d.sh) if not x[1]]
        need = n - len(up_i)
        idx = sorted(set(up_i + (dn_i[len(dn_i) - need:] if need > 0 else [])))
        broken = [d.sh[j] for j in idx]
        d.brk_t += n
        for j in reversed(idx):                    # 取り除きは先に、後ろから（番号がずれないように）
            s.shield_out(di, j, "break")
        for f in BREAKWATCH:
            f(s, ai, di, n)
        s.ev(f"　シールドを{n}枚ブレイク（残り{len(d.sh)}）")
        # BREAKREP は「先に True を返した1枚が割れたシールド全部を処理する」古い形。
        # 1枚ごとの行き先は SHIELDDEST（shield_to の中）で決められるので、新しいカードはそちらを使う。
        for f in BREAKREP:
            if f(s, ai, di, broken):
                return
        for k, up in broken:
            s.shield_to(di, k, up, "grave" if (up and CARD[k].kind == "G") else "hand")
        for k, up in broken:
            if s.over or s.stop:
                break
            if not up and k in d.hand:
                s.trigger(di, k)

    def trigger(s, di, k):
        """シールドから手札に来たカードの受け（S・トリガー／G・ストライク）"""
        d = s.P[di]
        c = CARD[k]
        ai = 1 - di
        f = SHIELDCAST.get(k)
        if f is not None and f(s, di, k, len(d.sh)):
            # スーパー・S・トリガー：シールドから手札に加える時に、その場で処理しきった
            # （nsh＝その時のシールドの枚数。「シールドが0ならS能力も得る」の判定に使う）
            return
        extra = bool(TRIGOK) and any(f(s, di, k) for f in TRIGOK)
        if c.kind == "C" and (c.trig or extra or (k == "viride" and s.ncre(ai) >= 3)):
            if s.fate(di, k, "hand", True) == "ok":
                d.hand.remove(k)
                s.trig[di] += 1
                s.ev(f"　S・トリガー：{c.name}")
                s.enter(di, k, "hand", True)
            return
        if c.kind == "S" and (c.trig or extra):
            if k == "saitan" and not s.saitan_ok(di):
                return
            if s.spell_ok(di, c.cost, k):
                d.hand.remove(k)
                s.trig[di] += 1
                s.ev(f"　S・トリガー：{c.name}")
                s.cast(di, k)
            return
        if c.kind == "T" and (c.trig or extra):
            if d.ban != c.cost:
                d.hand.remove(k)
                s.trig[di] += 1
                s.ev(f"　S・トリガー：{c.name}")
                s.place_tama(di, k)
            return
        if c.twin and c.twin[2]:
            if k == "takkyu" and not s.takkyu_ok(di):
                return
            if s.spell_ok(di, c.twin[0], k):
                d.hand.remove(k)
                s.trig[di] += 1
                s.ev(f"　S・トリガー：{c.name}（呪文側）")
                s.cast(di, k, True)
            return
        if c.gs or (GSOK and any(f(s, di, k) for f in GSOK)):
            if s.atk is not None and s.atk.k in NOGS:
                return
            if s.atk is not None and NOGSX and any(f(s, 1 - di, s.atk) for f in NOGSX):
                return
            t = s.target(di, lambda x: not x.tap and not x.c.noatk and x.c.kind == "C")
            if t is not None:
                t.lock = s.turn
                s.trig[di] += 1
                s.ev(f"　G・ストライク：{c.name} → {t.c.name}")
            for g in GSWATCH:
                if not s.over:
                    g(s, di, k)

    # ------------------------------------------------------------------ 出る／離れる
    def limit(s, i):
        """プレイヤー i がこのターン出せるクリーチャーの数の上限（相手のメタによる）"""
        lim = 99
        for u in s.P[1 - i].board:
            if "LIMIT2" in u.c.meta:
                if lim > 2:
                    lim = 2
            elif u.k == "ichion" and u.under:
                lim = 1
        return lim

    def manaexec(s, i):
        """手札・山札以外から使えず、出せない（相手のポッピなど）"""
        return s.has(1 - i, "poppi") or bool(MANAEXEC and any(f(s, i) for f in MANAEXEC))

    def fate(s, i, k, src, summon, mn=None):
        """プレイヤー i のクリーチャー k が出ようとした時の行き先。
        ok＝出る／no＝出せない（元の場所に残る）／mana・grave＝かわりにそこへ／delay＝次のターンに遅れる"""
        c = CARD[k]
        p = s.P[i]
        o = s.P[1 - i]
        if p.ban == c.cost:
            return "no"
        if p.nosmall == 1 and c.power <= 5000:
            return "no"
        if summon and p.nolow == 1 and c.cost <= 2:
            return "no"
        if p.ent >= MAXENT:
            return "no"
        mine = s.tp == i
        lim = 99
        res = "ok"
        for u in o.board:
            m = u.c.meta
            uk = u.k
            if uk == "ichion":
                if u.under:
                    lim = 1
            elif not m:
                if uk == "venom" or uk == "robin":
                    pass
                continue
            elif "LIMIT2" in m:
                if lim > 2:
                    lim = 2
            elif uk == "poppi":
                if src != "hand" and src != "deck":
                    return "no"
            elif uk == "zoro":
                if mine and src != "zone" and res == "ok":
                    res = "delay"
            elif uk == "magnum":
                if not mine and res == "ok":
                    res = "grave"
            elif uk == "kabocha":
                if c.cost > (len(p.mana) if mn is None else mn) and res == "ok":
                    res = "mana"
            elif uk == "tokoshie":
                if src != "hand" and res == "ok":
                    res = "mana"
            elif uk == "testa":
                if mine and not summon and res == "ok":
                    res = "grave"
        if FATEX:
            for j in (1 - i, i):            # 相手の場だけでなく自分の場も見る（ドリーム・クリーチャーなど）
                for u in s.P[j].board:
                    f = FATEX.get(u.k)
                    if f is not None:
                        res = f(s, j, u, i, k, src, summon, res)
                        if res == "no":
                            return "no"
        if p.ent >= lim:
            return "no"
        if not summon and res == "ok":
            for x, up in o.sh:
                if up and x == "hustle":
                    return "mana"
        return res

    def enter(s, i, k, src, summon, on=None, sa=False, pw=0):
        """クリーチャーを出す。カードは呼び出し側が元のゾーンから取り除いておく
        （出たカードの u.x["src"] に、どこから出たかが入る）"""
        p = s.P[i]
        o = s.P[1 - i]
        f = s.fate(i, k, src, summon)
        if f != "ok":
            if f == "mana":
                s.add_mana(i, k, src=src)      # どこから出ようとしたかを引き継ぐ（ニンギョの判定用）
            elif f == "grave":
                s.grave_put(i, k)
            elif f == "delay":
                p.delayed.append(k)
            elif src == "mana":
                p.mana.append(k)
            elif src == "grave":
                p.grave.append(k)
            elif src == "deck":
                p.deck.insert(0, k)
            else:
                p.hand.append(k)
            s.ev(f"　{CARD[k].name} は出られない（{f}）")
            return None
        u = U(k)
        if on is not None and on in p.board:
            j = p.board.index(on)
            u.under = [on.k] + on.under
            u.tap = on.tap
            u.frz = on.frz
            if on.k == "aroma":
                u.unb = True
            p.board[j] = u
        else:
            p.board.append(u)
        u.sa = sa
        u.pw = pw
        u.x["summoned"] = summon
        u.x["src"] = src
        p.ent += 1
        # 「出た」はここで書き留める。この直後に進化元として下に入る（＝盤面を見ても
        # 一度も立っていないように見える）カードを取りこぼさないため。
        s.note("enter", i, k)
        if k == "zaze":
            s.tap_cre(i, u)
        else:
            for x in o.board:
                if x.k == "venom" and x.hyper:
                    s.tap_cre(i, u)
                    break
        if s.tp == i:
            s.first_play(i, u.c.cost)
        trig_ok = not (ENTERTRIGLOCK and any(f(s, i, u) for f in ENTERTRIGLOCK)) and s.abi(i, u)
        fn = ENTER.get(k) if trig_ok else None
        if fn is not None:
            fn(s, i, u)
        if trig_ok:
            for f in ENTERWATCH:
                if not s.over:
                    f(s, i, u)
        if "puppet" in u.c.races and not p.klin_used and s.has(i, "klin"):
            p.klin_used = True
            s.draw(i)
        if k == "pon":
            if summon:
                for j in (0, 1):
                    if s.has(j, "teacher"):
                        s.draw(j)
            if u in p.board:
                s.leave(i, u, "grave", destroy=True)
        return u

    def leave(s, i, u, dest, by_opp=False, destroy=False, burst=True):
        """カードが場を離れる。離れたら True"""
        p = s.P[i]
        if u not in p.board:
            return False
        if by_opp and p.protect and u.c.kind == "C":
            return False
        for f in LEAVEREP:
            if f(s, i, u, dest, destroy):
                return False
        for f in LEAVEDEST:
            nd = f(s, i, u, dest, destroy)
            if nd is not None:
                dest = nd
                destroy = False
                break
        if u.c.gneo and u.under:                 # G-NEO：かわりに下のカードがすべて離れる
            for k in u.under:
                s.put_zone(i, k, "grave" if dest == "shield" else dest)
            u.under = []
            return False
        if u.link:
            # G・リンクしているクリーチャーが離れる時は、**構成しているカードのうち1枚だけ**が離れる
            # （公式の決まり）。どれを選ぶかは持ち主なので、全デッキ共通の「重要度のいちばん低い札」で決める。
            ps = list(s.parts(u))
            z = min(ps, key=lambda x: PRI.get(x.k, 0))
            if z is u:                           # 頭が離れる：次のカードを頭に繰り上げる
                nu = u.link[0]
                nu.link = u.link[1:]
                nu.tap, nu.sick, nu.frz = u.tap, u.sick, u.frz
                p.board[p.board.index(u)] = nu
            else:
                u.link.remove(z)
            s.put_zone(i, z.k, dest)
            for k in z.under:
                s.put_zone(i, k, "grave" if dest == "shield" else dest)
            s.ev(f"　G・リンクのうち {z.c.name} だけが離れる")
            f = LEFT.get(z.k)
            if f is not None and not s.over:
                f(s, i, z, dest)
            if destroy:
                s.dcount[i] += 1
                f = DESTROYED.get(z.k)
                if f is not None and not s.over:
                    f(s, i, z)
            for f in LEAVEWATCH:
                if not s.over:
                    f(s, i, z, dest, destroy)
            return True
        if u.k == "zoro":
            dest = "hand"
        if destroy:
            if u.k == "poppi" and p.sh:          # エスケープ
                for j in range(len(p.sh) - 1, -1, -1):
                    if not p.sh[j][1]:
                        p.hand.append(p.sh.pop(j)[0])
                        s.shield_left()
                        return False
            if s.has(i, "dokkoi"):
                dest = "hand"
        p.board.remove(u)
        s.put_zone(i, u.k, dest)
        for k in u.under:
            s.put_zone(i, k, "grave" if dest == "shield" else dest)
        ok = s.abi(i, u)
        f = LEFT.get(u.k) if ok else None
        if f is not None and not s.over:
            f(s, i, u, dest)
        if destroy:
            s.dcount[i] += 1
            f = DESTROYED.get(u.k) if ok else None
            if f is not None and not s.over:
                f(s, i, u)
        for f in LEAVEWATCH:
            if not s.over:
                f(s, i, u, dest, destroy)
        if u.k == "douki" and burst and dest != "deck" and dest != "shield" and not s.over:
            if s.spell_ok(i, 4, "douki"):        # メガ・ラスト・バースト：呪文側をただで唱える
                s.ev("　同期の妖精が離れ、ド浮きの動悸")
                p.spl += 1
                sp_douki(s, i)
        return True

    def first_play(s, i, cost):
        """自分のターンにはじめてカードを出したか唱えた：相手のウィリデが反応する"""
        p = s.P[i]
        if p.fp or s.tp != i:
            return
        p.fp = True
        o = s.P[1 - i]
        for u in o.board[:]:
            if u.k == "viride" and u in o.board:
                s.draw(1 - i)
                best, bv = None, -1
                for k in sorted(set(o.hand)):
                    c = CARD[k]
                    if c.kind == "C" and c.cost <= cost and not (c.evo and not c.neo) and PRI[k] > bv:
                        if s.fate(1 - i, k, "hand", False) == "ok":
                            best, bv = k, PRI[k]
                if best is not None:
                    o.hand.remove(best)
                    s.ev(f"　ウィリデの効果で {CARD[best].name}")
                    s.enter(1 - i, best, "hand", False)

    def noncre(s, i):
        """クリーチャーでないカードを実行した：自分のターンなら der'Bande が強くなる"""
        if s.tp == i:
            for u in s.P[i].board:
                if u.k == "derbande":
                    u.pw += 3000
                    u.unb = True

    def _aura(s, i, k, twin=False):
        """全体のコスト補正の合計。twin＝ツインパクトの呪文側として聞いている。

        補正を書く側は `fn(s, i, k, twin=False)` で受けると、ツインパクトの呪文側かどうかが分かる
        （古い `fn(s, i, k)` の書き方もそのまま動く）。"""
        n = 0
        for g in SPCOSTAURA:
            try:
                n += g(s, i, k, twin)
            except TypeError:
                n += g(s, i, k)
        return n

    def spcost(s, i, k):
        """呪文・クロスギアの実際のコスト（G・ゼロや別コストを見る）。
        SPCOSTAURA は「自分の〈種族〉のカードを使うコストを1少なく」のような全体の補正。"""
        f = SPCOST.get(k)
        n = CARD[k].cost if f is None else f(s, i, k)
        return max(0, n + s._aura(i, k))

    def ncost(s, i, k, base=None, twin=False):
        """クリーチャーでないカード（タマシード・城・クロスギア・ツインパクトの呪文側）を使うコスト。

        もとの値（base）に、全体のコスト補正（SPCOSTAURA）を足して返す。
        クリーチャーの召喚は ccost（COSTAURA）、呪文は spcost が見るので、
        「自分の〈種族〉の**カード**を使うコストを1少なくする」はこの3本で全部まかなえる。"""
        c = CARD[k]
        n = (c.twin[0] if twin else c.cost) if base is None else base
        return max(0 if twin else 1, n + s._aura(i, k, twin))

    def seal(s, i, u, m=1):
        """クリーチャーに封印を m つ付ける（封印されている間はバトルゾーンにないものとして扱う）"""
        p = s.P[i]
        if u not in p.board:
            return
        got = 0
        for _ in range(m):
            if len(p.deck) <= 1:
                break
            u.x.setdefault("sealcards", []).append(p.deck.pop())
            got += 1
        if not got:
            return
        p.board.remove(u)
        p.sealed.append((u, got))
        s.ev(f"　封印：{u.c.name} に封印{got}つ")

    def unseal(s, i, civ=None):
        """文明が合う封印を1つ外す。外し切れたらバトルゾーンに戻る。外したら True"""
        p = s.P[i]
        for j, (u, m) in enumerate(p.sealed):
            if civ is not None and not (set(civ) & set(u.c.civ)):
                continue
            cs = u.x.get("sealcards") or []
            if cs:
                p.grave.append(cs.pop())
            m -= 1
            if m <= 0:
                del p.sealed[j]
                p.board.append(u)
                s.ev(f"　封印が外れた：{u.c.name}")
                f = ENTER.get(u.k) if u.x.pop("sealflip", False) else None
                if f is not None:
                    f(s, i, u)
            else:
                p.sealed[j] = (u, m)
            return True
        return False

    def spell_ok(s, i, cost, k=None):
        """その呪文を唱えられるか。k＝呪文のキー（文明・種族で止める能力のために渡す。省略可）"""
        p = s.P[i]
        if p.ban == cost:
            return False
        for f in SPELLLOCK:
            try:
                if f(s, i, cost, k):
                    return False
            except TypeError:                    # 古い書き方 fn(s, i, cost) も受ける
                if f(s, i, cost):
                    return False
        for u in s.P[1 - i].board:
            if u.k == "ichion":
                if p.spl >= 1:
                    return False
            elif u.k == "chakra":
                if u.hyper and cost <= 5:
                    return False
        return True

    def cast(s, i, k, twin=False):
        """呪文を唱える。カードは呼び出し側が元のゾーンから取り除いておく"""
        p = s.P[i]
        c = CARD[k]
        p.spl += 1
        s.note("cast", i, k)
        s.first_play(i, c.twin[0] if twin else c.cost)
        prev = s.spc
        s.spc = c.twin[0] if twin else c.cost
        for f in SPELLWATCH:
            if not s.over:
                f(s, i, k)
        SPELL[k](s, i)
        s.spc = prev
        if k == "saitan" and "saitan" in p.hand:
            pass
        if k not in NOGRAVE:
            s.grave_put(i, k)
        if not c.twin:
            s.noncre(i)

    def place_tama(s, i, k):
        p = s.P[i]
        u = U(k)
        u.sick = False
        p.board.append(u)
        s.first_play(i, u.c.cost)
        s.noncre(i)
        fn = ENTER.get(k)
        if fn is not None:
            fn(s, i, u)
        for f in TAMAIN:
            if not s.over:
                f(s, i, u)
        if u in p.board and k not in STAY:
            for z in p.board:
                if z.k == "zen":                    # 創世竜の下に置く（シンカパワー）
                    p.board.remove(u)
                    z.under.append(k)
                    if k == "leviya":
                        e_leviya(s, i, None)
                    elif k == "parli":
                        s.ramp(i, 2)
                        if p.mana:
                            best = max(p.mana, key=PRI.get)
                            s.take_mana(i, best)
                            p.hand.append(best)
                    break

    def place_castle(s, i, k):
        if not s.add_shield(i, k, True):
            s.P[i].hand.append(k)
            return
        s.first_play(i, CARD[k].cost)
        s.noncre(i)
        if k == "hustle":
            s.ramp(i, 1)
        f = CASTLEX.get(k)
        if f is not None:
            f(s, i, k)

    def exec_free(s, i, k):
        """クリーチャーでないカードを、マナか手札からただで実行する（der'Bande）"""
        p = s.P[i]
        if k in p.mana and not s.manaexec(i):
            s.take_mana(i, k)
        elif k in p.hand:
            p.hand.remove(k)
        else:
            return
        kind = CARD[k].kind
        s.ev(f"　ただで実行：{CARD[k].name}")
        if kind == "S":
            s.cast(i, k)
        elif kind == "T":
            s.place_tama(i, k)
        else:
            s.place_castle(i, k)

    def free_opts(s, i):
        """der'Bande の攻撃時に実行できるカード"""
        p = s.P[i]
        out = []
        pool = set(p.hand)
        if not s.manaexec(i):
            pool |= set(p.mana)
        fuj = s.has(1 - i, "fujin")
        for k in sorted(pool):
            c = CARD[k]
            if c.cost > 4 or c.kind == "C" or p.ban == c.cost:
                continue
            if c.kind == "S":
                if not s.spell_ok(i, c.cost, k):
                    continue
            elif c.kind == "G" and fuj:
                continue
            out.append(k)
        return out

    # ------------------------------------------------------------------ バトル・攻撃
    def battle(s, ai, au, di, du):
        for f in BATTLESWAP:                       # スーパーガードマン：守る側がバトルする相手を差し替える
            nu = f(s, di, du, ai, au)
            if nu is not None and nu in s.P[di].board:
                s.ev(f"　{nu.c.name} が {du.c.name} のかわりにバトルする")
                du = nu
                break
        return s._battle(ai, au, di, du)

    def _battle(s, ai, au, di, du):
        ap = s.power(ai, au, True) + (2000 if au.k == "testa" else 0)
        dp = s.power(di, du) + (2000 if du.k == "testa" else 0)
        a_dies = ap <= dp or du.k == "kuzen"
        d_dies = dp <= ap or au.k == "kuzen"
        for f in BATTLEFX:
            a_dies, d_dies = f(s, ai, au, di, du, a_dies, d_dies)
        if d_dies:
            s.leave(di, du, "grave", destroy=True)
            if not a_dies and s.has(ai, "shuto"):
                s.draw(ai)
        if a_dies:
            s.leave(ai, au, "grave", destroy=True)
            if not d_dies and s.has(di, "shuto"):
                s.draw(di)

    def can_block(s, u):
        c = u.c
        if BLOCKLOCK and any(f(s, u) for f in BLOCKLOCK):
            return False
        if c.kind != "C" or u.tap or u.lock == s.turn:
            return False
        if ABILOCK:                              # 能力を無視されていればブロッカーでもなくなる
            for j in (0, 1):
                if u in s.P[j].board and not s.abi(j, u):
                    return False
        if s.kw(u, "blocker"):
            return True
        if any(z.k == "chakra" and u.hyper for z in s.parts(u)):
            return True
        return any(f(s, u) for f in BLOCKOK)

    def choose_block(s, di, ai, au, tu):
        d = s.P[di]
        ap = s.power(ai, au, True)
        lethal = tu is None and not d.sh and not d.protect
        win, any_ = None, None
        for b in d.board:
            if not s.can_block(b):
                continue
            if s.power(di, b) > ap and au.k != "kuzen":
                if win is None or s.val(b) < s.val(win):
                    win = b
            if any_ is None or s.val(b) < s.val(any_):
                any_ = b
        if win is not None:
            return win
        return any_ if lethal else None

    def change_zone(s, i, k):
        """そのカードを革命チェンジで探せるゾーンの中身。既定は手札だけ。
        CHANGEZONE に ("hand", "shield") と書くと、表向きのシールドからも入れ替えられる（S革命チェンジ）。"""
        p = s.P[i]
        zs = CHANGEZONE.get(k)
        if not zs:
            return k in p.hand
        if "hand" in zs and k in p.hand:
            return True
        if "shield" in zs and any(x == k and up for x, up in p.sh):
            return True
        return False

    def change_take(s, i, k):
        """革命チェンジで入れ替えるカードを、あったゾーンから取り出す"""
        p = s.P[i]
        if k in p.hand:
            p.hand.remove(k)
            return True
        for j, (x, up) in enumerate(p.sh):
            if x == k and up:
                del p.sh[j]
                s.shield_left()
                return True
        return False

    def change_card(s, i, u):
        """革命チェンジできるカードを返す（既定は手札。S革命チェンジは表向きのシールドも）"""
        p = s.P[i]
        if u.c.brk >= 99:
            return None
        w = None
        for k in CHANGE_ORDER:
            if s.change_zone(i, k) and k != u.k and not s.has(i, k):
                civ, need = CHANGE[k]
                if civ is not None and not (set(civ) & set(u.c.civ)):
                    continue
                if w is None:
                    w = s.power(i, u, True)
                if w >= need and s.fate(i, k, "hand", False) == "ok":
                    return k
        for k, cond in CHANGEX.items():
            if (s.change_zone(i, k) and k != u.k and not s.has(i, k) and cond(s, i, u)
                    and s.fate(i, k, "hand", False) == "ok"):
                return k
        return None

    def ninja_block(s, di, au, b):
        """相手がブロックした時に手札から出る（ブロック側のウラ・ニンジャ・ストライク）"""
        if not BLOCKREACT:
            return
        d = s.P[di]
        for k, f in BLOCKREACT.items():
            if k in d.hand and f(s, di, au, b):
                return

    def ninja(s, di, au):
        """ウラ・ニンジャ・ストライク（テンサイ・ハート）"""
        d = s.P[di]
        for k, f in REACT.items():
            if k in d.hand and f(s, di, au):
                return
        if "tensai" not in d.hand or len(d.mana) < 3 or "W" not in civs(d):
            return
        if s.fate(di, "tensai", "hand", True) != "ok":
            return
        d.hand.remove("tensai")
        t = s.enter(di, "tensai", "hand", True)
        if t is None:
            return
        t.eot = True
        s.ev("　ウラ・ニンジャ・ストライク：テンサイ・ハート")
        s.draw(di, 2)
        if not d.hand:
            return
        a = s.P[1 - di]
        cnt = {}
        for x in a.board:
            if x is not au and x.c.kind == "C" and not x.tap and not x.c.noatk:
                cnt[x.c.cost] = cnt.get(x.c.cost, 0) + 1
        best = max(d.hand, key=lambda k: cnt.get(CARD[k].cost, 0) * 10 - PRI[k])
        cost = CARD[best].cost
        s.discard(di, best, by_opp=True)
        if cnt.get(cost):
            s.trig[di] += 1
            for x in a.board:
                if x is not au and x.c.cost == cost:
                    x.lock = s.turn

    def attack(s, idx, tgt, sp=None):
        i = s.tp
        p = s.P[i]
        o = s.P[1 - i]
        u = p.board[idx]
        tu = o.board[tgt] if tgt != "P" else None
        s.tap_cre(i, u)
        s.atk = u
        s.atktgt = tu            # いま攻撃している相手（プレイヤーへの攻撃なら None）
        k = u.k
        if tu is None and not s.fa[i]:
            s.fa[i] = s.myturn(i)
        s.ev(f"{u.c.name} が攻撃 → {'プレイヤー' if tu is None else tu.c.name}")
        # 攻撃する時の能力
        if k == "derbande":
            if sp is not None:
                s.exec_free(i, sp)
        elif k == "koori":
            s.draw(i, 2)
        elif k == "everlast":
            s.everlast(i)
        elif k == "hangyaku":
            e_hangyaku(s, i, u)
        elif k == "venom":
            s.mill(1 - i, 1)
            if not p.ven_used:
                p.ven_used = True
                s.draw(i)
        elif k == "doom":
            s.meteor(i, u)
        elif k == "jaouga":
            if not p.jao_used:
                p.jao_used = True
                s.mill(i, 2)
                s.revive(i, lambda c: c.cost <= 6 and ("D" in c.civ or "F" in c.civ))
        # 能力を無視されていても**攻撃そのものは通る**（止まるのは「攻撃する時」の誘発だけ）。
        # ここで return すると、ブロックもシールドのブレイクも起きなくなる。
        if not (ABILOCK and not s.abi(i, u)):
            if u.link:                           # G・リンク：つないだカードの能力も併せ持つ
                for z in u.link:
                    g = ATTACK.get(z.k)
                    if g is not None and not s.over and u in s.P[i].board:
                        g(s, i, u)
            fn = ATTACK.get(k)
            if fn is not None and not s.over and u in p.board:
                fn(s, i, u)
            for f in ATKWATCH:
                if not s.over and u in p.board:
                    f(s, i, u)
        if s.over or s.stop or u not in p.board:
            s.atk = None
            s.atktgt = None
            return
        sw = ATKSWAP.get(k)
        if sw is not None:
            nu = sw(s, i, u)
            if nu is not None:
                u = nu
                s.atk = u
                k = u.k
                if s.over or s.stop or u not in p.board:
                    s.atk = None
                    return
        # 侵略：手札からこのクリーチャーの上に重ねる（何回でも）
        for _ in range(6):
            iv = zn = None
            for ik in sorted(INVADEX):
                for z in INVZONE.get(ik, ("hand",)):
                    if z == "board":         # S級侵略：バトルゾーンにあるこのカードを重ねる
                        if any(x is not u and x.k == ik and not x.under for x in p.board) \
                                and INVADEX[ik](s, i, u) and s.fate(i, ik, "zone", False) == "ok":
                            iv, zn = ik, z
                            break
                        continue
                    zone = p.hand if z == "hand" else (p.mana if z == "mana" else p.grave)
                    if ik in zone and INVADEX[ik](s, i, u) and s.fate(i, ik, z, False) == "ok":
                        iv, zn = ik, z
                        break
                if iv is not None:
                    break
            if iv is None:
                break
            j = p.board.index(u)
            if zn == "mana":
                s.take_mana(i, iv)
            elif zn == "grave":
                p.grave.remove(iv)
            elif zn == "board":
                x = next(x for x in p.board if x is not u and x.k == iv and not x.under)
                p.board.remove(x)
                j = p.board.index(u)
            else:
                p.hand.remove(iv)
            nu = U(iv)
            nu.under = [u.k] + u.under
            nu.tap = u.tap
            nu.sick = False
            nu.unb = u.unb
            nu.re = u.re
            p.board[j] = nu
            p.ent += 1
            s.note("surface", i, nu.k)
            s.ev(f"　侵略：{u.c.name} → {nu.c.name}")
            u = nu
            s.atk = u
            k = iv
            s.first_play(i, nu.c.cost)
            fn = ENTER.get(iv)
            if fn is not None:
                fn(s, i, u)
            for f in ENTERWATCH:
                if not s.over:
                    f(s, i, u)
            if s.over or s.stop or u not in p.board:
                s.atk = None
                return
        # 革命チェンジ
        ch = s.change_card(i, u)
        if ch is not None:
            j = p.board.index(u)
            s.change_take(i, ch)                 # 手札か、表向きのシールド（S革命チェンジ）から取る
            p.hand.append(u.k)
            p.hand.extend(u.under)
            n = U(ch)
            n.tap = True
            n.sick = False
            n.unb = u.unb
            p.board[j] = n
            p.ent += 1
            s.note("surface", i, n.k)
            s.chg[i] += 1
            s.ev(f"　革命チェンジ：{u.c.name} → {n.c.name}")
            u = n
            s.atk = u
            k = ch
            s.first_play(i, n.c.cost)
            if ch == "ops":
                e_ops(s, i, u)
            else:
                fn = ENTER.get(ch)
                if fn is not None:
                    fn(s, i, u)
            if s.over or s.stop or u not in p.board:
                s.atk = None
                return
        s.ninja(1 - i, u)
        if s.over or s.stop or u not in p.board:
            s.atk = None
            return
        if tu is not None and tu not in o.board:
            tu = None
            hit = False
        else:
            hit = True
        if hit:
            for f in GUARD:                  # ガードマン：攻撃先を引き受ける
                nt = f(s, 1 - i, u, tu)
                if nt is not None and nt in o.board and nt is not tu:
                    s.ev(f"　ガードマン：{nt.c.name} が攻撃を引き受ける")
                    tu = nt
                    break
            unb = u.unb or bool(UNBOK and any(f(s, i, u) for f in UNBOK))
            b = None if unb else s.choose_block(1 - i, i, u, tu)
            if b is not None:
                s.tap_cre(1 - i, b)
                s.ev(f"　{b.c.name} がブロック")
                s.ninja_block(1 - i, u, b)        # ブロックした時に手札から出る札
                if BLOCKDONE and not s.over and b in s.P[1 - i].board:
                    for z in s.parts(b):          # ブロックした側の「ブロックした時」
                        g = BLOCKDONE.get(z.k)
                        if g is not None and not s.over and b in s.P[1 - i].board:
                            g(s, 1 - i, b, u)
                if s.over or s.stop or u not in s.P[i].board or b not in s.P[1 - i].board:
                    return
                for f in BLOCKWATCH:              # ブロックされた時（攻撃している側の誘発）
                    if not s.over and u in s.P[i].board:
                        f(s, i, u, b)
                if s.over or s.stop or u not in s.P[i].board or b not in s.P[1 - i].board:
                    return
                s.battle(i, u, 1 - i, b)
            elif tu is not None:
                s.battle(i, u, 1 - i, tu)
            elif not o.sh:
                if not o.protect:
                    s.win(i, "ダイレクトアタック")
                else:
                    s.ev("　ドギラゴン逆の効果で負けない")
            else:
                s.break_sh(i, s.brk(i, u))
        if s.over:
            return
        if u in p.board:
            if k == "dagra" and u.hyper and not s.stop:
                s.dagra_end(i)
            for f in ATKEND:
                if not s.over and u in p.board:
                    f(s, i, u)
            if u.re:
                u.re = False
                u.tap = False
        s.atk = None

    def everlast(s, i):
        o = s.P[1 - i]
        t = None if o.protect else s.target(i, kinds="CT")
        if t is not None and t.k != "douki" and PRI[t.k] >= 5:
            s.ev(f"　エバーラスト：{t.c.name} をシールドに")
            s.leave(1 - i, t, "shield", by_opp=True)
        else:
            s.add_shield(i)

    def revive(s, i, pred, src="grave"):
        """墓地（かマナ）から、条件に合う進化でないクリーチャーを1体出す"""
        p = s.P[i]
        zone = p.grave if src == "grave" else p.mana
        best, bv = None, -1
        for k in sorted(set(zone)):
            c = CARD[k]
            if c.kind == "C" and not c.evo and pred(c) and PRI[k] > bv and s.fate(i, k, src, False) == "ok":
                best, bv = k, PRI[k]
        if best is None:
            return None
        if src == "grave":
            p.grave.remove(best)
        else:
            s.take_mana(i, best)
        s.ev(f"　{'墓地' if src == 'grave' else 'マナ'}から {CARD[best].name}")
        return s.enter(i, best, src, False)

    def meteor(s, i, u):
        """DOOM・ドラゲリオン：下のカードを墓地に置き、相手1体を-9000、墓地から進化でないクリーチャーを出す"""
        p = s.P[i]
        if not u.under:
            return
        k = max(u.under, key=lambda x: PRI[x] if not CARD[x].evo else -1)
        u.under.remove(k)
        p.grave.append(k)
        t = s.target(i, lambda x: s.power(1 - i, x) <= 9000)
        if t is not None:
            s.leave(1 - i, t, "grave", by_opp=True, destroy=True)
        s.revive(i, lambda c: True)

    def dagra_end(s, i):
        p = s.P[i]
        if s.manaexec(i):
            return
        n = len(p.mana)
        s.revive(i, lambda c: c.cost < n, "mana")

    def dogi_end(s, i):
        """ドギラゴン逆：ターンの終わりに2マナ加速し、手札かマナから2体まで（コスト合計7以下）出す"""
        p = s.P[i]
        s.ramp(i, 2, False)
        budget, n = 7, 0
        cands = []
        if not s.manaexec(i):
            cands += [(PRI[k], 1, k) for k in p.mana]
        cands += [(PRI[k], 0, k) for k in p.hand]
        cands.sort(reverse=True)
        for _, m, k in cands:
            if n >= 2:
                break
            c = CARD[k]
            if c.kind != "C" or c.evo and not c.neo or c.cost > budget:
                continue
            src = "mana" if m else "hand"
            zone = p.mana if m else p.hand
            if k not in zone or s.fate(i, k, src, False) != "ok":
                continue
            if m:
                s.take_mana(i, k)
            else:
                p.hand.remove(k)
            budget -= c.cost
            n += 1
            s.ev(f"　ドギラゴン逆の効果で {c.name}")
            s.enter(i, k, src, False)
            if s.over:
                return

    # ------------------------------------------------------------------ ループ
    def loop_d_ok(s, i):
        p = s.P[i]
        if p.looped or "pon" not in p.hand or len(p.deck) < 2:
            return False
        if not (s.has(i, "teacher") and s.has(i, "dokkoi")):
            return False
        if s.limit(i) < 99 or s.fate(i, "pon", "hand", True) != "ok":
            return False
        for u in s.P[1 - i].board:
            if u.k == "vamilia" and u.hyper:
                return False
        return True

    def loop_d(s, i):
        """ドッコイループ：ポンの助を出し直し続けて山札を引く。勝てる形なら勝ち、足りなければ次のターンに備える"""
        p = s.P[i]
        p.looped = True
        if not s.loopt[i]:
            s.loopt[i] = s.myturn(i)
        allc = p.hand + p.deck
        pons = allc.count("pon")
        m = len(p.mana) + pons - 1
        av = len(p.mana) - p.mused + pons - 1
        cv = civs(p)
        win = False
        if "shako" in allc:
            if av >= 9 and "W" in cv and s.fate(i, "shako", "hand", True, m) == "ok":
                win = True
            elif "saitan" in allc and "L" in cv and s.spell_ok(i, 3, "saitan") and s.fate(i, "shako", "hand", False, 99) == "ok":
                nk = allc.count("kohaku") if cv >= {"L", "W", "N"} and s.fate(i, "kohaku", "hand", True) == "ok" else 0
                for j in range(nk + 1):
                    if m + j >= 9 and av - 2 * j >= 3:
                        win = True
                        break
        if win:
            s.ev("ドッコイループ → シャコガイルで勝ち")
            s.win(i, "ループ")
            return
        while len(p.deck) > 5:
            p.hand.append(p.deck.pop())
        while p.hand.count("pon") > 1:
            p.hand.remove("pon")
            p.mana.append("pon")
        s.ev(f"ドッコイループ：山札を引き、マナは{len(p.mana)}枚（このターンは勝てない）")
        if "efc" in p.hand and s.efc_ok(i):
            p.hand.remove("efc")
            s.cast(i, "efc")

    def efc_ok(s, i):
        p = s.P[i]
        return sum(1 for k in p.hand if k in SNOW) >= 5 and s.spell_ok(i, 15, "endless")

    def loop_z_ok(s, i):
        p = s.P[i]
        if p.looped or "leviya" not in p.hand or len(p.deck) < 4:
            return False
        nz = sum(1 for u in p.board if u.k == "zen")
        if not nz or len(p.mana) - p.mused < (3 if nz == 1 else 1):
            return False
        m = p.mana
        if "leviya" not in m or "trap" not in m or "parli" not in m or p.ban == 3 or p.ban == 5:
            return False
        for u in s.P[1 - i].board:
            if u.k == "poppi" or u.k == "robin":
                return False
        return True

    def loop_z(s, i):
        """創世竜ループ：無限にマナを増やし、トラップで相手の小型をどかし、ウォカンナの出し入れで相手の山札を削りきる"""
        p = s.P[i]
        o = s.P[1 - i]
        p.looped = True
        if not s.loopt[i]:
            s.loopt[i] = s.myturn(i)
        if not o.protect:
            for u in o.board[:]:
                if u.c.cost <= 4 and not u.jd and u in o.board:
                    s.leave(1 - i, u, "mana", by_opp=True, burst=False)
        zones = p.hand + p.deck + p.mana + p.grave
        for u in p.board:
            zones.append(u.k)
            zones.extend(u.under)
        shk = [k for k, up in p.sh]
        esm = "esmel" in zones
        okv = "valhalla" in zones or (esm and "valhalla" in shk)
        okw = "wokanna" in zones or (esm and "wokanna" in shk)
        ent = p.ent
        p.ent = 0
        can = okv and okw and not o.protect and s.limit(i) >= 99 and s.fate(i, "wokanna", "mana", False, 99) == "ok"
        p.ent = ent
        if can:
            s.ev("創世竜ループ → 相手の山札を削りきって勝ち")
            s.win(i, "ループ")
            return
        while len(p.deck) > 8:
            p.mana.append(p.deck.pop())
            p.mused += 1
        s.ev(f"創世竜ループ：マナが{len(p.mana)}枚に（このターンは勝ちきれない）")

    # ------------------------------------------------------------------ コスト
    def ccost(s, i, k, av):
        """手札から召喚する時のコスト"""
        c = CARD[k]
        p = s.P[i]
        n = c.cost
        if k == "kohaku":
            n = 2
        elif k == "vt":
            n = max(1, 8 - s.ncre(0) - s.ncre(1))
        elif k == "viride":
            n = 2 if len(p.sh) > len(s.P[1 - i].sh) else 6
        elif k == "everlast":
            n = 5 if sum(1 for x in p.mana if "L" in MCIV[x]) >= 3 else 7
        elif k == "obza":
            n = max(1, 9 - s.gc(i))
        elif k == "crossfire":
            n = 0 if s.gc(i) >= 6 and not s.has(i, "crossfire") else 7
        elif k == "shuto":
            for x in s.P[1 - i].mana:
                if MULTI[x]:
                    n = 3
                    break
        elif k == "jaouga":
            costs = {u.c.cost for u in p.board if u.c.kind == "C" and not u.tap}
            n = 99
            for t in range(len(costs) + 1):
                if max(1, 8 - 2 * t) <= av:
                    n = max(1, 8 - 2 * t)
                    break
        elif k == "doom":
            g = s.gc(i)
            n = 99 if g < 1 else max(1, 12 - g)
        f = COSTX.get(k)
        if f is not None:
            n = f(s, i, av)
        for f in COSTAURA:
            n = f(s, i, k, n)
        if n > 1 and n < 99 and not p.gc_used:
            for x, up in p.sh:
                if up and x == "gcross":
                    n -= 1
                    break
        return n

    # ------------------------------------------------------------------ ターンの進行
    def start_turn(s):
        s.turn += 1
        i = s.tp
        p = s.P[i]
        o = s.P[1 - i]
        s.dcount = [0, 0]
        for q in s.P:
            q.ent = q.spl = q.drawn = 0
            q.sc_used = q.klin_used = False
            q.brk_t = 0
        p.fp = p.zen_used = p.gc_used = p.looped = p.jao_used = p.ven_used = False
        p.protect = False
        o.ban = -1
        frozen = p.frozen
        p.frozen = False
        for u in p.board:
            u.sick = False
            u.hyper = False
            u.jd = False
            if frozen:
                continue
            if u.frz:
                u.frz = 0
            elif u.k != "zaze":
                u.tap = False
        p.mused = len(p.mana) if frozen else 0
        if TSTART or TSTARTALL:
            for u in p.board[:]:
                if not s.abi(i, u):
                    continue
                for z in s.parts(u):
                    f = TSTART.get(z.k)
                    if f is not None and u in p.board and not s.over:
                        f(s, i, u)
                for g in TSTARTALL:
                    if u in p.board and not s.over:
                        g(s, i, u)
        for f in TURNSTART:                        # ターンのはじめ（バトルゾーンに何もなくても呼ばれる）
            if not s.over:
                f(s, i)
        if p.delayed:
            ds = p.delayed
            p.delayed = []
            for k in ds:
                s.enter(i, k, "zone", False)
        for j in range(len(p.sh) - 1, -1, -1):
            if p.sh[j][1] and p.sh[j][0] == "keikan":
                del p.sh[j]
                s.shield_left()
                s.enter(i, "keikan", "shield", True)
        if s.turn > 1:
            s.draw(i)
        s.phase = "C"

    def end_turn(s):
        i = s.tp
        p = s.P[i]
        o = s.P[1 - i]
        if not s.over:
            if TEND or TENDALL:
                for j in (i, 1 - i):
                    q = s.P[j]
                    for u in q.board[:]:
                        if j == i and s.abi(j, u):
                            for z in s.parts(u):
                                f = TEND.get(z.k)
                                if f is not None and u in q.board and not s.over:
                                    f(s, j, u)
                        for g in TENDALL:
                            if u in q.board and not s.over:
                                g(s, j, u)
            for j in (i, 1 - i):                   # ターンの終わり（バトルゾーンに何もなくても呼ばれる）
                for f in TENDP:
                    if not s.over:
                        f(s, j)
            if s.has(i, "dogigyaku"):
                s.dogi_end(i)
            for x, up in p.sh:
                if up and x == "gcross":
                    if s.ncre(i) > s.ncre(1 - i):
                        s.draw(i)
                    break
            for u in p.board:
                if u.k == "vamilia" and not u.hyper:       # ハイパー化：ほかのクリーチャーを1体タップ
                    oth = [x for x in p.board if x is not u and x.c.kind == "C" and not x.tap and not x.c.blocker]
                    if oth:
                        s.tap_cre(i, min(oth, key=s.val))
                        u.hyper = True
        for q in s.P:
            for u in q.board[:]:
                if u.eot:
                    q.board.remove(u)
                    q.deck.insert(0, u.k)
                    for k in u.under:
                        q.deck.insert(0, k)
                    continue
                u.sa = False
                u.pw = 0
                u.re = False
                u.unb = False
        if p.nosmall:
            p.nosmall -= 1
        if p.nolow:
            p.nolow -= 1
        s.atk = None
        s.stop = False
        if p.extra > 0:
            # 追加ターン：同じプレイヤーがもう1回。turn を2つ進めて「どちらの手番か」の勘定を合わせる
            # （myturn は turn の偶奇で見ているので、1つだけ進めると持ち主が入れ替わってしまう）。
            p.extra -= 1
            s.turn += 1
            s.ev(f"★ プレイヤー{i} の追加ターン")
        else:
            s.tp = 1 - i
        if s.over:
            return
        if s.turn >= MAXTURN:
            s.over = True
            s.how = "時間切れ"
            return
        s.start_turn()

    # ------------------------------------------------------------------ 打てる手
    def legal(s):
        """打てる手の一覧。

        **ここは盤面を書き換えてはいけない。** 手を数える途中で `s.target()` を呼ぶ判定
        （《卓球の妖精》の無駄撃ち判定など）があり、そのままだと「相手に選ばれた時」（CHOSENWATCH）が
        誘発して、生きている盤面が壊れる（手を数えるだけでシールドが割れる、という不具合が実際にあった）。
        数えている間は `s.dry` を立てて、観測だけの誘発を止める。"""
        if s.over:
            return []
        s.dry += 1
        try:
            return s._legal()
        finally:
            s.dry -= 1

    def _legal(s):
        if s.over:
            return []
        i = s.tp
        p = s.P[i]
        if s.phase == "C":
            return [("charge", k) for k in sorted(set(p.hand))] + [("skip",)]
        if s.phase == "M":
            return s.legal_main(i)
        return s.legal_attack(i)

    def evo_src(s, i, k):
        """進化元にするカードを選ぶ（アンタップしているもの、重要度の低いものを優先）"""
        e = CARD[k].evo
        best, bv = None, None
        ex = EVOX.get(k)
        for u in s.P[i].board:
            if u.c.kind != "C" and u.k not in SHINKA:
                continue                      # 進化元になれるのはクリーチャー（シンカライズを持つカードは例外）
            if ex is not None:
                ok = ex(s, i, u)
            elif e == "cyberv":
                ok = "cyberv" in u.c.races
            else:
                ok = False
                for x in u.c.civ:
                    if x in e:
                        ok = True
                        break
            if ok:
                v = (u.tap, bool(u.c.meta), PRI[u.k] + len(u.under))
                if bv is None or v < bv:
                    best, bv = u, v
        return best

    def legal_main(s, i):
        p = s.P[i]
        acts = []
        av = len(p.mana) - p.mused
        cv = civs(p)
        zen = s.has(i, "zen")
        fuj = s.has(1 - i, "fujin")
        loop_d = s.loop_d_ok(i)
        for k in sorted(set(p.hand)):
            c = CARD[k]
            kind = c.kind
            if kind == "C":
                if k == "pon" and (p.looped or loop_d):
                    pass
                else:
                    n = s.ccost(i, k, av)
                    if n <= av and (n == 0 or cv.issuperset(c.civ)) and s.fate(i, k, "hand", True) == "ok":
                        ez = EVOSRC.get(k)
                        if ez is not None:          # 手札進化・墓地進化・マナ進化
                            if ez(s, i) is not None:
                                acts.append(("play", k, 1))
                        elif c.evo == "grave":
                            acts.append(("play", k, 1))
                        elif c.evo:
                            if c.neo:
                                acts.append(("play", k, 0))
                            if s.evo_src(i, k) is not None:
                                acts.append(("play", k, 1))
                        else:
                            acts.append(("play", k, 0))
            elif kind == "S":
                if k == "efc":
                    if s.efc_ok(i):
                        acts.append(("play", k, 0))
                else:
                    sc = s.spcost(i, k)
                    if sc <= av and (sc == 0 or cv.issuperset(c.civ)) and s.spell_ok(i, c.cost, k):
                        if k != "saitan" or s.saitan_ok(i):
                            acts.append(("play", k, 0))
            elif kind == "T":
                n = s.ncost(i, k, max(1, c.cost - 2) if zen else c.cost)
                if n <= av and cv.issuperset(c.civ) and p.ban != c.cost:
                    acts.append(("play", k, 0))
            elif kind == "G":
                if s.ncost(i, k) <= av and cv.issuperset(c.civ) and p.ban != c.cost and not fuj:
                    acts.append(("play", k, 0))
        for k in sorted(set(p.hand)):
            c = CARD[k]
            if not c.twin:
                continue
            # ツインパクトの呪文側。クリーチャー側がタマシードのツインパクトもあるので、
            # 「クリーチャーの枝の中」ではなくここで作る（以前は kind=="C" の中にしかなく、
            #  タマシードのツインパクトは「シールドからは唱えられるのに手札からは唱えられない」状態だった）
            tc, tciv, _ = c.twin
            tc = s.ncost(i, k, twin=True)
            if tc <= av and cv.issuperset(tciv) and s.spell_ok(i, tc, k):
                if k != "takkyu" or s.takkyu_ok(i):
                    acts.append(("spell", k))
        if "keikan" in p.hand and av >= 2 and "W" in cv and not fuj and p.ban != 4:
            acts.append(("gal",))
        mex = s.manaexec(i)
        if zen and not p.zen_used and not mex:
            for k in sorted(set(p.mana)):
                c = CARD[k]
                if c.kind == "T" and max(1, c.cost - 2) <= av and p.ban != c.cost:
                    acts.append(("zen", k))
        if not mex:
            if "gigan" in p.grave and cv >= {"D", "N"}:
                mx = max((u.c.cost for u in p.board if u.c.kind == "C" and u.k != "zoro"), default=-1)
                if mx >= 0 and max(2, 14 - mx) <= av and s.fate(i, "gigan", "grave", True) == "ok":
                    acts.append(("gigan",))
            if "margani" in p.grave and av >= 2 and "D" in cv and s.fate(i, "margani", "grave", True) == "ok":
                acts.append(("abyss",))
        if loop_d:
            acts.append(("loop", "d"))
        if zen and s.loop_z_ok(i):
            acts.append(("loop", "z"))
        for f in FREE_ACTS:
            acts.extend(f(s, i, av, cv))
        acts.append(("attack",))
        return acts

    def legal_attack(s, i):
        p = s.P[i]
        o = s.P[1 - i]
        acts = []
        seen = set()
        gig = s.has(1 - i, "gigan")
        jao = s.has(i, "jaouga")
        sps = None
        for idx, u in enumerate(p.board):
            c = u.c
            ign = bool(NOATKIGN) and any(f(s, i, u) for f in NOATKIGN)
            if c.kind != "C" or u.tap or (s.kw(u, "noatk") and not ign) or (u.lock == s.turn and not ign):
                continue
            if (u.k in CANTATK and CANTATK[u.k](s, i, u)) or any(f(s, i, u) for f in ATKLOCK):
                continue
            full = ((not u.sick) or u.sa or s.kw(u, "sa") or jao or bool(c.evo and u.under)
                    or bool(u.link)                      # G・リンクしているクリーチャーは召喚酔いしない
                    or (u.k == "fujin" and not o.sh)
                    or bool(SAOK and any(f(s, i, u) for f in SAOK)))
            mf = u.sick and (s.kw(u, "mach") or (u.k == "dagra" and u.hyper)
                             or bool(MACHOK and any(f(s, i, u) for f in MACHOK)))
            if not full and not mf:
                continue
            sig = (u.k, full, u.hyper, u.pw, u.unb, len(u.under) if u.k in ("doom", "koori") else 0)
            if sig in seen:
                continue
            seen.add(sig)
            ap = s.power(i, u, True)
            opts = (None,)
            if u.k == "derbande":
                if sps is None:
                    sps = s.free_opts(i)
                if sps:
                    opts = sps
            tg = []
            nop = (s.kw(u, "noatkp") and not ign) or bool(NOATKPX and any(f(s, i, u) for f in NOATKPX))
            if full and not nop and not (gig and ap < 50000):
                tg.append("P")
            ts = set()
            for j, t in enumerate(o.board):
                if t.c.kind != "C" or t.jd or (not t.tap and not mf) or t.k in ts:
                    continue
                if ATKTARGETLOCK and any(f(s, i, u, t) for f in ATKTARGETLOCK):
                    continue
                if s.power(1 - i, t) > ap:
                    continue
                ts.add(t.k)
                tg.append(j)
            if MUSTATKTGT and len(tg) > 1:
                # 「可能ならこのクリーチャーを攻撃しなければならない」。候補を絞り終えた後で見る
                # （MUSTPICK と同じ考え方。条件に合う候補が無ければ縛られない）。
                for f in MUSTATKTGT:
                    want = f(s, i, u, tg)
                    if want is not None and want in tg:
                        tg = [want]
                        break
            for t in tg:
                for sp in opts:
                    acts.append(("atk", idx, t, sp))
        if acts and MUSTATK and any(f(s, i) for f in MUSTATK):
            return acts                       # 攻撃の強制：攻撃できるなら「ターンを終える」を出さない
        acts.append(("end",))
        return acts

    def apply(s, a):
        t = a[0]
        i = s.tp
        p = s.P[i]
        if t == "charge":
            p.hand.remove(a[1])
            s.add_mana(i, a[1], src="hand")
            f = CHARGEX.get(a[1])
            if f is not None:
                f(s, i)
            s.phase = "M"
            s.ev(f"マナに {CARD[a[1]].name}（{len(p.mana)}枚）")
        elif t == "skip":
            s.phase = "M"
        elif t == "play":
            s.play(i, a[1], a[2])
        elif t == "spell":
            k = a[1]
            p.mused += s.ncost(i, k, twin=True)
            p.hand.remove(k)
            s.ev(f"呪文：{CARD[k].name}（呪文側）")
            s.cast(i, k, True)
        elif t == "gal":
            p.mused += 2
            p.hand.remove("keikan")
            s.ev("「敬虔なる警官」を表向きの盾に")
            if s.add_shield(i, "keikan", True):
                x = s.target(i, lambda u: u.c.cost <= 2)
                if x is not None:
                    s.leave(1 - i, x, "hand", by_opp=True)
                s.P[1 - i].nolow = 1
            else:
                p.hand.append("keikan")
        elif t == "zen":
            k = a[1]
            p.zen_used = True
            p.mused += max(1, CARD[k].cost - 2)
            s.take_mana(i, k)
            s.ev(f"創世竜の能力でマナから {CARD[k].name}")
            s.place_tama(i, k)
            s.ramp(i, 1)
        elif t == "gigan":
            cands = [u for u in p.board if u.c.kind == "C" and u.k != "zoro"]
            x = max(cands, key=lambda u: u.c.cost)
            p.mused += max(2, 14 - x.c.cost)
            p.board.remove(x)
            s.add_mana(i, x.k, True)
            for k in x.under:
                s.add_mana(i, k, True)
            p.grave.remove("gigan")
            s.ev(f"フシギバース：{x.c.name} をマナに置いてギガンディダノス")
            s.enter(i, "gigan", "grave", True)
        elif t == "abyss":
            p.mused += 2
            p.grave.remove("margani")
            s.ev("アビスラッシュ：ハニー＝マーガニー")
            u = s.enter(i, "margani", "grave", True)
            if u is not None:
                u.sa = True
                u.eot = True
        elif t == "loop":
            if a[1] == "d":
                s.loop_d(i)
            else:
                s.loop_z(i)
        elif t == "attack":
            s.phase = "A"
        elif t == "atk":
            s.attack(a[1], a[2], a[3])
        elif t in ACTAPPLY:
            ACTAPPLY[t](s, a)
        else:
            s.end_turn()
            return
        if s.stop and not s.over:
            s.ev("　ターンの残りをとばす")
            s.end_turn()

    def play(s, i, k, mode):
        p = s.P[i]
        c = CARD[k]
        av = len(p.mana) - p.mused
        if c.kind == "C":
            n = s.ccost(i, k, av)
            base = 2 if k == "kohaku" else c.cost
            if not p.gc_used and n > 0 and k not in ("jaouga", "doom", "vt", "obza"):
                for x, up in p.sh:
                    if up and x == "gcross":
                        p.gc_used = True
                        break
            elif not p.gc_used and k in ("jaouga", "doom", "vt", "obza") and n >= 1:
                for x, up in p.sh:
                    if up and x == "gcross":
                        p.gc_used = True
                        break
            del base
            p.hand.remove(k)
            on = None
            if k == "jaouga":
                t = (8 - n + 1) // 2 if n < 8 else 0
                used = set()
                for u in sorted((u for u in p.board if u.c.kind == "C" and not u.tap), key=lambda u: s.power(i, u)):
                    if t <= 0:
                        break
                    if u.c.cost not in used:
                        used.add(u.c.cost)
                        s.tap_cre(i, u)
                        t -= 1
            f = PAYX.get(k)
            if f is not None:
                f(s, i, k, n)
            p.mused += n
            s.ev(f"召喚：{c.name}（{n}マナ）")
            if k == "doom":
                gs = sorted((x for x in p.grave if CARD[x].kind == "C"), key=PRI.get)
                u = s.enter(i, k, "hand", True)
                if u is not None:
                    for x in gs:
                        p.grave.remove(x)
                        u.under.append(x)
                return
            ez = EVOSRC.get(k)
            if ez is not None:                      # バトルゾーン以外からの進化元
                got = ez(s, i)
                u = s.enter(i, k, "hand", True)
                if u is not None and got is not None:
                    zone, ek = got
                    z = {"hand": p.hand, "grave": p.grave, "mana": p.mana}.get(zone)
                    if z is not None and ek in z:
                        if zone == "mana":
                            s.take_mana(i, ek)
                        else:
                            z.remove(ek)
                        u.under.append(ek)
                        s.ev(f"　進化元：{CARD[ek].name}（{zone}）を下に置く")
                return
            if mode:
                on = s.evo_src(i, k)
            s.enter(i, k, "hand", True, on=on)
        elif c.kind == "S":
            p.hand.remove(k)
            if k == "efc":
                s.ev("エンドレス・フローズン・カーニバル（スノーフェアリー5体を捨てる）")
            else:
                p.mused += s.spcost(i, k)
                s.ev(f"呪文：{c.name}")
            s.cast(i, k)
        elif c.kind == "T":
            p.mused += s.ncost(i, k, max(1, c.cost - 2) if s.has(i, "zen") else c.cost)
            p.hand.remove(k)
            s.ev(f"タマシード：{c.name}")
            s.place_tama(i, k)
        else:
            p.mused += s.ncost(i, k)
            p.hand.remove(k)
            s.ev(f"G城：{c.name}")
            s.place_castle(i, k)

    # ------------------------------------------------------------------ 使えるかの判定（無駄撃ちを省く）
    def saitan_ok(s, i):
        p = s.P[i]
        if not any(u.c.kind == "C" for u in p.board):
            return False
        n = len(p.mana)
        for k in p.hand:
            c = CARD[k]
            if c.kind == "C" and c.cost <= n and c.cost >= 3 and not (c.evo and not c.neo):
                if s.fate(i, k, "hand", False) == "ok":
                    return True
        return False

    def takkyu_ok(s, i):
        mine = [s.power(i, u) for u in s.P[i].board if u.c.kind == "C"]
        if not mine:
            return False
        m = max(mine)
        return s.target(i, lambda x: s.power(1 - i, x) < m) is not None


# ====================================================================== 出た時の能力
def e_kohaku(s, i, u):
    p = s.P[i]
    n = min(2, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    k = max(top, key=lambda x: PRI[x] - 3 * p.hand.count(x))
    top.remove(k)
    for x in top:
        p.deck.insert(0, x)
    if len(p.mana) <= 3 and not s.has(1 - i, "robin"):
        k2 = k
        s.add_mana(i, k2)
    else:
        p.hand.append(k)


def e_chakra(s, i, u):
    s.add_shield(i)


def e_vt(s, i, u):
    o = s.P[1 - i]
    for x in o.board[:]:
        if x.c.kind == "C" and x in o.board and s.power(1 - i, x) <= 5000:
            s.leave(1 - i, x, "hand", by_opp=True)
    o.nosmall = 2 if s.tp != i else 1


def e_clock(s, i, u):
    s.stop = True


def e_eringi(s, i, u):
    p = s.P[i]
    s.draw(i, 2)
    if p.hand and len(p.mana) < 8:
        k = min(p.hand, key=PRI.get)
        p.hand.remove(k)
        s.add_mana(i, k)
    if s.tp != i and p.brk_t >= 2:
        for x in s.P[1 - i].board:
            if x.c.kind == "C":
                s.tap_cre(1 - i, x)


def e_anti(s, i, u):
    p = s.P[i]
    s.draw(i)
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = CARD[k]
        if c.kind == "C" and c.cost <= 3 and not (c.evo and not c.neo) and PRI[k] > bv:
            if s.fate(i, k, "hand", False) == "ok":
                best, bv = k, PRI[k]
    if best is not None:
        p.hand.remove(best)
        s.ev(f"　アンティハムトの効果で {CARD[best].name}")
        s.enter(i, best, "hand", False, sa=True, pw=3000)


def e_dagra(s, i, u):
    p = s.P[i]
    for j in range(len(p.sh) - 1, -1, -1):
        if not p.sh[j][1]:
            k = p.sh.pop(j)[0]
            s.add_mana(i, k)
            s.shield_left()
            return


def e_katsuemon(s, i, u):
    for _ in range(2):
        t = s.target(i, lambda x: not x.tap and x.c.blocker)
        if t is not None:
            s.tap_cre(1 - i, t)
            if t.c.blocker:
                s.leave(1 - i, t, "grave", by_opp=True, destroy=True)
        else:
            s.draw(i)


def e_everlast(s, i, u):
    s.everlast(i)


def e_dogigyaku(s, i, u):
    """極限ファイナル革命は1ゲーム1回（ターンごとに戻る final_turn とは別の印を使う）"""
    p = s.P[i]
    if not p.final_used:
        p.final_used = True
        p.protect = True
        s.ev("　極限ファイナル革命：次の自分のターンまで負けず、クリーチャーは相手の効果で離れない")


def e_leviya(s, i, u):
    """マナからコスト3以下のクリーチャーかタマシードを出す"""
    p = s.P[i]
    if s.manaexec(i):
        return
    zen = s.has(i, "zen")
    o = s.P[1 - i]
    best, bv = None, -99
    for k in sorted(set(p.mana)):
        c = CARD[k]
        if c.cost > 3 or p.ban == c.cost:
            continue
        if c.kind == "C":
            if c.evo and not c.neo or s.fate(i, k, "mana", False) != "ok":
                continue
            v = PRI[k] + (6 if k == "zen" and not zen else 0)
        elif c.kind == "T":
            v = PRI[k]
            if k == "parli":
                v += 3 if zen else -3
            elif k == "trap":
                if o.protect or s.target(i, lambda x: x.c.cost <= 4, "CT") is None:
                    v -= 4
        else:
            continue
        if v > bv:
            best, bv = k, v
    if best is None:
        return
    s.take_mana(i, best)
    s.ev(f"　レヴィヤの効果でマナから {CARD[best].name}")
    if CARD[best].kind == "C":
        s.enter(i, best, "mana", False)
    else:
        s.place_tama(i, best)


def e_trap(s, i, u):
    o = s.P[1 - i]
    t = None if o.protect else s.target(i, lambda x: x.c.cost <= 4, "CT")
    if t is not None:
        s.ev(f"　トラップ：{t.c.name} をマナへ")
        s.leave(1 - i, t, "mana", by_opp=True)
    elif u is not None and not s.has(i, "zen") and u in s.P[i].board:
        s.P[i].board.remove(u)
        s.add_mana(i, "trap")


def e_parli(s, i, u):
    j = 1 - i if s.gc(1 - i) >= 4 else i
    q = s.P[j]
    if q.grave:
        g = q.grave
        q.grave = []
        s.rng.shuffle(g)
        q.deck[0:0] = g


def e_jasmine(s, i, u):
    s.ramp(i, 1)


def e_manhattan(s, i, u):
    for j in (i, 1 - i):
        q = s.P[j]
        cs = [x for x in q.board if x.c.kind == "C"]
        if len(cs) <= 1:
            continue
        if j == i:
            keep = max(cs, key=s.val)
        else:
            ch = [x for x in cs if not x.jd]
            dk = [x for x in ch if x.k == "douki"]
            keep = dk[0] if dk else (min(ch, key=s.val) if ch else None)
        for x in cs:
            if x is not keep and x in q.board:
                s.leave(j, x, "mana", by_opp=(j != i), burst=False)


def e_wokanna(s, i, u):
    out = s.mill(1 - i, 1)
    if out:
        n = CARD[out[0]].cost
        t = s.target(i, lambda x: x.c.cost <= n, "CT")
        if t is not None:
            s.leave(1 - i, t, "hand", by_opp=True)


def e_esmel(s, i, u):
    e_dagra(s, i, u)


def e_princess(s, i, u):
    o = s.P[1 - i]
    if o.protect:
        return
    ts = []
    for _ in range(3):
        t = s.target(i, lambda x: x not in ts)
        if t is None:
            break
        ts.append(t)
    dests = ["shield", "mana", "hand"][:len(ts)]
    ts.sort(key=s.val)                       # 相手は、大事なものほど手札に近い行き先を選ぶ
    for t, d in zip(ts, dests):
        s.leave(1 - i, t, d, by_opp=True)


def e_leaf(s, i, u):
    s.draw(i, 3)


def e_hangyaku(s, i, u):
    t = s.target(i)
    if t is not None:
        s.leave(1 - i, t, "deck", by_opp=True)


def e_robin(s, i, u):
    s.discard_random(1 - i)


def e_ops(s, i, u):
    """ファイナル革命：コストを1つ選び、そのコストの相手をすべて破壊。次の自分のターンまで相手はそのコストを使えない"""
    o = s.P[1 - i]
    sc = {}
    for x in o.board:
        sc[x.c.cost] = sc.get(x.c.cost, 0) + 10 + PRI[x.k]
    for k in o.hand + o.deck:
        sc[CARD[k].cost] = sc.get(CARD[k].cost, 0) + 1
    if not sc:
        return
    n = max(sorted(sc), key=sc.get)
    for x in o.board[:]:
        if x.c.cost == n and x in o.board:
            s.leave(1 - i, x, "grave", by_opp=True, destroy=True)
    o.ban = n
    s.ev(f"　ファイナル革命：コスト{n}を指定")


def e_vamilia(s, i, u):
    t = s.target(i, kinds="CT")
    if t is not None:
        s.leave(1 - i, t, "hand", by_opp=True)
    s.discard_random(1 - i)


def e_artel(s, i, u):
    for _ in range(2):
        if s.over:
            return
        if s.revive(i, lambda c: c.cost <= 4) is not None:
            continue
        t = s.target(i, lambda x: s.power(1 - i, x) <= 4000)
        if t is not None:
            s.leave(1 - i, t, "grave", by_opp=True, destroy=True)
            continue
        s.mill(i, 4)


def _fight(s, i, u):
    if u is None or u not in s.P[i].board:
        return
    w = s.power(i, u)
    t = s.target(i, lambda x: s.power(1 - i, x) < w)
    if t is not None:
        s.ev(f"　{u.c.name} が {t.c.name} とバトル")
        s.battle(i, u, 1 - i, t)


def e_jaouga(s, i, u):
    o = s.P[1 - i]
    dn = [j for j, x in enumerate(o.sh) if not x[1]]
    if len(o.sh) > 3:
        cut = set(dn[:len(o.sh) - 3])
        gone = [x for j, x in enumerate(o.sh) if j in cut]
        o.sh = [x for j, x in enumerate(o.sh) if j not in cut]
        for k, up in gone:
            o.grave.append(k)
        s.shield_left()
    if len(o.hand) > 2:
        hs = sorted(o.hand, key=PRI.get, reverse=True)
        o.hand = hs[:2]
        for k in hs[2:]:
            s.grave_put(1 - i, k)
    cs = [x for x in o.board if x.c.kind == "C"]
    if len(cs) > 1 and not o.protect:
        keep = max(cs, key=s.val)
        for x in cs:
            if x is not keep and x in o.board:
                s.leave(1 - i, x, "grave", by_opp=True, burst=False)


def e_scarlet(s, i, u):
    s.mill(i, 3)


def e_gigan(s, i, u):
    o = s.P[1 - i]
    for k in o.hand:
        s.add_mana(1 - i, k)
    o.hand = []


def e_dangerdeon(s, i, u):
    s.ramp(i, 3)


def e_obza(s, i, u):
    n = s.gc(i) * 1000
    t = s.target(i, lambda x: s.power(1 - i, x) <= n)
    if t is not None:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def e_shako(s, i, u):
    p = s.P[i]
    if p.grave:
        p.deck.extend(p.grave)
        p.grave = []
        s.rng.shuffle(p.deck)


def e_hustle(s, i, u):
    pass


ENTER = {
    "kohaku": e_kohaku, "chakra": e_chakra, "vt": e_vt, "clock": e_clock, "eringi": e_eringi, "anti": e_anti, "dagra": e_dagra,
    "katsuemon": e_katsuemon, "everlast": e_everlast, "dogigyaku": e_dogigyaku, "leviya": e_leviya, "trap": e_trap,
    "parli": e_parli, "jasmine": e_jasmine, "manhattan": e_manhattan, "wokanna": e_wokanna, "esmel": e_esmel,
    "princess": e_princess, "leaf": e_leaf, "hangyaku": e_hangyaku, "robin": e_robin, "vamilia": e_vamilia, "artel": e_artel,
    "shuto": _fight, "lelady": _fight, "apul": _fight, "jaouga": e_jaouga, "scarlet": e_scarlet, "gigan": e_gigan,
    "dangerdeon": e_dangerdeon, "obza": e_obza, "shako": e_shako,
}


# ====================================================================== 呪文
def sp_douki(s, i):
    t = s.target(i)
    if t is not None:
        s.leave(1 - i, t, "hand", by_opp=True)
    s.draw(i)


def sp_tenbin(s, i):
    p = s.P[i]
    o = s.P[1 - i]
    if s.tp == i:
        if any(u.c.kind == "C" and u.tap and not u.c.noatk for u in p.board):
            for u in p.board:
                u.tap = False
            return
        cs = sorted((u for u in o.board if s.can_block(u)), key=lambda u: -s.power(1 - i, u))
    else:
        cs = sorted((u for u in o.board if u.c.kind == "C" and not u.tap and not u.c.noatk and not u.jd),
                    key=lambda u: -s.power(1 - i, u))
    dk = [u for u in cs if u.k == "douki"]
    for u in (dk + [u for u in cs if u.k != "douki"])[:2]:
        s.tap_cre(1 - i, u)


def sp_shunsen(s, i):
    p = s.P[i]
    n = 2
    a = s.atk
    if s.tp == i and a is not None and a in p.board and not a.re:
        a.re = True
        n -= 1
    while n > 0:
        n -= 1
        best, bv = None, -1
        for k in sorted(set(p.hand)):
            c = CARD[k]
            if c.kind == "C" and c.cost <= 3 and not (c.evo and not c.neo) and PRI[k] > bv:
                if s.fate(i, k, "hand", False) == "ok":
                    best, bv = k, PRI[k]
        if best is not None:
            p.hand.remove(best)
            u = s.enter(i, best, "hand", False)
            if u is not None and n > 0 and s.tp == i and not u.c.noatk:
                u.sa = True
                n -= 1
            continue
        if s.tp == i:
            cs = [u for u in p.board if u.c.kind == "C" and u.sick and not u.sa and not u.c.noatk and not u.tap]
            if cs:
                max(cs, key=lambda u: s.power(i, u)).sa = True
                continue
            cs = [u for u in p.board if u.c.kind == "C" and not u.re and not u.c.noatk and not u.tap]
            if cs:
                max(cs, key=lambda u: s.power(i, u)).re = True


def sp_radio(s, i):
    p = s.P[i]
    n = min(5, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    if not s.has(1 - i, "robin"):
        for _ in range(2):
            best, bv = None, -1
            for k in top:
                c = CARD[k]
                if c.kind == "C" and c.cost <= 3 and not (c.evo and not c.neo) and PRI[k] > bv:
                    if s.fate(i, k, "deck", False) == "ok":
                        best, bv = k, PRI[k]
            if best is None:
                break
            top.remove(best)
            s.ev(f"　ラジオで {CARD[best].name}")
            s.enter(i, best, "deck", False)
    for k in top:
        p.deck.insert(0, k)


def sp_shinten(s, i):
    p = s.P[i]
    o = s.P[1 - i]
    for _ in range(2):
        if s.over:
            return
        mid = s.tp == i and s.atk is not None
        if mid:                                    # 攻撃の途中なら、手札の再攻撃札をただで使う
            k = None
            if "tenbin" in p.hand and s.spell_ok(i, 3, "tenbin"):
                k = "tenbin"
            elif "shunsen" in p.hand and s.spell_ok(i, 3, "shunsen") and not s.atk.re:
                k = "shunsen"
            if k is not None:
                p.hand.remove(k)
                s.ev(f"　心転地：手札の {CARD[k].name} をただで")
                s.cast(i, k)
                continue
        t = None if o.protect else s.target(i, lambda x: x.c.cost <= 6, "CT")
        if t is not None and (PRI[t.k] >= 5 or (mid and s.can_block(t))):
            s.ev(f"　心転地：{t.c.name} をマナへ")
            s.leave(1 - i, t, "mana", by_opp=True)
            continue
        best, bv = None, 0
        for k in sorted(set(p.hand)):
            c = CARD[k]
            if c.cost > 3 or p.ban == c.cost:
                continue
            if c.kind == "C":
                if c.evo and not c.neo or s.fate(i, k, "hand", True) != "ok":
                    continue
            elif c.kind == "S":
                continue
            elif c.kind == "G" and s.tp == i and s.has(1 - i, "fujin"):
                continue
            if PRI[k] > bv:
                best, bv = k, PRI[k]
        if best is not None:
            p.hand.remove(best)
            s.ev(f"　心転地：手札の {CARD[best].name} をただで")
            kind = CARD[best].kind
            if kind == "C":
                s.enter(i, best, "hand", True)
            elif kind == "T":
                s.place_tama(i, best)
            else:
                s.place_castle(i, best)
            continue
        s.draw(i, 2)
        if p.hand:
            k = min(p.hand, key=PRI.get)
            p.hand.remove(k)
            p.deck.insert(0, k)


def sp_majin(s, i):
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    k = max(top, key=lambda x: PRI[x] - 3 * p.hand.count(x))
    top.remove(k)
    for x in top:
        p.deck.insert(0, x)
    if len(p.mana) <= 3 and not s.has(1 - i, "robin"):
        s.add_mana(i, k)
    else:
        p.hand.append(k)


def sp_esmel(s, i):
    s.add_shield(i)


def sp_kerola(s, i):
    s.dig(i, 4, lambda k: True)


def sp_takkyu(s, i):
    p = s.P[i]
    cs = [u for u in p.board if u.c.kind == "C"]
    if not cs:
        return
    u = max(cs, key=lambda x: s.power(i, x))
    _fight(s, i, u)


def sp_mirai(s, i):
    s.dig(i, 6, lambda k: CARD[k].kind == "C")


def sp_saitan(s, i):
    p = s.P[i]
    cs = [u for u in p.board if u.c.kind == "C"]
    if not cs:
        return
    n = len(p.mana)
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = CARD[k]
        if c.kind == "C" and c.cost <= n and not (c.evo and not c.neo) and PRI[k] + c.cost > bv:
            if s.fate(i, k, "hand", False) == "ok":
                best, bv = k, PRI[k] + c.cost
    if best is None:
        return
    s.leave(i, min(cs, key=s.val), "grave", destroy=True)
    if best in p.hand:
        p.hand.remove(best)
        s.ev(f"　緊急再誕で {CARD[best].name}")
        s.enter(i, best, "hand", False)


def sp_efc(s, i):
    p = s.P[i]
    o = s.P[1 - i]
    sn = sorted((k for k in p.hand if k in SNOW), key=PRI.get)[:5]
    for k in sn:
        s.discard(i, k)
    for u in o.board[:]:
        if u.c.kind == "T":
            o.board.remove(u)
            o.grave.append(u.k)
        else:
            s.tap_cre(1 - i, u)
    if any(up for _, up in o.sh):
        for k, up in o.sh:
            if up:
                o.grave.append(k)
        o.sh = [x for x in o.sh if not x[1]]
        s.shield_left()
    o.mused = len(o.mana)
    o.frozen = True
    s.ev("　相手のクリーチャーとマナをすべてタップ。次のターンのはじめに起きない")


def sp_margani(s, i):
    s.dig(i, 3, lambda k: CARD[k].kind == "C", "grave")


def sp_kuzen(s, i):
    s.ramp(i, 1, False)
    s.mill(i, 1)


def sp_dangerdeon(s, i):
    o = s.P[1 - i]
    if o.protect:
        return
    for _ in range(2):
        t = s.target(i, kinds="CT")
        if t is not None:
            s.leave(1 - i, t, "mana", by_opp=True)


def sp_lelady(s, i):
    s.dig(i, 3, lambda k: CARD[k].twin is not None)


def sp_apul(s, i):
    s.dig(i, 3, lambda k: CARD[k].kind == "C" and CARD[k].power >= 12000)


def sp_obza(s, i):
    p = s.P[i]
    s.mill(i, 3)
    best, bv = None, -99
    for k in sorted(set(p.grave)):
        if CARD[k].kind == "C":
            v = PRI[k] - 3 * p.hand.count(k)
            if v > bv:
                best, bv = k, v
    if best is not None:
        p.grave.remove(best)
        p.hand.append(best)


def sp_gio(s, i):
    p = s.P[i]
    n = min(4, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    for k in top:
        if CARD[k].kind == "C" and CARD[k].cost >= 7:
            p.hand.append(k)
        else:
            p.deck.insert(0, k)


SPELL = {
    "douki": sp_douki, "tenbin": sp_tenbin, "shunsen": sp_shunsen, "radio": sp_radio, "shinten": sp_shinten, "majin": sp_majin,
    "esmel": sp_esmel, "kerola": sp_kerola, "takkyu": sp_takkyu, "mirai": sp_mirai, "saitan": sp_saitan, "efc": sp_efc,
    "margani": sp_margani, "kuzen": sp_kuzen, "dangerdeon": sp_dangerdeon, "lelady": sp_lelady, "apul": sp_apul,
    "obza": sp_obza, "gio": sp_gio,
}


# ---- 現環境の新カードを登録する（このファイルの中身がすべて決まったあとに読み込む）----
import envcards            # noqa: E402,F401


def selftest(n_games=2000, seed=1):
    """でたらめな手で対戦を回して、例外が出ないかを見る"""
    from cards3 import DECKS
    rng = random.Random(seed)
    names = list(DECKS)
    n = 0
    for t in range(n_games):
        a, b = rng.choice(names), rng.choice(names)
        g = Game(DECKS[a], DECKS[b], rng, first=t % 2)
        while not g.over:
            g.apply(rng.choice(g.legal()))
            n += 1
    return n


if __name__ == "__main__":
    import engine3                      # 二重読み込みを避けるため、モジュールとして呼び直す
    print("ok", engine3.selftest())
