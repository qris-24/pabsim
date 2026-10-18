"""Phase-clock stage S1 (approved 2026-10-18): a turn/step clock the kernel
carries. NO behaviour change: no existing method consults it, nothing is
triggered, emptied or expired by advancing it. S2 will route step-boundary
triggers, mana emptying and until-end-of-turn expiry through it.

CR 500.1 turn structure (MagicCompRules 20260619, EVIDENCE/CR_20260619_EVIDENCE.json):
beginning phase (untap, upkeep, draw), precombat main, combat (beginning of
combat, declare attackers, declare blockers, combat damage, end of combat),
postcombat main, ending phase (end, cleanup).
"""
from __future__ import annotations
from dataclasses import dataclass, field

PHASES=(
  ('beginning',('untap','upkeep','draw')),
  ('precombat_main',('precombat_main',)),
  ('combat',('beginning_of_combat','declare_attackers','declare_blockers','combat_damage','end_of_combat')),
  ('postcombat_main',('postcombat_main',)),
  ('ending',('end','cleanup')),
)
STEPS=tuple((ph,st) for ph,steps in PHASES for st in steps)   # 12 (phase, step) pairs in order
SEATS=4

class ClockError(ValueError):
    """Illegal clock operation."""

@dataclass
class TurnClock:
    seats:int=SEATS
    turn:int=1                     # 1-based game turn counter
    active_player:int=0            # seat index; seat 0 is the PAB controller
    index:int=0                    # position in STEPS
    boundaries:list=field(default_factory=list)   # ('step_begin', turn, active_player, phase, step)

    def __post_init__(self):
        if not isinstance(self.seats,int) or self.seats<1: raise ClockError('seats must be a positive integer')
        self.boundaries.append(('step_begin',self.turn,self.active_player)+STEPS[self.index])

    @property
    def phase(self): return STEPS[self.index][0]
    @property
    def step(self): return STEPS[self.index][1]
    @property
    def is_controller_turn(self): return self.active_player==0

    def advance(self):
        """Move to the next step; after cleanup, the next seat's untap. Returns (turn, active_player, phase, step)."""
        self.index+=1
        if self.index==len(STEPS):
            self.index=0; self.turn+=1; self.active_player=(self.active_player+1)%self.seats
        entry=('step_begin',self.turn,self.active_player)+STEPS[self.index]
        self.boundaries.append(entry)
        return entry[1:]

    def advance_to(self,step,*,active_player=None,max_steps=10_000):
        """Advance until the named step begins (optionally for a given seat). Returns the boundary."""
        names={st for _,st in STEPS}
        if step not in names: raise ClockError(f'unknown step {step!r}')
        for _ in range(max_steps):
            self.advance()
            if self.step==step and (active_player is None or self.active_player==active_player):
                return self.boundaries[-1]
        raise ClockError('advance_to exceeded max_steps')

    def state(self): return (self.turn,self.active_player,self.phase,self.step)


class ClockMixin:
    """Gives a Game a clock and an advance_step() that only records boundaries in the
    game trace. Deliberately inert: existing step methods (begin_upkeep,
    roaster_end_step, moseo_end_step, reset_turn) are unchanged and not invoked."""
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.clock=TurnClock()
    def advance_step(self):
        turn,ap,phase,step=self.clock.advance()
        self.trace.append(('step_begin',turn,ap,phase,step))
        return turn,ap,phase,step
    def advance_to(self,step,*,active_player=None):
        b=self.clock.advance_to(step,active_player=active_player)
        self.trace.append(b)
        return b[1:]
