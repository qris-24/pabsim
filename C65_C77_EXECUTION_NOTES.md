# C65–C77 execution notes (issues R35–R40, lands) — 2026-10-18

`tests/test_c65_c77_contracts.py`: 20 counted fixtures (total 396). Land support in the kernel: Forest, Swamp, Command Tower (physical bridge); Sol Ring / Arcane Signet / Golgari Signet rocks; basic-only Nature's Lore and Sakura-Tribe Elder fixtures. Everything else fails closed.

| Contract | Status | Tests | What was asserted |
|---|---|---|---|
| C65 | BLOCKED_UNSUPPORTED | 1 (2 subTests) | Blooming Marsh, Deathcap Glade: `play_physical_land` raises `UnsupportedZoneMechanic`; all zones, permanents, mana, tap states and land-play count unchanged; bridge integrity holds. |
| C66 | BLOCKED_UNSUPPORTED | 1 | Undergrowth Stadium: same fail-closed probe. |
| C67 | BLOCKED_UNSUPPORTED | 2 | Overgrown Tomb, Underground Mortuary: fail-closed. **Control executed:** Forest enters untapped, no life change, second land play in the turn refused. |
| C68 | BLOCKED_UNSUPPORTED | 1 | Pathway (MDFC face) fail-closed. |
| C69 | PARTIAL_EXECUTED | 4 | Basic Forest qualifies for Nature's Lore; Swamp index rejected before any mana is paid; physical basic-Forest search enters untapped; Sakura control: nonbasic rejected, basic Swamp enters tapped. **Not asserted:** Tomb/Mortuary qualifying by Forest subtype and Cemetery/Pathway exclusion — nonbasic Forest-typed search is unmodeled and fails closed. |
| C70 | BLOCKED_UNSUPPORTED | 1 | Verdant Catacombs fail-closed. |
| C71 | BLOCKED_UNSUPPORTED | 1 | Phyrexian Tower fail-closed. |
| C72 | BLOCKED_UNSUPPORTED | 1 (2) | High Market, Grim Backwoods fail-closed. |
| C73 | BLOCKED_UNSUPPORTED | 1 (2) | Llanowar Wastes, Nurturing Peatland fail-closed. |
| C74 | BLOCKED_UNSUPPORTED | 1 | Castle Locthwain fail-closed. |
| C75 | BLOCKED_UNSUPPORTED | 1 (2) | Boseiju, Takenuma fail-closed; no channel API exists. |
| C76 | BLOCKED_UNSUPPORTED | 1 (2) | Geier Reach Sanitarium, Mikokoro fail-closed. |
| C77 | PARTIAL_EXECUTED | 4 | Command Tower makes {B} or {G}, {U} refused without tapping or adding mana; Forest {G}; Swamp {B} and {G} refused; tapped land cannot tap again until the fixture turn refresh; Sol Ring {C}{C}, colored request refused. Grim Backwoods {C} fails closed. |

Coverage fact established by this family: **all 18 unsupported land names are verified fail-closed** (refusal + no state mutation), not merely declared unsupported. That is the first executable evidence for the "18/21 fail closed" claim in the Phase 6 report.

Blocked until modeled: conditional ETBs (land count, opponent count, life payment), surveil, MDFC faces, fetch activation, sacrifice/utility land activations, painland damage, Castle Locthwain, Channel, symmetrical draw effects.
