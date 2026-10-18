"""Strict local regression gate, *not* a Commander legality/engine validation."""
import hashlib, json, sys, unittest, re, importlib.util, io
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import build_registry

old_test_files=['test_reference_events.py','test_v03_extended.py',
                'test_v04_cost_and_copy.py','test_v04_hunger_saga.py',
                'test_v05_fixture_cards.py']

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
# Fail closed if historical reference engine, v0.6 zone source, original
# test contracts or immutable audit inputs have been silently modified.
for name in ['pab_focus_engine.py','pab_zones.py']:
    assert (ROOT/name).read_bytes() == (ROOT/'frozen_phase6'/name).read_bytes(), name
for name in old_test_files+['test_v06_physical_zones.py']:
    assert (ROOT/'tests'/name).read_bytes()==(ROOT/'frozen_phase6'/'tests'/name).read_bytes(), name
# The retained v0.6 archive manifest is a pinned prior-build checksum record.
prior_manifest=json.loads((ROOT/'FILE_MANIFEST.json').read_text())
assert prior_manifest['build']=='pab_reliability_v0_6'
for path,digest in prior_manifest['files_sha256'].items():
    if path.startswith('upstream_frozen/') or path.startswith('frozen_phase5/') or path.startswith('frozen_previous_tests/'):
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
for path in ['pab_focus_engine.py','pab_zones.py',
             'tests/test_reference_events.py','tests/test_v03_extended.py',
             'tests/test_v04_cost_and_copy.py','tests/test_v04_hunger_saga.py',
             'tests/test_v05_fixture_cards.py','tests/test_v06_physical_zones.py']:
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==prior_manifest['files_sha256'][path],path


suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
count=suite.countTestCases()
assert sum(len(re.findall(r'^\s+def test_', (ROOT/'tests'/p).read_text(), re.M))
           for p in old_test_files)==149, 'v0.5 regression contracts changed'
assert count==257, count
assert len(re.findall(r"^\s+def test_",(ROOT/"tests"/"test_v07_zone_bridge.py").read_text(),re.M))==52
out=unittest.TextTestRunner(verbosity=1).run(suite)
# Additional, separate compatibility gate: execute every one of the 149
# original v0.5 contracts against the *candidate* Game with canonical tokens.
# These are replays, not distinct new tests or proof of full-card fidelity.
from pab_focus_engine_v07 import Game as CandidateGame
candidate_passed=0
candidate_errors=[]
for name in old_test_files:
    spec=importlib.util.spec_from_file_location('phase7_replay_'+name,ROOT/'tests'/name)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.Game=CandidateGame
    replay=unittest.defaultTestLoader.loadTestsFromModule(mod)
    log=io.StringIO()
    result_replay=unittest.TextTestRunner(stream=log).run(replay)
    candidate_passed+=result_replay.testsRun-len(result_replay.errors)-len(result_replay.failures)-len(result_replay.skipped)
    if not result_replay.wasSuccessful() or result_replay.skipped:
        candidate_errors.append({'file':name,'output':log.getvalue()})

result={
 'scope':'v0.5 reference events + v0.6 physical zones + v0.7 bounded opt-in zone-event bridge; no performance predictions',
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
 'basic_land_fixture_only_in_v05_event_kernel':True,
 'real_individual_card_library_in_new_zone_kernel':True,
 'new_zone_kernel_integrated_with_v05_events':False,
 'bounded_phase7_opt_in_bridge':True,
 'candidate_historical_contract_replays':149,
 'candidate_historical_contract_passes':candidate_passed,
 'candidate_historical_contract_replay_errors':candidate_errors,
 'new_unique_phase7_tests':52,
 'partial_land_mana_paths':['Forest','Swamp','Command Tower'],
 'other_land_names_unimplemented':18,
 'partial_demonic_tutor_resolution_only':True,
 'full_card_behavior_verified':0,
 'upstream_engine_edited':False,
 'existing_v05_event_kernel_modified':False,
 'v07_candidate_5_legacy_draw_sites_routed_through_shared_draw':True,
 'old_compiler_contracts_passing':10,'old_compiler_contracts_failing':15,
 'mass_replacement_sweep_allowed':False,
 'baseline_sha256':hashlib.sha256((ROOT/'upstream_frozen/FROZEN_PABTRV3_BASELINE.txt').read_bytes()).hexdigest()
}
(ROOT/'VALIDATION_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if not out.wasSuccessful() or candidate_errors or candidate_passed!=149:sys.exit(1)
