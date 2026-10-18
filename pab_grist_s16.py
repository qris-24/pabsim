"""Stage S16 (authorized 2026-10-18 11:05): Grist, the Hunger Tide.

Layered above pab_cast_s15.InteractionSpellsMixin (PhysicalZoneGame only). No frozen file
edited. EVIDENCE/S16_PLANESWALKER_EVIDENCE.json. The last of the 65 nonland cards.

Grist {1}{B}{G}, Legendary Planeswalker — Grist, loyalty 3.
  Static (CR 205.1b-style text-changing: "As long as Grist isn't on the battlefield, it's a
  1/1 Insect creature in addition to its other types"): in the library, hand, graveyard and
  on the stack Grist is a creature card. S16 makes that true where the kernel looks:
  Unearth / Takenuma / Grisly Salvage / Rise of the Witch-king treat the card as a creature
  card (an event-kernel LKI with creature=True, mana value 3 is kept in the graveyard list
  when Grist leaves the battlefield or is milled/discarded, so the frozen _grave_target()
  finds it), and the frozen _return_creature_from_graveyard() is overridden for Grist so
  she re-enters as a planeswalker, not as a 1/1 body.
  On the battlefield: a noncreature, non-artifact permanent with `loyalty` (counters on the
  Permanent's `counters` field are NOT used: loyalty is its own attribute). CR 704.5i: at
  zero loyalty she goes to the graveyard as a state-based action.
  Loyalty abilities (CR 606): once per turn, controller's main phase, empty stack; the
  loyalty change is the cost (paid at once), the ability resolves from the stack.
  +1  create a 1/1 black and green Insect token (the frozen INSECT kind), then mill a card;
      if an Insect CARD was milled, put a loyalty counter on Grist and repeat. Grist herself
      is the deck's only Insect card and cannot be milled while on the battlefield, so the
      repeat never fires in this deck — the loop is still implemented and traced.
  -2  you may sacrifice a creature (sacrifice_uid, through the frozen sacrifice()); when you
      do, a reflexive trigger destroys target creature or planeswalker (target_uid, chosen
      when the reflexive trigger is put on the stack; checked again at resolution)
  -5  each opponent still in the game loses life equal to the number of creature cards in
      your graveyard (physical graveyard, counting Grist's static)

Not modeled: opponents attacking Grist (no combat); loyalty-ability responses by opponents;
Grist on the stack as a creature spell for effects that care (none in this kernel).
"""
from __future__ import annotations
from pab_cast_s15 import InteractionSpellsMixin, CASTABLE as CASTABLE_S15, check_invariants_s11
from pab_cast_s7 import CREATURES
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger, Permanent, INSECT, SAVRA

GRIST='Grist, the Hunger Tide'
GRIST_SPEC={'kind':'planeswalker','cost':(1,1,1),'additional':None,'mana_value':3,'loyalty':3}
CASTABLE={**CASTABLE_S15,GRIST:GRIST_SPEC}
CREATURE_CARD_NAMES=frozenset(CREATURES)|{SAVRA,GRIST}

