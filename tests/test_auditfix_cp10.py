"""CP10 audit repairs (2026-10-18).

A: AUD-01 / A-S20-12 — tap_lands_policy counted produced colours twice (pool=g.mana_pool+produced
   while tap_physical_land_for_mana already appends to g.mana_pool).
B: AUD-02 / A-S20-13 — script_opponent_actions accepted a (seat, turn) pair the fixed four-seat clock can
   never reach (turn t belongs to seat (t-1) % 4); the entry stayed pending forever and never executed.
"""
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST
from pab_kernel import PhysicalZoneGame
from pab_lands_s9 import tap_lands_policy, _need, LAND_MANA
from pab_opponents_s8 import check_invariants_s8, OPPONENT_SEATS
from pab_interaction_s11 import check_invariants_s11

class _Lands(unittest.TestCase):
    def game(self):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve(); check_invariants_s8(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); return uid
    def lands(self,g,*names):
        for n in names:
            g.zones.land_plays_this_turn=0
            p=g.play_physical_land(self.to_hand(g,n)); g.resolve(); check_invariants_s8(g)
            self.assertFalse(p.tapped,n)
    def expected_from_need(self,g,names):
        """Reference policy computed from the hand's need alone, one colour counted per land."""
        need=_need(g); counted={'G':0,'B':0}; out=[]
        for n in names:
            choices=LAND_MANA[n]
            short=[x for x in ('G','B') if counted[x]<need[x] and x in choices]
            c=short[0] if short else ('C' if 'C' in choices else 'B')
            counted[c]=counted.get(c,0)+1; out.append(c)
        return out

class TestCP10ColoredMana(_Lands):
    def test_reproduction_two_duals_need_g2_gives_g_g(self):
        g=self.game(); self.lands(g,'Command Tower','Blooming Marsh')
        self.to_hand(g,'Essence Warden'); self.to_hand(g,'Pest Rescuer')
        self.assertEqual(_need(g)['G'],2); self.assertEqual(g.mana_pool,[])
        self.assertEqual(tap_lands_policy(g),['G','G']); self.assertEqual(g.mana_pool,['G','G'])
    def test_two_duals_need_g1_b1_gives_one_each(self):
        g=self.game(); self.lands(g,'Command Tower','Blooming Marsh'); self.to_hand(g,"Teacher's Pest")
        self.assertEqual(_need(g),{'B':1,'G':1}); self.assertEqual(sorted(tap_lands_policy(g)),['B','G'])
    def test_two_duals_no_colour_need_use_the_policy_default_per_land(self):
        g=self.game(); self.lands(g,'Command Tower','Blooming Marsh')
        self.assertEqual(_need(g),{'B':0,'G':0})
        self.assertEqual(tap_lands_policy(g),['B','B'])                                   # neither land offers {C}
        g2=self.game(); self.lands(g2,'Llanowar Wastes','Command Tower')
        self.assertEqual(tap_lands_policy(g2),['C','B'])                                  # Wastes defaults to {C}, Tower to {B}
    def test_llanowar_wastes_gives_g_not_c_when_g_is_short(self):
        g=self.game(); self.lands(g,'Llanowar Wastes'); self.to_hand(g,'Pest Rescuer'); life=g.life[0]
        self.assertEqual(tap_lands_policy(g),['G']); self.assertEqual(g.life[0],life-1)   # painland damage on coloured mana
    def test_single_dual_need_g2_gives_g(self):
        g=self.game(); self.lands(g,'Command Tower'); self.to_hand(g,'Essence Warden'); self.to_hand(g,'Pest Rescuer')
        self.assertEqual(tap_lands_policy(g),['G'])
    def test_negative_control_old_double_count_arithmetic_is_not_used(self):
        g=self.game(); names=('Command Tower','Blooming Marsh'); self.lands(g,*names)
        self.to_hand(g,'Essence Warden'); self.to_hand(g,'Pest Rescuer'); need=_need(g)
        # what the pre-CP10 arithmetic (pool=g.mana_pool+produced, each colour counted twice) would pick
        old=[]; pool_double=[]
        for n in names:
            short=[x for x in ('G','B') if pool_double.count(x)<need[x] and x in LAND_MANA[n]]
            c=short[0] if short else 'B'; old.append(c); pool_double+= [c,c]
        self.assertEqual(old,['G','B'])
        expected=self.expected_from_need(g,names); self.assertEqual(expected,['G','G'])
        got=tap_lands_policy(g); self.assertEqual(got,expected); self.assertNotEqual(got,old)

BOARD=[{'name':'Bear','power':2,'toughness':2,'colors':'G'}]

class TestCP10ScriptValidation(unittest.TestCase):
    def game(self):
        g=PhysicalZoneGame(); g.resolve()
        for s in OPPONENT_SEATS: g.declare_opponent_board(s,BOARD)
        check_invariants_s11(g); return g
    def to_main(self,g,seat,turn):
        while not (g.clock.step=='precombat_main' and g.clock.active_player==seat and g.clock.turn==turn):
            g.advance_step(); g.resolve(); check_invariants_s11(g)
    def test_seat_2_turn_2_is_impossible_and_raises_naming_the_owner(self):
        g=self.game()
        with self.assertRaises(ValueError) as cm: g.script_opponent_actions(2,[{'turn':2,'kind':'edict'}])
        msg=str(cm.exception); self.assertIn('seat 2',msg); self.assertIn('turn 2',msg); self.assertIn('seat 1',msg)
        self.assertEqual(g.opponent_script,[]); self.assertFalse([t for t in g.trace if t[0]=='opponent_script_declared'])
    def test_seat_2_turn_3_is_accepted_and_executes_by_turn_3(self):
        g=self.game(); g.script_opponent_actions(2,[{'turn':3,'kind':'edict'}]); p=g.make_tokens(PEST)[0]; g.resolve()
        self.to_main(g,2,3)
        self.assertEqual(g.opponent_actions_done,[(3,2,'edict')]); self.assertNotIn(p.uid,g.permanents)
        self.assertEqual(g.opponent_script,[]); g.assert_opponent_script_exhausted()
    def test_seat_1_turn_2_is_accepted(self):
        g=self.game(); g.script_opponent_actions(1,[{'turn':2,'kind':'edict'}])
        self.assertEqual(g.opponent_script,[{'seat':1,'turn':2,'kind':'edict'}])
        for seat,turn in ((1,6),(2,7),(3,4),(3,8)): self.game().script_opponent_actions(seat,[{'turn':turn,'kind':'edict'}])
    def test_whole_list_is_validated_before_anything_is_scheduled(self):
        g=self.game()
        with self.assertRaises(ValueError): g.script_opponent_actions(1,[{'turn':2,'kind':'edict'},{'turn':3,'kind':'edict'}])
        self.assertEqual(g.opponent_script,[])
    def test_exhausted_check_fails_while_a_valid_far_future_action_is_pending(self):
        g=self.game(); g.script_opponent_actions(1,[{'turn':2,'kind':'edict'},{'turn':42,'kind':'edict'}]); g.make_tokens(PEST); g.resolve()
        self.to_main(g,1,2); self.assertEqual(g.opponent_actions_done,[(2,1,'edict')])
        with self.assertRaises(AssertionError) as cm: g.assert_opponent_script_exhausted()
        self.assertIn('turn 42',str(cm.exception)); self.assertLess(g.clock.turn,42)

if __name__=='__main__': unittest.main()
