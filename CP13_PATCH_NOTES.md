# CP13 — AUD-03 (A-S20-14): tutor selection moves from cast time to resolution (2026-10-18)

One step, committed and tagged `rp-CP13`. No frozen file edited (`pab_zones.py` untouched). Gate
bookkeeping moved with the step as at CP02–CP10: `run_validation.py` `REFERENCE_TEST_COUNT` (796 → 805) and
the per-file count assertion for `tests/test_auditfix_cp13.py`, `release_gate_tests/test_r02_release_gate.py`
expected `(tests_run, tests_passed)` = (805, 805), the coverage registry (`py -3.14 build_registry.py`,
output redirected), the manifest (`py -3.14 build_manifest.py`), the ledger entry for A-S20-14
(`cp13_status: CLOSED`, `status: REPAIRED`) and `CLAUDE.md`'s stale "779 tests" → 805.

## What
- `pab_cast_s13.py` `SpellCastMixin._tutor`: the cast-time preflight that refused Demonic Tutor / Diabolic
  Intent without a library card already chosen is removed. Casting still pays the mana and the Diabolic
  Intent creature sacrifice. The resolution closure now chooses the card against the library as it is when
  the spell resolves: an explicit `selected_land_uid` is honoured if that card is still in the library;
  otherwise the `search_selection_gone` trace is kept and `tutor_selection(self)` runs at resolution; if the
  policy returns nothing (or something no longer in the library) the first library card is taken, so the
  unrestricted mandatory search always finds a card while the library is nonempty. An empty library passes
  `None` to the frozen `zones.resolve_demonic_tutor` / `zones.search_library(eligible='any')`, which shuffle
  and record `search_resolved`.
- `pab_cast_s13.py` `cast_when_able`: the driver no longer calls `tutor_selection` before casting and no
  longer skips the cast when the policy returns `None`; `_cast_spell_s13`'s `selected_land_uid →
  selected_uid` wiring is unchanged.
- `tests/test_cast_s13.py` line 80 (authorized exception): the two `self.refused(...)` calls that pinned the
  old cast-time refusal become (a) a cast with no selection that resolves and finds a card and (b) a stale
  explicit selection (the Tutor's own uid) that falls back to resolution-time selection with the
  `search_selection_gone` trace. Nothing else in the file changed; the Diabolic Intent no-sacrifice refusal
  stays.

## Why
A tutor's search happens on resolution (CR 701.19a); the choice was being locked in at cast, before any
response could change the library, and a cast with no choice was refused outright.

## Verification
`tests/test_auditfix_cp13.py` (9 tests): no-selection cast succeeds; the selector runs at resolution and not
at cast (module-level policy wrapped with a counter); the selection sees the library as it is at resolution
(the cast-time pick is removed from the library before resolving and a different card is found); a stale
explicit choice falls back with the `search_selection_gone` trace; an empty library shuffles and records
`search_resolved`/`demonic_tutor_resolved` with `None`; the Diabolic Intent sacrifice and mana are paid at
cast and the additional cost is still required; an explicit choice still in the library is honoured without
invoking the policy; the driver resolves a Tutor with exactly one policy call (from resolution, none from
the driver); negative control: the pre-CP13 cast-time refusal no longer occurs and the library is untouched
until resolution. Kernel suite `Ran 805 tests` / `OK` (796 + 9); 18/18 release checks; full output in
`EVIDENCE/CP13_gate.txt`. All pinned-seed driver fixtures passed unchanged; none of the 311 frozen v0.5–v0.8
fixtures changed; no `EVIDENCE/CP13_SUPERSEDED/` entry needed.
