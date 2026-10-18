"""Stage S6 (Task 1a, authorized 2026-10-18): casting from the physical hand.

Layered above pab_clock_s4.TurnBasedActionsMixin. Adds, on PhysicalZoneGame only,
cast_from_hand(physical_uid, **kw) for exactly five already-modeled cards:
Village Rites, Deadly Dispute, Tend the Pests, Nature's Lore, Sakura-Tribe Elder.
Every other name fails closed (BridgeError). No frozen file is edited.

Casting procedure (CR 601.2, reduced to what the kernel models):
  601.2a the card must be in zones['hand'] and not already on the S6 stack ledger;
  601.2a timing is derived from the clock once engaged (CR 117.1a, 302.1, 304.1,
         307.1): sorcery/creature = controller's main phase, empty stack, own
         turn; instant = whenever the controller has priority (any step except
         untap and cleanup, CR 502.4 / 514.3a);
  601.2g-h mana is paid from the SHARED pool (zones.mana_pool is Game.mana_pool),
         then the additional sacrifice cost is paid via the existing sacrifice()
         path, so Savra / death triggers are enqueued by the frozen kernel exactly
         as for cast_pab_spell; the 'cast' event follows the paid costs (Magecraft).
  All refusals happen before any mutation (preflight), so a refused cast leaves
  hand, pool and board unchanged.

Resolution (CR 608.2): a Trigger appended BELOW the cost/cast triggers (same
limited-stack order the frozen kernel uses). The effect uses the existing
event-kernel primitives (_fixture_draw, make_tokens, _search_basic_at_resolution,
add + linked_battlefield); then the physical card moves hand->graveyard
(instant/sorcery, 608.2n) or hand->battlefield linked (creature, 608.3).

Stack ledger: pab_zones (frozen) has no 'stack' zone, so while a spell is on the
stack its physical card stays in zones['hand'] and is recorded in self.stack_cards
{physical_uid: name}. check_invariants_s6() requires every ledger card to be in
hand and refuses a second cast of the same card. This is a documented substitute
for a real stack zone, not a claim that the hand still contains the card.

R52 (found while building S6, NOT fixed in frozen code): the frozen
cast_pab_spell charges Village Rites {1}{B}; the printed cost is {B}
(scryfall.com card page, EVIDENCE/S6_CARD_EVIDENCE.json). S6 charges {B}. The
frozen fixture test_91 (tests/test_v04_cost_and_copy.py) pins the wrong cost on
the frozen path and is left untouched; superseding it needs approval.

Not modeled: the stack as a zone, targets (none of the five has one), spell
copies, counterspells, opponents' priority passes, X costs, alternative costs,
cost increases/reductions, mana of other colors as payment beyond the pool
symbols already allowed, Nature's Lore for nonbasic Forests (bridge subset).
"""
from __future__ import annotations
from pab_clock_s4 import TurnBasedActionsMixin, MAIN_STEPS
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger, PEST, TREASURE, SAVRA
from pab_zones import SUPPORTED_LAND_MANA
import pab_turn_loop as _loop

NO_PRIORITY_STEPS={'untap','cleanup'}

# (black, green, generic) from the printed mana cost; see EVIDENCE/S6_CARD_EVIDENCE.json
CASTABLE={
  'Village Rites':      {'kind':'instant', 'cost':(1,0,0), 'additional':'creature'},
  'Deadly Dispute':     {'kind':'instant', 'cost':(1,0,1), 'additional':'artifact_or_creature'},
  'Tend the Pests':     {'kind':'instant', 'cost':(1,1,0), 'additional':'creature'},
  "Nature's Lore":      {'kind':'sorcery', 'cost':(0,1,1), 'additional':None},
  'Sakura-Tribe Elder': {'kind':'creature','cost':(0,1,1), 'additional':None,
                         'mana_value':2,'power':1,'toughness':1,'colors':'G'},
}
SACRIFICE_SPELLS=('Village Rites','Deadly Dispute','Tend the Pests')

