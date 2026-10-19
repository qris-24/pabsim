# CP15 — Deck-migration impact audit (frozen kernel deck → accepted PAB v2)

Read-only. Base: master `e20bda4` (rp-CP14), 2026-10-19. Inputs: `upstream_frozen/FROZEN_PABTRV3_BASELINE.txt`
(sha256 `c9589a8f…3381`, frozen) and `..\PABTRV3_ACCEPTED_V2_2026-10-19.txt` (outside the repo, not copied in).
Method: parsed both lists with a scratch script; exact-name and snake_case-identifier counts over every
`.py/.json/.md/.txt/.csv/.snapshot` file (excluding `.git`, `__pycache__`); AST walk of test functions.
No code, test, registry, frozen or upstream file was edited. No cards certified; no values, rankings or sweeps.
**Scope exception (user-authorized 2026-10-19):** `PHASE8_R02_FILE_MANIFEST.json` re-pinned with `build_manifest.py`
so the R02 preflight's file set includes this report. It was the only other file changed.

## 1. Deck diff

| | frozen baseline | accepted v2 |
|---|---|---|
| Commander | 1 (Savra, Queen of the Golgari) | 1 (same, `*F* [Commander{top}]`) |
| Mainboard | 99 (34 land / 65 nonland) | 99 (34 `[Land]` incl. Agadeem MDFC / 65 other) |
| Total | 100 | 100 |
| Sideboard | 1 (Pest Summoning, Lesson) | none |

Counts match the brief: **17 mainboard cards removed + the Pest Summoning Lesson; 17 added.** Basics unchanged (6 Forest, 9 Swamp).

Removed (17): Agent of the Iron Throne, Bastion of Remembrance, Beledros Witherbloom, Blood Artist, Demonic Tutor,
Essence Warden, Geier Reach Sanitarium, Grave Pact, Grisly Salvage, Hunt for Specimens, Infuse with Vitality,
Marauding Blight-Priest, Mikokoro, Center of the Sea, Sangromancer, Skullclamp, Starscape Cleric, Witherbloom Command.
Plus sideboard: Pest Summoning.

Added (17): Agadeem's Awakening // Agadeem, the Undercrypt, Altar of Dementia, Ashnod's Altar, Beifong's Bounty Hunters,
Beseech the Mirror, Bitterblossom, Bojuka Bog, Creakwood Liege, Eldritch Evolution, Fiend Artisan, Gravecrawler,
Greater Good, Pitiless Plunderer, Plunge into Darkness, Sylvan Library, Tom, Bert, and William, Victimize.

## 2. Removed cards — references

`file:N` = exact full-name occurrences; `+Ki` = extra snake_case identifier hits (e.g. `hunt_for_specimens(`).
`t/` = `tests/`. **F311** = inside the 311 frozen fixtures (`test_reference_events`, `test_v03_extended`,
`test_v04_cost_and_copy`, `test_v04_hunger_saga`, `test_v05_fixture_cards`, `test_v06_physical_zones`,
`test_v07_zone_bridge`, `test_v08_mana_tokens`). **Release gate: 0 references for every removed card.**

