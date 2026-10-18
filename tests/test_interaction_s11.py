"""Stage S11: scripted opponent interaction. Declaration and firing on the scripted seat's
precombat main; the six actions with their fixed target policies; board wipe as one event
with look-back triggers (CR 603.10a); Savra's return after destroy/exile (903.9a);
graveyard exile drops links and LKI; indestructible survives a wipe; lost seats do not act;
driver run with boards and a script. """
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, PEST
from pab_zone_bridge import BridgeError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_interaction_s11 import check_invariants_s11, run_turns_casting, KINDS
from pab_opponents_s8 import OPPONENT_SEATS
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
BOARD=[{'name':'Bear','power':2,'toughness':2,'colors':'G'},{'name':'Wall','power':0,'toughness':4,'colors':'W'}]
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names,boards=OPPONENT_SEATS):
        g=PhysicalZoneGame()
        for n in names: g.add(n)
        g.resolve()
        for s in boards: g.declare_opponent_board(s,BOARD)
        check_invariants_s11(g); return g
    def savra(self,g):
        g.advance_to('precombat_main',active_player=0); g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve(); check_invariants_s11(g)
        return next(p for p in g.permanents.values() if p.name==SAVRA)
    def to_main(self,g,seat,turn):
        while not (g.clock.step=='precombat_main' and g.clock.active_player==seat and g.clock.turn==turn):
            g.advance_step(); g.resolve(); check_invariants_s11(g)
    def hand_creature(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=uid,destination='hand')
        g.add_mana('B','B','G','G','C','C','C'); g.cast_from_hand(uid); g.resolve(); check_invariants_s11(g)
        return next(p for p in g.permanents.values() if p.name==name)

class Declaration(_B):
    def test_kernel_promoted_and_declaration_rules(self):
        self.assertIn('+S11',KERNEL_VERSION); self.assertIn('S11',PROMOTED); self.assertEqual(len(KINDS),6)
        g=self.game()
        with self.assertRaises(BridgeError): g.script_opponent_actions(0,[{'turn':2,'kind':'edict'}])
        with self.assertRaises(BridgeError): g.script_opponent_actions(1,[{'turn':2,'kind':'counterspell'}])
        with self.assertRaises(BridgeError): g.script_opponent_actions(1,[{'turn':0,'kind':'edict'}])
        g.script_opponent_actions(1,[{'turn':2,'kind':'edict'}]); g.advance_step()
        with self.assertRaises(BridgeError): g.script_opponent_actions(2,[{'turn':3,'kind':'edict'}])
        self.assertEqual(len(g.opponent_script),1)
    def test_fires_only_on_the_scripted_seats_main_of_that_turn(self):
        g=self.game(); g.script_opponent_actions(2,[{'turn':3,'kind':'edict'}]); p=g.make_tokens(PEST)[0]; g.resolve()
        self.to_main(g,1,2); self.assertIn(p.uid,g.permanents)
        self.to_main(g,2,3); self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.opponent_actions_done,[(3,2,'edict')]); self.assertEqual(g.opponent_script,[])
    def test_lost_seat_does_not_act(self):
        g=self.game(); g.script_opponent_actions(1,[{'turn':6,'kind':'edict'}]); g.life[1]=0; g.resolve(); p=g.make_tokens(PEST)[0]; g.resolve()
        for _ in range(80): g.advance_step(); g.resolve(); check_invariants_s11(g)
        self.assertIn(p.uid,g.permanents); self.assertEqual(g.opponent_actions_done,[])

