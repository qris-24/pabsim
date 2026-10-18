"""Phase 8: additional bounded bridges, not a legal Commander engine.

Provides a SHARED mana symbol list for the bridge's provisional Forest/Swamp/
Command Tower and already limited rock paths. Mirrors event-kernel-created tokens
into physical zone token UIDs which cease on leave, preserving event-kernel death
triggers. Physical token and linked non-token map sets must remain disjoint.

Only use these explicit fixture APIs. Most land names, activation/priority rules,
actual token ownership under control changes, SBA timing and opponent objects remain
outside the reference kernel. This is not a whole-board implementation.
"""
from __future__ import annotations
from pab_zone_bridge import PhysicalZoneGame as Phase7Game, BridgeError
from pab_zones import ZoneError

class PhysicalZoneGame(Phase7Game):
    def __init__(self, *, seed=0, zones=None, **kwargs):
        super().__init__(seed=seed,zones=zones,**kwargs)
        # One shared reference pool, instead of the phase 7 independent copies.
        # Direct pool replacement by callers is invalid and caught by integrity.
        self.mana_pool=self.zones.mana_pool
        self.linked_tokens: dict[int,int] = {}  # Game token event UID -> physical token UID

    def pay_mana(self, *, black=0, green=0, generic=0):
        # Old pay_mana atomically replaces the list after it validates costs.
        super().pay_mana(black=black,green=green,generic=generic)
        self.zones.mana_pool=self.mana_pool  # reshare reference after replacement

    def make_tokens(self, kind, count=1, *, controller=0):
        """Mirror the exact expanded event token batch (incl. Chatterfang)."""
        produced=super().make_tokens(kind,count,controller=controller)
        for event_token in produced:
            physical=self.zones.create_battlefield_token(event_token.name,
                                                         controller=event_token.controller)
            self.linked_tokens[event_token.uid]=physical.uid
            self.trace.append(('physical_token_created',event_token.uid,physical.uid,
                               event_token.token.label,event_token.token.colors))
        self.assert_bridge_integrity()
        return produced

    def _leave(self, uid, *, sacrificed):
        """A token dies/changes zones in the event kernel, then ceases physically."""
        token_uid=self.linked_tokens.get(uid)
        if token_uid is not None:
            token=self.zones._require_in_zone(token_uid,'battlefield')
            if not token.token: raise BridgeError('Token link points to nontoken card')
            event=self.permanents.get(uid)
            if event is None or event.token is None or event.name!=token.name:
                raise BridgeError('Token event identity not found')
        departed=super()._leave(uid,sacrificed=sacrificed)
        if token_uid is not None:
            self.zones.move(token_uid,'graveyard') # card immediately ceases to exist
            del self.linked_tokens[uid]
            self.trace.append(('physical_token_ceased',uid,token_uid,sacrificed))
        self.assert_bridge_integrity()
        return departed

    def play_physical_land(self, physical_uid, *, main_phase=True, stack_empty=True):
        """Physical land play; only Forest, Swamp, Command Tower provisionally."""
        card=self.zones.play_land(physical_uid,main_phase=main_phase,
                                  stack_empty=stack_empty)
        p=self.add(card.name,colors='',creature=False,artifact=False,tapped=card.tapped)
        self.linked_battlefield[p.uid]=card.uid
        self.trace.append(('physical_land_played',p.uid,card.uid,card.name))
        self.assert_bridge_integrity()
        return p

    def tap_physical_land_for_mana(self,event_uid,*,color=None):
        """Uses DeckZones' three provisionally supported mana abilities only."""
        p=self.permanents.get(event_uid)
        physical_uid=self.linked_battlefield.get(event_uid)
        if p is None or physical_uid is None:
            raise BridgeError('Must use an explicitly linked physical land')
        card=self.zones._require_in_zone(physical_uid,'battlefield')
        if not card.is_land or p.name!=card.name or p.tapped!=card.tapped:
            raise BridgeError('Land is not a coherent linked land')
        mana=self.zones.tap_land_for_mana(physical_uid,color=color)
        p.tapped=True
        # zones.tap_land_for_mana appended into THE SAME Game.mana_pool object.
        self.trace.append(('physical_land_mana',event_uid,physical_uid,mana))
        self.assert_bridge_integrity()
        return mana

    def fixture_new_turn(self):
        """Explicit opt-in untap/count reset for linked cards only, not a full turn."""
        self.reset_turn()
        self.zones.new_turn()
        for event_uid,physical_uid in self.linked_battlefield.items():
            self.permanents[event_uid].tapped=self.zones.cards[physical_uid].tapped
        self.trace.append(('phase8_linked_turn_refresh',))
        self.assert_bridge_integrity()

    def assert_bridge_integrity(self):
        # Game may call this during initialization of Phase7Game, so guard new
        # fields until constructed. Other inherited invariants still execute.
        super().assert_bridge_integrity()
        if not hasattr(self,'linked_tokens'): return True
        if self.mana_pool is not self.zones.mana_pool:
            raise AssertionError('Mana pools no longer share a single list')
        if any(c not in ('W','U','B','R','G','C') for c in self.mana_pool):
            raise AssertionError('Unrecognized mana symbol in shared pool')
        all_linked = set(self.linked_battlefield.values()) | set(self.linked_graveyard.values())
        if len(self.linked_tokens)!=len(set(self.linked_tokens.values())):
            raise AssertionError('Multiple event tokens linked to one physical token')
        if all_linked.intersection(self.linked_tokens.values()):
            raise AssertionError('Token physical UID also linked to nontoken event')
        for event_uid,physical_uid in self.linked_tokens.items():
            p=self.permanents.get(event_uid)
            c=self.zones.cards.get(physical_uid)
            if not p or not p.token or not c or not c.token:
                raise AssertionError('Broken token link')
            if c.zone!='battlefield' or p.name!=c.name or p.controller!=c.controller:
                raise AssertionError('Token game/zone identity mismatch')
            if p.tapped != c.tapped:
                raise AssertionError('Token tapped states disagree')
        return True
