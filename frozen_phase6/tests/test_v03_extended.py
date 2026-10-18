"""v0.3 standalone *event* contracts; no opponent strategy or full game simulator."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import *

class EventKernelV03(unittest.TestCase):
    def setup(self,*cards,**kw):
        g=Game(**kw)
        for name in cards: g.add(name)
        g.resolve()
        return g

    def test_43_deathgreeter_duplicate_other_copy(self):
        g=self.setup('Deathgreeter','Deathgreeter')
        one=next(p for p in g.permanents.values() if p.name=='Deathgreeter')
        g.destroy(one.uid);g.resolve()
        self.assertEqual(g.life[0],41)
    def test_44_poison_tip_archer_duplicate_other_copy(self):
        g=self.setup('Poison-Tip Archer','Poison-Tip Archer')
        one=next(p for p in g.permanents.values() if p.name=='Poison-Tip Archer')
        g.destroy(one.uid);g.resolve()
        self.assertEqual(g.life,[40,39,39,39])
    def test_45_south_wind_duplicate_uses_other_toughness(self):
        g=self.setup('South Wind Avatar','South Wind Avatar')
        one=next(p for p in g.permanents.values() if p.name=='South Wind Avatar')
        one.toughness=5
        g.destroy(one.uid);g.resolve()
        self.assertEqual(g.life,[45,39,39,39])
        self.assertEqual([x[1] for x in g.trace if x[0]=='gain'],[5])
    def test_46_bogwater_lumaret_own_etb_and_other_controlled(self):
        g=self.setup('Bogwater Lumaret')
        self.assertEqual(g.life[0],41)
        g.make_tokens(PEST,2);g.resolve()
        self.assertEqual(g.life[0],43)
    def test_47_bogwater_does_not_gain_from_opponent_etb(self):
        g=self.setup('Bogwater Lumaret')
        g.add('Reassembling Skeleton',controller=1);g.resolve()
        self.assertEqual(g.life[0],41)
    def test_48_essence_warden_opponent_creature_enters(self):
        g=self.setup('Essence Warden')
        g.add('Reassembling Skeleton',controller=1);g.resolve()
        self.assertEqual(g.life[0],41)
    def test_49_exogenous_death_global_cards_not_savra_or_grave_pact(self):
        g=self.setup(SAVRA,'Blood Artist','Poison-Tip Archer','Deathgreeter',
                     'Sangromancer','Grave Pact')
        g.opposing_creature_dies();g.resolve()
        self.assertEqual(g.life,[45,38,39,39])
        self.assertEqual(g.edict_opportunities,0)
        self.assertEqual(g.opponent_sacrifices,0)
    def test_50_sangromancer_each_discard_distinct_gain_event(self):
        g=self.setup('Sangromancer','Dina, Soul Steeper')
        g.opponent_discards(2);g.resolve()
        self.assertEqual(g.life,[46,38,38,38])
        self.assertEqual([x[1] for x in g.trace if x[0]=='gain'],[3,3])
    def test_51_sangromancer_declines_opponent_events(self):
        g=self.setup('Sangromancer',choose_sangromancer_gain=False)
        g.opposing_creature_dies();g.opponent_discards();g.resolve()
        self.assertEqual(g.life,[40,40,40,40])
    def test_52_reanimation_new_object_identity_counters_reset(self):
        g=self.setup(SAVRA)
        victim=g.add('Reassembling Skeleton',counters=3,mana_value=2)
        g.destroy(victim.uid);g.resolve();g.gain(2,'fixture');g.resolve()
        g.add("Moseo, Vein's New Dean");g.resolve()
        g.moseo_end_step(target_uid=victim.uid);g.resolve()
        new=[p for p in g.permanents.values() if p.name=='Reassembling Skeleton']
        self.assertEqual(len(new),1);self.assertNotEqual(new[0].uid,victim.uid)
        self.assertEqual(new[0].counters,0);self.assertFalse(new[0].tapped)
    def test_53_cauldron_return_has_new_object_and_etb_triggers(self):
        g=self.setup('Cauldron of Essence','Essence Warden')
        victim=g.add('Reassembling Skeleton');g.destroy(victim.uid);g.resolve()
        fodder=g.add('Infestation Sage');g.resolve()
        prev=g.life[0]
        g.add_mana('B','G','C')
        g.cauldron_reanimate(target_uid=victim.uid,sacrificed_uid=fodder.uid)
        g.resolve()
        self.assertEqual(len([p for p in g.permanents.values() if p.name=='Reassembling Skeleton']),1)
        self.assertNotIn(victim.uid,g.permanents)
        self.assertGreater(g.life[0],prev)
    def test_54_skeleton_b_c_returns_tapped_and_pays(self):
        g=self.setup();p=g.add('Reassembling Skeleton');g.destroy(p.uid);g.resolve()
        g.add_mana('B','C')
        q=g.skeleton_return(p.uid);g.resolve()
        self.assertTrue(q.tapped);self.assertNotEqual(q.uid,p.uid)
        self.assertEqual(g.mana_pool,[])
    def test_55_skeleton_missing_mana_atomic_no_effect(self):
        g=self.setup();p=g.add('Reassembling Skeleton');g.destroy(p.uid);g.resolve()
        g.add_mana('G','C')
        with self.assertRaises(IllegalAction):g.skeleton_return(p.uid)
        self.assertEqual(g.mana_pool,['G','C']);self.assertIn(p,g.graveyard)
    def test_56_skeleton_generic_can_use_colored(self):
        g=self.setup();p=g.add('Reassembling Skeleton');g.destroy(p.uid);g.resolve()
        g.add_mana('B','G');self.assertTrue(g.skeleton_return(p.uid).tapped)
    def test_57_teachers_pest_requires_both_colors_and_tapped(self):
        g=self.setup();p=g.add("Teacher's Pest");g.destroy(p.uid);g.resolve()
        g.add_mana('B','C')
        with self.assertRaises(IllegalAction):g.teachers_pest_return(p.uid)
        self.assertEqual(g.mana_pool,['B','C'])
        g.add_mana('G')
        q=g.teachers_pest_return(p.uid)
        self.assertTrue(q.tapped);self.assertEqual(g.mana_pool,['C'])
    def test_58_reclamation_gy_to_hand_not_battlefield(self):
        g=self.setup('Phyrexian Reclamation')
        p=g.add('Reassembling Skeleton');g.destroy(p.uid);g.resolve()
        g.add_mana('B','G');g.phyrexian_reclamation(p.uid);g.resolve()
        self.assertIn(p.name,g.hand);self.assertNotIn(p.uid,g.permanents)
        self.assertNotIn(p,g.graveyard);self.assertEqual(g.life[0],38)
    def test_59_reclamation_at_one_life_rejected_atomically(self):
        g=self.setup('Phyrexian Reclamation')
        p=g.add('Reassembling Skeleton');g.destroy(p.uid);g.resolve()
        g.life[0]=1;g.add_mana('B','C')
        with self.assertRaises(IllegalAction):g.phyrexian_reclamation(p.uid)
        self.assertEqual(g.life[0],1);self.assertEqual(g.mana_pool,['B','C'])
    def test_60_reclamation_pay_to_zero_loses_before_return(self):
        g=self.setup('Phyrexian Reclamation')
        p=g.add('Reassembling Skeleton');g.destroy(p.uid);g.resolve()
        g.life[0]=2;g.add_mana('B','C');g.phyrexian_reclamation(p.uid);g.resolve()
        self.assertTrue(g.game_lost);self.assertNotIn(p.name,g.hand)
        self.assertIn(p,g.graveyard)
    def test_61_mana_atomicity_color_and_generic(self):
        g=self.setup();g.add_mana('B','G')
        with self.assertRaises(IllegalAction):g.pay_mana(black=1,green=1,generic=1)
        self.assertEqual(g.mana_pool,['B','G'])
        with self.assertRaises(IllegalAction):g.pay_mana(black=2)
        self.assertEqual(g.mana_pool,['B','G'])
    def test_62_viscera_seer_scry_no_silent_implementation(self):
        g=self.setup(SAVRA,'Viscera Seer')
        p=g.make_tokens(PEST)[0];g.viscera_seer_sacrifice(p.uid);g.resolve()
        self.assertEqual(g.edict_opportunities,1)
        self.assertTrue(any(t[0]=='scry_unimplemented' for t in g.trace))
    def test_63_viscera_seer_can_self_sac(self):
        g=self.setup('Viscera Seer')
        seer=next(p for p in g.permanents.values() if p.name=='Viscera Seer')
        g.viscera_seer_sacrifice(seer.uid);g.resolve()
        self.assertNotIn(seer.uid,g.permanents)
    def test_64_carrion_feeder_sac_add_counter_after_death(self):
        g=self.setup('Carrion Feeder')
        feeder=next(p for p in g.permanents.values() if p.name=='Carrion Feeder')
        victim=g.add('Reassembling Skeleton')
        g.carrion_feeder_sacrifice(feeder.uid,victim.uid);g.resolve()
        self.assertEqual(g.permanents[feeder.uid].counters,1)
        self.assertLess(next(i for i,t in enumerate(g.trace) if t[0]=='sacrifice'),
                        next(i for i,t in enumerate(g.trace) if t[0]=='plus_one_counter'))
    def test_65_carrion_feeder_self_sac_no_counter_on_absent_source(self):
        g=self.setup('Carrion Feeder')
        feeder=next(p for p in g.permanents.values() if p.name=='Carrion Feeder')
        g.carrion_feeder_sacrifice(feeder.uid,feeder.uid);g.resolve()
        self.assertNotIn(feeder.uid,g.permanents)
        self.assertFalse(any(t[0]=='plus_one_counter' for t in g.trace))
    def test_66_warren_soultrader_cannot_sac_itself(self):
        g=self.setup('Warren Soultrader')
        s=next(p for p in g.permanents.values() if p.name=='Warren Soultrader')
        with self.assertRaises(IllegalAction):g.warren_soultrader_sacrifice(s.uid,s.uid)
        self.assertEqual(g.life[0],40)
    def test_67_soultrader_treasure_and_bats_token_creation(self):
        g=self.setup('Warren Soultrader','Mirkwood Bats')
        s=next(p for p in g.permanents.values() if p.name=='Warren Soultrader')
        p=g.make_tokens(PEST)[0];g.resolve()
        g.warren_soultrader_sacrifice(s.uid,p.uid);g.resolve()
        treasures=[p for p in g.permanents.values() if p.token==TREASURE]
        self.assertEqual(len(treasures),1)
        self.assertEqual(g.life[0],40) # 40-1+1 Pest death
        self.assertEqual(g.life[1],37) # Pest create, Pest sacrifice, Treasure create
    def test_68_soultrader_pay_to_zero_loses_before_treasure(self):
        g=self.setup('Warren Soultrader')
        s=next(p for p in g.permanents.values() if p.name=='Warren Soultrader')
        victim=g.add('Reassembling Skeleton')
        g.life[0]=1
        g.warren_soultrader_sacrifice(s.uid,victim.uid);g.resolve()
        self.assertTrue(g.game_lost)
        self.assertFalse(any(p.token==TREASURE for p in g.permanents.values()))
    def test_69_global_death_does_not_spur_pest_self_dies_gain(self):
        g=self.setup(SAVRA,'Dina, Soul Steeper')
        g.opposing_creature_dies();g.resolve()
        self.assertEqual(g.life,[40,40,40,40])
        self.assertEqual(g.edict_opportunities,0)
    def test_70_token_reentry_reanimation_rejected(self):
        g=self.setup('Phyrexian Reclamation')
        token=g.make_tokens(PEST)[0];g.destroy(token.uid);g.resolve()
        g.add_mana('B','C')
        with self.assertRaises(IllegalAction):g.phyrexian_reclamation(token.uid)
        self.assertEqual(g.mana_pool,['B','C'])
    def test_71_skeleton_requires_target_record_in_own_grave(self):
        g=self.setup();g.add_mana('B','C')
        with self.assertRaises(IllegalAction):g.skeleton_return(999)
        self.assertEqual(g.mana_pool,['B','C'])
    def test_72_invalid_mana_symbol_rejected(self):
        g=self.setup()
        with self.assertRaises(IllegalAction):g.add_mana('Q')
        self.assertEqual(g.mana_pool,[])

    def test_73_cauldron_invalid_opposing_sac_has_no_side_effects(self):
        g=self.setup('Cauldron of Essence')
        target=g.add('Reassembling Skeleton');g.destroy(target.uid);g.resolve()
        opposing=g.add('Infestation Sage',controller=1)
        cauldron=next(p for p in g.permanents.values() if p.name=='Cauldron of Essence')
        previous=tuple(g.trace)
        with self.assertRaises(IllegalAction):
            g.cauldron_reanimate(target_uid=target.uid,sacrificed_uid=opposing.uid)
        self.assertFalse(cauldron.tapped)
        self.assertIn(opposing.uid,g.permanents)
        self.assertEqual(tuple(g.trace),previous)
    def test_74_immoral_bargain_invalid_cost_no_partial_sacrifice(self):
        g=self.setup()
        ours=g.add('Reassembling Skeleton')
        opposing=g.add('Infestation Sage',controller=1)
        with self.assertRaises(IllegalAction):
            g.immoral_bargain(2,[ours.uid,opposing.uid],['a','b'])
        self.assertIn(ours.uid,g.permanents)
        self.assertIn(opposing.uid,g.permanents)
        self.assertFalse(any(x[0]=='cast' for x in g.trace))
    def test_75_cast_cost_rejects_opposing_creature_before_trace(self):
        g=self.setup('Sedgemoor Witch')
        opposing=g.add('Infestation Sage',controller=1)
        trace=tuple(g.trace)
        with self.assertRaises(IllegalAction):
            g.cast_with_sacrifice_cost('Village Rites',opposing.uid)
        self.assertEqual(tuple(g.trace),trace)
        self.assertIn(opposing.uid,g.permanents)
    def test_76_cauldron_invalid_creature_untapped_and_own_target_untouched(self):
        g=self.setup('Cauldron of Essence')
        target=g.add('Reassembling Skeleton');g.destroy(target.uid);g.resolve()
        c=next(p for p in g.permanents.values() if p.name=='Cauldron of Essence')
        treasure=g.make_tokens(TREASURE)[0]
        with self.assertRaises(IllegalAction):
            g.cauldron_reanimate(target_uid=target.uid,sacrificed_uid=treasure.uid)
        self.assertFalse(c.tapped);self.assertIn(target,g.graveyard)
        self.assertIn(treasure.uid,g.permanents)

if __name__=='__main__': unittest.main()
