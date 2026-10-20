# CP28 — derived `oracle_referenced` from a pinned Oracle excerpt; CR stays unauthenticated

## Summary
- `oracle_referenced` True for 57/59 contracts; `refs: []` for 2 (C96: CR-only rule, mana emptying; C76: both subject cards missing).
- Cards in neither source: 3 (Skullclamp — C45 subject, C45 references only Savra; Geier Reach Sanitarium, Mikokoro, Center of the Sea — C76).
- Decision (user): Oracle only. No CR text in the repo, so `oracle_cr_authenticated` is False for all 59.
- Decision (user): the gate reads Oracle text only from `decks/ORACLE_EXCERPT_CP28.json` (58 cards: 54 golgari_commander.json, 4 supplement).
- `run_validation.oracle_reference_check()` normalizes whitespace and curly quotes; fails closed (missing excerpt/mapping/card,
  supplement sha256 mismatch) with per-contract `oracle_ref_errors`; never raises. New top-level `contracts_oracle_referenced`.
- Gate semantics unchanged: `contracts_ok` does not read the Oracle fields; tests/test_oracle_refs_cp28.py (7 tests) enforces them.
- Reference test count 843 → 850 (run_validation.py, release gate expectation, registry `current_reference_test_count`).
- Follow-up: C51/C52 SUBSTITUTIONS say Chatterfang "-X/-X"; Oracle says "+X/-X" (wording, not changed here).
- Follow-up: source Oracle text for the 3 missing cards; CR text needed for C96 and the CR parts named in mapping notes.
- A reference is not a certification: 0 cards certified; no STATUS values changed.

## Files
- New: `build_oracle_excerpt.py`, `decks/ORACLE_EXCERPT_CP28.json`, `CONTRACT_ORACLE_REFS_CP28.json`,
  `EVIDENCE/CP28_ORACLE_EXCERPT_SUMMARY.txt`, `tests/test_oracle_refs_cp28.py`, this file.
- Changed: `run_validation.py` (contract loop + `oracle_reference_check`, counts), `release_gate_tests/test_r02_release_gate.py`
  (850/850), `PABTRV3_CARD_COVERAGE.json` (via build_registry.py), `CLAUDE.md`, manifest.

## Method
Fragments are verbatim substrings of the excerpt text, chosen from the rule text each contract class's tests exercise
(C80–C94 subject = the `assert_card_refused()` argument). Fixture stand-ins and unasserted clauses (C83 "can't be
countered", C84 opponent search, C92 repeat, C94 mode 1 on an opponent) are named in notes, not referenced.
build_oracle_excerpt.py takes golgari_commander.json first, the supplement for the rest; multi-face text is
"face name\ntext" per face joined with "\n//\n".
