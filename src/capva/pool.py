"""Reference-counted pool of PV instances keyed by protocol and name."""

from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Dict, List, Tuple

from .protocol import pvname_key
from .pv import PV


def _pool_key_from_pv(pv: PV) -> str:
    return f"{pv.protocol}:{pv.pvname}"


@dataclass
class _PoolEntry:
    pv: PV
    refs: int = 0


class PVPool:
    _lock = threading.Lock()
    _entries: Dict[str, _PoolEntry] = {}

    @classmethod
    def getPV(cls, pvname: str) -> PV:
        if not pvname or not pvname.strip():
            raise ValueError("pvname must be a non-empty string")

        key = pvname_key(pvname)
        with cls._lock:
            entry = cls._entries.get(key)
            if entry is None:
                entry = _PoolEntry(pv=PV(pvname))
                cls._entries[key] = entry
            entry.refs += 1
            return entry.pv

    @classmethod
    def releasePV(cls, pv: PV) -> None:
        key = _pool_key_from_pv(pv)
        with cls._lock:
            entry = cls._entries.get(key)
            if entry is None:
                return
            entry.refs -= 1
            if entry.refs <= 0:
                entry.pv.close()
                del cls._entries[key]

    @classmethod
    def getReferenceCount(cls, pvname: str) -> int:
        key = pvname_key(pvname)
        with cls._lock:
            entry = cls._entries.get(key)
            return entry.refs if entry else 0

    @classmethod
    def getPVReferences(cls) -> List[Tuple[str, PV, int]]:
        with cls._lock:
            return [
                (key, entry.pv, entry.refs)
                for key, entry in cls._entries.items()
            ]
