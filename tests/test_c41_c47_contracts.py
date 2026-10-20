"""Executable contracts C41–C47 (issues R22–R26) against the promoted kernel.

Each class declares CONTRACT, STATUS and SUBSTITUTIONS. STATUS is
'EXECUTED' only when every named card and mechanic in the contract setup is
modeled; otherwise 'EXECUTED_WITH_SUBSTITUTION' and SUBSTITUTIONS names what
was replaced by an exogenous fixture action. run_validation.py collects these
into the C41–C47 status record. No contract here is Oracle/CR-authenticated.
Expectations are the contract bodies' provisional expectations, transcribed.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST, WORM, TREASURE, SAVRA, IllegalAction
from pab_kernel import Game

def labels(g): return [t.label for t in g.pending]
def tokens(g,kind): return [p for p in g.permanents.values() if p.token==kind]
def trace(g,key): return [t for t in g.trace if t[0]==key]
def find(g,name): return next(p for p in g.permanents.values() if p.name==name)

class _Base(unittest.TestCase):
    def game(self,*names,**kw):
        g=Game(**kw)
        for n in names: g.add(n)
        g.resolve(); return g
    def treasure_board(self,*names):
        """Contract setup: the Treasure is ALREADY on the battlefield. Creating it
        before Mirkwood Bats enters keeps Bats' creation drain out of the measurement."""
        g=self.game(*[n for n in names if n!='Mirkwood Bats'])
        t=g.make_tokens(TREASURE)[0]; g.resolve()
        if 'Mirkwood Bats' in names: g.add('Mirkwood Bats'); g.resolve()
        self.assertEqual(g.life,[40,40,40,40]); return g,t


class C41(_Base):
    CONTRACT='C41'; ISSUES=['R22']
    STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['High Market: modeled in S14 on PhysicalZoneGame (high_market); this test keeps the event-kernel '
                   'stand-in, an exogenous gain(1) after the end-step boundary; sacrifice cost modeled as sacrifice of a '
                   'controlled creature',
                   'engine has no step clock: "beginning of end step" is the moseo_end_step() call; '
                   'non-retroactivity is asserted on the trigger queue and trace, not on a timing model']

    def test_no_gain_no_moseo_trigger_at_end_step_boundary(self):
        g=self.game(SAVRA,"Moseo, Vein's New Dean",'Deathgreeter')
        g.resolve(); g.reset_turn()                      # Moseo ETB Pest resolved; fresh turn
        self.assertEqual(g.life_gained_turn,0)
        admitted=g.moseo_end_step()                      # boundary check
        self.assertFalse(admitted)
        self.assertNotIn('Moseo infusion end step',labels(g))
        self.assertEqual(trace(g,'moseo_choose_no_target'),[])   # not even a no-target admission

    def test_gain_after_boundary_is_not_retroactive_but_is_accounted(self):
        g=self.game(SAVRA,"Moseo, Vein's New Dean"); g.resolve(); g.reset_turn()
        self.assertFalse(g.moseo_end_step())
        pest=tokens(g,PEST)[0] if tokens(g,PEST) else g.make_tokens(PEST)[0]
        g.sacrifice(pest.uid)                            # High Market cost stand-in
        g.resolve()
        g.gain(1,'High Market stand-in (exogenous)')     # gain later in the end step
        g.resolve()
        self.assertGreaterEqual(g.life_gained_turn,1)    # preserved for turn accounting
        self.assertNotIn('Moseo infusion end step',labels(g))
        self.assertEqual([t for t in g.trace if t[0]=='resolve' and 'Moseo' in t[1]],[])

    def test_control_gain_before_boundary_admits_trigger_with_target(self):
        g=self.game(SAVRA,"Moseo, Vein's New Dean"); g.resolve(); g.reset_turn()
        dead=g.add('Deathgreeter',mana_value=1); g.sacrifice(dead.uid); g.resolve()
        g.gain(1,'manual'); g.resolve()
        self.assertTrue(g.moseo_end_step(dead.uid))
        self.assertIn('Moseo infusion end step',labels(g))


