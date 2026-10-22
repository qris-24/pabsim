"""Stage S20: Shigeki, Jukai Visionary (cast, tap ability with reveal-four, channel) and the
per-card model-coverage registry (byte-identical regeneration; every deck card present with
modeled and not-modeled lists; nothing certified; no values). """
import sys, json, unittest, importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA
from pab_zone_bridge import BridgeError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_shigeki_s20 import SHIGEKI, check_invariants_s20, LEGENDARY_CARDS

def trace(g,key): return [t for t in g.trace if t[0]==key]

class Shigeki(unittest.TestCase):
    def game(self):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve(); g.advance_to('precombat_main',active_player=0); return g
    def cast(self,g):
        u=next(x for x in g.zones.zones['library'] if g.zones.cards[x].name==SHIGEKI); g.zones.search_library(selected_uid=u,destination='hand'); g.add_mana('G','C'); g.cast_from_hand(u); g.resolve(); check_invariants_s20(g)
        return u,next(q for q in g.permanents.values() if q.name==SHIGEKI)
    def test_cast_body_and_refusals(self):
        self.assertIn('+S20',KERNEL_VERSION); self.assertIn('S20',PROMOTED)
        g=self.game(); u,p=self.cast(g); self.assertEqual((p.power,p.toughness,p.colors,p.creature,g.linked_battlefield[p.uid]),(1,3,'G',True,u)); self.assertTrue(p.enchantment)
        g2=self.game(); u=next(x for x in g2.zones.zones['library'] if g2.zones.cards[x].name==SHIGEKI); g2.zones.search_library(selected_uid=u,destination='hand'); g2.add_mana('C','C')
        with self.assertRaises(BridgeError): g2.cast_from_hand(u)                           # no green
        with self.assertRaises(BridgeError): g2.cast_from_hand(u,target_uid=1)
    def test_tap_ability_reveals_four_lands_tapped_rest_to_graveyard_and_summoning_sickness(self):
        g=self.game(); u,p=self.cast(g); g.add_mana('G','C')
        with self.assertRaises(BridgeError): g.shigeki_activate(p.uid)                       # entered this turn
        g.advance_to('cleanup',active_player=0); g.advance_to('precombat_main',active_player=0); g.add_mana('G','C'); top=list(g.zones.zones['library'][:4]); n=len(g.zones.zones['graveyard'])
        g.shigeki_activate(p.uid); self.assertEqual(g.zones.cards[u].zone,'hand'); self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.mana_pool,[])
        g.resolve(); check_invariants_s20(g); pick=trace(g,'shigeki_reveal')[-1][1]
        lands=[x for x in top if g.zones.cards[x].is_land]; self.assertEqual(pick,lands[0] if lands else None)
        if pick is not None: self.assertEqual(g.zones.cards[pick].zone,'battlefield'); self.assertTrue(g.zones.cards[pick].tapped)
        self.assertEqual(len(g.zones.zones['graveyard']),n+4-(1 if pick is not None else 0))
    def test_channel_returns_nonlegendary_cards_only(self):
        g=self.game(); u=next(x for x in g.zones.zones['library'] if g.zones.cards[x].name==SHIGEKI); g.zones.search_library(selected_uid=u,destination='hand')
        a=next(x for x in g.zones.zones['library'] if g.zones.cards[x].name=='Village Rites'); b=next(x for x in g.zones.zones['library'] if g.zones.cards[x].name=='Dina, Soul Steeper'); c=next(x for x in g.zones.zones['library'] if g.zones.cards[x].name=='Swamp')
        for x in (a,b,c): g.zones.move(x,'graveyard')
        g.add_mana('G','G','C','C','C','C')
        with self.assertRaises(BridgeError): g.channel_shigeki(u,[a,b])                       # Dina is legendary
        with self.assertRaises(BridgeError): g.channel_shigeki(u,[a,a])
        g.channel_shigeki(u,[a,c]); self.assertEqual(g.mana_pool,[]); self.assertEqual(g.zones.cards[u].zone,'graveyard'); g.resolve(); check_invariants_s20(g)
        self.assertEqual((g.zones.cards[a].zone,g.zones.cards[c].zone),('hand','hand')); self.assertIn('Dina, Soul Steeper',LEGENDARY_CARDS)

class Registry(unittest.TestCase):
    def test_registry_is_reproducible_and_complete(self):
        """CP42 (T4): reproducible bytes; 'complete' = same cards and quantities as PABTRV3_CARD_COVERAGE.json.
        The 'modeled' flags checked here are the file's own hand-written claims (A-S20-08), not checked against code."""
        spec=importlib.util.spec_from_file_location('mc20',ROOT/'build_model_coverage_s20.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        data=m.build(ROOT); self.assertEqual(m.canonical_bytes(data),(ROOT/'PABTRV3_MODEL_COVERAGE_S20.json').read_bytes())
        ref={c['name']:c for c in json.loads((ROOT/'PABTRV3_CARD_COVERAGE.json').read_text(encoding='utf-8'))['cards']}
        self.assertEqual(set(data['cards']),set(ref)); self.assertEqual(data['summary']['cards_total'],101); self.assertEqual(data['summary']['certified'],0)
        for n,e in data['cards'].items():
            self.assertTrue(e['modeled'],n); self.assertIsNone(e['value_for_optimization']); self.assertFalse(e['certified']); self.assertEqual(e['quantity'],ref[n]['quantity'])
        self.assertIn('Shigeki, Jukai Visionary',data['cards']); self.assertEqual(data['cards']['Shigeki, Jukai Visionary']['physical_path_stage'],'S20')

if __name__=='__main__': unittest.main()
