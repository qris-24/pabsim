"""Phase 7 partial Game/DeckZones bridge. Positive/negative and trace checks.

Tests explicitly inject fixture event permanents or move frozen real cards into
hand; no test calls a nonimplemented general casting/priority engine.
"""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_zone_bridge import PhysicalZoneGame, BridgeError
from pab_zones import DeckZones, ZoneError
from pab_focus_engine_v07 import Game as CandidateGame, SAVRA, PEST
from pab_focus_engine import Game as HistoricalGame

class Phase7PhysicalBridge(unittest.TestCase):
    def setUp(self):
        self.g=PhysicalZoneGame(seed=701)

    def one(self,name,zone='library'):
        return next(c for c in self.g.zones.zone_cards(zone) if c.name==name)

    def put_hand(self,name):
        c=self.one(name)
        self.g.zones.move(c.uid,'hand')
        return c

    def test_206_integrity_at_start_and_no_physical_board(self):
        self.assertTrue(self.g.assert_bridge_integrity())
        self.assertEqual(len(self.g.zones.zone_cards('library')),99)
        self.assertEqual(self.g.linked_battlefield,{})
        self.assertEqual(self.g.cards_drawn,0)

    def test_207_single_draw_has_real_uid_and_removed_from_library(self):
        uid=self.g.zones.zone_cards('library')[0].uid
        self.g._fixture_draw(1,'manual')
        self.assertEqual([c.uid for c in self.g.zones.zone_cards('hand')],[uid])
        self.assertEqual(len(self.g.zones.zone_cards('library')),98)
        self.assertEqual(self.g.cards_drawn,1)
        self.assertIn(('physical_draw','manual',(uid,),0),self.g.trace)

    def test_208_draw_two_distinct_objects(self):
        ids=[c.uid for c in self.g.zones.zone_cards('library')[:2]]
        self.g._fixture_draw(2,'two')
        self.assertEqual([x.uid for x in self.g.zones.zone_cards('hand')],ids)
        self.assertEqual(self.g.cards_drawn,2)
        self.assertTrue(self.g.assert_bridge_integrity())

    def test_209_zero_draw_no_side_effect(self):
        self.g._fixture_draw(0,'none')
        self.assertEqual(len(self.g.zones.zone_cards('library')),99)
        self.assertEqual(self.g.cards_drawn,0)

    def test_210_negative_draw_rejected_immutably(self):
        with self.assertRaises(ValueError):self.g._fixture_draw(-1,'wrong')
        self.assertEqual(self.g.trace,[])

    def test_211_draw_reproducibility_with_seed(self):
        g1=PhysicalZoneGame(seed=122);g2=PhysicalZoneGame(seed=122)
        for g in (g1,g2):
            g.zones.shuffle_library();g._fixture_draw(5,'seed test')
        self.assertEqual([c.uid for c in g1.zones.zone_cards('hand')],
                         [c.uid for c in g2.zones.zone_cards('hand')])

    def test_212_empty_library_attempt_is_explicit_unadjudicated(self):
        for c in list(self.g.zones.zone_cards('library')):
            self.g.zones.move(c.uid,'exile')
        self.g._fixture_draw(2,'empty')
        self.assertEqual(self.g.cards_drawn,0)
        self.assertTrue(self.g.unadjudicated_empty_library_draw)
        self.assertFalse(self.g.game_lost)
        self.assertEqual(self.g.zones.failed_draws,2)

    def test_213_partial_deck_draw_one_success_one_failure(self):
        for c in list(self.g.zones.zone_cards('library'))[1:]:
            self.g.zones.move(c.uid,'exile')
        self.g._fixture_draw(2,'partial')
        self.assertEqual(self.g.cards_drawn,1)
        self.assertEqual(self.g.zones.failed_draws,1)
        self.assertEqual(self.g.trace[-2:], [('physical_draw','partial',
                            (self.g.zones.zone_cards('hand')[0].uid,),1),
                            ('unadjudicated_empty_library_draw','partial',1)])

    def test_214_counter_matches_zone_hand_deltas_from_moldervine(self):
        self.g.add('Moldervine Reclamation');self.g.add('Reassembling Skeleton')
        self.g.sacrifice(next(p.uid for p in self.g.permanents.values() if p.name=='Reassembling Skeleton'))
        self.g.resolve()
        self.assertEqual(self.g.cards_drawn,1)
        self.assertEqual(len(self.g.zones.zone_cards('hand')),1)

    def test_215_dark_prophecy_draws_physical_and_loses_life(self):
        self.g.add('Dark Prophecy');p=self.g.add('Reassembling Skeleton')
        self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.cards_drawn,1)
        self.assertEqual(len(self.g.zones.zone_cards('hand')),1)
        self.assertEqual(self.g.life[0],39)

    def test_216_village_rites_physical_two_after_sacrifice(self):
        p=self.g.add('Reassembling Skeleton');self.g.add_mana('B','C')
        self.g.cast_pab_spell('Village Rites',p.uid);self.g.resolve()
        self.assertEqual(self.g.cards_drawn,2)
        self.assertEqual(len(self.g.zones.zone_cards('hand')),2)
        self.assertNotIn(p.uid,self.g.permanents)

    def test_217_deadly_dispute_physical_two_and_treasure(self):
        p=self.g.add('Reassembling Skeleton');self.g.add_mana('B','C')
        self.g.cast_pab_spell('Deadly Dispute',p.uid);self.g.resolve()
        self.assertEqual(self.g.cards_drawn,2)
        self.assertTrue(any(p.token and p.token.label=='Treasure' for p in self.g.permanents.values()))

    def test_218_plumb_copy_count_matches_distinct_physical_draws(self):
        p=self.g.add('Reassembling Skeleton');self.g.add_mana('B','C')
        self.g.plumb_the_forbidden([p.uid]);self.g.resolve()
        self.assertEqual(self.g.cards_drawn,2)
        self.assertEqual(len(self.g.zones.zone_cards('hand')),2)
        self.assertEqual(self.g.life[0],38)

    def test_219_skullclamp_death_creates_two_physical_draws(self):
        c=self.g.add('Skullclamp',creature=False,artifact=True)
        target=self.g.add('Reassembling Skeleton',toughness=1)
        self.g.add_mana('C');self.g.equip_skullclamp(c.uid,target.uid);self.g.resolve()
        self.assertEqual(self.g.cards_drawn,2)
        self.assertEqual(len(self.g.zones.zone_cards('hand')),2)

    def test_220_yawgmoth_draw_has_real_card(self):
        src=self.g.add('Yawgmoth, Thran Physician');fodder=self.g.add('Reassembling Skeleton')
        self.g.yawgmoth_sacrifice(src.uid,fodder.uid);self.g.resolve()
        self.assertEqual(self.g.cards_drawn,1)
        self.assertEqual(len(self.g.zones.zone_cards('hand')),1)

    def test_221_legacy_and_candidate_unlinked_draw_parity(self):
        for cls in (HistoricalGame,CandidateGame):
            g=cls();p=g.add('Reassembling Skeleton');g.add_mana('B','C')
            g.cast_pab_spell('Village Rites',p.uid);g.resolve()
            self.assertEqual(g.cards_drawn,2)
            self.assertIn(('draw',2,'Village Rites'),g.trace)

    def test_222_sakura_tribe_finds_physical_swamp_tapped(self):
        selected=self.one('Swamp').uid
        elder=self.g.add('Sakura-Tribe Elder')
        self.g.add(SAVRA)
        self.g.sakura_tribe_elder_physical(elder.uid,selected_land_uid=selected)
        self.g.resolve()
        self.assertEqual(self.g.zones.cards[selected].zone,'battlefield')
        self.assertTrue(self.g.zones.cards[selected].tapped)
        self.assertEqual(len(self.g.linked_battlefield),1)
        self.assertEqual(self.g.life[0],42)
        self.assertEqual(self.g.edict_opportunities,0)
        self.assertEqual(len(self.g.zones.zone_cards('library')),98)

    def test_223_sakura_can_qualify_to_fail_to_find(self):
        elder=self.g.add('Sakura-Tribe Elder')
        self.g.sakura_tribe_elder_physical(elder.uid)
        self.g.resolve()
        self.assertEqual(len(self.g.zones.zone_cards('library')),99)
        self.assertEqual(len(self.g.linked_battlefield),0)
        self.assertIn(('physical_basic_search_no_selection','Sakura-Tribe Elder'),self.g.trace)

    def test_224_sakura_rejects_nonbasic_land_before_sacrifice(self):
        elder=self.g.add('Sakura-Tribe Elder')
        with self.assertRaises(BridgeError):
            self.g.sakura_tribe_elder_physical(elder.uid,selected_land_uid=self.one('Command Tower').uid)
        self.assertIn(elder.uid,self.g.permanents)
        self.assertEqual(self.g.pending.__len__(),0)

    def test_225_sakura_rejects_unknown_source_before_search(self):
        with self.assertRaises(BridgeError):
            self.g.sakura_tribe_elder_physical(999,selected_land_uid=self.one('Swamp').uid)

    def test_226_sakura_draws_selected_candidate_before_resolution(self):
        elder=self.g.add('Sakura-Tribe Elder')
        uid=self.one('Swamp').uid
        self.g.sakura_tribe_elder_physical(elder.uid,selected_land_uid=uid)
        self.g.zones.move(uid,'hand')
        self.g.resolve()
        self.assertEqual(self.g.zones.cards[uid].zone,'hand')
        self.assertEqual(len(self.g.linked_battlefield),0)
        self.assertIn(('search_candidate_no_longer_in_library','Sakura-Tribe Elder',uid),self.g.trace)

    def test_227_natures_lore_real_forest_untapped(self):
        uid=self.one('Forest').uid
        self.g.add_mana('G','C')
        self.g.natures_lore_physical(selected_land_uid=uid)
        self.g.resolve()
        self.assertFalse(self.g.zones.cards[uid].tapped)
        self.assertEqual(self.g.zones.cards[uid].zone,'battlefield')
        self.assertEqual(len(self.g.zones.zone_cards('library')),98)
        self.assertEqual(self.g.mana_pool,[])

    def test_228_natures_lore_swamp_rejected_without_payment(self):
        self.g.add_mana('G','C')
        with self.assertRaises(BridgeError):
            self.g.natures_lore_physical(selected_land_uid=self.one('Swamp').uid)
        self.assertEqual(self.g.mana_pool,['G','C'])
        self.assertEqual(len(self.g.pending),0)

    def test_229_natures_lore_insufficient_green_no_mutation(self):
        uid=self.one('Forest').uid
        self.g.add_mana('C','C')
        with self.assertRaises(ValueError):self.g.natures_lore_physical(selected_land_uid=uid)
        self.assertEqual(self.g.zones.cards[uid].zone,'library')
        self.assertEqual(self.g.mana_pool,['C','C'])

    def test_230_natures_lore_sorcery_gate(self):
        uid=self.one('Forest').uid
        self.g.add_mana('G','C')
        with self.assertRaises(BridgeError):self.g.natures_lore_physical(selected_land_uid=uid,sorcery_window=False)
        self.assertEqual(self.g.mana_pool,['G','C'])

    def test_231_natures_lore_with_witch_magecraft(self):
        uid=self.one('Forest').uid
        self.g.add('Sedgemoor Witch');self.g.add_mana('G','C')
        self.g.natures_lore_physical(selected_land_uid=uid)
        self.g.resolve()
        self.assertEqual(sum(p.token==PEST for p in self.g.permanents.values()),1)
        self.assertEqual(self.g.zones.cards[uid].zone,'battlefield')

    def test_232_link_creature_moves_real_card_once(self):
        c=self.put_hand('Reassembling Skeleton')
        p=self.g.enter_linked_creature(c.uid,mana_value=2,power=2,toughness=1)
        self.assertEqual(self.g.linked_battlefield[p.uid],c.uid)
        self.assertEqual(self.g.zones.cards[c.uid].zone,'battlefield')
        self.assertTrue(self.g.assert_bridge_integrity())

    def test_233_linked_creature_sacrifice_preserves_physical_uid(self):
        c=self.put_hand('Reassembling Skeleton')
        p=self.g.enter_linked_creature(c.uid,mana_value=2)
        self.g.sacrifice(p.uid)
        self.assertNotIn(p.uid,self.g.permanents)
        self.assertEqual(self.g.linked_graveyard[p.uid],c.uid)
        self.assertEqual(self.g.zones.cards[c.uid].zone,'graveyard')
        self.assertTrue(self.g.assert_bridge_integrity())

    def test_234_linked_creature_destroy_not_savra_sacrifice(self):
        self.g.add(SAVRA)
        c=self.put_hand('Reassembling Skeleton')
        p=self.g.enter_linked_creature(c.uid,mana_value=2)
        self.g.destroy(p.uid);self.g.resolve()
        self.assertEqual(self.g.edict_opportunities,0)
        self.assertEqual(self.g.zones.cards[c.uid].zone,'graveyard')

    def test_235_linked_savra_trigger_on_real_sacrifice(self):
        self.g.add(SAVRA)
        c=self.put_hand("Teacher's Pest")
        p=self.g.enter_linked_creature(c.uid,mana_value=2)
        self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.life[0],40)  # pay 2 black, gain 2 green
        self.assertEqual(self.g.edict_opportunities,1)
        self.assertEqual(self.g.opponent_sacrifices,0)
        self.assertEqual(c.zone,'graveyard')

    def test_236_linked_skeleton_return_preserves_physical_uid(self):
        c=self.put_hand('Reassembling Skeleton')
        p=self.g.enter_linked_creature(c.uid,mana_value=2)
        self.g.sacrifice(p.uid);self.g.add_mana('B','C')
        new=self.g.skeleton_return(p.uid)
        self.assertEqual(c.zone,'battlefield')
        self.assertTrue(c.tapped)
        self.assertEqual(self.g.linked_battlefield[new.uid],c.uid)
        self.assertNotIn(p.uid,self.g.linked_graveyard)

    def test_237_teacher_pest_return_preserves_physical_uid(self):
        c=self.put_hand("Teacher's Pest")
        p=self.g.enter_linked_creature(c.uid,mana_value=2)
        self.g.sacrifice(p.uid);self.g.add_mana('B','G')
        new=self.g.teachers_pest_return(p.uid)
        self.assertEqual(new.name,"Teacher's Pest")
        self.assertTrue(c.tapped)
        self.assertEqual(c.zone,'battlefield')

    def test_238_unearthed_linked_card_is_same_physical_card(self):
        c=self.put_hand('Reassembling Skeleton')
        p=self.g.enter_linked_creature(c.uid,mana_value=2)
        self.g.sacrifice(p.uid);self.g.add_mana('B')
        self.g.unearth(p.uid);self.g.resolve()
        self.assertEqual(c.zone,'battlefield')
        self.assertIn(c.uid,self.g.linked_battlefield.values())
        self.assertTrue(self.g.assert_bridge_integrity())

    def test_239_no_linked_creature_for_unimplemented_card(self):
        c=self.put_hand('Witherbloom Charm')
        with self.assertRaises(BridgeError):
            self.g.enter_linked_creature(c.uid,mana_value=1)
        self.assertEqual(c.zone,'hand')

    def test_240_reject_link_when_card_not_in_hand(self):
        c=self.one('Reassembling Skeleton')
        with self.assertRaises(ZoneError):self.g.enter_linked_creature(c.uid,mana_value=2)
        self.assertEqual(c.zone,'library')

    def test_241_reject_duplicate_linking(self):
        c=self.put_hand('Reassembling Skeleton')
        self.g.enter_linked_creature(c.uid,mana_value=2)
        with self.assertRaises(ZoneError):self.g.enter_linked_creature(c.uid,mana_value=2)
        self.assertEqual(len(self.g.linked_battlefield),1)

    def test_242_moved_linked_graveyard_outside_bridge_detected(self):
        c=self.put_hand('Reassembling Skeleton')
        p=self.g.enter_linked_creature(c.uid,mana_value=2)
        self.g.sacrifice(p.uid)
        self.g.zones.move(c.uid,'exile')
        with self.assertRaises(AssertionError):self.g.assert_bridge_integrity()

    def test_243_moved_linked_battlefield_outside_bridge_detected(self):
        c=self.put_hand('Reassembling Skeleton')
        self.g.enter_linked_creature(c.uid,mana_value=2)
        self.g.zones.move(c.uid,'exile')
        with self.assertRaises(AssertionError):self.g.assert_bridge_integrity()

    def test_244_fixture_unlinked_creatures_stay_unlinked(self):
        p=self.g.add('Reassembling Skeleton')
        self.g.sacrifice(p.uid)
        self.assertEqual(self.g.linked_graveyard,{})
        self.assertEqual(len(self.g.zones.zone_cards('library')),99)
        self.assertTrue(self.g.assert_bridge_integrity())

    def test_245_sequential_library_draw_search_no_identity_duplication(self):
        self.g._fixture_draw(3,'prep')
        forest=self.one('Forest').uid
        self.g.add_mana('G','C');self.g.natures_lore_physical(selected_land_uid=forest)
        self.g.resolve()
        self.assertEqual(len(self.g.zones.zone_cards('library')),95)
        self.assertEqual(len(self.g.zones.zone_cards('hand')),3)
        self.assertTrue(self.g.assert_bridge_integrity())

    def test_246_linked_reanimation_second_death_consistent(self):
        c=self.put_hand('Reassembling Skeleton')
        p=self.g.enter_linked_creature(c.uid,mana_value=2)
        self.g.sacrifice(p.uid);self.g.add_mana('B','C')
        new=self.g.skeleton_return(p.uid)
        self.g.sacrifice(new.uid)
        self.assertEqual(c.zone,'graveyard')
        self.assertEqual(self.g.linked_graveyard[new.uid],c.uid)
        self.assertTrue(self.g.assert_bridge_integrity())

    def test_247_unlinked_old_and_v07_engine_savra_trace_parity(self):
        for cls in (HistoricalGame,CandidateGame):
            g=cls();g.add(SAVRA);p=g.add("Teacher's Pest")
            g.sacrifice(p.uid);g.resolve()
            self.assertEqual(g.life[0],40)
            self.assertEqual(g.edict_opportunities,1)

