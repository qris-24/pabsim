"""Stage S11 (authorized 2026-10-18 11:05): scripted opponent interaction.

Layered above pab_commander_s10.CommanderMixin (PhysicalZoneGame only). No frozen file edited.
Opponents still have no cards, mana or decisions. What they gain is a SCRIPT: a list of
actions declared at game start that fire when the clock reaches the named game turn in that
seat's own precombat main phase (sorcery speed; the controller cannot respond — no priority
exchange is modeled, so the action simply happens when the step begins). Each action is an
exogenous event with a fixed, documented target policy; nothing is inferred from the board.

  destroy_commander   destroy Savra if she is on the battlefield (frozen destroy(): honours
                      until-end-of-turn indestructibility); traced `no_target` otherwise
  destroy_creature    destroy the controller's highest-power nontoken creature (Savra last,
                      tokens never); frozen destroy() -> dies triggers, graveyard link
  exile_creature      same policy; the permanent leaves without dying (no triggers), the
                      card goes to zones['exile'], tokens cease; Savra then returns to the
                      command zone at the next SBA check (S10, CR 903.9a)
  exile_commander     CP38 (K5), policy-only (S18 exile_instead): exile Savra if she is on
                      the battlefield (same exile path); traced `no_target` otherwise
  board_wipe          every creature of every seat is destroyed as ONE event: leave-the-
                      battlefield triggers look back at the whole pre-wipe board (CR 603.10a,
                      the S3 look-back view), including the controller's own dying Blood
                      Artist / Deathgreeter / Poison-Tip Archer for every other death;
                      indestructible creatures survive; CP38 (K2): a creature with a
                      regeneration shield is regenerated instead (CR 701.15a)
  graveyard_exile     every card in the controller's graveyard is exiled (Bojuka Bog style):
                      physical cards -> exile, graveyard links and LKI dropped
  edict               the controller sacrifices one creature by a fixed policy (a token if
                      any, else the lowest-power nontoken that is not Savra, else Savra;
                      CP38 (K11): power is the current power, counters and Skullclamp included)
                      through the frozen sacrifice(), so Savra's own triggers fire

Not modeled: counterspells, instant-speed interaction, targeted discard, bounce, -X/-X,
stolen permanents, opponents' responses, opponents' creatures attacking, and any choice
by the opponents beyond the script.
"""
from __future__ import annotations
from pab_commander_s10 import CommanderMixin, check_invariants_s10, commander_need, cast_commander_when_able
from pab_lands_s9 import tap_lands_policy, play_land_policy
from pab_opponents_s8 import OPPONENT_SEATS
from pab_clock_s3 import _LookBack
from pab_zone_bridge import BridgeError
from pab_focus_engine import SAVRA
import pab_cast_s7 as _s7

KINDS=('destroy_commander','destroy_creature','exile_creature','board_wipe','graveyard_exile','edict')
POLICY_ONLY_KINDS=('exile_commander',)     # CP38 (K5): fired by S18 policies, not scriptable (KINDS stays the scripted six)

