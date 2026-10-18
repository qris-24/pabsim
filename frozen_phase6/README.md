# PABTRV3 — Phase 6 reference artifacts (v0.6)

**Purpose:** Continue validation of the **frozen** PABTRV3 Savra deck, without optimizing cards or running a mass replacement sweep. This is **not** a complete or playable Commander simulator.

## Execute

Using Python 3.10+ standard library only:

```sh
python run_validation.py
```

This runs **205** isolated deterministic tests: the unmodified **149** Phase 5 tests plus **56** new physical-card-zone tests. It validates the SHA-256 of the exact 100-card baseline, generates `PABTRV3_CARD_COVERAGE.json`, and records outcomes in `VALIDATION_RESULTS.json`.

## New, separate `pab_zones.py` prototype

- Construct **99 individual mainboard cards** (including six different physical Forests and nine different physical Swamps), **one Savra commander** in command, and one **Pest Summoning** Lesson outside the game. Default Learn cannot retrieve it; the recorded local house rule is explicit opt-in.
- Use a fixed RNG seed and top-of-library ordering. Shuffle reproducibly, draw actual unique card objects to hand, mill them to graveyard, discard from hand, exile, and move individual cards through zones without duplicating them. Attempting a draw from an empty library records a failed draw; the *game loss* from it is not adjudicated (SBA engine missing).
- The owner stays distinct from controller, which is assigned only on the battlefield. Creation and death/exile of a modeled token never inserts that token into the actual 99-card library or leaves an available graveyard card after its SBA checkpoint.
- Resolve **Demonic Tutor selection only**: chosen real library card goes to hand, rest of library shuffles, invalid choices rejected. This **does not cast Demonic Tutor or pay mana**.
- Explicitly **play and tap only basic Forest, basic Swamp, or Command Tower** in restricted fixtures; Command Tower produces **B or G** for Savra, never another color. These are based on the prior package's *unpinned* land descriptions. Eighteen other distinct nonbasic land entries reject unsupported plays rather than silently doing nothing.
- Select only **basic Forest/Swamp** in restricted search-to-battlefield fixtures; optional hidden-zone failure is modeled where applicable. Full nonbasic Forest/Swamp type, ETB, cost, shuffling and selection interactions remain outside scope.

## Preservation and truth-in-coverage

- `pab_focus_engine.py` and all original v0.5 tests are **unchanged**; they do **not** share zones, hand, mana, or events with `pab_zones.py` yet. `frozen_phase5/` saves pre-edit copies of the v0.5 registry, runner, engine, and test sources. `upstream_frozen/` is unchanged.
- Mainboard nonlands: **54/65** have **partial reference coverage**, **11/65** remain without dedicated behavioral support. **Zero** card implementations are fully verified. The new tutor coverage is strictly a resolution path, not full playability.
- **No** independent live Oracle verification of the 21 unique land names or the four colorless-source cards has occurred. Their printed legal text and all specific ETB rules still need independent verification.
- No original `engine.py`/`oracle.py` integration, opponent model, stack, APNAP order, realistic casting, or win-rate simulation. Historical old compiler contracts remain at saved **10 passed/15 failed**, **not rerun**.
- All recommendation/optimizer values remain `null`; no decklist changes were made.

See `PABTRV3_PHASE6_ENGINEERING_REPORT.md` and `PABTRV3_PHASE6_NEW_SESSION_HANDOFF.md` for further sequencing and gates.
