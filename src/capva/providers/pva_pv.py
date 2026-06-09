"""EPICS PVAccess (PVA) PV implementation using p4p"""

from typing import Any, Callable

from p4p.client.thread import Context, Disconnected, TimeoutError
from ..constants import DEFAULT_IO_TIMEOUT
from ..pv_data import PVData
from ..pv_parser import parse_pva, parse_pva_update, pva_metadata
from ..monitor_handle import MonitorHandle
from ..exceptions import EPICSTimeoutError, EPICSConnectionError, EPICSGetError, EPICSPutError

_pva_context = Context("pva", nt=False)


class PVAPV:
    def __init__(self, pvname: str):
        self.pvname = pvname
        self._subscriptions: list = []

    def get(self, *, timeout: float = DEFAULT_IO_TIMEOUT) -> PVData:
        pva_value = _pva_context.get(
            self.pvname, timeout=timeout, throw=False
        )
        if isinstance(pva_value, Exception):
            if isinstance(pva_value, TimeoutError):
                raise EPICSTimeoutError(
                    f"Get operation timed out after {timeout}s for {self.pvname}"
                )
            if isinstance(pva_value, Disconnected):
                raise EPICSConnectionError(
                    f"PV {self.pvname} not connected: {pva_value}"
                )
            raise EPICSGetError(
                f"Failed to get {self.pvname}: "
                f"{type(pva_value).__name__}: {pva_value}"
            )
        return parse_pva(pva_value, self.pvname)

    def put(self, value, *, timeout: float = DEFAULT_IO_TIMEOUT, wait: bool = False) -> None:
        result = _pva_context.put(
            self.pvname,
            value,
            timeout=timeout,
            wait=wait,
            throw=False,
        )
        if result is not None:
            if isinstance(result, TimeoutError):
                raise EPICSTimeoutError(
                    f"Put operation timed out after {timeout}s for {self.pvname}"
                )
            if isinstance(result, Disconnected):
                raise EPICSConnectionError(
                    f"PV {self.pvname} not connected: {result}"
                )
            raise EPICSPutError(
                f"Failed to put {self.pvname}: "
                f"{type(result).__name__}: {result}"
            )

    def info(self, *, timeout: float = DEFAULT_IO_TIMEOUT) -> dict[str, Any]:
        pva_value = _pva_context.get(
            self.pvname, timeout=timeout, throw=False
        )
        if isinstance(pva_value, Exception):
            if isinstance(pva_value, TimeoutError):
                raise EPICSTimeoutError(
                    f"Get operation timed out after {timeout}s for {self.pvname}"
                )
            if isinstance(pva_value, Disconnected):
                raise EPICSConnectionError(
                    f"PV {self.pvname} not connected: {pva_value}"
                )
            raise EPICSGetError(
                f"Failed to get {self.pvname}: "
                f"{type(pva_value).__name__}: {pva_value}"
            )

        info: dict[str, Any] = {
            "pvName": self.pvname,
            "protocol": "pva",
            "state": "CONNECTED",
            "host": "",
            "type": pva_value.getID(),
        }
        info.update(pva_metadata(pva_value))
        return info

    def monitor(
        self,
        callback: Callable[[PVData], None],
    ) -> MonitorHandle:
        def wrapped_callback(pva_update):
            if isinstance(pva_update, Disconnected):
                callback(PVData.create_disconnected(self.pvname))
                return
            if isinstance(pva_update, Exception):
                return
            callback(parse_pva_update(pva_update, self.pvname))

        subscription = _pva_context.monitor(
            self.pvname, wrapped_callback, notify_disconnect=True
        )
        self._subscriptions.append(subscription)
        return MonitorHandle(self, subscription)

    def clear_monitor(self, handle: MonitorHandle) -> None:
        if handle._owner is not self:
            raise ValueError(
                f"MonitorHandle does not belong to PV {self.pvname!r}"
            )
        subscription = handle._handle
        subscription.close()
        try:
            self._subscriptions.remove(subscription)
        except ValueError:
            pass

    def disconnect(self) -> None:
        for subscription in list(self._subscriptions):
            subscription.close()
        self._subscriptions.clear()
        # This call is optional in p4p; unused channels are removed from the context cache after ~20 seconds.
        # _pva_context.disconnect(self.pvname)

    def close(self) -> None:
        self.disconnect()
