# CP07 — Windows path separators in preflight; manifest re-pinned (2026-10-18)

Kernel unchanged. No frozen file, deck, Oracle, test, or fixture edited. Suite shape unchanged: 779 tests, 18/18 release gate.

## What
- `run_validation.py` `preflight()`: the `on_disk` set was built with `str(p.relative_to(root))`, which yields backslash-separated paths on Windows. It now uses `p.relative_to(root).as_posix()`, so the on-disk file set compares equal to the manifest's forward-slash keys.
- `build_manifest.py`: the manifest key `rel` had the same `str(p.relative_to(root))` form. It now uses `.as_posix()` too, so re-pinning on Windows writes the same forward-slash keys the Linux build wrote. Without this, re-pinning here would have rewritten every key with backslashes.
- `release_gate_tests/test_r02_release_gate.py`: checked for the same pattern; none present, unchanged.
- `PHASE8_R02_FILE_MANIFEST.json`: re-pinned with `py -3.14 build_manifest.py` (not hand-edited). Only the two edited files' digests changed and this notes file was added; 195 inputs pinned, 2 outputs recorded.

## Why
First run of the release gate on Windows failed in preflight with `R02 manifest file set mismatch`: every nested path appeared in `+` with backslashes and in `-` with forward slashes. The manifest format (forward slashes) was correct; the comparison carried a Linux-only separator assumption. `as_posix()` is a no-op on Linux, so the gate behaves identically there.

## Verification
`py -3.14 run_validation.py` run twice on Windows 10 (Python 3.14): both runs `Ran 779 tests ... OK`, exit 0; `VALIDATION_RESULTS.json` reports `r02_release_gate_tests_run` 18, `r02_release_gate_tests_passed` 18, `tests_passed` 779, `frozen_engines_modified` false. The regenerated `VALIDATION_RESULTS.json` was byte-identical to the committed one apart from CRLF line endings (Windows text-mode write), so it was restored and is not part of this commit.
