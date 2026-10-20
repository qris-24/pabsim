# CP31 — Pest Rescuer Oracle text vs the R01 snapshot (record only; nothing fixed)

## The two texts
- R01 snapshot, `pab_r01_pest_rescuer.py:4-6` (docstring; "offline snapshot; NOT independently authenticated"):
  "At the beginning of **your** upkeep, if you don't control a Pest creature token, create a 1/1 black and green
  Pest creature token..."
- Scryfall Oracle, `decks/ORACLE_SOURCE_SCRYFALL_CP31.json` (record "Pest Rescuer", id
  1f2a066a-7bcd-4e9d-8e52-0769cd6c8124, raw_response_sha256 e79839be…d4a):
  "At the beginning of **each** upkeep, if you don't control a Pest creature token, create a 1/1 black and green
  Pest creature token with "When this token dies, you gain 1 life."" followed by the lifegain replacement line.

## golgari_commander.json
`C:\pabsim\data\golgari_commander.json` has a Pest Rescuer object, and its `oracle_text` is exactly equal to the
Scryfall record's `oracle_text` (string equality, checked in CP31). So the card data already carried "each upkeep";
only the R01 docstring quotes "your upkeep".

## Which upkeeps the kernel fires on (code reading; no experiments)
- `pab_focus_engine_v07.py:428-439` `begin_upkeep()` takes no seat. It checks `controls_pest()` at trigger time
  (`:431`) and again on resolution (`:434`, intervening-if), once per Pest Rescuer (`:432`); Beledros is `:437-438`.
  It fires whenever it is called; it does not know whose upkeep it is.
- `pab_r01_pest_rescuer.py:21-26` (R01 mixin) replaces only `controls_pest()` (seat 0 must control a Pest creature
  *token*). It does not change when `begin_upkeep()` is called.
- `pab_clock_s2.py:35-37` (S2, included in `pab_kernel.Game` via `pab_clock_s4`, `pab_kernel.py:8,26`): on entering
  the upkeep of ANY seat, the clock calls `begin_upkeep()` ("each upkeep, every seat"; docstring `:5-6`).
  `pab_clock_s2.py:66-69`: a direct call is allowed only while the clock is unengaged (fixture shortcut).
- `tests/test_turn_clock_s2.py:26-42` (C95) already asserts this: Pest Rescuer is evaluated on all four seats'
  upkeeps, and retriggers on an opponent's upkeep after the Pest dies (`:38-42`).

## Conclusion
With the clock engaged, the kernel fires Pest Rescuer on every upkeep, which matches the Oracle text. The mismatch
is in the R01 docstring's quoted text ("your upkeep"), not in kernel behaviour. Unengaged fixtures call
`begin_upkeep()` directly and have no seat notion. Not changed in CP31 (record only).