class Phase7IdentitySafety(unittest.TestCase):
    def test_248_reclamation_returns_same_physical_uid_to_hand(self):
        g=PhysicalZoneGame();c=next(c for c in g.zones.zone_cards('library') if c.name=='Reassembling Skeleton')
        g.zones.move(c.uid,'hand')
        p=g.enter_linked_creature(c.uid,mana_value=2)
        g.sacrifice(p.uid);g.add('Phyrexian Reclamation')
        g.add_mana('B','C')
        g.phyrexian_reclamation(p.uid)
        self.assertEqual(c.zone,'graveyard')
        g.resolve()
        self.assertEqual(c.zone,'hand')
        self.assertNotIn(p.uid,g.linked_graveyard)
        self.assertTrue(g.assert_bridge_integrity())
        self.assertEqual(g.life[0],38)

    def test_249_reclamation_illegal_mana_does_not_lose_identity(self):
        g=PhysicalZoneGame();c=next(c for c in g.zones.zone_cards('library') if c.name=='Reassembling Skeleton')
        g.zones.move(c.uid,'hand');p=g.enter_linked_creature(c.uid,mana_value=2)
        g.sacrifice(p.uid);g.add('Phyrexian Reclamation')
        with self.assertRaises(ValueError):g.phyrexian_reclamation(p.uid)
        self.assertEqual(c.zone,'graveyard')
        self.assertTrue(g.assert_bridge_integrity())

    def test_250_real_unearth_cycling_moves_actual_card_and_draws(self):
        g=PhysicalZoneGame();c=next(c for c in g.zones.zone_cards('library') if c.name=='Unearth')
        g.zones.move(c.uid,'hand');g.add_mana('C','C');g.cycle_unearth();g.resolve()
        self.assertEqual(c.zone,'graveyard')
        self.assertEqual(g.cards_drawn,1)
        self.assertEqual(len(g.zones.zone_cards('hand')),1)
        self.assertIn(('physical_cycle_discard',c.uid,'Unearth'),g.trace)

    def test_251_unearth_cycling_imaginary_hand_rejected(self):
        g=PhysicalZoneGame();g.hand.append('Unearth');g.add_mana('C','C')
        with self.assertRaises(BridgeError):g.cycle_unearth()
        self.assertEqual(g.mana_pool,['C','C'])

    def test_252_real_unearth_cycling_insufficient_mana_atomic(self):
        g=PhysicalZoneGame();c=next(c for c in g.zones.zone_cards('library') if c.name=='Unearth')
        g.zones.move(c.uid,'hand')
        with self.assertRaises(ValueError):g.cycle_unearth()
        self.assertEqual(c.zone,'hand')

    def test_253_lesson_default_house_rule_disabled_no_pest_or_hand(self):
        g=PhysicalZoneGame()
        with self.assertRaises(ZoneError):g.hunt_for_specimens(lesson=True)
        self.assertEqual(len(g.permanents),0)
        self.assertEqual(len(g.zones.zone_cards('outside_game')),1)

    def test_254_lesson_house_rule_links_physical_one_copy(self):
        g=PhysicalZoneGame(learn_sideboard_allowed=True)
        g.hunt_for_specimens(lesson=True)
        self.assertEqual(len(g.zones.zone_cards('outside_game')),0)
        self.assertEqual(len(g.zones.zone_cards('hand')),1)
        self.assertEqual(g.zones.zone_cards('hand')[0].name,'Pest Summoning')
        self.assertEqual(sum(p.token==PEST for p in g.permanents.values()),1)
        with self.assertRaises(ZoneError):g.hunt_for_specimens(lesson=True)
        self.assertEqual(sum(p.token==PEST for p in g.permanents.values()),1)

    def test_255_skeleton_power_preserved_through_reanimation(self):
        g=PhysicalZoneGame();c=next(c for c in g.zones.zone_cards('library') if c.name=='Reassembling Skeleton')
        g.zones.move(c.uid,'hand');p=g.enter_linked_creature(c.uid,mana_value=2,power=3)
        g.sacrifice(p.uid);g.add_mana('B','C')
        new=g.skeleton_return(p.uid)
        self.assertEqual(new.power,3)
        self.assertEqual(new.mana_value,2)
        self.assertEqual(g.linked_battlefield[new.uid],c.uid)

    def test_256_canonical_types_same_as_historical(self):
        from pab_focus_engine import PEST as original_pest, IllegalAction as OriginalException
        from pab_focus_engine_v07 import PEST as candidate_pest, IllegalAction as CandidateException
        self.assertIs(original_pest,candidate_pest)
        self.assertIs(OriginalException,CandidateException)

    def test_257_mismatch_learn_policy_refused(self):
        z=DeckZones(learn_sideboard_allowed=True)
        with self.assertRaises(BridgeError):PhysicalZoneGame(zones=z,learn_sideboard_allowed=False)

if __name__=='__main__': unittest.main()

if __name__=='__main__': unittest.main()
