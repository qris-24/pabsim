# Phase/step clock — dependency map and staged design (DESIGN ONLY; implementation not authorized)

Audit date 2026-10-18. Kernel v0.8+R02+R01+R47+R48. CR evidence: `EVIDENCE/CR_20260619_EVIDENCE.json` (MagicCompRules 20260619, SHA 7c9cd7e8…).

## 1. Upkeep/trigger audit results (read-only)

| Item | Finding | Evidence | Disposition |
|---|---|---|---|
| Pest Rescuer "each upkeep" | Card text: "At the beginning of each upkeep, if you don't control a Pest creature token…" (two web sources; official feed unreachable). Kernel `begin_upkeep()` takes no player and has no active-player state; it fires Rescuer + Beledros on every call. Caller discipline, not the engine, decides whose upkeep it is. | `tests/test_upkeep_trigger_audit.py::ActivePlayerAbsent`; inventory CSV already says "Each upkeep (not just yours)" for Beledros | **R50 — coverage gap, not a wrong result.** Blocked on the clock. Proposed C95. |
| "Your end step" cards (Moseo, Roaster) | `roaster_end_step()` / `moseo_end_step()` fire whenever called; no guard against being invoked on an opponent's end step. | audit test `test_your_end_step_cards_cannot_be_scoped_to_a_player` | Part of R50. Proposed C98. |
| Mana emptying | CR 106.4: pools empty at the end of each step and phase. Kernel never empties (reset_turn, fixture_new_turn keep the pool). | audit test `test_mana_pool_not_emptied_by_any_turn_reset`; A05 | **R51 — coverage gap.** Proposed C96. |
| Until-end-of-turn expiry | CR 514.2. Kernel: `reset_turn()` clears `indestructible_until_eot` and `life_gained_turn` — correct effect, caller-driven timing. | audit tests | OK under caller discipline; clock should own it. |
| Intervening-if (603.4) | Checked at trigger and resolution (R01). | audit `InterveningIf` | Confirmed. |
| **R47 review** | Live counter count at resolution: correct per 608.2h first sentence. **Source-left branch is wrong**: 608.2h second sentence requires last known information; R47 creates nothing. | audit `R49RoasterSourceLeftLKI` (expectedFailure + pin) | **R49 — fixed and promoted** (LKI fallback; see R49_S1_PATCH_NOTES.md). |
| **R48 review** | CR 704.5f verbatim: toughness ≤0 → graveyard; regeneration can't replace it. Indestructible irrelevant. Kernel now performs the check after the ability's full resolution (counter → draw → SBA), consistent with 704.3/117.5. | audit `R48Confirmed` | Confirmed. Yawgmoth's own text was not re-fetched (pages unreachable); R48 rests on the CR, not the card. |

## 2. What the clock must provide (components)

| # | Component | CR | Kernel today |
|---|---|---|---|
| K1 | Turn order and **active player** (4 seats, APNAP) | 500.1, 603.3b | none |
| K2 | **Steps/phases** as explicit state: untap, upkeep, draw, main 1, combat (begin/attack/block/damage/end), main 2, end, cleanup | 500.x–514.x | none; `begin_upkeep`, `*_end_step`, `reset_turn` are caller-invoked |
| K3 | **Step-boundary trigger admission**: "at the beginning of [step]" for the active player's step vs each player's | 503.1, 513.1, 603.2 | per-method, unscoped |
| K4 | **Mana pool emptying** at every step/phase end | 106.4 | never |
| K5 | **Priority loop**: SBA check → triggers to stack (APNAP, controller orders) → priority | 117.5, 704.3, 603.3b | triggers resolve FIFO from a deque; SBA only inside specific abilities |
| K6 | **Until-end-of-turn expiry** and cleanup | 514.2, 500.4 | `reset_turn()` partial |
| K7 | **Turn-based actions**: untap (502.3), draw (504.1), land-play count reset | 502–504 | bridge `fixture_new_turn()` partial |
| K8 | **LKI** for sources that leave before resolution | 608.2h, 113.7a | absent (R49) |

## 3. What each component unblocks

| Component | Contracts / issues it unblocks or de-substitutes |
|---|---|
| K1 + K3 | C95, C98 (R50); C63 loses its queue-reordering substitution; C41 gains a real end-step boundary; C44's command-zone removal is unrelated (needs zones) |
| K2 + K6 | C41 (step clock), C42 (response-window timing), C60/C61 (end-step admission), C79 expiry control becomes clock-driven |
| K4 | C96 (R51); C77 gains pool-expiry assertions; all mana tests stop assuming persistence |
| K5 | C97; C52/C78 SBA deaths become engine-driven instead of ability-internal; C53 trigger ordering becomes APNAP-driven; R48's in-ability SBA call becomes a general check |
| K7 | C57/C58 lore-counter advancement (precombat main), C64 draw-step draws on the physical bridge, C74 Castle Locthwain draw ordering |
| K8 | C99 (R49) |

Not unblocked by the clock (need other work): opponent permanents/targeting (C52, C53, C83–C86), copy tokens (C50), modal spells (C80, C94), Channel (C75, C89–C90), Grist/Shigeki (C88–C93), all 18 lands' card-specific mechanics (C65–C76), command-zone replacement (C44), devour (C60), Beledros untap (C62), Treasure mana (C43/C56).

## 4. Staged design (each stage a separate authorized session, versioned candidate → promotion)

| Stage | Scope | Stop condition |
|---|---|---|
| S1 ✅ promoted 2026-10-18 | `TurnClock` object: seats, active player, current step; `advance()` emits step-boundary events; **no behaviour change** to existing methods (they keep working when called directly) | done: `pab_turn_clock.py`, 11 fixtures, all prior fixtures unchanged |
| S2 ✅ promoted 2026-10-18 | Route `begin_upkeep`/`*_end_step` through boundary events with player scoping (K3); add K4 pool emptying at boundaries; K6 expiry at cleanup | done: `pab_clock_s2.py`; C95, C96, C98, C99 executed; C63's clock substitution removed (queue-order choice remains) |
| S3 ✅ promoted 2026-10-18 | Priority loop K5: SBA check between resolutions (look-back for simultaneous deaths), controller trigger ordering API; Yawgmoth's inline check retired (Skullclamp's immediate check kept: equip has no stack here) | done: `pab_clock_s3.py`; C97 executed; C63 fully de-substituted; C52 still needs opponent permanents; C78 still needs Golgari Charm |
| S4 ✅ promoted 2026-10-18 | K7 turn-based actions (untap, draw, land window) on event kernel and physical bridge; K8 LKI was delivered earlier with R49 | done: `pab_clock_s4.py`; opponents' draws remain unmodeled (no opponent libraries) |

| S5 ✅ promoted 2026-10-18 | Integrated turn loop over existing capabilities with invariants at every boundary (`pab_turn_loop.py`) | done; hard stop reached (see HARD_STOP_2026-10-18.md) |

Rules for every stage: frozen files untouched; new layer module + `pab_kernel.py` promotion; tests that pin the pre-clock behaviour stay as frozen-engine pins; reference count pinned in the runner; manifest regenerated; approval before promotion.

## 5. Locked
Deck and Lesson unchanged. Phase 9 NO-GO. No replacement sweeps, rankings or performance claims. 0 cards certified. This document authorizes nothing.
