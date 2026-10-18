"""Stage S14 (authorized 2026-10-18 11:05): the nine remaining nonbasic lands.

Layered above pab_cast_s13.SpellCastMixin (PhysicalZoneGame only). No frozen file edited.
Playing and tapping reuse the S9 procedure through FixerLandsMixin._land_spec(); the
activated abilities are S14's (EVIDENCE/S14_LAND_EVIDENCE.json):

  Phyrexian Tower   {T}: C.  tower_sacrifice(land_uid, creature_uid): {T}, sacrifice a creature
                    (frozen sacrifice(): Savra/death triggers enqueue), add {B}{B} — a mana
                    ability, no stack (CR 605.3b)
  High Market       {T}: C.  high_market(land_uid, creature_uid): {T}, sacrifice: gain 1 life on
                    resolution (uses the stack; the sacrifice is a cost)
  Grim Backwoods    {T}: C.  grim_backwoods(land_uid, creature_uid): {2}{B}{G}, {T}, sacrifice:
                    draw a card on resolution
  Castle Locthwain  enters tapped unless you control a Swamp (land type: Swamp, Overgrown Tomb,
                    Underground Mortuary); {T}: B.  castle_locthwain(land_uid): {1}{B}{B}, {T}:
                    draw a card, then lose life equal to the number of cards in hand — the
                    draw happens first, so the count includes the drawn card (contract C74)
  Verdant Catacombs no mana.  verdant_catacombs(land_uid, selected_uid, pay_life=False,
                    surveil_graveyard=False): {T}, pay 1 life, sacrifice this land; on
                    resolution the selected library card with the Swamp or Forest TYPE
                    (Swamp, Forest, Overgrown Tomb, Underground Mortuary) enters with its own
                    entry rule (Tomb may pay 2 life, Mortuary tapped + surveil), then shuffle.
                    The sacrificed land goes to the graveyard (no death trigger for lands)
  Boseiju, Who Endures  {T}: G.  Channel: no opponent controls an artifact, enchantment or
                    nonbasic land in this kernel, so the ability has no legal target and is
                    refused (CR 602.2b); the land itself is fully playable
  Takenuma, Abandoned Mire  {T}: B.  channel_takenuma(card_uid, return_uid=None): from hand,
                    {3}{B} less {1} per legendary creature you control, discard the card:
                    mill three, then return a creature card from the graveyard to hand (the
                    choice is made at resolution: return_uid is a pre-commitment; None or a
                    card no longer there -> the first eligible card, or nothing)
  Geier Reach Sanitarium  {T}: C.  geier_reach(land_uid, discard_uid): {2}, {T}: you draw then
                    discard the chosen card (opponents have no hands: traced unmodeled)
  Mikokoro          {T}: C.  mikokoro(land_uid): {2}, {T}: you draw (opponents traced unmodeled)

Not modeled: opponents' draws/discards from the symmetric lands, Boseiju's channel (no
targets exist), planeswalker cards for Takenuma, Grist.
"""
from __future__ import annotations
from pab_cast_s13 import SpellCastMixin, check_invariants_s11
from pab_lands_s9 import FIXERS, SWAMP_FOREST_TYPED, LAND_MANA as LAND_MANA_S9, tap_lands_policy, play_land_policy
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger, SAVRA

LANDS14={
  'Phyrexian Tower':           {'mana':('C',),'enters':'untapped'},
  'High Market':               {'mana':('C',),'enters':'untapped'},
  'Grim Backwoods':            {'mana':('C',),'enters':'untapped'},
  'Castle Locthwain':          {'mana':('B',),'enters':'tapped_unless_swamp_type'},
  'Verdant Catacombs':         {'mana':(),   'enters':'untapped'},
  'Boseiju, Who Endures':      {'mana':('G',),'enters':'untapped'},
  'Takenuma, Abandoned Mire':  {'mana':('B',),'enters':'untapped'},
  'Geier Reach Sanitarium':    {'mana':('C',),'enters':'untapped'},
  'Mikokoro, Center of the Sea':{'mana':('C',),'enters':'untapped'},
}
S14_NAMES=frozenset(LANDS14)
LAND_MANA={**LAND_MANA_S9,**{n:s['mana'] for n,s in LANDS14.items() if s['mana']}}
SWAMP_TYPED=frozenset({'Swamp','Overgrown Tomb','Underground Mortuary'})
FETCHABLE=SWAMP_FOREST_TYPED

