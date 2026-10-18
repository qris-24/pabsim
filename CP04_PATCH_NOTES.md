# CP04 — S19 adversarial terminal continuation audit

Parent `rp-CP03`; scoped issue A-S20-07.

`pab_terminal_audit_cp04.no_steps_after_terminal` replays controller life
changes from event traces (same event vocabulary as S19), and rejects a
`step_begin` if the controller is already at or below zero or if a terminal
`win_game`/`lose_game` marker has appeared. A life dip repaired during the
same resolution is not incorrectly treated as terminal merely by its amount.

`pab_validation_s19.clock_legal` invokes this additional check; the prior
7 existing S19 metric keys and four S19 tests are preserved. Six regression
tests include *mutated otherwise-contiguous step traces*, genuine controller
losses, terminal wins and a timeout negative control.

No frozen historical file, 100-card deck, card source or Phase 9 permission
changed. This check is **trace consistency**, not a replacement for a real
stack/SBA/priority-aware game end engine.
