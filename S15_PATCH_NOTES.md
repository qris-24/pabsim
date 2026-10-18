# S15 — the nine interaction spells (2026-10-18)

Kernel `…+S14+S15`. New layer `pab_cast_s15.py` (`InteractionSpellsMixin`, above `RemainingLandsMixin`; PhysicalZoneGame only). 703 reference fixtures (690 + 13). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## What was built
`cast_from_hand()` for Abrupt Decay, Assassin's Trophy, Witherbloom Charm, Golgari Charm, Heroic Intervention, Infuse with Vitality, Grisly Salvage, Rise of the Witch-king, Witherbloom Command (`EVIDENCE/S15_SPELL_EVIDENCE.json`; the module docstring gives each spell's modeled text). Targets are checked at cast and again at resolution (CR 608.2b); a spell whose targets all left fizzles. New general machinery:
- until-end-of-turn P/T changes (`eot_pt`) for any creature, included in the S3 toughness SBA, which now also kills opponents' creatures (routed to the S8 death path);
- hexproof (`hexproof_eot`): S11's scripted opponent actions skip hexproof permanents (hexproof does not stop the controller's own spells);
- regeneration shields (CR 701.15): the next `destroy()` this turn taps the creature instead;
- Infuse with Vitality's return-when-it-dies as a trigger after the death triggers (the frozen linked reanimation, tapped);
- `destroy()` on an opponent's creature goes through the S8 death path;
- every until-end-of-turn state, including the frozen `indestructible_until_eot`, is cleared at EVERY cleanup step (CR 514.2) — the S2 `reset_turn` ran only at the controller's cleanup, which would have kept an instant cast on an opponent's turn in force too long.
Opponent bodies may now declare `mana_value` (S8 `declare_opponent_board`), which the MV-bounded removal checks.
Driver `pab_cast_s15.run_turns_casting()` with fixed policies (Decay/Trophy on the strongest opposing creature; Charm mode 2; Golgari Charm −1/−1 only when it kills more opposing than own creatures; Command modes 4+1 on seat 1; Infuse on Savra; Rise with a token; Heroic Intervention never — there is no threat model to react to).

After S15: 65/65 nonland cards fail-closed count is 1 — Grist, the Hunger Tide (recorded in the evidence, not modeled: a planeswalker with loyalty abilities and a type-changing static needs its own stage). All 34 lands playable. Opponents still never decide.

## Found while building
- The fixture `add(SAVRA)` body is 1/1 (the frozen `add()` defaults), not the printed 2/2; the S10 cast path uses the printed body. Tests that care about Savra's toughness must cast her.
- Milled creature cards (Grisly Salvage, Takenuma, Witherbloom Command) have no event-kernel LKI and are therefore not Unearth / Phyrexian Reclamation targets — a pre-existing bridge limitation (the frozen `_grave_target` reads the event graveyard list), documented, not fixed.

## Not modeled
Grist; deathtouch (no combat); opponents' basic-land search (Trophy) and mills (Command); "can't be countered" (no counterspells); regeneration's remove-from-combat; the choice to leave a creature un-regenerated.

## Earlier-stage tests re-scoped (R54-style, not frozen)
The S6 fail-closed sweep now skips `S15_NAMES`. `tests/test_opponents_s8.py::test_counters_count_toward_the_policy` gave an opposing 2/2 two −1/−1 counters to make it the lowest-power edict choice; with the SBA now applying to opponents' creatures that creature dies to the SBA first, so the test uses one counter (1/1, still chosen by the tie-break).
