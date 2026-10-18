"""Build-only R02 manifest generator. Never invoked by run_validation.py.

Pins every input file of the v0.8 R02 release (sorted, canonical JSON).
Runner outputs and the manifest itself are recorded under
`runner_outputs_sha256_at_build` for review only; preflight never verifies
them, so the release cannot invalidate itself by running.
"""
import hashlib, json, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
NAME='PHASE8_R02_FILE_MANIFEST.json'
RUNNER_OUTPUTS={'VALIDATION_RESULTS.json','validation_stdout.txt'}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def build(root=HERE):
    files={}; outputs={}
    for p in sorted(root.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or p.name==NAME: continue
        rel=str(p.relative_to(root))
        (outputs if rel in RUNNER_OUTPUTS else files)[rel]=sha(p)  # top-level only; nested frozen copies are inputs
    return {
      'build':'pab_reliability_v0_8_r02_r01',
      'scope':'frozen Savra deterministic rules reference only; R02 runner integrity + R01 Pest Rescuer token predicate + R47 Roaster resolution-time count + R48 zero-toughness SBA promoted; frozen files, deck and Oracle untouched',
      'patches':["R02", "R01", "R47", "R48", "R49", "S1", "S2", "S3"],
      'parent_manifest':'PHASE8_FILE_MANIFEST.json',
      'baseline_sha256':sha(root/'upstream_frozen/FROZEN_PABTRV3_BASELINE.txt'),
      'unique_fixture_tests':473,
      'full_card_verified':0,
      'files_sha256':files,
      'runner_outputs_sha256_at_build':outputs,
    }

def canonical_bytes(obj):
    return (json.dumps(obj,indent=2,sort_keys=True)+'\n').encode('utf-8')

if __name__=='__main__':
    data=build()
    (HERE/NAME).write_bytes(canonical_bytes(data))
    print(f'{NAME}: {len(data["files_sha256"])} inputs pinned, {len(data["runner_outputs_sha256_at_build"])} outputs recorded')
