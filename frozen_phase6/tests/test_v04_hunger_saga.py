"""Bounded The Hunger Tide Rises chapter IV fixtures: library is explicit only."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import *

class HungerSagaIV(unittest.TestCase):
    def setup(self,*names):
        g=Game()
        for n in names:g.add(n)
        g.resolve()
        return g

    def test_102_saga_enters_with_insect_not_ordinary_pest(self):
        g=self.setup('The Hunger Tide Rises')
        self.assertEqual(len([p for p in g.permanents.values() if p.token==INSECT]),1)
        self.assertEqual(len([p for p in g.permanents.values() if p.token==PEST]),0)

    def test_103_chatterfang_saga_insect_plus_green_squirrel(self):
        g=self.setup('Chatterfang, Squirrel General','The Hunger Tide Rises')
        self.assertEqual(len([p for p in g.permanents.values() if p.token==INSECT]),1)
        self.assertEqual(len([p for p in g.permanents.values() if p.token==SQUIRREL]),1)

    def test_104_saga_four_sacrificed_creature_available_in_graveyard_search(self):
        g=self.setup('The Hunger Tide Rises',SAVRA)
        target=g.add('Infestation Sage',mana_value=1)
        g.saga_chapter(4,sacrifice_uids=[target.uid],grave_selection_uid=target.uid)
        g.resolve()
        self.assertTrue(any(p.name=='Infestation Sage' and p.uid!=target.uid for p in g.permanents.values()))
        self.assertFalse(g.has('The Hunger Tide Rises'))
        self.assertEqual(g.edict_opportunities,1)
        self.assertEqual(g.opponent_sacrifices,0)

    def test_105_saga_four_existing_grave_target_mv_threshold(self):
        g=self.setup('The Hunger Tide Rises')
        old=g.add('Reassembling Skeleton',mana_value=2);g.destroy(old.uid);g.resolve()
        one=g.make_tokens(INSECT)[0]
        with self.assertRaises(IllegalAction):
            g.saga_chapter(4,sacrifice_uids=[one.uid],grave_selection_uid=old.uid)
        self.assertIn(one.uid,g.permanents)
        self.assertEqual(g.has('The Hunger Tide Rises'),1)
        two=g.make_tokens(INSECT)[0]
        g.saga_chapter(4,sacrifice_uids=[one.uid,two.uid],grave_selection_uid=old.uid)
        g.resolve()
        self.assertTrue(any(p.name=='Reassembling Skeleton' for p in g.permanents.values()))

    def test_106_saga_four_explicit_library_mv_and_not_generic_tutor(self):
        g=self.setup('The Hunger Tide Rises')
        idx=g.put_creature_in_fixture_library('Reassembling Skeleton',mana_value=2)
        x,y=g.make_tokens(INSECT,2)
        g.saga_chapter(4,sacrifice_uids=[x.uid,y.uid],library_selection_index=idx)
        g.resolve()
        self.assertTrue(any(p.name=='Reassembling Skeleton' for p in g.permanents.values()))
        self.assertEqual(g.fixture_library_creatures,[])
        self.assertIn(('fixture_library_shuffled_unmodeled',),g.trace)

    def test_107_saga_library_choice_too_expensive_is_atomic(self):
        g=self.setup('The Hunger Tide Rises')
        idx=g.put_creature_in_fixture_library('Reassembling Skeleton',mana_value=5)
        x=g.make_tokens(INSECT)[0]
        with self.assertRaises(IllegalAction):
            g.saga_chapter(4,sacrifice_uids=[x.uid],library_selection_index=idx)
        self.assertIn(x.uid,g.permanents)
        self.assertEqual(g.has('The Hunger Tide Rises'),1)
        self.assertEqual(len(g.fixture_library_creatures),1)

    def test_108_saga_no_creature_choice_is_allowed_and_finite(self):
        g=self.setup('The Hunger Tide Rises')
        g.saga_chapter(4)
        g.resolve()
        self.assertEqual(g.has('The Hunger Tide Rises'),0)
        self.assertIn(('saga_iv_chose_no_creature',0),g.trace)

    def test_109_saga_refuses_selecting_both_sources_without_sacrifice(self):
        g=self.setup('The Hunger Tide Rises')
        idx=g.put_creature_in_fixture_library('Reassembling Skeleton',mana_value=0)
        with self.assertRaises(IllegalAction):
            g.saga_chapter(4,grave_selection_uid=101,library_selection_index=idx)
        self.assertEqual(g.has('The Hunger Tide Rises'),1)

    def test_110_saga_refuses_opponents_and_duplicate_creatures_as_sacrifice(self):
        g=self.setup('The Hunger Tide Rises')
        mine=g.make_tokens(INSECT)[0]
        enemy=g.add('Reassembling Skeleton',controller=1)
        with self.assertRaises(IllegalAction):g.saga_chapter(4,sacrifice_uids=[enemy.uid])
        with self.assertRaises(IllegalAction):g.saga_chapter(4,sacrifice_uids=[mine.uid,mine.uid])
        self.assertIn(mine.uid,g.permanents)

    def test_111_saga_tokens_do_not_enter_graveyard_as_cards(self):
        g=self.setup('The Hunger Tide Rises')
        x=g.make_tokens(INSECT)[0]
        g.saga_chapter(4,sacrifice_uids=[x.uid]);g.resolve()
        self.assertFalse(any(p.uid==x.uid for p in g.graveyard))
        self.assertNotIn(x.uid,g.permanents)

if __name__=='__main__':unittest.main()
