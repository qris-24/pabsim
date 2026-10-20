"""Stage S15 (authorized 2026-10-18 11:05): the nine interaction spells with no prior kernel
behaviour, cast from the physical hand.

Layered above pab_lands_s14.RemainingLandsMixin (PhysicalZoneGame only). No frozen file
edited. EVIDENCE/S15_SPELL_EVIDENCE.json. New general machinery, all cleared at EVERY
cleanup step (CR 514.2; the S2 reset_turn only ran at the controller's own cleanup, which
left an instant cast on an opponent's turn in force too long — S15 clears its own state and
the frozen indestructible_until_eot set at each seat's cleanup):
  eot_pt           until-end-of-turn power/toughness changes for any creature; the S3
                   state-based toughness check now includes them and opponents' creatures
  hexproof_eot     own permanents opponents' scripted actions may not target (S11 policies
                   skip them; hexproof does not stop the controller's own spells)
  regen_shields    regeneration (CR 701.15): the next destroy() this turn instead taps the
                   creature and the shield is spent
  infused_eot      Infuse with Vitality: when the creature dies this turn it returns tapped
                   (a Trigger after the death triggers; tokens cannot return)
  destroy()        an opponent's creature is destroyed through the S8 death path (the frozen
                   destroy() only accepts the controller's objects)
  _leave()         the S3 toughness SBA may now kill an opponent's creature (routed to the
                   S8 death path)

Targets are checked when the spell is cast and again at resolution (CR 608.2b): a target
that left or stopped qualifying is skipped; with no legal target left the spell fizzles.
  Abrupt Decay          {B}{G} instant: destroy target nonland permanent with MV <= 3
  Assassin's Trophy     {B}{G} instant: destroy target permanent an opponent controls (their
                        basic-land search is traced unmodeled: no libraries)
  Witherbloom Charm     {B}{G} instant, mode 1: may sacrifice a permanent, draw two (creatures
                        and artifacts through the frozen sacrifice(); enchantments and lands
                        through S15's _sacrifice_noncreature); mode 2: gain 5; mode 3: destroy
                        target nonland permanent with MV <= 2
  Golgari Charm         {B}{G} instant, mode 1: all creatures -1/-1 until end of turn (SBA
                        follows); mode 2: destroy target enchantment (own: frozen
                        _destroy_supported_noncreature; opponents have none); mode 3:
                        regenerate each creature you control
  Heroic Intervention   {1}{G} instant: your permanents gain hexproof and indestructible
  Infuse with Vitality  {B}{G} instant: target creature gains the return-when-it-dies ability
                        (deathtouch has no combat to matter in); you gain 2
  Grisly Salvage        {B}{G} instant: top five revealed; one creature or land card to hand
                        (choice_uid, else the first creature, else the first land); the rest
                        to the graveyard. Milled creature cards have no event-kernel LKI and
                        are therefore not Unearth/Reclamation targets — a pre-existing
                        bridge limitation, documented
  Rise of the Witch-king{2}{B}{G} sorcery: you sacrifice sacrifice_uid (required while you
                        control a creature); each opponent sacrifices by the S8 policy; if
                        you sacrificed, return_uid (another permanent card in your graveyard:
                        creature via the frozen linked reanimation, land via the S14 entry,
                        artifact/enchantment via add()) may come back
  Witherbloom Command   {B}{G} sorcery, two distinct modes: 1 target player mills three (you:
                        real mill; an opponent: traced unmodeled) then a land card from your
                        graveyard to hand; 2 destroy target noncreature nonland permanent
                        with MV <= 2; 3 target creature -3/-1 until end of turn; 4 target_opponent
                        loses 2, you gain 2
Grist, the Hunger Tide is recorded in the evidence but NOT modeled (fails closed): a
planeswalker with loyalty abilities and a type-changing static needs its own stage.
"""
from __future__ import annotations
from pab_lands_s14 import RemainingLandsMixin, FIXERS
from pab_cast_s13 import check_invariants_s11, CASTABLE as CASTABLE_S14, cast_when_able as _cast_s13
from pab_opponents_s8 import OPPONENT_SEATS
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger, SAVRA

