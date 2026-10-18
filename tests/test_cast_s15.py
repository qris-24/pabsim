"""Stage S15: the nine interaction spells. Each: positive, refusals before mutation, target
re-check at resolution (fizzle), the until-end-of-turn machinery (every cleanup), hexproof
against scripted removal, regeneration, Infuse return, Rise with the S8 opponent policy,
Command modes, driver run with boards. """
import sys, re, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST
from pab_zone_bridge import BridgeError
from pab_zones import ZoneError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_cast_s15 import SPELLS15, S15_NAMES, CASTABLE, run_turns_casting, cast_when_able
from pab_cast_s13 import check_invariants_s11
from pab_opponents_s8 import OPPONENT_SEATS
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
BOARD=[{'name':'Bear','power':2,'toughness':2,'mana_value':2},{'name':'Wall','power':0,'toughness':4,'mana_value':3},{'name':'Dragon','power':5,'toughness':5,'mana_value':6}]
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names,board=True,fixture_savra=True):
        g=PhysicalZoneGame()
        if fixture_savra: g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve()
        if board:
            for s in OPPONENT_SEATS: g.declare_opponent_board(s,BOARD)
        check_invariants_s11(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s11(g); return uid
    def opp(self,g,seat,name): return next(p.uid for p in g.opponent_creatures(seat) if p.name==name)
    def cast(self,g,name,*mana,**kw):
        uid=self.to_hand(g,name); g.add_mana(*mana); g.cast_from_hand(uid,**kw); check_invariants_s11(g); self.assertIn(uid,g.stack_cards)
        g.resolve(); check_invariants_s11(g); self.assertEqual(g.zones.cards[uid].zone,'graveyard'); g.zones.move(uid,'library'); return uid   # singleton: back to the library for reuse
    def hold(self,g,name,*mana,**kw):
        """Cast without resolving (to act in response)."""
        uid=self.to_hand(g,name); g.add_mana(*mana); g.cast_from_hand(uid,**kw); check_invariants_s11(g); return uid
    def refused(self,g,name,*mana,exc=BridgeError,**kw):
        uid=self.to_hand(g,name); g.add_mana(*mana); hand=list(g.zones.zones['hand']); pool=list(g.mana_pool); perms=set(g.permanents); n=len(g.trace); life=list(g.life)
        with self.assertRaises(exc): g.cast_from_hand(uid,**kw)
        self.assertEqual((list(g.zones.zones['hand']),list(g.mana_pool),set(g.permanents),len(g.trace),list(g.life)),(hand,pool,perms,n,life)); self.assertEqual(g.stack_cards,{}); check_invariants_s11(g)
        g.zones.move(uid,'library'); del g.mana_pool[:]
    def creature(self,g,name):
        uid=self.to_hand(g,name); g.add_mana('B','B','G','G','C','C','C','C'); g.cast_from_hand(uid); g.resolve(); del g.mana_pool[:]; check_invariants_s11(g)
        return next(p for p in g.permanents.values() if p.name==name)

class Scope(_B):
    def test_kernel_promoted_and_evidence(self):
        self.assertIn('+S15',KERNEL_VERSION); self.assertIn('S15',PROMOTED); self.assertEqual(len(S15_NAMES),9)
        ev=json.loads((ROOT/'EVIDENCE'/'S15_SPELL_EVIDENCE.json').read_text(encoding='utf-8'))['cards']; self.assertEqual(set(ev)-{'Grist, the Hunger Tide'},S15_NAMES)
        for n in S15_NAMES:
            syms=re.findall(r'\{([^}]+)\}',ev[n]['mana_cost']); self.assertEqual((syms.count('B'),syms.count('G'),sum(int(s) for s in syms if s.isdigit())),SPELLS15[n]['cost'],n)
            self.assertEqual(SPELLS15[n]['kind'],'instant' if 'Instant' in ev[n]['type_line'] else 'sorcery',n)
        g=self.game(); uid=self.to_hand(g,'Golgari Charm'); g.add_mana('B','G'); g.advance_to('precombat_main',active_player=1); g.add_mana('B','G'); g.advance_to('precombat_main',active_player=1)   # (Grist is castable since S16; the S15 probe keeps a timing refusal instead)
        with self.assertRaises(BridgeError): g.cast_from_hand(uid,mode=1,main_phase=True)              # kw timing refused once the clock is engaged
    def test_common_refusals(self):
        g=self.game(); bear=self.opp(g,1,'Bear')
        self.refused(g,'Abrupt Decay','B')                                                           # mana
        self.refused(g,'Abrupt Decay','B','G',target_uid=999); self.refused(g,'Abrupt Decay','B','G',target_uid=self.opp(g,1,'Dragon'))   # no target / MV 6
        self.refused(g,"Assassin's Trophy",'B','G',target_uid=next(p.uid for p in g.permanents.values() if p.name==SAVRA))               # own permanent
        self.refused(g,'Witherbloom Charm','B','G'); self.refused(g,'Witherbloom Charm','B','G',mode=3,target_uid=self.opp(g,1,'Wall'))  # no mode / MV 3
        self.refused(g,'Golgari Charm','B','G',mode=2,target_uid=bear)                               # not an enchantment
        self.refused(g,'Infuse with Vitality','B','G',target_uid=999)
        self.refused(g,'Witherbloom Command','B','G',modes=(1,1),target_player=0); self.refused(g,'Witherbloom Command','B','G',modes=(2,4),target_uid=bear,target_opponent=1)   # dup / creature
        self.refused(g,'Rise of the Witch-king','B','G','C','C')                                      # must choose a creature to sacrifice while controlling one
        uid=self.to_hand(g,'Abrupt Decay'); g.add_mana('B','G'); g.advance_to('cleanup',active_player=0); g.advance_step(); g.add_mana('B','G')
        with self.assertRaises(BridgeError): g.cast_from_hand(uid,target_uid=bear)                   # untap: no priority
        uid=self.to_hand(g,'Rise of the Witch-king'); g.advance_to('upkeep',active_player=0); g.add_mana('B','G','C','C')
        with self.assertRaises(BridgeError): g.cast_from_hand(uid,sacrifice_uid=next(p.uid for p in g.permanents.values() if p.name==SAVRA))   # sorcery in upkeep

class Removal(_B):
    def test_abrupt_decay_and_trophy_destroy_real_targets_with_own_card_triggers(self):
        g=self.game('Deathgreeter'); bear=self.opp(g,1,'Bear'); dragon=self.opp(g,2,'Dragon'); life=g.life[0]
        self.cast(g,'Abrupt Decay','B','G',target_uid=bear); self.assertNotIn(bear,g.permanents); self.assertEqual(g.life[0],life+1)
        self.cast(g,"Assassin's Trophy",'B','G',target_uid=dragon); self.assertNotIn(dragon,g.permanents); self.assertEqual(trace(g,'opponent_basic_land_search_unmodeled'),[('opponent_basic_land_search_unmodeled',2,"Assassin's Trophy")])
        self.assertEqual([t[3] for t in trace(g,'opponent_creature_dies')],['Bear','Dragon']); self.assertEqual(trace(g,'targets_locked')[-1][2],"Assassin's Trophy")
    def test_decay_on_own_permanent_and_fizzle_when_target_left(self):
        g=self.game(); gp=self.creature(g,'Blood Artist'); uid=g.linked_battlefield[gp.uid]
        self.cast(g,'Abrupt Decay','B','G',target_uid=gp.uid); self.assertEqual(g.zones.cards[uid].zone,'graveyard')
        wall=self.opp(g,1,'Wall'); self.hold(g,"Assassin's Trophy",'B','G',target_uid=wall); g._opponent_creature_dies(wall,cause='test'); g.resolve(); check_invariants_s11(g)
        self.assertIn(('spell_fizzles_all_targets_illegal',"Assassin's Trophy"),g.trace)
    def test_witherbloom_charm_three_modes(self):
        g=self.game(); life=g.life[0]; self.cast(g,'Witherbloom Charm','B','G',mode=2); self.assertEqual(g.life[0],life+5)
        land=self.to_hand(g,'Swamp'); lp=g.play_physical_land(land); d=g.cards_drawn
        self.cast(g,'Witherbloom Charm','B','G',mode=1,sacrifice_uid=lp.uid); self.assertEqual(g.zones.cards[land].zone,'graveyard'); self.assertNotIn(lp.uid,g.permanents); self.assertEqual(g.cards_drawn,d+2)
        self.cast(g,'Witherbloom Charm','B','G',mode=1); self.assertEqual(g.cards_drawn,d+2); self.assertIn(('witherbloom_charm_no_sacrifice',),g.trace)
        bear=self.opp(g,3,'Bear'); self.cast(g,'Witherbloom Charm','B','G',mode=3,target_uid=bear); self.assertNotIn(bear,g.permanents)
    def test_golgari_charm_minus_one_sba_enchantment_and_regeneration(self):
        g=self.game('Deathgreeter','Grave Pact',fixture_savra=False); g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve(); d=next(p for p in g.permanents.values() if p.name=='Deathgreeter'); gp=next(p for p in g.permanents.values() if p.name=='Grave Pact')
        self.cast(g,'Golgari Charm','B','G',mode=1); self.assertNotIn(d.uid,g.permanents)                                   # 1/1 dies to SBA; Grave Pact: each opponent loses its Wall
        for s in OPPONENT_SEATS: self.assertEqual(sorted(p.name for p in g.opponent_creatures(s)),['Bear','Dragon'])
        self.assertEqual(g.eot_pt[next(p.uid for p in g.permanents.values() if p.name==SAVRA)],(-1,-1))
        self.cast(g,'Golgari Charm','B','G',mode=1)                                                                            # second -1/-1 this turn: Savra 2/2 -> 0/0 dies (command zone), Bears 2/2 -> 0/0
        self.assertEqual(g.zones.cards[g.zones.zones['command'][0]].name,SAVRA); self.assertTrue(all(p.name!='Bear' for s in OPPONENT_SEATS for p in g.opponent_creatures(s)))
        self.cast(g,'Golgari Charm','B','G',mode=2,target_uid=gp.uid); self.assertNotIn(gp.uid,g.permanents)
        w=self.creature(g,'Sedgemoor Witch'); self.cast(g,'Golgari Charm','B','G',mode=3); self.assertIn(w.uid,g.regen_shields)
        g.destroy(w.uid); self.assertIn(w.uid,g.permanents); self.assertTrue(w.tapped); self.assertNotIn(w.uid,g.regen_shields); self.assertEqual(trace(g,'regenerated'),[('regenerated',w.uid,'Sedgemoor Witch')])
        g.destroy(w.uid); self.assertNotIn(w.uid,g.permanents)                                                               # shield spent

class ProtectionAndTiming(_B):
    def test_heroic_intervention_blocks_scripted_removal_and_expires_at_any_cleanup(self):
        g=self.game(board=False,fixture_savra=False); g.script_opponent_actions(1,[{'turn':2,'kind':'destroy_commander'},{'turn':6,'kind':'destroy_commander'}])
        g.advance_to('precombat_main',active_player=0); g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve(); sv=next(p for p in g.permanents.values() if p.name==SAVRA)
        g.advance_to('upkeep',active_player=1); self.cast(g,'Heroic Intervention','G','C')                                    # in response on seat 1's upkeep
        self.assertIn(sv.uid,g.hexproof_eot); self.assertIn(sv.uid,g.indestructible_until_eot)
        g.advance_to('precombat_main',active_player=1); self.assertIn(sv.uid,g.permanents); self.assertEqual(trace(g,'no_target'),[('no_target',1,'destroy_commander')])   # hexproof: no legal target
        g.advance_to('cleanup',active_player=1); self.assertEqual((g.hexproof_eot,g.indestructible_until_eot),(set(),set())); self.assertTrue(trace(g,'until_end_of_turn_expired_s15'))
        g.advance_to('precombat_main',active_player=1); g.resolve(); self.assertNotIn(sv.uid,g.permanents); self.assertEqual(g.commander_deaths,1)   # turn 6: unprotected
    def test_infuse_with_vitality_returns_the_creature_tapped_and_gains(self):
        g=self.game('Blood Artist'); w=self.creature(g,'Sedgemoor Witch'); wuid=g.linked_battlefield[w.uid]; life=g.life[0]
        self.cast(g,'Infuse with Vitality','B','G',target_uid=w.uid); self.assertEqual(g.life[0],life+2)
        g.sacrifice(w.uid); g.resolve(); check_invariants_s11(g)
        back=next(p for p in g.permanents.values() if p.name=='Sedgemoor Witch'); self.assertNotEqual(back.uid,w.uid); self.assertTrue(back.tapped); self.assertEqual(g.linked_battlefield[back.uid],wuid)
        self.assertEqual(g.life[0],life+2-2+1+3)                                                                             # Savra black paid (edict: three opposing deaths, Blood Artist +3), Blood Artist for the Witch
        g.advance_to('cleanup',active_player=0); g.sacrifice(back.uid); g.resolve(); self.assertEqual(g.zones.cards[wuid].zone,'graveyard')   # ability expired
    def test_grisly_salvage_choice_and_rest_to_graveyard(self):
        g=self.game(); uid=self.to_hand(g,'Grisly Salvage'); top=list(g.zones.zones['library'][:5]); n=len(g.zones.zones['graveyard'])
        g.add_mana('B','G'); g.cast_from_hand(uid); g.resolve(); check_invariants_s11(g); pick=trace(g,'grisly_salvage')[-1][1]
        if pick is not None: self.assertEqual(g.zones.cards[pick].zone,'hand'); self.assertIn(pick,top)
        self.assertEqual(len(g.zones.zones['graveyard']),n+1+(4 if pick is not None else 5)); self.assertEqual(trace(g,'revealed')[-1],('revealed',tuple(top)))

class RiseAndCommand(_B):
    def test_rise_each_player_sacrifices_and_returns_a_permanent_card(self):
        g=self.game(); w=self.creature(g,'Sedgemoor Witch'); wuid=g.linked_battlefield[w.uid]; g.sacrifice(w.uid); g.resolve()
        p=g.make_tokens(PEST)[0]; g.resolve(); sacs=g.opponent_sacrifices
        self.cast(g,'Rise of the Witch-king','B','G','C','C',sacrifice_uid=p.uid,return_uid=wuid)
        self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.zones.cards[wuid].zone,'battlefield'); self.assertEqual(g.opponent_sacrifices,sacs+6)   # Pest BG: Savra black edict (3) + Rise (3)
        self.assertEqual({t[4] for t in trace(g,'opponent_sacrifice')},{'Savra black','Rise of the Witch-king'})
        for s in OPPONENT_SEATS: self.assertEqual(g.opponent_creatures(s),[])                                              # Witch's Savra edict (Wall), the Pest's (Bear), Rise (Dragon)
        g2=self.game(board=False); land=self.to_hand(g2,'Forest'); g2.zones.move(land,'graveyard'); q=g2.make_tokens(PEST)[0]; g2.resolve()
        self.cast(g2,'Rise of the Witch-king','B','G','C','C',sacrifice_uid=q.uid,return_uid=land); self.assertEqual(g2.zones.cards[land].zone,'battlefield')
        g3=self.game(board=False); sv=next(p for p in g3.permanents.values() if p.name==SAVRA); g3.sacrifice(sv.uid); g3.resolve()   # fixture body gone, no creatures left
        self.cast(g3,'Rise of the Witch-king','B','G','C','C'); self.assertEqual([t for t in trace(g3,'edict_no_creature') if t[2]=='Rise of the Witch-king'],[('edict_no_creature',s,'Rise of the Witch-king') for s in OPPONENT_SEATS])
    def test_witherbloom_command_modes(self):
        g=self.game('Deathgreeter'); gp=self.creature(g,'Sedgemoor Witch'); land=self.to_hand(g,'Swamp'); g.zones.move(land,'graveyard'); life=g.life[0]; n=len(g.zones.zones['library'])
        self.cast(g,'Witherbloom Command','B','G',modes=(1,4),target_player=0,target_opponent=1)
        self.assertEqual(len(g.zones.zones['library']),n-3); self.assertEqual(g.zones.cards[land].zone,'hand'); self.assertEqual(g.life[0],life+2); self.assertEqual(g.life[1],40-2)
        self.cast(g,'Witherbloom Command','B','G',modes=(3,1),target_uid=gp.uid,target_player=2); self.assertEqual(g.eot_pt[gp.uid],(-3,-1)); self.assertIn(('opponent_mill_unmodeled',2),g.trace)
        self.assertIn(gp.uid,g.permanents)                                                                                     # Witch 3/2 -> 0/1 survives
    def test_command_minus_three_minus_one_kills_a_one_toughness_creature(self):
        g=self.game('Deathgreeter'); d=next(p for p in g.permanents.values() if p.name=='Deathgreeter')
        self.cast(g,'Witherbloom Command','B','G',modes=(3,4),target_uid=d.uid,target_opponent=3); self.assertNotIn(d.uid,g.permanents); self.assertEqual(g.life[3],38)

class Driver(_B):
    def test_eight_seeds_24_turns_with_boards(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=PhysicalZoneGame(seed=seed,learn_sideboard_allowed=True); opening_hand(g)
                for s in OPPONENT_SEATS: g.declare_opponent_board(s,BOARD)
                ledger=run_turns_casting(g,24); self.assertEqual([t for t,*_ in ledger],[1,5,9,13,17,21]); self.assertEqual(g.stack_cards,{})
                for _,name,uid,cost,_ in trace(g,'physical_cast'):
                    self.assertIn(name,CASTABLE)
                    if CASTABLE[name]['kind'] in ('instant','sorcery'): self.assertEqual(g.zones.cards[uid].zone,'graveyard')
                self.assertEqual(g.eot_pt,{}); self.assertEqual(g.hexproof_eot,set())

if __name__=='__main__': unittest.main()
