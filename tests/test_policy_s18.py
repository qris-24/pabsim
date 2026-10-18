"""Stage S18: policy opponents. Policy declaration; each rule fires with its reason and
consumes its budget; priority order; hexproof respected; opponents untap and attack the
controller; the controller's blocks; the controller can lose; R55 (Unearth on a
token-making creature) regression; whole games end. """
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, PEST
from pab_zone_bridge import BridgeError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_policy_s18 import run_game, check_invariants_s18
from pab_opponents_s8 import OPPONENT_SEATS
from pab_turn_loop import opening_hand

BOARD=[{'name':'Bear','power':2,'toughness':2,'mana_value':2},{'name':'Knight','power':3,'toughness':3,'mana_value':3}]
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,policies,*names,bp='none',board=True):
        g=PhysicalZoneGame(block_policy=bp)
        for n in names: g.add(n)
        g.resolve()
        for s in OPPONENT_SEATS:
            if board: g.declare_opponent_board(s,BOARD)
            if s in policies: g.set_opponent_policy(s,policies[s])
        check_invariants_s18(g); return g
    def savra(self,g):
        g.advance_to('precombat_main',active_player=0); g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve(); return next(p for p in g.permanents.values() if p.name==SAVRA)
    def to_main(self,g,seat):
        g.advance_to('precombat_main',active_player=seat); g.resolve(); check_invariants_s18(g)
    def creature(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=uid,destination='hand'); g.add_mana('B','B','G','G','C','C','C','C'); g.cast_from_hand(uid); g.resolve(); del g.mana_pool[:]
        return next(p for p in g.permanents.values() if p.name==name)

class Policies(_B):
    def test_kernel_promoted_and_declaration(self):
        self.assertIn('+S18',KERNEL_VERSION); self.assertIn('S18',PROMOTED)
        g=self.game({})
        with self.assertRaises(BridgeError): g.set_opponent_policy(0,{'edict_budget':1})
        with self.assertRaises(BridgeError): g.set_opponent_policy(1,{'counterspells':1})
        with self.assertRaises(BridgeError): g.set_opponent_policy(1,{'attack':'sometimes'})
        g.set_opponent_policy(1,{'wipe_at':3}); self.assertEqual(g.opponent_policy[1]['wipe_budget'],1); g.advance_step()
        with self.assertRaises(BridgeError): g.set_opponent_policy(2,{'edict_budget':1})
    def test_removal_prefers_savra_then_power_and_spends_budget(self):
        g=self.game({1:{'removal_budget':2,'removal_min_power':3}}); sv=self.savra(g); w=self.creature(g,'Sedgemoor Witch')
        self.to_main(g,1); self.assertEqual(g.policy_actions,[(2,1,'destroy_commander','Savra on the battlefield')]); self.assertEqual(g.zones.cards[g.zones.zones['command'][0]].name,SAVRA)
        self.to_main(g,1); self.assertEqual(g.policy_actions[-1][2:],('destroy_creature','Sedgemoor Witch power 3')); self.assertNotIn(w.uid,g.permanents); self.assertEqual(g.opponent_policy[1]['removal_budget'],0)
        self.to_main(g,0); d=self.creature(g,'Deathgreeter'); self.to_main(g,1); self.assertEqual(len(g.policy_actions),2)      # budget spent
    def test_wipe_threshold_then_graveyard_hate_then_edict_in_that_order(self):
        g=self.game({2:{'wipe_at':3,'graveyard_hate_at':2,'edict_budget':1}}); g.make_tokens(PEST,3); g.resolve()
        self.to_main(g,2); self.assertEqual(g.policy_actions[-1][2],'board_wipe'); self.assertEqual(g.opponent_policy[2]['wipe_budget'],0)
        for n in ('Swamp','Forest'):
            u=next(x for x in g.zones.zones['library'] if g.zones.cards[x].name==n); g.zones.move(u,'graveyard')
        self.to_main(g,2); self.assertEqual(g.policy_actions[-1][2],'graveyard_exile'); self.assertEqual(g.zones.zones['graveyard'],[])
        g.make_tokens(PEST); g.resolve(); self.to_main(g,2); self.assertEqual(g.policy_actions[-1][2],'edict')
        g.make_tokens(PEST); g.resolve(); self.to_main(g,2); self.assertEqual(len(g.policy_actions),3)                          # all budgets spent
        self.assertEqual(len(trace(g,'opponent_action')),3)
    def test_hexproof_savra_is_not_a_removal_target(self):
        g=self.game({1:{'removal_budget':1}}); sv=self.savra(g)
        g.advance_to('upkeep',active_player=1); uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Heroic Intervention'); g.zones.search_library(selected_uid=uid,destination='hand'); g.add_mana('G','C'); g.cast_from_hand(uid); g.resolve()
        self.to_main(g,1); self.assertEqual(g.policy_actions,[]); self.assertIn(sv.uid,g.permanents); self.assertEqual(g.opponent_policy[1]['removal_budget'],1)   # nothing legal: budget kept

