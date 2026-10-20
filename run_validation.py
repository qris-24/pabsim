"""Strict local regression gate, *not* a Commander legality/engine validation.

R02 patch (v0.8 R02): the runner is split into `preflight()` (read-only
integrity checks, no writes of any kind), `run_suites()` and `main()`.
Every integrity check runs before any file is written. The coverage registry
is regenerated IN MEMORY and must be byte-identical to the shipped file; the
runner never rewrites it. Runner outputs (VALIDATION_RESULTS.json,
validation_stdout.txt) are not verified as inputs.
"""
import hashlib, json, sys, unittest, re, importlib.util, io, os
from pathlib import Path

ROOT=Path(__file__).resolve().parent

OLD_TEST_FILES=['test_reference_events.py','test_v03_extended.py',
                'test_v04_cost_and_copy.py','test_v04_hunger_saga.py',
                'test_v05_fixture_cards.py']
BASELINE_SHA='c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381'
# Files explicitly re-versioned by the R02 patch. The legacy Phase 8 manifest
# is still enforced for everything else.
R02_VERSIONED={'run_validation.py','build_registry.py','build_manifest.py',
               'PABTRV3_CARD_COVERAGE.json','README.md',
               'PHASE8_R02_FILE_MANIFEST.json','R02_PATCH_NOTES.md','R01_PATCH_NOTES.md',
               'pab_kernel.py','pab_r01_pest_rescuer.py','pab_r47_r48_sba.py','R47_R48_PATCH_NOTES.md','PHASE_CLOCK_DEPENDENCY_MAP.md','UPKEEP_AUDIT_NOTES.md','pab_turn_clock.py','R49_S1_PATCH_NOTES.md','pab_clock_s2.py','S2_PATCH_NOTES.md','pab_clock_s3.py','S3_PATCH_NOTES.md','pab_clock_s4.py','S4_PATCH_NOTES.md','pab_turn_loop.py','S5_PATCH_NOTES.md','HARD_STOP_2026-10-18.md','00_HANDOFF_2026-10-18.md','C41_C47_EXECUTION_NOTES.md','C48_C64_EXECUTION_NOTES.md','C65_C77_EXECUTION_NOTES.md','C78_C94_EXECUTION_NOTES.md','CONTRACTS_C41_C94_STATUS.md','pab_cast_s6.py','S6_PATCH_NOTES.md','pab_r52_village_rites.py','R52_R53_PATCH_NOTES.md','pab_cast_s7.py','S7_PATCH_NOTES.md','pab_opponents_s8.py','S8_PATCH_NOTES.md','pab_lands_s9.py','S9_PATCH_NOTES.md','s9_tests/__init__.py','s9_tests/test_v08_mana_tokens_s9.py','pab_commander_s10.py','S10_PATCH_NOTES.md','pab_interaction_s11.py','S11_PATCH_NOTES.md','pab_cast_s12.py','S12_PATCH_NOTES.md','pab_cast_s13.py','S13_PATCH_NOTES.md','pab_lands_s14.py','S14_PATCH_NOTES.md','pab_cast_s15.py','S15_PATCH_NOTES.md','pab_grist_s16.py','S16_PATCH_NOTES.md','pab_combat_s17.py','S17_PATCH_NOTES.md','pab_policy_s18.py','S18_PATCH_NOTES.md','pab_validation_s19.py','S19_PATCH_NOTES.md','pab_shigeki_s20.py','S20_PATCH_NOTES.md','build_model_coverage_s20.py','PABTRV3_MODEL_COVERAGE_S20.json'}
# Outputs the runner itself produces. Never verified as inputs.
RUNNER_OUTPUTS={'VALIDATION_RESULTS.json','validation_stdout.txt','PASTE_ME.md'}
R02_MANIFEST='PHASE8_R02_FILE_MANIFEST.json'
MANIFEST_BUILD='pab_reliability_v0_8_r02_r01'
REFERENCE_TEST_COUNT=857  # sum of per-file counts asserted below
TEST_DEF_RE=re.compile(r'^\s+def test_',re.M)   # one shared definition; build_manifest.py imports it

def count_test_defs(path):
    """Static `def test_` count of one test file (no import). Shared with build_manifest.py."""
    return len(TEST_DEF_RE.findall(Path(path).read_text()))

def sha(path):
    path=Path(path)
    assert path.is_file(), f'missing input: {path.name}'
    return hashlib.sha256(path.read_bytes()).hexdigest()

