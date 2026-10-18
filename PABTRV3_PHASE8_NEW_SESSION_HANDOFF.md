# PABTRV3 Reliability Lab — new-session handoff after Phase 8

**Build:** `PABTRV3_Reference_Kernel_v0_8_Validated.zip`  
**Date:** October 17, 2026  
**Absolute scope:** ONE frozen Savra, Queen of the Golgari deck and its deterministic rules comprehension. No multiplayer expansion, tuning, card edits or replacement sweeps.

## Mandatory first action in the NEW session — AUDIT ALL EIGHT PHASES

**Do not commence Phase 9 code, card coverage expansion, or additional numerical experiments until an evidence-led independent retrospective AUDIT OF PHASES 1 THROUGH 8 has been completed and reported.**

Start with these exact instructions:

> Extract `PABTRV3_Reference_Kernel_v0_8_Validated.zip`. Read its Phase 8 engineering report and all available prior phase reports, handoffs, sources and preserved snapshots. Independently verify frozen-deck file hash, archive integrity, test totals, previous-source checksums, and rerun `python run_validation.py`. Then audit **each of the eight phases separately** for actual implementation versus documented claims, source provenance, missing semantics, false-positive/inadequate tests, mutation errors, invariant violations, regression compatibility, and coverage misclassification. Perform adversarial targeted re-tests of suspicious paths. Distinguish documentation assertions from inspected source evidence. Produce a phase-by-phase evidence table and a prioritized issue register with severity, reproduction instructions, probable repair steps, and stop/go gates. If Phase 1–4 primary records or the original inherited engine are unavailable, mark their conclusions unverified, request or enumerate missing artifacts, and do not fabricate details. **Only after reporting the audit should any Phase 9 implementation be considered.** The deck remains frozen.

### Audit protocol and deliverables

1. **Archive and trust chain:** hash-check 100-card frozen baseline, 99+1+Lesson composition, all recorded inherited checksums and past versioned code, no unauthorized accepted edits. Check missing primary evidence explicitly.
2. **Phase-by-phase reconstruction:** For **Phase 1**, **Phase 2**, **Phase 3**, **Phase 4**, **Phase 5**, **Phase 6**, **Phase 7**, **Phase 8**, enumerate baseline intent, actual available source/tests, the new rule semantics, test total, regression status, and confidence. Do not equate a passed fixture with card-level oracle certification.
3. **Independent replay:** validate v0.8 `311/311` distinct fixtures; separately check 149/149 inherited v0.5 event replay against v0.7 candidate and 52/52 v0.7 bridge replay against v0.8. Historical original **25 compiler signatures (10 pass/15 fail)** are NOT those reference replays; do not report them as repaired.
4. **Rules/mechanics challenge:** examine black/green Savra triggers, Pest deaths versus sacrifices, non-Pest tokens, Chatterfang replacement, Mirkwood Bats creation/sacrifice, Pest Rescuer event replacement, Teacher's Pest nontoken condition, timing/costs, lost/drawn UIDs, zero-toughness and tokens ceasing, alternate Graveyard/command-zone behavior, and linked ownership/controller distinction. Add reproducible bug probes only as audit fixtures, not performance tests.
5. **Mana/zone challenge:** audit v0.6 object-zone invariants, v0.7 bridge UID mappings and real draw/land search/recursion, v0.8 shared pool and physical token mirroring. Investigate bypass methods that mutate `Game.permanents`, physical zones or mana pools directly, external control changes, unsupported nonbasic ETB/mana, double consumption, stale references, failed operation transactionality, and out-of-order SBA effects. Treat fixture-sourced manual spells and `Game.hand` as still not fully physical.
6. **Card/source matrix:** reconcile all **65 mainboard nonlands** and **34 land copies (21 unique names)** with asserted Oracle provenance and actual code/test branches. **54 nonlands only PARTIAL, 11 unsupported, zero fully verified** as of v0.8. Verify missing source for four nonland artifact cards, plus original editable `engine.py`, `oracle.py`, `golgari_commander.json`.
7. **Evidence integrity:** check historical heuristic performance findings against their original assumptions only if primary data are supplied. Do not promote the 195-slot sweep, 780,000 trials, or Dread Return preference to deck guidance.
8. **Audit output:** a phase-by-phase table, a risk-ranked defect ledger with reproducible tests, an implementation/evidence coverage matrix, a list of unavailable evidence, and a recommended gated engineering roadmap. Clearly state which claims are independently reproducible and which require external validation.

