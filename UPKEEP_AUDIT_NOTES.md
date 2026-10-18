# Upkeep / trigger audit notes — 2026-10-18 (read-only)

Deliverables: `tests/test_upkeep_trigger_audit.py` (14 fixtures, 1 expected failure = R49), `EVIDENCE/CR_20260619_EVIDENCE.json` (official CR text for 21 rules), `EVIDENCE/PROPOSED_CONTRACTS_C95_C99.json`, `PHASE_CLOCK_DEPENDENCY_MAP.md`. Reference fixtures: 434.

Findings: R49 (R47's source-left branch contradicts CR 608.2h LKI; fix unapproved), R50 (no active player: "each upkeep"/"your end step" scoping is caller discipline), R51 (mana never empties, CR 106.4). R48 confirmed against CR 704.5f/704.3. R01 text re-confirmed by two web sources; "each upkeep" wording noted.

No engine change. Phase clock: design only, four stages, each needing authorization.
