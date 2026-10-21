# CP35 cardsource export pinned and checked (2026-10-21)

- File: `decks/CARDSOURCE_BG_COMMANDER_20261021.json`, sha256 `f0b12ceb8878d4b92be836b4ca3cc7b95f0999ed07b4c97e6c9a5d45781b1254`.
- Produced by cardsource.py (sha256 starting `7be877a5f298d927`; the copy at C:\pabsim\cardsource matches it)
  - stated provenance, not checkable from the repo: run by Claude in its sandbox on 2026-10-21 - from Scryfall Oracle Cards bulk data updated
  2026-10-21T09:01:59.312+00:00 (download sha256 `4f0593ac82360766842eefc8c754137f86a70c0f5eb2a0b9bd8fe378a028aaf6`), filters: color identity within BG,
  legal in Commander. 12628 cards. Exported 2026-10-21T15:27:37+00:00.
- Checks (computed by night\CP35_apply.py; the stage refuses to run if any fails):
  - PAB v3: 87 names, all present in the export.
  - Oracle supplement: all 8 records (colorless-identity cards) are also in the export.
  - Pinned excerpt (decks/ORACLE_EXCERPT_CP28.json): all 61 card texts equal the export's current Oracle text
    (multi-face cards composed as in build_oracle_excerpt.py).
  - CONTRACT_ORACLE_REFS_CP28.json: all 149 fragments occur verbatim in the export's text.
  - Oracle supplement texts (8) and the CP31 Scryfall records (4): all equal the export's text.
- Meaning: the pinned excerpt, the contract fragments, the supplement and the CP31 records all match Scryfall's current Oracle
  text as of the date above. Oracle wording inside test strings (SUBSTITUTIONS, notes) is not checked here.
- Not changed: the excerpt and its sources (golgari_commander.json, the supplement, the CP31 Scryfall file) stay as pinned;
  build_oracle_excerpt.py still reads C:\pabsim\data (not run by the gate).
