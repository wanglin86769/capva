"""PVPool: write on a pooled PV, then release."""

import sys

from capva import PVPool
from capva.exceptions import (
    EPICSConnectionError,
    EPICSGetError,
    EPICSPutError,
    EPICSTimeoutError,
)

PV_NAME = "pva://calcExample"
PUT_VALUE = 3.14

pv = PVPool.getPV(PV_NAME)
try:
    before = pv.get()
    print(f"before: value={before.value!r}")

    pv.put(PUT_VALUE, wait=True)

    after = pv.get()
    print(f"after:  value={after.value!r}")
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError, EPICSPutError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    PVPool.releasePV(pv)
