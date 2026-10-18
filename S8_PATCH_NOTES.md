# S8 — opponents as life totals plus a fixed scripted board (Task 2b, 2026-10-18)

Kernel `…+S7+S8`. New layer `pab_opponents_s8.py` (`OpponentsMixin`, above `CreatureCastMixin`; PhysicalZoneGame only). 622 reference fixtures (601 + 21). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## What was built
- `declare_opponent_board(seat, bodies)` at game start (clock not engaged): generic creature bodies (name, power, toughness, colours) become ordinary controller 1–3 permanents through the frozen `add()`. No libraries, hands, mana, spells, attacks or decisions; opponents never act. The frozen Essence Warden 'another creature enters' trigger already sees them.
- Real edicts (CR 701.19b): the frozen Savra-black and Grave Pact triggers are wrapped at enqueue time; when the frozen action records an `edict_opportunity` (Savra only if the 2 life was actually paid), each opponent still in the game sacrifices one creature by a fixed, documented stand-in for "their choice" — lowest power (counters included), then lowest toughness, then lowest uid — or is traced `edict_no_creature`. `opponent_sacrifices` now counts only observed sacrifices; `edict_opportunities` keeps the frozen meaning; `edicts_resolved` counts resolutions.
- `_opponent_creature_dies(uid, cause)`: the permanent leaves and exactly the five triggers the frozen exogenous path (`Game.opposing_creature_dies`) enqueues — Deathgreeter, Poison-Tip Archer, Blood Artist, Yahenni, Sangromancer — are enqueued with the frozen labels (parity test). Opponents keep no graveyard.
- Leaving the game (CR 704.5a, 800.4a, 800.4g): at every SBA check a seat at ≤ 0 life leaves; its permanents leave without dying (no triggers); `LossAwareClock` gives it no further turns (a turn already under way continues). All three gone ⇒ `game_won` recorded (CR 104.2a); nothing stops.
- Blood Artist's fixed target is the lowest-numbered opponent still in the game (the controller if none); drains apply only to seats still in the game. With nobody lost, both behave exactly as the frozen fixtures.

## Evidence
CR 800.4 sub-rules were read on 2026-10-18 from a secondary transcription (cardboard.readthedocs.io, Multiplayer Rules); `EVIDENCE/CR_20260619_EVIDENCE.json` does not carry 104/704/800 text. Treat the 800.4 citations as secondary until the official PDF text is added to the evidence file.

## Not modeled
Opponents' spells, attacks, blocks, removal, board wipes, graveyard hate, hands, libraries, mana, commander damage, their own death triggers, and any choice beyond the fixed edict policy. Savra removal/recast is still not modeled. The `Game` (event-only) class is unchanged; only `PhysicalZoneGame` carries S8.

## Observed, not a claim about the deck
Under the 8-seed 8-turn driver with 3-creature boards no edict fires (the driver never sacrifices a black creature); edicts are exercised by direct tests and by `cast_when_able` with Village Rites in hand.
