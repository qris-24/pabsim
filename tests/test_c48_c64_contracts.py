"""Executable contracts C48–C64 (issues R27–R34) against the promoted kernel.

Same conventions as test_c41_c47_contracts.py: each class declares CONTRACT,
ISSUES, STATUS, SUBSTITUTIONS. Statuses used here:
  EXECUTED                   every named card/mechanic modeled
  EXECUTED_WITH_SUBSTITUTION some setup element replaced by an exogenous fixture action
  DISAGREEMENT_OBSERVED      kernel contradicts the provisional expectation (expectedFailure)
  BLOCKED_UNSUPPORTED        the contract's core mechanic is not modeled; no test is asserted
No contract is Oracle/CR-authenticated.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import (PEST, MOSEO_PEST, INSECT, SQUIRREL, TREASURE, WORM, SAVRA, IllegalAction)
from pab_zones import ZoneError
from pab_kernel import Game, PhysicalZoneGame

def labels(g): return [t.label for t in g.pending]
def tokens(g,kind): return [p for p in g.permanents.values() if p.token==kind]
def trace(g,key): return [t for t in g.trace if t[0]==key]
def find(g,name): return next(p for p in g.permanents.values() if p.name==name)

class _Base(unittest.TestCase):
    def game(self,*names,**kw):
        g=Game(**kw)
        for n in names: g.add(n)
        g.resolve(); return g


class C48(_Base):
    CONTRACT='C48'; ISSUES=['R27','R14']; STATUS='EXECUTED'; SUBSTITUTIONS=[]
    def test_two_pests_two_squirrels_four_bats_triggers(self):
        g=self.game('Chatterfang, Squirrel General','Mirkwood Bats')
        g.pest_summoning()
        self.assertEqual(labels(g).count('Mirkwood Bats creation drain'),4)
        g.resolve()
        pests,sq=tokens(g,PEST),tokens(g,SQUIRREL)
        self.assertEqual((len(pests),len(sq)),(2,2))
        self.assertTrue(all(s.colors=='G' and 'Pest' not in s.subtypes for s in sq))
        self.assertTrue(all(p.colors=='BG' for p in pests))
        self.assertEqual(g.life,[40,36,36,36])
    def test_control_without_chatterfang_two_pests(self):
        g=self.game('Mirkwood Bats'); g.pest_summoning(); g.resolve()
        self.assertEqual((len(tokens(g,PEST)),len(tokens(g,SQUIRREL))),(2,0)); self.assertEqual(g.life,[40,38,38,38])
    def test_control_without_bats_no_loss(self):
        g=self.game('Chatterfang, Squirrel General'); g.pest_summoning(); g.resolve()
        self.assertEqual(g.life,[40,40,40,40]); self.assertEqual(len(tokens(g,SQUIRREL)),2)


class C49(_Base):
    CONTRACT='C49'; ISSUES=['R27','R30']; STATUS='EXECUTED'; SUBSTITUTIONS=[]
    def test_treasure_plus_one_squirrel_no_loop(self):
        g=self.game('Chatterfang, Squirrel General','Mirkwood Bats','Warren Soultrader')
        victim=g.add('Deathgreeter'); g.resolve()           # nontoken cost creature: no Bats token-sac noise
        trader=find(g,'Warren Soultrader'); g.warren_soultrader_sacrifice(trader.uid,victim.uid)
        self.assertEqual(trace(g,'pay_life')[-1][1],1); self.assertEqual(trace(g,'sacrifice')[-1][1],victim.uid)
        self.assertEqual(tokens(g,TREASURE),[])                # nothing before resolution
        g.resolve()
        t,sq=tokens(g,TREASURE),tokens(g,SQUIRREL)
        self.assertEqual((len(t),len(sq)),(1,1))
        self.assertTrue(t[0].artifact and not t[0].creature and sq[0].creature and sq[0].colors=='G')
        self.assertEqual(len([x for x in trace(g,'resolve') if x[1]=='Mirkwood Bats creation drain']),2)
    def test_control_without_chatterfang(self):
        g=self.game('Mirkwood Bats','Warren Soultrader'); v=g.add('Deathgreeter'); g.resolve()
        g.warren_soultrader_sacrifice(find(g,'Warren Soultrader').uid,v.uid); g.resolve()
        self.assertEqual((len(tokens(g,TREASURE)),len(tokens(g,SQUIRREL))),(1,0))


class C50(_Base):
    CONTRACT='C50'; ISSUES=['R27']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Offspring (token copy of Starscape Cleric on ETB) is not modeled; no copy characteristics exist to assert']
    def test_blocked_offspring_not_modeled(self):
        g=self.game('Chatterfang, Squirrel General')
        self.assertFalse(hasattr(g,'cast_with_offspring'))
        self.assertFalse(any('offspring' in n.lower() for n in dir(g)))


class C51(_Base):
    CONTRACT='C51'; ISSUES=['R28','R13']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Chatterfang {B} activation (X, target, -X/-X) not modeled; the X=2 Squirrel sacrifices are '
                   'performed directly as the cost; only sacrifice-side observations are asserted']
    def test_two_squirrels_green_only_savra_and_two_bats(self):
        g=self.game(SAVRA); sq=g.make_tokens(SQUIRREL,2); g.resolve()        # two normal Squirrels
        g.add('Chatterfang, Squirrel General'); g.add('Mirkwood Bats'); g.resolve()
        self.assertEqual(len(tokens(g,SQUIRREL)),2)
        for s in sq: g.sacrifice(s.uid)
        L=labels(g)
        self.assertEqual(L.count('Savra green sacrifice'),2); self.assertEqual(L.count('Savra black sacrifice'),0)
        self.assertEqual(L.count('Mirkwood Bats token sacrifice'),2)
        self.assertTrue(all(s.colors=='G' for s in sq))
    def test_control_bg_pest_yields_both_savra_colors(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); g.sacrifice(p.uid)
        self.assertEqual((labels(g).count('Savra black sacrifice'),labels(g).count('Savra green sacrifice')),(1,1))


class C52(_Base):
    CONTRACT='C52'; ISSUES=['R28','R24']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Opponent creatures and -X/-X SBA are not modeled; the target\'s death is the exogenous '
                   'opposing_creature_dies() event; the cost Squirrel sacrifice is performed directly']
    def test_target_death_no_savra_no_second_bats(self):
        g=self.game(SAVRA,'Poison-Tip Archer'); s=g.make_tokens(SQUIRREL)[0]; g.resolve()
        g.add('Chatterfang, Squirrel General'); g.add('Mirkwood Bats'); g.resolve()
        g.sacrifice(s.uid)                                  # cost, X=1
        self.assertEqual(labels(g).count('Mirkwood Bats token sacrifice'),1)
        g.resolve(); before=labels(g)
        g.opposing_creature_dies('targeted 1/1 at toughness 0 (exogenous SBA stand-in)')
        new=labels(g)
        self.assertEqual(new,['Poison-Tip Archer opposing death'])
        self.assertNotIn('Savra black sacrifice',new); self.assertNotIn('Mirkwood Bats token sacrifice',new)


class C53(_Base):
    CONTRACT='C53'; ISSUES=['R29']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Blood Artist target choice is fixed by the fixture to opponent 1; no target-selection or hexproof model']
    def test_one_target_player_vs_each_opponent_sources(self):
        g=self.game('Blood Artist','Bastion of Remembrance','Deathgreeter','Poison-Tip Archer')
        v=g.add('Viscera Seer'); g.resolve(); g.destroy(v.uid)
        L=labels(g)
        for lab in ('Blood Artist target drain','Bastion death drain/gain','Deathgreeter death life','Poison-Tip Archer death drain'):
            self.assertEqual(L.count(lab),1)
        g.resolve()
        self.assertEqual(g.life[1:],[37,38,38])             # BA one target; Bastion+Archer each opponent
        self.assertEqual(g.life[0],40+1+1+1)                  # BA gain, Bastion gain, Deathgreeter gain
        self.assertEqual(trace(g,'target_opponent_loses'),[('target_opponent_loses',1,'Blood Artist')])


class C54(_Base):
    CONTRACT='C54'; ISSUES=['R29']; STATUS='EXECUTED'; SUBSTITUTIONS=[]
    def test_observer_scope_for_external_death(self):
        g=self.game('Blood Artist','Deathgreeter','Poison-Tip Archer','Bastion of Remembrance',
                    'Moldervine Reclamation','Dark Prophecy','Sangromancer')
        g.opposing_creature_dies()
        L=sorted(labels(g))
        self.assertEqual(L,sorted(['Blood Artist opposing death','Deathgreeter opposing death',
                                   'Poison-Tip Archer opposing death','Sangromancer opposing death']))
        self.assertEqual(trace(g,'sacrifice'),[]); self.assertEqual(trace(g,'external_opponent_discard'),[])
        g.resolve(); self.assertEqual(g.life[0],40+1+1+3)


class C55(_Base):
    CONTRACT='C55'; ISSUES=['R30','R21']; STATUS='EXECUTED'; SUBSTITUTIONS=[]
    def test_costs_precede_treasure_and_life_paid_not_gain(self):
        g=self.game(SAVRA,'Warren Soultrader'); p=g.make_tokens(PEST)[0]; g.resolve(); g.reset_turn()
        g.warren_soultrader_sacrifice(find(g,'Warren Soultrader').uid,p.uid)
        i_pay=g.trace.index(('pay_life',1,'Warren Soultrader cost')); i_sac=g.trace.index(('sacrifice',p.uid,'ordinary Pest'))
        self.assertLess(i_pay,i_sac); self.assertEqual(tokens(g,TREASURE),[])
        L=labels(g)
        self.assertIn('Pest dies-gain',L); self.assertIn('Savra black sacrifice',L); self.assertIn('Savra green sacrifice',L)
        self.assertEqual(L[-1],'Warren Soultrader Treasure')   # Treasure creation last on this queue
        self.assertEqual(g.life_gained_turn,0)
        g.resolve()
        self.assertEqual(len(tokens(g,TREASURE)),1)
        self.assertEqual(g.life_gained_turn,1+2)              # Pest gain + Savra green; the paid life never enters the tally
    def test_control_cannot_pay_life_at_zero(self):
        g=self.game('Warren Soultrader'); p=g.make_tokens(PEST)[0]; g.resolve(); g.life[0]=0
        with self.assertRaises(IllegalAction): g.warren_soultrader_sacrifice(find(g,'Warren Soultrader').uid,p.uid)


class C56(_Base):
    CONTRACT='C56'; ISSUES=['R30','R23']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Treasure mana ability not modeled; cash-in is a direct sacrifice with no mana added']
    def test_treasure_cash_in_bats_and_agent_not_savra(self):
        g=self.game(SAVRA,'Agent of the Iron Throne','Warren Soultrader'); v=g.add('Deathgreeter'); g.resolve()
        g.warren_soultrader_sacrifice(find(g,'Warren Soultrader').uid,v.uid); g.resolve()
        t=tokens(g,TREASURE)[0]; g.add('Mirkwood Bats'); g.resolve(); base=list(g.life)
        g.sacrifice(t.uid)
        self.assertEqual(sorted(labels(g)),sorted(['Mirkwood Bats token sacrifice','Agent-granted commander artifact drain']))
        g.resolve(); self.assertEqual(g.life,[base[0]]+[x-2 for x in base[1:]])


class C57(_Base):
    CONTRACT='C57'; ISSUES=['R31','R14']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['No lore-counter or phase clock: chapters I–III are invoked directly via saga_chapter(n)']
    def test_chapters_make_insects_plus_squirrels_not_pests(self):
        g=self.game('Chatterfang, Squirrel General','Pest Rescuer')
        for n in (1,2,3): g.saga_chapter(n); g.resolve()
        ins,sq=tokens(g,INSECT),tokens(g,SQUIRREL)
        self.assertEqual((len(ins),len(sq)),(3,3))
        self.assertTrue(all(i.colors=='BG' and 'Insect' in i.subtypes and 'Pest' not in i.subtypes for i in ins))
        self.assertFalse(g.controls_pest())                  # Insects do not satisfy the Pest-token predicate
        self.assertEqual(trace(g,'cast'),[])                  # chapters are not casts


class C58(_Base):
    CONTRACT='C58'; ISSUES=['R31']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Library is a fixture candidate list; shuffle is traced as unmodeled']
    def board(self):
        g=self.game(SAVRA,'The Hunger Tide Rises'); a=g.add('Deathgreeter'); b=g.add('Viscera Seer'); g.resolve()
        mv2=g.add('Blood Artist',mana_value=2); mv3=g.add('Sangromancer',mana_value=3)
        g.destroy(mv2.uid); g.destroy(mv3.uid); g.resolve(); return g,a,b,mv2,mv3
    def test_two_sacrifices_mv2_eligible_mv3_not(self):
        g,a,b,mv2,mv3=self.board()
        with self.assertRaises(IllegalAction): g.saga_chapter(4,sacrifice_uids=(a.uid,b.uid),grave_selection_uid=mv3.uid)
        self.assertEqual(trace(g,'sacrifice'),[])             # preflight rejected before any mutation
        g.saga_chapter(4,sacrifice_uids=(a.uid,b.uid),grave_selection_uid=mv2.uid)
        self.assertEqual([t[1] for t in trace(g,'sacrifice')],[a.uid,b.uid])
        self.assertEqual(trace(g,'reanimate')[-1][1],mv2.uid)
        self.assertEqual(len(trace(g,'saga_sacrifice_after_final_chapter')),1)
        self.assertNotIn('The Hunger Tide Rises',[t[2] for t in trace(g,'sacrifice')])   # Saga leave is not a creature sacrifice
    def test_library_branch_mv_filter_and_shuffle_flag(self):
        g,a,b,mv2,mv3=self.board()
        i2=g.put_creature_in_fixture_library('Deathgreeter',mana_value=2); i3=g.put_creature_in_fixture_library('Blood Artist',mana_value=3)
        with self.assertRaises(IllegalAction): g.saga_chapter(4,sacrifice_uids=(a.uid,b.uid),library_selection_index=i3)
        g.saga_chapter(4,sacrifice_uids=(a.uid,b.uid),library_selection_index=i2)
        self.assertEqual(trace(g,'fixture_library_found_to_battlefield'),[('fixture_library_found_to_battlefield','Deathgreeter')])
        self.assertEqual(len(trace(g,'fixture_library_shuffled_unmodeled')),1)
    def test_control_no_sacrifice_only_mv0(self):
        g=self.game(SAVRA,'The Hunger Tide Rises'); c0=g.add('Deathgreeter',mana_value=0); c1=g.add('Viscera Seer',mana_value=1)
        g.destroy(c0.uid); g.destroy(c1.uid); g.resolve()
        with self.assertRaises(IllegalAction): g.saga_chapter(4,grave_selection_uid=c1.uid)
        g.saga_chapter(4,grave_selection_uid=c0.uid); self.assertEqual(trace(g,'reanimate')[-1][1],c0.uid)


class C59(_Base):
    CONTRACT='C59'; ISSUES=['R31']; STATUS='EXECUTED'; SUBSTITUTIONS=[]
    def test_ceiling_is_sacrificed_count_not_token_count(self):
        g=self.game(SAVRA,'The Hunger Tide Rises'); g.make_tokens(PEST,4); g.resolve()
        one=g.add('Deathgreeter'); mv1=g.add('Viscera Seer',mana_value=1); mv4=g.add('Blood Artist',mana_value=4)
        g.destroy(mv1.uid); g.destroy(mv4.uid); g.resolve()
        self.assertEqual(len(tokens(g,PEST)),4)
        with self.assertRaises(IllegalAction): g.saga_chapter(4,sacrifice_uids=(one.uid,),grave_selection_uid=mv4.uid)
        g.saga_chapter(4,sacrifice_uids=(one.uid,),grave_selection_uid=mv1.uid)
        self.assertEqual(len([t for t in trace(g,'reanimate')]),1)
    def test_control_three_sacrifices_ceiling_three(self):
        g=self.game(SAVRA,'The Hunger Tide Rises'); cs=[g.add('Deathgreeter') for _ in range(3)]
        mv3=g.add('Blood Artist',mana_value=3); g.destroy(mv3.uid); g.resolve()
        g.saga_chapter(4,sacrifice_uids=tuple(c.uid for c in cs),grave_selection_uid=mv3.uid)
        self.assertEqual(trace(g,'reanimate')[-1][1],mv3.uid)


class C60(_Base):
    CONTRACT='C60'; ISSUES=['R32']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Devour is not modeled: Roaster is added with counters=2 and the two devoured creatures are sacrificed '
                   'directly before it enters (ordering as a fixture, not a replacement-effect model)']
    def test_two_counters_two_pests_two_squirrels_at_end_step(self):
        g=self.game(SAVRA,'Chatterfang, Squirrel General'); v1=g.add('Deathgreeter'); v2=g.add('Viscera Seer'); g.resolve()
        g.sacrifice(v1.uid); g.sacrifice(v2.uid)
        self.assertEqual(labels(g).count('Savra black sacrifice'),2)
        g.resolve(); r=g.add('Ribtruss Roaster',counters=2); g.resolve()
        g.roaster_end_step(); g.resolve()
        self.assertEqual((len(tokens(g,PEST)),len(tokens(g,SQUIRREL))),(2,2))
    def test_control_devour_zero_no_pests(self):
        g=self.game('Ribtruss Roaster'); g.roaster_end_step(); g.resolve(); self.assertEqual(len(tokens(g,PEST)),0)


class C61(_Base):
    CONTRACT='C61'; ISSUES=['R32']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Counter added/removed by direct Permanent.counters mutation between trigger and resolution. '
                   'R47 promoted: count is read at resolution. The frozen v0.7 engine\'s trigger-time snapshot is pinned below.']
    def test_contract_counter_count_read_at_resolution(self):
        g=self.game('Ribtruss Roaster'); r=find(g,'Ribtruss Roaster'); r.counters=1
        g.roaster_end_step(); r.counters=2; g.resolve()
        self.assertEqual(len(tokens(g,PEST)),2)
        self.assertIn(('roaster_counters_at_resolution',r.uid,2),g.trace)
    def test_contract_counter_removed_before_resolution(self):
        g=self.game('Ribtruss Roaster'); r=find(g,'Ribtruss Roaster'); r.counters=2
        g.roaster_end_step(); r.counters=1; g.resolve()
        self.assertEqual(len(tokens(g,PEST)),1)
    def test_control_source_leaves_before_resolution_uses_lki(self):
        # R49 (CR 608.2h): the original R47 control wrongly expected 0 here.
        g=self.game('Ribtruss Roaster'); r=find(g,'Ribtruss Roaster'); r.counters=2
        g.roaster_end_step(); g.destroy(r.uid); g.resolve()
        self.assertEqual(len(tokens(g,PEST)),2)
    def test_frozen_v07_engine_snapshots_count_at_trigger(self):
        """Pins the FROZEN v0.7 behaviour (R47) so the discrepancy stays documented."""
        import pab_focus_engine_v07 as v07
        g=v07.Game(); g.add('Ribtruss Roaster'); g.resolve(); r=find(g,'Ribtruss Roaster'); r.counters=1
        g.roaster_end_step(); r.counters=2; g.resolve()
        self.assertEqual(len(tokens(g,PEST)),1)

class C62(_Base):
    CONTRACT='C62'; ISSUES=['R33']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Beledros "Pay 10 life: untap all lands" and once-per-turn tracking are not modeled; the event kernel has no lands']
    def test_blocked_untap_ability_not_modeled(self):
        g=self.game('Beledros Witherbloom')
        self.assertFalse(any('untap' in n.lower() or 'beledros' in n.lower() for n in dir(g)))


class C63(_Base):
    CONTRACT='C63'; ISSUES=['R33','R01']
    STATUS='EXECUTED'; SUBSTITUTIONS=[]   # S2: clock-driven upkeep; S3: set_trigger_order() is the controller's ordering choice
    def test_s3_ordering_api_beledros_first_one_pest(self):
        g=self.game('Beledros Witherbloom','Pest Rescuer'); g.set_trigger_order(lambda batch: list(reversed(batch)))
        g.advance_to('upkeep',active_player=0)
        self.assertEqual(labels(g),['Beledros each upkeep','Pest Rescuer conditional upkeep']); g.resolve(); self.assertEqual(len(tokens(g,PEST)),1)
    def test_clock_driven_upkeep_admits_both_rescuer_first(self):
        g=self.game('Beledros Witherbloom','Pest Rescuer'); g.advance_to('upkeep',active_player=0)
        self.assertEqual(labels(g),['Pest Rescuer conditional upkeep','Beledros each upkeep']); g.resolve(); self.assertEqual(len(tokens(g,PEST)),2)
    def test_rescuer_first_two_pests(self):
        g=self.game('Beledros Witherbloom','Pest Rescuer'); g.begin_upkeep()
        self.assertEqual(labels(g),['Pest Rescuer conditional upkeep','Beledros each upkeep'])   # both admitted
        g.resolve(); self.assertEqual(len(tokens(g,PEST)),2)
    def test_beledros_first_one_pest(self):
        g=self.game('Beledros Witherbloom','Pest Rescuer'); g.begin_upkeep()
        self.assertEqual(len(g.pending),2); g.pending.reverse()
        self.assertEqual(labels(g),['Beledros each upkeep','Pest Rescuer conditional upkeep'])
        g.resolve(); self.assertEqual(len(tokens(g,PEST)),1)  # Rescuer's intervening-if now false
    def test_control_pest_present_only_beledros_triggers(self):
        g=self.game('Beledros Witherbloom','Pest Rescuer'); g.make_tokens(PEST); g.resolve(); g.begin_upkeep()
        self.assertEqual(labels(g),['Beledros each upkeep']); g.resolve(); self.assertEqual(len(tokens(g,PEST)),2)


class C64(_Base):
    CONTRACT='C64'; ISSUES=['R34']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['The discard-a-card-to-draw Learn branch is not modeled (traced as not modeled); Hunt\'s cast is the direct method call']
    def test_lesson_outside_mainboard_and_retrieved_only_with_pod_rule(self):
        g=PhysicalZoneGame(learn_sideboard_allowed=True)   # Hunt is a spell: cast via hunt_for_specimens()
        z=g.zones; self.assertEqual((len(z.zones['library']),len(z.zones['outside_game'])),(99,1))
        g.hunt_for_specimens(lesson=True); g.resolve()
        self.assertEqual(len(tokens(g,PEST)),1)
        self.assertEqual((len(z.zones['library']),len(z.zones['outside_game'])),(99,0))
        self.assertEqual([z.cards[u].name for u in z.zones['hand']],['Pest Summoning'])
        self.assertNotIn('Pest Summoning',g.hand)             # never a fake event-kernel card
        with self.assertRaises(ZoneError): g.hunt_for_specimens(lesson=True)   # one Lesson only
    def test_control_without_pod_rule_lesson_refused_pest_still_made(self):
        g=PhysicalZoneGame(learn_sideboard_allowed=False)
        with self.assertRaises(ZoneError): g.hunt_for_specimens(lesson=True)
        g.hunt_for_specimens(lesson=False); g.resolve()
        self.assertEqual(len(tokens(g,PEST)),1); self.assertEqual(len(g.zones.zones['outside_game']),1)
        self.assertIn(('learn_choice','discard/draw or decline not modeled'),g.trace)

if __name__=='__main__':
    unittest.main()
