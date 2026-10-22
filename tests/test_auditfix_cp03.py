"""Seven independent CP03 regression checks: source contract, target and combat paths."""
import json
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))   # CP42 (T6): imports work without the runner's sys.path
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION, PROMOTED
from pab_focus_engine import SAVRA
from pab_zone_bridge import BridgeError

class InfuseDeathtouch(unittest.TestCase):
    def setUp(self):
        self.g=PhysicalZoneGame(block_policy='none')

    def _infuse(self,target):
        g=self.g
        u=next(x for x in g.zones.zones['library'] if g.zones.cards[x].name=='Infuse with Vitality')
        g.zones.search_library(selected_uid=u,destination='hand')
        g.add_mana('B','G')
        g.cast_from_hand(u,target_uid=target)
        self.assertNotIn(target,g.infused_eot, 'Not active before resolution')
        g.resolve()
        self.assertIn(target,g.infused_eot)

    def test_01_metadata_and_source(self):
        data=json.loads((Path(__file__).parents[1]/'EVIDENCE'/'S15_SPELL_EVIDENCE.json').read_text())['cards']['Infuse with Vitality']
        self.assertIn('gains deathtouch',data['oracle_text'])
        self.assertIn('CP03',PROMOTED)
        self.assertIn('+CP03',KERNEL_VERSION)

    def test_02_own_target_receives_deathtouch_only_after_resolution(self):
        p=self.g.add(SAVRA)
        self.assertFalse(self.g._deathtouch(p))
        self._infuse(p.uid)
        self.assertTrue(self.g._deathtouch(p))
        self.assertEqual(self.g.life[0],42)

    def test_03_opponent_target_receives_deathtouch(self):
        b=self.g.declare_opponent_board(1,[{'name':'Bear','power':2,'toughness':2}])[0]
        self.assertFalse(self.g._deathtouch(self.g.permanents[b]))
        self._infuse(b)
        self.assertTrue(self.g._deathtouch(self.g.permanents[b]))

    def test_04_infused_attacker_lethal_to_larger_blocker(self):
        g=self.g
        p=g.add(SAVRA)
        wall=g.declare_opponent_board(1,[{'name':'Wall','power':0,'toughness':4}])[0]
        self._infuse(p.uid)
        g.attackers={p.uid:1};g.blocks={p.uid:[wall]};p.tapped=True
        g._combat_damage()
        self.assertNotIn(wall,g.permanents)
        self.assertIn(p.uid,g.permanents)
        self.assertEqual(g.life[1],40)

    def test_05_infused_opponent_attacker_lethal_to_own_larger_blocker(self):
        g=self.g
        b=g.declare_opponent_board(1,[{'name':'Bear','power':2,'toughness':2}])[0]
        own=g.add(SAVRA);own.power=0;own.toughness=4  # legal supported fixture body with benchmark stats
        self._infuse(b)
        g.attackers={b:0};g.blocks={b:[own.uid]};g.permanents[b].tapped=True
        g._combat_damage()
        self.assertNotIn(own.uid,g.permanents)
        self.assertIn(b,g.permanents)
        self.assertEqual(g.life[0],42)

    def test_06_effect_expires_during_cleanup(self):
        p=self.g.add(SAVRA)
        self._infuse(p.uid)
        self.g.advance_to('cleanup',active_player=0)
        self.assertNotIn(p.uid,self.g.infused_eot)
        self.assertFalse(self.g._deathtouch(p))

    def test_07_invalid_target_has_no_deathtouch_or_gain(self):
        g=self.g
        p=g.add(SAVRA)
        u=next(x for x in g.zones.zones['library'] if g.zones.cards[x].name=='Infuse with Vitality')
        g.zones.search_library(selected_uid=u,destination='hand');g.add_mana('B','G')
        with self.assertRaises(BridgeError): g.cast_from_hand(u,target_uid=123456789)
        self.assertFalse(g.infused_eot)
        self.assertFalse(g._deathtouch(p))
        self.assertEqual(g.life[0],40)

if __name__=='__main__': unittest.main()
