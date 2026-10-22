"""CP02 independent executable regression contracts for A-S20-01 and A-S20-02.

All cases reproduce behavior at public kernel entrypoint; no edits to frozen tests.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))   # CP42 (T6): imports work without the runner's sys.path
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_focus_engine import SAVRA
from pab_policy_s18 import run_game
from pab_auditfix_cp02 import run_game_terminal
from pab_opponents_s8 import OPPONENT_SEATS
from pab_turn_loop import opening_hand

class CombatBlockedStatus(unittest.TestCase):
    def setup_combat(self, attacker_from_seat=0, blockers=1):
        g=PhysicalZoneGame(block_policy='all')
        if attacker_from_seat==0:
            a=g.add(SAVRA,controller=0,creature=True,power=2,toughness=2)
            seat=1
            targets=g.declare_opponent_board(1,[{'name':f'Blocker-{i}','power':1,'toughness':1} for i in range(blockers)])
        else:
            a=g.declare_opponent_board(1,[{'name':'Attacker','power':2,'toughness':2}])[0]
            seat=0
            targets=[g.add('Deathgreeter',controller=0,creature=True,power=1,toughness=1).uid for i in range(blockers)]
        auid=a.uid if hasattr(a,'uid') else a
        g.attackers={auid:seat}
        g.blocks={auid:list(targets)}
        return g,auid,seat,targets

    def remove_blocker(self,g,seat,uid):
        if seat==1: g._opponent_creature_dies(uid,cause='CP02 removed blocker')
        else:
            g.destroy(uid);g.resolve()

    def test_candidate_scope_and_version(self):
        self.assertIn('CP02',PROMOTED)
        self.assertIn('+CP02',KERNEL_VERSION)

    def test_blocked_attacker_no_player_damage_if_only_blocker_removed(self):
        g,a,seat,bs=self.setup_combat()
        self.remove_blocker(g,seat,bs[0]);g._combat_damage()
        self.assertEqual(g.life[seat],40)
        self.assertEqual(g.commander_damage[seat],0)
        self.assertEqual(g.combat_log[-1][1],())

    def test_originally_unblocked_attacker_still_damages_player(self):
        g,a,seat,bs=self.setup_combat()
        g.blocks={};g._combat_damage()
        self.assertEqual(g.life[seat],38)
        self.assertEqual(g.commander_damage[seat],0) # synthetic Savra has no physical UID

    def test_still_present_blocker_absorbs_combat_damage(self):
        g,a,seat,bs=self.setup_combat()
        g._combat_damage()
        self.assertEqual(g.life[seat],40)
        self.assertEqual(g.combat_log[-1][1][0][0],'creature')

    def test_multiple_original_blockers_gone_no_player_damage(self):
        g,a,seat,bs=self.setup_combat(blockers=2)
        for b in bs: self.remove_blocker(g,seat,b)
        g._combat_damage()
        self.assertEqual(g.life[seat],40)
        self.assertEqual(g.combat_log[-1][1],())

    def test_one_remaining_of_two_blocks_damage(self):
        g,a,seat,bs=self.setup_combat(blockers=2)
        self.remove_blocker(g,seat,bs[0]);g._combat_damage()
        self.assertEqual(g.life[seat],40)
        self.assertTrue(any(ev[0]=='creature' for ev in g.combat_log[-1][1]))

    def test_normal_clock_declare_blocks_then_remove_blocker_before_damage(self):
        g,a,seat,bs=self.setup_combat()
        g.blocks={}
        g.advance_to('declare_blockers',active_player=0)
        self.assertEqual(g._cp02_blocked_attackers,{a})
        self.remove_blocker(g,seat,bs[0])
        g.advance_to('combat_damage',active_player=0)
        self.assertEqual(g.life[seat],40)
        self.assertEqual(g.combat_log[-1][1],())

    def test_controller_not_hit_by_blocked_opponent_after_blocker_removed(self):
        g,a,seat,bs=self.setup_combat(attacker_from_seat=1)
        self.remove_blocker(g,seat,bs[0]);g._combat_damage()
        self.assertEqual(g.life[0],40)
        self.assertEqual(g.combat_log[-1][1],())

    def test_removed_attacker_does_not_damage_unblocked(self):
        g,a,seat,bs=self.setup_combat()
        g.blocks={};g.destroy(a);g.resolve();g._combat_damage()
        self.assertEqual(g.life[seat],40)

    def test_original_blocked_status_survives_block_map_reset(self):
        g,a,seat,bs=self.setup_combat()
        g._cp02_blocked_attackers.add(a)
        g.blocks={};g._combat_damage()
        self.assertEqual(g.life[seat],40)

class TerminalTurnGate(unittest.TestCase):
    @staticmethod
    def loss_game():
        g=PhysicalZoneGame(seed=7,block_policy='none');opening_hand(g)
        for seat in OPPONENT_SEATS:
            g.declare_opponent_board(seat,[{'name':'Bear','power':2,'toughness':2}])
            g.set_opponent_policy(seat,{'attack':'all'})
        g.life[0]=1
        return g

    def test_terminal_loss_stops_before_more_steps_and_batch_overshoot(self):
        g=self.loss_game()
        outcome,t,rows=run_game(g,max_turns=9)
        self.assertEqual(outcome,'lost');self.assertEqual(t,2)
        self.assertEqual(len(rows),1)
        hit=next(i for i,x in enumerate(g.trace) if x[0]=='combat_damage' and any(ev[0]=='player' and ev[1]==0 for ev in x[1]))
        self.assertEqual([x for x in g.trace[hit+1:] if x[0]=='step_begin'],[])

    def test_terminal_loss_cannot_begin_next_player_phase(self):
        g=self.loss_game()
        run_game_terminal(g,max_turns=60)
        steps=[x for x in g.trace if x[0]=='step_begin']
        self.assertLessEqual(max(x[1] for x in steps if isinstance(x[1],int)),2)
        self.assertTrue(g.game_lost)

    def test_terminal_win_immediately_stops_clock(self):
        g=PhysicalZoneGame(block_policy='none')
        for seat in (2,3): g.life[seat]=0
        g.life[1]=1
        g.state_based_actions()
        g.add('Deathgreeter',creature=True,controller=0,power=1,toughness=1)
        outcome,t,rows=run_game(g,max_turns=60)
        self.assertEqual(outcome,'won')
        self.assertEqual(t,1)
        self.assertFalse(g.game_lost)
        self.assertTrue(g.game_won)
        damage=next(i for i,x in enumerate(g.trace) if x[0]=='combat_damage' and any(ev[0]=='player' for ev in x[1]))
        self.assertFalse(any(x[0]=='step_begin' for x in g.trace[damage+1:]))

    def test_preexisting_terminal_flag_does_not_advance_step(self):
        g=self.loss_game();g.game_lost=True
        before=list(g.trace);start=g.clock.turn
        self.assertEqual(run_game(g,max_turns=40),('lost',start,[]))
        self.assertEqual(g.trace,before)

    def test_timeout_honors_max_turns_not_four_turn_overshoot(self):
        g=PhysicalZoneGame(block_policy='none')
        out,t,_=run_game(g,max_turns=2)
        self.assertEqual((out,t),('timeout',2))
        self.assertFalse(g.game_lost or g.game_won)

if __name__=='__main__': unittest.main()
