# R01 patch notes — Pest Rescuer "Pest creature token" condition (2026-10-18)

Scope authorized: R01, as a versioned candidate on top of R02. No frozen file edited. Phase 9 still paused.

## Discrepancy (CP09, reproduced here against unmodified v0.7 code)
Supplied text: "if you don't control a Pest creature token". Phase 5's `controls_pest()` matched any
Pest-subtype creature, so a nontoken Teacher's Pest suppressed the trigger. Expected/observed with
Teacher's Pest only: 1/0. The supplied text is an offline snapshot and still lacks authenticated Oracle confirmation.

## Change
| File | Change |
|---|---|
| pab_r01_pest_rescuer.py | NEW. `PestTokenPredicateMixin.controls_pest()` requires `p.token is not None`. `Game` = mixin + v0.7 Game; `PhysicalZoneGame` = mixin + v0.8 bridge. Admission and resolution both use it (`begin_upkeep` calls the predicate at both points). Lifegain +1 replacement untouched. `EXPECTED_LEGACY_FAILURES = {112, 113}`. |
| r01_tests/test_r01_pest_rescuer.py | NEW. 11 controls × 2 candidates + 2 pins of the frozen engine's old behaviour = 24. |
| r01_tests/test_v05_fixture_cards_r01.py | NEW. Copy of the frozen v0.5 file; only 112/113 expectations changed (0 → 1); 114 unchanged. 38/38 against the candidate. |
| run_validation.py | R01 section: runs `r01_tests/` (62) and replays the 149 frozen contracts against the candidate, requiring failures == exactly {112, 113} and 147 passes. Results recorded under `r01_*`. |
| release_gate_tests/ | +1 tamper case (candidate edit) and end-to-end asserts the exact R01 failure set. |

## Result
`python run_validation.py`: exit 0. 311/311 fixtures; 149/149 v0.7 replay; 52/52 bridge replay; 17/17 gate; 62/62 R01; legacy replay vs R01 candidate 147/149 with failures exactly {112, 113}.

## Nonclaims
Frozen tests 112/113 still assert the old result and still pass against the frozen engine — by design. 0 cards certified. The candidate is not adopted into the frozen kernel; promoting it requires its own approval.

## Promotion (authorized 2026-10-18)
- `pab_kernel.py` is the canonical entry point: `Game` / `PhysicalZoneGame` are the R01 classes. `KERNEL_VERSION='v0.8+R02+R01'`.
- `tests/test_r01_pest_rescuer.py` (13 contracts; 11 run on both kernel and bridge via subTest) and `tests/test_v05_r01_corrections.py` (2) are counted reference fixtures. **Reference test count: 311 → 326.**
- Frozen `test_112` / `test_113` are untouched and still pass against the frozen v0.5 engine; the registry lists them under `superseded_frozen_contracts`.
- The runner replays every frozen family against the promoted kernel: 149 v0.5 contracts → 147 pass, failures exactly {112, 113}; 52 v0.7 bridge → 52; 54 v0.8 bridge → 54; corrected v0.5 copy → 38/38.
- Manifest build id `pab_reliability_v0_8_r02_r01`, 80 inputs pinned. Frozen files, deck, Oracle data: untouched.
- Still not independently authenticated: the Pest Rescuer text. If official Oracle reads "Pest creature" without "token", R01 reverses.
