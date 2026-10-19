"""Stage S13 (authorized 2026-10-18 11:05): the eight remaining spells with frozen behaviour,
cast from the physical hand.

Layered above pab_cast_s12.PermanentCastMixin (PhysicalZoneGame only). No frozen file edited.
Each spell's effect is the frozen kernel's existing procedure; S13 adds the physical card:
in hand, timing from the clock, printed cost, stack ledger, card to the graveyard when the
spell (its original) finishes resolving. EVIDENCE/S13_SPELL_EVIDENCE.json.

  Demonic Tutor      {1}{B} sorcery; selected_land_uid is reused as `selected_uid` (optional explicit
                     library card); since CP13 the choice is made at resolution (explicit card if still
                     in the library, else tutor_selection against the library as it is then);
                     resolution = frozen zones.resolve_demonic_tutor (card to hand, shuffle)
  Diabolic Intent    {1}{B} sorcery, additional cost sacrifice a creature (frozen sacrifice());
                     resolution = the same unrestricted search to hand; the frozen kernel
                     refused this spell rather than fake its search — now the search is real
  Hunt for Specimens {1}{B} sorcery; resolution = one Pest token (frozen make_tokens) then
                     Learn: learn='lesson' (house rule: PhysicalZoneGame(learn_sideboard_
                     allowed=True); the Lesson card moves outside_game -> hand through the
                     frozen bridge), learn='discard' with discard_uid (discard that card, draw
                     one), or learn=None (decline). CR 702.139a
  Pest Summoning     {1}{B/G}{B/G} sorcery (Lesson, in hand only after Learn); hybrid pips are
                     paid from the pool with black first, then green (hybrid= 'BB'|'BG'|'GG'
                     overrides); resolution = two Pests (frozen)
  Unearth            {B} sorcery; target_uid = event uid of a creature card in the graveyard
                     with mana value <= 3 (frozen unearth(): target check, cost, resolution
                     through the bridge's linked reanimation); card to graveyard afterwards
  Plumb the Forbidden{1}{B} instant; sacrifice_uids (0+ controlled creatures); frozen
                     plumb_the_forbidden(): cost, copies, Magecraft per copy, draw/lose per
                     resolution; the card goes to the graveyard when the original resolves
  Immoral Bargain    {1}{B}{G} sorcery; x, sacrifice_uids (X controlled creatures), target_uids
                     (X distinct nonland permanents of any seat). The frozen immoral_bargain()
                     pays no mana and destroys nothing ("outside current reference kernel");
                     S13 pays the printed cost first and, at resolution, destroys each target
                     still legal: own creatures through the frozen destroy(), own artifacts/
                     enchantments through the frozen _destroy_supported_noncreature(),
                     opponents' creatures through _opponent_creature_dies() (S8). CR 608.2b:
                     a target that left is skipped; all illegal -> fizzles
  Pest Infestation   {X}{X}{G} sorcery; x and up to X target_uids (frozen pest_infestation():
                     cost, target validity, destruction, 2X Pests)

Not modeled: Witherbloom Charm, Witherbloom Command, Golgari Charm, Grisly Salvage, Heroic
Intervention, Infuse with Vitality, Rise of the Witch-king, Abrupt Decay, Assassin's Trophy,
Grist (no kernel behaviour yet); Learn's "discard a card to draw a card" when the hand is
empty; the Lesson as a sideboard object outside the house rule.
"""
from __future__ import annotations
from pab_cast_s12 import PermanentCastMixin, check_invariants_s11, CASTABLE as CASTABLE_S12, cast_when_able as _cast_s12
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger, PEST
import pab_cast_s7 as _s7

SPELLS={
  'Demonic Tutor':      {'kind':'sorcery','cost':(1,0,1),'additional':None},
  'Diabolic Intent':    {'kind':'sorcery','cost':(1,0,1),'additional':'creature'},
  'Hunt for Specimens': {'kind':'sorcery','cost':(1,0,1),'additional':None},
  'Pest Summoning':     {'kind':'sorcery','cost':(0,0,1),'additional':None,'hybrid_pips':2},   # {1}{B/G}{B/G}
  'Unearth':            {'kind':'sorcery','cost':(1,0,0),'additional':None},
  'Plumb the Forbidden':{'kind':'instant','cost':(1,0,1),'additional':None},
  'Immoral Bargain':    {'kind':'sorcery','cost':(1,1,1),'additional':None},
  'Pest Infestation':   {'kind':'sorcery','cost':(0,1,0),'additional':None},                  # + {X}{X}
}
for _s in SPELLS.values(): _s['mana_value']=sum(_s['cost'])+_s.get('hybrid_pips',0)
S13_NAMES=frozenset(SPELLS)
CASTABLE={**CASTABLE_S12,**SPELLS}

