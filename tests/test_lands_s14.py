"""Stage S14: the nine remaining nonbasic lands. All playable and tappable (Verdant has no
mana ability); the sacrifice lands' costs and effects through the frozen sacrifice();
Castle Locthwain's entry and draw-then-lose; Verdant Catacombs' fetch with the fetched
land's own entry rule; Takenuma channel with the legendary discount; Geier Reach /
Mikokoro draws; Boseiju channel refused (no target); refusals; all 34 lands in the driver.
"""
import sys, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST
from pab_zone_bridge import BridgeError
from pab_zones import LAND_NAMES
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_lands_s14 import LANDS14, S14_NAMES, LAND_MANA, LAND_MANA_DRIVER, run_turns_casting
from pab_cast_s13 import check_invariants_s11
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names):
        g=PhysicalZoneGame(); g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve(); check_invariants_s11(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s11(g); return uid
    def play(self,g,name,**kw):
        g.zones.land_plays_this_turn=0; uid=self.to_hand(g,name); p=g.play_physical_land(uid,**kw); g.resolve(); check_invariants_s11(g)
        self.assertEqual(g.linked_battlefield[p.uid],uid); return p
    def pest(self,g):
        p=g.make_tokens(PEST)[0]; g.resolve(); check_invariants_s11(g); return p
    def untap(self,g): g._untap_step(0)
    def refused(self,g,fn,*a,**kw):
        pool=list(g.mana_pool); perms=set(g.permanents); life=g.life[0]; n=len(g.trace); hand=list(g.zones.zones['hand'])
        with self.assertRaises(BridgeError): fn(*a,**kw)
        self.assertEqual((list(g.mana_pool),set(g.permanents),g.life[0],len(g.trace),list(g.zones.zones['hand'])),(pool,perms,life,n,hand)); check_invariants_s11(g)

class Scope(_B):
    def test_kernel_promoted_evidence_and_all_34_lands_playable(self):
        self.assertIn('+S14',KERNEL_VERSION); self.assertIn('S14',PROMOTED)
        ev=json.loads((ROOT/'EVIDENCE'/'S14_LAND_EVIDENCE.json').read_text(encoding='utf-8'))['cards']; self.assertEqual(set(ev),S14_NAMES)
        self.assertEqual(set(LAND_MANA_DRIVER),LAND_NAMES); self.assertEqual(LAND_NAMES-set(LAND_MANA),{'Verdant Catacombs'})
        for n in sorted(S14_NAMES):
            with self.subTest(land=n):
                g=self.game(); p=self.play(g,n); self.assertEqual(p.tapped,n=='Castle Locthwain')
                if LANDS14[n]['mana']: self.untap(g); self.assertEqual(g.tap_physical_land_for_mana(p.uid),LANDS14[n]['mana'][0])
                else: self.refused(g,g.tap_physical_land_for_mana,p.uid)
    def test_still_frozen_zones_path_refuses_and_face_kwargs_refused(self):
        from pab_zones import UnsupportedZoneMechanic
        g=self.game(); uid=self.to_hand(g,'Phyrexian Tower')
        with self.assertRaises(UnsupportedZoneMechanic): g.zones.play_land(uid)
        with self.assertRaises(BridgeError): g.play_physical_land(uid,face='Darkbore')
        with self.assertRaises(BridgeError): g.play_physical_land(uid,pay_life=True)

class SacrificeLands(_B):
    def test_phyrexian_tower_mana_ability_sacrifice_adds_BB_savra_and_pest_triggers(self):
        g=self.game('Blood Artist'); t=self.play(g,'Phyrexian Tower'); p=self.pest(g); life=g.life[0]
        g.tower_sacrifice(t.uid,p.uid); self.assertEqual(g.mana_pool,['B','B']); self.assertTrue(t.tapped); self.assertNotIn(p.uid,g.permanents)
        labels=[x.label for x in g.pending]; self.assertIn('Savra black sacrifice',labels); self.assertIn('Pest dies-gain',labels); self.assertEqual(trace(g,'mana_ability'),[('mana_ability','Phyrexian Tower',p.uid,('B','B'))])
        g.resolve(); self.assertEqual(g.life[0],life-2+2+1+1)       # Savra black/green, Pest, Blood Artist
        self.refused(g,g.tower_sacrifice,t.uid,999)                   # tapped and no creature
    def test_high_market_and_grim_backwoods_cost_before_resolution(self):
        g=self.game(); hm=self.play(g,'High Market'); p=self.pest(g); life=g.life[0]
        g.high_market(hm.uid,p.uid); self.assertNotIn(p.uid,g.permanents); self.assertTrue(hm.tapped); self.assertEqual(g.pending[-1].label,'High Market resolution (S14)')
        g.resolve(); self.assertEqual(g.life[0],life-2+2+1+1)        # + High Market
        gb=self.play(g,'Grim Backwoods'); q=self.pest(g); self.refused(g,g.grim_backwoods,gb.uid,q.uid)            # no mana
        g.add_mana('B','G','C','C'); d=g.cards_drawn; g.grim_backwoods(gb.uid,q.uid); self.assertEqual(g.mana_pool,[]); self.assertNotIn(q.uid,g.permanents); g.resolve(); self.assertEqual(g.cards_drawn,d+1)
        self.untap(g); self.refused(g,g.high_market,hm.uid,hm.uid)   # a land is not a creature
    def test_savra_herself_can_be_the_cost(self):
        g=PhysicalZoneGame(); g.resolve(); g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve(); sv=next(p for p in g.permanents.values() if p.name==SAVRA)
        hm=self.play(g,'High Market'); g.high_market(hm.uid,sv.uid); g.resolve(); check_invariants_s11(g)
        self.assertEqual(g.zones.cards[g.zones.zones['command'][0]].name,SAVRA); self.assertEqual(g.commander_deaths,1)

class CastleAndVerdant(_B):
    def test_castle_enters_untapped_with_a_swamp_type_and_draws_before_losing(self):
        g=self.game(); self.play(g,'Overgrown Tomb',pay_life=True); cl=self.play(g,'Castle Locthwain'); self.assertFalse(cl.tapped)
        for u in list(g.zones.zones['hand']): g.zones.move(u,'library')
        self.to_hand(g,'Swamp'); self.to_hand(g,'Forest'); g.add_mana('B','B','C'); life=g.life[0]
        g.castle_locthwain(cl.uid); g.resolve(); self.assertEqual(len(g.zones.zones['hand']),3); self.assertEqual(g.life[0],life-3)   # 2 + drawn = 3, not 2
        self.assertEqual(trace(g,'castle_locthwain_hand'),[('castle_locthwain_hand',2,3)]); self.assertEqual(trace(g,'lose_life')[-1],('lose_life',3,'Castle Locthwain'))
        self.untap(g); g.add_mana('B','C','C'); self.refused(g,g.castle_locthwain,cl.uid)                         # {1}{B}{B}: one black short
    def test_castle_zero_hand_control_and_empty_library(self):
        g=self.game(); cl=self.play(g,'Castle Locthwain'); self.untap(g)
        for u in list(g.zones.zones['hand']): g.zones.move(u,'library')
        g.add_mana('B','B','C'); life=g.life[0]; g.castle_locthwain(cl.uid); g.resolve(); self.assertEqual(g.life[0],life-1)   # 0 + drawn = 1
        g2=self.game(); cl=self.play(g2,'Castle Locthwain'); self.untap(g2)
        for u in list(g2.zones.zones['library']): g2.zones.move(u,'exile')
        for u in list(g2.zones.zones['hand']): g2.zones.move(u,'exile')
        g2.add_mana('B','B','C'); g2.castle_locthwain(cl.uid); g2.resolve(); self.assertEqual(g2.zones.failed_draws,1)       # empty-library draw recorded, not ignored
    def test_verdant_fetches_by_land_type_with_the_fetched_entry_rule(self):
        for name,kw,tapped,life_delta in (('Swamp',{},False,-1),('Overgrown Tomb',{'pay_life':True},False,-3),('Overgrown Tomb',{},True,-1),('Underground Mortuary',{'surveil_graveyard':True},True,-1),('Forest',{},False,-1)):
            with self.subTest(fetch=name,kw=kw):
                g=self.game(); vc=self.play(g,'Verdant Catacombs'); sel=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); life=g.life[0]; vcuid=g.linked_battlefield[vc.uid]
                g.verdant_catacombs(vc.uid,sel,**kw); self.assertNotIn(vc.uid,g.permanents); self.assertEqual(g.zones.cards[vcuid].zone,'graveyard'); self.assertEqual(g.life[0],life-1)
                g.resolve(); check_invariants_s11(g)
                self.assertEqual(g.zones.cards[sel].zone,'battlefield'); self.assertEqual(g.zones.cards[sel].tapped,tapped); self.assertEqual(g.life[0],life+life_delta)
                self.assertGreaterEqual(len([t for t in g.zones.trace if t[0]=='library_shuffled']),2)      # the search shuffled (the first was the fixture to_hand)
                if name=='Underground Mortuary': self.assertEqual(trace(g,'surveil')[-1][2],'graveyard')
        g=self.game(); vc=self.play(g,'Verdant Catacombs'); bad=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Woodland Cemetery'); self.refused(g,g.verdant_catacombs,vc.uid,bad)   # no Swamp/Forest type
        inhand=self.to_hand(g,'Swamp'); self.refused(g,g.verdant_catacombs,vc.uid,inhand)                                                        # selection must be in the library

