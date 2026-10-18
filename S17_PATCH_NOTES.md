# S17 — combat: the controller attacks (2026-10-18)

Kernel `…+S16+S17`. New layer `pab_combat_s17.py` (`CombatMixin`, above `GristMixin`; PhysicalZoneGame only; constructor option `block_policy='none'|'all'`). 719 reference fixtures (711 + 8). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## What was built
- `declare_attackers([(uid, seat), …])` in the controller's declare-attackers step: untapped creatures controlled since the turn began (`entered_turn` recorded by `add()`/`make_tokens()`; Yahenni has haste), against seats in the game; attacking taps; the frozen `attack_with()` enqueues the Moseo-Pest and Teacher's Pest attack triggers.
- Blocks at the declare-blockers step by a fixed policy: 'none', or 'all' — each defending creature blocks the highest-power attacker aimed at its seat that it may legally block (menace from Blight Mound on attacking Pests needs two blockers).
- Combat damage simultaneously (CR 510.2): unblocked attackers hit the defending player (Feral Appetite / Blight Mound +1/+0 for attacking Pests, counters and until-end-of-turn changes counted); blocked creatures damage each other (all damage to the first blocker — documented simplification); deathtouch (Poison-Tip Archer, South Wind Avatar, Feral Appetite's Pests) makes any damage lethal; damage is marked, the S3 state-based loop kills lethally damaged creatures with look-back (CR 704.5g), and damage wears off at cleanup.
- Commander damage from Savra per seat; 21 or more → that seat loses at the next SBA check (CR 903.10a); opponents' life loss feeds the S8 seat removal.
- Driver `pab_combat_s17.run_turns_full()`: the S15 driver plus combat each controller turn (fixed attack policy: everything legal attacks the lowest-life opponent; Savra stays home against untapped blockers under 'all'). 8-turn ledgers show the first games where opponents' life actually falls.

## Found while building
Fixture bodies added with the frozen `add()` are 1/1 regardless of the printed card (its defaults). Combat tests that care about printed P/T must cast the creature. This is the same finding as S15's Savra note, now general.

## Not modeled
Opponents attacking; first/double strike, trample; flying/reach on opponents' side; damage-assignment order among several blockers; combat tricks after blocks; regeneration's remove-from-combat; lifelink (none in the deck).
