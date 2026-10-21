"""R01 candidate: Pest Rescuer's upkeep condition checks for a Pest creature
*token*, not any Pest-subtype creature (CP09 / CP12 design).

Supplied text: "At the beginning of your upkeep, if you don't control a Pest
creature token, create a 1/1 black and green Pest creature token..."
(offline snapshot; NOT independently authenticated against official Oracle).
Oracle (Scryfall, CP31): "At the beginning of each upkeep, ..."; the kernel fires it on every
seat's upkeep through the S2 clock (C95). See EVIDENCE/CP31_PEST_RESCUER_ORACLE.md.

Phase 5 widened `controls_pest()` to every Pest-subtype creature, so a nontoken
Teacher's Pest wrongly suppressed the trigger. That predicate is frozen in
`pab_focus_engine.py` / `pab_focus_engine_v07.py` and is NOT edited here; this
module provides versioned candidates via a mixin. Both admission (trigger
time) and resolution (intervening-if) re-use the same corrected predicate
because `begin_upkeep()` calls `self.controls_pest()` at both points.

Scope: only the upkeep condition. The lifegain replacement ("+1") is untouched.
"""
from __future__ import annotations
from pab_focus_engine_v07 import Game as V07Game
from pab_zone_bridge_v08 import PhysicalZoneGame as V08Bridge

class PestTokenPredicateMixin:
    def controls_pest(self):
        """True only if the controller (seat 0) controls a Pest creature TOKEN."""
        return any(p.controller==0 and p.creature and p.token is not None
                   and 'Pest' in p.subtypes
                   for p in self.permanents.values())

class Game(PestTokenPredicateMixin, V07Game):
    """R01 event-kernel candidate."""

class PhysicalZoneGame(PestTokenPredicateMixin, V08Bridge):
    """R01 physical-bridge candidate (v0.8 bridge + corrected predicate)."""

# Original v0.5 contracts that assert the pre-R01 (wrong) result. They are kept
# frozen for history and are EXPECTED to fail against the R01 candidate.
EXPECTED_LEGACY_FAILURES={
    'test_112_teacher_pest_blocks_rescuer_at_upkeep_start',
    'test_113_teacher_pest_entered_before_rescuer_trigger_resolves',
}
