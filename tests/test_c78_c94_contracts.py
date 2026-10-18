"""Executable contracts C78–C94 (issues R41–R46, the 11 reference-unsupported
nonlands) against the promoted kernel.

Same status conventions as the earlier contract files. A BLOCKED_UNSUPPORTED
probe asserts only that the kernel refuses the card (`add()` raises
IllegalAction: no verified partial definition) without mutating state.
No contract is Oracle/CR-authenticated.
"""
import sys, unittest
from collections import deque
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST, SAVRA, BODIES, NONCREATURE, IllegalAction
from pab_zones import DeckZones
from pab_kernel import Game

def labels(g): return [t.label for t in g.pending]
def tokens(g,kind): return [p for p in g.permanents.values() if p.token==kind]
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _Base(unittest.TestCase):
    def game(self,*names,**kw):
        g=Game(**kw)
        for n in names: g.add(n)
        g.resolve(); return g
    def assert_card_refused(self,name):
        g=self.game(SAVRA); before=(dict(g.permanents),list(g.pending),list(g.trace),list(g.graveyard))
        with self.assertRaises(IllegalAction): g.add(name)
        self.assertEqual((dict(g.permanents),list(g.pending),list(g.trace),list(g.graveyard)),before)
        self.assertNotIn(name,BODIES)
        return g
    def zero_toughness_via_yawgmoth(self,g,target_uid):
        """Only modeled -1/-1 path: Yawgmoth's activation (cost sacrifice resolved first)."""
        y=g.add('Yawgmoth, Thran Physician'); cost=g.add('Deathgreeter'); g.resolve()
        g.yawgmoth_sacrifice(y.uid,cost.uid,target_uid=target_uid)
        cost_labels=labels(g); self.assertIn('Savra black sacrifice',cost_labels)
        g.pending=deque(t for t in g.pending if t.label=='Yawgmoth activation')   # drop cost-side triggers; keep the activation
        return y


class C78(_Base):
    CONTRACT='C78'; ISSUES=['R41']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=["Golgari Charm's global -1/-1 mode is not modeled; the single modeled -1/-1 path (Yawgmoth counter) "
                   'is used; cost-side triggers are discarded so only the target death is measured']
    def test_zero_toughness_death_observers_but_no_savra_sacrifice(self):
        g=self.game(SAVRA,'Blood Artist'); pest=g.make_tokens(PEST)[0]; g.resolve()
        self.zero_toughness_via_yawgmoth(g,pest.uid)
        g.resolve()                                           # Yawgmoth resolution: counter, draw, SBA
        self.assertNotIn(pest.uid,g.permanents)
        self.assertEqual(trace(g,'destroy'),[('destroy',pest.uid,'ordinary Pest')])
        self.assertEqual([t for t in trace(g,'sacrifice') if t[1]==pest.uid],[])
        res=[t[1] for t in trace(g,'resolve')]
        self.assertIn('Blood Artist target drain',res); self.assertIn('Pest dies-gain',res)
        self.assertNotIn('Savra black sacrifice',res[res.index('Yawgmoth activation'):]); self.assertNotIn('Savra green sacrifice',res[res.index('Yawgmoth activation'):])


