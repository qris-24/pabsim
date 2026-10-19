# CLAUDE.md — PABTRV3 kernel (pab_reliability_v0_8_r02_r01)

## Layout
- `tests/` — kernel reference suite (`test_*.py`), part of the 779-test gate.
- `release_gate_tests/` — the 18 release integrity checks run by `run_validation.py`.
- `s9_tests/` — S9 land/mana layer fixtures.
- `r01_tests/` — R01 Pest rescuer fixtures.
- `r52_tests/` — R52 Village Rites fixtures.
- `frozen_*/` — frozen phase 5/6/7 and previous-test snapshots; read-only.
- `upstream_frozen/` — frozen upstream v0.5–v0.8 sources; read-only.
- `EVIDENCE/` — before-copies and supersession records (e.g. `EVIDENCE/CP06_SUPERSEDED/`).
- Layer files are named `pab_<thing>_s<n>.py` (stage layers) or `pab_*_cp<nn>.py` (checkpoint repairs).
- `pab_kernel.py` is the only import point. Use `Game` / `PhysicalZoneGame` from it.

## Commands (Python 3.14.7 on Windows, PowerShell)
- Full gate (expect `Ran 779 tests` / `OK`, and 18/18 in `VALIDATION_RESULTS.json`):
  `py -3.14 run_validation.py 2> ..\gate.txt | Out-Null; Get-Content ..\gate.txt -Tail 3`
- Kernel suite only: `py -3.14 -m unittest discover -s tests -p "test_*.py" -q`
- Re-pin after any tracked-file change: `py -3.14 build_manifest.py`
- Registry: `build_registry.py` (redirect its output; never let it print to the terminal).
- Line endings are LF; `core.autocrlf` is `false`. Do not introduce CRLF.

## Frozen, never edited
- `pab_focus_engine.py`, `pab_focus_engine_v07.py`, `pab_zone_bridge.py`, `pab_zone_bridge_v08.py`, `pab_zones.py`.
- `frozen_*/`, `upstream_frozen/`, and the 311 v0.5–v0.8 fixtures.
- Fixes are layered in new files (versioned subclasses / mixins), never patched into frozen ones.
- A frozen expectation that must move = stop and ask. Document any approved supersession with
  before-copies in `EVIDENCE/`.

## Project rules
- Deck (Savra + 99 mainboard) and the Pest Summoning Lesson are unchanged. Savra is the only
  irreplaceable card.
- Phase 9 is NO-GO. S21 not started.
- No sweeps, rankings, card values, or performance claims.
- 0 cards are certified until the registry is verified against code.
- Kernel bugs found during work are fixed as found, in a layer, without stopping, unless a frozen
  expectation would move (then stop and ask).

## Session rules
- Adding a test file also requires updating REFERENCE_TEST_COUNT and the per-file count in run_validation.py, the expected (tests_run, tests_passed) in release_gate_tests/test_r02_release_gate.py, build_registry.py output and the manifest; these are gate bookkeeping and always in scope.
- One scoped task per session; file paths named explicitly.
- Run tests with `-q`; read tails only. No decklists or results printed to the terminal.
- Do not re-read files just edited.
- Stop after 2 failed attempts at the same step.
- Each stage ends with: `CP<nn>_PATCH_NOTES.md` + commit + lightweight tag `rp-CP<nn>` +
  `git push; git push origin rp-CP<nn>`.
- Edits to this file also require a manifest re-pin (`py -3.14 build_manifest.py`).

## Open queue (see ISSUE_LEDGER_CP06.json for detail)
- AUD-01 (A-S20-12): colored-mana double count in `pab_lands_s9.py` `tap_lands_policy`
  (`pool = g.mana_pool + produced`).
- AUD-02 (A-S20-13): impossible opponent script accepted in `pab_interaction_s11.py`.
- AUD-03 (A-S20-14): tutor pre-commits library choice at cast in `pab_cast_s13.py`.
- A-S20-05, A-S20-06, A-S20-08, A-S20-09, A-S20-10, A-S20-11: as in the ledger.
- AUD-04 = A-S20-03, repaired at CP06.
