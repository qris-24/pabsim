"""Canonical kernel entry point. Import Game / PhysicalZoneGame from here.

KERNEL_VERSION tracks promoted patches. Frozen historical modules
(pab_focus_engine v0.5, pab_focus_engine_v07, pab_zone_bridge, pab_zone_bridge_v08)
are never edited; each promotion layers on top and is verified by run_validation.py.
"""
import pab_r47_r48_sba as _sba                        # R47+R48+R49 layered on R01
from pab_clock_s4 import TurnBasedActionsMixin        # S4: untap/draw/land window (includes S1–S3)
from pab_cast_s6 import CastMixin                     # S6: cast_from_hand on the physical bridge (includes S1–S4)
from pab_cast_s7 import CreatureCastMixin             # S7: creature spells from the physical hand (27 names; includes S6)
from pab_opponents_s8 import OpponentsMixin           # S8: opponents as life totals + scripted board, real edicts (includes S7)
from pab_lands_s9 import FixerLandsMixin, SUPERSEDED_V08_FIXTURES   # S9: the nine B/G fixer lands (includes S8); supersedes frozen v0.8 fixtures 274/307
from pab_commander_s10 import CommanderMixin          # S10: Savra from the command zone (cast, tax, 903.9a return) (includes S9)
from pab_interaction_s11 import InteractionMixin      # S11: scripted opponent interaction (removal, wipes, graveyard hate, edicts) (includes S10)
from pab_r52_village_rites import VillageRitesCostMixin, EXPECTED_LEGACY_FAILURES   # R52: Village Rites costs {B}; supersedes frozen test_91 (+R01's 112/113)
class Game(VillageRitesCostMixin,TurnBasedActionsMixin,_sba.Game): pass
class PhysicalZoneGame(VillageRitesCostMixin,InteractionMixin,_sba.PhysicalZoneGame): pass
KERNEL_VERSION='v0.8+R02+R01+R47+R48+R49+S1+S2+S3+S4+S5+S6+R52+R53+S7+S8+S9+S10+S11'
PROMOTED=["R02", "R01", "R47", "R48", "R49", "S1", "S2", "S3", "S4", "S5", "S6", "R52", "R53", "S7", "S8", "S9", "S10", "S11"]
SUPERSEDED_FROZEN_CONTRACTS=sorted(EXPECTED_LEGACY_FAILURES)
SUPERSEDED_V08_CONTRACTS=sorted(SUPERSEDED_V08_FIXTURES)
