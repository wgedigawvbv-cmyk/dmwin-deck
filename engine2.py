"""窓理論のゲームエンジン（第2版）

基本ルール：40枚、シールド5枚、初期手札5枚、先攻1ターン目はドローなし、毎ターン1枚マナチャージ。
第1版（engine.py）との違い
  ・手札から1ターンで決める攻め、手札からの受け、G・ストライク、複数の働きを持つメタ、クリーチャーループを扱う
  ・「待つか、毎ターン動くか」はデッキの性質（遺伝子）として持たせる
      毎ターン動く：出せるものを出し、殴れるなら殴る
      待つ        ：手札の速攻札を抱え、このターンで決め切れると見積もったときだけ一気に出して殴る
  ・相手の正体が分からない想定と、使い手のミスは入れていない（第1版の実験で扱った）
"""
import random
from dataclasses import dataclass

from cards2 import (BY_KEY, CHAIN_NEED, CLOOP_MANA, CLOSURE_JA, COMBO, LOOP_MANA, PATH_JA, STOPS, WB_GRAVE,
                    deck_defense, deck_paths, is_big)

TEMPO = 0            # 両者が最初から持つマナ
LOCK_SWAP_COST = 4   # 一手封殺の入れ替えの元になれるクリーチャーの最小コスト（「入れ替えの元になる大型」はコストを問わない）
NINJA_MANA = 4       # 手札受けを使うのに必要なマナ

# 大会のカバレージから読み取った行動の型（Game の policies で、プレイヤーごとに指定する）
POLICY_FLAGS = {
    "hold": "1ターンで決める：デッキの性質に関係なく「待つ」で動く",
    "onemeta": "メタは1枚だけ先置き：2枚目以降の封殺は後回しにして自分の動きを優先する",
    "clear": "受けを消してから殴る：決めるターンに、トリガー封じを先に出す／ブロッカーを除去する",
    "save": "除去を温存：自分を縛る封殺やコンボの核にだけ使い、小さい相手には撃たない",
}
PRO = frozenset(POLICY_FLAGS)

KEEP = {"castle": 9, "ramp": 3, "mendel": 5, "draw": 2, "mill": 5, "b1": 2, "b2": 4, "b3": 5, "src": 6,
        "sa1": 5, "sa2": 6, "sa3": 6, "rush": 7, "dbl": 8, "dig": 6, "wb": 9, "swap": 8, "swap_lock": 9,
        "m_trig": 6, "m_free": 6, "m_spell": 6, "m_attack": 6, "m_summon": 6, "chakra": 7, "rod": 7, "vt": 6,
        "removal": 6, "wipe": 5, "handes_c": 4, "handes_s": 4,
        "t_stop": 3, "t_tap": 3, "t_remove": 4, "t_wipe": 4, "t_block": 3, "t_big": 5,
        "gs": 3, "ninja": 8, "madness": 7, "counter0": 8, "blocker": 3, "shield": 3}


@dataclass
class View:
    paths: set
    defense: dict


def profile_of(counts):
    return View(deck_paths(counts), deck_defense(counts))


def relevant_closures(v):
    """このデッキに刺さる封殺の種類（勝ち筋か守りのどちらかを止めるもの）"""
    r, p, d = set(), v.paths, v.defense
    if d["triggers"] >= 4:
        r.add("C_TRIG")
    if p & STOPS["C_FREE"] or d["counter0"] >= 2:
        r.add("C_FREE")
    if "LOOP" in p or "WB" in p or d["triggers"] >= 6:
        r.add("C_SPELL")
    if p & STOPS["C_ATTACK"] or d["sa"] >= 6:
        r.add("C_ATTACK")
    if p & STOPS["C_SUMMON"]:
        r.add("C_SUMMON")
    if p & {"ATTACK", "RUSH"}:
        r.add("C_HIT")
    if p & STOPS["C_SMALL"]:
        r.add("C_SMALL")
    return r


@dataclass(eq=False)
class Unit:
    card: object
    tapped: bool = False
    sick: bool = True
    entered: int = 0
    acts: int = 0        # このターンに攻撃した回数
    temp: bool = False   # ターンの終わりに山札の下へ戻る（手札受け）


