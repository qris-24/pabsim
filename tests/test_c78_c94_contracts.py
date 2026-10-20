"""Executable contracts C78–C94 (issues R41–R46, the 11 reference-unsupported
nonlands) against the promoted kernel.

Same status conventions as the earlier contract files. A BLOCKED_UNSUPPORTED
probe asserts only that the kernel refuses the card (`add()` raises
IllegalAction: no verified partial definition) without mutating state.
No contract is Oracle/CR-authenticated.

CP21: C80-C86 and C88-C94 are re-statused on pab_kernel.PhysicalZoneGame, where
S15 / S16 / S20 model the cards (EVIDENCE/CP19_CONTRACT_PATH_AUDIT.md c.3/c.4).
Each `test_pzg_*` method asserts the contract's claims (the class's former
"not modeled (...)" list and the rules_contract column of the frozen
upstream_frozen/PABTRV3_MECHANICAL_INVENTORY.csv). The former Game.add()
refusal stays in each class as `test_event_kernel_control_add_refused`.
"""
import sys, unittest
from collections import deque
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST, SAVRA, BODIES, NONCREATURE, IllegalAction
from pab_zones import DeckZones
from pab_zone_bridge import BridgeError
from pab_kernel import Game, PhysicalZoneGame
from pab_grist_s16 import GRIST, CREATURE_CARD_NAMES
from pab_shigeki_s20 import SHIGEKI, LEGENDARY_CARDS

BEAR={'name':'Bear','power':2,'toughness':2,'mana_value':2}
WALL={'name':'Wall','power':0,'toughness':4,'mana_value':3}
OGRE={'name':'Ogre','power':3,'toughness':3,'mana_value':4}

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

    # ---- CP21: the PhysicalZoneGame path (S15 / S16 / S20 layers) ----
    def pzg(self,boards=None,*,main=False):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve()
        for seat,bodies in (boards or {}).items(): g.declare_opponent_board(seat,bodies)
        if main: g.advance_to('precombat_main',active_player=0)
        return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=uid,destination='hand'); return uid
    def to_graveyard(self,g,name):
        uid=self.to_hand(g,name); g.zones.move(uid,'graveyard'); return uid
    def stack_library(self,g,names):
        uids=[self.to_hand(g,n) for n in names]
        for u in reversed(uids): g.zones.move(u,'library',top=True)
        self.assertEqual(g.zones.zones['library'][:len(uids)],uids); return uids
    def pest(self,g):
        p=g.make_tokens(PEST)[0]; g.resolve(); return p
    def opp(self,g,seat,name): return next(p.uid for p in g.opponent_creatures(seat) if p.name==name)
    def own(self,g,name): return next(p for p in g.permanents.values() if p.name==name and p.controller==0)
    def cast_physical(self,g,name,*mana,**kw):
        uid=self.to_hand(g,name); g.add_mana(*mana); g.cast_from_hand(uid,**kw); self.assertIn(uid,g.stack_cards); return uid
    def creature(self,g,name):
        self.cast_physical(g,name,'B','B','G','G','C','C','C','C'); g.resolve(); del g.mana_pool[:]; return self.own(g,name)
    def physical_refused(self,g,uid,*mana,**kw):
        """A refused cast changes nothing: hand, pool, permanents, trace, life, stack ledger."""
        g.add_mana(*mana); snap=lambda:(list(g.zones.zones['hand']),list(g.mana_pool),set(g.permanents),len(g.trace),list(g.life),dict(g.stack_cards)); before=snap()
        with self.assertRaises(BridgeError): g.cast_from_hand(uid,**kw)
        self.assertEqual(snap(),before); del g.mana_pool[:]
    def shigeki(self,g):
        ph=self.cast_physical(g,SHIGEKI,'G','C'); g.resolve(); return next(k for k,v in g.linked_battlefield.items() if v==ph),ph
    def grist(self,g):
        ph=self.cast_physical(g,GRIST,'B','G','C'); g.resolve(); return g.grist(),ph


