# S10 — Savra from the command zone (2026-10-18)

Kernel `…+S9+S10`. New layer `pab_commander_s10.py` (`CommanderMixin`, above `FixerLandsMixin`; PhysicalZoneGame only). 650 reference fixtures (640 + 10). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## What was built
- `cast_commander()`: Savra's physical card from `zones['command']`; S6 creature timing; cost {2}{B}{G} plus {2} per previous cast from the command zone (commander tax, `commander_casts`); resolution command zone → battlefield through the frozen `add(SAVRA)` + linked path (ETB behaviour is the frozen kernel's). `command_stack` is the S6-style ledger while she is on the stack; `assert_bridge_integrity` checks it.
- Death (CR 903.9a, 2020 wording): a linked Savra dies through the frozen `_leave()` — every dies trigger and her own look-back sacrifice triggers fire unchanged — and at the next state-based-action check she goes to the command zone (fixed policy: always; traced `commander_to_command_zone`; graveyard link and graveyard LKI removed, so she is no longer a reanimation target; `commander_deaths`). The SBA runs before the pending triggers resolve, as in paper. The same SBA would apply to exile.
- The fixture `add(SAVRA)` path (event body without a card) is untouched and still used by every frozen test.
- Driver `pab_commander_s10.run_turns_casting()`: Savra cast from the command zone whenever cost + tax is payable, before the hand pass; `pab_lands_s9.tap_lands_policy()` gained an optional `extra` colour need (backward compatible).

## Found while building
- The S5 invariant "Savra neither in command zone nor on battlefield" was too strong once she can die: she legitimately sits in the graveyard between a sacrifice (e.g. as Village Rites' cost) and the next SBA check. `pab_turn_loop.check_invariants` now requires her in exactly one of command / battlefield / graveyard / exile; `check_invariants_s10` additionally requires graveyard/exile only while something is pending. All S5 tests pass unchanged.

## Evidence
`EVIDENCE/S10_COMMANDER_EVIDENCE.json`: Savra's printed cost/P/T from the same source as S7/S9; CR 903.9a/903.9b from a secondary transcription (the official 20260619 PDF fetch truncated before section 903); 903.8 commander tax from general knowledge. Flagged: 903.x not yet in `EVIDENCE/CR_20260619_EVIDENCE.json`.

## Not modeled
Opponents' removal of Savra (next stage), protection, commander damage, choosing to leave her in the graveyard, hand/library replacement (903.9b: nothing bounces or tucks yet).
