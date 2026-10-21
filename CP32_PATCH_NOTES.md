# CP32 — determinism soak recorded as evidence (2026-10-21)

Applied by night\CP32_apply.py (deterministic; no Claude session). No kernel, test or doc change outside EVIDENCE.

## Summary
- 500-seed determinism soak of rp-CP31d (`d56670a`) on Codie: no failing test under any seed, one distinct result,
  identical to the committed VALIDATION_RESULTS.json; mean 44.9 s per seed.
- Evidence: EVIDENCE/CP32_DETERMINISM_SOAK.md plus REPORT.txt and summary.csv (normalised to UTF-8 without BOM, LF).
- Limits recorded: only the hash seed varies; covers what the gate covers.
- The 2026-10-20 run on faulty RAM is recorded as void, not used as evidence.
- Follow-ups: none from this stage.