class CastMixin(TurnBasedActionsMixin):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.stack_cards: dict[int,str]={}        # physical uid -> card name, while on the stack

    # ---- timing -----------------------------------------------------------
    def _timing(self,kind,*,main_phase,stack_empty,has_priority):
        if self.clock_engaged:
            if main_phase is not None or stack_empty is not None or has_priority is not None:
                raise BridgeError('S6: timing is clock-derived once the clock is engaged')
            c=self.clock
            own_turn=c.is_controller_turn
            main_phase=own_turn and c.step in MAIN_STEPS
            stack_empty=not self.pending
            has_priority=c.step not in NO_PRIORITY_STEPS
        else:                                      # fixture shortcut, pre-clock behaviour
            if main_phase is None: main_phase=True
            if stack_empty is None: stack_empty=not self.pending
            if has_priority is None: has_priority=True
        if not has_priority: raise BridgeError('S6: controller does not have priority in this step')
        if kind in ('sorcery','creature') and not (main_phase and stack_empty):
            raise BridgeError(f'S6: {kind} timing requires your main phase and an empty stack')

    # ---- preflight ----------------------------------------------------------
    def _preflight_cast(self,physical_uid,spec,sacrifice_uid):
        if self.game_lost: raise BridgeError('S6: game already lost')
        card=self.zones._require_in_zone(physical_uid,'hand')
        if physical_uid in self.stack_cards: raise BridgeError('S6: card is already on the stack')
        black,green,generic=spec['cost']
        pool=self.mana_pool
        if pool.count('B')<black or pool.count('G')<green or len(pool)<black+green+generic:
            raise BridgeError(f'S6: mana unavailable for {card.name}')
        cost=None
        if spec['additional'] is not None:
            cost=self.permanents.get(sacrifice_uid)
            if cost is None or cost.controller!=0:
                raise BridgeError('S6: additional cost needs a controlled permanent')
            if spec['additional']=='creature' and not cost.creature:
                raise BridgeError('S6: additional cost must be a creature')
            if spec['additional']=='artifact_or_creature' and not (cost.creature or cost.artifact):
                raise BridgeError('S6: additional cost must be an artifact or creature')
        elif sacrifice_uid is not None:
            raise BridgeError(f'S6: {card.name} has no additional sacrifice cost')
        return card,cost

    # ---- the one public entry point ----------------------------------------
    def cast_from_hand(self,physical_uid,*,sacrifice_uid=None,selected_land_uid=None,
                       main_phase=None,stack_empty=None,has_priority=None):
        card=self.zones.cards.get(physical_uid)
        if card is None: raise BridgeError('S6: unknown physical card')
        spec=CASTABLE.get(card.name)
        if spec is None or card.token:
            raise BridgeError(f'S6: not castable from the physical hand: {card.name}')
        self._timing(spec['kind'],main_phase=main_phase,stack_empty=stack_empty,has_priority=has_priority)
        card,cost=self._preflight_cast(physical_uid,spec,sacrifice_uid)
        if card.name=="Nature's Lore": self._preflight_basic(selected_land_uid,'basic_forest')
        elif selected_land_uid is not None: raise BridgeError(f'S6: {card.name} takes no land selection')
        name=card.name; black,green,generic=spec['cost']
        # ---- mutation starts here (601.2a: announce; 601.2g-h: pay costs) ----
        self.stack_cards[physical_uid]=name
        self.trace.append(('cast_begin',name,physical_uid))
        self.pay_mana(black=black,green=green,generic=generic)
        power=None
        if cost is not None:
            power=max(0,cost.power+cost.counters-cost.minus_counters)   # LKI for Tend the Pests' X
            self.sacrifice(cost.uid)                                    # cost triggers enqueue in the frozen kernel
        self.trace.append(('cast',name))
        self.trace.append(('physical_cast',name,physical_uid,(black,green,generic),None if cost is None else cost.uid))
        self.pending.append(Trigger(name+' resolution (S6)',
            lambda:self._resolve_cast(physical_uid,name,power=power,selected_land_uid=selected_land_uid)))
        if spec['kind']!='creature': self.sedgemoor_spell_cast_or_copied()   # Magecraft: instant or sorcery only
        self.assert_bridge_integrity()
        return card

    # ---- resolution ----------------------------------------------------------
    def _resolve_cast(self,physical_uid,name,*,power,selected_land_uid):
        if self.stack_cards.get(physical_uid)!=name:
            raise BridgeError('S6: resolving a spell that is not on the stack ledger')
        self.zones._require_in_zone(physical_uid,'hand')
        if name in ('Village Rites','Deadly Dispute'): self._fixture_draw(2,name)
        if name=='Deadly Dispute': self.make_tokens(TREASURE)
        if name=='Tend the Pests': self.make_tokens(PEST,power)
        if name=="Nature's Lore":
            self._search_basic_at_resolution(selected_land_uid,filter_='basic_forest',tapped=False,source="Nature's Lore")
        if name=='Sakura-Tribe Elder':
            spec=CASTABLE[name]
            self.zones.move(physical_uid,'battlefield',controller=0)
            p=self.add(name,colors=spec['colors'],creature=True,mana_value=spec['mana_value'],
                       power=spec['power'],toughness=spec['toughness'])
            self.linked_battlefield[p.uid]=physical_uid
            del self.stack_cards[physical_uid]
            self.trace.append(('physical_creature_spell_resolved',name,physical_uid,p.uid))
        else:
            self.zones.move(physical_uid,'graveyard')
            del self.stack_cards[physical_uid]
            self.trace.append(('physical_spell_resolved',name,physical_uid))
        self.assert_bridge_integrity()

    def assert_bridge_integrity(self):
        super().assert_bridge_integrity()
        ledger=getattr(self,'stack_cards',None)
        if ledger:
            for uid,name in ledger.items():
                c=self.zones.cards.get(uid)
                if c is None or c.zone!='hand' or c.name!=name:
                    raise AssertionError('S6 stack ledger card is not the named card in hand')
        return True

