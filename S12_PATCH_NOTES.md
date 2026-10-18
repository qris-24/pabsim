# S12 — noncreature permanents from the physical hand (2026-10-18)

Kernel `…+S11+S12`. New layer `pab_cast_s12.py` (`PermanentCastMixin`, above `InteractionMixin`; PhysicalZoneGame only). 668 reference fixtures (662 + 6). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## What was built
`cast_from_hand()` for the 15 names in `pab_focus_engine.NONCREATURE` — Agent of the Iron Throne, Arcane Signet, Bastion of Remembrance, Blight Mound, Cauldron of Essence, Dark Prophecy, Feral Appetite, Golgari Signet, Grave Pact, Moldervine Reclamation, Phyrexian Altar, Phyrexian Reclamation, Skullclamp, Sol Ring, The Hunger Tide Rises — with printed costs (`EVIDENCE/S12_PERMANENT_EVIDENCE.json`), sorcery-speed timing, no Magecraft, resolution hand → battlefield through the frozen `add()` + linked path (Bastion's token and the Saga's chapter I are the frozen kernel's; type flags from the frozen NONCREATURE/ARTIFACT tables). A board assembled by casting behaves identically to the fixture board (tested: same life, draws and edict count after a Pest sacrifice). Driver `pab_cast_s12.run_turns_casting()` adds a permanent pass after the S7 pass (hand order).

After S12 the physical hand can cast: 5 S6 spells, 28 creatures (S7), Savra from the command zone (S10), 15 permanents. Still fail closed from hand: Diabolic Intent, Immoral Bargain, Plumb the Forbidden, Pest Infestation, Unearth, Hunt for Specimens, Demonic Tutor (frozen fixture methods exist, not yet wired to the physical card), Grist, the Hunger Tide, Witherbloom Charm, Witherbloom Command, Golgari Charm, Grisly Salvage, Heroic Intervention, Infuse with Vitality, Rise of the Witch-king, Abrupt Decay, Assassin's Trophy (no kernel behaviour yet); 9 nonbasic lands.

## Not modeled
Equip from the cast path (Skullclamp enters unattached; equip is the frozen activation), the Saga's later chapters beyond the frozen kernel's handling, any of the spells listed above.

## Two earlier-stage fail-closed tests re-scoped (R54-style, not frozen)
`tests/test_cast_s6.py::FailClosed` and `tests/test_cast_s7.py::test_savra_lands_and_lesson_still_fail_closed` pinned Grave Pact / Sol Ring (and every non-S7 name) as refused; S12 makes the 15 permanents castable by design, so the S6 sweep now also skips `S12_NAMES` and the S7 probe uses Demonic Tutor and Abrupt Decay as its still-refused examples. Counts unchanged. The first gate run after S12 was committed red because of these two; the tag was moved after the fix.