| Card | Non-frozen modules | Non-frozen tests | Flags |
|---|---|---|---|
| Agent of the Iron Throne | build_model_coverage_s20:1, build_registry:1, pab_cast_s12:1, pab_cast_s13:1, pab_cast_s15:1, pab_shigeki_s20:1 | t/test_c41_c47_contracts:5, t/test_c48_c64_contracts:1, t/test_cast_s12:1 | **F311** test_reference_events (3 tests) |
| Bastion of Remembrance | build_model_coverage_s20:1, build_registry:1, pab_cast_s12:2, pab_cast_s13:1, pab_cast_s15:1 | t/test_c48_c64_contracts:2, t/test_cast_s12:2, s9_tests/test_v08_mana_tokens_s9:1 | **F311** test_reference_events, test_v08_mana_tokens (2 tests); s9 corrected copy |
| Beledros Witherbloom | build_model_coverage_s20:1, build_registry:1, pab_cast_s7:1, pab_lands_s14:1, pab_shigeki_s20:1 | t/test_c48_c64_contracts:6, t/test_cast_s7:2, t/test_turn_clock_s2:2, test_cast_s13/integrated_turn_loop_s5/opponents_s8/turn_actions_s4/turn_clock_s1/upkeep_trigger_audit:1 each | **F311** test_reference_events (1 test) |
| Blood Artist | build_model_coverage_s20:1, build_registry:1, pab_cast_s7:1, pab_commander_s10:1, pab_opponents_s8:7+2i | t/test_c48_c64_contracts:10, t/test_opponents_s8:8+1i, t/test_cast_s13:6, c41_c47/cast_s15/cast_s7/interaction_s11:4 each, commander_s10/lands_s14:3, c78_c94/grist_s16/priority_s3:2 | **F311** test_v03_extended (1 test) |
| Demonic Tutor | build_model_coverage_s20:1, build_registry:2, pab_cast_s12:1, pab_cast_s13:5+3i | t/test_auditfix_cp13:12+4i, t/test_cast_s13:7+4i | **F311** test_v06_physical_zones (2 tests, +8i); **driver** test_cast_s13::test_driver_policies_and_eight_seeds |
| Essence Warden | build_model_coverage_s20:1, build_registry:1, pab_cast_s7:2, pab_commander_s10:1, pab_opponents_s8:1 | t/test_opponents_s8:4+1i, t/test_auditfix_cp10:3, t/test_cast_s7:3, t/test_commander_s10:1, t/test_lands_s9:1 | **F311** test_v03_extended (2 tests) |
| Geier Reach Sanitarium | build_model_coverage_s20:1, pab_lands_s14:7, pab_shigeki_s20:1 | t/test_c65_c77_contracts:1, t/test_lands_s14:1 | frozen `pab_zones.LAND_NAMES` |
| Grave Pact | build_model_coverage_s20:1, build_registry:2, pab_cast_s12:1, pab_cast_s13:3, pab_cast_s15:1, pab_commander_s10:1, pab_opponents_s8:3 | t/test_cast_s13:3, t/test_cast_s15:3, t/test_commander_s10:3, t/test_opponents_s8:3+1i, t/test_auditfix_cp13:2, t/test_cast_s6:2, t/test_cast_s12:1 | **F311** test_v03_extended (1 test) |
| Grisly Salvage | build_model_coverage_s20:1, build_registry:1, pab_cast_s13:1, pab_cast_s15:3+2i, pab_grist_s16:1 | t/test_grist_s16:2+1i, t/test_cast_s15:1+2i, t/test_c78_c94_contracts:1 | — |
| Hunt for Specimens | build_model_coverage_s20:1, build_registry:2, pab_cast_s12:1, pab_cast_s13:5+1i | t/test_cast_s13:6, t/test_c48_c64_contracts:0+5i, s9_tests/…_s9:0+1i | **F311** identifier only: test_reference_events +3i, test_v07 +3i, test_v08 +1i; **driver** test_cast_s13 (as above) |
| Infuse with Vitality | build_model_coverage_s20:1, build_registry:1, pab_auditfix_cp03:1, pab_cast_s13:1, pab_cast_s15:11+1i | t/test_auditfix_cp03:3, t/test_auditfix_cp10:3, t/test_c41_c47_contracts:2, t/test_c78_c94_contracts:2, t/test_cast_s15:2+1i | — |
| Marauding Blight-Priest | build_model_coverage_s20:1, build_registry:1, pab_cast_s7:1 | t/test_cast_s7:2 | **F311** test_reference_events (1 test) |
| Mikokoro, Center of the Sea | build_model_coverage_s20:1, pab_lands_s14:5, pab_shigeki_s20:1 | t/test_c65_c77_contracts:1, t/test_lands_s14:1 | frozen `pab_zones.LAND_NAMES` |
| Sangromancer | build_model_coverage_s20:1, build_registry:1, pab_cast_s7:1, pab_opponents_s8:4+1i | t/test_c48_c64_contracts:3, t/test_cast_s7:3, t/test_opponents_s8:2 | **F311** test_v03_extended (3 tests) |
| Skullclamp | build_model_coverage_s20:1, build_registry:2, pab_cast_s12:2, pab_clock_s3:1, pab_interaction_s11:0+2i, pab_r47_r48_sba:0+1i | t/test_c41_c47_contracts:4+1i, t/test_priority_s3:3+2i, r01_tests/test_v05_fixture_cards_r01:16+7i | **F311** test_v05_fixture_cards:16+7i, test_v06:1, test_v07:1+2i (10 tests); r01 corrected copy |
| Starscape Cleric | build_model_coverage_s20:1, build_registry:2, pab_cast_s7:2 | t/test_c48_c64_contracts:1, t/test_cast_s7:2 | — |
| Witherbloom Command | build_model_coverage_s20:1, build_registry:1, pab_cast_s13:1, pab_cast_s15:10+2i, pab_validation_s19:2+1i | t/test_cast_s15:5+1i, t/test_c78_c94_contracts:2 | — |
| Pest Summoning (Lesson) | build_model_coverage_s20:1, build_registry:3, pab_cast_s13:7+3i | t/test_cast_s13:7+6i, t/test_c48_c64_contracts:2+3i, s9_tests/…_s9:1 | **F311** test_reference_events, test_v06, test_v07, test_v08 (5 tests); **driver** test_cast_s13; frozen `pab_zones` asserts it (pab_zones.py:93) |

