"""Stage S6: casting from the physical hand (Village Rites, Deadly Dispute, Tend the
Pests, Nature's Lore, Sakura-Tribe Elder). One positive and three refusals (wrong
zone, wrong step, insufficient mana) per spell; invariants after every action; one
S5-style 8-turn run where the driver casts when able. CR refs: 601.2, 608.2n, 608.3,
117.1a, 302.1, 304.1, 307.1, 103.3.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, PEST, TREASURE
from pab_zone_bridge import BridgeError
from pab_zones import ZoneError
from pab_kernel import PhysicalZoneGame
from pab_cast_s6 import (CASTABLE, check_invariants_s6, run_turns_casting,
                         opening_hand_shuffled, cast_when_able)
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def bridge(self,*names):
        g=PhysicalZoneGame(); g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve(); check_invariants_s6(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s6(g); return uid
    def pest(self,g):
        p=g.make_tokens(PEST)[0]; g.resolve(); check_invariants_s6(g); return p
    def forest_in_library(self,g):
        return next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Forest')
    def cast(self,g,uid,**kw):
        g.cast_from_hand(uid,**kw); check_invariants_s6(g)
        self.assertIn(uid,g.stack_cards); self.assertEqual(g.zones.cards[uid].zone,'hand')
        g.resolve(); check_invariants_s6(g)
        self.assertNotIn(uid,g.stack_cards)
    def refused(self,g,uid,exc=BridgeError,**kw):
        hand=list(g.zones.zones['hand']); pool=list(g.mana_pool); perms=set(g.permanents); n=len(g.trace)
        with self.assertRaises(exc): g.cast_from_hand(uid,**kw)
        self.assertEqual((list(g.zones.zones['hand']),list(g.mana_pool),set(g.permanents),len(g.trace)),(hand,pool,perms,n))  # refusal mutates nothing
        self.assertEqual(g.stack_cards,{}); check_invariants_s6(g)

# ---------------------------------------------------------------- Village Rites
class VillageRites(_B):
    def test_positive_pays_B_sacrifices_draws_two_card_to_graveyard(self):
        g=self.bridge('Sedgemoor Witch'); uid=self.to_hand(g,'Village Rites'); p=self.pest(g); g.add_mana('B')
        self.cast(g,uid,sacrifice_uid=p.uid)
        self.assertEqual(g.mana_pool,[]); self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.cards_drawn,2)
        self.assertEqual(g.zones.cards[uid].zone,'graveyard'); self.assertEqual(len(g.zones.zones['hand']),2)
        t=g.trace; self.assertLess(t.index(('sacrifice',p.uid,'ordinary Pest')),t.index(('cast','Village Rites')))   # cost before cast event
        self.assertEqual(sum(1 for x in g.permanents.values() if x.token==PEST),1)                                   # Magecraft Pest
    def test_refuse_wrong_zone_card_in_library(self):
        g=self.bridge(); uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Village Rites'); p=self.pest(g); g.add_mana('B')
        self.refused(g,uid,exc=ZoneError,sacrifice_uid=p.uid)
    def test_refuse_wrong_step_untap_no_priority(self):
        g=self.bridge(); uid=self.to_hand(g,'Village Rites'); p=self.pest(g)
        g.advance_to('cleanup',active_player=0); g.advance_step()                  # seat 1 untap: nobody has priority
        self.assertEqual(g.clock.step,'untap'); g.add_mana('B')
        self.refused(g,uid,sacrifice_uid=p.uid)
    def test_refuse_insufficient_mana_no_black(self):
        g=self.bridge(); uid=self.to_hand(g,'Village Rites'); p=self.pest(g); g.add_mana('G','C')
        self.refused(g,uid,sacrifice_uid=p.uid)
    def test_instant_castable_on_opponents_turn_and_in_response(self):
        g=self.bridge(); uid=self.to_hand(g,'Village Rites'); p=self.pest(g)
        g.advance_to('upkeep',active_player=2); g.add_mana('B'); g.add_mana('B'); q=g.make_tokens(PEST)[0]  # token ETB leaves nothing pending; sacrifice puts triggers on the stack
        g.sacrifice(q.uid); self.assertTrue(g.pending)                                # stack not empty
        self.cast(g,uid,sacrifice_uid=p.uid); self.assertEqual(g.cards_drawn,3)              # 1 draw-step draw on turn 1 + 2
    def test_r52_frozen_engine_charges_1B_kernel_paths_charge_B(self):
        from pab_focus_engine_v07 import Game as FrozenGame
        f=FrozenGame(); q=f.add('Reassembling Skeleton'); f.add_mana('B')
        with self.assertRaises(Exception): f.cast_pab_spell('Village Rites',q.uid)    # frozen, untouched: {1}{B}
        g=self.bridge(); p=self.pest(g); g.add_mana('B'); g.cast_pab_spell('Village Rites',p.uid); g.resolve()   # R52 kernel path: {B}
        self.assertEqual(g.mana_pool,[]); uid=self.to_hand(g,'Village Rites'); r=self.pest(g); g.add_mana('B')
        self.cast(g,uid,sacrifice_uid=r.uid); self.assertEqual(g.mana_pool,[])                                     # S6 path: {B}
        self.assertEqual(CASTABLE['Village Rites']['cost'],(1,0,0))

# ---------------------------------------------------------------- Deadly Dispute
class DeadlyDispute(_B):
    def test_positive_artifact_cost_treasure_and_two_draws(self):
        g=self.bridge(); uid=self.to_hand(g,'Deadly Dispute'); t=g.make_tokens(TREASURE)[0]; g.resolve(); g.add_mana('B','C')
        self.cast(g,uid,sacrifice_uid=t.uid)
        self.assertEqual(g.cards_drawn,2); self.assertEqual(sum(1 for x in g.permanents.values() if x.token==TREASURE),1)
        self.assertEqual(g.zones.cards[uid].zone,'graveyard'); self.assertEqual(g.mana_pool,[])
    def test_refuse_wrong_zone_card_in_graveyard(self):
        g=self.bridge(); uid=self.to_hand(g,'Deadly Dispute'); g.zones.discard(uid); p=self.pest(g); g.add_mana('B','C')
        self.refused(g,uid,exc=ZoneError,sacrifice_uid=p.uid)
    def test_refuse_wrong_step_cleanup(self):
        g=self.bridge(); uid=self.to_hand(g,'Deadly Dispute'); p=self.pest(g); g.advance_to('cleanup',active_player=0); g.add_mana('B','C')
        self.refused(g,uid,sacrifice_uid=p.uid)
    def test_refuse_insufficient_mana_only_B(self):
        g=self.bridge(); uid=self.to_hand(g,'Deadly Dispute'); p=self.pest(g); g.add_mana('B')
        self.refused(g,uid,sacrifice_uid=p.uid)
    def test_refuse_noncreature_nonartifact_additional_cost(self):
        g=self.bridge('Grave Pact'); uid=self.to_hand(g,'Deadly Dispute'); gp=next(x.uid for x in g.permanents.values() if x.name=='Grave Pact'); g.add_mana('B','C')
        self.refused(g,uid,sacrifice_uid=gp)

# ---------------------------------------------------------------- Tend the Pests
class TendThePests(_B):
    def test_positive_X_equals_sacrificed_power_lki(self):
        g=self.bridge(); uid=self.to_hand(g,'Tend the Pests'); big=g.add('Mirkwood Bats',power=3); g.resolve(); g.add_mana('B','G')
        self.cast(g,uid,sacrifice_uid=big.uid)
        self.assertEqual(sum(1 for x in g.permanents.values() if x.token==PEST),3); self.assertEqual(g.zones.cards[uid].zone,'graveyard')
    def test_refuse_wrong_zone_already_on_stack_double_cast(self):
        g=self.bridge(); uid=self.to_hand(g,'Tend the Pests'); p=self.pest(g); q=self.pest(g); g.add_mana('B','G','B','G')
        g.cast_from_hand(uid,sacrifice_uid=p.uid); check_invariants_s6(g)
        with self.assertRaises(BridgeError): g.cast_from_hand(uid,sacrifice_uid=q.uid)   # same card twice
        self.assertIn(q.uid,g.permanents); self.assertEqual(g.mana_pool,['B','G']); g.resolve(); check_invariants_s6(g)
    def test_refuse_wrong_step_untap_own_turn(self):
        g=self.bridge(); uid=self.to_hand(g,'Tend the Pests'); p=self.pest(g); g.advance_to('cleanup',active_player=3); g.advance_step()
        self.assertEqual(g.clock.state()[1:],(0,'beginning','untap')); g.add_mana('B','G')
        self.refused(g,uid,sacrifice_uid=p.uid)
    def test_refuse_insufficient_mana_no_green(self):
        g=self.bridge(); uid=self.to_hand(g,'Tend the Pests'); p=self.pest(g); g.add_mana('B','B')
        self.refused(g,uid,sacrifice_uid=p.uid)
    def test_refuse_artifact_additional_cost(self):
        g=self.bridge(); uid=self.to_hand(g,'Tend the Pests'); t=g.make_tokens(TREASURE)[0]; g.resolve(); g.add_mana('B','G')
        self.refused(g,uid,sacrifice_uid=t.uid)

# ---------------------------------------------------------------- Nature's Lore
class NaturesLore(_B):
    def test_positive_forest_untapped_card_to_graveyard(self):
        g=self.bridge('Sedgemoor Witch'); uid=self.to_hand(g,"Nature's Lore"); f=self.forest_in_library(g); g.add_mana('G','B')
        self.cast(g,uid,selected_land_uid=f)
        self.assertEqual(g.zones.cards[f].zone,'battlefield'); self.assertFalse(g.zones.cards[f].tapped); self.assertIn(f,g.linked_battlefield.values())
        self.assertEqual(g.zones.cards[uid].zone,'graveyard'); self.assertTrue(trace(g,'physical_library_search_shuffled'))
        self.assertEqual(sum(1 for x in g.permanents.values() if x.token==PEST),1)     # Magecraft
    def test_refuse_wrong_zone_card_on_battlefield_name_check(self):
        g=self.bridge(); uid=self.to_hand(g,"Nature's Lore"); g.zones.move(uid,'exile'); g.add_mana('G','B')
        self.refused(g,uid,exc=ZoneError,selected_land_uid=self.forest_in_library(g))
    def test_refuse_wrong_step_sorcery_in_upkeep_and_on_opponents_main(self):
        g=self.bridge(); uid=self.to_hand(g,"Nature's Lore"); f=self.forest_in_library(g)
        g.advance_to('upkeep',active_player=0); g.add_mana('G','B'); self.refused(g,uid,selected_land_uid=f)
        g.advance_to('precombat_main',active_player=1); g.add_mana('G','B'); self.refused(g,uid,selected_land_uid=f)
        g.advance_to('precombat_main',active_player=0); g.add_mana('G','B'); self.cast(g,uid,selected_land_uid=f)
    def test_refuse_sorcery_with_nonempty_stack(self):
        g=self.bridge(); uid=self.to_hand(g,"Nature's Lore"); f=self.forest_in_library(g); p=self.pest(g)
        g.advance_to('precombat_main',active_player=0); g.add_mana('G','B'); g.sacrifice(p.uid); self.assertTrue(g.pending)
        self.refused(g,uid,selected_land_uid=f); g.resolve(); self.cast(g,uid,selected_land_uid=f)
    def test_refuse_insufficient_mana_one_green_only(self):
        g=self.bridge(); uid=self.to_hand(g,"Nature's Lore"); g.add_mana('G')
        self.refused(g,uid,selected_land_uid=self.forest_in_library(g))

# ---------------------------------------------------------------- Sakura-Tribe Elder
class SakuraTribeElder(_B):
    def test_positive_enters_linked_then_existing_sacrifice_path_works(self):
        g=self.bridge('Sedgemoor Witch'); uid=self.to_hand(g,'Sakura-Tribe Elder'); g.add_mana('G','B')
        self.cast(g,uid)
        self.assertEqual(g.zones.cards[uid].zone,'battlefield'); ev=next(k for k,v in g.linked_battlefield.items() if v==uid)
        p=g.permanents[ev]; self.assertEqual((p.name,p.colors,p.power,p.toughness,p.mana_value),('Sakura-Tribe Elder','G',1,1,2))
        self.assertEqual(sum(1 for x in g.permanents.values() if x.token==PEST),0)     # creature spell: no Magecraft
        swamp=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Swamp')
        g.sakura_tribe_elder_physical(ev,selected_land_uid=swamp); g.resolve(); check_invariants_s6(g)
        self.assertEqual(g.zones.cards[uid].zone,'graveyard'); self.assertEqual(g.zones.cards[swamp].zone,'battlefield'); self.assertTrue(g.zones.cards[swamp].tapped)
        self.assertTrue(trace(g,'savra_green_gain') or any('Savra green' in x[1] for x in trace(g,'resolve')))   # Savra saw its own sacrifice
    def test_refuse_wrong_zone_card_in_library(self):
        g=self.bridge(); uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Sakura-Tribe Elder'); g.add_mana('G','B')
        self.refused(g,uid,exc=ZoneError)
    def test_refuse_wrong_step_combat(self):
        g=self.bridge(); uid=self.to_hand(g,'Sakura-Tribe Elder'); g.advance_to('declare_attackers',active_player=0); g.add_mana('G','B')
        self.refused(g,uid)
    def test_refuse_insufficient_mana_colorless_only(self):
        g=self.bridge(); uid=self.to_hand(g,'Sakura-Tribe Elder'); g.add_mana('C','C')
        self.refused(g,uid)

# ---------------------------------------------------------------- fail closed / integrity
class FailClosed(_B):
    def test_every_other_hand_card_is_refused_without_mutation(self):
        from pab_cast_s7 import S7_NAMES                        # S7 (2026-10-18) widened the castable set; everything else still fails closed
        from pab_cast_s12 import S12_NAMES                      # S12 widened it again
        from pab_cast_s13 import S13_NAMES                      # S13 widened it again
        from pab_cast_s15 import S15_NAMES                      # S15 widened it again
        g=self.bridge(); g.add_mana('B','G','C','C','C')
        for u in list(g.zones.zones['library']):
            if g.zones.cards[u].name in CASTABLE or g.zones.cards[u].name in S7_NAMES or g.zones.cards[u].name in S12_NAMES or g.zones.cards[u].name in S13_NAMES or g.zones.cards[u].name in S15_NAMES: continue
            g.zones.search_library(selected_uid=u,destination='hand'); self.refused(g,u); g.zones.move(u,'library')
        self.assertEqual(trace(g,'cast'),[])
    def test_kw_timing_refused_once_clock_engaged(self):
        g=self.bridge(); uid=self.to_hand(g,'Sakura-Tribe Elder'); g.advance_to('precombat_main',active_player=0); g.add_mana('G','B')
        self.refused(g,uid,main_phase=True)
    def test_token_and_lesson_names_not_castable(self):
        g=self.bridge(); pest=g.make_tokens(PEST)[0]; g.resolve(); g.add_mana('B','G')
        with self.assertRaises(BridgeError): g.cast_from_hand(g.linked_tokens[pest.uid])
        lesson=g.zones.zones['outside_game'][0]
        with self.assertRaises(BridgeError): g.cast_from_hand(lesson)
    def test_frozen_fixture_paths_unchanged_under_s6_kernel(self):
        g=self.bridge(); p=self.pest(g); g.add_mana('B','C'); g.cast_pab_spell('Deadly Dispute',p.uid); g.resolve()
        self.assertEqual(g.cards_drawn,2); self.assertEqual(g.stack_cards,{})

# ---------------------------------------------------------------- integrated turn loop
class CastingTurnLoop(_B):
    def game(self,seed):
        g=PhysicalZoneGame(seed=seed); g.add(SAVRA); g.resolve(); return g
    def test_eight_turns_all_seeds_invariants_and_every_cast_accounted(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=self.game(seed); opening_hand_shuffled(g); ledger=run_turns_casting(g,8)
                self.assertEqual([t for t,_,_,_ in ledger],[1,5]); self.assertEqual(g.stack_cards,{}); self.assertEqual(g.mana_pool,[])
                casts=trace(g,'physical_cast'); self.assertEqual(len(casts),sum(len(c) for *_,c in ledger))
                for _,name,uid,cost,_ in casts:
                    self.assertEqual(g.zones.cards[uid].zone,'battlefield' if name=='Sakura-Tribe Elder' else 'graveyard')
                    self.assertEqual(cost,CASTABLE[name]['cost'])
                z=g.zones; self.assertEqual(sum(len(z.zones[k]) for k in ('library','hand','battlefield','graveyard')),99+sum(1 for c in z.cards.values() if c.token))
    def test_seed_7_driver_casts_natures_lore_turn_5(self):
        g=self.game(7); opening_hand_shuffled(g); ledger=run_turns_casting(g,8)
        self.assertEqual(ledger[1][3],("Nature's Lore",)); self.assertEqual(ledger[1][1],'Forest')
        lands=[g.zones.cards[u].name for u in g.zones.zones['battlefield'] if g.zones.cards[u].is_land]
        self.assertEqual(sorted(lands),['Forest','Forest','Swamp'])                   # Swamp T1, Forest T5, Forest fetched
        self.assertEqual(len(g.linked_battlefield),3)
    def test_r53_fixed_opening_hand_and_shuffled_alias_are_the_same_procedure(self):
        a=self.game(11); opening_hand(a); b=self.game(11); opening_hand_shuffled(b)
        self.assertEqual(a.zones.zones['hand'],b.zones.zones['hand']); self.assertEqual(a.zones.zones['library'],b.zones.zones['library'])
        hands={tuple(self.game(s).zones.zones['library'][:7]) for s in SEEDS}; self.assertEqual(len(hands),1)   # unshuffled order is seed-independent
        drawn=set()
        for s in SEEDS:
            g=self.game(s); opening_hand(g); drawn.add(tuple(g.zones.zones['hand']))
        self.assertGreater(len(drawn),1); check_invariants_s6(g)
    def test_driver_casts_sacrifice_spell_when_fodder_and_mana_exist(self):
        g=self.game(0); opening_hand_shuffled(g); g.advance_to('precombat_main',active_player=0)
        uid=self.to_hand(g,'Village Rites'); self.pest(g); g.add_mana('B')
        self.assertEqual(cast_when_able(g),['Village Rites']); self.assertEqual(g.zones.cards[uid].zone,'graveyard'); check_invariants_s6(g)

if __name__=='__main__': unittest.main()
