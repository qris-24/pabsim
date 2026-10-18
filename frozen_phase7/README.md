# PABTRV3 — Phase 7 isolated reliability kernel (v0.7)

## Scope and reproduction

This is a deterministic **rules-reference fixture**, not a playable Commander simulator or deck optimizer. Frozen PABTRV3: **1 Savra + 99 mainboard (34 lands / 65 nonlands) + separate Pest Summoning Lesson**. The exact deck baseline SHA-256 is `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`.

With Python 3.10+ only:

```sh
cd pab_reliability_v0_7
python run_validation.py
```

The gate runs **257 distinct fixture tests**: 149 retained v0.5 + 56 retained v0.6 + 52 new v0.7. It also **replays the 149 v0.5 event tests against `pab_focus_engine_v07.Game`** to detect backwards regression. These 149 replays are not additional unique tests. The runner writes `PABTRV3_CARD_COVERAGE.json` and `VALIDATION_RESULTS.json`.

## Phase 7 engineering files

- `pab_focus_engine.py`: **unchanged historical isolated v0.5 event reference** (not the original inherited simulator).
- `pab_zones.py`: **unchanged v0.6 physical-card zones**; exact persistent physical UIDs.
- `pab_focus_engine_v07.py`: versioned candidate, routing five legacy manual draw-counter call sites through `_fixture_draw` and preserving reanimated fixture power; imports canonical v0.5 token/constants/exception classes to keep identity comparisons meaningful.
- `pab_zone_bridge.py`: explicit `PhysicalZoneGame`, **opt-in subset bridge only**. Its linked Game permanents use a separate Game UID and a stable physical card UID; a map reconciles movement through battlefield and graveyard. The rest of Game may still contain *unlinked injected fixtures*.
- `tests/test_v07_zone_bridge.py`: **52** positive/negative deterministic bridge regressions.
- `frozen_phase6/`: snapshots of original prior source, tests, coverage and runner; `frozen_phase5/` contains earlier snapshots; `upstream_frozen/` contains untouched frozen project baseline and original historical compiler results.

## Supported v0.7 bridge paths and limits

1. **Actual draw cards**: Moldervine Reclamation, Dark Prophecy, Yawgmoth, Village Rites, Deadly Dispute, Plumb the Forbidden, Unearth cycling and Skullclamp route their *already limited Game effects* through `DeckZones.draw()` in bridge mode. The `cards_drawn` metric counts successful physical transitions only. Empty-library attempts are explicitly flagged and **game loss is not adjudicated**. Old `Game.hand` remains a deprecated fixture list, not a physical authoritative hand.
2. **Selected real basic land**: Sakura-Tribe Elder and the basic-Forest-only subset of Nature's Lore search and shuffle physical library; Game receives a mapped corresponding land event permanent. The opt-in stub chooses at resolution, not at cast/activation. Other 18 land names still lack behavior and independent Oracle text pinning. `pab_zones`' separate mana pool and `Game.mana_pool` are not synchronized; manually injected Game mana is required for test casts.
3. **Explicitly linked creature**: Move a physical creature card from physical hand into a Game event fixture with `enter_linked_creature`; sacrifices/destruction move the *same UID* to physical graveyard; chosen reanimations preserve its physical UID and Game dead-card UID -> new event-UID relationship. Phyrexian Reclamation can return a linked creature to physical hand, and Unearth cycling discards the actual Unearth card. Other Game permanents and tokens are not all linked to physical cards. Existing v0.5 Game triggers remain approximations and should not be mistaken for a stack/layers engine.
4. **Optional Learn house rule**: `hunt_for_specimens(lesson=True)` in bridge mode physically moves the sole Lesson from outside_game to hand only when opted in; no phantom hand string or second outside-game copy. Its Pest token remains an unlinked event fixture.

## Unresolved hard stops

**54/65 partial** nonlands, **11/65 unsupported**, **zero fully verified**. All **21 distinct land names** and **four colorless-source cards** still lack independently pinned Oracle snapshots, even the limited three-name land probes. The original full simulator `engine.py` / `oracle.py` is not patched or available as editable source; its saved **10/25 pass, 15/25 fail** compiler contract snapshot has not been rerun.

No generic casting, priority, real stack, APNAP, opponent model, general mana pool, full card ownership/controller semantics, layers, search policies, draw-loss SBA, full zones for tokens, or independent Oracle certification. **No card swaps, replacement sweeps, simulations of performance, recommendations, or changes to the accepted deck.**

Read `PABTRV3_PHASE7_ENGINEERING_REPORT.md` and `PABTRV3_PHASE7_NEW_SESSION_HANDOFF.md` before extending.
