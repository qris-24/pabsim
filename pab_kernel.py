"""Canonical kernel entry point. Import Game / PhysicalZoneGame from here.

KERNEL_VERSION tracks promoted patches. Frozen historical modules
(pab_focus_engine v0.5, pab_focus_engine_v07, pab_zone_bridge, pab_zone_bridge_v08)
are never edited; each promotion layers on top and is verified by run_validation.py.
"""
import pab_r47_r48_sba as _sba                        # R47+R48+R49 layered on R01
from pab_clock_s4 import TurnBasedActionsMixin        # S4: untap/draw/land window (includes S1–S3)
from pab_cast_s6 import CastMixin                     # S6: cast_from_hand on the physical bridge (includes S1–S4)
from pab_r52_village_rites import VillageRitesCostMixin, EXPECTED_LEGACY_FAILURES   # R52: Village Rites costs {B}; supersedes frozen test_91 (+R01's 112/113)
class Game(VillageRitesCostMixin,TurnBasedActionsMixin,_sba.Game): pass
class PhysicalZoneGame(VillageRitesCostMixin,CastMixin,_sba.PhysicalZoneGame): pass
KERNEL_VERSION='v0.8+R02+R01+R47+R48+R49+S1+S2+S3+S4+S5+S6+R52+R53'
PROMOTED=["R02", "R01", "R47", "R48", "R49", "S1", "S2", "S3", "S4", "S5", "S6", "R52", "R53"]
SUPERSEDED_FROZEN_CONTRACTS=sorted(EXPECTED_LEGACY_FAILURES)
