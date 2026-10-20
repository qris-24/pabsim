"""CP23 (A-S20-10): target bookkeeping for Witherbloom Command and Grist, the Hunger Tide -2.

Witherbloom Command (pab_cast_s15.py): modes 2 and 3 take their own targets (mode2_uid / mode3_uid), every
chosen target is locked at cast as (mode, target), mode 1 needs you or an opponent still in the game, and at
resolution every target is re-checked first (CR 608.2b): a mode with an illegal target does nothing (mode 1:
no mill and no land return); with every target illegal the spell does nothing.

Grist -2 (pab_grist_s16.py): the sacrifice is made at resolution; the reflexive target is chosen and checked
when the reflexive trigger is put on the stack (CR 603.12). With no legal target then, the trigger is not put
on the stack (CR 603.3d, traced grist_minus_two_no_legal_target, not a fizzle); a target that leaves after
that makes the trigger fizzle at resolution.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import PEST, SAVRA
from pab_zone_bridge import BridgeError
from pab_kernel import PhysicalZoneGame
from pab_grist_s16 import GRIST

BEAR={'name':'Bear','power':2,'toughness':2,'mana_value':2}
OGRE={'name':'Ogre','power':3,'toughness':3,'mana_value':4}
WC='Witherbloom Command'
FIZZLE='spell_fizzles_all_targets_illegal'
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def pzg(self,boards=None,*,main=False):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve()
        for seat,bodies in (boards or {}).items(): g.declare_opponent_board(seat,bodies)
        if main: g.advance_to('precombat_main',active_player=0)
        return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=uid,destination='hand'); return uid
    def to_graveyard(self,g,name):
        uid=self.to_hand(g,name); g.zones.move(uid,'graveyard'); return uid
    def opp(self,g,seat,name): return next(p.uid for p in g.opponent_creatures(seat) if p.name==name)
    def cast_physical(self,g,name,*mana,**kw):
        uid=self.to_hand(g,name); g.add_mana(*mana); g.cast_from_hand(uid,**kw); self.assertIn(uid,g.stack_cards); return uid
    def refused(self,g,uid,*mana,**kw):
        g.add_mana(*mana); snap=lambda:(list(g.zones.zones['hand']),list(g.mana_pool),set(g.permanents),len(g.trace),list(g.life),dict(g.stack_cards)); before=snap()
        with self.assertRaises(BridgeError): g.cast_from_hand(uid,**kw)
        self.assertEqual(snap(),before); del g.mana_pool[:]
    def sol_ring(self,g):
        ph=self.cast_physical(g,'Sol Ring','C'); g.resolve(); return next(k for k,v in g.linked_battlefield.items() if v==ph)
    def leave(self,g,seat):
        g.life[seat]=0; g.state_based_actions(); self.assertIn(seat,g.lost_seats)
    def locked(self,g,name): return [t[1] for t in trace(g,'targets_locked') if t[2]==name]
    def step(self,g):
        """Resolve exactly one pending object, as the kernel's resolve loop does (SBA after it)."""
        t=g.pending.popleft(); g.trace.append(('resolve',t.label)); t.action(); g.state_based_actions(); return t.label


