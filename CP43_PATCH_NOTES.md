# CP43 — Stage B ledger 1: A-S20-05 menace blocks, keyword lists from card data (2026-10-21)

Kernel stage, applied by night\CP43_apply.py (deterministic; built and gated in a sandbox clone of rp-CP42). No frozen file edited. User decision (2026-10-21): both items; one existing expectation moves (approved): tests/test_combat_s17.py test_all_policy_blocks_biggest_menace_needs_two_deathtouch_kills (before-copy EVIDENCE/CP43_SUPERSEDED/test_combat_s17_menace_pre_cp43.py).

## Summary
- A-S20-05 (pab_combat_s17.py _declare_blocks): under block_policy 'all' a blocker takes a menace attacker when another untapped blocker of the seat is still to come, which then joins it (CR 702.110b). Before, a menace attacker was never blocked. check_invariants_s17 refuses a lone blocker on a menace attacker.
- Moved expectation: Bear and Wall now double-block the 3/1 menace deathtouch Pest (was: both on Savra); Savra deals 2, the Pest kills Bear and dies (was: Pest unblocked for 3, Savra and Bear trade).
- Keywords (open queue): new pab_keywords_cp43.py reads Flying, Menace, Deathtouch, Haste (Scryfall keywords) and printed "This creature can't block." from decks/CARDSOURCE_BG_COMMANDER_20261021.json for the old-baseline creatures; pab_combat_s17.py's five name sets come from it (same contents as the hand-written lists). A deck card missing from the card data raises.
- tests/test_auditfix_cp37.py: the keyword test also pins the five sets as literals (its card-data comparison is circular now); values unchanged.
- tests/test_auditfix_cp43.py: 9 tests (menace double block, lone blocker never on menace, intrinsic menace, invariant, whole games with double blocks; keyword sets, reader rules, data-driven and fail-closed reader).
- Tests: 927 reference tests (was 918); release gate 29/29. KERNEL_VERSION/PROMOTED gain CP43.
- CLAUDE.md: open queue drops A-S20-05 and the keyword-list item; Next stages ledger now: auditor constant-resolution fix, A-S20-09.
- Follow-ups: none.
