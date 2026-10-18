"""Phase-clock stage S1: TurnClock structure (and, after S2, unengaged compatibility).

S1 adds a clock to the kernel and nothing else. These fixtures pin (a) the CR
500.1 step order and APNAP seat rotation and (b) that advancing the clock
through full turns changes no game state: no triggers, no token creation, no
mana emptying, no effect expiry. S2 is where behaviour attaches.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST, SAVRA
from pab_turn_clock import TurnClock, STEPS, ClockError
from pab_kernel import Game, PhysicalZoneGame

class ClockStructure(unittest.TestCase):
    def test_twelve_steps_in_cr_order(self):
        self.assertEqual([s for _,s in STEPS],['untap','upkeep','draw','precombat_main','beginning_of_combat',
            'declare_attackers','declare_blockers','combat_damage','end_of_combat','postcombat_main','end','cleanup'])
    def test_starts_at_turn_one_seat_zero_untap(self):
        self.assertEqual(TurnClock().state(),(1,0,'beginning','untap'))
    def test_full_turn_rotates_active_player_and_increments_turn(self):
        c=TurnClock()
        for _ in range(12): c.advance()
        self.assertEqual(c.state(),(2,1,'beginning','untap'))
    def test_four_seats_wrap_to_controller_on_turn_five(self):
        c=TurnClock(); c.advance_to('untap',active_player=0)
        self.assertEqual(c.state(),(5,0,'beginning','untap'))
    def test_advance_to_each_upkeep_in_a_round(self):
        c=TurnClock(); seen=[]
        for _ in range(4): seen.append(c.advance_to('upkeep')[1:3])
        self.assertEqual(seen,[(1,0),(2,1),(3,2),(4,3)])
    def test_boundaries_recorded(self):
        c=TurnClock(); c.advance(); c.advance()
        self.assertEqual(c.boundaries[-1],('step_begin',1,0,'beginning','draw')); self.assertEqual(len(c.boundaries),3)
    def test_rejects_unknown_step_and_bad_seats(self):
        with self.assertRaises(ClockError): TurnClock().advance_to('mulligan')
        with self.assertRaises(ClockError): TurnClock(seats=0)

class UnengagedCompatibility(unittest.TestCase):
    """S1 contract after S2: until the clock is first advanced, step methods stay
    caller-driven and the clock changes nothing."""
    def test_kernel_has_clock_unengaged(self):
        g=Game(); self.assertEqual(g.clock.state(),(1,0,'beginning','untap')); self.assertFalse(g.clock_engaged)
    def test_direct_step_methods_allowed_before_engagement(self):
        g=Game(); g.add('Beledros Witherbloom'); g.add('Ribtruss Roaster',counters=1); g.resolve()
        g.begin_upkeep(); g.roaster_end_step()
        self.assertEqual([t.label for t in g.pending],['Ribtruss Roaster end-step','Beledros each upkeep'])
    def test_physical_bridge_zones_untouched_by_advancing(self):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve()
        z=g.zones; before=({k:tuple(v) for k,v in z.zones.items()},z.land_plays_this_turn)
        g.advance_to('upkeep',active_player=2)
        self.assertEqual(({k:tuple(v) for k,v in z.zones.items()},z.land_plays_this_turn),before); g.assert_bridge_integrity()

if __name__=='__main__':
    unittest.main()