class Actions(_B):
    def test_destroy_commander_sends_savra_to_command_zone_with_dies_triggers(self):
        g=self.game('Blood Artist','Deathgreeter'); g.script_opponent_actions(1,[{'turn':2,'kind':'destroy_commander'}]); sv=self.savra(g); uid=g.linked_battlefield[sv.uid]; life=g.life[0]
        self.to_main(g,1,2); g.resolve(); check_invariants_s11(g)
        self.assertEqual(g.zones.cards[uid].zone,'command'); self.assertEqual(g.commander_deaths,1); self.assertEqual(g.life[0],life+2); self.assertEqual(g.life[1],39)
        self.assertIn(('destroy',sv.uid,SAVRA),g.trace)
    def test_destroy_commander_without_savra_is_a_no_target(self):
        g=self.game(); g.script_opponent_actions(1,[{'turn':2,'kind':'destroy_commander'}]); self.to_main(g,1,2)
        self.assertEqual(trace(g,'no_target'),[('no_target',1,'destroy_commander')]); self.assertEqual(len(g.zones.zones['command']),1)
    def test_destroy_creature_picks_highest_power_nontoken_savra_last_tokens_never(self):
        g=self.game(); g.script_opponent_actions(1,[{'turn':2,'kind':'destroy_creature'},{'turn':6,'kind':'destroy_creature'}]); sv=self.savra(g)
        w=self.hand_creature(g,'Sedgemoor Witch'); g.make_tokens(PEST,3); g.resolve()
        self.to_main(g,1,2); self.assertNotIn(w.uid,g.permanents); self.assertIn(sv.uid,g.permanents); self.assertEqual(sum(1 for p in g.permanents.values() if p.token==PEST),3)
        self.to_main(g,1,6); self.assertNotIn(sv.uid,g.permanents); self.assertEqual(g.commander_deaths,1); self.assertEqual(sum(1 for p in g.permanents.values() if p.token==PEST),3)
    def test_exile_creature_no_dies_triggers_card_in_exile_savra_returns(self):
        g=self.game(); g.script_opponent_actions(1,[{'turn':2,'kind':'exile_creature'},{'turn':6,'kind':'exile_creature'}]); sv=self.savra(g)
        w=self.hand_creature(g,'Sedgemoor Witch'); wuid=g.linked_battlefield[w.uid]; life=g.life[0]
        self.to_main(g,1,2); self.assertEqual(g.zones.cards[wuid].zone,'exile'); self.assertEqual(g.life[0],life); self.assertNotIn(w.uid,g.linked_battlefield); self.assertEqual(g.cards_exiled,['Sedgemoor Witch'])
        self.to_main(g,1,6); self.assertEqual(g.zones.cards[g.zones.zones['command'][0]].name,SAVRA); self.assertEqual(trace(g,'commander_to_command_zone')[-1][2],'exile'); self.assertEqual(g.life[0],life)
    def test_board_wipe_is_one_event_with_look_back_triggers(self):
        g=self.game('Blood Artist','Deathgreeter'); g.script_opponent_actions(2,[{'turn':3,'kind':'board_wipe'}]); sv=self.savra(g); g.make_tokens(PEST,2); g.resolve(); life=g.life[0]; opp1=g.life[1]
        self.to_main(g,2,3); g.resolve(); check_invariants_s11(g)
        self.assertEqual(g.permanents,{})                                         # 5 own + 6 opposing creatures gone
        self.assertEqual(g.life[1],opp1-11)                                        # Blood Artist saw all 11 deaths, including its own
        self.assertEqual(g.life[0],life+11+10+2)                                   # Blood Artist +11, Deathgreeter +10 others, two Pests +1
        self.assertEqual(len(trace(g,'board_wipe')),1); self.assertEqual(len(trace(g,'board_wipe')[0][2]),11)
        self.assertEqual(g.zones.cards[g.zones.zones['command'][0]].name,SAVRA); self.assertEqual(g.commander_deaths,1)
        for s in OPPONENT_SEATS: self.assertEqual(g.opponent_creatures(s),[])
    def test_indestructible_yahenni_survives_a_wipe(self):
        g=self.game(); g.script_opponent_actions(2,[{'turn':3,'kind':'board_wipe'}]); sv=self.savra(g); ya=self.hand_creature(g,'Yahenni, Undying Partisan')
        while not (g.clock.step=='precombat_main' and g.clock.active_player==2 and g.clock.turn==3):
            g.advance_step(); g.resolve()
            if g.clock.step=='upkeep' and g.clock.active_player==2 and g.clock.turn==3:
                f=g.make_tokens(PEST)[0]; g.resolve(); g.yahenni_sacrifice(ya.uid,f.uid); g.resolve()   # indestructible until end of turn
        self.assertIn(ya.uid,g.permanents); self.assertNotIn(sv.uid,g.permanents); self.assertEqual(len(g.permanents),1)
    def test_graveyard_exile_drops_links_and_lki(self):
        g=self.game(); g.script_opponent_actions(3,[{'turn':4,'kind':'graveyard_exile'}]); self.savra(g); w=self.hand_creature(g,'Sedgemoor Witch'); wuid=g.linked_battlefield[w.uid]
        g.sacrifice(w.uid); g.resolve(); self.assertEqual(g.zones.cards[wuid].zone,'graveyard'); self.assertIn(wuid,g.linked_graveyard.values()); self.assertIsNotNone(g._grave_target(w.uid))
        self.to_main(g,3,4); self.assertEqual(g.zones.cards[wuid].zone,'exile'); self.assertEqual(g.linked_graveyard,{}); self.assertIsNone(g._grave_target(w.uid)); self.assertEqual(g.zones.zones['graveyard'],[])
        self.assertEqual(trace(g,'graveyard_exiled'),[('graveyard_exiled',3,(wuid,))])
    def test_edict_token_first_then_lowest_power_then_savra_and_savra_triggers(self):
        g=self.game(); g.script_opponent_actions(1,[{'turn':2,'kind':'edict'},{'turn':6,'kind':'edict'},{'turn':10,'kind':'edict'}]); sv=self.savra(g)
        w=self.hand_creature(g,'Sedgemoor Witch'); p=g.make_tokens(PEST)[0]; g.resolve()
        self.to_main(g,1,2); self.assertNotIn(p.uid,g.permanents); self.assertIn(w.uid,g.permanents); self.assertEqual(g.opponent_sacrifices,3)   # Pest is BG: Savra black edict hit all three
        self.to_main(g,1,6); self.assertNotIn(w.uid,g.permanents); self.assertIn(sv.uid,g.permanents); self.assertEqual(g.opponent_sacrifices,6)   # Witch is B
        self.to_main(g,1,10); self.assertNotIn(sv.uid,g.permanents); self.assertEqual(g.commander_deaths,1)
        self.assertEqual([t[3] for t in trace(g,'edict_against_controller')],['ordinary Pest','Sedgemoor Witch',SAVRA])

