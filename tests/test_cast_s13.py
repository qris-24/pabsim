"""Stage S13: the eight remaining frozen-behaviour spells cast from the physical hand.
Each spell: positive with the card ending in the graveyard, refusals before mutation
(wrong zone, wrong step, insufficient mana, bad selection/target), effect through the
frozen procedure; Learn modes; hybrid payment; Immoral Bargain destroying real targets;
driver run. """
import sys, re, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST
from pab_zone_bridge import BridgeError
from pab_zones import ZoneError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_cast_s13 import SPELLS, S13_NAMES, CASTABLE, check_invariants_s11, run_turns_casting, cast_when_able, tutor_selection
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
def trace(g,key): return [t for t in g.trace if t[0]==key]
def pests(g): return sum(1 for p in g.permanents.values() if p.token==PEST)

class _B(unittest.TestCase):
    def bridge(self,*names,learn=False,board=False):
        g=PhysicalZoneGame(learn_sideboard_allowed=learn); g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve()
        if board: g.declare_opponent_board(1,[{'name':'Bear','power':2,'toughness':2},{'name':'Wall','power':0,'toughness':4}])
        check_invariants_s11(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s11(g); return uid
    def lib(self,g,name): return next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
    def pest(self,g):
        p=g.make_tokens(PEST)[0]; g.resolve(); check_invariants_s11(g); return p
    def cast(self,g,uid,**kw):
        g.cast_from_hand(uid,**kw); check_invariants_s11(g); self.assertIn(uid,g.stack_cards); g.resolve(); check_invariants_s11(g)
        self.assertNotIn(uid,g.stack_cards); self.assertEqual(g.zones.cards[uid].zone,'graveyard')
    def refused(self,g,uid,exc=BridgeError,**kw):
        hand=list(g.zones.zones['hand']); pool=list(g.mana_pool); perms=set(g.permanents); n=len(g.trace); lib=list(g.zones.zones['library'])
        with self.assertRaises(exc): g.cast_from_hand(uid,**kw)
        self.assertEqual((list(g.zones.zones['hand']),list(g.mana_pool),set(g.permanents),len(g.trace),list(g.zones.zones['library'])),(hand,pool,perms,n,lib)); self.assertEqual(g.stack_cards,{}); check_invariants_s11(g)

class Scope(_B):
    def test_kernel_promoted_and_evidence(self):
        self.assertIn('+S13',KERNEL_VERSION); self.assertIn('S13',PROMOTED); self.assertEqual(len(S13_NAMES),8)
        ev=json.loads((ROOT/'EVIDENCE'/'S13_SPELL_EVIDENCE.json').read_text(encoding='utf-8'))['cards']; self.assertEqual(set(ev),S13_NAMES)
        for n,c in ev.items():
            syms=re.findall(r'\{([^}]+)\}',c['mana_cost']); plain=[s for s in syms if s in ('B','G') or s.isdigit()]
            self.assertEqual((plain.count('B'),plain.count('G'),sum(int(s) for s in plain if s.isdigit())),SPELLS[n]['cost'],n)
            self.assertEqual(syms.count('B/G'),SPELLS[n].get('hybrid_pips',0),n); self.assertEqual(syms.count('X'),2 if n=='Pest Infestation' else 0,n)
            self.assertEqual(SPELLS[n]['kind'],'instant' if 'Instant' in c['type_line'] else 'sorcery',n)
    def test_common_refusals_every_spell(self):
        for name in sorted(S13_NAMES):
            with self.subTest(name=name):
                g=self.bridge(learn=True); uid=self.lib(g,name) if name!='Pest Summoning' else None
                if name=='Pest Summoning': g.zones.learn_pest_summoning(); uid=next(u for u in g.zones.zones['hand'] if g.zones.cards[u].name==name); g.zones.move(uid,'library')
                g.add_mana('B','B','G','G','C','C','C','C'); self.refused(g,uid,exc=ZoneError,**self.okkw(g,name))                     # wrong zone
                g=self.bridge(learn=True); uid=self.hand(g,name); kw=self.okkw(g,name); g.advance_to('cleanup',active_player=0); g.advance_step(); g.add_mana('B','B','G','G','C','C'); self.refused(g,uid,**kw)   # wrong step: seat 1's untap, nobody has priority
                g=self.bridge(learn=True); uid=self.hand(g,name); self.refused(g,uid,**self.okkw(g,name))                                                                               # no mana
                g=self.bridge(learn=True); uid=self.hand(g,name); g.add_mana('B','B','G','G','C','C'); self.refused(g,uid,devour_uids=[1],**self.okkw(g,name))                          # bad kwarg
    def hand(self,g,name):
        if name=='Pest Summoning': return g.zones.learn_pest_summoning().uid
        return self.to_hand(g,name)
    def okkw(self,g,name):
        if name in ('Demonic Tutor','Diabolic Intent'):
            kw={'selected_land_uid':self.lib(g,'Swamp')}
            if name=='Diabolic Intent': kw['sacrifice_uid']=self.pest(g).uid
            return kw
        if name=='Unearth':
            w=g.add('Deathgreeter'); g.destroy(w.uid); g.resolve(); return {'target_uid':w.uid}
        if name=='Immoral Bargain': return {'x':0,'sacrifice_uids':[],'target_uids':[]}
        if name=='Pest Infestation': return {'x':0}
        return {}

class Tutors(_B):
    def test_demonic_tutor_and_diabolic_intent_search_the_real_library(self):
        g=self.bridge('Sedgemoor Witch'); dt=self.to_hand(g,'Demonic Tutor'); sel=self.lib(g,'Grave Pact'); g.add_mana('B','C'); n=len(g.zones.zones['library'])
        self.cast(g,dt,selected_land_uid=sel); self.assertEqual(g.zones.cards[sel].zone,'hand'); self.assertEqual(len(g.zones.zones['library']),n-1); self.assertEqual(pests(g),1)   # Magecraft
        self.assertIn(('demonic_tutor_resolved',sel),g.zones.trace); self.assertIn(('library_shuffled',n-1),g.zones.trace)
        di=self.to_hand(g,'Diabolic Intent'); p=self.pest(g); sel=self.lib(g,'Blood Artist'); g.add_mana('B','C'); life=g.life[0]
        self.cast(g,di,sacrifice_uid=p.uid,selected_land_uid=sel); self.assertEqual(g.zones.cards[sel].zone,'hand'); self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.life[0],life-2+2+1)   # Savra black paid, green, Pest
        g=self.bridge(); dt=self.to_hand(g,'Demonic Tutor'); g.add_mana('B','C'); self.refused(g,dt); self.refused(g,dt,selected_land_uid=dt)
        di=self.to_hand(g,'Diabolic Intent'); self.refused(g,di,selected_land_uid=self.lib(g,'Swamp'))        # no sacrifice

