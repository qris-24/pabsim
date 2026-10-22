# CP42 — A2 Tests 2: T2, T4, T5, T6 (2026-10-21)

Test-only stage, applied by night\CP42_apply.py (deterministic; built and gated in a sandbox clone of rp-CP41). No kernel, frozen or frozen-fixture file changed; no expected value changed and no test renamed. User decisions (2026-10-21): make each name's claim true where the stronger check passes, otherwise narrow the docstring and record it; keep every test name (docstrings and comments only).

## Summary
- T2 (test_combat_s17.py): the driver test runs the eight seeds its name says (was four), and its tautology is replaced: each opponent lost at least its combat damage, and life_ledger matches the life totals.
- T5: assertRaises(Exception) narrowed to the exact error and message (c65_c77 C70, C72, C75: BridgeError; test_cast_s6.py: IllegalAction); test_policy_s18.py's always-true assertTrue(outcomes) now pins the observed {'lost'} (all eight games).
- T4 made true: s6 refuses the card on the battlefield too; s14 plays every land type directly; s19 shows all eight life-change kinds the ledger replays (seeds 0, 6, 14 plus a Witherbloom Command / Blood Artist scenario); s5 checks mana produced equals lands played and is emptied at the step's end, over all eight seeds; s10 checks Savra is cast on the first turn the lands make {2}{B}{G}.
- T4 narrowed (docstring or comment): s3 (no kernel card makes a second SBA round; one round is tested), s9, c65 Grim Backwoods, s20 registry ('modeled' are hand-written claims, A-S20-08), s10 (runs 20 turns, not 16), s7 (Pest Summoning is castable since S13, so the name's 'lesson' is stale); stale docstrings in test_upkeep_trigger_audit.py and test_c48_c64_contracts.py.
- T6: test_auditfix_cp02/cp03/cp04 and test_stack_cp06 put the repo root on sys.path before their imports; release_gate_tests/test_tests_cp42.py checks every reference test file does (fails on rp-CP41).
- Tests: 918 reference tests (unchanged); release gate 29/29 (was 28/28). CLAUDE.md: 29/29 in the gate note, and its release_gate_tests/ line no longer says 21 (stale since CP41). T1 stays documented only (frozen files).
- Follow-ups: none.
