"""EPICS Channel Access (CA) PV implementation using pyepics"""

from dataclasses import dataclass
from typing import Any, Callable

import epics
from epics.ca import ChannelAccessGetFailure, ChannelAccessException
from ..constants import DEFAULT_IO_TIMEOUT
from ..exceptions import EPICSConnectionError, EPICSGetError, EPICSPutError, EPICSTimeoutError
from ..monitor_handle import MonitorHandle
from ..monitor_raw import RawMonitorEvent, raw_monitor_disconnected
from ..protocol import CA
from ..pv_data import PVData
from ..pv_parser import ca_metadata, parse_ca, parse_ca_update


@dataclass
class _MonitorEntry:
    callback: Callable[[PVData], None] | Callable[[RawMonitorEvent], None]
    raw: bool


class CAPV:
    def __init__(self, pvname: str):
        self.pvname = pvname
        self._pv = epics.PV(pvname)
        self._monitors: dict[int, _MonitorEntry] = {}

    def get(self, *, timeout: float = DEFAULT_IO_TIMEOUT) -> PVData:
        if not self._pv.wait_for_connection(timeout=timeout):
            raise EPICSConnectionError(f"PV {self.pvname} not connected")

        try:
            ca_dict = self._pv.get_with_metadata(
                with_ctrlvars=True,
                use_monitor=False,
                timeout=timeout,
            )
        except ChannelAccessGetFailure as e:
            raise EPICSGetError(
                f"Get failed for {self.pvname}: {e}"
            )
        if ca_dict is None:
            raise EPICSTimeoutError(
                f"Get operation timed out after {timeout}s for {self.pvname}"
            )
        return parse_ca(ca_dict, self.pvname)

    def put(self, value, *, timeout: float = DEFAULT_IO_TIMEOUT, wait: bool = False) -> None:
        if not self._pv.wait_for_connection(timeout=timeout):
            raise EPICSConnectionError(f"PV {self.pvname} not connected")

        try:
            result = self._pv.put(value, wait=wait, timeout=timeout)
        except ChannelAccessException as e:
            raise EPICSPutError(f"Put failed for {self.pvname}: {e}")

        if result is None:
            raise EPICSConnectionError(f"PV {self.pvname} not connected")
        elif result == 1:
            pass
        elif result == -1:
            if wait:
                raise EPICSTimeoutError(
                    f"Put timed out after {timeout}s for {self.pvname}"
                )
            raise EPICSPutError(
                f"Put failed for {self.pvname}: unexpected result {result}"
            )
        else:
            raise EPICSPutError(
                f"Put failed for {self.pvname}: unexpected result {result}"
            )

    def info(self, *, timeout: float = DEFAULT_IO_TIMEOUT) -> dict[str, Any]:
        if not self._pv.wait_for_connection(timeout=timeout):
            raise EPICSConnectionError(f"PV {self.pvname} not connected")

        try:
            ca_dict = self._pv.get_with_metadata(
                with_ctrlvars=True,
                use_monitor=False,
                timeout=timeout,
            )
        except ChannelAccessGetFailure as e:
            raise EPICSGetError(
                f"Get failed for {self.pvname}: {e}"
            )
        if ca_dict is None:
            raise EPICSTimeoutError(
                f"Get operation timed out after {timeout}s for {self.pvname}"
            )

        base_type = self._pv.type
        type_str = f"{base_type}[]" if self._pv.nelm > 1 else base_type
        info: dict[str, Any] = {
            "pvName": self.pvname,
            "protocol": "ca",
            "state": "CONNECTED",
            "host": self._pv.host or "",
            "type": type_str,
        }
        info.update(ca_metadata(ca_dict))
        return info

    def _notify_disconnected(self, entry: _MonitorEntry) -> None:
        if entry.raw:
            entry.callback(raw_monitor_disconnected(CA, self.pvname))
        else:
            entry.callback(PVData.create_disconnected(self.pvname))

    def _on_connection_change(self, *, conn=None, **kw):
        if conn:
            return
        for entry in self._monitors.values():
            self._notify_disconnected(entry)

    def monitor(self, callback: Callable[[PVData], None]) -> MonitorHandle:
        return self._monitor(callback, raw=False)

    def monitor_raw(self, callback: Callable[[RawMonitorEvent], None]) -> MonitorHandle:
        return self._monitor(callback, raw=True)

    def _monitor(
        self,
        callback: Callable[[PVData], None] | Callable[[RawMonitorEvent], None],
        *,
        raw: bool,
    ) -> MonitorHandle:
        if not self._monitors:
            self._pv.connection_callbacks.append(self._on_connection_change)

        entry = _MonitorEntry(callback=callback, raw=raw)

        def wrapped_callback(**ca_kwargs):
            if raw:
                callback(RawMonitorEvent(protocol=CA, pvname=self.pvname, payload=ca_kwargs))
            else:
                callback(parse_ca_update(ca_kwargs, self.pvname, with_metadata=False))

        # run_now=False: CA monitor delivers an initial update on subscribe;
        # True would duplicate it via run_callback.
        index = self._pv.add_callback(
            wrapped_callback,
            with_ctrlvars=True,
            run_now=False,
        )
        self._monitors[index] = entry

        if not self._pv.connected:
            self._notify_disconnected(entry)

        return MonitorHandle(self, index)

    def clear_monitor(self, handle: MonitorHandle) -> None:
        if handle._owner is not self:
            raise ValueError(
                f"MonitorHandle does not belong to PV {self.pvname!r}"
            )
        self._monitors.pop(handle._handle, None)
        self._pv.remove_callback(handle._handle)
        if not self._monitors:
            try:
                self._pv.connection_callbacks.remove(self._on_connection_change)
            except ValueError:
                pass

    def disconnect(self) -> None:
        self._monitors.clear()
        try:
            self._pv.connection_callbacks.remove(self._on_connection_change)
        except ValueError:
            pass
        # Clears monitor callbacks and the shared CA subscription;
        # explicit remove_callback is unnecessary.
        self._pv.disconnect()

    def close(self) -> None:
        chid = self._pv.chid
        self.disconnect()
        if chid is not None:
            try:
                epics.ca.clear_channel(chid)
            except Exception:
                pass
