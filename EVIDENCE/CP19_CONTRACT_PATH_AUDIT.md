# CP19 — Contract engine-path audit (read-only, 2026-10-19)

Scope: `run_validation.py`, `build_manifest.py`, `pab_kernel.py`, `pab_cast_s15.py`, `pab_grist_s16.py`,
`pab_shigeki_s20.py`, the four contract test files, and a grep for C95–C99 in `tests/`. One probe script
outside the repo (`..\cp19_probe.py`, output `..\cp19_probe.txt`, not committed). Nothing fixed.
Line numbers are those of the files at commit 345474d (CP18).

## (a) Manifest metadata

| key | file:line | hardcoded / derived | value |
|---|---|---|---|
| `scope` | `build_manifest.py:25` | hardcoded string literal | "frozen Savra deterministic rules reference only; R02 runner integrity + R01 … + R48 zero-toughness SBA promoted; …" — describes R02/R01/R47/R48 only; no S-stage or CP mentioned |
| `patches` | `build_manifest.py:26` | hardcoded list literal | `["R02", … , "S20", "CP02", "CP03", "CP04", "CP06"]` — 31 entries, stops at CP06 |
| `unique_fixture_tests` | `build_manifest.py:29` | hardcoded int literal | `779` (see (b)) |
| `full_card_verified` | `build_manifest.py:30` | hardcoded int literal | `0` |

The runtime truth for the same two facts is derived elsewhere:
- `pab_kernel.py:30` `PROMOTED` (36 entries) is what `run_validation.py:278` writes to
  `VALIDATION_RESULTS.promoted_patches`.
- `pab_kernel.py:29` `KERNEL_VERSION` is what `run_validation.py:277` writes to `kernel_version`.

PROMOTED entries missing from `build_manifest.py:26` `patches`: **CP10a, CP10b, CP10c, CP13, CP14** (5).
Every entry of `patches` is in PROMOTED; the order is identical for the first 31.

Why the gate does not notice: `run_validation.py:99–108` reads only `build` and `files_sha256` from
`PHASE8_R02_FILE_MANIFEST.json`. `patches`, `scope`, `unique_fixture_tests` and `full_card_verified` are
written by the builder and never read back by the runner, so they cannot drift-fail.

Related hand-written literal in the runner: `run_validation.py:255` `release` ("… through CP16") is a string
literal, not derived from `PROMOTED`; `run_validation.py:254` `scope` likewise. Both lag by hand.

## (b) Fixture count: 779 vs 810

`unique_fixture_tests` does **not** appear in `VALIDATION_RESULTS.json` (its `result` dict,
`run_validation.py:253–310`, has no such key). It lives only in `PHASE8_R02_FILE_MANIFEST.json:263`,
copied from the literal at `build_manifest.py:29`. The literal was last changed in CP06 (commit 4e017ee,
"CP06 approved physical stack zone migration and 15 regression fixtures"); `git log -L29,29` shows no
later edit.

`tests_run` (810) is computed: `run_validation.py:176–178` discovers `tests/test_*.py` and runs them;
`REFERENCE_TEST_COUNT=810` at `:29` is asserted against the static per-file counts at `:117–157`.

Per-file counts (from the asserts at `run_validation.py:117–155`):

| file | tests | added |
|---|---|---|
| five v0.5 files (`OLD_TEST_FILES`) | 149 | ≤ v0.5 |
| test_v06_physical_zones | 56 | v0.6 |
| test_v07_zone_bridge | 52 | v0.7 |
| test_v08_mana_tokens | 54 | v0.8 |
| test_c41_c47 / c48_c64 / c65_c77 / c78_c94 | 19 / 34 / 20 / 23 | R02 era |
| test_v05_r01_corrections | 2 | R01 |
| test_r01_pest_rescuer | 13 | R01 |
| test_upkeep_trigger_audit | 14 | R49 |
| test_turn_clock_s1 / s2 | 10 / 16 | S1 / S2 |
| test_priority_s3 | 11 | S3 |
| test_turn_actions_s4 | 13 | S4 |
| test_integrated_turn_loop_s5 | 7 | S5 |
| test_cast_s6 / s7 | 33 / 71 | S6 / S7 |
| test_r52_village_rites | 4 | R52 |
| test_opponents_s8 | 21 | S8 |
| test_lands_s9 | 18 | S9 |
| test_commander_s10 | 10 | S10 |
| test_interaction_s11 | 12 | S11 |
| test_cast_s12 / s13 | 6 / 10 | S12 / S13 |
| test_lands_s14 | 12 | S14 |
| test_cast_s15 | 13 | S15 |
| test_grist_s16 | 8 | S16 |
| test_combat_s17 | 8 | S17 |
| test_policy_s18 | 9 | S18 |
| test_validation_s19 | 4 | S19 |
| test_shigeki_s20 | 4 | S20 |
| test_auditfix_cp02 / cp03 / cp04 | 15 / 7 / 6 | CP02–CP04 |
| test_stack_cp06 | 15 | CP06 |
| **subtotal through CP06** | **779** | |
| test_auditfix_cp10 | 17 | CP10a (commit 0c92fe9) |
| test_auditfix_cp13 | 9 | CP13 (commit 44643f0) |
| test_auditfix_cp14 | 5 | CP14 (commit e20bda4) |
| **total** | **810** | |

