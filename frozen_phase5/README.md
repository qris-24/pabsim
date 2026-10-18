# PABTRV3 — deterministic reference kernel v0.5 (Phase 5)

**Purpose:** An isolated, *partial* event-contract reference for the **frozen** PABTRV3 — Death Bog, Thousand Cuts Commander deck. This is **not** an integrated patch to the previous full simulator, a playable Commander game, independent Oracle validation, or a deck evaluation.

## Reproduce

Python 3.10+ and the standard library:

```sh
python run_validation.py
```

The command verifies the exact frozen decklist SHA-256, regenerates the coverage registry, runs exactly **149 local unit tests**, and rewrites `VALIDATION_RESULTS.json`. No random simulation, deck modification, or optimizer is run.

## Changed from v0.4

- **Bug repair:** Pest Rescuer now checks all controlled creatures with the **Pest** subtype, including nontoken **Teacher's Pest**, at trigger creation and trigger resolution. Earlier versions incorrectly checked Pest tokens only.
- **Mana fixtures:** Tap an already-present Sol Ring for two colorless, Arcane Signet for either of Savra's black or green, or Golgari Signet for exactly black and green after spending one existing mana. Respect tapped status and control. The historical audit does *not* pin the exact supplemental Oracle text for Arcane Signet or Sol Ring.
- **Basic-land searches:** Sakura-Tribe Elder sacrifices as an activation cost, then can find an explicitly supplied basic Forest/Swamp to the battlefield **tapped**. Nature's Lore pays {1}{G} and finds an explicitly supplied basic Forest **untapped**. Search results are fixtures only. **No nonbasic Forest ETBs or mana-producing land engine.**
- **Pest Infestation:** {X}{X}{G}; up to X explicit artifact/enchantment targets, including zero; destroy still-legal objects, then create **2X ordinary BG dies-gain Pests**. If it had targets and all became illegal, it fails to resolve, producing no Pests. Magecraft and Chatterfang hooks use the existing reference model.
- **Unearth:** {B}, target creature card in graveyard with mana value at most 3, reanimate on resolution; target legality is checked again at resolution. Separate {2} cycling fixture does not cast a spell or trigger Magecraft. No complete hand/library engine.
- **Skullclamp:** {1} equip fixture; +1/-1 effective toughness check for modeled stats, death-trigger draw-two counter and equipment detachment. Zero-toughness death is **not a sacrifice** and can happen through indestructible. No full equipment/attachment rules or complete counter/layer/SBA/priority engine. Exact supplementary Oracle text not pinned.

**38 additional passing tests** (111 → **149**). **Eight** previously unsupported mainboard nonlands have now gained *partial* reference behavior, increasing **45/65 → 53/65**. **Twelve** remain without dedicated reference behavior. **Zero** full cards are certified.

## Strict limitations

- `Game.add` is an artificial battlefield setup helper, **not casting**.
- Floating mana is supplied directly or via a modeled rock; lands do not yet tap for mana.
- Library candidates and basic lands are deliberately **injected fixtures**, not a shuffled legal 99-card library. Draws are counters; they do not create real hand cards.
- No real opponent board, active edicts, full mana timing, arbitrary stack priority/APNAP, counterspells, continuous effects, combat, complete token-state actions, protection, or all modes of modal spells.
- The old `engine.py` and `oracle.py` are **unmodified and not validated**. The saved **10/25 pass, 15/25 fail** compiler signatures have not been rerun.
- Card records are derived from the attached focus audit, which describes reading snapshot text for 61 colored cards, not independently pinning live Oracle data. Four colorless cards and 34 land *copies* remain incompletely source-verified.
- All `value_for_optimization` fields are `null`; none may be interpreted as zero-value. No replacement sweeps or card changes are authorized.

See `PABTRV3_PHASE5_REPORT.md` and `PABTRV3_NEW_SESSION_HANDOFF.md` for exact engineering state and next gates.
