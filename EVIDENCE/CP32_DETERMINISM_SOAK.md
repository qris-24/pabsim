# CP32 determinism soak (2026-10-20/21)

- Commit tested: `d56670a` (rp-CP31d), from REPORT.txt line 1.
- Method (night\kernel_soak.ps1): fresh clone of the committed repo with `core.autocrlf=false` in %TEMP%; the full gate
  `py -3.14 run_validation.py` once per PYTHONHASHSEED 1..500; per seed: exit code, failing test names, and the sha256 of
  VALIDATION_RESULTS.json.
- Machine: Codie (i5-3570K, Windows, Python 3.14), after the faulty RAM was removed and a memory test passed.
- Seeds run: 500 of 500. Failing tests: none under any seed. Non-zero exit codes: none.
- Distinct VALIDATION_RESULTS.json results: 1 (`BA63BFE62FEA...` in summary.csv); REPORT.txt states it is identical to the
  committed file.
- Time per seed: mean 44.9 s, min 39.2 s, max 68.8 s (summary.csv).
- Files: `CP32_DETERMINISM_SOAK/REPORT.txt` and `summary.csv`, copied from C:\pabsim\soak\soak_20261020_2002 and
  normalised from UTF-8 with BOM and CRLF (as PowerShell wrote them) to UTF-8 without BOM and LF. Seed logs and
  results_seed_*.json are not copied.

## Limits
- Only the hash seed varies. Clock, the `random` module, file-system order and the machine stay the same, so this shows
  hash-order independence of the gate, not determinism in general.
- A clean soak covers what the gate covers, not the whole kernel; it is not evidence about rules coverage.

## Void earlier run
- The run in C:\pabsim\soak_20261020_0918 (rp-CP30, seeds 1-419, no REPORT.txt) ran on faulty RAM: a Python access
  violation (seed 334), two corrupt reads of intact card data (seeds 413, 418) and two unclean reboots on 2026-10-20.
  It is not evidence and is not copied here.
