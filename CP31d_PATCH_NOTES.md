# CP31d — documentation integrity cleanup (2026-10-20)

Applied by night\CP31d_apply.py (deterministic; no Claude session). No kernel behaviour or test change.

## Summary
- Integrity review of rp-CP31 recorded in EVIDENCE/CP31d_INTEGRITY_REVIEW.md (kernel, tests, docs, gate).
- README.md: reading notice (history vs live state); duplicate "Clock S2 promoted" section removed.
- CONTRACTS_C41_C94_STATUS.md: current table generated from VALIDATION_RESULTS.json (59 contracts); old tables labelled historical (fixes C63 and the C65-C77 rows).
- ISSUE_LEDGER_CP06.json: status filled for A-S20-04/-08/-11, note on A-S20-10 fix_authorized; CP06 top-level counts labelled historical.
- validation_stdout.txt: stale Phase 8 shell capture (no script writes it) replaced by a pointer.
- PHASE_CLOCK_DEPENDENCY_MAP.md title and R47_R48_PATCH_NOTES.md upkeep line labelled historical.
- CP07_PATCH_NOTES.md: BOM and mojibake removed. pab_r01_pest_rescuer.py: Oracle "each upkeep" added to the docstring.
- CLAUDE.md: Pest Rescuer queue item closed; CP27 follow-up superseded; CP31d follow-up added.
- Follow-ups: K1-K14, G1-G4, T1-T7 and the registry summary, one stage each (see the evidence file).
- Not changed (source data): EVIDENCE/S6 Tend the Pests wording, Archidekt CSV rows 20/30, PASTE_ME South Wind Avatar line.
