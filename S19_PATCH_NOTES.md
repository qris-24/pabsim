# S19 — integrated whole-game validation (2026-10-18)

Kernel `…+S18+S19` (S19 is a validation tool over the kernel, `pab_validation_s19.py`, not a layer). 732 reference fixtures (728 + 4). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged. No deck score is produced or implied.

## What was built
`validate_games(seeds, config)` runs whole games under the S17/S18 driver (configurable opponent boards, policies, the controller's block policy, a turn cap) and checks what a correct kernel must satisfy regardless of the deck:
- reproducibility: the same seed and configuration give a byte-identical trace and life totals;
- clock legality: every `step_begin` follows the CR 500.1 order, seats rotate skipping those that left, a lost seat never begins a turn (the checker is tested against a doctored trace);
- life ledger: every seat's final life recomputed from the trace alone (gains, losses, payments, drains to seats in the game at the time, targeted losses, combat damage, commander-damage loss) equals the game's life vector;
- stack discipline (both ledgers empty, nothing pending), count consistency (opponent sacrifices, commander casts and returns), lost seats at ≤ 0, 101 card identities each in exactly one zone — on top of the S5–S18 invariants the driver checks at every step.
The report's `observed` block carries counts (outcome, turns, casts, lands, Savra casts/deaths, edict opportunities vs observed sacrifices, policy actions, attacks, trace length, SBA checks) and an explicit note that they are not deck scores. `write_report()` serialises it; the gate does not ship a report.

## Observed, not a claim about the deck
Default configuration (three 2-body opponents all attacking with small removal budgets): 8/8 seeds lost by the controller on turn 13. Quiet configuration (no attacks, modest budgets, controller blocks): games reach the 40-turn cap. All checks pass in both. Any claim about the deck would need an opponent configuration calibrated against something real; none has been.

## Not modeled
Opponents' decks; statistical comparison across configurations (deliberately absent until Phase 9 is authorized).
