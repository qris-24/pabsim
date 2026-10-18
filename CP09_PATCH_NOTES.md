# CP09 — CLAUDE.md and ledger reconciliation (A01 findings folded in) (2026-10-18)

Docs only. Kernel unchanged. No source, frozen file, deck, Oracle, test, or fixture edited. Suite shape unchanged: 779 tests, 18/18 release gate.

## What
- `CLAUDE.md` (new, 54 lines): repo layout, gate/suite/re-pin/registry commands, frozen-file list, project rules, session rules, and the open queue (AUD-01/02/03 as A-S20-12/13/14; A-S20-05/06/08/09/10/11 per ledger; AUD-04 = A-S20-03 repaired at CP06).
- `ISSUE_LEDGER_CP06.json`: added A-S20-12 (AUD-01, P1, `pab_lands_s9.py:tap_lands_policy`, colored-mana double count), A-S20-13 (AUD-02, P2, `pab_interaction_s11.py`, impossible opponent script accepted), A-S20-14 (AUD-03, P1, `pab_cast_s13.py`, tutor pre-commits library choice at cast); all `status: OPEN`, source "A01 audit 2026-10-18, probes replayed at CP06: persisting". Set `fix_authorized: true` on A-S20-04 and A-S20-07 with note "merged to master 2026-10-18 under fix-as-found rule". Nothing else in the file changed (sorted-key, indent-2 formatting verified byte-identical on roundtrip before editing).
- `PHASE8_R02_FILE_MANIFEST.json`: re-pinned with `py -3.14 build_manifest.py` (not hand-edited); CLAUDE.md and this notes file added as inputs, ledger digest updated.

## Why
The A01 audit (2026-10-18) found three kernel issues not yet in the ledger, and A-S20-04 / A-S20-07 had been repaired and merged to master at CP03 / CP04 under the fix-as-found rule while the ledger still showed `fix_authorized: false`. CLAUDE.md records the working rules so new sessions do not have to rediscover them from the handoff and patch-note chain.

## Verification
`py -3.14 run_validation.py 2> ..\gate.txt | Out-Null; Get-Content ..\gate.txt -Tail 3` run once on Windows 10 (Python 3.14.7): `Ran 779 tests ... OK`, exit 0; `VALIDATION_RESULTS.json` reports 18/18 release checks. After the run `git status --porcelain` listed only the files this task intentionally changed.
