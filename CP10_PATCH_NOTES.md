# CP10 — audit repairs AUD-01, AUD-02, A-S20-11 (2026-10-18)

Three steps, each committed and tagged separately (`rp-CP10a`, `rp-CP10b`, `rp-CP10c`). No frozen file
edited. Gate bookkeeping moved with each step exactly as at CP02–CP06: `run_validation.py`
`REFERENCE_TEST_COUNT` and the per-file count assertion for `tests/test_auditfix_cp10.py`,
`release_gate_tests/test_r02_release_gate.py` expected `(tests_run, tests_passed)`, the coverage registry
(`py -3.14 build_registry.py`, output redirected) and the manifest (`py -3.14 build_manifest.py`). These
files were not on the step file lists; they are the only way the gate accepts a new test file and were
treated as part of "the gate", not as a logic change.

## CP10a — AUD-01 (A-S20-12): colored-mana planning counts the pool once

### What
`pab_lands_s9.py` `tap_lands_policy`: `pool=g.mana_pool+produced` → `pool=g.mana_pool`. Confirmed first by
reading `FixerLandsMixin.tap_physical_land_for_mana` (same file): it does `self.mana_pool.append(color)` for
every tap, so `produced` was a second copy of the same colours. No other logic changed; the short-colour
rule and the default (`'C'` if offered, else `'B'`) are as before.

### Why
With Command Tower + Blooming Marsh untapped and a hand needing {G}{G} (Essence Warden + Pest Rescuer), the
first tap gave `G`, after which the pool counted `G` twice (`['G']+['G']`), so the second dual saw no
shortfall and gave `B`: `['G','B']` instead of `['G','G']`. Every multi-dual turn in the S9–S18 drivers was
planned with this double count.

### Verification
`tests/test_auditfix_cp10.py` class `TestCP10ColoredMana` (6 tests): the reproduction yields `['G','G']`;
need G1 B1 over two duals → one of each; no colour need → policy default per land (`['B','B']` for
Tower + Marsh, `['C','B']` for Wastes + Tower); Llanowar Wastes with G short → `G` (and 1 damage), not `C`;
single dual with need G2 → `G`; negative control recomputes the old double-count arithmetic (`['G','B']`),
derives the expectation from need alone (`['G','G']`), asserts the policy matches the latter and not the
former. Full gate: `Ran 785 tests` / `OK` (779 + 6), 18/18 release checks. All S9 pinned-seed driver
fixtures (`tests/test_lands_s9.py`, `s9_tests/`) passed unchanged — no expectation moved, no
`EVIDENCE/CP10_SUPERSEDED/` entry needed for this step.

## CP10b — AUD-02 (A-S20-13): opponent scripts fail closed on impossible seat/turn

### What
`pab_interaction_s11.py` `InteractionMixin.script_opponent_actions`: each action's turn is checked against
the seat that owns it; a mismatch raises `ValueError` naming the seat, the turn and the owning seat. The
whole list is validated before any entry is appended, so a bad list schedules nothing. New method
`assert_opponent_script_exhausted()` raises `AssertionError` (listing seat/turn/kind of every pending
entry) when `opponent_script` is non-empty, for scenarios to call at their end. `advance_step` execution
semantics are unchanged.

### Formula confirmed
`pab_turn_clock.TurnClock`: `SEATS=4`, initial state `turn=1, active_player=0`, and at each turn boundary
`turn+=1; active_player=(active_player+1)%seats`. Hence turn t belongs to seat `(t-1) % 4`, checked
empirically turns 1–12 (`{1:0, 2:1, 3:2, 4:3, 5:0, …}`). `pab_opponents_s8.LossAwareClock` skips a seat
only after it has left the game, which cannot have happened when scripts are declared (declaration requires
the clock not yet engaged); a seat that loses later leaves its own entries pending, which the new
exhausted check now surfaces instead of hiding.

### Why
`script_opponent_actions(2,[{'turn':2,...}])` was accepted although turn 2 is seat 1's; the entry stayed in
`opponent_script` forever and never fired, so a scenario could believe it had scripted interaction that
never occurred.

### Verification
`tests/test_auditfix_cp10.py` class `TestCP10ScriptValidation` (5 tests): seat 2 / turn 2 edict raises
`ValueError` mentioning seat 2, turn 2 and seat 1 and schedules nothing; seat 2 / turn 3 is accepted,
fires at turn 3 (`opponent_actions_done == [(3,2,'edict')]`, the Pest token is gone) and the exhausted check
then passes; seat 1 / turn 2 accepted (plus (1,6), (2,7), (3,4), (3,8)); a list with one bad entry schedules
nothing; the exhausted check fails naming "turn 42" while a valid far-future action is pending at turn 2.
All existing script call sites in the suite (seat 1 turns 2/6/10, seat 2 turn 3, seat 3 turn 4, and the
S11/S15/S16/S20 driver scripts) already satisfied the formula; no expectation moved. Full gate:
`Ran 790 tests` / `OK` (785 + 5), 18/18 release checks.
