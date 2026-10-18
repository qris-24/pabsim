"""R52: Village Rites costs {B} on the promoted kernel's frozen-style cast_pab_spell path.
Frozen v0.7 behaviour ({1}{B}) is pinned by tests/test_v04_cost_and_copy.py::test_91 and is
superseded. Both kernel classes are covered; other spells are delegated unchanged.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, PEST, TREASURE, IllegalAction
from pab_focus_engine_v07 import Game as FrozenGame
from pab_kernel import Game, PhysicalZoneGame, SUPERSEDED_FROZEN_CONTRACTS
from pab_r52_village_rites import VILLAGE_RITES_COST

class R52(unittest.TestCase):
    def test_village_rites_pays_exactly_B_on_both_kernel_classes(self):
        for cls in (Game,PhysicalZoneGame):
            with self.subTest(cls=cls.__name__):
                g=cls(); g.add(SAVRA); g.add('Sedgemoor Witch'); g.resolve(); p=g.make_tokens(PEST)[0]; g.resolve()
                g.add_mana('B','C'); g.cast_pab_spell('Village Rites',p.uid)
                self.assertEqual(g.mana_pool,['C'])                                      # {1} was never on the card
                self.assertNotIn(p.uid,g.permanents)
                t=g.trace; self.assertLess(t.index(('sacrifice',p.uid,'ordinary Pest')),t.index(('cast','Village Rites')))
                g.resolve(); self.assertEqual(g.cards_drawn,2)
                self.assertEqual(sum(1 for x in g.permanents.values() if x.token==PEST),1)   # Magecraft
    def test_refusals_unchanged_no_black_or_illegal_cost_mutate_nothing(self):
        g=Game(); p=g.add('Reassembling Skeleton'); g.add_mana('C','G')
        with self.assertRaises(IllegalAction): g.cast_pab_spell('Village Rites',p.uid)
        t=g.make_tokens(TREASURE)[0]; g.resolve(); g.add_mana('B')
        with self.assertRaises(IllegalAction): g.cast_pab_spell('Village Rites',t.uid)   # artifact is not a creature
        self.assertEqual(g.mana_pool,['C','G','B']); self.assertIn(p.uid,g.permanents); self.assertIn(t.uid,g.permanents)
    def test_frozen_engine_still_charges_1B_and_test_91_is_superseded(self):
        g=FrozenGame(); p=g.add('Reassembling Skeleton'); g.add_mana('B')
        with self.assertRaises(IllegalAction): g.cast_pab_spell('Village Rites',p.uid)      # frozen, untouched
        self.assertIn('test_91_village_rejects_mana_shortage_before_sac',SUPERSEDED_FROZEN_CONTRACTS)
        self.assertEqual(len(SUPERSEDED_FROZEN_CONTRACTS),3); self.assertEqual(VILLAGE_RITES_COST,(1,0,0))
    def test_other_spells_delegate_to_frozen_costs(self):
        g=Game(); p=g.make_tokens(PEST)[0]; g.resolve(); g.add_mana('B')
        with self.assertRaises(IllegalAction): g.cast_pab_spell('Deadly Dispute',p.uid)      # {1}{B} still required
        g.add_mana('G'); g.cast_pab_spell('Tend the Pests',p.uid); g.resolve()
        self.assertEqual(g.mana_pool,[]); self.assertEqual(sum(1 for x in g.permanents.values() if x.token==PEST),1)

if __name__=='__main__': unittest.main()
