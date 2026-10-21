# R47 + R48 patch notes — promoted 2026-10-18

Both found by executing C61 and C79 against the kernel; both approved together ("as rec").

| Issue | Frozen behaviour (v0.5/v0.7) | Fix in `pab_r47_r48_sba.py` | Rule |
|---|---|---|---|
| R47 | `roaster_end_step` captured `p.counters` in a lambda default at trigger time | Trigger reads the live counter count at resolution; makes nothing if Roaster has left; traces `roaster_counters_at_resolution` | CR 608.2h |
| R48 | `yawgmoth_sacrifice` resolved zero toughness via `destroy()`, so indestructible kept the creature | Uses `_leave(uid, sacrificed=False)` (the path `equip_skullclamp` already used) and traces `sba_zero_toughness` | CR 704.5f |

- `pab_kernel.py`: `Game`/`PhysicalZoneGame` now come from `pab_r47_r48_sba` (R47+R48 layered on R01). `KERNEL_VERSION='v0.8+R02+R01+R47+R48'`.
- C61 → EXECUTED_WITH_SUBSTITUTION (4 tests, incl. a source-leaves control); C79 → EXECUTED_WITH_SUBSTITUTION (5). Each keeps one test that pins the frozen v0.7 behaviour so the discrepancy stays documented. No expected failures remain.
- Reference fixtures: 420. Frozen files untouched; all frozen replays unchanged (149 → 147 + {112,113}; 52/52; 54/54; 38/38).
- Pest Rescuer text check: Aetherhub and EchoMTG agree on "if you don't control a Pest creature token" → R01 stands. The text also reads "each upkeep" (not "your upkeep"); the kernel models only the controller's upkeep. Noted, not acted on. (Historical: since S2 the kernel fires each-upkeep triggers on every seat's upkeep; see S2_PATCH_NOTES.md and EVIDENCE/CP31_PEST_RESCUER_ORACLE.md.)
