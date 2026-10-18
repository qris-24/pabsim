# Clock stage S2 — promoted 2026-10-18

`pab_clock_s2.py` (`StepRoutingMixin`, includes S1's `ClockMixin`). On every `advance_step()` / `advance_to()`:

| Boundary | Action | CR |
|---|---|---|
| any boundary | mana pool emptied in place (bridge shares the list with DeckZones) | 106.4 |
| any seat's upkeep | `begin_upkeep()` — Pest Rescuer and Beledros are "each upkeep" | 503.1, 603.2, 603.4 |
| controller's end step | `roaster_end_step()`; Moseo intervening-if admission recorded (`moseo_end_step_admission`, life gained this turn) | 513.1, 603.4 |
| controller's cleanup | `reset_turn()` — "until end of turn"/"this turn" effects end | 514.2 |

Engagement: before the first advance, step methods may be called directly (fixture shortcut). After it, `begin_upkeep`/`roaster_end_step` raise `ClockError` (the clock owns them) and `moseo_end_step(target)` works only at the controller's end step after admission.

Executed: C95 (each-upkeep round [2,1,1,1]; Rescuer retriggers on an opponent's upkeep once its Pest dies), C96 (pool empties at each boundary, upkeep mana unavailable in the draw step, bridge pool emptied in place), C98 (opponent end step fires nothing; controller end step fires Roaster and admits Moseo; post-boundary gain not retroactive; direct calls refused once engaged), C99 (Roaster LKI at a clock-driven end step). Contracts: 58.

Known limit (pinned): the kernel keeps one "this turn" ledger (`life_gained_turn`), the controller's; an opponent's cleanup does not clear it. Correct for Moseo ("your end step"), but any future "each player's turn" effect needs per-seat ledgers.

Not in S2: priority loop / SBA between resolutions (S3); untap, draw, land-play reset as turn-based actions (S4); APNAP ordering choice API; opponents' permanents.
