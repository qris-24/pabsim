# CP31c — original compiler retired (2026-10-20)

## Decision (user, 2026-10-20)
Go/no-go condition 2 ("original compiler integrated and tested") is RETIRED. The original card-text compiler
(engine.py / oracle.py; not in the repo) is superseded by the kernel's contract suite (C41-C99) and reference
tests. Its 25-signature result (10 pass / 15 fail) stays as a historical record only.

## Reason
- Source unavailable: the compiler (`tablesim.oracle.compile_card`, imported from `phase2_candidate/`) is not in the repo.
- The kernel supersedes it: card behaviour is now checked by the contract suite (C41-C99) and the reference tests.
- Old engine output was already ruled not usable as evidence.

The historical assertions in `run_validation.py` (old_compiler 10/15, lines 115-116 and 374) are unchanged and stay
as tamper checks on the historical record. No frozen file was edited.

## Signature records (step 3, read-only)
Search: the words "compiler" / "signature" in `upstream_frozen/` and `frozen_previous_tests/`.
- `upstream_frozen/test_pab_compiler.py`: the 25 signatures (`TESTS`, lines 46-72), each a predicate on the compiled card.
- `upstream_frozen/PAB_COMPILER_CONTRACT_RESULTS.json` (found by file name in the same folder): per-signature results, 10 PASS / 15 FAIL.
- `upstream_frozen/PABTRV3_MECHANICAL_INVENTORY.csv:89`: Pest Summoning "KNOWN PHASE2 DEFECT — compiler misreads as immediate gain1".
- `frozen_previous_tests/`: no matches.

Coverage = contracts in `CONTRACT_ORACLE_REFS_CP28.json` whose `refs` name the card (card level only; whether a
contract exercises the same mechanic as the signature is not assessed here).

| # | Signature | Card | What it checked | Old result | Covering contract(s) |
|---|---|---|---|---|---|
| 1 | Savra separate BG sacrifice triggers | Savra, Queen of the Golgari | two color-filtered (B, G) sacrifice triggers | PASS | C43, C45, C51, C52, C55, C60, C71, C78, C79 |
| 2 | Pest Summoning makes 2 tokens | Pest Summoning | creates 2 BG Pest tokens (not immediate lifegain) | FAIL | C48 |
| 3 | Sedgemoor Witch magecraft makes token | Sedgemoor Witch | magecraft (cast/copy instant/sorcery) creates a BG Pest | FAIL | none |
| 4 | Hunger Tide first chapters make BG Insects | The Hunger Tide Rises | chapters I-III create BG Insect tokens | FAIL | C57, C58, C59 |
| 5 | Hunger Tide fourth chapter sacrifices and searches | The Hunger Tide Rises | chapter IV sacrifice then tutor/reanimate | FAIL | C57, C58, C59 |
| 6 | Wriggling Grub makes TWO BG worms | Wriggling Grub | dies -> two BG Worm tokens | PASS | C47 |
| 7 | Infestation Sage dies to BG flying Insect | Infestation Sage | dies -> BG Insect token with flying | PASS | none |
| 8 | Pest Rescuer creates tokens | Pest Rescuer | upkeep BG Pest creation | FAIL | C42, C57, C63, C95 |
| 9 | Pest Rescuer lifegain replacement | Pest Rescuer | lifegain replacement (gain that much plus 1) | FAIL | C42, C57, C63, C95 |
| 10 | Moseo ETB creates Pest | Moseo, Vein's New Dean | ETB Pest token | FAIL | C41, C42, C98 |
| 11 | Moseo infusion reanimates | Moseo, Vein's New Dean | end-step infusion reanimation, MV <= life gained | FAIL | C41, C42, C98 |
| 12 | Cauldron of Essence death drain | Cauldron of Essence | creature death -> each opponent drain | PASS | none |
| 13 | Cauldron of Essence activated reanimation | Cauldron of Essence | {1}{B}{G}, T, sacrifice: reanimate | PASS | none |
| 14 | South Wind Avatar lifegain at death | South Wind Avatar | another creature dies -> gain life (toughness) | FAIL | none |
| 15 | South Wind Avatar drains on gain | South Wind Avatar | lifegain -> each opponent loses 1 | PASS | none |
| 16 | Teacher's Pest returns from graveyard | Teacher's Pest | {B}{G} graveyard recursion | PASS | none |
| 17 | Blight Mound makes BG tokens on nontoken death | Blight Mound | nontoken creature dies -> BG Pest | FAIL | C43, C47 |
| 18 | Feral Appetite graveyard-targeted tokens | Feral Appetite | exile creature card from graveyard -> BG Pest | FAIL | none |
| 19 | Ribtruss Roaster makes BG tokens by counters | Ribtruss Roaster | end step Pests equal to +1/+1 counters | FAIL | C60, C61, C98, C99 |
| 20 | Immoral Bargain sacrifices X as cost | Immoral Bargain | sacrifice X creatures as additional cost | FAIL | none |
| 21 | Chatterfang adds GREEN squirrels | Chatterfang, Squirrel General | token replacement adds green Squirrels | PASS | C48, C49, C51, C52, C57, C60 |
| 22 | Beledros upkeep makes BG Pest | Beledros Witherbloom | upkeep BG Pest creation | FAIL | C62, C63, C95 |
| 23 | Witherbloom Charm modal sac/draw | Witherbloom Charm | sacrifice a permanent -> draw two | PASS | C80 |
| 24 | Witherbloom Command mill and land | Witherbloom Command | mill mode | PASS | C94 |
| 25 | Agent grants commander artifact/creature deaths | Agent of the Iron Throne | commander gains artifact/creature death drain | FAIL | C43, C44, C56 |

Uncovered (no contract names the card): Sedgemoor Witch (#3), Infestation Sage (#7), Cauldron of Essence (#12, #13),
South Wind Avatar (#14, #15), Teacher's Pest (#16), Feral Appetite (#18), Immoral Bargain (#20).
These are new contract candidates (CLAUDE.md "## Next stages", CP31c follow-up). Nothing was reconstructed or re-run.
