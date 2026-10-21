"""Stage S7 (Task 1b, authorized sequence of 2026-10-18): creature spells from the physical hand.

Layered above pab_cast_s6.CastMixin. Extends cast_from_hand() on PhysicalZoneGame to the
28 creature names in pab_focus_engine.BODIES minus NONCREATURE minus Savra, each with its
printed mana cost, power, toughness and colors (EVIDENCE/S7_CARD_EVIDENCE.json: the
project's Scryfall bulk-export card JSON; not Wizards' official feed). The five S6 names
keep the S6 procedure unchanged; every other name still fails closed. No frozen file edited.

Casting (CR 601.2, reduced to what the kernel models): same preflight/timing as S6
(hand, not already on the stack ledger, controller's main phase, empty stack, priority),
mana paid from the shared pool, 'cast' event after costs. Creatures are not instants or
sorceries, so Magecraft (Sedgemoor Witch) does not trigger. No additional sacrifice cost:
sacrifice_uid / selected_land_uid are refused for every S7 name.

Resolution (CR 608.3): the card moves hand -> battlefield and enters through the frozen
kernel's add() + linked_battlefield path, exactly as S6 does for Sakura-Tribe Elder, so
enters-the-battlefield behaviour is the frozen kernel's: Moseo's Pest, Innkeeper's
Treasure (add()), and the 'another creature enters' lifegain of Essence Warden,
Prosperous Innkeeper and Bogwater Lumaret (_enter_creature_triggers), plus Chatterfang's
token replacement and Mirkwood Bats on those tokens (make_tokens).

Devour (CR 702.82, Ribtruss Roaster only): "as this creature enters, you may sacrifice any
number of creatures; it enters with that many +1/+1 counters" (devour 1). The choice is
made as it enters, so cast_from_hand(..., devour_uids=[...]) records an intended choice;
at resolution each uid that is still a controlled creature is sacrificed through the
frozen sacrifice() (Savra / death triggers enqueue there) BEFORE the Roaster is added with
counters=len(devoured); uids that left the battlefield in the meantime are dropped and
traced, not refused. Default devour is zero, a legal choice. devour_uids is refused for
every other name.

Not modeled (fail closed or documented): Starscape Cleric's optional Offspring {2}{B}
(cast only for its printed cost; a token copy is never made); the legend rule for a second
copy of a legendary creature (CR 704.5j; singleton deck, no copy effect in the kernel);
keywords with no kernel semantics (flying, menace, ward, haste, deathtouch, reach,
forestwalk, protection, can't block); summoning sickness; combat. (Later layers: S17 adds
combat, summoning sickness, haste and deathtouch; CP37 adds flying, menace and can't block.)
"""
from __future__ import annotations
from pab_cast_s6 import CastMixin, CASTABLE as CASTABLE_S6, check_invariants_s6, _fodder, _tap_for
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger, BODIES, NONCREATURE, SAVRA
import pab_turn_loop as _loop

