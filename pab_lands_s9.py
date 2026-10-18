"""Stage S9 (Task 3b, authorized 2026-10-18): the black-green fixer lands.

Layered above pab_opponents_s8.OpponentsMixin (PhysicalZoneGame only). No frozen file edited.
The frozen pab_zones.SUPPORTED_LAND_MANA (Forest, Swamp, Command Tower) is not touched; the
frozen zones.play_land / tap_land_for_mana still fail closed for every other name. S9 adds
play_physical_land / tap_physical_land_for_mana handling for the nine nonbasic lands of the
deck that produce {B} or {G} (EVIDENCE/S9_LAND_EVIDENCE.json), reproducing the frozen
physical land-play procedure (hand check, one land per turn, move to battlefield, land-play
count, 'land_played' trace, add() + linked_battlefield, 'physical_land_played' trace) with
each card's enters-the-battlefield condition and mana ability:

  Blooming Marsh        tapped unless you control two or fewer other lands; {T}: B or G
  Deathcap Glade        tapped unless you control two or more other lands;  {T}: B or G
  Woodland Cemetery     tapped unless you control a Swamp or a Forest (land TYPES: basics,
                        Overgrown Tomb, Underground Mortuary); {T}: B or G
  Undergrowth Stadium   tapped unless you have two or more opponents (seats still in the
                        game, S8); {T}: B or G
  Overgrown Tomb        Swamp Forest; as it enters you may pay 2 life (pay_life=True) or it
                        enters tapped; {T}: B or G
  Underground Mortuary  Swamp Forest; enters tapped; when it enters, surveil 1 — a trigger
                        whose choice is pre-committed at play time (surveil_graveyard=
                        False keeps the card on top; True mills it), CR 701.46
  Darkbore Pathway //   modal double-faced land: play_physical_land(..., face='Darkbore')
  Slitherbore Pathway   taps for {B}, face='Slitherbore' taps for {G}; face is required.
                        The bridge requires permanent.name == physical name, so the
                        permanent keeps the full card name and records `face`; CR 712.8
                        says only the played face's characteristics exist — the name
                        compromise is documented, the mana ability follows the face.
  Llanowar Wastes       {T}: C (no damage) or {T}: B or G and 1 damage to you (life loss,
                        no prevention modeled); untapped
  Nurturing Peatland    {T}, pay 1 life: B or G; untapped; its sacrifice-draw ability is
                        not modeled

Not modeled: the other nine nonbasic lands (Boseiju, Castle Locthwain, Geier Reach,
Grim Backwoods, High Market, Mikokoro, Phyrexian Tower, Takenuma, Verdant Catacombs) —
still fail closed; Channel; land destruction; Nature's Lore for nonbasic Forests (the
frozen bridge's basic-only subset is unchanged).
"""
from __future__ import annotations
from pab_opponents_s8 import OpponentsMixin, check_invariants_s8
from pab_clock_s4 import MAIN_STEPS
from pab_turn_clock import ClockError
from pab_zone_bridge import BridgeError
from pab_zones import SUPPORTED_LAND_MANA, BASIC_LANDS
from pab_focus_engine import Trigger
import pab_turn_loop as _loop
import pab_cast_s7 as _s7

PATHWAY='Darkbore Pathway // Slitherbore Pathway'
PATHWAY_FACES={'Darkbore':'B','Slitherbore':'G'}
SWAMP_FOREST_TYPED=frozenset({'Forest','Swamp','Overgrown Tomb','Underground Mortuary'})   # lands with the Swamp or Forest subtype

# name -> ('B','G') producers plus their entry/tap rules; see EVIDENCE/S9_LAND_EVIDENCE.json
FIXERS={
  'Blooming Marsh':      {'mana':('B','G'),'enters':'tapped_unless_at_most_2_other_lands'},
  'Deathcap Glade':      {'mana':('B','G'),'enters':'tapped_unless_at_least_2_other_lands'},
  'Woodland Cemetery':   {'mana':('B','G'),'enters':'tapped_unless_swamp_or_forest'},
  'Undergrowth Stadium': {'mana':('B','G'),'enters':'tapped_unless_2_or_more_opponents'},
  'Overgrown Tomb':      {'mana':('B','G'),'enters':'tapped_unless_pay_2_life'},
  'Underground Mortuary':{'mana':('B','G'),'enters':'tapped','etb':'surveil_1'},
  PATHWAY:               {'mana':('B','G'),'enters':'untapped','modal':True},
  'Llanowar Wastes':     {'mana':('B','G','C'),'enters':'untapped','colored_damage':1},
  'Nurturing Peatland':  {'mana':('B','G'),'enters':'untapped','tap_life':1},
}
S9_NAMES=frozenset(FIXERS)
# Frozen v0.8 bridge fixtures that pinned 'fail closed' for two of these lands; superseded the R01/R52 way
# (corrected full copy in s9_tests/test_v08_mana_tokens_s9.py). The frozen file is untouched.
SUPERSEDED_V08_FIXTURES=frozenset({'test_274_unsupported_land_fails_closed','test_307_unsupported_named_nonbasic_mana_does_not_fallback'})
LAND_MANA={**SUPPORTED_LAND_MANA,**{n:s['mana'] for n,s in FIXERS.items()}}   # everything a linked land can tap for after S9

