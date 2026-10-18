# PABTRV3 — Phase 7 engineering report

**Date:** October 17, 2026  
**Build:** `pab_reliability_v0_7`  
**Scope:** Frozen Savra deck; deterministic reference and limited opt-in physical-zone/event-kernel integration. **No optimization or multiplayer modeling.**

## Results and preservation

- `python run_validation.py`: **257/257 distinct tests pass; zero failures/errors/skips**. This includes all 149 historical event fixtures, 56 Phase 6 physical-zone fixtures, and 52 new Phase 7 integration fixtures.
- **Additional compatibility gate:** the complete historical 149-test v0.5 suite was loaded separately and run again against the `pab_focus_engine_v07.Game` candidate: **149/149 passing**. Those are *replays* and do not increase the count of distinct tests. This is not the original 25-contract card-text compiler suite.
- The original `pab_focus_engine.py`, `pab_zones.py`, inherited tests, and frozen deck/audit inputs remain unchanged. Phase 6 snapshots are retained in `frozen_phase6/`. Source fingerprints and a packaged manifest allow independent verification.
- The frozen deck remains exactly **1 Savra commander + 99 mainboard (34 land copies, 65 nonlands) + separate 1 Pest Summoning Lesson**, with SHA-256 `c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381`.

## Engineering changes: bounded bridge, not wholesale integration

### A. Versioned draw call normalization

`pab_focus_engine_v07.py` is a **separate copy** of the historical isolated event kernel. Previously Moldervine Reclamation, Dark Prophecy, Yawgmoth, Village Rites/Deadly Dispute and Plumb the Forbidden bypassed `_fixture_draw` and merely incremented `cards_drawn`. Those five code locations now route through the common draw method without otherwise changing their trigger or sacrifice logic. The v0.7 candidate uses *canonical inherited token kinds, permanent types and exception classes*; it therefore passed all 149 original isolated tests in a second replay. It also retains the explicit fixture creature power after reference reanimation rather than quietly changing `power=3` to `power=1`.

### B. Real drawn cards for opted-in event fixture

`PhysicalZoneGame` is opt-in. A trigger from the versioned Game may draw actual physical card UIDs from `DeckZones.library` into `DeckZones.hand`; it never fabricates a card to satisfy a draw. It records the identities, preserves seeded library ordering, and increments `cards_drawn` **only for successful physical draws**. If the requested draw exceeds available library contents, a failed-draw trace and `unadjudicated_empty_library_draw` flag are recorded. **This is not a working loss-by-draw state-based-action handler**; do not use for deck outcomes.

The historical `Game.hand` list still exists for fixture-only effects. It is not a reconciled physical hand, and the new bridge does not claim that all old hand-mutating abilities have been converted.

### C. Actual basic-land search and mapped ETB reference event

`Sakura-Tribe Elder` and the **basic Forest only** subset of `Nature's Lore` can search the physical 99-card library for a specified *real UID*, shuffle the remaining cards and place the physical card on battlefield. A separate mapped Game permanent receives the event identity: Sakura's selected basic enters **tapped**; Nature's selected basic Forest enters **untapped**. The explicit search decision is resolved at the search step (not incorrectly fixed as a spell target). The qualified-search option to find nothing is represented. Selection failures, impossible mana, invalid card types, and moved candidates have negative tests.

The three provisional land names (Forest, Swamp, Command Tower) in v0.6 remain **not independently Oracle-pinned**; the other 18 distinct land names still intentionally refuse unsupported land plays. **No shared Game/DeckZones mana pool exists**; spell mana tests supply fixture mana explicitly.

### D. Persistent creature IDs through controlled death and recursion

`enter_linked_creature` explicitly starts with an actual physical card in hand, then creates a mapped Game event permanent. A linked creature's sacrifice or destruction moves **the same physical card UID** to graveyard; a supported reanimation pathway moves that same UID back onto the battlefield even if the Game event UID changes. Reference flows tested include Reassembling Skeleton, Teacher's Pest, Unearth, and the linked card's second death; Phyrexian Reclamation physically returns a linked graveyard card to hand. `assert_bridge_integrity()` rejects a missing/moved linked object or double use of one physical UID. **Unlinked Game fixture objects, other hand/zone effects, tokens and general spells remain unintegrated.** The bridge does not provide a complete transaction system or exhaustive Commander state-based actions.

### E. Physical discard and Lesson identity

In bridge mode, cycling Unearth must use the *real physical Unearth* from hand: the card goes to graveyard, and resolving the cycling trigger draws from the real library. A fake hand-list string cannot pass. The pod-specific opt-in Learn house rule moves the single physical Pest Summoning Lesson from outside_game to hand; without opt-in the action fails before making a Pest. **This does not make Learn outside-game rules universally legal Commander behavior.**

## Honest coverage and stop conditions

| Measurement | v0.6 | v0.7 |
|---|---:|---:|
| Distinct passing deterministic tests | 205 | **257** |
| Additional replay of old 149 against candidate | — | **149/149** |
| Partial-reference mainboard nonlands | 54/65 | **54/65** |
| Mainboard nonlands without behavior | 11/65 | **11/65** |
| Fully verified card effects | 0 | **0** |
| Land names with provisional limited probes | 3/21 | **3/21** |
| Land entries independently source-verified | 0/21 | **0/21** |
| Full source compiler contracts repaired | 0 | **0** |

**Eleven nonlands still lack dedicated behavior:** Witherbloom Charm; Grisly Salvage; Golgari Charm; Heroic Intervention; Infuse with Vitality; Shigeki, Jukai Visionary; Rise of the Witch-king; Abrupt Decay; Assassin's Trophy; Witherbloom Command; Grist, the Hunger Tide.

No full 65/65 mechanics or land Oracle certification. The inherited full simulator's `engine.py`, `oracle.py` and standalone `golgari_commander.json` were **not available here as editable/reference sources**. No live internet Oracle checks were made. Historic original compiler contracts are **10 passes / 15 failures**, previously recorded and **not rerun**. Card-effect coverage is not win-rate evidence; all optimizer values remain `null` and missing effects are **unknown, never zero-valued**.

## Next prioritized engineering gates

1. **Source acquisition and protection:** original editable `engine.py` and `oracle.py`; the cited `golgari_commander.json`; pinned Oracle text for all 21 distinct lands and Arcane Signet / Phyrexian Altar / Skullclamp / Sol Ring, with source dates and provenance. Preserve the original bytes.
2. **Bridge completeness:** converge both pools of mana safely; unify true physical hand operations and drawn-card identity through spell/cycling/reclamation effects; implement explicit token lifecycle mapping and a real empty-library-draw SBA. Add negative tests for zones moved after abilities were activated and for legal counter/response handling.
3. **Card typing and library:** source-verify exact type lines, mana values, modal spell decisions, and target restrictions before implementing Grisly Salvage, Shigeki, and Witherbloom Command. Fail loudly on missing source metadata.
4. **Original compiler repairs:** integrate into a versioned copy of full simulator when available, replay original 25 historical signature contracts, and repair the known Pest/Magecraft/Saga/trigger omissions. Do not infer repair from the replay of the *different* 149-event suite.
5. **Hold optimization:** no numerical predictions or card replacements until all explicit accuracy/coverage gates pass and the user approves deck changes.

**No deck edit, replacement sweep, optimization score or multiplayer simulation occurred in Phase 7.**
