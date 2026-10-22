"""CP06 independent migration checks; a cast spell is in the physical stack, not hand."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))   # CP42 (T6): imports work without the runner's sys.path
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_cast_s6 import check_invariants_s6
from pab_focus_engine import PEST, SAVRA
from pab_zones import ZoneError
from pab_zone_bridge import BridgeError

def pull(g,name):
    uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
    g.zones.search_library(selected_uid=uid,destination='hand')
    return uid

def spells(g):
    return tuple(g.zones.zones['stack'])

class StackMigration(unittest.TestCase):
    def test_layer_promoted_and_empty_at_start(self):
        g=PhysicalZoneGame()
        self.assertIn('+CP06',KERNEL_VERSION); self.assertIn('CP06',PROMOTED)
        self.assertEqual(spells(g),()); self.assertEqual(g.stack_cards,{})
        check_invariants_s6(g)

    def test_village_rites_leave_hand_at_cast_not_at_resolution(self):
        g=PhysicalZoneGame(); p=g.make_tokens(PEST)[0]; g.resolve()
        uid=pull(g,'Village Rites'); g.add_mana('B')
        g.cast_from_hand(uid,sacrifice_uid=p.uid)
        self.assertNotIn(uid,g.zones.zones['hand']); self.assertEqual(spells(g),(uid,))
        self.assertEqual(g.zones.cards[uid].zone,'stack')
        self.assertTrue(any(t[:5]==('zone_move',uid,'Village Rites','hand','stack') for t in g.zones.trace))
        check_invariants_s6(g)
        g.resolve()
        self.assertEqual(spells(g),()); self.assertEqual(g.zones.cards[uid].zone,'graveyard')
        self.assertIn(('zone_move',uid,'Village Rites','stack','graveyard'),g.zones.trace)
        self.assertEqual(g.cards_drawn,2); check_invariants_s6(g)

    def test_cast_creature_from_stack_to_battlefield_same_uid(self):
        g=PhysicalZoneGame(); u=pull(g,'Deathgreeter'); g.add_mana('B')
        g.cast_from_hand(u); self.assertEqual(g.zones.cards[u].zone,'stack')
        g.resolve()
        self.assertEqual(g.zones.cards[u].zone,'battlefield')
        self.assertIn(u,g.linked_battlefield.values())
        self.assertIn(('zone_move',u,'Deathgreeter','stack','battlefield'),g.zones.trace)
        check_invariants_s6(g)

    def test_cast_noncreature_permanent_to_battlefield(self):
        g=PhysicalZoneGame(); u=pull(g,'Sol Ring'); g.add_mana('C')
        g.cast_from_hand(u); self.assertEqual(g.zones.cards[u].zone,'stack')
        g.resolve(); self.assertEqual(g.zones.cards[u].zone,'battlefield'); check_invariants_s6(g)

    def test_spell_with_target_to_graveyard(self):
        g=PhysicalZoneGame(); g.declare_opponent_board(1,[{'name':'Target','power':2,'toughness':2,'mana_value':1}])
        p=next(p.uid for p in g.opponent_creatures(1)); u=pull(g,'Abrupt Decay'); g.add_mana('B','G')
        g.cast_from_hand(u,target_uid=p); self.assertEqual(g.zones.cards[u].zone,'stack')
        g.resolve(); self.assertEqual(g.zones.cards[u].zone,'graveyard'); self.assertNotIn(p,g.permanents); check_invariants_s6(g)

    def test_shigeki_and_grist_enter_from_stack(self):
        for name,mana in [('Shigeki, Jukai Visionary',('G','C')),('Grist, the Hunger Tide',('B','G','C'))]:
            with self.subTest(name=name):
                g=PhysicalZoneGame(); u=pull(g,name); g.add_mana(*mana)
                g.cast_from_hand(u); self.assertEqual(g.zones.cards[u].zone,'stack')
                g.resolve(); self.assertEqual(g.zones.cards[u].zone,'battlefield'); check_invariants_s6(g)

    def test_two_instant_spells_stay_distinct_on_stack(self):
        g=PhysicalZoneGame(); a=pull(g,'Village Rites'); b=pull(g,'Deadly Dispute')
        t1=g.make_tokens(PEST)[0]; t2=g.make_tokens(PEST)[0]; g.resolve(); g.add_mana('B','B','C')
        g.cast_from_hand(a,sacrifice_uid=t1.uid)
        g.cast_from_hand(b,sacrifice_uid=t2.uid)
        self.assertEqual(set(spells(g)),{a,b}); self.assertEqual(len(g.stack_cards),2)
        self.assertNotIn(a,g.zones.zones['hand']); self.assertNotIn(b,g.zones.zones['hand'])
        check_invariants_s6(g); g.resolve(); self.assertEqual(spells(g),())
        resolved=[x[1] for x in g.trace if x[0]=='physical_spell_resolved']
        self.assertEqual(resolved,['Deadly Dispute','Village Rites'])
        self.assertEqual(g.zones.cards[a].zone,'graveyard'); self.assertEqual(g.zones.cards[b].zone,'graveyard')
        check_invariants_s6(g)

    def test_duplicate_cast_rejected_without_spending_second_cost(self):
        g=PhysicalZoneGame(); u=pull(g,'Deathgreeter'); g.add_mana('B','B')
        g.cast_from_hand(u); before=(list(g.mana_pool),list(g.trace),list(spells(g)))
        with self.assertRaises(BridgeError): g.cast_from_hand(u)
        self.assertEqual((g.mana_pool,g.trace,list(spells(g))),before)
        g.resolve(); check_invariants_s6(g)

    def test_rejected_cast_stays_hand_and_no_stack(self):
        g=PhysicalZoneGame(); u=pull(g,'Village Rites'); g.add_mana('B')
        with self.assertRaises(BridgeError): g.cast_from_hand(u,sacrifice_uid=999)
        self.assertEqual(g.zones.cards[u].zone,'hand'); self.assertEqual(spells(g),())
        self.assertEqual(g.mana_pool,['B']); check_invariants_s6(g)

    def test_library_and_battlefield_cannot_move_onto_stack(self):
        g=PhysicalZoneGame()
        lib=g.zones.zones['library'][0]
        with self.assertRaises(ZoneError): g.zones.move(lib,'stack')
        land=pull(g,'Forest')
        with self.assertRaises(ZoneError): g.zones.move(land,'stack')
        self.assertEqual(spells(g),()); check_invariants_s6(g)

    def test_corrupt_stack_detected_by_bridge_integrity(self):
        g=PhysicalZoneGame(); u=pull(g,'Deathgreeter'); g.add_mana('B'); g.cast_from_hand(u)
        g.zones.zones['stack'].remove(u)
        with self.assertRaises(AssertionError): g.assert_bridge_integrity()

    def test_live_stack_card_not_visible_in_hand_search(self):
        g=PhysicalZoneGame(); u=pull(g,'Sol Ring'); g.add_mana('C'); g.cast_from_hand(u)
        self.assertNotIn(u,[c.uid for c in g.zones.zone_cards('hand')])
        with self.assertRaises(ZoneError): g.zones._require_in_zone(u,'hand')
        self.assertEqual([c.uid for c in g.zones.zone_cards('stack')],[u])
        g.resolve(); check_invariants_s6(g)

    def test_source_deck_integrity_and_shared_mana(self):
        g=PhysicalZoneGame()
        self.assertEqual(len(g.zones.zones['library']),99)
        self.assertEqual(len(g.zones.zones['command']),1)
        self.assertEqual(len(g.zones.zones['outside_game']),1)
        self.assertIs(g.mana_pool,g.zones.mana_pool)
        self.assertTrue(g.zones.assert_integrity())

    def test_standalone_s6_mixin_remains_compatible_without_cp06(self):
        from pab_cast_s6 import CastMixin
        from pab_r47_r48_sba import PhysicalZoneGame as LegacyBase
        class LegacyPhysical(CastMixin, LegacyBase):
            pass
        g=LegacyPhysical()
        u=pull(g,'Sakura-Tribe Elder'); g.add_mana('G','C')
        g.cast_from_hand(u)
        self.assertEqual(g.zones.cards[u].zone,'hand')
        g.resolve(); self.assertEqual(g.zones.cards[u].zone,'battlefield')
        self.assertNotIn('stack',g.zones.zones)

    def test_unrelated_frozen_zone_only_game_remains_seven_zones(self):
        from pab_zones import DeckZones,ZONES
        z=DeckZones()
        self.assertEqual(set(z.zones),set(ZONES)); self.assertNotIn('stack',z.zones)
        with self.assertRaises(ZoneError): z.move(z.zones['library'][0],'stack')
