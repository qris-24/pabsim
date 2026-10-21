"""CP37 (A2 Kernel 1; review items K1, K4, K9, K10, K12 in EVIDENCE/CP31d_INTEGRITY_REVIEW.md): combat and
state-based actions.

K1   lethal damage destroys (CR 704.5g/h): an indestructible creature is not destroyed (CR 702.12b); a regeneration
     shield replaces the destruction (CR 701.15a: shield used, damage removed, tapped, removed from combat);
     toughness 0 or less still kills through both (CR 704.5f). Found during CP37: a regenerated token's physical card
     was left untapped (bridge integrity failure); regeneration is now one routine for destroy() and lethal damage.
K4   one current power/toughness: Skullclamp's +1/-1 (per attached Skullclamp) counts in the state-based toughness
     check (S3 event kernel and S15), in combat (S17) and in Tend the Pests' X (S6), which also sees until-end-of-turn
     changes and Blight Mound's / Feral Appetite's +1/+0 for an attacking Pest. (South Wind Avatar's lifegain still
     reads printed toughness in a frozen file: a CP37 follow-up.)
K9   opponents' generic bodies have no flying or reach, so they cannot block an attacker with flying (CR 702.9b);
     intrinsic menace (Sedgemoor Witch, Teacher's Pest) counts like Blight Mound's.
K10  a creature that "can't block" never blocks under block_policy 'all'.
K12  21 commander damage makes the seat leave without changing its life total (CR 704.6c); the S19 life replay
     and lost-seat check follow.
The keyword name sets are checked against the pinned card data for the old baseline.
"""
import json, re, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pab_focus_engine import SAVRA, PEST, FLYING_INSECT
import pab_kernel
from pab_kernel import PhysicalZoneGame, Game, KERNEL_VERSION, PROMOTED
from pab_opponents_s8 import OPPONENT_SEATS
import pab_combat_s17 as s17
import pab_validation_s19 as s19

BEAR={'name':'Bear','power':2,'toughness':2,'mana_value':2}
WALL={'name':'Wall','power':0,'toughness':4,'mana_value':3}
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names,policy='none',board=(BEAR,)):
        g=PhysicalZoneGame(block_policy=policy)
        for n in names: g.add(n)
        g.resolve()
        for s in OPPONENT_SEATS: g.declare_opponent_board(s,list(board))
        g.advance_to('precombat_main',active_player=0); g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve()
        return g
    def savra(self,g): return next(p for p in g.permanents.values() if p.name==SAVRA)
    def named(self,g,name): return next(p for p in g.permanents.values() if p.name==name)
    def next_attack_step(self,g):
        g.advance_to('cleanup',active_player=0); g.advance_to('declare_attackers',active_player=0); g.resolve()
    def to_blocks(self,g,assignments):
        g.declare_attackers(assignments); g.resolve(); g.advance_to('declare_blockers',active_player=0); g.resolve()
    def to_damage(self,g): g.advance_to('combat_damage',active_player=0); g.resolve()
    def cast(self,g,name,*mana,**kw):
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name==name)
        g.zones.search_library(selected_uid=uid,destination='hand'); g.add_mana(*mana); g.cast_from_hand(uid,**kw); g.resolve()
    def equip(self,g,target):
        clamp=self.named(g,'Skullclamp'); g.add_mana('C'); g.equip_skullclamp(clamp.uid,target.uid); g.resolve()

class Version(_B):
    def test_kernel_promoted(self):
        self.assertIn('CP37',PROMOTED); self.assertIn('+CP37',KERNEL_VERSION)

