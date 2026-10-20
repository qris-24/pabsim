# CP16 — Read-only v3 delta audit (2026-10-19; notes written retroactively at CP17)

Read-only audit. Kernel, tests, deck, Oracle data, ledger and frozen files unchanged. Suite shape unchanged: 810 tests, 18/18 release gate.

- Scope: delta from PAB v2 to PAB v3 on top of the CP15 audit (swaps and v3 added-card list, coverage status, Oracle text sourcing from `C:\pabsim\data\golgari_commander.json`, ledger effect of the two swaps, static reading of release-check failure counts under v3). Nothing executed or implemented.
- Commit: `4a9e757` ("CP16: v3 delta audit, read-only"). Tag: `rp-CP16`.
- Files changed: `EVIDENCE/CP15_DECK_MIGRATION_AUDIT.md` (section 8 "v3 delta (CP16)" appended), `CLAUDE.md` (Layout: card-data path line added), `PHASE8_R02_FILE_MANIFEST.json` (re-pinned with `py -3.14 build_manifest.py`).
- Findings: `EVIDENCE/CP15_DECK_MIGRATION_AUDIT.md` section 8.
- No patch notes were written at CP16; this file was added at CP17 under the rule that read-only audit stages also get `CP<nn>_PATCH_NOTES.md`.
