"""Phase-clock stage S3: state-based actions between resolutions, simultaneous-death
look-back, retired inline Yawgmoth check, controller trigger ordering.
Executes C97. CR refs: 704.3, 117.5, 704.5f, 603.10, 603.3b.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST, SAVRA
from pab_kernel import Game

def pests(g): return sum(p.token==PEST for p in g.permanents.values())
def labels(g): return [t.label for t in g.pending]
def trace(g,key): return [t for t in g.trace if t[0]==key]
def resolved(g): return [t[1] for t in g.trace if t[0]=='resolve']

class _B(unittest.TestCase):
    def game(self,*names,**kw):
        g=Game(**kw)
        for n in names: g.add(n)
        g.resolve(); return g

class C97(_B):
    CONTRACT='C97'; ISSUES=['R24','R48']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['The synthetic "one effect gives two creatures -1/-1" is applied by direct minus_counters mutation; no card is modeled for it']
    def test_sba_after_full_resolution_not_mid_effect(self):
        g=self.game(SAVRA); y=g.add('Yawgmoth, Thran Physician'); g.resolve()
        p=g.make_tokens(PEST)[0]; c=g.add('Deathgreeter'); g.resolve()
        g.yawgmoth_sacrifice(y.uid,c.uid,target_uid=p.uid); g.resolve()
        k=[t[0] for t in g.trace]
        self.assertLess(k.index('minus_one_counter'),k.index('draw')); self.assertLess(k.index('draw'),k.index('sba_event'))
        self.assertEqual(trace(g,'sba_zero_toughness'),[('sba_zero_toughness',p.uid,'state-based')])
        r=resolved(g); self.assertLess(r.index('Yawgmoth activation'),r.index('Pest dies-gain'))   # death trigger placed after resolution
    def test_simultaneous_deaths_one_event_with_look_back(self):
        g=self.game(SAVRA,'Blood Artist'); d=g.add('Deathgreeter'); p=g.make_tokens(PEST)[0]; g.resolve()
        d.minus_counters=1; p.minus_counters=1                 # synthetic: one effect, two 1-toughness creatures
        g.resolve()
        self.assertEqual(trace(g,'sba_event'),[('sba_event','zero_toughness',(d.uid,p.uid))])
        self.assertNotIn(d.uid,g.permanents); self.assertNotIn(p.uid,g.permanents)
        r=resolved(g)
        self.assertEqual(r.count('Blood Artist target drain'),2)        # observer sees both deaths
        self.assertEqual(r.count('Deathgreeter death life'),1)          # dying Deathgreeter still saw the Pest die (603.10 look-back)
        self.assertEqual(r.count('Pest dies-gain'),1); self.assertEqual(trace(g,'sacrifice'),[])
    def test_control_no_sba_when_nothing_applies(self):
        g=self.game(SAVRA); n=g.sba_checks; g.resolve(); self.assertGreater(g.sba_checks,n); self.assertEqual(trace(g,'sba_event'),[])

class GeneralCheck(_B):
    def test_direct_mutation_then_resolve_kills(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); p.minus_counters=1; g.resolve()
        self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.life[0],41)
    def test_indestructible_irrelevant_to_general_check(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); g.indestructible_until_eot.add(p.uid); p.minus_counters=1; g.resolve()
        self.assertNotIn(p.uid,g.permanents); self.assertEqual(trace(g,'destroy_prevented_indestructible'),[])
    def test_repeat_until_none_apply(self):
        """CP42 (T4): one creature at toughness 0 dies in one SBA event, and the check runs again before
        priority (sba_checks >= 3). A second round caused by the first is not built here: no card in the
        kernel lets one SBA death put another creature at toughness 0."""
        g=self.game(SAVRA,'Blight Mound'); grub=g.add('Wriggling Grub'); g.resolve(); grub.minus_counters=1; g.resolve()
        self.assertEqual(len(trace(g,'sba_event')),1); self.assertGreaterEqual(g.sba_checks,3)
    def test_skullclamp_equip_keeps_immediate_check(self):
        g=self.game(SAVRA,'Skullclamp'); p=g.make_tokens(PEST)[0]; g.resolve(); clamp=next(x for x in g.permanents.values() if x.name=='Skullclamp')
        g.add_mana('C'); g.equip_skullclamp(clamp.uid,p.uid)
        self.assertIn(('sba_zero_toughness',p.uid,'Skullclamp'),g.trace); self.assertNotIn(p.uid,g.permanents)
    def test_look_back_view_is_dropped_after_event(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); p.minus_counters=1; g.resolve()
        self.assertIs(type(g.permanents),dict)

class TriggerOrdering(_B):
    def test_policy_must_permute(self):
        g=self.game(SAVRA); g.set_trigger_order(lambda b: b[:1])
        p=g.make_tokens(PEST)[0]; g.resolve()
        with self.assertRaises(ValueError): g.sacrifice(p.uid)   # Savra black + green batch truncated
    def test_default_order_unchanged(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); g.sacrifice(p.uid)
        self.assertEqual(labels(g),['Savra black sacrifice','Savra green sacrifice','Pest dies-gain'])
    def test_reversed_order_recorded(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); g.set_trigger_order(lambda b: list(reversed(b))); g.sacrifice(p.uid)
        self.assertEqual(labels(g),['Pest dies-gain','Savra green sacrifice','Savra black sacrifice'])
        self.assertEqual(trace(g,'trigger_order_chosen')[-1][1],('Pest dies-gain','Savra green sacrifice','Savra black sacrifice'))

if __name__=='__main__':
    unittest.main()
