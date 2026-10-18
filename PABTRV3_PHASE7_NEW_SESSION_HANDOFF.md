# PABTRV3 Reliability Lab — Phase 7 fresh-session handoff

**Date:** October 17, 2026  
**Artifact:** `PABTRV3_Reference_Kernel_v0_7_Validated.zip`  
**Workstream:** exact frozen-deck Savra mechanics and deterministic reference reliability; NO tuning and no multiplayer model.

## How to start Phase 8

Extract the v0.7 ZIP and run `python run_validation.py` in `pab_reliability_v0_7/` **before making changes**. Read `README.md`, the Phase 7 engineering report, the source in `pab_zone_bridge.py`, and its tests. Verify all old and new source hashes/frozen-baseline hash. A 257-pass fixture run plus 149-pass replay is **not** equivalent to full-card rules validation.

## Verified build state

- **257/257 distinct positive/negative fixture tests passed**, consisting of 149 historical v0.5 + 56 physical-zone v0.6 + 52 bounded opt-in bridge v0.7.
- Separately reran the original 149 event tests **against the v0.7 candidate**: 149/149 passing; this is a **replay**, not 149 extra distinct tests. Original compiler's **25 old signature contracts are not rerun**, saved 10 pass/15 fail.
- Commander: Savra, Queen of the Golgari. **99** mainboard: **34** lands, **65** nonlands. **1** outside-game Lesson Pest Summoning, retrievable by explicit opt-in pod house rule only. SHA-256 baseline: `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`.
- Source and test baseline copied into `frozen_phase6/`; original event kernel and zone prototype remain unmodified. Versioned candidate normalization occurs **only** in `pab_focus_engine_v07.py` and opt-in glue in `pab_zone_bridge.py`.
- Mainboard coverage indicators **54/65 partial; 11/65 unsupported; zero fully verified**. Land probe **3/21 distinct names provisional**, none independently Oracle pinned. No accepted deck change or optimizer values; all `value_for_optimization` fields are `null`.

## New behavior with strict limits

1. The versioned v0.7 event kernel routes manual draw counters in five call sites to `_fixture_draw`; canonical historical token types and exception classes are retained. Opt-in `PhysicalZoneGame` draws actual physical UIDs from DeckZones, records both successful cards and attempted empty draws; **the loss condition is still unadjudicated**.
2. Sakura-Tribe Elder and the basic-Forest-only subset of Nature's Lore search a **real 99-card physical library** and shuffle; their selected real basic land gets a mapped event UID. **No full nonbasic Forest ETBs, no shared Game/DeckZones mana pool**, and no true casting stack.
3. Explicitly linked creature cards move real UIDs through hand -> battlefield -> graveyard -> battlefield reanimation, or graveyard -> hand through a limited Phyrexian Reclamation path. Cycling Unearth discards its actual card. Opt-in Learn moves the actual single Lesson. Game's other permanents/hand effects/tokens remain fixture-only and **not reconciled**.
4. Bridge integrity checks guard explicitly linked UIDs; they do not prove every possible Game object has an equivalent physical card. No complete game engine, opponent interaction, rule stack, APNAP, SBA/layer engine, full casting legality or win-rate simulation exists.

## Required Phase 8 work, in order

**Source-first:** obtain original `engine.py`, `oracle.py`, `golgari_commander.json`, and independent pinned Oracle text for all 21 land names + Arcane Signet, Phyrexian Altar, Skullclamp and Sol Ring. This ZIP does not supply those full original sources; do not claim they were used or that 15 historic failures were repaired.

**Integrate one subsystem at a time:** shared mana pool, zone-safe physical cycling/hand return/drawing, token object lifecycle (including Pest death and black/green Savra triggers) and real draw-from-empty loss detection. Build both positive and adversarial tests; keep unimplemented operations rejecting instead of silently assigning zeros.

**Remaining unsupported 11:** Witherbloom Charm; Grisly Salvage; Golgari Charm; Heroic Intervention; Infuse with Vitality; Shigeki, Jukai Visionary; Rise of the Witch-king; Abrupt Decay; Assassin's Trophy; Witherbloom Command; Grist, the Hunger Tide. Grisly Salvage must wait for verified typing/library behavior.

**Do not optimize:** no mass replacement sweep, cuts, adds, performance scores or win-rate claims. Savra is the only irreplaceable card; the accepted deck remains frozen without explicit approval.
