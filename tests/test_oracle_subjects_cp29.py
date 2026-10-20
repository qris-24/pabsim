"""CP29: oracle_referenced requires every subject card (CONTRACT_ORACLE_REFS_CP28.json `subjects`) to have
Oracle text in the pinned excerpt and at least one matching ref. A subject is a card whose own behaviour the
contract's tests assert (not a fixture helper or stand-in); it must be a string literal in the contract class.
Certifies nothing."""
import ast, copy, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
CONTRACT_MODULES=['test_c41_c47_contracts.py','test_c48_c64_contracts.py','test_c65_c77_contracts.py',
                  'test_c78_c94_contracts.py','test_turn_clock_s2.py','test_priority_s3.py']   # run_validation.py contract loop
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def runner():
    spec=importlib.util.spec_from_file_location('rv_cp29',ROOT/'run_validation.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def class_literals():
    """{contract id: set of string constants in that contract's class body}, from the module source (no import)."""
    out={}
    for f in CONTRACT_MODULES:
        for node in ast.parse((ROOT/'tests'/f).read_text(encoding='utf-8')).body:
            if not isinstance(node,ast.ClassDef): continue
            cid=next((s.value.value for s in node.body if isinstance(s,ast.Assign) and isinstance(s.value,ast.Constant)
                      and any(isinstance(t,ast.Name) and t.id=='CONTRACT' for t in s.targets)),None)
            if cid: out[cid]={n.value for n in ast.walk(node) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
    return out

class OracleSubjects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rv=runner(); cls.mapping=load(ROOT/cls.rv.ORACLE_REFS); cls.excerpt=load(ROOT/cls.rv.ORACLE_EXCERPT)
        cls.literals=class_literals(); cls.ids=sorted(cls.literals)
        cls.result=cls.rv.oracle_reference_check(ROOT,cls.ids)

    def test_every_subject_is_a_literal_in_its_contract_class(self):
        self.assertEqual(sorted(self.mapping['contracts']),self.ids)
        for cid,entry in self.mapping['contracts'].items():
            with self.subTest(contract=cid):
                self.assertIsInstance(entry['subjects'],list); self.assertTrue(entry['subject_basis'].strip())
                self.assertEqual(sorted(set(entry['subjects'])-self.literals[cid]),[])

    def test_c45_true_skullclamp_covered(self):   # CP31 (approved): Skullclamp Oracle text from scryfall_cp31; was False/missing
        self.assertTrue(self.result['C45']['oracle_referenced'])
        self.assertEqual(self.result['C45']['oracle_subjects_missing'],[])
        self.assertEqual(self.excerpt['cards']['Skullclamp']['source'],'scryfall_cp31')

    def test_c76_true(self):   # CP31 (approved): both subject lands sourced from scryfall_cp31; was False
        self.assertTrue(self.result['C76']['oracle_referenced'])
        self.assertEqual(self.result['C76']['oracle_subjects_missing'],[])

    def test_c96_false_with_no_subjects(self):
        self.assertEqual(self.mapping['contracts']['C96']['subjects'],[])
        self.assertFalse(self.result['C96']['oracle_referenced'])

    def test_negative_control_subject_removed_from_excerpt_copy(self):
        cid=next(c for c in self.ids if self.result[c]['oracle_referenced'])
        subject=self.mapping['contracts'][cid]['subjects'][0]
        e=copy.deepcopy(self.excerpt); del e['cards'][subject]
        r=self.rv.oracle_reference_check(ROOT,self.ids,excerpt=e)
        self.assertFalse(r[cid]['oracle_referenced']); self.assertIn(subject,r[cid]['oracle_subjects_missing'])

    def test_no_true_contract_has_an_uncovered_subject(self):
        cards=self.excerpt['cards']; norm=self.rv.oracle_normalize
        for cid,r in self.result.items():
            subjects=self.mapping['contracts'][cid]['subjects']
            with self.subTest(contract=cid):
                self.assertEqual(r['oracle_subjects_missing']==[] and bool(subjects) or not r['oracle_referenced'],True)
                if r['oracle_referenced']:
                    for s in subjects:
                        self.assertIn(s,cards)
                        self.assertTrue(any(x['card']==s and norm(x['fragment']) in norm(cards[s]['oracle_text'])
                                            for x in self.mapping['contracts'][cid]['refs']))

    def test_empty_subjects_always_false_and_cr_unauthenticated(self):
        for cid,r in self.result.items():
            with self.subTest(contract=cid):
                if not self.mapping['contracts'][cid]['subjects']: self.assertFalse(r['oracle_referenced'])
                self.assertIs(r['oracle_cr_authenticated'],False)

if __name__=='__main__':
    unittest.main()
