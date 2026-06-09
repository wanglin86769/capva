"""Protocol detection and constants for EPICS PV client."""

from typing import Tuple

CA = "ca"
PVA = "pva"
DEFAULT_PROTOCOL = CA


def parse_protocol(pv_name: str) -> Tuple[str, str]:
    if pv_name.startswith("pva://"):
        return PVA, pv_name[6:]
    elif pv_name.startswith("ca://"):
        return CA, pv_name[5:]
    return DEFAULT_PROTOCOL, pv_name


def pvname_key(pvname: str) -> str:
    protocol, clean_name = parse_protocol(pvname)
    return f"{protocol}:{clean_name}"
