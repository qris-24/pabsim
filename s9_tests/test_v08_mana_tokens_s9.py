"""S9-corrected versioned copy of tests/test_v08_mana_tokens.py.

ONLY tests 274 and 307 differ from the frozen original: Blooming Marsh and Overgrown
Tomb are playable on the bridge since S9 (pab_lands_s9.py), so the two fail-closed
probes become positive plays with the card's printed entry condition; everything else
is byte-for-byte the frozen fixture. The frozen original is untouched and still
asserts fail-closed. Run against pab_kernel.PhysicalZoneGame.
"""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_zone_bridge_v08 import BridgeError
from pab_kernel import PhysicalZoneGame   # promoted kernel replaces the frozen v0.8 bridge
from pab_zones import ZoneError, UnsupportedZoneMechanic, DeckZones
from pab_focus_engine import (PEST, MOSEO_PEST, INSECT, SQUIRREL, TREASURE,
                              HUMAN, SAVRA, IllegalAction)

class Phase8ManaTokens(unittest.TestCase):
    def setUp(self):
        self.g=PhysicalZoneGame(seed=808)
    def one(self,name,zone='library'):
        return next(c for c in self.g.zones.zone_cards(zone) if c.name==name)
    def hand(self,name):
        c=self.one(name);self.g.zones.move(c.uid,'hand');return c
    def land(self,name):
        c=self.hand(name)
        return self.g.play_physical_land(c.uid)
    def assert_integrity(self):
        self.assertTrue(self.g.assert_bridge_integrity())
        self.assertIs(self.g.mana_pool,self.g.zones.mana_pool)
    def tokens(self,kind=None):
        return [p for p in self.g.permanents.values() if p.token and (kind is None or p.token==kind)]
    def test_258_initial_pool_is_single_shared_object(self):
        self.assert_integrity();self.assertEqual(self.g.mana_pool,[])
    def test_259_manual_mana_add_is_shared(self):
        self.g.add_mana('B','C');self.assertEqual(self.g.zones.mana_pool,['B','C']);self.assert_integrity()
    def test_260_atomic_failed_payment_preserves_alias(self):
        self.g.add_mana('C','C')
        with self.assertRaises(IllegalAction):self.g.pay_mana(black=1,generic=1)
        self.assertEqual(self.g.zones.mana_pool,['C','C']);self.assert_integrity()
    def test_261_payment_rebinds_shared_pool(self):
        self.g.add_mana('B','G','C');self.g.pay_mana(black=1,green=1,generic=1)
        self.assertEqual(self.g.mana_pool,[]);self.assert_integrity()
    def test_262_seeded_existing_pool_is_adopted(self):
        z=DeckZones(seed=4);z.mana_pool.extend(('G','C'))
        g=PhysicalZoneGame(zones=z)
        self.assertIs(g.mana_pool,z.mana_pool);self.assertEqual(g.mana_pool,['G','C'])
    def test_263_physical_forest_enters_untapped_and_links(self):
        p=self.land('Forest');self.assertEqual(self.g.zones.cards[self.g.linked_battlefield[p.uid]].zone,'battlefield')
        self.assertFalse(p.tapped);self.assert_integrity()
    def test_264_physical_forest_adds_only_green(self):
        p=self.land('Forest')
        self.assertEqual(self.g.tap_physical_land_for_mana(p.uid),'G')
        self.assertEqual(self.g.mana_pool,['G']);self.assertTrue(p.tapped);self.assert_integrity()
    def test_265_physical_swamp_adds_only_black(self):
        p=self.land('Swamp')
        self.assertEqual(self.g.tap_physical_land_for_mana(p.uid),'B');self.assert_integrity()
    def test_266_command_tower_black_selection(self):
        p=self.land('Command Tower')
        self.assertEqual(self.g.tap_physical_land_for_mana(p.uid,color='B'),'B');self.assert_integrity()
    def test_267_command_tower_green_selection(self):
        p=self.land('Command Tower')
        self.assertEqual(self.g.tap_physical_land_for_mana(p.uid,color='G'),'G');self.assert_integrity()
    def test_268_command_tower_requires_selected_color(self):
        p=self.land('Command Tower')
        with self.assertRaises(ZoneError):self.g.tap_physical_land_for_mana(p.uid)
        self.assertFalse(p.tapped);self.assertEqual(self.g.mana_pool,[])
    def test_269_forest_rejects_black_without_tapping(self):
        p=self.land('Forest')
        with self.assertRaises(ZoneError):self.g.tap_physical_land_for_mana(p.uid,color='B')
        self.assertFalse(p.tapped);self.assert_integrity()
    def test_270_second_tap_rejected_without_extra_mana(self):
        p=self.land('Swamp');self.g.tap_physical_land_for_mana(p.uid)
        with self.assertRaises(ZoneError):self.g.tap_physical_land_for_mana(p.uid)
        self.assertEqual(self.g.mana_pool,['B']);self.assert_integrity()
    def test_271_physical_land_play_rejects_second_play(self):
        self.land('Forest');second=self.hand('Swamp')
        with self.assertRaises(ZoneError):self.g.play_physical_land(second.uid)
        self.assertEqual(self.g.zones.cards[second.uid].zone,'hand');self.assert_integrity()
    def test_272_land_play_rejects_wrong_phase(self):
        card=self.hand('Forest')
        with self.assertRaises(ZoneError):self.g.play_physical_land(card.uid,main_phase=False)
        self.assertEqual(self.g.zones.cards[card.uid].zone,'hand')
    def test_273_land_play_rejects_nonempty_stack(self):
        card=self.hand('Forest')
        with self.assertRaises(ZoneError):self.g.play_physical_land(card.uid,stack_empty=False)
        self.assertEqual(self.g.zones.cards[card.uid].zone,'hand')
    def test_274_unsupported_land_fails_closed(self):
        card=self.hand('Blooming Marsh')                       # S9: playable; enters untapped with <= 2 other lands
        p=self.g.play_physical_land(card.uid)
        self.assertEqual(self.g.zones.cards[card.uid].zone,'battlefield');self.assertFalse(p.tapped);self.assert_integrity()
    def test_275_land_tap_rejects_unlinked_fixture(self):
        p=self.g.add('Forest',colors='',creature=False)
        with self.assertRaises(BridgeError):self.g.tap_physical_land_for_mana(p.uid)
    def test_276_natures_lore_uses_mana_generated_by_real_lands(self):
        forest=self.land('Forest');self.g.tap_physical_land_for_mana(forest.uid)
        self.g.add_mana('C')
        second=next(c for c in self.g.zones.zone_cards('library') if c.name=='Forest')
        self.g.natures_lore_physical(selected_land_uid=second.uid);self.g.resolve()
        self.assertEqual(self.g.zones.cards[second.uid].zone,'battlefield')
        self.assertFalse(self.g.zones.cards[second.uid].tapped)
        self.assertEqual(self.g.mana_pool,[]);self.assert_integrity()
    def test_277_rock_produced_mana_in_shared_pool(self):
        ring=self.g.add('Sol Ring',creature=False,artifact=True)
        self.g.tap_mana_rock(ring.uid)
        self.assertEqual(self.g.zones.mana_pool,['C','C']);self.assert_integrity()
    def test_278_signet_consumes_existing_mana_and_returns_BG(self):
        ring=self.g.add('Sol Ring',creature=False,artifact=True)
        signet=self.g.add('Golgari Signet',creature=False,artifact=True)
        self.g.tap_mana_rock(ring.uid);self.g.tap_mana_rock(signet.uid)
        self.assertEqual(self.g.mana_pool,['C','B','G']);self.assert_integrity()
    def test_279_altar_mana_shared_after_token_sacrifice(self):
        self.g.add('Phyrexian Altar',creature=False,artifact=True)
        pest=self.g.make_tokens(PEST)[0]
        self.g.phyrexian_altar_sacrifice(pest.uid,'G')
        self.assertEqual(self.g.mana_pool,['G']);self.assert_integrity()
    def test_280_physical_basic_search_tapped_rejects_mana(self):
        elder=self.g.add('Sakura-Tribe Elder');selected=self.one('Swamp')
        self.g.sakura_tribe_elder_physical(elder.uid,selected_land_uid=selected.uid);self.g.resolve()
        event_id=next(k for k,v in self.g.linked_battlefield.items() if v==selected.uid)
        with self.assertRaises(ZoneError):self.g.tap_physical_land_for_mana(event_id)
        self.assertEqual(self.g.mana_pool,[]);self.assert_integrity()
    def test_281_fixture_turn_resets_land_count_and_tapped_state(self):
        first=self.land('Forest');self.g.tap_physical_land_for_mana(first.uid)
        self.g.fixture_new_turn();self.assertFalse(first.tapped)
        self.assertEqual(self.g.tap_physical_land_for_mana(first.uid),'G')
        other=self.hand('Swamp');self.g.play_physical_land(other.uid)
        self.assert_integrity()
    def test_282_refuses_to_hide_mana_alias_mutation(self):
        self.g.mana_pool=['B']
        with self.assertRaises(AssertionError):self.g.assert_bridge_integrity()
    def test_283_real_tokens_have_distinct_physical_uids(self):
        ps=self.g.make_tokens(PEST,3)
        ids=[self.g.linked_tokens[p.uid] for p in ps]
        self.assertEqual(len(set(ids)),3);self.assert_integrity()
    def test_284_token_identity_is_separate_from_frozen_mainboard(self):
        before=len(self.g.zones.zone_cards('library'))
        self.g.make_tokens(PEST,4)
        self.assertEqual(len(self.g.zones.zone_cards('library')),before)
        self.assertEqual(len(self.g.zones.cards),105);self.assert_integrity() # 101 + 4
    def test_285_token_positive_creation_zero_no_effect(self):
        self.assertEqual(self.g.make_tokens(PEST,0),[])
        self.assertEqual(self.g.linked_tokens,{});self.assert_integrity()
    def test_286_negative_token_creation_has_no_effect(self):
        with self.assertRaises(IllegalAction):self.g.make_tokens(PEST,-1)
        self.assertEqual(self.g.linked_tokens,{});self.assert_integrity()
    def test_287_ordinary_pest_sacrifice_savra_two_separate_triggers(self):
        self.g.add(SAVRA);p=self.g.make_tokens(PEST)[0]
        self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.life[0],41) # -2 black, +2 green, +1 Pest death
        self.assertEqual(self.g.edict_opportunities,1)
        self.assertEqual(self.g.opponent_sacrifices,0)
        self.assertEqual(self.g.linked_tokens,{});self.assert_integrity()
    def test_288_ordinary_pest_dies_no_savra_triggers(self):
        self.g.add(SAVRA);p=self.g.make_tokens(PEST)[0]
        self.g.destroy(p.uid);self.g.resolve()
        self.assertEqual(self.g.edict_opportunities,0)
        self.assertEqual(self.g.life[0],41) # death gain, no sacrifice gain
        self.assert_integrity()
    def test_289_pest_dies_gain_once_physically_disappears(self):
        p=self.g.make_tokens(PEST)[0];physical_uid=self.g.linked_tokens[p.uid]
        self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.life[0],41)
        self.assertNotIn(physical_uid,self.g.zones.cards)
        self.assertNotIn(physical_uid,self.g.zones.zones['graveyard'])
        self.assert_integrity()
    def test_290_moseo_pest_no_death_gain(self):
        p=self.g.make_tokens(MOSEO_PEST)[0]
        self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.life[0],40);self.assert_integrity()
    def test_291_hunger_tide_insect_bg_savra_not_pest_gain(self):
        self.g.add(SAVRA);p=self.g.make_tokens(INSECT)[0]
        self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.life[0],40)
        self.assertEqual(self.g.edict_opportunities,1);self.assert_integrity()
    def test_292_chatterfang_additional_squirrels_have_green_only(self):
        self.g.add('Chatterfang, Squirrel General')
        self.g.make_tokens(PEST,2)
        self.assertEqual(len(self.tokens(PEST)),2)
        self.assertEqual(len(self.tokens(SQUIRREL)),2)
        self.assertEqual(len(self.g.linked_tokens),4);self.assert_integrity()
    def test_293_squirrel_sacrifice_green_savra_only(self):
        self.g.add(SAVRA);self.g.add('Chatterfang, Squirrel General')
        ps=self.g.make_tokens(PEST);s=next(p for p in self.tokens() if p.token==SQUIRREL)
        self.g.sacrifice(s.uid);self.g.resolve()
        self.assertEqual(self.g.life[0],42);self.assertEqual(self.g.edict_opportunities,0)
        self.assertEqual(len(self.g.linked_tokens),1);self.assert_integrity()
    def test_294_pest_rescuer_modifies_single_gain_event(self):
        self.g.add('Pest Rescuer');p=self.g.make_tokens(PEST)[0]
        self.g.destroy(p.uid);self.g.resolve()
        self.assertEqual(self.g.life[0],42);self.assert_integrity()
    def test_295_mirkwood_bats_drain_on_token_creation(self):
        self.g.add('Mirkwood Bats');self.g.make_tokens(PEST,2);self.g.resolve()
        self.assertEqual(self.g.life[1:], [38,38,38]);self.assert_integrity()
    def test_296_mirkwood_bats_drain_on_token_sacrifice_not_destruction(self):
        self.g.add('Mirkwood Bats');ps=self.g.make_tokens(PEST,2);self.g.resolve()
        self.g.destroy(ps[0].uid);self.g.sacrifice(ps[1].uid);self.g.resolve()
        self.assertEqual(self.g.life[1:], [37,37,37]);self.assert_integrity()
    def test_297_token_treasure_is_artifact_not_creature(self):
        p=self.g.make_tokens(TREASURE)[0]
        self.assertFalse(p.creature);self.assertTrue(p.artifact)
        self.assertTrue(self.g.zones.cards[self.g.linked_tokens[p.uid]].token)
        self.assert_integrity()
    def test_298_treasure_cannot_trigger_savra_creature_sacrifice(self):
        self.g.add(SAVRA);p=self.g.make_tokens(TREASURE)[0]
        self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.edict_opportunities,0);self.assert_integrity()
    def test_299_token_cannot_be_reanimated_as_card(self):
        p=self.g.make_tokens(PEST)[0];self.g.destroy(p.uid);self.g.resolve()
        self.assertFalse(any(c.token for c in self.g.zones.zone_cards('graveyard')))
        self.assertFalse(any(g.uid==p.uid for g in self.g.graveyard))
    def test_300_multiple_token_batches_preserve_distinct_identity(self):
        first=self.g.make_tokens(PEST,2);second=self.g.make_tokens(PEST,2)
        self.assertEqual(len(self.g.linked_tokens),4)
        self.g.destroy(first[0].uid);self.g.resolve()
        self.assertEqual(len(self.g.linked_tokens),3);self.assert_integrity()
    def test_301_bastion_human_token_white_no_savra(self):
        self.g.add(SAVRA);self.g.add('Bastion of Remembrance')
        human=self.tokens(HUMAN)[0]
        self.g.sacrifice(human.uid);self.g.resolve()
        self.assertEqual(self.g.edict_opportunities,0);self.assert_integrity()
    def test_302_learn_hunt_pest_and_lesson_distinct_physical(self):
        g=PhysicalZoneGame(learn_sideboard_allowed=True)
        g.hunt_for_specimens(lesson=True)
        self.assertEqual(sum(c.name=='Pest Summoning' for c in g.zones.zone_cards('hand')),1)
        self.assertEqual(len(g.linked_tokens),1);self.assertTrue(g.assert_bridge_integrity())
    def test_303_linked_real_creature_and_token_mappings_disjoint(self):
        card=self.hand('Reassembling Skeleton')
        p=self.g.enter_linked_creature(card.uid,mana_value=2)
        token=self.g.make_tokens(PEST)[0]
        self.assertNotEqual(self.g.linked_battlefield[p.uid],self.g.linked_tokens[token.uid])
        self.g.sacrifice(token.uid);self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.zones.cards[card.uid].zone,'graveyard')
        self.assert_integrity()
    def test_304_wrong_manual_token_zone_mutation_detected(self):
        p=self.g.make_tokens(PEST)[0];uid=self.g.linked_tokens[p.uid]
        self.g.zones.move(uid,'graveyard')
        with self.assertRaises(AssertionError):self.g.assert_bridge_integrity()
    def test_305_disjoint_multiple_sources_and_physical_draws(self):
        self.g.add(SAVRA);self.g.add('Moldervine Reclamation')
        ps=self.g.make_tokens(PEST,2)
        for p in ps:self.g.sacrifice(p.uid)
        self.g.resolve()
        self.assertEqual(self.g.cards_drawn,2)
        self.assertEqual(len(self.g.zones.zone_cards('hand')),2)
        self.assert_integrity()
    def test_306_zero_mana_colorless_cannot_pay_green(self):
        ring=self.g.add('Sol Ring',creature=False,artifact=True)
        self.g.tap_mana_rock(ring.uid)
        with self.assertRaises(IllegalAction):self.g.pay_mana(green=1)
        self.assert_integrity()
    def test_307_unsupported_named_nonbasic_mana_does_not_fallback(self):
        card=self.one('Overgrown Tomb');self.g.zones.move(card.uid,'hand')   # S9: playable; no payment -> enters tapped
        p=self.g.play_physical_land(card.uid)
        self.assertTrue(p.tapped);self.assertEqual(self.g.life[0],40);self.assert_integrity()
    def test_308_pest_token_after_life_drain_has_no_phantom_card_count(self):
        self.g.add(SAVRA);self.g.add('Dina, Soul Steeper')
        base=len(self.g.zones.cards);p=self.g.make_tokens(PEST)[0]
        self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(len(self.g.zones.cards),base);self.assert_integrity()
    def test_309_token_creation_does_not_count_as_draw(self):
        self.g.make_tokens(PEST,5)
        self.assertEqual(self.g.cards_drawn,0)
        self.assertEqual(len(self.g.zones.zone_cards('hand')),0);self.assert_integrity()
    def test_310_token_no_savra_sacrifice_when_savra_absent(self):
        p=self.g.make_tokens(PEST)[0];self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.edict_opportunities,0);self.assert_integrity()
    def test_311_real_land_and_savra_trigger_token_with_shared_mana(self):
        land=self.land('Swamp');self.g.tap_physical_land_for_mana(land.uid)
        self.g.add(SAVRA);p=self.g.make_tokens(PEST)[0]
        self.g.sacrifice(p.uid);self.g.resolve()
        self.assertEqual(self.g.mana_pool,['B']);self.assertEqual(self.g.edict_opportunities,1)
        self.assert_integrity()
