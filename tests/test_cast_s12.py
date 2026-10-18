"""Stage S12: the 15 noncreature permanents from the physical hand. Per card (subTests):
positive cast linked with the right type flags; refusals for wrong zone, wrong step and
insufficient mana; evidence cross-check; frozen ETB behaviour through the cast path
(Bastion token, Saga chapter I); no Magecraft; the frozen death-trigger board assembled
by casting; driver run. """
import sys, re, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST, HUMAN, ARTIFACT
from pab_zone_bridge import BridgeError
from pab_zones import ZoneError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_cast_s12 import PERMANENTS, S12_NAMES, CASTABLE, check_invariants_s11, run_turns_casting, cast_when_able
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
def trace(g,key): return [t for t in g.trace if t[0]==key]
def mana_for(spec):
    b,gr,gen=spec['cost']; return ['B']*b+['G']*gr+['C']*gen

class _B(unittest.TestCase):
    def bridge(self,*names):
        g=PhysicalZoneGame(); g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve(); check_invariants_s11(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s11(g); return uid
    def cast(self,g,uid):
        g.cast_from_hand(uid); check_invariants_s11(g); self.assertIn(uid,g.stack_cards); g.resolve(); check_invariants_s11(g); self.assertNotIn(uid,g.stack_cards)
    def refused(self,g,uid,exc=BridgeError,**kw):
        hand=list(g.zones.zones['hand']); pool=list(g.mana_pool); perms=set(g.permanents); n=len(g.trace)
        with self.assertRaises(exc): g.cast_from_hand(uid,**kw)
        self.assertEqual((list(g.zones.zones['hand']),list(g.mana_pool),set(g.permanents),len(g.trace)),(hand,pool,perms,n)); self.assertEqual(g.stack_cards,{}); check_invariants_s11(g)

class Cast(_B):
    def test_kernel_promoted_and_table_matches_evidence(self):
        self.assertIn('+S12',KERNEL_VERSION); self.assertIn('S12',PROMOTED); self.assertEqual(len(S12_NAMES),15); self.assertEqual(set(CASTABLE),set(CASTABLE)|S12_NAMES)
        ev=json.loads((ROOT/'EVIDENCE'/'S12_PERMANENT_EVIDENCE.json').read_text(encoding='utf-8'))['cards']; self.assertEqual(set(ev),S12_NAMES)
        for n,c in ev.items():
            syms=re.findall(r'\{([^}]+)\}',c['mana_cost']); self.assertTrue(all(s in ('B','G') or s.isdigit() for s in syms),n)
            self.assertEqual((syms.count('B'),syms.count('G'),sum(int(s) for s in syms if s.isdigit())),PERMANENTS[n]['cost'],n); self.assertEqual(int(c['cmc']),PERMANENTS[n]['mana_value'],n)
            self.assertFalse('Creature' in c['type_line'] or 'Land' in c['type_line'],n); self.assertEqual(('Artifact' in c['type_line']),PERMANENTS[n]['artifact'],n)
    def test_positive_every_permanent_linked_with_type_flags(self):
        for name in sorted(S12_NAMES):
            with self.subTest(name=name):
                g=self.bridge(); uid=self.to_hand(g,name); spec=PERMANENTS[name]; hand=len(g.zones.zones['hand']); g.add_mana(*mana_for(spec)); self.cast(g,uid)
                self.assertEqual(g.mana_pool,[]); self.assertEqual(g.zones.cards[uid].zone,'battlefield'); self.assertEqual(len(g.zones.zones['hand']),hand-1)
                ev=next(e for e,ph in g.linked_battlefield.items() if ph==uid); p=g.permanents[ev]
                self.assertEqual((p.name,p.creature,p.artifact,p.mana_value,p.controller),(name,False,name in ARTIFACT,spec['mana_value'],0))
                self.assertEqual(trace(g,'physical_cast')[-1],('physical_cast',name,uid,spec['cost'],None)); self.assertEqual(trace(g,'physical_permanent_spell_resolved')[-1][3],ev)
                self.assertEqual(sum(1 for p in g.permanents.values() if p.token==PEST),0)      # no Magecraft (Sedgemoor absent anyway); checked below with the Witch
    def test_refusals_every_permanent_wrong_zone_wrong_step_insufficient_mana_bad_kwargs(self):
        for name in sorted(S12_NAMES):
            with self.subTest(name=name):
                spec=PERMANENTS[name]; full=mana_for(spec)
                g=self.bridge(); uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.add_mana(*full); self.refused(g,uid,exc=ZoneError)
                g=self.bridge(); uid=self.to_hand(g,name); g.advance_to('upkeep',active_player=0); g.add_mana(*full); self.refused(g,uid)
                g=self.bridge(); uid=self.to_hand(g,name); g.advance_to('precombat_main',active_player=1); g.add_mana(*full); self.refused(g,uid)
                g=self.bridge(); uid=self.to_hand(g,name); g.add_mana(*full[:-1]); self.refused(g,uid)
                g=self.bridge(); uid=self.to_hand(g,name); g.add_mana(*full); p=g.make_tokens(PEST)[0]; g.resolve(); self.refused(g,uid,sacrifice_uid=p.uid); self.refused(g,uid,devour_uids=[p.uid])
    def test_frozen_etb_through_the_cast_path_and_no_magecraft(self):
        g=self.bridge('Sedgemoor Witch'); uid=self.to_hand(g,'Bastion of Remembrance'); g.add_mana('B','C','C'); self.cast(g,uid)
        self.assertEqual(sum(1 for p in g.permanents.values() if p.token==HUMAN),1); self.assertEqual(sum(1 for p in g.permanents.values() if p.token==PEST),0)
        uid=self.to_hand(g,'The Hunger Tide Rises'); g.add_mana('G','C','C'); self.cast(g,uid); self.assertIn(('saga_chapter',1),g.trace)
    def test_death_trigger_board_assembled_by_casting_behaves_like_the_fixture_board(self):
        names=('Bastion of Remembrance','Cauldron of Essence','Moldervine Reclamation','Dark Prophecy','Agent of the Iron Throne','Grave Pact','Blight Mound')
        g=self.bridge()
        for n in names: uid=self.to_hand(g,n); g.add_mana(*mana_for(PERMANENTS[n])); self.cast(g,uid)
        f=self.bridge(*names)
        for x in (g,f):
            x.cards_drawn=0; p=x.make_tokens(PEST)[0]; x.resolve(); x.life=[40,40,40,40]; x.sacrifice(p.uid); x.resolve()
        self.assertEqual(g.life,f.life); self.assertEqual(g.cards_drawn,f.cards_drawn); self.assertEqual(g.edict_opportunities,f.edict_opportunities)
        self.assertEqual(g.life[0],40+1-2+2+1+1+1-1); self.assertEqual(g.life[1],40-1-1-1)         # Bastion, Cauldron, Agent drains
    def test_driver_eight_seeds_twenty_turns(self):
        total=0
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=PhysicalZoneGame(seed=seed); opening_hand(g); ledger=run_turns_casting(g,20)
                casts=trace(g,'physical_cast'); self.assertEqual(len(casts),sum(len(c) for *_,c in ledger)-sum(c.count(SAVRA) for *_,c in ledger)); total+=len(casts)
                for _,name,uid,cost,_ in casts:
                    self.assertEqual(cost,CASTABLE[name]['cost']); self.assertEqual(g.zones.cards[uid].zone,'graveyard' if CASTABLE[name]['kind'] in ('instant','sorcery') else 'battlefield')
        self.assertGreater(total,0)
        g=PhysicalZoneGame(seed=2); g.advance_to('precombat_main',active_player=0); uid=self.to_hand(g,'Sol Ring'); g.add_mana('C'); self.assertIn('Sol Ring',cast_when_able(g)); self.assertEqual(g.zones.cards[uid].zone,'battlefield')   # no opening hand: Sol Ring is in the library

if __name__=='__main__': unittest.main()
