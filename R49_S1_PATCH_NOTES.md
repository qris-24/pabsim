# R49 + clock stage S1 — promoted 2026-10-18

**R49** (in `pab_r47_r48_sba.py`): Roaster's end-step trigger snapshots the counter count when created and uses it as last known information if Roaster has left the battlefield before resolution (CR 608.2h, second sentence); while Roaster is present the live count is read (R47). Trace: `roaster_counters_at_resolution` vs `roaster_counters_lki`. The C61 control that expected 0 encoded the R47 mistake and was corrected to 2. The frozen v0.7 lambda happened to agree on this branch; it was wrong only in the source-present case.

**S1** (`pab_turn_clock.py`): `TurnClock` — 4 seats, turn counter, active player, 12 (phase, step) pairs in CR 500.1 order, `advance()` / `advance_to(step, active_player=)`, boundary log. `ClockMixin` gives `Game`/`PhysicalZoneGame` a `.clock`, `advance_step()` and `advance_to()` that only write `step_begin` entries to the trace. **Inert by contract**: no existing method consults the clock; `begin_upkeep`, `roaster_end_step`, `moseo_end_step`, `reset_turn` are unchanged and still caller-driven. `tests/test_turn_clock_s1.py` (11) pins step order, seat rotation, and that eight full turns change no game or zone state.

Kernel `v0.8+R02+R01+R47+R48+R49+S1`. Reference fixtures: 445. R50/R51 stay open until S2. S2–S4 not authorized.
