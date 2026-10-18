"""Stage S18 (authorized 2026-10-18 11:05; "pause at 20"): policy opponents.

Layered above pab_combat_s17.CombatMixin (PhysicalZoneGame only). No frozen file edited.
Opponents stop being pure scripts: each seat may carry a POLICY — a small, fixed, documented
decision rule evaluated at that seat's own precombat main and declare-attackers steps.
Every action it takes is one of the S11 primitives, so the rules semantics are unchanged;
what is new is WHEN they fire and that the controller can now be attacked and can lose.

set_opponent_policy(seat, {...}) at game start (clock not engaged). Keys, all optional:
  wipe_at           wipe the board when the controller controls at least this many creatures
  wipe_budget       how many wipes this seat has (default 1 when wipe_at is set)
  removal_budget    single-target removals (destroy_commander if Savra is on the battlefield,
                    else destroy_creature when the controller's best nontoken creature has
                    power >= removal_min_power, default 2)
  exile_instead     use exile_creature instead of destroy_creature (removal that beats
                    Infuse / regeneration / the command-zone return is still only the
                    exile_creature primitive: Savra returns from exile too, CR 903.9a)
  graveyard_hate_at exile the controller's graveyard once it holds at least this many cards
  graveyard_budget  default 1 when graveyard_hate_at is set
  edict_budget      edicts, used only when the controller controls a creature and no
                    removal fired this turn
  attack            'none' (default) | 'all' — every creature the seat has controlled since
                    its turn began attacks the controller (opponents never attack each other)
At most one main-phase action per seat per turn, in the order wipe > removal > graveyard
hate > edict. Each firing is traced ('policy_action', seat, turn, kind, reason).

Controller defense: block_policy applies to the controller too when an opponent attacks
(PhysicalZoneGame(block_policy='none'|'all'); 'all' = each untapped controller creature
blocks the highest-power attacker it legally can; Savra never blocks under 'all'). Damage to
the controller goes to life[0]; the frozen resolve() adjudicates the loss at 0 or less
(game_lost) — the first time the kernel can lose a game.

Not modeled: opponents attacking each other, opponents' responses or instant-speed play,
threat assessment beyond these rules, opponents casting anything.
"""
from __future__ import annotations
from pab_combat_s17 import CombatMixin, check_invariants_s17, HASTE_NAMES
from pab_opponents_s8 import OPPONENT_SEATS
from pab_zone_bridge import BridgeError
from pab_focus_engine import SAVRA

POLICY_KEYS={'wipe_at','wipe_budget','removal_budget','removal_min_power','exile_instead','graveyard_hate_at','graveyard_budget','edict_budget','attack'}

