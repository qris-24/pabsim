# CP31d integrity review of rp-CP31 (63b560b), 2026-10-20

Method: three independent read-only reviewers (root Python, test suites, docs/data/evidence) read every in-scope file; runtime probes re-run in a separate session. Gate on a clean Linux clone with the card data supplied: 861/861, 21/21. Status: REPRODUCED = probe re-run and confirmed; VERIFIED = checked against file contents; UNCONFIRMED = needs evidence the repo lacks. Nothing in this file changes kernel behaviour; each item below is its own follow-up stage.

## Clean
- PHASE8_R02_FILE_MANIFEST.json: all 250 pinned files match; no unpinned file on disk; unique_fixture_tests 861 = REFERENCE_TEST_COUNT.
- Test bookkeeping: 48 per-file counts match; loader runs 861; release gate expects (861, 861); no duplicate test names, skips or expectedFailure.
- Determinism: identical results across 10 PYTHONHASHSEED values.
- CONTRACT_ORACLE_REFS_CP28.json: all 149 fragments occur verbatim in decks/ORACLE_EXCERPT_CP28.json; source hashes match.
- decks/PAB_V3.json: 100 cards, 34 lands, no duplicates; identical to the Archidekt CSV.

## Kernel defects
- K1 REPRODUCED: lethal combat damage ignores indestructible (pab_combat_s17.py:164-170 -> pab_clock_s3.py:58).
- K2 REPRODUCED: scripted board wipe ignores regeneration shields (pab_interaction_s11.py:115-121; shields only work through destroy(), pab_cast_s15.py:129).
- K3 REPRODUCED: life_gained_turn is reset only at the controller's own cleanup (pab_clock_s2.py:42-43; the every-seat cleanup in pab_cast_s15.py:88-91 does not), so life gained on an opponent's turn counts at the controller's end step (Moseo admission and threshold).
- K4 REPRODUCED: Skullclamp's equip P/T is ignored by later toughness checks (pab_clock_s3.py:40-42, pab_cast_s15.py:95-97, pab_combat_s17.py:160; power at :155-159).
- K5 REPRODUCED: with exile_instead, the "remove Savra" policy exiles a different creature (pab_policy_s18.py:72 -> pab_interaction_s11.py:110-113 uses _own_creature_target); the S19 default seat-3 policy uses exile_instead (pab_validation_s19.py:195).
- K6 REPRODUCED: S19 clock_legal reports failures after a seat leaves (pab_validation_s19.py:241 requires turn==pturn+1; LossAwareClock skips seats, pab_opponents_s8.py:232-237).
- K7 REPRODUCED: resolve() at <=0 life sets game_lost without a lose_game trace entry (pab_clock_s3.py:67-68).
- K8 VERIFIED: Shigeki missing from creature/legend tables after S20 (pab_lands_s14.py:150,186; pab_cast_s15.py:266-267,299-305; pab_grist_s16.py:44).
- K9 VERIFIED: opponent blocks ignore flying (pab_combat_s17.py:213-218).
- K10 VERIFIED: "can't block" creatures can block under block_policy 'all' (pab_policy_s18.py:95-98).
- K11 VERIFIED: scripted edict ignores counters (pab_interaction_s11.py:137).
- K12 VERIFIED: commander-damage loss rewrites life to min(life,0) (pab_combat_s17.py:243; copied at pab_validation_s19.py:226).
- K13 VERIFIED: Shigeki's bounce cost leaves a stale skullclamp_attached link (pab_shigeki_s20.py:68).
- K14 UNCONFIRMED (needs CR text): Ribtruss Roaster counter LKI is taken when the trigger is created (pab_r47_r48_sba.py:29); C99 test name says the removed counter is reflected but the body asserts it is not (tests/test_turn_clock_s2.py:97-100).

## Gate hardening
- G1 VERIFIED: the gate reads C:\pabsim\data\golgari_commander.json (tests/test_pab_v3_deck_cp26.py:9), outside the repo and unpinned; contradicts CLAUDE.md ("never C:\pabsim\data"); fails on any other machine.
- G2 VERIFIED: every preflight check is a bare assert; python -O disables them while results still report frozen files verified (run_validation.py:38,108-220,240,322,356,371).
- G3 VERIFIED: PAB_R02_SKIP_GATE=1 gives exit 0 with 0 release checks run (run_validation.py:311,378-380).
- G4 VERIFIED: any untracked file in the repo folder fails the gate (run_validation.py:164-166 compares the on-disk set); manifests certify themselves (a coordinated edit of a frozen file, its frozen copy, the legacy manifests and a re-pin passes).

## Test hygiene
- T1 VERIFIED: 5 reference tests assert known-superseded behaviour against frozen engines and count as passes (v05 112/113, v04 91, v08 274/307); frozen, so only documentable.
- T2 VERIFIED: tautology at tests/test_combat_s17.py:96; the name says eight seeds, the loop has four.
- T3 VERIFIED: C87 tests its own fixture helper, never the kernel (tests/test_c78_c94_contracts.py:287-306).
- T4 VERIFIED: names or docstrings claim more than the body checks: test_priority_s3.py:53-57, test_c65_c77_contracts.py:254-258, test_lands_s9.py:50, test_cast_s6.py:128-130, test_lands_s14.py:127,134, test_validation_s19.py:29-31, test_integrated_turn_loop_s5.py:39-42, test_commander_s10.py:86, test_shigeki_s20.py:53, test_cast_s7.py:171-174; stale docstrings in test_upkeep_trigger_audit.py and test_c48_c64_contracts.py:7.
- T5 VERIFIED: broad assertRaises(Exception) at test_c65_c77_contracts.py:147,172,219 and test_cast_s6.py:72; assertTrue(outcomes) always true at test_policy_s18.py:95.
- T6 VERIFIED: test_auditfix_cp02/cp03/cp04 and test_stack_cp06 depend on import order (no sys.path.insert).
- T7 VERIFIED: the release gate leaks 16 temporary repo copies per run (release_gate_tests/test_r02_release_gate.py:16-19).

## Registry and documents
- PABTRV3_CARD_COVERAGE.json (built by build_registry.py:107-113): kernel_version and promoted_patches stop at S20; 21 executed contracts (C80-C86, C88-C99) appear in neither contract list; self-contradicting status keys; S15/S16 coverage claims retracted by S20 still present. Needs a build_registry.py stage.
- Fixed in CP31d: CONTRACTS_C41_C94_STATUS.md current table (C63, C65-C77 rows), validation_stdout.txt, ISSUE_LEDGER_CP06.json field gaps, README.md notice and duplicate section, PHASE_CLOCK_DEPENDENCY_MAP.md title, R47_R48_PATCH_NOTES.md upkeep line, CP07_PATCH_NOTES.md BOM/mojibake, pab_r01_pest_rescuer.py docstring.
- Source data, recorded and not changed: EVIDENCE/S6_CARD_EVIDENCE.json gives Tend the Pests as "When this creature dies" where the pinned excerpt says "When this token dies"; decks/PAB_V3_ARCHIDEKT_EXPORT.csv rows 20 (Creakwood Liege) and 30 (Fiend Artisan) have the hybrid cost spilling into extra fields (PAB_V3.json is correct); PASTE_ME.md says South Wind Avatar came in with the Oct 19 baseline, but it is already in upstream_frozen/FROZEN_PABTRV3_BASELINE.txt (UNCONFIRMED: may refer to an intermediate list).
- GitHub: the default branch is audit-cp02, not master; user decision 2026-10-20: set it to master in the GitHub settings and keep the old branches.
