# PABTRV3 Reliability Lab — Phase 8 (`pab_reliability_v0_8`)

This is an isolated, **incomplete deterministic Savra reference kernel**, **not** the inherited playable simulator and **not** a deck optimizer. Frozen 100-card main/commander and a separate optional Pest Summoning Lesson. Exact baseline SHA-256: `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`.

Run `python run_validation.py` with Python 3.10+ and standard library only.

Expected: **311/311 distinct tests**, zero failures/errors/skips; historical compatibility replays **149/149** old event contracts on the v0.7 candidate and **52/52** Phase 7 bridge contracts on the v0.8 candidate. Neither replaces the **original** 25 compiler signature tests (saved historical 10 pass / 15 fail). All outcomes are local fixture results.

## Phase 8 changes

- `pab_zone_bridge_v08.py`: opt-in subclass of the unmodified Phase 7 bridge, with one shared mana-pool list, cost re-sharing and provisional real card land play/mana for only Forest, Swamp, Command Tower. It physically mirrors newly created event tokens into token UIDs and removes them from persistent card storage on battlefield leave.
- `tests/test_v08_mana_tokens.py`: 54 new positive and negative deterministic tests.
- `run_validation.py`: new fail-closed suite gate, frozen source checks, checksum review, replays, result report.
- `build_registry.py`: retains all previous 54/65 PARTIAL / 11/65 UNSUPPORTED counts and null optimizer values; only metadata updated.
- `frozen_phase7/`: reference copies of Phase 7 bridge source, versioned candidate, original Phase 7 runner and registry, and Phase 7 tests. `PHASE7_FILE_MANIFEST.json` remains source of previous-file checksums.

No original source, frozen deck, card data, historical tests or accepted changes were modified. No live Oracle verification. Full original compiler `engine.py`, `oracle.py`, `golgari_commander.json` still missing, as are verified land texts and full rules coverage.

## Mandatory NEXT SESSION starting step

**AUDIT ALL EIGHT PHASES BEFORE CONTINUING ENGINEERING.** Read `PABTRV3_PHASE8_NEW_SESSION_HANDOFF.md` for the exact deliverables. Unverifiable early-phase claims must be marked unverified; no performance inference or new replacement sweep.

## R02 patch (release-runner integrity; no rules or deck changes)

Problem (CP07): importing `build_registry.py` rewrote `PABTRV3_CARD_COVERAGE.json`
with filesystem-dependent key order, so `python run_validation.py` tripped its own
Phase 8 manifest check before running any test.

Fix:
- `build_registry.py` is build-only: importing it has no side effects; `build()` is pure;
  `canonical_bytes()` serialises with sorted keys; `sorted(iterdir())`. Writes only via `python build_registry.py`.
- `run_validation.py` = `preflight()` (read-only, every integrity check before any write)
  → `run_suites()` → `main()`. The runner never writes the registry; it regenerates it in
  memory and fails closed if the shipped file is not byte-identical.
- `PHASE8_R02_FILE_MANIFEST.json` (from `build_manifest.py`, build-only) pins every input.
  Runner outputs (`VALIDATION_RESULTS.json`, `validation_stdout.txt`) are recorded, never verified.
  The legacy `PHASE8_FILE_MANIFEST.json` is still enforced for every file R02 did not re-version.
- `release_gate_tests/`: separate suite (not part of the 311): determinism, double clean-clone
  build identity, read-only preflight, tamper cases requiring the specific failure message,
  and a two-run end-to-end check of the shipped command.

Release procedure (only when an input legitimately changes): `python build_registry.py`,
review the diff, `python build_manifest.py`, review, then `python run_validation.py`.

## R01 patch (Pest Rescuer "Pest creature token" condition; PROMOTED)

`pab_r01_pest_rescuer.py` provides `Game` and `PhysicalZoneGame` candidates (v0.7 event kernel /
v0.8 bridge + a mixin) whose `controls_pest()` requires a Pest creature *token*. Frozen engines
and the 311 fixtures are untouched. `r01_tests/` holds 24 controls (both candidates, plus a pin
of the frozen engine's old behaviour) and a versioned copy of `test_v05_fixture_cards.py` with only
tests 112/113 corrected (114 unchanged). The runner replays the 149 frozen contracts against the
kernel and requires that exactly 112 and 113 fail. Supplied Oracle text remains unauthenticated.

Promoted: import `Game`/`PhysicalZoneGame` from `pab_kernel.py`. Reference fixtures: 326 (311 frozen + 13 R01 + 2 corrections). Frozen 112/113 are superseded, not edited. See R01_PATCH_NOTES.md.

## C41–C47 (R22–R26) executed
`tests/test_c41_c47_contracts.py`: 19 fixtures; 3 contracts fully EXECUTED, 4 EXECUTED_WITH_SUBSTITUTION (substitutions listed per class and in `VALIDATION_RESULTS.json → contracts_executed`). Reference fixtures: 345. See C41_C47_EXECUTION_NOTES.md.

## C48–C64 (R27–R34) executed
`tests/test_c48_c64_contracts.py`: 31 fixtures; 6 EXECUTED, 8 EXECUTED_WITH_SUBSTITUTION, 1 DISAGREEMENT_OBSERVED (C61 → new issue R47, design-only), 2 BLOCKED_UNSUPPORTED (C50, C62). Reference fixtures: 376. See C48_C64_EXECUTION_NOTES.md.

## C65–C77 (R35–R40, lands) executed
`tests/test_c65_c77_contracts.py`: 20 fixtures; 2 PARTIAL_EXECUTED (C69, C77), 11 BLOCKED_UNSUPPORTED with fail-closed probes covering all 18 unsupported land names. Reference fixtures: 396. See C65_C77_EXECUTION_NOTES.md.

## C78–C94 (R41–R46) executed — all 54 contracts now executed or probed
`tests/test_c78_c94_contracts.py`: 23 fixtures; 2 EXECUTED_WITH_SUBSTITUTION, 1 DISAGREEMENT_OBSERVED (C79 → new issue R48), 14 BLOCKED_UNSUPPORTED. Reference fixtures: 419. Consolidated table: CONTRACTS_C41_C94_STATUS.md.

## R47 + R48 promoted
`pab_r47_r48_sba.py` (Roaster resolution-time counter count; zero toughness as SBA, not destruction) layered on R01; `pab_kernel.py` now exports it. Reference fixtures: 420. See R47_R48_PATCH_NOTES.md.

## R49 + clock S1 promoted
R49: Roaster LKI when the source has left (CR 608.2h). S1: inert `TurnClock` (`pab_turn_clock.py`), carried by the kernel, consulted by nothing yet. Reference fixtures: 445. See R49_S1_PATCH_NOTES.md and PHASE_CLOCK_DEPENDENCY_MAP.md.

## Clock S2 promoted
Step boundaries now drive each-upkeep triggers, the controller's end step, mana emptying and cleanup expiry (`pab_clock_s2.py`). C95/C96/C98/C99 executed. See S2_PATCH_NOTES.md.

## Clock S2 promoted
Step boundaries now drive each-upkeep triggers, the controller's end step, mana emptying and cleanup expiry (`pab_clock_s2.py`). C95/C96/C98/C99 executed. See S2_PATCH_NOTES.md.

## Clock S3 promoted
SBA between resolutions with simultaneous-death look-back; Yawgmoth inline check retired; `set_trigger_order()`. C97 executed; C63 de-substituted. See S3_PATCH_NOTES.md.

## Clock S4 promoted
Untap, draw and land-play window driven by the clock on both kernels (`pab_clock_s4.py`). Clock stages S1–S4 complete. See S4_PATCH_NOTES.md.
