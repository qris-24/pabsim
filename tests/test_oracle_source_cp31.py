"""CP31: third pinned Oracle source, decks/ORACLE_SOURCE_SCRYFALL_CP31.json (Scryfall card fields, verbatim),
used by build_oracle_excerpt.py after golgari_commander.json and the supplement (source label scryfall_cp31).
Checks that the excerpt text equals the source records, that run_validation.oracle_reference_check() fails
closed on a scryfall sha256 mismatch, and that the recorded deck-export sha256 matches the file. Certifies nothing."""
import copy, hashlib, importlib.util, json, shutil, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
EXPORT='decks/CP31_SCRYFALL_DECK_EXPORT.json'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def runner():
    spec=importlib.util.spec_from_file_location('rv_cp31',ROOT/'run_validation.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

class OracleSourceScryfall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rv=runner(); cls.excerpt=load(ROOT/cls.rv.ORACLE_EXCERPT); cls.source=load(ROOT/cls.rv.ORACLE_SCRYFALL)
        cls.records={r['name']:r for r in cls.source['records']}
        cls.ids=['C%d'%n for n in range(41,100)]

    def test_excerpt_records_scryfall_path_and_sha256(self):
        s=self.excerpt['sources']['scryfall']
        self.assertEqual(s['path'],self.rv.ORACLE_SCRYFALL)
        self.assertEqual(s['sha256'],sha(ROOT/self.rv.ORACLE_SCRYFALL))

    def test_scryfall_cards_in_excerpt_match_source_records(self):
        from_scryfall=sorted(n for n,c in self.excerpt['cards'].items() if c['source']=='scryfall_cp31')
        self.assertEqual(from_scryfall,['Geier Reach Sanitarium','Mikokoro, Center of the Sea','Skullclamp'])
        for n in from_scryfall:
            with self.subTest(card=n):
                self.assertEqual(self.excerpt['cards'][n]['oracle_text'],self.records[n]['oracle_text'])
                self.assertRegex(self.records[n]['raw_response_sha256'],r'^[0-9a-f]{64}$')

    def test_fail_closed_on_mutated_scryfall_copy(self):
        with tempfile.TemporaryDirectory() as d:
            for f in (self.rv.ORACLE_REFS,self.rv.ORACLE_EXCERPT,self.rv.ORACLE_SUPPLEMENT,self.rv.ORACLE_SCRYFALL):
                (Path(d)/f).parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/f,Path(d)/f)
            self.assertTrue(self.rv.oracle_reference_check(d,['C45'])['C45']['oracle_referenced'])   # unmutated copy passes
            p=Path(d)/self.rv.ORACLE_SCRYFALL; p.write_bytes(p.read_bytes()+b' ')
            r=self.rv.oracle_reference_check(d,self.ids)
        self.assertTrue(all(not v['oracle_referenced'] for v in r.values()))
        self.assertTrue(all(any('scryfall sha256' in x for x in v['oracle_ref_errors']) for v in r.values()))
        e=copy.deepcopy(self.excerpt); e['sources']['scryfall']['sha256']='0'*64
        r=self.rv.oracle_reference_check(ROOT,self.ids,excerpt=e)
        self.assertTrue(all(not v['oracle_referenced'] for v in r.values()))

    def test_card_ids_from_sha256_equals_export_file(self):
        self.assertEqual(self.source['card_ids_from']['path'],EXPORT)
        self.assertEqual(self.source['card_ids_from']['sha256'],sha(ROOT/EXPORT))

if __name__=='__main__':
    unittest.main()