## Frozen PABTRV3 identity

- Commander: **Savra, Queen of the Golgari** (only irreplaceable card).
- Mainboard: **99 cards = 34 lands + 65 nonlands**.
- Separate Lesson sideboard: **Pest Summoning** (1), outside-game Learn allowed only under explicit pod house-rule opt-in; disabled by default.
- Raw baseline SHA-256 `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`.
- Nothing added or cut without explicit user approval; proposed future changes would need mechanically evidenced tradeoffs and a verified full 100-card list plus separate Lesson.

## Quick reproduction

With Python 3.10+ standard library:

```sh
unzip PABTRV3_Reference_Kernel_v0_8_Validated.zip
cd pab_reliability_v0_8
python run_validation.py
```

**Expected Phase 8 results:** 311 unique deterministic tests passed, 0 errors/failures/skips. Distinct composition **149 (v0.5), 56 (v0.6), 52 (v0.7), 54 (v0.8)**. Separate compatibility replays: 149 original v0.5 event fixtures on v0.7 Game + 52 older v0.7 bridge tests against v0.8 PhysicalZoneGame. Tests validate a bounded reference fixture, *not a real Commander simulator*.

## What's now implemented — cautiously

- v0.5 event reference (`pab_focus_engine.py`) retains limited trigger, sacrifice, death, life, and selected named spell abilities.
- v0.6 (`pab_zones.py`) tracks persistent card UIDs, deterministic library, draw, mill, search/shuffle, and three provisional land mana definitions.
- v0.7 (`pab_focus_engine_v07.py`, `pab_zone_bridge.py`) permits opt-in limited physical drawing and searching, identity-preserving linked creature deaths/recursion, Unearth cycling, and house-rule Learn. The original Game `hand` remains a fixture list.
- v0.8 (`pab_zone_bridge_v08.py`) links a single shared Game/DeckZones mana symbol pool, explicitly mirrors Event tokens with unique physical token identities and cessation on leaving battlefield, and adds an explicit three-name land-play/tap reference path. All prior implementations remain separate and unmodified.

## Remaining 11 unsupported nonlands

Witherbloom Charm; Grisly Salvage; Golgari Charm; Heroic Intervention; Infuse with Vitality; Shigeki, Jukai Visionary; Rise of the Witch-king; Abrupt Decay; Assassin's Trophy; Witherbloom Command; Grist, the Hunger Tide.

**Zero fully verified effects.** All 21 distinct lands still need independent source pinning (18 names have no partial land mana implementation), and **Arcane Signet, Phyrexian Altar, Skullclamp and Sol Ring** also still need pinned independent card text. Original full simulator not patched; historical original compiler 15 failures not fixed.

## Evidence-location warning for Phases 1–4

The v0.8 ZIP contains snapshots of earlier *reference* implementation and tests and some historical compiler fixtures, but it may **not** contain full primary Phase 1–4 reports or the original full simulator. Do not reconstruct unobservable work as fact from later summaries. List missing documents and lower confidence appropriately. Original source acquisition is a blocker, not license to fill mechanics from intuition.

## Stop/go gates

Before any optimization: independently sourced card texts; actual original compiler integrated/tested; validated all 65 nonland paths plus land behaviors; stack/priority, explicit mana/zone/trigger semantics, test challenge probes and multiplayer calibration as separately authorized. Hold all deck changes, performance scoring, replacement sweeps and simulation predictions. **New session begins with eight-phase audit, not Phase 9.**
