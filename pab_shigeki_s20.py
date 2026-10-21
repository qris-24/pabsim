"""Stage S20 (authorized 2026-10-18 11:05; "pause at 20"): Shigeki, Jukai Visionary, and the
per-card model-coverage registry (build_model_coverage_s20.py).

Found while building the registry: Shigeki, Jukai Visionary (Legendary Enchantment Creature —
Snake Druid, {1}{G}, 1/3) is in the deck but in none of the frozen tables (BODIES), so S7's
"every creature in BODIES" rule skipped it; the S15/S16 notes' "every nonland card" claim was
therefore one card short. Corrected here. Layered above pab_policy_s18.PolicyOpponentsMixin.

Modeled: cast from the physical hand as a 1/3 green enchantment creature (sorcery timing,
printed cost, linked body); it attacks, blocks, dies and returns like any creature; its
enchantment type makes it a legal Golgari Charm mode-2 / Pest Infestation target (S15/S13
ENCHANTMENTS lists extended through _tgt below).
  shigeki_activate(uid, land_uid=None): {1}{G}, {T}, return Shigeki to hand: reveal the top
      four cards of the library, may put a land card from among them onto the battlefield
      tapped (land_uid pre-commits the choice; None -> the first land among them, or none),
      the rest to the graveyard (a library shorter than four reveals what there is)
  channel_shigeki(card_uid, targets): {X}{X}{G}{G}, discard: return X target nonlegendary
      cards from your graveyard to hand (X = len(targets); legendary cards refused; event
      LKI and graveyard links dropped for returned cards)
Not modeled: the summoning-sickness interaction of the tap ability is enforced (it taps:
cannot be activated the turn it entered, CR 302.6).
"""
from __future__ import annotations
from pab_policy_s18 import PolicyOpponentsMixin, check_invariants_s18
from pab_cast_s15 import CASTABLE as CASTABLE_S15, ENCHANTMENTS as ENCH15
from pab_grist_s16 import CASTABLE as CASTABLE_S16
from pab_combat_s17 import HASTE_NAMES
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger

SHIGEKI='Shigeki, Jukai Visionary'
SHIGEKI_SPEC={'kind':'creature','cost':(0,1,1),'additional':None,'mana_value':2,'power':1,'toughness':3,'colors':'G','enchantment':True}
CASTABLE={**CASTABLE_S16,SHIGEKI:SHIGEKI_SPEC}
LEGENDARY_CARDS={'Savra, Queen of the Golgari','Dina, Soul Steeper','Chatterfang, Squirrel General',"Moseo, Vein's New Dean",'Beledros Witherbloom','Yawgmoth, Thran Physician','Yahenni, Undying Partisan','Agent of the Iron Throne','Grist, the Hunger Tide',SHIGEKI,'Boseiju, Who Endures','Takenuma, Abandoned Mire','Geier Reach Sanitarium','Mikokoro, Center of the Sea','Phyrexian Tower'}

