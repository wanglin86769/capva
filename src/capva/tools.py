"""Procedural API aligned with EPICS pvget, pvput, pvinfo, and pvmonitor."""

from __future__ import annotations

from typing import Any, Callable

from .constants import DEFAULT_IO_TIMEOUT
from .monitor_handle import MonitorHandle
from .pv import PV
from .pv_data import PVData


class MonitorSession:
    def __init__(self, pv: PV, handle: MonitorHandle) -> None:
        self._pv = pv
        self._handle = handle

    def close(self) -> None:
        pv = self._pv
        if pv is None:
            return
        self._pv = None
        pv.clear_monitor(self._handle)
        pv.close()


def pvget(
    pvname: str,
    *,
    timeout: float = DEFAULT_IO_TIMEOUT,
) -> PVData:
    pv = PV(pvname)
    try:
        return pv.get(timeout=timeout)
    finally:
        pv.close()


def pvput(
    pvname: str,
    value,
    *,
    timeout: float = DEFAULT_IO_TIMEOUT,
    wait: bool = False,
) -> None:
    pv = PV(pvname)
    try:
        pv.put(value, timeout=timeout, wait=wait)
    finally:
        pv.close()


def pvinfo(
    pvname: str,
    *,
    timeout: float = DEFAULT_IO_TIMEOUT,
) -> dict[str, Any]:
    pv = PV(pvname)
    try:
        return pv.info(timeout=timeout)
    finally:
        pv.close()


def pvmonitor(
    pvname: str,
    callback: Callable[[PVData], None],
) -> MonitorSession:
    pv = PV(pvname)
    handle = pv.monitor(callback)
    return MonitorSession(pv, handle)
