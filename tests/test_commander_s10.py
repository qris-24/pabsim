"""Stage S10: Savra from the command zone. Cast with cost and commander tax, refusals,
death -> graveyard (dies triggers) -> command zone at the next SBA check (CR 903.9a),
recast with tax, fixture add(SAVRA) path unchanged, driver run without the fixture.
"""
import sys, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST
from pab_zone_bridge import BridgeError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_commander_s10 import check_invariants_s10, run_turns_casting, COMMANDER_COST, TAX_PER_CAST, cast_commander_when_able
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
def trace(g,key): return [t for t in g.trace if t[0]==key]
def mana(g,*extra): g.add_mana('B','G','C','C',*extra)

class _B(unittest.TestCase):
    def game(self,*names):
        g=PhysicalZoneGame()
        for n in names: g.add(n)
        g.resolve(); check_invariants_s10(g); return g
    def cast(self,g):
        g.cast_commander(); check_invariants_s10(g); self.assertIn(g.commander_card().uid,g.command_stack)
        g.resolve(); check_invariants_s10(g); self.assertEqual(g.command_stack,{})
        return next(p for p in g.permanents.values() if p.name==SAVRA)
    def refused(self,g,exc=BridgeError,**kw):
        pool=list(g.mana_pool); perms=set(g.permanents); cmd=list(g.zones.zones['command']); n=len(g.trace); casts=g.commander_casts
        with self.assertRaises(exc): g.cast_commander(**kw)
        self.assertEqual((list(g.mana_pool),set(g.permanents),list(g.zones.zones['command']),len(g.trace),g.commander_casts),(pool,perms,cmd,n,casts)); check_invariants_s10(g)

class Cast(_B):
    def test_kernel_promoted_and_evidence(self):
        self.assertIn('+S10',KERNEL_VERSION); self.assertIn('S10',PROMOTED)
        ev=json.loads((ROOT/'EVIDENCE'/'S10_COMMANDER_EVIDENCE.json').read_text(encoding='utf-8'))
        self.assertEqual((ev['card']['mana_cost'],ev['card']['power'],ev['card']['toughness']),('{2}{B}{G}','2','2')); self.assertEqual(COMMANDER_COST,(1,1,2)); self.assertEqual(TAX_PER_CAST,2)
    def test_positive_cast_from_command_zone_linked_body(self):
        g=self.game('Essence Warden'); mana(g); uid=g.commander_card().uid; life=g.life[0]
        sv=self.cast(g)
        self.assertEqual(g.mana_pool,[]); self.assertEqual(g.zones.cards[uid].zone,'battlefield'); self.assertEqual(g.linked_battlefield[sv.uid],uid)
        self.assertEqual((sv.power,sv.toughness,sv.colors,sv.mana_value,sv.controller),(2,2,'BG',4,0)); self.assertEqual(g.life[0],life+1)   # Warden
        self.assertEqual(trace(g,'commander_cast'),[('commander_cast',uid,(1,1,2),0)]); self.assertEqual(g.commander_casts,1); self.assertEqual(g.zones.zones['command'],[])
    def test_refusals_not_in_command_zone_wrong_step_insufficient_mana(self):
        g=self.game(); g.add_mana('B','G','C'); self.refused(g)                                   # one short
        g=self.game(); g.add_mana('C','G','C','C'); self.refused(g)                               # no black
        g=self.game(); mana(g); g.advance_to('upkeep',active_player=0); self.refused(g)         # not a main phase
        g=self.game(); mana(g); g.advance_to('precombat_main',active_player=2); self.refused(g) # not your turn
        g=self.game(); mana(g); self.cast(g); mana(g); self.refused(g)                           # already on the battlefield
        g=self.game(); mana(g); g.cast_commander()
        with self.assertRaises(BridgeError): g.cast_commander()                                 # already on the stack
        g.resolve(); check_invariants_s10(g)
    def test_fixture_add_savra_path_unchanged(self):
        g=self.game(SAVRA); self.assertEqual(len(g.zones.zones['command']),1)                   # body without a card
        sv=next(p for p in g.permanents.values() if p.name==SAVRA); self.assertNotIn(sv.uid,g.linked_battlefield)
        g.sacrifice(sv.uid); g.resolve(); check_invariants_s10(g)
        self.assertEqual(g.commander_deaths,0); self.assertEqual([q.name for q in g.graveyard],[SAVRA]); self.assertEqual(len(g.zones.zones['command']),1)