Frozen sources holding removed names (never edited, stay valid for the frozen deck): `pab_focus_engine.py` and
`pab_focus_engine_v07.py` (BODIES/triggers for 12 of the creature/permanent names, e.g. Skullclamp:10), `pab_zones.py`
(Demonic Tutor, Geier Reach, Mikokoro, Pest Summoning).

**Pinned-seed driver fixtures.** 24 seeded whole-deck tests exist outside the 311 (cast_s6/s7/s12/s13/s15, lands_s9/s14,
commander_s10, opponents_s8, interaction_s11, combat_s17, policy_s18, validation_s19, integrated_turn_loop_s5,
c78_c94). Only `test_cast_s13::test_driver_policies_and_eight_seeds` names removed cards, but **all 24 are bound to the
frozen deck implicitly**: they shuffle `DeckZones`' library, so any composition change re-deals every seed, including the
explicit pins `test_cast_s6::test_seed_7_driver_casts_natures_lore_turn_5`, `test_cast_s7::test_pinned_seed_7_…`,
`test_lands_s9::test_pinned_seed_42_…`. They must stay on the frozen deck.

## 3. Added cards — coverage and required mechanics

`PABTRV3_CARD_COVERAGE.json`: **all 17 absent → UNMODELED (17/17).** Also absent from `PABTRV3_MODEL_COVERAGE_S20.json`
and `upstream_frozen/PABTRV3_MECHANICAL_INVENTORY.csv`. The only repo mention is "Bojuka Bog style" in a docstring of
`pab_interaction_s11.py:22` (opponent `graveyard_exile` primitive), not a card model. No card text for any of them is in
`EVIDENCE/`; the lines below are mechanics to source and model, not certified Oracle text.

| Card | Mechanics the kernel would need |
|---|---|
| Agadeem's Awakening // Agadeem, the Undercrypt | MDFC with spell face (Pathway support is land/land only); X-cost sorcery returning creature cards with distinct mana values ≤ X; land face: enters tapped unless 3 life paid |
| Altar of Dementia | Free sacrifice outlet; **targeted mill** equal to sacrificed power (LKI); opponents have no library (S8 seats) — only self-mill (`zones.mill`) exists |
| Ashnod's Altar | Sacrifice outlet as a mana ability adding {C}{C} (no stack); colorless mana from a nonland source in the bridge pool |
| Beifong's Bounty Hunters | **Earthbend** (land becomes a 0/0 haste creature with +1/+1 counters, returns when it leaves); trigger text unsourced |
| Beseech the Mirror | **Bargain** additional cost (sacrifice artifact/enchantment/token); tutor to exile; cast without paying if MV ≤ 4, else to hand; resolution-time choice (AUD-03 pattern) |
| Bitterblossom | **Upkeep token + life loss** (1/1 flying Faerie Rogue; lose 1); S2 each-upkeep clock exists, Faerie/flying token kind does not |
| Bojuka Bog | Land enters tapped with ETB trigger exiling a target player's graveyard (S11 exile runs opponent → controller only) |
| Creakwood Liege | Hybrid {B/G} cost (S13 hybrid payment exists); static anthem by colour (B/G creatures +2/+2); optional upkeep B/G Worm token (feeds both Savra triggers) |
| Eldritch Evolution | Sacrifice as additional cost; search creature MV ≤ sacrificed MV + 2 onto battlefield; exile itself |
| Fiend Artisan | Dynamic P/T from creature cards in graveyard; **X-cost sorcery-speed tutor-to-battlefield** ({X}{B/G}, {T}, sacrifice another) |
| Gravecrawler | **Cast from graveyard while you control a Zombie**; can't block; no Zombie subtype exists in any kernel module |
| Greater Good | Sacrifice: draw equal to power (LKI), then discard three (discard choice policy) |
| Pitiless Plunderer | **Treasure creation** on another own creature dying (TREASURE token kind exists in the frozen engine) |
| Plunge into Darkness | **Entwine**; modes: sacrifice any number for 3 life each / pay X life, look at top X, one to hand, exile rest |
| Sylvan Library | **Draw-step choice**: draw two extra, then for two cards drawn this turn pay 4 life or put back on top (needs drawn-this-turn tracking at the S4 draw step) |
| Tom, Bert, and William | No text in the repo or evidence; mechanics unknown — source before any modeling |
| Victimize | Two-target graveyard reanimation tapped, with sacrifice of a creature at resolution |

