"""CP39 (A2 Kernel 3; review items K3, K6, K7 in EVIDENCE/CP31d_INTEGRITY_REVIEW.md, plus the CP37/CP38 follow-ups):
turn clock and validation.

K3   "life gained this turn" starts at 0 at every seat's untap step, so life gained on an opponent's turn does not
     count at your end step (Moseo).
K6   S19 clock_legal accepts the turn number a seat that left the game uses up (the clock skips the seat and its turn).
K7   resolve() at 0 or less life records lose_game (once), like a loss during a resolution.
CP37 follow-up: a creature killed by lethal damage is traced sba_lethal_damage (event 'lethal_damage'), not as a
     zero-toughness death.
CP38 follow-up (whole-game errors under all-exile policies):
     - a loss in the middle of a resolution ends the game with the spell still on the stack ledger: the stack
       invariants and S19 stacks_empty accept that, and the casting drivers stop casting;
     - the land-tapping policy never pays its last life (Nurturing Peatland at 1 life);
     - the S13 driver casts Pest Summoning only when the pool can pay {1}{B/G}{B/G}.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, PEST
from pab_kernel import PhysicalZoneGame, Game, KERNEL_VERSION, PROMOTED
from pab_opponents_s8 import OPPONENT_SEATS
from pab_interaction_s11 import check_invariants_s11
import pab_validation_s19 as s19
import pab_cast_s13 as s13
import pab_lands_s9 as s9

BEAR={'name':'Bear','power':2,'toughness':2,'mana_value':2}
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,board=True,policy='none'):
        g=PhysicalZoneGame(block_policy=policy); g.resolve()
        if board:
            for s in OPPONENT_SEATS: g.declare_opponent_board(s,[BEAR])
        g.advance_to('precombat_main',active_player=0); return g
    def to_hand(self,g,name):
        u=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=u,destination='hand'); return u

class Version(_B):
    def test_kernel_promoted(self):
        self.assertIn('CP39',PROMOTED); self.assertIn('+CP39',KERNEL_VERSION)

class LifeGainedThisTurn(_B):
    def test_gain_on_an_opponents_turn_does_not_reach_your_end_step(self):
        g=self.game(); g.advance_to('precombat_main',active_player=1); g.gain(3,'test'); self.assertEqual(g.life_gained_turn,3)
        g.advance_to('end',active_player=0)
        self.assertEqual(g.life_gained_turn,0); self.assertEqual(trace(g,'moseo_end_step_admission')[-1],('moseo_end_step_admission',False,0))
        self.assertEqual(trace(g,'life_gained_turn_reset')[-1][3],3)
    def test_reset_happens_at_every_seats_untap(self):
        g=self.game(); g.advance_to('precombat_main',active_player=1); g.gain(1,'test'); g.advance_to('upkeep',active_player=2)
        self.assertEqual(g.life_gained_turn,0); self.assertEqual(trace(g,'life_gained_turn_reset')[-1][2],2)
    def test_gain_on_your_turn_still_counts(self):
        g=self.game(); g.gain(2,'test'); g.advance_to('end',active_player=0)
        self.assertEqual(trace(g,'moseo_end_step_admission')[-1][2],2)

class ClockAfterSeatLeaves(_B):
    def test_clock_legal_after_a_seat_leaves(self):
        g=self.game(); g.life[2]=1; g.drain_opponents(1,'test'); g.resolve(); self.assertIn(2,g.lost_seats)
        for _ in range(3): g.advance_to('cleanup',active_player=3); g.resolve()
        self.assertTrue(g.clock.skipped); ok,problems=s19.clock_legal(g); self.assertTrue(ok,problems)
    def test_clock_legal_still_rejects_a_wrong_turn_number(self):
        g=self.game(); g.life[2]=1; g.drain_opponents(1,'test'); g.resolve(); g.advance_to('cleanup',active_player=3)
        last=max(t[1] for t in g.trace if t[0]=='step_begin')
        for shift in (1,-1):
            with self.subTest(shift=shift):
                h=[(t[0],t[1]+shift)+t[2:] if t[0]=='step_begin' and t[1]==last else t for t in g.trace]   # seat 3's whole turn renumbered
                saved=g.trace; g.trace=h
                try: ok,problems=s19.clock_legal(g)
                finally: g.trace=saved
                self.assertFalse(ok); self.assertEqual(problems[0][0],'turn boundary')

class LossRecorded(_B):
    def test_resolve_at_zero_life_records_the_loss_once(self):
        for cls in (Game,PhysicalZoneGame):
            with self.subTest(cls=cls.__name__):
                g=cls(); g.resolve(); g.life[0]=0; g.resolve(); g.resolve()
                self.assertTrue(g.game_lost); self.assertEqual(trace(g,'lose_game'),[('lose_game','life_zero_or_less')])

class LethalDamageLabel(_B):
    def test_combat_death_is_traced_as_lethal_damage(self):
        g=self.game(policy='all')
        g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve(); sv=next(p for p in g.permanents.values() if p.name==SAVRA)
        g.advance_to('cleanup',active_player=0); g.advance_to('declare_attackers',active_player=0); g.declare_attackers([(sv.uid,1)]); g.resolve()
        g.advance_to('combat_damage',active_player=0); g.resolve()
        self.assertIn(('sba_lethal_damage',sv.uid,'state-based'),g.trace); self.assertNotIn(('sba_zero_toughness',sv.uid,'state-based'),g.trace)
        self.assertEqual(trace(g,'sba_event')[-1][1],'lethal_damage')
    def test_mixed_event_names_both(self):
        g=self.game(); pe=g.make_tokens(PEST,2); g.resolve(); a,b=pe
        a.minus_counters=1; g.damage_marked[b.uid]=1; g.resolve()
        self.assertEqual(trace(g,'sba_event')[-1],('sba_event','lethal_damage+zero_toughness',(a.uid,b.uid)))

class LossMidResolution(_B):
    def test_loss_mid_resolution_keeps_invariants_and_stops_the_driver(self):
        g=self.game(board=False); g.make_tokens(PEST,2); g.resolve(); g.life[0]=1
        u=self.to_hand(g,'Plumb the Forbidden'); toks=[p.uid for p in g.permanents.values() if p.token is not None and p.creature]
        g.add_mana('B','C'); g.cast_from_hand(u,sacrifice_uids=toks); g.resolve()
        self.assertTrue(g.game_lost); self.assertIn(u,g.stack_cards); check_invariants_s11(g); self.assertTrue(s19.stacks_ok(g))   # the spell stays on the stack; no error
        self.to_hand(g,'Deathgreeter'); g.add_mana('B'); self.assertEqual(s13.cast_when_able(g),[])  # nothing is cast after the loss
        self.assertTrue(s19.lost_seats_ok(g))

    def test_stacks_check_accepts_only_a_lost_game(self):
        g=self.game(board=False); u=self.to_hand(g,'Plumb the Forbidden'); g.add_mana('B','C'); g.cast_from_hand(u,sacrifice_uids=[]); g.pending.clear()
        self.assertFalse(s19.stacks_ok(g)); g.game_lost=True; self.assertFalse(s19.stacks_ok(g))      # a loss with no snapshot explains nothing
        marker=object(); orig=s19.stacks_ok; s19.stacks_ok=lambda g: marker
        try: x=s19.validate_game(0,{**s19.DEFAULT_CONFIG,'max_turns':2})
        finally: s19.stacks_ok=orig
        self.assertIs(x['checks']['stacks_empty'],marker)
    def test_a_stray_stack_card_is_still_caught_after_a_loss(self):
        g=self.game(board=False); g.life[0]=0; g.resolve(); self.assertTrue(g.game_lost); self.assertTrue(s19.stacks_ok(g))
        u=self.to_hand(g,'Plumb the Forbidden'); g.stack_cards[u]='Plumb the Forbidden'                 # not there when the game was lost
        self.assertFalse(s19.stacks_ok(g))
    def test_command_ledger_invariant_after_a_loss(self):
        from pab_commander_s10 import check_invariants_s10
        g=self.game(board=False); g.add_mana('B','G','C','C'); g.cast_commander(); self.assertTrue(g.command_stack)
        g.life[0]=0; g.resolve(); self.assertTrue(g.game_lost); self.assertTrue(g.command_stack); check_invariants_s10(g)
    def test_every_casting_driver_stops_after_a_loss(self):
        import pab_cast_s6 as s6, pab_cast_s12 as s12, pab_cast_s15 as s15
        cases=((s6,"Nature's Lore",('G','C')),(s12,'Skullclamp',('C',)),(s13,'Pest Summoning',('B','B','C')),(s15,'Grisly Salvage',('B','G')))
        for mod,name,mana in cases:
            with self.subTest(driver=mod.__name__):
                g=PhysicalZoneGame(learn_sideboard_allowed=True); g.resolve(); g.advance_to('precombat_main',active_player=0)
                for x in list(g.zones.zones['hand']): g.zones.move(x,'graveyard')
                if name=='Pest Summoning': g.zones.learn_pest_summoning()
                else: self.to_hand(g,name)
                g.add_mana(*mana); g.game_lost=True
                self.assertEqual(mod.cast_when_able(g),[])

class Policies(_B):
    def test_tapping_policy_keeps_the_last_life(self):
        g=self.game(); u=self.to_hand(g,'Nurturing Peatland'); g.play_physical_land(u); g.resolve(); del g.mana_pool[:]
        g.life[0]=1; self.assertEqual(s9.tap_lands_policy(g),[]); self.assertEqual(g.life[0],1)
        g.life[0]=2; self.assertEqual(len(s9.tap_lands_policy(g)),1); self.assertEqual(g.life[0],1)
    def test_llanowar_wastes_gives_colorless_at_one_life(self):
        g=self.game(); u=self.to_hand(g,'Llanowar Wastes'); g.play_physical_land(u); g.resolve(); del g.mana_pool[:]
        g.life[0]=1; s9.tap_lands_policy(g,extra={'B':5}); self.assertEqual(g.life[0],1); self.assertEqual(g.mana_pool,['C'])
    def test_plumb_is_not_cast_for_the_last_life(self):
        for life,expect in ((3,False),(4,True)):
            with self.subTest(life=life):
                g=self.game(board=False)
                for x in list(g.zones.zones['hand']): g.zones.move(x,'graveyard')
                g.make_tokens(PEST,2); g.resolve(); self.to_hand(g,'Plumb the Forbidden'); g.add_mana('B','C'); g.life[0]=life
                self.assertEqual('Plumb the Forbidden' in s13.cast_when_able(g),expect)
    def test_pest_summoning_needs_three_mana(self):
        g=PhysicalZoneGame(learn_sideboard_allowed=True); g.resolve(); g.advance_to('precombat_main',active_player=0)
        for x in list(g.zones.zones['hand']): g.zones.move(x,'graveyard')
        u=g.zones.learn_pest_summoning().uid; self.assertEqual(g.zones.zones['hand'],[u])
        g.add_mana('B','B'); self.assertNotIn('Pest Summoning',s13.cast_when_able(g)); self.assertIn(u,g.zones.zones['hand'])
        del g.mana_pool[:]; g.add_mana('B','C','C'); self.assertNotIn('Pest Summoning',s13.cast_when_able(g))   # only one B/G for two hybrid pips
        g.add_mana('B'); self.assertIn('Pest Summoning',s13.cast_when_able(g))

if __name__=='__main__': unittest.main()