Verdict: the gap is exactly the three test files added after CP06 (17 + 9 + 5 = 31). The 779 literal is
**STALE**, not a different definition of "unique" (the replays at `run_validation.py:180–223` are not
counted in either number).

## (c) Contract source and engine path

### c.1 Status source (VALIDATION_RESULTS `contracts_executed`)

Collected at `run_validation.py:225–241`. For every class with a `CONTRACT` attribute in the six
contract modules (`:229`):

| field | source | line |
|---|---|---|
| `status` | **literal** — the class attribute `STATUS` in the test file, copied verbatim | `:235` |
| `substitutions` | **literal** — class attribute `SUBSTITUTIONS`, copied verbatim | `:236` |
| `issues` | literal — class attribute `ISSUES` | `:235` |
| `tests_run`, `tests_passed`, `expected_failures`, `unexpected_successes` | **computed** from a fresh run of that class | `:234–238` |
| `engine_test_executed` | **derived from the literal**: `cls.STATUS!='BLOCKED_UNSUPPORTED'` | `:239` |
| `oracle_cr_authenticated` | **literal `False`** for every contract | `:239` |

`contracts_ok` (`:240`) checks only that 59 contracts exist and every one has tests_run > 0 and
passed + expected_failures == run. It never checks a status against the kernel. So a contract keeps its
`BLOCKED_UNSUPPORTED` status for as long as its test file says so, whatever later layers model.

### c.2 Engine path per test file

All four contract files import from `pab_kernel` (the promoted kernel), never from the frozen modules
directly as their engine, with two pinned exceptions.

| file | imports | engine instantiated |
|---|---|---|
| `tests/test_c41_c47_contracts.py:13–14` | constants/`IllegalAction` from `pab_focus_engine`; `Game` from `pab_kernel` | `pab_kernel.Game` (`_Base.game`, `:23`) — event kernel |
| `tests/test_c48_c64_contracts.py:14–16` | constants from `pab_focus_engine`; `ZoneError` from `pab_zones`; `Game, PhysicalZoneGame` from `pab_kernel` | `pab_kernel.Game` (`:25`) for C48–C63; `pab_kernel.PhysicalZoneGame` (`:307, :316`) for C64. C61 additionally instantiates frozen `pab_focus_engine_v07.Game` directly (`:266–267`) in one test that pins the frozen trigger-time snapshot |
| `tests/test_c65_c77_contracts.py:15–17` | `SAVRA, IllegalAction` from `pab_focus_engine`; zone errors from `pab_zones`; `Game, PhysicalZoneGame` from `pab_kernel` | `pab_kernel.PhysicalZoneGame` (`_Land.bridge`, `:26`) for C65–C68, C70–C76; C69 and C77 also use `pab_kernel.Game` (`:105`, `:250`) for the event-fixture / Sol Ring tests; C75 builds `PhysicalZoneGame()` directly (`:213`) |
| `tests/test_c78_c94_contracts.py:13–15` | constants/`BODIES` from `pab_focus_engine`; `DeckZones` from `pab_zones`; `Game` from `pab_kernel` | `pab_kernel.Game` (`_Base.game`, `:23`) for all; C79 additionally instantiates frozen `pab_focus_engine_v07.Game` (`:78–79`) for one pinned frozen-behaviour test; C87 and C91 instantiate frozen `pab_zones.DeckZones` directly (`:141, :148, :175`) with no engine at all |
| `tests/test_turn_clock_s2.py:10,18` (C95, C96, C98, C99) | `Game, PhysicalZoneGame` from `pab_kernel` | `pab_kernel.Game` by default (`_B.game`, `:18`); C96 uses `pab_kernel.PhysicalZoneGame` in one test (`:53`) |
| `tests/test_priority_s3.py:9,18` (C97) | `Game` from `pab_kernel` | `pab_kernel.Game` |