class PolicyOpponentsMixin(CombatMixin):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw); self.opponent_policy={}; self.policy_actions=[]

    def set_opponent_policy(self,seat,policy):
        if seat not in OPPONENT_SEATS: raise BridgeError('S18: seat must be 1, 2 or 3')
        if self.clock_engaged: raise BridgeError('S18: policies are set before the clock is engaged')
        bad=set(policy)-POLICY_KEYS
        if bad: raise BridgeError(f'S18: unknown policy keys {sorted(bad)}')
        if policy.get('attack','none') not in ('none','all'): raise BridgeError("S18: attack must be 'none' or 'all'")
        p=dict(policy)
        if 'wipe_at' in p: p.setdefault('wipe_budget',1)
        if 'graveyard_hate_at' in p: p.setdefault('graveyard_budget',1)
        p.setdefault('removal_budget',0); p.setdefault('removal_min_power',2); p.setdefault('edict_budget',0); p.setdefault('attack','none')
        self.opponent_policy[seat]=p; self.trace.append(('opponent_policy_set',seat,tuple(sorted(p.items()))))

    # ---- decisions ----
    def _own_creatures(self): return [p for p in self.permanents.values() if p.controller==0 and p.creature]
    def _policy_main(self,seat,turn):
        pol=self.opponent_policy.get(seat)
        if not pol: return
        own=self._own_creatures(); gy=len(self.zones.zones['graveyard'])
        if pol.get('wipe_at') is not None and pol['wipe_budget']>0 and len(own)>=pol['wipe_at']:
            pol['wipe_budget']-=1; self._fire(seat,turn,'board_wipe',f'controller creatures {len(own)} >= {pol["wipe_at"]}'); return
        if pol['removal_budget']>0:
            sv=next((p for p in own if p.name==SAVRA and p.uid in self.linked_battlefield and p.uid not in self.hexproof_eot),None)
            best=max([p for p in own if p.token is None and p.name!=SAVRA and p.uid not in self.hexproof_eot],key=lambda p:(self._power(p),-p.uid),default=None)
            if sv is not None:
                pol['removal_budget']-=1; self._fire(seat,turn,'exile_creature' if pol.get('exile_instead') else 'destroy_commander','Savra on the battlefield'); return
            if best is not None and self._power(best)>=pol['removal_min_power']:
                pol['removal_budget']-=1; self._fire(seat,turn,'exile_creature' if pol.get('exile_instead') else 'destroy_creature',f'{best.name} power {self._power(best)}'); return
        if pol.get('graveyard_hate_at') is not None and pol['graveyard_budget']>0 and gy>=pol['graveyard_hate_at']:
            pol['graveyard_budget']-=1; self._fire(seat,turn,'graveyard_exile',f'graveyard {gy} >= {pol["graveyard_hate_at"]}'); return
        if pol['edict_budget']>0 and own:
            pol['edict_budget']-=1; self._fire(seat,turn,'edict',f'controller has {len(own)} creatures'); return
    def _fire(self,seat,turn,kind,reason):
        self.trace.append(('policy_action',seat,turn,kind,reason)); self.trace.append(('opponent_action',seat,turn,kind)); self.policy_actions.append((turn,seat,kind,reason))
        getattr(self,'_act_'+kind)(seat); self.opponent_actions_done.append((turn,seat,kind)); self.state_based_actions(); self.assert_bridge_integrity()

    # ---- opponents' attacks and the controller's blocks ----
    def _opponent_attacks(self,seat,turn):
        pol=self.opponent_policy.get(seat)
        if not pol or pol['attack']!='all' or seat in self.lost_seats: return
        atk=[q for q in self.opponent_creatures(seat) if not q.tapped and getattr(q,'entered_turn',0)<turn]
        if not atk: return
        for q in atk: q.tapped=True; self.attackers[q.uid]=0
        self.trace.append(('opponent_attackers_declared',seat,tuple(q.uid for q in atk)))
    def _controller_blocks(self):
        self.blocks={}
        if self.block_policy!='all': self.trace.append(('blocks_declared',())); return
        targets=[u for u,s in self.attackers.items() if s==0 and u in self.permanents]
        for b in sorted(self._own_creatures(),key=lambda q:(-self._power(q),q.uid)):
            if b.tapped or b.name==SAVRA: continue
            cands=sorted(targets,key=lambda u:(-self._power(self.permanents[u]),u))
            if cands: self.blocks.setdefault(cands[0],[]).append(b.uid)
        self.trace.append(('blocks_declared',tuple((a,tuple(bs)) for a,bs in self.blocks.items())))

    def advance_step(self):
        turn,ap,phase,step=super().advance_step()
        if ap in OPPONENT_SEATS and ap not in self.lost_seats:
            if step=='untap':                                              # CR 502.3 for the active opponent (S4 untaps only the controller)
                n=0
                for q in self.permanents.values():
                    if q.controller==ap and q.tapped: q.tapped=False; n+=1
                self.trace.append(('opponent_untap_step',ap,turn,n))
            elif step=='precombat_main': self._policy_main(ap,turn)
            elif step=='declare_attackers': self._opponent_attacks(ap,turn)
            elif step=='declare_blockers' and self.attackers: self._controller_blocks()
            elif step=='combat_damage' and self.attackers: self._combat_damage(); self.resolve()
        return turn,ap,phase,step
    def _combat_damage(self):
        if self.attackers and all(s==0 for s in self.attackers.values()):
            events=[]
            for a in list(self.attackers):
                p=self.permanents.get(a)
                if p is None: continue
                blockers=[b for b in self.blocks.get(a,[]) if b in self.permanents]; dmg=self._power(p)
                if not blockers: self.life[0]-=dmg; events.append(('player',0,a,dmg))
                else:
                    first=blockers[0]; self.damage_marked[first]=self.damage_marked.get(first,0)+dmg; events.append(('creature',first,a,dmg))
                    for b in blockers:
                        q=self.permanents[b]; bd=self._power(q); self.damage_marked[a]=self.damage_marked.get(a,0)+bd; events.append(('creature',a,b,bd))
                        if self._deathtouch(q) and bd>0: self.damage_marked[('deathtouch',a)]=True
            self.trace.append(('combat_damage',tuple(events))); self.combat_log.append((self.clock.turn,tuple(events)))
            self.state_based_actions(); return
        return super()._combat_damage()

    # ---- R55 (found by S18 whole-game runs): the frozen bridge's _return_creature_from_graveyard runs the
    # engine's add() BEFORE dropping the graveyard link; a returning creature whose add() makes tokens
    # (Moseo, Innkeeper) hits assert_bridge_integrity with a link to a card that has no LKI any more.
    # Same steps in a safe order: drop the link, engine return, move the card, relink. Frozen file untouched.
    def _return_creature_from_graveyard(self,cand,source,*,tapped=False):
        from pab_grist_s16 import GRIST
        import pab_focus_engine_v07 as _engine
        ph=self.linked_graveyard.get(cand.uid)
        if cand.name==GRIST or ph is None: return super()._return_creature_from_graveyard(cand,source,tapped=tapped)
        self.zones._require_in_zone(ph,'graveyard'); del self.linked_graveyard[cand.uid]
        result=_engine.Game._return_creature_from_graveyard(self,cand,source,tapped=tapped)
        if result is None: self.linked_graveyard[cand.uid]=ph; return None
        self.zones.move(ph,'battlefield',controller=0); self.zones.cards[ph].tapped=tapped
        self.linked_battlefield[result.uid]=ph; self.trace.append(('linked_reanimated',cand.uid,result.uid,ph,source)); self.trace.append(('r55_safe_order',cand.name))
        self.assert_bridge_integrity(); return result

def check_invariants_s18(g):
    check_invariants_s17(g)
    for seat,pol in g.opponent_policy.items():
        if any(v<0 for k,v in pol.items() if k.endswith('_budget')): raise AssertionError('S18: a budget went negative')
    if g.life[0]<=0 and not g.game_lost and not g.pending: raise AssertionError('S18: controller at 0 life without loss adjudication')

def run_game(g,max_turns=60):
    """Whole game under the S17 driver: ends when the controller has lost, has won, or max_turns passed.
    Returns (outcome, turns, ledger). outcome in {'lost','won','timeout'}."""
    from pab_combat_s17 import run_turns_full
    ledger=[]
    while g.clock.turn<max_turns and not g.game_lost and not g.game_won:
        ledger+=run_turns_full(g,4); check_invariants_s18(g)
    return ('lost' if g.game_lost else 'won' if g.game_won else 'timeout'),g.clock.turn,ledger
