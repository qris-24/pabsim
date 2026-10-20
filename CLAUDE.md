# CLAUDE.md — PABTRV3 kernel (pab_reliability_v0_8_r02_r01)

## Layout
- `tests/` — kernel reference suite (`test_*.py`), part of the 810-test gate.
- `release_gate_tests/` — the 18 release integrity checks run by `run_validation.py`.
- `s9_tests/` — S9 land/mana layer fixtures.
- `r01_tests/` — R01 Pest rescuer fixtures.
- `r52_tests/` — R52 Village Rites fixtures.
- `frozen_*/` — frozen phase 5/6/7 and previous-test snapshots; read-only.
- `upstream_frozen/` — frozen upstream v0.5–v0.8 sources; read-only.
- `EVIDENCE/` — before-copies and supersession records (e.g. `EVIDENCE/CP06_SUPERSEDED/`).
- Card data (Oracle text lookup): `C:\pabsim\data\golgari_commander.json` — outside the repo, read-only.
- Layer files are named `pab_<thing>_s<n>.py` (stage layers) or `pab_*_cp<nn>.py` (checkpoint repairs).
- `pab_kernel.py` is the only import point. Use `Game` / `PhysicalZoneGame` from it.

## Commands (Python 3.14.7 on Windows, PowerShell)
- Full gate (expect `Ran 810 tests` / `OK`, and 18/18 in `VALIDATION_RESULTS.json`):
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
- Two deck targets. Old baseline (Savra + 99 + Pest Summoning Lesson): frozen, the only gated deck,
  regression reference. PAB v3 (Savra + 99, no sideboard): frozen pending kernel completion, not gated,
  not yet in the repo (deck file planned for CP19). Savra is the only irreplaceable card.
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
- Read-only audit stages also get CP<nn>_PATCH_NOTES.md; findings live in EVIDENCE/.
- Edits to this file also require a manifest re-pin (`py -3.14 build_manifest.py`).

## Open queue (see ISSUE_LEDGER_CP06.json for detail; closed items and their CPs: CP17_PATCH_NOTES.md)
- A-S20-05: two legal blockers do not coordinate to block menace.
- A-S20-08: hand-authored model coverage claims not mechanically certified (CP11 audit and CP12
  Infuse correction done; Darkbore Pathway WEAK; nothing certified).
- A-S20-09: inherited v0.8 counters and S20 path counters coexist.
- A-S20-10: target bookkeeping for Witherbloom Command and Grist -2.
- Auditor constant-resolution fix.
- Pest Rescuer Oracle sourcing.
- `HASTE_NAMES` in `pab_combat_s17.py` is a hardcoded name list; keywords should come from card data.
