"""CP06: physically distinct zone for spells pending on the bounded reference stack.

Explicitly authorized compatibility migration of A-S20-03 (2026-10-18).
The v0.8 DeckZones source is FROZEN. This wrapper owns an additional physical
`stack` zone and a cast-entry postcondition. It is not a comprehensive MTG
priority/counter/copy engine. Only normal, modeled cast_from_hand spells are
migrated here; commander objects and ability-only triggers remain in ledgers.
"""
from __future__ import annotations
from collections import deque
from pab_zones import DeckZones, ZoneError
from pab_zone_bridge import BridgeError

STACK_ZONE = 'stack'

class StackEnabledZones(DeckZones):
    """Versioned physical zones: same UIDs, a new stack-zone index.

    All existing zone operations retain their semantics. Only stack-involving
    moves need custom handling, because frozen DeckZones.move checks its
    constant seven-zone enumeration.
    """
    @classmethod
    def from_existing(cls, original):
        if 'stack' in original.zones:
            raise ZoneError('CP06: source already contains a stack zone')
        instance=cls.__new__(cls)
        instance.__dict__.update(original.__dict__)
        instance.zones=dict(original.zones)
        instance.zones['stack']=[]
        instance.assert_integrity()
        return instance

    def zone_cards(self, zone):
        if zone==STACK_ZONE:
            return tuple(self.cards[uid] for uid in self.zones[STACK_ZONE])
        return super().zone_cards(zone)

    def _require_in_zone(self, uid, zone):
        if zone==STACK_ZONE:
            card=self.cards.get(uid)
            if card is None or card.zone!=STACK_ZONE or uid not in self.zones[STACK_ZONE]:
                raise ZoneError('Card UID must be in stack')
            return card
        return super()._require_in_zone(uid,zone)

    def move(self, uid, destination, *, controller=None, top=False, bottom=False):
        card=self.cards.get(uid)
        source=card.zone if card is not None else None
        if destination != STACK_ZONE and source != STACK_ZONE:
            return super().move(uid,destination,controller=controller,top=top,bottom=bottom)
        if card is None: raise ZoneError('Unknown card UID')
        if source==destination: raise ZoneError('No-op zone move forbidden')
        if destination not in self.zones: raise ZoneError('Unknown destination')
        if destination==STACK_ZONE and source!='hand':
            raise ZoneError('CP06: only a card in hand may be cast onto the stack')
        if destination==STACK_ZONE and (card.token or card.is_land):
            raise ZoneError('CP06: no tokens or lands may be cast as spells')
        if source==STACK_ZONE and destination not in ('battlefield','graveyard','exile','hand'):
            raise ZoneError('CP06: unsupported spell stack destination')
        if top or bottom: raise ZoneError('CP06: stack moves cannot reorder a library')
        if destination=='battlefield' and controller is None:
            raise ZoneError('Controller must be specified for battlefield entry')
        if destination!='battlefield' and controller is not None:
            raise ZoneError('Nonbattlefield card has no controller')
        self.zones[source].remove(uid)
        self.zones[destination].append(uid)
        card.zone=destination
        card.controller=controller
        card.tapped=False
        self.trace.append(('zone_move',uid,card.name,source,destination))

    def assert_integrity(self):
        ids=[uid for zone in self.zones for uid in self.zones[zone]]
        if len(ids)!=len(set(ids)) or set(ids)!=set(self.cards):
            raise AssertionError('CP06: missing or duplicated physical card identity')
        for zone, uids in self.zones.items():
            for uid in uids:
                c=self.cards[uid]
                if c.zone!=zone:
                    raise AssertionError('CP06: physical zone label disagreement')
                if (c.controller is not None)!=(zone=='battlefield'):
                    raise AssertionError('CP06: controller only on battlefield')
                if zone==STACK_ZONE and (c.is_land or c.token):
                    raise AssertionError('CP06: invalid physical spell on stack')
        return True

class PhysicalStackCP06Mixin:
    """Outer public casting wrapper: preflight, pay, queue, THEN move hand->stack.

    Existing S6-S20 casting callbacks execute during super().cast_from_hand().
    They remain unchanged and receive the same physical UID. No opportunity for
    other player actions is exposed before the postcondition is established.
    """
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        if not isinstance(self.zones,StackEnabledZones):
            self.zones=StackEnabledZones.from_existing(self.zones)
        self.cp06_stack_enabled=True
        self.assert_bridge_integrity()

    def cast_from_hand(self,physical_uid,**kw):
        card=self.zones.cards.get(physical_uid)
        if card is not None and (card.token or card.zone=='outside_game' or physical_uid in self.stack_cards):
            raise BridgeError('CP06: token or spell already on stack is not castable')
        if card is None or card.zone!='hand':
            self.zones._require_in_zone(physical_uid,'hand')
        # The parent may refuse before spending resources; it also enqueues
        # the resolution callbacks and the usual cast/Magecraft event traces.
        before={id(trigger) for trigger in self.pending}
        self._cp06_cast_ongoing=True
        try:
            result=super().cast_from_hand(physical_uid,**kw)
        finally:
            self._cp06_cast_ongoing=False
        if physical_uid not in self.stack_cards:
            raise AssertionError('CP06: successful cast must enter the spell ledger')
        # Place the newly cast spell and its generated triggers above the
        # already-pending stack objects. Preserve the frozen kernel's ordering
        # among the new cost/cast triggers and this spell's resolution actions.
        pending=list(self.pending)
        new=[trigger for trigger in pending if id(trigger) not in before]
        old=[trigger for trigger in pending if id(trigger) in before]
        if not new:
            raise AssertionError('CP06: cast did not queue any resolution object')
        self.pending=deque(new+old)
        self.zones.move(physical_uid,STACK_ZONE)
        self.trace.append(('physical_spell_entered_stack',physical_uid,card.name))
        self.assert_bridge_integrity()
        return result

    def assert_bridge_integrity(self):
        # S6's versioned ledger check runs through super(), then enforce the
        # stronger CP06 invariant: ledgers and stack-zone UID sets agree exactly.
        result=super().assert_bridge_integrity()
        if getattr(self,'cp06_stack_enabled',False) and not getattr(self,'_cp06_cast_ongoing',False):
            if set(self.stack_cards)!=set(self.zones.zones[STACK_ZONE]):
                raise AssertionError('CP06: physical stack and ledger UID sets differ')
        return result
