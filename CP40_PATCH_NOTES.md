# CP40 — A2 Tests 1: C87 tests the kernel (T3) (2026-10-21)

Test-only stage, applied by night\CP40_apply.py (deterministic; built and gated in a sandbox clone of rp-CP39). Approved by the user (2026-10-21): the C87 class changes (before-copy EVIDENCE/CP40_SUPERSEDED/C87_pre_cp40.py). No kernel or frozen file changed.

## Summary
- T3: C87's two tests (same names) cast the kernel's Grisly Salvage on PhysicalZoneGame instead of a stand-in composed in the test file: top five, the chosen card (a land, picked over the first eligible creature) to hand, the rest and the spell to the graveyard, the rest of the library untouched, no shuffle; with no creature or land among them, all five go to the graveyard.
- The new tests catch three kernel mutations of Grisly Salvage that the stand-in could not (chosen card to graveyard, top four instead of five, choice ignored so the first eligible card is taken; the test picks the land Swamp behind the creature Deathgreeter).
- C87: STATUS EXECUTED_WITH_SUBSTITUTION -> EXECUTED (approved; current table row and counts 30 EXECUTED / 20 EXECUTED_WITH_SUBSTITUTION; the historical R02-era table is left as written); oracle_referenced False -> True with subject Grisly Salvage (54 of 59 contracts).
- CLAUDE.md: test hygiene now T1, T2, T4-T6; C87 removed from the CP29 follow-up list (it is no longer False).
- Tests: 918 (no test added); release gate 21/21.
- Follow-ups: none.
