# CLAUDE.md — PABTRV3 kernel (pab_reliability_v0_8_r02_r01)

## Layout
- `tests/` — kernel reference suite (`test_*.py`), part of the gate (test count: REFERENCE_TEST_COUNT in run_validation.py).
- `release_gate_tests/` — the release integrity checks run by `run_validation.py` (RELEASE_GATE_TEST_COUNT, 29 since CP42).
- `s9_tests/` — S9 land/mana layer fixtures.
- `r01_tests/` — R01 Pest rescuer fixtures.
- `r52_tests/` — R52 Village Rites fixtures.
- `decks/` — PAB v3 second deck target (CP26): Archidekt export, `PAB_V3.json`, `PAB_V3_ORACLE_SUPPLEMENT.json`; not gated.
- `decks/ORACLE_EXCERPT_CP28.json` — pinned Oracle text (CP28) for the cards the contract references name; the
  gate's only Oracle text source (never C:\pabsim\data). Built by `build_oracle_excerpt.py` (repo root; not run by the gate).
- `decks/ORACLE_SOURCE_SCRYFALL_CP31.json` — third pinned Oracle source (CP31; Scryfall card fields verbatim, excerpt
  source `scryfall_cp31`, lookup order golgari_commander.json, supplement, scryfall); never edited.
- `decks/CP31_SCRYFALL_DECK_EXPORT.json` — the user's Scryfall deck export supplying the printing ids (sha256 in the source file).
- `decks/CARDSOURCE_BG_COMMANDER_20261021.json` — pinned cardsource.py export (Scryfall Oracle bulk data of 2026-10-21; Commander-legal, color identity within BG incl. colorless; 12628 cards). The gate's card-data source for name resolution (CP35); never edited, a newer export is a new file.
- `CONTRACT_ORACLE_REFS_CP28.json` — per-contract (C41–C99) Oracle references {card, fragment} + note; drives
  `oracle_referenced` / `oracle_refs_checked` in VALIDATION_RESULTS.json. `oracle_cr_authenticated` stays False (no CR text).
- `frozen_*/` — frozen phase 5/6/7 and previous-test snapshots; read-only.
- `upstream_frozen/` — frozen upstream v0.5–v0.8 sources; read-only.
- `EVIDENCE/` — before-copies and supersession records (e.g. `EVIDENCE/CP06_SUPERSEDED/`).
- Card data (Oracle text lookup): `C:\pabsim\data\golgari_commander.json` — outside the repo, read-only; used only by build_oracle_excerpt.py. The gate's card data is the pinned `decks/CARDSOURCE_BG_COMMANDER_20261021.json` (CP35).
- Layer files are named `pab_<thing>_s<n>.py` (stage layers) or `pab_*_cp<nn>.py` (checkpoint repairs).
- `pab_kernel.py` is the only import point. Use `Game` / `PhysicalZoneGame` from it.

## Commands (Python 3.14.7 on Windows, PowerShell)
- Full gate (expect `Ran N tests` / `OK`, N = REFERENCE_TEST_COUNT in run_validation.py,
  and 29/29 release checks in `VALIDATION_RESULTS.json`, = RELEASE_GATE_TEST_COUNT):
  `py -3.14 run_validation.py 2> ..\gate.txt | Out-Null; Get-Content ..\gate.txt -Tail 3`
- Kernel suite only: `py -3.14 -m unittest discover -s tests -p "test_*.py" -q`
- Re-pin after any tracked-file change: `py -3.14 build_manifest.py`
- `py -3.14 build_oracle_excerpt.py` re-pins the excerpt after a mapping change (then re-pin the manifest).
- Registry: `build_registry.py` (redirect its output; never let it print to the terminal).
- Line endings are LF. `.gitattributes` (`* -text`, CP30) disables line-ending conversion in every clone,
  whatever the machine's `core.autocrlf`. Do not introduce CRLF.
- Headless Claude Code on this machine runs commands in Git Bash; there the gate command is: py -3.14 run_validation.py > ../gate/gate_stdout.txt 2> ../gate/gate.txt (a redirect to NUL creates a stray file).

