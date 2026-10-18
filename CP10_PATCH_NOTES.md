# CP10 — audit repairs AUD-01, AUD-02, A-S20-11 (2026-10-18)

Three steps, each committed and tagged separately (`rp-CP10a`, `rp-CP10b`, `rp-CP10c`). No frozen file
edited. Gate bookkeeping moved with each step exactly as at CP02–CP06: `run_validation.py`
`REFERENCE_TEST_COUNT` and the per-file count assertion for `tests/test_auditfix_cp10.py`,
`release_gate_tests/test_r02_release_gate.py` expected `(tests_run, tests_passed)`, the coverage registry
(`py -3.14 build_registry.py`, output redirected) and the manifest (`py -3.14 build_manifest.py`). These
files were not on the step file lists; they are the only way the gate accepts a new test file and were
treated as part of "the gate", not as a logic change.

## CP10a — AUD-01 (A-S20-12): colored-mana planning counts the pool once

### What
`pab_lands_s9.py` `tap_lands_policy`: `pool=g.mana_pool+produced` → `pool=g.mana_pool`. Confirmed first by
reading `FixerLandsMixin.tap_physical_land_for_mana` (same file): it does `self.mana_pool.append(color)` for
every tap, so `produced` was a second copy of the same colours. No other logic changed; the short-colour
rule and the default (`'C'` if offered, else `'B'`) are as before.

### Why
With Command Tower + Blooming Marsh untapped and a hand needing {G}{G} (Essence Warden + Pest Rescuer), the
first tap gave `G`, after which the pool counted `G` twice (`['G']+['G']`), so the second dual saw no
shortfall and gave `B`: `['G','B']` instead of `['G','G']`. Every multi-dual turn in the S9–S18 drivers was
planned with this double count.

### Verification
`tests/test_auditfix_cp10.py` class `TestCP10ColoredMana` (6 tests): the reproduction yields `['G','G']`;
need G1 B1 over two duals → one of each; no colour need → policy default per land (`['B','B']` for
Tower + Marsh, `['C','B']` for Wastes + Tower); Llanowar Wastes with G short → `G` (and 1 damage), not `C`;
single dual with need G2 → `G`; negative control recomputes the old double-count arithmetic (`['G','B']`),
derives the expectation from need alone (`['G','G']`), asserts the policy matches the latter and not the
former. Full gate: `Ran 785 tests` / `OK` (779 + 6), 18/18 release checks. All S9 pinned-seed driver
fixtures (`tests/test_lands_s9.py`, `s9_tests/`) passed unchanged — no expectation moved, no
`EVIDENCE/CP10_SUPERSEDED/` entry needed for this step.
