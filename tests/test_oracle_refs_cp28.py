"""CP28: per-contract Oracle references (CONTRACT_ORACLE_REFS_CP28.json) checked against the pinned
excerpt (decks/ORACLE_EXCERPT_CP28.json) by run_validation.oracle_reference_check(). Oracle only: no CR
text is in the repo, so oracle_cr_authenticated stays False for every contract. Certifies nothing."""
import copy, hashlib, importlib.util, json, re, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
CONTRACT_MODULES=['test_c41_c47_contracts.py','test_c48_c64_contracts.py','test_c65_c77_contracts.py',
                  'test_c78_c94_contracts.py','test_turn_clock_s2.py','test_priority_s3.py']   # run_validation.py contract loop
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def runner():
    spec=importlib.util.spec_from_file_location('rv_cp28',ROOT/'run_validation.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

class OracleRefs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rv=runner(); cls.mapping=load(ROOT/cls.rv.ORACLE_REFS); cls.excerpt=load(ROOT/cls.rv.ORACLE_EXCERPT)
        cls.ids=sorted({m for f in CONTRACT_MODULES for m in re.findall(r"CONTRACT='(C\d+)'",(ROOT/'tests'/f).read_text(encoding='utf-8'))})
        cls.result=cls.rv.oracle_reference_check(ROOT,cls.ids)

    def test_mapping_covers_exactly_the_59_contracts(self):
        self.assertEqual(self.ids,['C%d'%n for n in range(41,100)])
        self.assertEqual(sorted(self.mapping['contracts']),self.ids)

    def test_every_fragment_matches_its_card_excerpt(self):
        for cid,r in self.result.items():
            with self.subTest(contract=cid):
                self.assertEqual(r['oracle_ref_errors'],[])
                self.assertEqual(r['oracle_refs_checked'],len(self.mapping['contracts'][cid]['refs']))
                self.assertEqual(r['oracle_referenced'],r['oracle_refs_checked']>0)

    def test_excerpt_supplement_sha256_equals_repo_file(self):
        digest=hashlib.sha256((ROOT/self.rv.ORACLE_SUPPLEMENT).read_bytes()).hexdigest()
        self.assertEqual(self.excerpt['sources']['supplement']['sha256'],digest)
        self.assertEqual(self.excerpt['sources']['supplement']['path'],self.rv.ORACLE_SUPPLEMENT)

    def test_negative_control_mutated_fragment_not_matched(self):
        m=copy.deepcopy(self.mapping); ref=m['contracts']['C47']['refs'][0]
        ref['fragment']=ref['fragment'].replace('nontoken','token')
        r=self.rv.oracle_reference_check(ROOT,self.ids,mapping=m)
        self.assertFalse(r['C47']['oracle_referenced']); self.assertEqual(len(r['C47']['oracle_ref_errors']),1)
        self.assertTrue(r['C48']['oracle_referenced'])                                   # other contracts unaffected

    def test_fail_closed_missing_files_and_card(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.rv.oracle_reference_check(d,self.ids)                                  # no excerpt, mapping or supplement
        self.assertTrue(all(not v['oracle_referenced'] and v['oracle_ref_errors'] for v in r.values()))
        e=copy.deepcopy(self.excerpt); del e['cards']['Wriggling Grub']
        r=self.rv.oracle_reference_check(ROOT,self.ids,excerpt=e)
        self.assertFalse(r['C47']['oracle_referenced']); self.assertIn('card not in excerpt',r['C47']['oracle_ref_errors'][0])

    def test_fail_closed_supplement_sha256_mismatch(self):
        e=copy.deepcopy(self.excerpt); e['sources']['supplement']['sha256']='0'*64
        r=self.rv.oracle_reference_check(ROOT,self.ids,excerpt=e)
        self.assertTrue(all(not v['oracle_referenced'] for v in r.values()))
        self.assertTrue(all(any('sha256' in x for x in v['oracle_ref_errors']) for v in r.values()))

    def test_oracle_cr_authenticated_false_for_all_59(self):
        self.assertEqual(len(self.result),59)
        self.assertTrue(all(v['oracle_cr_authenticated'] is False for v in self.result.values()))

if __name__=='__main__':
    unittest.main()