class Attacks(_B):
    def test_opponents_untap_and_attack_the_controller_each_turn(self):
        g=self.game({1:{'attack':'all'}}); g.advance_to('combat_damage',active_player=1); g.resolve()
        self.assertEqual(g.life[0],40-5); self.assertEqual(trace(g,'opponent_attackers_declared')[-1][1],1)
        g.advance_to('combat_damage',active_player=1); g.resolve(); self.assertEqual(g.life[0],40-10); self.assertEqual(trace(g,'opponent_untap_step')[-1][1:],(1,6,2))
        g.advance_to('combat_damage',active_player=2); g.resolve(); self.assertEqual(g.life[0],30)                              # seat 2 has no attack policy
    def test_controller_blocks_under_all_and_savra_never_blocks(self):
        g=self.game({1:{'attack':'all'}},'Poison-Tip Archer',bp='all'); sv=self.savra(g); pta=next(p for p in g.permanents.values() if p.name=='Poison-Tip Archer')
        g.advance_to('declare_blockers',active_player=1); knight=next(q.uid for q in g.opponent_creatures(1) if q.name=='Knight')
        self.assertEqual(g.blocks,{knight:[pta.uid]}); self.assertNotIn(sv.uid,[b for bs in g.blocks.values() for b in bs])
        g.advance_to('combat_damage',active_player=1); g.resolve(); check_invariants_s18(g)
        self.assertNotIn(knight,g.permanents); self.assertNotIn(pta.uid,g.permanents); self.assertEqual(g.life[0],40-2)         # deathtouch kills the Knight; Bear unblocked for 2
    def test_controller_can_lose(self):
        g=self.game({s:{'attack':'all'} for s in OPPONENT_SEATS}); g.life[0]=12
        g.advance_to('precombat_main',active_player=0); g.advance_to('combat_damage',active_player=3); g.resolve(); check_invariants_s18(g)
        self.assertTrue(g.game_lost); self.assertLessEqual(g.life[0],0); self.assertEqual(g.pending.__len__(),0)                 # frozen resolve() adjudicates at entry (no trace line in that branch)

class WholeGames(_B):
    def test_r55_unearth_on_a_token_making_creature(self):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve(); m=self.creature(g,"Moseo, Vein's New Dean"); muid=g.linked_battlefield[m.uid]; g.destroy(m.uid); g.resolve()
        un=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Unearth'); g.zones.search_library(selected_uid=un,destination='hand'); g.add_mana('B'); g.cast_from_hand(un,target_uid=m.uid); g.resolve(); check_invariants_s18(g)
        back=next(p for p in g.permanents.values() if p.name=="Moseo, Vein's New Dean"); self.assertEqual(g.linked_battlefield[back.uid],muid); self.assertIn(('r55_safe_order',"Moseo, Vein's New Dean"),g.trace)
    def test_whole_games_end_with_an_outcome_and_invariants(self):
        pol={1:{'removal_budget':2,'attack':'all'},2:{'wipe_at':4,'edict_budget':1,'attack':'all'},3:{'graveyard_hate_at':5,'attack':'all','exile_instead':True,'removal_budget':1}}
        outcomes=set()
        for seed in (0,1,7,42):
            for bp in ('none','all'):
                with self.subTest(seed=seed,bp=bp):
                    g=PhysicalZoneGame(seed=seed,learn_sideboard_allowed=True,block_policy=bp); opening_hand(g)
                    for s in OPPONENT_SEATS: g.declare_opponent_board(s,BOARD); g.set_opponent_policy(s,pol[s])
                    out,t,ledger=run_game(g,60); outcomes.add(out); self.assertIn(out,('lost','won','timeout')); self.assertLessEqual(t,61)
                    if out=='lost': self.assertTrue(g.game_lost)
        self.assertTrue(outcomes)

if __name__=='__main__': unittest.main()
