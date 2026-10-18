"""Stage S8: opponents as life totals plus a fixed scripted board. Boards declared and
visible as controller 1-3 permanents; Savra black and Grave Pact edicts resolve against
real opposing creatures by the documented policy; no edict when a seat has no creature;
opponent deaths reach the frozen own-card triggers with the frozen labels (parity with
Game.opposing_creature_dies); seats at 0 life leave the game and the clock skips them;
8-seed 8-turn driver run with a 3-creature board per seat. CR refs: 701.19b, 704.5a,
800.4a, 800.4g, 104.2a.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, PEST
from pab_zone_bridge import BridgeError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_focus_engine_v07 import Game as FrozenGame
from pab_opponents_s8 import check_invariants_s8, run_turns_casting, OPPONENT_SEATS
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
BOARD=[{'name':'Bear','power':2,'toughness':2,'colors':'G'},{'name':'Goblin','power':1,'toughness':1,'colors':'R'},{'name':'Wall','power':0,'toughness':4,'colors':'W'}]
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names,seed=0,boards=OPPONENT_SEATS):
        g=PhysicalZoneGame(seed=seed); g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve()
        for s in boards: g.declare_opponent_board(s,BOARD)
        check_invariants_s8(g); return g
    def pest(self,g):
        p=g.make_tokens(PEST)[0]; g.resolve(); check_invariants_s8(g); return p
    def names(self,g,seat): return sorted(p.name for p in g.opponent_creatures(seat))

class Boards(_B):
    def test_kernel_promoted_s8(self):
        self.assertIn('+S8',KERNEL_VERSION); self.assertIn('S8',PROMOTED)
    def test_declared_board_is_visible_as_controller_1_to_3_permanents(self):
        g=self.game()
        for s in OPPONENT_SEATS: self.assertEqual(self.names(g,s),['Bear','Goblin','Wall'])
        self.assertEqual(len(trace(g,'opponent_board_declared')),3); self.assertEqual(g.life,[40,40,40,40])
        self.assertTrue(all(p.controller!=0 for s in OPPONENT_SEATS for p in g.opponent_creatures(s)))
    def test_declaration_refused_for_seat_0_bad_body_or_after_clock_engaged(self):
        g=self.game(boards=())
        with self.assertRaises(BridgeError): g.declare_opponent_board(0,BOARD)
        with self.assertRaises(BridgeError): g.declare_opponent_board(1,[{'name':'x','power':1,'toughness':0}])
        g.advance_step()
        with self.assertRaises(BridgeError): g.declare_opponent_board(1,BOARD)
        self.assertEqual([p for p in g.permanents.values() if p.controller!=0],[])
    def test_essence_warden_sees_an_opponents_creature_enter(self):
        g=PhysicalZoneGame(); g.add(SAVRA); g.add('Essence Warden'); g.resolve(); life=g.life[0]
        g.declare_opponent_board(1,BOARD); g.resolve(); self.assertEqual(g.life[0],life+3)

class Edicts(_B):
    def test_savra_black_edict_each_opponent_sacrifices_lowest_power_then_toughness_then_uid(self):
        g=self.game(); p=self.pest(g); g.sacrifice(p.uid); g.resolve(); check_invariants_s8(g)
        for s in OPPONENT_SEATS: self.assertEqual(self.names(g,s),['Bear','Goblin'])
        self.assertEqual(g.opponent_sacrifices,3); self.assertEqual(g.edicts_resolved,1); self.assertEqual(g.edict_opportunities,1)
        self.assertEqual([(t[1],t[3],t[4]) for t in trace(g,'opponent_sacrifice')],[(s,'Wall','Savra black') for s in OPPONENT_SEATS])
        self.assertEqual(g.life[0],40-2+1+2)                     # paid 2, Pest dies +1, Savra green +2
        g2=self.game(); q=self.pest(g2); g2.sacrifice(q.uid); g2.resolve()
        self.assertEqual(g.life[0],g2.life[0]); self.assertEqual(g2.opponent_sacrifices,3)
    def test_no_edict_when_life_not_paid(self):
        g=self.game(); g.pay_savra_black=False; p=self.pest(g); g.sacrifice(p.uid); g.resolve(); check_invariants_s8(g)
        self.assertEqual((g.edict_opportunities,g.opponent_sacrifices,g.edicts_resolved),(0,0,0))
        for s in OPPONENT_SEATS: self.assertEqual(len(g.opponent_creatures(s)),3)
    def test_green_only_sacrifice_no_edict(self):
        g=self.game('Essence Warden'); w=next(p for p in g.permanents.values() if p.name=='Essence Warden')
        g.sacrifice(w.uid); g.resolve(); self.assertEqual(g.opponent_sacrifices,0); self.assertEqual(trace(g,'opponent_sacrifice'),[])
    def test_seat_without_creatures_is_traced_not_invented(self):
        g=self.game(boards=(2,)); p=self.pest(g); g.sacrifice(p.uid); g.resolve(); check_invariants_s8(g)
        self.assertEqual([(t[1],t[2]) for t in trace(g,'edict_no_creature')],[(1,'Savra black'),(3,'Savra black')])
        self.assertEqual(g.opponent_sacrifices,1); self.assertEqual(self.names(g,2),['Bear','Goblin'])
    def test_grave_pact_edict_on_any_controlled_creature_death(self):
        g=self.game('Grave Pact'); w=g.add('Essence Warden'); g.resolve(); g.destroy(w.uid); g.resolve(); check_invariants_s8(g)
        self.assertEqual(g.opponent_sacrifices,3); self.assertEqual({t[4] for t in trace(g,'opponent_sacrifice')},{'Grave Pact'})
    def test_four_edicts_empty_every_board_then_trace_only(self):
        g=self.game()
        for _ in range(4): p=self.pest(g); g.sacrifice(p.uid); g.resolve(); check_invariants_s8(g)
        self.assertEqual(g.opponent_sacrifices,9); self.assertEqual(len(trace(g,'edict_no_creature')),3)
        for s in OPPONENT_SEATS: self.assertEqual(g.opponent_creatures(s),[])
    def test_counters_count_toward_the_policy(self):
        g=self.game(boards=(1,)); bear=next(p for p in g.opponent_creatures(1) if p.name=='Bear'); wall=next(p for p in g.opponent_creatures(1) if p.name=='Wall')
        bear.minus_counters=1; wall.counters=3     # Bear 1/1 ties Goblin 1/1 and wins on uid; Wall 3/7 (S15: a creature at 0 toughness would die to the SBA before any edict)
        p=self.pest(g); g.sacrifice(p.uid); g.resolve(); self.assertEqual(self.names(g,1),['Goblin','Wall'])
    def test_frozen_fixture_paths_without_boards_unchanged(self):
        g=self.game(boards=()); p=self.pest(g); g.sacrifice(p.uid); g.resolve()
        self.assertEqual((g.edict_opportunities,g.opponent_sacrifices),(1,0)); self.assertEqual(len(trace(g,'edict_no_creature')),3)

class OpponentDeaths(_B):
    OWN=('Deathgreeter','Poison-Tip Archer','Blood Artist','Yahenni, Undying Partisan','Sangromancer')
    def test_parity_with_frozen_exogenous_trigger_labels(self):
        f=FrozenGame(); f.add(SAVRA)
        for n in self.OWN: f.add(n)
        f.resolve(); f.opposing_creature_dies('x'); frozen=[t.label for t in f.pending]
        g=self.game(*self.OWN,boards=(1,)); u=g.opponent_creatures(1)[0].uid; g._opponent_creature_dies(u,cause='test')
        self.assertEqual([t.label for t in g.pending],frozen); self.assertEqual(len(frozen),5)
        self.assertEqual(trace(g,'external_opponent_creature_dies'),[])
    def test_own_cards_react_to_an_edict_death(self):
        g=self.game(*self.OWN,boards=(1,)); ya=next(p for p in g.permanents.values() if p.name=='Yahenni, Undying Partisan'); life=g.life[0]; opp=g.life[1:]
        p=self.pest(g); g.sacrifice(p.uid); g.resolve(); check_invariants_s8(g)
        self.assertEqual(ya.counters,1)                                                                 # one opponent creature died
        self.assertEqual(g.life[0],life-2+1+2 +(1+1+3) +(1+1))   # paid 2, Pest +1, Savra green +2; opposing death: Deathgreeter, Blood Artist, Sangromancer; Pest's own death: Deathgreeter, Blood Artist
        self.assertEqual(g.life[1],opp[0]-2-1-1)                                                        # Blood Artist x2, Archer x1 (opposing death only)
    def test_refuses_own_or_missing_creature(self):
        g=self.game('Deathgreeter'); d=next(p for p in g.permanents.values() if p.name=='Deathgreeter')
        with self.assertRaises(BridgeError): g._opponent_creature_dies(d.uid,cause='x')
        with self.assertRaises(BridgeError): g._opponent_creature_dies(999,cause='x')

class LeavingTheGame(_B):
    def test_seat_at_zero_life_leaves_permanents_leave_without_triggers(self):
        g=self.game('Blood Artist','Deathgreeter'); g.life[1]=0; life=g.life[0]; g.resolve(); check_invariants_s8(g)
        self.assertEqual(g.lost_seats,{1}); self.assertEqual(g.opponent_creatures(1),[]); self.assertEqual(g.life[0],life)
        self.assertEqual(len(trace(g,'seat_leaves_game')),1); self.assertEqual(trace(g,'opponent_creature_dies'),[])
    def test_clock_skips_a_lost_seats_later_turns_but_finishes_the_current_one(self):
        g=self.game('Beledros Witherbloom'); g.advance_to('precombat_main',active_player=1); g.life[1]=0; g.resolve()
        self.assertEqual(g.clock.active_player,1)                                  # CR 800.4g: turn under way continues
        starts=[]
        for _ in range(70):
            t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s8(g)
            if st=='untap': starts.append((t,ap))
        self.assertEqual(starts[:4],[(3,2),(4,3),(5,0),(7,2)]); self.assertEqual(g.clock.skipped[:1],[(6,1)])            # turn 2 was not skipped: it was under way
        upkeeps=[t for t in trace(g,'step_begin') if t[4]=='upkeep' and t[2]==1]; self.assertEqual(len(upkeeps),1)   # seat 1 had one upkeep (turn 2) before leaving
    def test_edicts_drains_and_blood_artist_skip_lost_seats(self):
        g=self.game('Blood Artist','Poison-Tip Archer'); g.life[1]=0; g.resolve(); opp=list(g.life)
        p=self.pest(g); g.sacrifice(p.uid); g.resolve(); check_invariants_s8(g)
        self.assertEqual(g.life[1],0)                                               # untouched after leaving
        self.assertEqual([t[1] for t in trace(g,'opponent_sacrifice')],[2,3])
        self.assertLess(g.life[2],opp[2]); self.assertLess(g.life[3],opp[3]); self.assertEqual(trace(g,'edict_no_creature'),[])
    def test_all_opponents_left_is_a_recorded_win(self):
        g=self.game('Blood Artist'); g.life[1]=g.life[2]=g.life[3]=0; g.resolve(); check_invariants_s8(g)
        self.assertTrue(g.game_won); self.assertEqual(len(trace(g,'win_game')),1); self.assertEqual(g.lost_seats,{1,2,3})
        p=self.pest(g); g.sacrifice(p.uid); g.resolve(); self.assertEqual(trace(g,'target_self_loses'),[('target_self_loses',1,'Blood Artist')])

class Driver(_B):
    def test_eight_seeds_eight_turns_with_three_creature_boards(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=self.game(seed=seed); opening_hand(g); ledger=run_turns_casting(g,8)
                self.assertEqual([t for t,*_ in ledger],[1,5]); self.assertEqual(g.lost_seats,set())
                self.assertEqual(sum(len(g.opponent_creatures(s)) for s in OPPONENT_SEATS),9-g.opponent_sacrifices)
                self.assertEqual(g.opponent_sacrifices,len(trace(g,'opponent_sacrifice'))); self.assertGreaterEqual(g.sba_checks,1)
    def test_driver_village_rites_on_a_pest_produces_a_real_edict(self):
        from pab_cast_s7 import cast_when_able
        g=self.game(seed=0); opening_hand(g); g.advance_to('precombat_main',active_player=0)
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Village Rites'); g.zones.search_library(selected_uid=uid,destination='hand')
        self.pest(g); g.add_mana('B'); self.assertEqual(cast_when_able(g),['Village Rites']); check_invariants_s8(g)
        self.assertEqual(g.opponent_sacrifices,3); self.assertEqual(g.cards_drawn,3)   # draw step + 2

if __name__=='__main__': unittest.main()