class HuntAndLesson(_B):
    def test_learn_modes_lesson_discard_decline(self):
        g=self.bridge(learn=True); h=self.to_hand(g,'Hunt for Specimens'); g.add_mana('B','C'); self.cast(g,h,learn='lesson')
        ps=next(u for u in g.zones.zones['hand'] if g.zones.cards[u].name=='Pest Summoning'); self.assertEqual(g.zones.zones['outside_game'],[]); self.assertEqual(pests(g),1)
        g.add_mana('B','G','C'); self.cast(g,ps); self.assertEqual(pests(g),3); self.assertEqual(trace(g,'physical_cast')[-1][3],(1,1,1))
        g=self.bridge(); h=self.to_hand(g,'Hunt for Specimens'); other=self.to_hand(g,'Forest'); g.add_mana('B','C'); d=g.cards_drawn
        self.cast(g,h,learn='discard',discard_uid=other); self.assertEqual(g.zones.cards[other].zone,'graveyard'); self.assertEqual(g.cards_drawn,d+1)
        g=self.bridge(); h=self.to_hand(g,'Hunt for Specimens'); g.add_mana('B','C'); self.cast(g,h); self.assertEqual(trace(g,'learn_declined'),[('learn_declined',)])
        g=self.bridge(); h=self.to_hand(g,'Hunt for Specimens'); g.add_mana('B','C'); self.refused(g,h,learn='lesson'); self.refused(g,h,learn='discard'); self.refused(g,h,learn='x')
    def test_pest_summoning_hybrid_payment_and_refusals(self):
        g=self.bridge(learn=True); ps=g.zones.learn_pest_summoning().uid; g.add_mana('G','G','C'); self.cast(g,ps); self.assertEqual(trace(g,'physical_cast')[-1][3],(0,2,1)); self.assertEqual(pests(g),2)
        g=self.bridge(learn=True); ps=g.zones.learn_pest_summoning().uid; g.add_mana('B','G','C'); self.refused(g,ps,hybrid='BB'); self.refused(g,ps,hybrid='XY')
        g.add_mana('B'); self.cast(g,ps,hybrid='BB'); self.assertEqual(g.mana_pool,['G'])
        g=self.bridge(learn=True); ps=g.zones.learn_pest_summoning().uid; g.add_mana('C','C','C'); self.refused(g,ps)

