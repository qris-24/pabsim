"""Upkeep / step-boundary trigger audit (read-only) against kernel v0.8+R02+R01+R47+R48.

Pins what the kernel does today at step boundaries, against the official CR
(MagicCompRules 20260619, see EVIDENCE/CR_20260619_EVIDENCE.json) and the
supplied card texts. Nothing here changes engine behaviour. Where the kernel
disagrees with the CR, the contract assertion is an expectedFailure and a
sibling test pins the frozen behaviour. Where the kernel merely lacks
a model (no active player, no step clock, no mana emptying), the probe pins
the absence so the phase-clock milestone has an executable baseline.
"""
import sys, unittest, inspect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST, SAVRA
from pab_kernel import Game, PhysicalZoneGame

def pests(g): return sum(p.token==PEST for p in g.permanents.values())
def labels(g): return [t.label for t in g.pending]
def find(g,name): return next(p for p in g.permanents.values() if p.name==name)

class ActivePlayerAbsent(unittest.TestCase):
    """R50 (coverage gap): 'each upkeep' cards. begin_upkeep() takes no player; the
    kernel cannot distinguish the controller's upkeep from an opponent's."""
    def test_begin_upkeep_has_no_player_parameter(self):
        self.assertEqual(list(inspect.signature(Game.begin_upkeep).parameters),['self'])
        # S1 added an inert clock; R50 remains open until S2 routes these methods through it.
        self.assertFalse(any(a in ('active_player','turn_player','current_step','step','phase') for a in vars(Game()) if a!='clock'))
    def test_end_step_methods_have_no_player_parameter(self):
        self.assertEqual(list(inspect.signature(Game.roaster_end_step).parameters),['self'])
        self.assertEqual(list(inspect.signature(Game.moseo_end_step).parameters),['self','target_uid'])
    def test_each_upkeep_round_of_four_under_caller_discipline(self):
        """Provisional C95 shape: calling begin_upkeep() once per player's upkeep.
        Beledros ('each upkeep') makes one Pest per call; Rescuer ('each upkeep, if
        you don't control a Pest creature token') only while the condition holds."""
        g=Game(); g.add('Beledros Witherbloom'); g.add('Pest Rescuer'); g.resolve()
        made=[]
        for _ in range(4):
            before=pests(g); g.begin_upkeep(); g.resolve(); made.append(pests(g)-before)
        self.assertEqual(made,[2,1,1,1])          # kernel order: Rescuer resolves first, then Beledros
    def test_your_end_step_cards_cannot_be_scoped_to_a_player(self):
        """Moseo and Roaster say 'your end step'; the caller must not invoke them on
        opponents' end steps. The kernel offers no guard."""
        g=Game(); g.add(SAVRA); g.add('Ribtruss Roaster',counters=1); g.resolve()
        g.roaster_end_step(); self.assertIn('Ribtruss Roaster end-step',labels(g))   # fires regardless of whose end step

class ManaAndEffectExpiry(unittest.TestCase):
    def test_mana_pool_not_emptied_by_any_turn_reset(self):
        """CR 106.4: pools empty at the end of each step and phase. Kernel: no emptying (A05 reconfirmed)."""
        g=Game(); g.add_mana('B','G'); g.reset_turn(); self.assertEqual(g.mana_pool,['B','G'])
        b=PhysicalZoneGame(); b.add_mana('B'); b.fixture_new_turn(); self.assertEqual(list(b.mana_pool),['B'])
    def test_until_end_of_turn_cleared_by_reset_turn(self):
        """CR 514.2: 'until end of turn' effects end in cleanup. Kernel: reset_turn() clears them (caller-driven)."""
        g=Game(); g.add(SAVRA); g.resolve(); p=g.make_tokens(PEST)[0]; g.resolve()
        g.indestructible_until_eot.add(p.uid); g.reset_turn(); self.assertEqual(g.indestructible_until_eot,set())
    def test_life_gained_turn_cleared_by_reset_turn(self):
        g=Game(); g.gain(2,'x'); self.assertEqual(g.life_gained_turn,2); g.reset_turn(); self.assertEqual(g.life_gained_turn,0)

