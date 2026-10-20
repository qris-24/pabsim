# CP21 — Re-status stale contracts on PhysicalZoneGame; blocked-status release check (2026-10-19)

Contract-test stage. No kernel layer, frozen file, deck, Oracle data or ledger entry edited. Implements CP19 proposed fixes 4 and 6 (`EVIDENCE/CP19_CONTRACT_PATH_AUDIT.md`) and the CLAUDE.md release check. Suite 810 -> 828 tests (`tests/test_c78_c94_contracts.py` 23 -> 41); release gate 20 -> 21 checks.

## Summary
- Contract status counts, all 59 (before -> after): BLOCKED_UNSUPPORTED 16 -> 2 (C50, C62); EXECUTED 23 -> 28; EXECUTED_WITH_SUBSTITUTION 17 -> 21; PARTIAL_EXECUTED 3 -> 8.
- Re-statused on `pab_kernel.PhysicalZoneGame` (S15/S16/S20): EXECUTED C80, C81, C86, C88, C89; WITH_SUBSTITUTION C82, C85, C90, C91; PARTIAL C83, C84, C92, C93, C94. Each keeps its `Game.add()` refusal as `test_event_kernel_control_add_refused`.
- Claims left unasserted: C83 "can't be countered" (no counterspell model); C84 opponent's basic-land search (traced unmodeled); C92 Grist +1 Insect-card repeat (unreachable: Grist is the deck's only Insect card); C93 target bookkeeping, A-S20-10 (CP22); C94 target bookkeeping, A-S20-10 (CP22), and mode 1 on an opponent (no opponent libraries).
- Stand-ins named: C82 deathtouch via `_deathtouch()` predicate, opponent body re-declared; C85 opponent choice = S8 `edict_choice()`; C90 "nonlegendary" = `LEGENDARY_CARDS` name set; C91 creature-card static by name, not type line (n3).
- Decision: CONTRACTS_C41_C94_STATUS.md has no per-contract claim list, so claims were taken from each class's former "not modeled (...)" text plus the rules_contract column of `upstream_frozen/PABTRV3_MECHANICAL_INVENTORY.csv` (read only).
- Release check `BlockedContractsProbed`: every BLOCKED_UNSUPPORTED class defines `KERNEL_PROBE` (added to C50, C62, logic as CP19 c.3); fails on a missing probe or a probe returning True. Both return False.
- [n1] SUBSTITUTIONS text refreshed for C41, C42, C44, C57, C60, C78, C79, C87 (text only; statuses unchanged).
- Kernel defects found: none. Frozen pins: grep found no BLOCKED_UNSUPPORTED count or status under `frozen_*/` or `upstream_frozen/`.
- Open follow-ups: CP22 (A-S20-10, then C93/C94); README.md and C78_C94_EXECUTION_NOTES.md still say BLOCKED for C80–C94 (out of CP21 scope; added to CLAUDE.md "## Next stages").

## Files
- `tests/test_c78_c94_contracts.py` (PhysicalZoneGame helpers, 18 new `test_pzg_*` methods, 14 STATUS/SUBSTITUTIONS, control tests renamed), `tests/test_c41_c47_contracts.py` and `tests/test_c48_c64_contracts.py` (SUBSTITUTIONS text; C50/C62 `KERNEL_PROBE`), `release_gate_tests/test_r02_release_gate.py` (new check; EndToEnd 828), `run_validation.py` (REFERENCE_TEST_COUNT 828, per-file 41), `CONTRACTS_C41_C94_STATUS.md` (appended "CP21 re-status"), `PABTRV3_CARD_COVERAGE.json` (rebuilt: reference count 828), `CLAUDE.md`, `PASTE_ME.md` (AUTO via builder), new `CP21_PATCH_NOTES.md`, re-pinned `PHASE8_R02_FILE_MANIFEST.json`.

## Verification
- Mutation check (scratch, not committed): removing the S15 mana-value filter, dropping Dina from `LEGENDARY_CARDS`, or disabling regeneration each fails the matching C83 / C90 / C81 test.

## Gate
Pre-edit (CP20 close): `Ran 810 tests` / `OK`; 20/20. After the edits, registry rebuild and manifest re-pin: `Ran 828 tests` / `OK`; `VALIDATION_RESULTS.json` `tests_run` 828, `tests_passed` 828, release gate 21/21. Re-run after `build_paste_me.py --stage CP21` and the final re-pin recorded in the commit.
