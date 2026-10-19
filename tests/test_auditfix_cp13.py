"""CP13 audit repair (2026-10-18).

AUD-03 / A-S20-14 — Demonic Tutor and Diabolic Intent pre-committed the library choice when the spell
was cast (and refused the cast without one). Since CP13 the cast pays only the mana and the Diabolic
Intent sacrifice; the library card is chosen when the spell resolves, against the library as it is then:
an explicit `selected_land_uid` is honoured if the card is still in the library, otherwise (or with no
selection) `tutor_selection` runs at resolution, falling back to the first library card so the
unrestricted mandatory search always finds one. An empty library shuffles and resolves with None.
"""
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST
from pab_zone_bridge import BridgeError
from pab_kernel import PhysicalZoneGame
import pab_cast_s13 as _s13
from pab_cast_s13 import check_invariants_s11, cast_when_able, tutor_selection

def ztrace(g,key): return [t for t in g.zones.trace if t[0]==key]
def gtrace(g,key): return [t for t in g.trace if t[0]==key]

class TestCP13TutorAtResolution(unittest.TestCase):
    def bridge(self):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve(); check_invariants_s11(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s11(g); return uid
    def lib(self,g,name): return next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
    def pest(self,g):
        p=g.make_tokens(PEST)[0]; g.resolve(); check_invariants_s11(g); return p
    def found(self,g):
        """uid the last Demonic Tutor resolution put in hand."""
        return ztrace(g,'demonic_tutor_resolved')[-1][1]
    def counting(self):
        """Replace the module-level policy with a counting wrapper; returns (restore, calls)."""
        calls=[]; real=_s13.tutor_selection
        def wrapped(g):
            u=real(g); calls.append((u,len(g.zones.zones['library']))); return u
        _s13.tutor_selection=wrapped
        return (lambda: setattr(_s13,'tutor_selection',real)), calls

    def test_cast_without_selection_succeeds_and_finds_a_card(self):
        g=self.bridge(); dt=self.to_hand(g,'Demonic Tutor'); g.add_mana('B','C'); n=len(g.zones.zones['library'])
        g.cast_from_hand(dt); check_invariants_s11(g); g.resolve(); check_invariants_s11(g)
        u=self.found(g); self.assertIsNotNone(u); self.assertEqual(g.zones.cards[u].zone,'hand')
        self.assertEqual(len(g.zones.zones['library']),n-1); self.assertEqual(g.zones.cards[dt].zone,'graveyard'); self.assertEqual(g.mana_pool,[])

    def test_selector_runs_at_resolution_not_at_cast(self):
        g=self.bridge(); dt=self.to_hand(g,'Demonic Tutor'); g.add_mana('B','C'); restore,calls=self.counting()
        try:
            g.cast_from_hand(dt); check_invariants_s11(g)
            self.assertEqual(calls,[]); self.assertEqual(ztrace(g,'demonic_tutor_resolved'),[]); self.assertIn(dt,g.stack_cards)
            g.resolve(); check_invariants_s11(g)
        finally: restore()
        self.assertEqual(len(calls),1); self.assertEqual(calls[0][0],self.found(g))

    def test_selection_sees_the_library_as_it_is_at_resolution(self):
        g=self.bridge(); dt=self.to_hand(g,'Demonic Tutor'); g.add_mana('B','C')
        g.cast_from_hand(dt); check_invariants_s11(g); pre=tutor_selection(g)       # what a cast-time choice would have been
        g.zones.search_library(selected_uid=pre,destination='hand')                 # that card leaves the library before resolution
        expected=tutor_selection(g); self.assertNotEqual(expected,pre)
        g.resolve(); check_invariants_s11(g)
        self.assertEqual(self.found(g),expected); self.assertEqual(g.zones.cards[expected].zone,'hand'); self.assertEqual(gtrace(g,'search_selection_gone'),[])

    def test_stale_explicit_choice_falls_back_to_resolution_selection(self):
        g=self.bridge(); dt=self.to_hand(g,'Demonic Tutor'); sel=self.lib(g,'Grave Pact'); g.add_mana('B','C')
        g.cast_from_hand(dt,selected_land_uid=sel); check_invariants_s11(g)
        g.zones.search_library(selected_uid=sel,destination='hand')                 # explicit choice gone by resolution
        g.resolve(); check_invariants_s11(g)
        self.assertIn(('search_selection_gone','Demonic Tutor',sel),g.trace)
        u=self.found(g); self.assertIsNotNone(u); self.assertNotEqual(u,sel); self.assertEqual(g.zones.cards[u].zone,'hand'); self.assertEqual(g.zones.cards[dt].zone,'graveyard')

    def test_empty_library_shuffles_and_resolves_with_none(self):
        g=self.bridge(); dt=self.to_hand(g,'Demonic Tutor'); g.add_mana('B','C')
        for u in list(g.zones.zones['library']): g.zones.move(u,'exile')
        check_invariants_s11(g); hand=len(g.zones.zones['hand'])
        g.cast_from_hand(dt); check_invariants_s11(g); g.resolve(); check_invariants_s11(g)
        self.assertIn(('search_resolved','any','hand',None),g.zones.trace); self.assertIn(('demonic_tutor_resolved',None),g.zones.trace)
        self.assertIn(('library_shuffled',0),g.zones.trace); self.assertEqual(len(g.zones.zones['hand']),hand-1); self.assertEqual(g.zones.cards[dt].zone,'graveyard')

    def test_diabolic_intent_sacrifice_and_mana_paid_at_cast(self):
        g=self.bridge(); di=self.to_hand(g,'Diabolic Intent'); p=self.pest(g); g.add_mana('B','C')
        g.cast_from_hand(di,sacrifice_uid=p.uid); check_invariants_s11(g)
        self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.mana_pool,[]); self.assertIn(di,g.stack_cards)
        self.assertEqual(gtrace(g,'diabolic_intent_resolved'),[])
        g.resolve(); check_invariants_s11(g)
        res=gtrace(g,'diabolic_intent_resolved'); self.assertEqual(len(res),1); u=res[0][1]
        self.assertIsNotNone(u); self.assertEqual(g.zones.cards[u].zone,'hand'); self.assertEqual(g.zones.cards[di].zone,'graveyard')
        g=self.bridge(); di=self.to_hand(g,'Diabolic Intent'); g.add_mana('B','C')
        with self.assertRaises(BridgeError): g.cast_from_hand(di)                   # the additional cost is still required at cast
        self.assertEqual(g.stack_cards,{}); check_invariants_s11(g)

    def test_explicit_choice_still_in_library_is_honoured(self):
        g=self.bridge(); dt=self.to_hand(g,'Demonic Tutor'); sel=self.lib(g,'Grave Pact'); g.add_mana('B','C'); restore,calls=self.counting()
        try:
            g.cast_from_hand(dt,selected_land_uid=sel); check_invariants_s11(g); g.resolve(); check_invariants_s11(g)
        finally: restore()
        self.assertEqual(calls,[]); self.assertEqual(self.found(g),sel); self.assertEqual(g.zones.cards[sel].zone,'hand'); self.assertEqual(gtrace(g,'search_selection_gone'),[])

    def test_driver_casts_tutor_without_preselection(self):
        g=self.bridge(); g.advance_to('precombat_main',active_player=0); dt=self.to_hand(g,'Demonic Tutor'); g.add_mana('B','C'); restore,calls=self.counting()
        try: self.assertEqual(cast_when_able(g),['Demonic Tutor'])
        finally: restore()
        self.assertEqual(len(calls),1)                                              # once, from the resolution closure; none from the driver
        self.assertEqual(calls[0][0],self.found(g)); self.assertEqual(g.zones.cards[self.found(g)].zone,'hand'); self.assertEqual(g.stack_cards,{})

    def test_negative_control_cast_time_refusal_no_longer_occurs(self):
        g=self.bridge(); dt=self.to_hand(g,'Demonic Tutor'); g.add_mana('B','C'); lib=list(g.zones.zones['library'])
        try: g.cast_from_hand(dt)                                                  # pre-CP13 raised BridgeError: needs a selected library card
        except BridgeError as e: self.fail(f'cast-time selection refusal still occurs: {e}')
        check_invariants_s11(g); self.assertIn(dt,g.stack_cards); self.assertEqual(list(g.zones.zones['library']),lib); self.assertEqual(ztrace(g,'demonic_tutor_resolved'),[])
        g.resolve(); check_invariants_s11(g); self.assertEqual(g.stack_cards,{}); self.assertEqual(len(g.zones.zones['library']),len(lib)-1)

if __name__=='__main__': unittest.main()