Kernel composition (from `pab_kernel.py:26–27` and the probe's MRO line):
- `pab_kernel.Game` = VillageRites → TurnBasedActions (S1–S4) → R47/R48 SBA → R01 → **frozen
  `pab_focus_engine_v07.Game`**. The event kernel: `add(name)` is the frozen BODIES-table path. S6–S20
  are NOT in this class.
- `pab_kernel.PhysicalZoneGame` = VillageRites → CP06 stack → CP03 → CP02 → **S20 Shigeki → S18 → S17 →
  S16 Grist → S15 interaction spells → S14 → … → S6** → S4–S1 → R47/R48 → R01 → frozen
  `pab_zone_bridge_v08` → `pab_zone_bridge` → frozen `pab_focus_engine_v07.Game`. Every card modeled from
  S6 on is modeled here, through `cast_from_hand(physical_uid, …)` and per-card activation methods.

**This is the mechanism behind every STALE_STATUS verdict below.** The sixteen BLOCKED_UNSUPPORTED probes
in `test_c78_c94_contracts.py` (and C50, C62) assert `pab_kernel.Game.add(name)` raises `IllegalAction`
(`_Base.assert_card_refused`, `:26–31`). That is the frozen event-kernel `add()`; it still refuses, so the
tests still pass. The layers that model these cards (S15, S16, S20) extend `PhysicalZoneGame.cast_from_hand`
and add methods the probes never call. The tests measure the wrong path.

### c.3 Probe

`..\cp19_probe.py` builds `pab_kernel.PhysicalZoneGame()`, adds Savra, moves the card from the physical
library to hand, adds mana and calls the current path. KERNEL_VERSION line and MRO line were recorded in
`..\cp19_probe.txt`. Summary lines (the only lines read):

| contract | current path called | result | observation |
|---|---|---|---|
| C50 | `cast_from_hand(uid, offspring=True)` on Starscape Cleric; `dir(g)` for "offspring" | **refused** | `TypeError` unexpected keyword in `pab_cast_s7._cast_creature_s7`; no offspring attribute. `pab_cast_s7.py:63` comment: "Offspring {2}{B} not modeled" |
| C62 | `dir(g)` for beledros / pay_ten / untap_all | **refused** | no such method on PhysicalZoneGame |
| C80 | `cast_from_hand(uid, mode=1, sacrifice_uid=pest)` → `pab_cast_s15._s15_witherbloom_charm` | accepted | pest sacrificed, drew 2, card to graveyard |
| C81 | `cast_from_hand(uid, mode=3)` → `_s15_golgari_charm` | accepted | 2 regeneration shields; Pest survives `destroy()` |
| C82 | `cast_from_hand(uid, target_uid=pest)` → `_s15_infuse_with_vitality` | accepted | `infused_eot` set, gained 2 |
| C83 | `cast_from_hand(uid, target_uid=pest)` → `_s15_abrupt_decay` | accepted | target destroyed |
| C84 | `declare_opponent_board` + `cast_from_hand(uid, target_uid=<opp body>)` → `_s15_assassins_trophy` | accepted | opponent permanent destroyed; basic-land search traced unmodeled |
| C85 | `cast_from_hand(uid, sacrifice_uid=pest)` → `_s15_rise_of_the_witch_king` | accepted | own creature sacrificed; opponent seat 1 edicted to 0 creatures |
| C86 | same | accepted | same |
| C88 | cast Shigeki, `shigeki_activate(uid)` → `pab_shigeki_s20.ShigekiMixin.shigeki_activate` | accepted | returned to hand, library −4, reveal traced |
| C89 | `channel_shigeki(uid, [card])`, X=1 → `ShigekiMixin.channel_shigeki` | accepted | card returned to hand, Shigeki discarded |
| C90 | `channel_shigeki(uid, [legendary card])` | accepted (path exists) | legendary target refused with `BridgeError: S20: X distinct nonlegendary cards` — the exclusion IS modeled |
| C91 | `cast_from_hand(uid)` on Grist → `pab_grist_s16.GristMixin.cast_from_hand` | accepted | on battlefield, loyalty 3, creature False |
| C92 | `grist_plus_one()` → `GristMixin.grist_plus_one` | accepted | loyalty 4, 1 Insect token, 1 milled |
| C93 | `grist_minus_two(sacrifice_uid, target_uid)` → `GristMixin.grist_minus_two` | accepted | loyalty 1, sacrificed, target destroyed, reflexive trigger traced |
| C94 | `cast_from_hand(uid, modes=(1,4), target_player=0, target_opponent=1)` → `_s15_witherbloom_command` | accepted | milled 3, opponent 1 lost 2 |

Accepted 14 / refused 2.

### c.4 Verdict table

Results status = `VALIDATION_RESULTS.contracts_executed[C].status` (identical to the test-file literal).
Engine path abbreviations: K.Game = `pab_kernel.Game`; K.PZG = `pab_kernel.PhysicalZoneGame`;
v07 = frozen `pab_focus_engine_v07.Game` instantiated directly; DZ = frozen `pab_zones.DeckZones`.

| contract | test class | engine path | results status | layer | probe | verdict |
|---|---|---|---|---|---|---|
| C41 | test_c41_c47_contracts.C41 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT [n1] |
| C42 | test_c41_c47_contracts.C42 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT [n1] |
| C43 | test_c41_c47_contracts.C43 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT |
| C44 | test_c41_c47_contracts.C44 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT [n1] |
| C45 | test_c41_c47_contracts.C45 | K.Game | EXECUTED | — | — | CURRENT |
| C46 | test_c41_c47_contracts.C46 | K.Game | EXECUTED | — | — | CURRENT |
| C47 | test_c41_c47_contracts.C47 | K.Game | EXECUTED | — | — | CURRENT |
| C48 | test_c48_c64_contracts.C48 | K.Game | EXECUTED | — | — | CURRENT |
| C49 | test_c48_c64_contracts.C49 | K.Game | EXECUTED | — | — | CURRENT |
| C50 | test_c48_c64_contracts.C50 | K.Game | BLOCKED_UNSUPPORTED | none (`pab_cast_s7.py:63`: Offspring not modeled) | refused | CURRENT |
| C51 | test_c48_c64_contracts.C51 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT |
| C52 | test_c48_c64_contracts.C52 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT |
| C53 | test_c48_c64_contracts.C53 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT |
| C54 | test_c48_c64_contracts.C54 | K.Game | EXECUTED | — | — | CURRENT |
| C55 | test_c48_c64_contracts.C55 | K.Game | EXECUTED | — | — | CURRENT |
| C56 | test_c48_c64_contracts.C56 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT |
| C57 | test_c48_c64_contracts.C57 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT [n1] |
| C58 | test_c48_c64_contracts.C58 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT |
| C59 | test_c48_c64_contracts.C59 | K.Game | EXECUTED | — | — | CURRENT |
| C60 | test_c48_c64_contracts.C60 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT [n1] |
| C61 | test_c48_c64_contracts.C61 | K.Game + v07 (one pinned test) | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT |
| C62 | test_c48_c64_contracts.C62 | K.Game | BLOCKED_UNSUPPORTED | none | refused | OLD_BASELINE_ONLY (Beledros) |
| C63 | test_c48_c64_contracts.C63 | K.Game | EXECUTED | — | — | CURRENT (Beledros: old-baseline card, see C62) |
| C64 | test_c48_c64_contracts.C64 | K.PZG | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT (Lesson: old-baseline sideboard) |
| C65 | test_c65_c77_contracts.C65 | K.PZG | EXECUTED | S9 | — | CURRENT |
| C66 | test_c65_c77_contracts.C66 | K.PZG | EXECUTED | S9 + S8 | — | CURRENT |
| C67 | test_c65_c77_contracts.C67 | K.PZG | EXECUTED | S9 | — | CURRENT |
| C68 | test_c65_c77_contracts.C68 | K.PZG | EXECUTED | S9 | — | CURRENT |
| C69 | test_c65_c77_contracts.C69 | K.Game + K.PZG | PARTIAL_EXECUTED | — | — | CURRENT |
| C70 | test_c65_c77_contracts.C70 | K.PZG | EXECUTED | S14 | — | CURRENT |
| C71 | test_c65_c77_contracts.C71 | K.PZG | EXECUTED | S14 | — | CURRENT |
| C72 | test_c65_c77_contracts.C72 | K.PZG | EXECUTED | S14 | — | CURRENT |
| C73 | test_c65_c77_contracts.C73 | K.PZG | EXECUTED | S9 | — | CURRENT |
| C74 | test_c65_c77_contracts.C74 | K.PZG | EXECUTED | S14 | — | CURRENT |
| C75 | test_c65_c77_contracts.C75 | K.PZG | PARTIAL_EXECUTED | S14 | — | CURRENT |
| C76 | test_c65_c77_contracts.C76 | K.PZG | PARTIAL_EXECUTED | S14 | — | CURRENT |
| C77 | test_c65_c77_contracts.C77 | K.PZG + K.Game | EXECUTED | S14 | — | CURRENT |
| C78 | test_c78_c94_contracts.C78 | K.Game | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT [n1] |
| C79 | test_c78_c94_contracts.C79 | K.Game + v07 (one pinned test) | EXECUTED_WITH_SUBSTITUTION | — | — | CURRENT [n1] |
| C80 | test_c78_c94_contracts.C80 | K.Game | BLOCKED_UNSUPPORTED | `pab_cast_s15.py` `_s15_witherbloom_charm` (:221) | accepted | STALE_STATUS |
| C81 | test_c78_c94_contracts.C81 | K.Game | BLOCKED_UNSUPPORTED | `pab_cast_s15.py` `_s15_golgari_charm` mode 3 (:236), `regen_shields` | accepted | STALE_STATUS |
| C82 | test_c78_c94_contracts.C82 | K.Game | BLOCKED_UNSUPPORTED | `pab_cast_s15.py` `_s15_infuse_with_vitality` (:258); opponent-owned return `_infuse_return_opponent_body` (:121, CP10 A-S20-11) | accepted | STALE_STATUS |
| C83 | test_c78_c94_contracts.C83 | K.Game | BLOCKED_UNSUPPORTED | `pab_cast_s15.py` `_s15_abrupt_decay` (:208) | accepted | STALE_STATUS |
| C84 | test_c78_c94_contracts.C84 | K.Game | BLOCKED_UNSUPPORTED | `pab_cast_s15.py` `_s15_assassins_trophy` (:214); opponent permanents via `pab_opponents_s8.declare_opponent_board` | accepted | STALE_STATUS |
| C85 | test_c78_c94_contracts.C85 | K.Game | BLOCKED_UNSUPPORTED | `pab_cast_s15.py` `_s15_rise_of_the_witch_king` (:276) | accepted | OLD_BASELINE_ONLY [n2] |
| C86 | test_c78_c94_contracts.C86 | K.Game | BLOCKED_UNSUPPORTED | same | accepted | OLD_BASELINE_ONLY [n2] |
| C87 | test_c78_c94_contracts.C87 | DZ only (no engine) | EXECUTED_WITH_SUBSTITUTION | `pab_cast_s15.py` `_s15_grisly_salvage` (:265) exists | — | CURRENT [n1] |
| C88 | test_c78_c94_contracts.C88 | K.Game | BLOCKED_UNSUPPORTED | `pab_shigeki_s20.py` `ShigekiMixin.shigeki_activate` (:60) | accepted | STALE_STATUS |
| C89 | test_c78_c94_contracts.C89 | K.Game | BLOCKED_UNSUPPORTED | `pab_shigeki_s20.py` `ShigekiMixin.channel_shigeki` (:77) | accepted | STALE_STATUS |
| C90 | test_c78_c94_contracts.C90 | K.Game | BLOCKED_UNSUPPORTED | `pab_shigeki_s20.py` `channel_shigeki` legendary refusal via `LEGENDARY_CARDS` (:34, :81) | accepted | STALE_STATUS |
| C91 | test_c78_c94_contracts.C91 | K.Game + DZ | BLOCKED_UNSUPPORTED | `pab_grist_s16.py` `GristMixin.cast_from_hand` (:77), graveyard LKI as creature card (:100–138) | accepted | STALE_STATUS [n3] |
| C92 | test_c78_c94_contracts.C92 | K.Game | BLOCKED_UNSUPPORTED | `pab_grist_s16.py` `grist_plus_one` (:155) | accepted | STALE_STATUS |
| C93 | test_c78_c94_contracts.C93 | K.Game | BLOCKED_UNSUPPORTED | `pab_grist_s16.py` `grist_minus_two` (:166), reflexive trigger (:178) | accepted | STALE_STATUS (target bookkeeping open: A-S20-10) |
| C94 | test_c78_c94_contracts.C94 | K.Game | BLOCKED_UNSUPPORTED | `pab_cast_s15.py` `_s15_witherbloom_command` (:307) | accepted | STALE_STATUS (target bookkeeping open: A-S20-10) |
| C95 | test_turn_clock_s2.C95 | K.Game | EXECUTED | S2 | — | CURRENT |
| C96 | test_turn_clock_s2.C96 | K.Game + K.PZG | EXECUTED | S2 | — | CURRENT |
| C97 | test_priority_s3.C97 | K.Game | EXECUTED_WITH_SUBSTITUTION | S3 | — | CURRENT |
| C98 | test_turn_clock_s2.C98 | K.Game | EXECUTED | S2 | — | CURRENT |
| C99 | test_turn_clock_s2.C99 | K.Game | EXECUTED | S2 | — | CURRENT |

Totals: CURRENT 43, STALE_STATUS 13, OLD_BASELINE_ONLY 3, UNCLEAR 0.

Notes:
- [n1] Status is accurate (the test really does substitute), but the SUBSTITUTIONS text names a card or
  mechanic as "unsupported / not modeled" that a later layer now models on `PhysicalZoneGame`: C41 High
  Market (S14 `high_market`); C42 Infuse with Vitality (S15); C44 command zone (S10); C57 lore counter /
  phase clock (S2 clock; Saga chapters still direct); C60 Devour (S7 `devour_uids` kw at
  `pab_cast_s7.py:83`); C78 Golgari Charm mode 1 (S15); C79 Heroic Intervention (S15); C87 Grisly Salvage
  (S15). The event-kernel tests were not moved. Stale text, not stale status.
- [n2] Rise of the Witch-king is an old-baseline card (not in PAB v3). The kernel path accepts it (S15), so
  the status is stale on the old-baseline target too; verdict follows the task's fixed assignment.
- [n3] The C91 probe also asserts `DeckZones` cards carry no `types` attribute. That is still true
  (`pab_zones.py` is frozen); S16 makes the creature-card static true by name, not by a type line.

## Proposed fixes (not implemented)

1. `build_manifest.py:26` — derive `patches` from `pab_kernel.PROMOTED` (import the module, or read the
   literal) instead of a hand-copied list; or at minimum append CP10a, CP10b, CP10c, CP13, CP14. Add a
   release-gate check that `manifest.patches == pab_kernel.PROMOTED`.
2. `build_manifest.py:29` — derive `unique_fixture_tests` from the per-file `def test_` count (the same
   regex `run_validation.py:116` uses) or drop the key; today it is 779 against a real 810. Gate check:
   `manifest.unique_fixture_tests == REFERENCE_TEST_COUNT`.
3. `build_manifest.py:25` `scope` and `run_validation.py:254–255` `scope`/`release` — hand-written; either
   derive the stage suffix from `PROMOTED[-1]` or add them to the stage-end checklist.
4. The 13 STALE_STATUS contracts (C80–C84, C88–C94): add a `PhysicalZoneGame` test per contract that
   executes the contract body through the S15/S16/S20 path (the probe calls above are the skeleton), set
   STATUS to EXECUTED / EXECUTED_WITH_SUBSTITUTION / PARTIAL_EXECUTED with honest SUBSTITUTIONS, keep the
   `Game.add()` refusal as a control. Each is a test-file change: REFERENCE_TEST_COUNT, the per-file
   count at `run_validation.py:121`, `release_gate_tests/test_r02_release_gate.py`, registry and manifest
   move with it (session rule). Ledger order first: A-S20-10 (C93, C94 target bookkeeping) before C93/C94
   are re-statused.
5. C85, C86, C62 (old-baseline-only): leave the test as is; when the v3 deck file lands (CP21) record in
   the contract docstring that these contracts belong to the old baseline target only.
6. [n1] contracts: refresh SUBSTITUTIONS text to say "modeled in S<n> on PhysicalZoneGame; this test keeps
   the event-kernel stand-in" so the results record stops calling modeled cards unsupported. Text-only; no
   status or count changes.
7. `run_validation.py:239` `oracle_cr_authenticated: False` literal — leave until CP21's pinned Oracle
   supplement exists; then derive from a per-contract Oracle reference check.
