"""
capva - Unified EPICS Process Variable client (CA + PVA).

Supports both Channel Access (CA) and PV Access (PVA) with a single, consistent API.
Automatically selects the optimal backend: p4p for PVA, pyepics for CA.
"""

from .monitor_raw import (
    RawMonitorEvent,
    parse_raw_monitor_to_pvdata,
    parse_raw_monitor_to_update_dict,
    parse_raw_monitor_to_metadata_dict,
)
from .pool import PVPool
from .pv import PV
from .pv_data import PVData
from .tools import pvget, pvinfo, pvmonitor, pvmonitor_raw, pvput
from .exceptions import (
    EPICSConnectionError,
    EPICSGetError,
    EPICSPutError,
    EPICSTimeoutError,
)

__all__ = [
    "PV",
    "PVData",
    "PVPool",
    "RawMonitorEvent",
    "parse_raw_monitor_to_pvdata",
    "parse_raw_monitor_to_update_dict",
    "parse_raw_monitor_to_metadata_dict",
    "pvget",
    "pvput",
    "pvinfo",
    "pvmonitor",
    "pvmonitor_raw",
    "EPICSConnectionError",
    "EPICSGetError",
    "EPICSPutError",
    "EPICSTimeoutError",
]