# ---- invariants and driver --------------------------------------------------
def opening_hand_shuffled(g,n=_loop.OPENING_HAND):
    """CR 103.3: shuffle, then draw the opening hand. R53: pab_turn_loop.opening_hand()
    never shuffles, so every S5 seed plays the frozen decklist order; the seed only
    affects later searches. Left in S5 pending approval; S6 drivers use this."""
    g.zones.shuffle_library(); g.trace.append(('opening_shuffle_103_3',g.zones.seed))
    return _loop.opening_hand(g,n)

def check_invariants_s6(g):
    _loop.check_invariants(g)
    for uid,name in g.stack_cards.items():
        c=g.zones.cards[uid]
        if c.zone!='hand' or c.name!=name: raise _loop.InvariantError('stack ledger card not in hand')
    if g.stack_cards and not g.pending: raise _loop.InvariantError('cards on the stack ledger with nothing pending')

def _fodder(g):
    """A controlled creature the driver may sacrifice: a token, or a linked nontoken that is not Savra."""
    for p in g.permanents.values():
        if p.controller==0 and p.creature and (p.token is not None or (p.uid in g.linked_battlefield and p.name!=SAVRA)):
            return p.uid
    return None

def _tap_for(g,need):
    """Tap every untapped linked land; Command Tower produces what `need` is short of."""
    produced=[]
    for ev,ph in list(g.linked_battlefield.items()):
        p=g.permanents.get(ev); c=g.zones.cards[ph]
        if p is None or p.tapped or not c.is_land or c.name not in SUPPORTED_LAND_MANA: continue
        choices=SUPPORTED_LAND_MANA[c.name]
        color=None
        if len(choices)>1:
            pool=g.mana_pool+produced
            color='G' if pool.count('G')<need.get('G',0) else 'B'
        produced.append(g.tap_physical_land_for_mana(ev,color=color)); check_invariants_s6(g)
    return produced

def cast_when_able(g):
    """One pass over the hand in a main phase: cast each castable card the pool can pay for.
    Returns the names cast. Sacrifice spells need fodder; Nature's Lore needs a Forest in library."""
    cast=[]
    for uid in list(g.zones.zones['hand']):
        name=g.zones.cards[uid].name
        spec=CASTABLE.get(name)
        if spec is None: continue
        b,gr,gen=spec['cost']; pool=g.mana_pool
        if pool.count('B')<b or pool.count('G')<gr or len(pool)<b+gr+gen: continue
        kw={}
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
    """S5-style whole turns; in each controller precombat main: land, tap lands, cast when able.
    Returns a ledger of (turn, land_played, mana_produced, names_cast)."""
    ledger=[]; start=g.clock.turn
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s6(g)
        if ap!=0 or st!='precombat_main': continue
        land=_loop.playable_land_in_hand(g); played=None
        if land is not None: played=g.play_physical_land(land).name; check_invariants_s6(g)
        need={'G':sum(1 for u in g.zones.zones['hand'] if g.zones.cards[u].name in CASTABLE and CASTABLE[g.zones.cards[u].name]['cost'][1])}
        mana=_tap_for(g,need)
        cast=cast_when_able(g)
        ledger.append((t,played,tuple(mana),tuple(cast)))
    return ledger
