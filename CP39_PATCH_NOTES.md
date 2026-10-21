# CP39 — A2 Kernel 3: turn clock and validation (K3, K6, K7 + CP37/CP38 follow-ups) (2026-10-21)

Kernel repair stage, applied by night\\CP39_apply.py (deterministic; built and gated in a sandbox clone of rp-CP38; no Claude implementation session). One existing test expectation moved with user approval (tests/test_auditfix_cp04.py:26; before-copy EVIDENCE/CP39_SUPERSEDED/test_auditfix_cp04_pre_cp39.py). No frozen file changed.

## Summary
- K3: life gained this turn resets at every seat's untap step (traced life_gained_turn_reset), so an opponent's-turn gain no longer reaches your end step (Moseo).
- K6: S19 clock_legal accepts the turn number a seat that left uses up; a wrong turn number is still rejected.
- K7: resolve() at 0 or less life records lose_game once. Approved: test_auditfix_cp04.py:26 now expects 'step after terminal marker' (still detects the corrupted trace).
- CP37 follow-up: lethal-damage deaths are traced sba_lethal_damage; an SBA event names its kinds ('lethal_damage', 'zero_toughness', or both).
- CP38 follow-up: a loss mid-resolution leaves the spell on the stack; the stack invariants and S19 stacks_ok accept exactly the ledgers recorded at the loss (a later or earlier stray is still caught), and every casting driver stops after a loss.
- Policies: the tapping policy never pays its last life (Peatland skipped, Llanowar Wastes gives C); the S13 driver never casts Plumb for its last life and casts Pest Summoning only when the pool can pay it.
- S19 whole games: no errors and no failed checks (default, all-exile, wipe-heavy: seeds 0-799; all-exile with blocks: 0-299); rp-CP38 had errors in both exile mixes.
- Tests: tests/test_auditfix_cp39.py (18; 17 fail on rp-CP38); suite 918, release gate 21/21. KERNEL_VERSION/PROMOTED gain CP39.
- Follow-ups: none.
