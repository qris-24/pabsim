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
| C70 | R36,R37,R38 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C71 | R37 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C72 | R37 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C73 | R38 | EXECUTED (S9) | 1 | 1 |
| C74 | R38 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C75 | R39 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C76 | R40 | BLOCKED_UNSUPPORTED | 1 | 0 |
| C77 | R40 | PARTIAL_EXECUTED | 4 | 0 |
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
