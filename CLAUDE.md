# CLAUDE.md — PABTRV3 kernel (pab_reliability_v0_8_r02_r01)

## Layout
- `tests/` — kernel reference suite (`test_*.py`), part of the 828-test gate.
- `release_gate_tests/` — the 21 release integrity checks run by `run_validation.py`.
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
- Full gate (expect `Ran 828 tests` / `OK`, and 21/21 in `VALIDATION_RESULTS.json`):
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
  not yet in the repo (deck file planned for CP24). Savra is the only irreplaceable card.
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
- Each stage ends, in order, with:
  gate run → `CP<nn>_PATCH_NOTES.md` → `py -3.14 build_paste_me.py --stage CP<nn>`
  → manifest re-pin → gate re-run → commit → tag `rp-CP<nn>`
  → `git push; git push origin rp-CP<nn>`
  → `Get-Content PASTE_ME.md -Raw -Encoding UTF8 | Set-Clipboard`
  → final message states the PASTE_ME.md path and "copied to clipboard".
  This applies to read-only stages too.
  Edit only the MANUAL section of PASTE_ME.md, and only when a decision changes.
- Read-only audit stages also get CP<nn>_PATCH_NOTES.md; findings live in EVIDENCE/.
- Every CP<nn>_PATCH_NOTES.md has "## Summary" (findings, decisions, open follow-ups; at most 12 lines).
  `build_paste_me.py` copies it into PASTE_ME.md and refuses to run without it.
- Stage-end bookkeeping, always in scope (read-only stages included): remove the closed stage from
  "## Next stages" and add the follow-ups it raised.
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
- CP21 claims left unasserted (no model): C83 "can't be countered" (no counterspell model), C84
  opponent basic-land search, C92 Grist +1 Insect-card repeat (unreachable with the deck), C94 mode 1
  on an opponent (no opponent libraries). Stand-ins named in C82, C85, C90, C91 SUBSTITUTIONS.

## Next stages
- CP22: A-S20-10 (target bookkeeping for Witherbloom Command, Grist -2), then re-status C93, C94
  (PARTIAL_EXECUTED since CP21; the gap is the only unasserted claim besides C94's opponent mill).
- Docs follow-up (from CP21): README.md and C78_C94_EXECUTION_NOTES.md still describe C80–C94 as
  BLOCKED_UNSUPPORTED; the CP21 re-status is recorded only in CONTRACTS_C41_C94_STATUS.md.
  C95–C99 are now documented there (CP22); README.md and C78_C94_EXECUTION_NOTES.md stay open.
- CP23: read-only lookup of all 100 PAB v3 names in C:\pabsim\data\golgari_commander.json.
- CP24: pinned Oracle supplement (incl. Altar of Dementia, Ashnod's Altar) + v3 deck file as second
  target, delta cards UNMODELED. Mark C62, C63, C64, C85, C86 old-baseline-only. Derive
  oracle_cr_authenticated (run_validation.py:239) from a per-contract Oracle reference check.
- Then the ledger, in order: auditor constant-resolution fix, Pest Rescuer Oracle sourcing,
  A-S20-05, A-S20-09, HASTE_NAMES.
