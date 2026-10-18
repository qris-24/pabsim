# S18 — policy opponents (2026-10-18)

Kernel `…+S17+S18`. New layer `pab_policy_s18.py` (`PolicyOpponentsMixin`, above `CombatMixin`; PhysicalZoneGame only). 728 reference fixtures (719 + 9). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## What was built
- `set_opponent_policy(seat, {...})` at game start: fixed, documented decision rules evaluated at that seat's precombat main — wipe when the controller controls ≥ `wipe_at` creatures; single-target removal (`destroy_commander` while Savra is on the battlefield, else `destroy_creature` on the best nontoken creature with power ≥ `removal_min_power`; `exile_instead` uses exile); graveyard exile at ≥ `graveyard_hate_at` cards; an edict while the controller has a creature. One action per seat per turn in that order, each with a budget, each traced `('policy_action', seat, turn, kind, reason)` and run through the S11 primitives (hexproof respected: a protected Savra keeps the budget unspent).
- Opponents untap their permanents on their untap step (CR 502.3; S4 only untapped the controller) and, with `attack: 'all'`, attack the controller with every creature controlled since their turn began. The controller blocks by the game's `block_policy` ('all': each untapped non-Savra creature blocks the highest-power attacker). Damage to the controller goes to `life[0]`; the frozen `resolve()` adjudicates the loss — the kernel can now lose a game.
- `run_game(g, max_turns)`: whole games under the S17 driver, ending in 'lost' | 'won' | 'timeout'.

## R55 — found by the first whole-game runs, fixed here (frozen file untouched)
The frozen bridge's `_return_creature_from_graveyard` runs the engine's `add()` before dropping the graveyard link, so returning a creature whose `add()` makes tokens (Moseo, Prosperous Innkeeper) tripped `assert_bridge_integrity` ("Linked graveyard LKI missing") from inside `make_tokens`. S18 overrides it with the same steps in a safe order (drop the link, engine return, move the card, relink; trace `r55_safe_order`). Unearth on Moseo is the regression test.

## Observed, not a claim about the deck
16 seeds × 2 controller block policies against three opponents with 2 bodies each, all attacking every turn and carrying small removal budgets: every game is lost by the controller around turn 13 (the controller never blocks under 'none' and never races 15 damage a round). This is a property of that opponent configuration, not of the deck; no opponent configuration has been calibrated against anything real.

## Not modeled
Opponents attacking each other, opponents' responses or instant-speed play, opponents casting anything, threat assessment beyond these rules, a controller who stops taking turns after losing (the clock keeps running; `run_game` stops at the next 4-turn boundary).