## 4. How the deck enters the engine

- **Single deck parser:** frozen `pab_zones.DeckZones._read_frozen_deck` (pab_zones.py:96-113) reads the hard-wired
  `BASELINE` path (pab_zones.py:17), raises `ZoneError` on a sha mismatch with `FROZEN_SHA256` (pab_zones.py:16, 98),
  requires `Commander/Mainboard/Sideboard` headers and `Nx Name` lines, then asserts 99/1/1, 34 lands via `LAND_NAMES`,
  Savra and Pest Summoning (pab_zones.py:89-93). `PhysicalZoneGame` builds it at pab_zone_bridge.py:29 unless a `zones=`
  object is injected. The v2 file would fail this parser on its first line (no section header; `(set) [Category]` suffix).
- **Event kernel** (`pab_focus_engine*.py`) reads no deck; cards are addressed by name (BODIES).
- **Registry:** `build_registry.py:24-33` reads `upstream_frozen/PABTRV3_MECHANICAL_INVENTORY.csv` (not the .txt) and
  asserts 99/34/65, one commander = Savra, one Lesson = Pest Summoning; `summary.source_hashes_sha256` hashes every
  file in `upstream_frozen/` (:153). `build_model_coverage_s20.py` is a hand-written name table.
- **baseline_sha256:** `run_validation.py:18` (`BASELINE_SHA`), `:59` preflight `'frozen baseline changed'`, `:309`
  output field; `pab_zones.py:98`; `build_manifest.py:28` records it; v0.6 `FILE_MANIFEST.json` pins `upstream_frozen/*`
  (`run_validation.py:69-71`); `frozen_phase5/6/7/run_validation.py` (not run by the gate).
- **Preflight registry counts** (`run_validation.py:50-54`) require exactly one Lesson; v2 has none.

Release checks (18 = RegistryDeterminism 5, PreflightReadOnly 1, TamperFailClosed 11, EndToEnd 1) that would fail,
derived from preflight assertion order (static reading, not executed):

| Scenario | First preflight failure | Failing release checks |
|---|---|---|
| A. Second deck file anywhere in the tree, manifest not re-pinned | `R02 manifest file set mismatch` (:108) | 2: `test_clean_clone_passes_and_writes_nothing`, `test_shipped_command_runs_twice_cleanly` |
| A'. Same, outside `upstream_frozen/`, manifest re-pinned, not loaded | none | 0 |
| B. File placed in `upstream_frozen/`, re-pinned | `coverage registry is stale` (:113; source hashes) | 3: A's two + `test_shipped_registry_matches_rebuild` |
| C. v2 bytes loaded in place of the baseline | `frozen baseline changed` (:59) | 13: B's three + 10 of 11 tamper cases (all but `test_registry_semantic_edit_detected`, whose check at :56 fires first) |
| D. Registry rebuilt from a v2 inventory (no Lesson), asserts unchanged | `lesson count` (:54); `build()` asserts at :31 | 16: all but `test_source_hash_keys_sorted`, `test_manifest_builder_deterministic_and_excludes_outputs` |

In C and D the main suite also breaks: `DeckZones` raises, so every physical-zone fixture and all 24 seeded drivers error.

## 5. Ledger relevance

