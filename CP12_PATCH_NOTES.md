# CP12 — Infuse with Vitality registry correction

- Source: CP11 registry audit finding A-S20-08, UNDERCLAIM.
- Updated `build_model_coverage_s20.py` and regenerated `PABTRV3_MODEL_COVERAGE_S20.json`: added "deathtouch until end of turn with lethal combat effects (CP03)" to Infuse with Vitality's `modeled` list and removed its obsolete `not_modeled` deathtouch note.
- `with_not_modeled_items`: 42 → 41.
- All 88/88 distinct card entries remain PARTIAL; 0 cards are certified.
- Registry documentation only; no other card entries, kernel files, tests, or deck contents changed.
- Added these patch notes and re-pinned the release manifest for the CP12 checkpoint.
