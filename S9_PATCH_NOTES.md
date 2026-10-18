# S9 — the black-green fixer lands (Task 3b, 2026-10-18)

Kernel `…+S8+S9`. New layer `pab_lands_s9.py` (`FixerLandsMixin`, above `OpponentsMixin`; PhysicalZoneGame only). 640 reference fixtures (622 + 18). No frozen file edited; `pab_zones.SUPPORTED_LAND_MANA` untouched (the frozen zones path still fails closed for every nonbasic). Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## Scope decision
The authorized step said "the 7 fixer lands" without naming them, and no earlier record names them. S9 covers the nine nonbasic lands whose Scryfall `produced_mana` includes both B and G (EVIDENCE/S9_LAND_EVIDENCE.json): Blooming Marsh, Deathcap Glade, Woodland Cemetery, Undergrowth Stadium, Overgrown Tomb, Underground Mortuary, Darkbore Pathway // Slitherbore Pathway, Llanowar Wastes, Nurturing Peatland — a superset of any plausible seven. Playable lands: 16/34 → 25/34.

## What was built
- `play_physical_land(uid, face=None, pay_life=False, surveil_graveyard=False)`: the frozen physical land-play procedure reproduced for S9 names (hand, your main phase, empty stack, one land per turn, move, land-play count, `land_played`, `add()` + link, `physical_land_played`) plus each card's entry rule (CR text in the module docstring). Woodland Cemetery checks land *types* (basics, Overgrown Tomb, Underground Mortuary). Undergrowth Stadium counts seats still in the game (S8). Overgrown Tomb's 2 life is paid as it enters and refused if unpayable. Underground Mortuary enters tapped and its surveil 1 is a trigger whose choice is pre-committed at play time.
- Pathway: played as one face (`face='Darkbore'|'Slitherbore'`), required; the permanent keeps the full card name because the frozen bridge requires `permanent.name == physical name`, and records `face`; the mana ability follows the face (CR 712.8 compromise, documented).
- `tap_physical_land_for_mana(uid, color=...)`: duals require a colour choice; Llanowar Wastes gives {C} free or {B}/{G} with 1 damage (life loss, no prevention); Nurturing Peatland pays 1 life per tap and refuses at 0.
- Driver `pab_lands_s9.run_turns_casting()` with fixed, documented policies: Pathway face = colour the hand needs more (ties to Darkbore); Overgrown Tomb pays while life > 10; Mortuary keeps a land on top when the hand holds no land, else mills; duals give the colour the hand is short of; Wastes gives {C} unless a colour is short. Hand order, no further prioritisation.

## Evidence
Same source as S7 (user-provided Scryfall bulk export via the audit reference JSON; secondary-official; scryfall unreachable from here on 2026-10-18).

## Not modeled
Boseiju, Castle Locthwain, Geier Reach Sanitarium, Grim Backwoods, High Market, Mikokoro, Phyrexian Tower, Takenuma, Verdant Catacombs (still fail closed); Channel; Peatland's sacrifice-draw; land destruction; Nature's Lore for nonbasic Forests (frozen bridge subset unchanged); damage prevention.

## Observed, not a claim about the deck
8 seeds × 16 game turns (4 controller turns) under the S9 driver: 14 casts total (was 2 across 40 seeds × 16 turns under S6 with 16/34 lands). Casting frequency remains partly a land-coverage artifact (9 lands still unplayable) and entirely a driver-policy artifact.

## Frozen expectation moved — approval required before promotion (stop point)
Two frozen v0.8 bridge fixtures pin "fail closed" for lands S9 makes playable: `tests/test_v08_mana_tokens.py::test_274_unsupported_land_fails_closed` (Blooming Marsh) and `::test_307_unsupported_named_nonbasic_mana_does_not_fallback` (Overgrown Tomb). They are coverage pins, not rules claims. S9 supersedes them the R01/R52 way: `pab_kernel.SUPERSEDED_V08_CONTRACTS` lists the two; the runner requires the frozen v0.8 replay to fail on exactly those two (52/54) and replays a corrected full copy, `s9_tests/test_v08_mana_tokens_s9.py` (only 274 and 307 changed: positive plays with the printed entry condition), 54/54. The frozen file is untouched. Contracts C65, C66, C67, C68 and C73 moved from BLOCKED_UNSUPPORTED to EXECUTED in `tests/test_c65_c77_contracts.py` (their fail-closed probes replaced by the contract's own expectations; counts unchanged). Under the standing rule this promotion waits for explicit approval; the work is held on git branch `s9-candidate` (tag `rp-S9-candidate`), gate exit 0 twice.
