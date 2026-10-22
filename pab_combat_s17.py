"""Stage S17 (authorized 2026-10-18 11:05): combat — the controller attacks.

Layered above pab_grist_s16.GristMixin (PhysicalZoneGame only). No frozen file edited.
The clock already walks the combat steps (S1). S17 gives them content, for the controller's
attacks only (opponents never attack: they do not decide):

  declare_attackers(assignments)   in the controller's declare_attackers step, before anything
      is pending: assignments = [(creature_uid, defending_seat), ...]. Legal attackers are
      untapped creatures the controller has controlled continuously since the turn began
      (CR 302.6; `entered_turn` is recorded by add(); Yahenni has haste, CR 702.10) against
      seats still in the game. Attacking taps the creature (no vigilance in the deck) and the
      frozen attack_with() enqueues the attack triggers (Moseo's Pest, Teacher's Pest).
  blocks                             at the start of the declare_blockers step, each defending
      seat blocks by a fixed, documented policy (block_policy): 'none' (default), or 'all' —
      each of the seat's untapped creatures blocks the highest-power attacker aimed at that
      seat that it can legally block (menace from Blight Mound on attacking Pests needs two
      blockers, CR 702.110b; CP43, A-S20-05: a blocker takes a menace attacker when another
      untapped blocker of that seat is still to come, which then joins it, so the seat's
      blockers coordinate). Opponents' creatures are generic bodies: no flying/reach on their side.
      CP37: so they cannot block an attacker with flying (CR 702.9b: FLYING_NAMES, or a token
      kind with flying); intrinsic menace (MENACE_NAMES) counts like Blight Mound's.
  combat damage                      at the combat_damage step, simultaneously (CR 510.2):
      unblocked attackers deal their power (printed + counters + until-end-of-turn changes +
      Feral Appetite's and Blight Mound's +1/+0 for attacking Pests) to the defending player;
      blocked attackers and blockers deal damage to each other (one blocker per attacker in
      this policy; an attacker blocked by several assigns all damage to the first in uid
      order, lethal first — a documented simplification). Deathtouch (Poison-Tip Archer, South
      Wind Avatar, Feral Appetite's attacking Pests) makes any damage lethal (CR 702.2b).
      Damage is marked (`damage_marked`), state-based actions then kill creatures with lethal
      damage (CR 704.5g, the S3 loop with look-back), and marked damage clears at cleanup.
      CP37: lethal damage destroys, so an indestructible creature stays (CR 702.12b) and a
      regeneration shield replaces the destruction (CR 701.15a: shield used, damage removed,
      tapped, removed from combat); Skullclamp's +1/-1 counts in power and toughness.
  commander damage                   damage from Savra to a player is tracked per seat
      (`commander_damage`); 21 or more from her makes that seat lose at the next SBA check
      (CR 903.10a, 704.6c). CP37: the seat leaves with its life total unchanged.
  life                               opponents' life goes down; S8 removes a seat at 0 or
      less; the controller is never attacked.

Not modeled: opponents attacking, first/double strike, trample, lifelink (none in the deck),
flying/reach on opponents' side (their bodies have no keywords), multiple blockers' damage
order choices, combat tricks after blocks, forestwalk (opponents control no lands).
"""
from __future__ import annotations
from pab_grist_s16 import GristMixin, check_invariants_s16
from pab_opponents_s8 import OPPONENT_SEATS
from pab_clock_s3 import _LookBack
from pab_zone_bridge import BridgeError
from pab_focus_engine import SAVRA

from pab_keywords_cp43 import KEYWORDS

# CP43: printed keywords of the old-baseline creatures, read from the pinned card data (pab_keywords_cp43.py);
# hand-written lists with the same contents before (S17; CP37 K9, K10).
DEATHTOUCH_NAMES=KEYWORDS['deathtouch']
HASTE_NAMES=KEYWORDS['haste']
FLYING_NAMES=KEYWORDS['flying']
MENACE_NAMES=KEYWORDS['menace']
CANT_BLOCK_NAMES=KEYWORDS['cant_block']
COMMANDER_DAMAGE_LOSS=21

