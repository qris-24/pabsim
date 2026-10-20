# CP25 — PAB v3 name lookup in card data (read-only)

Read-only. Base: master `2e1adbe` (rp-CP24), 2026-10-20. Full per-name table: `EVIDENCE/CP25_V3_NAME_LOOKUP.json`
(87 distinct names, quantity, zone, source line, status, JSON index, type line, mana cost, land flag).
Card data: `C:\pabsim\data\golgari_commander.json` (outside the repo, read-only; 9877 objects; sha256 `f184c661a0ca…`,
full hash in the JSON). Method: a scratch script outside the repo; no Oracle text copied; no kernel, test, deck-target
or card-data file changed. No cards certified; no values, rankings or sweeps.

**v3 list pending user approval before CP26.**

## 1. List derivation

| Step | Source (file:line) | Effect |
|---|---|---|
| Base | `upstream_frozen/FROZEN_PABTRV3_BASELINE.txt:2` (Commander), `:5-90` (Mainboard); sha256 `c9589a8f…3381` = `pab_zones.FROZEN_SHA256` | Savra + 99 |
| Drop Lesson | `upstream_frozen/FROZEN_PABTRV3_BASELINE.txt:93` (Sideboard: Pest Summoning) | v3 has no sideboard |
| Remove 17 | `EVIDENCE/CP15_DECK_MIGRATION_AUDIT.md:22-24` (§1 Removed) | each was a qty-1 baseline mainboard card |
| Add 17 | `EVIDENCE/CP15_DECK_MIGRATION_AUDIT.md:27-29` (§1 Added) | none was in the baseline |
| Swap 2 | `EVIDENCE/CP15_DECK_MIGRATION_AUDIT.md:182-183` (§8.1: Rise of the Witch-king → Ooze Garden; Yahenni, Undying Partisan → Scavenger's Talent) | both OUT cards kept from baseline; both IN cards new |
| Cross-check | `EVIDENCE/CP15_DECK_MIGRATION_AUDIT.md:191-194` (§8.1 v3 added (19)) | equals §1 Added + the 2 swap INs |

Comma-separated names were split by greedily joining `, `-tokens until the result is a known name (baseline name or
card-data name, plus the two Altars), so multi-comma names (Mikokoro, Center of the Sea; Tom, Bert, and William;
the Agadeem MDFC) parse as one card.

Result: **100 cards = Savra + 99 mainboard; 87 distinct names (6 Forest, 9 Swamp); 34 lands / 66 nonland incl.
Savra (65 nonland mainboard). Source conflicts: 0.** Land rule: card-data `type_line` (any face) contains `Land`;
every baseline name found in the card data agreed with frozen `pab_zones.LAND_NAMES` (pab_zones.py:21-29). Names
absent from the card data were classified by `LAND_NAMES` (Command Tower, High Market, Verdant Catacombs = land);
Altar of Dementia and Ashnod's Altar as nonland per `EVIDENCE/CP15_DECK_MIGRATION_AUDIT.md:252`. The Agadeem MDFC
counts as a land (back face type line), as in the v2 file (CP15 §1).

## 2. Lookup counts (per distinct name)

| Status | Names |
|---|---|
| found (exact: top-level `name` or `card_faces[].name`) | 79 |
| normalized match (NFKD, curly → straight apostrophe, casefold, drop non-alphanumerics) | 0 |
| missing | 8 |

Every found name matched exactly one JSON object; all matched on the top-level `name` (the Agadeem MDFC's top-level
name is the full `A // B` name).

## 3. Missing names

| Name | Source line | Expected |
|---|---|---|
| Altar of Dementia | CP15 audit :27-29 | yes |
| Ashnod's Altar | CP15 audit :27-29 | yes |
| Arcane Signet | baseline :57 | **no** |
| Command Tower | baseline :19 | **no** |
| High Market | baseline :25 | **no** |
| Phyrexian Altar | baseline :44 | **no** |
| Sol Ring | baseline :63 | **no** |
| Verdant Catacombs | baseline :35 | **no** |

Finding: the card data contains **no colorless-identity objects** (`color_identity` counts: B 4774, G 4669, BG 434,
colorless 0). All 8 missing names are colorless-identity cards, which explains every miss. A substring probe (normalized
name contained in any card-data name) found 0 hits for all 8. No Oracle text was guessed for any of them. CP16 §8.3
checked only the added cards, so the 6 baseline colorless cards were not previously reported as missing.

Consequence for CP26: the pinned Oracle supplement must cover all 8 names, not only the two Altars.

## 4. Normalization hits

None.
