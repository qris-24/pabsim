"""Stage S19: integrated whole-game validation. Reproducibility, clock legality (and that the
checker catches a doctored trace), the life ledger reconciling every seat from the trace,
stack discipline and counts, over two opponent configurations; report shape and writing. """
import sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_kernel import KERNEL_VERSION, PROMOTED
from pab_validation_s19 import validate_games, validate_game, new_game, clock_legal, life_ledger, write_report, DEFAULT_CONFIG
from pab_policy_s18 import run_game

QUIET={'policy':{1:{'removal_budget':1},2:{'wipe_at':5},3:{'graveyard_hate_at':6}},'block_policy':'all','max_turns':40}

class Validation(unittest.TestCase):
    def test_kernel_promoted_and_eight_seeds_two_configs_all_checks_pass(self):
        self.assertIn('+S19',KERNEL_VERSION); self.assertIn('S19',PROMOTED)
        for cfg in (None,QUIET):
            with self.subTest(config='default' if cfg is None else 'quiet'):
                rep=validate_games(list(range(8)),cfg); self.assertTrue(rep['all_ok'],rep['failed_seeds'])
                self.assertEqual(len(rep['games']),8); self.assertEqual(rep['kernel_version'],KERNEL_VERSION); self.assertIn('not deck scores',rep['note'])
                for x in rep['games']:
                    self.assertEqual(set(x['checks']),{'reproducible','clock_legal','life_ledger','stacks_empty','counts','lost_seats_at_zero','card_identity'}); self.assertEqual(x['life_ledger'],x['observed']['life'])
                outcomes={x['observed']['outcome'] for x in rep['games']}
                if cfg is None: self.assertEqual(outcomes,{'lost'})
                else: self.assertIn('timeout',outcomes)
    def test_clock_checker_catches_a_doctored_trace(self):
        g=new_game(3,{**DEFAULT_CONFIG,'max_turns':12}); run_game(g,12); ok,_=clock_legal(g); self.assertTrue(ok)
        i=next(k for k,t in enumerate(g.trace) if t[0]=='step_begin' and t[4]=='draw'); g.trace[i]=('step_begin',g.trace[i][1],g.trace[i][2],'precombat_main','precombat_main')
        ok,detail=clock_legal(g); self.assertFalse(ok); self.assertEqual(detail[0][0],'step order')
    def test_life_ledger_matches_after_every_kind_of_life_change(self):
        g=new_game(7,{**DEFAULT_CONFIG,'block_policy':'all','max_turns':20}); run_game(g,20)
        keys={t[0] for t in g.trace}; self.assertIn('combat_damage',keys); self.assertEqual(life_ledger(g),g.life)   # which life events occur depends on the seed
        # CP42 (T4): every kind life_ledger replays occurs, and the ledger matches each time
        KINDS={'gain','lose_life','pay_life','opponents_lose_each','target_opponent_loses','witherbloom_command_target','target_self_loses','combat_damage'}
        seen=set()
        for seed in (0,6,14):
            g=new_game(seed,{**DEFAULT_CONFIG,'block_policy':'all','max_turns':20}); run_game(g,20); seen|={t[0] for t in g.trace}&KINDS
            self.assertEqual(life_ledger(g),g.life,seed)
        from pab_kernel import PhysicalZoneGame                                       # the two kinds no seed reaches: Witherbloom Command mode 4, Blood Artist with no opponent left
        from pab_focus_engine import PEST
        g=PhysicalZoneGame(); g.resolve(); g.advance_to('precombat_main',active_player=0)
        u=next(x for x in g.zones.zones['library'] if g.zones.cards[x].name=='Witherbloom Command'); g.zones.search_library(selected_uid=u,destination='hand')
        g.add_mana('B','G'); g.cast_from_hand(u,modes=(1,4),target_player=0,target_opponent=2); g.resolve()
        g.add('Blood Artist'); g.resolve(); g.drain_opponents(40,'test'); g.resolve(); self.assertTrue(g.game_won)
        p=g.make_tokens(PEST)[0]; g.resolve(); g.sacrifice(p.uid); g.resolve(); seen|={t[0] for t in g.trace}&KINDS
        self.assertEqual(life_ledger(g),g.life); self.assertEqual(seen,KINDS)
    def test_write_report(self):
        rep=validate_games([0],{'max_turns':8})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.json'; write_report(rep,p); back=json.loads(p.read_text(encoding='utf-8')); self.assertEqual(back['all_ok'],rep['all_ok']); self.assertEqual(back['games'][0]['seed'],0)

if __name__=='__main__': unittest.main()