class ChannelAndDraws(_B):
    def test_takenuma_channel_discount_mill_and_return(self):
        g=self.game(); ba=g.add('Blood Artist'); g.destroy(ba.uid); g.resolve()
        for legends,generic in ((0,3),(1,2),(2,1),(4,0)):
            with self.subTest(legends=legends):
                h=PhysicalZoneGame(); h.resolve()
                for n in (SAVRA,'Dina, Soul Steeper','Yahenni, Undying Partisan','Yawgmoth, Thran Physician')[:legends]: h.add(n)
                h.resolve()
                tk=self.to_hand(h,'Takenuma, Abandoned Mire'); w=self.to_hand(h,'Sedgemoor Witch'); h.zones.move(w,'graveyard')
                h.add_mana('B',*(['C']*generic)); n=len(h.zones.zones['library'])
                h.channel_takenuma(tk,w); self.assertEqual(h.mana_pool,[]); self.assertEqual(h.zones.cards[tk].zone,'graveyard'); self.assertEqual(trace(h,'channel')[-1][3],generic)
                h.resolve(); check_invariants_s11(h); self.assertEqual(len(h.zones.zones['library']),n-3); self.assertEqual(h.zones.cards[w].zone,'hand')
        g=self.game(); tk=self.to_hand(g,'Takenuma, Abandoned Mire'); g.add_mana('B','C'); self.refused(g,g.channel_takenuma,tk)            # fixture Savra is one legend: {2}{B} needed, one short
    def test_takenuma_counts_the_fixture_savra_and_boseiju_channel_is_refused(self):
        g=self.game(); tk=self.to_hand(g,'Takenuma, Abandoned Mire'); g.add_mana('B','C','C'); g.channel_takenuma(tk); self.assertEqual(trace(g,'channel')[-1][3],2); g.resolve(); check_invariants_s11(g)
        bo=self.to_hand(g,'Boseiju, Who Endures'); g.add_mana('G','C'); self.refused(g,g.boseiju_channel,bo)
    def test_geier_reach_and_mikokoro(self):
        g=self.game(); gr=self.play(g,'Geier Reach Sanitarium'); keep=self.to_hand(g,'Swamp'); toss=self.to_hand(g,'Forest'); g.add_mana('C','C'); d=g.cards_drawn; h=len(g.zones.zones['hand'])
        g.geier_reach(gr.uid,toss); g.resolve(); self.assertEqual(g.cards_drawn,d+1); self.assertEqual(g.zones.cards[toss].zone,'graveyard'); self.assertEqual(len(g.zones.zones['hand']),h); self.assertEqual(len(trace(g,'opponent_draw_discard_unmodeled')),3)
        mk=self.play(g,'Mikokoro, Center of the Sea'); g.add_mana('C','C'); g.mikokoro(mk.uid); g.resolve(); self.assertEqual(g.cards_drawn,d+2); self.assertEqual(len(trace(g,'opponent_draw_unmodeled')),3)
        self.untap(g); g.add_mana('C'); self.refused(g,g.mikokoro,mk.uid)

class Driver(_B):
    def test_eight_seeds_24_turns_every_land_type_playable(self):
        played=set()
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=PhysicalZoneGame(seed=seed,learn_sideboard_allowed=True); opening_hand(g); ledger=run_turns_casting(g,24)
                self.assertEqual([t for t,*_ in ledger],[1,5,9,13,17,21]); played|={l for _,l,_,_ in ledger if l}
                self.assertEqual(len([l for _,l,_,_ in ledger if l]),len(trace(g,'physical_land_played')))
        self.assertTrue(played & S14_NAMES); self.assertFalse(any(l not in LAND_NAMES for l in played))

if __name__=='__main__': unittest.main()