class DeathAndReturn(_B):
    def test_dies_then_returns_to_command_zone_at_sba_with_triggers_intact(self):
        g=self.game('Blood Artist','Deathgreeter','Grave Pact'); mana(g); sv=self.cast(g); uid=g.linked_battlefield[sv.uid]; life=g.life[0]
        g.sacrifice(sv.uid); self.assertEqual(g.zones.cards[uid].zone,'graveyard'); self.assertIn(uid,g.linked_graveyard.values())
        labels=[t.label for t in g.pending]; self.assertIn('Savra black sacrifice',labels); self.assertIn('Grave Pact edict opportunity',labels); self.assertIn('Blood Artist target drain',labels)
        g.resolve(); check_invariants_s10(g)
        self.assertEqual(g.zones.cards[uid].zone,'command'); self.assertEqual(g.linked_graveyard,{}); self.assertEqual([q.name for q in g.graveyard],[])
        self.assertEqual(g.commander_deaths,1); self.assertEqual(trace(g,'commander_to_command_zone'),[('commander_to_command_zone',uid,'graveyard',sv.uid)])
        self.assertEqual(g.life[0],life-2+2+1+1)                      # Savra black paid 2, green +2, Blood Artist +1, Deathgreeter +1
        self.assertEqual(g.edict_opportunities,2)                       # Savra black + Grave Pact
        t=g.trace; self.assertLess(t.index(('commander_to_command_zone',uid,'graveyard',sv.uid)),t.index(('resolve','Savra black sacrifice')))   # SBA before triggers resolve
    def test_recast_costs_tax_and_refuses_without_it(self):
        g=self.game(); mana(g); sv=self.cast(g); g.sacrifice(sv.uid); g.resolve(); check_invariants_s10(g)
        self.assertEqual(g.commander_cost(),(1,1,4)); mana(g); self.refused(g)                 # 4 mana no longer enough
        g.add_mana('C','C'); sv2=self.cast(g); self.assertEqual(g.mana_pool,[]); self.assertEqual(g.commander_casts,2)
        self.assertEqual(trace(g,'commander_cast')[-1][2:],((1,1,4),1))
        g.sacrifice(sv2.uid); g.resolve(); self.assertEqual(g.commander_cost(),(1,1,6)); self.assertEqual(g.commander_deaths,2)
    def test_village_rites_sacrificing_savra_returns_her(self):
        g=self.game(); mana(g); sv=self.cast(g); uid=g.linked_battlefield[sv.uid]
        vr=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Village Rites'); g.zones.search_library(selected_uid=vr,destination='hand')
        g.add_mana('B'); g.cast_from_hand(vr,sacrifice_uid=sv.uid); check_invariants_s10(g); g.resolve(); check_invariants_s10(g)
        self.assertEqual(g.zones.cards[uid].zone,'command'); self.assertEqual(g.cards_drawn,2); self.assertEqual(g.commander_deaths,1)
    def test_savra_in_command_zone_is_not_a_reanimation_target(self):
        g=self.game(); mana(g); sv=self.cast(g); g.sacrifice(sv.uid); g.resolve()
        self.assertIsNone(g._grave_target(sv.uid))

class Driver(_B):
    def test_sixteen_turns_all_seeds_savra_cast_when_affordable(self):
        casts=0
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=PhysicalZoneGame(seed=seed); opening_hand(g); ledger=run_turns_casting(g,20)
                self.assertEqual([t for t,*_ in ledger],[1,5,9,13,17]); self.assertEqual(g.command_stack,{})
                n=sum(c.count(SAVRA) for *_,c in ledger); casts+=n; self.assertEqual(n,g.commander_casts); self.assertLessEqual(n,1)
                if n: self.assertEqual(len(g.zones.zones['command']),0); self.assertTrue(any(p.name==SAVRA and p.uid in g.linked_battlefield for p in g.permanents.values()))
                else: self.assertEqual(len(g.zones.zones['command']),1)
        self.assertGreater(casts,0)
    def test_policy_casts_savra_only_with_cost_plus_tax(self):
        g=PhysicalZoneGame(seed=3); opening_hand(g); g.advance_to('precombat_main',active_player=0)
        g.add_mana('B','G','C'); self.assertFalse(cast_commander_when_able(g)); g.add_mana('C'); self.assertTrue(cast_commander_when_able(g)); self.assertEqual(g.commander_casts,1)

if __name__=='__main__': unittest.main()
