# CP02 — explicitly approved repairs after S20 independent audit

Date: 2026-10-18. Authorization: user replied "approved" to the previously stated two
scoped repairs (A-S20-01 blocked attacker and A-S20-02 terminal advancement).

## Scope and source provenance
- Baseline: `rp-S20`; original archive and `SOURCE_SNAPSHOT` left unchanged.
- New versioned repair implementation: `pab_auditfix_cp02.py`.
- Entry integration: `pab_kernel.py` selects `AuditFixCP02Mixin` and marks `+CP02`;
  `pab_policy_s18.py:run_game` delegates to `run_game_terminal` to preserve caller imports.
- New tests: `tests/test_auditfix_cp02.py` (15 independent fixtures).
- Release accounting updated to 751 distinct tests (736 inherited + 15 new),
  with 18 release-gate tests retained. Build-time manifest regenerated.

## A-S20-01
Keep original blocked status across removal of some or all blockers. A previously
blocked attacker without trample does not deal damage to the defending player
if the final blocker leaves before the combat-damage step. Both controller and
opponent attacking cases addressed. The S17/S18 existing simplifications on
multiple blockers, unimplemented trample/flying/first strike/etc remain open.
No general damage-assignment or comprehensive combat validation claim.

## A-S20-02
New mid-batch terminal-aware loop, preserving completed 6-column controller-turn
ledger rows. Checks terminal state immediately after `advance_step`, after resolve,
and between controller policy actions. `pab_policy_s18.run_game` is adapted to
invoke it; opponents may end the game on their own combat step without subsequent
`step_begin` events. Stopping at an exact max-turn boundary also prevents batching
overshoot. No opponent calibration or performance claim.

## Exclusions
No patch for A-S20-03 through A-S20-10, no S21, no Phase 9, no optimizer,
no changes to the accepted commander/mainboard/Lesson, no frozen tests modified.
Existing card-completeness count remains zero.
