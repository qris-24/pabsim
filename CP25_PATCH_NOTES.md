# CP25 — Read-only PAB v3 name lookup (2026-10-20)

Read-only stage. No kernel, test, deck-target or Oracle-data changes. No frozen file edited. No cards certified.

## Summary
- v3 list derived from the frozen baseline (lines 2, 5-90; Lesson line 93 dropped) − CP15 §1 Removed (audit :22-24) + §1 Added (:27-29) + §8.1 swaps (:182-183), cross-checked against §8.1 v3 added (:191-194).
- Derivation result: 100 cards (Savra + 99), 87 distinct names, 34 lands; 0 source conflicts.
- Lookup in C:\pabsim\data\golgari_commander.json (per distinct name): found 79, normalized 0, missing 8.
- Missing: Altar of Dementia, Ashnod's Altar (expected) + Arcane Signet, Command Tower, High Market, Phyrexian Altar, Sol Ring, Verdant Catacombs (not expected).
- Cause: the card data has no colorless-identity objects (B/G/BG only); all 8 are colorless identity. No Oracle text guessed.
- v3 list pending user approval before CP26.
- CLAUDE.md: stage-close order now re-pins before the gate (edits + notes → re-pin → gate → paste → commit → tag → push → clipboard; on failure fix, re-pin, re-run); "any tracked-file edit after the gate requires re-pin + gate re-run".
- Follow-up: CP26 Oracle supplement must cover all 8 missing names, not only the two Altars.
- Follow-up: README.md lines 63 and 66 still state pre-CP21 BLOCKED counts for C65–C77 and C78–C94.

## Files
- New: EVIDENCE/CP25_V3_NAME_LOOKUP.json, EVIDENCE/CP25_V3_NAME_LOOKUP.md, CP25_PATCH_NOTES.md
- CLAUDE.md (stage-close order; Next stages: CP25 removed, v3 approval + 8-name supplement + README docs follow-ups added)
- Re-pinned PHASE8_R02_FILE_MANIFEST.json; PASTE_ME.md (AUTO via builder), VALIDATION_RESULTS.json (runner outputs)