class C79(_Base):
    CONTRACT='C79'; ISSUES=['R42']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Heroic Intervention not modeled; indestructible is granted by adding the creature to '
                   'indestructible_until_eot (the kernel\'s own until-end-of-turn set). Hexproof and exile are not modeled. '
                   'R48 promoted: zero toughness is an SBA death. The frozen v0.7 behaviour is pinned below.']
    def protected_pest(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); g.indestructible_until_eot.add(p.uid); return g,p
    def test_destroy_prevented(self):
        g,p=self.protected_pest(); g.destroy(p.uid)
        self.assertIn(p.uid,g.permanents); self.assertEqual(trace(g,'destroy_prevented_indestructible'),[('destroy_prevented_indestructible',p.uid)])
    def test_sacrifice_still_happens(self):
        g,p=self.protected_pest(); g.sacrifice(p.uid); self.assertNotIn(p.uid,g.permanents)
        self.assertIn('Savra black sacrifice',labels(g))
    def test_contract_zero_toughness_still_dies_despite_indestructible(self):
        g,p=self.protected_pest(); self.zero_toughness_via_yawgmoth(g,p.uid); g.resolve()
        self.assertNotIn(p.uid,g.permanents)                  # contract / CR 704.5f
        self.assertEqual(trace(g,'sba_zero_toughness'),[('sba_zero_toughness',p.uid,'Yawgmoth')])
        self.assertEqual(trace(g,'destroy_prevented_indestructible'),[])
        self.assertEqual([t for t in trace(g,'sacrifice') if t[1]==p.uid],[])
    def test_frozen_v07_engine_indestructible_blocks_zero_toughness_death(self):
        """Pins the FROZEN v0.7 behaviour (R48): its Yawgmoth SBA path called destroy()."""
        import pab_focus_engine_v07 as v07
        g=v07.Game(); g.add(SAVRA); g.resolve(); p=g.make_tokens(PEST)[0]; g.resolve(); g.indestructible_until_eot.add(p.uid)
        self.zero_toughness_via_yawgmoth(g,p.uid); g.resolve()
        self.assertIn(p.uid,g.permanents); self.assertEqual(len(trace(g,'destroy_prevented_indestructible')),1)
    def test_control_expires_at_turn_reset(self):
        g,p=self.protected_pest(); g.reset_turn(); g.destroy(p.uid); self.assertNotIn(p.uid,g.permanents)


class C80(_Base):
    CONTRACT='C80'; ISSUES=['R41','R43']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Witherbloom Charm (modes, optional resolution-time sacrifice) not modeled. The Village Rites '
                   'additional-cost contrast from the contract IS executed as a control.']
    def test_blocked(self): self.assert_card_refused('Witherbloom Charm')
    def test_control_village_rites_sacrifice_is_a_cost_before_cast(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); g.cast_with_sacrifice_cost('Village Rites',p.uid)
        i_cost=g.trace.index(('cost_start','Village Rites')); i_sac=g.trace.index(('sacrifice',p.uid,'ordinary Pest')); i_cast=g.trace.index(('cast','Village Rites'))
        self.assertLess(i_cost,i_sac); self.assertLess(i_sac,i_cast)


class C81(_Base):
    CONTRACT='C81'; ISSUES=['R42']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Regeneration not modeled; Golgari Charm refused']
    def test_blocked(self):
        g=self.assert_card_refused('Golgari Charm'); self.assertFalse(any('regenerat' in a.lower() for a in dir(g)))

class C82(_Base):
    CONTRACT='C82'; ISSUES=['R42']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Infuse with Vitality (granted owner-return death trigger) not modeled; opponent-owned objects not modeled']
    def test_blocked(self): self.assert_card_refused('Infuse with Vitality')

class C83(_Base):
    CONTRACT='C83'; ISSUES=['R43']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Abrupt Decay (targeting, MV filter, uncounterable, fizzle) not modeled; no opponent permanents']
    def test_blocked(self): self.assert_card_refused('Abrupt Decay')

class C84(_Base):
    CONTRACT='C84'; ISSUES=['R43']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=["Assassin's Trophy not modeled; no opponent permanents or opponent library search"]
    def test_blocked(self): self.assert_card_refused("Assassin's Trophy")

class C85(_Base):
    CONTRACT='C85'; ISSUES=['R44']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Rise of the Witch-king not modeled; no per-player sacrifice choices']
    def test_blocked(self): self.assert_card_refused('Rise of the Witch-king')

class C86(_Base):
    CONTRACT='C86'; ISSUES=['R44']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Rise of the Witch-king not modeled']
    def test_blocked(self): self.assert_card_refused('Rise of the Witch-king')


