# S20 — Shigeki, Jukai Visionary + per-card model-coverage registry (2026-10-18)

Kernel `…+S19+S20` (`ShigekiMixin` layered above `PolicyOpponentsMixin`; `pab_validation_s19.py` remains a tool above the kernel). 736 reference fixtures (732 + 4). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged. No deck score is produced or implied. This is the stop point requested ("pause at 20, then audit all work"): no further stage is started after S20.

## Finding that forced the card work
Building the coverage registry over the full decklist (`PABTRV3_CARD_COVERAGE.json`, 101 identities) asserted a name absent from every table in the kernel: **Shigeki, Jukai Visionary**. It is in the deck, had no fixture body, no cast table entry and no path from the physical hand; `cast_from_hand` refused it (fail-closed), which is why the S6 fail-closed sweep never flagged it — the sweep proves refusal, not coverage.

**Correction of earlier notes.** S15_PATCH_NOTES ("65/65 nonland cards, fail-closed count is 1 — Grist") and the handoff line "64/65 nonland cards castable … (Grist not modeled)" were wrong by one card: before S16 the count was 63/65, after S16 64/65, and only after S20 is it 65/65 (65 = the 67 distinct nonland names minus Savra, cast from the command zone, and the Pest Summoning Lesson). The S16 notes' implication that Grist was the last unmodeled card was likewise wrong. The audit that follows S20 must treat "every card" claims as unverified unless derived from the deck list itself.

## Shigeki (`pab_shigeki_s20.py`)
Text from the user's Scryfall export (secondary-official; recorded in `EVIDENCE/S7_CARD_EVIDENCE.json` convention is not extended here — the text is quoted in the module docstring and the registry entry).
- Cast `{1}{G}`, 1/3 legendary enchantment creature, controller 0, linked to its physical card; green required; targets refused.
- `shigeki_activate(uid)`: `{1}{G}`, `{T}`, return Shigeki to its owner's hand as a cost (card to hand, permanent removed, link dropped, mana paid, all before the ability is placed); summoning sickness refused (CR 302.6, `entered_turn` from S17); on resolution reveal the top four cards, the controller chooses one land card to put onto the battlefield tapped (`land_uid` pre-commits the choice; otherwise the first land revealed, or none; `('shigeki_reveal', chosen_or_None, rest)` traced), the rest go to the graveyard. A library shorter than four reveals what there is.
- `channel_shigeki(card_uid, targets)`: `{X}{X}{G}{G}`, discard Shigeki from hand, return X target nonlegendary cards from the graveyard to hand; legendary targets refused (`LEGENDARY_CARDS` listed from the deck's supertypes), duplicate targets refused, X = the number of targets (X = 0 is allowed: `{G}{G}`, discard, return nothing), targets validated and the full cost paid before the discard; Shigeki's own card is in hand when targets are checked, so it cannot target itself.
- `check_invariants_s20` chains S18 only; Shigeki's link is covered by `assert_bridge_integrity` like any linked creature.

## Coverage registry (`build_model_coverage_s20.py` → `PABTRV3_MODEL_COVERAGE_S20.json`)
One entry per distinct name (88; quantities sum to 101 identities): kind, the stage that gives it a physical path, a `modeled` list, an explicit `not_modeled` list (42 names carry at least one item), `certified: false` for all, `value_for_optimization: null` for all. Regeneration is byte-identical (tested). The registry is the inventory the audit works from; it is not a scoring input, and the rule line in its summary says so.

## Re-scoped earlier-stage test (non-frozen, R54-style)
`tests/test_cast_s6.py::FailClosed.test_every_other_hand_card_is_refused_without_mutation` now also skips Shigeki, since it is castable after S20. After S20 the sweep's refused set is lands and the Lesson only.

## Pins
`run_validation.py` REFERENCE_TEST_COUNT 736, `test_shigeki_s20.py` == 4; release gate (736, 736); registry `coverage_stage_s20` line; manifest patches + S20; R02_VERSIONED + `pab_shigeki_s20.py`, `S20_PATCH_NOTES.md`, `build_model_coverage_s20.py`, `PABTRV3_MODEL_COVERAGE_S20.json`.

## Not modeled / open for the audit
- Shigeki's reveal policy is fixed (first land); no choice among several lands.
- The channel's X is bounded only by the mana pool.
- The registry's `not_modeled` lists are hand-written from the stage notes and card texts; they have not been machine-checked against the code and are a primary audit target.