class CombatMixin(GristMixin):
    def __init__(self,*a,block_policy='none',**kw):
        super().__init__(*a,**kw)
        self.block_policy=block_policy; self.attackers={}; self.blocks={}; self.damage_marked={}
        self.commander_damage={s:0 for s in OPPONENT_SEATS}; self.combat_log=[]; self._indestructible_lethal_noted=set()
    def add(self,name,**kw):
        p=super().add(name,**kw); p.entered_turn=self.clock.turn if self.clock_engaged else 0; return p
    def make_tokens(self,kind,count=1,*,controller=0):
        made=super().make_tokens(kind,count,controller=controller)
        for p in made: p.entered_turn=self.clock.turn if self.clock_engaged else 0
        return made

    # ---- helpers ----
    def _current_power(self,p):
        v=super()._current_power(p)                                                # CP37 (K4): Skullclamp, until-end-of-turn changes
        if p.controller==0 and p.uid in self.attackers and 'Pest' in p.subtypes:
            v+=self.has('Feral Appetite')+self.has('Blight Mound')
        return v
    def _power(self,p): return max(0,self._current_power(p))
    def _toughness(self,p): return self._current_toughness(p)
    def _deathtouch(self,p):
        return p.controller==0 and (p.name in DEATHTOUCH_NAMES or (p.uid in self.attackers and 'Pest' in p.subtypes and self.has('Feral Appetite')>0))
    def _menace(self,p):
        return p.controller==0 and p.uid in self.attackers and (p.name in MENACE_NAMES or ('Pest' in p.subtypes and self.has('Blight Mound')>0))
    def _flying(self,p): return p.controller==0 and (p.name in FLYING_NAMES or (p.token is not None and p.token.flying))   # CP37 (K9)
    def _lethally_damaged(self,p):
        d=self.damage_marked.get(p.uid,0)
        return bool(d) and (d>=self._toughness(p) or bool(self.damage_marked.get(('deathtouch',p.uid))))
    def _dying_by_toughness(self):
        base=super()._dying_by_toughness(); ids={p.uid for p in base}
        for p in self.permanents.values():
            # CP37 (K1): lethal damage destroys (CR 704.5g/h); an indestructible creature is not destroyed (CR 702.12b)
            if p.creature and p.uid not in ids and p.uid not in self.indestructible_until_eot and self._lethally_damaged(p): base.append(p)
        return base
    def _sba_reason(self,p): return 'lethal_damage' if self._toughness(p)>0 else super()._sba_reason(p)   # CP39
    def _lethal_damage_replacements(self):
        """CP37 (K1), before the SBA event: a lethally damaged indestructible creature stays (traced once); one with a
        regeneration shield is regenerated instead (CR 701.15a). Toughness 0 or less still kills (CR 704.5f).
        Runs once per check, before the event: lethal damage is only marked by combat damage, before the check."""
        for p in list(self.permanents.values()):
            if not p.creature or self._toughness(p)<=0 or not self._lethally_damaged(p): continue
            if p.uid in self.indestructible_until_eot:
                if p.uid not in self._indestructible_lethal_noted:
                    self._indestructible_lethal_noted.add(p.uid); self.trace.append(('lethal_damage_indestructible',p.uid,p.name))
            elif p.uid in self.regen_shields: self._regenerate(p)
    def _regenerate(self,p):
        super()._regenerate(p); uid=p.uid                                           # CP37 (K1): CR 701.15a in combat
        self.damage_marked.pop(uid,None); self.damage_marked.pop(('deathtouch',uid),None)
        self.attackers.pop(uid,None); self.blocks.pop(uid,None)
        for bs in self.blocks.values():
            if uid in bs: bs.remove(uid)

    # ---- declare attackers ----
    def declare_attackers(self,assignments):
        c=self.clock
        if not (self.clock_engaged and c.is_controller_turn and c.step=='declare_attackers'): raise BridgeError('S17: attackers are declared in your declare-attackers step')
        if self.pending: raise BridgeError('S17: the stack must be empty')
        if self.attackers: raise BridgeError('S17: attackers already declared this combat')
        seen=set()
        for uid,seat in assignments:
            p=self.permanents.get(uid)
            if p is None or p.controller!=0 or not p.creature: raise BridgeError('S17: attack with creatures you control')
            if uid in seen: raise BridgeError('S17: a creature attacks once')
            if p.tapped: raise BridgeError('S17: a tapped creature cannot attack')
            if getattr(p,'entered_turn',0)==c.turn and p.name not in HASTE_NAMES: raise BridgeError('S17: summoning sickness (CR 302.6)')
            if seat not in self.seats_in_game(): raise BridgeError('S17: attack a seat still in the game')
            seen.add(uid)
        for uid,seat in assignments:
            p=self.permanents[uid]; p.tapped=True
            ph=self.linked_battlefield.get(uid)
            if ph is not None: self.zones.cards[ph].tapped=True
            tk=getattr(self,'linked_tokens',{}).get(uid)
            if tk is not None: self.zones.cards[tk].tapped=True
            self.attackers[uid]=seat; self.attack_with(uid)
        self.trace.append(('attackers_declared',tuple(assignments))); self.assert_bridge_integrity()

    # ---- the clock drives blocks, damage and cleanup ----
    def advance_step(self):
        turn,ap,phase,step=super().advance_step()
        if ap==0 and step=='declare_blockers' and self.attackers: self._declare_blocks()
        elif ap==0 and step=='combat_damage' and self.attackers: self._combat_damage()
        elif step=='end_of_combat': self.attackers={}; self.blocks={}
        if step=='cleanup':
            if self.damage_marked: self.trace.append(('damage_wears_off',tuple(sorted(k for k in self.damage_marked if not isinstance(k,tuple)))))
            self.damage_marked={}; self._indestructible_lethal_noted.clear()
        return turn,ap,phase,step
    def _declare_blocks(self):
        self.blocks={}
        if self.block_policy=='none': self.trace.append(('blocks_declared',())); return
        if self.block_policy!='all': raise BridgeError('S17: unknown block_policy')
        for seat in self.seats_in_game():
            targets=[u for u,s in self.attackers.items() if s==seat and u in self.permanents]
            if not targets: continue
            free=[b for b in sorted(self.opponent_creatures(seat),key=lambda q:(-self._power(q),q.uid)) if not b.tapped]
            cands=sorted(targets,key=lambda u:(-self._power(self.permanents[u]),u))
            for i,b in enumerate(free):
                pick=next((u for u in cands if not self._flying(self.permanents[u])
                           and (not self._menace(self.permanents[u]) or self.blocks.get(u) or i+1<len(free))),None)   # CP43 (A-S20-05): a second blocker is still to come
                if pick is None: continue
                self.blocks.setdefault(pick,[]).append(b.uid)
        self.trace.append(('blocks_declared',tuple((a,tuple(bs)) for a,bs in self.blocks.items())))
    def _combat_damage(self):
        events=[]
        for a,seat in list(self.attackers.items()):
            p=self.permanents.get(a)
            if p is None: continue
            blockers=[b for b in self.blocks.get(a,[]) if b in self.permanents]
            dmg=self._power(p)
            if not blockers:
                if seat not in self.seats_in_game(): continue
                self.life[seat]-=dmg; events.append(('player',seat,a,dmg))
                if p.name==SAVRA and p.uid in self.linked_battlefield: self.commander_damage[seat]+=dmg
            else:
                first=blockers[0]; self.damage_marked[first]=self.damage_marked.get(first,0)+dmg
                if self._deathtouch(p) and dmg>0: self.damage_marked[('deathtouch',first)]=True
                events.append(('creature',first,a,dmg))
                for b in blockers:
                    q=self.permanents[b]; bd=self._power(q); self.damage_marked[a]=self.damage_marked.get(a,0)+bd; events.append(('creature',a,b,bd))
        self.trace.append(('combat_damage',tuple(events))); self.combat_log.append((self.clock.turn,tuple(events)))
        self.state_based_actions()
    def state_based_actions(self):
        self._lethal_damage_replacements()
        for seat in OPPONENT_SEATS:        # CP37 (K12): traced here, the seat leaves in S8's check below; life is not changed
            if seat not in self.lost_seats and self.commander_damage[seat]>=COMMANDER_DAMAGE_LOSS:
                self.trace.append(('commander_damage_loss',seat,self.commander_damage[seat]))
        return super().state_based_actions()
    def _seat_has_lost(self,seat):
        return super()._seat_has_lost(seat) or self.commander_damage[seat]>=COMMANDER_DAMAGE_LOSS