SPELLS15={
  'Abrupt Decay':         {'kind':'instant','cost':(1,1,0)},
  "Assassin's Trophy":    {'kind':'instant','cost':(1,1,0)},
  'Witherbloom Charm':    {'kind':'instant','cost':(1,1,0)},
  'Golgari Charm':        {'kind':'instant','cost':(1,1,0)},
  'Heroic Intervention':  {'kind':'instant','cost':(0,1,1)},
  'Infuse with Vitality': {'kind':'instant','cost':(1,1,0)},
  'Grisly Salvage':       {'kind':'instant','cost':(1,1,0)},
  'Rise of the Witch-king':{'kind':'sorcery','cost':(1,1,2)},
  'Witherbloom Command':  {'kind':'sorcery','cost':(1,1,0)},
}
for _s in SPELLS15.values(): _s['additional']=None; _s['mana_value']=sum(_s['cost'])
S15_NAMES=frozenset(SPELLS15)
CASTABLE={**CASTABLE_S14,**SPELLS15}
S15_KW=('target_uid','mode','modes','sacrifice_uid','return_uid','choice_uid','target_player','target_opponent','mode2_uid','mode3_uid')
ENCHANTMENTS={'Bastion of Remembrance','Moldervine Reclamation','Dark Prophecy','Grave Pact','Blight Mound','Feral Appetite','Phyrexian Reclamation','Agent of the Iron Throne','The Hunger Tide Rises'}

