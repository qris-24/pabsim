# S13 — the eight remaining frozen-behaviour spells from the physical hand (2026-10-18)

Kernel `…+S12+S13`. New layer `pab_cast_s13.py` (`SpellCastMixin`, above `PermanentCastMixin`; PhysicalZoneGame only). 678 reference fixtures (668 + 10). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## What was built
`cast_from_hand()` for Demonic Tutor, Diabolic Intent, Hunt for Specimens, Pest Summoning (Lesson, after Learn), Unearth, Plumb the Forbidden, Immoral Bargain and Pest Infestation (`EVIDENCE/S13_SPELL_EVIDENCE.json`). Each effect is the frozen kernel's procedure; S13 adds the physical card (hand, clock timing, printed cost, stack ledger, card to graveyard when the original finishes resolving) and fills two gaps the frozen kernel had left open rather than faked:
- the tutors now search the real library (`zones.resolve_demonic_tutor` / `search_library`), with the selection made at cast time (the S6 Nature's Lore convention);
- Immoral Bargain now pays its mana and destroys its targets at resolution — own creatures through `destroy()`, own artifacts/enchantments through `_destroy_supported_noncreature()`, opponents' creatures through the S8 death path — skipping targets that left (CR 608.2b) and fizzling when all have.
Learn (CR 702.139a): `learn='lesson'` (house rule `learn_sideboard_allowed=True`; the Lesson card moves outside_game → hand through the frozen bridge), `learn='discard'` with `discard_uid` (discard, draw one), or decline. Pest Summoning's hybrid pips are paid black-first from the pool (`hybrid='BB'|'BG'|'GG'` overrides). Unearth, Plumb the Forbidden and Pest Infestation wrap the frozen methods (cost, copies, targets, Magecraft are theirs) after S13's own pre-checks so a refusal mutates nothing.
Driver `pab_cast_s13.run_turns_casting()` with fixed policies (tutor: a basic while fewer than four lands, else Grave Pact, else the first creature; Hunt learns the Lesson when allowed; Unearth the highest-MV eligible card; Plumb only with two or more tokens; Infestation X from the pool, no targets; Immoral Bargain is not driven).

After S13 the physical hand can cast 56 of the 65 nonland cards plus Savra from the command zone. Still fail closed: Witherbloom Charm, Witherbloom Command, Golgari Charm, Grisly Salvage, Heroic Intervention, Infuse with Vitality, Rise of the Witch-king, Abrupt Decay, Assassin's Trophy, Grist, the Hunger Tide (no kernel behaviour yet); 9 nonbasic lands.

## Not modeled
Learn's discard-to-draw with an empty hand (refused), the Lesson outside the house rule, Plumb copies as separate stack objects (the frozen limited-stack model), opponents' noncreature permanents as targets (they have none).

## Earlier-stage probes re-scoped (R54-style, not frozen)
The S6 fail-closed sweep now also skips `S13_NAMES`; the S7 still-refused probe uses Abrupt Decay and Golgari Charm. A Lesson outside the game is refused with `BridgeError` ("Learn it first"), the type the S6/S7 probes expect. Counts unchanged.
