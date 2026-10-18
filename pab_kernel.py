"""Canonical kernel entry point. Import Game / PhysicalZoneGame from here.

KERNEL_VERSION tracks promoted patches. Frozen historical modules
(pab_focus_engine v0.5, pab_focus_engine_v07, pab_zone_bridge, pab_zone_bridge_v08)
are never edited; each promotion layers on top and is verified by run_validation.py.
"""
from pab_r01_pest_rescuer import EXPECTED_LEGACY_FAILURES
import pab_r47_r48_sba as _sba                        # R47+R48+R49 layered on R01
from pab_clock_s3 import PriorityMixin                # S3: SBA between resolutions + trigger ordering (includes S1/S2)
class Game(PriorityMixin,_sba.Game): pass
class PhysicalZoneGame(PriorityMixin,_sba.PhysicalZoneGame): pass
KERNEL_VERSION='v0.8+R02+R01+R47+R48+R49+S1+S2+S3'
PROMOTED=["R02", "R01", "R47", "R48", "R49", "S1", "S2", "S3"]
SUPERSEDED_FROZEN_CONTRACTS=sorted(EXPECTED_LEGACY_FAILURES)