class C87(_Base):
    CONTRACT='C87'; ISSUES=['R45']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Grisly Salvage is not a kernel spell; its resolution is composed from physical-zone primitives in the '
                   'fixture (top five by library order, chosen creature/land to hand, rest to graveyard, no shuffle)']
    def is_creature_or_land(self,z,uid):
        n=z.cards[uid].name; return z.cards[uid].is_land or (n in BODIES and n not in NONCREATURE)
    def salvage(self,z,choose):
        top=list(z.zones['library'][:5]); rest=list(z.zones['library'][5:])
        chosen=next((u for u in top if choose and self.is_creature_or_land(z,u)),None)
        for u in top: z.move(u,'hand' if u==chosen else 'graveyard')
        return top,rest,chosen
    def test_top_five_one_to_hand_rest_graveyard_no_shuffle(self):
        z=DeckZones(seed=3); n0=len(z.zones['library'])
        top,rest,chosen=self.salvage(z,choose=True)
        self.assertIsNotNone(chosen)
        self.assertEqual(z.zones['hand'],[chosen]); self.assertEqual(sorted(z.zones['graveyard']),sorted(set(top)-{chosen}))
        self.assertEqual(z.zones['library'],rest); self.assertEqual(len(z.zones['library']),n0-5)
        self.assertEqual([t for t in z.trace if t[0]=='library_shuffled'],[])
    def test_none_eligible_branch_all_five_to_graveyard(self):
        z=DeckZones(seed=3)
        spells=[u for u in z.zones['library'] if not self.is_creature_or_land(z,u)][:5]
        for u in reversed(spells): z.move(u,'hand'); z.move(u,'library',top=True)   # arrange a creature/land-free top five
        top,rest,chosen=self.salvage(z,choose=True)
        self.assertIsNone(chosen); self.assertEqual(z.zones['hand'],[]); self.assertEqual(sorted(z.zones['graveyard']),sorted(top))


class C88(_Base):
    CONTRACT='C88'; ISSUES=['R45']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Shigeki, Jukai Visionary not modeled (self-bounce cost, top-four reveal)']
    def test_blocked(self): self.assert_card_refused('Shigeki, Jukai Visionary')

class C89(_Base):
    CONTRACT='C89'; ISSUES=['R45','R18']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Shigeki Channel {X}{X}{G}{G} not modeled']
    def test_blocked(self): self.assert_card_refused('Shigeki, Jukai Visionary')

class C90(_Base):
    CONTRACT='C90'; ISSUES=['R45']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Shigeki Channel legendary-exclusion targeting not modeled']
    def test_blocked(self): self.assert_card_refused('Shigeki, Jukai Visionary')

class C91(_Base):
    CONTRACT='C91'; ISSUES=['R46']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Grist, the Hunger Tide not modeled; physical cards carry no type line, so zone-dependent types cannot be asserted']
    def test_blocked(self):
        self.assert_card_refused('Grist, the Hunger Tide')
        z=DeckZones(); c=z.cards[next(u for u in z.zones['library'] if z.cards[u].name=='Grist, the Hunger Tide')]
        self.assertFalse(hasattr(c,'types'))

class C92(_Base):
    CONTRACT='C92'; ISSUES=['R46']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Grist +1 (Insect token, mill, repeat on Insect card) not modeled; composing the loop from mill '
                   'primitives would fabricate Grist, so only the refusal is asserted']
    def test_blocked(self): self.assert_card_refused('Grist, the Hunger Tide')

class C93(_Base):
    CONTRACT='C93'; ISSUES=['R46','R20']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Grist -2 reflexive trigger not modeled']
    def test_blocked(self): self.assert_card_refused('Grist, the Hunger Tide')

class C94(_Base):
    CONTRACT='C94'; ISSUES=['R41','R43']; STATUS='BLOCKED_UNSUPPORTED'
    SUBSTITUTIONS=['Witherbloom Command (two distinct modes, mill target player, return land) not modeled']
    def test_blocked(self): self.assert_card_refused('Witherbloom Command')

if __name__=='__main__':
    unittest.main()
