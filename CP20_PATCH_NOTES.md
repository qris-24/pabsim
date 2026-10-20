# CP20 — Bookkeeping: derived manifest/results metadata, two gate checks, PASTE_ME repairs (2026-10-19)

Bookkeeping stage. No kernel, contract test, deck, Oracle, ledger or frozen file edited. Suite shape unchanged: 810 tests; release gate 18 -> 20 checks. Implements CP19 proposed fixes 1–3 (`EVIDENCE/CP19_CONTRACT_PATH_AUDIT.md`).

## Summary
- `build_manifest.py`: `patches` = `list(pab_kernel.PROMOTED)` (was a literal stopping at CP06); `scope` is one sentence built from `pab_kernel.KERNEL_VERSION`; `unique_fixture_tests` is counted from `tests/test_*.py` (was the stale literal 779; now 810).
- `run_validation.py`: the `def test_` regex lives once, as `TEST_DEF_RE` / `count_test_defs()`; `build_manifest.py` imports it. `scope` and `release` in VALIDATION_RESULTS are built from `pab_kernel.PROMOTED`; no hand-written stage number remains.
- `release_gate_tests/test_r02_release_gate.py`: new `ManifestMetadata` class — shipped manifest `patches` == `pab_kernel.PROMOTED`; shipped manifest `unique_fixture_tests` == `REFERENCE_TEST_COUNT`. Gate is now 20 checks.
- `build_paste_me.py`: copies the closing stage's `## Summary` into AUTO right after "Stage state"; exits non-zero without writing if `CP<nn>_PATCH_NOTES.md` or its `## Summary` is missing; label renamed "Uncommitted files (before stage commit)"; strips a BOM on read, writes UTF-8 without BOM, LF.
- `CLAUDE.md`: clipboard command uses `-Encoding UTF8`; two session rules added (every patch note has `## Summary`; stage-end "## Next stages" bookkeeping); 18/18 -> 20/20; deck file planned for CP24; "## Next stages" replaced with CP21–CP24 and the ledger order.
- `PASTE_ME.md` MANUAL: "deck file at CP21" -> "deck file at CP24". No other MANUAL line changed.
- Grep of `tests/`, `s9_tests/`, `r01_tests/`, `r52_tests/`, `release_gate_tests/` for the old `release` / `scope` text: no pins. Frozen runners carry their own `scope` literals only; nothing under `frozen_*/` or `upstream_frozen/` touched.
- Decision: the shared counter lives in `run_validation.py` (the gate owner); `build_manifest.py` imports it, so the builder is still never invoked by the runner.
- Open follow-ups: CP21 contract re-status (see CLAUDE.md "## Next stages"); `full_card_verified` in the manifest and `oracle_cr_authenticated` in the runner remain literals (CP24).

## Files
- `build_manifest.py`, `run_validation.py`, `release_gate_tests/test_r02_release_gate.py`, `build_paste_me.py`, `CLAUDE.md`, `PASTE_ME.md` (MANUAL: one line; AUTO regenerated), new `CP20_PATCH_NOTES.md`, re-pinned `PHASE8_R02_FILE_MANIFEST.json`.

## Gate
Pre-edit (CP19 close): `Ran 810 tests` / `OK`; 18/18. After the edits and manifest re-pin: `Ran 810 tests` / `OK`; `VALIDATION_RESULTS.json` `tests_run` 810, `tests_passed` 810, release gate 20/20, `r02_release_gate_errors` empty. Re-run after `build_paste_me.py --stage CP20` and the final re-pin recorded below.
