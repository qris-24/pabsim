"""Executable contracts C65–C77 (issues R35–R40, lands) against the promoted kernel.

Land support is Forest {G}, Swamp {B}, Command Tower {B}/{G} (physical bridge)
plus Sol Ring / Arcane Signet / Golgari Signet rocks and basic-only
Nature's Lore / Sakura-Tribe Elder fixtures. The other 18 land names fail
closed. Statuses:
  EXECUTED / EXECUTED_WITH_SUBSTITUTION / PARTIAL_EXECUTED (some expectations
  asserted, the rest blocked) / BLOCKED_UNSUPPORTED (probe asserts ONLY that the
  kernel refuses the card without mutating state — never the contract's
  expectation).
No contract is Oracle/CR-authenticated.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, IllegalAction
from pab_zones import ZoneError, UnsupportedZoneMechanic
from pab_kernel import Game, PhysicalZoneGame

def snapshot(g):
    z=g.zones
    return ({k:tuple(v) for k,v in z.zones.items()}, tuple(sorted(g.permanents)), tuple(g.mana_pool),
            z.land_plays_this_turn, tuple((u,z.cards[u].tapped) for u in z.zones['battlefield']))

class _Land(unittest.TestCase):
    def bridge(self):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve(); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); return uid
    def assert_fails_closed(self,name):
        """Playing NAME must raise UnsupportedZoneMechanic and leave every zone,
        permanent, mana and tap state exactly as before."""
        g=self.bridge(); uid=self.to_hand(g,name); before=snapshot(g)
        with self.assertRaises(UnsupportedZoneMechanic): g.play_physical_land(uid)
        self.assertEqual(snapshot(g),before); g.assert_bridge_integrity()
        self.assertEqual(g.zones.cards[uid].zone,'hand')
        return g


class C65(_Land):
    CONTRACT='C65'; ISSUES=['R35']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Blooming Marsh / Deathcap Glade conditional ETB not modeled; probe asserts fail-closed only']
    def test_blocked_fail_closed(self):
        for n in ('Blooming Marsh','Deathcap Glade'):
            with self.subTest(land=n): self.assert_fails_closed(n)

class C66(_Land):
    CONTRACT='C66'; ISSUES=['R35']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Undergrowth Stadium opponent-count ETB not modeled (no opponent count state); probe asserts fail-closed only']
    def test_blocked_fail_closed(self): self.assert_fails_closed('Undergrowth Stadium')

class C67(_Land):
    CONTRACT='C67'; ISSUES=['R35','R38']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Overgrown Tomb life payment and Underground Mortuary surveil not modeled; probe asserts fail-closed only. '
                   'The Forest control from the contract IS executed.']
    def test_blocked_fail_closed(self):
        for n in ('Overgrown Tomb','Underground Mortuary'):
            with self.subTest(land=n): self.assert_fails_closed(n)
    def test_control_forest_enters_untapped_no_life_change(self):
        g=self.bridge(); uid=self.to_hand(g,'Forest'); p=g.play_physical_land(uid)
        self.assertFalse(p.tapped); self.assertEqual(g.life,[40,40,40,40])
        self.assertEqual(g.zones.land_plays_this_turn,1)
        with self.assertRaises(ZoneError): g.play_physical_land(self.to_hand(g,'Swamp'))   # one land per turn

class C68(_Land):
    CONTRACT='C68'; ISSUES=['R35','R15']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Modal double-faced Pathway face selection not modeled; probe asserts fail-closed only']
    def test_blocked_fail_closed(self): self.assert_fails_closed('Darkbore Pathway // Slitherbore Pathway')

class C69(_Land):
    CONTRACT='C69'; ISSUES=['R36']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['Asserted: basic Forest qualifies, Swamp does not, Forest enters untapped, Sakura basic-only control. '
                   'NOT asserted: Overgrown Tomb / Underground Mortuary qualifying by Forest subtype, and Woodland '
                   'Cemetery / Pathway exclusion — nonbasic Forest-typed search is unmodeled and fails closed']
    def test_event_fixture_forest_qualifies_swamp_rejected(self):
        g=Game(); g.add(SAVRA); g.resolve()
        f=g.put_basic_land_in_fixture_library('Forest'); s=g.put_basic_land_in_fixture_library('Swamp')
        g.add_mana('G','C')
        with self.assertRaises(IllegalAction): g.natures_lore(land_index=s)
        self.assertEqual(g.mana_pool,['G','C'])                    # rejected before payment
        g.natures_lore(land_index=f); g.resolve()
        found=[t for t in g.trace if t[0]=='fixture_basic_land_to_battlefield']
        self.assertEqual(len(found),1); self.assertFalse(g.permanents[found[0][1]].tapped)
    def test_physical_nonbasic_forest_typed_search_fails_closed(self):
        g=self.bridge(); z=g.zones
        tomb=next(u for u in z.zones['library'] if z.cards[u].name=='Overgrown Tomb'); before=snapshot(g)
        with self.assertRaises((ZoneError,UnsupportedZoneMechanic)):
            z.search_library(selected_uid=tomb,destination='battlefield',eligible='basic_forest')
        self.assertEqual(snapshot(g),before)
    def test_physical_basic_forest_search_enters(self):
        g=self.bridge(); z=g.zones
        forest=next(u for u in z.zones['library'] if z.cards[u].name=='Forest')
        z.search_library(selected_uid=forest,destination='battlefield',eligible='basic_forest')
        self.assertEqual(z.cards[forest].zone,'battlefield'); self.assertFalse(z.cards[forest].tapped)
    def test_control_sakura_basic_only(self):
        g=self.bridge(); z=g.zones
        tomb=next(u for u in z.zones['library'] if z.cards[u].name=='Overgrown Tomb')
        with self.assertRaises((ZoneError,UnsupportedZoneMechanic)):
            z.search_library(selected_uid=tomb,destination='battlefield',eligible='basic',tapped=True)
        swamp=next(u for u in z.zones['library'] if z.cards[u].name=='Swamp')
        z.search_library(selected_uid=swamp,destination='battlefield',eligible='basic',tapped=True)
        self.assertTrue(z.cards[swamp].tapped)

class C70(_Land):
    CONTRACT='C70'; ISSUES=['R36','R37','R38']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Verdant Catacombs activation (tap, pay 1 life, sacrifice) and subtype search not modeled; probe asserts fail-closed only']
    def test_blocked_fail_closed(self): self.assert_fails_closed('Verdant Catacombs')

class C71(_Land):
    CONTRACT='C71'; ISSUES=['R37']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Phyrexian Tower sacrifice mana ability not modeled; probe asserts fail-closed only']
    def test_blocked_fail_closed(self): self.assert_fails_closed('Phyrexian Tower')

class C72(_Land):
    CONTRACT='C72'; ISSUES=['R37']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['High Market and Grim Backwoods activations not modeled; probe asserts fail-closed only']
    def test_blocked_fail_closed(self):
        for n in ('High Market','Grim Backwoods'):
            with self.subTest(land=n): self.assert_fails_closed(n)

class C73(_Land):
    CONTRACT='C73'; ISSUES=['R38']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Llanowar Wastes damage and Nurturing Peatland life payment not modeled; probe asserts fail-closed only']
    def test_blocked_fail_closed(self):
        for n in ('Llanowar Wastes','Nurturing Peatland'):
            with self.subTest(land=n): self.assert_fails_closed(n)

class C74(_Land):
    CONTRACT='C74'; ISSUES=['R38']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Castle Locthwain draw-then-lose not modeled; probe asserts fail-closed only']
    def test_blocked_fail_closed(self): self.assert_fails_closed('Castle Locthwain')

class C75(_Land):
    CONTRACT='C75'; ISSUES=['R39']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Channel (discard-from-hand activation with legendary-creature discount) not modeled; probe asserts '
                   'fail-closed for the land play and that no channel API exists']
    def test_blocked_fail_closed(self):
        for n in ('Boseiju, Who Endures','Takenuma, Abandoned Mire'):
            with self.subTest(land=n):
                g=self.assert_fails_closed(n); self.assertFalse(any('channel' in a.lower() for a in dir(g)))

class C76(_Land):
    CONTRACT='C76'; ISSUES=['R40']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Geier Reach Sanitarium / Mikokoro symmetrical draw effects not modeled (no opponent hands/libraries); probe asserts fail-closed only']
    def test_blocked_fail_closed(self):
        for n in ('Geier Reach Sanitarium','Mikokoro, Center of the Sea'):
            with self.subTest(land=n): self.assert_fails_closed(n)

class C77(_Land):
    CONTRACT='C77'; ISSUES=['R40']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['Grim Backwoods {C} not modeled (fails closed). Tower/Forest/Swamp via the physical bridge; Sol Ring via the rock fixture']
    def test_tower_b_or_g_u_rejected(self):
        g=self.bridge(); p=g.play_physical_land(self.to_hand(g,'Command Tower'))
        with self.assertRaises(ZoneError): g.tap_physical_land_for_mana(p.uid,color='U')
        self.assertEqual(g.mana_pool,[]); self.assertFalse(p.tapped)
        self.assertEqual(g.tap_physical_land_for_mana(p.uid,color='B'),'B'); self.assertTrue(p.tapped)
        g.fixture_new_turn(); self.assertEqual(g.tap_physical_land_for_mana(p.uid,color='G'),'G')
        self.assertEqual(g.mana_pool,['B','G'])
    def test_forest_g_swamp_b(self):
        g=self.bridge(); f=g.play_physical_land(self.to_hand(g,'Forest'))
        self.assertEqual(g.tap_physical_land_for_mana(f.uid),'G')
        with self.assertRaises(ZoneError): g.tap_physical_land_for_mana(f.uid)           # already tapped
        g.fixture_new_turn(); s=g.play_physical_land(self.to_hand(g,'Swamp'))
        self.assertEqual(g.tap_physical_land_for_mana(s.uid),'B')
        with self.assertRaises(ZoneError): g.tap_physical_land_for_mana(s.uid,color='G')
    def test_sol_ring_cc_not_colored(self):
        g=Game(); g.add(SAVRA); r=g.add('Sol Ring'); g.resolve()
        with self.assertRaises(IllegalAction): g.tap_mana_rock(r.uid,color='B')
        self.assertEqual(g.tap_mana_rock(r.uid),('C','C')); self.assertEqual(g.mana_pool,['C','C'])
        self.assertNotIn('B',g.mana_pool); self.assertNotIn('G',g.mana_pool)
    def test_grim_backwoods_blocked(self): self.assert_fails_closed('Grim Backwoods')

if __name__=='__main__':
    unittest.main()
