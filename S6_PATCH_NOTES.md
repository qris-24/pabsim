# S6 — casting from the physical hand (Task 1a, 2026-10-18)

## Scope
`pab_cast_s6.py` (new layer above `pab_clock_s4.TurnBasedActionsMixin`), promoted through `pab_kernel.py` as `PhysicalZoneGame(CastMixin, …)`. `Game` (event-only) is unchanged. No frozen file edited. Deck, Lesson, Phase 9, sweeps, rankings: locked.

## API
`PhysicalZoneGame.cast_from_hand(physical_uid, *, sacrifice_uid=None, selected_land_uid=None, main_phase=None, stack_empty=None, has_priority=None)` for exactly: Village Rites, Deadly Dispute, Tend the Pests, Nature's Lore, Sakura-Tribe Elder. Any other name, a token, or the Lesson → `BridgeError` (fail closed).

| Requirement (handoff §5) | Implementation |
|---|---|
| (1) card in `zones['hand']` | `zones._require_in_zone(uid,'hand')`; a card already on the S6 stack ledger is refused |
| (2) clock-derived timing | engaged clock: sorcery/creature = own turn ∧ main step ∧ `not pending`; instant = step ∉ {untap, cleanup}. kw timing args are refused once engaged; before engagement they are the fixture shortcut (defaults: main phase, stack = `not pending`, priority) |
| (3) real mana from the shared pool | preflight on counts, then `pay_mana()` (v0.8 reshares the pool reference) |
| (4) card leaves hand on resolution | instant/sorcery → `zones.move(uid,'graveyard')` (608.2n); creature → `zones.move(uid,'battlefield',controller=0)` + `add()` + `linked_battlefield` (608.3) |
| (5) existing event-kernel resolution | effects use `_fixture_draw`, `make_tokens`, `_search_basic_at_resolution`, `add`; sacrifice cost via `sacrifice()` so Savra/death triggers are the frozen kernel's; `sedgemoor_spell_cast_or_copied()` after the cast event for instants/sorceries only |

Refusals are preflighted: a refused cast leaves hand, pool, permanents and trace unchanged (asserted in every refusal test).

Stack ledger: `pab_zones` (frozen) has no stack zone. While a spell is on the stack its card stays in `zones['hand']` and is recorded in `g.stack_cards`. `check_invariants_s6()` = `pab_turn_loop.check_invariants()` + ledger cards are in hand + no ledger entry without something pending. `assert_bridge_integrity()` also checks the ledger.

Costs (black, green, generic): Village Rites (1,0,0); Deadly Dispute (1,0,1); Tend the Pests (1,1,0); Nature's Lore (0,1,1); Sakura-Tribe Elder (0,1,1), 1/1, MV 2, G. Source: `EVIDENCE/S6_CARD_EVIDENCE.json` (scryfall.com card pages, fetched 2026-10-18; api.scryfall.com unreachable).

## Driver
`run_turns_casting(g, turns)`: S5-style whole turns; in each controller precombat main: land play (S4), tap linked lands (Command Tower picks G when a green spell in hand needs it), `cast_when_able()` (fodder = a token or a linked non-Savra creature; Nature's Lore selects the first Forest in library). `opening_hand_shuffled()` shuffles first (CR 103.3), see R53.

## Tests — `tests/test_cast_s6.py`, 33
Per spell: 1 positive + refusals for wrong zone (library / graveyard / exile / on-stack), wrong step (untap, cleanup, upkeep, opponent's main, combat, nonempty stack), insufficient mana; plus illegal additional-cost permanents. Fail-closed sweep over every other deck name. kw timing refused once engaged. Frozen `cast_pab_spell` path unchanged under the S6 kernel. Turn loop: 8 seeds × 8 turns with `check_invariants_s6` after every boundary and action; every `physical_cast` trace entry accounted for by a card in graveyard/battlefield; seed 7 casts Nature's Lore on turn 5 and fetches a Forest. Reference count 492 → 525.

## Findings (not fixed; approval needed)
- **R52** — `pab_focus_engine_v07.cast_pab_spell` charges Village Rites {1}{B}; printed cost is {B}. Frozen `test_91` (tests/test_v04_cost_and_copy.py) pins the wrong cost on the frozen path. S6 charges {B}. Options: (a) leave the frozen path as a documented discrepancy; (b) supersede `test_91` via `EXPECTED_LEGACY_FAILURES` with an R52 correction layer, as done for R01 (112/113).
- **R53** — `pab_turn_loop.opening_hand()` (S5) never calls `shuffle_library()`: every S5 seed draws the frozen decklist order, so S5's "8 seeds" are one game; the seed only affects later searches. CR 103.3. S6 adds `opening_hand_shuffled()`; proposed fix: shuffle inside S5's `opening_hand()` (S5 test counts unaffected; only the land-play/cast outcomes per seed change).
- Observation: with only Forest/Swamp/Command Tower playable (16 of 34 lands), the driver cast 2 spells across 40 seeds × 16 turns. Casting frequency is a land-coverage artifact (step 3b), not a deck property.

## Not modeled
Stack as a zone; opponents' priority; counterspells and copies; targets (none of the five has one); X/alternative costs; cost changes; nonbasic Forests for Nature's Lore (bridge subset); any other card from hand (step 1b).

## Gate
`python run_validation.py` → exit 0 (525 fixtures, 59 contracts, 18 gate tests; frozen replays 147/149 + superseded {112,113}, 52/52, 54/54, 38/38). Restore point `rp-S6`.
