"""Phase 6: tests of physical identities and deterministic, partial land/zone paths.

No full spells, search/shuffle timing, priority, multiplayer or Oracle certification.
"""
import sys, unittest
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_zones import DeckZones, ZoneError, UnsupportedZoneMechanic, LAND_NAMES


class PhysicalZones(unittest.TestCase):
    def setUp(self):
        self.g=DeckZones(seed=17)

    def first(self,name,zone='library'):
        return next(c for c in self.g.zone_cards(zone) if c.name==name)

    def test_150_baseline_exact_counts_and_separate_commander_lesson(self):
        g=self.g
        self.assertEqual(len(g.zone_cards('library')),99)
        self.assertEqual(len(g.zone_cards('command')),1)
        self.assertEqual(len(g.zone_cards('outside_game')),1)
        self.assertEqual(g.zone_cards('command')[0].name,'Savra, Queen of the Golgari')
        self.assertEqual(g.zone_cards('outside_game')[0].name,'Pest Summoning')
        self.assertEqual(sum(c.is_land for c in g.zone_cards('library')),34)

    def test_151_21_distinct_lands_and_34_physical_copies(self):
        lands=[c for c in self.g.zone_cards('library') if c.is_land]
        self.assertEqual(len(set(c.name for c in lands)),21)
        self.assertEqual(set(c.name for c in lands),LAND_NAMES)
        counts=Counter(c.name for c in lands)
        self.assertEqual(counts['Forest'],6)
        self.assertEqual(counts['Swamp'],9)

    def test_152_all_cards_distinct_objects_including_repeated_basics(self):
        ids=[c.uid for c in self.g.cards.values()]
        self.assertEqual(len(ids),101)
        self.assertEqual(len(set(ids)),101)
        self.assertTrue(self.g.assert_integrity())

    def test_153_initial_cards_have_owner_and_no_controller_off_battlefield(self):
        self.assertTrue(all(c.owner==0 and c.controller is None for c in self.g.cards.values()))
        self.assertTrue(self.g.assert_integrity())

    def test_154_draw_moves_real_top_card_with_same_uid(self):
        uid=self.g.zone_cards('library')[0].uid
        card=self.g.draw()[0]
        self.assertEqual(card.uid,uid)
        self.assertEqual(card.zone,'hand')
        self.assertEqual(len(self.g.zone_cards('library')),98)
        self.assertEqual(len(self.g.zone_cards('hand')),1)
        self.assertTrue(self.g.assert_integrity())

    def test_155_draw_repeats_move_top_in_known_order(self):
        before=[c.uid for c in self.g.zone_cards('library')[:4]]
        drawn=self.g.draw(4)
        self.assertEqual([c.uid for c in drawn],before)
        self.assertEqual([c.uid for c in self.g.zone_cards('hand')],before)

    def test_156_negative_draw_count_is_atomic(self):
        with self.assertRaises(ZoneError): self.g.draw(-1)
        self.assertEqual(len(self.g.zone_cards('library')),99)

    def test_157_empty_library_draw_fails_no_fabricated_hand_cards(self):
        self.g.draw(99)
        self.assertEqual(len(self.g.zone_cards('hand')),99)
        self.assertEqual(self.g.draw(),())
        self.assertEqual(self.g.failed_draws,1)
        self.assertEqual(len(self.g.zone_cards('hand')),99)
        self.assertEqual(len(self.g.cards),101)

    def test_158_draw_past_end_only_records_attempts(self):
        drawn=self.g.draw(102)
        self.assertEqual(len(drawn),99)
        self.assertEqual(self.g.failed_draws,3)
        self.assertTrue(self.g.assert_integrity())

    def test_159_identical_seed_identical_shuffled_order(self):
        a=DeckZones(seed=22);b=DeckZones(seed=22)
        a.shuffle_library();b.shuffle_library()
        self.assertEqual([c.uid for c in a.zone_cards('library')],
                         [c.uid for c in b.zone_cards('library')])

    def test_160_different_seed_changes_order_but_not_multiset(self):
        a=DeckZones(seed=22);b=DeckZones(seed=23)
        a.shuffle_library();b.shuffle_library()
        self.assertNotEqual([c.uid for c in a.zone_cards('library')],
                            [c.uid for c in b.zone_cards('library')])
        self.assertEqual(Counter(c.name for c in a.zone_cards('library')),
                         Counter(c.name for c in b.zone_cards('library')))

    def test_161_search_any_card_moves_uid_then_shuffles_98(self):
        chosen=self.first('Demonic Tutor')
        result=self.g.search_library(selected_uid=chosen.uid,destination='hand')
        self.assertIs(result,chosen)
        self.assertEqual(result.zone,'hand')
        self.assertNotIn(chosen.uid,[x.uid for x in self.g.zone_cards('library')])
        self.assertEqual(len(self.g.zone_cards('library')),98)
        self.assertIn(('library_shuffled',98),self.g.trace)
        self.assertTrue(self.g.assert_integrity())

    def test_162_mandatory_unrestricted_search_cannot_decline(self):
        before=tuple(c.uid for c in self.g.zone_cards('library'))
        with self.assertRaises(ZoneError):
            self.g.search_library(selected_uid=None,destination='hand')
        self.assertEqual(before,tuple(c.uid for c in self.g.zone_cards('library')))
        self.assertEqual(self.g.trace,[])

    def test_163_hidden_qualified_search_can_fail_and_still_shuffle(self):
        result=self.g.search_library(selected_uid=None,destination='battlefield',
                                     eligible='basic')
        self.assertIsNone(result)
        self.assertEqual(len(self.g.zone_cards('library')),99)
        self.assertEqual(len(self.g.zone_cards('battlefield')),0)
        self.assertIn(('library_shuffled',99),self.g.trace)

    def test_164_selecting_nonbasic_as_basic_rejected_atomically(self):
        x=self.first('Overgrown Tomb')
        with self.assertRaises(ZoneError):
            self.g.search_library(selected_uid=x.uid,destination='battlefield',eligible='basic')
        self.assertEqual(x.zone,'library')
        self.assertEqual(self.g.trace,[])

    def test_165_basic_land_search_to_battlefield_tapped(self):
        x=self.first('Forest')
        self.g.search_library(selected_uid=x.uid,destination='battlefield',eligible='basic',tapped=True)
        self.assertTrue(x.tapped)
        self.assertEqual(x.zone,'battlefield')
        self.assertEqual(x.controller,0)
        self.assertEqual(len(self.g.zone_cards('library')),98)
        self.assertTrue(self.g.assert_integrity())

    def test_166_basic_forest_search_rejects_swamp(self):
        x=self.first('Swamp')
        with self.assertRaises(ZoneError):
            self.g.search_library(selected_uid=x.uid,destination='battlefield',eligible='basic_forest')
        self.assertEqual(x.zone,'library')
        self.assertEqual(self.g.trace,[])

    def test_167_basic_forest_search_can_enter_untapped(self):
        x=self.first('Forest')
        self.g.search_library(selected_uid=x.uid,destination='battlefield',eligible='basic_forest')
        self.assertFalse(x.tapped)
        self.assertEqual(x.zone,'battlefield')

    def test_168_search_fails_if_uid_no_longer_in_library(self):
        x=self.first('Forest');self.g.move(x.uid,'hand')
        with self.assertRaises(ZoneError):
            self.g.search_library(selected_uid=x.uid,destination='battlefield',eligible='basic')
        self.assertEqual(x.zone,'hand')

    def test_169_nonbasic_forest_search_rejects_unverified_etb(self):
        x=self.first('Overgrown Tomb')
        with self.assertRaises(UnsupportedZoneMechanic):
            self.g.search_library(selected_uid=x.uid,destination='battlefield',eligible='any')
        self.assertEqual(x.zone,'library')
        self.assertEqual(self.g.trace,[])

    def test_170_mill_moves_real_top_cards_to_graveyard(self):
        uids=[c.uid for c in self.g.zone_cards('library')[:3]]
        milled=self.g.mill(3)
        self.assertEqual([c.uid for c in milled],uids)
        self.assertEqual([c.uid for c in self.g.zone_cards('graveyard')],uids)
        self.assertTrue(self.g.assert_integrity())

    def test_171_mill_past_empty_does_not_count_as_failed_draw(self):
        milled=self.g.mill(200)
        self.assertEqual(len(milled),99)
        self.assertEqual(self.g.failed_draws,0)
        self.assertEqual(len(self.g.zone_cards('graveyard')),99)

    def test_172_discard_moves_one_card_not_a_counter(self):
        x=self.g.draw()[0]
        self.g.discard(x.uid)
        self.assertEqual(x.zone,'graveyard')
        self.assertEqual(len(self.g.zone_cards('hand')),0)

    def test_173_cannot_discard_from_library(self):
        x=self.g.zone_cards('library')[0]
        with self.assertRaises(ZoneError):self.g.discard(x.uid)
        self.assertEqual(x.zone,'library')

    def test_174_move_from_graveyard_to_hand_keeps_original_uid(self):
        x=self.g.draw()[0];self.g.discard(x.uid)
        self.g.move(x.uid,'hand')
        self.assertEqual(x.zone,'hand')
        self.assertEqual(self.g.zone_cards('hand')[0].uid,x.uid)

    def test_175_token_created_on_battlefield_not_from_library(self):
        original_count=len(self.g.cards)
        t=self.g.create_battlefield_token('ordinary Pest')
        self.assertTrue(t.token)
        self.assertEqual(len(self.g.zone_cards('library')),99)
        self.assertEqual(len(self.g.cards),original_count+1)
        self.assertTrue(self.g.assert_integrity())

    def test_176_dead_token_vanishes_not_in_graveyard_or_library(self):
        t=self.g.create_battlefield_token('ordinary Pest')
        self.g.move(t.uid,'graveyard')
        self.assertNotIn(t.uid,self.g.cards)
        self.assertEqual(len(self.g.zone_cards('graveyard')),0)
        self.assertIn(('token_ceases',t.uid,t.name),self.g.trace)
        self.assertTrue(self.g.assert_integrity())

    def test_177_token_exile_does_not_become_retrievable(self):
        t=self.g.create_battlefield_token('Hunger Tide Insect')
        self.g.move(t.uid,'exile')
        self.assertNotIn(t.uid,self.g.cards)
        self.assertEqual(len(self.g.zone_cards('exile')),0)

    def test_178_lesson_default_not_retrievable(self):
        with self.assertRaises(ZoneError):self.g.learn_pest_summoning()
        self.assertEqual(len(self.g.zone_cards('outside_game')),1)

    def test_179_house_rule_lesson_moves_once_without_added_card(self):
        g=DeckZones(seed=17,learn_sideboard_allowed=True)
        old=len(g.cards)
        x=g.learn_pest_summoning()
        self.assertEqual(x.name,'Pest Summoning')
        self.assertEqual(x.zone,'hand')
        self.assertEqual(len(g.cards),old)
        self.assertEqual(len(g.zone_cards('outside_game')),0)
        self.assertTrue(g.assert_integrity())
        with self.assertRaises(ZoneError):g.learn_pest_summoning()

    def test_180_generic_move_cannot_extract_lesson_without_rule(self):
        x=self.g.zone_cards('outside_game')[0]
        with self.assertRaises(ZoneError):self.g.move(x.uid,'hand')
        self.assertEqual(x.zone,'outside_game')

    def test_181_basic_forest_land_play_requires_hand(self):
        x=self.first('Forest')
        with self.assertRaises(ZoneError):self.g.play_land(x.uid)
        self.assertEqual(x.zone,'library')

    def test_182_basic_forest_land_play_and_mana_tap(self):
        x=self.first('Forest');self.g.move(x.uid,'hand')
        self.g.play_land(x.uid)
        self.assertFalse(x.tapped)
        self.assertEqual(self.g.tap_land_for_mana(x.uid),'G')
        self.assertTrue(x.tapped)
        self.assertEqual(self.g.mana_pool,['G'])

    def test_183_basic_swamp_mana_black_not_green(self):
        x=self.first('Swamp');self.g.move(x.uid,'hand');self.g.play_land(x.uid)
        with self.assertRaises(ZoneError):self.g.tap_land_for_mana(x.uid,color='G')
        self.assertFalse(x.tapped)
        self.assertEqual(self.g.tap_land_for_mana(x.uid),'B')

    def test_184_command_tower_uses_only_savra_identity_colors(self):
        x=self.first('Command Tower');self.g.move(x.uid,'hand');self.g.play_land(x.uid)
        with self.assertRaises(ZoneError):self.g.tap_land_for_mana(x.uid,color='W')
        self.assertFalse(x.tapped)
        self.assertEqual(self.g.tap_land_for_mana(x.uid,color='B'),'B')

    def test_185_land_not_tapped_twice_in_same_turn(self):
        x=self.first('Forest');self.g.move(x.uid,'hand');self.g.play_land(x.uid)
        self.g.tap_land_for_mana(x.uid)
        with self.assertRaises(ZoneError):self.g.tap_land_for_mana(x.uid)
        self.assertEqual(self.g.mana_pool,['G'])

    def test_186_only_one_land_play_per_fixture_turn(self):
        a=self.first('Swamp');b=self.first('Forest')
        self.g.move(a.uid,'hand');self.g.move(b.uid,'hand')
        self.g.play_land(a.uid)
        with self.assertRaises(ZoneError):self.g.play_land(b.uid)
        self.assertEqual(b.zone,'hand')
        self.g.new_turn();self.g.play_land(b.uid)
        self.assertEqual(b.zone,'battlefield')

    def test_187_land_play_requires_main_phase_empty_stack(self):
        a=self.first('Swamp');self.g.move(a.uid,'hand')
        with self.assertRaises(ZoneError):self.g.play_land(a.uid,main_phase=False)
        with self.assertRaises(ZoneError):self.g.play_land(a.uid,stack_empty=False)
        self.assertEqual(self.g.land_plays_this_turn,0)
        self.assertEqual(a.zone,'hand')

    def test_188_nonbasic_land_etb_unimplemented_does_not_silently_enter(self):
        x=self.first('Overgrown Tomb');self.g.move(x.uid,'hand')
        with self.assertRaises(UnsupportedZoneMechanic):self.g.play_land(x.uid)
        self.assertEqual(x.zone,'hand')
        self.assertEqual(self.g.land_plays_this_turn,0)

    def test_189_untap_partial_turn_refreshes_controlled_only(self):
        x=self.first('Forest');self.g.move(x.uid,'hand');self.g.play_land(x.uid)
        self.g.tap_land_for_mana(x.uid)
        other=self.g.create_battlefield_token('test opponent token',controller=1)
        other.tapped=True
        self.g.new_turn()
        self.assertFalse(x.tapped)
        self.assertTrue(other.tapped)

    def test_190_reject_nonland_play_as_land(self):
        x=self.first('Demonic Tutor');self.g.move(x.uid,'hand')
        with self.assertRaises(ZoneError):self.g.play_land(x.uid)
        self.assertEqual(x.zone,'hand')

    def test_191_exile_physical_card_retains_unique_identity(self):
        x=self.g.draw()[0];uid=x.uid
        self.g.move(uid,'exile')
        self.assertEqual(x.zone,'exile')
        self.assertEqual(self.g.zone_cards('exile')[0].uid,uid)
        self.assertTrue(self.g.assert_integrity())

    def test_192_return_to_top_or_bottom_preserves_order(self):
        a,b=self.g.draw(2)
        self.g.move(a.uid,'library',top=True)
        self.assertEqual(self.g.zone_cards('library')[0].uid,a.uid)
        self.g.move(b.uid,'library',bottom=True)
        self.assertEqual(self.g.zone_cards('library')[-1].uid,b.uid)

    def test_193_cannot_put_noncommander_in_command_zone(self):
        x=self.g.draw()[0]
        with self.assertRaises(ZoneError):self.g.move(x.uid,'command')
        self.assertEqual(x.zone,'hand')

    def test_194_commander_move_command_to_battlefield_requires_controller(self):
        x=self.g.zone_cards('command')[0]
        with self.assertRaises(ZoneError):self.g.move(x.uid,'battlefield')
        self.g.move(x.uid,'battlefield',controller=0)
        self.assertEqual(x.zone,'battlefield')
        self.g.move(x.uid,'command')
        self.assertEqual(x.zone,'command')
        self.assertEqual(x.owner,0)
        self.assertIsNone(x.controller)
        self.assertTrue(self.g.assert_integrity())

    def test_195_wrong_color_requests_do_not_tap_land_or_make_mana(self):
        x=self.first('Forest');self.g.move(x.uid,'hand');self.g.play_land(x.uid)
        with self.assertRaises(ZoneError):self.g.tap_land_for_mana(x.uid,color='C')
        self.assertFalse(x.tapped)
        self.assertEqual(self.g.mana_pool,[])

    def test_196_search_destination_with_tapped_flag_must_be_battlefield(self):
        x=self.first('Forest')
        with self.assertRaises(ZoneError):
            self.g.search_library(selected_uid=x.uid,destination='hand',tapped=True)
        self.assertEqual(x.zone,'library')

    def test_198_tutor_resolution_returns_unique_selected_card_not_random_draw(self):
        x=self.first('Skullclamp')
        result=self.g.resolve_demonic_tutor(x.uid)
        self.assertIs(result,x)
        self.assertEqual(x.zone,'hand')
        self.assertEqual(len(self.g.zone_cards('library')),98)
        self.assertEqual(self.g.failed_draws,0)
        self.assertIn(('demonic_tutor_resolved',x.uid),self.g.trace)

    def test_199_tutor_cannot_select_card_already_in_hand(self):
        x=self.g.draw()[0]
        state=tuple(c.uid for c in self.g.zone_cards('library'))
        with self.assertRaises(ZoneError):self.g.resolve_demonic_tutor(x.uid)
        self.assertEqual(tuple(c.uid for c in self.g.zone_cards('library')),state)

    def test_200_tutor_cannot_select_outside_game_lesson(self):
        x=self.g.zone_cards('outside_game')[0]
        with self.assertRaises(ZoneError):self.g.resolve_demonic_tutor(x.uid)
        self.assertEqual(x.zone,'outside_game')

    def test_201_tutor_cannot_fail_to_find_with_nonempty_library(self):
        with self.assertRaises(ZoneError):self.g.resolve_demonic_tutor(None)
        self.assertEqual(len(self.g.zone_cards('library')),99)
        self.assertEqual(self.g.trace,[])

    def test_202_tutor_empty_library_search_returns_none_shuffles(self):
        self.g.draw(99)
        self.assertIsNone(self.g.resolve_demonic_tutor(None))
        self.assertEqual(len(self.g.zone_cards('hand')),99)
        self.assertIn(('library_shuffled',0),self.g.trace)
        self.assertIn(('demonic_tutor_resolved',None),self.g.trace)

    def test_203_tutor_cannot_select_a_pest_token(self):
        x=self.g.create_battlefield_token('ordinary Pest')
        with self.assertRaises(ZoneError):self.g.resolve_demonic_tutor(x.uid)
        self.assertEqual(x.zone,'battlefield')

    def test_204_optional_qualified_forest_search_can_fail_with_forests_still_present(self):
        self.assertGreater(sum(c.name=='Forest' for c in self.g.zone_cards('library')),0)
        self.assertIsNone(self.g.search_library(selected_uid=None,
                           destination='battlefield',eligible='basic_forest'))
        self.assertEqual(len(self.g.zone_cards('library')),99)

    def test_205_qualified_search_can_fail_when_no_qualified_cards_remain(self):
        forests=[c for c in self.g.zone_cards('library') if c.name=='Forest']
        for c in forests:self.g.move(c.uid,'hand')
        self.assertIsNone(self.g.search_library(selected_uid=None,
                           destination='battlefield',eligible='basic_forest'))
        self.assertEqual(len(self.g.zone_cards('battlefield')),0)

    def test_197_zone_integrity_rechecks_after_mixed_fixture_ops(self):
        self.g.shuffle_library()
        a,b,c=self.g.draw(3)
        self.g.discard(a.uid)
        self.g.move(b.uid,'exile')
        self.g.move(c.uid,'library',bottom=True)
        t=self.g.create_battlefield_token('ordinary Pest')
        self.g.move(t.uid,'graveyard')
        self.assertTrue(self.g.assert_integrity())
        self.assertEqual(len(self.g.cards),101)

if __name__=='__main__':unittest.main()
