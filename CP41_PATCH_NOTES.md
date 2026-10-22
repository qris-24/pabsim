# CP41 — A2 Gate: G2-G4 (2026-10-21)

Gate-only stage, applied by night\CP41_apply.py (deterministic; built and gated in a sandbox clone of rp-CP40). No kernel, frozen or reference-test file changed. User decisions (2026-10-21): keep the strict on-disk check and name the stray files; anchor the legacy manifests with hardcoded sha256; the EndToEnd exit-code expectation moves 0 -> 3 (approved; before-copy EVIDENCE/CP41_SUPERSEDED/test_r02_release_gate_pre_cp41.py).

## Summary
- G2: preflight() and run_suites() call require_assertions(): under python -O or PYTHONOPTIMIZE the runner raises before any check or write ("assertions are disabled ... the gate refuses to run") and exits 1.
- G3: PAB_R02_SKIP_GATE=1 (only the release gate's inner run uses it) now exits 3 (SKIPPED_GATE_EXIT), never 0, and VALIDATION_RESULTS.json records r02_release_gate_skipped. A full run must execute RELEASE_GATE_TEST_COUNT (28) release checks and pass them all, or it fails.
- G4: the strict on-disk file-set check stays (user decision); its error now says what to do (+ unpinned: delete it or re-pin; - pinned but missing). The three legacy manifests are pinned by sha256 in run_validation.py (LEGACY_MANIFEST_SHA; unchanged since the root commit 7e8ddfe), so the review's coordinated edit (frozen file, frozen copy, legacy manifests, re-pin) now fails.
- release_gate_tests/test_gate_cp41.py: 7 release-gate tests; each fails on rp-CP40. EndToEnd (test_r02_release_gate.py) expects exit 3 and r02_release_gate_skipped True.
- Tests: 918 reference tests (unchanged); release gate 28/28 (was 21/21).
- CLAUDE.md: gate command note, RELEASE_GATE_TEST_COUNT bookkeeping, -O and skip-flag rule, legacy-manifest pin, Next stages (G1-G4 closed).
- Limit (unchanged by design): run_validation.py itself is pinned only by the re-pinnable R02 manifest; the anchor makes a coordinated edit visible as a change to its LEGACY_MANIFEST_SHA constants.
- Follow-ups: none.