class C78(_Base):
    CONTRACT='C78'; ISSUES=['R41']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=["Golgari Charm's global -1/-1 mode: modeled in S15 on PhysicalZoneGame; this test keeps the event-kernel "
                   'stand-in, the Yawgmoth -1/-1 counter path; cost-side triggers are discarded so only the target death is measured']
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
    SUBSTITUTIONS=['Heroic Intervention: modeled in S15 on PhysicalZoneGame (indestructible_until_eot + hexproof_eot); this '
                   'test keeps the event-kernel stand-in: indestructible is granted by adding the creature to '
                   'indestructible_until_eot (the kernel\'s own until-end-of-turn set). Exile is not modeled. '
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
        self.assertEqual(trace(g,'sba_zero_toughness'),[('sba_zero_toughness',p.uid,'state-based')])   # S3: general check
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
    CONTRACT='C80'; ISSUES=['R41','R43']; STATUS='EXECUTED'
    SUBSTITUTIONS=[]
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: pab_kernel.Game.add() still refuses the card (S15 models it on PhysicalZoneGame only)."""
        self.assert_card_refused('Witherbloom Charm')
    def test_control_village_rites_sacrifice_is_a_cost_before_cast(self):
        g=self.game(SAVRA); p=g.make_tokens(PEST)[0]; g.resolve(); g.cast_with_sacrifice_cost('Village Rites',p.uid)
        i_cost=g.trace.index(('cost_start','Village Rites')); i_sac=g.trace.index(('sacrifice',p.uid,'ordinary Pest')); i_cast=g.trace.index(('cast','Village Rites'))
        self.assertLess(i_cost,i_sac); self.assertLess(i_sac,i_cast)
    def test_pzg_mode1_optional_sacrifice_on_resolution_draws_two(self):
        """CP21 PhysicalZoneGame (S15): mode 1's sacrifice is chosen on resolution, not paid as a cost (the Village Rites
        contrast); it draws two real cards; declining the sacrifice draws nothing."""
        g=self.pzg(); p=self.pest(g); uid=self.cast_physical(g,'Witherbloom Charm','B','G',mode=1,sacrifice_uid=p.uid)
        self.assertIn(p.uid,g.permanents); self.assertIsNone(trace(g,'physical_cast')[-1][4]); self.assertEqual([t for t in trace(g,'sacrifice') if t[1]==p.uid],[])
        g.resolve()
        self.assertNotIn(p.uid,g.permanents); self.assertLess(g.trace.index(('cast','Witherbloom Charm')),g.trace.index(('sacrifice',p.uid,'ordinary Pest')))
        drawn=[t for t in trace(g,'physical_draw') if t[1]=='Witherbloom Charm']; self.assertEqual(len(drawn),1); self.assertEqual(len(drawn[0][2]),2)
        self.assertTrue(all(g.zones.cards[u].zone=='hand' for u in drawn[0][2])); self.assertEqual(g.zones.cards[uid].zone,'graveyard')
        g2=self.pzg(); q=self.pest(g2); self.cast_physical(g2,'Witherbloom Charm','B','G',mode=1); g2.resolve()
        self.assertIn(q.uid,g2.permanents); self.assertIn(('witherbloom_charm_no_sacrifice',),g2.trace); self.assertEqual([t for t in trace(g2,'physical_draw') if t[1]=='Witherbloom Charm'],[])
    def test_pzg_mode2_gain_five_mode3_destroy_mv2_or_less(self):
        g=self.pzg({1:[BEAR,WALL]}); life=g.life[0]; uid=self.cast_physical(g,'Witherbloom Charm','B','G',mode=2); g.resolve(); self.assertEqual(g.life[0],life+5)
        g.zones.move(uid,'library'); uid=self.to_hand(g,'Witherbloom Charm'); bear,wall=self.opp(g,1,'Bear'),self.opp(g,1,'Wall')
        self.physical_refused(g,uid,'B','G',mode=3,target_uid=wall)                     # mana value 3
        self.physical_refused(g,uid,'B','G',mode=4)                                     # choose one of three
        g.add_mana('B','G'); g.cast_from_hand(uid,mode=3,target_uid=bear); g.resolve()
        self.assertNotIn(bear,g.permanents); self.assertIn(wall,g.permanents); self.assertIn(('destroyed_by',bear,'Bear','Witherbloom Charm'),g.trace)


class C81(_Base):
    CONTRACT='C81'; ISSUES=['R42']; STATUS='EXECUTED'
    SUBSTITUTIONS=[]
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() refuses Golgari Charm and the event kernel has no regeneration API."""
        g=self.assert_card_refused('Golgari Charm'); self.assertFalse(any('regenerat' in a.lower() for a in dir(g)))
    def test_pzg_mode3_regenerates_each_creature_you_control(self):
        """CP21 PhysicalZoneGame (S15): one shield per creature you control (none for opponents'); the next destroy
        taps the creature instead and spends the shield; unused shields expire at cleanup."""
        g=self.pzg({1:[BEAR]}); a,b=self.pest(g),self.pest(g); bear=self.opp(g,1,'Bear')
        self.cast_physical(g,'Golgari Charm','B','G',mode=3); g.resolve()
        self.assertEqual(g.regen_shields,{p.uid for p in g.permanents.values() if p.controller==0 and p.creature}); self.assertNotIn(bear,g.regen_shields)
        g.destroy(a.uid); self.assertIn(a.uid,g.permanents); self.assertTrue(g.permanents[a.uid].tapped); self.assertEqual(trace(g,'regenerated'),[('regenerated',a.uid,a.name)])
        g.destroy(a.uid); g.resolve(); self.assertNotIn(a.uid,g.permanents)              # shield spent
        g.destroy(bear); g.resolve(); self.assertNotIn(bear,g.permanents)                 # opponents' creatures unshielded
        g.advance_to('cleanup',active_player=0); g.resolve(); self.assertNotIn(b.uid,g.regen_shields)
        g.destroy(b.uid); g.resolve(); self.assertNotIn(b.uid,g.permanents)


