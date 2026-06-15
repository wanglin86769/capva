"""Tests for parse_ca / parse_pva (no EPICS IOC required)."""

import json

import numpy as np
import pytest

from capva.array_b64 import encode_array
from capva.pv_data import PVData
from capva.pv_parser import (
    _ca_parse_metadata_fields,
    ca_metadata,
    parse_ca,
    parse_ca_update,
    parse_pva,
    parse_pva_update,
    pva_metadata,
)


def _ca_raw_scalar(*, with_metadata: bool = True) -> dict:
    raw = {
        "value": 3.14,
        "severity": 0,
        "status": 0,
        "timestamp": 1700000000.5,
    }
    if with_metadata:
        raw.update(
            {
                "lower_disp_limit": 0.0,
                "upper_disp_limit": 10.0,
                "units": "mm",
                "precision": 2,
                "lower_ctrl_limit": 0.0,
                "upper_ctrl_limit": 10.0,
            }
        )
    return raw


def _ca_raw_array() -> dict:
    return {
        "value": np.array([1.0, 2.0, 3.0], dtype=np.float64),
        "severity": 0,
        "status": 0,
        "timestamp": 1700000000.0,
    }


def _pva_raw_scalar(*, with_metadata: bool = True) -> dict:
    raw = {
        "value": 42,
        "alarm": {"severity": 0, "status": 0, "message": "NO_ALARM"},
        "timeStamp": {
            "secondsPastEpoch": 1700000000,
            "nanoseconds": 0,
            "userTag": 0,
        },
    }
    if with_metadata:
        raw["display"] = {"units": "counts", "precision": 0}
        raw["control"] = {}
        raw["valueAlarm"] = {}
    return raw


def test_parse_ca_full_has_metadata():
    pv = parse_ca(_ca_raw_scalar(), "motor:x")
    assert isinstance(pv, PVData)
    assert pv.pvName == "motor:x"
    assert pv.value == pytest.approx(3.14)
    assert pv.display is not None
    assert pv.display.units == "mm"


def test_parse_ca_update_omits_metadata():
    raw = _ca_raw_scalar(with_metadata=True)
    pv = parse_ca_update(raw, "motor:x")
    assert pv.pvName == "motor:x"
    assert pv.value == pytest.approx(3.14)
    assert pv.display is None
    assert pv.control is None
    assert pv.valueAlarm is None
    assert pv.alarm is not None
    assert pv.timeStamp is not None


def test_parse_ca_array_has_native_value():
    data = parse_ca(_ca_raw_array(), "wf:data")
    assert data.value == [1.0, 2.0, 3.0]


def test_parse_ca_full_matches_to_dict_full():
    raw = _ca_raw_scalar()
    pv = parse_ca(raw, "motor:x")
    full = pv.to_dict(mode="full")
    assert full["pvName"] == pv.pvName
    assert full["value"] == pv.value
    assert full["display"]["units"] == pv.display.units
    for key in ("pvName", "value", "alarm", "timeStamp", "display"):
        assert full[key] is not None


def test_ca_metadata_excludes_value():
    meta = ca_metadata(_ca_raw_scalar())
    assert "value" not in meta
    assert meta["display"]["units"] == "mm"
    assert "control" in meta
    assert "valueAlarm" in meta


def test_ca_metadata_nan_limits_become_none():
    raw = {
        "value": 1.0,
        "severity": 0,
        "status": 0,
        "timestamp": 0.0,
        "lower_disp_limit": float("nan"),
        "upper_disp_limit": 10.0,
        "lower_ctrl_limit": float("nan"),
        "upper_ctrl_limit": float("nan"),
        "units": "mm",
        "precision": 2,
        "lower_alarm_limit": float("nan"),
    }
    display, control, value_alarm = _ca_parse_metadata_fields(raw)
    assert display.limitLow is None
    assert display.limitHigh == 10.0
    assert control.limitLow is None
    assert control.limitHigh is None
    assert value_alarm.lowAlarmLimit is None

    pv = parse_ca(raw, "motor:x")
    json.dumps(pv.to_dict(mode="metadata"))


def test_parse_pva_full_has_metadata():
    pv = parse_pva(_pva_raw_scalar(), "pva:pv")
    assert isinstance(pv, PVData)
    assert pv.value == 42
    assert pv.display is not None
    assert pv.display.units == "counts"


def test_parse_pva_update_omits_metadata():
    raw = _pva_raw_scalar(with_metadata=True)
    pv = parse_pva_update(raw, "pva:pv")
    assert pv.pvName == "pva:pv"
    assert pv.value == 42
    assert pv.display is None
    assert pv.control is None
    assert pv.valueAlarm is None
    assert pv.alarm is not None
    assert pv.timeStamp is not None