class C42(_Base):
    CONTRACT='C42'; ISSUES=['R22','R21']
    STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Infuse with Vitality: modeled in S15 on PhysicalZoneGame; this test keeps the event-kernel stand-in, '
                   'an exogenous gain(2) base event; the Pest Rescuer +1 replacement is the kernel\'s own']

    def setup_board(self):
        g=self.game(SAVRA,"Moseo, Vein's New Dean",'Pest Rescuer','Phyrexian Reclamation')
        g.resolve(); g.reset_turn()
        mv3=g.add('Deathgreeter',mana_value=3); mv4=g.add('Blood Artist',mana_value=4)
        recl=g.add('Viscera Seer',mana_value=2)
        for u in (mv3.uid,mv4.uid,recl.uid): g.destroy(u)
        g.resolve(); g.reset_turn()
        return g,mv3,mv4,recl

    def test_gross_gain_three_despite_paying_two(self):
        g,mv3,mv4,recl=self.setup_board()
        base=g.life[0]
        g.gain(2,'Infuse with Vitality stand-in (exogenous)')     # base 2 -> replaced 3
        self.assertEqual(trace(g,'gain')[-1][1],3)
        g.add_mana('B','C'); g.phyrexian_reclamation(recl.uid); g.resolve()
        self.assertEqual(trace(g,'pay_life')[-1][1],2)
        self.assertEqual(g.life_gained_turn,3)                   # gross, not net +1
        self.assertEqual(g.life[0],base+3-2)

    def test_mv3_eligible_mv4_not(self):
        g,mv3,mv4,recl=self.setup_board()
        g.gain(2,'exogenous'); g.resolve()
        with self.assertRaises(IllegalAction): g.moseo_end_step(mv4.uid)
        self.assertTrue(g.moseo_end_step(mv3.uid))

    def test_target_locked_after_later_response_gain(self):
        g,mv3,mv4,recl=self.setup_board()
        g.gain(2,'exogenous'); g.resolve()
        self.assertTrue(g.moseo_end_step(mv3.uid))             # trigger on stack with target mv3
        g.gain(5,'response-window gain'); g.resolve()            # resolves everything incl. Moseo
        names=[p.name for p in g.permanents.values()]
        self.assertIn('Deathgreeter',names); self.assertNotIn('Blood Artist',names)
        self.assertEqual(trace(g,'reanimate')[-1][1],mv3.uid)

    def test_control_without_rescuer_base_gain_is_two(self):
        g=self.game(SAVRA,"Moseo, Vein's New Dean"); g.resolve(); g.reset_turn()
        g.gain(2,'exogenous')
        self.assertEqual(g.life_gained_turn,2)


class C43(_Base):
    CONTRACT='C43'; ISSUES=['R23','R06','R09']
    STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Treasure mana ability not modeled: the sacrifice is performed directly; '
                   'no mana is added (mana creation is outside this contract\'s life-loss claims)']

    def test_treasure_sacrifice_two_life_loss_no_savra_triggers(self):
        g,t=self.treasure_board(SAVRA,'Agent of the Iron Throne','Mirkwood Bats')
        self.assertTrue(t.artifact and not t.creature)
        g.sacrifice(t.uid)
        self.assertEqual(sorted(labels(g)),sorted(['Mirkwood Bats token sacrifice','Agent-granted commander artifact drain']))
        g.resolve()
        self.assertEqual(g.life,[40,38,38,38])
        self.assertEqual(trace(g,'edict_opportunity'),[]); self.assertEqual(trace(g,'gain'),[])
        self.assertNotIn(t,g.graveyard)                          # token ceased; not a graveyard object

    def test_control_without_bats_one_loss(self):
        g=self.game(SAVRA,'Agent of the Iron Throne')
        t=g.make_tokens(TREASURE)[0]; g.resolve(); g.sacrifice(t.uid); g.resolve()
        self.assertEqual(g.life,[40,39,39,39])

    def test_control_no_fabricated_creature_death(self):
        g,t=self.treasure_board(SAVRA,'Agent of the Iron Throne','Mirkwood Bats','Blood Artist','Blight Mound')
        g.sacrifice(t.uid)
        self.assertNotIn('Blood Artist target drain',labels(g))
        self.assertNotIn('Blight Mound nontoken death Pest',labels(g))


class C44(_Base):
    CONTRACT='C44'; ISSUES=['R23']
    STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Command zone: modeled in S10 on PhysicalZoneGame; this test keeps the event-kernel stand-in: in '
                   'branch B, Savra is removed from the battlefield by an exogenous harness deletion (no death event), '
                   'standing in for the commander-zone replacement']

    def test_A_savra_in_command_zone_only_bats(self):
        g,t=self.treasure_board('Agent of the Iron Throne','Mirkwood Bats')   # Savra absent from battlefield
        g.sacrifice(t.uid)
        self.assertEqual(labels(g),['Mirkwood Bats token sacrifice'])
        g.resolve(); self.assertEqual(g.life,[40,39,39,39])

    def test_B_granted_trigger_persists_after_host_leaves(self):
        g,t=self.treasure_board(SAVRA,'Agent of the Iron Throne','Mirkwood Bats')
        g.sacrifice(t.uid)
        self.assertIn('Agent-granted commander artifact drain',labels(g))
        savra=find(g,SAVRA); del g.permanents[savra.uid]             # exogenous: to command zone, no death
        g.trace.append(('exogenous_zone_change',savra.uid,'command zone'))
        g.resolve()
        self.assertEqual(g.life,[40,38,38,38])
        self.assertEqual(trace(g,'sacrifice')+trace(g,'destroy'),[('sacrifice',t.uid,'Treasure')])


