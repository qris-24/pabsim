# PABTRV3 — Phase 6 engineering report

**Date:** October 17, 2026  
**Build:** `pab_reliability_v0_6`  
**Scope:** Frozen-deck physical card identity and zone correctness, limited mana/land probes, and deterministic tests. **No deck evaluation.**

## Verified local outcome

`python run_validation.py`: **205/205 tests passed, 0 failures, 0 errors, 0 skips**. This comprises the **149 unchanged v0.5 tests** and **56 new v0.6 tests**. The isolated Phase 5 `pab_focus_engine.py` and all its five original test files are byte-for-byte unmodified; snapshots are saved in `frozen_phase5/`.

The frozen accepted deck is unchanged: **Savra, Queen of the Golgari (commander), 99 mainboard cards (34 lands, 65 nonlands), and separate Pest Summoning Lesson**. Baseline SHA-256: `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`.

## New standalone physical-zone kernel

`pab_zones.py` constructs **101 distinct physical card objects** with persistent unique identities: 99 mainboard cards in the library, Savra in the command zone, Pest Summoning in outside-game sideboard. The 34 lands include **6 separate Forest cards and 9 separate Swamp cards**. It never creates a fake card to meet a draw/search and tracks owner separately from battlefield controller.

The prototype supports seeded, reproducible library shuffles; draws from the real top of library into actual hand objects; empty-library draw attempts; milling to graveyard; discard; exile; return from graveyard to hand; and ordered moves to top/bottom of library. It removes tokens that leave the battlefield at a modeled state-based-action checkpoint, without leaving retrievable token cards. **There is no spell priority/stack engine or adjudication of the draw-from-empty-library game loss.** The learned Lesson stays out of the deck and can only be retrieved with the recorded opt-in pod house rule.

Search checks actual eligible card UIDs, moves exactly the selected object, then shuffles the remaining library. It distinguishes mandatory unrestricted library searches (must choose a card while library nonempty) from quality-qualified hidden-zone searches, which may fail to find even with valid matching cards present. `resolve_demonic_tutor` performs **only the unrestricted card-to-hand search and shuffle**; it does not put or cast Demonic Tutor on a stack or pay {1}{B}.

**Provisional land behavior**: restricted fixture land plays and taps for **Forest {G}, Swamp {B}, and Command Tower {B} or {G} for Savra**. One land may be played per fixture turn, only if it is a physical card in hand and explicit main-phase/empty-stack flags are supplied. Tapped state and controller checks are enforced. Basic land searches can place selected actual Forest/Swamp cards tapped or untapped. This is **3/21 distinct land names with partial behavior**; the other **18 distinct land names refuse unsupported land plays** pending independently pinned ETB/mana rules. No complete land subsystem or actual shared mana pool between the two kernels exists.

## Truthful coverage

| Measure | Phase 5 | Phase 6 |
|---|---:|---:|
| Passing isolated deterministic tests | 149 | **205** |
| Nonlands with at least one partial reference path | 53/65 | **54/65** |
| Nonlands without a dedicated reference behavior | 12/65 | **11/65** |
| Fully verified nonlands | 0 | **0** |
| Land names with limited play/mana probe | 0 | **3/21** |
| Independently source-verified land names | 0 | **0** |
| Original compiler historical contract failures | 15/25 | **15/25** (not rerun) |

The newly partially modeled nonland is **Demonic Tutor (resolution only)**. The eleven still unsupported are: Witherbloom Charm; Grisly Salvage; Golgari Charm; Heroic Intervention; Infuse with Vitality; Shigeki, Jukai Visionary; Rise of the Witch-king; Abrupt Decay; Assassin's Trophy; Witherbloom Command; Grist, the Hunger Tide.

No mainboard card has fully verified behavior. All missing contributions remain **unknown/unimplemented, not value zero**. `value_for_optimization` remains `null` for all registry entries.

## Independence and known failures still to address

1. The new zone prototype and the old `Game` event kernel are **not integrated**: draws inside `pab_focus_engine.Game` still increment a counter; its graveyard, hand, and basic-land fixtures are still separate, and its lands do not tap to produce actual mana. The two systems must **not** be treated as one playable engine.
2. Source text remains **not independently pinned** for all 21 land entries, and for Arcane Signet, Phyrexian Altar, Skullclamp and Sol Ring. `golgari_commander.json` was referenced in the inherited audit, not directly supplied as an independent verified Oracle source in this package. This session did not claim live Oracle verification.
3. No general enter-the-battlefield replacement effects; conditional duals, pathway faces, land types, modal choices, surveil, channel, fetch abilities, and nonbasic Forest/Swamp tutor behavior remain unsupported. Only explicit probe paths are implemented.
4. No general casting, timing authority, targeting, response window, arbitrary stack, APNAP, state-based-action/layer engine, resolved opponent board, or calibrated policy. The `main_phase`/`stack_empty` flags are injected test assumptions, not proof of a real turn manager.
5. The historical original `engine.py`/`oracle.py` were unavailable in editable form here. Original 25 compiler contract outcomes remain *saved historical results*: 10 pass and 15 fail; no compiler repair/re-execution or full-engine patch occurred.

## Phase 7 priority plan

1. **Source gate:** acquire the original editable `engine.py`, `oracle.py`, `golgari_commander.json`, and independent pinned Oracle text for 21 distinct lands and 4 colorless-source cards. Preserve original bytes and provenance.
2. **Zone-event integration:** build an opt-in, trace-checkable adapter between the physical card zones and v0.5 Game events. Replace only one old counter or fixture path at a time (first a draw, then an actual searched basic land, then a physical graveyard card), with comparison tests proving no duplicate effects or lost identities.
3. **Land-entry behavior:** source-first tests for each of the remaining 18 distinct lands, including tapped checks, actual subtype requirements, conditional entry, and mana production. Verify the six Forests and nine Swamps as separate identities throughout search and recursion.
4. **Remaining unsupported nonlands:** start with Grisly Salvage once physical card types are source-verified, then Shigeki and Witherbloom Command; reserve protection, modal target locking, symmetrical sacrifice, and planeswalker behavior for dedicated positive and negative fixtures.
5. **Full validation before optimization:** general stack/casting/priority and compiler contract integration. No win-rate forecasts or card swap scores until all explicit gates pass.

**STOP:** Frozen deck unchanged. No multiplayer simulation, card recommendations, mass replacement sweep, or acceptance of adds/cuts. This is a locally validated reference-fixture build, not Commander rules certification.