# name -> (black, green, generic) from the printed mana cost; power, toughness, colors.
# Checked symbol-by-symbol against EVIDENCE/S7_CARD_EVIDENCE.json by tests/test_cast_s7.py.
CREATURES={
  'Dina, Soul Steeper':            {'cost':(1,1,0),'power':1,'toughness':3,'colors':'BG'},
  'Mirkwood Bats':                 {'cost':(1,0,3),'power':2,'toughness':3,'colors':'B'},
  'Pest Rescuer':                  {'cost':(0,1,2),'power':2,'toughness':2,'colors':'G'},
  'Chatterfang, Squirrel General': {'cost':(0,1,2),'power':3,'toughness':3,'colors':'G'},
  "Moseo, Vein's New Dean":        {'cost':(1,0,2),'power':2,'toughness':1,'colors':'B'},
  'Reassembling Skeleton':         {'cost':(1,0,1),'power':1,'toughness':1,'colors':'B'},
  "Teacher's Pest":                {'cost':(1,1,0),'power':1,'toughness':1,'colors':'BG'},
  'Infestation Sage':              {'cost':(1,0,0),'power':1,'toughness':1,'colors':'B'},
  'Wriggling Grub':                {'cost':(1,0,1),'power':1,'toughness':1,'colors':'B'},
  'Sedgemoor Witch':               {'cost':(1,0,2),'power':3,'toughness':2,'colors':'B'},
  'Beledros Witherbloom':          {'cost':(1,1,5),'power':4,'toughness':4,'colors':'BG'},
  'Ribtruss Roaster':              {'cost':(0,1,4),'power':3,'toughness':3,'colors':'G','devour':1},
  'South Wind Avatar':             {'cost':(1,0,3),'power':3,'toughness':4,'colors':'B'},
  'Deathgreeter':                  {'cost':(1,0,0),'power':1,'toughness':1,'colors':'B'},
  'Blood Artist':                  {'cost':(1,0,1),'power':0,'toughness':1,'colors':'B'},
  'Poison-Tip Archer':             {'cost':(1,1,2),'power':2,'toughness':3,'colors':'BG'},
  'Marauding Blight-Priest':       {'cost':(1,0,2),'power':3,'toughness':2,'colors':'B'},
  'Starscape Cleric':              {'cost':(1,0,1),'power':2,'toughness':1,'colors':'B'},   # Offspring {2}{B} not modeled
  'Prosperous Innkeeper':          {'cost':(0,1,1),'power':1,'toughness':1,'colors':'G'},
  'Essence Warden':                {'cost':(0,1,0),'power':1,'toughness':1,'colors':'G'},
  'Warren Soultrader':             {'cost':(1,0,2),'power':3,'toughness':3,'colors':'B'},
  'Carrion Feeder':                {'cost':(1,0,0),'power':1,'toughness':1,'colors':'B'},
  'Viscera Seer':                  {'cost':(1,0,0),'power':1,'toughness':1,'colors':'B'},
  'Bogwater Lumaret':              {'cost':(1,1,0),'power':2,'toughness':2,'colors':'BG'},
  'Sangromancer':                  {'cost':(2,0,2),'power':3,'toughness':3,'colors':'B'},
  'Yawgmoth, Thran Physician':     {'cost':(2,0,2),'power':2,'toughness':4,'colors':'B'},
  'Yahenni, Undying Partisan':     {'cost':(1,0,2),'power':2,'toughness':2,'colors':'B'},
  'Sakura-Tribe Elder':            {'cost':(0,1,1),'power':1,'toughness':1,'colors':'G'},   # cast by the S6 procedure
}
for _n,_s in CREATURES.items():
    _s['kind']='creature'; _s['mana_value']=sum(_s['cost']); _s['additional']=None; _s.setdefault('devour',0)
    assert _n in BODIES and _n not in NONCREATURE and _n!=SAVRA and BODIES[_n]==_s['colors'], _n
assert set(CREATURES)=={n for n in BODIES if n not in NONCREATURE and n!=SAVRA}
S7_NAMES=frozenset(n for n in CREATURES if n not in CASTABLE_S6)      # the 27 new names
CASTABLE={**CASTABLE_S6,**{n:CREATURES[n] for n in S7_NAMES}}          # everything cast_from_hand accepts after S7

