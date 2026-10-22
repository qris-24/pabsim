"""Stage S5: integrated turn-loop validation over existing capabilities, with
state invariants checked at every boundary and after every action, across seeds.
This is evidence of connected legal sequences, not of deck performance.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA
from pab_zones import SUPPORTED_LAND_MANA
from pab_kernel import PhysicalZoneGame
from pab_turn_loop import opening_hand, run_turns, check_invariants, InvariantError

SEEDS=(0,1,2,3,4,7,11,42)

def game(seed):
    g=PhysicalZoneGame(seed=seed); g.add(SAVRA); g.resolve(); return g   # Savra as an event-kernel fixture; physical Savra stays in command

class TurnLoop(unittest.TestCase):
    def test_opening_hand_then_eight_turns_all_seeds(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=game(seed); opening_hand(g); ledger=run_turns(g,8)
                self.assertEqual([t for t,_,_,_ in ledger],[1,5])            # controller turns in two rounds of four
                self.assertEqual(ledger[-1][1],2)                             # two draw-step draws so far
                z=g.zones; self.assertEqual(len(z.zones['library'])+len(z.zones['hand'])+len(z.zones['battlefield'])+len(z.zones['graveyard']),99)
                self.assertEqual(len(z.zones['library']),99-7-2)
                self.assertEqual(g.clock.state(),(9,0,'beginning','untap'))
    def test_land_plays_never_exceed_one_and_only_supported_names(self):
        total=0
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=game(seed); opening_hand(g); ledger=run_turns(g,16)
                played=[l for _,_,l,_ in ledger if l]
                self.assertTrue(all(n in SUPPORTED_LAND_MANA for n in played))
                self.assertEqual(len(played),len([x for x in g.trace if x[0]=='physical_land_played']))   # R54: was 'land_played' (a zones-trace key, never in g.trace); passed vacuously while R53 kept hands landless
                self.assertEqual(len(played),len([x for x in g.zones.trace if x[0]=='land_played']))
                total+=len(played)
        self.assertGreater(total,0)                                           # not vacuous: some seed plays a land in 16 turns
    def test_mana_produced_equals_untapped_linked_lands_and_empties_by_next_step(self):
        g=game(3); opening_hand(g); ledger=run_turns(g,12)
        for t,_,_,mana in ledger:
            self.assertLessEqual(len(mana),len(g.linked_battlefield))
        self.assertEqual(g.mana_pool,[])
        for seed in SEEDS:                                                    # CP42 (T4): equals, not just at most, and emptied at the step's end
            with self.subTest(seed=seed):
                g=game(seed); opening_hand(g); ledger=run_turns(g,12); lands=0
                for t,_,played,mana in ledger:
                    lands+=played is not None; self.assertEqual(len(mana),lands)   # every land enters untapped and untaps each turn
                self.assertEqual([x[1] for x in g.trace if x[0]=='mana_emptied' and x[1]],[len(m) for *_,m in ledger if m])
        emptied=[x for x in g.trace if x[0]=='mana_emptied']
        self.assertEqual(sum(x[1] for x in emptied),sum(len(m) for _,_,_,m in ledger))
    def test_hand_size_accounting(self):
        g=game(5); opening_hand(g); ledger=run_turns(g,8); z=g.zones
        lands=sum(1 for _,_,l,_ in ledger if l)
        self.assertEqual(len(z.zones['hand']),7+2-lands)
    def test_invariant_checker_catches_corruption(self):
        g=game(0); opening_hand(g); u=g.zones.zones['hand'][0]
        g.zones.zones['library'].append(u)                                   # same card in two zones
        with self.assertRaises(InvariantError): check_invariants(g)
    def test_thirty_turns_no_failed_draw_and_tokens_do_not_break_card_count(self):
        g=game(1); g.add('Beledros Witherbloom'); g.resolve(); opening_hand(g); run_turns(g,30)
        self.assertEqual(g.zones.failed_draws,0)
        self.assertGreaterEqual(sum(1 for p in g.permanents.values() if p.token is not None),30)   # one Pest per upkeep, every seat
        check_invariants(g)
    def test_r53_opening_hand_shuffles_first_so_seeds_differ(self):
        hands=set()
        for seed in SEEDS:
            g=game(seed); opening_hand(g)
            self.assertEqual(g.trace.index(('opening_shuffle_103_3',seed))+1,g.trace.index(('opening_hand',7)))   # shuffle immediately before the draw
            self.assertEqual([x[0] for x in g.zones.trace[:2]],['library_shuffled','zone_move'])
            hands.add(tuple(g.zones.cards[u].name for u in g.zones.zones['hand']))
        self.assertGreater(len(hands),1)                                      # R53: before the fix every seed drew the frozen list order
        g1=game(2); opening_hand(g1); g2=game(2); opening_hand(g2)
        self.assertEqual(g1.zones.zones['hand'],g2.zones.zones['hand'])        # still deterministic per seed

if __name__=='__main__':
    unittest.main()
