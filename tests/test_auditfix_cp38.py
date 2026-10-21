"""CP38 (A2 Kernel 2; review items K2, K5, K8, K11, K13 in EVIDENCE/CP31d_INTEGRITY_REVIEW.md): interaction and policy.

K2   the scripted board wipe destroys: a creature with a regeneration shield is regenerated instead (CR 701.15a);
     indestructible creatures still survive; the wipe is still one event.
K5   with exile_instead, the S18 "Savra on the battlefield" removal exiles Savra (policy-only action exile_commander;
     the scripted KINDS stay six), not the controller's best other creature.
K8   Shigeki, Jukai Visionary (legendary enchantment creature) is in the creature-card and legend tables: Takenuma's
     cost reduction and return (which now also returns Grist, a planeswalker card), Grisly Salvage, Rise of the
     Witch-king's return, Grist -5's count and the S13 tutor policy.
K11  the scripted edict and the removal target policy read current power (counters, Skullclamp), so the creature
     S18's reason names is the one removed.
K13  returning Shigeki to hand with its own ability unattaches Skullclamp.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, PEST
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_opponents_s8 import OPPONENT_SEATS
import pab_interaction_s11 as s11
import pab_cast_s13 as s13
from pab_grist_s16 import GRIST

SH='Shigeki, Jukai Visionary'
BEAR={'name':'Bear','power':2,'toughness':2,'mana_value':2}
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,policies=None,board=True):
        g=PhysicalZoneGame(); g.resolve()
        for s in OPPONENT_SEATS:
            if board: g.declare_opponent_board(s,[BEAR])
            if policies and s in policies: g.set_opponent_policy(s,policies[s])
        g.advance_to('precombat_main',active_player=0); return g
    def savra(self,g):
        g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve(); return self.named(g,SAVRA)
    def named(self,g,name): return next(p for p in g.permanents.values() if p.name==name)
    def to_hand(self,g,name):
        u=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=u,destination='hand'); return u
    def cast(self,g,name,*mana,**kw):
        u=self.to_hand(g,name); g.add_mana(*mana); g.cast_from_hand(u,**kw); g.resolve(); return u
    def creature(self,g,name,*mana): self.cast(g,name,*mana); return self.named(g,name)
    def clamp(self,g,target):
        if not any(p.name=='Skullclamp' for p in g.permanents.values()): self.cast(g,'Skullclamp','C')
        c=self.named(g,'Skullclamp'); g.add_mana('C'); g.equip_skullclamp(c.uid,target.uid); g.resolve(); return c

class Version(_B):
    def test_kernel_promoted_and_scripted_kinds_unchanged(self):
        self.assertIn('CP38',PROMOTED); self.assertIn('+CP38',KERNEL_VERSION)
        self.assertEqual(len(s11.KINDS),6); self.assertEqual(s11.POLICY_ONLY_KINDS,('exile_commander',))

class BoardWipe(_B):
    def test_wipe_regenerates_shielded_creatures(self):
        g=self.game({2:{'wipe_at':1}}); sv=self.savra(g); w=self.creature(g,'Sedgemoor Witch','B','C','C'); pe=g.make_tokens(PEST)[0]; g.resolve()
        d=self.creature(g,'Deathgreeter','B')
        g.advance_to('upkeep',active_player=2); g.regen_shields.update({sv.uid,w.uid,pe.uid})
        g.advance_to('precombat_main',active_player=2); g.resolve()
        for p in (sv,w,pe):
            self.assertIn(p.uid,g.permanents); self.assertTrue(p.tapped); self.assertNotIn(p.uid,g.regen_shields)
        self.assertTrue(g.zones.cards[g.linked_battlefield[w.uid]].tapped); self.assertTrue(g.zones.cards[g.linked_tokens[pe.uid]].tapped)
        self.assertNotIn(d.uid,g.permanents); self.assertEqual(g.opponent_creatures(1),[])
        wipe=trace(g,'board_wipe')[-1][2]; self.assertIn(d.uid,wipe); self.assertNotIn(w.uid,wipe)
        self.assertEqual(sorted(t[1] for t in trace(g,'regenerated')),sorted([sv.uid,w.uid,pe.uid])); g.assert_bridge_integrity()
    def test_wipe_regenerates_a_shielded_opponent_creature(self):
        g=self.game({2:{'wipe_at':0}}); bear=g.opponent_creatures(1)[0]
        g.advance_to('upkeep',active_player=2); g.regen_shields.add(bear.uid); g.advance_to('precombat_main',active_player=2); g.resolve()
        self.assertIn(bear.uid,g.permanents); self.assertTrue(bear.tapped); self.assertEqual(g.opponent_creatures(3),[])
    def test_indestructible_keeps_its_shield_and_survives(self):
        g=self.game({2:{'wipe_at':1}}); w=self.creature(g,'Sedgemoor Witch','B','C','C')
        g.advance_to('upkeep',active_player=2); g.regen_shields.add(w.uid); g.indestructible_until_eot.add(w.uid)
        g.advance_to('precombat_main',active_player=2); g.resolve()
        self.assertIn(w.uid,g.permanents); self.assertFalse(w.tapped); self.assertIn(w.uid,g.regen_shields); self.assertEqual(trace(g,'regenerated'),[])

class ExileCommander(_B):
    def test_exile_instead_exiles_savra_not_another_creature(self):
        g=self.game({1:{'removal_budget':1,'exile_instead':True}}); sv=self.savra(g); w=self.creature(g,'Sedgemoor Witch','B','C','C')
        g.advance_to('precombat_main',active_player=1); g.resolve()
        self.assertEqual(g.policy_actions,[(2,1,'exile_commander','Savra on the battlefield')])
        self.assertNotIn(sv.uid,g.permanents); self.assertIn(w.uid,g.permanents)
        self.assertEqual(g.zones.cards[g.zones.zones['command'][0]].name,SAVRA); self.assertEqual(trace(g,'exiled')[-1][1:],(sv.uid,SAVRA,'exile_commander'))
    def test_exile_commander_without_savra_has_no_target(self):
        g=self.game(); w=self.creature(g,'Sedgemoor Witch','B','C','C'); g._act_exile_commander(1)
        self.assertIn(w.uid,g.permanents); self.assertEqual(trace(g,'no_target'),[('no_target',1,'exile_commander')])

class Shigeki(_B):
    def test_takenuma_counts_shigeki_and_returns_it(self):
        g=self.game(); self.creature(g,SH,'G','C')
        tk=self.to_hand(g,'Takenuma, Abandoned Mire'); g.add_mana('B','C','C'); g.channel_takenuma(tk); g.resolve()
        self.assertEqual(trace(g,'channel')[-1][3],2)                                           # {3}{B} less one legendary creature
        g2=self.game(); u=self.to_hand(g2,SH); g2.zones.move(u,'graveyard'); tk=self.to_hand(g2,'Takenuma, Abandoned Mire')
        g2.add_mana('B','C','C','C'); g2.channel_takenuma(tk,return_uid=u); g2.resolve()
        self.assertIn(u,g2.zones.zones['hand']); self.assertEqual(trace(g2,'takenuma_returned')[-1][2],SH)
    def test_takenuma_returns_grist(self):
        g=self.game(); u=self.to_hand(g,GRIST); g.zones.move(u,'graveyard'); tk=self.to_hand(g,'Takenuma, Abandoned Mire')
        g.add_mana('B','C','C','C'); g.channel_takenuma(tk,return_uid=u); g.resolve()
        self.assertIn(u,g.zones.zones['hand']); g.assert_bridge_integrity()
    def test_grisly_salvage_can_take_shigeki(self):
        g=self.game(); gs=self.to_hand(g,'Grisly Salvage'); lib=g.zones.zones['library']
        u=next(x for x in lib if g.zones.cards[x].name==SH); lib.remove(u); lib.insert(0,u)
        g.add_mana('B','G'); g.cast_from_hand(gs,choice_uid=u); g.resolve(); self.assertIn(u,g.zones.zones['hand'])
    def test_rise_returns_shigeki_milled_or_dead(self):
        for how in ('milled','dead'):
            with self.subTest(how=how):
                g=self.game(); self.savra(g)
                if how=='milled': u=self.to_hand(g,SH); g.zones.move(u,'graveyard')
                else:
                    sh=self.creature(g,SH,'G','C'); u=g.linked_battlefield[sh.uid]; g.destroy(sh.uid); g.resolve(); self.assertIn(u,g.zones.zones['graveyard'])
                pe=g.make_tokens(PEST)[0]; g.resolve()
                self.cast(g,'Rise of the Witch-king','B','G','C','C',sacrifice_uid=pe.uid,return_uid=u)
                p=self.named(g,SH); self.assertEqual((p.power,p.toughness,p.colors),(1,3,'G')); self.assertTrue(p.enchantment)
                self.assertEqual(g.linked_battlefield[p.uid],u); g.assert_bridge_integrity()
                with self.assertRaises(Exception): g.add_mana('G','C'); g.shigeki_activate(p.uid)          # entered this turn: summoning sick
    def test_grist_minus_five_counts_shigeki(self):
        g=self.game(); u=self.to_hand(g,SH); g.zones.move(u,'graveyard')
        gu=self.to_hand(g,GRIST); g.add_mana('B','G','C'); g.cast_from_hand(gu); g.resolve(); grist=self.named(g,GRIST); grist.loyalty=6                     # stays on the battlefield after -5
        g.grist_minus_five(); g.resolve(); self.assertEqual(trace(g,'grist_minus_five')[-1][1],1)
    def test_tutor_policy_sees_shigeki(self):
        g=self.game(); lib=g.zones.zones['library']
        for n in ('Swamp','Forest'):
            for x in [x for x in lib if g.zones.cards[x].name==n]: g.zones.move(x,'exile')
        for x in [x for x in lib if g.zones.cards[x].name=='Grave Pact']: g.zones.move(x,'exile')
        u=next(x for x in lib if g.zones.cards[x].name==SH); lib.remove(u); lib.insert(0,u)
        self.assertEqual(s13.tutor_selection(g),u)
        gu=next(x for x in lib if g.zones.cards[x].name==GRIST); lib.remove(gu); lib.insert(0,gu); self.assertEqual(s13.tutor_selection(g),gu)   # Grist is a creature card too
    def test_bounce_unattaches_skullclamp(self):
        g=self.game(); sh=self.creature(g,SH,'G','C'); c=self.clamp(g,sh)
        g.advance_to('cleanup',active_player=0); g.advance_to('precombat_main',active_player=0)
        g.add_mana('G','C'); g.shigeki_activate(sh.uid); g.resolve()
        self.assertEqual(g.skullclamp_attached,{}); self.assertIn(c.uid,g.permanents)
        w=self.creature(g,'Sedgemoor Witch','B','C','C'); self.clamp(g,w); self.assertEqual(g.skullclamp_attached,{c.uid:w.uid})

class PowerPolicies(_B):
    def test_edict_reads_current_power(self):
        for boost in ('counters','skullclamp'):
            with self.subTest(boost=boost):
                g=self.game(); self.savra(g); a=self.creature(g,'Deathgreeter','B'); b=self.creature(g,'Bogwater Lumaret','B','G')   # 1/1 and 2/2
                if boost=='counters': a.counters=2
                else: a.toughness=2; self.clamp(g,a); a.counters=1                                   # 1+1+1 = 3 power
                g._act_edict(1); g.resolve(); self.assertIn(a.uid,g.permanents); self.assertNotIn(b.uid,g.permanents)
    def test_removal_hits_the_creature_the_reason_names(self):
        g=self.game({1:{'removal_budget':1,'removal_min_power':3}}); a=self.creature(g,'Bogwater Lumaret','B','G'); b=self.creature(g,'Yahenni, Undying Partisan','B','C','C')
        self.clamp(g,b)                                                                              # Yahenni 2/2 +1/-1 = 3 power; Lumaret 2
        g.advance_to('precombat_main',active_player=1); g.resolve()
        self.assertEqual(g.policy_actions[-1][3],'Yahenni, Undying Partisan power 3'); self.assertNotIn(b.uid,g.permanents); self.assertIn(a.uid,g.permanents)
    def test_opponent_edict_choice_reads_current_values(self):
        g=PhysicalZoneGame(); g.resolve(); g.declare_opponent_board(1,[{'name':'Knight','power':3,'toughness':3,'mana_value':3},{'name':'Elf','power':1,'toughness':1,'mana_value':1}])
        k=next(p for p in g.opponent_creatures(1) if p.name=='Knight'); g.eot_pt[k.uid]=(-3,-1)
        self.assertEqual(g.edict_choice(1).uid,k.uid)                                              # Knight is 0/2 now, the Elf 1/1
    def test_driver_decay_target_and_charm_count_read_current_values(self):
        import pab_cast_s15 as s15
        g=PhysicalZoneGame(); g.resolve()
        g.declare_opponent_board(1,[{'name':'Knight','power':3,'toughness':3,'mana_value':3},{'name':'Ogre','power':2,'toughness':2,'mana_value':2}])
        g.advance_to('precombat_main',active_player=0); k,o=sorted(g.opponent_creatures(1),key=lambda p:p.name!='Knight')
        g.eot_pt[k.uid]=(-3,0); u=self.to_hand(g,'Abrupt Decay'); g.add_mana('B','G'); s15.cast_when_able(g); g.resolve()
        self.assertIn(k.uid,g.permanents); self.assertNotIn(o.uid,g.permanents)                       # Knight's current power 0 < Ogre 2
        g2=PhysicalZoneGame(); g2.resolve(); g2.declare_opponent_board(1,[{'name':'Ogre','power':2,'toughness':2,'mana_value':2}])
        g2.advance_to('precombat_main',active_player=0); og=g2.opponent_creatures(1)[0]; g2.eot_pt[og.uid]=(0,-1)
        self.to_hand(g2,'Golgari Charm'); g2.add_mana('B','G'); s15.cast_when_able(g2); g2.resolve()
        self.assertNotIn(og.uid,g2.permanents)                                                     # 2/1 now: mode 1 kills it, nothing of yours dies
    def test_hexproof_fallback_reads_current_power(self):
        g=self.game(); a=self.creature(g,'Warren Soultrader','B','C','C'); b=self.creature(g,'Bogwater Lumaret','B','G'); c=self.creature(g,'Yahenni, Undying Partisan','B','C','C')
        self.clamp(g,c); g.hexproof_eot.add(a.uid)                                                   # a 3 (hexproof), b 2, c 2+1
        self.assertEqual(g._own_creature_target().uid,c.uid)

if __name__=='__main__': unittest.main()