| Item | Deck change | Evidence |
|---|---|---|
| A-S20-05 menace block coordination (`pab_combat_s17.py:_declare_blocks`) | **Unchanged** | Menace source is Blight Mound on attacking Pests (`pab_combat_s17.py:70`); Blight Mound and Teacher's Pest are kept; no added mechanic above involves menace (Tom, Bert, and William unsourced) |
| A-S20-09 inherited v0.8 vs S20 counters (`run_validation.py`) | **Unchanged; scope grows** | Output hard-codes `mainboard 99, lands 34, nonlands 65, lesson_sideboard 1, frozen_deck_verified, baseline_sha256` (:256-257, :309); v2 keeps 99/34/65 but has no Lesson, so a v2 run needs its own clearly labelled counters — settle provenance first |
| A-S20-10 target bookkeeping, Witherbloom Command + Grist −2 | **Partly moot** | Witherbloom Command removed (handler `pab_cast_s15.py:307`, seat bookkeeping `pab_validation_s19.py:57`); Grist −2 kept (`pab_grist_s16.py:166`). For v2 only Grist −2 remains; the Command half still matters for frozen-deck fixtures |
| Auditor constant-resolution fix (CP11 method: exact literals; alias/constant evidence) | **Unchanged** | The three CP11 records whose evidence relies on a constant or alias — Savra (`SAVRA`), Darkbore Pathway (`PATHWAY`), Shigeki — are all kept; the 17 added names have no code yet and will need the same resolution once modeled |
| Pest Rescuer Oracle sourcing (R01: "Pest creature token") | **Unchanged** | Pest Rescuer and Teacher's Pest both kept; R01 reverses if Oracle lacks "token" (`R01_PATCH_NOTES.md:31`); Pest Summoning's removal does not affect the predicate |

## 6. Proposed layered migration (not implemented)

1. **Deck file:** `decks/PABTRV3_ACCEPTED_V2_2026-10-19.txt`, byte copy of the accepted file, outside `upstream_frozen/`;
   its sha256 recorded as `V2_SHA256` in the new layer and pinned by the R02 manifest only. The frozen baseline,
   `BASELINE_SHA`, the inventory CSV and `FILE_MANIFEST.json` stay untouched.
2. **Opt-in loader:** new layer `pab_deck_v2_cp<nn>.py` with `DeckZonesV2(DeckZones)` overriding `_read_frozen_deck`
   (parses `Nx Name (set) [Category]`, commander by `*F*`, checks `V2_SHA256`) and `__init__` (99 library / 1 command /
   0 outside_game, 34 lands via `V2_LAND_NAMES` = frozen set − Geier Reach − Mikokoro + Bojuka Bog + Agadeem MDFC,
   `learn_sideboard_allowed` forced False). Entry is injection only: `PhysicalZoneGame(zones=DeckZonesV2(seed=…))` via
   an explicit `pab_kernel` helper (e.g. `v2_zones(seed)`); the default constructor keeps the frozen deck.
3. **Old fixtures stay bound:** the 311, the r01/r52/s9 corrected copies, all 24 seeded drivers and every existing test
   keep the default `DeckZones`; no frozen seed expectation moves. v2 gets new test files only (parser, counts, sha
   tamper, fail-closed cast of every unmodeled name, own seeds), with the gate bookkeeping from CLAUDE.md.
4. **Coverage:** keep `PABTRV3_CARD_COVERAGE.json` as the frozen-deck registry (its asserts are untouched). Add
   `PABTRV3_CARD_COVERAGE_V2.json` from a separate `build_registry_v2.py`: the kept cards (83 by quantity) inherit their frozen status;
   the 17 added cards get `status: INSUFFICIENTLY_MODELED`, `modeled: []`, `not_modeled:` the §3 line,
   `text_provenance: UNSOURCED`, `full_card_behavior_verified: false`, `value_for_optimization: null` — never omitted,
   never zero. Any v2 whole-game output must carry `insufficiently_modeled_cards: 17` and no score.
5. **Gate:** new release checks for the v2 file (sha tamper → `'v2 deck changed'`, registry-v2 rebuild identity); the
   existing 18 and their messages unchanged.
6. **Sequencing:** loader + parser tests first; then source Oracle evidence for the 17 (Tom, Bert, and William and
   Beifong's Bounty Hunters first); then model per mechanic family. Phase 9 stays NO-GO; S21 not started.

## 7. Gate and commit blocker

Stopped before the gate. With only this report added, read-only `run_validation.preflight()` fails with
`R02 manifest file set mismatch: +['EVIDENCE/CP15_DECK_MIGRATION_AUDIT.md']` (scenario A above, run_validation.py:106-108).
Passing the gate needs `py -3.14 build_manifest.py`, which rewrites `PHASE8_R02_FILE_MANIFEST.json`. The CP15 brief
forbids any .json edit and says to stop in that case. CP11 (also read-only) re-pinned the manifest in its commit.
Committing without a re-pin would leave rp-CP15 failing the gate. Resolution: the user authorized the re-pin as a
scope exception (see header). The full gate was then run once on the re-pinned tree; totals are in the rp-CP15 commit message.