# ---- invariants and driver ----
def check_invariants_s17(g):
    check_invariants_s16(g)
    if g.attackers and g.clock.step not in ('declare_attackers','declare_blockers','combat_damage','end_of_combat'): raise AssertionError('S17: attackers outside combat')
    for a in g.attackers:
        if a in g.permanents and not g.permanents[a].tapped: raise AssertionError('S17: an attacking creature is untapped')
    for a,bs in g.blocks.items():   # CP43 (A-S20-05): CR 702.110b
        if a in g.permanents and g._menace(g.permanents[a]) and len(bs)==1: raise AssertionError('S17: a menace attacker has a lone blocker')

def attack_policy(g):
    """Fixed policy: every legal attacker except Savra attacks the opponent with the lowest life
    (ties: lowest seat); Savra attacks only when she would not be blocked by the 'all' policy."""
    seats=g.seats_in_game()
    if not seats: return []
    target=min(seats,key=lambda s:(g.life[s],s)); out=[]
    for p in g.permanents.values():
        if p.controller!=0 or not p.creature or p.tapped or (getattr(p,'entered_turn',0)==g.clock.turn and p.name not in HASTE_NAMES): continue
        if p.name==SAVRA and g.block_policy!='none' and any(not q.tapped for q in g.opponent_creatures(target)): continue
        out.append((p.uid,target))
    return out

