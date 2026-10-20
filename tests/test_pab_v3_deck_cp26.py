"""CP26: PAB v3 deck file and Oracle supplement (second deck target, not gated for kernel behaviour).
Asserts the deck counts, that every v3 name resolves to the card data or the supplement, and that the
supplement's recorded source hashes match the files. Models nothing; every v3 card not on the old
baseline stays UNMODELED in the registry. """
import hashlib, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DECKS=ROOT/'decks'
CARD_DATA=Path(r'C:\pabsim\data\golgari_commander.json')
EXPORT_SHA='b3db879a4f27b5fa97fb87afcd17a16d9fba552673e957fa26cb8f356f94b104'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))

class PabV3Deck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deck=load(DECKS/'PAB_V3.json'); cls.supp=load(DECKS/'PAB_V3_ORACLE_SUPPLEMENT.json')
        cls.names=[cls.deck['commander']['name']]+[e['name'] for e in cls.deck['mainboard']]

    def test_counts_100_cards_34_lands_87_names_savra_commander(self):
        d=self.deck; main=d['mainboard']
        self.assertEqual(d['commander']['name'],'Savra, Queen of the Golgari'); self.assertEqual(d['commander']['qty'],1)
        self.assertEqual(1+sum(e['qty'] for e in main),100)
        self.assertEqual(sum(e['qty'] for e in main if e['is_land']),34)
        self.assertEqual(len(set(self.names)),87); self.assertEqual(len(self.names),87)
        self.assertFalse(d['gated'])

    def test_every_v3_name_resolves_to_card_data_or_supplement(self):
        data={n for c in load(CARD_DATA) for n in [c['name']]+[f['name'] for f in c.get('card_faces',[])]}
        supp={r['name'] for r in self.supp['records']}
        unresolved=[n for n in self.names if n not in data and n not in supp]
        self.assertEqual(unresolved,[])
        self.assertEqual(sorted(n for n in self.names if n not in data),sorted(supp))   # supplement covers exactly the gaps
        self.assertEqual(len(supp),8)

    def test_supplement_source_sha256s_match_files(self):
        self.assertEqual(sha(DECKS/'PAB_V3_ARCHIDEKT_EXPORT.csv'),EXPORT_SHA)
        self.assertEqual(self.deck['source']['sha256'],EXPORT_SHA)
        for r in self.supp['records']:
            self.assertEqual(r['source_sha256'],sha(ROOT/r['source_file']),r['name'])
            self.assertIn(r['source_tier'],('user-provided Scryfall export','user-provided Archidekt export'))

    def test_supplement_records_have_text_and_no_certification(self):
        self.assertFalse(self.supp['certified'])
        for r in self.supp['records']:
            self.assertTrue(r['oracle_text'],r['name']); self.assertIn('mana_cost',r); self.assertTrue(r['scryfall_id'],r['name'])

    def test_registry_marks_19_added_cards_unmodeled(self):
        t=load(ROOT/'PABTRV3_CARD_COVERAGE.json')['summary']['pab_v3_deck_target']
        self.assertEqual(len(t['added_vs_old_baseline']),19)
        self.assertEqual(set(t['added_vs_old_baseline'].values()),{'UNMODELED'})
        self.assertEqual(t['deck_file_sha256'],sha(DECKS/'PAB_V3.json'))
        self.assertEqual(t['oracle_supplement_sha256'],sha(DECKS/'PAB_V3_ORACLE_SUPPLEMENT.json'))
        self.assertEqual(t['certified'],0); self.assertFalse(t['gated'])

if __name__=='__main__':
    unittest.main()
