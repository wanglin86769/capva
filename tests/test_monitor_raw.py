"""Tests for raw monitor events and deferred parsing."""

import numpy as np
import pytest

from capva.monitor_raw import (
    RawMonitorEvent,
    parse_raw_monitor_to_pvdata,
    parse_raw_monitor_to_update_dict,
    parse_raw_monitor_to_metadata_dict,
    raw_monitor_is_array,
)
from capva.protocol import CA, PVA
from capva.pv_parser import ca_alarm_message


def _ca_raw() -> dict:
    return {
        "value": 1.23,
        "severity": 0,
        "status": 0,
        "timestamp": 1700000000.5,
        "units": "mm",
        "precision": 2,
        "lower_disp_limit": 0.0,
        "upper_disp_limit": 100.0,
        "lower_ctrl_limit": 0.0,
        "upper_ctrl_limit": 100.0,
        "lower_alarm_limit": 0.0,
        "upper_alarm_limit": 100.0,
        "lower_warning_limit": 10.0,
        "upper_warning_limit": 90.0,
    }


def test_parse_raw_monitor_to_pvdata_connected():
    event = RawMonitorEvent(protocol=CA, pvname="TEST:PV", payload=_ca_raw())
    data = parse_raw_monitor_to_pvdata(event, with_metadata=False)
    assert data.pvName == "TEST:PV"
    assert data.value == 1.23
    assert data.display is None


def test_parse_raw_monitor_to_pvdata_with_metadata():
    event = RawMonitorEvent(protocol=CA, pvname="TEST:PV", payload=_ca_raw())
    data = parse_raw_monitor_to_pvdata(event, with_metadata=True)
    assert data.display is not None
    assert data.display.units == "mm"


def test_parse_raw_monitor_to_pvdata_disconnected():
    event = RawMonitorEvent(protocol=CA, pvname="TEST:PV", disconnected=True)
    data = parse_raw_monitor_to_pvdata(event)
    assert data.is_disconnected()


def test_parse_raw_monitor_to_metadata_dict():
    event = RawMonitorEvent(protocol=CA, pvname="TEST:PV", payload=_ca_raw())
    meta = parse_raw_monitor_to_metadata_dict(event)
    assert meta["display"]["units"] == "mm"
    assert "control" in meta
    assert "valueAlarm" in meta


@pytest.mark.parametrize("base64_encode", [False, True])
def test_parse_raw_monitor_to_update_dict_matches_pvdata_scalar(base64_encode):
    event = RawMonitorEvent(protocol=CA, pvname="TEST:PV", payload=_ca_raw())
    expected = parse_raw_monitor_to_pvdata(event).to_dict(
        mode="update", base64_encode=base64_encode
    )
    assert parse_raw_monitor_to_update_dict(event, base64_encode=base64_encode) == expected
    assert expected["pvName"] == "TEST:PV"
    assert expected["alarm"]["message"] == ca_alarm_message(0)


@pytest.mark.parametrize("base64_encode", [False, True])
def test_parse_raw_monitor_to_update_dict_matches_pvdata_array(base64_encode):
    payload = _ca_raw()
    payload["value"] = np.arange(3, dtype=np.float64)
    event = RawMonitorEvent(protocol=CA, pvname="TEST:PV", payload=payload)
    expected = parse_raw_monitor_to_pvdata(event).to_dict(
        mode="update", base64_encode=base64_encode
    )
    assert parse_raw_monitor_to_update_dict(event, base64_encode=base64_encode) == expected
    if base64_encode:
        assert "b64arr" in expected
        assert "value" not in expected
    else:
        assert expected["value"] == [0.0, 1.0, 2.0]


def test_parse_raw_monitor_to_update_dict_disconnected():
    event = RawMonitorEvent(protocol=CA, pvname="TEST:PV", disconnected=True)
    expected = parse_raw_monitor_to_pvdata(event).to_dict(mode="update")
    assert parse_raw_monitor_to_update_dict(event) == expected
    assert expected["alarm"]["message"] == "Disconnected"


class _PvaEnumValue:
    def has(self, key: str) -> bool:
        return key in ("index", "choices")

    def get(self, key: str):
        return {"index": 2, "choices": ["OFF", "ON"]}[key]


@pytest.mark.parametrize(
    ("event",),
    [
        (RawMonitorEvent(protocol=CA, pvname="TEST:PV", payload=_ca_raw()),),
        (
            RawMonitorEvent(
                protocol=CA,
                pvname="TEST:PV",
                payload={**_ca_raw(), "value": np.arange(3, dtype=np.float64)},
            ),
        ),
        (
            RawMonitorEvent(
                protocol=CA,
                pvname="TEST:PV",
                payload={**_ca_raw(), "value": [1.0, 2.0]},
            ),
        ),
        (
            RawMonitorEvent(
                protocol=CA,
                pvname="TEST:PV",
                payload={**_ca_raw(), "value": [1.0]},
            ),
        ),
        (
            RawMonitorEvent(
                protocol=CA,
                pvname="TEST:PV",
                payload={**_ca_raw(), "value": np.array(3.0)},
            ),
        ),
        (RawMonitorEvent(protocol=CA, pvname="TEST:PV", disconnected=True),),
        (
            RawMonitorEvent(
                protocol=PVA,
                pvname="TEST:PV",
                payload={"value": 1.23, "alarm": {}, "timeStamp": {}},
            ),
        ),
        (
            RawMonitorEvent(
                protocol=PVA,
                pvname="TEST:PV",
                payload={"value": _PvaEnumValue(), "alarm": {}, "timeStamp": {}},
            ),
        ),
        (
            RawMonitorEvent(
                protocol=PVA,
                pvname="TEST:PV",
                payload={"value": [1.0, 2.0], "alarm": {}, "timeStamp": {}},
            ),
        ),
        (
            RawMonitorEvent(
                protocol=PVA,
                pvname="TEST:PV",
                payload={
                    "value": np.arange(2, dtype=np.float64),
                    "alarm": {},
                    "timeStamp": {},
                },
            ),
        ),
    ],
)
def test_raw_monitor_is_array_matches_pvdata_is_array(event: RawMonitorEvent) -> None:
    if event.disconnected:
        assert raw_monitor_is_array(event) is False
        return
    assert raw_monitor_is_array(event) == parse_raw_monitor_to_pvdata(event).is_array()
