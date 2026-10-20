# C41–C94 consolidated execution status (54/54) — 2026-10-18

Kernel v0.8+R02+R01+R47+R48. Reference fixtures: 420. Statuses from the live test classes; per-contract substitutions are in each class and in `VALIDATION_RESULTS.json → contracts_executed`. None Oracle/CR-authenticated.

| Status | Count |
|---|---:|
| BLOCKED_UNSUPPORTED | 27 |
| EXECUTED | 8 |
| EXECUTED_WITH_SUBSTITUTION | 17 |
| PARTIAL_EXECUTED | 2 |

| Contract | Issues | Status | Tests | Expected failures |
|---|---|---|---:|---:|
| C41 | R22 | EXECUTED_WITH_SUBSTITUTION | 3 | 0 |
| C42 | R22,R21 | EXECUTED_WITH_SUBSTITUTION | 4 | 0 |
| C43 | R23,R06,R09 | EXECUTED_WITH_SUBSTITUTION | 3 | 0 |
| C44 | R23 | EXECUTED_WITH_SUBSTITUTION | 2 | 0 |
| C45 | R24,R01 | EXECUTED | 2 | 0 |
| C46 | R25,R14 | EXECUTED | 2 | 0 |
| C47 | R26,R14 | EXECUTED | 3 | 0 |
| C48 | R27,R14 | EXECUTED | 3 | 0 |
| C49 | R27,R30 | EXECUTED | 2 | 0 |
| C50 | R27 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C51 | R28,R13 | EXECUTED_WITH_SUBSTITUTION | 2 | 0 |
| C52 | R28,R24 | EXECUTED_WITH_SUBSTITUTION | 1 | 0 |
| C53 | R29 | EXECUTED_WITH_SUBSTITUTION | 1 | 0 |
| C54 | R29 | EXECUTED | 1 | 0 |
| C55 | R30,R21 | EXECUTED | 2 | 0 |
| C56 | R30,R23 | EXECUTED_WITH_SUBSTITUTION | 1 | 0 |
| C57 | R31,R14 | EXECUTED_WITH_SUBSTITUTION | 1 | 0 |
| C58 | R31 | EXECUTED_WITH_SUBSTITUTION | 3 | 0 |
| C59 | R31 | EXECUTED | 2 | 0 |
| C60 | R32 | EXECUTED_WITH_SUBSTITUTION | 2 | 0 |
| C61 | R32 | EXECUTED_WITH_SUBSTITUTION | 4 | 0 |
| C62 | R33 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C63 | R33,R01 | EXECUTED_WITH_SUBSTITUTION | 3 | 0 |
| C64 | R34 | EXECUTED_WITH_SUBSTITUTION | 2 | 0 |
| C65 | R35 | EXECUTED (S9) | 1 | 1 |
| C66 | R35 | EXECUTED (S9) | 1 | 1 |
| C67 | R35,R38 | EXECUTED (S9) | 2 | 2 |
| C68 | R35,R15 | EXECUTED (S9) | 1 | 1 |
| C69 | R36 | PARTIAL_EXECUTED | 4 | 0 |
| C70 | R36,R37,R38 | EXECUTED (S14) | 1 | 1 |
| C71 | R37 | EXECUTED (S14) | 1 | 1 |
| C72 | R37 | EXECUTED (S14) | 1 | 1 |
| C73 | R38 | EXECUTED (S9) | 1 | 1 |
| C74 | R38 | EXECUTED (S14) | 1 | 1 |
| C75 | R39 | PARTIAL_EXECUTED (S14) | 1 | 1 |
| C76 | R40 | PARTIAL_EXECUTED (S14) | 1 | 1 |
| C77 | R40 | EXECUTED (S14) | 4 | 4 |
| C78 | R41 | EXECUTED_WITH_SUBSTITUTION | 1 | 0 |
| C79 | R42 | EXECUTED_WITH_SUBSTITUTION | 5 | 0 |
| C80 | R41,R43 | BLOCKED_UNSUPPORTED | 2 | 0 |
| C81 | R42 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C82 | R42 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C83 | R43 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C84 | R43 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C85 | R44 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C86 | R44 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C87 | R45 | EXECUTED_WITH_SUBSTITUTION | 2 | 0 |
| C88 | R45 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C89 | R45,R18 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C90 | R45 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C91 | R46 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C92 | R46 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C93 | R46,R20 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C94 | R41,R43 | BLOCKED_UNSUPPORTED | 1 | 0 |

## Kernel disagreements found by execution (both PROMOTED 2026-10-18, see R47_R48_PATCH_NOTES.md)
- **R47** (C61): Ribtruss Roaster end-step trigger snapshots the +1/+1 counter count at trigger time; CR 608.2h reads it at resolution.
- **R48** (C79): the Yawgmoth -1/-1 state-based death path calls `destroy()`, so an indestructible creature at toughness 0 survives; CR 704.5f puts it into the graveyard regardless.
- (R01, already promoted) Pest Rescuer predicate.

## Blocked mechanics (what the kernel must model before the BLOCKED contracts can execute)
offspring/copy tokens; Chatterfang activation and -X/-X; opponent permanents and targeting (Blood Artist, Abrupt Decay, Trophy, Rise); lore counters and a phase/step clock; devour; Beledros untap; Treasure mana ability; command-zone replacement; regeneration; hexproof/exile; Channel; modal spells (Charms, Command); Grist; Shigeki; all 18 unsupported lands (conditional ETBs, surveil, MDFC faces, fetch, utility activations, painlands, Castle Locthwain, symmetrical draws).


