"""Stage S16: Grist, the Hunger Tide. Cast as a planeswalker (loyalty 3, linked card);
the three loyalty abilities with costs, timing and once-per-turn; zero loyalty SBA;
leaving to the graveyard as a creature card (Unearth brings her back as a planeswalker;
Grisly Salvage counts her); removal by Abrupt Decay; a milled Grist gets an LKI. """
import sys, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST, INSECT
from pab_zone_bridge import BridgeError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_grist_s16 import GRIST, GRIST_SPEC, CASTABLE, check_invariants_s16
from pab_opponents_s8 import OPPONENT_SEATS

BOARD=[{'name':'Bear','power':2,'toughness':2,'mana_value':2},{'name':'Dragon','power':5,'toughness':5,'mana_value':6}]
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names,board=True):
        g=PhysicalZoneGame(); g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve()
        if board:
            for s in OPPONENT_SEATS: g.declare_opponent_board(s,BOARD)
        check_invariants_s16(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s16(g); return uid
    def grist(self,g):
        g.advance_to('precombat_main',active_player=0); uid=self.to_hand(g,GRIST); g.add_mana('B','G','C'); g.cast_from_hand(uid); check_invariants_s16(g); g.resolve(); check_invariants_s16(g)
        p=g.grist(); self.assertEqual((p.loyalty,p.creature,g.linked_battlefield[p.uid]),(3,False,uid)); return p,uid
    def main(self,g): g.advance_to('precombat_main',active_player=0)

class Cast(_B):
    def test_kernel_promoted_evidence_and_cast(self):
        self.assertIn('+S16',KERNEL_VERSION); self.assertIn('S16',PROMOTED); self.assertIn(GRIST,CASTABLE)
        ev=json.loads((ROOT/'EVIDENCE'/'S16_PLANESWALKER_EVIDENCE.json').read_text(encoding='utf-8'))['card']; self.assertEqual((ev['mana_cost'],ev['loyalty']),('{1}{B}{G}','3')); self.assertEqual(GRIST_SPEC['cost'],(1,1,1))
        g=self.game(); p,uid=self.grist(g); self.assertEqual(trace(g,'grist_enters'),[('grist_enters',p.uid,3)]); self.assertFalse(p.artifact); self.assertEqual(p.mana_value,3)
        g2=self.game(); uid=self.to_hand(g2,GRIST); g2.add_mana('B','G')
        with self.assertRaises(BridgeError): g2.cast_from_hand(uid)                                     # one short
        g2.add_mana('C'); g2.advance_to('upkeep',active_player=0); g2.add_mana('B','G','C')
        with self.assertRaises(BridgeError): g2.cast_from_hand(uid)                                     # sorcery speed
        with self.assertRaises(BridgeError): g2.cast_from_hand(uid,target_uid=1)
    def test_plus_one_insect_and_mill_once_per_turn_sorcery_speed(self):
        g=self.game(); p,uid=self.grist(g); n=len(g.zones.zones['library'])
        g.grist_plus_one(); self.assertEqual(p.loyalty,4); self.assertEqual(trace(g,'loyalty_ability'),[('loyalty_ability','+1',1,4)]); g.resolve(); check_invariants_s16(g)
        self.assertEqual(sum(1 for q in g.permanents.values() if q.token==INSECT),1); self.assertEqual(len(g.zones.zones['library']),n-1); self.assertEqual(trace(g,'grist_repeat'),[])
        with self.assertRaises(BridgeError): g.grist_plus_one()                                        # once per turn
        g.advance_to('upkeep',active_player=0)
        with self.assertRaises(BridgeError): g.grist_plus_one()                                        # not a main phase
        g.advance_to('precombat_main',active_player=2)
        with self.assertRaises(BridgeError): g.grist_plus_one()                                        # not your turn
        self.main(g); g.grist_plus_one(); g.resolve(); self.assertEqual(p.loyalty,5)
    def test_minus_two_sacrifice_then_reflexive_destroy_and_fizzle(self):
        g=self.game('Blood Artist'); p,uid=self.grist(g); pe=g.make_tokens(PEST)[0]; g.resolve(); dragon=next(q.uid for q in g.opponent_creatures(2) if q.name=='Dragon')
        with self.assertRaises(BridgeError): g.grist_minus_two(None,dragon)
        with self.assertRaises(BridgeError): g.grist_minus_two(pe.uid,999)
        g.grist_minus_two(pe.uid,dragon); self.assertEqual(p.loyalty,1); self.assertIn(pe.uid,g.permanents)      # cost paid, nothing else yet
        g.resolve(); check_invariants_s16(g); self.assertNotIn(pe.uid,g.permanents); self.assertNotIn(dragon,g.permanents)
        self.assertEqual([t[2] for t in trace(g,'destroyed_by') if t[3]=='Grist -2'],['Dragon']); self.assertEqual([t[3] for t in trace(g,'opponent_creature_dies') if t[4]=='Savra black'],['Bear','Bear','Bear'])   # the reflexive destroy resolved first (newest trigger), then the Pest's Savra edict
        g2=self.game(); q,_=self.grist(g2); pe2=g2.make_tokens(PEST)[0]; g2.resolve(); bear=next(x.uid for x in g2.opponent_creatures(1) if x.name=='Bear')
        g2.grist_minus_two(pe2.uid,bear); g2._opponent_creature_dies(bear,cause='test'); g2.resolve(); self.assertNotIn(pe2.uid,g2.permanents); self.assertIn(('grist_minus_two_no_legal_target',bear),g2.trace); self.assertNotIn(('spell_fizzles_all_targets_illegal','Grist -2'),g2.trace); self.assertEqual([x for x in trace(g2,'destroyed_by') if x[3]=='Grist -2'],[])   # target gone before the reflexive trigger exists: no trigger (CR 603.3d), not a fizzle
        self.main(g)
        with self.assertRaises(BridgeError): g.grist_minus_two()                                       # loyalty 1 - 2 < 0
        g.grist_plus_one(); g.resolve(); self.main(g); g.grist_minus_two(); g.resolve(); self.assertEqual(trace(g,'grist_no_sacrifice'),[('grist_no_sacrifice',)]); self.assertIsNone(g.grist())   # declined the sacrifice; 0 loyalty -> gone
    def test_minus_two_needs_loyalty_and_zero_loyalty_sba(self):
        g=self.game(); p,uid=self.grist(g); pe=g.make_tokens(PEST)[0]; g.resolve(); dragon=next(q.uid for q in g.opponent_creatures(1) if q.name=='Dragon')
        g.grist_minus_two(pe.uid,dragon); g.resolve(); self.assertEqual(p.loyalty,1)
        self.main(g)
        with self.assertRaises(BridgeError): g.grist_minus_two()                                       # 1 - 2 < 0
        g.grist_plus_one(); g.resolve(); self.main(g); g.grist_minus_two(); g.resolve(); check_invariants_s16(g)   # 2 - 2 = 0 -> SBA
        self.assertIsNone(g.grist()); self.assertEqual(g.zones.cards[uid].zone,'graveyard'); self.assertEqual(trace(g,'sba_zero_loyalty'),[('sba_zero_loyalty',p.uid)])
        self.assertTrue(any(q.name==GRIST and q.creature for q in g.graveyard))                          # creature card in the graveyard
    def test_minus_five_drains_by_creature_cards_in_graveyard(self):
        g=self.game(); p,uid=self.grist(g); g.grist_plus_one(); g.resolve(); self.main(g); g.grist_plus_one(); g.resolve(); self.assertEqual(p.loyalty,5)
        for n in ('Sedgemoor Witch','Blood Artist'): g.zones.move(self.to_hand(g,n),'graveyard')
        from pab_grist_s16 import CREATURE_CARD_NAMES
        creatures=sum(1 for u in g.zones.zones['graveyard'] if g.zones.cards[u].name in CREATURE_CARD_NAMES); self.assertGreaterEqual(creatures,2)
        self.main(g); g.grist_minus_five(); self.assertEqual(p.loyalty,0); opp=list(g.life[1:]); g.resolve(); check_invariants_s16(g)
        self.assertEqual(g.life[1:],[x-creatures-1 for x in opp]); self.assertIsNone(g.grist())          # 0 loyalty after the cost: the SBA puts Grist in the graveyard before the ability resolves, and she counts herself there
        self.assertEqual(trace(g,'grist_minus_five'),[('grist_minus_five',creatures+1)])

class Zones(_B):
    def test_abrupt_decay_kills_her_unearth_returns_a_planeswalker(self):
        g=self.game(); p,uid=self.grist(g); d=self.to_hand(g,'Abrupt Decay'); g.add_mana('B','G'); g.cast_from_hand(d,target_uid=p.uid); g.resolve(); check_invariants_s16(g)
        self.assertIsNone(g.grist()); self.assertEqual(g.zones.cards[uid].zone,'graveyard'); self.assertIsNotNone(g._grave_target(p.uid))
        un=self.to_hand(g,'Unearth'); g.add_mana('B'); g.cast_from_hand(un,target_uid=p.uid); g.resolve(); check_invariants_s16(g)
        q=g.grist(); self.assertIsNotNone(q); self.assertEqual((q.loyalty,q.creature,g.zones.cards[uid].zone,g.linked_battlefield[q.uid]),(3,False,'battlefield',uid)); self.assertNotEqual(q.uid,p.uid)
    def test_milled_grist_gets_an_lki_and_grisly_salvage_counts_her(self):
        g=self.game(); uid=self.to_hand(g,GRIST); g.zones.move(uid,'graveyard'); self.assertIsNone(g.grist()); lki=g.grist_graveyard_lki()
        self.assertTrue(lki.creature); self.assertEqual(lki.mana_value,3); self.assertIs(g.grist_graveyard_lki(),lki)
        g.advance_to('precombat_main',active_player=0); un=self.to_hand(g,'Unearth'); g.add_mana('B'); g.cast_from_hand(un,target_uid=lki.uid); g.resolve(); check_invariants_s16(g); self.assertIsNotNone(g.grist())
        g2=self.game(); gs=self.to_hand(g2,'Grisly Salvage'); gu=self.to_hand(g2,GRIST); g2.zones.move(gu,'library',top=True)
        g2.add_mana('B','G'); g2.cast_from_hand(gs,choice_uid=gu); g2.resolve(); self.assertEqual(g2.zones.cards[gu].zone,'hand')
    def test_scripted_removal_and_edicts_ignore_a_planeswalker(self):
        g=PhysicalZoneGame(); g.resolve(); g.script_opponent_actions(1,[{'turn':2,'kind':'destroy_creature'},{'turn':2,'kind':'edict'},{'turn':2,'kind':'board_wipe'}])
        g.advance_to('precombat_main',active_player=0); uid=self.to_hand(g,GRIST); g.add_mana('B','G','C'); g.cast_from_hand(uid); g.resolve(); p=g.grist()
        g.advance_to('precombat_main',active_player=1); g.resolve(); check_invariants_s16(g); self.assertIn(p.uid,g.permanents); self.assertEqual(p.loyalty,3)

if __name__=='__main__': unittest.main()
