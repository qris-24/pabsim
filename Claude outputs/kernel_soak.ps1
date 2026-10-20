<#
kernel_soak.ps1 - determinism soak for the PAB kernel (C:\pabsim\pab_reliability_v0_8_r02_r01).

Read-only: clones the last COMMITTED state of the repo into a temp folder, runs the full gate
(run_validation.py) once per PYTHONHASHSEED, and writes a report to C:\pabsim\soak_<stamp>\.
The working repo is never touched. Uncommitted changes are not tested.

Two checks per seed:
  1. pass/fail of the gate and the names of failing tests (unittest "FAIL:" / "ERROR:" lines);
  2. sha256 of VALIDATION_RESULTS.json (sorted keys, no timestamps), so any seed-dependent
     result - including the known replay-failure lists - shows up as a different hash.

Run:  powershell -NoProfile -ExecutionPolicy Bypass -File C:\pabsim\night\kernel_soak.ps1
#>
param(
    [string]$Repo  = "C:\pabsim\pab_reliability_v0_8_r02_r01",
    [int]$Seeds    = 500,
    [double]$Hours = 8
)

$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$work  = Join-Path $env:TEMP "kernel_soak_$stamp"
$out   = "C:\pabsim\soak_$stamp"                     # outside the repo
New-Item -ItemType Directory -Force -Path $out | Out-Null

# 1. Isolated copy of the committed code
git clone --quiet $Repo $work
if ($LASTEXITCODE -ne 0) { throw "git clone failed - check `$Repo" }
$commit = git -C $work rev-parse --short HEAD
$results = Join-Path $work "VALIDATION_RESULTS.json"
$baseline = (Get-FileHash $results -Algorithm SHA256).Hash      # committed results, for comparison
Set-Location $work

# 2. One full gate run per seed, until the seed limit or the time limit
$deadline = (Get-Date).AddHours($Hours)
$summary  = Join-Path $out "summary.csv"
"seed,exit_code,seconds,results_sha256,failed_tests" | Out-File $summary -Encoding utf8
$failCounts = @{}
$hashSeeds  = @{}
$ErrorActionPreference = "Continue"
try {
  for ($s = 1; $s -le $Seeds -and (Get-Date) -lt $deadline; $s++) {
    $env:PYTHONHASHSEED = "$s"
    $sw   = [Diagnostics.Stopwatch]::StartNew()
    $log  = cmd /c "py -3.14 run_validation.py 2>&1"
    $code = $LASTEXITCODE
    $sw.Stop()
    $failed = @($log | ForEach-Object { if ($_ -match '^(FAIL|ERROR): (\S+) \((.+)\)') { "$($Matches[3])" } })
    foreach ($f in $failed) { $failCounts[$f] = 1 + [int]$failCounts[$f] }
    $h = if (Test-Path $results) { (Get-FileHash $results -Algorithm SHA256).Hash } else { "MISSING" }
    if (-not $hashSeeds.ContainsKey($h)) {
        $hashSeeds[$h] = @()
        if (Test-Path $results) { Copy-Item $results (Join-Path $out "results_seed_$s.json") }   # one copy per distinct result
    }
    $hashSeeds[$h] += $s
    if ($code -ne 0) { $log | Out-File (Join-Path $out "seed_$s.log") -Encoding utf8 }
    "$s,$code,$([math]::Round($sw.Elapsed.TotalSeconds,1)),$($h.Substring(0,12)),$($failed -join ';')" |
        Out-File $summary -Append -Encoding utf8
  }
} finally {
  $ran = $s - 1
  # 3. Report
  $report = @("commit $commit | seeds run: $ran | command: py -3.14 run_validation.py", "")
  if ($failCounts.Count -eq 0) {
      $report += "Gate: no failing test under any seed."
  } else {
      $report += "test,failed_seeds,of_seeds,verdict"
      foreach ($k in $failCounts.Keys) {
          $n = $failCounts[$k]
          $v = if ($n -eq $ran) { "always fails (ordinary bug)" } else { "FLAKY: depends on seed" }
          $report += "$k,$n,$ran,$v"
      }
  }
  $report += ""
  if ($hashSeeds.Count -eq 1) {
      $only = @($hashSeeds.Keys)[0]
      $same = if ($only -eq $baseline) { "identical to the committed file" } else { "DIFFERS from the committed file (results_seed_1.json saved)" }
      $report += "VALIDATION_RESULTS.json: one result across all $ran seeds; $same."
  } else {
      $report += "VALIDATION_RESULTS.json: $($hashSeeds.Count) DIFFERENT results across seeds (nondeterminism). Copies saved as results_seed_<first seed>.json:"
      foreach ($k in $hashSeeds.Keys) { $report += "  $($k.Substring(0,12)): seeds $(@($hashSeeds[$k])[0..9] -join ',')$(if ($hashSeeds[$k].Count -gt 10) {' ...'}) ($($hashSeeds[$k].Count) seeds)" }
  }
  $report | Out-File (Join-Path $out "REPORT.txt") -Encoding utf8
  Set-Location $env:TEMP
  Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
}
