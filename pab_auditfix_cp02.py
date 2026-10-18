"""Approved, versioned CP02 repair for audit A-S20-01 and A-S20-02 only.

Correctness scope:
 * Blocked status survives removal of the last blocker (no trample engine yet).
 * Whole-game scheduling ends immediately when a terminal loss/win is adjudicated.

No other gameplay, card data, frozen source, or accepted deck is modified.
"""
from __future__ import annotations
from pab_shigeki_s20 import ShigekiMixin
from pab_focus_engine import SAVRA
from pab_lands_s14 import LAND_MANA_DRIVER
from pab_lands_s9 import play_land_policy, tap_lands_policy
from pab_commander_s10 import commander_need, cast_commander_when_able
from pab_cast_s15 import cast_when_able
from pab_combat_s17 import attack_policy
from pab_policy_s18 import check_invariants_s18

class AuditFixCP02Mixin(ShigekiMixin):
    """Override only combat blocked-status handling; retain all existing S20 layers."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._cp02_blocked_attackers=set()

    def advance_step(self):
        result=super().advance_step()
        _, _, _, step=result
        if step=='declare_blockers':
            # Super runs both opponent and controller blocking policies first.
            self._cp02_blocked_attackers={uid for uid,blockers in self.blocks.items() if blockers}
        elif step=='end_of_combat':
            self._cp02_blocked_attackers.clear()
        return result

    def _combat_damage(self):
        events=[]
        for attacker,seat in list(self.attackers.items()):
            p=self.permanents.get(attacker)
            if p is None: continue  # removed attacker deals no combat damage
            originally_blocked=(attacker in self._cp02_blocked_attackers
                                or bool(self.blocks.get(attacker)))
            surviving_blockers=[uid for uid in self.blocks.get(attacker,()) if uid in self.permanents]
            dmg=self._power(p)
            if not originally_blocked:
                # The controller's seat 0 can receive attacking opponent damage;
                # other seats must still participate in the game.
                if seat!=0 and seat not in self.seats_in_game(): continue
                self.life[seat]-=dmg
                events.append(('player',seat,attacker,dmg))
                if p.name==SAVRA and attacker in self.linked_battlefield and seat!=0:
                    self.commander_damage[seat]+=dmg
            elif surviving_blockers:
                first=surviving_blockers[0]
                self.damage_marked[first]=self.damage_marked.get(first,0)+dmg
                if self._deathtouch(p) and dmg>0:
                    self.damage_marked[('deathtouch',first)]=True
                events.append(('creature',first,attacker,dmg))
                for b in surviving_blockers:
                    blocker=self.permanents[b]
                    bd=self._power(blocker)
                    self.damage_marked[attacker]=self.damage_marked.get(attacker,0)+bd
                    events.append(('creature',attacker,b,bd))
                    if self._deathtouch(blocker) and bd>0:
                        self.damage_marked[('deathtouch',attacker)]=True
            # Previously blocked and no blockers remaining: no player damage.
            # Trample and other unimplemented damage mechanics remain OUT OF SCOPE.
        self.trace.append(('combat_damage',tuple(events)))
        self.combat_log.append((self.clock.turn,tuple(events)))
        self.state_based_actions()


def run_turns_full_terminal(g,turns):
    """S17 controller-turn policy, but stop on terminal adjudication mid-batch.

    Partial final turns produce no fabricated completed-turn ledger rows.
    Return the existing 6-field ledger shape for completed controller turns.
    """
    ledger=[]
    start=g.clock.turn
    row=None
    while g.clock.turn<start+turns and not (g.game_lost or g.game_won):
        t,ap,ph,st=g.advance_step()
        # A combat step can adjudicate game end inside advance_step().
        # Do not resolve another spell, trigger, player choice, or clock step
        # once a terminal outcome is established.
        if g.game_lost or g.game_won: break
        g.resolve()
        check_invariants_s18(g)
        if g.game_lost or g.game_won: break
        if ap!=0: continue
        if st=='precombat_main':
            u,kw=play_land_policy(g,LAND_MANA_DRIVER)
            played=None
            if u is not None:
                played=g.play_physical_land(u,**kw).name
                g.resolve(); check_invariants_s18(g)
            if g.game_lost or g.game_won: break
            mana=tap_lands_policy(g,extra=commander_need(g),land_mana=LAND_MANA_DRIVER)
            cast=[SAVRA] if cast_commander_when_able(g) else []
            if g.game_lost or g.game_won: break
            cast+=cast_when_able(g)
            check_invariants_s18(g)
            if g.game_lost or g.game_won: break
            row=[t,played,tuple(mana),tuple(cast),(),()]
        elif st=='declare_attackers' and row is not None:
            assignments=attack_policy(g)
            if assignments:
                g.declare_attackers(assignments)
                if g.game_lost or g.game_won: break
                g.resolve(); check_invariants_s18(g)
            if g.game_lost or g.game_won: break
            row[4]=tuple(assignments)
        elif st=='combat_damage' and row is not None:
            row[5]=g.combat_log[-1][1] if g.combat_log and g.combat_log[-1][0]==t else ()
        elif st=='cleanup' and row is not None:
            ledger.append(tuple(row)); row=None
    return ledger


def run_game_terminal(g,max_turns=60):
    """Drop-in replacement for pab_policy_s18.run_game, no 4-turn overshoot."""
    ledger=[]
    while g.clock.turn<max_turns and not (g.game_lost or g.game_won):
        ledger.extend(run_turns_full_terminal(g,min(4,max_turns-g.clock.turn)))
        check_invariants_s18(g)
    return ('lost' if g.game_lost else 'won' if g.game_won else 'timeout'),g.clock.turn,ledger