class RemainingLandsMixin(SpellCastMixin):
    def _land_spec(self,name): return LANDS14[name] if name in LANDS14 else super()._land_spec(name)
    def _has_land_spec(self,name): return name in LANDS14 or super()._has_land_spec(name)
    def _enters_tapped(self,spec,*,pay_life):
        if spec['enters']=='tapped_unless_swamp_type':
            return not any(c.name in SWAMP_TYPED for c in self._controlled_lands())
        return super()._enters_tapped(spec,pay_life=pay_life)

    def play_physical_land(self,physical_uid,**kw):
        card=self.zones.cards.get(physical_uid)
        if card is not None and not card.token and card.name in S14_NAMES:
            return self._play_fixer(physical_uid,card,face=kw.pop('face',None),pay_life=kw.pop('pay_life',False),surveil_graveyard=kw.pop('surveil_graveyard',False),**kw)
        return super().play_physical_land(physical_uid,**kw)

    def tap_physical_land_for_mana(self,event_uid,*,color=None):
        p=self.permanents.get(event_uid)
        if p is not None and p.name=='Verdant Catacombs': raise BridgeError('S14: Verdant Catacombs has no mana ability')
        return super().tap_physical_land_for_mana(event_uid,color=color)

    # ---- helpers -------------------------------------------------------------
    def _linked_land(self,event_uid,name):
        p=self.permanents.get(event_uid); ph=self.linked_battlefield.get(event_uid)
        if p is None or ph is None or p.name!=name: raise BridgeError(f'S14: not a linked {name}')
        card=self.zones._require_in_zone(ph,'battlefield')
        if card.tapped or p.tapped: raise BridgeError(f'S14: {name} is tapped')
        return p,card
    def _own_creature(self,uid):
        c=self.permanents.get(uid)
        if c is None or c.controller!=0 or not c.creature: raise BridgeError('S14: the cost needs a creature you control')
        return c
    def _tap(self,p,card): p.tapped=True; card.tapped=True

    # ---- sacrifice lands -----------------------------------------------------
    def tower_sacrifice(self,land_uid,creature_uid):
        p,card=self._linked_land(land_uid,'Phyrexian Tower'); self._own_creature(creature_uid)
        self._tap(p,card); self.sacrifice(creature_uid)
        self.mana_pool.extend(['B','B']); self.trace.append(('mana_ability','Phyrexian Tower',creature_uid,('B','B'))); self.assert_bridge_integrity()
    def high_market(self,land_uid,creature_uid):
        p,card=self._linked_land(land_uid,'High Market'); self._own_creature(creature_uid)
        self._tap(p,card); self.sacrifice(creature_uid); self.trace.append(('activate','High Market',creature_uid))
        self.pending.append(Trigger('High Market resolution (S14)',lambda:self.gain(1,'High Market'))); self.assert_bridge_integrity()
    def grim_backwoods(self,land_uid,creature_uid):
        p,card=self._linked_land(land_uid,'Grim Backwoods'); self._own_creature(creature_uid)
        pool=self.mana_pool
        if pool.count('B')<1 or pool.count('G')<1 or len(pool)<4: raise BridgeError('S14: Grim Backwoods needs {2}{B}{G}')
        self.pay_mana(black=1,green=1,generic=2); self._tap(p,card); self.sacrifice(creature_uid); self.trace.append(('activate','Grim Backwoods',creature_uid))
        self.pending.append(Trigger('Grim Backwoods resolution (S14)',lambda:self._fixture_draw(1,'Grim Backwoods'))); self.assert_bridge_integrity()

    # ---- Castle Locthwain (C74) ----------------------------------------------
    def castle_locthwain(self,land_uid):
        p,card=self._linked_land(land_uid,'Castle Locthwain'); pool=self.mana_pool
        if pool.count('B')<2 or len(pool)<3: raise BridgeError('S14: Castle Locthwain needs {1}{B}{B}')
        self.pay_mana(black=2,generic=1); self._tap(p,card); self.trace.append(('activate','Castle Locthwain'))
        def resolve():
            before=len(self.zones.zones['hand']); self._fixture_draw(1,'Castle Locthwain'); n=len(self.zones.zones['hand'])
            self.trace.append(('castle_locthwain_hand',before,n)); self.lose_life(n,'Castle Locthwain')
        self.pending.append(Trigger('Castle Locthwain resolution (S14)',resolve)); self.assert_bridge_integrity()

    # ---- Verdant Catacombs (C70) ----------------------------------------------
    def verdant_catacombs(self,land_uid,selected_uid,*,pay_life=False,surveil_graveyard=False):
        p,card=self._linked_land(land_uid,'Verdant Catacombs')
        if selected_uid is not None and (selected_uid not in self.zones.zones['library'] or self.zones.cards[selected_uid].name not in FETCHABLE):
            raise BridgeError('S14: Verdant Catacombs fetches a Swamp or Forest card from the library')
        if self.life[0]<1: raise BridgeError('S14: cannot pay 1 life')
        self._tap(p,card); self.pay_life(1,'Verdant Catacombs')
        del self.permanents[land_uid]; del self.linked_battlefield[land_uid]
        self.zones.move(card.uid,'graveyard'); self.trace.append(('land_sacrificed',land_uid,card.uid,'Verdant Catacombs'))
        def resolve():
            uid=selected_uid
            if uid is not None and (uid not in self.zones.zones['library']): self.trace.append(('search_candidate_no_longer_in_library','Verdant Catacombs',uid)); uid=None
            if uid is None: self.trace.append(('physical_search_no_selection','Verdant Catacombs'))
            else: self._enter_fetched_land(uid,pay_life=pay_life,surveil_graveyard=surveil_graveyard)
            self.zones.shuffle_library(); self.trace.append(('search_resolved','swamp_or_forest_type','battlefield',uid))
        self.pending.append(Trigger('Verdant Catacombs resolution (S14)',resolve)); self.assert_bridge_integrity()
    def _enter_fetched_land(self,uid,*,pay_life,surveil_graveyard):
        card=self.zones.cards[uid]; spec=FIXERS.get(card.name)
        tapped=False if spec is None else self._enters_tapped(spec,pay_life=pay_life)
        self.zones.move(uid,'battlefield',controller=0); card.tapped=tapped
        p=self.add(card.name,colors='',creature=False,artifact=False,tapped=tapped)
        self.linked_battlefield[p.uid]=uid; self.trace.append(('fetched_land_entered',card.name,uid,p.uid,'tapped' if tapped else 'untapped'))
        if spec is not None and spec.get('etb')=='surveil_1':
            self._enqueue([Trigger('Underground Mortuary surveil 1',lambda:self._surveil_1(surveil_graveyard))])
        self.assert_bridge_integrity()

    # ---- Channel / symmetric draws ----------------------------------------------
    def channel_takenuma(self,card_uid,return_uid=None):
        card=self.zones._require_in_zone(card_uid,'hand')
        if card.name!='Takenuma, Abandoned Mire': raise BridgeError('S14: not Takenuma')
        if self.clock_engaged and self.clock.step in ('untap','cleanup'): raise BridgeError('S14: no priority in this step')
        legends=sum(1 for q in self.permanents.values() if q.controller==0 and q.creature and q.name in (SAVRA,'Dina, Soul Steeper','Chatterfang, Squirrel General',"Moseo, Vein's New Dean",'Beledros Witherbloom','Yawgmoth, Thran Physician','Yahenni, Undying Partisan'))
        generic=max(0,3-legends); pool=self.mana_pool
        if pool.count('B')<1 or len(pool)<1+generic: raise BridgeError(f'S14: Takenuma channel needs {{{generic}}}{{B}}')
        self.pay_mana(black=1,generic=generic); self.zones.discard(card_uid); self.trace.append(('channel','Takenuma, Abandoned Mire',card_uid,generic))
        def resolve():
            milled=self.zones.mill(3); self.trace.append(('milled',tuple(c.uid for c in milled)))
            cands=[u for u in self.zones.zones['graveyard'] if self.zones.cards[u].name in _CREATURE_NAMES]
            pick=return_uid if return_uid in cands else (cands[0] if cands else None)
            if pick is None: self.trace.append(('takenuma_no_creature_card',)); return
            ev=next((e for e,ph in self.linked_graveyard.items() if ph==pick),None)
            if ev is not None: del self.linked_graveyard[ev]; self.graveyard=[q for q in self.graveyard if q.uid!=ev]
            self.zones.move(pick,'hand'); self.trace.append(('takenuma_returned',pick,self.zones.cards[pick].name))
        self.pending.append(Trigger('Takenuma channel resolution (S14)',resolve)); self.assert_bridge_integrity()
    def boseiju_channel(self,card_uid):
        self.zones._require_in_zone(card_uid,'hand')
        raise BridgeError('S14: Boseiju channel has no legal target — no opponent controls an artifact, enchantment or nonbasic land in this kernel')
    def geier_reach(self,land_uid,discard_uid):
        p,card=self._linked_land(land_uid,'Geier Reach Sanitarium')
        if len(self.mana_pool)<2: raise BridgeError('S14: Geier Reach needs {2}')
        self.pay_mana(generic=2); self._tap(p,card); self.trace.append(('activate','Geier Reach Sanitarium'))
        def resolve():
            self._fixture_draw(1,'Geier Reach Sanitarium')
            d=discard_uid if discard_uid in self.zones.zones['hand'] else (self.zones.zones['hand'][-1] if self.zones.zones['hand'] else None)
            if d is not None: self.zones.discard(d); self.trace.append(('discard',d,'Geier Reach Sanitarium'))
            for s in self.seats_in_game(): self.trace.append(('opponent_draw_discard_unmodeled',s,'Geier Reach Sanitarium'))
        self.pending.append(Trigger('Geier Reach resolution (S14)',resolve)); self.assert_bridge_integrity()
    def mikokoro(self,land_uid):
        p,card=self._linked_land(land_uid,'Mikokoro, Center of the Sea')
        if len(self.mana_pool)<2: raise BridgeError('S14: Mikokoro needs {2}')
        self.pay_mana(generic=2); self._tap(p,card); self.trace.append(('activate','Mikokoro, Center of the Sea'))
        def resolve():
            self._fixture_draw(1,'Mikokoro, Center of the Sea')
            for s in self.seats_in_game(): self.trace.append(('opponent_draw_unmodeled',s,'Mikokoro, Center of the Sea'))
        self.pending.append(Trigger('Mikokoro resolution (S14)',resolve)); self.assert_bridge_integrity()

from pab_cast_s7 import CREATURES as _C
_CREATURE_NAMES=frozenset(_C)|{SAVRA}

# ---- driver ------------------------------------------------------------------
LAND_MANA_DRIVER={**LAND_MANA,'Verdant Catacombs':()}      # playable; never tapped by the policy

def run_turns_casting(g,turns):
    """S13 driver with all 34 lands playable (hand order; activated land abilities are not driven)."""
    import pab_cast_s13 as _s13
    from pab_commander_s10 import commander_need, cast_commander_when_able
    ledger=[]; start=g.clock.turn
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s11(g)
        if ap!=0 or st!='precombat_main': continue
        u,kw=play_land_policy(g,LAND_MANA_DRIVER); played=None
        if u is not None: played=g.play_physical_land(u,**kw).name; g.resolve(); check_invariants_s11(g)
        mana=tap_lands_policy(g,extra=commander_need(g),land_mana=LAND_MANA_DRIVER)
        cast=[SAVRA] if cast_commander_when_able(g) else []
        cast+=_s13.cast_when_able(g); check_invariants_s11(g)
        ledger.append((t,played,tuple(mana),tuple(cast)))
    return ledger
