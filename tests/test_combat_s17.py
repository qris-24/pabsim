"""Stage S17: combat. Declaration rules (step, summoning sickness, haste, tapped, seat),
attack triggers, 'none' and 'all' block policies with menace, simultaneous damage with
deathtouch and the Pest bonuses, lethal-damage SBA with look-back, damage wearing off,
commander damage loss, driver run. """
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, PEST, MOSEO_PEST
from pab_zone_bridge import BridgeError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_combat_s17 import check_invariants_s17, run_turns_full, attack_policy, COMMANDER_DAMAGE_LOSS
from pab_opponents_s8 import OPPONENT_SEATS
from pab_turn_loop import opening_hand
from pab_validation_s19 import life_ledger

BOARD=[{'name':'Bear','power':2,'toughness':2,'mana_value':2},{'name':'Wall','power':0,'toughness':4,'mana_value':3}]
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names,policy='none',board=True):
        g=PhysicalZoneGame(block_policy=policy)
        for n in names: g.add(n)
        g.resolve()
        if board:
            for s in OPPONENT_SEATS: g.declare_opponent_board(s,BOARD)
        g.advance_to('precombat_main',active_player=0); g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve(); check_invariants_s17(g)
        return g
    def savra(self,g): return next(p for p in g.permanents.values() if p.name==SAVRA)
    def next_attack_step(self,g):
        g.advance_to('cleanup',active_player=0); g.advance_to('declare_attackers',active_player=0); g.resolve(); check_invariants_s17(g)
    def to_damage(self,g):
        g.advance_to('combat_damage',active_player=0); g.resolve(); check_invariants_s17(g)

class Declaration(_B):
    def test_kernel_promoted_and_declaration_rules(self):
        self.assertIn('+S17',KERNEL_VERSION); self.assertIn('S17',PROMOTED)
        g=self.game(); sv=self.savra(g); pe=g.make_tokens(PEST)[0]; g.resolve()
        with self.assertRaises(BridgeError): g.declare_attackers([(sv.uid,1)])                       # main phase
        g.advance_to('declare_attackers',active_player=0)
        with self.assertRaises(BridgeError): g.declare_attackers([(sv.uid,1)])                       # summoning sick (cast this turn)
        with self.assertRaises(BridgeError): g.declare_attackers([(pe.uid,1)])                       # token made this turn
        self.next_attack_step(g)
        with self.assertRaises(BridgeError): g.declare_attackers([(sv.uid,0)])                       # not a seat in the game
        with self.assertRaises(BridgeError): g.declare_attackers([(sv.uid,1),(sv.uid,2)])
        g.declare_attackers([(sv.uid,1),(pe.uid,2)]); g.resolve(); self.assertTrue(sv.tapped and pe.tapped); self.assertEqual(g.attackers,{sv.uid:1,pe.uid:2})
        with self.assertRaises(BridgeError): g.declare_attackers([(sv.uid,1)])                       # already declared
        self.assertEqual([t[1] for t in trace(g,'attack')],[sv.uid,pe.uid]); check_invariants_s17(g)
        ya=g.add('Yahenni, Undying Partisan'); g.advance_to('cleanup',active_player=0); g.advance_to('precombat_main',active_player=0); g.permanents  # new turn
        g.advance_to('declare_attackers',active_player=0); ya2=g.add('Yahenni, Undying Partisan'); g.declare_attackers([(ya2.uid,1)])   # haste: attacks the turn it entered
        with self.assertRaises(BridgeError): g.declare_attackers([(ya.uid,1)])
    def test_attack_triggers_and_unblocked_damage_commander_damage(self):
        g=self.game("Moseo, Vein's New Dean","Teacher's Pest"); sv=self.savra(g); mp=next(p for p in g.permanents.values() if p.token==MOSEO_PEST); tp=next(p for p in g.permanents.values() if p.name=="Teacher's Pest")
        self.next_attack_step(g); life=g.life[0]; g.declare_attackers([(sv.uid,1),(mp.uid,1),(tp.uid,2)]); g.resolve()
        self.assertEqual(g.life[0],life+2)                                                            # Moseo Pest + Teacher's Pest attack gains
        self.to_damage(g); ev=trace(g,'combat_damage')[-1][1]
        self.assertEqual(g.life[1],40-2-1); self.assertEqual(g.life[2],40-1); self.assertEqual(g.commander_damage,{1:2,2:0,3:0})   # fixture Teacher's Pest is 1/1
        self.assertEqual(sorted(ev),sorted([('player',1,sv.uid,2),('player',1,mp.uid,1),('player',2,tp.uid,1)]))
        g.advance_to('end_of_combat',active_player=0); self.assertEqual(g.attackers,{})
    def test_commander_damage_loss(self):
        g=self.game(board=False); sv=self.savra(g); g.commander_damage[1]=COMMANDER_DAMAGE_LOSS-2
        self.next_attack_step(g); g.declare_attackers([(sv.uid,1)]); g.resolve(); self.to_damage(g)
        self.assertEqual(g.commander_damage[1],COMMANDER_DAMAGE_LOSS); self.assertIn(1,g.lost_seats); self.assertEqual(trace(g,'commander_damage_loss'),[('commander_damage_loss',1,21)])
        self.assertEqual(g.seats_in_game(),[2,3])