def run_turns_full(g,turns):
    """S15 driver plus combat each controller turn. Ledger: (turn, land, mana, cast, attackers, damage_events)."""
    from pab_lands_s14 import LAND_MANA_DRIVER
    from pab_lands_s9 import play_land_policy, tap_lands_policy
    from pab_commander_s10 import commander_need, cast_commander_when_able
    from pab_cast_s15 import cast_when_able
    ledger=[]; start=g.clock.turn; row=None
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s17(g)
        if ap!=0: continue
        if st=='precombat_main':
            u,kw=play_land_policy(g,LAND_MANA_DRIVER); played=None
            if u is not None: played=g.play_physical_land(u,**kw).name; g.resolve(); check_invariants_s17(g)
            mana=tap_lands_policy(g,extra=commander_need(g),land_mana=LAND_MANA_DRIVER)
            cast=[SAVRA] if cast_commander_when_able(g) else []
            cast+=cast_when_able(g); check_invariants_s17(g); row=[t,played,tuple(mana),tuple(cast),(),()]
        elif st=='declare_attackers' and row is not None:
            a=attack_policy(g)
            if a: g.declare_attackers(a); g.resolve(); check_invariants_s17(g)
            row[4]=tuple(a)
        elif st=='combat_damage' and row is not None:
            row[5]=g.combat_log[-1][1] if g.combat_log and g.combat_log[-1][0]==t else ()
        elif st=='cleanup' and row is not None: ledger.append(tuple(row)); row=None
    return ledger
