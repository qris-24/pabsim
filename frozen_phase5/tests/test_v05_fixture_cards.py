"""New positive and negative v0.5 partial mechanics, based on inherited PAB audit.

These tests are not an end-to-end Commander rules or Oracle verification.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import *

class Phase5Fixtures(unittest.TestCase):
    def game(self, *names, **kw):
        g=Game(**kw)
        for n in names:g.add(n)
        g.resolve()
        return g
    def find(self,g,name):
        return next(p for p in g.permanents.values() if p.name==name)
    def token_count(self,g,kind):
        return sum(p.token==kind for p in g.permanents.values())

    def test_112_teacher_pest_blocks_rescuer_at_upkeep_start(self):
        g=self.game('Pest Rescuer',"Teacher's Pest")
        g.begin_upkeep();g.resolve()
        self.assertEqual(self.token_count(g,PEST),0)

    def test_113_teacher_pest_entered_before_rescuer_trigger_resolves(self):
        g=self.game('Pest Rescuer')
        g.begin_upkeep();g.add("Teacher's Pest");g.resolve()
        self.assertEqual(self.token_count(g,PEST),0)

    def test_114_teacher_pest_leaves_before_upkeep_triggers(self):
        g=self.game('Pest Rescuer');x=g.add("Teacher's Pest")
        g.sacrifice(x.uid);g.resolve();g.begin_upkeep();g.resolve()
        self.assertEqual(self.token_count(g,PEST),1)

    def test_115_signet_consumes_one_to_produce_exact_BG(self):
        g=self.game('Golgari Signet');p=self.find(g,'Golgari Signet')
        g.add_mana('C');self.assertEqual(g.tap_mana_rock(p.uid),('B','G'))
        self.assertEqual(g.mana_pool,['B','G']);self.assertTrue(p.tapped)

    def test_116_signet_cannot_run_without_starting_mana(self):
        g=self.game('Golgari Signet');p=self.find(g,'Golgari Signet')
        with self.assertRaises(IllegalAction):g.tap_mana_rock(p.uid)
        self.assertFalse(p.tapped)

    def test_117_signet_cannot_activate_twice_while_tapped(self):
        g=self.game('Golgari Signet');p=self.find(g,'Golgari Signet')
        g.add_mana('B','C');g.tap_mana_rock(p.uid)
        with self.assertRaises(IllegalAction):g.tap_mana_rock(p.uid)
        self.assertEqual(g.mana_pool,['B','B','G'])

    def test_118_arcane_signet_savra_identity_two_legal_colors(self):
        for c in ('B','G'):
            g=self.game('Arcane Signet');p=self.find(g,'Arcane Signet')
            self.assertEqual(g.tap_mana_rock(p.uid,color=c),(c,))
            self.assertEqual(g.mana_pool,[c])

    def test_119_arcane_signet_rejects_white_without_tapping(self):
        g=self.game('Arcane Signet');p=self.find(g,'Arcane Signet')
        with self.assertRaises(IllegalAction):g.tap_mana_rock(p.uid,color='W')
        self.assertFalse(p.tapped)

    def test_120_sol_ring_creates_colorless_only_not_green(self):
        g=self.game('Sol Ring');p=self.find(g,'Sol Ring');g.tap_mana_rock(p.uid)
        self.assertEqual(g.mana_pool,['C','C'])
        with self.assertRaises(IllegalAction):g.pay_mana(green=1)
        self.assertEqual(g.mana_pool,['C','C'])

    def test_121_sol_ring_rejects_selected_green(self):
        g=self.game('Sol Ring');p=self.find(g,'Sol Ring')
        with self.assertRaises(IllegalAction):g.tap_mana_rock(p.uid,color='G')
        self.assertFalse(p.tapped)

    def test_122_rock_rejects_opponent_owned_and_nonrock(self):
        g=self.game('Sol Ring');x=g.add('Golgari Signet',controller=1)
        with self.assertRaises(IllegalAction):g.tap_mana_rock(x.uid)
        with self.assertRaises(IllegalAction):g.tap_mana_rock(self.find(g,'Sol Ring').uid,color='G')
        self.assertFalse(x.tapped)

    def test_123_sakura_sac_is_green_only_and_tapped_basic_after_resolve(self):
        g=self.game(SAVRA);elder=g.add('Sakura-Tribe Elder')
        idx=g.put_basic_land_in_fixture_library('Swamp')
        g.sakura_tribe_elder_sacrifice(elder.uid,land_index=idx)
        self.assertNotIn(elder.uid,g.permanents)
        self.assertEqual(g.edict_opportunities,0)
        self.assertEqual(g.life[0],40)
        g.resolve()
        sw=self.find(g,'Swamp');self.assertTrue(sw.tapped)
        self.assertEqual(g.life[0],42)
        self.assertEqual(g.edict_opportunities,0)

    def test_124_sakura_no_basic_to_find_still_sacrificed(self):
        g=self.game();elder=g.add('Sakura-Tribe Elder')
        g.sakura_tribe_elder_sacrifice(elder.uid);g.resolve()
        self.assertNotIn(elder.uid,g.permanents)
        self.assertTrue(any(x[0]=='fixture_basic_land_search_failed_to_find' for x in g.trace))

    def test_125_sakura_rejects_other_creature_as_activation_source(self):
        g=self.game();x=g.add('Reassembling Skeleton')
        with self.assertRaises(IllegalAction):g.sakura_tribe_elder_sacrifice(x.uid)
        self.assertIn(x.uid,g.permanents)

    def test_126_natures_lore_finds_basic_forest_untapped(self):
        g=self.game('Sedgemoor Witch');idx=g.put_basic_land_in_fixture_library('Forest')
        g.add_mana('G','C');g.natures_lore(land_index=idx)
        self.assertFalse(any(p.name=='Forest' for p in g.permanents.values()))
        g.resolve()
        self.assertFalse(self.find(g,'Forest').tapped)
        self.assertEqual(self.token_count(g,PEST),1)

    def test_127_natures_lore_rejects_nonforest_swamp(self):
        g=self.game();idx=g.put_basic_land_in_fixture_library('Swamp')
        g.add_mana('G','C')
        with self.assertRaises(IllegalAction):g.natures_lore(land_index=idx)
        self.assertEqual(g.mana_pool,['G','C'])

    def test_128_natures_lore_needs_green_not_just_sol_ring_mana(self):
        g=self.game();g.add_mana('C','C')
        idx=g.put_basic_land_in_fixture_library('Forest')
        with self.assertRaises(IllegalAction):g.natures_lore(land_index=idx)
        self.assertEqual(g.mana_pool,['C','C'])

    def test_129_natures_lore_sorcery_timing_gate(self):
        g=self.game();g.add_mana('G','C');idx=g.put_basic_land_in_fixture_library('Forest')
        with self.assertRaises(IllegalAction):g.natures_lore(land_index=idx,sorcery_window=False)
        self.assertEqual(g.mana_pool,['G','C'])

    def test_130_pest_infestation_no_targets_makes_2x(self):
        g=self.game('Mirkwood Bats');g.add_mana('G','C','C','C','C')
        g.pest_infestation(2);g.resolve()
        self.assertEqual(self.token_count(g,PEST),4)
        self.assertEqual(g.life[1],36)

    def test_131_pest_infestation_x0_no_tokens_but_magecraft(self):
        g=self.game('Sedgemoor Witch');g.add_mana('G')
        g.pest_infestation(0);g.resolve()
        self.assertEqual(self.token_count(g,PEST),1)

    def test_132_pest_infestation_x_cost_double_colorless(self):
        g=self.game();g.add_mana('G','C','C','C')
        with self.assertRaises(IllegalAction):g.pest_infestation(2)
        self.assertEqual(g.mana_pool,['G','C','C','C'])

    def test_133_pest_infestation_x1_destoys_artifact_then_two_pests(self):
        g=self.game('Sol Ring');p=self.find(g,'Sol Ring')
        g.add_mana('G','C','C');g.pest_infestation(1,target_uids=[p.uid]);g.resolve()
        self.assertNotIn(p.uid,g.permanents)
        self.assertEqual(self.token_count(g,PEST),2)

    def test_134_pest_infestation_rejects_creature_target(self):
        g=self.game();p=g.add('Reassembling Skeleton');g.add_mana('G','C','C')
        with self.assertRaises(IllegalAction):g.pest_infestation(1,target_uids=[p.uid])
        self.assertEqual(g.mana_pool,['G','C','C'])
        self.assertIn(p.uid,g.permanents)

    def test_135_pest_infestation_rejects_too_many_targets(self):
        g=self.game('Sol Ring','Skullclamp');a=self.find(g,'Sol Ring');b=self.find(g,'Skullclamp')
        g.add_mana('G','C','C')
        with self.assertRaises(IllegalAction):g.pest_infestation(1,target_uids=[a.uid,b.uid])
        self.assertEqual(g.mana_pool,['G','C','C'])

    def test_136_pest_infestation_all_illegal_at_resolution_fizzles(self):
        g=self.game('Sol Ring');p=self.find(g,'Sol Ring');g.add_mana('G','C','C')
        g.pest_infestation(1,target_uids=[p.uid]);g.destroy(p.uid);g.resolve()
        self.assertEqual(self.token_count(g,PEST),0)
        self.assertIn(('spell_fizzles_all_targets_illegal','Pest Infestation'),g.trace)

    def test_137_pest_infestation_partial_target_illegal_still_makes_tokens(self):
        g=self.game('Sol Ring','Skullclamp');a=self.find(g,'Sol Ring');b=self.find(g,'Skullclamp')
        g.add_mana('G','C','C','C','C')
        g.pest_infestation(2,target_uids=[a.uid,b.uid]);g.destroy(a.uid);g.resolve()
        self.assertNotIn(b.uid,g.permanents)
        self.assertEqual(self.token_count(g,PEST),4)

    def test_138_unearth_returns_mana_value_3_or_less(self):
        g=self.game('Sedgemoor Witch');p=g.add('Reassembling Skeleton',mana_value=3)
        g.destroy(p.uid);g.resolve();g.add_mana('B');g.unearth(p.uid);g.resolve()
        self.assertTrue(any(q.name==p.name and q.uid!=p.uid for q in g.permanents.values()))
        self.assertEqual(self.token_count(g,PEST),1)

    def test_139_unearth_rejects_mana_value_4_without_paying(self):
        g=self.game();p=g.add('Reassembling Skeleton',mana_value=4)
        g.destroy(p.uid);g.resolve();g.add_mana('B')
        with self.assertRaises(IllegalAction):g.unearth(p.uid)
        self.assertEqual(g.mana_pool,['B'])

    def test_140_unearth_illegal_grave_target_cannot_pay(self):
        g=self.game();p=g.add('Reassembling Skeleton');g.add_mana('B')
        with self.assertRaises(IllegalAction):g.unearth(p.uid)
        self.assertEqual(g.mana_pool,['B'])

    def test_141_unearth_target_removed_before_resolution_fizzles(self):
        g=self.game();p=g.add('Reassembling Skeleton',mana_value=2)
        g.destroy(p.uid);g.resolve();g.add_mana('B');g.unearth(p.uid)
        g.graveyard.remove(p);g.resolve()
        self.assertTrue(any(t[0]=='spell_fizzles_all_targets_illegal' for t in g.trace))

    def test_142_unearth_cycling_discards_and_draws_no_magecraft(self):
        g=self.game('Sedgemoor Witch');g.hand.append('Unearth');g.add_mana('C','C')
        g.cycle_unearth();g.resolve()
        self.assertNotIn('Unearth',g.hand);self.assertEqual(g.cards_drawn,1)
        self.assertEqual(self.token_count(g,PEST),0)

    def test_143_unearth_cycle_fails_without_card_in_hand(self):
        g=self.game();g.add_mana('C','C')
        with self.assertRaises(IllegalAction):g.cycle_unearth()
        self.assertEqual(g.mana_pool,['C','C'])

    def test_144_clamp_equip_one_toughness_pest_dies_draw_two_no_savra(self):
        g=self.game(SAVRA,'Skullclamp');clamp=self.find(g,'Skullclamp')
        p=g.make_tokens(PEST)[0];g.add_mana('C');g.equip_skullclamp(clamp.uid,p.uid)
        g.resolve()
        self.assertNotIn(p.uid,g.permanents)
        self.assertEqual(g.cards_drawn,2)
        self.assertEqual(g.life[0],41)
        self.assertEqual(g.edict_opportunities,0)

    def test_145_clamp_attached_survivor_draws_when_sacrificed(self):
        g=self.game('Skullclamp');clamp=self.find(g,'Skullclamp')
        p=g.add('Reassembling Skeleton',toughness=2)
        g.add_mana('C');g.equip_skullclamp(clamp.uid,p.uid)
        self.assertIn(p.uid,g.permanents)
        g.sacrifice(p.uid);g.resolve();self.assertEqual(g.cards_drawn,2)

    def test_146_clamp_does_not_draw_if_equipment_unattached(self):
        g=self.game('Skullclamp');clamp=self.find(g,'Skullclamp')
        p=g.add('Reassembling Skeleton',toughness=2)
        g.add_mana('C');g.equip_skullclamp(clamp.uid,p.uid)
        g.destroy(clamp.uid);g.destroy(p.uid);g.resolve()
        self.assertEqual(g.cards_drawn,0)

    def test_147_clamp_equip_cost_atomic_if_no_mana(self):
        g=self.game('Skullclamp');clamp=self.find(g,'Skullclamp');p=g.make_tokens(PEST)[0]
        with self.assertRaises(IllegalAction):g.equip_skullclamp(clamp.uid,p.uid)
        self.assertIn(p.uid,g.permanents)
        self.assertEqual(g.skullclamp_attached,{})

    def test_148_clamp_equip_forbids_opponent_target(self):
        g=self.game('Skullclamp');clamp=self.find(g,'Skullclamp');p=g.add('Reassembling Skeleton',controller=1)
        g.add_mana('C')
        with self.assertRaises(IllegalAction):g.equip_skullclamp(clamp.uid,p.uid)
        self.assertEqual(g.mana_pool,['C'])

    def test_149_clamp_counter_protects_pest_from_zero_toughness(self):
        g=self.game('Skullclamp');clamp=self.find(g,'Skullclamp')
        p=g.add('Reassembling Skeleton',toughness=1,counters=1)
        g.add_mana('C');g.equip_skullclamp(clamp.uid,p.uid)
        self.assertIn(p.uid,g.permanents)

if __name__ == '__main__': unittest.main()
