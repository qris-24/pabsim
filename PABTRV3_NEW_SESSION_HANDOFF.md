# PABTRV3 Reliability Lab — fresh-session handoff (after Phase 5)

**Prepared:** October 17, 2026  
**Latest runnable module:** `PABTRV3_Reference_Kernel_v0_5_Validated.zip`  
**Scope:** strictly **one frozen Savra deck**, not multiplayer calibration, not tuning.

## Mandatory initial instruction in the new session

**Read this handoff and the v0.5 ZIP, inspect code and the exact frozen decklist, run `python run_validation.py`, then continue engineering the reference framework with truthful positive/negative tests. Preserve every historical source and the accepted deck. No deck optimization or replacement sweep.**

## Frozen deck identity — never change without explicit approval

- Commander: **Savra, Queen of the Golgari** — the only irreplaceable card.
- 99 mainboard cards = 34 lands (21 distinct names) + 65 nonland cards.
- Separate one-card Lesson sideboard: **Pest Summoning**.
- Group house rule: Learn may obtain Pest Summoning from outside the game (configurable; off by default).
- Frozen deck text is within the ZIP at `upstream_frozen/FROZEN_PABTRV3_BASELINE.txt`.
- Baseline SHA-256: `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`.
- **Absolutely no accepted adds/cuts** without direct user approval; no new rankings or simulated win-rates now.

## Verified development checkpoints

| Build | Locally passing reference tests | Mainboard nonlands with partial behavior | Unsupported nonlands |
|---|---:|---:|---:|
| Phase 2 v0.2 | 42 | baseline partial registry | – |
| Phase 3 v0.3 | 76 | 41/65 | 24/65 |
| Phase 4 v0.4 | 111 | 45/65 | 20/65 |
| **Phase 5 v0.5** | **149/149** | **53/65** | **12/65** |

All these tests apply to a **separate reference kernel**, NOT to the full inherited simulator. **Fully verified card count remains ZERO**. These counts describe coverage indicators, not game-power contributions.

Phase 5 preserved 111 older passing tests and added 38, all passing. It corrected Pest Rescuer ignoring nontoken **Teacher's Pest** in upkeep's trigger-time and resolution-time conditions. It added limited reference contracts for **Sol Ring, Arcane Signet, Golgari Signet, Sakura-Tribe Elder, Nature's Lore, Pest Infestation, Unearth and Skullclamp**. See `README.md`, `PABTRV3_PHASE5_REPORT.md`, `tests/test_v05_fixture_cards.py` for exact limits. Basic Forest/Swamp cards are **supplied fixtures**; lands do not yet produce mana in a full engine. Skullclamp and two mana rocks still require independent Oracle text pinning.

The inherited old card-text compiler's **25 signature contracts historically showed 10 passes and 15 failures**. That suite has **not** been rerun against the original compiler because its editable bytes were unavailable; it is still not repaired. Historical ~195-slot replacement study, 780,000 variant trials and Dread Return rankings remain **unvalidated**; do not use them to recommend cuts.

## What matters about this exact deck

- Savra only triggers for your **sacrifice**, not generic death. BG body produces separate black (optional 2 life for each opponent edict) and green (optional +2 life) triggers. Opportunities are **not actual opponent sacrifices**.
- **Ordinary BG Pest** gains 1 on death; **Moseo attack-gain BG Pest** does not; **Teacher's Pest** is a **BG nontoken Pest creature card** with attack-gain and graveyard recursion; Hunger Tide makes **BG Insects**; Infestation Sage flying Insect; Wriggling Grub two BG Worms; Chatterfang extra **green** Squirrels; Bastion makes **white** Human; Reassembling Skeleton **black** only.
- Life gain is event-based: Dina / Marauding / Starscape / South Wind trigger once **per event**. Pest Rescuer modifies amount (+1 per event). Mirkwood Bats triggers token creation or **sacrifice**, not token death caused by destruction.
- Sacrifice as **casting cost** precedes Magecraft cast triggers. Grave Pact triggers on any controlled creature death. Cauldron, Moseo, The Hunger Tide, Reclamation, Teacher's Pest, Skeleton, Unearth all have **different** resource/target/destination behavior.

## Remaining 12 nonlands without dedicated reference implementations

Witherbloom Charm; Grisly Salvage; Golgari Charm; Heroic Intervention; Infuse with Vitality; Shigeki, Jukai Visionary; Rise of the Witch-king; Abrupt Decay; Assassin's Trophy; Witherbloom Command; Grist, the Hunger Tide; Demonic Tutor.

**The 34 lands have not been independently source-verified**, and source text for Arcane Signet, Phyrexian Altar, Skullclamp, Sol Ring needs supplemental pinning. No card has full test coverage. No missing card may be valued at zero in comparative tests.

## File map inside ZIP

- `pab_focus_engine.py` — v0.5 standalone partial reference kernel, no original engine modification.
- `tests/test_reference_events.py` — 42 initial reference tests.
- `tests/test_v03_extended.py` — 34 added v0.3 tests.
- `tests/test_v04_cost_and_copy.py` + `test_v04_hunger_saga.py` — 35 added v0.4 tests.
- `tests/test_v05_fixture_cards.py` — 38 added v0.5 tests.
- `run_validation.py` — complete 149-test deterministic gate with frozen-deck SHA.
- `build_registry.py` and `PABTRV3_CARD_COVERAGE.json` — all 65 nonland statuses, source metadata, null optimization values.
- `VALIDATION_RESULTS.json` and `validation_stdout.txt` — actual passing test outcomes.
- `upstream_frozen/` — exact deck, inventory, old compiler test and saved failure results; do not mutate.
- `frozen_previous_tests/` — earlier snapshots preserved for regression review.
- `PABTRV3_PHASE5_REPORT.md` — engineering details and limitations.

To rerun: unzip, enter `pab_reliability_v0_5`, run `python run_validation.py` with Python 3.10+. No external packages required.

## Next assignment, in order

1. **Read and execute the v0.5 package**, and independently inspect the tests for false positives. Don't assume 149 passing means validated rules coverage.
2. **Acquire authoritative pinned Oracle text** for all 4 missing colorless cards and all land entries, plus editable original simulator `engine.py` and card compiler `oracle.py`; don't overwrite old sources.
3. **Introduce actual card-object zones and card-specific land ETB/mana** with deterministic draw/search/shuffle decisions before tackling Grisly Salvage, Demonic Tutor, Shigeki and other library-centric spells. Maintain token objects and controller/owner distinction.
4. Add **positive and negative** reference contracts for all remaining 12 unsupported nonlands, including protection, modes, target locking, mill, planeswalkers, and symmetrical sacrifice.
5. Re-run the original compiler contracts against a versioned integrated candidate, fix its Pest-related and other failures, and verify full 65/65 behavioral paths and 34 lands before any numerical deck-performance claim.
6. Only after full validation and separate user authorization resume controlled replacement research. **Savra is the only irreplaceable card; deck remains frozen until approval.**

## Work must be reported truthfully

Local passing fixture tests are not authoritative Oracle/legal gameplay certification or win-rate evidence. Clearly distinguish source snapshot records, supplemental unpinned known card text, hand-built reference mechanics, historical compiler tests, and integration status. No more mass sweeps until stated gates pass.