class C82(_Base):
    CONTRACT='C82'; ISSUES=['R42']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Modeled in S15 (+CP03 deathtouch, CP10 opponent-owned return) on PhysicalZoneGame. Deathtouch is asserted '
                   'through the kernel predicate _deathtouch(), not in a combat. Opponents have no cards or graveyards (S8): '
                   'an opponent-owned body "returns" as a new declared body (same name/P/T), tapped, under its owner']
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused('Infuse with Vitality')
    def test_pzg_deathtouch_gain_two_and_return_tapped_under_owner(self):
        """CP21 PhysicalZoneGame (S15): target creature gains deathtouch and 'returns tapped under its owner's control when
        it dies this turn'; you gain 2. Own nontoken card returns linked to the same physical card; an opponent's body
        returns under that opponent."""
        g=self.pzg({1:[BEAR]}); dg=self.creature(g,'Deathgreeter'); ph=g.linked_battlefield[dg.uid]; life=g.life[0]
        uid=self.cast_physical(g,'Infuse with Vitality','B','G',target_uid=dg.uid); g.resolve()
        self.assertEqual(g.life[0],life+2); self.assertIn(dg.uid,g.infused_eot); self.assertTrue(g._deathtouch(g.permanents[dg.uid]))
        g.destroy(dg.uid); g.resolve(); back=self.own(g,'Deathgreeter')
        self.assertNotEqual(back.uid,dg.uid); self.assertTrue(back.tapped); self.assertEqual(g.linked_battlefield[back.uid],ph); self.assertEqual(g.zones.cards[ph].zone,'battlefield')
        g.zones.move(uid,'library'); bear=self.opp(g,1,'Bear'); self.cast_physical(g,'Infuse with Vitality','B','G',target_uid=bear); g.resolve(); g.destroy(bear); g.resolve()
        nb=[p for p in g.opponent_creatures(1) if p.name=='Bear']; self.assertEqual(len(nb),1); self.assertNotEqual(nb[0].uid,bear); self.assertTrue(nb[0].tapped)
    def test_pzg_infused_token_does_not_return(self):
        g=self.pzg(); p=self.pest(g); self.cast_physical(g,'Infuse with Vitality','B','G',target_uid=p.uid); g.resolve(); g.destroy(p.uid); g.resolve()
        self.assertNotIn(p.uid,g.permanents); self.assertNotIn('Infuse with Vitality return (S15)',[t[1] for t in trace(g,'resolve')])


