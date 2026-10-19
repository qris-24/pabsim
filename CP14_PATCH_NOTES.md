# CP14 — A-S20-06: automatic graveyard LKI for a milled or discarded Grist (2026-10-19)

One step, committed and tagged `rp-CP14`. No frozen file edited (`pab_zones.py`, `pab_zone_bridge.py`
untouched). Gate bookkeeping moved with the step as at CP02–CP13: `run_validation.py`
`REFERENCE_TEST_COUNT` (805 → 810) and the per-file count assertion for `tests/test_auditfix_cp14.py`,
`release_gate_tests/test_r02_release_gate.py` expected `(tests_run, tests_passed)` = (810, 810), the
coverage registry (`py -3.14 build_registry.py`, output redirected), the manifest (`py -3.14
build_manifest.py`), the ledger entry for A-S20-06 (`cp14_status: CLOSED`, `status: REPAIRED`,
`fix_authorized: true`, `latest_evidence`) and `CLAUDE.md`'s test count 805 → 810.

## What
- `pab_grist_s16.py` `GristMixin.__init__`: after `super().__init__(...)`, `_wrap_zone_move_for_grist()`
  replaces the instance's `zones.move` with a wrapper. The frozen-file constraint is the reason for the
  wrapper: `pab_zones.py` (`DeckZones.move`, and `mill` / `discard` which call it) is frozen and cannot be
  taught about Grist, and the eight `zones.mill` / `zones.discard` call sites across S9, S13, S14, S15, S16,
  S20 and the frozen bridge cannot all be patched. The wrapper records the card's source zone, calls the
  original `move`, and then, only for a non-token card named Grist:
  - source `library` or `hand` and destination `graveyard` → `grist_graveyard_lki()` (idempotent; the
    existing `grist_graveyard_lki` trace is kept as the evidence that the LKI was made);
  - source `graveyard` → `_drop_grist_graveyard_lki(uid)`: removes the event LKI whose `linked_graveyard`
    value is this physical uid, and the link, when both are still present, then
    `assert_bridge_integrity()`; trace `('grist_lki_dropped', lki_uid, ph)`. A half-removed pair is left
    alone, because `pab_cast_s15._return_permanent_card` removes both before the move and the frozen
    Phyrexian Reclamation path (`pab_zone_bridge.py`) removes the LKI before and the link after the move.
  Any other move, and any non-Grist card or token, is unchanged. The battlefield → graveyard path
  (`_grist_to_graveyard`, Abrupt Decay / zero-loyalty SBA / `_destroy_any`) still makes its own LKI; the
  wrapper does not fire for a battlefield source, so no duplicate is made.
- The wrapper closes over the game, not the zones object, and resolves `self.zones` and
  `type(self.zones).move` at call time: `pab_stack_cp06.PhysicalStackCP06Mixin.__init__` runs after
  `GristMixin.__init__` and replaces `self.zones` with a `StackEnabledZones` built from the old instance's
  `__dict__`, which carries the wrapper across; a wrapper bound to the old `DeckZones` would have bypassed
  the stack zone.
- Module docstring and the `grist_graveyard_lki` docstring now say the LKI is automatic and that the
  manual call is idempotent.
- `tests/test_grist_s16.py` unchanged; its line-89 manual call now returns the automatically made LKI.

## Why
Grist's static makes her a creature card off the battlefield. A Grist milled (Grist +1, Grisly Salvage,
Witherbloom Command, Underground Mortuary surveil, Shigeki) or discarded entered the physical graveyard
with no event-kernel LKI unless a caller remembered `grist_graveyard_lki()`, so the frozen `_grave_target()`
could not see her for Unearth / Rise of the Witch-king / Takenuma, and a physical Grist returned to hand or
library from the graveyard could leave a stale LKI behind.

## Verification
`tests/test_auditfix_cp14.py` (5 tests): Grist on top of the library, `zones.mill(1)`: exactly one LKI with
creature=True, mana value 3, linked to the physical uid, made by the wrapper with no helper call, visible
to `_grave_target()`; Unearth targeting the LKI uid resolves and Grist is a loyalty-3 planeswalker on the
battlefield with the physical card (check_invariants_s16). Grist in hand, `zones.discard(uid)`: same LKI
assertions and Unearth. Battlefield → graveyard via `destroy`: exactly one Grist LKI (the battlefield
one), no `grist_graveyard_lki` trace, invariant holds. Milled Grist then `zones.move(uid,'library')`: LKI
and link gone, `_grave_target()` returns None, `grist_lki_dropped` trace present, `assert_bridge_integrity()`
passes; moving her back to the graveyard makes a fresh single LKI. Manual `grist_graveyard_lki()` after an
automatic creation returns the same object twice, with one trace and one LKI. Kernel suite `Ran 810
tests` / `OK` (805 + 5); 18/18 release checks; full output in `EVIDENCE/CP14_gate.txt`. All pinned-seed
driver fixtures passed unchanged; none of the 311 frozen v0.5–v0.8 fixtures changed; no
`EVIDENCE/CP14_SUPERSEDED/` entry needed.