class Player:
    def __init__(self, name, counts, aggr, rng):
        self.name = name
        self.counts = counts
        self.aggr = aggr
        self.deck = [BY_KEY[k] for k, n in counts.items() for _ in range(n)]
        rng.shuffle(self.deck)
        self.shields = [self.deck.pop() for _ in range(5)]
        self.hand = [self.deck.pop() for _ in range(5)]
        self.mana = TEMPO
        self.mana_cards = []
        self.grave = 0            # 墓地の枚数
        self.discount = 0         # クリーチャーのコスト軽減
        self.safe_until = -1
        self.final_used = False
        self.pol = frozenset()
        self.board = []
        self.spells = 0
        self.summons = 0
        self.burst = False        # このターンで決めにいく
        self.clear_first = False  # 決める前にブロッカーをどかす
        self.used = set()         # このターンに攻撃したカードの役割
        self.paths = deck_paths(counts)
        self.defense = deck_defense(counts)
        self.profile = View(self.paths, self.defense)

    def closes(self, kind):
        return any(kind in u.card.closes for u in self.board)


class Game:
    def __init__(self, deck_a, deck_b, rng, first=0, max_rounds=25, log=None, policies=(None, None)):
        self.log = log
        self._ev = []
        self._free = False
        self.rng = rng
        self.p = [Player("A", deck_a[0], deck_a[1], rng), Player("B", deck_b[0], deck_b[1], rng)]
        self.p[0].pol, self.p[1].pol = (frozenset(x or ()) for x in policies)
        self.views = {"A": self.p[1].profile, "B": self.p[0].profile}
        self.relv = {n: relevant_closures(v) for n, v in self.views.items()}        # 相手に刺さる封殺
        self.hurt = {"A": relevant_closures(self.p[0].profile), "B": relevant_closures(self.p[1].profile)}   # 自分に刺さる封殺
        self.first = first
        self.max_rounds = max_rounds
        self.winner = None
        self.win_path = None
        self.round = 0
        self.turn_idx = 0
        self.turn_ended = False
        self.swapped = False
        self.pre = 5
        # lock：封殺が完了したターン／trig：盾からの受けが効いた回数／hand：手札からの受けが効いた回数
        # meta3：3ターン目の終わりに場にある封殺の枚数（1人あたり）／clean：盾5枚からの1ターンキルで決まったか
        self.stats = {"lock": {}, "trig": 0, "hand": 0, "meta3": 0.0, "clean": False}

    # ---------- 共通 ----------
    def waits(self, me):
        return "hold" in me.pol or not me.aggr

    def keep_score(self, me, c):
        r = c.role
        if r == "castle":
            return 0 if me.discount else 9
        if r in ("chain", "chain_fin"):
            return 8 if "CHAIN" in me.paths else 1
        if r in ("loop_spell", "loop_engine"):
            return 9 if "LOOP" in me.paths else 0
        if r in ("cl_engine", "cl_piece"):
            return 9 if "CLOOP" in me.paths else 1
        if r == "mill":
            return 6 if ("WB" in me.paths and me.grave < WB_GRAVE) else 1
        if r == "mendel":
            return 6 if me.mana <= 4 else 0
        return KEEP.get(c.key, 3)

    def cost_of(self, me, opp, c):
        if c.kind != "creature":
            return c.cost
        if c.role == "wb" and me.grave >= WB_GRAVE and not opp.closes("C_FREE"):
            return 0
        cost = c.cost
        if c.role == "vt":
            cost = max(2, cost - len(opp.board))
        return max(1, cost - me.discount)

    def can_summon(self, me, opp, c):
        if opp.closes("C_SUMMON") and me.summons >= 1:
            return False
        return not (opp.closes("C_SMALL") and c.cost <= 3)

    def can_cast(self, me, opp):
        return not (opp.closes("C_SPELL") and me.spells >= 1)

    def protected(self, pl):
        return self.turn_idx <= pl.safe_until

    def ev(self, who, tag, text):
        if self.log is not None:
            self._ev.append({"who": who.name, "tag": tag, "text": text})

    def snapshot(self):
        def side(p):
            return {"shields": len(p.shields), "hand": len(p.hand), "mana": p.mana,
                    "board": [u.card.name + ("（タップ）" if u.tapped else "") for u in p.board]}
        return {p.name: side(p) for p in self.p}

    def enter(self, me, card, tapped=False, sick=True, temp=False):
        u = Unit(card, tapped=tapped, sick=sick, entered=self.round, temp=temp)
        me.board.append(u)
        me.summons += 1
        if card.role == "swap_lock" and not me.final_used:
            me.final_used = True
            me.safe_until = self.turn_idx + 1
            self.ev(me, "guard", "耐性がつく（次の自分のターンの初めまで、負けない・自分のクリーチャーが相手の効果で離れない）")
        return u

    def threat(self, chooser, owner, u):
        c = u.card
        s = min(c.breaks, 3) * 10 * c.attacks
        for k in c.closes:
            s += 60 if k in self.hurt[chooser.name] else 10
        if c.role in ("loop_engine", "cl_engine"):
            s += 70
        if c.role in ("chain", "chain_fin") and "CHAIN" in owner.paths:
            s += 35
        if c.blocker:
            s += 8
        return s

    def destroy(self, chooser, owner, n, prefer_untapped=False, prefer_blocker=False):
        if chooser is not owner and self.protected(owner):
            self.ev(chooser, "fail", "除去は効かない（相手の耐性）")
            return
        for _ in range(n):
            cand = [u for u in owner.board if not u.card.protect]
            if not cand:
                return
            cand.sort(key=lambda u: ((u.card.blocker and not u.tapped) if prefer_blocker else 0,
                                     (not u.tapped) if prefer_untapped else 0, self.threat(chooser, owner, u)),
                      reverse=True)
            owner.board.remove(cand[0])
            owner.grave += 1
            self.ev(chooser, "remove", f"相手の「{cand[0].card.name}」を除去")

    def bounce(self, chooser, owner, units):
        if chooser is not owner and self.protected(owner):
            return
        for u in units:
            if u in owner.board and not u.card.protect:
                owner.board.remove(u)
                if not u.temp:
                    owner.hand.append(u.card)
                self.ev(chooser, "remove", f"相手の「{u.card.name}」を手札に戻す")

    def draw(self, me, n=1):
        for _ in range(n):
            if not me.deck:
                return False
            me.hand.append(me.deck.pop())
        return True

    def discard(self, me, opp, n):
        """me が opp の手札を捨てさせる。捨てられると出る札は、タダで出て me のクリーチャーを1体手札に戻す"""
        for _ in range(n):
            if not opp.hand:
                return
            c = self.rng.choice(opp.hand)
            opp.hand.remove(c)
            if c.role == "madness" and not me.closes("C_FREE") and self.can_summon(opp, me, c):
                self.enter(opp, c, sick=False)
                self.stats["hand"] += 1
                self.ev(opp, "free", f"捨てさせられた「{c.name}」がタダで出る")
                tg = [u for u in me.board if not u.card.protect]
                if tg:
                    self.bounce(opp, me, [max(tg, key=lambda u: self.threat(opp, me, u))])
            else:
                opp.grave += 1

    # ---------- 判断 ----------
    def chain_count(self, me):
        return sum(1 for u in me.board if u.card.role in ("chain", "chain_fin"))

    def explosive(self, c):
        """手札に抱えておいて、決めるターンに一気に出す札"""
        return (c.kind == "creature" and c.sa and c.role != "chain_fin") or c.role == "dig"

    def priority(self, me, opp, c):
        role = c.role
        if role in ("loop_spell", "counter0", "ninja") or c.trig in ("stop", "tap"):
            return None
        if role == "cl_piece" and "CLOOP" in me.paths:
            return None
        if role in ("swap", "swap_lock") and not self._free:
            return 80 if (role == "swap_lock" and me.mana >= 8) else None
        if role == "castle":
            return None if me.discount else 99
        if c.key == "ramp":
            return 100 if me.mana <= 4 else 5
        if role == "mendel":
            if me.mana > 5:
                return None
            return 96 if me.defense["big"] >= 10 else 50
        if role == "mill":
            return 85 if ("WB" in me.paths and me.grave < WB_GRAVE) else 35
        if self.explosive(c):
            if self.waits(me) and not me.burst:
                return None                      # 待つ：決めるターンまで抱える
            if me.burst:
                return 97 if role == "rush" else (60 if role == "dig" else 90 + min(c.breaks, 5))
            if role == "rush":
                return 86
            if role == "dig":
                return 75 if "RUSH" in me.paths else 35
            if role == "wb":
                return 97 if self.cost_of(me, opp, c) == 0 else 70
            return 50 + c.cost * 5
        if c.closes:
            kind = c.closes[0]
            multi = c.blocker or c.removal or role == "vt"      # 複数の働きを持つメタ
            rel = kind in self.relv[me.name]
            if role == "vt" and sum(1 for u in opp.board if u.card.cost <= 3 and not u.card.protect) >= 2:
                return 94
            if c.removal and any(k in self.hurt[me.name] for u in opp.board for k in u.card.closes):
                return 93
            if me.closes(kind):
                return 55 if multi else 25
            if me.pol and rel and not self._free:
                if "clear" in me.pol and kind == "C_TRIG" and me.burst:
                    return 99
                if "onemeta" in me.pol:
                    if {x for u in me.board for x in u.card.closes} & self.relv[me.name]:
                        return 30
                    return 92 if STOPS[kind] & self.views[me.name].paths else 90
            if rel:
                return 90
            return 60 if multi else 30
        if role == "loop_engine":
            return 88 if "LOOP" in me.paths else 20
        if role == "cl_engine":
            return 88 if "CLOOP" in me.paths else 25
        if role == "chain":
            return 80 if "CHAIN" in me.paths else 25
        if role == "chain_fin":
            return 97 if self.chain_count(me) + 1 >= CHAIN_NEED else 35
        if c.removal and c.kind == "spell":
            cand = [u for u in opp.board if not u.card.protect]
            if not cand or self.protected(opp):
                return None
            if me.clear_first and c.removal == 1:
                return 99
            best = max(self.threat(me, opp, u) for u in cand)
            if c.removal >= 2:
                return 75 if len(cand) >= 3 else None
            if "save" in me.pol:
                return 85 if best >= 60 else None
            return 85 if best >= 60 else (55 if best >= 20 else None)
        if c.handes:
            if not opp.hand:
                return None if c.kind == "spell" else 30
            return 70
        if role == "madness":
            return None if self.views[me.name].defense["handes"] >= 2 else 65
        if c.kind == "spell":
            return 40 if c.shield_add else (45 if c.draw else None)
        if role == "src":
            return 72 if "SWAP" in me.paths else 55
        return 40 + c.cost * 5

    def attack_units(self, me, opp):
        return [u for u in me.board if self.can_attack(me, opp, u)]

    def enough(self, opp, acts, less_blockers=0):
        """攻撃のならび acts（1回の攻撃で割れる枚数のリスト）で、相手の盾を割り切ってダイレクトまで届くか"""
        blockers = sum(1 for b in opp.board if b.card.blocker and not b.tapped)
        if less_blockers:
            blockers = max(0, blockers - min(less_blockers, sum(1 for b in opp.board if b.card.blocker and not b.tapped
                                                               and not b.card.protect)))
        if opp.closes("C_HIT"):
            return bool(acts) and not opp.shields and not blockers
        acts = sorted(acts, reverse=True)[blockers:]
        need, used, got = len(opp.shields), 0, 0
        for b in acts:
            if got >= need:
                break
            got += b
            used += 1
        return got >= need and len(acts) - used >= 1

    def board_acts(self, me, opp):
        acts = []
        for u in self.attack_units(me, opp):
            acts += [u.card.breaks] * (u.card.attacks - u.acts)
        if acts and any(c.role == "swap" for c in me.hand) and not opp.closes("C_FREE"):
            acts[acts.index(min(acts))] = max(min(acts), 3)
        return acts

    def burst_possible(self, me, opp, avail, less_blockers=0):
        """場と手札を合わせて、このターンで決め切れるかの見積もり"""
        acts = self.board_acts(me, opp)
        if not opp.closes("C_ATTACK"):
            mana = avail
            left = (1 - me.summons) if opp.closes("C_SUMMON") else 99
            free = not opp.closes("C_FREE")
            cands = [c for c in me.hand if c.kind == "creature" and c.sa and c.role != "chain_fin"
                     and not (opp.closes("C_SMALL") and c.cost <= 3)]
            rush = next((c for c in cands if c.role == "rush"), None)
            if rush and self.cost_of(me, opp, rush) <= mana and left > 0:
                mana -= self.cost_of(me, opp, rush)
                left -= 1
                cands.remove(rush)
                acts.append(1)
                if free:
                    small = [c for c in cands if c.cost <= 3][:max(0, left)]
                    for c in small:
                        cands.remove(c)
                        acts.append(c.breaks)
                    left -= len(small)
            cands.sort(key=lambda c: -(min(c.breaks, 5) * c.attacks) / max(1, self.cost_of(me, opp, c)))
            for c in cands:
                cost = self.cost_of(me, opp, c)
                if cost <= mana and left > 0:
                    mana -= cost
                    left -= 1
                    acts += [c.breaks] * c.attacks
            if free and left > 0 and self.can_cast(me, opp) and any(c.role == "dig" and c.cost <= mana for c in me.hand):
                acts.append(1)   # 山札からの展開は、1体出ると見込む
        return self.enough(opp, acts, less_blockers)

    # ---------- 自分のターン ----------
    def main_phase(self, me, opp):
        if me.hand and (me.mana < 5 or len(me.hand) >= 3) and not (me.mana >= 8 and len(me.hand) < 4):
            ch = min(me.hand, key=lambda c: (self.keep_score(me, c), self.rng.random()))
            me.hand.remove(ch)
            me.mana_cards.append(ch)
            me.mana += 1
        avail = me.mana
        me.burst = me.clear_first = False
        if self.try_loops(me, opp, avail):
            return
        if self.waits(me):
            if self.burst_possible(me, opp, avail):
                me.burst = True
            elif "clear" in me.pol and self.can_cast(me, opp) and not self.protected(opp):
                rm = [c for c in me.hand if c.kind == "spell" and c.removal == 1 and c.cost <= avail]
                if rm and self.burst_possible(me, opp, avail - min(c.cost for c in rm), less_blockers=1):
                    me.burst = me.clear_first = True
        while avail > 0 and not self.winner:
            opts = []
            for c in me.hand:
                cost = self.cost_of(me, opp, c)
                if cost > avail:
                    continue
                if c.kind == "spell" and not self.can_cast(me, opp):
                    continue
                if c.kind == "creature" and not self.can_summon(me, opp, c):
                    continue
                pr = self.priority(me, opp, c)
                if pr is not None:
                    opts.append((pr, cost, self.rng.random(), c))
            if not opts:
                break
            opts.sort(key=lambda x: x[:3], reverse=True)
            _, cost, _, c = opts[0]
            me.hand.remove(c)
            avail -= cost
            self.play_card(me, opp, c, "タダで" if cost == 0 else f"コスト{cost}で")
            if c.kind == "spell" and c.removal == 1:
                me.clear_first = False
            if self.try_loops(me, opp, avail):
                return
        # タダで出せる全ブレイクは、マナが尽きていても出せる
        if not self.winner and (me.burst or not self.waits(me)):
            for c in [x for x in me.hand if x.role == "wb"]:
                if self.cost_of(me, opp, c) == 0 and self.can_summon(me, opp, c):
                    me.hand.remove(c)
                    self.play_card(me, opp, c, "タダで")

    def try_loops(self, me, opp, avail):
        if self.protected(opp):
            return False
        if "LOOP" in me.paths and avail >= LOOP_MANA and not opp.closes("C_SPELL") and \
                any(u.card.role == "loop_engine" for u in me.board) and any(c.role == "loop_spell" for c in me.hand):
            self.winner, self.win_path = me, "LOOP"
            self.ev(me, "win", "呪文ループが成立して勝ち")
            return True
        if "CLOOP" in me.paths and avail >= CLOOP_MANA and not opp.closes("C_SUMMON") and not opp.closes("C_SMALL") and \
                any(u.card.role == "cl_engine" for u in me.board) and sum(c.role == "cl_piece" for c in me.hand) >= 2:
            self.winner, self.win_path = me, "CLOOP"
            self.ev(me, "win", "クリーチャーループが成立して勝ち")
            return True
        return False

    def play_card(self, me, opp, c, how):
        self.ev(me, "play", f"「{c.name}」を{how}{'出す' if c.kind == 'creature' else '使う'}")
        if c.kind == "field":
            me.discount = 1
            return
        if c.kind == "spell":
            me.spells += 1
            me.grave += 1
            if c.role == "mill":
                n = min(3, max(0, len(me.deck) - 1))
                del me.deck[len(me.deck) - n:]
                me.grave += n
            elif c.role == "mendel":
                for _ in range(2):
                    if len(me.deck) > 1:
                        x = me.deck.pop()
                        if is_big(x):
                            me.mana_cards.append(x)
                            me.mana += 1
                        else:
                            me.grave += 1
            elif c.role == "dig":
                top = [me.deck.pop() for _ in range(min(5, max(0, len(me.deck) - 1)))]
                if not opp.closes("C_FREE"):
                    score = lambda x: 3 if x.role == "rush" else (2 if x.sa else (1.5 if x.closes and x.closes[0] in self.relv[me.name] else 1))
                    picks = sorted([x for x in top if x.kind == "creature" and x.cost <= 3], key=score, reverse=True)[:2]
                    for x in picks:
                        if self.can_summon(me, opp, x):
                            top.remove(x)
                            self.put(me, opp, x, "山札からタダで")
                for x in top:
                    me.deck.insert(0, x)
            self.effects(me, opp, c)
            return
        self.put(me, opp, c, None)

    def put(self, me, opp, c, how):
        """クリーチャーを場に出して、出た時の効果を解決する"""
        if how:
            self.ev(me, "free", f"「{c.name}」を{how}出す")
        self.enter(me, c)
        self.effects(me, opp, c)
        r = c.role
        if r == "chain" and not opp.closes("C_FREE"):
            while True:
                nxt = next((x for x in me.hand if x.role in ("chain", "chain_fin") and self.can_summon(me, opp, x)), None)
                if not nxt:
                    break
                me.hand.remove(nxt)
                self.enter(me, nxt)
                self.ev(me, "free", f"連鎖：「{nxt.name}」をタダで出す")
        elif r == "rush":
            self.draw(me, 1)
            if not opp.closes("C_FREE"):
                cand = [x for x in me.hand if x.kind == "creature" and x.cost <= 3 and self.can_summon(me, opp, x)
                        and x.role not in ("cl_piece", "ninja")]
                if cand:
                    nxt = max(cand, key=lambda x: (x.role == "rush", x.sa, x.breaks))
                    me.hand.remove(nxt)
                    self.put(me, opp, nxt, "連鎖展開でタダで")
        elif r == "vt":
            self.bounce(me, opp, [u for u in opp.board if u.card.cost <= 3])

    def effects(self, me, opp, c):
        if c.ramp and len(me.deck) > 1:
            me.mana_cards.append(me.deck.pop())
            me.mana += c.ramp
        if c.draw:
            self.draw(me, c.draw)
        if c.handes:
            self.discard(me, opp, c.handes)
        if c.removal:
            self.destroy(me, opp, c.removal, prefer_blocker=me.clear_first)
        if c.shield_add:
            for _ in range(c.shield_add):
                if len(me.deck) > 1:
                    me.shields.append(me.deck.pop())

    # ---------- 攻撃 ----------
    def can_attack(self, me, opp, u):
        if u.tapped or u.card.breaks == 0 or u.temp or u.acts >= u.card.attacks:
            return False
        if u.entered == self.round:
            if opp.closes("C_ATTACK"):
                return False
            return u.card.sa or not u.sick
        return True

    def lock_swap_ok(self, me, opp, u):
        return ((u.card.cost >= LOCK_SWAP_COST or u.card.role == "src") and u.card.role not in ("swap_lock", "wb")
                and (not opp.closes("C_FREE") or not me.final_used)
                and any(c.role == "swap_lock" for c in me.hand)
                and self.can_summon(me, opp, BY_KEY["swap_lock"]))

    def attack_phase(self, me, opp):
        ready = self.attack_units(me, opp)
        fin = next((u for u in ready if u.card.role == "chain_fin"), None)
        if fin and self.chain_count(me) >= CHAIN_NEED and not self.protected(opp):
            self.winner, self.win_path = me, "CHAIN"
            self.ev(me, "win", "連鎖がそろった状態でフィニッシャーが攻撃 → 特殊勝利")
            return
        if not ready:
            return
        go = (not self.waits(me)) or me.burst or not opp.shields or self.enough(opp, self.board_acts(me, opp))
        attacks = 0
        while not self.winner and not self.turn_ended:
            ready = [u for u in self.attack_units(me, opp) if go or self.lock_swap_ok(me, opp, u)]
            if not ready:
                return
            if attacks >= 1 and opp.closes("C_HIT"):
                self.ev(me, "fail", "これ以上は攻撃できない（相手の「攻撃は1体まで」）")
                return
            u = max(ready, key=lambda x: (min(x.card.breaks, 9), x.card.cost))
            attacks += 1
            self.attack_with(me, opp, u)

    def attack_with(self, me, opp, u):
        lock_now = self.lock_swap_ok(me, opp, u)
        u.acts += 1
        u.tapped = u.acts >= u.card.attacks
        attacker = u
        me.used.add(u.card.role or u.card.key)
        self.ev(me, "attack", f"「{u.card.name}」で攻撃")
        sw = next((c for c in me.hand if c.role == "swap"), None)
        if lock_now or (sw and u.card.breaks < sw.breaks and not opp.closes("C_FREE") and self.can_summon(me, opp, sw)):
            new = next(c for c in me.hand if c.role == "swap_lock") if lock_now else sw
            me.hand.remove(new)
            me.board.remove(u)
            me.hand.append(u.card)
            self.ev(me, "free", f"入れ替え：「{u.card.name}」が手札に戻り、「{new.name}」がタダで出る")
            attacker = self.enter(me, new, tapped=True)
            self.swapped = True
        # 守る側：ブロッカー → 手札受け → 0コスト受け
        blk = next((b for b in opp.board if b.card.blocker and not b.tapped), None)
        if blk and (not opp.shields or attacker.card.breaks >= 2 or opp.closes("C_HIT")):
            blk.tapped = True
            self.ev(opp, "block", f"「{blk.card.name}」でブロック")
            return
        nj = next((c for c in opp.hand if c.role == "ninja"), None)
        if nj and opp.mana >= NINJA_MANA and len(opp.shields) <= 2 and not me.closes("C_FREE") and self.can_summon(opp, me, nj):
            opp.hand.remove(nj)
            self.enter(opp, nj, tapped=True, sick=False, temp=True)
            self.stats["hand"] += 1
            self.ev(opp, "free", f"手札受け：「{nj.name}」が手札からタダで出てブロック")
            return
        if not opp.shields:
            cnt = next((c for c in opp.hand if c.role == "counter0"), None)
            if cnt and not me.closes("C_FREE") and self.can_summon(opp, me, cnt):
                opp.hand.remove(cnt)
                if attacker in me.board and not self.protected(me):
                    me.board.remove(attacker)
                    me.grave += 1
                self.enter(opp, cnt, sick=False)
                self.stats["hand"] += 1
                self.ev(opp, "free", f"0コスト受け：「{cnt.name}」が手札からタダで出て、ダイレクトアタックを止める")
                return
            if self.protected(opp):
                self.ev(opp, "guard", "ダイレクトアタックを受けたが、耐性で負けない")
                return
            used = me.used
            self.win_path = "WB" if "wb" in used else ("SWAP" if self.swapped else ("RUSH" if used & {"rush", "dbl"} else "ATTACK"))
            self.winner = me
            self.ev(me, "win", "ダイレクトアタックが通って勝ち")
            return
        for _ in range(min(attacker.card.breaks, len(opp.shields))):
            self.shield_to(opp, me, opp.shields.pop())
            if self.turn_ended:
                return

    def shield_to(self, owner, atk, s):
        """割られたシールドの処理"""
        if s.gstrike:
            owner.hand.append(s)
            tg = self.attack_units(atk, owner)
            if tg:
                t = max(tg, key=lambda u: (min(u.card.breaks, 9), u.card.cost))
                t.tapped = True
                t.acts = 99
                self.stats["trig"] += 1
                self.ev(owner, "trigger", f"盾が割られる → G・ストライク「{s.name}」：相手の「{t.card.name}」の攻撃を止める")
            else:
                self.ev(owner, "break", f"盾が割られる →「{s.name}」が手札へ")
            return
        why = ""
        usable = bool(s.trig)
        if usable and atk.closes("C_TRIG"):
            usable, why = False, "トリガー封じ"
        if usable and s.kind == "spell" and not self.can_cast(owner, atk):
            usable, why = False, "呪文制限"
        if usable and s.kind == "creature" and (atk.closes("C_FREE") or not self.can_summon(owner, atk, s)):
            usable, why = False, "踏み倒し封じ・展開制限"
        if not usable:
            owner.hand.append(s)
            self.ev(owner, "fail" if why else "break",
                    f"盾が割られる →「{s.name}」" + (f"（S・トリガーだが{why}で使えない）" if why else "") + "が手札へ")
            return
        t = s.trig
        self.stats["trig"] += 1
        self.ev(owner, "trigger", f"盾が割られる → S・トリガー「{s.name}」")
        if s.kind == "spell":
            owner.spells += 1
            owner.grave += 1
        if t == "stop":
            self.turn_ended = True
        elif t == "tap":
            for u in atk.board:
                u.tapped = True
        elif t == "remove":
            self.destroy(owner, atk, 1, prefer_untapped=True)
        elif t == "wipe":
            self.destroy(owner, atk, 2, prefer_untapped=True)
        elif t in ("block", "big"):
            self.enter(owner, s, sick=False)

    # ---------- ターンの終わり ----------
    def end_phase(self, me, opp):
        """一手封殺の入れ替えが場にいれば：山札の上2枚をマナへ。手札かマナからクリーチャーを2体まで（コスト合計7以下）タダで出す"""
        if not any(u.card.role == "swap_lock" for u in me.board):
            return
        for _ in range(2):
            if len(me.deck) > 1:
                me.mana_cards.append(me.deck.pop())
                me.mana += 1
        if opp.closes("C_FREE") and not self.protected(me):
            return
        scored = []
        for c, src in [(c, "hand") for c in me.hand] + [(c, "mana") for c in me.mana_cards]:
            if c.kind != "creature" or c.role in ("swap_lock", "swap", "wb", "ninja") or c.cost > 7:
                continue
            self._free = True
            pr = self.priority(me, opp, c)
            self._free = False
            if self.explosive(c):
                pr = 35
            scored.append((20 if pr is None else pr, c, src))
        if not scored:
            return
        best, best_v = None, -1.0
        for i, (v1, c1, s1) in enumerate(scored):
            if v1 > best_v:
                best, best_v = [(c1, s1)], v1
            for v2, c2, s2 in scored[i + 1:]:
                if c1.cost + c2.cost > 7:
                    continue
                v = v1 + (25 if (c2.closes and c2.closes == c1.closes) else v2)
                if v > best_v:
                    best, best_v = [(c1, s1), (c2, s2)], v
        for c, src in best:
            if not self.can_summon(me, opp, c):
                continue
            if src == "hand":
                me.hand.remove(c)
            else:
                me.mana_cards.remove(c)
                me.mana -= 1
            self.put(me, opp, c, "ターンの終わりに" + ("手札から" if src == "hand" else "マナから") + "タダで")

    def path_closed(self, x, p, y):
        if p == "ATTACK":
            return x.closes("C_HIT") and any(u.card.blocker for u in x.board)
        if p == "SWAP":
            unused = y.counts.get("swap_lock", 0) >= 2 and not y.final_used
            return x.closes("C_FREE") and not unused
        return any(x.closes(k) for k, ps in STOPS.items() if p in ps)

    def note_lock(self):
        for x, y in ((self.p[0], self.p[1]), (self.p[1], self.p[0])):
            if x.name in self.stats["lock"] or not y.paths:
                continue
            if all(self.path_closed(x, p, y) for p in y.paths):
                self.stats["lock"][x.name] = self.round
                self.ev(x, "lock", "封殺が完了：相手の経路（" + "・".join(PATH_JA[p] for p in sorted(y.paths)) + "）をすべて閉じた")

    # ---------- 進行 ----------
    def play(self):
        cur = self.first
        for turn in range(self.max_rounds * 2):
            me, opp = self.p[cur], self.p[1 - cur]
            self.round = turn // 2 + 1
            self.turn_idx = turn
            self.turn_ended = False
            self.swapped = False
            self.pre = len(opp.shields)
            self._ev = []
            me.spells = me.summons = opp.spells = opp.summons = 0
            me.used = set()
            for u in me.board:
                u.tapped = False
                u.sick = False
                u.acts = 0
            if turn > 0 and not self.draw(me):
                self.winner, self.win_path = opp, "DECKOUT"
            if not self.winner:
                self.main_phase(me, opp)
            if not self.winner and not self.turn_ended:
                self.attack_phase(me, opp)
            if not self.winner:
                if not self.turn_ended:
                    self.end_phase(me, opp)
                self.note_lock()
                for pl in self.p:                      # 手札受けは山札の下へ戻る
                    for u in [u for u in pl.board if u.temp]:
                        pl.board.remove(u)
                        pl.deck.insert(0, u.card)
                if self.round == 3:
                    self.stats["meta3"] = sum(bool(u.card.closes) for pl in self.p for u in pl.board) / 2
            if self.log is not None:
                self.log.append({"round": self.round, "player": me.name, "events": self._ev, "state": self.snapshot()})
            if self.winner:
                self.stats["clean"] = self.pre >= 5 and self.win_path in ("ATTACK", "SWAP", "RUSH", "WB")
                break
            cur = 1 - cur
        return self.winner.name if self.winner else None