class C83(_Base):
    CONTRACT='C83'; ISSUES=['R43']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['Modeled in S15 on PhysicalZoneGame. NOT ASSERTED: "this spell can\'t be countered" - the kernel has no '
                   'counterspell model (pab_interaction_s11.py: counterspells not modeled), so uncounterability is untestable']
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused('Abrupt Decay')
    def test_pzg_destroy_nonland_mv3_or_less_and_fizzle(self):
        """CP21 PhysicalZoneGame (S15): target nonland permanent with mana value 3 or less (boundary 3 accepted, 4 refused,
        before any mutation); destroyed on resolution; a target gone at resolution makes the spell fizzle."""
        g=self.pzg({1:[WALL,OGRE]}); wall,ogre=self.opp(g,1,'Wall'),self.opp(g,1,'Ogre'); uid=self.to_hand(g,'Abrupt Decay')
        self.physical_refused(g,uid,'B','G',target_uid=ogre)
        g.add_mana('B','G'); g.cast_from_hand(uid,target_uid=wall); g.resolve()
        self.assertNotIn(wall,g.permanents); self.assertIn(ogre,g.permanents); self.assertIn(('destroyed_by',wall,'Wall','Abrupt Decay'),g.trace)
        g.zones.move(uid,'library'); p=self.pest(g); self.cast_physical(g,'Abrupt Decay','B','G',target_uid=p.uid); g.sacrifice(p.uid); g.resolve()
        self.assertIn(('spell_fizzles_all_targets_illegal','Abrupt Decay'),g.trace); self.assertEqual(g.zones.cards[uid].zone,'graveyard')
    def test_pzg_land_is_not_a_legal_target(self):
        g=self.pzg(main=True); land=self.to_hand(g,'Swamp'); g.play_physical_land(land); g.resolve(); e=next(k for k,v in g.linked_battlefield.items() if v==land)
        self.physical_refused(g,self.to_hand(g,'Abrupt Decay'),'B','G',target_uid=e)


class C84(_Base):
    CONTRACT='C84'; ISSUES=['R43']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['Modeled in S15 on PhysicalZoneGame. NOT ASSERTED: "its controller may search for a basic land card, put it '
                   'onto the battlefield, then shuffle" - opponents have no libraries (S8); the search is only traced as unmodeled']
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused("Assassin's Trophy")
    def test_pzg_destroy_target_permanent_an_opponent_controls(self):
        """CP21 PhysicalZoneGame (S15): only a permanent an opponent controls is a legal target (own Pest refused before any
        mutation); destroyed on resolution through the S8 death path; the basic-land search is traced unmodeled."""
        g=self.pzg({1:[BEAR]}); bear=self.opp(g,1,'Bear'); p=self.pest(g); uid=self.to_hand(g,"Assassin's Trophy")
        self.physical_refused(g,uid,'B','G',target_uid=p.uid)
        g.add_mana('B','G'); g.cast_from_hand(uid,target_uid=bear); g.resolve()
        self.assertNotIn(bear,g.permanents); self.assertIn(p.uid,g.permanents); self.assertIn(('opponent_basic_land_search_unmodeled',1,"Assassin's Trophy"),g.trace)


class C85(_Base):
    CONTRACT='C85'; ISSUES=['R44']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Modeled in S15 on PhysicalZoneGame. Each opponent\'s "creature of their choice" is chosen by the S8 '
                   'stand-in policy edict_choice() (lowest power, then toughness, then uid), not by the opponent']
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused('Rise of the Witch-king')
    def test_pzg_each_player_sacrifices_a_creature(self):
        """CP21 PhysicalZoneGame (S15): you sacrifice the creature you chose (required while you control one; must be yours);
        each opponent with a creature sacrifices one; an opponent with none is traced."""
        g=self.pzg({1:[BEAR],2:[OGRE,WALL]}); a,b=self.pest(g),self.pest(g); uid=self.to_hand(g,'Rise of the Witch-king')
        self.physical_refused(g,uid,'B','G','C','C')
        self.physical_refused(g,uid,'B','G','C','C',sacrifice_uid=self.opp(g,1,'Bear'))
        g.add_mana('B','G','C','C'); g.cast_from_hand(uid,sacrifice_uid=b.uid); g.resolve()
        self.assertIn(a.uid,g.permanents); self.assertNotIn(b.uid,g.permanents)
        rise=[t for t in g.trace if t[0] in ('opponent_sacrifice','edict_no_creature') and t[-1]=='Rise of the Witch-king']
        self.assertEqual([(t[0],t[1]) for t in rise],[('opponent_sacrifice',1),('opponent_sacrifice',2),('edict_no_creature',3)])
        self.assertEqual(rise[1][3],'Wall')                                               # S8 stand-in: lowest power


