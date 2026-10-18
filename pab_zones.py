"""Phase 6: independent, opt-in, deterministic PABTRV3 physical card-zone prototype.

NOT integrated with pab_focus_engine.Game and NOT an MTG turn/priority engine.
Deck composition is read only from the frozen, hash-checked baseline. Each physical
card has a stable unique ID through zones; no card effect is inferred from its
presence. Only Forest, Swamp and Command Tower have provisional partial land
entry/mana paths. All other lands deliberately reject play pending exact sourcing.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import random
import re

FROZEN_SHA256 = 'c9589a8f66b41cd2de67d229f1d8ddcfc61cd53130e9a5a277c63cfb91d43381'
BASELINE = Path(__file__).resolve().parent/'upstream_frozen'/'FROZEN_PABTRV3_BASELINE.txt'
ZONES = frozenset({'library', 'hand', 'battlefield', 'graveyard', 'exile', 'command', 'outside_game'})
# All 21 distinct names as they occur in the frozen deck. This list only
# identifies the land card type; it does not certify their printed rules text.
LAND_NAMES = frozenset({
    'Blooming Marsh','Boseiju, Who Endures','Castle Locthwain','Command Tower',
    'Darkbore Pathway // Slitherbore Pathway','Deathcap Glade','Forest',
    'Geier Reach Sanitarium','Grim Backwoods','High Market','Llanowar Wastes',
    'Mikokoro, Center of the Sea','Nurturing Peatland','Overgrown Tomb',
    'Phyrexian Tower','Swamp','Takenuma, Abandoned Mire',
    'Underground Mortuary','Undergrowth Stadium','Verdant Catacombs',
    'Woodland Cemetery'
})
BASIC_LANDS = frozenset({'Forest','Swamp'})
SUPPORTED_LAND_MANA = {'Forest': ('G',), 'Swamp': ('B',),
                       'Command Tower': ('B','G')}

class ZoneError(ValueError):
    """Illegal zone operation in this intentionally restricted prototype."""

class UnsupportedZoneMechanic(NotImplementedError):
    """A known card exists, but its full behavior has not been represented."""

@dataclass
class PhysicalCard:
    uid: int
    name: str
    owner: int
    zone: str
    controller: int | None = None
    tapped: bool = False
    token: bool = False

    @property
    def is_land(self) -> bool:
        return self.name in LAND_NAMES

    @property
    def is_basic_land(self) -> bool:
        return self.name in BASIC_LANDS and not self.token


class DeckZones:
    """One player's frozen PAB deck; top of library is index zero.

    Zone moves are event/identity fixtures, not spell resolution or triggers.
    Library order is deterministic given a seed and operation order. No cards
    are generated to satisfy draws or searches. Mutable state is per instance.
    """
    def __init__(self, *, seed: int = 0, learn_sideboard_allowed: bool = False):
        if not isinstance(seed, int):
            raise ZoneError('Random seed must be an integer')
        self.rng = random.Random(seed)
        self.seed = seed
        self.learn_sideboard_allowed = learn_sideboard_allowed
        self.cards: dict[int, PhysicalCard] = {}
        self.zones: dict[str,list[int]] = {name: [] for name in ZONES}
        self.trace: list[tuple] = []
        self.mana_pool: list[str] = []
        self.land_plays_this_turn = 0
        self.failed_draws = 0  # Would cause loss at next applicable SBA; not adjudicated.
        self._next_uid = 1
        deck_sections = self._read_frozen_deck()
        for name, count in deck_sections['Mainboard']:
            for _ in range(count):
                self._create_physical(name, 'library')
        for name,count in deck_sections['Commander']:
            for _ in range(count):
                self._create_physical(name, 'command')
        for name,count in deck_sections['Sideboard']:
            for _ in range(count):
                self._create_physical(name, 'outside_game')
        if len(self.zones['library']) != 99 or len(self.zones['command']) != 1 or len(self.zones['outside_game']) != 1:
            raise ZoneError('Incorrect deck/commander/Lesson counts')
        assert sum(self.cards[u].is_land for u in self.zones['library']) == 34
        assert {self.cards[u].name for u in self.zones['command']} == {'Savra, Queen of the Golgari'}
        assert {self.cards[u].name for u in self.zones['outside_game']} == {'Pest Summoning'}

    @staticmethod
    def _read_frozen_deck() -> dict[str,list[tuple[str,int]]]:
        content = BASELINE.read_bytes()
        if hashlib.sha256(content).hexdigest() != FROZEN_SHA256:
            raise ZoneError('Frozen original deck checksum mismatch')
        parsed: dict[str,list[tuple[str,int]]] = {s:[] for s in ('Commander','Mainboard','Sideboard')}
        section = None
        for line in content.decode('utf-8').splitlines():
            line=line.strip()
            if not line: continue
            if line in parsed:
                section=line; continue
            m = re.fullmatch(r'(\d+)x (.+)',line)
            if not m or section is None:
                raise ZoneError(f'Unexpected baseline syntax: {line}')
            n=int(m.group(1))
            if n < 1: raise ZoneError('Deck quantities must be positive')
            parsed[section].append((m.group(2),n))
        return parsed

    def _create_physical(self, name: str, zone: str, *, owner=0, token=False, controller=None) -> PhysicalCard:
        if zone not in ZONES: raise ZoneError('Unknown zone')
        uid=self._next_uid
        self._next_uid+=1
        card=PhysicalCard(uid,name,owner,zone,controller,False,token)
        self.cards[uid]=card
        self.zones[zone].append(uid)
        return card

    def zone_cards(self, zone: str) -> tuple[PhysicalCard,...]:
        if zone not in ZONES: raise ZoneError('Unknown zone')
        return tuple(self.cards[uid] for uid in self.zones[zone])

    def _require_in_zone(self, uid:int, zone:str) -> PhysicalCard:
        card=self.cards.get(uid)
        if not card or card.zone != zone or uid not in self.zones[zone]:
            raise ZoneError(f'Card UID must be in {zone}')
        return card

    def move(self, uid:int, destination: str, *, controller: int | None = None,
             top: bool = False, bottom: bool = False) -> None:
        """Primitive physical move. Casting, triggers, APNAP, replacement not implied."""
        if destination not in ZONES: raise ZoneError('Unknown destination')
        if top and bottom: raise ZoneError('Top and bottom are mutually exclusive')
        if (top or bottom) and destination != 'library':
            raise ZoneError('Top/bottom ordering only for library')
        card=self.cards.get(uid)
        if card is None: raise ZoneError('Unknown card UID')
        source=card.zone
        if source==destination: raise ZoneError('No-op zone move forbidden')
        if card.token and source != 'battlefield':
            raise ZoneError('Token cannot change zones after leaving battlefield')
        if destination=='outside_game':
            raise ZoneError('No generic transfer to Lesson sideboard')
        if source=='outside_game':
            raise ZoneError('Lesson must be retrieved by explicit opt-in Learn action')
        if destination=='command' and card.name!='Savra, Queen of the Golgari':
            raise ZoneError('Only Savra can enter this prototype command zone')
        if destination=='battlefield' and controller is None:
            raise ZoneError('Controller must be specified for battlefield entry')
        if destination!='battlefield' and controller is not None:
            raise ZoneError('Nonbattlefield card has no controller')
        self.zones[source].remove(uid)
        if destination=='library' and top:
            self.zones[destination].insert(0,uid)
        else:
            self.zones[destination].append(uid)
        card.zone=destination
        card.controller=controller
        card.tapped=False
        self.trace.append(('zone_move',uid,card.name,source,destination))
        if card.token and destination!='battlefield':
            # The event happens (so future death triggers could see it), then
            # the token ceases to exist during the modeled SBA checkpoint.
            self.zones[destination].remove(uid)
            del self.cards[uid]
            self.trace.append(('token_ceases',uid,card.name))

    def shuffle_library(self) -> None:
        self.rng.shuffle(self.zones['library'])
        self.trace.append(('library_shuffled',len(self.zones['library'])))

    def draw(self, count: int = 1) -> tuple[PhysicalCard,...]:
        if not isinstance(count,int) or count < 0:
            raise ZoneError('Draw count must be nonnegative integer')
        drawn=[]
        for _ in range(count):
            if not self.zones['library']:
                self.failed_draws+=1
                self.trace.append(('empty_library_draw_attempt',self.failed_draws))
                continue
            uid=self.zones['library'][0]
            self.move(uid,'hand')
            drawn.append(self.cards[uid])
        return tuple(drawn)

    def mill(self, count:int) -> tuple[PhysicalCard,...]:
        if not isinstance(count,int) or count<0: raise ZoneError('Mill count must be nonnegative integer')
        milled=[]
        for _ in range(min(count,len(self.zones['library']))):
            uid=self.zones['library'][0]
            self.move(uid,'graveyard')
            milled.append(self.cards[uid])
        return tuple(milled)

    def discard(self, uid:int) -> None:
        self._require_in_zone(uid,'hand')
        self.move(uid,'graveyard')

    def search_library(self, *, selected_uid: int | None,
                       destination: str, eligible: str = 'any',
                       tapped: bool = False) -> PhysicalCard | None:
        """Resolve a selected search and shuffle. Source-provided selection only.

        'any': tutor for any card; if library is nonempty failure is disallowed.
        'basic': select basic Forest/Swamp; optional failure in hidden library.
        'basic_forest': only Forest (nonbasic Forest integration is future work).
        Untargeted, no spell/ability effects, target locks or mana costs here.
        """
        if destination not in ('hand','graveyard','battlefield','exile','library'):
            raise ZoneError('Unsupported search destination')
        if destination == 'library': raise ZoneError('Searching into same library is unsupported')
        if eligible not in ('any','basic','basic_forest'):
            raise ZoneError('Unknown search filter')
        if tapped and destination!='battlefield':
            raise ZoneError('Tapped flag requires battlefield destination')
        if selected_uid is None:
            # Hidden-zone qualified searches may fail to find by choice, even
            # when qualifying cards remain. Searching for any card is required
            # to find one unless the library is actually empty.
            if eligible=='any' and self.zones['library']:
                raise ZoneError('Cannot elect to fail an unrestricted mandatory search')
            selected=None
        else:
            selected=self._require_in_zone(selected_uid,'library')
            if eligible=='basic' and not selected.is_basic_land:
                raise ZoneError('Search must find a basic land')
            if eligible=='basic_forest' and selected.name!='Forest':
                raise ZoneError('Search must find a basic Forest')
            if destination=='battlefield' and not selected.is_land:
                raise ZoneError('Nonland search-to-battlefield effect is unmodeled')
            if destination=='battlefield' and selected.name not in BASIC_LANDS:
                raise UnsupportedZoneMechanic('Nonbasic search land ETB requires pinned card rules')
        if selected is not None:
            self.move(selected.uid,destination,controller=0 if destination=='battlefield' else None)
            if destination=='battlefield':
                selected.tapped=tapped
                self.trace.append(('searched_basic_land_entered',selected.uid,tapped))
        self.shuffle_library()  # Even a failed search may require shuffling.
        self.trace.append(('search_resolved',eligible,destination,
                           selected.uid if selected is not None else None))
        return selected

    def resolve_demonic_tutor(self, selected_uid: int | None) -> PhysicalCard | None:
        """Demonic Tutor *resolution only*: select any actual library card to hand.

        The artifact does not yet cast the spell, pay {1}{B}, resolve a stack,
        move the Tutor card itself, or validate timing. This is NOT a functional
        full-card implementation. Original audited rule: unrestricted search
        for a library card, hand destination, then shuffle.
        """
        selected=self.search_library(selected_uid=selected_uid,destination='hand',
                                     eligible='any')
        self.trace.append(('demonic_tutor_resolved',selected.uid if selected else None))
        return selected

    def play_land(self, uid:int, *, main_phase: bool = True, stack_empty: bool = True) -> PhysicalCard:
        card=self._require_in_zone(uid,'hand')
        if not card.is_land: raise ZoneError('Only a land can be played as a land')
        if not main_phase or not stack_empty:
            raise ZoneError('Land play requires controlled main phase with empty stack')
        if self.land_plays_this_turn>=1:
            raise ZoneError('Only one land play per turn supported')
        if card.name not in SUPPORTED_LAND_MANA:
            raise UnsupportedZoneMechanic('Card-specific land ETB/mana unresolved: '+card.name)
        self.move(uid,'battlefield',controller=0)
        self.land_plays_this_turn+=1
        self.trace.append(('land_played',uid,card.name))
        return card

    def tap_land_for_mana(self,uid:int, *, color:str|None=None) -> str:
        card=self._require_in_zone(uid,'battlefield')
        if not card.is_land or card.controller != 0 or card.tapped:
            raise ZoneError('Land must be controlled and untapped')
        choices=SUPPORTED_LAND_MANA.get(card.name)
        if choices is None:
            raise UnsupportedZoneMechanic('Land mana ability not implemented: '+card.name)
        if color is None and len(choices)==1:
            color=choices[0]
        if color not in choices:
            raise ZoneError('Land cannot produce requested mana color')
        card.tapped=True
        self.mana_pool.append(color)
        self.trace.append(('land_tapped_for_mana',uid,color))
        return color

    def new_turn(self):
        """Explicit partial turn refresh; does not claim a full untap phase."""
        self.land_plays_this_turn=0
        for uid in self.zones['battlefield']:
            card=self.cards[uid]
            if card.controller==0:
                card.tapped=False
        self.trace.append(('fixture_turn_reset',))

    def create_battlefield_token(self, name:str, *, controller:int=0) -> PhysicalCard:
        card=self._create_physical(name,'battlefield',token=True,controller=controller)
        self.trace.append(('fixture_token_created',card.uid,name,controller))
        return card

    def learn_pest_summoning(self) -> PhysicalCard:
        if not self.learn_sideboard_allowed:
            raise ZoneError('Outside-game Learn house rule disabled')
        uid=next((u for u in self.zones['outside_game']
                  if self.cards[u].name=='Pest Summoning'),None)
        if uid is None: raise ZoneError('Pest Summoning is not available outside game')
        card=self.cards[uid]
        self.zones['outside_game'].remove(uid)
        self.zones['hand'].append(uid)
        card.zone='hand'
        self.trace.append(('house_rule_lesson_to_hand',uid,'Pest Summoning'))
        return card

    def assert_integrity(self):
        """Development invariant: no duplicate UID across zones or lost physical cards."""
        ids=[uid for z in ZONES for uid in self.zones[z]]
        if len(ids)!=len(set(ids)) or set(ids)!=set(self.cards):
            raise AssertionError('Missing or duplicated card identity')
        for zone in ZONES:
            for uid in self.zones[zone]:
                card=self.cards[uid]
                if card.zone!=zone: raise AssertionError('Wrong zone on card')
                if (card.controller is not None)!=(zone=='battlefield'):
                    raise AssertionError('Controller must exist exactly on battlefield')
        return True
