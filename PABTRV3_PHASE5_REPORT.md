# PABTRV3 — Phase 5 engineering report

**Date:** October 17, 2026  
**Build:** `pab_reliability_v0_5`  
**Workstream:** Frozen-deck mechanics and deterministic rules fixtures ONLY.

## Outcome — independently reproducible locally

The full supplied test suite ran with **149/149 passing, zero errors, zero skips** via `python run_validation.py`. This retained all **111** v0.4 checks and added **38** new tests. Deck composition and original baseline SHA-256 are unchanged:

- Commander: **Savra, Queen of the Golgari** (1).
- Mainboard: **99 cards**, including **34 lands** and **65 nonlands**.
- Sideboard: **Pest Summoning** (1 separate Lesson; optional outside-game Learn is a house rule).
- Frozen baseline SHA-256: `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`.
- Original compiler's saved signature contracts: **10 passed, 15 failed**. These historical contracts **were not re-executed** against the original compiler here.
- Original 195-slot replacement sweep and old full simulator remain **unvalidated**; no optimizer was run.

## New defect correction

**Pest Rescuer:** prior `begin_upkeep` logic looked for only `x.token` with Pest subtype. This ignored **Teacher's Pest**, a nontoken Pest. The v0.5 `controls_pest()` checks creature subtype regardless of token status, both when the intervening-if trigger is created and again when resolved. Three new tests cover the presence, late entry, and absence of Teacher's Pest.

## New limited behaviors

| Card / function | What has deterministic reference coverage | Not yet verified |
|---|---|---|
| **Golgari Signet** | Cost {1}, tap, add B and G, control/tapped checks | Casting the rock, all priority and mana-production windows |
| **Sol Ring** | Tap for two **colorless**; cannot pay green requirement | Independently pinned Oracle/source and full artifacts framework |
| **Arcane Signet** | Tap for B or G with Savra as commander; no W | Independently pinned Oracle/source and commander identity variants |
| **Sakura-Tribe Elder** | Own sacrifice as activation cost; green Savra trigger; explicit **basic** land enters tapped | Real library, timing/priority, library order or nonbasic selection |
| **Nature's Lore** | Pay {1}{G}, sorcery check, explicit **basic Forest** enters untapped | Nonbasic Forest cards with distinct ETB rules; true search/shuffle |
| **Pest Infestation** | {X}{X}{G}, zero to X targets, 2X proper BG Pests, all-illegal target handling | Opponent interactions/comprehensive artifact creatures and targeting |
| **Unearth** | {B} reanimation with mana-value cap, fizzle if target moved; separate cycling | Actual card zones, deck library, wider stack and response choices |
| **Skullclamp** | Pay {1} equip, 1-toughness SBA death not sacrifice, draw two once, detach | Independent text pin, attachment/layers and general game engine |

The reference model deliberately uses **injected basic-land/library fixtures** and a `cards_drawn` counter. Passing tests do **not** demonstrate that a full Commander hand, deck, search, draw, state-based-action, equipment, or priority system works.

## Coverage and unresolved engineering state

| Metric | Phase 4 | Phase 5 |
|---|---:|---:|
| Isolated reference tests | 111 | **149** |
| Mainboard nonlands with **partial** support | 45/65 | **53/65** |
| Mainboard nonlands with **no dedicated** support | 20/65 | **12/65** |
| Fully card-level verified nonlands | 0 | **0** |
| Fully verified 34 land copies | No | **No** |
| Old compiler failures not repaired | 15/25 | **15/25** |

The 12 unsupported mainboard nonlands are **Witherbloom Charm, Grisly Salvage, Golgari Charm, Heroic Intervention, Infuse with Vitality, Shigeki, Jukai Visionary, Rise of the Witch-king, Abrupt Decay, Assassin's Trophy, Witherbloom Command, Grist, the Hunger Tide, Demonic Tutor.**

## Cautions and remaining defects

1. No actual library or creature cards drawn to hand. Additions such as Nature's Lore and Demonic Tutor cannot be fully meaningful yet without a properly tracked library.
2. Missing authoritative independently pinned text for **Arcane Signet, Phyrexian Altar, Skullclamp, Sol Ring**, plus card data verification for **all 34 lands** (21 distinct land entries, including 6 Forest and 9 Swamp copies).
3. New methods represent selected rules paths only: don't generalize their test passes into full-card equivalence or use the 53/65 figure as a percentage of complete coverage.
4. No arbitrary stack, actual opponent permanents, response windows, decisions, phase advancement, full colored lands, or target/continuous-effect layers.
5. The original simulator's `engine.py` and `oracle.py` were not available here as editable raw bytes; no integration patch or original compiler re-run was performed. The historical engine and benchmark code/results were not changed.
6. Known original-compiler omissions remain around normal Pest creation, Witch Magecraft, Pest Rescuer, Moseo, Saga chapters, South Wind Avatar, Agent of the Iron Throne, Immoral Bargain, and other token sources.

## Reproduction and source integrity

Unzip `PABTRV3_Reference_Kernel_v0_5_Validated.zip`, enter `pab_reliability_v0_5/`, run `python run_validation.py`. It rebuilds `PABTRV3_CARD_COVERAGE.json`, rechecks mainboard/commander/Lesson and exact baseline digest, executes exactly 149 deterministic tests, and writes `VALIDATION_RESULTS.json`. A human-readable result is in `validation_stdout.txt`. No dependencies beyond Python 3.10+ standard library. The `upstream_frozen/` inputs are copies of the focus audit and remain unchanged. The historical snapshots are in `frozen_previous_tests/`.

## Next steps, strictly prioritized

**Priority 1 — source integrity:** obtain editable copies of the original `engine.py` and `oracle.py` plus verified Oracle snapshots for the four colorless cards and exact ETB/mana behavior for all 34 lands. Preserve original source unmodified.

**Priority 2 — model source-first game zones:** implement an explicit individual-card library, hand, basic/nonbasic lands with tapped/mana, and card move/shuffle/search operations; prove exact deterministic traces before adding tutors as functional simulation.

**Priority 3 — the remaining 12 cards:** introduce dedicated positive/negative fixtures for each, with modal selection, protection, targeting, mill, graveyard, land and planeswalker behaviors. Do not treat missing effects as zero.

**Priority 4 — validate casting and stack:** make cast-time target locking, costs, responses, APNAP and state-based actions consistent across all cards, then integrate into versioned full-engine copy. Re-execute original 25 compiler contracts and resolve actual failures.

**STOP:** do not run another mass replacement sweep, assign performance scores, or propose a card cut until all correctness/coverage gates pass and the user explicitly authorizes deck changes.
