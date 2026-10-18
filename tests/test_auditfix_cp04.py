"""CP04: clock validator that must reject continued turns after terminal outcomes."""
import unittest
from pab_terminal_audit_cp04 import no_steps_after_terminal
from pab_validation_s19 import new_game,clock_legal,DEFAULT_CONFIG
from pab_policy_s18 import run_game
from pab_kernel import KERNEL_VERSION, PROMOTED

class TerminalValidator(unittest.TestCase):
    def test_01_promoted(self):
        self.assertIn('CP04',PROMOTED);self.assertIn('+CP04',KERNEL_VERSION)

    def test_02_actual_loss_has_no_later_steps(self):
        g=new_game(7,DEFAULT_CONFIG)
        outcome,_,_=run_game(g,18)
        self.assertEqual(outcome,'lost');self.assertTrue(g.game_lost)
        self.assertTrue(no_steps_after_terminal(g.trace)[0])
        self.assertTrue(clock_legal(g)[0])

    def test_03_mutated_trace_after_loss_detected(self):
        g=new_game(7,DEFAULT_CONFIG);run_game(g,18)
        # Construct a fake, clock-contiguous but terminal-illegal next step.
        final=next(t for t in reversed(g.trace) if t[0]=='step_begin')
        self.assertEqual(final[4],'combat_damage')
        g.trace.append(('step_begin',final[1],final[2],'combat','end_of_combat'))
        ok,errors=clock_legal(g)
        self.assertFalse(ok);self.assertTrue(any(e[0]=='step after nonpositive controller life' for e in errors),errors)

    def test_04_legal_recovery_inside_single_resolution(self):
        t=[('step_begin',1,0,'precombat_main','precombat_main'),('lose_life',50,'hypothetical'),('gain',20,'hypothetical'),('step_begin',1,0,'combat','beginning_of_combat')]
        self.assertTrue(no_steps_after_terminal(t)[0])

    def test_05_explicit_winner_blocks_next_step(self):
        t=[('step_begin',1,0,'combat','combat_damage'),('win_game','all_opponents_left'),('step_begin',1,0,'combat','end_of_combat')]
        ok,errors=no_steps_after_terminal(t);self.assertFalse(ok);self.assertEqual(errors[0][0],'step after terminal marker')

    def test_06_timeout_normal_clock_accepted_and_control_negative(self):
        g=new_game(1,{**DEFAULT_CONFIG,'policy':{},'board':[], 'max_turns':3})
        outcome,_,_=run_game(g,3)
        self.assertEqual(outcome,'timeout');self.assertTrue(clock_legal(g)[0])
        t=[('step_begin',1,0,'precombat_main','precombat_main'),('pay_life',41,'test'),('step_begin',1,0,'combat','beginning_of_combat')]
        self.assertFalse(no_steps_after_terminal(t)[0])

if __name__=='__main__': unittest.main()
