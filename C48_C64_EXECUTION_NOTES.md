# C48–C64 execution notes (issues R27–R34) — 2026-10-18

`tests/test_c48_c64_contracts.py`: 31 counted fixtures (total 376). Statuses recorded by the runner in `VALIDATION_RESULTS.json → contracts_executed`. None Oracle/CR-authenticated.

| Contract | Status | Tests | Substitutions / limits |
|---|---|---|---|
| C48 | EXECUTED | 3/3 | 2 Pests + 2 G Squirrels, 4 Bats creation triggers; Squirrels carry no Pest subtype or BG colors. |
| C49 | EXECUTED | 2/2 | Treasure (noncreature artifact) + 1 Squirrel; 2 Bats observations; nothing created before resolution; no loop. Nontoken cost creature used to keep Bats token-sacrifice out of the count. |
| C50 | BLOCKED_UNSUPPORTED | 1/1 (probe) | Offspring/token copy not modeled; nothing to assert about copy characteristics. |
| C51 | EXECUTED_WITH_SUBSTITUTION | 2/2 | Chatterfang activation (X, target, -X/-X) not modeled; two Squirrel sacrifices performed directly. 2 Savra green, 0 black, 2 Bats. Squirrels created before Chatterfang enters (otherwise its replacement doubles them). |
| C52 | EXECUTED_WITH_SUBSTITUTION | 1/1 | Opponent creatures and -X/-X SBA not modeled; target death = exogenous `opposing_creature_dies()`. Only Archer observes; no Savra, no second Bats. |
| C53 | EXECUTED_WITH_SUBSTITUTION | 1/1 | Blood Artist target fixed by fixture to opponent 1. Opponents end [37,38,38]; four distinct trigger identities. |
| C54 | EXECUTED | 1/1 | Blood Artist, Deathgreeter, Archer, Sangromancer observe; Bastion, Moldervine, Dark Prophecy do not; no inferred sacrifice/discard. |
| C55 | EXECUTED | 2/2 | pay_life precedes sacrifice precedes Treasure; Pest gain + both Savra colors queued; paid life never enters the gross tally. |
| C56 | EXECUTED_WITH_SUBSTITUTION | 1/1 | Treasure mana ability not modeled; cash-in is a direct sacrifice. Bats + Agent-granted → 2 per opponent; no Savra. |
| C57 | EXECUTED_WITH_SUBSTITUTION | 1/1 | No lore/phase clock; chapters invoked directly. 3 BG Insects + 3 Squirrels; `controls_pest()` false; no cast events. |
| C58 | EXECUTED_WITH_SUBSTITUTION | 3/3 | Fixture library list; shuffle traced unmodeled. MV2 eligible, MV3 rejected before any mutation; Saga leave is not a creature sacrifice; 0-sacrifice branch allows only MV0. |
| C59 | EXECUTED | 2/2 | Ceiling = sacrificed count (1) with four tokens present; 3 sacrifices → ceiling 3. |
| C60 | EXECUTED_WITH_SUBSTITUTION | 2/2 | Devour not modeled; Roaster added with counters=2 after the two victims are sacrificed directly. 2 Pests + 2 Squirrels at end step. |
| **C61** | **DISAGREEMENT_OBSERVED** | 1/3 + 2 expected failures | **New issue R47 (design-only):** `roaster_end_step()` captures `p.counters` when the trigger is enqueued (`lambda n=p.counters`), so a counter added or removed between trigger and resolution is ignored. Contract expects the count at resolution. Both contract assertions are `expectedFailure`; a third test pins the observed kernel behaviour. No frozen code changed; a fix needs approval. |
| C62 | BLOCKED_UNSUPPORTED | 1/1 (probe) | Beledros 10-life untap and once-per-turn tracking not modeled; event kernel has no lands. |
| C63 | EXECUTED_WITH_SUBSTITUTION | 3/3 | No step clock; alternate order produced by reversing the pending queue. Rescuer-first → 2 Pests; Beledros-first → 1 (intervening-if false); Pest already present → only Beledros admitted. |
| C64 | EXECUTED_WITH_SUBSTITUTION | 2/2 | Discard-to-draw Learn branch not modeled. Physical bridge: library 99 / outside-game 1 before; Lesson moves to physical hand only with the pod rule; never a fake event-kernel card; second Learn refused; without the rule Hunt still makes its Pest. |

Blocked until modeled: offspring/copy tokens, Chatterfang activation and -X/-X, opponent permanents, Blood Artist targeting, lore counters/phase clock, devour, Beledros untap, Treasure mana ability.
