"""Stage S9: the nine B/G fixer lands. Entry condition both ways, mana ability, life/damage
costs, Pathway faces, Mortuary surveil, refusals (second land, wrong step, wrong kwargs),
the other nine nonbasics still fail closed, frozen basic/Command Tower path unchanged,
8-seed 16-turn driver run with invariants. CR refs: 305.1-2, 712.8, 701.46, 120.3e.
"""
import sys, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA
from pab_zone_bridge import BridgeError
from pab_zones import ZoneError, UnsupportedZoneMechanic, LAND_NAMES, SUPPORTED_LAND_MANA
from pab_turn_clock import ClockError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_lands_s9 import FIXERS, S9_NAMES, PATHWAY, LAND_MANA, run_turns_casting, play_land_policy, playable_land_in_hand
from pab_opponents_s8 import check_invariants_s8
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names):
        g=PhysicalZoneGame(); g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve(); check_invariants_s8(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s8(g); return uid
    def play(self,g,name,**kw):
        uid=self.to_hand(g,name); p=g.play_physical_land(uid,**kw); g.resolve(); check_invariants_s8(g)
        self.assertEqual(g.zones.cards[uid].zone,'battlefield'); self.assertEqual(g.linked_battlefield[p.uid],uid); self.assertEqual(p.tapped,g.zones.cards[uid].tapped)
        return p
    def new_land_drop(self,g): g.zones.land_plays_this_turn=0            # fixture shortcut, pre-clock: another land play
    def refused(self,g,uid,exc=BridgeError,**kw):
        hand=list(g.zones.zones['hand']); plays=g.zones.land_plays_this_turn; perms=set(g.permanents); life=g.life[0]
        with self.assertRaises(exc): g.play_physical_land(uid,**kw)
        self.assertEqual((list(g.zones.zones['hand']),g.zones.land_plays_this_turn,set(g.permanents),g.life[0]),(hand,plays,perms,life)); check_invariants_s8(g)

class Scope(_B):
    def test_kernel_promoted_and_table_matches_evidence(self):
        self.assertIn('+S9',KERNEL_VERSION); self.assertIn('S9',PROMOTED)
        ev=json.loads((ROOT/'EVIDENCE'/'S9_LAND_EVIDENCE.json').read_text(encoding='utf-8'))['cards']
        self.assertEqual(set(ev),S9_NAMES); self.assertEqual(len(S9_NAMES),9)
        for n,c in ev.items():
            self.assertTrue({'B','G'}<=set(c['produced_mana']),n); self.assertEqual(set(FIXERS[n]['mana'])-{'C'},{'B','G'},n)
            self.assertTrue(c['type_line'].startswith('Land'),n)
        self.assertEqual(ev['Llanowar Wastes']['oracle_text'].count('{T}'),2); self.assertIn('Pay 1 life',ev['Nurturing Peatland']['oracle_text'])
        self.assertEqual([f['name'] for f in ev[PATHWAY]['card_faces']],['Darkbore Pathway','Slitherbore Pathway'])
    def test_other_nonbasics_still_fail_closed_and_frozen_zone_path_untouched(self):
        g=self.game()
        for name in sorted(LAND_NAMES-set(LAND_MANA)):                                    # S14 (2026-10-18) made these nine playable on the bridge; the frozen zones path still refuses them
            uid=self.to_hand(g,name)
            with self.assertRaises(UnsupportedZoneMechanic): g.zones.play_land(uid)
            self.assertEqual(g.zones.cards[uid].zone,'hand')
        self.assertEqual(len(LAND_NAMES-set(LAND_MANA)),9)
        uid=self.to_hand(g,'Blooming Marsh')
        with self.assertRaises(UnsupportedZoneMechanic): g.zones.play_land(uid)        # frozen zones path unchanged
        self.assertEqual(SUPPORTED_LAND_MANA,{'Forest':('G',),'Swamp':('B',),'Command Tower':('B','G')})
    def test_frozen_basic_and_command_tower_path_unchanged(self):
        g=self.game(); p=self.play(g,'Command Tower'); self.assertEqual(g.tap_physical_land_for_mana(p.uid,color='G'),'G')
        self.new_land_drop(g); q=self.play(g,'Swamp'); self.assertEqual(g.tap_physical_land_for_mana(q.uid),'B'); self.assertEqual(g.mana_pool,['G','B'])
        self.new_land_drop(g); uid=self.to_hand(g,'Forest'); self.refused(g,uid,face='Darkbore'); self.refused(g,uid,pay_life=True); self.refused(g,uid,surveil_graveyard=True)

class EntryConditions(_B):
    def test_blooming_marsh_untapped_with_two_or_fewer_other_lands_then_tapped(self):
        g=self.game()
        for n in ('Swamp','Forest'): self.play(g,n); self.new_land_drop(g)
        self.assertFalse(self.play(g,'Blooming Marsh').tapped)                      # 2 others
        g2=self.game()
        for n in ('Swamp','Forest','Command Tower'): self.play(g2,n); self.new_land_drop(g2)
        self.assertTrue(self.play(g2,'Blooming Marsh').tapped)                      # 3 others
    def test_deathcap_glade_tapped_with_fewer_than_two_other_lands(self):
        g=self.game(); self.play(g,'Swamp'); self.new_land_drop(g); self.assertTrue(self.play(g,'Deathcap Glade').tapped)
        g2=self.game(); self.play(g2,'Swamp'); self.new_land_drop(g2); self.play(g2,'Forest'); self.new_land_drop(g2); self.assertFalse(self.play(g2,'Deathcap Glade').tapped)
    def test_woodland_cemetery_needs_a_swamp_or_forest_type_not_just_any_land(self):
        g=self.game(); self.play(g,'Command Tower'); self.new_land_drop(g); self.assertTrue(self.play(g,'Woodland Cemetery').tapped)
        g2=self.game(); self.play(g2,'Overgrown Tomb',pay_life=True); self.new_land_drop(g2); self.assertFalse(self.play(g2,'Woodland Cemetery').tapped)   # Swamp Forest type
        g3=self.game(); self.assertTrue(self.play(g3,'Woodland Cemetery').tapped)
    def test_undergrowth_stadium_depends_on_opponents_still_in_the_game(self):
        g=self.game(); self.assertFalse(self.play(g,'Undergrowth Stadium').tapped)
        g2=self.game(); g2.life[1]=g2.life[2]=0; g2.resolve(); self.assertEqual(g2.seats_in_game(),[3]); self.assertTrue(self.play(g2,'Undergrowth Stadium').tapped)
    def test_overgrown_tomb_pay_two_life_or_tapped(self):
        g=self.game(); p=self.play(g,'Overgrown Tomb',pay_life=True); self.assertFalse(p.tapped); self.assertEqual(g.life[0],38); self.assertEqual(trace(g,'pay_life')[-1],('pay_life',2,'Overgrown Tomb'))
        g3=self.game(); g3.life[0]=1; uid=self.to_hand(g3,'Overgrown Tomb'); self.refused(g3,uid,pay_life=True)   # cannot pay
        g2=self.game(); p=self.play(g2,'Overgrown Tomb'); self.assertTrue(p.tapped); self.assertEqual(g2.life[0],40)
    def test_underground_mortuary_enters_tapped_and_surveils_by_precommitted_choice(self):
        g=self.game(); uid=self.to_hand(g,'Underground Mortuary'); top=g.zones.zones['library'][0]; p=g.play_physical_land(uid); g.resolve(); check_invariants_s8(g); self.assertTrue(p.tapped)
        self.assertEqual(trace(g,'surveil'),[('surveil',top,'top')]); self.assertEqual(g.zones.zones['library'][0],top)
        g2=self.game(); uid=self.to_hand(g2,'Underground Mortuary'); top=g2.zones.zones['library'][0]; n=len(g2.zones.zones['graveyard']); g2.play_physical_land(uid,surveil_graveyard=True); g2.resolve(); check_invariants_s8(g2)
        self.assertEqual(trace(g2,'surveil'),[('surveil',top,'graveyard')]); self.assertEqual(g2.zones.cards[top].zone,'graveyard'); self.assertEqual(len(g2.zones.zones['graveyard']),n+1)
        self.assertEqual(trace(g2,'resolve')[-1],('resolve','Underground Mortuary surveil 1'))

class ManaAbilities(_B):
    def test_duals_produce_either_colour_and_refuse_others(self):
        for name in ('Blooming Marsh','Deathcap Glade','Woodland Cemetery','Undergrowth Stadium','Overgrown Tomb','Underground Mortuary'):
            with self.subTest(name=name):
                g=self.game(); p=self.play(g,name,**({'pay_life':True} if name=='Overgrown Tomb' else {}))
                if p.tapped: g.zones.new_turn(); p.tapped=False
                with self.assertRaises(BridgeError): g.tap_physical_land_for_mana(p.uid,color='C')
                with self.assertRaises(BridgeError): g.tap_physical_land_for_mana(p.uid)        # a choice is required
                self.assertEqual(g.tap_physical_land_for_mana(p.uid,color='G'),'G'); self.assertTrue(p.tapped); self.assertEqual(g.mana_pool,['G'])
                with self.assertRaises(BridgeError): g.tap_physical_land_for_mana(p.uid,color='B')   # already tapped
                check_invariants_s8(g)
    def test_pathway_face_decides_the_colour_and_is_required(self):
        g=self.game(); uid=self.to_hand(g,PATHWAY); self.refused(g,uid); self.refused(g,uid,face='Swamp')
        p=g.play_physical_land(uid,face='Darkbore'); check_invariants_s8(g); self.assertEqual((p.face,p.tapped,p.name),('Darkbore',False,PATHWAY))
        with self.assertRaises(BridgeError): g.tap_physical_land_for_mana(p.uid,color='G')
        self.assertEqual(g.tap_physical_land_for_mana(p.uid),'B')
        g2=self.game(); q=self.play(g2,PATHWAY,face='Slitherbore'); self.assertEqual(g2.tap_physical_land_for_mana(q.uid),'G')
        self.assertEqual(trace(g,'s9_land_entered'),[('s9_land_entered',PATHWAY,'Darkbore','untapped')])
    def test_llanowar_wastes_colourless_free_coloured_costs_one_life(self):
        g=self.game(); p=self.play(g,'Llanowar Wastes'); self.assertEqual(g.tap_physical_land_for_mana(p.uid,color='C'),'C'); self.assertEqual(g.life[0],40)
        g.zones.new_turn(); p.tapped=False; self.assertEqual(g.tap_physical_land_for_mana(p.uid,color='B'),'B'); self.assertEqual(g.life[0],39)
        self.assertEqual(trace(g,'damage_to_controller'),[('damage_to_controller',1,'Llanowar Wastes')]); self.assertEqual(trace(g,'lose_life')[-1],('lose_life',1,'Llanowar Wastes'))
    def test_nurturing_peatland_pays_one_life_per_tap_and_refuses_at_zero(self):
        g=self.game(); p=self.play(g,'Nurturing Peatland'); self.assertEqual(g.tap_physical_land_for_mana(p.uid,color='G'),'G'); self.assertEqual(g.life[0],39)
        g.zones.new_turn(); p.tapped=False; g.life[0]=0
        with self.assertRaises(BridgeError): g.tap_physical_land_for_mana(p.uid,color='B')
        self.assertFalse(p.tapped); self.assertEqual(g.mana_pool,['G'])

class Refusals(_B):
    def test_second_land_play_wrong_step_wrong_turn_and_kwargs_on_wrong_lands(self):
        g=self.game(); self.play(g,'Swamp'); uid=self.to_hand(g,'Blooming Marsh'); self.refused(g,uid)                 # second land this turn
        g2=self.game(); uid=self.to_hand(g2,'Deathcap Glade'); self.refused(g2,uid,pay_life=True); self.refused(g2,uid,surveil_graveyard=True); self.refused(g2,uid,face='Darkbore')
        g2.advance_to('upkeep',active_player=0); self.refused(g2,uid)                                                  # not a main phase
        g2.advance_to('precombat_main',active_player=1); self.refused(g2,uid,exc=ClockError)                           # not your turn
        g2.advance_to('precombat_main',active_player=0); uid2=self.to_hand(g2,'Village Rites'); self.refused(g2,uid2,exc=ZoneError)   # not a land
        self.refused(g2,uid,main_phase=True)                                                                          # kw timing refused once engaged
        p=g2.play_physical_land(uid); check_invariants_s8(g2); self.assertTrue(p.tapped)                                 # 0 other lands: Glade enters tapped
    def test_glade_with_no_other_land_is_tapped(self):
        g=self.game(); self.assertTrue(self.play(g,'Deathcap Glade').tapped)

class Driver(_B):
    def game_seed(self,seed):
        g=PhysicalZoneGame(seed=seed); g.add(SAVRA); g.resolve(); return g
    def test_sixteen_turns_all_seeds_invariants_every_land_and_cast_accounted(self):
        total_casts=0; fixers=0
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=self.game_seed(seed); opening_hand(g); ledger=run_turns_casting(g,16)
                self.assertEqual([t for t,*_ in ledger],[1,5,9,13]); self.assertEqual(g.mana_pool,[]); self.assertEqual(g.stack_cards,{})
                lands=[l for _,l,_,_ in ledger if l]; self.assertEqual(len(lands),len(trace(g,'physical_land_played')))
                self.assertTrue(all(l in LAND_MANA for l in lands)); fixers+=sum(l in S9_NAMES for l in lands)
                total_casts+=sum(len(c) for *_,c in ledger)
                z=g.zones; self.assertEqual(sum(len(z.zones[k]) for k in ('library','hand','battlefield','graveyard')),99+sum(1 for c in z.cards.values() if c.token))
        self.assertGreater(fixers,0); self.assertGreater(total_casts,0)
    def test_pinned_seed_42_plays_wastes_and_a_darkbore_pathway_and_casts_moseo(self):
        g=self.game_seed(42); opening_hand(g); ledger=run_turns_casting(g,16)
        self.assertEqual([(t,l,c) for t,l,_,c in ledger],[(1,'Swamp',()),(5,'Llanowar Wastes',()),(9,PATHWAY,("Moseo, Vein's New Dean",)),(13,None,('Sedgemoor Witch',))])
        pw=next(p for p in g.permanents.values() if p.name==PATHWAY); self.assertEqual(pw.face,'Darkbore')
    def test_policy_chooses_pathway_face_by_colour_need(self):
        g=self.game_seed(0); opening_hand(g); g.advance_to('precombat_main',active_player=0)
        for u in list(g.zones.zones['hand']): g.zones.move(u,'library')
        self.to_hand(g,PATHWAY); self.to_hand(g,'Essence Warden')
        u,kw=play_land_policy(g); self.assertEqual((g.zones.cards[u].name,kw),(PATHWAY,{'face':'Slitherbore'}))
        self.assertEqual(playable_land_in_hand(g),u)

if __name__=='__main__': unittest.main()
