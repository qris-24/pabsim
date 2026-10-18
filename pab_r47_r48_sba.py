"""R47 + R48 + R49 layer (approved 2026-10-18), stacked on the R01 kernel.

R47 — Ribtruss Roaster: the end-step trigger must read the +1/+1 counter count
when it RESOLVES (CR 608.2h), not when it is created. The frozen
`roaster_end_step` captured `p.counters` in a lambda default.

R49 — If Roaster leaves the battlefield before the trigger resolves, the
effect uses its last known counter count (CR 608.2h second sentence), not zero.
The LKI snapshot is taken when the trigger is created; a counter changed while
Roaster is still on the battlefield is read live at resolution.

R48 — Zero toughness is a state-based action (CR 704.5f), not destruction, so
indestructible does not save the creature. The frozen `yawgmoth_sacrifice`
called `destroy()` for the toughness check; this override uses `_leave(...,
sacrificed=False)` directly, the same path `equip_skullclamp` already uses, and
traces the SBA explicitly.

Frozen modules are not edited. The rest of `yawgmoth_sacrifice` is transcribed
from pab_focus_engine_v07 unchanged.
"""
from __future__ import annotations
from pab_focus_engine_v07 import Trigger, IllegalAction, PEST
import pab_r01_pest_rescuer as r01

class SbaFixesMixin:
    def roaster_end_step(self):
        for p in tuple(self.permanents.values()):
            if p.name == 'Ribtruss Roaster' and p.controller == 0:
                def make(uid=p.uid,lki=p.counters):
                    live=self.permanents.get(uid)
                    if live is not None:                          # CR 608.2h: current information while on the battlefield
                        n=live.counters; self.trace.append(('roaster_counters_at_resolution',uid,n))
                    else:                                         # R49: source left -> last known information
                        n=lki; self.trace.append(('roaster_counters_lki',uid,n))
                    self.make_tokens(PEST,n)
                self._enqueue([Trigger('Ribtruss Roaster end-step',make)])

    def yawgmoth_sacrifice(self, source_uid, sacrifice_uid, *, target_uid=None):
        source=self.permanents.get(source_uid)
        cost=self.permanents.get(sacrifice_uid)
        if not source or source.name!='Yawgmoth, Thran Physician' or source.controller!=0:
            raise IllegalAction('Missing controlled Yawgmoth')
        if not cost or not cost.creature or cost.controller!=0 or source_uid==sacrifice_uid:
            raise IllegalAction('Yawgmoth requires another controlled creature')
        if target_uid is not None:
            target=self.permanents.get(target_uid)
            if not target or not target.creature or target.controller!=0:
                raise IllegalAction('Target unsupported or illegal in restricted fixture')
        if self.life[0]<1: raise IllegalAction('Cannot pay 1 life')
        self.trace.append(('target_locked',target_uid,'Yawgmoth'))
        self.pay_life(1,'Yawgmoth activation cost')
        self.sacrifice(sacrifice_uid)
        def resolve_yawgmoth():
            if target_uid is not None and target_uid not in self.permanents:
                self.trace.append(('ability_fizzles_all_targets_illegal','Yawgmoth'))
                return
            if target_uid is not None:
                target=self.permanents[target_uid]
                target.minus_counters+=1
                self.trace.append(('minus_one_counter',target_uid))
            self._fixture_draw(1,'Yawgmoth')
            if target_uid is not None:
                target=self.permanents.get(target_uid)
                if target and target.toughness + target.counters - target.minus_counters<=0:
                    # R48: SBA death, not destruction; indestructible is irrelevant.
                    self.trace.append(('sba_zero_toughness',target_uid,'Yawgmoth'))
                    self._leave(target_uid,sacrificed=False)
        self.pending.append(Trigger('Yawgmoth activation',resolve_yawgmoth))

class Game(SbaFixesMixin, r01.Game):
    """R47+R48 event-kernel candidate."""

class PhysicalZoneGame(SbaFixesMixin, r01.PhysicalZoneGame):
    """R47+R48 physical-bridge candidate."""
