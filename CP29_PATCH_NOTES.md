# CP29 — oracle_referenced requires every subject card covered (2026-10-20)

## Summary
- oracle_referenced: 57 before -> 51 after (6 flips). C45: subject Skullclamp has no Oracle text. C64, C68, C69, C79, C87:
  `subjects: []` (card driven via method/constant, or a stand-in; no literal in the class). C76, C96 stay False.
- Subject rule: a card whose own behaviour the class's tests assert (not a fixture helper or SUBSTITUTIONS stand-in) and
  that is an exact string literal in the contract class; basis per entry in `subject_basis`.
- oracle_reference_check(): referenced = refs and subjects non-empty, every subject in the excerpt with a matching ref,
  every ref matches; new per-contract `oracle_subjects_missing`. Fail-closed; `contracts_ok` does not read it.
- Run stopped at its stop condition: tests/test_oracle_refs_cp28.py:30 encoded the CP28 rule. User approved changing it
  to the subject rule; user accepted the 6 flips as False for now.
- New tests/test_oracle_subjects_cp29.py (7). Reference test count 850 -> 857 (run_validation.py, release gate, registry).
- oracle_cr_authenticated False for all 59; 0 cards certified; no STATUS values changed.
- Follow-ups: Oracle sourcing for C45, C76; constant-resolved subjects (C68); method-driven subjects (C64, C69).

## Files
- CONTRACT_ORACLE_REFS_CP28.json: `subjects`, `subject_basis` per contract (refs and notes unchanged).
- run_validation.py: subject coverage, `oracle_subjects_missing`; REFERENCE_TEST_COUNT 857; per-file count (7).
- release_gate_tests/test_r02_release_gate.py: expected (857, 857).
- tests/test_oracle_subjects_cp29.py: new. tests/test_oracle_refs_cp28.py: line 30 expectation (approved).
- PABTRV3_CARD_COVERAGE.json: build_registry.py output. CLAUDE.md: Next stages follow-ups.
