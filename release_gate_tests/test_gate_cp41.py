"""CP41 (A2 Gate; review items G2-G4 in EVIDENCE/CP31d_INTEGRITY_REVIEW.md): the gate cannot be switched off or
certify itself. Release-gate tests, not reference fixtures.

G2  python -O / PYTHONOPTIMIZE strip assert statements: the runner refuses to run and writes nothing.
G3  PAB_R02_SKIP_GATE=1 never exits 0 (EndToEnd in test_r02_release_gate.py runs it); a full run must execute
    RELEASE_GATE_TEST_COUNT release checks and pass them all.
G4  an unpinned file on disk is named, with the fix; the legacy manifests are pinned in run_validation.py, so a
    coordinated edit of a frozen file, its frozen copy, the legacy manifests and a re-pin fails.
"""
import importlib.util, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEGACY=['FILE_MANIFEST.json','PHASE7_FILE_MANIFEST.json','PHASE8_FILE_MANIFEST.json']

def load(root,name):
    spec=importlib.util.spec_from_file_location(f'cp41gate_{name}_{abs(hash(str(root)))}',Path(root)/f'{name}.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

_CLONES=[]
def tearDownModule():
    for p in _CLONES: shutil.rmtree(p,ignore_errors=True)

def clone():
    t=Path(tempfile.mkdtemp(prefix='pab_cp41_')); _CLONES.append(t); d=t/'pkg'
    shutil.copytree(ROOT,d,ignore=shutil.ignore_patterns('__pycache__','.git'))
    return d

def preflight_message(root):
    try:
        load(root,'run_validation').preflight(root)
    except AssertionError as e:
        return str(e)
    return None

def snapshot(d):
    return {p:p.read_bytes() for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts}

def _env():
    """No inherited PYTHONOPTIMIZE; PAB_R02_SKIP_GATE=1 so a runner without the refusal cannot start these tests again."""
    return dict({k:v for k,v in os.environ.items() if k!='PYTHONOPTIMIZE'},PAB_R02_SKIP_GATE='1')

class OptimizeRefused(unittest.TestCase):
    def _refused(self,args,env):
        d=clone(); before=snapshot(d)
        r=subprocess.run([sys.executable,*args,'run_validation.py'],cwd=d,env=env,capture_output=True,text=True,timeout=900)
        self.assertEqual(r.returncode,1,r.stderr[-2000:])
        self.assertIn('assertions are disabled (python -O or PYTHONOPTIMIZE): the gate refuses to run',r.stderr)
        self.assertEqual(before,snapshot(d))                    # nothing written, results included
    def test_python_O_refused(self):
        self._refused(['-O'],_env())
    def test_pythonoptimize_env_refused(self):
        self._refused([],dict(_env(),PYTHONOPTIMIZE='1'))
    def test_each_entry_point_refuses(self):
        d=clone(); env=_env()
        for call in ('preflight(r.ROOT)','run_suites(r.ROOT,None)'):
            with self.subTest(call=call):
                r=subprocess.run([sys.executable,'-O','-c',f'import run_validation as r; r.{call}'],cwd=d,env=env,capture_output=True,text=True,timeout=900)
                self.assertNotEqual(r.returncode,0); self.assertIn('AssertionError: assertions are disabled',r.stderr)

class ReleaseChecksCounted(unittest.TestCase):
    def test_exit_code_needs_every_release_check(self):
        rv=load(ROOT,'run_validation'); n=rv.RELEASE_GATE_TEST_COUNT
        def res(run,passed,skipped=False): return {'r02_release_gate_tests_run':run,'r02_release_gate_tests_passed':passed,'r02_release_gate_skipped':skipped}
        self.assertEqual(rv.exit_code(True,res(n,n)),0)
        self.assertEqual(rv.exit_code(True,res(n-1,n-1)),1)        # a release check went missing
        self.assertEqual(rv.exit_code(True,res(n+1,n+1)),1)        # one was added without the bookkeeping
        self.assertEqual(rv.exit_code(True,res(0,0)),1)
        self.assertEqual(rv.exit_code(True,res(n,n-1)),1)
        self.assertEqual(rv.exit_code(True,res(0,0,True)),rv.SKIPPED_GATE_EXIT)
        self.assertEqual([rv.exit_code(False,res(n,n)),rv.exit_code(False,res(0,0,True))],[1,1])
        self.assertNotIn(rv.SKIPPED_GATE_EXIT,(0,1))

class StrayFilesNamed(unittest.TestCase):
    def test_unpinned_file_is_named_with_the_fix(self):
        d=clone(); (d/'notes.txt').write_text('x\n')
        msg=preflight_message(d)
        self.assertIsNotNone(msg)
        self.assertIn("R02 manifest file set mismatch: +['notes.txt'] -[]",msg)
        self.assertIn('delete it, or run build_manifest.py',msg)

class LegacyManifestsAnchored(unittest.TestCase):
    def test_reformatted_legacy_manifest_detected(self):
        for name in LEGACY:
            with self.subTest(manifest=name):
                d=clone(); p=d/name; J=json.loads(p.read_text())
                p.write_text(json.dumps(J,indent=1)+'\n')        # same content, other bytes
                bm=load(ROOT,'build_manifest'); (d/bm.NAME).write_bytes(bm.canonical_bytes(bm.build(d)))
                self.assertEqual(preflight_message(d),f'legacy manifest changed: {name} (frozen since the root commit 7e8ddfe; LEGACY_MANIFEST_SHA in run_validation.py)')
    def test_coordinated_frozen_edit_detected(self):
        """The review's case: frozen file + its frozen copy + every legacy manifest that pins them + a re-pin."""
        d=clone()
        for rel in ('pab_zones.py','frozen_phase6/pab_zones.py'):
            p=d/rel; p.write_bytes(p.read_bytes()+b'\n# coordinated edit\n')
        changed=0
        for name in LEGACY:
            p=d/name; J=json.loads(p.read_text())
            for rel in ('pab_zones.py','frozen_phase6/pab_zones.py'):
                if rel in J['files_sha256']:
                    J['files_sha256'][rel]=__import__('hashlib').sha256((d/rel).read_bytes()).hexdigest(); changed+=1
            p.write_text(json.dumps(J,indent=2)+'\n')
        self.assertEqual(changed,5)
        bm=load(ROOT,'build_manifest'); (d/bm.NAME).write_bytes(bm.canonical_bytes(bm.build(d)))
        self.assertEqual(preflight_message(d),'legacy manifest changed: FILE_MANIFEST.json (frozen since the root commit 7e8ddfe; LEGACY_MANIFEST_SHA in run_validation.py)')

if __name__=='__main__':
    unittest.main()