class C86(_Base):
    CONTRACT='C86'; ISSUES=['R44']; STATUS='EXECUTED'
    SUBSTITUTIONS=[]
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused('Rise of the Witch-king')
    def test_pzg_if_you_sacrificed_return_another_permanent_card(self):
        """CP21 PhysicalZoneGame (S15): if you sacrificed, another permanent card from your graveyard returns to the
        battlefield; the return card must already be in the graveyard when the spell is cast (so it is never the creature
        just sacrificed); if your sacrifice did not happen, nothing returns."""
        g=self.pzg(); p=self.pest(g); card=self.to_hand(g,'Deathgreeter'); g.zones.move(card,'graveyard'); uid=self.to_hand(g,'Rise of the Witch-king')
        self.physical_refused(g,uid,'B','G','C','C',sacrifice_uid=p.uid,return_uid=self.to_hand(g,'Village Rites'))   # not in the graveyard
        g.add_mana('B','G','C','C'); g.cast_from_hand(uid,sacrifice_uid=p.uid,return_uid=card); g.resolve()
        self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.zones.cards[card].zone,'battlefield'); self.assertIn(card,g.linked_battlefield.values())
        g2=self.pzg(); q=self.pest(g2); card2=self.to_hand(g2,'Deathgreeter'); g2.zones.move(card2,'graveyard')
        self.cast_physical(g2,'Rise of the Witch-king','B','G','C','C',sacrifice_uid=q.uid,return_uid=card2); g2.sacrifice(q.uid); g2.resolve()   # sacrifice target gone
        self.assertEqual(g2.zones.cards[card2].zone,'graveyard')