class FrozenWrappers(_B):
    def test_unearth_returns_a_linked_card_and_refuses_bad_targets(self):
        g=self.bridge(); ba=self.to_hand(g,'Blood Artist'); g.add_mana('B','C'); g.cast_from_hand(ba); g.resolve()
        bp=next(p for p in g.permanents.values() if p.name=='Blood Artist'); g.destroy(bp.uid); g.resolve(); self.assertEqual(g.zones.cards[ba].zone,'graveyard')
        un=self.to_hand(g,'Unearth'); g.add_mana('B'); self.refused(g,un); self.refused(g,un,target_uid=999)
        self.cast(g,un,target_uid=bp.uid); self.assertEqual(g.zones.cards[ba].zone,'battlefield'); self.assertTrue(any(p.name=='Blood Artist' and p.uid in g.linked_battlefield for p in g.permanents.values()))
        g=self.bridge(); big=g.add('Beledros Witherbloom',mana_value=7); g.destroy(big.uid); g.resolve(); un=self.to_hand(g,'Unearth'); g.add_mana('B'); self.refused(g,un,target_uid=big.uid)   # MV > 3
    def test_plumb_copies_per_sacrifice_card_to_graveyard(self):
        g=self.bridge('Sedgemoor Witch'); pl=self.to_hand(g,'Plumb the Forbidden'); a=self.pest(g); b=self.pest(g); g.add_mana('B','C'); d=g.cards_drawn; life=g.life[0]
        self.cast(g,pl,sacrifice_uids=[a.uid,b.uid]); self.assertEqual(g.cards_drawn,d+3); self.assertEqual(len(trace(g,'copy')),2)
        self.assertEqual(pests(g),3)                                                   # Magecraft: 1 cast + 2 copies
        g=self.bridge(); pl=self.to_hand(g,'Plumb the Forbidden'); g.add_mana('B','C'); self.refused(g,pl,sacrifice_uids=[999])
        g.advance_to('upkeep',active_player=2); g.add_mana('B','C'); self.cast(g,pl)                 # instant on an opponent's upkeep, no sacrifice
    def test_immoral_bargain_destroys_real_targets_and_fizzles_when_gone(self):
        g=self.bridge('Blood Artist',board=True); ib=self.to_hand(g,'Immoral Bargain'); p=self.pest(g); bear=next(q.uid for q in g.opponent_creatures(1) if q.name=='Bear'); g.add_mana('B','G','C'); opp=g.life[1]
        self.cast(g,ib,x=1,sacrifice_uids=[p.uid],target_uids=[bear]); self.assertNotIn(bear,g.permanents); self.assertNotIn(p.uid,g.permanents)
        self.assertEqual([t[3] for t in trace(g,'opponent_creature_dies')],['Wall','Bear'])                      # Savra black edict took the Wall as the cost resolved, then the Bear died to the spell
        self.assertEqual(g.life[1],opp-3)                                                                         # Blood Artist: Pest, Wall, Bear
        g=self.bridge(board=True); ib=self.to_hand(g,'Immoral Bargain'); p=self.pest(g); bear=next(q.uid for q in g.opponent_creatures(1) if q.name=='Bear'); g.add_mana('B','G','C')
        self.refused(g,ib,x=1,sacrifice_uids=[p.uid],target_uids=[bear,bear]); self.refused(g,ib,x=2,sacrifice_uids=[p.uid],target_uids=[bear]); self.refused(g,ib,x=1,sacrifice_uids=[p.uid],target_uids=[999])
        g.cast_from_hand(ib,x=1,sacrifice_uids=[p.uid],target_uids=[bear]); g._opponent_creature_dies(bear,cause='test') if bear in g.permanents else None
        g.resolve(); check_invariants_s11(g); self.assertIn(('spell_fizzles_all_targets_illegal','Immoral Bargain'),g.trace)
    def test_pest_infestation_x_targets_and_refusals(self):
        g=self.bridge('Grave Pact'); pi=self.to_hand(g,'Pest Infestation'); gp=next(p.uid for p in g.permanents.values() if p.name=='Grave Pact'); g.add_mana('G','C','C','C','C')
        self.refused(g,pi,x=3); self.refused(g,pi,x=1,target_uids=[gp,gp]); self.refused(g,pi,x=0,target_uids=[gp]); self.refused(g,pi,x=1,target_uids=[999])
        self.cast(g,pi,x=2,target_uids=[gp]); self.assertEqual(pests(g),4); self.assertNotIn(gp,g.permanents); self.assertEqual(g.mana_pool,[]); self.assertEqual(trace(g,'physical_cast')[-1][3],(0,1,4))

