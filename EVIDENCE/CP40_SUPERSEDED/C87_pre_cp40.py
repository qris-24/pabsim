class C87(_Base):
    CONTRACT='C87'; ISSUES=['R45']; STATUS='EXECUTED_WITH_SUBSTITUTION'
    SUBSTITUTIONS=['Grisly Salvage: modeled in S15 on PhysicalZoneGame; this test keeps the stand-in: its resolution is '
                   'composed from physical-zone primitives in the fixture (top five by library order, chosen creature/land '
                   'to hand, rest to graveyard, no shuffle)']
    def is_creature_or_land(self,z,uid):
        n=z.cards[uid].name; return z.cards[uid].is_land or (n in BODIES and n not in NONCREATURE)
    def salvage(self,z,choose):
        top=list(z.zones['library'][:5]); rest=list(z.zones['library'][5:])
        chosen=next((u for u in top if choose and self.is_creature_or_land(z,u)),None)
        for u in top: z.move(u,'hand' if u==chosen else 'graveyard')
        return top,rest,chosen
    def test_top_five_one_to_hand_rest_graveyard_no_shuffle(self):
        z=DeckZones(seed=3); n0=len(z.zones['library'])
        top,rest,chosen=self.salvage(z,choose=True)
        self.assertIsNotNone(chosen)
        self.assertEqual(z.zones['hand'],[chosen]); self.assertEqual(sorted(z.zones['graveyard']),sorted(set(top)-{chosen}))
        self.assertEqual(z.zones['library'],rest); self.assertEqual(len(z.zones['library']),n0-5)
        self.assertEqual([t for t in z.trace if t[0]=='library_shuffled'],[])
    def test_none_eligible_branch_all_five_to_graveyard(self):
        z=DeckZones(seed=3)
        spells=[u for u in z.zones['library'] if not self.is_creature_or_land(z,u)][:5]
        for u in reversed(spells): z.move(u,'hand'); z.move(u,'library',top=True)   # arrange a creature/land-free top five
        top,rest,chosen=self.salvage(z,choose=True)
        self.assertIsNone(chosen); self.assertEqual(z.zones['hand'],[]); self.assertEqual(sorted(z.zones['graveyard']),sorted(top))