class C87(_Base):
    CONTRACT='C87'; ISSUES=['R45']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Grisly Salvage: modeled in S15 on PhysicalZoneGame; this test keeps the stand-in: its resolution is '
                   'composed from physical-zone primitives in the fixture (top five by library order, chosen creature/land '
                   'to hand, rest to graveyard, no shuffle)']
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
    CONTRACT='C88'; ISSUES=['R45']; STATUS='EXECUTED'
    SUBSTITUTIONS=[]
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card (S20 models it on PhysicalZoneGame only)."""
        self.assert_card_refused('Shigeki, Jukai Visionary')
    def test_pzg_activation_reveal_four_land_tapped_rest_to_graveyard(self):
        """CP21 PhysicalZoneGame (S20): {1}{G}, {T}, return Shigeki to hand, paid on activation (one mana short refused);
        reveal the top four; a land card among them enters the battlefield tapped; the other three go to the graveyard;
        with no land among them all four do."""
        g=self.pzg(); e,ph=self.shigeki(g); top=self.stack_library(g,['Village Rites','Swamp','Abrupt Decay','Witherbloom Charm'])
        g.add_mana('G')
        with self.assertRaises(BridgeError): g.shigeki_activate(e)
        self.assertIn(e,g.permanents); g.add_mana('C'); g.shigeki_activate(e)
        self.assertEqual(g.zones.cards[ph].zone,'hand'); self.assertNotIn(e,g.permanents); self.assertEqual(g.mana_pool,[]); self.assertEqual(g.zones.zones['library'][:4],top)
        g.resolve(); land=top[1]
        self.assertEqual(g.zones.cards[land].zone,'battlefield'); self.assertTrue(g.zones.cards[land].tapped); self.assertTrue(g.permanents[next(k for k,v in g.linked_battlefield.items() if v==land)].tapped)
        self.assertEqual([g.zones.cards[u].zone for u in (top[0],top[2],top[3])],['graveyard']*3)
        g2=self.pzg(); e2,_=self.shigeki(g2); top2=self.stack_library(g2,['Village Rites','Abrupt Decay','Witherbloom Charm','Golgari Charm'])
        g2.add_mana('G','C'); g2.shigeki_activate(e2); g2.resolve()
        self.assertEqual([g2.zones.cards[u].zone for u in top2],['graveyard']*4); self.assertIsNone(trace(g2,'shigeki_reveal')[-1][1])


class C89(_Base):
    CONTRACT='C89'; ISSUES=['R45','R18']; STATUS='EXECUTED'
    SUBSTITUTIONS=[]
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused('Shigeki, Jukai Visionary')
    def test_pzg_channel_x_returns_x_cards_and_discards_shigeki(self):
        """CP21 PhysicalZoneGame (S20): Channel {X}{X}{G}{G}, discard Shigeki: return X target cards from your graveyard to
        your hand. X=2 needs six mana; five is refused before any mutation."""
        g=self.pzg(); uid=self.to_hand(g,SHIGEKI); a,b=self.to_graveyard(g,'Village Rites'),self.to_graveyard(g,'Swamp'); g.add_mana('G','G','C','C','C')
        snap=lambda:(list(g.zones.zones['hand']),list(g.zones.zones['graveyard']),list(g.mana_pool),len(g.trace)); before=snap()
        with self.assertRaises(BridgeError): g.channel_shigeki(uid,[a,b])
        self.assertEqual(snap(),before)
        g.add_mana('C'); g.channel_shigeki(uid,[a,b]); self.assertEqual(g.zones.cards[uid].zone,'graveyard'); self.assertEqual(g.mana_pool,[]); self.assertIn(('channel',SHIGEKI,uid,2),g.trace)
        g.resolve(); self.assertEqual((g.zones.cards[a].zone,g.zones.cards[b].zone),('hand','hand'))


class C90(_Base):
    CONTRACT='C90'; ISSUES=['R45']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Modeled in S20 on PhysicalZoneGame. "Nonlegendary" is checked against the hand-written name set '
                   'pab_shigeki_s20.LEGENDARY_CARDS, not a supertype read from card data (physical cards carry no type line)']
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused('Shigeki, Jukai Visionary')
    def test_pzg_channel_refuses_legendary_targets(self):
        """CP21 PhysicalZoneGame (S20): a legendary card (alone or among the targets) is refused before any mutation; the
        nonlegendary target alone is returned and the legendary card stays in the graveyard."""
        g=self.pzg(); uid=self.to_hand(g,SHIGEKI); dina=self.to_graveyard(g,'Dina, Soul Steeper'); rites=self.to_graveyard(g,'Village Rites'); g.add_mana('G','G','C','C','C','C')
        self.assertIn('Dina, Soul Steeper',LEGENDARY_CARDS); self.assertNotIn('Village Rites',LEGENDARY_CARDS)
        for targets in ([dina],[rites,dina]):
            with self.assertRaises(BridgeError): g.channel_shigeki(uid,targets)
        self.assertEqual((g.zones.cards[uid].zone,g.zones.cards[dina].zone,len(g.mana_pool)),('hand','graveyard',6))
        g.channel_shigeki(uid,[rites]); g.resolve(); self.assertEqual((g.zones.cards[rites].zone,g.zones.cards[dina].zone),('hand','graveyard'))


class C91(_Base):
    CONTRACT='C91'; ISSUES=['R46']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Modeled in S16 on PhysicalZoneGame. The "1/1 Insect creature card while not on the battlefield" static is by '
                   'name (pab_grist_s16.CREATURE_CARD_NAMES and a creature=True graveyard LKI), not by a type line: physical '
                   'cards carry no type line (frozen pab_zones.py; CP19 note n3)']
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() refuses Grist, and frozen DeckZones cards have no type line (n3)."""
        self.assert_card_refused('Grist, the Hunger Tide')
        z=DeckZones(); c=z.cards[next(u for u in z.zones['library'] if z.cards[u].name=='Grist, the Hunger Tide')]
        self.assertFalse(hasattr(c,'types'))
    def test_pzg_planeswalker_on_battlefield_creature_card_elsewhere(self):
        """CP21 PhysicalZoneGame (S16): on the battlefield a noncreature planeswalker with loyalty 3; destroyed, she is a 1/1
        creature card (MV 3) in the graveyard, and a 'return a creature card' effect (Rise of the Witch-king) brings her
        back as a planeswalker, not a 1/1; milled from the library she gets the same graveyard creature LKI."""
        self.assertIn(GRIST,CREATURE_CARD_NAMES)
        g=self.pzg(); gr,ph=self.grist(g); self.assertEqual((gr.creature,gr.artifact,gr.loyalty,gr.mana_value),(False,False,3,3))
        g.destroy(gr.uid); lki=next(q for q in g.graveyard if q.name==GRIST)
        self.assertEqual((lki.creature,lki.power,lki.toughness,lki.mana_value),(True,1,1,3)); self.assertEqual(g.zones.cards[ph].zone,'graveyard')
        p=self.pest(g); self.cast_physical(g,'Rise of the Witch-king','B','G','C','C',sacrifice_uid=p.uid,return_uid=ph); g.resolve()
        back=g.grist(); self.assertEqual((back.creature,back.loyalty),(False,3)); self.assertEqual(g.linked_battlefield[back.uid],ph); self.assertNotIn(lki,g.graveyard)
        g2=self.pzg(); top=self.stack_library(g2,[GRIST]); g2.zones.mill(1)
        self.assertEqual(g2.zones.cards[top[0]].zone,'graveyard'); lki2=next(q for q in g2.graveyard if q.name==GRIST)
        self.assertTrue(lki2.creature); self.assertEqual(g2.linked_graveyard[lki2.uid],top[0])