class CreatureCastMixin(CastMixin):
    def cast_from_hand(self,physical_uid,*,devour_uids=None,**kw):
        card=self.zones.cards.get(physical_uid)
        if card is not None and not card.token and card.name in S7_NAMES:
            return self._cast_creature_s7(physical_uid,card,devour_uids=devour_uids,**kw)
        if devour_uids is not None:
            raise BridgeError('S7: devour_uids is only accepted for Ribtruss Roaster')
        return super().cast_from_hand(physical_uid,**kw)

    def _preflight_devour(self,spec,devour_uids):
        if devour_uids is None: return ()
        if not spec['devour']: raise BridgeError('S7: this creature has no devour')
        uids=tuple(devour_uids)
        if len(set(uids))!=len(uids): raise BridgeError('S7: devour choices must be distinct creatures')
        for u in uids:
            p=self.permanents.get(u)
            if p is None or p.controller!=0 or not p.creature:
                raise BridgeError('S7: devour may only sacrifice creatures you control')
        return uids

    def _cast_creature_s7(self,physical_uid,card,*,devour_uids,sacrifice_uid=None,selected_land_uid=None,
                          main_phase=None,stack_empty=None,has_priority=None):
        spec=CREATURES[card.name]
        self._timing('creature',main_phase=main_phase,stack_empty=stack_empty,has_priority=has_priority)
        card,_=self._preflight_cast(physical_uid,spec,None)          # hand, ledger, mana; refuses any sacrifice_uid below
        if sacrifice_uid is not None: raise BridgeError(f'S7: {card.name} has no additional sacrifice cost')
        if selected_land_uid is not None: raise BridgeError(f'S7: {card.name} takes no land selection')
        devour=self._preflight_devour(spec,devour_uids)
        name=card.name; black,green,generic=spec['cost']
        # ---- mutation starts here (601.2a announce; 601.2g-h pay) ----
        self.stack_cards[physical_uid]=name
        self.trace.append(('cast_begin',name,physical_uid))
        self.pay_mana(black=black,green=green,generic=generic)
        self.trace.append(('cast',name))
        self.trace.append(('physical_cast',name,physical_uid,(black,green,generic),None))
        self.pending.append(Trigger(name+' resolution (S7)',
            lambda:self._resolve_creature_s7(physical_uid,name,devour)))
        self.assert_bridge_integrity()
        return card

    def _resolve_creature_s7(self,physical_uid,name,devour):
        if self.stack_cards.get(physical_uid)!=name:
            raise BridgeError('S7: resolving a creature spell that is not on the stack ledger')
        self.zones._require_in_zone(physical_uid,'stack' if getattr(self,'cp06_stack_enabled',False) else 'hand')
        spec=CREATURES[name]
        devoured=[]
        for u in devour:                                               # CR 702.82a: chosen as it enters
            p=self.permanents.get(u)
            if p is None or p.controller!=0 or not p.creature:
                self.trace.append(('devour_choice_gone',name,u)); continue
            self.sacrifice(u); devoured.append(u)
        if devour: self.trace.append(('devour',name,tuple(devoured)))
        self.zones.move(physical_uid,'battlefield',controller=0)
        del self.stack_cards[physical_uid]        # off the stack before add(): ETB make_tokens asserts bridge integrity
        p=self.add(name,colors=spec['colors'],creature=True,mana_value=spec['mana_value'],
                   power=spec['power'],toughness=spec['toughness'],counters=spec['devour']*len(devoured))
        self.linked_battlefield[p.uid]=physical_uid
        self.trace.append(('physical_creature_spell_resolved',name,physical_uid,p.uid))
        self.assert_bridge_integrity()

# ---- driver ------------------------------------------------------------------
def _affordable(g,spec):
    b,gr,gen=spec['cost']; pool=g.mana_pool
    return pool.count('B')>=b and pool.count('G')>=gr and len(pool)>=b+gr+gen

def cast_when_able(g):
    """One main-phase pass over the hand: S6 spells by the S6 rules, then creatures (devour 0).
    Returns the names cast."""
    cast=[]
    for uid in list(g.zones.zones['hand']):
        name=g.zones.cards[uid].name; spec=CASTABLE.get(name)
        if spec is None or not _affordable(g,spec): continue
        kw={}
        if name in CASTABLE_S6:
            if spec['additional'] is not None:
                f=_fodder(g)
                if f is None: continue
                kw['sacrifice_uid']=f
            if name=="Nature's Lore":
                forest=next((u for u in g.zones.zones['library'] if g.zones.cards[u].name=='Forest'),None)
                if forest is None: continue
                kw['selected_land_uid']=forest
        g.cast_from_hand(uid,**kw); check_invariants_s6(g)
        g.resolve(); check_invariants_s6(g)
        cast.append(name)
    return cast

def run_turns_casting(g,turns):
    """S6 driver shape with the S7 cast pass; ledger of (turn, land_played, mana_produced, names_cast)."""
    ledger=[]; start=g.clock.turn
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s6(g)
        if ap!=0 or st!='precombat_main': continue
        land=_loop.playable_land_in_hand(g); played=None
        if land is not None: played=g.play_physical_land(land).name; check_invariants_s6(g)
        hand=[g.zones.cards[u].name for u in g.zones.zones['hand']]
        need={'G':sum(CASTABLE[n]['cost'][1] for n in hand if n in CASTABLE)}
        mana=_tap_for(g,need)
        cast=cast_when_able(g)
        ledger.append((t,played,tuple(mana),tuple(cast)))
    return ledger
