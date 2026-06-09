"""Unified PV client interface for EPICS CA and PVA"""

from typing import Any, Callable

from .constants import DEFAULT_IO_TIMEOUT
from .pv_data import PVData
from .monitor_handle import MonitorHandle
from .protocol import parse_protocol, CA, PVA
from .providers.ca_pv import CAPV
from .providers.pva_pv import PVAPV
from .exceptions import (
    EPICSProtocolError,
    EPICSConnectionError,
    EPICSGetError,
    EPICSPutError,
    EPICSTimeoutError,
)


class PV:
    def __init__(self, pvname: str):
        protocol, clean_name = parse_protocol(pvname)
        self.protocol = protocol
        self.pvname = clean_name

        if protocol == CA:
            self._pv = CAPV(clean_name)
        elif protocol == PVA:
            self._pv = PVAPV(clean_name)
        else:
            raise EPICSProtocolError(f"Unsupported protocol: {protocol}")

    def get(self, *, timeout: float = DEFAULT_IO_TIMEOUT) -> PVData:
        return self._pv.get(timeout=timeout)

    def get_or_none(self, *, timeout: float = DEFAULT_IO_TIMEOUT) -> PVData | None:
        try:
            return self.get(timeout=timeout)
        except (EPICSTimeoutError, EPICSConnectionError):
            return None

    def put(self, value, *, timeout: float = DEFAULT_IO_TIMEOUT, wait: bool = False) -> None:
        self._pv.put(value, timeout=timeout, wait=wait)

    def put_or_false(self, value, *, timeout: float = DEFAULT_IO_TIMEOUT, wait: bool = False) -> bool:
        try:
            self.put(value, timeout=timeout, wait=wait)
            return True
        except (EPICSTimeoutError, EPICSConnectionError, EPICSPutError):
            return False

    def info(self, *, timeout: float = DEFAULT_IO_TIMEOUT) -> dict[str, Any]:
        return self._pv.info(timeout=timeout)

    def monitor(
        self,
        callback: Callable[[PVData], None],
    ) -> MonitorHandle:
        return self._pv.monitor(callback)

    def clear_monitor(self, handle: MonitorHandle) -> None:
        self._pv.clear_monitor(handle)

    def disconnect(self) -> None:
        self._pv.disconnect()

    def close(self) -> None:
        self._pv.close()
