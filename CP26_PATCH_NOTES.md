# CP26 — PAB v3 deck file + Oracle supplement as second deck target (2026-10-20)

No kernel behaviour changes. No frozen file edited. Old baseline stays the only gated deck. No cards certified.

## Summary
- Input decks/PAB_V3_ARCHIDEKT_EXPORT.csv sha256 b3db879a…b104 matches; names, quantities and land flags equal EVIDENCE/CP25_V3_NAME_LOOKUP.json.
- decks/PAB_V3.json: Savra + 86 mainboard entries; 100 cards, 34 lands, 87 distinct names (asserted at build and in the new test).
- decks/PAB_V3_ORACLE_SUPPLEMENT.json: 8 records (Sol Ring, Arcane Signet, Phyrexian Altar from S12 evidence; High Market, Verdant Catacombs from S14 evidence; Command Tower, Altar of Dementia, Ashnod's Altar from the export, cost split and braced). 0 unresolved v3 names.
- Export vs evidence mismatches recorded, not resolved: High Market oracle text (newline vs space; equal after whitespace normalization); Verdant Catacombs scryfall_id (different printing).
- Registry: summary.pab_v3_deck_target derived from decks/PAB_V3.json; 19 added cards UNMODELED, 20 old-baseline-only cards (19 + Lesson); deck/supplement sha256s; gated false.
- Old-baseline-only contracts: C62, C63, C64, C82, C85, C86, C94. Rule: user-designated five + subject cards all absent from v3 (subject = assert_card_refused() argument in C80–C94, else deck-card literals in the class). C93 is Grist (in v3), not marked.
- New test file tests/test_pab_v3_deck_cp26.py (5 tests); REFERENCE_TEST_COUNT 838 → 843; release-gate expectation (843, 843).
- CLAUDE.md: decks/ in Layout; v3 in the repo; test count 843 at CP26; CP26 and the CP25 lines removed from Next stages; CP27 added above the ledger. PASTE_ME MANUAL: two lines updated.
- Follow-up: the literal subject rule counts fixture helpers; 16 contracts reference an old-baseline-only card but are not marked (listed in CLAUDE.md).
- Follow-up: the oracle_cr_authenticated line cited as run_validation.py:239 is now :246 (one per-file count line added above it).

## Method
Scratch scripts outside the repo built both deck files and derived the contract card sets (AST walk over the six contract test
files). The export's oracle text field ends at the last double quote; the mana cost after it is split off. Archidekt costs
carry no braces; simple costs were braced ({2}, {3}; Command Tower none) and the raw string kept as `mana_cost_export_raw`.

## Files
- New: decks/PAB_V3_ARCHIDEKT_EXPORT.csv (user input), decks/PAB_V3.json, decks/PAB_V3_ORACLE_SUPPLEMENT.json, tests/test_pab_v3_deck_cp26.py, CP26_PATCH_NOTES.md
- build_registry.py (pab_v3_deck_target), PABTRV3_CARD_COVERAGE.json (regenerated)
- run_validation.py (REFERENCE_TEST_COUNT, per-file count), release_gate_tests/test_r02_release_gate.py:159
- CONTRACTS_C41_C94_STATUS.md (CP26 section), CLAUDE.md, PASTE_ME.md (MANUAL two lines; AUTO via builder)
- Re-pinned PHASE8_R02_FILE_MANIFEST.json; VALIDATION_RESULTS.json (runner output)
