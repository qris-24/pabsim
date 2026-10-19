"""CP14 (A-S20-06): a milled or discarded Grist gets her event-kernel graveyard LKI automatically.
The LKI (creature=True, mana value 3, linked to the physical card) is made by the zones.move wrapper
installed by GristMixin, so the frozen _grave_target() sees her without a grist_graveyard_lki() call;
the battlefield->graveyard path keeps its own LKI (no duplicate); the LKI and link are dropped again
when the physical card leaves the graveyard; the manual helper stays idempotent. """
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA
from pab_kernel import PhysicalZoneGame
from pab_grist_s16 import GRIST, check_invariants_s16
from pab_opponents_s8 import OPPONENT_SEATS

BOARD=[{'name':'Bear','power':2,'toughness':2,'mana_value':2},{'name':'Dragon','power':5,'toughness':5,'mana_value':6}]
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names,board=True):
        g=PhysicalZoneGame(); g.add(SAVRA)
        for n in names: g.add(n)
        g.resolve()
        if board:
            for s in OPPONENT_SEATS: g.declare_opponent_board(s,BOARD)
        check_invariants_s16(g); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); g.zones.search_library(selected_uid=uid,destination='hand'); check_invariants_s16(g); return uid
    def grist(self,g):
        g.advance_to('precombat_main',active_player=0); uid=self.to_hand(g,GRIST); g.add_mana('B','G','C'); g.cast_from_hand(uid); check_invariants_s16(g); g.resolve(); check_invariants_s16(g)
        p=g.grist(); self.assertEqual((p.loyalty,p.creature,g.linked_battlefield[p.uid]),(3,False,uid)); return p,uid
    def lki_assertions(self,g,uid):
        """Exactly one Grist LKI, creature=True, MV 3, linked to the physical card, made by the wrapper (one trace)."""
        lkis=[q for q in g.graveyard if q.name==GRIST]; self.assertEqual(len(lkis),1); lki=lkis[0]
        self.assertTrue(lki.creature); self.assertFalse(lki.token); self.assertEqual(lki.mana_value,3)
        self.assertEqual(g.linked_graveyard[lki.uid],uid); self.assertEqual(g.zones.cards[uid].zone,'graveyard')
        self.assertEqual(trace(g,'grist_graveyard_lki'),[('grist_graveyard_lki',lki.uid,uid)])
        self.assertIs(g._grave_target(lki.uid),lki); g.assert_bridge_integrity(); check_invariants_s16(g); return lki
    def unearth(self,g,lki):
        g.advance_to('precombat_main',active_player=0); un=self.to_hand(g,'Unearth'); g.add_mana('B'); g.cast_from_hand(un,target_uid=lki.uid); g.resolve(); check_invariants_s16(g)
        p=g.grist(); self.assertIsNotNone(p); self.assertEqual((p.loyalty,p.creature),(3,False)); self.assertNotIn(lki,g.graveyard); self.assertNotIn(lki.uid,g.linked_graveyard)

class AutomaticLKI(_B):
    def test_milled_grist_has_an_lki_without_the_helper_and_unearth_returns_her(self):
        g=self.game(); uid=self.to_hand(g,GRIST); g.zones.move(uid,'library',top=True); self.assertEqual(trace(g,'grist_graveyard_lki'),[])
        milled=g.zones.mill(1); self.assertEqual([c.uid for c in milled],[uid])
        lki=self.lki_assertions(g,uid); self.unearth(g,lki); self.assertEqual(g.zones.cards[uid].zone,'battlefield')
    def test_discarded_grist_has_an_lki_without_the_helper(self):
        g=self.game(); uid=self.to_hand(g,GRIST); g.zones.discard(uid)
        lki=self.lki_assertions(g,uid); self.unearth(g,lki)
    def test_battlefield_to_graveyard_keeps_exactly_one_lki(self):
        g=self.game(); p,uid=self.grist(g); g.destroy(p.uid); check_invariants_s16(g)
        self.assertIsNone(g.grist()); self.assertEqual(g.zones.cards[uid].zone,'graveyard')
        self.assertEqual([q.uid for q in g.graveyard if q.name==GRIST],[p.uid]); self.assertEqual(g.linked_graveyard[p.uid],uid)
        self.assertEqual(trace(g,'grist_graveyard_lki'),[]); g.assert_bridge_integrity()                   # the wrapper did not add a second
    def test_leaving_the_graveyard_drops_the_automatic_lki(self):
        g=self.game(); uid=self.to_hand(g,GRIST); g.zones.move(uid,'library',top=True); g.zones.mill(1); lki=self.lki_assertions(g,uid)
        g.zones.move(uid,'library'); self.assertEqual(g.zones.cards[uid].zone,'library')
        self.assertNotIn(lki,g.graveyard); self.assertEqual([q for q in g.graveyard if q.name==GRIST],[]); self.assertNotIn(lki.uid,g.linked_graveyard)
        self.assertEqual(trace(g,'grist_lki_dropped'),[('grist_lki_dropped',lki.uid,uid)]); self.assertIsNone(g._grave_target(lki.uid))
        g.assert_bridge_integrity(); check_invariants_s16(g)
        g.zones.move(uid,'graveyard'); self.assertEqual(len(trace(g,'grist_graveyard_lki')),2)         # back in: a fresh LKI, still exactly one
        self.assertEqual(len([q for q in g.graveyard if q.name==GRIST]),1); g.assert_bridge_integrity(); check_invariants_s16(g)
    def test_manual_helper_after_automatic_creation_returns_the_same_object(self):
        g=self.game(); uid=self.to_hand(g,GRIST); g.zones.move(uid,'graveyard'); lki=self.lki_assertions(g,uid)
        self.assertIs(g.grist_graveyard_lki(),lki); self.assertIs(g.grist_graveyard_lki(),lki)
        self.assertEqual(len(trace(g,'grist_graveyard_lki')),1); self.assertEqual(len([q for q in g.graveyard if q.name==GRIST]),1); g.assert_bridge_integrity()

if __name__=='__main__': unittest.main()