class FixerLandsMixin(OpponentsMixin):
    # ---- play -----------------------------------------------------------------
    def play_physical_land(self,physical_uid,*,face=None,pay_life=False,surveil_graveyard=False,**kw):
        card=self.zones.cards.get(physical_uid)
        if card is not None and not card.token and card.name in S9_NAMES:
            return self._play_fixer(physical_uid,card,face=face,pay_life=pay_life,surveil_graveyard=surveil_graveyard,**kw)
        if face is not None or pay_life or surveil_graveyard:
            raise BridgeError('S9: face / pay_life / surveil_graveyard apply only to the S9 lands')
        return super().play_physical_land(physical_uid,**kw)

    def _land_timing(self,main_phase,stack_empty):
        if self.clock_engaged:
            if main_phase is not None or stack_empty is not None: raise BridgeError('S9: timing is clock-derived once the clock is engaged')
            c=self.clock
            if not c.is_controller_turn: raise ClockError('land play only on your own turn (305.1)')
            main_phase=c.step in MAIN_STEPS; stack_empty=not self.pending
        else:
            if main_phase is None: main_phase=True
            if stack_empty is None: stack_empty=True
        if not main_phase or not stack_empty: raise BridgeError('S9: land play requires your main phase and an empty stack (305.1)')

    def _controlled_lands(self):
        return [self.zones.cards[ph] for ev,ph in self.linked_battlefield.items() if self.zones.cards[ph].is_land]

    def _enters_tapped(self,spec,*,pay_life):
        rule=spec['enters']; others=self._controlled_lands()
        if rule=='untapped': return False
        if rule=='tapped': return True
        if rule=='tapped_unless_at_most_2_other_lands': return not (len(others)<=2)
        if rule=='tapped_unless_at_least_2_other_lands': return not (len(others)>=2)
        if rule=='tapped_unless_swamp_or_forest': return not any(c.name in SWAMP_FOREST_TYPED for c in others)
        if rule=='tapped_unless_2_or_more_opponents': return not (len(self.seats_in_game())>=2)
        if rule=='tapped_unless_pay_2_life':
            if not pay_life: return True
            if not self.pay_life(2,'Overgrown Tomb'): raise BridgeError('S9: cannot pay 2 life for Overgrown Tomb')
            return False
        raise BridgeError('S9: unknown entry rule')

    def _play_fixer(self,physical_uid,card,*,face,pay_life,surveil_graveyard,main_phase=None,stack_empty=None):
        spec=FIXERS[card.name]
        self._land_timing(main_phase,stack_empty)
        self.zones._require_in_zone(physical_uid,'hand')
        if self.zones.land_plays_this_turn>=1: raise BridgeError('S9: only one land play per turn (305.2)')
        if spec.get('modal'):
            if face not in PATHWAY_FACES: raise BridgeError('S9: a Pathway is played as exactly one of its faces')
        elif face is not None: raise BridgeError(f'S9: {card.name} has no faces to choose')
        if pay_life and spec['enters']!='tapped_unless_pay_2_life': raise BridgeError(f'S9: {card.name} offers no life payment')
        if surveil_graveyard and spec.get('etb')!='surveil_1': raise BridgeError(f'S9: {card.name} does not surveil')
        # ---- mutation (same order as the frozen physical land play) ----
        tapped=self._enters_tapped(spec,pay_life=pay_life)                 # Overgrown Tomb's payment happens here (as it enters)
        self.zones.move(physical_uid,'battlefield',controller=0)
        card.tapped=tapped
        self.zones.land_plays_this_turn+=1
        self.zones.trace.append(('land_played',physical_uid,card.name))
        p=self.add(card.name,colors='',creature=False,artifact=False,tapped=tapped)
        if spec.get('modal'): p.face=face
        self.linked_battlefield[p.uid]=physical_uid
        self.trace.append(('physical_land_played',p.uid,physical_uid,card.name))
        self.trace.append(('s9_land_entered',card.name,face,'tapped' if tapped else 'untapped'))
        if spec.get('etb')=='surveil_1':
            self._enqueue([Trigger('Underground Mortuary surveil 1',lambda:self._surveil_1(surveil_graveyard))])
        self.assert_bridge_integrity()
        return p

    def _surveil_1(self,to_graveyard):
        lib=self.zones.zones['library']
        if not lib: self.trace.append(('surveil',None,'empty library')); return
        top=self.zones.cards[lib[0]]
        if to_graveyard: self.zones.mill(1); self.trace.append(('surveil',top.uid,'graveyard'))
        else: self.trace.append(('surveil',top.uid,'top'))

    # ---- tap ------------------------------------------------------------------
    def tap_physical_land_for_mana(self,event_uid,*,color=None):
        p=self.permanents.get(event_uid)
        if p is None or p.name not in S9_NAMES: return super().tap_physical_land_for_mana(event_uid,color=color)
        physical_uid=self.linked_battlefield.get(event_uid)
        if physical_uid is None: raise BridgeError('S9: land is not a linked physical land')
        card=self.zones._require_in_zone(physical_uid,'battlefield')
        if not card.is_land or card.controller!=0 or card.tapped or p.tapped or p.name!=card.name:
            raise BridgeError('S9: land must be a coherent, controlled, untapped linked land')
        spec=FIXERS[p.name]
        if spec.get('modal'):
            choices=(PATHWAY_FACES[p.face],)
        else: choices=spec['mana']
        if color is None and len(choices)==1: color=choices[0]
        if color not in choices: raise BridgeError(f'S9: {p.name} cannot produce {color}')
        if spec.get('tap_life') and not self.pay_life(spec['tap_life'],p.name):
            raise BridgeError(f'S9: cannot pay life to tap {p.name}')
        card.tapped=True; p.tapped=True
        self.mana_pool.append(color)
        self.zones.trace.append(('land_tapped_for_mana',physical_uid,color))
        self.trace.append(('physical_land_mana',event_uid,physical_uid,color))
        if spec.get('colored_damage') and color!='C':
            self.trace.append(('damage_to_controller',spec['colored_damage'],p.name))
            self.lose_life(spec['colored_damage'],p.name)                  # CR 120.3e: damage to a player is life loss
        self.assert_bridge_integrity()
        return color

