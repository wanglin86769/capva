"""Parsing utilities for EPICS PV client"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, List, Optional, Union

import math

import numpy as np
from epics import dbr
from p4p.wrapper import Value as p4pValue

from .pv_data import PVData, Alarm, TimeStamp, Display, Control, ValueAlarm


def get_none_if_nan(obj, k: str):
    v = obj.get(k)
    return None if isinstance(v, float) and math.isnan(v) else v


def ca_alarm_message(status) -> str:
    try:
        return dbr.AlarmStatus(int(status)).name
    except (ValueError, TypeError):
        return "UNKNOWN"


# ---------------------------------------------------------------------------
# CA helpers
# ---------------------------------------------------------------------------


def _ca_normalize(v):
    """Converts numpy types and arrays to JSON-serializable Python types."""
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


def _ca_parse_value(pv_obj: dict) -> tuple[Any, Optional[List[str]]]:
    value_field = pv_obj.get("value")
    enumChoices = pv_obj.get("enum_strs")
    value = _ca_normalize(value_field)
    return value, enumChoices


def _ca_parse_alarm_ts(pv_obj: dict) -> tuple[Alarm, TimeStamp]:
    status = _ca_normalize(pv_obj.get("status", 0))
    alarm = Alarm(
        severity = _ca_normalize(pv_obj.get("severity", 0)),
        status = status,
        message = ca_alarm_message(status),
    )
    ts = _ca_normalize(pv_obj.get("timestamp", 0.0)) or 0.0
    sec = int(ts)
    nsec = int((ts - sec) * 1e9)
    timestamp = TimeStamp(
        secondsPastEpoch = sec,
        nanoseconds = nsec,
    )
    return alarm, timestamp


def _ca_parse_metadata_fields(
    pv_obj: dict,
) -> tuple[Display, Control, ValueAlarm]:
    display = Display(
        limitLow = _ca_normalize(get_none_if_nan(pv_obj, "lower_disp_limit")),
        limitHigh = _ca_normalize(get_none_if_nan(pv_obj, "upper_disp_limit")),
        units = pv_obj.get("units"),
        precision = _ca_normalize(get_none_if_nan(pv_obj, "precision")),
    )
    control = Control(
        limitLow = _ca_normalize(get_none_if_nan(pv_obj, "lower_ctrl_limit")),
        limitHigh = _ca_normalize(get_none_if_nan(pv_obj, "upper_ctrl_limit")),
    )
    value_alarm = ValueAlarm(
        lowAlarmLimit = _ca_normalize(get_none_if_nan(pv_obj, "lower_alarm_limit")),
        highAlarmLimit = _ca_normalize(get_none_if_nan(pv_obj, "upper_alarm_limit")),
        lowWarningLimit = _ca_normalize(get_none_if_nan(pv_obj, "lower_warning_limit")),
        highWarningLimit = _ca_normalize(get_none_if_nan(pv_obj, "upper_warning_limit")),

        # pyepics CA metadata has no hysteresis/HYST
        hysteresis = None,
    )
    return display, control, value_alarm


def ca_metadata(pv_obj: dict) -> dict[str, Any]:
    display, control, value_alarm = _ca_parse_metadata_fields(pv_obj)
    return {
        "display": asdict(display),
        "control": asdict(control),
        "valueAlarm": asdict(value_alarm),
    }


def _ca_to_pvdata(
    pv_obj: dict,
    pv_name: str,
    *,
    with_metadata: bool,
) -> PVData:
    value, enumChoices = _ca_parse_value(pv_obj)
    alarm, timestamp = _ca_parse_alarm_ts(pv_obj)
    display = control = value_alarm = None
    if with_metadata:
        display, control, value_alarm = _ca_parse_metadata_fields(pv_obj)
    return PVData(
        pvName = pv_name,
        value = value,
        enumChoices = enumChoices,
        alarm = alarm,
        timeStamp = timestamp,
        display = display,
        control = control,
        valueAlarm = value_alarm,
    )


def parse_ca(pv_obj: dict, pv_name: str) -> PVData:
    """Full CA snapshot: value, alarm, timeStamp, and metadata."""
    return _ca_to_pvdata(pv_obj, pv_name, with_metadata=True)


def parse_ca_update(pv_obj: dict, pv_name: str) -> PVData:
    """Fast CA monitor path: value, alarm, timeStamp only (no metadata)."""
    return _ca_to_pvdata(pv_obj, pv_name, with_metadata=False)


# ---------------------------------------------------------------------------
# PVA helpers
# ---------------------------------------------------------------------------


def _pva_parse_value(pv_obj) -> tuple[Any, Optional[List[str]]]:
    enumChoices: Optional[List[str]] = None
    value: Any = None

    value_field = pv_obj.get("value")

    if isinstance(value_field, (int, float, str)):
        value = value_field
    elif (
        isinstance(value_field, p4pValue)
        and value_field.has("index")
        and value_field.has("choices")
    ):
        value = value_field.get("index")
        enumChoices = value_field.get("choices")
    elif isinstance(value_field, (list, np.ndarray)):
        value = (
            value_field.tolist()
            if isinstance(value_field, np.ndarray)
            else list(value_field)
        )

    return value, enumChoices


def _pva_parse_alarm_ts(pv_obj) -> tuple[Alarm, TimeStamp]:
    a = pv_obj.get("alarm") or {}
    alarm = Alarm(
        severity = a.get("severity", 0),
        status = a.get("status", 0),
        message = a.get("message", "NO_ALARM"),
    )
    ts = pv_obj.get("timeStamp") or {}
    timestamp = TimeStamp(
        secondsPastEpoch = ts.get("secondsPastEpoch", 0),
        nanoseconds = ts.get("nanoseconds", 0),
        userTag = ts.get("userTag", 0),
    )
    return alarm, timestamp


def _pva_parse_metadata_fields(
    pv_obj,
) -> tuple[Display, Control, ValueAlarm]:
    d = pv_obj.get("display") or {}
    form = d.get("form") or {}
    display = Display(
        limitLow = get_none_if_nan(d, "limitLow"),
        limitHigh = get_none_if_nan(d, "limitHigh"),
        description = d.get("description"),
        units = d.get("units"),
        precision = d.get("precision"),
        form = form.get("index"),
        choices = form.get("choices"),
    )
    c = pv_obj.get("control") or {}
    control = Control(
        limitLow = get_none_if_nan(c, "limitLow"),
        limitHigh = get_none_if_nan(c, "limitHigh"),
        minStep = c.get("minStep"),
    )
    va = pv_obj.get("valueAlarm") or {}
    value_alarm = ValueAlarm(
        active = va.get("active"),
        lowAlarmLimit = get_none_if_nan(va, "lowAlarmLimit"),
        lowWarningLimit = get_none_if_nan(va, "lowWarningLimit"),
        highWarningLimit = get_none_if_nan(va, "highWarningLimit"),
        highAlarmLimit = get_none_if_nan(va, "highAlarmLimit"),
        lowAlarmSeverity = va.get("lowAlarmSeverity"),
        lowWarningSeverity = va.get("lowWarningSeverity"),
        highWarningSeverity = va.get("highWarningSeverity"),
        highAlarmSeverity = va.get("highAlarmSeverity"),
        hysteresis = get_none_if_nan(va, "hysteresis"),
    )
    return display, control, value_alarm


def pva_metadata(pv_obj) -> dict[str, Any]:
    display, control, value_alarm = _pva_parse_metadata_fields(pv_obj)
    return {
        "display": asdict(display),
        "control": asdict(control),
        "valueAlarm": asdict(value_alarm),
    }


def _pva_to_pvdata(
    pv_obj,
    pv_name: Optional[str],
    *,
    with_metadata: bool,
) -> PVData:
    value, enumChoices = _pva_parse_value(pv_obj)
    alarm, timestamp = _pva_parse_alarm_ts(pv_obj)
    display = control = value_alarm = None
    if with_metadata:
        display, control, value_alarm = _pva_parse_metadata_fields(pv_obj)
    return PVData(
        pvName = pv_name,
        value = value,
        enumChoices = enumChoices,
        alarm = alarm,
        timeStamp = timestamp,
        display = display,
        control = control,
        valueAlarm = value_alarm,
    )


def parse_pva(pv_obj, pv_name: Optional[str] = None) -> PVData:
    """Full PVA snapshot: value, alarm, timeStamp, and metadata."""
    return _pva_to_pvdata(pv_obj, pv_name, with_metadata=True)


def parse_pva_update(pv_obj, pv_name: Optional[str] = None) -> PVData:
    """Fast PVA monitor path: value, alarm, timeStamp only (no metadata)."""
    return _pva_to_pvdata(pv_obj, pv_name, with_metadata=False)
