"""Strict local regression gate, *not* a Commander legality/engine validation."""
import hashlib, json, sys, unittest
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import build_registry

J=json.loads((ROOT/'PABTRV3_CARD_COVERAGE.json').read_text())
cards=J['cards']
main=[c for c in cards if c['section']=='Mainboard']
assert sum(c['quantity'] for c in main)==99
assert sum(c['quantity'] for c in main if c['group']=='land')==34
assert sum(c['quantity'] for c in main if c['group']=='nonland')==65
assert sum(c['quantity'] for c in cards if c['group']=='commander')==1
assert sum(c['quantity'] for c in cards if c['group']=='lesson')==1
assert all(c['full_card_behavior_verified'] is False for c in cards)
assert all(c['value_for_optimization'] is None for c in cards)
assert J['summary']['old_compiler_25_contract_passes']==10
assert J['summary']['old_compiler_25_contract_failures']==15
assert hashlib.sha256((ROOT/'upstream_frozen/FROZEN_PABTRV3_BASELINE.txt').read_bytes()).hexdigest()== 'c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381'

suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
count=suite.countTestCases()
assert count==149, count
out=unittest.TextTestRunner(verbosity=1).run(suite)
result={
 'scope':'isolated PABTRV3 event kernel only; no performance predictions',
 'date':'2026-10-17',
 'frozen_deck_verified':True,
 'mainboard':99,'lands':34,'nonlands':65,'commander':1,'lesson_sideboard':1,
 'tests_run':out.testsRun,
 'tests_passed':out.testsRun-len(out.failures)-len(out.errors)-len(out.skipped),
 'failures':len(out.failures), 'errors':len(out.errors), 'skipped':len(out.skipped),
 'reference_partial_nonlands':sum(c['group']=='nonland' and c['status']=='PARTIAL_REFERENCE_TESTED' for c in cards),
 'reference_unsupported_nonlands':sum(c['group']=='nonland' and c['status']=='NOT_IN_REFERENCE_KERNEL' for c in cards),
 'land_source_verified':False,
 'colorless_nonlands_pinned':False,
 'basic_land_fixture_only':True,
 'full_card_behavior_verified':0,
 'upstream_engine_edited':False,
 'old_compiler_contracts_passing':10,'old_compiler_contracts_failing':15,
 'mass_replacement_sweep_allowed':False,
 'baseline_sha256':hashlib.sha256((ROOT/'upstream_frozen/FROZEN_PABTRV3_BASELINE.txt').read_bytes()).hexdigest()
}
(ROOT/'VALIDATION_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if not out.wasSuccessful():sys.exit(1)
