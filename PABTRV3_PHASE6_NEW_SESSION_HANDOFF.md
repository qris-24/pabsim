# PABTRV3 Reliability Lab — handoff after Phase 6

**Date:** October 17, 2026  
**Latest artifact:** `PABTRV3_Reference_Kernel_v0_6_Validated.zip`  
**Next objective:** source-first integration of physical card zones into the existing isolated Savra reference events.

## Startup instructions for next session

Extract the zip, read `README.md` and `PABTRV3_PHASE6_ENGINEERING_REPORT.md`, inspect `pab_zones.py`, `pab_focus_engine.py` and the tests, then run `python run_validation.py` before changes. Reproduce results yourself rather than accepting a saved JSON file as evidence. **Preserve upstream sources and the frozen 100-card deck.**

## Frozen deck and house-rule facts

- Savra commander + **99 mainboard (34 lands, 65 nonlands)** + separate **Pest Summoning** Lesson sideboard.
- The pod allows optional Learn to retrieve the outside-game Lesson (opt-in feature; default off).
- Frozen baseline SHA-256: `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`.
- Savra is the only irreplaceable card; every other card may be evaluated **only after** correctness is demonstrated and explicit deck-modification approval obtained. No additions/cuts now.

## What actually passed

**205 tests = 149 byte-for-byte retained v0.5 fixture tests + 56 new v0.6 tests; all locally passed.** New separate `pab_zones.py` tracks individual physical cards, deterministic shuffles, hand/graveyard/library/exile/command/outside-game zone moves, opt-in Lesson Learn, disappearing tokens, limited play/tap for Forest/Swamp/Command Tower, and the library-search-and-shuffle resolution path of Demonic Tutor. The exact 21 distinct lands are identified; the other 18 distinct land names intentionally refuse unsupported land plays.

Mainboard **54/65 partial** nonlands (new: Demonic Tutor resolution), **11/65 with no dedicated reference behavior**, **0 fully verified**. All 21 distinct land names remain **without independent Oracle pinning**, including the three limited probes. Four colorless sources (Arcane Signet, Phyrexian Altar, Skullclamp, Sol Ring) also lack independent source pinning.

## Do not overclaim

`pab_zones.py` and `pab_focus_engine.Game` are **not connected**. The original event kernel still has a counter-only draw, separate graveyard/hand objects and injected basic searches. There is no full casting, mana-cost payment through lands, spell stack or game-turn priority implementation. Demonic Tutor is not a castable spell; it only has a real card-selection/search resolution fixture. Passing 205 tests is not proof of Oracle correctness or simulated competitive performance.

Original compiler signature contract results **10 passed/15 failed historically, not rerun**; original `engine.py`/`oracle.py` remain unavailable as editable source here, and there has been no integration into the old simulator. Previous replacement sweeps/Dread Return scores remain unvalidated.

## Remaining unsupported nonlands

Witherbloom Charm; Grisly Salvage; Golgari Charm; Heroic Intervention; Infuse with Vitality; Shigeki, Jukai Visionary; Rise of the Witch-king; Abrupt Decay; Assassin's Trophy; Witherbloom Command; Grist, the Hunger Tide.

## Files and immediate roadmap

- `pab_zones.py`: new v0.6 physical-card identity and zone fixtures.
- `tests/test_v06_physical_zones.py`: 56 new positive/negative regression tests.
- `pab_focus_engine.py` + five prior test files: preserved unchanged v0.5 reference engine, 149 historical local fixture contracts.
- `frozen_phase5/`: snapshots of pre-edit code and runner/coverage/test files.
- `upstream_frozen/`: untouched accepted deck, inventory, digest records, old compiler tests/results.
- `build_registry.py`, `PABTRV3_CARD_COVERAGE.json`: all card coverage statuses; all optimizer values `null`.
- `run_validation.py`, `VALIDATION_RESULTS.json`, `validation_stdout.txt`: reproducible regression execution.

**Next:** (1) obtain source and independent Oracle pins; (2) build opt-in trace-checked bridge between zones and event kernel; (3) implement exact ETB/mana for remaining lands; (4) begin source-first Grisly Salvage and Shigeki tests; (5) only later re-run old compiler contracts and increase card coverage. **Do not run performance simulations or modify accepted cards without approval.**
