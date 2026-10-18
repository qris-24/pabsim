# R52 + R53 (+R54) — approved and promoted 2026-10-18

User instruction (2026-10-18 10:01): fix bugs as found, including `cast_pab_spell` and `opening_hand`, as long as nothing breaks. Frozen files remain untouched; fixes are layered or made in promoted (non-frozen) files.

## R52 — Village Rites costs {B}
- Defect: `pab_focus_engine_v07.cast_pab_spell` costs Village Rites `(black=1, generic=1)` = {1}{B}. Printed cost {B} (`EVIDENCE/S6_CARD_EVIDENCE.json`: scryfall.com card page, mtg.wtf corroboration).
- Fix: `pab_r52_village_rites.py` → `VillageRitesCostMixin.cast_pab_spell` intercepts only `'Village Rites'`, runs the same procedure with cost (1,0,0) using the frozen primitives (preflight → `pay_mana` → `sacrifice` → `'cast'` trace → resolution Trigger → Magecraft); every other name is delegated to the frozen method. Promoted on both `Game` and `PhysicalZoneGame` in `pab_kernel.py`.
- Frozen contract superseded: `tests/test_v04_cost_and_copy.py::test_91_village_rejects_mana_shortage_before_sac` (asserts ['B'] is insufficient). Added to `EXPECTED_LEGACY_FAILURES`; the kernel's 149-replay now fails on exactly {91, 112, 113} → 146 passes. Corrected full copy: `r52_tests/test_v04_cost_and_copy_r52.py` (25 tests, only test_91 differs), replayed by `run_validation.py` (`kernel_corrected_v04_copy_25_replay_passes`).
- Tests: `tests/test_r52_village_rites.py` (4): both kernel classes pay exactly {B}; refusals (no black, artifact cost) mutate nothing; frozen engine still charges {1}{B}; other spells delegate unchanged. S6's `test_r52_*` updated (frozen refuses, kernel and S6 paths pay {B}).

## R53 — opening hand shuffles first (CR 103.3)
- Defect: `pab_turn_loop.opening_hand()` (S5) drew 7 from the unshuffled frozen decklist order; every seed produced the same game. The seed only affected later searches.
- Fix: `opening_hand()` now calls `zones.shuffle_library()` and traces `('opening_shuffle_103_3', seed)` before drawing. `pab_cast_s6.opening_hand_shuffled()` is now a plain alias (one shuffle, so S6's seed-7 result is unchanged).
- Tests: `tests/test_integrated_turn_loop_s5.py::test_r53_opening_hand_shuffles_first_so_seeds_differ` (shuffle immediately precedes the draw; seeds differ; same seed is deterministic). S6's R53 test rewritten: fixed `opening_hand` and the alias give identical hands and libraries.

## R54 — vacuous S5 land-play test (found by R53)
- Defect: `test_land_plays_never_exceed_one_and_only_supported_names` compared ledger land plays against `g.trace` entries keyed `'land_played'`, a key only `zones.trace` emits (`g.trace` emits `'physical_land_played'`). It passed as 0 == 0 because R53 kept every seed's hand landless. With R53 fixed it failed on 6/8 seeds.
- Fix: compares against `'physical_land_played'` in `g.trace` and `'land_played'` in `zones.trace`, and asserts the total across seeds is > 0 so it cannot pass vacuously again.

## Effect on S5 claims
S5's "8 seeds" were one game until R53. All S5 pins (library counts, turn ledger shape, clock state, mana emptying, hand accounting, 30-turn token count) still hold under shuffled hands; the land-play test is the only one that changed meaning.

## Counts
Reference fixtures 525 → 530 (S5 6→7, +4 R52). Release-gate pins updated (total, superseded set of 3, corrected-copy 38 + 25). `KERNEL_VERSION` … `+S6+R52+R53`.
