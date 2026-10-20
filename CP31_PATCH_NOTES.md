# CP31 — Scryfall Oracle source for C45/C76; Pest Rescuer each-upkeep finding (2026-10-20)

Base: night/CP31 at cb24447 (CP30). No kernel layer or frozen file changed. Test count 857 -> 861.

## Summary
- New third Oracle source `decks/ORACLE_SOURCE_SCRYFALL_CP31.json` + `decks/CP31_SCRYFALL_DECK_EXPORT.json` (copied byte-exact).
- oracle_referenced: 51 -> 53 of 59. C45 True (Skullclamp, 3 refs) and C76 True (Sanitarium, Mikokoro); both were False.
- Gate fails closed on a `sources.scryfall` sha256 mismatch (as for the supplement).
- Pest Rescuer: Oracle (Scryfall, equal to golgari_commander.json) says "each upkeep"; R01 docstring quotes "your upkeep".
- But the kernel already fires it on every seat's upkeep (S2 clock, pab_clock_s2.py:37; asserted by C95), so the
  prompt's queue wording "the kernel models only your own upkeep" would be false. CLAUDE.md records the accurate finding.
- Approved expectation change: tests/test_oracle_subjects_cp29.py C45/C76 assertions False -> True (details below).
- Follow-ups: correct the R01 docstring text (pab_r01_pest_rescuer.py:4); Pest Rescuer is not referenced by any
  contract mapping, so its Scryfall record is not in the excerpt.

## Changes
- `build_oracle_excerpt.py`: scryfall as third source (lookup order golgari_commander.json, supplement, scryfall);
  `sources.scryfall` {path, sha256}; source label `scryfall_cp31`; summary line `from scryfall_cp31`.
- `decks/ORACLE_EXCERPT_CP28.json`, `EVIDENCE/CP28_ORACLE_EXCERPT_SUMMARY.txt`: rebuilt (61 cards: 54 golgari, 4 supplement,
  3 scryfall_cp31, 0 missing).
- `run_validation.py`: `ORACLE_SCRYFALL`; `oracle_reference_check()` fails closed on a scryfall sha256 mismatch;
  REFERENCE_TEST_COUNT 857 -> 861; per-file count for `test_oracle_source_cp31.py` (4).
- `CONTRACT_ORACLE_REFS_CP28.json`: C45 +3 Skullclamp refs, C76 +2 refs (Sanitarium, Mikokoro); both notes updated.
  `subjects` unchanged: Skullclamp (C45) and both lands (C76) were already subjects and are string literals in their classes.
- `tests/test_oracle_subjects_cp29.py` (approved in the CP31 prompt):
  - `test_c45_false_skullclamp_missing` -> `test_c45_true_skullclamp_covered`: assertFalse(oracle_referenced) and
    assertIn('Skullclamp', missing) became assertTrue, missing == [], excerpt source == scryfall_cp31.
  - `test_c76_false` -> `test_c76_true`: assertFalse became assertTrue, missing == [].
- New `tests/test_oracle_source_cp31.py` (4 tests): excerpt text equals source records; sha256 fails closed on a
  mutated copy and on a mutated excerpt hash; `card_ids_from.sha256` equals the export file.
- `release_gate_tests/test_r02_release_gate.py`: expected (tests_run, tests_passed) (861, 861).
- `PABTRV3_CARD_COVERAGE.json` (build_registry.py, output redirected), manifest re-pinned.
- `EVIDENCE/CP31_PEST_RESCUER_ORACLE.md`: the finding (record only).
- `CLAUDE.md`: Layout +2 decks files; queue item replaced; C45/C76 Oracle-sourcing follow-ups removed.