ORACLE_EXCERPT='decks/ORACLE_EXCERPT_CP28.json'      # CP28: the gate's only Oracle text source
ORACLE_REFS='CONTRACT_ORACLE_REFS_CP28.json'
ORACLE_SUPPLEMENT='decks/PAB_V3_ORACLE_SUPPLEMENT.json'
_QUOTES=str.maketrans({'‘':"'",'’':"'",'“':'"','”':'"'})

def oracle_normalize(text):
    """Collapse whitespace runs to one space; curly quotes to straight."""
    return re.sub(r'\s+',' ',text.translate(_QUOTES)).strip()

def oracle_reference_check(root,contract_ids,mapping=None,excerpt=None):
    """CP28: per contract, {'oracle_referenced','oracle_refs_checked','oracle_cr_authenticated','oracle_ref_errors',
    'oracle_subjects_missing'}. oracle_referenced is True only if the contract has refs and every fragment is found
    in its card's excerpt text; CP29: and it has subjects, each with excerpt text and at least one matching ref
    (oracle_subjects_missing lists the subjects that fail this). Fails closed (never raises): a missing/unreadable excerpt or mapping, a supplement sha256 mismatch,
    a contract absent from the mapping or a card absent from the excerpt makes the field False with an error.
    No CR text exists in the repo, so oracle_cr_authenticated is always False."""
    root=Path(root); errors=[]
    try:
        if mapping is None: mapping=json.loads((root/ORACLE_REFS).read_text(encoding='utf-8'))
        refs_by_contract=mapping['contracts']
    except Exception as e:
        refs_by_contract=None; errors.append(f'mapping unavailable: {ORACLE_REFS}: {type(e).__name__}')
    try:
        if excerpt is None: excerpt=json.loads((root/ORACLE_EXCERPT).read_text(encoding='utf-8'))
        cards=excerpt['cards']
        if excerpt['sources']['supplement']['sha256']!=hashlib.sha256((root/ORACLE_SUPPLEMENT).read_bytes()).hexdigest():
            cards=None; errors.append(f'excerpt supplement sha256 != {ORACLE_SUPPLEMENT}')
    except Exception as e:
        cards=None; errors.append(f'excerpt unavailable: {ORACLE_EXCERPT}: {type(e).__name__}')
    out={}
    for cid in contract_ids:
        entry=(refs_by_contract or {}).get(cid)
        refs=entry.get('refs',[]) if isinstance(entry,dict) else []
        subjects=entry.get('subjects',[]) if isinstance(entry,dict) else []
        errs=list(errors)
        if refs_by_contract is not None and entry is None: errs.append(f'{cid} not in mapping')
        found=0; matched=set()
        for r in refs:
            text=(cards or {}).get(r.get('card'),{}).get('oracle_text') if isinstance(r,dict) else None
            if text is None:
                if cards is not None: errs.append(f'{cid}: card not in excerpt: {r.get("card") if isinstance(r,dict) else r!r}')
            elif oracle_normalize(r.get('fragment') or '') and oracle_normalize(r['fragment']) in oracle_normalize(text): found+=1; matched.add(r['card'])
            else: errs.append(f'{cid}: fragment not found in {r["card"]}')
        # CP29: every subject card needs Oracle text in the excerpt and at least one matching ref.
        missing=[s for s in subjects if cards is None or s not in cards or s not in matched]
        out[cid]={'oracle_referenced':bool(refs) and bool(subjects) and not missing and not errs and found==len(refs),
                  'oracle_refs_checked':len(refs),'oracle_cr_authenticated':False,'oracle_ref_errors':errs,
                  'oracle_subjects_missing':missing}
    return out