def test_parse_pva_array_has_native_list():
    raw = {
        "value": [1.0, 2.0],
        "alarm": {"severity": 0, "status": 0, "message": "NO_ALARM"},
        "timeStamp": {"secondsPastEpoch": 0, "nanoseconds": 0, "userTag": 0},
    }
    pv = parse_pva(raw, "wf")
    assert pv.value == [1.0, 2.0]


def test_parse_pva_full_matches_to_dict_full():
    raw = _pva_raw_scalar()
    pv = parse_pva(raw, "pva:pv")
    full = pv.to_dict(mode="full")
    assert full["pvName"] == pv.pvName
    assert full["value"] == pv.value
    assert full["display"]["units"] == pv.display.units


def test_pva_metadata_excludes_value():
    meta = pva_metadata(_pva_raw_scalar())
    assert "value" not in meta
    assert meta["display"]["units"] == "counts"


def test_pva_metadata_nan_float_limits_become_none():
    raw = {
        "value": 1,
        "alarm": {"severity": 0, "status": 0, "message": "NO_ALARM"},
        "timeStamp": {"secondsPastEpoch": 0, "nanoseconds": 0, "userTag": 0},
        "display": {"limitLow": float("nan"), "limitHigh": 10.0, "precision": 2},
        "control": {"limitLow": float("nan"), "limitHigh": float("nan")},
        "valueAlarm": {"hysteresis": float("nan")},
    }
    meta = pva_metadata(raw)
    assert meta["display"]["limitLow"] is None
    assert meta["display"]["limitHigh"] == 10.0
    assert meta["display"]["precision"] == 2
    assert meta["control"]["limitLow"] is None
    assert meta["control"]["limitHigh"] is None
    assert meta["valueAlarm"]["hysteresis"] is None

    pv = parse_pva(raw, "pv")
    json.dumps(pv.to_dict(mode="metadata"))


def test_pva_metadata_none_subobjects_do_not_crash():
    raw = {
        "value": 1,
        "alarm": {"severity": 0, "status": 0, "message": "NO_ALARM"},
        "timeStamp": {"secondsPastEpoch": 0, "nanoseconds": 0, "userTag": 0},
        "display": None,
        "control": None,
        "valueAlarm": None,
    }
    meta = pva_metadata(raw)
    assert meta["display"]["units"] is None
    assert meta["control"]["limitLow"] is None
    assert meta["valueAlarm"]["active"] is None

    pv = parse_pva(raw, "pv")
    json.dumps(pv.to_dict(mode="metadata"))


def test_create_disconnected_omits_value():
    pv = PVData.create_disconnected("motor:x")
    assert pv.value is None
    assert pv.is_disconnected()
    assert not pv.is_array()
    wire = pv.to_dict(mode="update")
    assert wire["pvName"] == "motor:x"
    assert "value" not in wire
    assert wire["alarm"]["severity"] == 3
    assert wire["alarm"]["message"] == "Disconnected"
    json.dumps(wire)


def test_is_array():
    assert not PVData(pvName="X", value=1.0).is_array()
    assert not PVData(pvName="X", value="text").is_array()
    assert PVData(pvName="X", value=[1.0, 2.0]).is_array()
    assert PVData(pvName="X", value=["a", "b"]).is_array()
    assert PVData(pvName="X", value=[]).is_array()


def test_encode_array_from_ndarray():
    arr = np.array([100000, 200000, 300000], dtype=np.int32)
    b64, dtype = encode_array(arr)
    assert b64 is not None
    assert dtype == "int32"


def test_to_dict_update_base64_encode():
    pv = parse_ca(_ca_raw_array(), "wf:data")
    wire = pv.to_dict(mode="update", base64_encode=True)
    assert "value" not in wire
    assert wire["b64arr"] is not None
    assert wire["b64dtype"] == "float64"
    assert wire["pvName"] == "wf:data"


def test_to_dict_full_base64_encode():
    pv = parse_ca(_ca_raw_array(), "wf:data")
    wire = pv.to_dict(mode="full", base64_encode=True)
    assert "value" not in wire
    assert wire["b64arr"] is not None
    assert wire["b64dtype"] == "float64"


def test_to_dict_metadata_ignores_base64_encode():
    raw = _ca_raw_scalar()
    pv = parse_ca(raw, "motor:x")
    meta = pv.to_dict(mode="metadata", base64_encode=True)
    assert "b64arr" not in meta
    assert "b64dtype" not in meta
