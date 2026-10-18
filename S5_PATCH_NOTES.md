# Stage S5 — integrated turn loop (promoted 2026-10-18)

`pab_turn_loop.py`: `opening_hand()`, `run_turns(game, turns)`, `check_invariants(game)`. Drives a `PhysicalZoneGame` through whole four-seat turns with the S1–S4 clock using only existing capabilities: opening hand of 7, untap, draw, one supported land play per controller turn (Forest/Swamp/Command Tower), tapping linked lands in the first main phase. No casting from the physical hand (not modeled), no opponents' libraries or boards.

**Invariants checked at every step boundary and after every action:** exactly 101 card identities; every card in exactly one zone and its zone label consistent; Savra in command zone or on the battlefield; ≤ 1 land play per turn; no empty-library draw; nothing tapped outside the battlefield; bridge integrity; no life ≤ 0 without loss adjudication. A deliberate corruption (one card in two zones) is caught.

Fixtures: `tests/test_integrated_turn_loop_s5.py` (6; 8 seeds; up to 30 turns with Beledros making a Pest at every seat's upkeep). Library/hand/battlefield/graveyard always sum to 99; hand = 7 + draws − lands.

This is evidence of connected legal sequences and state conservation, not of deck performance.
