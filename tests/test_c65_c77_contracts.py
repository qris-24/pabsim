"""Executable contracts C65–C77 (issues R35–R40, lands) against the promoted kernel.

Land support is Forest {G}, Swamp {B}, Command Tower {B}/{G} (physical bridge),
since S9 (2026-10-18) the nine B/G fixer lands as well, plus Sol Ring / Arcane Signet / Golgari Signet rocks and basic-only
Nature's Lore / Sakura-Tribe Elder fixtures; since S14 all 34 lands are playable. Statuses:
  EXECUTED / EXECUTED_WITH_SUBSTITUTION / PARTIAL_EXECUTED (some expectations
  asserted, the rest blocked) / BLOCKED_UNSUPPORTED (probe asserts ONLY that the
  kernel refuses the card without mutating state — never the contract's
  expectation).
No contract is Oracle/CR-authenticated.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, IllegalAction
from pab_zones import ZoneError, UnsupportedZoneMechanic
from pab_kernel import Game, PhysicalZoneGame

def snapshot(g):
    z=g.zones
    return ({k:tuple(v) for k,v in z.zones.items()}, tuple(sorted(g.permanents)), tuple(g.mana_pool),
            z.land_plays_this_turn, tuple((u,z.cards[u].tapped) for u in z.zones['battlefield']))

class _Land(unittest.TestCase):
    def bridge(self):
        g=PhysicalZoneGame(); g.add(SAVRA); g.resolve(); return g
    def to_hand(self,g,name):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); return uid
    def assert_fails_closed(self,name):
        """Playing NAME must raise UnsupportedZoneMechanic and leave every zone,
        permanent, mana and tap state exactly as before."""
        g=self.bridge(); uid=self.to_hand(g,name); before=snapshot(g)
        with self.assertRaises(UnsupportedZoneMechanic): g.play_physical_land(uid)
        self.assertEqual(snapshot(g),before); g.assert_bridge_integrity()
        self.assertEqual(g.zones.cards[uid].zone,'hand')
        return g


class C65(_Land):
    CONTRACT='C65'; ISSUES=['R35']; STATUS='EXECUTED'
    SUBSTITUTIONS=['S9 (2026-10-18) executes the contract: other-land counts 1, 2, 3 for both lands; the boundary-2 comparison; a nontoken land entering earlier in the turn is the pre-state (fixture land-drop reset)']
    def test_land_count_boundaries(self):
        exp={'Blooming Marsh':{1:False,2:False,3:True},'Deathcap Glade':{1:True,2:False,3:False}}   # tapped?
        for name,table in exp.items():
            for others,tapped in table.items():
                with self.subTest(land=name,other_lands=others):
                    g=self.bridge()
                    for n in ('Swamp','Forest','Command Tower')[:others]: g.play_physical_land(self.to_hand(g,n)); g.zones.land_plays_this_turn=0
                    pre=sum(1 for c in g.zones.cards.values() if c.zone=='battlefield' and c.is_land); self.assertEqual(pre,others)
                    uid=self.to_hand(g,name); q=g.play_physical_land(uid); g.assert_bridge_integrity()
                    self.assertEqual(q.tapped,tapped); self.assertEqual(g.zones.cards[uid].tapped,tapped)
                    self.assertEqual([t for t in g.trace if t[0]=='s9_land_entered'][-1],('s9_land_entered',name,None,'tapped' if tapped else 'untapped'))

class C66(_Land):
    CONTRACT='C66'; ISSUES=['R35']; STATUS='EXECUTED'
    SUBSTITUTIONS=['S9 + S8 execute the contract: the opponent count is the number of seats still in the game (seats 1-3 minus those that left at 0 life), never an assumed pod size']
    def test_opponent_count_decides_tapped(self):
        for lost,tapped in (((),False),((1,),False),((1,2),True),((1,2,3),True)):
            with self.subTest(opponents=3-len(lost)):
                g=self.bridge()
                for seat in lost: g.life[seat]=0
                g.resolve(); self.assertEqual(sorted(g.lost_seats),sorted(lost))
                uid=self.to_hand(g,'Undergrowth Stadium'); q=g.play_physical_land(uid); g.assert_bridge_integrity()
                self.assertEqual(q.tapped,tapped); self.assertEqual(len(g.seats_in_game()),3-len(lost))

class C67(_Land):
    CONTRACT='C67'; ISSUES=['R35','R38']; STATUS='EXECUTED'
    SUBSTITUTIONS=['S9 executes the contract: Tomb pay 2 life -> untapped (pay_life trace names the cause), no payment -> tapped; Mortuary always tapped and surveils 1 (top card traced, kept or milled by the pre-committed choice). Forest control retained.']
    def test_tomb_payment_and_mortuary_surveil(self):
        g=self.bridge(); uid=self.to_hand(g,'Overgrown Tomb'); q=g.play_physical_land(uid,pay_life=True)
        self.assertFalse(q.tapped); self.assertEqual(g.life[0],38); self.assertIn(('pay_life',2,'Overgrown Tomb'),g.trace)
        g=self.bridge(); uid=self.to_hand(g,'Overgrown Tomb'); q=g.play_physical_land(uid); self.assertTrue(q.tapped); self.assertEqual(g.life[0],40)
        for to_grave in (False,True):
            g=self.bridge(); uid=self.to_hand(g,'Underground Mortuary'); top=g.zones.zones['library'][0]
            q=g.play_physical_land(uid,surveil_graveyard=to_grave); self.assertTrue(q.tapped); g.resolve(); g.assert_bridge_integrity()
            self.assertEqual([t for t in g.trace if t[0]=='surveil'],[('surveil',top,'graveyard' if to_grave else 'top')])
            self.assertEqual(g.zones.cards[top].zone,'graveyard' if to_grave else 'library'); self.assertEqual(g.life[0],40)
    def test_control_forest_enters_untapped_no_life_change(self):
        g=self.bridge(); uid=self.to_hand(g,'Forest'); p=g.play_physical_land(uid)
        self.assertFalse(p.tapped); self.assertEqual(g.life,[40,40,40,40])
        self.assertEqual(g.zones.land_plays_this_turn,1)
        with self.assertRaises(ZoneError): g.play_physical_land(self.to_hand(g,'Swamp'))   # one land per turn

class C68(_Land):
    CONTRACT='C68'; ISSUES=['R35','R15']; STATUS='EXECUTED'
    SUBSTITUTIONS=['S9 executes the contract: one reset game per face; the selected face is recorded on the permanent and fixes the only available colour; the other colour is refused. The permanent keeps the full card name (bridge identity rule), documented in S9_PATCH_NOTES.md']
    def test_face_fixed_on_entry(self):
        from pab_lands_s9 import PATHWAY
        from pab_zone_bridge import BridgeError
        for face,color,other in (('Darkbore','B','G'),('Slitherbore','G','B')):
            with self.subTest(face=face):
                g=self.bridge(); uid=self.to_hand(g,PATHWAY); q=g.play_physical_land(uid,face=face); g.assert_bridge_integrity()
                self.assertEqual(q.face,face); self.assertFalse(q.tapped)
                with self.assertRaises(BridgeError): g.tap_physical_land_for_mana(q.uid,color=other)
                self.assertEqual(g.tap_physical_land_for_mana(q.uid),color); self.assertEqual(g.mana_pool,[color])
                self.assertIn(('s9_land_entered',PATHWAY,face,'untapped'),g.trace)

class C69(_Land):
    CONTRACT='C69'; ISSUES=['R36']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['Asserted: basic Forest qualifies, Swamp does not, Forest enters untapped, Sakura basic-only control. '
                   'NOT asserted: Overgrown Tomb / Underground Mortuary qualifying by Forest subtype, and Woodland '
                   'Cemetery / Pathway exclusion — nonbasic Forest-typed search is unmodeled and fails closed']
    def test_event_fixture_forest_qualifies_swamp_rejected(self):
        g=Game(); g.add(SAVRA); g.resolve()
        f=g.put_basic_land_in_fixture_library('Forest'); s=g.put_basic_land_in_fixture_library('Swamp')
        g.add_mana('G','C')
        with self.assertRaises(IllegalAction): g.natures_lore(land_index=s)
        self.assertEqual(g.mana_pool,['G','C'])                    # rejected before payment
        g.natures_lore(land_index=f); g.resolve()
        found=[t for t in g.trace if t[0]=='fixture_basic_land_to_battlefield']
        self.assertEqual(len(found),1); self.assertFalse(g.permanents[found[0][1]].tapped)
    def test_physical_nonbasic_forest_typed_search_fails_closed(self):
        g=self.bridge(); z=g.zones
        tomb=next(u for u in z.zones['library'] if z.cards[u].name=='Overgrown Tomb'); before=snapshot(g)
        with self.assertRaises((ZoneError,UnsupportedZoneMechanic)):
            z.search_library(selected_uid=tomb,destination='battlefield',eligible='basic_forest')
        self.assertEqual(snapshot(g),before)
    def test_physical_basic_forest_search_enters(self):
        g=self.bridge(); z=g.zones
        forest=next(u for u in z.zones['library'] if z.cards[u].name=='Forest')
        z.search_library(selected_uid=forest,destination='battlefield',eligible='basic_forest')
        self.assertEqual(z.cards[forest].zone,'battlefield'); self.assertFalse(z.cards[forest].tapped)
    def test_control_sakura_basic_only(self):
        g=self.bridge(); z=g.zones
        tomb=next(u for u in z.zones['library'] if z.cards[u].name=='Overgrown Tomb')
        with self.assertRaises((ZoneError,UnsupportedZoneMechanic)):
            z.search_library(selected_uid=tomb,destination='battlefield',eligible='basic',tapped=True)
        swamp=next(u for u in z.zones['library'] if z.cards[u].name=='Swamp')
        z.search_library(selected_uid=swamp,destination='battlefield',eligible='basic',tapped=True)
        self.assertTrue(z.cards[swamp].tapped)

class C70(_Land):
    CONTRACT='C70'; ISSUES=['R36','R37','R38']; STATUS='EXECUTED'
    SUBSTITUTIONS=['S14 (2026-10-18) executes the contract: tap + pay 1 life + sacrifice as the activation cost (land to graveyard, life traced), search by Swamp/Forest TYPE (Swamp, Forest, Overgrown Tomb, Underground Mortuary; Woodland Cemetery refused), fetched land enters by its own rule (Tomb paid/declined), shuffle. Not asserted: resources lacking beyond life/tap (Verdant has no mana cost).']
    def test_activation_cost_order_type_search_and_fetch_etb(self):
        from pab_lands_s14 import FETCHABLE
        self.assertEqual(FETCHABLE,frozenset({'Swamp','Forest','Overgrown Tomb','Underground Mortuary'}))
        for name,kw,tapped,delta in (('Swamp',{},False,-1),('Overgrown Tomb',{'pay_life':True},False,-3),('Overgrown Tomb',{},True,-1),('Underground Mortuary',{},True,-1)):
            with self.subTest(fetch=name,kw=kw):
                g=self.bridge(); uid=self.to_hand(g,'Verdant Catacombs'); vc=g.play_physical_land(uid); sel=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name); life=g.life[0]
                g.verdant_catacombs(vc.uid,sel,**kw); t=g.trace
                self.assertLess(t.index(('pay_life',1,'Verdant Catacombs')),t.index(('land_sacrificed',vc.uid,uid,'Verdant Catacombs'))); self.assertEqual(g.zones.cards[uid].zone,'graveyard'); self.assertEqual(g.zones.cards[sel].zone,'library')   # costs paid, effect pending
                g.resolve(); g.assert_bridge_integrity(); self.assertEqual(g.zones.cards[sel].zone,'battlefield'); self.assertEqual(g.zones.cards[sel].tapped,tapped); self.assertEqual(g.life[0],life+delta)
                self.assertEqual([x for x in g.trace if x[0]=='fetched_land_entered'][-1][1],name)
        g=self.bridge(); uid=self.to_hand(g,'Verdant Catacombs'); vc=g.play_physical_land(uid); bad=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Woodland Cemetery')
        with self.assertRaises(Exception): g.verdant_catacombs(vc.uid,bad)
        self.assertEqual(g.zones.cards[uid].zone,'battlefield'); self.assertEqual(g.life[0],40)                    # refused before any cost

class C71(_Land):
    CONTRACT='C71'; ISSUES=['R37']; STATUS='EXECUTED'
    SUBSTITUTIONS=['S14 executes the contract: the creature is sacrificed as the mana-ability cost (frozen sacrifice()), {B}{B} is added at once (no stack), and the Pest death-gain and Savra sacrifice triggers are distinct pending triggers; {C} ability and High Market as controls.']
    def test_tower_sacrifice_mana_ability_and_distinct_triggers(self):
        from pab_focus_engine import PEST
        g=self.bridge(); uid=self.to_hand(g,'Phyrexian Tower'); t=g.play_physical_land(uid); p=g.make_tokens(PEST)[0]; g.resolve()
        g.tower_sacrifice(t.uid,p.uid); self.assertEqual(g.mana_pool,['B','B']); self.assertTrue(t.tapped); self.assertNotIn(p.uid,g.permanents)
        self.assertEqual(sorted(x.label for x in g.pending),sorted(['Savra black sacrifice','Savra green sacrifice','Pest dies-gain'])); self.assertIn(('mana_ability','Phyrexian Tower',p.uid,('B','B')),g.trace)
        g.resolve(); g.assert_bridge_integrity()
        g2=self.bridge(); uid=self.to_hand(g2,'Phyrexian Tower'); t=g2.play_physical_land(uid); self.assertEqual(g2.tap_physical_land_for_mana(t.uid),'C'); self.assertEqual(g2.pending.__len__(),0)   # {C} control: no sacrifice, nothing pending

class C72(_Land):
    CONTRACT='C72'; ISSUES=['R37']; STATUS='EXECUTED'
    SUBSTITUTIONS=['S14 executes the contract: for both lands the sacrifice (and Grim Backwoods\' {2}{B}{G}) is paid before the ability goes on the stack; High Market gains 1 on resolution, Grim Backwoods draws on resolution; a sacrifice-free activation (a land as the creature) is refused.']
    def test_cost_before_resolution_gain_vs_draw(self):
        from pab_focus_engine import PEST
        g=self.bridge(); uid=self.to_hand(g,'High Market'); hm=g.play_physical_land(uid); p=g.make_tokens(PEST)[0]; g.resolve(); life=g.life[0]
        g.high_market(hm.uid,p.uid); self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.life[0],life); self.assertEqual(g.pending[-1].label,'High Market resolution (S14)')
        g.resolve(); self.assertIn(('gain',1,'High Market'),g.trace)
        g=self.bridge(); uid=self.to_hand(g,'Grim Backwoods'); gb=g.play_physical_land(uid); p=g.make_tokens(PEST)[0]; g.resolve(); g.add_mana('B','G','C','C'); d=g.cards_drawn
        g.grim_backwoods(gb.uid,p.uid); self.assertEqual(g.mana_pool,[]); self.assertNotIn(p.uid,g.permanents); self.assertEqual(g.cards_drawn,d); g.resolve(); self.assertEqual(g.cards_drawn,d+1)
        g=self.bridge(); uid=self.to_hand(g,'High Market'); hm=g.play_physical_land(uid)
        with self.assertRaises(Exception): g.high_market(hm.uid,hm.uid)
        self.assertFalse(hm.tapped)

class C73(_Land):
    CONTRACT='C73'; ISSUES=['R38']; STATUS='EXECUTED'
    SUBSTITUTIONS=['S9 executes the contract: Wastes {C} no damage; Wastes {B} one damage (traced as damage, applied as life loss, CR 120.3e; no prevention modeled); Peatland {B} pays 1 life (pay_life trace). No gain event in any case.']
    def test_wastes_damage_vs_peatland_payment(self):
        g=self.bridge(); uid=self.to_hand(g,'Llanowar Wastes'); q=g.play_physical_land(uid)
        self.assertEqual(g.tap_physical_land_for_mana(q.uid,color='C'),'C'); self.assertEqual(g.life[0],40)
        g=self.bridge(); uid=self.to_hand(g,'Llanowar Wastes'); q=g.play_physical_land(uid)
        self.assertEqual(g.tap_physical_land_for_mana(q.uid,color='B'),'B'); self.assertEqual(g.life[0],39)
        self.assertIn(('damage_to_controller',1,'Llanowar Wastes'),g.trace); self.assertIn(('lose_life',1,'Llanowar Wastes'),g.trace); self.assertNotIn('pay_life',{t[0] for t in g.trace})
        g=self.bridge(); uid=self.to_hand(g,'Nurturing Peatland'); q=g.play_physical_land(uid)
        self.assertEqual(g.tap_physical_land_for_mana(q.uid,color='B'),'B'); self.assertEqual(g.life[0],39)
        self.assertIn(('pay_life',1,'Nurturing Peatland'),g.trace); self.assertNotIn('damage_to_controller',{t[0] for t in g.trace})
        self.assertEqual([t for t in g.trace if t[0]=='gain'],[]); self.assertTrue(q.tapped)

class C74(_Land):
    CONTRACT='C74'; ISSUES=['R38']; STATUS='EXECUTED'
    SUBSTITUTIONS=['S14 executes the contract: with two cards in hand the draw happens first and the loss equals the resulting hand size (3); zero-card control loses 1; an empty library records a failed draw rather than ignoring it.']
    def test_draw_then_hand_size_loss(self):
        g=self.bridge(); uid=self.to_hand(g,'Castle Locthwain'); cl=g.play_physical_land(uid); g._untap_step(0)
        for u in list(g.zones.zones['hand']): g.zones.move(u,'library')
        self.to_hand(g,'Swamp'); self.to_hand(g,'Forest'); g.add_mana('B','B','C'); life=g.life[0]
        g.castle_locthwain(cl.uid); self.assertTrue(cl.tapped); g.resolve(); self.assertEqual(len(g.zones.zones['hand']),3); self.assertEqual(g.life[0],life-3)
        self.assertIn(('castle_locthwain_hand',2,3),g.trace)
        g2=self.bridge(); uid=self.to_hand(g2,'Castle Locthwain'); cl=g2.play_physical_land(uid); g2._untap_step(0)
        for u in list(g2.zones.zones['hand']): g2.zones.move(u,'library')
        g2.add_mana('B','B','C'); g2.castle_locthwain(cl.uid); g2.resolve(); self.assertEqual(g2.life[0],39)
        g3=self.bridge(); uid=self.to_hand(g3,'Castle Locthwain'); cl=g3.play_physical_land(uid); g3._untap_step(0)
        for z in ('hand','library'):
            for u in list(g3.zones.zones[z]): g3.zones.move(u,'exile')
        g3.add_mana('B','B','C'); g3.castle_locthwain(cl.uid); g3.resolve(); self.assertEqual(g3.zones.failed_draws,1)

class C75(_Land):
    CONTRACT='C75'; ISSUES=['R39']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['S14: Takenuma executed — channel from hand (discard as the cost, not a land play or cast), generic 3 reduced by one per legendary creature you control to a floor of 0 (0, 1, 2, 4 legends). Boseiju NOT executed: no opponent controls an artifact, enchantment or nonbasic land in this kernel, so its channel has no legal target and is refused. Controls not asserted: a legendary non-creature land, Grist.']
    def test_takenuma_discount_and_boseiju_refused(self):
        from pab_focus_engine import SAVRA
        for legends,generic in ((0,3),(1,2),(2,1),(4,0)):
            with self.subTest(legends=legends):
                h=PhysicalZoneGame(); h.resolve()
                for n in (SAVRA,'Dina, Soul Steeper','Yahenni, Undying Partisan','Yawgmoth, Thran Physician')[:legends]: h.add(n)
                h.resolve(); tk=self.to_hand(h,'Takenuma, Abandoned Mire'); h.add_mana('B',*(['C']*generic)); n=len(h.zones.zones['library'])
                h.channel_takenuma(tk); self.assertEqual(h.mana_pool,[]); self.assertEqual(h.zones.cards[tk].zone,'graveyard'); self.assertEqual([x for x in h.trace if x[0]=='channel'][-1][3],generic)
                self.assertEqual([x for x in h.zones.trace if x[0]=='land_played'],[]); h.resolve(); self.assertEqual(len(h.zones.zones['library']),n-3)
        g=self.bridge(); bo=self.to_hand(g,'Boseiju, Who Endures'); g.add_mana('G','C')
        with self.assertRaises(Exception): g.boseiju_channel(bo)
        self.assertEqual(g.zones.cards[bo].zone,'hand'); self.assertEqual(g.mana_pool,['G','C'])

class C76(_Land):
    CONTRACT='C76'; ISSUES=['R40']; STATUS='PARTIAL_EXECUTED'
    SUBSTITUTIONS=['S14: the controller\'s side executed — Sanitarium draws then discards, Mikokoro only draws, both {2} + tap, no tokens. Opponents have no hands or libraries (S8), so their draws/discards are traced as unmodeled, not asserted.']
    def test_controller_side_of_the_symmetric_draws(self):
        g=self.bridge(); uid=self.to_hand(g,'Geier Reach Sanitarium'); gr=g.play_physical_land(uid); toss=self.to_hand(g,'Forest'); g.add_mana('C','C'); d=g.cards_drawn; h=len(g.zones.zones['hand']); n=len(g.permanents)
        g.geier_reach(gr.uid,toss); self.assertTrue(gr.tapped); g.resolve(); self.assertEqual((g.cards_drawn,len(g.zones.zones['hand']),g.zones.cards[toss].zone,len(g.permanents)),(d+1,h,'graveyard',n))
        uid=self.to_hand(g,'Mikokoro, Center of the Sea'); g.zones.land_plays_this_turn=0; mk=g.play_physical_land(uid); g.add_mana('C','C'); h=len(g.zones.zones['hand'])
        g.mikokoro(mk.uid); g.resolve(); self.assertEqual((g.cards_drawn,len(g.zones.zones['hand']),len(g.permanents)),(d+2,h+1,n+1))
        self.assertEqual(len([x for x in g.trace if x[0]=='opponent_draw_unmodeled']),3)

class C77(_Land):
    CONTRACT='C77'; ISSUES=['R40']; STATUS='EXECUTED'
    SUBSTITUTIONS=['Tower/Forest/Swamp via the physical bridge; Sol Ring via the rock fixture; Grim Backwoods {C} via S14 (2026-10-18), colourless never conflated with coloured']
    def test_tower_b_or_g_u_rejected(self):
        g=self.bridge(); p=g.play_physical_land(self.to_hand(g,'Command Tower'))
        with self.assertRaises(ZoneError): g.tap_physical_land_for_mana(p.uid,color='U')
        self.assertEqual(g.mana_pool,[]); self.assertFalse(p.tapped)
        self.assertEqual(g.tap_physical_land_for_mana(p.uid,color='B'),'B'); self.assertTrue(p.tapped)
        g.fixture_new_turn(); self.assertEqual(g.tap_physical_land_for_mana(p.uid,color='G'),'G')
        self.assertEqual(g.mana_pool,['B','G'])
    def test_forest_g_swamp_b(self):
        g=self.bridge(); f=g.play_physical_land(self.to_hand(g,'Forest'))
        self.assertEqual(g.tap_physical_land_for_mana(f.uid),'G')
        with self.assertRaises(ZoneError): g.tap_physical_land_for_mana(f.uid)           # already tapped
        g.fixture_new_turn(); s=g.play_physical_land(self.to_hand(g,'Swamp'))
        self.assertEqual(g.tap_physical_land_for_mana(s.uid),'B')
        with self.assertRaises(ZoneError): g.tap_physical_land_for_mana(s.uid,color='G')
    def test_sol_ring_cc_not_colored(self):
        g=Game(); g.add(SAVRA); r=g.add('Sol Ring'); g.resolve()
        with self.assertRaises(IllegalAction): g.tap_mana_rock(r.uid,color='B')
        self.assertEqual(g.tap_mana_rock(r.uid),('C','C')); self.assertEqual(g.mana_pool,['C','C'])
        self.assertNotIn('B',g.mana_pool); self.assertNotIn('G',g.mana_pool)
    def test_grim_backwoods_blocked(self):
        g=self.bridge(); gb=g.play_physical_land(self.to_hand(g,'Grim Backwoods'))                     # S14: {C} only
        from pab_zone_bridge import BridgeError
        with self.assertRaises(BridgeError): g.tap_physical_land_for_mana(gb.uid,color='B')
        self.assertEqual(g.tap_physical_land_for_mana(gb.uid),'C'); self.assertEqual(g.mana_pool,['C']); self.assertTrue(gb.tapped)

if __name__=='__main__':
    unittest.main()
