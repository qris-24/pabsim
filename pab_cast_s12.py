"""Stage S12 (authorized 2026-10-18 11:05): noncreature permanents from the physical hand.

Layered above pab_interaction_s11.InteractionMixin (PhysicalZoneGame only). No frozen file
edited. Extends cast_from_hand() to the 15 names in pab_focus_engine.NONCREATURE — the
artifacts, enchantments, the Background and the Saga whose behaviour the frozen kernel
already models once they are on the battlefield (EVIDENCE/S12_PERMANENT_EVIDENCE.json).

Timing: an artifact or enchantment spell is cast at sorcery speed (CR 307.1 applies to
sorceries; for these permanents CR 301.1 / 303.1: main phase, empty stack, own turn) —
the S6 'sorcery' timing rule. Magecraft does not trigger (not an instant or sorcery).
Cost: printed mana cost from the shared pool; no additional costs.
Resolution (CR 608.3): hand -> battlefield through the frozen add() + linked path, so
enters-the-battlefield behaviour is the frozen kernel's: Bastion of Remembrance's Human
Soldier token, The Hunger Tide Rises' chapter I, Chatterfang/Mirkwood Bats on those tokens.
Type flags come from the frozen tables (NONCREATURE, ARTIFACT); Skullclamp enters unattached
(equip is the frozen kernel's existing activation).

Not modeled: the deck's remaining noncreature spells (next stage: Diabolic Intent, Immoral
Bargain, Plumb the Forbidden, Pest Infestation, Unearth, Hunt for Specimens, Demonic Tutor,
and the charms/commands/removal with no kernel behaviour yet), Grist, the Hunger Tide.
"""
from __future__ import annotations
from pab_interaction_s11 import InteractionMixin, check_invariants_s11
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger, NONCREATURE, ARTIFACT
import pab_cast_s7 as _s7

# name -> (black, green, generic); checked symbol-by-symbol against EVIDENCE/S12_PERMANENT_EVIDENCE.json
PERMANENTS={
  'Agent of the Iron Throne':{'cost':(1,0,2)},
  'Arcane Signet':           {'cost':(0,0,2)},
  'Bastion of Remembrance':  {'cost':(1,0,2)},
  'Blight Mound':            {'cost':(1,0,2)},
  'Cauldron of Essence':     {'cost':(1,1,1)},
  'Dark Prophecy':           {'cost':(3,0,0)},
  'Feral Appetite':          {'cost':(0,1,2)},
  'Golgari Signet':          {'cost':(0,0,2)},
  'Grave Pact':              {'cost':(3,0,1)},
  'Moldervine Reclamation':  {'cost':(1,1,3)},
  'Phyrexian Altar':         {'cost':(0,0,3)},
  'Phyrexian Reclamation':   {'cost':(1,0,0)},
  'Skullclamp':              {'cost':(0,0,1)},
  'Sol Ring':                {'cost':(0,0,1)},
  'The Hunger Tide Rises':   {'cost':(0,1,2)},
}
for _n,_s in PERMANENTS.items():
    _s['kind']='permanent'; _s['mana_value']=sum(_s['cost']); _s['additional']=None; _s['artifact']=_n in ARTIFACT
assert set(PERMANENTS)==set(NONCREATURE)
S12_NAMES=frozenset(PERMANENTS)
CASTABLE={**_s7.CASTABLE,**PERMANENTS}

class PermanentCastMixin(InteractionMixin):
    def cast_from_hand(self,physical_uid,**kw):
        card=self.zones.cards.get(physical_uid)
        if card is not None and not card.token and card.name in S12_NAMES:
            return self._cast_permanent_s12(physical_uid,card,**kw)
        return super().cast_from_hand(physical_uid,**kw)

    def _cast_permanent_s12(self,physical_uid,card,*,sacrifice_uid=None,selected_land_uid=None,devour_uids=None,
                            main_phase=None,stack_empty=None,has_priority=None):
        spec=PERMANENTS[card.name]
        self._timing('sorcery',main_phase=main_phase,stack_empty=stack_empty,has_priority=has_priority)
        card,_=self._preflight_cast(physical_uid,spec,None)
        if sacrifice_uid is not None or selected_land_uid is not None or devour_uids is not None:
            raise BridgeError(f'S12: {card.name} takes no sacrifice, land selection or devour')
        name=card.name; black,green,generic=spec['cost']
        self.stack_cards[physical_uid]=name
        self.trace.append(('cast_begin',name,physical_uid))
        self.pay_mana(black=black,green=green,generic=generic)
        self.trace.append(('cast',name))
        self.trace.append(('physical_cast',name,physical_uid,(black,green,generic),None))
        self.pending.append(Trigger(name+' resolution (S12)',lambda:self._resolve_permanent_s12(physical_uid,name)))
        self.assert_bridge_integrity()
        return card

    def _resolve_permanent_s12(self,physical_uid,name):
        if self.stack_cards.get(physical_uid)!=name: raise BridgeError('S12: resolving a permanent spell that is not on the stack ledger')
        self.zones._require_in_zone(physical_uid,'stack' if getattr(self,'cp06_stack_enabled',False) else 'hand')
        spec=PERMANENTS[name]
        self.zones.move(physical_uid,'battlefield',controller=0)
        del self.stack_cards[physical_uid]                                   # off the stack before add(): ETB make_tokens asserts integrity
        p=self.add(name,colors='',creature=False,artifact=spec['artifact'],mana_value=spec['mana_value'])
        self.linked_battlefield[p.uid]=physical_uid
        self.trace.append(('physical_permanent_spell_resolved',name,physical_uid,p.uid))
        self.assert_bridge_integrity()

# ---- driver ------------------------------------------------------------------
def cast_when_able(g):
    """S7 pass, then the noncreature permanents the pool can still pay for (hand order)."""
    cast=_s7.cast_when_able(g)
    for uid in list(g.zones.zones['hand']):
        if getattr(g,'game_lost',False): break                         # CP39: the game is over (CR 104.3a)
        name=g.zones.cards[uid].name
        if name not in S12_NAMES or not _s7._affordable(g,PERMANENTS[name]): continue
        g.cast_from_hand(uid); check_invariants_s11(g); g.resolve(); check_invariants_s11(g); cast.append(name)
    return cast

def run_turns_casting(g,turns):
    """S11 driver shape with the S12 cast pass. Ledger: (turn, land, mana, names_cast)."""
    from pab_commander_s10 import commander_need, cast_commander_when_able
    from pab_lands_s9 import tap_lands_policy, play_land_policy
    from pab_focus_engine import SAVRA
    ledger=[]; start=g.clock.turn
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s11(g)
        if ap!=0 or st!='precombat_main': continue
        u,kw=play_land_policy(g); played=None
        if u is not None: played=g.play_physical_land(u,**kw).name; g.resolve(); check_invariants_s11(g)
        mana=tap_lands_policy(g,extra=commander_need(g))
        cast=[SAVRA] if cast_commander_when_able(g) else []
        cast+=cast_when_able(g); check_invariants_s11(g)
        ledger.append((t,played,tuple(mana),tuple(cast)))
    return ledger