class InteractionSpellsMixin(RemainingLandsMixin):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.eot_pt={}; self.hexproof_eot=set(); self.regen_shields=set(); self.infused_eot=set()

    # ---- until end of turn, every turn (CR 514.2) ----
    def advance_step(self):
        turn,ap,phase,step=super().advance_step()
        if step=='cleanup':
            n=len(self.eot_pt)+len(self.hexproof_eot)+len(self.regen_shields)+len(self.infused_eot)+len(self.indestructible_until_eot)
            self.eot_pt.clear(); self.hexproof_eot.clear(); self.regen_shields.clear(); self.infused_eot.clear(); self.indestructible_until_eot.clear()
            if n: self.trace.append(('until_end_of_turn_expired_s15',turn,ap,n))
        return turn,ap,phase,step

    # ---- general machinery ----
    def _dying_by_toughness(self):
        return [p for p in self.permanents.values() if p.creature
                and p.toughness+p.counters-p.minus_counters+self.eot_pt.get(p.uid,(0,0))[1]<=0]
    def _leave(self,uid,*,sacrificed):
        p=self.permanents.get(uid)
        if p is not None and p.controller!=0 and p.creature:
            return self._opponent_creature_dies(uid,cause='sacrifice' if sacrificed else 'state-based')   # CP10 (A-S20-11): the Infuse return for an opponent body is handled there, so destroy/wipe/edict deaths are covered too
        infused=uid in self.infused_eot and p is not None and p.controller==0 and p.creature and p.token is None
        departed=super()._leave(uid,sacrificed=sacrificed)
        if infused:
            self.infused_eot.discard(uid); cand=departed
            self.pending.append(Trigger('Infuse with Vitality return (S15)',lambda:self._return_creature_from_graveyard(cand,'Infuse with Vitality',tapped=True) if cand in self.graveyard else self.trace.append(('infuse_return_card_gone',uid))))
        return departed
    def _opponent_creature_dies(self,uid,*,cause):
        """CP10 (A-S20-11): an infused opponent-owned body returns tapped under its owner's control as a
        NEW declared body (same name/P/T/colours/mana value; no counters or until-end-of-turn state carried).
        Opponents have no cards or graveyards (S8), so the body is re-declared rather than moved."""
        p=self.permanents.get(uid)
        infused=uid in self.infused_eot and p is not None and p.controller!=0 and p.creature
        if infused:
            self.infused_eot.discard(uid); seat=p.controller
            spec=dict(name=p.name,colors=p.colors,power=p.power,toughness=p.toughness,mana_value=p.mana_value)
        out=super()._opponent_creature_dies(uid,cause=cause)
        if infused:
            self.pending.append(Trigger('Infuse with Vitality return (S15)',lambda:self._infuse_return_opponent_body(uid,seat,spec)))
        return out
    def _infuse_return_opponent_body(self,uid,seat,spec):
        if seat in self.lost_seats: self.trace.append(('infuse_return_seat_gone',uid,seat)); return None
        new=self.add(spec['name'],controller=seat,colors=spec['colors'],creature=True,artifact=False,tapped=True,
                     power=spec['power'],toughness=spec['toughness'],mana_value=spec['mana_value'],counters=0)
        self.trace.append(('reanimate',uid,new.uid,'Infuse with Vitality',True)); return new
    def destroy(self,uid):
        p=self.permanents.get(uid)
        if p is None: return super().destroy(uid)
        if uid in self.regen_shields and uid not in self.indestructible_until_eot:
            self.regen_shields.discard(uid); p.tapped=True
            ph=self.linked_battlefield.get(uid)
            if ph is not None: self.zones.cards[ph].tapped=True
            self.trace.append(('regenerated',uid,p.name)); return None
        if p.controller!=0: return self._opponent_creature_dies(uid,cause='destroy')
        return super().destroy(uid)
    def _own_creature_target(self,*,commander_only=False):
        p=super()._own_creature_target(commander_only=commander_only)
        if p is not None and p.uid in self.hexproof_eot:
            own=[q for q in self.permanents.values() if q.controller==0 and q.creature and q.token is None and q.uid not in self.hexproof_eot]
            if commander_only: return None
            others=[q for q in own if q.name!=SAVRA]
            if others: return max(others,key=lambda q:(q.power+q.counters-q.minus_counters,-q.uid))
            return next((q for q in own if q.name==SAVRA),None)
        return p
    def _is_land_permanent(self,uid):
        ph=self.linked_battlefield.get(uid); return ph is not None and self.zones.cards[ph].is_land
    def _sacrifice_noncreature(self,uid,source):
        p=self.permanents[uid]
        if p.creature or p.artifact: return self.sacrifice(uid)
        if self._is_land_permanent(uid):
            ph=self.linked_battlefield.pop(uid); del self.permanents[uid]; self.zones.move(ph,'graveyard'); self.trace.append(('land_sacrificed',uid,ph,source)); return p
        self._destroy_supported_noncreature(uid); self.trace.append(('sacrifice_permanent',uid,p.name,source))
        ph=self.linked_battlefield.pop(uid,None)
        if ph is not None: self.zones.move(ph,'graveyard'); self.linked_graveyard[uid]=ph
        return p

    # ---- target predicates ----
    def _tgt(self,uid,*,opponent=False,nonland=False,creature=False,noncreature=False,enchantment=False,mv_max=None):
        p=self.permanents.get(uid)
        if p is None: return False
        if opponent and p.controller==0: return False
        if nonland and self._is_land_permanent(uid): return False
        if creature and not p.creature: return False
        if noncreature and p.creature: return False
        if enchantment and not (p.controller==0 and p.name in ENCHANTMENTS): return False
        if mv_max is not None and p.mana_value>mv_max: return False
        return True
    def _destroy_any(self,uid,source):
        p=self.permanents[uid]
        if p.creature or p.artifact or p.controller!=0: self.destroy(uid)
        else:
            self._destroy_supported_noncreature(uid); ph=self.linked_battlefield.pop(uid,None)
            if ph is not None: self.zones.move(ph,'graveyard'); self.linked_graveyard[uid]=ph
        self.trace.append(('destroyed_by',uid,p.name,source))

    # ---- cast entry ----
    def cast_from_hand(self,physical_uid,**kw):
        card=self.zones.cards.get(physical_uid)
        if card is not None and not card.token and card.name in S15_NAMES:
            return self._cast_s15(physical_uid,card,**kw)
        for k in S15_KW:
            if kw.get(k) is not None and k not in ('sacrifice_uid','target_uid'): raise BridgeError(f'S15: {k} applies only to the S15 spells')
        return super().cast_from_hand(physical_uid,**{k:v for k,v in kw.items() if k not in ('mode','modes','return_uid','choice_uid','target_player','target_opponent','mode2_uid','mode3_uid')})
    def _cast_s15(self,physical_uid,card,*,target_uid=None,mode=None,modes=None,sacrifice_uid=None,return_uid=None,choice_uid=None,target_player=None,target_opponent=None,mode2_uid=None,mode3_uid=None,
                  main_phase=None,stack_empty=None,has_priority=None,**rest):
        if rest: raise BridgeError(f'S15: {card.name} takes none of {sorted(rest)}')
        name=card.name; spec=SPELLS15[name]
        self._timing(spec['kind'],main_phase=main_phase,stack_empty=stack_empty,has_priority=has_priority)
        self._preflight_cast(physical_uid,spec,None)
        handler=getattr(self,'_s15_'+name.lower().replace(' ','_').replace('-','_').replace("'",''))
        plan=handler(target_uid=target_uid,mode=mode,modes=modes,sacrifice_uid=sacrifice_uid,return_uid=return_uid,choice_uid=choice_uid,target_player=target_player,target_opponent=target_opponent,mode2_uid=mode2_uid,mode3_uid=mode3_uid)
        b,g,gen=spec['cost']
        self.stack_cards[physical_uid]=name; self.trace.append(('cast_begin',name,physical_uid))
        self.pay_mana(black=b,green=g,generic=gen)
        if plan.get('cost_sacrifice') is not None: self.sacrifice(plan['cost_sacrifice'])
        self.trace.append(('cast',name)); self.trace.append(('physical_cast',name,physical_uid,(b,g,gen),plan.get('cost_sacrifice')))
        if plan.get('targets'): self.trace.append(('targets_locked',tuple(plan['targets']),name))
        def resolve():
            plan['resolve']()
            if self.stack_cards.get(physical_uid)!=name: raise BridgeError('S15: ledger mismatch')
            self.zones._require_in_zone(physical_uid,'stack' if getattr(self,'cp06_stack_enabled',False) else 'hand'); self.zones.move(physical_uid,'graveyard'); del self.stack_cards[physical_uid]
            self.trace.append(('physical_spell_resolved',name,physical_uid)); self.assert_bridge_integrity()
        self.pending.append(Trigger(name+' resolution (S15)',resolve)); self.sedgemoor_spell_cast_or_copied(); self.assert_bridge_integrity()
        return card
    def _fizzle(self,name): self.trace.append(('spell_fizzles_all_targets_illegal',name))

    # ---- the nine spells ----
    def _s15_abrupt_decay(self,*,target_uid,**_):
        if not self._tgt(target_uid,nonland=True,mv_max=3): raise BridgeError('S15: Abrupt Decay targets a nonland permanent with mana value 3 or less')
        def resolve():
            if self._tgt(target_uid,nonland=True,mv_max=3): self._destroy_any(target_uid,'Abrupt Decay')
            else: self._fizzle('Abrupt Decay')
        return {'targets':[target_uid],'resolve':resolve}
    def _s15_assassins_trophy(self,*,target_uid,**_):
        if not self._tgt(target_uid,opponent=True): raise BridgeError("S15: Assassin's Trophy targets a permanent an opponent controls")
        def resolve():
            if self._tgt(target_uid,opponent=True):
                seat=self.permanents[target_uid].controller; self._destroy_any(target_uid,"Assassin's Trophy"); self.trace.append(('opponent_basic_land_search_unmodeled',seat,"Assassin's Trophy"))
            else: self._fizzle("Assassin's Trophy")
        return {'targets':[target_uid],'resolve':resolve}
    def _s15_witherbloom_charm(self,*,mode,sacrifice_uid,target_uid,**_):
        if mode not in (1,2,3): raise BridgeError('S15: Witherbloom Charm needs mode 1, 2 or 3')
        if mode==1:
            if sacrifice_uid is not None and (sacrifice_uid not in self.permanents or self.permanents[sacrifice_uid].controller!=0): raise BridgeError('S15: sacrifice a permanent you control')
            def resolve():
                if sacrifice_uid is not None and sacrifice_uid in self.permanents and self.permanents[sacrifice_uid].controller==0:
                    self._sacrifice_noncreature(sacrifice_uid,'Witherbloom Charm'); self._fixture_draw(2,'Witherbloom Charm')
                else: self.trace.append(('witherbloom_charm_no_sacrifice',))
            return {'resolve':resolve}
        if mode==2: return {'resolve':lambda:self.gain(5,'Witherbloom Charm')}
        if not self._tgt(target_uid,nonland=True,mv_max=2): raise BridgeError('S15: Witherbloom Charm mode 3 targets a nonland permanent with mana value 2 or less')
        def resolve():
            if self._tgt(target_uid,nonland=True,mv_max=2): self._destroy_any(target_uid,'Witherbloom Charm')
            else: self._fizzle('Witherbloom Charm')
        return {'targets':[target_uid],'resolve':resolve}
    def _s15_golgari_charm(self,*,mode,target_uid,**_):
        if mode not in (1,2,3): raise BridgeError('S15: Golgari Charm needs mode 1, 2 or 3')
        if mode==1:
            def resolve():
                for p in list(self.permanents.values()):
                    if p.creature: dp,dt=self.eot_pt.get(p.uid,(0,0)); self.eot_pt[p.uid]=(dp-1,dt-1)
                self.trace.append(('all_creatures_minus_one_minus_one','Golgari Charm'))
            return {'resolve':resolve}
        if mode==2:
            if not self._tgt(target_uid,enchantment=True): raise BridgeError('S15: Golgari Charm mode 2 targets an enchantment')
            def resolve():
                if self._tgt(target_uid,enchantment=True): self._destroy_any(target_uid,'Golgari Charm')
                else: self._fizzle('Golgari Charm')
            return {'targets':[target_uid],'resolve':resolve}
        def resolve():
            own=[p.uid for p in self.permanents.values() if p.controller==0 and p.creature]; self.regen_shields.update(own); self.trace.append(('regeneration_shields','Golgari Charm',tuple(own)))
        return {'resolve':resolve}
    def _s15_heroic_intervention(self,**_):
        def resolve():
            own=[p.uid for p in self.permanents.values() if p.controller==0]; self.indestructible_until_eot.update(own); self.hexproof_eot.update(own)
            self.trace.append(('hexproof_indestructible_until_end_of_turn','Heroic Intervention',tuple(own)))
        return {'resolve':resolve}
    def _s15_infuse_with_vitality(self,*,target_uid,**_):
        if not self._tgt(target_uid,creature=True): raise BridgeError('S15: Infuse with Vitality targets a creature')
        def resolve():
            if self._tgt(target_uid,creature=True): self.infused_eot.add(target_uid); self.trace.append(('infused',target_uid))
            else: self._fizzle('Infuse with Vitality'); return
            self.gain(2,'Infuse with Vitality')
        return {'targets':[target_uid],'resolve':resolve}
    def _s15_grisly_salvage(self,*,choice_uid,**_):
        from pab_cast_s7 import CREATURES
        names=set(CREATURES)|{SAVRA,'Grist, the Hunger Tide'}
        def resolve():
            top=list(self.zones.zones['library'][:5]); self.trace.append(('revealed',tuple(top)))
            elig=[u for u in top if self.zones.cards[u].name in names or self.zones.cards[u].is_land]
            pick=choice_uid if choice_uid in elig else next((u for u in elig if not self.zones.cards[u].is_land),next(iter(elig),None))
            for u in top:
                self.zones.move(u,'hand' if u==pick else 'graveyard')
            self.trace.append(('grisly_salvage',pick,tuple(u for u in top if u!=pick)))
        return {'resolve':resolve}
    def _s15_rise_of_the_witch_king(self,*,sacrifice_uid,return_uid,**_):
        own=[p for p in self.permanents.values() if p.controller==0 and p.creature]
        if own and (sacrifice_uid not in {p.uid for p in own}): raise BridgeError('S15: Rise of the Witch-king: choose a creature you control to sacrifice')
        if not own and sacrifice_uid is not None: raise BridgeError('S15: nothing to sacrifice')
        if return_uid is not None and (return_uid not in self.zones.zones['graveyard'] or return_uid in self.linked_battlefield.values()): raise BridgeError('S15: return_uid must be a card in your graveyard')
        def resolve():
            did=False
            if sacrifice_uid in self.permanents and self.permanents[sacrifice_uid].controller==0 and self.permanents[sacrifice_uid].creature:
                self.sacrifice(sacrifice_uid); did=True
            self._edict_each_opponent('Rise of the Witch-king')
            if did and return_uid is not None and return_uid in self.zones.zones['graveyard']:
                self._return_permanent_card(return_uid,'Rise of the Witch-king')
            elif did and return_uid is not None: self.trace.append(('return_card_gone',return_uid))
        return {'resolve':resolve}
    def _return_permanent_card(self,uid,source):
        card=self.zones.cards[uid]
        if card.is_land: self._enter_fetched_land(uid,pay_life=False,surveil_graveyard=False); return
        ev=next((e for e,ph in self.linked_graveyard.items() if ph==uid),None)
        if ev is not None:
            cand=next((q for q in self.graveyard if q.uid==ev),None)
            if cand is not None and cand.creature: self._return_creature_from_graveyard(cand,source); return
            self.graveyard=[q for q in self.graveyard if q.uid!=ev]; del self.linked_graveyard[ev]
        from pab_cast_s12 import PERMANENTS
        from pab_cast_s7 import CREATURES
        if card.name in PERMANENTS:
            spec=PERMANENTS[card.name]; self.zones.move(uid,'battlefield',controller=0)
            p=self.add(card.name,colors='',creature=False,artifact=spec['artifact'],mana_value=spec['mana_value']); self.linked_battlefield[p.uid]=uid; self.trace.append(('returned_permanent',card.name,uid,p.uid,source)); return
        if card.name in CREATURES:
            spec=CREATURES[card.name]; self.zones.move(uid,'battlefield',controller=0)
            p=self.add(card.name,colors=spec['colors'],creature=True,mana_value=spec['mana_value'],power=spec['power'],toughness=spec['toughness']); self.linked_battlefield[p.uid]=uid; self.trace.append(('returned_permanent',card.name,uid,p.uid,source)); return
        self.trace.append(('return_not_a_permanent_card',uid,card.name))
    def _s15_witherbloom_command(self,*,modes,target_uid,target_player,target_opponent,mode2_uid=None,mode3_uid=None,**_):
        """CP23 (A-S20-10): each mode has its own target (modes 2 and 3: mode2_uid / mode3_uid; target_uid still names
        the one permanent when only one of 2/3 is chosen). Every chosen target is locked at cast as (mode, target).
        Resolution (CR 608.2b): every target is re-checked first; a mode whose target is illegal does nothing (mode 1:
        no mill and no land return); with every target illegal the spell does nothing."""
        modes=tuple(modes or ())
        if len(modes)!=2 or len(set(modes))!=2 or any(m not in (1,2,3,4) for m in modes): raise BridgeError('S15: Witherbloom Command needs two distinct modes 1-4')
        if mode2_uid is not None and 2 not in modes: raise BridgeError('S15: mode2_uid without mode 2')
        if mode3_uid is not None and 3 not in modes: raise BridgeError('S15: mode3_uid without mode 3')
        if target_uid is not None:
            if 2 in modes and 3 in modes: raise BridgeError('S15: modes 2 and 3 take mode2_uid and mode3_uid, not one target_uid')
            if (2 in modes and mode2_uid is not None) or (3 in modes and mode3_uid is not None): raise BridgeError('S15: target_uid and a per-mode uid both given')
            if 2 in modes: mode2_uid=target_uid
            elif 3 in modes: mode3_uid=target_uid
        def legal(m):
            if m==1: return target_player==0 or target_player in self.seats_in_game()
            if m==2: return self._tgt(mode2_uid,nonland=True,noncreature=True,mv_max=2)
            if m==3: return self._tgt(mode3_uid,creature=True)
            return target_opponent in self.seats_in_game()
        if 1 in modes and not legal(1): raise BridgeError('S15: mode 1 needs target_player, you (0) or an opponent still in the game')
        if 2 in modes and not legal(2): raise BridgeError('S15: mode 2 targets a noncreature nonland permanent with mana value 2 or less')
        if 3 in modes and not legal(3): raise BridgeError('S15: mode 3 targets a creature')
        if 4 in modes and not legal(4): raise BridgeError('S15: mode 4 needs target_opponent, an opponent still in the game')
        chosen={1:('mode1_player',target_player),2:('mode2_permanent',mode2_uid),3:('mode3_creature',mode3_uid),4:('mode4_opponent',target_opponent)}
        targets=[chosen[m] for m in modes]
        def resolve():
            ok={m:legal(m) for m in modes}                  # CR 608.2b: all targets re-checked before any mode acts
            if not any(ok.values()): self._fizzle('Witherbloom Command'); return
            for m in modes:
                if not ok[m]: self.trace.append(('mode_target_illegal','Witherbloom Command',m,chosen[m])); continue
                if m==1:
                    if target_player==0:
                        milled=self.zones.mill(3); self.trace.append(('milled',tuple(c.uid for c in milled)))
                    else: self.trace.append(('opponent_mill_unmodeled',target_player))
                    land=next((u for u in self.zones.zones['graveyard'] if self.zones.cards[u].is_land),None)
                    if land is not None: self.zones.move(land,'hand'); self.trace.append(('land_returned_to_hand',land))
                elif m==2:
                    if self._tgt(mode2_uid,nonland=True,noncreature=True,mv_max=2): self._destroy_any(mode2_uid,'Witherbloom Command')
                    else: self.trace.append(('mode_target_illegal','Witherbloom Command',m,chosen[m]))
                elif m==3:
                    if self._tgt(mode3_uid,creature=True): dp,dt=self.eot_pt.get(mode3_uid,(0,0)); self.eot_pt[mode3_uid]=(dp-3,dt-1); self.trace.append(('minus_three_minus_one',mode3_uid))
                    else: self.trace.append(('mode_target_illegal','Witherbloom Command',m,chosen[m]))
                elif m==4:
                    self.life[target_opponent]-=2; self.trace.append(('target_opponent_loses',2,'Witherbloom Command')); self.trace.append(('witherbloom_command_target',target_opponent,2)); self.gain(2,'Witherbloom Command')
        return {'targets':targets,'resolve':resolve}