class C92(_Base):
    CONTRACT='C92'; ISSUES=['R46']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['Modeled in S16 on PhysicalZoneGame. NOT ASSERTED: "if an Insect card was milled this way, put a loyalty '
                   'counter on Grist and repeat" - Grist is the deck\'s only Insect card and cannot be milled while on the '
                   'battlefield, so the repeat branch is unreachable with this deck (implemented in grist_plus_one, not executed)']
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused('Grist, the Hunger Tide')
    def test_pzg_plus_one_insect_token_and_mill(self):
        """CP21 PhysicalZoneGame (S16): +1 is paid as the cost (loyalty 4 before resolution); resolution creates a 1/1
        black-green Insect creature token and mills one card; a second loyalty ability that turn is refused."""
        g=self.pzg(main=True); gr,_=self.grist(g); top=g.zones.zones['library'][0]; n=len(g.zones.zones['library'])
        g.grist_plus_one(); self.assertEqual(gr.loyalty,4); self.assertEqual(trace(g,'token_created'),[])
        g.resolve(); ins=[q for q in g.permanents.values() if q.token is not None and 'Insect' in q.subtypes]
        self.assertEqual([(q.colors,q.power,q.toughness,q.creature) for q in ins],[('BG',1,1,True)])
        self.assertEqual(len(g.zones.zones['library']),n-1); self.assertEqual(g.zones.cards[top].zone,'graveyard'); self.assertEqual(trace(g,'grist_repeat'),[])
        with self.assertRaises(BridgeError): g.grist_plus_one()
        self.assertEqual(gr.loyalty,4)


class C93(_Base):
    CONTRACT='C93'; ISSUES=['R46','R20']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['Modeled in S16 on PhysicalZoneGame. NOT ASSERTED: target bookkeeping, A-S20-10 (CP22) - the reflexive '
                   'trigger\'s target is fixed when -2 is activated (target_uid), not chosen when the reflexive trigger is put '
                   'on the stack, and it is not recorded as a locked target']
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused('Grist, the Hunger Tide')
    def test_pzg_minus_two_sacrifice_then_reflexive_destroy(self):
        """CP21 PhysicalZoneGame (S16): -2 is paid as the cost (loyalty 1 at once); on resolution you may sacrifice a
        creature; when you do, a reflexive trigger destroys target creature; without a sacrifice nothing is destroyed and
        a target is refused."""
        g=self.pzg({1:[BEAR,OGRE]}); gr,_=self.grist(g); p=self.pest(g); ogre=self.opp(g,1,'Ogre')
        g.grist_minus_two(sacrifice_uid=p.uid,target_uid=ogre); self.assertEqual(gr.loyalty,1); self.assertIn(p.uid,g.permanents)
        g.resolve(); self.assertNotIn(p.uid,g.permanents); self.assertNotIn(ogre,g.permanents)
        res=[t[1] for t in trace(g,'resolve')]; self.assertLess(res.index('Grist -2 (S16)'),res.index('Grist -2 reflexive destroy (S16)'))
        self.assertLess(g.trace.index(('sacrifice',p.uid,'ordinary Pest')),g.trace.index(('destroyed_by',ogre,'Ogre','Grist -2')))
        g2=self.pzg({1:[BEAR]}); gr2,_=self.grist(g2); bear=self.opp(g2,1,'Bear')
        with self.assertRaises(BridgeError): g2.grist_minus_two(target_uid=bear)
        self.assertEqual(gr2.loyalty,3); g2.grist_minus_two(); g2.resolve()
        self.assertIn(('grist_no_sacrifice',),g2.trace); self.assertIn(bear,g2.permanents); self.assertEqual(gr2.loyalty,1)