## Frozen, never edited
- `pab_focus_engine.py`, `pab_focus_engine_v07.py`, `pab_zone_bridge.py`, `pab_zone_bridge_v08.py`, `pab_zones.py`.
- `frozen_*/`, `upstream_frozen/`, and the 311 v0.5–v0.8 fixtures.
- Fixes are layered in new files (versioned subclasses / mixins), never patched into frozen ones.
- A frozen expectation that must move = stop and ask. Document any approved supersession with
  before-copies in `EVIDENCE/`.
- Best-effort guard for Claude Code: deny rules in .claude/settings.json. The enforcement is the launcher's scope check and the gate's frozen-file checks.

## Project rules
- Two deck targets. Old baseline (Savra + 99 + Pest Summoning Lesson): frozen, the only gated deck,
  regression reference. PAB v3 (Savra + 99, no sideboard): frozen pending kernel completion, not gated,
  in the repo (decks/, since CP26); v3 cards not on the old baseline are UNMODELED. Savra is the only irreplaceable card.
- Phase 9 is NO-GO. S21 not started.
- No sweeps, rankings, card values, or performance claims.
- 0 cards are certified until the registry is verified against code.
- Kernel bugs found during work are fixed as found, in a layer, without stopping, unless a frozen
  expectation would move (then stop and ask).
- Original compiler retired (CP31c): go/no-go condition 2 superseded by the kernel contract suite; 10/15 kept as history (EVIDENCE/CP31c_COMPILER_RETIREMENT.md).

