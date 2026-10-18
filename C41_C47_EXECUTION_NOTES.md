# C41–C47 execution notes (issues R22–R26) — 2026-10-18

Executed against the promoted kernel (v0.8+R02+R01) as `tests/test_c41_c47_contracts.py` (19 counted reference fixtures; total 345). Statuses are recorded by the runner in `VALIDATION_RESULTS.json → contracts_executed`. None is Oracle/CR-authenticated; expectations are the contract bodies' provisional expectations.

| Contract | Status | Tests | Substitutions / limits |
|---|---|---|---|
| C41 | EXECUTED_WITH_SUBSTITUTION | 3/3 | High Market (unsupported land) → exogenous `gain(1)` after the boundary, with a controlled-creature sacrifice. Engine has no step clock: the boundary is the `moseo_end_step()` call; non-retroactivity is asserted on the trigger queue and trace, not a timing model. |
| C42 | EXECUTED_WITH_SUBSTITUTION | 4/4 | Infuse with Vitality (unsupported) → exogenous `gain(2)` base event; the +1 replacement is the kernel's own Pest Rescuer. Gross 3 vs net +1 confirmed; MV 3 eligible, MV 4 raises; target locked after later gains. |
| C43 | EXECUTED_WITH_SUBSTITUTION | 3/3 | Treasure mana ability not modeled; sacrifice performed directly. Bats + Agent-granted artifact drain → 2 per opponent; Savra black/green and creature-death observers zero; token not in graveyard. |
| C44 | EXECUTED_WITH_SUBSTITUTION | 2/2 | No command zone: branch B removes Savra by harness deletion (no death event). Branch A: Savra absent → only Bats (1). Branch B: granted trigger already on the queue still resolves (2). |
| C45 | EXECUTED | 2/2 | Equip pays {1}; 1/1 Pest dies by SBA (`destroy` path, no `sacrifice` trace); clamp draws 2; Pest dies-gain 1; Savra triggers zero. Control: sacrificing the same Pest yields Savra black+green. |
| C46 | EXECUTED | 2/2 | Carrion Feeder with one +1/+1 counter sacrificed to Tend → 2 BG Pests with dies-gain; no token exists during cost payment (trace order). Control: no counter → 1. |
| C47 | EXECUTED | 3/3 | Grub death → Mound Pest (1) + 2 Worms (not Pests, no dies-gain). Pest token death → no Mound, dies-gain 1. Generated tokens dying → no recursive Mound. |

Setup note (not a kernel disagreement): Mirkwood Bats also drains on token *creation*. The contracts state the Treasure is already on the battlefield, so the Treasure is created before Bats enters and life is compared to a post-setup baseline.

Blocked for full execution until the kernel models them: High Market, Infuse with Vitality, Treasure mana ability, command-zone replacement, step/phase clock.