class InteractionMixin(CommanderMixin):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.opponent_script: list[dict]=[]         # {'seat','turn','kind'} pending
        self.opponent_actions_done: list[tuple]=[]

    # ---- declaration ------------------------------------------------------
    def script_opponent_actions(self,seat,actions):
        if seat not in OPPONENT_SEATS: raise BridgeError('S11: seat must be 1, 2 or 3')
        if self.clock_engaged: raise BridgeError('S11: scripts are declared before the clock is engaged')
        for a in actions:
            if a.get('kind') not in KINDS or not isinstance(a.get('turn'),int) or a['turn']<1:
                raise BridgeError('S11: action needs a known kind and a positive game turn')
            owner=(a['turn']-1)%self.clock.seats                   # CP10 (AUD-02): fixed four-seat clock, turn 1 = seat 0, so turn t belongs to seat (t-1) % 4
            if owner!=seat:
                raise ValueError(f"S11: seat {seat} cannot act on turn {a['turn']}: that turn belongs to seat {owner} ((turn-1) % {self.clock.seats})")
        for a in actions:                                          # validated as a whole before anything is scheduled
            self.opponent_script.append({'seat':seat,'turn':a['turn'],'kind':a['kind']})
        self.trace.append(('opponent_script_declared',seat,tuple((a['turn'],a['kind']) for a in actions)))

    def assert_opponent_script_exhausted(self):
        """CP10 (AUD-02): for scenario ends — every scheduled opponent action must have fired."""
        if self.opponent_script:
            raise AssertionError('S11: opponent script still pending: '+', '.join(f"seat {a['seat']} turn {a['turn']} {a['kind']}" for a in self.opponent_script))

    # ---- firing -----------------------------------------------------------
    def advance_step(self):
        turn,ap,phase,step=super().advance_step()
        if step=='precombat_main' and ap in OPPONENT_SEATS and ap not in self.lost_seats:
            due=[a for a in self.opponent_script if a['seat']==ap and a['turn']==turn]
            for a in due:
                self.opponent_script.remove(a)
                self.trace.append(('opponent_action',ap,turn,a['kind']))
                getattr(self,'_act_'+a['kind'])(ap)
                self.opponent_actions_done.append((turn,ap,a['kind']))
                self.state_based_actions()                     # a player would receive priority (704.3); Savra's 903.9a return happens here
                self.assert_bridge_integrity()
        return turn,ap,phase,step

    # ---- target policy ----------------------------------------------------
    def _own_creature_target(self,*,commander_only=False):
        own=[p for p in self.permanents.values() if p.controller==0 and p.creature and p.token is None]
        if commander_only: return next((p for p in own if p.name==SAVRA),None)
        others=[p for p in own if p.name!=SAVRA]
        if others: return max(others,key=lambda p:(self._current_power(p),-p.uid))      # CP38: the power S18's reason reads
        return next((p for p in own if p.name==SAVRA),None)

    def _exile_own(self,p,cause):
        uid=p.uid; physical=self.linked_battlefield.get(uid); token_uid=getattr(self,'linked_tokens',{}).get(uid)
        del self.permanents[uid]
        self.skullclamp_attached={k:v for k,v in self.skullclamp_attached.items() if k!=uid and v!=uid}
        if physical is not None:
            del self.linked_battlefield[uid]; self.zones.move(physical,'exile')
        elif token_uid is not None:
            del self.linked_tokens[uid]; self.zones.move(token_uid,'exile')        # token ceases on leaving the battlefield
        self.cards_exiled.append(p.name)
        self.trace.append(('exiled',uid,p.name,cause))

    # ---- the six actions --------------------------------------------------
    def _act_destroy_commander(self,seat):
        p=self._own_creature_target(commander_only=True)
        if p is None: self.trace.append(('no_target',seat,'destroy_commander')); return
        self.destroy(p.uid)
    def _act_destroy_creature(self,seat):
        p=self._own_creature_target()
        if p is None: self.trace.append(('no_target',seat,'destroy_creature')); return
        self.destroy(p.uid)
    def _act_exile_creature(self,seat):
        p=self._own_creature_target()
        if p is None: self.trace.append(('no_target',seat,'exile_creature')); return
        self._exile_own(p,'exile_creature')
    def _act_exile_commander(self,seat):
        p=self._own_creature_target(commander_only=True)
        if p is None: self.trace.append(('no_target',seat,'exile_commander')); return
        self._exile_own(p,'exile_commander')
    def _act_board_wipe(self,seat):
        dying=[p for p in self.permanents.values() if p.creature and p.uid not in self.indestructible_until_eot]
        shielded=[q for q in dying if q.uid in getattr(self,'regen_shields',())]
        for p in shielded: self._regenerate(p)                                    # CP38 (K2): destruction replaced (CR 701.15a)
        dying=[p for p in dying if p not in shielded]
        self.trace.append(('board_wipe',seat,tuple(p.uid for p in dying)))
        live=self.permanents; self.permanents=_LookBack(live,live.values())
        try:
            for p in dying:
                if p.controller==0: self._leave(p.uid,sacrificed=False)
                else: self._opponent_creature_dies(p.uid,cause='board_wipe')
        finally:
            self.permanents=dict(self.permanents)
    def _act_graveyard_exile(self,seat):
        uids=list(self.zones.zones['graveyard'])
        for u in uids: self.zones.move(u,'exile')
        self.linked_graveyard={}; self.graveyard=[]
        self.cards_exiled.extend(self.zones.cards[u].name for u in uids)
        self.trace.append(('graveyard_exiled',seat,tuple(uids)))
    def _act_edict(self,seat):
        own=[p for p in self.permanents.values() if p.controller==0 and p.creature]
        if not own: self.trace.append(('no_target',seat,'edict')); return
        tokens=[p for p in own if p.token is not None]
        if tokens: p=min(tokens,key=lambda q:q.uid)
        else:
            others=[q for q in own if q.name!=SAVRA]
            p=min(others,key=lambda q:(self._current_power(q),q.uid)) if others else next(q for q in own if q.name==SAVRA)   # CP38 (K11)
        self.trace.append(('edict_against_controller',seat,p.uid,p.name))
        self.sacrifice(p.uid)

# ---- invariants and driver --------------------------------------------------
def check_invariants_s11(g):
    check_invariants_s10(g)
    z=g.zones
    if any(z.cards[u].token for u in z.zones['exile']): raise AssertionError('S11: a token is in exile')
    if len(g.opponent_actions_done)!=len([t for t in g.trace if t[0]=='opponent_action']): raise AssertionError('S11: action log and trace disagree')

def run_turns_casting(g,turns):
    """S10 driver shape with S11 invariants; scripted actions fire inside advance_step()."""
    ledger=[]; start=g.clock.turn
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s11(g)
        if ap!=0 or st!='precombat_main': continue
        u,kw=play_land_policy(g); played=None
        if u is not None: played=g.play_physical_land(u,**kw).name; g.resolve(); check_invariants_s11(g)
        mana=tap_lands_policy(g,extra=commander_need(g))
        cast=[SAVRA] if cast_commander_when_able(g) else []
        cast+=_s7.cast_when_able(g); check_invariants_s11(g)
        ledger.append((t,played,tuple(mana),tuple(cast)))
    return ledger