def _load_registry_module(root):
    spec=importlib.util.spec_from_file_location('pab_build_registry_r02',root/'build_registry.py')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def preflight(root=ROOT):
    """All integrity checks. Read-only. Raises AssertionError with a specific
    message on the first failure. Returns the parsed coverage registry."""
    root=Path(root)
    registry_bytes=(root/'PABTRV3_CARD_COVERAGE.json').read_bytes()
    J=json.loads(registry_bytes)
    cards=J['cards']
    main=[c for c in cards if c['section']=='Mainboard']
    assert sum(c['quantity'] for c in main)==99, 'mainboard count'
    assert sum(c['quantity'] for c in main if c['group']=='land')==34, 'land count'
    assert sum(c['quantity'] for c in main if c['group']=='nonland')==65, 'nonland count'
    assert sum(c['quantity'] for c in cards if c['group']=='commander')==1, 'commander count'
    assert sum(c['quantity'] for c in cards if c['group']=='lesson')==1, 'lesson count'
    assert all(c['full_card_behavior_verified'] is False for c in cards), 'full_card_behavior_verified must be False'
    assert all(c['value_for_optimization'] is None for c in cards), 'value_for_optimization must be null'
    assert J['summary']['old_compiler_25_contract_passes']==10, 'old compiler passes'
    assert J['summary']['old_compiler_25_contract_failures']==15, 'old compiler failures'
    assert sha(root/'upstream_frozen/FROZEN_PABTRV3_BASELINE.txt')==BASELINE_SHA, 'frozen baseline changed'

    # Fail closed if historical reference engine, v0.6 zone source, original
    # test contracts or immutable audit inputs have been silently modified.
    for name in ['pab_focus_engine.py','pab_zones.py']:
        assert sha(root/name)==sha(root/'frozen_phase6'/name), f'frozen_phase6 drift: {name}'
    for name in OLD_TEST_FILES+['test_v06_physical_zones.py']:
        assert sha(root/'tests'/name)==sha(root/'frozen_phase6'/'tests'/name), f'frozen_phase6 test drift: {name}'
    prior_manifest=json.loads((root/'FILE_MANIFEST.json').read_text())
    assert prior_manifest['build']=='pab_reliability_v0_6', 'v0.6 manifest build id'
    for path,digest in prior_manifest['files_sha256'].items():
        if path.startswith(('upstream_frozen/','frozen_phase5/','frozen_previous_tests/')):
            assert sha(root/path)==digest, f'v0.6 input modified: {path}'
    for path in ['pab_focus_engine.py','pab_zones.py',
                 'tests/test_reference_events.py','tests/test_v03_extended.py',
                 'tests/test_v04_cost_and_copy.py','tests/test_v04_hunger_saga.py',
                 'tests/test_v05_fixture_cards.py','tests/test_v06_physical_zones.py']:
        assert sha(root/path)==prior_manifest['files_sha256'][path], f'v0.6 input modified: {path}'

    # Phase 7 manifest: all previous source and tests; generated metadata and
    # the (re)versioned runner/registry are exempt, exactly as in v0.8.
    phase7_manifest=json.loads((root/'PHASE7_FILE_MANIFEST.json').read_text())
    assert phase7_manifest['build']=='pab_reliability_v0_7', 'v0.7 manifest build id'
    for path,digest in phase7_manifest['files_sha256'].items():
        if path in ('PABTRV3_CARD_COVERAGE.json','VALIDATION_RESULTS.json','build_registry.py','run_validation.py','README.md','validation_stdout.txt'):
            continue
        assert sha(root/path)==digest, f'Phase 7 input modified: {path}'
    for name in ['pab_zone_bridge.py','pab_focus_engine_v07.py']:
        assert sha(root/name)==sha(root/'frozen_phase7'/name), f'frozen_phase7 drift: {name}'

    # Legacy Phase 8 manifest: enforced for every file R02 did not re-version.
    phase8_manifest=json.loads((root/'PHASE8_FILE_MANIFEST.json').read_text())
    assert phase8_manifest['build']=='pab_reliability_v0_8', 'v0.8 manifest build id'
    for path,digest in phase8_manifest['files_sha256'].items():
        if path in R02_VERSIONED or path in RUNNER_OUTPUTS:
            continue
        assert sha(root/path)==digest, f'Phase 8 package changed: {path}'

    # R02 manifest: pins every input of this release, including the
    # re-versioned files. Runner outputs are recorded but never verified.
    r02=json.loads((root/R02_MANIFEST).read_text())
    assert r02['build']==MANIFEST_BUILD, 'kernel manifest build id'
    for path,digest in r02['files_sha256'].items():
        assert path not in RUNNER_OUTPUTS, f'R02 manifest must not pin runner output: {path}'
        assert path!=R02_MANIFEST, 'R02 manifest must not pin itself'
        assert sha(root/path)==digest, f'R02 package changed: {path}'
    listed=set(r02['files_sha256'])
    on_disk={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
             and '__pycache__' not in p.parts and '.git' not in p.parts}-RUNNER_OUTPUTS-{R02_MANIFEST}
    assert on_disk==listed, f'R02 manifest file set mismatch: +{sorted(on_disk-listed)} -{sorted(listed-on_disk)}'

    # Registry must be reproducible in memory, byte for byte. Never rewritten here.
    reg=_load_registry_module(root)
    regenerated=reg.canonical_bytes(reg.build(root))
    assert regenerated==registry_bytes, 'coverage registry is stale: on-disk PABTRV3_CARD_COVERAGE.json != build_registry.build()'

    # Suite shape (static counts; preflight imports no test modules).
    def n(f): return count_test_defs(root/'tests'/f)
    assert sum(n(p) for p in OLD_TEST_FILES)==149, 'v0.5 regression contracts changed'
    assert n('test_c41_c47_contracts.py')==19, 'test_c41_c47_contracts.py count'
    assert n('test_c48_c64_contracts.py')==34, 'test_c48_c64_contracts.py count'
    assert n('test_c65_c77_contracts.py')==20, 'test_c65_c77_contracts.py count'
    assert n('test_c78_c94_contracts.py')==43, 'test_c78_c94_contracts.py count'
    assert n('test_stack_cp06.py')==15, 'test_stack_cp06.py count'
    assert n('test_cast_s6.py')==33, 'test_cast_s6.py count'
    assert n('test_cast_s7.py')==71, 'test_cast_s7.py count'
    assert n('test_opponents_s8.py')==21, 'test_opponents_s8.py count'
    assert n('test_lands_s9.py')==18, 'test_lands_s9.py count'
    assert n('test_commander_s10.py')==10, 'test_commander_s10.py count'
    assert n('test_interaction_s11.py')==12, 'test_interaction_s11.py count'
    assert n('test_cast_s12.py')==6, 'test_cast_s12.py count'
    assert n('test_cast_s13.py')==10, 'test_cast_s13.py count'
    assert n('test_lands_s14.py')==12, 'test_lands_s14.py count'
    assert n('test_cast_s15.py')==13, 'test_cast_s15.py count'
    assert n('test_grist_s16.py')==8, 'test_grist_s16.py count'
    assert n('test_combat_s17.py')==8, 'test_combat_s17.py count'
    assert n('test_policy_s18.py')==9, 'test_policy_s18.py count'
    assert n('test_validation_s19.py')==4, 'test_validation_s19.py count'
    assert n('test_auditfix_cp02.py')==15, 'test_auditfix_cp02.py count'
    assert n('test_auditfix_cp03.py')==7, 'test_auditfix_cp03.py count'
    assert n('test_auditfix_cp04.py')==6, 'test_auditfix_cp04.py count'
    assert n('test_auditfix_cp10.py')==17, 'test_auditfix_cp10.py count'
    assert n('test_auditfix_cp13.py')==9, 'test_auditfix_cp13.py count'
    assert n('test_auditfix_cp14.py')==5, 'test_auditfix_cp14.py count'
    assert n('test_auditfix_cp23.py')==8, 'test_auditfix_cp23.py count'
    assert n('test_shigeki_s20.py')==4, 'test_shigeki_s20.py count'
    assert n('test_r52_village_rites.py')==4, 'test_r52_village_rites.py count'
    assert n('test_integrated_turn_loop_s5.py')==7, 'test_integrated_turn_loop_s5.py count'
    assert n('test_priority_s3.py')==11, 'test_priority_s3.py count'
    assert n('test_r01_pest_rescuer.py')==13, 'test_r01_pest_rescuer.py count'
    assert n('test_turn_actions_s4.py')==13, 'test_turn_actions_s4.py count'
    assert n('test_turn_clock_s1.py')==10, 'test_turn_clock_s1.py count'
    assert n('test_turn_clock_s2.py')==16, 'test_turn_clock_s2.py count'
    assert n('test_upkeep_trigger_audit.py')==14, 'test_upkeep_trigger_audit.py count'
    assert n('test_v05_r01_corrections.py')==2, 'test_v05_r01_corrections.py count'
    assert n('test_v06_physical_zones.py')==56, 'test_v06_physical_zones.py count'
    assert n('test_v07_zone_bridge.py')==52, 'test_v07_zone_bridge.py count'
    assert n('test_v08_mana_tokens.py')==54, 'test_v08_mana_tokens.py count'
    assert n('test_pab_v3_deck_cp26.py')==5, 'test_pab_v3_deck_cp26.py count'
    assert n('test_oracle_refs_cp28.py')==7, 'test_oracle_refs_cp28.py count'
    assert n('test_oracle_subjects_cp29.py')==7, 'test_oracle_subjects_cp29.py count'
    total=sum(n(f.name) for f in (root/'tests').glob('test_*.py'))
    assert total==REFERENCE_TEST_COUNT, f'expected {REFERENCE_TEST_COUNT} reference tests, found {total}'
    return J

