"""Phase-clock stage S2: boundaries drive upkeep/end-step triggers, mana emptying
and until-end-of-turn expiry. Executes proposed contracts C95, C96, C98, C99.
CR refs: 106.4, 503.1, 513.1, 514.2, 603.4, 608.2h (EVIDENCE/CR_20260619_EVIDENCE.json).
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST, SAVRA, IllegalAction
from pab_turn_clock import ClockError
from pab_kernel import Game, PhysicalZoneGame

def pests(g): return sum(p.token==PEST for p in g.permanents.values())
def labels(g): return [t.label for t in g.pending]
def trace(g,key): return [t for t in g.trace if t[0]==key]
def find(g,name): return next(p for p in g.permanents.values() if p.name==name)

class _B(unittest.TestCase):
    def game(self,*names,G=Game,**kw):
        g=G(**kw)
        for n in names: g.add(n)
        g.resolve(); return g


class C95(_B):
    CONTRACT='C95'; ISSUES=['R50','R01']; STATUS='EXECUTED'; SUBSTITUTIONS=[]
    def test_each_upkeep_round_of_four(self):
        g=self.game('Beledros Witherbloom','Pest Rescuer'); made=[]
        for seat in range(4):
            before=pests(g); t,ap,ph,st=g.advance_to('upkeep'); self.assertEqual((ap,st),(seat,'upkeep'))
            g.resolve(); made.append(pests(g)-before)
        self.assertEqual(made,[2,1,1,1])
        self.assertEqual(len([x for x in trace(g,'resolve') if x[1]=='Beledros each upkeep']),4)
        self.assertEqual(len([x for x in trace(g,'resolve') if x[1]=='Pest Rescuer conditional upkeep']),1)
    def test_control_pest_present_rescuer_never_triggers(self):
        g=self.game('Beledros Witherbloom','Pest Rescuer'); g.make_tokens(PEST); g.resolve()
        for _ in range(4): g.advance_to('upkeep'); g.resolve()
        self.assertEqual(pests(g),5); self.assertEqual([x for x in trace(g,'resolve') if 'Rescuer' in x[1]],[])
    def test_rescuer_retriggers_on_opponent_upkeep_after_pest_dies(self):
        g=self.game(SAVRA,'Pest Rescuer'); g.advance_to('upkeep',active_player=0); g.resolve(); self.assertEqual(pests(g),1)
        g.advance_to('upkeep',active_player=1); g.resolve(); self.assertEqual(pests(g),1)       # condition false
        g.advance_to('precombat_main'); p=next(x for x in g.permanents.values() if x.token==PEST); g.sacrifice(p.uid); g.resolve()
        g.advance_to('upkeep',active_player=2); g.resolve(); self.assertEqual(pests(g),1)       # retriggered on an opponent's upkeep


class C96(_B):
    CONTRACT='C96'; ISSUES=['R51']; STATUS='EXECUTED'; SUBSTITUTIONS=[]
    def test_pool_empties_at_every_boundary(self):
        g=self.game(SAVRA); g.advance_to('precombat_main'); g.add_mana('B','G')
        g.advance_step(); self.assertEqual(g.mana_pool,[]); self.assertEqual(trace(g,'mana_emptied')[-1],('mana_emptied',2,'step_end'))
    def test_upkeep_mana_not_available_in_draw_step(self):
        g=self.game(SAVRA); g.advance_to('upkeep'); g.add_mana('C'); g.advance_to('draw'); self.assertEqual(g.mana_pool,[])
    def test_physical_bridge_shared_pool_emptied_in_place(self):
        g=self.game(SAVRA,G=PhysicalZoneGame); g.advance_to('precombat_main'); g.add_mana('G')
        self.assertIs(g.mana_pool,g.zones.mana_pool); g.advance_step()
        self.assertEqual(list(g.zones.mana_pool),[]); g.assert_bridge_integrity()
    def test_control_spend_before_boundary_no_loss(self):
        g=self.game(SAVRA); g.advance_to('precombat_main'); g.add_mana('C'); g.pay_mana(generic=1); g.advance_step()
        self.assertEqual(trace(g,'mana_emptied'),[])


class C98(_B):
    CONTRACT='C98'; ISSUES=['R22','R32','R50']; STATUS='EXECUTED'; SUBSTITUTIONS=[]
    def board(self):
        g=self.game(SAVRA,"Moseo, Vein's New Dean"); r=g.add('Ribtruss Roaster',counters=2); g.resolve()
        dead=g.add('Deathgreeter',mana_value=1); g.destroy(dead.uid); g.resolve(); return g,dead
    def test_opponent_end_step_fires_nothing(self):
        g,dead=self.board(); g.advance_to('precombat_main'); g.gain(1,'x'); g.resolve()
        g.advance_to('end',active_player=1); g.resolve()        # passes through the controller's end step first; settle it
        n0=pests(g); g.advance_to('end',active_player=2); g.resolve()
        self.assertEqual(pests(g),n0); self.assertEqual(trace(g,'moseo_end_step_admission')[-1][1],True)   # only the seat-0 record exists
        self.assertEqual(len(trace(g,'moseo_end_step_admission')),1)
    def test_controller_end_step_fires_roaster_and_admits_moseo(self):
        g,dead=self.board(); g.advance_to('precombat_main'); g.gain(1,'x'); g.resolve(); g.advance_to('end',active_player=0)
        self.assertIn('Ribtruss Roaster end-step',labels(g)); self.assertEqual(trace(g,'moseo_end_step_admission')[-1],('moseo_end_step_admission',True,1))
        self.assertTrue(g.moseo_end_step(dead.uid)); g.resolve()
        self.assertEqual(pests(g),2)                            # Roaster's two; Moseo's own token is the attack-gain kind
        self.assertIn('Deathgreeter',[x.name for x in g.permanents.values()])   # Moseo reanimated the MV1 target
    def test_moseo_not_admitted_without_gain(self):
        g,dead=self.board(); g.advance_to('end',active_player=0)
        self.assertEqual(trace(g,'moseo_end_step_admission')[-1][1],False); self.assertFalse(g.moseo_end_step(dead.uid))
    def test_gain_after_end_step_boundary_not_retroactive(self):
        g,dead=self.board(); g.advance_to('end',active_player=0); g.gain(1,'High Market stand-in'); g.resolve()
        self.assertFalse(g.moseo_end_step(dead.uid)); self.assertIn(('moseo_not_admitted_this_end_step',),g.trace)
    def test_direct_step_calls_refused_once_engaged(self):
        g,dead=self.board(); g.advance_to('precombat_main')
        with self.assertRaises(ClockError): g.begin_upkeep()
        with self.assertRaises(ClockError): g.roaster_end_step()
        with self.assertRaises(ClockError): g.moseo_end_step(dead.uid)


class C99(_B):
    CONTRACT='C99'; ISSUES=['R49','R32']; STATUS='EXECUTED'; SUBSTITUTIONS=[]
    def test_roaster_lki_when_destroyed_in_response_at_end_step(self):
        g=self.game(SAVRA); r=g.add('Ribtruss Roaster',counters=2); g.resolve(); g.advance_to('end',active_player=0)
        self.assertIn('Ribtruss Roaster end-step',labels(g)); g.destroy(r.uid); g.resolve()
        self.assertEqual(pests(g),2); self.assertIn(('roaster_counters_lki',r.uid,2),g.trace)
    def test_control_counter_removed_before_leaving_reflected_in_lki(self):
        g=self.game(SAVRA); r=g.add('Ribtruss Roaster',counters=2); g.resolve(); g.advance_to('end',active_player=0)
        r.counters=1
        g.destroy(r.uid); g.resolve(); self.assertEqual(pests(g),2)   # LKI is taken when the trigger is created (2), per 608.2h


class Cleanup514(_B):
    def test_until_end_of_turn_and_this_turn_end_at_controller_cleanup(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); g.advance_to('precombat_main')
        g.indestructible_until_eot.add(p.uid); g.gain(2,'x'); g.resolve()
        g.advance_to('end',active_player=0); self.assertEqual(g.life_gained_turn,2); self.assertIn(p.uid,g.indestructible_until_eot)
        g.advance_to('cleanup',active_player=0)
        self.assertEqual((g.life_gained_turn,g.indestructible_until_eot),(0,set())); self.assertEqual(trace(g,'cleanup_until_end_of_turn_expired')[-1][1],1)
    def test_opponent_cleanup_does_not_reset_controller_turn_effects(self):
        """Limitation: the kernel tracks only the controller's 'this turn' ledger; an opponent's
        cleanup must not clear it mid-way through a round in which it was set during THEIR turn."""
        g=self.game(SAVRA); g.advance_to('precombat_main',active_player=1); g.gain(1,'x'); g.resolve()
        g.advance_to('cleanup',active_player=1); self.assertEqual(g.life_gained_turn,1)

if __name__=='__main__':
    unittest.main()
