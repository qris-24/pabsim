# S7 — creature spells from the physical hand (Task 1b, 2026-10-18)

Kernel `v0.8+…+R52+R53+S7`. New layer `pab_cast_s7.py` (`CreatureCastMixin`, above `pab_cast_s6.CastMixin`; `VillageRitesCostMixin` stays first in `pab_kernel.py`). 601 reference fixtures (530 + 71). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## What was built
- `cast_from_hand(physical_uid)` now accepts the 27 creature names in `pab_focus_engine.BODIES` minus `NONCREATURE` minus Savra that S6 did not cover (Sakura-Tribe Elder keeps the S6 procedure). Lands, Savra, noncreatures, the Lesson and any other name still fail closed.
- Per card: printed mana cost as (black, green, generic), power, toughness, colours — table `CREATURES` in `pab_cast_s7.py`, checked symbol-by-symbol against `EVIDENCE/S7_CARD_EVIDENCE.json` by `tests/test_cast_s7.py`. All 28 costs are plain generic + {B}/{G} (no hybrid, X or Phyrexian symbols).
- Same preflight and timing as S6 (CR 601.2: in hand, not on the stack ledger, own main phase, empty stack, priority; mana from the shared pool; refusal before any mutation). Creatures do not trigger Magecraft. `sacrifice_uid` / `selected_land_uid` refused for every S7 name.
- Resolution (CR 608.3): hand → battlefield via the frozen `add()` + `linked_battlefield` path. ETB behaviour reached through casting is therefore the frozen kernel's and is tested through the cast path: Moseo's attack-gain Pest, Innkeeper's Treasure, Essence Warden / Innkeeper / Bogwater Lumaret lifegain, Chatterfang's Squirrel replacement and Mirkwood Bats' drain on the created tokens.
- Devour (CR 702.82, Ribtruss Roaster only): `cast_from_hand(uid, devour_uids=[…])`. At resolution each listed uid still a controlled creature is sacrificed through the frozen `sacrifice()` (Savra and death triggers enqueue there) before the Roaster enters with that many +1/+1 counters; a uid that left in the meantime is dropped and traced (`devour_choice_gone`). Default is devour zero. Refused: duplicates, uncontrolled, noncreature, and `devour_uids` on any other name.
- Driver: `pab_cast_s7.cast_when_able()` / `run_turns_casting()` — the S6 shape, one main-phase pass over the hand in hand order, S6 spells by the S6 rules, creatures with devour zero. The S6 driver is untouched (its seed-7 pin still holds).

## Evidence
`EVIDENCE/S7_CARD_EVIDENCE.json`: cost, P/T, colours, type line, Oracle text, oracle_id and printing id per card, taken from `audit/…/reference/pabtrv3_oracle_reference.json` (the user-provided Scryfall bulk export `oracle-cards-20261017210157.jsonl`, sha256 recorded). `golgari_commander.json` was not available. scryfall.com and api.scryfall.com were unreachable from the build environment on 2026-10-18, so no card page was fetched; the per-card locator is recorded, not visited. Status: secondary-official, same as S6.

## Found while building (no behaviour change to S6)
- S6 orders creature resolution as move → `add()` → delete ledger entry. For the Elder that is harmless; for any creature whose `add()` creates tokens (Moseo, Innkeeper) the v0.8 bridge's `make_tokens` asserts bridge integrity while the ledger still names a card that is now on the battlefield, and fails. S7 deletes the ledger entry before `add()` (the card has left the stack as it enters). S6 itself is unchanged.

## One S6 test re-scoped (not frozen; R54-style in-place edit)
`tests/test_cast_s6.py::FailClosed.test_every_other_hand_card_is_refused_without_mutation` pinned "every name outside the S6 five fails closed". S7 widens that set by design, so the test now skips `pab_cast_s7.S7_NAMES` as well and still proves every remaining library card is refused without mutation (lands, Savra, noncreatures, instants/sorceries outside S6, the Lesson). Count unchanged (33). Every other S6 test, including the S6 driver's seed-7 Nature's Lore pin, passes unchanged.

## Not modeled
Starscape Cleric's optional Offspring {2}{B} (cast only for the printed cost; no token copy); the legend rule (CR 704.5j) for a second copy of a legendary creature (singleton deck, no copy effect in the kernel); keywords without kernel semantics (flying, menace, ward, haste, deathtouch, reach, forestwalk, protection, can't block); summoning sickness; combat; opponents; the stack as a zone (S6 ledger substitute).

## Observed, not a claim about the deck
Under the 8-seed 8-turn driver only 16/34 lands are playable (step 3b), so casting frequency is a land-coverage artifact. Seed 7 now casts Deathgreeter T1 and Dina T5 under the S7 driver (hand order, no prioritisation); under the S6 driver the same seed casts Nature's Lore T5.
