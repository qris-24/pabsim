# Clock stage S3 — promoted 2026-10-18

`pab_clock_s3.py` (`PriorityMixin`, includes S1/S2).
- **SBA between resolutions** (CR 704.3, 117.5): `resolve()` checks before the first resolution, after every resolution, and repeats until nothing applies. Modeled: controller's creatures at toughness ≤ 0 die (704.5f); the 0-life loss as before. Trace `sba_event` / `sba_zero_toughness(…, 'state-based')`.
- **Simultaneous deaths are one event with look-back** (603.10): a `_LookBack` view makes `_leave()`'s trigger snapshot the pre-event board, so creatures dying together see each other (a dying Deathgreeter still gains for the Pest dying beside it). The view is dropped after the event.
- **Yawgmoth's inline R48 check retired** (hook `_inline_zero_toughness_check` → no-op); the general check performs the death after the full resolution (counter → draw → SBA). Skullclamp's immediate check is kept: equip has no stack here and priority follows at once; C45's trace contract is preserved.
- **Trigger ordering API** (603.3b, one controller): `set_trigger_order(policy)`; the policy must permute the batch; the chosen order is traced. C63 is now fully EXECUTED.

Executed: C97 (EXECUTED_WITH_SUBSTITUTION — the two-creature -1/-1 is synthetic). Two prior assertions changed trace source from `'Yawgmoth'` to `'state-based'` (expected consequence).

Not modeled: opponents' permanents (no SBA on them), legend rule, counter annihilation, loyalty, APNAP interleaving across seats.