# ---- driver ------------------------------------------------------------------
def playable_land_in_hand(g):
    for u in g.zones.zones['hand']:
        if g.zones.cards[u].name in LAND_MANA: return u
    return None

def _need(g):
    hand=[g.zones.cards[u].name for u in g.zones.zones['hand']]
    return {'B':sum(_s7.CASTABLE[n]['cost'][0] for n in hand if n in _s7.CASTABLE),
            'G':sum(_s7.CASTABLE[n]['cost'][1] for n in hand if n in _s7.CASTABLE)}

def play_land_policy(g):
    """Fixed, documented choices: Pathway face = the colour the hand needs more (G ties to B);
    Overgrown Tomb: pay 2 life while life > 10; Mortuary surveil: keep a land on top when the
    hand holds no land, otherwise mill. Returns the kwargs for play_physical_land."""
    u=playable_land_in_hand(g)
    if u is None: return None,{}
    name=g.zones.cards[u].name; kw={}
    if name==PATHWAY:
        need=_need(g); kw['face']='Slitherbore' if need['G']>need['B'] else 'Darkbore'
    elif name=='Overgrown Tomb': kw['pay_life']=g.life[0]>10
    elif name=='Underground Mortuary':
        lib=g.zones.zones['library']; top=g.zones.cards[lib[0]] if lib else None
        hand_has_land=any(g.zones.cards[x].is_land for x in g.zones.zones['hand'] if x!=u)
        kw['surveil_graveyard']=not (top is not None and top.is_land and not hand_has_land)
    return u,kw

def tap_lands_policy(g,extra=None):
    """Tap every untapped linked land; dual lands give the colour the hand is short of;
    Llanowar Wastes gives {C} unless a colour is short; Peatland pays its life.
    `extra` (S10): additional colour needs, e.g. Savra in the command zone."""
    produced=[]; need=_need(g)
    for k,v in (extra or {}).items(): need[k]=need.get(k,0)+v
    for ev,ph in list(g.linked_battlefield.items()):
        p=g.permanents.get(ev); c=g.zones.cards[ph]
        if p is None or p.tapped or not c.is_land or c.name not in LAND_MANA: continue
        spec=FIXERS.get(c.name); color=None
        choices=(PATHWAY_FACES[p.face],) if spec and spec.get('modal') else LAND_MANA[c.name]
        if len(choices)>1:
            pool=g.mana_pool+produced
            short=[x for x in ('G','B') if pool.count(x)<need[x] and x in choices]
            color=short[0] if short else ('C' if 'C' in choices else 'B')
        produced.append(g.tap_physical_land_for_mana(ev,color=color)); check_invariants_s8(g)
    return produced

def run_turns_casting(g,turns):
    """S7 driver shape with S9 land play and tapping; ledger of (turn, land_played, mana, names_cast)."""
    ledger=[]; start=g.clock.turn
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s8(g)
        if ap!=0 or st!='precombat_main': continue
        u,kw=play_land_policy(g); played=None
        if u is not None:
            played=g.play_physical_land(u,**kw).name; g.resolve(); check_invariants_s8(g)
        mana=tap_lands_policy(g)
        cast=_s7.cast_when_able(g); check_invariants_s8(g)
        ledger.append((t,played,tuple(mana),tuple(cast)))
    return ledger
