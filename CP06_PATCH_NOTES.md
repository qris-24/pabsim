# CP06 — A-S20-03 physical spell stack migration

**Authorization:** 2026-10-18 user explicitly requested "correct the bug" following the recorded CP05 hard stop. This includes supersession of the obsolete S6/S7 *cast spell remains in physical hand* assertion. Scope is the new CP06 migration layer; no deck, Lesson, frozen source, Phase 9, or optimizer modifications.

## New implementation

- `pab_stack_cp06.py`: `StackEnabledZones` extends the frozen `DeckZones` without modifying `pab_zones.py`. A card cast through `PhysicalZoneGame.cast_from_hand` leaves `hand`, enters physical `stack`, and stays linked to its original UID in `stack_cards`. Every one of the currently supported hand-cast paths is routed through this new top-layer postcondition. Casting costs/triggers are paid/emitted by the original implementation; the physical move to stack occurs before `cast_from_hand` returns or priority can be exercised.
- The physical `stack` is a distinct zone, included in physical identity/integrity checks. It allows no token or land casts, retains no controller, and enforces one-to-one physical stack/ledger UID accounting after casting.
- Resolution-time zone requirements in **versioned** modules `pab_cast_s6`, `s7`, `s12`, `s13`, `s15`, `pab_grist_s16`, and `pab_shigeki_s20` were changed from `hand` to `stack`. Permanent spells move stack → battlefield; instants/sorceries stack → graveyard. Legacy zones are not affected.
- S6 ledger and helper invariants are revised strictly: standalone S6 stage objects still require hand if used on a pre-CP06 instance, while the promoted CP06 instance requires stack. No global relaxation of hand membership or erroneous alias between stack and hand.
- New spell and associated triggers are placed above earlier pending objects, retaining the inherited relative cost-trigger/magecraft order. This repairs the order of two sequential instant casts as a bounded policy; it does not establish full MTG APNAP or a general response engine.
- Both `tests/test_cast_s6.py` and `tests/test_cast_s7.py` are *versioned revised expectations*: their helper asserts that a pending spell is in `stack`, instead of asserting `hand`. Immutable exact pre-CP06 sources were copied to `EVIDENCE/CP06_SUPERSEDED/`, and the original frozen Phase 8 311 fixtures remain untouched.
- `tests/test_stack_cp06.py` adds 15 positive/negative/identity/zone-integrity probes, including single and multiple simultaneous instant spells, a source-side unaffected frozen `DeckZones`, rejected casts, spell-to-graveyard, and creature/permanent-to-battlefield outcomes.

## Bounded and not claimed

No opponent reactive spells, comprehensive responses/priority, countering/copying/replacement spells, APNAP, target re-picking, or full multiplayer stack functionality has been certified. A passing release gate demonstrates only the covered local contracts. Do not declare any of the 88 distinct deck/sideboard names fully certified or run replacement comparisons. A-S20-03's missing **physical hand→stack→resolution zone link** is addressed; full Magic stack semantics remain open.

**Reference release gate:** `python run_validation.py`; **baseline:** frozen 100-card deck plus separate Pest Summoning Lesson; **Phase 9:** NO-GO.
