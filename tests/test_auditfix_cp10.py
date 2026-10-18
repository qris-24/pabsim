"""CP10 audit repairs (2026-10-18).

A: AUD-01 / A-S20-12 — tap_lands_policy counted produced colours twice (pool=g.mana_pool+produced
   while tap_physical_land_for_mana already appends to g.mana_pool).
"""
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA
from pab_kernel import PhysicalZoneGame
from pab_lands_s9 import tap_lands_policy, _need, LAND_MANA
from pab_opponents_s8 import check_invariants_s8

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

if __name__=='__main__': unittest.main()