class Driver(_B):
    def test_driver_policies_and_eight_seeds(self):
        g=self.bridge(learn=True); g.advance_to('precombat_main',active_player=0); dt=self.to_hand(g,'Demonic Tutor'); g.add_mana('B','C')
        self.assertEqual(g.zones.cards[tutor_selection(g)].name in ('Swamp','Forest'),True); self.assertEqual(cast_when_able(g),['Demonic Tutor'])
        h=self.to_hand(g,'Hunt for Specimens'); g.add_mana('B','C'); self.assertEqual(cast_when_able(g),['Hunt for Specimens']); self.assertTrue(any(g.zones.cards[u].name=='Pest Summoning' for u in g.zones.zones['hand']))
        for u in list(g.zones.zones['hand']):
            if g.zones.cards[u].name!='Pest Summoning': g.zones.move(u,'library')
        g.add_mana('B','B','C'); self.assertEqual(cast_when_able(g),['Pest Summoning'])
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=PhysicalZoneGame(seed=seed,learn_sideboard_allowed=True); opening_hand(g); ledger=run_turns_casting(g,24)
                self.assertEqual([t for t,*_ in ledger],[1,5,9,13,17,21]); self.assertEqual(g.stack_cards,{})
                for _,name,uid,cost,_ in trace(g,'physical_cast'):
                    self.assertIn(name,CASTABLE)
                    if CASTABLE[name]['kind'] in ('instant','sorcery'): self.assertEqual(g.zones.cards[uid].zone,'graveyard')
                    else: self.assertIn(g.zones.cards[uid].zone,('battlefield','graveyard','exile'))   # permanents may have died since

if __name__=='__main__': unittest.main()