def _replay(root,name,module_attr,replacement):
    spec=importlib.util.spec_from_file_location('replay_'+name,root/'tests'/name)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    setattr(mod,module_attr,replacement)
    log=io.StringIO()
    r=unittest.TextTestRunner(stream=log).run(unittest.defaultTestLoader.loadTestsFromModule(mod))
    passed=r.testsRun-len(r.errors)-len(r.failures)-len(r.skipped)
    ok=r.wasSuccessful() and not r.skipped
    failed={t.id().rsplit('.',1)[-1] for t,_ in r.failures+r.errors}
    return passed,(None if ok else log.getvalue()),failed

def run_suites(root=ROOT,J=None):
    root=Path(root)
    sys.path.insert(0,str(root))
    cards=J['cards']
    suite=unittest.TestLoader().discover(str(root/'tests'),pattern='test_*.py')
    assert suite.countTestCases()==REFERENCE_TEST_COUNT, f'loader found {suite.countTestCases()} tests, expected {REFERENCE_TEST_COUNT}'
    out=unittest.TextTestRunner(verbosity=1).run(suite)

    # Separate compatibility gate: the 149 original v0.5 contracts replayed
    # against the candidate Game. Replays, not distinct tests.
    from pab_focus_engine_v07 import Game as CandidateGame
    candidate_passed=0; candidate_errors=[]
    for name in OLD_TEST_FILES:
        p,err,_=_replay(root,name,'Game',CandidateGame)
        candidate_passed+=p
        if err: candidate_errors.append({'file':name,'output':err})
    from pab_zone_bridge_v08 import PhysicalZoneGame as Phase8Game
    phase8_replay_passed,err,_=_replay(root,'test_v07_zone_bridge.py','PhysicalZoneGame',Phase8Game)
    phase8_replay_errors=[] if err is None else [err]

    # Promoted kernel (R01): replay every frozen contract family against it.
    # The 149 v0.5 contracts must fail on EXACTLY the superseded ones (R01: 112/113; R52: 91);
    # the v0.7 bridge (52) and v0.8 bridge (54) contracts must all pass.
    import pab_kernel
    r01_legacy_passed=0; r01_legacy_failed=set()
    for name in OLD_TEST_FILES:
        p,_,failed=_replay(root,name,'Game',pab_kernel.Game)
        r01_legacy_passed+=p; r01_legacy_failed|=failed
    r01_legacy_ok=(r01_legacy_failed==set(pab_kernel.SUPERSEDED_FROZEN_CONTRACTS)
                   and r01_legacy_passed==149-len(pab_kernel.SUPERSEDED_FROZEN_CONTRACTS))
    k7,e7,_=_replay(root,'test_v07_zone_bridge.py','PhysicalZoneGame',pab_kernel.PhysicalZoneGame)
    k8,e8,failed8=_replay(root,'test_v08_mana_tokens.py','PhysicalZoneGame',pab_kernel.PhysicalZoneGame)
    sup8=set(pab_kernel.SUPERSEDED_V08_CONTRACTS)                       # S9: frozen 274/307 pinned fail-closed lands
    kernel_bridge_ok=(k7==52 and k8==54-len(sup8) and failed8==sup8 and e7 is None)
    # Corrected full copy of the v0.5 fixture file (112/113 fixed) as a replay.
    spec=importlib.util.spec_from_file_location('r01_corrected_copy',root/'r01_tests'/'test_v05_fixture_cards_r01.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    log=io.StringIO(); rc=unittest.TextTestRunner(stream=log).run(unittest.defaultTestLoader.loadTestsFromModule(mod))
    corrected_passed=rc.testsRun-len(rc.errors)-len(rc.failures)-len(rc.skipped)
    corrected_ok=rc.wasSuccessful() and rc.testsRun==38
    # R52: corrected full copy of the v0.4 cost file (test_91 fixed: Village Rites costs {B}) as a replay.
    spec=importlib.util.spec_from_file_location('r52_corrected_copy',root/'r52_tests'/'test_v04_cost_and_copy_r52.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    log=io.StringIO(); rc52=unittest.TextTestRunner(stream=log).run(unittest.defaultTestLoader.loadTestsFromModule(mod))
    corrected52_passed=rc52.testsRun-len(rc52.errors)-len(rc52.failures)-len(rc52.skipped)
    corrected_ok=corrected_ok and rc52.wasSuccessful() and rc52.testsRun==25
    # S9: corrected full copy of the v0.8 bridge file (274/307: Blooming Marsh and Overgrown Tomb playable) as a replay.
    spec=importlib.util.spec_from_file_location('s9_corrected_copy',root/'s9_tests'/'test_v08_mana_tokens_s9.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    log=io.StringIO(); rc9=unittest.TextTestRunner(stream=log).run(unittest.defaultTestLoader.loadTestsFromModule(mod))
    corrected9_passed=rc9.testsRun-len(rc9.errors)-len(rc9.failures)-len(rc9.skipped)
    corrected_ok=corrected_ok and rc9.wasSuccessful() and rc9.testsRun==54

    # Contract execution record: one entry per contract class in the contract
    # test modules (CONTRACT/STATUS/SUBSTITUTIONS attributes), with its own
    # pass count from a fresh run of that class.
    contracts={}
    for modname in ['test_c41_c47_contracts.py','test_c48_c64_contracts.py','test_c65_c77_contracts.py','test_c78_c94_contracts.py','test_turn_clock_s2.py','test_priority_s3.py']:
        spec=importlib.util.spec_from_file_location('contracts_'+modname,root/'tests'/modname)
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        for cls in [getattr(mod,k) for k in dir(mod)]:
            if isinstance(cls,type) and hasattr(cls,'CONTRACT') and issubclass(cls,unittest.TestCase):
                rr=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
                contracts[cls.CONTRACT]={'issues':cls.ISSUES,'status':cls.STATUS,
                    'substitutions':cls.SUBSTITUTIONS,'tests_run':rr.testsRun,
                    'tests_passed':rr.testsRun-len(rr.failures)-len(rr.errors)-len(rr.skipped)-len(rr.expectedFailures),
                    'expected_failures':len(rr.expectedFailures),'unexpected_successes':len(rr.unexpectedSuccesses),
                    'engine_test_executed':cls.STATUS!='BLOCKED_UNSUPPORTED'}
    # CP28: oracle_referenced / oracle_refs_checked derived from the pinned excerpt; oracle_cr_authenticated stays False.
    oracle=oracle_reference_check(root,sorted(contracts))
    for cid,c in contracts.items(): c.update(oracle[cid])
    contracts_ok=(len(contracts)==59 and all(c['tests_run']>0 and c['tests_passed']+c['expected_failures']==c['tests_run']
                     and c['unexpected_successes']==0 for c in contracts.values()))

    # R02 release-gate tests: a separate suite, never counted in the 311.
    gate_run=gate_passed=0; gate_errors=[]
    if os.environ.get('PAB_R02_SKIP_GATE')!='1':
        gate=unittest.defaultTestLoader.discover(str(root/'release_gate_tests'),pattern='test_*.py',top_level_dir=str(root))
        log=io.StringIO()
        g=unittest.TextTestRunner(stream=log,verbosity=1).run(gate)
        gate_run=g.testsRun
        gate_passed=g.testsRun-len(g.errors)-len(g.failures)-len(g.skipped)
        if not g.wasSuccessful() or g.skipped: gate_errors=[log.getvalue()]

    result={
     'scope':'v0.5 events + v0.6 physical zones + v0.7 bounded zone bridge + v0.8 shared-mana and mirrored token reference, plus the promoted layers '+'+'.join(pab_kernel.PROMOTED)+'; NOT a playable engine',   # CP20: derived from pab_kernel.PROMOTED
     'release':'v0.8 with promoted patches '+', '.join(pab_kernel.PROMOTED)+' (frozen files untouched)',   # CP20: derived from pab_kernel.PROMOTED
     'frozen_deck_verified':True,
     'mainboard':99,'lands':34,'nonlands':65,'commander':1,'lesson_sideboard':1,
     'tests_run':out.testsRun,
     'tests_passed':out.testsRun-len(out.failures)-len(out.errors)-len(out.skipped),
     'failures':len(out.failures),'errors':len(out.errors),'skipped':len(out.skipped),
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
     'new_unique_phase8_tests':54,
     'phase8_previous_bridge_contract_replays':52,
     'phase8_previous_bridge_contract_passes':phase8_replay_passed,
     'phase8_previous_bridge_replay_errors':phase8_replay_errors,
     'kernel_version':pab_kernel.KERNEL_VERSION,
     'promoted_patches':pab_kernel.PROMOTED,
     'superseded_frozen_contracts':pab_kernel.SUPERSEDED_FROZEN_CONTRACTS,
     'kernel_legacy_149_replay_passes':r01_legacy_passed,
     'kernel_legacy_149_replay_failures':sorted(r01_legacy_failed),
     'kernel_legacy_failures_exactly_superseded_set':r01_legacy_ok,
     'kernel_v07_bridge_52_replay_passes':k7,
     'kernel_v08_bridge_54_replay_passes':k8,
     'kernel_corrected_v05_copy_38_replay_passes':corrected_passed,
     'kernel_corrected_v04_copy_25_replay_passes':corrected52_passed,
     'kernel_corrected_v08_copy_54_replay_passes':corrected9_passed,
     'kernel_v08_replay_failures':sorted(failed8),
     'superseded_v08_fixtures':pab_kernel.SUPERSEDED_V08_CONTRACTS,
     'frozen_engines_modified':False,
     'contracts_executed':contracts,
     'contracts_oracle_referenced':sum(c['oracle_referenced'] for c in contracts.values()),   # CP28
     'r02_release_gate_tests_run':gate_run,
     'r02_release_gate_tests_passed':gate_passed,
     'r02_release_gate_errors':gate_errors,
     'r02_registry_rewritten_by_runner':False,
     'shared_game_zone_mana_symbols_in_v08':True,
     'event_tokens_mirrored_with_distinct_physical_uids_in_v08':True,
     'complete_physical_board':False,
     'partial_land_mana_paths':['Forest','Swamp','Command Tower'],   # frozen zones path
     'partial_land_mana_paths_s9_bridge':['Blooming Marsh','Deathcap Glade','Woodland Cemetery','Undergrowth Stadium','Overgrown Tomb','Underground Mortuary','Darkbore Pathway // Slitherbore Pathway','Llanowar Wastes','Nurturing Peatland'],
     'other_land_names_unimplemented':0,   # S14
     'partial_demonic_tutor_resolution_only':False,   # S13
     'full_card_behavior_verified':0,
     'upstream_engine_edited':False,
     'existing_v05_event_kernel_modified':False,
     'v07_candidate_5_legacy_draw_sites_routed_through_shared_draw':True,
     'old_compiler_contracts_passing':10,'old_compiler_contracts_failing':15,
     'mass_replacement_sweep_allowed':False,
     'baseline_sha256':sha(root/'upstream_frozen/FROZEN_PABTRV3_BASELINE.txt'),
    }
    ok=(out.wasSuccessful() and not candidate_errors and candidate_passed==149
        and not phase8_replay_errors and phase8_replay_passed==52 and not gate_errors
        and r01_legacy_ok and kernel_bridge_ok and corrected_ok and contracts_ok)
    return result,ok

def main():
    J=preflight(ROOT)                      # no writes before this returns
    result,ok=run_suites(ROOT,J)
    (ROOT/'VALIDATION_RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')   # CP08: LF on Windows
    summary={k:result[k] for k in ('release','tests_run','tests_passed','failures','errors',
             'candidate_historical_contract_passes','phase8_previous_bridge_contract_passes',
             'r02_release_gate_tests_run','r02_release_gate_tests_passed',
             'kernel_version','kernel_legacy_149_replay_failures',
             'kernel_v07_bridge_52_replay_passes','kernel_v08_bridge_54_replay_passes',
             'kernel_corrected_v05_copy_38_replay_passes','kernel_corrected_v04_copy_25_replay_passes','kernel_corrected_v08_copy_54_replay_passes','kernel_v08_replay_failures')}
    summary['contracts']={k:f"{v['status']} {v['tests_passed']}/{v['tests_run']}"+(f" (+{v['expected_failures']} expected failures)" if v['expected_failures'] else '') for k,v in result['contracts_executed'].items()}
    print(json.dumps(summary,indent=2))
    if not ok: sys.exit(1)

if __name__=='__main__':
    main()
