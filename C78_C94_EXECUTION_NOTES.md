# C78–C94 execution notes (issues R41–R46, the 11 unsupported nonlands) — 2026-10-18

`tests/test_c78_c94_contracts.py`: 23 counted fixtures (total 419). Probes assert that `add()` refuses the card (no verified partial definition) with permanents, queue, trace and graveyard unchanged.

| Contract | Status | Tests | What was asserted |
|---|---|---|---|
| C78 | EXECUTED_WITH_SUBSTITUTION | 1 | Golgari Charm's global -1/-1 replaced by the kernel's only -1/-1 path (Yawgmoth counter). 1-toughness Pest dies by the `destroy` SBA path, no `sacrifice` trace; Blood Artist and Pest dies-gain observe; no Savra trigger after the activation. |
| **C79** | **DISAGREEMENT_OBSERVED** | 4 + 1 expected failure | Indestructible granted via `indestructible_until_eot`. Destroy prevented ✓; sacrifice still happens ✓; expires at turn reset ✓. **New issue R48:** 0-toughness indestructible creature survives because Yawgmoth's SBA path calls `destroy()`; contract/CR 704.5f expect death. Pinned; unapproved. Hexproof/exile unmodeled. |
| C80 | EXECUTED (CP21; was BLOCKED_UNSUPPORTED) | 2 | Witherbloom Charm refused. Control executed: Village Rites cost sacrifice precedes the cast event. |
| C81 | EXECUTED (CP21; was BLOCKED_UNSUPPORTED) | 1 | Golgari Charm refused; no regeneration API. |
| C82 | EXECUTED_WITH_SUBSTITUTION (CP21; was BLOCKED_UNSUPPORTED) | 1 | Infuse with Vitality refused. |
| C83 | PARTIAL_EXECUTED (CP21; was BLOCKED_UNSUPPORTED) | 1 | Abrupt Decay refused. |
| C84 | PARTIAL_EXECUTED (CP21; was BLOCKED_UNSUPPORTED) | 1 | Assassin's Trophy refused. |
| C85, C86 | C85 EXECUTED_WITH_SUBSTITUTION, C86 EXECUTED (CP21; was BLOCKED_UNSUPPORTED) | 1 each | Rise of the Witch-king refused. |
| C87 | EXECUTED_WITH_SUBSTITUTION | 2 | Grisly Salvage composed from zone primitives: top five by library order, one creature/land to hand, four to graveyard, remaining order preserved, no shuffle trace. None-eligible branch: all five to graveyard. |
| C88–C90 | C88 EXECUTED, C89 EXECUTED, C90 EXECUTED_WITH_SUBSTITUTION (CP21; was BLOCKED_UNSUPPORTED) | 1 each | Shigeki, Jukai Visionary refused (note: the deck's Shigeki is "Jukai Visionary", not "Zeal's Guardian"). |
| C91–C93 | C91 EXECUTED_WITH_SUBSTITUTION (CP21), C92 PARTIAL_EXECUTED (CP21), C93 EXECUTED (CP23; PARTIAL_EXECUTED at CP21) (was BLOCKED_UNSUPPORTED) | 1 each | Grist, the Hunger Tide refused; physical cards carry no type line. |
| C94 | PARTIAL_EXECUTED (CP21, CP23; opponent mill unasserted) (was BLOCKED_UNSUPPORTED) | 1 | Witherbloom Command refused. |

Status column updated at CP24 to match CONTRACTS_C41_C94_STATUS.md (CP21 and CP23 re-status sections); the "What was asserted" column is the R02-era text, left as written.