class SpellCastMixin(PermanentCastMixin):
    def cast_from_hand(self,physical_uid,**kw):
        card=self.zones.cards.get(physical_uid)
        if card is not None and not card.token and card.name in S13_NAMES:
            return self._cast_spell_s13(physical_uid,card,**kw)
        for k in ('x','target_uid','target_uids','sacrifice_uids','learn','discard_uid','hybrid'):
            if kw.get(k) is not None: raise BridgeError(f'S13: {k} applies only to the S13 spells')
        return super().cast_from_hand(physical_uid,**{k:v for k,v in kw.items() if k not in ('x','target_uid','target_uids','sacrifice_uids','learn','discard_uid','hybrid')})

    def _begin(self,physical_uid,name,cost_paid):
        self.stack_cards[physical_uid]=name
        self.trace.append(('cast_begin',name,physical_uid))
        self.trace.append(('physical_cast',name,physical_uid,cost_paid,None))

    def _finish_to_graveyard(self,physical_uid,name):
        if self.stack_cards.get(physical_uid)!=name: raise BridgeError('S13: resolving a spell that is not on the stack ledger')
        self.zones._require_in_zone(physical_uid,'stack' if getattr(self,'cp06_stack_enabled',False) else 'hand')
        self.zones.move(physical_uid,'graveyard'); del self.stack_cards[physical_uid]
        self.trace.append(('physical_spell_resolved',name,physical_uid)); self.assert_bridge_integrity()

    def _cast_spell_s13(self,physical_uid,card,*,sacrifice_uid=None,selected_land_uid=None,devour_uids=None,
                        x=None,target_uid=None,target_uids=None,sacrifice_uids=None,learn=None,discard_uid=None,hybrid=None,
                        main_phase=None,stack_empty=None,has_priority=None):
        name=card.name; spec=SPELLS[name]
        if card.zone=='outside_game': raise BridgeError('S13: a Lesson outside the game is not castable; Learn it first')
        if devour_uids is not None: raise BridgeError(f'S13: {name} has no devour')
        self._timing(spec['kind'],main_phase=main_phase,stack_empty=stack_empty,has_priority=has_priority)
        card,cost=self._preflight_cast(physical_uid,spec,sacrifice_uid)       # hand, ledger, base mana, additional creature
        handler=getattr(self,'_s13_'+name.lower().replace(' ','_'))
        return handler(physical_uid,cost,selected_uid=selected_land_uid,x=x,target_uid=target_uid,target_uids=target_uids,
                       sacrifice_uids=sacrifice_uids,learn=learn,discard_uid=discard_uid,hybrid=hybrid)

    # ---- tutors ---------------------------------------------------------------
    def _tutor(self,physical_uid,name,cost,selected_uid):
        # CP13 (AUD-03 / A-S20-14): the library card is chosen when the spell resolves, against the
        # library as it is then. Cast pays the mana and the Diabolic Intent sacrifice only.
        b,g,gen=SPELLS[name]['cost']
        self._begin(physical_uid,name,(b,g,gen)); self.pay_mana(black=b,green=g,generic=gen)
        if cost is not None: self.sacrifice(cost.uid)
        self.trace.append(('cast',name))
        def resolve():
            lib=self.zones.zones['library']; sel=selected_uid
            if sel is not None and sel not in lib: self.trace.append(('search_selection_gone',name,sel)); sel=None
            if sel is None and lib:
                sel=tutor_selection(self)                                        # policy at resolution
                if sel is None or sel not in lib: sel=lib[0]                     # unrestricted search must find a card
            if name=='Demonic Tutor': self.zones.resolve_demonic_tutor(sel)
            else: self.zones.search_library(selected_uid=sel,destination='hand',eligible='any'); self.trace.append(('diabolic_intent_resolved',sel))
            self._finish_to_graveyard(physical_uid,name)
        self.pending.append(Trigger(name+' resolution (S13)',resolve)); self.sedgemoor_spell_cast_or_copied(); self.assert_bridge_integrity(); return self.zones.cards[physical_uid]
    def _s13_demonic_tutor(self,physical_uid,cost,*,selected_uid,**_): return self._tutor(physical_uid,'Demonic Tutor',None,selected_uid)
    def _s13_diabolic_intent(self,physical_uid,cost,*,selected_uid,**_): return self._tutor(physical_uid,'Diabolic Intent',cost,selected_uid)

    # ---- Hunt for Specimens / Learn ------------------------------------------
    def _s13_hunt_for_specimens(self,physical_uid,cost,*,learn,discard_uid,**_):
        if learn not in (None,'lesson','discard'): raise BridgeError('S13: learn must be None, "lesson" or "discard"')
        if learn=='lesson' and (not self.learn_sideboard_allowed or not any(self.zones.cards[u].name=='Pest Summoning' for u in self.zones.zones['outside_game'])):
            raise BridgeError('S13: Lesson outside the game not allowed or unavailable')
        if learn=='discard' and (discard_uid is None or discard_uid not in self.zones.zones['hand'] or discard_uid==physical_uid):
            raise BridgeError('S13: learn="discard" needs another card in hand')
        if learn!='discard' and discard_uid is not None: raise BridgeError('S13: discard_uid only with learn="discard"')
        name='Hunt for Specimens'; self._begin(physical_uid,name,(1,0,1)); self.pay_mana(black=1,generic=1); self.trace.append(('cast',name))
        def resolve():
            self.make_tokens(PEST)
            if learn=='lesson':
                c=self.zones.learn_pest_summoning(); self.trace.append(('physical_learn_lesson_to_hand',c.uid))
            elif learn=='discard' and discard_uid in self.zones.zones['hand']:
                self.zones.discard(discard_uid); self.trace.append(('learn_discard',discard_uid)); self._fixture_draw(1,'Learn')
            else: self.trace.append(('learn_declined',))
            self._finish_to_graveyard(physical_uid,name)
        self.pending.append(Trigger(name+' resolution (S13)',resolve)); self.sedgemoor_spell_cast_or_copied(); self.assert_bridge_integrity(); return self.zones.cards[physical_uid]

    # ---- Pest Summoning (hybrid) -------------------------------------------------
    def _s13_pest_summoning(self,physical_uid,cost,*,hybrid,**_):
        pool=self.mana_pool
        if hybrid is None:
            b=min(2,pool.count('B')); g=2-b
        else:
            if hybrid not in ('BB','BG','GG'): raise BridgeError('S13: hybrid must be BB, BG or GG')
            b=hybrid.count('B'); g=hybrid.count('G')
        if pool.count('B')<b or pool.count('G')<g or len(pool)<b+g+1: raise BridgeError('S13: mana unavailable for Pest Summoning')
        name='Pest Summoning'; self._begin(physical_uid,name,(b,g,1)); self.pay_mana(black=b,green=g,generic=1); self.trace.append(('cast',name))
        def resolve(): self.pest_summoning(); self._finish_to_graveyard(physical_uid,name)
        self.pending.append(Trigger(name+' resolution (S13)',resolve)); self.sedgemoor_spell_cast_or_copied(); self.assert_bridge_integrity(); return self.zones.cards[physical_uid]

    # ---- frozen-method wrappers ----------------------------------------------------
    def _s13_unearth(self,physical_uid,cost,*,target_uid,**_):
        cand=self._grave_target(target_uid) if target_uid is not None else None
        if cand is None or cand.mana_value>3: raise BridgeError('S13: Unearth targets a creature card in your graveyard with mana value 3 or less')
        name='Unearth'; self._begin(physical_uid,name,(1,0,0))
        self.unearth(target_uid)                                               # frozen: pays {B}, 'cast', resolution trigger, Magecraft
        self.pending.append(Trigger(name+' card to graveyard (S13)',lambda:self._finish_to_graveyard(physical_uid,name)))
        self.assert_bridge_integrity(); return self.zones.cards[physical_uid]
    def _s13_plumb_the_forbidden(self,physical_uid,cost,*,sacrifice_uids,**_):
        ids=list(sacrifice_uids or [])
        if len(ids)!=len(set(ids)) or any(u not in self.permanents or not self.permanents[u].creature or self.permanents[u].controller!=0 for u in ids):
            raise BridgeError('S13: Plumb sacrifices distinct controlled creatures')
        name='Plumb the Forbidden'; self._begin(physical_uid,name,(1,0,1))
        self.plumb_the_forbidden(ids)                                          # frozen: pays {1}{B}, sacrifices, original + copies, Magecraft
        self.pending.append(Trigger(name+' card to graveyard (S13)',lambda:self._finish_to_graveyard(physical_uid,name)))
        self.assert_bridge_integrity(); return self.zones.cards[physical_uid]
    def _nonland_permanent(self,uid):
        p=self.permanents.get(uid)
        if p is None: return False
        ph=self.linked_battlefield.get(uid)
        return not (ph is not None and self.zones.cards[ph].is_land)
    def _s13_immoral_bargain(self,physical_uid,cost,*,x,sacrifice_uids,target_uids,**_):
        ids=list(sacrifice_uids or []); targets=list(target_uids or [])
        if not isinstance(x,int) or x<0 or len(ids)!=x or len(targets)!=x or len(set(targets))!=x or len(set(ids))!=x:
            raise BridgeError('S13: Immoral Bargain needs X sacrifices and X distinct targets')
        if any(u not in self.permanents or not self.permanents[u].creature or self.permanents[u].controller!=0 for u in ids):
            raise BridgeError('S13: sacrifices must be controlled creatures')
        if any(not self._nonland_permanent(u) for u in targets): raise BridgeError('S13: targets must be nonland permanents')
        name='Immoral Bargain'; self._begin(physical_uid,name,(1,1,1)); self.pay_mana(black=1,green=1,generic=1)
        self.immoral_bargain(x,ids,targets)                                    # frozen: validates, sacrifices, 'cast', Magecraft; destroys nothing
        def resolve():
            legal=[u for u in targets if self._nonland_permanent(u)]
            if targets and not legal: self.trace.append(('spell_fizzles_all_targets_illegal',name))
            for u in legal:
                p=self.permanents[u]
                if p.controller!=0: self._opponent_creature_dies(u,cause=name)
                elif p.creature: self.destroy(u)
                else: self._destroy_supported_noncreature(u)
            self._finish_to_graveyard(physical_uid,name)
        self.pending.append(Trigger(name+' resolution (S13)',resolve)); self.assert_bridge_integrity(); return self.zones.cards[physical_uid]
    ENCHANTMENTS={'Bastion of Remembrance','Moldervine Reclamation','Dark Prophecy','Grave Pact','Blight Mound','Feral Appetite','Phyrexian Reclamation','Agent of the Iron Throne','The Hunger Tide Rises'}   # the frozen kernel's own list
    def _infestation_target(self,uid):
        p=self.permanents.get(uid); return p is not None and (p.artifact or p.name in self.ENCHANTMENTS)
    def _s13_pest_infestation(self,physical_uid,cost,*,x,target_uids,**_):
        if not isinstance(x,int) or x<0: raise BridgeError('S13: Pest Infestation needs X >= 0')
        pool=self.mana_pool
        if pool.count('G')<1 or len(pool)<1+2*x: raise BridgeError('S13: mana unavailable for Pest Infestation')
        targets=tuple(target_uids or ())
        if len(targets)>x or len(set(targets))!=len(targets) or any(not self._infestation_target(u) for u in targets):
            raise BridgeError('S13: Pest Infestation targets up to X distinct artifacts/enchantments')
        name='Pest Infestation'; self._begin(physical_uid,name,(0,1,2*x))
        self.pest_infestation(x,target_uids=targets)                           # frozen: re-validates, pays {X}{X}{G}, resolution, Magecraft
        self.pending.append(Trigger(name+' card to graveyard (S13)',lambda:self._finish_to_graveyard(physical_uid,name)))
        self.assert_bridge_integrity(); return self.zones.cards[physical_uid]

