"""R02 release-gate tests. A SEPARATE suite from the 311 reference fixtures.

These test the release runner's integrity, not Magic rules. Each tamper case
clones the package, changes one thing, and requires preflight to fail with the
SPECIFIC message for that change (CP05 strictness), not merely any failure.
"""
import importlib.util, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(root,name):
    spec=importlib.util.spec_from_file_location(f'r02gate_{name}_{abs(hash(str(root)))}',Path(root)/f'{name}.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def clone():
    d=Path(tempfile.mkdtemp(prefix='pab_r02_'))/'pkg'
    shutil.copytree(ROOT,d,ignore=shutil.ignore_patterns('__pycache__','.git'))
    return d

def preflight_message(root):
    try:
        load(root,'run_validation').preflight(root)
    except AssertionError as e:
        return str(e)
    return None

class RegistryDeterminism(unittest.TestCase):
    def test_import_has_no_side_effects(self):
        d=clone(); before=(d/'PABTRV3_CARD_COVERAGE.json').read_bytes()
        reg=load(d,'build_registry'); reg.build(d)
        self.assertEqual(before,(d/'PABTRV3_CARD_COVERAGE.json').read_bytes())
    def test_two_clean_clones_build_identical_bytes(self):
        a,b=clone(),clone()
        ra,rb=load(a,'build_registry'),load(b,'build_registry')
        self.assertEqual(ra.canonical_bytes(ra.build(a)),rb.canonical_bytes(rb.build(b)))
    def test_shipped_registry_matches_rebuild(self):
        reg=load(ROOT,'build_registry')
        self.assertEqual(reg.canonical_bytes(reg.build(ROOT)),(ROOT/'PABTRV3_CARD_COVERAGE.json').read_bytes())
    def test_source_hash_keys_sorted(self):
        J=json.loads((ROOT/'PABTRV3_CARD_COVERAGE.json').read_text())
        keys=list(J['summary']['source_hashes_sha256'])
        self.assertEqual(keys,sorted(keys))
    def test_manifest_builder_deterministic_and_excludes_outputs(self):
        m=load(ROOT,'build_manifest')
        a,b=m.build(ROOT),m.build(ROOT)
        self.assertEqual(m.canonical_bytes(a),m.canonical_bytes(b))
        self.assertFalse(set(a['files_sha256'])&{'VALIDATION_RESULTS.json','validation_stdout.txt',m.NAME})

class PreflightReadOnly(unittest.TestCase):
    def test_clean_clone_passes_and_writes_nothing(self):
        d=clone()
        snap={p:p.read_bytes() for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts}
        self.assertIsNone(preflight_message(d))
        after={p:p.read_bytes() for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts}
        self.assertEqual(snap,after)

class TamperFailClosed(unittest.TestCase):
    """Each case: one mutation -> nonzero outcome AND the intended message."""
    def _expect(self,mutate,fragment):
        d=clone(); mutate(d)
        msg=preflight_message(d)
        self.assertIsNotNone(msg,'preflight passed on tampered package')
        self.assertIn(fragment,msg)
    def test_registry_key_order_change_detected(self):
        def m(d):
            p=d/'PABTRV3_CARD_COVERAGE.json'; J=json.loads(p.read_text())
            J['summary']=dict(reversed(list(J['summary'].items())))
            p.write_text(json.dumps(J,indent=2)+'\n')  # same semantics, non-canonical key order
            assert json.loads(p.read_text())==json.loads((ROOT/'PABTRV3_CARD_COVERAGE.json').read_text())
        self._expect(m,'R02 package changed: PABTRV3_CARD_COVERAGE.json')
    def test_registry_semantic_edit_detected(self):
        def m(d):
            p=d/'PABTRV3_CARD_COVERAGE.json'; J=json.loads(p.read_text())
            J['cards'][0]['value_for_optimization']=1.0
            reg=load(d,'build_registry'); p.write_bytes(reg.canonical_bytes(J))
        self._expect(m,'value_for_optimization must be null')
    def test_stale_registry_detected_when_manifest_also_updated(self):
        def m(d):
            p=d/'PABTRV3_CARD_COVERAGE.json'; J=json.loads(p.read_text())
            J['summary']['full_verified_cards']=1
            reg=load(d,'build_registry'); p.write_bytes(reg.canonical_bytes(J))
            bm=load(d,'build_manifest'); (d/bm.NAME).write_bytes(bm.canonical_bytes(bm.build(d)))
        self._expect(m,'coverage registry is stale')
    def test_frozen_engine_byte_flip_detected(self):
        def m(d):
            p=d/'pab_focus_engine.py'; p.write_bytes(p.read_bytes()+b'\n# tamper\n')
        self._expect(m,'frozen_phase6 drift: pab_focus_engine.py')
    def test_r01_candidate_edit_detected(self):
        def m(d):
            p=d/'pab_r01_pest_rescuer.py'; p.write_bytes(p.read_bytes()+b'\n# tamper\n')
        self._expect(m,'R02 package changed: pab_r01_pest_rescuer.py')
    def test_kernel_entry_edit_detected(self):
        def m(d):
            p=d/'pab_kernel.py'; p.write_bytes(p.read_bytes()+b'\n# tamper\n')
        self._expect(m,'R02 package changed: pab_kernel.py')
    def test_v08_test_file_edit_detected(self):
        def m(d):
            p=d/'tests'/'test_v08_mana_tokens.py'; p.write_bytes(p.read_bytes()+b'\n# tamper\n')
        self._expect(m,'Phase 8 package changed: tests/test_v08_mana_tokens.py')
    def test_runner_edit_detected(self):
        def m(d):
            p=d/'run_validation.py'; p.write_bytes(p.read_bytes()+b'\n# tamper\n')
        self._expect(m,'R02 package changed: run_validation.py')
    def test_added_file_detected(self):
        def m(d): (d/'tests'/'test_extra.py').write_text('import unittest\nclass T(unittest.TestCase):\n    def test_x(self): pass\n')
        self._expect(m,'R02 manifest file set mismatch')
    def test_deleted_file_detected(self):
        def m(d): (d/'frozen_phase5'/'pab_focus_engine.py').unlink()
        self._expect(m,'missing input: pab_focus_engine.py')
    def test_manifest_pinning_runner_output_rejected(self):
        def m(d):
            p=d/'PHASE8_R02_FILE_MANIFEST.json'; M=json.loads(p.read_text())
            M['files_sha256']['VALIDATION_RESULTS.json']='0'*64
            p.write_text(json.dumps(M,indent=2,sort_keys=True)+'\n')
        self._expect(m,'R02 manifest must not pin runner output')

class ManifestMetadata(unittest.TestCase):
    """CP20: builder-derived manifest keys must agree with the kernel and the runner (shipped manifest, not a clone)."""
    def _manifest(self): return json.loads((ROOT/'PHASE8_R02_FILE_MANIFEST.json').read_text())
    def test_manifest_patches_equal_kernel_promoted(self):
        if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
        import pab_kernel
        self.assertEqual(self._manifest()['patches'],list(pab_kernel.PROMOTED))
    def test_manifest_unique_fixture_tests_equal_reference_count(self):
        rv=load(ROOT,'run_validation')
        self.assertEqual(self._manifest()['unique_fixture_tests'],rv.REFERENCE_TEST_COUNT)

class BlockedContractsProbed(unittest.TestCase):
    """CP21: a BLOCKED_UNSUPPORTED contract must prove the block on the kernel that models cards. Every such class
    defines a KERNEL_PROBE staticmethod (True = the card's action is accepted on pab_kernel.PhysicalZoneGame,
    False = refused); the check fails on a missing probe or on any probe that returns True (stale status)."""
    CONTRACT_MODULES=['test_c41_c47_contracts.py','test_c48_c64_contracts.py','test_c65_c77_contracts.py','test_c78_c94_contracts.py','test_turn_clock_s2.py','test_priority_s3.py']   # = run_validation.py contract modules
    def test_every_blocked_contract_is_refused_on_physical_zone_game(self):
        if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
        blocked={}
        for f in self.CONTRACT_MODULES:
            spec=importlib.util.spec_from_file_location('r02gate_contracts_'+f[:-3],ROOT/'tests'/f)
            mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            for cls in vars(mod).values():
                if isinstance(cls,type) and issubclass(cls,unittest.TestCase) and hasattr(cls,'CONTRACT') and cls.STATUS=='BLOCKED_UNSUPPORTED': blocked[cls.CONTRACT]=cls
        self.assertEqual(sorted(c for c,cls in blocked.items() if not isinstance(cls.__dict__.get('KERNEL_PROBE'),staticmethod)),[],'BLOCKED_UNSUPPORTED contract without KERNEL_PROBE')
        self.assertEqual(sorted(c for c,cls in blocked.items() if cls.KERNEL_PROBE() is not False),[],'BLOCKED_UNSUPPORTED contract accepted on PhysicalZoneGame (stale status)')

class EndToEnd(unittest.TestCase):
    def test_shipped_command_runs_twice_cleanly(self):
        """`python run_validation.py` must succeed, leave inputs untouched, and
        succeed again on the second run (no self-invalidation)."""
        d=clone()
        reg_before=(d/'PABTRV3_CARD_COVERAGE.json').read_bytes()
        man_before=(d/'PHASE8_R02_FILE_MANIFEST.json').read_bytes()
        env=dict(os.environ,PAB_R02_SKIP_GATE='1')  # inner run skips this suite
        for i in (1,2):
            r=subprocess.run([sys.executable,'run_validation.py'],cwd=d,env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,f'run {i} failed:\n{r.stderr[-2000:]}')
        self.assertEqual(reg_before,(d/'PABTRV3_CARD_COVERAGE.json').read_bytes())
        self.assertEqual(man_before,(d/'PHASE8_R02_FILE_MANIFEST.json').read_bytes())
        res=json.loads((d/'VALIDATION_RESULTS.json').read_text())
        self.assertEqual((res['tests_run'],res['tests_passed']),(843,843))
        self.assertEqual(res['candidate_historical_contract_passes'],149)
        self.assertEqual(res['phase8_previous_bridge_contract_passes'],52)
        self.assertEqual(res['kernel_legacy_149_replay_failures'],sorted(['test_112_teacher_pest_blocks_rescuer_at_upkeep_start','test_113_teacher_pest_entered_before_rescuer_trigger_resolves','test_91_village_rejects_mana_shortage_before_sac']))
        self.assertTrue(res['kernel_legacy_failures_exactly_superseded_set'])
        self.assertEqual((res['kernel_v07_bridge_52_replay_passes'],res['kernel_v08_bridge_54_replay_passes'],res['kernel_corrected_v05_copy_38_replay_passes'],res['kernel_corrected_v04_copy_25_replay_passes'],res['kernel_corrected_v08_copy_54_replay_passes']),(52,52,38,25,54))
        self.assertEqual(res['kernel_v08_replay_failures'],['test_274_unsupported_land_fails_closed','test_307_unsupported_named_nonbasic_mana_does_not_fallback'])   # S9 supersedes exactly these two

if __name__=='__main__':
    unittest.main()
