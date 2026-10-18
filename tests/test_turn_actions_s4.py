"""Phase-clock stage S4: untap step, draw step, land-play window on both the event
kernel and the physical bridge. CR refs: 502.3, 504.1, 305.1, 305.2, 103.8a.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA
from pab_zones import ZoneError
from pab_turn_clock import ClockError
from pab_kernel import Game, PhysicalZoneGame

def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def bridge(self):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve(); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); return uid

class DrawStep(_B):
    def test_controller_draws_one_real_card_turn_one(self):
        g=self.bridge(); z=g.zones; lib=len(z.zones['library']); g.advance_to('draw',active_player=0)
        self.assertEqual((len(z.zones['library']),len(z.zones['hand']),g.cards_drawn),(lib-1,1,1))   # no 103.8a skip in 4-player
        self.assertEqual(trace(g,'draw')[-1],('draw',1,'draw step'))
    def test_opponent_draw_is_unmodeled_and_moves_nothing(self):
        g=self.bridge(); z=g.zones; g.advance_to('draw',active_player=0); lib=len(z.zones['library'])
        g.advance_to('draw',active_player=1)
        self.assertEqual(len(z.zones['library']),lib); self.assertEqual(trace(g,'opponent_draw_unmodeled'),[('opponent_draw_unmodeled',1)])
    def test_event_kernel_counts_draw(self):
        g=Game(); g.add(SAVRA); g.resolve(); g.advance_to('draw'); self.assertEqual(g.cards_drawn,1)
    def test_one_draw_per_controller_turn_over_a_round(self):
        g=self.bridge(); z=g.zones; g.advance_to('draw',active_player=0); g.advance_to('draw',active_player=0)
        self.assertEqual((g.clock.turn,len(z.zones['hand'])),(5,2))

class UntapStep(_B):
    def test_tapped_land_untaps_at_next_controller_untap(self):
        g=self.bridge(); g.advance_to('precombat_main',active_player=0); f=g.play_physical_land(self.to_hand(g,'Forest'))
        g.tap_physical_land_for_mana(f.uid); self.assertTrue(f.tapped)
        g.advance_to('end',active_player=3); self.assertTrue(f.tapped)                 # stays tapped through opponents' turns
        g.advance_to('untap',active_player=0)
        self.assertFalse(f.tapped); self.assertFalse(g.zones.cards[g.linked_battlefield[f.uid]].tapped)
        self.assertEqual(trace(g,'untap_step')[-1],('untap_step',5,1)); self.assertEqual(g.zones.land_plays_this_turn,0)
    def test_event_kernel_rock_untaps(self):
        g=Game(); g.add(SAVRA); r=g.add('Sol Ring'); g.resolve(); g.advance_to('precombat_main'); g.tap_mana_rock(r.uid)
        self.assertTrue(r.tapped); g.advance_to('untap',active_player=0); self.assertFalse(r.tapped)
    def test_mana_from_untapped_land_usable_again_next_turn(self):
        g=self.bridge(); g.advance_to('precombat_main'); f=g.play_physical_land(self.to_hand(g,'Forest')); g.tap_physical_land_for_mana(f.uid)
        g.advance_to('precombat_main',active_player=0); self.assertEqual(g.tap_physical_land_for_mana(f.uid),'G')

class LandWindow(_B):
    def test_main_phase_empty_stack_allowed(self):
        g=self.bridge(); g.advance_to('precombat_main'); p=g.play_physical_land(self.to_hand(g,'Swamp')); self.assertEqual(p.name,'Swamp')
    def test_refused_outside_main_phase(self):
        g=self.bridge(); uid=self.to_hand(g,'Swamp'); g.advance_to('upkeep')
        with self.assertRaises(ZoneError): g.play_physical_land(uid)
    def test_refused_with_pending_triggers(self):
        g=self.bridge(); g.add('Beledros Witherbloom'); g.resolve(); uid=self.to_hand(g,'Swamp'); g.advance_to('upkeep'); g.advance_to('precombat_main')
        # Beledros' upkeep trigger is still pending (not resolved): stack not empty
        with self.assertRaises(ZoneError): g.play_physical_land(uid)
        g.resolve(); g.play_physical_land(uid)
    def test_refused_on_opponent_turn(self):
        g=self.bridge(); uid=self.to_hand(g,'Swamp'); g.advance_to('precombat_main',active_player=2)
        with self.assertRaises(ClockError): g.play_physical_land(uid)
    def test_one_per_turn_then_reset(self):
        g=self.bridge(); g.advance_to('precombat_main'); g.play_physical_land(self.to_hand(g,'Swamp')); s2=self.to_hand(g,'Swamp')
        with self.assertRaises(ZoneError): g.play_physical_land(s2)
        g.advance_to('postcombat_main',active_player=0)
        with self.assertRaises(ZoneError): g.play_physical_land(s2)         # same turn, still one
        g.advance_to('precombat_main',active_player=0); g.play_physical_land(s2)
    def test_unengaged_defaults_preserved(self):
        g=self.bridge(); p=g.play_physical_land(self.to_hand(g,'Forest')); self.assertFalse(g.clock_engaged); self.assertEqual(p.name,'Forest')

if __name__=='__main__':
    unittest.main()
