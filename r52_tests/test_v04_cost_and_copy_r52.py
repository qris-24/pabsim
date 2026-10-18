"""R52-corrected versioned copy of tests/test_v04_cost_and_copy.py.

ONLY test 91 differs from the frozen original: Village Rites costs {B}, so a pool
of ['B'] is sufficient and the refusal is checked with a pool that has no black
mana. The frozen original is untouched and still asserts the old {1}{B} result.
Run against pab_kernel.Game.
"""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import *
from pab_kernel import Game  # promoted kernel replaces the frozen Game

class PABV04(unittest.TestCase):
    def fixture(self,*names,**kw):
        g=Game(**kw)
        for name in names:g.add(name)
        g.resolve()
        return g

    def test_77_altar_makes_black_before_pending_savra_trigger(self):
        g=self.fixture(SAVRA,'Phyrexian Altar','Dina, Soul Steeper')
        x=g.make_tokens(PEST)[0];g.resolve()
        g.phyrexian_altar_sacrifice(x.uid,'B')
        self.assertEqual(g.mana_pool,['B'])
        self.assertEqual(g.life,[40,40,40,40])
        self.assertGreater(len(g.pending),0)
        g.resolve()
        self.assertEqual(g.life,[41,38,38,38])
        self.assertEqual(g.edict_opportunities,1)
        self.assertEqual(g.opponent_sacrifices,0)

    def test_78_altar_colorless_rejected_no_cost(self):
        g=self.fixture('Phyrexian Altar');x=g.make_tokens(PEST)[0]
        with self.assertRaises(IllegalAction):g.phyrexian_altar_sacrifice(x.uid,'C')
        self.assertIn(x.uid,g.permanents)
        self.assertEqual(g.mana_pool,[])

    def test_79_altar_opponent_creature_rejected(self):
        g=self.fixture('Phyrexian Altar');x=g.add('Reassembling Skeleton',controller=1)
        with self.assertRaises(IllegalAction):g.phyrexian_altar_sacrifice(x.uid,'B')
        self.assertIn(x.uid,g.permanents)

    def test_80_altar_all_colors_are_colored(self):
        for symbol in 'WUBRG':
            g=self.fixture('Phyrexian Altar');x=g.make_tokens(PEST)[0]
            g.phyrexian_altar_sacrifice(x.uid,symbol)
            self.assertEqual(g.mana_pool,[symbol])

    def test_81_yahenni_ignores_self_as_other_sac(self):
        g=self.fixture();y=g.add('Yahenni, Undying Partisan')
        with self.assertRaises(IllegalAction):g.yahenni_sacrifice(y.uid,y.uid)
        self.assertIn(y.uid,g.permanents)

    def test_82_yahenni_temporary_indestructible_no_undeclared_recurrence(self):
        g=self.fixture(SAVRA);y=g.add('Yahenni, Undying Partisan');x=g.make_tokens(PEST)[0]
        g.yahenni_sacrifice(y.uid,x.uid);g.resolve()
        self.assertIn(y.uid,g.indestructible_until_eot)
        g.destroy(y.uid)
        self.assertIn(y.uid,g.permanents)
        g.reset_turn();g.destroy(y.uid)
        self.assertNotIn(y.uid,g.permanents)

    def test_83_yahenni_opposing_death_object_aware(self):
        g=self.fixture('Yahenni, Undying Partisan');y=next(iter(g.permanents.values()))
        g.opposing_creature_dies();g.resolve()
        self.assertEqual(y.counters,1)
        self.assertEqual(g.opponent_sacrifices,0)

    def test_84_yawgmoth_no_target_draw_and_pay_sac(self):
        g=self.fixture(SAVRA);y=g.add('Yawgmoth, Thran Physician')
        p=g.make_tokens(PEST)[0];g.resolve()
        g.yawgmoth_sacrifice(y.uid,p.uid);g.resolve()
        self.assertEqual(g.cards_drawn,1)
        self.assertEqual(g.life[0],40) # cost 1, Savra cost 2, gains 2 + 1
        self.assertEqual(g.edict_opportunities,1)

    def test_85_yawgmoth_sacrificed_locked_target_fizzles(self):
        g=self.fixture();y=g.add('Yawgmoth, Thran Physician');victim=g.add('Reassembling Skeleton')
        g.yawgmoth_sacrifice(y.uid,victim.uid,target_uid=victim.uid)
        g.resolve()
        self.assertEqual(g.cards_drawn,0)
        self.assertIn(('ability_fizzles_all_targets_illegal','Yawgmoth'),g.trace)

    def test_86_yawgmoth_selected_own_target_counter_and_draw(self):
        g=self.fixture();y=g.add('Yawgmoth, Thran Physician')
        cost=g.add('Reassembling Skeleton');t=g.add('Infestation Sage',toughness=2)
        g.yawgmoth_sacrifice(y.uid,cost.uid,target_uid=t.uid);g.resolve()
        self.assertEqual(g.permanents[t.uid].minus_counters,1)
        self.assertEqual(g.cards_drawn,1)

    def test_87_yawgmoth_counter_kills_toughness_one(self):
        g=self.fixture('Blight Mound');y=g.add('Yawgmoth, Thran Physician')
        cost=g.add('Reassembling Skeleton');t=g.add('Infestation Sage',toughness=1)
        g.yawgmoth_sacrifice(y.uid,cost.uid,target_uid=t.uid);g.resolve()
        self.assertNotIn(t.uid,g.permanents)
        self.assertEqual(g.cards_drawn,1)
        self.assertGreaterEqual(len([p for p in g.permanents.values() if p.token==FLYING_INSECT]),1)

    def test_88_yawgmoth_pay_to_zero_loses_before_draw(self):
        g=self.fixture();y=g.add('Yawgmoth, Thran Physician');p=g.add('Reassembling Skeleton')
        g.life[0]=1;g.yawgmoth_sacrifice(y.uid,p.uid);g.resolve()
        self.assertTrue(g.game_lost)
        self.assertEqual(g.cards_drawn,0)

    def test_89_yawgmoth_missing_cost_life_atomic(self):
        g=self.fixture();y=g.add('Yawgmoth, Thran Physician');p=g.add('Reassembling Skeleton')
        g.life[0]=0
        with self.assertRaises(IllegalAction):g.yawgmoth_sacrifice(y.uid,p.uid)
        self.assertIn(p.uid,g.permanents)

    def test_90_village_rites_cast_cost_and_two_drawn(self):
        g=self.fixture(SAVRA,'Sedgemoor Witch');p=g.make_tokens(PEST)[0];g.resolve()
        g.add_mana('B','C');g.cast_pab_spell('Village Rites',p.uid)
        self.assertNotIn(p.uid,g.permanents)
        self.assertEqual(g.cards_drawn,0)
        g.resolve()
        self.assertEqual(g.cards_drawn,2)
        self.assertEqual(len([p for p in g.permanents.values() if p.token==PEST]),1)

    def test_91_village_rejects_mana_shortage_before_sac(self):
        g=self.fixture();p=g.add('Reassembling Skeleton');g.add_mana('C')   # R52: {B} is the cost; colorless alone cannot pay it
        with self.assertRaises(IllegalAction):g.cast_pab_spell('Village Rites',p.uid)
        self.assertIn(p.uid,g.permanents)
        self.assertEqual(g.mana_pool,['C'])
        g.add_mana('B');g.cast_pab_spell('Village Rites',p.uid)              # R52: {B} alone pays; the {1} was never on the card
        self.assertNotIn(p.uid,g.permanents)
        self.assertEqual(g.mana_pool,['C'])

    def test_92_deadly_dispute_treasure_squirrel_and_draw(self):
        g=self.fixture('Chatterfang, Squirrel General','Mirkwood Bats')
        x=g.make_tokens(PEST)[0];g.resolve()
        g.add_mana('B','C');g.cast_pab_spell('Deadly Dispute',x.uid);g.resolve()
        self.assertEqual(g.cards_drawn,2)
        self.assertEqual(len([p for p in g.permanents.values() if p.token==TREASURE]),1)
        self.assertEqual(len([p for p in g.permanents.values() if p.token==SQUIRREL]),2)

    def test_93_deadly_dispute_can_sac_artifact_but_village_cannot(self):
        g=self.fixture();x=g.make_tokens(TREASURE)[0];g.add_mana('B','C','B','C')
        with self.assertRaises(IllegalAction):g.cast_pab_spell('Village Rites',x.uid)
        self.assertIn(x.uid,g.permanents)
        g.cast_pab_spell('Deadly Dispute',x.uid);g.resolve()
        self.assertEqual(g.cards_drawn,2)

    def test_94_tend_power_from_sac_not_one_fixed_pest(self):
        g=self.fixture('Sedgemoor Witch');x=g.add('Reassembling Skeleton',power=4)
        g.add_mana('B','G');g.cast_pab_spell('Tend the Pests',x.uid);g.resolve()
        self.assertEqual(len([p for p in g.permanents.values() if p.token==PEST]),5)

    def test_95_tend_cost_cannot_use_artifact(self):
        g=self.fixture();x=g.make_tokens(TREASURE)[0];g.add_mana('B','G')
        with self.assertRaises(IllegalAction):g.cast_pab_spell('Tend the Pests',x.uid)
        self.assertIn(x.uid,g.permanents)

    def test_96_diabolic_intent_not_false_tutor(self):
        g=self.fixture();x=g.add('Reassembling Skeleton');g.add_mana('B','C')
        with self.assertRaises(IllegalAction):g.cast_pab_spell('Diabolic Intent',x.uid)
        self.assertIn(x.uid,g.permanents)
        self.assertEqual(g.cards_drawn,0)

    def test_97_plumb_zero_sac_original_one_draw_one_life(self):
        g=self.fixture('Sedgemoor Witch');g.add_mana('B','G')
        g.plumb_the_forbidden([]);g.resolve()
        self.assertEqual(g.cards_drawn,1)
        self.assertEqual(g.life[0],39)
        self.assertEqual(len([p for p in g.permanents.values() if p.token==PEST]),1)

    def test_98_plumb_two_sac_three_draw_three_life_and_three_magecraft(self):
        g=self.fixture('Sedgemoor Witch',SAVRA,pay_savra_black=False)
        x=g.make_tokens(PEST,2);g.resolve();g.add_mana('B','C')
        g.plumb_the_forbidden([p.uid for p in x]);g.resolve()
        self.assertEqual(g.cards_drawn,3)
        self.assertEqual(len([p for p in g.permanents.values() if p.token==PEST]),3)
        self.assertEqual(g.life[0],43) # 2 old pests: each Savra +2, pest +1, minus3 for plumb => 43
        self.assertEqual(len([t for t in g.trace if t[:2]==('copy','Plumb the Forbidden')]),2)

    def test_99_plumb_rejects_duplicate_cost_no_changes(self):
        g=self.fixture();p=g.add('Reassembling Skeleton');g.add_mana('B','C')
        with self.assertRaises(IllegalAction):g.plumb_the_forbidden([p.uid,p.uid])
        self.assertIn(p.uid,g.permanents)
        self.assertEqual(g.mana_pool,['B','C'])

    def test_100_plumb_life_zero_stops_further_copies_and_draw(self):
        g=self.fixture();p=g.add('Reassembling Skeleton');g.add_mana('B','G')
        g.life[0]=1;g.plumb_the_forbidden([p.uid]);g.resolve()
        self.assertTrue(g.game_lost)
        self.assertEqual(g.cards_drawn,1)

    def test_101_cauldron_mana_cost_and_sorcery_gate(self):
        g=self.fixture('Cauldron of Essence');x=g.add('Reassembling Skeleton')
        g.destroy(x.uid);g.resolve();fodder=g.add('Infestation Sage')
        with self.assertRaises(IllegalAction):g.cauldron_reanimate(target_uid=x.uid,sacrificed_uid=fodder.uid)
        self.assertIn(fodder.uid,g.permanents)
        self.assertFalse(next(p for p in g.permanents.values() if p.name=='Cauldron of Essence').tapped)
        g.add_mana('B','G','C')
        with self.assertRaises(IllegalAction):g.cauldron_reanimate(target_uid=x.uid,sacrificed_uid=fodder.uid,sorcery_window=False)
        self.assertEqual(g.mana_pool,['B','G','C'])
        g.cauldron_reanimate(target_uid=x.uid,sacrificed_uid=fodder.uid)
        self.assertEqual(g.mana_pool,[])
        g.resolve()
        self.assertTrue(any(p.name=='Reassembling Skeleton' for p in g.permanents.values()))

if __name__=='__main__':unittest.main()
