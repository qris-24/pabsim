# S14 — the nine remaining nonbasic lands (2026-10-18)

Kernel `…+S13+S14`. New layer `pab_lands_s14.py` (`RemainingLandsMixin`, above `SpellCastMixin`; PhysicalZoneGame only). 690 reference fixtures (678 + 12). No frozen file edited; frozen `SUPPORTED_LAND_MANA` untouched. Deck, Lesson, Phase 9, sweeps and rankings unchanged. All 34 lands are now playable on the bridge.

## What was built
Playing and tapping reuse the S9 procedure through two small hooks added to `pab_lands_s9.py` (`_land_spec`, `_has_land_spec`; the S9 driver policies take an optional land table). Abilities (`EVIDENCE/S14_LAND_EVIDENCE.json`):
- Phyrexian Tower `tower_sacrifice`: {T}, sacrifice a creature (frozen `sacrifice()`, so Savra/death triggers enqueue) → {B}{B} at once, no stack (mana ability, CR 605.3b).
- High Market `high_market` / Grim Backwoods `grim_backwoods`: sacrifice (and {2}{B}{G}) paid as costs, gain 1 / draw 1 on resolution.
- Castle Locthwain: enters tapped unless a Swamp-typed land is controlled; `castle_locthwain` draws first, then loses life equal to the resulting hand size; an empty library records a failed draw.
- Verdant Catacombs `verdant_catacombs`: {T}, pay 1 life, sacrifice (land to graveyard, no death trigger); the selected library card with the Swamp or Forest TYPE enters by its own rule (Tomb may pay 2 life, Mortuary tapped + surveil), then shuffle; no mana ability.
- Takenuma `channel_takenuma`: from hand, {3}{B} less {1} per legendary creature you control (floor 0), discard as the cost; mill three, return a creature card from the graveyard to hand (choice at resolution, pre-committable).
- Boseiju: fully playable; its channel is refused because no opponent controls an artifact, enchantment or nonbasic land in this kernel (no legal target, CR 602.2b).
- Geier Reach `geier_reach` / Mikokoro `mikokoro`: {2}, {T}: the controller draws (and discards the chosen card); opponents have no hands, traced unmodeled.
Driver `pab_lands_s14.run_turns_casting()`: all 34 lands playable in hand order (Verdant played, never tapped); activated land abilities are not driven.

## Contracts
C70, C71, C72, C74 and C77 move to EXECUTED; C75 and C76 to PARTIAL_EXECUTED (Boseiju's channel and opponents' draws are the unexecuted halves) in `tests/test_c65_c77_contracts.py` (counts unchanged). CONTRACTS_C41_C94_STATUS.md and C65_C77_EXECUTION_NOTES.md updated.

## Not modeled
Opponents' side of the symmetric lands, Boseiju's channel, planeswalker cards for Takenuma, Nature's Lore for nonbasic Forests (the frozen bridge's basic-only subset; S14's fetch logic could serve it next).

## One S9 test re-scoped (R54-style, not frozen)
`tests/test_lands_s9.py::test_other_nonbasics_still_fail_closed_and_frozen_zone_path_untouched` pinned the nine lands as refused on the bridge; it now asserts that the frozen zones path still refuses them (unchanged) while the bridge plays them. `build_manifest.py`'s informational `patches`/`unique_fixture_tests` fields, which the runner does not verify, had not been advanced at S13; corrected here.
