"""R52 (approved 2026-10-18): Village Rites costs {B}, not {1}{B}.

The frozen pab_focus_engine_v07.cast_pab_spell table reads
    'Village Rites':(1,0,1)   # black=1, generic=1  ->  {1}{B}
The printed cost is {B} (EVIDENCE/S6_CARD_EVIDENCE.json, scryfall.com card page,
corroborated by mtg.wtf). The frozen file is NOT edited. This mixin intercepts
cast_pab_spell('Village Rites', ...) and performs the same procedure with the
corrected cost, using the same frozen primitives in the same order (preflight,
pay_mana, sacrifice, 'cast' trace, resolution Trigger below the cost triggers,
Magecraft). Every other spell name is delegated unchanged to the frozen method.

Frozen contract test_91 (tests/test_v04_cost_and_copy.py) asserts that a pool of
['B'] is insufficient for Village Rites; against the corrected kernel it fails and
is therefore superseded (EXPECTED_LEGACY_FAILURES), exactly as R01 superseded
112/113. The corrected full copy is r52_tests/test_v04_cost_and_copy_r52.py.
"""
from __future__ import annotations
from pab_focus_engine import Trigger, IllegalAction
from pab_r01_pest_rescuer import EXPECTED_LEGACY_FAILURES as _R01_FAILURES

VILLAGE_RITES_COST=(1,0,0)        # (black, green, generic) = {B}

class VillageRitesCostMixin:
    def cast_pab_spell(self,spell,sacrifice_uid):
        if spell!='Village Rites': return super().cast_pab_spell(spell,sacrifice_uid)
        cost=self.permanents.get(sacrifice_uid)
        if not cost or cost.controller!=0 or not cost.creature:
            raise IllegalAction('Illegal controlled permanent for additional casting cost')
        black,green,generic=VILLAGE_RITES_COST
        pool=self.mana_pool
        if pool.count('B')<black or len(pool)<black+green+generic:
            raise IllegalAction('Mana unavailable for PAB spell')
        self.pay_mana(black=black,green=green,generic=generic)
        self.sacrifice(sacrifice_uid)
        self.trace.append(('cast',spell))
        self.trace.append(('r52_village_rites_cost',VILLAGE_RITES_COST))
        self.pending.append(Trigger(spell+' resolution',lambda:self._fixture_draw(2,spell)))
        self.sedgemoor_spell_cast_or_copied()
        return cost

EXPECTED_LEGACY_FAILURES=set(_R01_FAILURES)|{'test_91_village_rejects_mana_shortage_before_sac'}
