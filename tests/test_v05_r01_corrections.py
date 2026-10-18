"""Promoted corrections to frozen v0.5 contracts 112 and 113 (R01).

The frozen originals in test_v05_fixture_cards.py assert that a nontoken
Teacher's Pest suppresses Pest Rescuer. Per the supplied text ("Pest creature
token") it does not. The originals stay frozen for history and are marked
SUPERSEDED in the coverage registry; these two are the reference assertions.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST
from pab_kernel import Game

class R01Corrections(unittest.TestCase):
    def game(self,*names):
        g=Game()
        for n in names: g.add(n)
        g.resolve(); return g
    def pests(self,g): return sum(p.token==PEST for p in g.permanents.values())
    def test_112r_teacher_pest_does_not_block_rescuer_at_upkeep_start(self):
        g=self.game('Pest Rescuer',"Teacher's Pest"); g.begin_upkeep(); g.resolve()
        self.assertEqual(self.pests(g),1)
    def test_113r_teacher_pest_entered_before_resolution_does_not_block(self):
        g=self.game('Pest Rescuer'); g.begin_upkeep(); g.add("Teacher's Pest"); g.resolve()
        self.assertEqual(self.pests(g),1)