class ShigekiMixin(PolicyOpponentsMixin):
    def cast_from_hand(self,physical_uid,**kw):
        card=self.zones.cards.get(physical_uid)
        if card is not None and not card.token and card.name==SHIGEKI:
            for k,v in kw.items():
                if k not in ('main_phase','stack_empty','has_priority') and v is not None: raise BridgeError(f'S20: Shigeki takes no {k}')
            self._timing('creature',main_phase=kw.get('main_phase'),stack_empty=kw.get('stack_empty'),has_priority=kw.get('has_priority'))
            self._preflight_cast(physical_uid,SHIGEKI_SPEC,None)
            self.stack_cards[physical_uid]=SHIGEKI; self.trace.append(('cast_begin',SHIGEKI,physical_uid)); self.pay_mana(green=1,generic=1)
            self.trace.append(('cast',SHIGEKI)); self.trace.append(('physical_cast',SHIGEKI,physical_uid,(0,1,1),None))
            self.pending.append(Trigger(SHIGEKI+' resolution (S20)',lambda:self._shigeki_enters(physical_uid))); self.assert_bridge_integrity(); return card
        return super().cast_from_hand(physical_uid,**kw)
    def _shigeki_enters(self,physical_uid):
        if self.stack_cards.get(physical_uid)!=SHIGEKI: raise BridgeError('S20: not on the ledger')
        self.zones._require_in_zone(physical_uid,'stack' if getattr(self,'cp06_stack_enabled',False) else 'hand'); self.zones.move(physical_uid,'battlefield',controller=0); del self.stack_cards[physical_uid]
        p=self.add(SHIGEKI,colors='G',creature=True,mana_value=2,power=1,toughness=3); p.enchantment=True; self.linked_battlefield[p.uid]=physical_uid
        self.trace.append(('physical_creature_spell_resolved',SHIGEKI,physical_uid,p.uid)); self.assert_bridge_integrity()
    def _return_permanent_card(self,uid,source):
        """CP38 (K8): Shigeki returns from the graveyard as a permanent card (Rise of the Witch-king) with its own body."""
        card=self.zones.cards[uid]
        if card.name!=SHIGEKI or card.is_land: return super()._return_permanent_card(uid,source)
        if any(ph==uid for ph in self.linked_graveyard.values()):              # died: the existing reanimation path, then its enchantment type
            super()._return_permanent_card(uid,source)
            p=next((q for e,ph in self.linked_battlefield.items() if ph==uid for q in [self.permanents.get(e)] if q is not None),None)
            if p is not None: p.enchantment=True
            return
        self.zones.move(uid,'battlefield',controller=0)
        p=self.add(SHIGEKI,colors='G',creature=True,mana_value=2,power=1,toughness=3); p.enchantment=True; self.linked_battlefield[p.uid]=uid
        self.trace.append(('returned_permanent',SHIGEKI,uid,p.uid,source)); self.assert_bridge_integrity()
    def _tgt(self,uid,*,enchantment=False,**kw):
        p=self.permanents.get(uid)
        if enchantment and p is not None and p.controller==0 and p.name==SHIGEKI: return super()._tgt(uid,enchantment=False,**kw)
        return super()._tgt(uid,enchantment=enchantment,**kw)
    def _infestation_target(self,uid):
        p=self.permanents.get(uid); return super()._infestation_target(uid) or (p is not None and p.name==SHIGEKI)

    def shigeki_activate(self,uid,land_uid=None):
        p=self.permanents.get(uid); ph=self.linked_battlefield.get(uid)
        if p is None or p.name!=SHIGEKI or p.controller!=0 or ph is None: raise BridgeError('S20: not a linked Shigeki you control')
        if p.tapped: raise BridgeError('S20: Shigeki is tapped')
        if self.clock_engaged and getattr(p,'entered_turn',0)==self.clock.turn: raise BridgeError('S20: summoning sickness (CR 302.6)')
        pool=self.mana_pool
        if pool.count('G')<1 or len(pool)<2: raise BridgeError('S20: needs {1}{G}')
        self.pay_mana(green=1,generic=1); p.tapped=True; self.zones.cards[ph].tapped=True
        del self.permanents[uid]; del self.linked_battlefield[uid]; self.zones.move(ph,'hand'); self.trace.append(('shigeki_returned_to_hand',uid,ph))
        self.skullclamp_attached={k:v for k,v in self.skullclamp_attached.items() if v!=uid}   # CP38 (K13): equipment becomes unattached
        def resolve():
            top=list(self.zones.zones['library'][:4]); self.trace.append(('revealed',tuple(top)))
            lands=[u for u in top if self.zones.cards[u].is_land]; pick=land_uid if land_uid in lands else (lands[0] if lands else None)
            for u in top:
                if u==pick: self._enter_fetched_land(u,pay_life=False,surveil_graveyard=False); self.zones.cards[u].tapped=True; self.permanents[next(e for e,x in self.linked_battlefield.items() if x==u)].tapped=True
                else: self.zones.move(u,'graveyard')
            self.trace.append(('shigeki_reveal',pick,tuple(u for u in top if u!=pick)))
        self.pending.append(Trigger('Shigeki reveal (S20)',resolve)); self.assert_bridge_integrity()
    def channel_shigeki(self,card_uid,targets):
        card=self.zones._require_in_zone(card_uid,'hand')
        if card.name!=SHIGEKI: raise BridgeError('S20: not Shigeki')
        targets=list(targets); x=len(targets)
        if len(set(targets))!=x or any(u not in self.zones.zones['graveyard'] or self.zones.cards[u].name in LEGENDARY_CARDS for u in targets): raise BridgeError('S20: X distinct nonlegendary cards in your graveyard')
        pool=self.mana_pool
        if pool.count('G')<2 or len(pool)<2+2*x: raise BridgeError(f'S20: needs {{{2*x}}}{{G}}{{G}}')
        self.pay_mana(green=2,generic=2*x); self.zones.discard(card_uid); self.trace.append(('channel',SHIGEKI,card_uid,x))
        def resolve():
            for u in targets:
                if u not in self.zones.zones['graveyard']: self.trace.append(('return_card_gone',u)); continue
                ev=next((e for e,x2 in self.linked_graveyard.items() if x2==u),None)
                if ev is not None: del self.linked_graveyard[ev]; self.graveyard=[q for q in self.graveyard if q.uid!=ev]
                self.zones.move(u,'hand'); self.trace.append(('shigeki_channel_returned',u,self.zones.cards[u].name))
        self.pending.append(Trigger('Shigeki channel (S20)',resolve)); self.assert_bridge_integrity()

def check_invariants_s20(g): check_invariants_s18(g)
