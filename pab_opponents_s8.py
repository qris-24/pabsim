"""Stage S8 (Task 2b, authorized 2026-10-18): opponents as life totals plus a fixed scripted board.

Layered above pab_cast_s7.CreatureCastMixin (PhysicalZoneGame only). No frozen file edited.

What an opponent is here: a life total (seats 1-3 already exist in Game.life) plus a board
of generic creature bodies declared once at game start with declare_opponent_board(seat,
bodies). No library, hand, mana, spells, attacks or decisions; opponents never act. Their
bodies are ordinary controller != 0 permanents created by the frozen add(), so the frozen
'another creature enters' trigger of Essence Warden already sees them.

Edicts become real (CR 701.19b, 608.2): the frozen kernel only counts Savra's black
sacrifice and Grave Pact as `edict_opportunities`. S8 wraps those two frozen triggers at
enqueue time: when the frozen action records an opportunity (for Savra, only if the 2 life
was actually paid), each opponent still in the game sacrifices one creature chosen by a
fixed, documented stand-in for "their choice" — lowest power, then lowest toughness, then
lowest uid — or is traced as having no creature. `opponent_sacrifices` counts only these
observed sacrifices; `edict_opportunities` keeps the frozen meaning.

An opponent's creature dying goes through _opponent_creature_dies(): the permanent leaves
and exactly the triggers the frozen exogenous path (Game.opposing_creature_dies) enqueues
are enqueued — Deathgreeter, Poison-Tip Archer, Blood Artist, Yahenni, Sangromancer — with
the same labels (parity is tested). No graveyard is kept for opponents.

Players leaving (CR 704.5a, 800.4a): at every state-based-action check a seat at 0 or less
life leaves the game; its permanents leave (they do not die, so nothing triggers) and the
clock gives it no further turns (a turn already under way continues, CR 800.4g), so its
later upkeeps and end steps never happen. When all three
opponents have left, seat 0 has won (CR 104.2a); nothing stops, it is only recorded.
Blood Artist's fixed target becomes the lowest-numbered opponent still in the game (the
controller if none); drains apply only to opponents still in the game.

Not modeled: opponents' spells, attacks, blocks, removal, graveyard hate, hands, libraries,
mana, decisions beyond the fixed edict policy; commander damage; opponents' death triggers.
"""
from __future__ import annotations
from pab_cast_s7 import CreatureCastMixin, check_invariants_s6, run_turns_casting as _run_s7
from pab_turn_clock import TurnClock, ClockError
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger

OPPONENT_SEATS=(1,2,3)
EDICT_SOURCES={'Savra black sacrifice':'Savra black','Grave Pact edict opportunity':'Grave Pact'}

class LossAwareClock(TurnClock):
    """TurnClock whose advance() skips seats that have left the game (CR 800.4a)."""
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw); self.lost=set(); self.skipped=[]
    def advance(self):
        entry=super().advance()
        while self.index==0 and self.active_player in self.lost:      # only at a turn boundary: CR 800.4g keeps the current turn
            if len(self.lost)>=self.seats: raise ClockError('every seat has left the game')
            self.skipped.append((self.turn,self.active_player))
            self.turn+=1; self.active_player=(self.active_player+1)%self.seats
            self.boundaries[-1]=('step_begin',self.turn,self.active_player,self.phase,self.step)
            entry=self.boundaries[-1][1:]
        return entry

