# CP11 — S20 Registry Verification (A-S20-08)
- Scope: read-only kernel/registry/generator; audited 88 names using runtime Python AST exact-name matches plus `tests/test_*.py` source grep.
- Counts: SUPPORTED 86; WEAK 1; UNSUPPORTED 0; OVERCLAIM 0; UNDERCLAIM 1.
- `EVIDENCE/CP11_REGISTRY_AUDIT.json`: one record per name, registry modeled/unmodeled claims, file:line code evidence, test filenames, verdict.
- `EVIDENCE/CP11_REGISTRY_AUDIT.md`: verdict counts, discrepancy evidence, approval-only registry/test proposals.
- Top finding: Infuse with Vitality deathtouch is implemented and combat-tested in CP03, contradicting S20 `not_modeled` note (UNDERCLAIM).
- WEAK: Darkbore Pathway // Slitherbore Pathway has PATHWAY-alias tests but no full card-name literal in `tests/` (strict grep only).
- Docs only: CLAUDE.md gate-bookkeeping rule; ISSUE_LEDGER_CP06.json A-S20-12 and A-S20-13 status REPAIRED.
- No cards certified; this is name/evidence verification, not proof of full rules coverage. Re-pin then run single gate; commit/tag at CP11.
