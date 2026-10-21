# CP35 — cardsource export pinned; gate no longer reads C:\pabsim\data (G1); release-gate temp leak fixed (T7) (2026-10-21)

Applied by night\CP35_apply.py (deterministic; no Claude session). No kernel change.

## Summary
- `decks/CARDSOURCE_BG_COMMANDER_20261021.json` added: cardsource.py export, Scryfall 2026-10-21, BG + colorless, Commander-legal, 12628 cards.
- G1: tests/test_pab_v3_deck_cp26.py resolves v3 names against the pinned export, not C:\pabsim\data (gate now self-contained).
- Expectation change in that test: "supplement covers exactly the gaps" became "no gaps; every supplement record is a v3 card
  and is also in the export". The export includes colorless cards, so the old gap list is empty.
- CLAUDE.md and PASTE_ME.md (MANUAL): card-data lines now name the pinned export as the gate's source; Next stages marks G1 and T7 closed.
- T7: release_gate_tests/test_r02_release_gate.py removes its temporary repo copies (tearDownModule); no test added or changed.
- Evidence: EVIDENCE/CP35_CARDSOURCE_CHECK.md - all 61 excerpt texts and 149 contract fragments match current Oracle text.
- Follow-ups: none from this stage.
