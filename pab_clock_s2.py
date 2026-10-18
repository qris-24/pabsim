"""Phase-clock stage S2 (approved 2026-10-18): step boundaries drive behaviour.

Layered above pab_turn_clock.ClockMixin (S1). On every clock advance:
  * the mana pool empties (CR 106.4: "at the end of each step and phase");
  * entering ANY seat's upkeep runs begin_upkeep()  — Pest Rescuer and Beledros
    say "each upkeep" (R50 closed for these two sources);
  * entering the CONTROLLER's end step runs roaster_end_step() ("your end step")
    and records Moseo's intervening-if admission (life gained this turn > 0);
  * entering the controller's cleanup runs reset_turn() (CR 514.2: "until end of
    turn" / "this turn" effects end).

Engagement rule: until the first advance the clock is unengaged and the step
methods may be called directly (fixture shortcut, pre-S2 behaviour). After the
first advance, begin_upkeep / roaster_end_step / moseo_end_step may only be
called at their own step for the right seat; otherwise ClockError.

Not in S2 (S3/S4): priority loop and SBA between resolutions; untap, draw and
land-play reset as turn-based actions; APNAP ordering choices; opponents'
permanents.
"""
from __future__ import annotations
from pab_turn_clock import ClockMixin, ClockError

class StepRoutingMixin(ClockMixin):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.clock_engaged=False
        self._moseo_admitted=False

    # ---- boundary driver -------------------------------------------------
    def advance_step(self):
        self.clock_engaged=True
        self._empty_mana_pool('step_end')
        turn,ap,phase,step=super().advance_step()
        if step=='upkeep':
            self._moseo_admitted=False
            super().begin_upkeep()                     # each upkeep, every seat
        elif step=='end' and ap==0:
            super().roaster_end_step()                 # your end step
            self._moseo_admitted=self.has("Moseo, Vein's New Dean") and self.life_gained_turn>0
            self.trace.append(('moseo_end_step_admission',self._moseo_admitted,self.life_gained_turn))
        elif step=='cleanup' and ap==0:
            super().reset_turn()
            self.trace.append(('cleanup_until_end_of_turn_expired',turn))
        return turn,ap,phase,step

    def advance_to(self,step,*,active_player=None,max_steps=10_000):
        for _ in range(max_steps):
            t,ap,ph,st=self.advance_step()
            if st==step and (active_player is None or ap==active_player): return t,ap,ph,st
        raise ClockError('advance_to exceeded max_steps')

    def _empty_mana_pool(self,reason):
        n=len(self.mana_pool)
        if n:
            del self.mana_pool[:]                      # in place: the bridge shares this list with DeckZones
            self.trace.append(('mana_emptied',n,reason))

    # ---- guarded direct calls --------------------------------------------
    def _require(self,step,seat=0):
        if not self.clock_engaged: return
        c=self.clock
        if c.step!=step or (seat is not None and c.active_player!=seat):
            raise ClockError(f'{step} action outside its step: clock at turn {c.turn} seat {c.active_player} {c.step}')

    def begin_upkeep(self):
        self._require('upkeep',seat=None)
        if self.clock_engaged: raise ClockError('upkeep triggers are driven by the clock once engaged')
        return super().begin_upkeep()

    def roaster_end_step(self):
        self._require('end')
        if self.clock_engaged: raise ClockError('end-step triggers are driven by the clock once engaged')
        return super().roaster_end_step()

    def moseo_end_step(self,target_uid=None):
        self._require('end')
        if self.clock_engaged and not self._moseo_admitted:
            self.trace.append(('moseo_not_admitted_this_end_step',))
            return False
        return super().moseo_end_step(target_uid)