## Session rules
- Adding a test file also requires updating REFERENCE_TEST_COUNT and the per-file count in run_validation.py, the expected (tests_run, tests_passed) in release_gate_tests/test_r02_release_gate.py, build_registry.py output and the manifest; these are gate bookkeeping and always in scope.
- Adding a release-gate test (release_gate_tests/) also requires updating RELEASE_GATE_TEST_COUNT in run_validation.py (gate bookkeeping).
- The gate refuses python -O / PYTHONOPTIMIZE; PAB_R02_SKIP_GATE=1 (only for the release gate's inner run) exits 3, never 0 (CP41).
- One scoped task per session; file paths named explicitly.
- Run tests with `-q`; read tails only. No decklists or results printed to the terminal.
- Do not re-read files just edited.
- Stop after 2 failed attempts at the same step.
- Each stage ends, in order, with:
  edits + `CP<nn>_PATCH_NOTES.md` → `py -3.14 build_manifest.py` → gate
  → `py -3.14 build_paste_me.py --stage CP<nn>` → commit → tag `rp-CP<nn>`
  → `git push; git push origin rp-CP<nn>`
  → `Get-Content PASTE_ME.md -Raw -Encoding UTF8 | Set-Clipboard`
  → final message states the PASTE_ME.md path and "copied to clipboard".
  On gate failure: fix, re-pin, re-run gate.
  This applies to read-only stages too.
  Any tracked-file edit after the gate requires re-pin + gate re-run.
  Edit only the MANUAL section of PASTE_ME.md, and only when a decision changes.
- Read-only audit stages also get CP<nn>_PATCH_NOTES.md; findings live in EVIDENCE/.
- Every CP<nn>_PATCH_NOTES.md has "## Summary" (findings, decisions, open follow-ups; at most 12 lines).
  `build_paste_me.py` copies it into PASTE_ME.md and refuses to run without it.
- Stage-end bookkeeping, always in scope (read-only stages included): remove the closed stage from
  "## Next stages" and add the follow-ups it raised.
- Edits to this file also require a manifest re-pin (`py -3.14 build_manifest.py`).
- Stage prompts and the launcher live outside the repo in C:\pabsim\night\ (run_stage.ps1 -Stages CP<nn>; it tags, pushes and copies PASTE_ME.md after checking the stage commit).
- Never delete or move a tracked file by hand; use git rm / git mv inside a stage.
- Every file on disk inside the repo is pinned by the manifest (run_validation.py checks the on-disk file set, not git's); any stray file in the repo folder fails the gate, and the error names it (CP41).
- The three legacy manifests are pinned by sha256 in run_validation.py (LEGACY_MANIFEST_SHA, CP41); they never change.

## Open queue (see ISSUE_LEDGER_CP06.json for detail; closed items and their CPs: CP17_PATCH_NOTES.md)
- A-S20-05: two legal blockers do not coordinate to block menace.
- A-S20-08: hand-authored model coverage claims not mechanically certified (CP11 audit and CP12
  Infuse correction done; Darkbore Pathway WEAK; nothing certified).
- A-S20-09: inherited v0.8 counters and S20 path counters coexist.
- Auditor constant-resolution fix.
- `HASTE_NAMES`, `DEATHTOUCH_NAMES`, `FLYING_NAMES`, `MENACE_NAMES`, `CANT_BLOCK_NAMES` in `pab_combat_s17.py` are
  hardcoded name lists (checked against the pinned card data since CP37); keywords should come from card data.
- CP21 claims left unasserted (no model): C83 "can't be countered" (no counterspell model), C84
  opponent basic-land search, C92 Grist +1 Insect-card repeat (unreachable with the deck), C94 mode 1
  on an opponent (no opponent libraries). Stand-ins named in C82, C85, C90, C91 SUBSTITUTIONS.

## Next stages
- CP31d follow-up: integrity review findings in EVIDENCE/CP31d_INTEGRITY_REVIEW.md, one stage each:
  kernel defect K14 (unconfirmed, needs CR text) (K1, K4, K9, K10, K12 closed in CP37; K2, K5, K8, K11, K13 in CP38; K3, K6, K7 in CP39); gate G1-G4 closed (G1 in CP35, G2-G4 in CP41);
  test hygiene T1 (documented only: frozen files; T2-T6 closed in CP40/CP42, T7 in CP35);
  PABTRV3_CARD_COVERAGE.json summary (build_registry.py). Some test fixes move expectations: ask first.
- CP38 follow-up (Stage C): build_model_coverage_s20.py and PABTRV3_MODEL_COVERAGE_S20.json still say Takenuma does not return planeswalker cards (CP38 returns Grist).
- CP37 follow-up (Stage C): South Wind Avatar's lifegain reads printed toughness (pab_focus_engine_v07.py:321, frozen), so
  Skullclamp, counters and until-end-of-turn changes are ignored; needs a layered last-known-information fix.
- CP30 follow-up: C:\pabsim-git (ChatGPT backup clone) predates .gitattributes; re-clone it or run
  `git rm --cached -r . -q; git reset --hard` there so its files are LF.
- CP26 follow-up: export vs evidence mismatches recorded, not resolved (High Market text whitespace;
  Verdant Catacombs printing id); see decks/PAB_V3_ORACLE_SUPPLEMENT.json.
- CP26 follow-up: old-baseline-only marking used deck-card string literals for C41-C79/C95-C99, which
  counts fixture helpers; C42, C43, C44, C45, C50, C53, C54, C56, C58, C59, C75, C76, C78, C91, C95, C97
  reference at least one old-baseline-only card and are not marked. Review their subject cards.
- CP28 follow-up: contracts whose rules need CR text (none in the repo): C96 has `refs: []` (mana emptying,
  CR 106.4); CR-only parts of other contracts are named in their CONTRACT_ORACLE_REFS_CP28.json notes.
- CP29 follow-up: False because `subjects: []` (subject card not a string literal in the class, or a stand-in):
  C64 (Hunt for Specimens), C68 (Pathway via PATHWAY), C69 (Nature's Lore / Sakura-Tribe Elder), C79 (Heroic
  Intervention stand-in); C96 is rules-only. User (CP29): accepted False for now.
  Open: resolve module constants as subject evidence (C68), decide on method-driven subjects (C64, C69).
- CP31c follow-up: compiler signatures with no covering contract (see EVIDENCE/CP31c_COMPILER_RETIREMENT.md) become new contract candidates.
- Then the ledger, in order: auditor constant-resolution fix,
  A-S20-05, A-S20-09, keyword name lists from card data.
