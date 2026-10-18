# PABTRV3 — Phase 8 engineering report

**Date:** October 17, 2026  
**Build:** `pab_reliability_v0_8`  
**Scope:** Frozen PABTRV3 Savra-only event/zone comprehension, **not** multiplayer, deck tuning, performance simulation, or a playable game engine.

## Result and reproducibility

From the build root run `python run_validation.py` with Python 3.10+ (standard library only). The complete gate passed **311/311 distinct tests, zero failures, zero errors and zero skips**, including all 257 previously distinct tests and **54 new v0.8 fixtures** in `tests/test_v08_mana_tokens.py`.

Additional replays, **not counted among the 311 unique tests**:

- **149/149** original v0.5 reference event tests replay against the **v0.7 event candidate** (same contract used in Phase 7).
- **52/52** v0.7 physical-bridge integration tests replay against the **new v0.8 bridge subclass**.
- The original *different* 25 inherited card-text compiler contracts are **not rerun** against `oracle.py`: the recorded historical result remains **10 pass / 15 fail**; the original compiler source is not available in this package.

Immutable deck: **1 Savra, Queen of the Golgari** as commander, **99 mainboard cards** (34 lands, 65 nonlands), plus **1 Pest Summoning** in its separate Lesson sideboard. The pod-specific Learn outside-game action remains opt-in. Frozen baseline byte digest: `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`. No accepted changes to cards or sideboard.

## New Phase 8 implementation

`pab_zone_bridge_v08.py` **subclasses** the unchanged versioned Phase 7 `PhysicalZoneGame` to narrow two physical/event synchronization gaps. It does not patch the original simulator or rewrite historical reference source.

### 1. Single opt-in Game/DeckZones reference mana pool

Both opt-in reference components use **one list of mana symbols**, not two independent floating resources. `pay_mana()` re-establishes this shared identity after the inherited cost routine atomically replaces its mana list. The limited Forest/Swamp/Command Tower zone abilities add to the actual Game pool and tap matching physical and event permanents. The existing partial Sol Ring, Golgari Signet and Phyrexian Altar output paths also operate on this same pool. Tests cover colored vs generic requirements, failed payment preserving state, a basic land entering tapped after Sakura-Tribe Elder, and Nature's Lore spending physically produced mana.

`play_physical_land()` and `tap_physical_land_for_mana()` are explicit fixture calls. **Only Forest, Swamp, Command Tower** have provisional support. Each other land name (18 of the 21 distinct entries) still throws a known-unsupported exception instead of defaulting to generic behavior. No independently pinned land text, generic land ETB, priority, tap-symbol timing, Treasure activation, nonbasic selection, full casting or comprehensive mana framework has been established. `fixture_new_turn()` is only an explicit partial reset; it is NOT a rules-complete untap step.

### 2. Physical identity for modeled event-generated tokens

When the inherited Game engine calls `make_tokens`, the v0.8 bridge mirrors the actual resulting token batch into physical **token** UIDs; this includes Chatterfang-added **green Squirrels**, rather than assuming every token is BG. Every event token receives exactly one physical token identity, separate from the accepted frozen deck's 101 physical non-token card objects. On a supported token sacrifice or destruction, the event Game queues its existing triggers and the physical token briefly moves away from battlefield then **ceases to exist**. It cannot sit in graveyard for recursive card effects. The bridge verifies token ID uniqueness, controller/name/tapped-state agreement, disjoint token/real-card mappings, and detection of untracked token disappearance.

Tested named paths include ordinary **BG Pests** with death-gain, Moseo's **BG attack-gain Pests** with no death-gain, The Hunger Tide Rises' **BG Insects**, Chatterfang's **G Squirrels**, Bastion's **white Human**, and noncreature **Treasure**. Sacrifice of a BG creature in Savra's presence can create black and green Savra triggers independently; Pest death gain occurs separately; a destruction is not a Savra sacrifice. **Mirkwood Bats** creation and sacrifice effects remain distinct from destruction. These are event-kernel contracts, not certified full-card Oracle behavior.

### 3. New tests and discovered expectation correction

54 tests cover paired positive and negative constraints around shared pool identity and costs, land play/tapping windows, explicit unsupported land types, token identity and disappearance, Savra color-sensitive triggers, lifegain replacement, Mirkwood Bats, Chatterfang, Learn, and coexistence of real creatures and tokens. An initial new-test expectation incorrectly assumed Savra's black (-2 life) and green (+2 life) triggers were the only life events when sacrificing an ordinary Pest; the correct reference outcome includes the **additional +1 from the Pest death trigger**. The test was corrected before the final all-pass gate. This was a test expectation error, not evidence of repairing the historical full simulator.

## Explicit remaining limitations

| Measure | Phase 7 | Phase 8 |
|---|---:|---:|
| Distinct deterministic tests passing | 257 | **311** |
| Added tests | 52 | **54** |
| Partial-reference nonland cards | 54/65 | **54/65** |
| Mainboard nonlands without dedicated reference behavior | 11/65 | **11/65** |
| Fully card-level verified nonlands | 0 | **0** |
| Distinct lands with provisional limited mana | 3/21 | **3/21** |
| Independently source-pinned lands | 0/21 | **0/21** |
| Original compiler repaired | No | **No** |

Unimplemented dedicated nonland paths: **Witherbloom Charm, Grisly Salvage, Golgari Charm, Heroic Intervention, Infuse with Vitality, Shigeki, Jukai Visionary, Rise of the Witch-king, Abrupt Decay, Assassin's Trophy, Witherbloom Command, Grist, the Hunger Tide.**

Other critical blocks: original editable simulator `engine.py` / `oracle.py` and `golgari_commander.json` not in this package; independent pinned card text for all 21 land names plus Arcane Signet, Sol Ring, Phyrexian Altar and Skullclamp missing; no general stack/priority, APNAP, comprehensive targeting/protection/layers, real opposing battlefield, combat/game-win assessment, true complete physical hand casting, token ownership/controller changes, or game loss after drawing from an empty library. Some event fixtures (including unlinked noncreature permanents) remain deliberately not physically reconciled. The shared mana pool tracks symbols, **not a comprehensive mana action engine**.

The old 195-slot replacement sweep and 780,000 recorded variant trials are **unvalidated** as performance evidence. Neither the old simulator nor its historical compiler contracts were repaired or rerun. All card values for optimization remain `null`, not zero. No decklist modifications, replacements, suggestions, new quantitative deck rankings or multiplayer trials occurred.

## Archival integrity

`upstream_frozen/` and prior source snapshots are preserved, along with `frozen_phase7/` snapshots of the immediately preceding bridge and runner. `PHASE7_FILE_MANIFEST.json` is checked for unchanged inherited sources and tests. New files and generated reports are versioned; `PHASE8_FILE_MANIFEST.json` records all distributed file digests except itself, plus the frozen baseline signature. The packaged archive was independently extracted and validation rerun before handoff; inspect the captured `validation_stdout.txt` and `VALIDATION_RESULTS.json`.

## Mandatory next-session starting condition

**FIRST ACTION: Perform an eight-phase retrospective audit (Phases 1–8), not Phase 9 engineering.** Use `PABTRV3_PHASE8_NEW_SESSION_HANDOFF.md` as the step-by-step audit specification. Audit the evidence, provenance, tests, false positives, missing semantics, cumulative changes, and completeness; explicitly mark any Phase 1–4 history that cannot be reconstructed from the supplied package. Present findings and corrective roadmap **before** implementing more rules paths, before any numerical simulation, and before any optimization.
