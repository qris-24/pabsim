    def test_all_policy_blocks_biggest_menace_needs_two_deathtouch_kills(self):
        g=self.game('Feral Appetite','Blight Mound',policy='all'); pe=g.make_tokens(PEST)[0]; g.resolve(); sv=self.savra(g)
        self.next_attack_step(g); g.declare_attackers([(pe.uid,1),(sv.uid,1)]); g.resolve()
        g.advance_to('declare_blockers',active_player=0)
        bear=next(q.uid for q in g.opponent_creatures(1) if q.name=='Bear'); wall=next(q.uid for q in g.opponent_creatures(1) if q.name=='Wall')
        self.assertEqual(g.blocks,{sv.uid:[bear,wall]})                                               # the 3/1 menace Pest cannot be the lone block of either creature in turn; both block Savra
        self.to_damage(g); self.assertEqual(g.life[1],40-3); self.assertNotIn(sv.uid,g.permanents); self.assertNotIn(bear,g.permanents)   # Pest unblocked for 3; Savra and Bear trade
