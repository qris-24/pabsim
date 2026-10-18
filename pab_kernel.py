"""Canonical kernel entry point. Import Game / PhysicalZoneGame from here.

KERNEL_VERSION tracks promoted patches. Frozen historical modules
(pab_focus_engine v0.5, pab_focus_engine_v07, pab_zone_bridge, pab_zone_bridge_v08)
are never edited; each promotion layers on top and is verified by run_validation.py.
"""
from pab_r01_pest_rescuer import EXPECTED_LEGACY_FAILURES
import pab_r47_r48_sba as _sba                        # R47+R48+R49 layered on R01
from pab_clock_s4 import TurnBasedActionsMixin        # S4: untap/draw/land window (includes S1–S3)
class Game(TurnBasedActionsMixin,_sba.Game): pass
class PhysicalZoneGame(TurnBasedActionsMixin,_sba.PhysicalZoneGame): pass
KERNEL_VERSION='v0.8+R02+R01+R47+R48+R49+S1+S2+S3+S4+S5'
PROMOTED=["R02", "R01", "R47", "R48", "R49", "S1", "S2", "S3", "S4", "S5"]
SUPERSEDED_FROZEN_CONTRACTS=sorted(EXPECTED_LEGACY_FAILURES)
