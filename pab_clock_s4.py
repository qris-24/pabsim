"""Phase-clock stage S4 (approved 2026-10-18): turn-based actions.

Layered above pab_clock_s3.PriorityMixin.
  * Controller's untap step (CR 502.3): all the controller's permanents untap;
    on the physical bridge DeckZones.new_turn() untaps linked cards and resets
    the land-play count, and event-side tapped flags are re-synced.
  * Draw step (CR 504.1): the active player draws. Controller: one real draw
    (physical on the bridge, counted on the event kernel). Opponents have no
    library here: traced as unmodeled, nothing moves. No first-turn skip: CR
    103.8a applies to two-player games only.
  * Land play window (CR 305.1/305.2): once the clock is engaged,
    play_physical_land() derives main_phase/stack_empty from the clock and the
    pending queue, and refuses plays on opponents' turns.

Not modeled: opponents' draws/libraries/untaps, cleanup discard to hand size
(514.1), 'doesn't untap' effects, extra land plays.
"""
from __future__ import annotations
from pab_clock_s3 import PriorityMixin
from pab_turn_clock import ClockError

MAIN_STEPS={'precombat_main','postcombat_main'}

class TurnBasedActionsMixin(PriorityMixin):
    def advance_step(self):
        turn,ap,phase,step=super().advance_step()
        if step=='untap' and ap==0: self._untap_step(turn)
        elif step=='draw':
            if ap==0: self._fixture_draw(1,'draw step')
            else: self.trace.append(('opponent_draw_unmodeled',ap))
        return turn,ap,phase,step

    def _untap_step(self,turn):
        n=sum(1 for p in self.permanents.values() if p.controller==0 and p.tapped)
        zones=getattr(self,'zones',None)
        if zones is not None:
            zones.new_turn()                                        # untaps linked physical cards, resets land plays
            for event_uid,physical_uid in getattr(self,'linked_battlefield',{}).items():
                p=self.permanents.get(event_uid)
                if p is not None: p.tapped=zones.cards[physical_uid].tapped
        for p in self.permanents.values():
            if p.controller==0: p.tapped=False
        self.trace.append(('untap_step',turn,n))

    def play_physical_land(self,physical_uid,*,main_phase=None,stack_empty=None):
        if self.clock_engaged:
            c=self.clock
            if not c.is_controller_turn: raise ClockError('land play only on your own turn (305.1)')
            if main_phase is None: main_phase=c.step in MAIN_STEPS
            if stack_empty is None: stack_empty=not self.pending
        else:
            if main_phase is None: main_phase=True
            if stack_empty is None: stack_empty=True
        return super().play_physical_land(physical_uid,main_phase=main_phase,stack_empty=stack_empty)