class C94(_Base):
    CONTRACT='C94'; ISSUES=['R41','R43']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['Modeled in S15 on PhysicalZoneGame. NOT ASSERTED: target bookkeeping, A-S20-10 (CP22) - modes 2 and 3 share '
                   'one target_uid, so the pair (2,3) cannot take two different targets, and target_player/target_opponent are '
                   'not recorded as locked targets. Mode 1 on an opponent is traced unmodeled (opponents have no libraries, S8)']
    def test_event_kernel_control_add_refused(self):
        """Event-kernel control: Game.add() still refuses the card."""
        self.assert_card_refused('Witherbloom Command')
    def test_pzg_two_distinct_modes_mill_land_and_drain(self):
        """CP21 PhysicalZoneGame (S15): exactly two distinct modes (one mode, or one mode twice, refused before mutation);
        mode 1: target player (you) mills three, then a land card from your graveyard returns to hand; mode 4: target
        opponent loses 2 life and you gain 2."""
        g=self.pzg(); swamp=self.to_graveyard(g,'Swamp'); uid=self.to_hand(g,'Witherbloom Command')
        self.physical_refused(g,uid,'B','G',modes=(1,),target_player=0); self.physical_refused(g,uid,'B','G',modes=(1,1),target_player=0)
        top=list(g.zones.zones['library'][:3]); life0,life1=g.life[0],g.life[1]
        g.add_mana('B','G'); g.cast_from_hand(uid,modes=(1,4),target_player=0,target_opponent=1); g.resolve()
        self.assertEqual(trace(g,'milled')[-1],('milled',tuple(top))); land=trace(g,'land_returned_to_hand')[-1][1]
        self.assertTrue(g.zones.cards[land].is_land); self.assertIn(land,[swamp]+top); self.assertEqual(g.zones.cards[land].zone,'hand')
        self.assertTrue(all(g.zones.cards[u].zone=='graveyard' for u in [swamp]+top if u!=land))
        self.assertEqual((g.life[0],g.life[1]),(life0+2,life1-2))
    def test_pzg_modes_destroy_mv2_noncreature_and_minus_three_minus_one(self):
        """CP21 PhysicalZoneGame (S15): mode 2 destroys a noncreature nonland permanent with MV 2 or less (a creature target
        refused); mode 3 gives target creature -3/-1 until end of turn."""
        g=self.pzg({1:[BEAR],2:[OGRE]}); ring=self.cast_physical(g,'Sol Ring','C'); g.resolve(); e=next(k for k,v in g.linked_battlefield.items() if v==ring)
        bear=self.opp(g,1,'Bear'); uid=self.to_hand(g,'Witherbloom Command')
        self.physical_refused(g,uid,'B','G',modes=(2,4),target_uid=bear,target_opponent=1)
        g.add_mana('B','G'); g.cast_from_hand(uid,modes=(2,4),target_uid=e,target_opponent=1); g.resolve()
        self.assertNotIn(e,g.permanents); self.assertEqual(g.zones.cards[ring].zone,'graveyard')
        g.zones.move(uid,'library'); ogre=self.opp(g,2,'Ogre'); self.cast_physical(g,'Witherbloom Command','B','G',modes=(3,1),target_uid=ogre,target_player=2); g.resolve()
        self.assertEqual(g.eot_pt[ogre],(-3,-1)); self.assertIn(ogre,g.permanents); self.assertIn(('opponent_mill_unmodeled',2),g.trace)

if __name__=='__main__':
    unittest.main()
