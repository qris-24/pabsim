"""R01 controls for Pest Rescuer's "Pest creature token" condition.

Promoted R01 reference fixtures (13 distinct contracts; 11 run on both the
event kernel and the physical bridge via subTest). Each case measures new Pest tokens
created by one upkeep. Controls cover: no Pest (positive), nontoken Teacher's
Pest (the CP09 discrepancy), ordinary and Moseo Pest tokens (negative),
opponent-controlled token, intervening-if at resolution, and the physical
bridge candidate. The last class pins the FROZEN engine's wrong behaviour so
the discrepancy stays visible rather than silently disappearing.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST, MOSEO_PEST
import pab_focus_engine_v07 as v07
import pab_kernel as r01  # promoted kernel

def pests(g): return sum(p.token==PEST for p in g.permanents.values())
def all_pest_tokens(g): return sum(p.token is not None and 'Pest' in p.subtypes for p in g.permanents.values())

CANDIDATES=(('event',r01.Game),('bridge',r01.PhysicalZoneGame))

def both(fn):
    """Run one control against the event kernel and the physical bridge."""
    def wrapper(self):
        for label,G in CANDIDATES:
            with self.subTest(candidate=label): fn(self,G)
    wrapper.__name__=fn.__name__; wrapper.__doc__=fn.__doc__
    return wrapper

class R01Controls(unittest.TestCase):
    def game(self,G,*names):
        g=G()
        for n in names: g.add(n)
        g.resolve(); return g
    def upkeep(self,g):
        before=pests(g); g.begin_upkeep(); g.resolve(); return pests(g)-before

    @both
    def test_positive_no_pest_creates_one(self,G):
        self.assertEqual(self.upkeep(self.game(G,'Pest Rescuer')),1)
    @both
    def test_nontoken_teachers_pest_does_not_suppress(self,G):
        g=self.game(G,'Pest Rescuer',"Teacher's Pest")
        self.assertEqual(self.upkeep(g),1)
        self.assertEqual(all_pest_tokens(g),1)
    @both
    def test_ordinary_pest_token_suppresses(self,G):
        g=self.game(G,'Pest Rescuer'); g.make_tokens(PEST)
        self.assertEqual(self.upkeep(g),0)
    @both
    def test_moseo_pest_token_suppresses(self,G):
        g=self.game(G,'Pest Rescuer'); g.make_tokens(MOSEO_PEST)
        self.assertEqual(self.upkeep(g),0)
    @both
    def test_opponent_pest_token_does_not_suppress(self,G):
        g=self.game(G,'Pest Rescuer'); g.make_tokens(PEST,controller=1)
        self.assertEqual(self.upkeep(g),1)
    @both
    def test_resolution_check_token_created_before_resolve(self,G):
        g=self.game(G,'Pest Rescuer'); g.begin_upkeep(); g.make_tokens(PEST); g.resolve()
        self.assertEqual(pests(g),1)   # intervening-if false at resolution: no second token
    @both
    def test_resolution_check_nontoken_entered_before_resolve(self,G):
        g=self.game(G,'Pest Rescuer'); g.begin_upkeep(); g.add("Teacher's Pest"); g.resolve()
        self.assertEqual(pests(g),1)   # nontoken Pest does not change the condition
    @both
    def test_token_sacrificed_before_upkeep_then_creates(self,G):
        g=self.game(G,'Pest Rescuer'); t=g.make_tokens(PEST)[0]
        g.sacrifice(t.uid); g.resolve()
        self.assertEqual(self.upkeep(g),1)
    @both
    def test_second_upkeep_with_token_present_is_idle(self,G):
        g=self.game(G,'Pest Rescuer')
        self.assertEqual(self.upkeep(g),1); self.assertEqual(self.upkeep(g),0)
    @both
    def test_two_rescuers_no_pest(self,G):
        # Both triggers admitted; the first resolution creates a token, the
        # second's intervening-if is then false. Net exactly one.
        g=self.game(G,'Pest Rescuer','Pest Rescuer')
        self.assertEqual(self.upkeep(g),1)
    @both
    def test_lifegain_replacement_unchanged(self,G):
        g=self.game(G,'Pest Rescuer'); g.gain(1,'manual'); g.resolve()
        self.assertEqual(g.life[0],42)   # +1 replacement is outside R01 scope and must not move

class FrozenEngineStillShowsDiscrepancy(unittest.TestCase):
    """Documents CP09 against the UNMODIFIED v0.7 candidate (same predicate as v0.5)."""
    def test_frozen_nontoken_teachers_pest_wrongly_suppresses(self):
        g=v07.Game(); g.add('Pest Rescuer'); g.add("Teacher's Pest"); g.resolve()
        g.begin_upkeep(); g.resolve()
        self.assertEqual(pests(g),0)   # wrong per supplied text; kept frozen
    def test_frozen_and_r01_agree_on_token_cases(self):
        for G in (v07.Game,r01.Game):
            g=G(); g.add('Pest Rescuer'); g.resolve(); g.make_tokens(PEST)
            g.begin_upkeep(); g.resolve(); self.assertEqual(pests(g),1)
            g=G(); g.add('Pest Rescuer'); g.resolve()
            g.begin_upkeep(); g.resolve(); self.assertEqual(pests(g),1)

if __name__=='__main__':
    unittest.main()
