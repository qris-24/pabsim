"""Stage S7: creature spells from the physical hand (27 new names + Sakura-Tribe Elder
unchanged on the S6 path). Per card: one positive cast and one refusal test covering
wrong zone, wrong step and insufficient mana; invariants after every action. Plus:
cost/P/T/colour cross-check against EVIDENCE/S7_CARD_EVIDENCE.json, frozen-kernel ETB
behaviour reached through the cast path, devour (CR 702.82), no Magecraft for creatures,
and an 8-seed 8-turn driver run. CR refs: 601.2, 608.3, 702.82, 117.1a, 302.1, 307.1.
"""
import sys, re, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST, MOSEO_PEST, TREASURE, SQUIRREL
from pab_zone_bridge import BridgeError
from pab_zones import ZoneError
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_cast_s6 import CASTABLE as CASTABLE_S6
from pab_cast_s7 import CREATURES, S7_NAMES, CASTABLE, check_invariants_s6, run_turns_casting, cast_when_able
from pab_turn_loop import opening_hand

SEEDS=(0,1,2,3,4,7,11,42)
def trace(g,key): return [t for t in g.trace if t[0]==key]
def mana_for(spec):
    b,gr,gen=spec['cost']; return ['B']*b+['G']*gr+['C']*gen

class _B(unittest.TestCase):
    def bridge(self,*names):
        g=PhysicalZoneGame(); g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve(); check_invariants_s6(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s6(g); return uid
    def in_library(self,g,name): return next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
    def pest(self,g):
        p=g.make_tokens(PEST)[0]; g.resolve(); check_invariants_s6(g); return p
    def cast(self,g,uid,**kw):
        g.cast_from_hand(uid,**kw); check_invariants_s6(g)
        self.assertIn(uid,g.stack_cards); self.assertEqual(g.zones.cards[uid].zone,'hand')
        g.resolve(); check_invariants_s6(g); self.assertNotIn(uid,g.stack_cards)
    def refused(self,g,uid,exc=BridgeError,**kw):
        hand=list(g.zones.zones['hand']); pool=list(g.mana_pool); perms=set(g.permanents); n=len(g.trace)
        with self.assertRaises(exc): g.cast_from_hand(uid,**kw)
        self.assertEqual((list(g.zones.zones['hand']),list(g.mana_pool),set(g.permanents),len(g.trace)),(hand,pool,perms,n))
        self.assertEqual(g.stack_cards,{}); check_invariants_s6(g)
    # ---- the two per-card checks ----
    def positive(self,name):
        spec=CREATURES[name]; g=self.bridge(); uid=self.to_hand(g,name); hand=len(g.zones.zones['hand'])
        g.add_mana(*mana_for(spec)); self.cast(g,uid)
        self.assertEqual(g.mana_pool,[]); self.assertEqual(g.zones.cards[uid].zone,'battlefield'); self.assertEqual(len(g.zones.zones['hand']),hand-1)
        ev=next(e for e,ph in g.linked_battlefield.items() if ph==uid); p=g.permanents[ev]
        self.assertEqual((p.name,p.power,p.toughness,p.colors,p.mana_value,p.creature,p.controller),
                         (name,spec['power'],spec['toughness'],spec['colors'],spec['mana_value'],True,0))
        t=g.trace; i=lambda key:next(k for k,x in enumerate(t) if x[0]==key and (len(x)<2 or x[1]==name or key=='mana_paid'))
        self.assertLess(i('cast_begin'),i('mana_paid')); self.assertLess(i('mana_paid'),i('cast')); self.assertLess(i('cast'),i('physical_cast'))
        self.assertEqual(trace(g,'physical_cast')[-1],('physical_cast',name,uid,spec['cost'],None))
        self.assertEqual(trace(g,'physical_creature_spell_resolved')[-1],('physical_creature_spell_resolved',name,uid,ev))
        return g
    def refusals(self,name):
        spec=CREATURES[name]; full=mana_for(spec)
        g=self.bridge(); uid=self.in_library(g,name); g.add_mana(*full); self.refused(g,uid,exc=ZoneError)   # wrong zone: library
        g=self.bridge(); uid=self.to_hand(g,name); g.advance_to('upkeep',active_player=0); g.add_mana(*full); self.refused(g,uid)   # wrong step: own upkeep
        g=self.bridge(); uid=self.to_hand(g,name); g.add_mana(*full[:-1]); self.refused(g,uid)             # one symbol short
        if 'B' in full or 'G' in full:                                                                       # colour short: a pip paid with {C}
            short=list(full); short[short.index('B' if 'B' in short else 'G')]='C'
            g=self.bridge(); uid=self.to_hand(g,name); g.add_mana(*short); self.refused(g,uid)

class Dina(_B):
    def test_positive(self): self.positive('Dina, Soul Steeper')
    def test_refusals(self): self.refusals('Dina, Soul Steeper')
class MirkwoodBats(_B):
    def test_positive(self): self.positive('Mirkwood Bats')
    def test_refusals(self): self.refusals('Mirkwood Bats')
class PestRescuer(_B):
    def test_positive(self): self.positive('Pest Rescuer')
    def test_refusals(self): self.refusals('Pest Rescuer')
class Chatterfang(_B):
    def test_positive(self): self.positive('Chatterfang, Squirrel General')
    def test_refusals(self): self.refusals('Chatterfang, Squirrel General')
class Moseo(_B):
    def test_positive(self): self.positive("Moseo, Vein's New Dean")
    def test_refusals(self): self.refusals("Moseo, Vein's New Dean")
class ReassemblingSkeleton(_B):
    def test_positive(self): self.positive('Reassembling Skeleton')
    def test_refusals(self): self.refusals('Reassembling Skeleton')
class TeachersPest(_B):
    def test_positive(self): self.positive("Teacher's Pest")
    def test_refusals(self): self.refusals("Teacher's Pest")
class InfestationSage(_B):
    def test_positive(self): self.positive('Infestation Sage')
    def test_refusals(self): self.refusals('Infestation Sage')
class WrigglingGrub(_B):
    def test_positive(self): self.positive('Wriggling Grub')
    def test_refusals(self): self.refusals('Wriggling Grub')
class SedgemoorWitch(_B):
    def test_positive(self): self.positive('Sedgemoor Witch')
    def test_refusals(self): self.refusals('Sedgemoor Witch')
class Beledros(_B):
    def test_positive(self): self.positive('Beledros Witherbloom')
    def test_refusals(self): self.refusals('Beledros Witherbloom')
class RibtrussRoaster(_B):
    def test_positive(self): self.positive('Ribtruss Roaster')
    def test_refusals(self): self.refusals('Ribtruss Roaster')
class SouthWindAvatar(_B):
    def test_positive(self): self.positive('South Wind Avatar')
    def test_refusals(self): self.refusals('South Wind Avatar')
class Deathgreeter(_B):
    def test_positive(self): self.positive('Deathgreeter')
    def test_refusals(self): self.refusals('Deathgreeter')
class BloodArtist(_B):
    def test_positive(self): self.positive('Blood Artist')
    def test_refusals(self): self.refusals('Blood Artist')
class PoisonTipArcher(_B):
    def test_positive(self): self.positive('Poison-Tip Archer')
    def test_refusals(self): self.refusals('Poison-Tip Archer')
class MaraudingBlightPriest(_B):
    def test_positive(self): self.positive('Marauding Blight-Priest')
    def test_refusals(self): self.refusals('Marauding Blight-Priest')
class StarscapeCleric(_B):
    def test_positive(self): self.positive('Starscape Cleric')
    def test_refusals(self): self.refusals('Starscape Cleric')
class ProsperousInnkeeper(_B):
    def test_positive(self): self.positive('Prosperous Innkeeper')
    def test_refusals(self): self.refusals('Prosperous Innkeeper')
class EssenceWarden(_B):
    def test_positive(self): self.positive('Essence Warden')
    def test_refusals(self): self.refusals('Essence Warden')
class WarrenSoultrader(_B):
    def test_positive(self): self.positive('Warren Soultrader')
    def test_refusals(self): self.refusals('Warren Soultrader')
class CarrionFeeder(_B):
    def test_positive(self): self.positive('Carrion Feeder')
    def test_refusals(self): self.refusals('Carrion Feeder')
class VisceraSeer(_B):
    def test_positive(self): self.positive('Viscera Seer')
    def test_refusals(self): self.refusals('Viscera Seer')
class BogwaterLumaret(_B):
    def test_positive(self): self.positive('Bogwater Lumaret')
    def test_refusals(self): self.refusals('Bogwater Lumaret')
class Sangromancer(_B):
    def test_positive(self): self.positive('Sangromancer')
    def test_refusals(self): self.refusals('Sangromancer')
class Yawgmoth(_B):
    def test_positive(self): self.positive('Yawgmoth, Thran Physician')
    def test_refusals(self): self.refusals('Yawgmoth, Thran Physician')
class Yahenni(_B):
    def test_positive(self): self.positive('Yahenni, Undying Partisan')
    def test_refusals(self): self.refusals('Yahenni, Undying Partisan')

# ---------------------------------------------------------------- scope and evidence
class ScopeAndEvidence(_B):
    def test_kernel_promoted_s7_and_name_sets(self):
        self.assertIn('+S7',KERNEL_VERSION); self.assertIn('S7',PROMOTED)
        self.assertEqual(len(CREATURES),28); self.assertEqual(len(S7_NAMES),27); self.assertNotIn('Sakura-Tribe Elder',S7_NAMES)
        self.assertEqual(set(CASTABLE),set(CASTABLE_S6)|S7_NAMES); self.assertNotIn(SAVRA,CASTABLE)
    def test_table_matches_card_evidence_symbol_by_symbol(self):
        ev=json.loads((ROOT/'EVIDENCE'/'S7_CARD_EVIDENCE.json').read_text(encoding='utf-8'))['cards']
        self.assertEqual(set(ev),set(CREATURES))
        for name,c in ev.items():
            syms=re.findall(r'\{([^}]+)\}',c['mana_cost']); self.assertTrue(all(s in ('B','G') or s.isdigit() for s in syms),name)   # no hybrid/X/Phyrexian
            cost=(syms.count('B'),syms.count('G'),sum(int(s) for s in syms if s.isdigit()))
            spec=CREATURES[name]
            self.assertEqual((cost,int(c['power']),int(c['toughness']),c['colors'],int(c['cmc'])),
                             (spec['cost'],spec['power'],spec['toughness'],spec['colors'],spec['mana_value']),name)
            self.assertTrue(c['type_line'].startswith(('Creature','Legendary Creature')),name)
        self.assertEqual(CREATURES['Ribtruss Roaster']['devour'],1); self.assertIn('Devour 1',ev['Ribtruss Roaster']['oracle_text'])
        self.assertTrue(all(CREATURES[n]['devour']==0 for n in CREATURES if n!='Ribtruss Roaster'))
    def test_elder_still_cast_by_the_s6_procedure(self):
        g=self.bridge(); uid=self.to_hand(g,'Sakura-Tribe Elder'); g.add_mana('G','C'); self.cast(g,uid)
        self.assertEqual(g.zones.cards[uid].zone,'battlefield'); self.assertEqual(CREATURES['Sakura-Tribe Elder']['cost'],CASTABLE_S6['Sakura-Tribe Elder']['cost'])
        self.assertEqual(trace(g,'physical_creature_spell_resolved')[-1][1],'Sakura-Tribe Elder')
    def test_savra_lands_and_lesson_still_fail_closed(self):
        g=self.bridge(); g.add_mana('B','G','C','C')
        for name in ('Forest','Swamp','Demonic Tutor','Abrupt Decay'):     # S12: Grave Pact and Sol Ring are castable now
            uid=self.to_hand(g,name); self.refused(g,uid)
        self.assertEqual(g.zones.cards[g.zones.zones['command'][0]].name,SAVRA); self.refused(g,g.zones.zones['command'][0],exc=(BridgeError,ZoneError))
        self.refused(g,g.zones.zones['outside_game'][0])
    def test_refuse_sacrifice_land_selection_and_devour_on_wrong_names(self):
        g=self.bridge(); uid=self.to_hand(g,'Deathgreeter'); p=self.pest(g); g.add_mana('B'); forest=self.in_library(g,'Forest')
        self.refused(g,uid,sacrifice_uid=p.uid); self.refused(g,uid,selected_land_uid=forest); self.refused(g,uid,devour_uids=[p.uid])
        vr=self.to_hand(g,'Village Rites'); self.refused(g,vr,sacrifice_uid=p.uid,devour_uids=[p.uid])   # S6 name never sees devour_uids

# ---------------------------------------------------------------- frozen-kernel ETB behaviour through the cast path
class EntersTheBattlefield(_B):
    def test_moseo_cast_creates_attack_gain_pest(self):
        g=self.positive("Moseo, Vein's New Dean")
        self.assertEqual(sum(1 for p in g.permanents.values() if p.token==MOSEO_PEST),1)
    def test_innkeeper_cast_creates_treasure_then_gains_for_the_next_creature(self):
        g=self.positive('Prosperous Innkeeper'); self.assertEqual(sum(1 for p in g.permanents.values() if p.token==TREASURE),1); life=g.life[0]
        uid=self.to_hand(g,'Deathgreeter'); g.add_mana('B'); self.cast(g,uid); self.assertEqual(g.life[0],life+1)
    def test_warden_and_lumaret_gain_when_a_cast_creature_enters(self):
        g=self.bridge('Essence Warden'); life=g.life[0]
        uid=self.to_hand(g,'Bogwater Lumaret'); g.add_mana('B','G'); self.cast(g,uid)           # Warden +1; Lumaret sees itself enter +1
        self.assertEqual(g.life[0],life+2)
        uid=self.to_hand(g,'Carrion Feeder'); g.add_mana('B'); self.cast(g,uid); self.assertEqual(g.life[0],life+4)   # Warden +1, Lumaret +1
    def test_chatterfang_and_bats_apply_to_moseos_token(self):
        g=self.bridge('Chatterfang, Squirrel General','Mirkwood Bats'); opp=list(g.life[1:])
        uid=self.to_hand(g,"Moseo, Vein's New Dean"); g.add_mana('B','C','C'); self.cast(g,uid)
        kinds=[p.token for p in g.permanents.values() if p.token]; self.assertEqual((kinds.count(MOSEO_PEST),kinds.count(SQUIRREL)),(1,1))
        self.assertEqual(g.life[1:],[x-2 for x in opp])                                          # Bats: two tokens created
    def test_creature_cast_does_not_trigger_magecraft(self):
        g=self.bridge('Sedgemoor Witch'); uid=self.to_hand(g,'Deathgreeter'); g.add_mana('B'); self.cast(g,uid)
        self.assertEqual(sum(1 for p in g.permanents.values() if p.token==PEST),0)
        vr=self.to_hand(g,'Village Rites'); p=self.pest(g); g.add_mana('B'); self.cast(g,vr,sacrifice_uid=p.uid)
        self.assertEqual(sum(1 for p in g.permanents.values() if p.token==PEST),1)             # instant: Magecraft Pest

# ---------------------------------------------------------------- devour (CR 702.82)
class Devour(_B):
    def roaster(self,g,*uids):
        uid=self.to_hand(g,'Ribtruss Roaster'); g.add_mana('G','C','C','C','C'); return uid
    def test_devour_two_pests_sacrificed_before_entry_two_counters_savra_triggers(self):
        g=self.bridge(); a=self.pest(g); b=self.pest(g); uid=self.roaster(g); life=g.life[0]
        self.cast(g,uid,devour_uids=[a.uid,b.uid])
        r=next(p for p in g.permanents.values() if p.name=='Ribtruss Roaster'); self.assertEqual(r.counters,2)
        self.assertNotIn(a.uid,g.permanents); self.assertNotIn(b.uid,g.permanents)
        t=g.trace; self.assertLess(t.index(('sacrifice',b.uid,'ordinary Pest')),t.index(('enter',r.uid,'Ribtruss Roaster')))
        self.assertEqual(trace(g,'devour')[-1],('devour','Ribtruss Roaster',(a.uid,b.uid)))
        self.assertEqual(g.life[0],life+2)                   # each Pest: dies +1, Savra black -2, Savra green +2
        self.assertEqual(g.edict_opportunities,2)
    def test_devour_zero_is_the_default_legal_choice(self):
        g=self.bridge(); self.pest(g); uid=self.roaster(g); self.cast(g,uid)
        r=next(p for p in g.permanents.values() if p.name=='Ribtruss Roaster'); self.assertEqual(r.counters,0)
        self.assertEqual(sum(1 for p in g.permanents.values() if p.token==PEST),1); self.assertEqual(trace(g,'devour'),[])
    def test_devour_choice_that_left_before_resolution_is_dropped_not_refused(self):
        g=self.bridge(); a=self.pest(g); b=self.pest(g); uid=self.roaster(g)
        g.cast_from_hand(uid,devour_uids=[a.uid,b.uid]); check_invariants_s6(g)
        g.sacrifice(a.uid); check_invariants_s6(g)            # a leaves in response
        g.resolve(); check_invariants_s6(g)
        r=next(p for p in g.permanents.values() if p.name=='Ribtruss Roaster'); self.assertEqual(r.counters,1)
        self.assertEqual(trace(g,'devour_choice_gone'),[('devour_choice_gone','Ribtruss Roaster',a.uid)]); self.assertEqual(trace(g,'devour')[-1][2],(b.uid,))
    def test_devour_refusals_uncontrolled_duplicate_noncreature(self):
        g=self.bridge(); a=self.pest(g); uid=self.roaster(g); tr=g.make_tokens(TREASURE)[0]; g.resolve()
        self.refused(g,uid,devour_uids=[a.uid,a.uid]); self.refused(g,uid,devour_uids=[tr.uid]); self.refused(g,uid,devour_uids=[999])
        q=g.make_tokens(PEST,controller=1)[0]; g.resolve(); self.refused(g,uid,devour_uids=[q.uid])

# ---------------------------------------------------------------- integrated turn loop
class CastingTurnLoop(_B):
    def game(self,seed):
        g=PhysicalZoneGame(seed=seed); g.add(SAVRA); g.resolve(); return g
    def test_eight_turns_all_seeds_invariants_and_every_cast_accounted(self):
        total=0
        for seed in SEEDS:
            with self.subTest(seed=seed):
                g=self.game(seed); opening_hand(g); ledger=run_turns_casting(g,8)
                self.assertEqual([t for t,_,_,_ in ledger],[1,5]); self.assertEqual(g.stack_cards,{}); self.assertEqual(g.mana_pool,[])
                casts=trace(g,'physical_cast'); self.assertEqual(len(casts),sum(len(c) for *_,c in ledger)); total+=len(casts)
                for _,name,uid,cost,_ in casts:
                    self.assertEqual(cost,CASTABLE[name]['cost'])
                    self.assertEqual(g.zones.cards[uid].zone,'battlefield' if CASTABLE[name]['kind']=='creature' else 'graveyard')
                    if CASTABLE[name]['kind']=='creature': self.assertIn(uid,g.linked_battlefield.values())
                z=g.zones; self.assertEqual(sum(len(z.zones[k]) for k in ('library','hand','battlefield','graveyard')),99+sum(1 for c in z.cards.values() if c.token))
        self.assertGreater(total,0)
    def test_pinned_seed_7_casts_deathgreeter_turn_1_and_dina_turn_5(self):
        g=self.game(7); opening_hand(g); ledger=run_turns_casting(g,8)
        self.assertEqual([(t,l,c) for t,l,_,c in ledger],[(1,'Swamp',('Deathgreeter',)),(5,'Forest',('Dina, Soul Steeper',))])
    def test_driver_casts_creature_in_main_phase_when_mana_exists(self):
        g=self.game(0); opening_hand(g); g.advance_to('precombat_main',active_player=0)
        uid=self.to_hand(g,'Blood Artist'); g.add_mana('B','C')
        self.assertEqual(cast_when_able(g),['Blood Artist']); self.assertEqual(g.zones.cards[uid].zone,'battlefield'); check_invariants_s6(g)

if __name__=='__main__': unittest.main()