class Driver(_B):
    def test_eight_seeds_twenty_turns_with_boards_and_a_script(self):
        script={1:[{'turn':6,'kind':'destroy_commander'},{'turn':14,'kind':'destroy_creature'}],2:[{'turn':11,'kind':'board_wipe'}],3:[{'turn':12,'kind':'graveyard_exile'},{'turn':16,'kind':'edict'}]}
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=PhysicalZoneGame(seed=seed); opening_hand(g)
                for s in OPPONENT_SEATS: g.declare_opponent_board(s,BOARD); g.script_opponent_actions(s,script[s])
                ledger=run_turns_casting(g,20)
                self.assertEqual([t for t,*_ in ledger],[1,5,9,13,17]); self.assertEqual([x[:3] for x in g.opponent_actions_done],[(6,1,'destroy_commander'),(11,2,'board_wipe'),(12,3,'graveyard_exile'),(14,1,'destroy_creature'),(16,3,'edict')])
                self.assertEqual(g.opponent_script,[]); self.assertEqual(sum(len(g.opponent_creatures(s)) for s in OPPONENT_SEATS),0)   # the wipe emptied every board
                z=g.zones; self.assertEqual(sum(len(z.zones[k]) for k in ('library','hand','battlefield','graveyard','exile','command')),100+sum(1 for c in z.cards.values() if c.token and c.zone=='battlefield'))

if __name__=='__main__': unittest.main()
