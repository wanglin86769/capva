"""Procedural API: pvput — write a value."""

import sys

from capva import pvget, pvput
from capva.exceptions import (
    EPICSConnectionError,
    EPICSGetError,
    EPICSPutError,
    EPICSTimeoutError,
)

PV_NAME = "pva://calcExample"
PUT_VALUE = 3.14

try:
    before = pvget(PV_NAME)
    print(f"before: value={before.value!r}")

    pvput(PV_NAME, PUT_VALUE, wait=True)

    after = pvget(PV_NAME)
    print(f"after:  value={after.value!r}")
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError, EPICSPutError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
