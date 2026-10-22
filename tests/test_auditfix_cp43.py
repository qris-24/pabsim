"""CP43 (Stage B ledger: A-S20-05 and the open-queue keyword lists).

A-S20-05  under block_policy 'all' a defending seat's blockers coordinate against menace (CR 702.110b): a blocker
          takes a menace attacker when another untapped blocker of that seat is still to come, which then joins it.
          Before, a menace attacker was never blocked. check_invariants_s17 now refuses a lone blocker on a menace
          attacker.
Keywords  FLYING_NAMES, MENACE_NAMES, DEATHTOUCH_NAMES, HASTE_NAMES, CANT_BLOCK_NAMES are read from the pinned card
          data for the old-baseline creatures (pab_keywords_cp43.py) instead of being hand-written; same contents.
"""
import sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pab_focus_engine import SAVRA, PEST
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
import pab_combat_s17 as s17
import pab_keywords_cp43 as kw
from pab_combat_s17 import check_invariants_s17, run_turns_full
from pab_opponents_s8 import OPPONENT_SEATS
from pab_turn_loop import opening_hand

ROOT=Path(__file__).resolve().parent.parent
BEAR={'name':'Bear','power':2,'toughness':2,'mana_value':2}; WALL={'name':'Wall','power':0,'toughness':4,'mana_value':3}
def trace(g,key): return [t for t in g.trace if t[0]==key]

class _B(unittest.TestCase):
    def game(self,*names,board=(BEAR,WALL)):
        g=PhysicalZoneGame(block_policy='all')
        for n in names: g.add(n)
        g.resolve()
        for s in OPPONENT_SEATS: g.declare_opponent_board(s,list(board))
        g.advance_to('precombat_main',active_player=0); g.add_mana('B','G','C','C'); g.cast_commander(); g.resolve(); check_invariants_s17(g)
        return g
    def savra(self,g): return next(p for p in g.permanents.values() if p.name==SAVRA)
    def attack(self,g,*uids):
        g.advance_to('cleanup',active_player=0); g.advance_to('declare_attackers',active_player=0); g.resolve()
        g.declare_attackers([(u,1) for u in uids]); g.resolve(); g.advance_to('declare_blockers',active_player=0); check_invariants_s17(g)
    def opp(self,g,name): return next(q.uid for q in g.opponent_creatures(1) if q.name==name)

class Version(unittest.TestCase):
    def test_kernel_promoted(self):
        self.assertIn('CP43',PROMOTED); self.assertIn('+CP43',KERNEL_VERSION)

class MenaceBlocks(_B):
    def test_two_blockers_double_block_a_lone_menace_attacker(self):
        g=self.game('Blight Mound'); pe=g.make_tokens(PEST)[0]; g.resolve(); self.attack(g,pe.uid)
        self.assertEqual(g.blocks,{pe.uid:[self.opp(g,'Bear'),self.opp(g,'Wall')]})
        g.advance_to('combat_damage',active_player=0); g.resolve(); check_invariants_s17(g)
        self.assertNotIn(pe.uid,g.permanents); self.assertEqual(g.life[1],40)                        # 2/1 Pest blocked by Bear and Wall
    def test_a_single_blocker_never_takes_a_menace_attacker(self):
        g=self.game('Blight Mound',board=(BEAR,)); pe=g.make_tokens(PEST)[0]; g.resolve(); sv=self.savra(g); self.attack(g,pe.uid,sv.uid)
        self.assertEqual(g.blocks,{sv.uid:[self.opp(g,'Bear')]})                                     # the lone Bear blocks Savra, not the menace Pest
        g2=self.game('Blight Mound',board=(BEAR,)); p2=g2.make_tokens(PEST)[0]; g2.resolve(); self.attack(g2,p2.uid)
        self.assertEqual(g2.blocks,{})                                                               # nothing else to block: no block
    def test_intrinsic_menace_is_double_blocked_too(self):
        g=self.game("Teacher's Pest"); tp=next(p for p in g.permanents.values() if p.name=="Teacher's Pest"); self.attack(g,tp.uid)
        self.assertEqual(g.blocks,{tp.uid:[self.opp(g,'Bear'),self.opp(g,'Wall')]})
    def test_invariant_refuses_a_lone_blocker_on_a_menace_attacker(self):
        g=self.game('Blight Mound'); pe=g.make_tokens(PEST)[0]; g.resolve(); self.attack(g,pe.uid)
        g.blocks={pe.uid:[self.opp(g,'Bear')]}
        with self.assertRaisesRegex(AssertionError,'a menace attacker has a lone blocker'): check_invariants_s17(g)
    def test_whole_games_double_block_menace_and_keep_invariants(self):
        doubles=0
        for seed in (0,1,2,3,4,7,11,42):
            with self.subTest(seed=seed):
                g=PhysicalZoneGame(seed=seed,learn_sideboard_allowed=True,block_policy='all'); opening_hand(g)
                for s in OPPONENT_SEATS: g.declare_opponent_board(s,[BEAR,WALL])
                orig=g._declare_blocks
                def record(g=g,orig=orig):
                    nonlocal doubles; orig(); doubles+=sum(1 for a,bs in g.blocks.items() if g._menace(g.permanents[a]) and len(bs)>=2)
                g._declare_blocks=record
                run_turns_full(g,40)                                                                  # the driver checks invariants every step
        self.assertGreater(doubles,0)

class Keywords(unittest.TestCase):
    PINNED={'flying':{'Beledros Witherbloom','Mirkwood Bats',"Moseo, Vein's New Dean",'Sangromancer','Starscape Cleric'},
            'menace':{'Sedgemoor Witch',"Teacher's Pest"},'deathtouch':{'Poison-Tip Archer','South Wind Avatar'},
            'haste':{'Yahenni, Undying Partisan'},'cant_block':{'Carrion Feeder','Starscape Cleric'}}
    def test_lists_come_from_the_card_data_and_equal_the_old_lists(self):
        self.assertEqual(kw.KEYWORDS,self.PINNED)
        for k,v in (('flying',s17.FLYING_NAMES),('menace',s17.MENACE_NAMES),('deathtouch',s17.DEATHTOUCH_NAMES),('haste',s17.HASTE_NAMES),('cant_block',s17.CANT_BLOCK_NAMES)):
            self.assertIs(v,kw.KEYWORDS[k])
    def test_rules_of_the_reader(self):
        c=lambda name,kws,text:{'name':name,'keywords':kws,'oracle_text':text,'type_line':'Creature'}
        out=kw.keyword_names([c('A',['Flying'],''),c('B',[],"This creature can't block."),c('Cee',[],"Cee can't block."),
                              c('D',[],"Target creature can't block this turn."),c('E',['Menace','Haste'],''),c('F',['Deathtouch'],'')])
        self.assertEqual(out,{'flying':{'A'},'menace':{'E'},'deathtouch':{'F'},'haste':{'E'},'cant_block':{'B','Cee'}})
    def test_reader_follows_the_data_and_fails_closed(self):
        data=json.loads(kw.CARD_DATA.read_text(encoding='utf-8'))
        for c in data['cards']:
            if c['name']=='Carrion Feeder': c['keywords']=c['keywords']+['Flying']
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'cards.json'; p.write_text(json.dumps(data),encoding='utf-8')
            self.assertIn('Carrion Feeder',kw.keyword_names(kw.deck_creatures(card_data=p))['flying'])
            data['cards']=[c for c in data['cards'] if c['name']!='Carrion Feeder']; p.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,"deck cards missing from the card data: \\['Carrion Feeder'\\]"): kw.deck_creatures(card_data=p)

if __name__=='__main__': unittest.main()
