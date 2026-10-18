"""Phase 7: bounded physical identity bridge for the frozen Savra reference kernel.

NOT a playable Magic engine. Explicitly links some (not all) Game events to
101 physical cards in DeckZones. Legacy Game can still add fixture permanents
that are *not* backed by a physical card; these must not be represented as a
fully reconciled board. Two IDs exist per bridged permanent: Game event UID and
physical card UID. A mapping preserves identity through death/reanimation.

Supported opt-in paths:
 - All Game draws normalized to _fixture_draw (v07 candidate) now remove real
   cards from DeckZones.library; no fabricated hand contents.
 - Sakura-Tribe Elder / Nature's Lore basic-land searches select at resolution
   from the real library, shuffle physically, and mirror their landed object.
 - A deliberately linked hand creature can die and be reanimated through the
   *existing* reference death/recursion event paths, with stable physical UID.
Unsupported Game.hand methods and unlinked permanents do not magically sync.
"""
from __future__ import annotations
from pab_zones import DeckZones, ZoneError
from pab_focus_engine_v07 import (Game, Trigger, IllegalAction,
                                  BODIES, NONCREATURE)

class BridgeError(IllegalAction):
    pass

class PhysicalZoneGame(Game):
    def __init__(self, *, seed=0, zones: DeckZones | None=None, **kwargs):
        super().__init__(**kwargs)
        self.zones = zones if zones is not None else DeckZones(seed=seed,learn_sideboard_allowed=self.learn_sideboard_allowed)
        if self.zones.learn_sideboard_allowed != self.learn_sideboard_allowed:
            raise BridgeError('Learn house-rule setting must match both kernels')
        self.linked_battlefield: dict[int,int] = {}  # Game UID -> physical UID
        self.linked_graveyard: dict[int,int] = {}    # departed Game UID -> physical UID
        self.unadjudicated_empty_library_draw = False

    def _fixture_draw(self, n, source):
        """Real draw transition instead of guessed counter-only draws.

        The original Game.hand is a *separate fixture list*, not an authoritative
        representation of drawn cards. Actual hand is zones.zone_cards('hand').
        Failed draws are exposed for a future SBA/loss handler, never hidden.
        """
        if not isinstance(n,int) or n<0: raise IllegalAction('Invalid draw count')
        failed_before=self.zones.failed_draws
        cards=self.zones.draw(n)
        failure=self.zones.failed_draws-failed_before
        self.cards_drawn+=len(cards)
        self.trace.append(('draw',len(cards),source))
        self.trace.append(('physical_draw',source,tuple(c.uid for c in cards),failure))
        if failure:
            self.unadjudicated_empty_library_draw=True
            self.trace.append(('unadjudicated_empty_library_draw',source,failure))
        return cards

    def _preflight_basic(self, uid, filter_):
        if uid is None: return
        card=self.zones._require_in_zone(uid,'library')
        if filter_=='basic' and not card.is_basic_land:
            raise BridgeError('Sakura-Tribe Elder may select a basic land only')
        if filter_=='basic_forest' and card.name!='Forest':
            raise BridgeError('Nature\'s Lore supported subset requires a basic Forest')

    def _search_basic_at_resolution(self, uid, *, filter_, source, tapped):
        """Resolution-time deterministic selection. The choice isn't a spell target."""
        # If the earlier candidate left library, treat as no selected candidate;
        # a different valid choice could be supplied by a future search policy.
        if uid is not None and (uid not in self.zones.cards or
                                self.zones.cards[uid].zone!='library'):
            self.trace.append(('search_candidate_no_longer_in_library',source,uid))
            uid=None
        card=self.zones.search_library(selected_uid=uid,
                                       destination='battlefield',eligible=filter_,
                                       tapped=tapped)
        if card is None:
            self.trace.append(('physical_basic_search_no_selection',source))
        else:
            p=self.add(card.name,colors='',creature=False,artifact=False,tapped=tapped)
            self.linked_battlefield[p.uid]=card.uid
            self.trace.append(('physical_basic_land_entered',p.uid,card.uid,
                               card.name,tapped,source))
        self.trace.append(('physical_library_search_shuffled',source))
        self.assert_bridge_integrity()
        return card

    def sakura_tribe_elder_physical(self, source_uid, *, selected_land_uid=None):
        """Own-color reference sacrifice activation and actual basic selection."""
        p=self.permanents.get(source_uid)
        if not p or p.name!='Sakura-Tribe Elder' or p.controller!=0 or not p.creature:
            raise BridgeError('Needs controlled Sakura-Tribe Elder')
        self._preflight_basic(selected_land_uid,'basic')
        self.sacrifice(source_uid)
        self.pending.append(Trigger('Sakura-Tribe Elder physical basic search',
             lambda:self._search_basic_at_resolution(selected_land_uid,
                  filter_='basic',tapped=True,source='Sakura-Tribe Elder')))

    def natures_lore_physical(self, *, selected_land_uid=None, sorcery_window=True):
        """Narrow physical basic-Forest-only spell; not full Nature's Lore."""
        if not sorcery_window: raise BridgeError('Nature\'s Lore sorcery window required')
        self._preflight_basic(selected_land_uid,'basic_forest')
        self.pay_mana(green=1,generic=1)
        self.trace.append(('cast',"Nature's Lore"))
        self.pending.append(Trigger("Nature's Lore physical basic Forest search",
             lambda:self._search_basic_at_resolution(selected_land_uid,
                  filter_='basic_forest',tapped=False,source="Nature's Lore")))
        self.sedgemoor_spell_cast_or_copied()

    def enter_linked_creature(self, physical_uid, *, mana_value, power=1,
                              toughness=1, colors=None):
        """Fixture enter from an actual physical hand card (NO cast/cost/priority)."""
        card=self.zones._require_in_zone(physical_uid,'hand')
        if card.name not in BODIES or card.name in NONCREATURE or card.is_land:
            raise BridgeError('Creature lacks reference definition; cannot link')
        if not isinstance(mana_value,int) or mana_value<0:
            raise BridgeError('Explicit fixture mana value required')
        if colors is None: colors=BODIES[card.name]
        self.zones.move(physical_uid,'battlefield',controller=0)
        p=self.add(card.name,colors=colors,creature=True,
                   mana_value=mana_value,power=power,toughness=toughness)
        self.linked_battlefield[p.uid]=physical_uid
        self.trace.append(('linked_creature_entered',p.uid,physical_uid))
        self.assert_bridge_integrity()
        return p

    def _leave(self,uid,*,sacrificed):
        linked=self.linked_battlefield.get(uid)
        if linked is not None:
            self.zones._require_in_zone(linked,'battlefield')
        departed=super()._leave(uid,sacrificed=sacrificed)
        if linked is not None:
            self.zones.move(linked,'graveyard')
            del self.linked_battlefield[uid]
            self.linked_graveyard[uid]=linked
            self.trace.append(('linked_creature_died',uid,linked,sacrificed))
            self.assert_bridge_integrity()
        return departed

    def _return_creature_from_graveyard(self,cand,source,*,tapped=False):
        physical_uid=self.linked_graveyard.get(cand.uid)
        if physical_uid is not None:
            self.zones._require_in_zone(physical_uid,'graveyard')
        result=super()._return_creature_from_graveyard(cand,source,tapped=tapped)
        if result is not None and physical_uid is not None:
            self.zones.move(physical_uid,'battlefield',controller=0)
            self.zones.cards[physical_uid].tapped=tapped
            del self.linked_graveyard[cand.uid]
            self.linked_battlefield[result.uid]=physical_uid
            self.trace.append(('linked_reanimated',cand.uid,result.uid,physical_uid,source))
            self.assert_bridge_integrity()
        return result

    def phyrexian_reclamation(self, uid):
        """Opt-in physical return-to-hand for a linked graveyard creature.

        Unlinked historical fixture objects use the original Game behavior.
        Mana is explicitly supplied to Game; the zones mana pool is still
        separate and must not be interpreted as synchronized land mana.
        """
        if uid not in self.linked_graveyard:
            return super().phyrexian_reclamation(uid)
        if not self.has('Phyrexian Reclamation'):
            raise BridgeError('Need Phyrexian Reclamation on battlefield')
        card=self._grave_target(uid)
        if card is None:
            raise BridgeError('Need linked creature card in graveyard')
        self.zones._require_in_zone(self.linked_graveyard[uid],'graveyard')
        if self.life[0]<2:
            raise BridgeError('Cannot pay life')
        self.pay_mana(black=1,generic=1)
        self.pay_life(2,'Phyrexian Reclamation')
        def resolve_return():
            if card not in self.graveyard:
                return
            physical_uid=self.linked_graveyard.get(uid)
            if physical_uid is None:
                raise BridgeError('Graveyard link disappeared without tracked transition')
            self.zones._require_in_zone(physical_uid,'graveyard')
            self.graveyard.remove(card)
            self.zones.move(physical_uid,'hand')
            del self.linked_graveyard[uid]
            self.trace.append(('physical_reclamation_to_hand',uid,physical_uid))
            self.assert_bridge_integrity()
        self.pending.append(Trigger('Phyrexian Reclamation physical return',resolve_return))

    def cycle_unearth(self):
        """The single frozen Unearth, moved from actual hand to graveyard.

        This is not a general cycling/stack or mana system. Unlike the old
        fixture-only method, an imaginary 'Unearth' in Game.hand is rejected.
        """
        card=next((c for c in self.zones.zone_cards('hand') if c.name=='Unearth'),None)
        if card is None:
            raise BridgeError('Unearth must be an actual card in physical hand')
        self.pay_mana(generic=2)
        self.zones.discard(card.uid)
        self.trace.append(('physical_cycle_discard',card.uid,'Unearth'))
        self.pending.append(Trigger('Unearth physical cycle draw',
                                    lambda:self._fixture_draw(1,'Unearth cycling')))

    def hunt_for_specimens(self, *, lesson=False):
        """Links opt-in house-rule Learn Lesson to actual physical card.

        Hunt's Pest remains an *event-kernel* token (token-zone integration
        is pending). The Lesson is never copied into Game.hand as a fake card.
        """
        if lesson:
            retrieved=self.zones.learn_pest_summoning()  # preflight before Pest
            self.trace.append(('physical_learn_lesson_to_hand',retrieved.uid))
        return super().hunt_for_specimens(lesson=False)

    def assert_bridge_integrity(self):
        """Reconciles exactly the subset explicitly linked, not entire Game."""
        self.zones.assert_integrity()
        all_ids=set(self.linked_battlefield.values()) | set(self.linked_graveyard.values())
        if len(all_ids)!=len(self.linked_battlefield)+len(self.linked_graveyard):
            raise AssertionError('Physical UID linked multiple times')
        for game_uid,card_uid in self.linked_battlefield.items():
            if game_uid not in self.permanents:
                raise AssertionError('Linked Game permanent missing')
            c=self.zones.cards[card_uid]
            p=self.permanents[game_uid]
            if c.zone!='battlefield' or p.name!=c.name or c.controller!=p.controller or p.tapped!=c.tapped:
                raise AssertionError('Battlefield identity mismatch')
        for game_uid,card_uid in self.linked_graveyard.items():
            if not any(p.uid==game_uid and p.name==self.zones.cards[card_uid].name for p in self.graveyard):
                raise AssertionError('Linked graveyard LKI missing')
            if self.zones.cards[card_uid].zone!='graveyard':
                raise AssertionError('Physical graveyard identity mismatch')
        return True
