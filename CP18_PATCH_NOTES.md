# CP18 — PASTE_ME.md handoff file + builder; stage-end sequence (2026-10-19)

Bookkeeping only. No kernel logic, test logic or card modeling changed. No frozen file, deck, Oracle data or ledger edited. No new test file. Suite shape unchanged: 810 tests, 18/18 release gate.

## Files
- new `PASTE_ME.md` — handoff file for a new Claude chat or Claude Code session. Two marked sections: `<!-- MANUAL:START/END -->` (hand-written project summary, standing rules, deck targets; edited only when a decision changes) and `<!-- AUTO:START/END -->` (generated).
- new `build_paste_me.py` — standard library only. `py -3.14 build_paste_me.py --stage CP<nn>` rewrites only the AUTO section: closing stage, build timestamp, branch, HEAD short hash + subject (parent of this stage's commit), latest `rp-CP` tag, uncommitted file count; from `VALIDATION_RESULTS.json`: tests run/passed, release gate passed/run, `kernel_version`, `frozen_engines_modified`, `full_card_behavior_verified`, `mass_replacement_sweep_allowed`, contract counts by status; CLAUDE.md `## Open queue`, `## Next stages`, `## Commands` verbatim; the three highest-numbered `CP<nn>_PATCH_NOTES.md` with their first heading. Exits non-zero without writing if a marker, `VALIDATION_RESULTS.json` or one of the three CLAUDE.md sections is missing. One line of terminal output (path + byte count). Output is identical between runs except the timestamp (checked by diff of two consecutive runs).
- edit `CLAUDE.md` — new `## Next stages` section directly after `## Open queue` (CP19 read-only contract-path audit, CP20 v3 name lookup, CP21 Oracle supplement + v3 deck file, then card modeling in ledger order); deck file now "planned for CP21"; stage-end line replaced by the ordered sequence below.
- re-pinned `PHASE8_R02_FILE_MANIFEST.json`.

## Stage-end sequence (now in CLAUDE.md, applies to read-only stages too)
gate run → `CP<nn>_PATCH_NOTES.md` → `py -3.14 build_paste_me.py --stage CP<nn>` → manifest re-pin → gate re-run → commit → tag `rp-CP<nn>` → `git push; git push origin rp-CP<nn>` → `Get-Content PASTE_ME.md -Raw | Set-Clipboard` → final message states the PASTE_ME.md path and "copied to clipboard".

## Observation (not fixed; bookkeeping note for the sequence)
`run_validation.py` verifies every manifest-pinned input before running tests, and the manifest pins `CLAUDE.md`, `PASTE_ME.md` and every `CP<nn>_PATCH_NOTES.md`. The first gate run of this stage therefore stopped at `R02 package changed: CLAUDE.md` before any test ran. In a stage that edits pinned non-kernel files, the first gate run is only meaningful before those edits; after them the re-pin must precede the gate. The gate reported below is the run after the re-pin. Because `PASTE_ME.md` is pinned, the builder must run before the re-pin and must not run again afterwards (its timestamp would change the pinned hash), which is why the AUTO section records HEAD as the parent of this stage's commit rather than the stage commit itself.

## Gate
Post-re-pin: `Ran 810 tests` / `OK`; `VALIDATION_RESULTS.json` 18/18 release gate, `tests_run` 810, `tests_passed` 810.