S9 (2026-10-18): C65, C66, C67, C68 and C73 executed against the promoted kernel once the nine B/G fixer lands became playable (pab_lands_s9.py); see C65_C77_EXECUTION_NOTES.md.

S14 (2026-10-18): C70, C71, C72, C74, C77 executed; C75, C76 partially executed (Boseiju channel has no target; opponents have no hands); see C65_C77_EXECUTION_NOTES.md.

## CP21 re-status (2026-10-19)

C80–C86 and C88–C94 were BLOCKED_UNSUPPORTED because their probes called the event kernel `pab_kernel.Game.add()`; S15/S16/S20 model the cards on `pab_kernel.PhysicalZoneGame` (EVIDENCE/CP19_CONTRACT_PATH_AUDIT.md c.3/c.4). Each class in `tests/test_c78_c94_contracts.py` now has `test_pzg_*` methods on PhysicalZoneGame and keeps the old refusal as `test_event_kernel_control_add_refused`. Claims source: the class's former "not modeled (…)" list plus the rules_contract column of `upstream_frozen/PABTRV3_MECHANICAL_INVENTORY.csv` (this file had no per-contract claim list). Reference fixtures: 828.

| Contract | Before | After | Not asserted / stand-in |
|---|---|---|---|
| C80 | BLOCKED_UNSUPPORTED | EXECUTED | — |
| C81 | BLOCKED_UNSUPPORTED | EXECUTED | — |
| C82 | BLOCKED_UNSUPPORTED | EXECUTED_WITH_SUBSTITUTION | deathtouch via the `_deathtouch()` predicate, not combat; opponent-owned body re-declared (no opponent cards) |
| C83 | BLOCKED_UNSUPPORTED | PARTIAL_EXECUTED | "can't be countered": no counterspell model |
| C84 | BLOCKED_UNSUPPORTED | PARTIAL_EXECUTED | opponent's basic-land search (traced unmodeled) |
| C85 | BLOCKED_UNSUPPORTED | EXECUTED_WITH_SUBSTITUTION | opponent's choice = S8 `edict_choice()` stand-in |
| C86 | BLOCKED_UNSUPPORTED | EXECUTED | — |
| C88 | BLOCKED_UNSUPPORTED | EXECUTED | — |
| C89 | BLOCKED_UNSUPPORTED | EXECUTED | — |
| C90 | BLOCKED_UNSUPPORTED | EXECUTED_WITH_SUBSTITUTION | "nonlegendary" = hand-written `LEGENDARY_CARDS` name set |
| C91 | BLOCKED_UNSUPPORTED | EXECUTED_WITH_SUBSTITUTION | creature-card static by name (S16), not a type line (n3) |
| C92 | BLOCKED_UNSUPPORTED | PARTIAL_EXECUTED | Insect-card repeat: unreachable with this deck |
| C93 | BLOCKED_UNSUPPORTED | PARTIAL_EXECUTED | target bookkeeping, A-S20-10 (CP22) |
| C94 | BLOCKED_UNSUPPORTED | PARTIAL_EXECUTED | target bookkeeping, A-S20-10 (CP22); opponent mill unmodeled |

C41–C94 counts after CP21 (the table at the top is the R02-era snapshot and is left as written):

| Status | Before CP21 | After CP21 |
|---|---:|---:|
| BLOCKED_UNSUPPORTED | 16 | 2 (C50, C62) |
| EXECUTED | 19 | 24 |
| EXECUTED_WITH_SUBSTITUTION | 16 | 20 |
| PARTIAL_EXECUTED | 3 | 8 |

C50 and C62 define `KERNEL_PROBE`; release check `BlockedContractsProbed` (21st) fails if a BLOCKED_UNSUPPORTED class has no probe or its probe reports the action accepted on PhysicalZoneGame. SUBSTITUTIONS text for C41, C42, C44, C57, C60, C78, C79, C87 now names the layer that models the card (CP19 note n1); statuses unchanged.

## C95–C99 (in VALIDATION_RESULTS.json, previously undocumented)

Added in CP22 (docs only; no status or test changes). Values from `VALIDATION_RESULTS.json → contracts_executed` and the live classes: C95, C96, C98, C99 in `tests/test_turn_clock_s2.py`; C97 in `tests/test_priority_s3.py`. None Oracle/CR-authenticated.

| Contract | Issues | Status | Tests | Expected failures |
|---|---|---|---:|---:|
| C95 | R50,R01 | EXECUTED | 3 | 0 |
| C96 | R51 | EXECUTED | 4 | 0 |
| C97 | R24,R48 | EXECUTED_WITH_SUBSTITUTION | 3 | 0 |
| C98 | R22,R32,R50 | EXECUTED | 5 | 0 |
| C99 | R49,R32 | EXECUTED | 2 | 0 |

C97 substitution: the synthetic "one effect gives two creatures -1/-1" is applied by direct `minus_counters` mutation; no card is modeled for it.

All 59 contracts in `VALIDATION_RESULTS.json` (C41–C99) after CP22: EXECUTED 28, EXECUTED_WITH_SUBSTITUTION 21, PARTIAL_EXECUTED 8, BLOCKED_UNSUPPORTED 2.
