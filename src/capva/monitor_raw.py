"""Raw monitor events and deferred parsing helpers."""

from dataclasses import dataclass
from typing import Any, Literal

from .protocol import CA, PVA
from .pv_data import PVData
from .pv_parser import (
    ca_metadata,
    ca_monitor_dict,
    disconnected_update_dict,
    parse_ca_update,
    pva_metadata,
    pva_monitor_dict,
    parse_pva_update,
)


@dataclass(frozen=True, slots=True)
class RawMonitorEvent:
    """Unparsed monitor event from CA or PVA (`monitor_raw()`)."""

    protocol: Literal["ca", "pva"]
    pvname: str
    payload: Any | None = None
    disconnected: bool = False


def raw_monitor_disconnected(
    protocol: Literal["ca", "pva"], pvname: str
) -> RawMonitorEvent:
    return RawMonitorEvent(protocol=protocol, pvname=pvname, disconnected=True)


def parse_raw_monitor_to_pvdata(
    event: RawMonitorEvent,
    *,
    with_metadata: bool = False,
) -> PVData:
    if event.disconnected:
        return PVData.create_disconnected(event.pvname)
    if event.payload is None:
        raise ValueError("connected RawMonitorEvent requires payload")
    if event.protocol == CA:
        return parse_ca_update(
            event.payload, event.pvname, with_metadata=with_metadata
        )
    else:
        return parse_pva_update(
            event.payload, event.pvname, with_metadata=with_metadata
        )


def parse_raw_monitor_to_metadata_dict(event: RawMonitorEvent) -> dict[str, Any]:
    if event.disconnected or event.payload is None:
        return {}
    if event.protocol == CA:
        return ca_metadata(event.payload)
    else:
        return pva_metadata(event.payload)


def parse_raw_monitor_to_update_dict(
    event: RawMonitorEvent,
    *,
    base64_encode: bool = True,
) -> dict[str, Any]:
    """Parse raw monitor event to update dict."""
    if event.disconnected:
        return disconnected_update_dict(event.pvname)
    if event.payload is None:
        raise ValueError("connected RawMonitorEvent requires payload")
    if event.protocol == CA:
        return ca_monitor_dict(
            event.payload, event.pvname, base64_encode=base64_encode
        )
    else:
        return pva_monitor_dict(
            event.payload, event.pvname, base64_encode=base64_encode
        )
