"""
capva - Unified EPICS Process Variable client (CA + PVA).

Supports both Channel Access (CA) and PV Access (PVA) with a single, consistent API.
Automatically selects the optimal backend: p4p for PVA, pyepics for CA.
"""

from .constants import DEFAULT_IO_TIMEOUT
from .pv import PV
from .pv_data import PVData
from .pool import PVPool
from .monitor_handle import MonitorHandle
from .tools import MonitorSession, pvget, pvinfo, pvmonitor, pvput
from .exceptions import (
    EPICSProtocolError,
    EPICSConnectionError,
    EPICSGetError,
    EPICSPutError,
    EPICSTimeoutError,
)

__all__ = [
    "PV",
    "PVData",
    "PVPool",
    "MonitorHandle",
    "pvget",
    "pvput",
    "pvinfo",
    "MonitorSession",
    "pvmonitor",
    "EPICSProtocolError",
    "EPICSConnectionError",
    "EPICSGetError",
    "EPICSPutError",
    "EPICSTimeoutError",
]