# ---- driver ------------------------------------------------------------------
def tutor_selection(g):
    """Fixed policy: a basic land while fewer than four lands are controlled, else Grave Pact if in
    the library, else the first creature card in the library."""
    lands=sum(1 for ph in g.linked_battlefield.values() if g.zones.cards[ph].is_land); lib=g.zones.zones['library']
    if lands<4:
        u=next((u for u in lib if g.zones.cards[u].name in ('Swamp','Forest')),None)
        if u is not None: return u
    u=next((u for u in lib if g.zones.cards[u].name=='Grave Pact'),None)
    if u is not None: return u
    return next((u for u in lib if g.zones.cards[u].name in _s7.CREATURES),None)

def cast_when_able(g):
    """S12 pass, then the S13 spells with fixed policies (Immoral Bargain is not driven)."""
    cast=_cast_s12(g)
    for uid in list(g.zones.zones['hand']):
        name=g.zones.cards[uid].name
        if name not in S13_NAMES or not _s7._affordable(g,SPELLS[name]): continue
        kw={}
        if name in ('Demonic Tutor','Diabolic Intent'):                      # CP13: no preselection; _tutor selects at resolution
            if name=='Diabolic Intent':
                f=_s7._fodder(g)
                if f is None: continue
                kw['sacrifice_uid']=f
        elif name=='Hunt for Specimens': kw['learn']='lesson' if (g.learn_sideboard_allowed and g.zones.zones['outside_game']) else None
        elif name=='Pest Summoning':
            if sum(g.mana_pool.count(c) for c in 'BG')<2: continue
        elif name=='Unearth':
            cands=[p for p in g.graveyard if p.creature and not p.token and p.mana_value<=3 and p.name!='Savra, Queen of the Golgari']
            if not cands: continue
            kw['target_uid']=max(cands,key=lambda p:(p.mana_value,p.uid)).uid
        elif name=='Plumb the Forbidden':
            toks=[p.uid for p in g.permanents.values() if p.controller==0 and p.token is not None and p.creature]
            if len(toks)<2: continue
            kw['sacrifice_uids']=toks
        elif name=='Immoral Bargain': continue
        elif name=='Pest Infestation': kw['x']=(len(g.mana_pool)-1)//2
        g.cast_from_hand(uid,**kw); check_invariants_s11(g); g.resolve(); check_invariants_s11(g); cast.append(name)
    return cast

def run_turns_casting(g,turns):
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