class OpponentsMixin(CreatureCastMixin):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.clock=LossAwareClock()          # fresh, same initial state as the S1 clock
        self.lost_seats=set(); self.game_won=False; self.edicts_resolved=0

    # ---- board declaration -------------------------------------------------
    def declare_opponent_board(self,seat,bodies):
        """bodies: iterable of dicts {name, power, toughness, colors}. Game start only (clock not engaged)."""
        if seat not in OPPONENT_SEATS: raise BridgeError('S8: seat must be 1, 2 or 3')
        if self.clock_engaged: raise BridgeError('S8: opponent boards are declared before the clock is engaged')
        if seat in self.lost_seats: raise BridgeError('S8: seat has left the game')
        uids=[]
        for b in bodies:
            name=b['name']; power=b.get('power',1); toughness=b.get('toughness',1); colors=b.get('colors','')
            if not isinstance(power,int) or not isinstance(toughness,int) or toughness<1 or power<0:
                raise BridgeError('S8: opponent body needs integer power >= 0 and toughness >= 1')
            p=self.add(name,controller=seat,colors=colors,creature=True,artifact=False,power=power,toughness=toughness,mana_value=b.get('mana_value',0))   # mana_value: S15 targets
            uids.append(p.uid)
        self.trace.append(('opponent_board_declared',seat,tuple(uids)))
        return uids

    def opponent_creatures(self,seat):
        return [p for p in self.permanents.values() if p.controller==seat and p.creature]
    def seats_in_game(self):
        return [s for s in OPPONENT_SEATS if s not in self.lost_seats]

    # ---- an opponent's creature dies --------------------------------------
    def _opponent_creature_dies(self,uid,*,cause):
        p=self.permanents.get(uid)
        if p is None or p.controller==0 or not p.creature: raise BridgeError('S8: not an opponent creature')
        del self.permanents[uid]
        self.trace.append(('opponent_creature_dies',p.controller,uid,p.name,cause))
        effects=[]                                             # same labels as the frozen exogenous path
        for source in tuple(self.permanents.values()):
            if source.controller!=0: continue
            if source.name=='Deathgreeter' and self.choose_deathgreeter_gain:
                effects.append(Trigger('Deathgreeter opposing death',lambda:self.gain(1,'Deathgreeter')))
            if source.name=='Poison-Tip Archer':
                effects.append(Trigger('Poison-Tip Archer opposing death',lambda:self.drain_opponents(1,'Poison-Tip Archer')))
            if source.name=='Blood Artist':
                effects.append(Trigger('Blood Artist opposing death',lambda:self._blood_artist()))
            if source.name=='Yahenni, Undying Partisan':
                effects.append(Trigger('Yahenni opponent death counter',lambda u=source.uid:self._yahenni_opponent_death(u)))
            if source.name=='Sangromancer' and self.choose_sangromancer_gain:
                effects.append(Trigger('Sangromancer opposing death',lambda:self.gain(3,'Sangromancer opposing death')))
        self._enqueue(effects)
        return p

    # ---- edicts ---------------------------------------------------------------
    def edict_choice(self,seat):
        """Stand-in for 'a creature of their choice': lowest power, then toughness, then uid."""
        cs=self.opponent_creatures(seat)
        return min(cs,key=lambda p:(p.power+p.counters-p.minus_counters,p.toughness+p.counters-p.minus_counters,p.uid)) if cs else None   # S15: counters count on both

    def _edict_each_opponent(self,source):
        self.edicts_resolved+=1
        for seat in self.seats_in_game():
            p=self.edict_choice(seat)
            if p is None:
                self.trace.append(('edict_no_creature',seat,source)); continue
            self.opponent_sacrifices+=1
            self.trace.append(('opponent_sacrifice',seat,p.uid,p.name,source))
            self._opponent_creature_dies(p.uid,cause=source)

    def _enqueue(self,triggers):
        batch=list(triggers)
        for t in batch:
            source=EDICT_SOURCES.get(t.label)
            if source is None or getattr(t,'_s8_wrapped',False): continue
            def wrapped(orig=t.action,source=source):
                before=self.edict_opportunities; orig()
                if self.edict_opportunities>before: self._edict_each_opponent(source)
            t.action=wrapped; t._s8_wrapped=True
        return super()._enqueue(batch)

    # ---- players leaving, targets, drains --------------------------------------
    def state_based_actions(self):
        rounds=super().state_based_actions()
        for seat in OPPONENT_SEATS:
            if seat in self.lost_seats or self.life[seat]>0: continue
            self.lost_seats.add(seat); self.clock.lost.add(seat)
            gone=[u for u,p in self.permanents.items() if p.controller==seat]
            for u in gone: del self.permanents[u]                 # CR 800.4a: leave the game, no death
            self.trace.append(('seat_leaves_game',seat,self.life[seat],tuple(gone)))
            if not self.seats_in_game() and not self.game_won:
                self.game_won=True; self.trace.append(('win_game','all_opponents_left'))
        return rounds

    def _blood_artist(self):
        alive=self.seats_in_game(); target=alive[0] if alive else 0
        self.life[target]-=1
        self.trace.append(('target_opponent_loses',1,'Blood Artist') if target else ('target_self_loses',1,'Blood Artist'))
        self.gain(1,'Blood Artist')

    def drain_opponents(self,amount,source):
        if amount<=0: return
        for i in self.seats_in_game(): self.life[i]-=amount
        self.trace.append(('opponents_lose_each',amount,source))

# ---- invariants and driver --------------------------------------------------
def check_invariants_s8(g):
    check_invariants_s6(g)
    for seat in OPPONENT_SEATS:
        if seat in g.lost_seats and any(p.controller==seat for p in g.permanents.values()):
            raise AssertionError('S8: a seat that left the game still has permanents')
    if g.lost_seats!=g.clock.lost: raise AssertionError('S8: clock and game disagree on lost seats')
    if g.clock.index==0 and g.clock.active_player in g.lost_seats: raise AssertionError('S8: a lost seat began a turn')
    if g.opponent_sacrifices!=len([t for t in g.trace if t[0]=='opponent_sacrifice']):
        raise AssertionError('S8: opponent_sacrifices does not match the trace')

def run_turns_casting(g,turns):
    """S7 driver with S8 invariants checked at every ledger entry."""
    ledger=_run_s7(g,turns); check_invariants_s8(g); return ledger