class C45(_Base):
    CONTRACT='C45'; ISSUES=['R24','R01']
    STATUS='EXECUTED'; SUBSTITUTIONS=[]

    def test_equip_1_1_pest_sba_death_no_sacrifice(self):
        g=self.game(SAVRA,'Skullclamp'); pest=g.make_tokens(PEST)[0]; g.resolve()
        clamp=find(g,'Skullclamp'); g.add_mana('C')
        g.equip_skullclamp(clamp.uid,pest.uid)
        self.assertIn(('sba_zero_toughness',pest.uid,'Skullclamp'),g.trace)
        self.assertEqual(trace(g,'destroy'),[('destroy',pest.uid,'ordinary Pest')])
        self.assertEqual(trace(g,'sacrifice'),[])
        self.assertEqual(sorted(labels(g)),sorted(['Skullclamp equipped death draw two','Pest dies-gain']))
        self.assertNotIn('Savra black sacrifice',labels(g)); self.assertNotIn('Savra green sacrifice',labels(g))
        g.resolve()
        self.assertEqual(g.cards_drawn,2); self.assertEqual(g.life[0],41)

    def test_control_sacrificing_pest_yields_savra_triggers(self):
        g=self.game(SAVRA); pest=g.make_tokens(PEST)[0]; g.resolve(); g.sacrifice(pest.uid)
        self.assertIn('Savra black sacrifice',labels(g)); self.assertIn('Savra green sacrifice',labels(g))


class C46(_Base):
    CONTRACT='C46'; ISSUES=['R25','R14']
    STATUS='EXECUTED'; SUBSTITUTIONS=[]

    def test_tend_uses_power_with_counter(self):
        g=self.game(SAVRA); feeder=g.add('Carrion Feeder',counters=1,power=1); g.resolve()
        g.add_mana('B','G'); g.cast_pab_spell('Tend the Pests',feeder.uid)
        self.assertEqual(trace(g,'token_created'),[])                # nothing exists during cost payment
        i_sac=g.trace.index(('sacrifice',feeder.uid,'Carrion Feeder'))
        g.resolve()
        pests=tokens(g,PEST); self.assertEqual(len(pests),2)
        self.assertTrue(all(p.colors=='BG' and 'Pest' in p.subtypes and p.token.dies_gain==1 for p in pests))
        self.assertLess(i_sac,g.trace.index(trace(g,'token_created')[0]))

    def test_control_no_counter_one_pest(self):
        g=self.game(SAVRA); feeder=g.add('Carrion Feeder'); g.resolve()
        g.add_mana('B','G'); g.cast_pab_spell('Tend the Pests',feeder.uid); g.resolve()
        self.assertEqual(len(tokens(g,PEST)),1)


class C47(_Base):
    CONTRACT='C47'; ISSUES=['R26','R14']
    STATUS='EXECUTED'; SUBSTITUTIONS=[]

    def test_grub_death_triggers_mound_and_worms(self):
        g=self.game(SAVRA,'Blight Mound'); grub=g.add('Wriggling Grub'); g.resolve()
        g.sacrifice(grub.uid)
        self.assertIn('Blight Mound nontoken death Pest',labels(g)); self.assertIn('Wriggling Grub death Worms',labels(g))
        g.resolve()
        worms=tokens(g,WORM); self.assertEqual(len(worms),2); self.assertEqual(len(tokens(g,PEST)),1)
        self.assertTrue(all('Pest' not in w.subtypes and not w.token.dies_gain for w in worms))

    def test_pest_token_death_does_not_trigger_mound(self):
        g=self.game(SAVRA,'Blight Mound'); pest=g.make_tokens(PEST)[0]; g.resolve()
        g.sacrifice(pest.uid)
        self.assertNotIn('Blight Mound nontoken death Pest',labels(g)); self.assertIn('Pest dies-gain',labels(g))
        g.resolve(); self.assertEqual(g.life[0],41); self.assertEqual(len(tokens(g,PEST)),0)

    def test_control_generated_tokens_dying_no_recursive_mound(self):
        g=self.game('Blight Mound'); grub=g.add('Wriggling Grub'); g.resolve(); g.sacrifice(grub.uid); g.resolve()
        for t in tokens(g,WORM)+tokens(g,PEST): g.sacrifice(t.uid)
        self.assertNotIn('Blight Mound nontoken death Pest',labels(g))
        g.resolve(); self.assertEqual(len(tokens(g,PEST))+len(tokens(g,WORM)),0)

if __name__=='__main__':
    unittest.main()
