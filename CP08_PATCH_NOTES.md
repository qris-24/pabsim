# CP08 — LF line endings for runner outputs on Windows; manifest re-pinned (2026-10-18)

Kernel unchanged. No frozen file, deck, Oracle, test, or fixture edited. Suite shape unchanged: 779 tests, 18/18 release gate.

## What
- `run_validation.py` `main()`: the only text-mode write in the runner, `(ROOT/'VALIDATION_RESULTS.json').write_text(...)`, now passes `encoding='utf-8', newline='\n'`. On Windows the default text-mode newline translation turned every `\n` into `\r\n`, so the file came out CRLF after each gate run. The JSON payload is unchanged (it is ASCII-only, `sort_keys=True`, `indent=2`, trailing newline), only the line terminator is fixed.
- `build_registry.py`: audited, no change needed. `PABTRV3_CARD_COVERAGE.json` is already written with `write_bytes(canonical_bytes(...))`, which encodes to UTF-8 with LF and bypasses newline translation. The only text-mode `open()` in the file is a read of the CSV inventory.
- `build_manifest.py`: audited, no change needed. `PHASE8_R02_FILE_MANIFEST.json` is already written with `write_bytes(canonical_bytes(...))`.
- `validation_stdout.txt`: not written by any of the three scripts. It is a shell capture of runner stdout and is listed only as a runner output (never verified as an input). The gate command for this task sends stdout to `Out-Null` and stderr to a file outside the repository, so it is not touched.
- `PHASE8_R02_FILE_MANIFEST.json`: re-pinned with `py -3.14 build_manifest.py` (not hand-edited). Only the digest of `run_validation.py` changed and this notes file was added; 196 inputs pinned, 2 outputs recorded.

## Why
CP07 verification found `VALIDATION_RESULTS.json` byte-identical to the committed file apart from CRLF line endings after a Windows run, so `git status` showed it modified after every gate run and it had to be restored by hand. The runner's write is now platform-independent. `newline='\n'` is a no-op on Linux, so the gate writes identical bytes there.

## Verification
`py -3.14 run_validation.py 2> ..\cp08_gate.txt | Out-Null` run twice on Windows 10 (Python 3.14.7): both runs `Ran 779 tests ... OK`, exit 0. After both runs `git status --porcelain` listed only the files this task intentionally changed (`run_validation.py`, `PHASE8_R02_FILE_MANIFEST.json`, `CP08_PATCH_NOTES.md`); the regenerated `VALIDATION_RESULTS.json` was byte-identical to the committed one, LF line endings included.