class InterveningIf(unittest.TestCase):
    """CR 603.4: condition checked on trigger AND on resolution (R01 promoted)."""
    def test_rescuer_checks_at_both_points(self):
        g=Game(); g.add('Pest Rescuer'); g.resolve(); g.begin_upkeep()
        self.assertEqual(labels(g),['Pest Rescuer conditional upkeep'])
        g.make_tokens(PEST); g.resolve(); self.assertEqual(pests(g),1)
    def test_rescuer_not_admitted_when_false_at_trigger(self):
        g=Game(); g.add('Pest Rescuer'); g.resolve(); g.make_tokens(PEST); g.resolve(); g.begin_upkeep()
        self.assertEqual(labels(g),[])

class R49RoasterSourceLeftLKI(unittest.TestCase):
    """CR 608.2h: if the source has left the expected zone, use its LAST KNOWN
    information. R49 promoted: the source-left branch now uses the LKI count."""
    def setup(self,G=Game):
        g=G(); g.add(SAVRA); g.resolve(); r=g.add('Ribtruss Roaster',counters=2); g.resolve()
        g.roaster_end_step(); g.destroy(r.uid); return g,r
    def test_cr_lki_counter_count_used_when_source_left(self):
        g,r=self.setup(); g.resolve(); self.assertEqual(pests(g),2); self.assertIn(('roaster_counters_lki',r.uid,2),g.trace)
    def test_r47_live_count_still_correct_when_source_present(self):
        g=Game(); g.add('Ribtruss Roaster'); g.resolve(); r=find(g,'Ribtruss Roaster'); r.counters=1
        g.roaster_end_step(); r.counters=3; g.resolve(); self.assertEqual(pests(g),3)
    def test_frozen_v07_trigger_time_snapshot_coincides_on_this_branch(self):
        """The frozen v0.7 lambda default happened to equal LKI when the source left; it was
        wrong only when the source stayed and its counters changed (R47)."""
        import pab_focus_engine_v07 as v07
        g,r=self.setup(v07.Game); g.resolve(); self.assertEqual(pests(g),2)

class R48Confirmed(unittest.TestCase):
    """CR 704.5f: toughness 0 → graveyard; regeneration can't replace it, indestructible is irrelevant."""
    def test_zero_toughness_indestructible_dies_on_promoted_kernel(self):
        g=Game(); g.add(SAVRA); y=g.add('Yawgmoth, Thran Physician'); g.resolve()
        p=g.make_tokens(PEST)[0]; c=g.add('Deathgreeter'); g.resolve(); g.indestructible_until_eot.add(p.uid)
        g.yawgmoth_sacrifice(y.uid,c.uid,target_uid=p.uid); g.resolve()
        self.assertNotIn(p.uid,g.permanents); self.assertIn(('sba_zero_toughness',p.uid,'state-based'),g.trace)   # S3: general check
    def test_sba_performed_after_full_resolution_not_mid_effect(self):
        """CR 704.3/117.5: SBAs happen when a player would receive priority, i.e. after the
        ability has fully resolved (counter then draw), not between its own effects."""
        g=Game(); g.add(SAVRA); y=g.add('Yawgmoth, Thran Physician'); g.resolve()
        p=g.make_tokens(PEST)[0]; c=g.add('Deathgreeter'); g.resolve()
        g.yawgmoth_sacrifice(y.uid,c.uid,target_uid=p.uid); g.resolve()
        keys=[t[0] for t in g.trace]
        self.assertLess(keys.index('minus_one_counter'),keys.index('draw')); self.assertLess(keys.index('draw'),keys.index('sba_zero_toughness'))

if __name__=='__main__':
    unittest.main()