class GristMixin(InteractionSpellsMixin):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw); self.grist_activated_turn=None

    # ---- cast ----
    def cast_from_hand(self,physical_uid,**kw):
        card=self.zones.cards.get(physical_uid)
        if card is not None and not card.token and card.name==GRIST:
            for k,v in kw.items():
                if k not in ('main_phase','stack_empty','has_priority') and v is not None: raise BridgeError(f'S16: Grist takes no {k}')
            self._timing('sorcery',main_phase=kw.get('main_phase'),stack_empty=kw.get('stack_empty'),has_priority=kw.get('has_priority'))
            self._preflight_cast(physical_uid,GRIST_SPEC,None)
            b,g,gen=GRIST_SPEC['cost']; self.stack_cards[physical_uid]=GRIST; self.trace.append(('cast_begin',GRIST,physical_uid))
            self.pay_mana(black=b,green=g,generic=gen); self.trace.append(('cast',GRIST)); self.trace.append(('physical_cast',GRIST,physical_uid,(b,g,gen),None))
            self.pending.append(Trigger(GRIST+' resolution (S16)',lambda:self._grist_enters(physical_uid)))
            self.assert_bridge_integrity(); return card
        return super().cast_from_hand(physical_uid,**kw)
    def _grist_enters(self,physical_uid):
        if self.stack_cards.get(physical_uid)!=GRIST: raise BridgeError('S16: Grist is not on the stack ledger')
        self.zones._require_in_zone(physical_uid,'hand'); self.zones.move(physical_uid,'battlefield',controller=0); del self.stack_cards[physical_uid]
        p=self._add_grist(); self.linked_battlefield[p.uid]=physical_uid; self.trace.append(('physical_permanent_spell_resolved',GRIST,physical_uid,p.uid)); self.assert_bridge_integrity()
    def _add_grist(self,*,loyalty=None):
        p=self.add(GRIST,colors='BG',creature=False,artifact=False,mana_value=3); p.loyalty=GRIST_SPEC['loyalty'] if loyalty is None else loyalty
        self.trace.append(('grist_enters',p.uid,p.loyalty)); return p
    def grist(self):
        return next((p for p in self.permanents.values() if p.name==GRIST and p.controller==0),None)

    # ---- leaving the battlefield: graveyard LKI as a creature card ----
    def _grist_to_graveyard(self,p,cause):
        ph=self.linked_battlefield.pop(p.uid,None); del self.permanents[p.uid]
        lki=Permanent(p.uid,GRIST,0,'BG',True,None,False,False,1,0,3,1)      # creature=True: the static applies off the battlefield
        self.graveyard.append(lki)
        if ph is not None: self.zones.move(ph,'graveyard'); self.linked_graveyard[p.uid]=ph
        self.trace.append(('grist_to_graveyard',p.uid,cause)); self.assert_bridge_integrity()
    def destroy(self,uid):
        p=self.permanents.get(uid)
        if p is not None and p.name==GRIST and p.controller==0:
            if uid in self.indestructible_until_eot: self.trace.append(('destroy_prevented_indestructible',uid)); return None
            self._grist_to_graveyard(p,'destroy'); return p
        return super().destroy(uid)
    def _destroy_any(self,uid,source):
        p=self.permanents.get(uid)
        if p is not None and p.name==GRIST and p.controller==0: self.destroy(uid); self.trace.append(('destroyed_by',uid,GRIST,source)); return
        return super()._destroy_any(uid,source)
    def state_based_actions(self):
        rounds=super().state_based_actions()
        g=self.grist()
        if g is not None and g.loyalty<=0: self.trace.append(('sba_zero_loyalty',g.uid)); self._grist_to_graveyard(g,'state-based')
        return rounds
    def _return_creature_from_graveyard(self,cand,source,*,tapped=False):
        if cand.name!=GRIST: return super()._return_creature_from_graveyard(cand,source,tapped=tapped)
        if cand not in self.graveyard: return None
        self.graveyard.remove(cand); ph=self.linked_graveyard.pop(cand.uid,None)
        p=self._add_grist()
        if ph is not None: self.zones.move(ph,'battlefield',controller=0); self.linked_battlefield[p.uid]=ph
        self.trace.append(('reanimate',cand.uid,p.uid,source,tapped)); self.assert_bridge_integrity(); return p
    def grist_graveyard_lki(self):
        """A milled or discarded Grist has no event-kernel LKI; make one (creature=True, MV 3) so Unearth /
        Rise / Takenuma can target it. Returns the LKI or None."""
        ph=next((u for u in self.zones.zones['graveyard'] if self.zones.cards[u].name==GRIST),None)
        if ph is None: return None
        ev=next((e for e,x in self.linked_graveyard.items() if x==ph),None)
        if ev is not None: return next((q for q in self.graveyard if q.uid==ev),None)
        lki=Permanent(self.next_uid,GRIST,0,'BG',True,None,False,False,1,0,3,1); self.next_uid+=1
        self.graveyard.append(lki); self.linked_graveyard[lki.uid]=ph; self.trace.append(('grist_graveyard_lki',lki.uid,ph)); self.assert_bridge_integrity(); return lki

    # ---- loyalty abilities ----
    def _loyalty_preflight(self,delta):
        g=self.grist()
        if g is None: raise BridgeError('S16: Grist is not on the battlefield')
        if self.clock_engaged:
            c=self.clock
            if not (c.is_controller_turn and c.step in ('precombat_main','postcombat_main') and not self.pending): raise BridgeError('S16: loyalty abilities are sorcery-speed (CR 606.3)')
            if self.grist_activated_turn==c.turn: raise BridgeError('S16: one loyalty ability per turn (CR 606.3)')
        elif self.pending: raise BridgeError('S16: the stack must be empty')
        if g.loyalty+delta<0: raise BridgeError('S16: not enough loyalty')
        return g
    def _loyalty_pay(self,g,delta,label):
        g.loyalty+=delta
        if self.clock_engaged: self.grist_activated_turn=self.clock.turn
        self.trace.append(('loyalty_ability',label,delta,g.loyalty))
    def grist_plus_one(self):
        g=self._loyalty_preflight(+1); self._loyalty_pay(g,+1,'+1')
        def resolve():
            while True:
                self.make_tokens(INSECT); milled=self.zones.mill(1)
                self.trace.append(('milled',tuple(c.uid for c in milled)))
                if milled and milled[0].name==GRIST:            # an Insect card: loyalty counter and repeat
                    live=self.grist()
                    if live is not None: live.loyalty+=1; self.trace.append(('grist_repeat',live.loyalty)); continue
                break
        self.pending.append(Trigger('Grist +1 (S16)',resolve)); self.assert_bridge_integrity()
    def grist_minus_two(self,sacrifice_uid=None,target_uid=None):
        g=self._loyalty_preflight(-2)
        if sacrifice_uid is not None:
            c=self.permanents.get(sacrifice_uid)
            if c is None or c.controller!=0 or not c.creature: raise BridgeError('S16: sacrifice a creature you control')
            t=self.permanents.get(target_uid)
            if t is None or not (t.creature or t.name==GRIST or getattr(t,'loyalty',None) is not None): raise BridgeError('S16: target a creature or planeswalker')
        elif target_uid is not None: raise BridgeError('S16: a target only comes with the sacrifice')
        self._loyalty_pay(g,-2,'-2')
        def resolve():
            if sacrifice_uid is None or sacrifice_uid not in self.permanents: self.trace.append(('grist_no_sacrifice',)); return
            self.sacrifice(sacrifice_uid)
            def reflexive():
                t=self.permanents.get(target_uid)
                if t is None or not (t.creature or getattr(t,'loyalty',None) is not None): self.trace.append(('spell_fizzles_all_targets_illegal','Grist -2')); return
                self._destroy_any(target_uid,'Grist -2')
            self._enqueue([Trigger('Grist -2 reflexive destroy (S16)',reflexive)])
        self.pending.append(Trigger('Grist -2 (S16)',resolve)); self.assert_bridge_integrity()
    def grist_minus_five(self):
        g=self._loyalty_preflight(-5); self._loyalty_pay(g,-5,'-5')
        def resolve():
            n=sum(1 for u in self.zones.zones['graveyard'] if self.zones.cards[u].name in CREATURE_CARD_NAMES)
            self.trace.append(('grist_minus_five',n))
            for s in self.seats_in_game(): self.life[s]-=n
            if n: self.trace.append(('opponents_lose_each',n,'Grist -5'))
        self.pending.append(Trigger('Grist -5 (S16)',resolve)); self.assert_bridge_integrity()

def check_invariants_s16(g):
    check_invariants_s11(g)
    gr=g.grist()
    if gr is not None and (gr.creature or gr.loyalty<=0) and not g.pending: raise AssertionError('S16: Grist on the battlefield with bad state')
    if sum(1 for q in g.graveyard if q.name==GRIST)>1: raise AssertionError('S16: duplicate Grist LKI')
