"""Phase-clock stage S3 (approved 2026-10-18): priority-loop semantics.

Layered above pab_clock_s2.StepRoutingMixin.
  * State-based actions are checked whenever a player would receive priority:
    before the first resolution in resolve(), after EVERY resolution, and once
    more before resolve() returns (CR 704.3, 117.5). Modeled SBA: creatures the
    controller controls with toughness <= 0 die (704.5f) and the 0-life loss the
    frozen loop already performed. Simultaneous deaths are one event: each
    leaves-the-battlefield trigger looks back at the board as it was immediately
    before the event (603.10), so creatures dying together see each other.
  * The R48 inline check inside Yawgmoth's resolution is retired; the general
    check performs that death. Skullclamp's equip keeps its immediate check
    (equip does not use the stack here and priority follows at once; result is
    identical and the C45 trace contract is preserved).
  * Trigger ordering: set_trigger_order(policy) lets the controller order a
    batch of simultaneously triggered abilities (603.3b; one controller, so no
    APNAP interleaving yet). Default keeps the kernel's existing order.

Not modeled: opponents' permanents (so no SBA on them), legend rule, +1/+1 and
-1/-1 counter annihilation, planeswalker loyalty, tokens-in-graveyard cessation
timing beyond the existing model.
"""
from __future__ import annotations
from pab_clock_s2 import StepRoutingMixin

class _LookBack(dict):
    """During one simultaneous SBA event, values() reports the pre-event board so
    _leave()'s trigger snapshot looks back (603.10); deletion and lookup are live."""
    def __init__(self,live,snapshot):
        super().__init__(live); self._snapshot=tuple(snapshot)
    def values(self): return self._snapshot

class PriorityMixin(StepRoutingMixin):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.sba_checks=0
        self.trigger_order_policy=None

    # ---- state-based actions --------------------------------------------
    def _dying_by_toughness(self):
        return [p for p in self.permanents.values() if p.controller==0 and p.creature
                and p.toughness+p.counters-p.minus_counters<=0]
    def state_based_actions(self):
        """Perform all applicable SBAs as a single event; repeat until none apply (704.3)."""
        rounds=0
        while True:
            self.sba_checks+=1
            dying=self._dying_by_toughness()
            if not dying: return rounds
            rounds+=1
            uids=[p.uid for p in dying]
            self.trace.append(('sba_event','zero_toughness',tuple(uids)))
            live=self.permanents
            self.permanents=_LookBack(live,live.values())
            try:
                for uid in uids:
                    self.trace.append(('sba_zero_toughness',uid,'state-based'))
                    self._leave(uid,sacrificed=False)
            finally:
                self.permanents=dict(self.permanents)          # drop the look-back view; keep live deletions

    def _inline_zero_toughness_check(self,target_uid,source):
        return                                                 # S3: general check owns this

    def resolve(self,max_resolutions=1000):
        n=0
        if self.life[0]<=0:
            self.game_lost=True; self.pending.clear(); return 0
        self.state_based_actions()                              # a player would receive priority
        while self.pending and not self.game_lost:
            if n>=max_resolutions: raise RuntimeError('Unbounded trigger chain')
            t=self.pending.popleft(); self.trace.append(('resolve',t.label))
            t.action(); n+=1
            if self.life[0]<=0:
                self.game_lost=True; self.trace.append(('lose_game','life_zero_or_less')); self.pending.clear(); break
            self.state_based_actions()                          # between resolutions, never inside one
        return n

    # ---- trigger ordering ---------------------------------------------------
    def set_trigger_order(self,policy):
        """policy(batch: list[Trigger]) -> list[Trigger]; None restores the default order."""
        self.trigger_order_policy=policy
    def _enqueue(self,triggers):
        batch=list(triggers)
        if batch and self.trigger_order_policy is not None:
            ordered=list(self.trigger_order_policy(batch))
            if sorted(id(t) for t in ordered)!=sorted(id(t) for t in batch):
                raise ValueError('trigger order policy must permute the batch')
            self.trace.append(('trigger_order_chosen',tuple(t.label for t in ordered)))
            batch=ordered
        return super()._enqueue(batch)