# ---- driver ------------------------------------------------------------------
def cast_when_able(g):
    """S13 pass, then S15 spells with fixed policies: Decay/Trophy on the strongest opposing creature,
    Heroic Intervention never (no threat model), Witherbloom Charm mode 2, Grisly Salvage, Golgari Charm
    mode 1 only if it kills more opposing than own creatures, Command modes (4,1) on seat 1, Infuse on Savra,
    Rise of the Witch-king when a token can be sacrificed."""
    from pab_cast_s7 import _affordable, _fodder
    cast=_cast_s13(g)
    for uid in list(g.zones.zones['hand']):
        name=g.zones.cards[uid].name
        if name not in S15_NAMES or not _affordable(g,SPELLS15[name]): continue
        opp=[p for s in OPPONENT_SEATS for p in g.opponent_creatures(s)]; kw={}
        if name in ('Abrupt Decay',"Assassin's Trophy"):
            cands=[p for p in opp if name!='Abrupt Decay' or p.mana_value<=3]
            if not cands: continue
            kw['target_uid']=max(cands,key=lambda p:(p.power,p.toughness,-p.uid)).uid
        elif name=='Witherbloom Charm': kw['mode']=2
        elif name=='Golgari Charm':
            kills_opp=sum(1 for p in opp if p.toughness+p.counters-p.minus_counters<=1); kills_own=sum(1 for p in g.permanents.values() if p.controller==0 and p.creature and p.toughness+p.counters-p.minus_counters<=1)
            if kills_opp<=kills_own: continue
            kw['mode']=1
        elif name=='Heroic Intervention': continue
        elif name=='Infuse with Vitality':
            sv=next((p for p in g.permanents.values() if p.controller==0 and p.name==SAVRA),None)
            if sv is None: continue
            kw['target_uid']=sv.uid
        elif name=='Rise of the Witch-king':
            f=_fodder(g)
            if f is None or not any(p.token is not None for p in g.permanents.values() if p.uid==f): continue
            kw['sacrifice_uid']=f
        elif name=='Witherbloom Command':
            if 1 not in g.seats_in_game(): continue
            kw['modes']=(4,1); kw['target_player']=0; kw['target_opponent']=1
        g.cast_from_hand(uid,**kw); check_invariants_s11(g); g.resolve(); check_invariants_s11(g); cast.append(name)
    return cast

def run_turns_casting(g,turns):
    from pab_lands_s14 import LAND_MANA_DRIVER
    from pab_lands_s9 import play_land_policy, tap_lands_policy
    from pab_commander_s10 import commander_need, cast_commander_when_able
    ledger=[]; start=g.clock.turn
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s11(g)
        if ap!=0 or st!='precombat_main': continue
        u,kw=play_land_policy(g,LAND_MANA_DRIVER); played=None
        if u is not None: played=g.play_physical_land(u,**kw).name; g.resolve(); check_invariants_s11(g)
        mana=tap_lands_policy(g,extra=commander_need(g),land_mana=LAND_MANA_DRIVER)
        cast=[SAVRA] if cast_commander_when_able(g) else []
        cast+=cast_when_able(g); check_invariants_s11(g)
        ledger.append((t,played,tuple(mana),tuple(cast)))
    return ledger
