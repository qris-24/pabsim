# Clock stage S4 — promoted 2026-10-18

`pab_clock_s4.py` (`TurnBasedActionsMixin`, includes S1–S3).
- **Untap step** (CR 502.3), controller's turn only: all controller permanents untap; on the bridge `DeckZones.new_turn()` untaps linked cards and resets the land-play count; event-side tapped flags re-synced. Trace `untap_step(turn, n_untapped)`.
- **Draw step** (CR 504.1): controller draws one real card (physical on the bridge; counted on the event kernel). No turn-1 skip: CR 103.8a is two-player only. Opponents have no library here: `opponent_draw_unmodeled(seat)`, nothing moves.
- **Land-play window** (CR 305.1/305.2): once engaged, `play_physical_land()` derives main-phase and empty-stack from the clock and the pending queue, refuses opponents' turns, and the one-per-turn count resets at the controller's untap.

Fixtures: `tests/test_turn_actions_s4.py` (13). Two prior probes adjusted (C62 name probe narrowed to Beledros-specific API; S1 compat test now stops before the draw step).

Clock stages S1–S4 complete. Still unmodeled: opponents' libraries/draws/untaps, cleanup discard (514.1), "doesn't untap" effects, extra land plays, combat (steps exist on the clock; no combat actions).