class Blocks(_B):
    def test_all_policy_blocks_biggest_menace_needs_two_deathtouch_kills(self):
        g=self.game('Feral Appetite','Blight Mound',policy='all'); pe=g.make_tokens(PEST)[0]; g.resolve(); sv=self.savra(g)
        self.next_attack_step(g); g.declare_attackers([(pe.uid,1),(sv.uid,1)]); g.resolve()
        g.advance_to('declare_blockers',active_player=0)
        bear=next(q.uid for q in g.opponent_creatures(1) if q.name=='Bear'); wall=next(q.uid for q in g.opponent_creatures(1) if q.name=='Wall')
        self.assertEqual(g.blocks,{sv.uid:[bear,wall]})                                               # the 3/1 menace Pest cannot be the lone block of either creature in turn; both block Savra
        self.to_damage(g); self.assertEqual(g.life[1],40-3); self.assertNotIn(sv.uid,g.permanents); self.assertNotIn(bear,g.permanents)   # Pest unblocked for 3; Savra and Bear trade
    def test_deathtouch_pest_kills_blocker_and_dies_damage_wears_off(self):
        g=self.game('Feral Appetite',policy='all'); pe=g.make_tokens(PEST)[0]; g.resolve(); bear=next(q.uid for q in g.opponent_creatures(1) if q.name=='Bear')
        self.next_attack_step(g); g.declare_attackers([(pe.uid,1)]); g.resolve(); g.advance_to('declare_blockers',active_player=0); self.assertEqual(g.blocks,{pe.uid:[bear,next(q.uid for q in g.opponent_creatures(1) if q.name=='Wall')]})
        self.to_damage(g); self.assertNotIn(bear,g.permanents); self.assertNotIn(pe.uid,g.permanents)      # Pest 2/1 deathtouch vs Bear 2/2: both die; Wall survives
        self.assertTrue(any(q.name=='Wall' for q in g.opponent_creatures(1))); self.assertEqual(g.life[1],40)
        g.advance_to('cleanup',active_player=0); self.assertEqual(g.damage_marked,{}); self.assertTrue(trace(g,'damage_wears_off'))
    def test_savra_blocked_by_wall_survives_marked_damage_then_dies_to_a_minus(self):
        g=self.game(policy='all'); sv=self.savra(g)
        for q in list(g.opponent_creatures(1)):
            if q.name=='Wall': g._opponent_creature_dies(q.uid,cause='setup')
        self.next_attack_step(g); g.declare_attackers([(sv.uid,1)]); g.resolve(); g.advance_to('declare_blockers',active_player=0)
        bear=next(q.uid for q in g.opponent_creatures(1)); self.assertEqual(g.blocks,{sv.uid:[bear]})
        self.to_damage(g); self.assertNotIn(bear,g.permanents); self.assertNotIn(sv.uid,g.permanents)      # 2/2 trades with 2/2
        self.assertEqual(g.zones.cards[g.zones.zones['command'][0]].name,SAVRA); self.assertEqual(g.commander_deaths,1)

class Driver(_B):
    def test_full_driver_eight_seeds_forty_turns_no_blocks_and_all_blocks(self):
        for policy in ('none','all'):
            for seed in (0,1,2,3,4,7,11,42):                                       # CP42 (T2): eight seeds, as the name says (was four)
                with self.subTest(policy=policy,seed=seed):
                    g=PhysicalZoneGame(seed=seed,learn_sideboard_allowed=True,block_policy=policy); opening_hand(g)
                    for s in OPPONENT_SEATS: g.declare_opponent_board(s,BOARD)
                    ledger=run_turns_full(g,40); self.assertEqual(len(ledger),10); self.assertEqual(g.attackers,{}); self.assertEqual(g.damage_marked,{})
                    dealt=sum(d for _,_,_,_,_,ev in ledger for kind,*rest in ev if kind=='player' for d in [rest[2]])
                    per={s:sum(rest[2] for _,_,_,_,_,ev in ledger for kind,*rest in ev if kind=='player' and rest[0]==s) for s in OPPONENT_SEATS}
                    for s in OPPONENT_SEATS: self.assertGreaterEqual(40-g.life[s],per[s])        # CP42 (T2, was a tautology): opponents gain no life, so each lost at least its combat damage
                    self.assertEqual(life_ledger(g),g.life)                                          # and the trace accounts for every life change
                    if policy=='none': self.assertGreater(dealt,0)
    def test_attack_policy_targets_lowest_life_and_keeps_savra_home_against_blockers(self):
        g=self.game(policy='all'); sv=self.savra(g); g.life[2]=10; self.next_attack_step(g)
        self.assertEqual(attack_policy(g),[])                                                            # Savra stays home: seat 2 has untapped blockers
        for q in list(g.opponent_creatures(2)): g._opponent_creature_dies(q.uid,cause='setup')
        self.assertEqual(attack_policy(g),[(sv.uid,2)])

if __name__=='__main__': unittest.main()
