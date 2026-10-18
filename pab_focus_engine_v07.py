"""PABTRV3 reference event kernel v0.5 (NOT a full Commander rules engine).

Strictly scoped: controlled sacrifice/death/token/lifegain, limited named entry,
upkeep, attack and recursion contracts. No full casting/mana, opponents, priority,
or full game-state-based actions. All effects must be invoked explicitly; support
boundaries are documented in COVERAGE.json and README.md.

Facts are derived from the frozen PABTRV3 focus package's recorded text.
The original simulator remains unchanged.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class TokenKind:
    label: str
    colors: str
    subtypes: frozenset[str]
    creature: bool = True
    dies_gain: int = 0
    attacks_gain: int = 0
    flying: bool = False
    artifact: bool = False


PEST = TokenKind('ordinary Pest', 'BG', frozenset({'Pest'}), dies_gain=1)
MOSEO_PEST = TokenKind('Moseo attack-gain Pest', 'BG', frozenset({'Pest'}), attacks_gain=1)
INSECT = TokenKind('Hunger Tide Insect', 'BG', frozenset({'Insect'}))
FLYING_INSECT = TokenKind('Infestation Sage Insect', 'BG', frozenset({'Insect'}), flying=True)
WORM = TokenKind('Wriggling Grub Worm', 'BG', frozenset({'Worm'}))
SQUIRREL = TokenKind('Chatterfang Squirrel', 'G', frozenset({'Squirrel'}))
HUMAN = TokenKind('Bastion Human Soldier', 'W', frozenset({'Human', 'Soldier'}))
TREASURE = TokenKind('Treasure', '', frozenset({'Treasure'}), creature=False, artifact=True)

SAVRA='Savra, Queen of the Golgari'

# Names here authorize only colors/types used by reference fixtures, not full cards.
BODIES = {
    SAVRA: 'BG', 'Dina, Soul Steeper': 'BG', 'Mirkwood Bats':'B',
    'Pest Rescuer':'G', 'Chatterfang, Squirrel General':'G',
    'Moseo, Vein\'s New Dean':'B', 'Blight Mound':'',
    'Bastion of Remembrance':'', 'Cauldron of Essence':'',
    'Reassembling Skeleton':'B', "Teacher's Pest":'BG',
    'Infestation Sage':'B', 'Wriggling Grub':'B',
    'Sedgemoor Witch':'B', 'Beledros Witherbloom':'BG',
    'Ribtruss Roaster':'G', 'South Wind Avatar':'B',
    'Agent of the Iron Throne':'', 'Deathgreeter':'B',
    'Blood Artist':'B', 'Poison-Tip Archer':'BG',
    'Marauding Blight-Priest':'B', 'Starscape Cleric':'B',
    'Moldervine Reclamation':'', 'Dark Prophecy':'',
    'Grave Pact':'', 'Prosperous Innkeeper':'G',
    'Essence Warden':'G', 'Feral Appetite':'',
    'Warren Soultrader':'B', 'Carrion Feeder':'B',
    'Viscera Seer':'B', 'Bogwater Lumaret':'BG', 'Sangromancer':'B',
    'Phyrexian Reclamation':'', 'Phyrexian Altar':'', 'Arcane Signet':'',
    'Yawgmoth, Thran Physician':'B', 'Yahenni, Undying Partisan':'B',
    'Sakura-Tribe Elder':'G',
    'Golgari Signet':'', 'Sol Ring':'', 'Skullclamp':'',
    'The Hunger Tide Rises':''
}
NONCREATURE = {'Blight Mound','Bastion of Remembrance', 'Cauldron of Essence',
               'Agent of the Iron Throne', 'Moldervine Reclamation',
               'Dark Prophecy','Grave Pact','Feral Appetite','Phyrexian Reclamation',
               'Phyrexian Altar','Arcane Signet','Golgari Signet','Sol Ring','Skullclamp',
               'The Hunger Tide Rises'}
ARTIFACT = {'Cauldron of Essence','Phyrexian Altar','Arcane Signet',
            'Golgari Signet','Sol Ring','Skullclamp'}


@dataclass
class Permanent:
    uid: int
    name: str
    controller: int
    colors: str
    creature: bool = True
    token: Optional[TokenKind] = None
    artifact: bool = False
    tapped: bool = False
    toughness: int = 1
    counters: int = 0
    mana_value: int = 0
    power: int = 1  # explicit known power in fixtures, not a continuous-layer engine
    minus_counters: int = 0  # selected Yawgmoth -1/-1 counter tests only

    @property
    def subtypes(self):
        if self.token: return self.token.subtypes
        return frozenset({'Pest'}) if self.name == "Teacher's Pest" else frozenset()


@dataclass
class Trigger:
    label: str
    action: Callable[[], None]


class IllegalAction(ValueError): pass


# Use the inherited canonical fixture types and exceptions so a versioned
# candidate does not manufacture a second token-identity universe.
from pab_focus_engine import (TokenKind, PEST, MOSEO_PEST, INSECT, FLYING_INSECT,
                              WORM, SQUIRREL, HUMAN, TREASURE, SAVRA, BODIES,
                              NONCREATURE, ARTIFACT, Permanent, Trigger,
                              IllegalAction)

class Game:
    """Controlled-object event trace. Default priority/stack order is *chosen* by controller.

    `pending` is in resolution order, including triggers from newer events, which
    resolve before older triggers. Does not arbitrate APNAP or opponent interactions.
    """
    def __init__(self, *, learn_sideboard_allowed=False, pay_savra_black=True,
                 choose_savra_green=True, choose_deathgreeter_gain=True,
                 choose_sangromancer_gain=True):
        self.life = [40,40,40,40]
        self.permanents: dict[int, Permanent] = {}
        self.graveyard: list[Permanent] = []
        self.hand: list[str] = []
        self.lesson_available = True
        self.learn_sideboard_allowed = learn_sideboard_allowed
        self.pay_savra_black = pay_savra_black
        self.choose_savra_green = choose_savra_green
        self.choose_deathgreeter_gain = choose_deathgreeter_gain
        self.choose_sangromancer_gain = choose_sangromancer_gain
        self.mana_pool: list[str] = []  # explicitly supplied mana, NO lands yet
        self.next_uid = 1
        self.pending: deque[Trigger] = deque()
        self.trace: list[tuple] = []
        self.edict_opportunities = 0
        self.opponent_sacrifices = 0  # no opponent objects: never invent a sacrifice
        self.cards_drawn = 0
        self.game_lost = False  # player zero life at a modeled priority boundary
        self.life_gained_turn = 0  # life gained by PAB controller, NOT net life
        self.cards_exiled: list[str] = []
        self.indestructible_until_eot: set[int] = set()  # Yahenni limited effect
        self.fixture_library_creatures: list[dict] = []  # explicit inputs only, NOT a full library
        self.fixture_library_lands: list[dict] = []  # Forest/Swamp basic-land fixtures ONLY
        self.skullclamp_attached: dict[int,int] = {}  # equipment UID -> creature UID; partial LKI

    def has(self, name):
        return sum(1 for p in self.permanents.values() if p.controller == 0 and p.name == name)

    def add(self, name, *, controller=0, colors=None, creature=None,
            artifact=None, toughness=1, mana_value=0, counters=0, tapped=False, power=1):
        if colors is None:
            if name not in BODIES:
                raise IllegalAction(f'No verified partial card definition for {name}')
            colors = BODIES[name]
        if creature is None: creature = name not in NONCREATURE
        if artifact is None: artifact = name in ARTIFACT
        p = Permanent(self.next_uid,name,controller,colors,creature,None,artifact,
                      tapped,toughness,counters,mana_value,power)
        self.next_uid += 1
        self.permanents[p.uid] = p
        self.trace.append(('enter',p.uid,name))
        if controller == 0:
            if name == 'Bastion of Remembrance': self.make_tokens(HUMAN)
            if name == "Moseo, Vein's New Dean": self.make_tokens(MOSEO_PEST)
            if name == 'Prosperous Innkeeper': self.make_tokens(TREASURE)
            if name == 'The Hunger Tide Rises':
                self._enqueue([Trigger('Hunger Tide ETB chapter I',lambda:self.saga_chapter(1))])
        if p.creature: self._enter_creature_triggers(p)
        return p

    def _enqueue(self, triggers):
        # One controller orders its triggers in this reference policy; first resolves first.
        if triggers: self.pending = deque(list(triggers)+list(self.pending))

    def resolve(self, max_resolutions=1000):
        n = 0
        if self.life[0] <= 0:
            self.game_lost=True; self.pending.clear()
            return 0
        while self.pending and not self.game_lost:
            if n >= max_resolutions: raise RuntimeError('Unbounded trigger chain')
            t=self.pending.popleft(); self.trace.append(('resolve',t.label))
            t.action(); n+=1
            # State-based actions occur between resolving stack objects, not between
            # simultaneous effects inside the same resolving trigger.
            if self.life[0] <= 0:
                self.game_lost=True
                self.trace.append(('lose_game','life_zero_or_less'))
                self.pending.clear()
        return n

    def _enter_creature_triggers(self, entered):
        effects=[]
        for p in tuple(self.permanents.values()):
            if p.controller == 0 and p.name == 'Bogwater Lumaret' and entered.controller == 0:
                effects.append(Trigger('Bogwater Lumaret controlled ETB',
                                       lambda: self.gain(1,'Bogwater Lumaret')))
            if p.controller == 0 and p.name == 'Essence Warden' and p.uid != entered.uid:
                effects.append(Trigger('Essence Warden ETB life',lambda: self.gain(1,'Essence Warden')))
            if p.controller == 0 and p.name == 'Prosperous Innkeeper' and p.uid != entered.uid and entered.controller == 0:
                effects.append(Trigger('Innkeeper ETB life',lambda: self.gain(1,'Prosperous Innkeeper')))
        self._enqueue(effects)

    def make_tokens(self, kind:TokenKind, count=1, *, controller=0):
        if count < 0: raise IllegalAction('Negative token creation count')
        # Chatterfang replaces the creation event ONCE, not recursively.
        kinds = [kind]*count
        if controller == 0 and self.has('Chatterfang, Squirrel General'):
            kinds += [SQUIRREL]*count
        effects=[]; produced=[]
        for k in kinds:
            p = Permanent(self.next_uid,k.label,controller,k.colors,k.creature,k,k.artifact)
            self.next_uid+=1; self.permanents[p.uid]=p; produced.append(p)
            self.trace.append(('token_created',p.uid,k.label,k.colors))
            if controller == 0:
                for bats in range(self.has('Mirkwood Bats')):
                    effects.append(Trigger('Mirkwood Bats creation drain',
                                           lambda: self.drain_opponents(1,'Mirkwood Bats create')))
            if k.creature:
                # Token enters simultanously in one creation event, and ETB checks all bodies.
                # collect triggers below, after the complete batch exists.
                pass
        self._enqueue(effects)
        for p in produced:
            if p.creature: self._enter_creature_triggers(p)
        return produced

    def pay_life(self, amount, source):
        if amount < 0 or self.life[0] < amount: return False
        self.life[0]-=amount
        self.trace.append(('pay_life',amount,source))
        return True

    def lose_life(self, amount,source):
        if amount < 0: raise IllegalAction('Negative life loss')
        self.life[0]-=amount
        self.trace.append(('lose_life',amount,source))

    def gain(self, amount,source):
        if amount <= 0: return
        amount += self.has('Pest Rescuer')  # replacement modifies one gain event
        self.life[0]+=amount; self.life_gained_turn+=amount
        self.trace.append(('gain',amount,source))
        effects=[]
        for name in ['Dina, Soul Steeper','Marauding Blight-Priest',
                     'Starscape Cleric','South Wind Avatar']:
            for _ in range(self.has(name)):
                effects.append(Trigger(name+' lifegain drain',
                    lambda n=name: self.drain_opponents(1,n+' lifegain')))
        self._enqueue(effects)

    def drain_opponents(self, amount, source):
        if amount <= 0: return
        for i in (1,2,3): self.life[i]-=amount
        self.trace.append(('opponents_lose_each',amount,source))

    def _leave(self, uid, *, sacrificed):
        if uid not in self.permanents: raise IllegalAction('Permanent not on battlefield')
        p=self.permanents[uid]
        if p.controller != 0: raise IllegalAction('Reference only accepts own controlled object')
        if not p.creature and not p.artifact: raise IllegalAction('Only creature/artifact sacrifice modeled')
        before = tuple(self.permanents.values())
        del self.permanents[uid]
        self.trace.append(('sacrifice' if sacrificed else 'destroy',uid,p.name))
        # Track an equipped creature's LKI for Skullclamp's death trigger,
        # and detach equipment when either the creature or equipment leaves.
        was_clamped = p.creature and any(target==uid for target in self.skullclamp_attached.values())
        self.skullclamp_attached = {k:v for k,v in self.skullclamp_attached.items()
                                    if k!=uid and v!=uid}
        # No immediate token graveyard recursion; tokens disappear after death triggers are queued.
        if not p.token: self.graveyard.append(p)
        effects=[]
        names = [x.name for x in before if x.controller==0]
        if sacrificed and p.creature and SAVRA in names:
            if 'B' in p.colors:
                def savra_black():
                    if self.pay_savra_black and self.pay_life(2,'Savra black option'):
                        self.edict_opportunities+=1
                        self.trace.append(('edict_opportunity',1,'Savra black'))
                effects.append(Trigger('Savra black sacrifice',savra_black))
            if 'G' in p.colors:
                def savra_green():
                    if self.choose_savra_green: self.gain(2,'Savra green option')
                effects.append(Trigger('Savra green sacrifice',savra_green))
        if sacrificed and p.token:
            for _ in range(names.count('Mirkwood Bats')):
                effects.append(Trigger('Mirkwood Bats token sacrifice',
                          lambda: self.drain_opponents(1,'Mirkwood Bats sacrifice')))
        # A token's own death trigger is derived from its SPEC, not its subtype.
        if p.creature:
            if was_clamped:
                effects.append(Trigger('Skullclamp equipped death draw two',
                     lambda: self._fixture_draw(2,'Skullclamp')))
            if p.token and p.token.dies_gain:
                effects.append(Trigger('Pest dies-gain',
                          lambda a=p.token.dies_gain: self.gain(a,'ordinary Pest death')))
            if p.name == 'Infestation Sage':
                effects.append(Trigger('Infestation Sage death Insect',
                          lambda:self.make_tokens(FLYING_INSECT)))
            if p.name == 'Wriggling Grub':
                effects.append(Trigger('Wriggling Grub death Worms',
                          lambda:self.make_tokens(WORM,2)))
            # Trigger counts snapshot just BEFORE the death; allows LKI self-deaths.
            for source in before:
                if source.controller != 0: continue
                name = source.name
                if name=='Grave Pact':
                    effects.append(Trigger('Grave Pact edict opportunity',
                                           lambda:self._grave_pact_opportunity()))
                if name=='Bastion of Remembrance':
                    effects.append(Trigger('Bastion death drain/gain',
                                           lambda:self._drain_and_gain('Bastion of Remembrance')))
                if name=='Cauldron of Essence':
                    effects.append(Trigger('Cauldron death drain/gain',
                                           lambda:self._drain_and_gain('Cauldron of Essence')))
                if name=='Dina, Soul Steeper': pass  # no death trigger
                if name=='Deathgreeter' and source.uid != p.uid:
                    if self.choose_deathgreeter_gain:
                        effects.append(Trigger('Deathgreeter death life',lambda:self.gain(1,'Deathgreeter')))
                if name=='South Wind Avatar' and source.uid != p.uid:
                    effects.append(Trigger('South Wind Avatar toughness-gain',
                                           lambda t=p.toughness:self.gain(t,'South Wind Avatar death')))
                if name=='Poison-Tip Archer' and source.uid != p.uid:
                    effects.append(Trigger('Poison-Tip Archer death drain',
                                  lambda:self.drain_opponents(1,'Poison-Tip Archer')))
                if name=='Moldervine Reclamation':
                    effects.append(Trigger('Moldervine death life/draw',lambda:self._moldervine()))
                if name=='Dark Prophecy':
                    effects.append(Trigger('Dark Prophecy death draw/loss',lambda:self._dark_prophecy()))
                if name=='Blood Artist':
                    effects.append(Trigger('Blood Artist target drain',lambda:self._blood_artist()))
                if name=='Blight Mound' and not p.token:
                    effects.append(Trigger('Blight Mound nontoken death Pest',
                                           lambda:self.make_tokens(PEST)))
            if SAVRA in names and 'Agent of the Iron Throne' in names:
                effects.append(Trigger('Agent-granted commander death drain',
                                      lambda:self.drain_opponents(1,'Agent of the Iron Throne')))
        elif p.artifact and SAVRA in names and 'Agent of the Iron Throne' in names:
            effects.append(Trigger('Agent-granted commander artifact drain',
                                   lambda:self.drain_opponents(1,'Agent of the Iron Throne')))
        self._enqueue(effects)
        return p

    def opposing_creature_dies(self, name='opponent creature'):
        """EXOGENOUS EVENT ONLY: no modeled opponent board, decision or removal.

        Used to validate our *existing* own-card global death triggers.
        """
        self.trace.append(('external_opponent_creature_dies', name))
        effects=[]
        for source in tuple(self.permanents.values()):
            if source.controller != 0: continue
            if source.name=='Deathgreeter' and self.choose_deathgreeter_gain:
                effects.append(Trigger('Deathgreeter opposing death',lambda:self.gain(1,'Deathgreeter')))
            if source.name=='Poison-Tip Archer':
                effects.append(Trigger('Poison-Tip Archer opposing death',
                                       lambda:self.drain_opponents(1,'Poison-Tip Archer')))
            if source.name=='Blood Artist':
                effects.append(Trigger('Blood Artist opposing death',lambda:self._blood_artist()))
            if source.name=='Yahenni, Undying Partisan':
                effects.append(Trigger('Yahenni opponent death counter',
                            lambda u=source.uid:self._yahenni_opponent_death(u)))
            if source.name=='Sangromancer' and self.choose_sangromancer_gain:
                effects.append(Trigger('Sangromancer opposing death',
                                       lambda:self.gain(3,'Sangromancer opposing death')))
        self._enqueue(effects)

    def opponent_discards(self, count=1):
        """Exogenously supplied distinct discard events, NOT discard policy."""
        if count < 0: raise IllegalAction('Negative discard count')
        for _ in range(count):
            self.trace.append(('external_opponent_discard', 1))
            if self.choose_sangromancer_gain:
                self._enqueue([Trigger('Sangromancer discard',
                     lambda:self.gain(3,'Sangromancer discard'))
                    for __ in range(self.has('Sangromancer'))])

    def _yahenni_opponent_death(self,uid):
        p=self.permanents.get(uid)
        if p and p.name=='Yahenni, Undying Partisan':
            p.counters+=1
            self.trace.append(('plus_one_counter',uid,'Yahenni opponent death'))

    def _grave_pact_opportunity(self):
        self.edict_opportunities+=1
        self.trace.append(('edict_opportunity',1,'Grave Pact'))

    def _drain_and_gain(self, source):
        self.drain_opponents(1,source)
        self.gain(1,source)

    def _blood_artist(self):
        # Fixture assumes targeting an opponent; not target-selection/hexproof validation.
        self.life[1]-=1
        self.trace.append(('target_opponent_loses',1,'Blood Artist'))
        self.gain(1,'Blood Artist')

    def _moldervine(self):
        self.gain(1,'Moldervine Reclamation')
        self._fixture_draw(1,'Moldervine Reclamation')

    def _dark_prophecy(self):
        self._fixture_draw(1,'Dark Prophecy')
        self.lose_life(1,'Dark Prophecy')

    def sacrifice(self,uid): return self._leave(uid,sacrificed=True)
    def destroy(self,uid):
        if uid in self.indestructible_until_eot:
            self.trace.append(('destroy_prevented_indestructible',uid))
            return None
        return self._leave(uid,sacrificed=False)

    def attack_with(self,uid):
        p=self.permanents.get(uid)
        if not p or not p.creature: raise IllegalAction('No attacking creature')
        self.trace.append(('attack',uid))
        effects=[]
        if p.token and p.token.attacks_gain:
            effects.append(Trigger('Moseo Pest attacks gain',lambda:self.gain(1,'Moseo Pest attack')))
        if p.name == "Teacher's Pest":
            effects.append(Trigger("Teacher's Pest attacks gain",lambda:self.gain(1,"Teacher's Pest attack")))
        self._enqueue(effects)

    def controls_pest(self):
        # The Pest subtype applies to tokens AND nontoken creatures (Teacher's Pest).
        return any(p.controller==0 and p.creature and 'Pest' in p.subtypes
                   for p in self.permanents.values())

    def begin_upkeep(self):
        # Conditional ability has an intervening-if check at trigger AND resolution.
        effects=[]
        if not self.controls_pest():
            for _ in range(self.has('Pest Rescuer')):
                def rescuers_upkeep():
                    if not self.controls_pest():
                        self.make_tokens(PEST)
                effects.append(Trigger('Pest Rescuer conditional upkeep',rescuers_upkeep))
        for _ in range(self.has('Beledros Witherbloom')):
            effects.append(Trigger('Beledros each upkeep',lambda:self.make_tokens(PEST)))
        self._enqueue(effects)

    def put_creature_in_fixture_library(self,name, *, mana_value, colors=None,
                                        power=1,toughness=1):
        """Provide an explicit eligible library candidate to an isolated fixture.

        Not an actual Commander shuffle, deck order, or library object model.
        """
        if name not in BODIES or name in NONCREATURE or mana_value<0:
            raise IllegalAction('Unknown or noncreature fixture library candidate')
        item={'name':name,'colors':colors if colors is not None else BODIES[name],
              'mana_value':mana_value,'power':power,'toughness':toughness}
        self.fixture_library_creatures.append(item)
        return len(self.fixture_library_creatures)-1

    def saga_chapter(self,chapter, *, sacrifice_uids=(),
                     grave_selection_uid=None, library_selection_index=None):
        if chapter in (1,2,3):
            self.trace.append(('saga_chapter',chapter))
            self.make_tokens(INSECT)
            return
        if chapter !=4: raise IllegalAction('Chapter must be I, II, III or IV')
        saga=next((p for p in self.permanents.values()
                   if p.controller==0 and p.name=='The Hunger Tide Rises'),None)
        if not saga: raise IllegalAction('No controlled Hunger Tide Rises for chapter IV')
        sacrifices=list(sacrifice_uids)
        if len(set(sacrifices))!=len(sacrifices) or any(
            u not in self.permanents or self.permanents[u].controller!=0
            or not self.permanents[u].creature for u in sacrifices):
            raise IllegalAction('Chapter IV can sacrifice distinct controlled creatures only')
        if grave_selection_uid is not None and library_selection_index is not None:
            raise IllegalAction('Select only one creature from library or graveyard')
        number=len(sacrifices)
        # Validate explicitly supplied selection before mutations; this is a
        # fixture contract, not an arbitrary search decision engine.
        chosen_gy=None
        if grave_selection_uid is not None:
            chosen_gy=self._grave_target(grave_selection_uid)
            if chosen_gy is None and grave_selection_uid in sacrifices:
                chosen_gy=self.permanents[grave_selection_uid]
            if not chosen_gy or chosen_gy.token or chosen_gy.mana_value>number:
                raise IllegalAction('Selected grave creature unavailable or MV above sacrificed count')
        chosen_lib=None
        if library_selection_index is not None:
            if not isinstance(library_selection_index,int) or not (
                    0<=library_selection_index<len(self.fixture_library_creatures)):
                raise IllegalAction('No supplied creature at chosen fixture library index')
            chosen_lib=self.fixture_library_creatures[library_selection_index]
            if chosen_lib['mana_value']>number:
                raise IllegalAction('Selected library creature MV above sacrificed count')
        self.trace.append(('saga_chapter',4))
        for u in sacrifices:self.sacrifice(u)
        if chosen_gy is not None:
            self._return_creature_from_graveyard(chosen_gy,'The Hunger Tide Rises IV')
        elif chosen_lib is not None:
            self.fixture_library_creatures.pop(library_selection_index)
            self.add(chosen_lib['name'],colors=chosen_lib['colors'],creature=True,
                     toughness=chosen_lib['toughness'],power=chosen_lib['power'],
                     mana_value=chosen_lib['mana_value'])
            self.trace.append(('fixture_library_found_to_battlefield',chosen_lib['name']))
            self.trace.append(('fixture_library_shuffled_unmodeled',))
        else:
            self.trace.append(('saga_iv_chose_no_creature',number))
        # Approximate the Saga leaving after its final ability; no counters/SBA timing model.
        self.permanents.pop(saga.uid,None)
        self.graveyard.append(saga)
        self.trace.append(('saga_sacrifice_after_final_chapter',saga.uid))

    def pest_summoning(self): self.make_tokens(PEST,2)
    def hunt_for_specimens(self, *, lesson=False):
        if lesson and (not self.learn_sideboard_allowed or not self.lesson_available):
            raise IllegalAction('Lesson outside game not allowed or unavailable')
        self.make_tokens(PEST)
        if lesson:
            self.hand.append('Pest Summoning'); self.lesson_available=False
            self.trace.append(('learn_lesson','Pest Summoning'))
        else:
            self.trace.append(('learn_choice','discard/draw or decline not modeled'))

    def sedgemoor_spell_cast_or_copied(self):
        for _ in range(self.has('Sedgemoor Witch')):
            self._enqueue([Trigger('Sedgemoor Witch Magecraft',lambda:self.make_tokens(PEST))])

    def cast_with_sacrifice_cost(self,spell,uid):
        # Mana, target lock, copy mechanics, interactions and legal spell timing excluded.
        if spell not in ('Village Rites','Diabolic Intent','Deadly Dispute','Tend the Pests'):
            raise IllegalAction('Unsupported spell')
        p=self.permanents.get(uid)
        if not p or not p.creature or p.controller!=0:
            raise IllegalAction('Controlled creature additional cost missing')
        self.trace.append(('cost_start',spell))
        self.sacrifice(uid)  # COST is paid before the cast event (Magecraft)
        self.trace.append(('cast',spell))
        self.sedgemoor_spell_cast_or_copied()
        return p

    def activate_feral_appetite(self, *, grave_card_is_creature:bool):
        if not self.has('Feral Appetite'): raise IllegalAction('Feral Appetite not controlled')
        # Mana payment & target legality must be checked by future full engine.
        self.trace.append(('exile_target_gy_card',grave_card_is_creature))
        if grave_card_is_creature: self.make_tokens(PEST)

    def roaster_end_step(self):
        for p in tuple(self.permanents.values()):
            if p.name == 'Ribtruss Roaster' and p.controller == 0:
                self._enqueue([Trigger('Ribtruss Roaster end-step',
                        lambda n=p.counters:self.make_tokens(PEST,n))])

    def _return_creature_from_graveyard(self, cand, source, *, tapped=False):
        if cand not in self.graveyard or not cand.creature or cand.token:
            return None
        self.graveyard.remove(cand)
        new=self.add(cand.name, controller=0, colors=cand.colors,
                     creature=True, tapped=tapped, toughness=cand.toughness,
                     mana_value=cand.mana_value, power=cand.power, counters=0)
        self.trace.append(('reanimate',cand.uid,new.uid,source,tapped))
        return new

    def moseo_end_step(self, target_uid=None):
        if not self.has("Moseo, Vein's New Dean") or self.life_gained_turn==0:
            return False
        if target_uid is None:
            self.trace.append(('moseo_choose_no_target',self.life_gained_turn))
            return False
        cand=next((p for p in self.graveyard if p.uid==target_uid and p.creature),None)
        if cand is None or cand.mana_value>self.life_gained_turn:
            raise IllegalAction('Illegal Moseo graveyard target or mana value')
        threshold=self.life_gained_turn
        def reanimate():
            # Check target remains in graveyard on resolution.
            if cand not in self.graveyard: return
            self._return_creature_from_graveyard(cand,'Moseo',tapped=False)
        self._enqueue([Trigger('Moseo infusion end step',reanimate)])
        return True

    def cauldron_reanimate(self, *, target_uid, sacrificed_uid, sorcery_window=True):
        if not sorcery_window: raise IllegalAction('Cauldron activation is sorcery-speed only')
        c=next((p for p in self.permanents.values() if p.name=='Cauldron of Essence' and p.controller==0 and not p.tapped),None)
        if not c: raise IllegalAction('No untapped Cauldron')
        cand=next((p for p in self.graveyard if p.uid==target_uid and p.creature),None)
        if not cand: raise IllegalAction('Target must be creature card in graveyard on activation')
        if sacrificed_uid not in self.permanents: raise IllegalAction('Missing sacrifice creature')
        if not self.permanents[sacrificed_uid].creature or self.permanents[sacrificed_uid].controller != 0:
            raise IllegalAction('Must sacrifice your controlled creature')
        # Targets are announced before costs; verify every cost without changing state.
        pool=self.mana_pool.copy()
        if pool.count('B')<1 or pool.count('G')<1 or len(pool)<3:
            raise IllegalAction('Cauldron needs {1}{B}{G} before activation')
        self.trace.append(('target_locked',target_uid,'Cauldron of Essence'))
        self.pay_mana(black=1,green=1,generic=1)
        c.tapped=True
        self.sacrifice(sacrificed_uid)
        def reanimate():
            if cand not in self.graveyard: return
            self._return_creature_from_graveyard(cand,'Cauldron of Essence',tapped=False)
        # The activated ability is on stack beneath triggers caused by its costs.
        self.pending.append(Trigger('Cauldron activated reanimation',reanimate))
        return cand

    def immoral_bargain(self, x, sacrifices, targets):
        if x<0 or len(sacrifices)!=x or len(targets)!=x or len(set(targets))!=x:
            raise IllegalAction('X, cost sacrifice count and distinct target count mismatch')
        if len(set(sacrifices))!=x or any(uid not in self.permanents or not self.permanents[uid].creature
                                          or self.permanents[uid].controller != 0 for uid in sacrifices):
            raise IllegalAction('Insufficient legal sacrifice creatures')
        self.trace.append(('targets_locked',tuple(targets),'Immoral Bargain'))
        for uid in sacrifices: self.sacrifice(uid)
        self.trace.append(('cast','Immoral Bargain'))
        self.sedgemoor_spell_cast_or_copied()
        # Destruction of targeted opposing permanents is outside current reference kernel.

    def add_mana(self, *symbols):
        """Manually load observed floating mana, including other colors; no land tapping."""
        if any(symbol not in ('W','U','B','R','G','C') for symbol in symbols):
            raise IllegalAction('Only explicit W/U/B/R/G/C mana in this reference')
        self.mana_pool.extend(symbols)
        self.trace.append(('mana_added',tuple(symbols)))

    def pay_mana(self, *, black=0, green=0, generic=0):
        """Atomically validate/pay B/G and generic mana; C pays only generic."""
        costs=(black,green,generic)
        if any(not isinstance(n,int) or n<0 for n in costs):
            raise IllegalAction('Invalid mana cost')
        pool=self.mana_pool.copy()
        for color,n in (('B',black),('G',green)):
            if pool.count(color)<n: raise IllegalAction('Colored mana unavailable')
            for _ in range(n): pool.remove(color)
        if len(pool)<generic: raise IllegalAction('Generic mana unavailable')
        paid=[pool.pop() for _ in range(generic)]
        self.mana_pool=pool
        self.trace.append(('mana_paid',{'B':black,'G':green,'generic_symbols':tuple(paid)}))

    def _grave_target(self,uid):
        return next((p for p in self.graveyard
                     if p.uid==uid and p.creature and not p.token),None)

    def skeleton_return(self,uid):
        """{1}{B}: Reassembling Skeleton card, from graveyard tapped."""
        p=self._grave_target(uid)
        if not p or p.name!='Reassembling Skeleton':
            raise IllegalAction('Skeleton must be in graveyard')
        self.pay_mana(black=1,generic=1)
        return self._return_creature_from_graveyard(p,'Reassembling Skeleton',tapped=True)

    def teachers_pest_return(self,uid):
        """{B}{G}: Teacher's Pest card, from graveyard tapped."""
        p=self._grave_target(uid)
        if not p or p.name!="Teacher's Pest":
            raise IllegalAction("Teacher's Pest must be in graveyard")
        self.pay_mana(black=1,green=1)
        return self._return_creature_from_graveyard(p,"Teacher's Pest",tapped=True)

    def phyrexian_reclamation(self,uid):
        """{1}{B}, pay 2 life: return target creature card to hand, not play."""
        if not self.has('Phyrexian Reclamation'):
            raise IllegalAction('Phyrexian Reclamation not on battlefield')
        p=self._grave_target(uid)
        if not p: raise IllegalAction('Target is not creature card in own graveyard')
        if self.life[0]<2: raise IllegalAction('Cannot pay two life')
        self.pay_mana(black=1,generic=1)
        self.pay_life(2,'Phyrexian Reclamation')
        def retrieve():
            if p not in self.graveyard: return
            self.graveyard.remove(p)
            self.hand.append(p.name)
            self.trace.append(('return_to_hand',p.uid,p.name,'Phyrexian Reclamation'))
        self.pending.append(Trigger('Phyrexian Reclamation returns to hand',retrieve))

    def viscera_seer_sacrifice(self,uid):
        """Reference sacrifice-cost and stack order; library scry is UNIMPLEMENTED."""
        if not self.has('Viscera Seer'): raise IllegalAction('No Viscera Seer controlled')
        target=self.permanents.get(uid)
        if not target or not target.creature or target.controller!=0:
            raise IllegalAction('No legal controlled creature to sacrifice')
        self.sacrifice(uid)
        self.pending.append(Trigger('Viscera Seer scry',
            lambda:self.trace.append(('scry_unimplemented',1,'Viscera Seer'))))

    def carrion_feeder_sacrifice(self,source_uid,sacrifice_uid):
        feeder=self.permanents.get(source_uid)
        sac=self.permanents.get(sacrifice_uid)
        if not feeder or feeder.name!='Carrion Feeder' or feeder.controller!=0:
            raise IllegalAction('No valid Carrion Feeder source')
        if not sac or not sac.creature or sac.controller!=0:
            raise IllegalAction('No controlled creature to sacrifice')
        self.sacrifice(sacrifice_uid)
        def add_counter():
            if source_uid in self.permanents:
                self.permanents[source_uid].counters+=1
                self.trace.append(('plus_one_counter',source_uid))
        self.pending.append(Trigger('Carrion Feeder activated +1/+1',add_counter))

    def warren_soultrader_sacrifice(self,source_uid,sacrifice_uid):
        trader=self.permanents.get(source_uid)
        sac=self.permanents.get(sacrifice_uid)
        if not trader or trader.name!='Warren Soultrader' or trader.controller!=0:
            raise IllegalAction('No valid Warren Soultrader source')
        if not sac or not sac.creature or sac.controller!=0 or source_uid==sacrifice_uid:
            raise IllegalAction('Warren Soultrader requires another controlled creature')
        if self.life[0]<1: raise IllegalAction('Cannot pay one life')
        self.pay_life(1,'Warren Soultrader cost')
        self.sacrifice(sacrifice_uid)
        self.pending.append(Trigger('Warren Soultrader Treasure',
             lambda:self.make_tokens(TREASURE)))

    def phyrexian_altar_sacrifice(self, uid, color):
        """PAB-reported mana outlet; exact supplemental Oracle pinning still pending.

        Activation cost is the sacrifice. Mana is produced without joining the stack;
        associated death/Savra triggers are queued, not immediately resolved.
        """
        if not self.has('Phyrexian Altar'):
            raise IllegalAction('No controlled Phyrexian Altar')
        if color not in ('W','U','B','R','G'):
            raise IllegalAction('Phyrexian Altar makes colored mana, not colorless')
        p=self.permanents.get(uid)
        if not p or not p.creature or p.controller!=0:
            raise IllegalAction('Mana cost requires sacrificing owned controlled creature')
        self.sacrifice(uid)
        self.mana_pool.append(color)
        self.trace.append(('phyrexian_altar_mana',color,uid))

    def yahenni_sacrifice(self, source_uid, sacrifice_uid):
        source=self.permanents.get(source_uid)
        cost=self.permanents.get(sacrifice_uid)
        if not source or source.name!='Yahenni, Undying Partisan' or source.controller!=0:
            raise IllegalAction('Missing controlled Yahenni')
        if not cost or not cost.creature or cost.controller!=0 or source_uid==sacrifice_uid:
            raise IllegalAction('Yahenni must sacrifice another controlled creature')
        self.sacrifice(sacrifice_uid)
        def protect():
            if source_uid in self.permanents:
                self.indestructible_until_eot.add(source_uid)
                self.trace.append(('indestructible_until_end_of_turn',source_uid))
        self.pending.append(Trigger('Yahenni indestructible activation',protect))

    def yawgmoth_sacrifice(self, source_uid, sacrifice_uid, *, target_uid=None):
        """Selective card implementation: pay one life, other-creature sacrifice,
        up-to-one own creature target, -1/-1 counter, and draw *event counter*.

        Does not model target opposing creatures or generic layer/SBA interactions.
        If the chosen target becomes illegal (including when sacrificed as the
        activation cost), the ability has no legal target and does not draw.
        """
        source=self.permanents.get(source_uid)
        cost=self.permanents.get(sacrifice_uid)
        if not source or source.name!='Yawgmoth, Thran Physician' or source.controller!=0:
            raise IllegalAction('Missing controlled Yawgmoth')
        if not cost or not cost.creature or cost.controller!=0 or source_uid==sacrifice_uid:
            raise IllegalAction('Yawgmoth requires another controlled creature')
        if target_uid is not None:
            target=self.permanents.get(target_uid)
            if not target or not target.creature or target.controller!=0:
                raise IllegalAction('Target unsupported or illegal in restricted fixture')
        if self.life[0]<1: raise IllegalAction('Cannot pay 1 life')
        self.trace.append(('target_locked',target_uid,'Yawgmoth'))
        self.pay_life(1,'Yawgmoth activation cost')
        self.sacrifice(sacrifice_uid)
        def resolve_yawgmoth():
            if target_uid is not None and target_uid not in self.permanents:
                self.trace.append(('ability_fizzles_all_targets_illegal','Yawgmoth'))
                return
            if target_uid is not None:
                target=self.permanents[target_uid]
                target.minus_counters+=1
                self.trace.append(('minus_one_counter',target_uid))
            self._fixture_draw(1,'Yawgmoth')
            if target_uid is not None:
                target=self.permanents.get(target_uid)
                if target and target.toughness + target.counters - target.minus_counters<=0:
                    self.destroy(target_uid)
        self.pending.append(Trigger('Yawgmoth activation',resolve_yawgmoth))

    def cast_pab_spell(self, spell, sacrifice_uid):
        """Limited PABTRV3 actual spell-resolutions. Requires explicitly loaded mana.

        Only card draw COUNT, mana, token generation and costs are resolved.
        Diabolic Intent's unrestricted library search is NOT implemented;
        it is rejected rather than misrepresented as a no-op tutor.
        """
        costs={'Village Rites':(1,0,1),'Deadly Dispute':(1,0,1),
               'Tend the Pests':(1,1,0)}
        if spell not in costs: raise IllegalAction('Unsupported full spell; no silent tutor no-op')
        cost=self.permanents.get(sacrifice_uid)
        if not cost or cost.controller!=0 or not (cost.creature or (spell=='Deadly Dispute' and cost.artifact)):
            raise IllegalAction('Illegal controlled permanent for additional casting cost')
        black,green,generic=costs[spell]
        # Preflight before mutating (including the illegal mana case).
        pool=self.mana_pool.copy()
        if pool.count('B')<black or pool.count('G')<green or len(pool)<black+green+generic:
            raise IllegalAction('Mana unavailable for PAB spell')
        power=max(0,cost.power+cost.counters-cost.minus_counters)
        self.pay_mana(black=black,green=green,generic=generic)
        self.sacrifice(sacrifice_uid)
        self.trace.append(('cast',spell))
        def spell_resolution():
            if spell in ('Village Rites','Deadly Dispute'):
                self._fixture_draw(2,spell)
            if spell=='Deadly Dispute': self.make_tokens(TREASURE)
            if spell=='Tend the Pests': self.make_tokens(PEST,power)
        # Spell is lower on this limited stack than its cost and cast triggers.
        self.pending.append(Trigger(spell+' resolution',spell_resolution))
        self.sedgemoor_spell_cast_or_copied()
        return cost

    def plumb_the_forbidden(self, sacrifice_uids):
        """{1}{B} instant, optionally sacrifice 0+ controlled creatures,
        one copy per sacrificed creature. Copies each resolve draw 1/lose 1.

        Fixtures start from empty stack. Copy-on-cast & Magecraft have chosen
        controller order; no opponents, priority, or actual library contents.
        """
        ids=list(sacrifice_uids)
        if len(ids)!=len(set(ids)) or any(u not in self.permanents or
             not self.permanents[u].creature or self.permanents[u].controller!=0 for u in ids):
            raise IllegalAction('Plumb additional cost must be distinct controlled creatures')
        pool=self.mana_pool.copy()
        if pool.count('B')<1 or len(pool)<2:
            raise IllegalAction('Plumb requires {1}{B}')
        self.pay_mana(black=1,generic=1)
        for u in ids: self.sacrifice(u)
        self.trace.append(('cast','Plumb the Forbidden'))
        def resolve_one(kind):
            self._fixture_draw(1,'Plumb '+kind)
            self.lose_life(1,'Plumb '+kind)
        self.pending.append(Trigger('Plumb original',lambda:resolve_one('original')))
        # One explicit copies trigger (not *casts*) and a Magecraft cast trigger.
        def create_copies():
            for _ in ids:
                self.pending.appendleft(Trigger('Plumb copy',lambda:resolve_one('copy')))
                self.trace.append(('copy','Plumb the Forbidden'))
                self.sedgemoor_spell_cast_or_copied()
        self._enqueue([Trigger('Plumb make copies',create_copies)])
        self.sedgemoor_spell_cast_or_copied()

    # v0.5 narrowly bounded tests. No constructed library, ETB land oracle, or general spell stack.
    def _fixture_draw(self, n, source):
        """Count draws only; no actual library or cards in hand are generated."""
        if n < 0: raise IllegalAction('Negative draw count')
        self.cards_drawn += n
        self.trace.append(('draw',n,source))

    def tap_mana_rock(self, source_uid, *, color=None):
        """Tap an existing rock; does not cast it or apply cost taxes.

        Sol Ring and Arcane Signet mechanics from historic audit; text pin pending.
        Golgari Signet cost/symbols from local card-data audit.
        """
        source=self.permanents.get(source_uid)
        if not source or source.controller!=0 or source.tapped or not source.artifact:
            raise IllegalAction('Missing controlled untapped mana rock')
        name=source.name
        if name=='Sol Ring':
            if color is not None: raise IllegalAction('Sol Ring produces only {C}{C}')
            produced=('C','C')
        elif name=='Arcane Signet':
            if color not in ('B','G'):
                raise IllegalAction('Savra Arcane Signet can produce B or G only')
            produced=(color,)
        elif name=='Golgari Signet':
            if color is not None: raise IllegalAction('Golgari Signet produces exactly {B}{G}')
            if not self.mana_pool: raise IllegalAction('Golgari Signet needs {1} activation mana')
            produced=('B','G')
        else:
            raise IllegalAction('No supported mana-rock activation for this card')
        if name=='Golgari Signet':
            self.pay_mana(generic=1)
        source.tapped=True
        self.mana_pool.extend(produced)
        self.trace.append(('rock_tapped_mana',source_uid,name,produced))
        return produced

    def put_basic_land_in_fixture_library(self, name):
        """Supply a *basic* Forest/Swamp. Other Forest-typed ETBs remain unsupported."""
        if name not in ('Forest','Swamp'):
            raise IllegalAction('Only basic Forest/Swamp library fixtures supported')
        obj={'name':name,'basic':True,'forest_subtype':name=='Forest'}
        self.fixture_library_lands.append(obj)
        return len(self.fixture_library_lands)-1

    def _resolve_basic_land_search(self, selected, *, tapped, source):
        # The fixture candidate is chosen at resolution; there is no real deck/shuffle.
        if selected is not None and selected in self.fixture_library_lands:
            self.fixture_library_lands.remove(selected)
            new=self.add(selected['name'],colors='',creature=False,artifact=False,
                         tapped=tapped)
            self.trace.append(('fixture_basic_land_to_battlefield',new.uid,
                               new.name,tapped,source))
        else:
            self.trace.append(('fixture_basic_land_search_failed_to_find',source))
        self.trace.append(('fixture_library_shuffled_unmodeled',source))

    def sakura_tribe_elder_sacrifice(self, source_uid, *, land_index=None):
        """Sacrifice activation cost; fetch basic tapped later, after cost triggers."""
        source=self.permanents.get(source_uid)
        if not source or source.name!='Sakura-Tribe Elder' or source.controller!=0:
            raise IllegalAction('Sakura-Tribe Elder ability needs controlled source')
        if land_index is not None and (not isinstance(land_index,int) or
                not 0 <= land_index < len(self.fixture_library_lands)):
            raise IllegalAction('No fixture basic at chosen index')
        selected=(self.fixture_library_lands[land_index] if land_index is not None else None)
        self.sacrifice(source_uid)
        self.pending.append(Trigger('Sakura-Tribe Elder basic search',
            lambda:self._resolve_basic_land_search(selected,tapped=True,
                                                    source='Sakura-Tribe Elder')))

    def natures_lore(self, *, land_index=None, sorcery_window=True):
        """{1}{G}, basic Forest subset only; actual nonbasic Forest ETBs unmodeled."""
        if not sorcery_window: raise IllegalAction("Nature's Lore sorcery window required")
        if land_index is not None and (not isinstance(land_index,int) or not
                0 <= land_index < len(self.fixture_library_lands) or
                not self.fixture_library_lands[land_index]['forest_subtype']):
            raise IllegalAction("Nature's Lore fixture must select a Forest")
        selected=(self.fixture_library_lands[land_index] if land_index is not None else None)
        self.pay_mana(green=1,generic=1)
        self.trace.append(('cast',"Nature's Lore"))
        self.pending.append(Trigger("Nature's Lore basic Forest search",
             lambda:self._resolve_basic_land_search(selected,tapped=False,
                                                     source="Nature's Lore")))
        self.sedgemoor_spell_cast_or_copied()

    def pest_infestation(self, x, *, target_uids=(), sorcery_window=True):
        """{X}{X}{G}, up to X artifact/enchantment targets, 2X ordinary Pests.

        Supports explicitly represented permanents only. No external hidden state.
        """
        if not sorcery_window: raise IllegalAction('Pest Infestation sorcery window required')
        if not isinstance(x,int) or x<0: raise IllegalAction('Pest Infestation X must be nonnegative int')
        targets=tuple(target_uids)
        if len(targets)>x or len(set(targets))!=len(targets):
            raise IllegalAction('Choose up to X distinct target artifacts/enchantments')
        enchantments={"Bastion of Remembrance",'Moldervine Reclamation','Dark Prophecy',
                      'Grave Pact','Blight Mound','Feral Appetite',
                      'Phyrexian Reclamation','Agent of the Iron Throne',
                      'The Hunger Tide Rises'}
        def valid(uid):
            p=self.permanents.get(uid)
            return p is not None and (p.artifact or p.name in enchantments)
        if any(not valid(uid) for uid in targets):
            raise IllegalAction('Pest Infestation targets artifact or enchantment only')
        self.pay_mana(green=1,generic=2*x)
        self.trace.append(('cast','Pest Infestation',x,targets))
        def effect():
            if targets and not any(valid(uid) for uid in targets):
                self.trace.append(('spell_fizzles_all_targets_illegal','Pest Infestation'))
                return
            for uid in targets:
                if valid(uid): self._destroy_supported_noncreature(uid)
            self.make_tokens(PEST,2*x)
        self.pending.append(Trigger('Pest Infestation resolve',effect))
        self.sedgemoor_spell_cast_or_copied()

    def _destroy_supported_noncreature(self, uid):
        p=self.permanents.get(uid)
        if not p or p.creature or not (p.artifact or p.name in {
             'Bastion of Remembrance','Moldervine Reclamation','Dark Prophecy',
             'Grave Pact','Blight Mound','Feral Appetite','Phyrexian Reclamation',
             'Agent of the Iron Throne','The Hunger Tide Rises'}):
            raise IllegalAction('Not a supported noncreature artifact or enchantment')
        if p.controller==0 and p.artifact:
            return self.destroy(uid)  # existing own-artifact death/Agent semantics
        del self.permanents[uid]
        self.skullclamp_attached.pop(uid,None)
        if not p.token: self.graveyard.append(p)
        self.trace.append(('noncreature_destroy',uid,p.name,p.controller))
        return p

    def unearth(self, target_uid, *, sorcery_window=True):
        """{B}: return creature card MV<=3; cycle mode is separate."""
        if not sorcery_window: raise IllegalAction('Unearth is a sorcery')
        candidate=self._grave_target(target_uid)
        if not candidate or candidate.mana_value>3:
            raise IllegalAction('Unearth targets creature card with mana value at most 3')
        self.pay_mana(black=1)
        self.trace.append(('cast','Unearth',target_uid))
        self.pending.append(Trigger('Unearth resolve',
            lambda: self._return_creature_from_graveyard(candidate,'Unearth')
             if candidate in self.graveyard else
             self.trace.append(('spell_fizzles_all_targets_illegal','Unearth'))))
        self.sedgemoor_spell_cast_or_copied()

    def cycle_unearth(self):
        """{2}, discard Unearth, draw event; no deck representation."""
        if 'Unearth' not in self.hand: raise IllegalAction('Unearth card must be in hand to cycle')
        self.pay_mana(generic=2)
        self.hand.remove('Unearth')
        self.trace.append(('cycle_discard','Unearth'))
        self.pending.append(Trigger('Unearth cycle draw',lambda:self._fixture_draw(1,'Unearth cycling')))

    def equip_skullclamp(self, clamp_uid, target_uid, *, sorcery_window=True):
        """{1} equip; death draw 2; only selected toughness/counters and +1/-1 modeled.

        This is provisional: supplementary Skullclamp card-text pinning remains pending.
        """
        clamp=self.permanents.get(clamp_uid)
        target=self.permanents.get(target_uid)
        if not sorcery_window: raise IllegalAction('Equip only at sorcery speed')
        if not clamp or clamp.name!='Skullclamp' or clamp.controller!=0:
            raise IllegalAction('Need controlled Skullclamp')
        if not target or not target.creature or target.controller!=0:
            raise IllegalAction('Equip target must be own creature')
        self.pay_mana(generic=1)
        # This partial fixture resolves equip immediately, ignoring responses.
        self.skullclamp_attached[clamp_uid]=target_uid
        self.trace.append(('equipped_skullclamp',clamp_uid,target_uid))
        eff_toughness=target.toughness+target.counters-target.minus_counters-1
        if eff_toughness<=0:
            self.trace.append(('sba_zero_toughness',target_uid,'Skullclamp'))
            self._leave(target_uid,sacrificed=False)  # SBA dies, NOT sacrifice

    def reset_turn(self):
        self.life_gained_turn=0
        self.indestructible_until_eot.clear()
