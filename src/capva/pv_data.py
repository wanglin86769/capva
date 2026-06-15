"""Data models for EPICS PV client"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, List, Literal, Optional, Union

from .array_b64 import encode_array


# NormativeType data definitions
# See: https://docs.epics-controls.org/en/latest/pv-access/Normative-Types-Specification.html
@dataclass
class Alarm:
    severity: int = 0
    status: int = 0
    message: str = "NO_ALARM"


@dataclass
class TimeStamp:
    secondsPastEpoch: int = 0
    nanoseconds: int = 0
    userTag: int = 0


@dataclass
class Display:
    limitLow: Optional[float] = None
    limitHigh: Optional[float] = None
    description: Optional[str] = None
    units: Optional[str] = None
    precision: Optional[int] = None
    form: Optional[int] = None
    choices: Optional[List[str]] = None


@dataclass
class Control:
    limitLow: Optional[float] = None
    limitHigh: Optional[float] = None
    minStep: Optional[float] = None


@dataclass
class ValueAlarm:
    active: Optional[bool] = None
    lowAlarmLimit: Optional[float] = None
    lowWarningLimit: Optional[float] = None
    highWarningLimit: Optional[float] = None
    highAlarmLimit: Optional[float] = None
    lowAlarmSeverity: Optional[int] = None
    lowWarningSeverity: Optional[int] = None
    highWarningSeverity: Optional[int] = None
    highAlarmSeverity: Optional[int] = None
    hysteresis: Optional[float] = None


@dataclass
class PVData:
    pvName: Optional[str] = None
    value: Optional[Union[float, int, str, List[float], List[int], List[str]]] = None
    enumChoices: Optional[List[str]] = None
    alarm: Optional[Alarm] = None
    timeStamp: Optional[TimeStamp] = None
    display: Optional[Display] = None
    control: Optional[Control] = None
    valueAlarm: Optional[ValueAlarm] = None

    @classmethod
    def create_disconnected(cls, pvname: str) -> "PVData":
        # Alarm shape aligned with org.epics.vtype.Alarm.disconnected():
        # INVALID(3), CLIENT(7), "Disconnected"
        return cls(
            pvName=pvname,
            alarm=Alarm(severity=3, status=7, message="Disconnected"),
        )

    def is_disconnected(self) -> bool:
        alarm = self.alarm
        return (
            alarm is not None
            and alarm.severity == 3
            and alarm.status == 7
            and alarm.message == "Disconnected"
        )

    def to_dict(
        self,
        *,
        mode: Literal["full", "update", "metadata"] = "full",
        base64_encode: bool = False,
    ) -> dict[str, Any]:
        if mode == "full":
            d = {k: v for k, v in asdict(self).items() if v is not None}
            if base64_encode and isinstance(self.value, list):
                b64, dtype = encode_array(self.value)
                if b64 is not None:
                    d.pop("value", None)
                    d["b64arr"] = b64
                    d["b64dtype"] = dtype
            return d

        if mode == "update":
            d: dict[str, Any] = {}
            if self.pvName is not None:
                d["pvName"] = self.pvName
            if base64_encode and isinstance(self.value, list):
                b64, dtype = encode_array(self.value)
                if b64 is not None:
                    d["b64arr"] = b64
                    d["b64dtype"] = dtype
                elif self.value is not None:
                    d["value"] = self.value
            elif self.value is not None:
                d["value"] = self.value
            if self.enumChoices is not None:
                d["enumChoices"] = self.enumChoices
            if self.alarm is not None:
                d["alarm"] = asdict(self.alarm)
            if self.timeStamp is not None:
                d["timeStamp"] = asdict(self.timeStamp)
            return d

        if mode == "metadata":
            d = {}
            if self.display is not None:
                d["display"] = asdict(self.display)
            if self.control is not None:
                d["control"] = asdict(self.control)
            if self.valueAlarm is not None:
                d["valueAlarm"] = asdict(self.valueAlarm)
            return d

        raise ValueError(
            f"mode must be 'full', 'update', or 'metadata', got {mode!r}"
        )

    def to_json(
        self,
        *,
        mode: Literal["full", "update", "metadata"] = "full",
        base64_encode: bool = False,
        **kwargs: Any,
    ) -> str:
        return json.dumps(
            self.to_dict(mode=mode, base64_encode=base64_encode),
            **kwargs,
        )