class LethalDamage(_B):
    def test_indestructible_attacker_survives_lethal_damage(self):
        g=self.game(policy='all'); sv=self.savra(g); self.next_attack_step(g); self.to_blocks(g,[(sv.uid,1)])
        bear=g.blocks[sv.uid][0]
        self.cast(g,'Heroic Intervention','G','C'); self.assertIn(sv.uid,g.indestructible_until_eot)
        self.to_damage(g); g.resolve(); g.resolve()
        self.assertIn(sv.uid,g.permanents); self.assertNotIn(bear,g.permanents); self.assertEqual(g.damage_marked[sv.uid],2)
        self.assertEqual(trace(g,'lethal_damage_indestructible'),[('lethal_damage_indestructible',sv.uid,SAVRA)])   # once, however many checks
        g.advance_to('cleanup',active_player=0); self.assertIn(sv.uid,g.permanents); self.assertEqual(g.damage_marked,{})
    def test_indestructible_note_is_traced_once_per_turn(self):
        g=self.game(); sv=self.savra(g)
        for _ in range(2):
            g.advance_to('precombat_main',active_player=0); g.indestructible_until_eot.add(sv.uid); g.damage_marked[sv.uid]=5; g.resolve(); g.resolve()
            self.assertIn(sv.uid,g.permanents); g.advance_to('cleanup',active_player=0)
        self.assertEqual(len(trace(g,'lethal_damage_indestructible')),2)                       # once per turn: the note clears with the damage
    def test_indestructible_blocker_survives_an_opponent_attack(self):
        g=PhysicalZoneGame(block_policy='all'); g.add(SAVRA); g.resolve()
        y=g.add('Yahenni, Undying Partisan',power=2,toughness=2); g.resolve()
        for s in OPPONENT_SEATS: g.declare_opponent_board(s,[{'name':'Ogre','power':3,'toughness':3,'mana_value':3}])
        g.set_opponent_policy(1,{'attack':'all'}); g.advance_to('declare_blockers',active_player=1); g.resolve()
        g.indestructible_until_eot.add(y.uid)                                                  # the set Yahenni's own ability writes (cleared at each cleanup)
        self.assertEqual([b for bs in g.blocks.values() for b in bs],[y.uid])                 # Savra never blocks under 'all'
        g.advance_to('combat_damage',active_player=1); g.resolve()
        self.assertIn(y.uid,g.permanents); self.assertEqual(g.damage_marked[y.uid],3)
    def test_regeneration_shield_replaces_lethal_damage(self):
        g=self.game(policy='all'); sv=self.savra(g); self.next_attack_step(g); self.to_blocks(g,[(sv.uid,1)])
        self.cast(g,'Golgari Charm','B','G',mode=3); self.assertIn(sv.uid,g.regen_shields)
        self.to_damage(g)
        self.assertIn(sv.uid,g.permanents); self.assertNotIn(sv.uid,g.regen_shields)
        self.assertNotIn(sv.uid,g.damage_marked); self.assertNotIn(sv.uid,g.attackers)
        self.assertEqual(trace(g,'regenerated'),[('regenerated',sv.uid,SAVRA)]); self.assertEqual(g.commander_deaths,0)
    def test_regenerated_token_keeps_the_bridge_consistent(self):
        g=self.game(); pe=g.make_tokens(PEST)[0]; g.resolve(); g.regen_shields.add(pe.uid)
        self.assertIsNone(g.destroy(pe.uid)); self.assertIn(pe.uid,g.permanents); self.assertTrue(pe.tapped)
        self.assertTrue(g.zones.cards[g.linked_tokens[pe.uid]].tapped); g.assert_bridge_integrity()
    def test_regenerated_blocker_is_tapped_and_removed_from_combat(self):
        g=PhysicalZoneGame(block_policy='all'); g.add(SAVRA); g.resolve()
        for s in OPPONENT_SEATS: g.declare_opponent_board(s,[{'name':'Ogre','power':3,'toughness':3,'mana_value':3}])
        g.set_opponent_policy(1,{'attack':'all'})
        uid=next(u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Sedgemoor Witch')
        g.zones.search_library(selected_uid=uid,destination='hand'); g.add_mana('B','C','C'); g.cast_from_hand(uid); g.resolve()
        w=self.named(g,'Sedgemoor Witch'); self.assertIn(w.uid,g.linked_battlefield)
        g.advance_to('declare_blockers',active_player=1); g.resolve(); ogre=next(a for a,bs in g.blocks.items() if w.uid in bs)
        self.assertFalse(w.tapped); g.regen_shields.add(w.uid)                                  # Golgari Charm's shield (cleared at each cleanup)
        g.advance_to('combat_damage',active_player=1); g.resolve()
        self.assertIn(w.uid,g.permanents); self.assertTrue(w.tapped); self.assertTrue(g.zones.cards[g.linked_battlefield[w.uid]].tapped)
        self.assertNotIn(w.uid,g.blocks.get(ogre,[])); self.assertNotIn(w.uid,g.damage_marked); g.assert_bridge_integrity()
    def test_zero_toughness_kills_through_indestructible_and_shield(self):
        for protect in ('indestructible','shield'):
            with self.subTest(protect=protect):
                g=self.game(); sv=self.savra(g)
                if protect=='indestructible': g.indestructible_until_eot.add(sv.uid)
                else: g.regen_shields.add(sv.uid)
                g.damage_marked[sv.uid]=5; sv.minus_counters=2; g.resolve()
                self.assertNotIn(sv.uid,g.permanents); self.assertEqual(trace(g,'regenerated'),[]); self.assertEqual(trace(g,'lethal_damage_indestructible'),[])

class Skullclamp(_B):
    def test_equipped_power_and_toughness_in_combat(self):
        g=self.game('Skullclamp',policy='all',board=(WALL,)); sv=self.savra(g); self.equip(g,sv)
        self.assertEqual((g._power(sv),g._toughness(sv)),(3,1))
        self.next_attack_step(g); self.to_blocks(g,[(sv.uid,1)]); wall=g.blocks[sv.uid][0]; self.to_damage(g)
        self.assertIn(('creature',wall,sv.uid,3),trace(g,'combat_damage')[-1][1])
    def test_minus_counter_kills_equipped_creature(self):
        g=self.game('Skullclamp'); sv=self.savra(g); self.equip(g,sv); self.assertIn(sv.uid,g.permanents)
        sv.minus_counters=1; g.resolve()                                                      # 2/2 +1/-1 with a -1/-1 counter: toughness 0
        self.assertNotIn(sv.uid,g.permanents); self.assertIn('Skullclamp equipped death draw two',[t[1] for t in trace(g,'resolve')])
    def test_event_kernel_game_counts_skullclamp(self):
        g=Game(); g.add('Skullclamp'); c=g.add('Mirkwood Bats',toughness=2); g.resolve()
        clamp=next(p for p in g.permanents.values() if p.name=='Skullclamp'); g.add_mana('C'); g.equip_skullclamp(clamp.uid,c.uid); g.resolve()
        self.assertIn(c.uid,g.permanents); c.minus_counters=1; g.resolve(); self.assertNotIn(c.uid,g.permanents)
    def test_two_skullclamps_give_plus_two_minus_two(self):
        g=self.game('Skullclamp','Skullclamp'); sv=self.savra(g)
        for clamp in [p for p in g.permanents.values() if p.name=='Skullclamp']:
            if sv.uid in g.permanents: g.add_mana('C'); g.equip_skullclamp(clamp.uid,sv.uid); g.resolve()
        self.assertNotIn(sv.uid,g.permanents)                                                  # 2/2 with +2/-2: toughness 0
    def test_tend_the_pests_x_sees_an_attacking_pest_bonus(self):
        g=self.game('Blight Mound',board=()); pe=g.make_tokens(PEST)[0]; g.resolve(); self.next_attack_step(g); self.to_blocks(g,[(pe.uid,1)])
        self.assertEqual(g._current_power(pe),2); before=len([p for p in g.permanents.values() if p.token==PEST])
        self.cast(g,'Tend the Pests','B','G',sacrifice_uid=pe.uid)
        self.assertEqual(len([p for p in g.permanents.values() if p.token==PEST])-(before-1),2)  # X = 1 + Blight Mound's +1/+0
    def test_tend_the_pests_x_counts_skullclamp(self):
        g=self.game('Skullclamp'); sv=self.savra(g); self.equip(g,sv); before=len([p for p in g.permanents.values() if p.token==PEST])
        self.cast(g,'Tend the Pests','B','G',sacrifice_uid=sv.uid)
        self.assertEqual(len([p for p in g.permanents.values() if p.token==PEST])-before,3)      # Savra 2 +1 from Skullclamp

class Blocking(_B):
    def test_flying_attackers_cannot_be_blocked_by_generic_bodies(self):
        g=self.game("Moseo, Vein's New Dean",policy='all',board=(BEAR,WALL)); mo=self.named(g,"Moseo, Vein's New Dean")
        ins=g.make_tokens(FLYING_INSECT)[0]; pe=g.make_tokens(PEST)[0]; g.resolve(); self.next_attack_step(g)
        self.to_blocks(g,[(mo.uid,1),(ins.uid,1),(pe.uid,1)])
        self.assertNotIn(mo.uid,g.blocks); self.assertNotIn(ins.uid,g.blocks); self.assertEqual(len(g.blocks[pe.uid]),2)
        self.to_damage(g); self.assertEqual(g.life[1],40-1-1)
    def test_intrinsic_menace_is_not_blocked_by_one_creature(self):
        g=self.game('Sedgemoor Witch',"Teacher's Pest",policy='all'); w=self.named(g,'Sedgemoor Witch'); tp=self.named(g,"Teacher's Pest")
        self.next_attack_step(g); self.to_blocks(g,[(w.uid,1),(tp.uid,2)])
        self.assertEqual(g.blocks,{})
    def test_cant_block_creatures_never_block(self):
        g=PhysicalZoneGame(block_policy='all')
        for n in ('Carrion Feeder','Starscape Cleric','Deathgreeter'): g.add(n)
        g.resolve(); dg=self.named(g,'Deathgreeter')
        for s in OPPONENT_SEATS: g.declare_opponent_board(s,[BEAR,BEAR,BEAR])
        g.set_opponent_policy(1,{'attack':'all'}); g.advance_to('declare_blockers',active_player=1); g.resolve()
        self.assertEqual([b for bs in g.blocks.values() for b in bs],[dg.uid])
    def test_keyword_names_match_pinned_card_data(self):
        data=json.loads((ROOT/'decks'/'CARDSOURCE_BG_COMMANDER_20261021.json').read_text(encoding='utf-8'))
        by={c['name']:c for c in data['cards']}
        names=[m.group(1) for line in (ROOT/'upstream_frozen'/'FROZEN_PABTRV3_BASELINE.txt').read_text(encoding='utf-8').splitlines()
               for m in [re.match(r'^\s*1x\s+(.+?)\s*$',line)] if m]
        creatures=[by[n] for n in names if n in by and 'Creature' in by[n]['type_line']]
        self.assertEqual(len(creatures),30)
        kw=lambda k:{c['name'] for c in creatures if k in c['keywords']}
        self.assertEqual(kw('Flying'),set(s17.FLYING_NAMES)); self.assertEqual(kw('Menace'),set(s17.MENACE_NAMES))
        self.assertEqual(kw('Deathtouch'),set(s17.DEATHTOUCH_NAMES)); self.assertEqual(kw('Haste'),set(s17.HASTE_NAMES))
        self.assertEqual({c['name'] for c in creatures if "can't block" in c['oracle_text']},set(s17.CANT_BLOCK_NAMES))
        self.assertTrue(FLYING_INSECT.flying)

class CommanderDamage(_B):
    def test_commander_damage_loss_leaves_life_unchanged(self):
        g=self.game(board=()); sv=self.savra(g); g.commander_damage[1]=s17.COMMANDER_DAMAGE_LOSS-2
        self.next_attack_step(g); g.declare_attackers([(sv.uid,1)]); g.resolve(); self.to_damage(g)
        self.assertEqual(g.life[1],38); self.assertIn(1,g.lost_seats); self.assertEqual(g.seats_in_game(),[2,3])
        keys=[t[0] for t in g.trace]; self.assertLess(keys.index('commander_damage_loss'),keys.index('seat_leaves_game'))
        self.assertEqual(trace(g,'seat_leaves_game'),[('seat_leaves_game',1,38,())]); self.assertEqual(len(trace(g,'commander_damage_loss')),1)
        self.assertEqual(s19.life_ledger(g),list(g.life)); self.assertTrue(s19.lost_seats_ok(g))
    def test_lost_seats_ok_rejects_a_seat_that_left_without_cause(self):
        g=self.game(board=()); g.lost_seats.add(1)
        self.assertFalse(s19.lost_seats_ok(g))                                                 # life 40, no commander damage
        g.commander_damage[1]=s17.COMMANDER_DAMAGE_LOSS-1; self.assertFalse(s19.lost_seats_ok(g))
        g.commander_damage[1]=s17.COMMANDER_DAMAGE_LOSS; self.assertTrue(s19.lost_seats_ok(g))
        g.commander_damage[1]=0; g.life[1]=0; self.assertTrue(s19.lost_seats_ok(g))
    def test_s19_lost_seat_check_uses_lost_seats_ok(self):
        marker=object(); orig=s19.lost_seats_ok; s19.lost_seats_ok=lambda g: marker
        try: x=s19.validate_game(0,{**s19.DEFAULT_CONFIG,'max_turns':2})
        finally: s19.lost_seats_ok=orig
        self.assertIs(x['checks']['lost_seats_at_zero'],marker)

if __name__=='__main__': unittest.main()