class CommandTargets(_B):
    def test_modes_2_and_3_castable_each_target_resolved_independently(self):
        g=self.pzg({1:[BEAR]}); e=self.sol_ring(g); bear=self.opp(g,1,'Bear'); uid=self.to_hand(g,WC)
        self.refused(g,uid,'B','G',modes=(2,3),target_uid=e)                                   # one uid for two targets
        self.refused(g,uid,'B','G',modes=(2,4),mode3_uid=bear,target_uid=e,target_opponent=1)  # mode3_uid without mode 3
        self.refused(g,uid,'B','G',modes=(2,3),mode2_uid=bear,mode3_uid=bear)                  # mode 2 cannot take a creature
        g.add_mana('B','G'); g.cast_from_hand(uid,modes=(2,3),mode2_uid=e,mode3_uid=bear)
        self.assertEqual(self.locked(g,WC),[(('mode2_permanent',e),('mode3_creature',bear))])
        g.resolve(); self.assertNotIn(e,g.permanents); self.assertEqual(g.eot_pt[bear],(-3,-1)); self.assertIn(bear,g.permanents)
        self.assertEqual(trace(g,FIZZLE),[]); self.assertEqual(trace(g,'mode_target_illegal'),[])
        # mode 3's target leaves before resolution: mode 2 still destroys, mode 3 does nothing, no fizzle
        g2=self.pzg({1:[BEAR]}); e2=self.sol_ring(g2); bear2=self.opp(g2,1,'Bear')
        self.cast_physical(g2,WC,'B','G',modes=(2,3),mode2_uid=e2,mode3_uid=bear2); g2._opponent_creature_dies(bear2,cause='test'); g2.resolve()
        self.assertNotIn(e2,g2.permanents); self.assertNotIn(bear2,g2.eot_pt); self.assertEqual(trace(g2,FIZZLE),[])
        self.assertEqual(trace(g2,'mode_target_illegal'),[('mode_target_illegal',WC,3,('mode3_creature',bear2))])
        # mode 2's target leaves before resolution: mode 3 still applies
        g3=self.pzg({1:[BEAR]}); e3=self.sol_ring(g3); bear3=self.opp(g3,1,'Bear')
        self.cast_physical(g3,WC,'B','G',modes=(3,2),mode2_uid=e3,mode3_uid=bear3); g3._destroy_any(e3,'test'); g3.resolve()
        self.assertEqual(g3.eot_pt[bear3],(-3,-1)); self.assertEqual(trace(g3,FIZZLE),[])
        self.assertEqual(trace(g3,'mode_target_illegal'),[('mode_target_illegal',WC,2,('mode2_permanent',e3))])

    def test_mode1_on_an_eliminated_seat_refused_at_cast(self):
        g=self.pzg(); self.leave(g,1); uid=self.to_hand(g,WC)
        self.refused(g,uid,'B','G',modes=(1,4),target_player=1,target_opponent=2)               # seat 1 has left the game
        self.refused(g,uid,'B','G',modes=(1,4),target_player=7,target_opponent=2)               # not a seat
        self.refused(g,uid,'B','G',modes=(1,4),target_opponent=2)                               # no target player
        g.add_mana('B','G'); g.cast_from_hand(uid,modes=(1,4),target_player=2,target_opponent=3)
        self.assertEqual(self.locked(g,WC),[(('mode1_player',2),('mode4_opponent',3))])

    def test_mode1_player_leaves_before_resolution_no_mill_no_land(self):
        g=self.pzg(); swamp=self.to_graveyard(g,'Swamp'); lib=len(g.zones.zones['library'])
        uid=self.cast_physical(g,WC,'B','G',modes=(1,4),target_player=2,target_opponent=3); life0,life3=g.life[0],g.life[3]
        self.leave(g,2); g.resolve()
        self.assertEqual(g.zones.cards[swamp].zone,'graveyard'); self.assertEqual(trace(g,'land_returned_to_hand'),[])
        self.assertEqual(trace(g,'opponent_mill_unmodeled'),[]); self.assertEqual(len(g.zones.zones['library']),lib-1)  # only the Command left the library
        self.assertEqual(trace(g,'mode_target_illegal'),[('mode_target_illegal',WC,1,('mode1_player',2))])
        self.assertEqual((g.life[0],g.life[3]),(life0+2,life3-2)); self.assertEqual(trace(g,FIZZLE),[]); self.assertEqual(g.zones.cards[uid].zone,'graveyard')

    def test_all_targets_illegal_whole_spell_does_nothing(self):
        g=self.pzg(); swamp=self.to_graveyard(g,'Swamp')
        uid=self.cast_physical(g,WC,'B','G',modes=(1,4),target_player=1,target_opponent=1); life0=g.life[0]
        self.leave(g,1); g.resolve()
        self.assertIn((FIZZLE,WC),g.trace); self.assertEqual(g.zones.cards[swamp].zone,'graveyard'); self.assertEqual(trace(g,'land_returned_to_hand'),[])
        self.assertEqual(g.life[0],life0); self.assertEqual(trace(g,'witherbloom_command_target'),[]); self.assertEqual(trace(g,'mode_target_illegal'),[])
        self.assertEqual(g.zones.cards[uid].zone,'graveyard')
        g2=self.pzg({1:[BEAR]}); e=self.sol_ring(g2); bear=self.opp(g2,1,'Bear')
        self.cast_physical(g2,WC,'B','G',modes=(2,3),mode2_uid=e,mode3_uid=bear); g2._destroy_any(e,'test'); g2._opponent_creature_dies(bear,cause='test'); g2.resolve()
        self.assertIn((FIZZLE,WC),g2.trace); self.assertNotIn(bear,g2.eot_pt); self.assertEqual([t for t in trace(g2,'destroyed_by') if t[3]==WC],[])

    def test_mode4_target_opponent_in_targets_locked(self):
        g=self.pzg(); self.cast_physical(g,WC,'B','G',modes=(1,4),target_player=0,target_opponent=2)
        self.assertEqual(self.locked(g,WC),[(('mode1_player',0),('mode4_opponent',2))])
        life2=g.life[2]; g.resolve(); self.assertEqual(g.life[2],life2-2); self.assertIn(('witherbloom_command_target',2,2),g.trace)


class GristReflexiveTarget(_B):
    def grist(self,g):
        ph=self.cast_physical(g,GRIST,'B','G','C'); g.resolve(); return g.grist()
    def pest(self,g):
        p=g.make_tokens(PEST)[0]; g.resolve(); return p
    def no_reflexive(self,g):
        self.assertNotIn('Grist -2 reflexive destroy (S16)',[t[1] for t in trace(g,'resolve')])
        self.assertEqual([t for t in trace(g,'destroyed_by') if t[3]=='Grist -2'],[]); self.assertNotIn((FIZZLE,'Grist -2'),g.trace)
        self.assertEqual(self.locked(g,'Grist -2 reflexive'),[])

    def test_sacrifice_is_the_target_no_trigger_traced(self):
        g=self.pzg({1:[BEAR]},main=True); gr=self.grist(g); p=self.pest(g)
        g.grist_minus_two(sacrifice_uid=p.uid,target_uid=p.uid); self.assertEqual(gr.loyalty,1); g.resolve()
        self.assertIn(('sacrifice',p.uid,'ordinary Pest'),g.trace); self.assertNotIn(p.uid,g.permanents)
        self.assertEqual(trace(g,'grist_minus_two_no_legal_target'),[('grist_minus_two_no_legal_target',p.uid)]); self.no_reflexive(g)

    def test_target_leaves_between_activation_and_trigger_no_trigger(self):
        g=self.pzg({1:[OGRE]},main=True); self.grist(g); p=self.pest(g); ogre=self.opp(g,1,'Ogre')
        g.grist_minus_two(sacrifice_uid=p.uid,target_uid=ogre); g._opponent_creature_dies(ogre,cause='test'); g.resolve()
        self.assertNotIn(p.uid,g.permanents); self.assertEqual(trace(g,'grist_minus_two_no_legal_target'),[('grist_minus_two_no_legal_target',ogre)]); self.no_reflexive(g)

    def test_target_leaves_after_trigger_fizzles_and_target_was_locked(self):
        g=self.pzg({1:[OGRE]},main=True); self.grist(g); p=self.pest(g); ogre=self.opp(g,1,'Ogre')
        g.grist_minus_two(sacrifice_uid=p.uid,target_uid=ogre); self.assertEqual(self.locked(g,'Grist -2 reflexive'),[])   # not chosen at activation
        self.assertEqual(self.step(g),'Grist -2 (S16)'); self.assertNotIn(p.uid,g.permanents)
        self.assertIn('Grist -2 reflexive destroy (S16)',[t.label for t in g.pending]); self.assertEqual(self.locked(g,'Grist -2 reflexive'),[(ogre,)])
        self.assertLess(g.trace.index(('sacrifice',p.uid,'ordinary Pest')),g.trace.index(('targets_locked',(ogre,),'Grist -2 reflexive')))
        g._opponent_creature_dies(ogre,cause='test'); g.resolve()
        self.assertIn((FIZZLE,'Grist -2'),g.trace); self.assertEqual(trace(g,'grist_minus_two_no_legal_target'),[])
        self.assertEqual([t for t in trace(g,'destroyed_by') if t[3]=='Grist -2'],[])

if __name__=='__main__':
    unittest.main()
