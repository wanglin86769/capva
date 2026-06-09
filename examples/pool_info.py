"""PVPool: read channel metadata from a pooled PV, then release."""

import json
import sys

from capva import PVPool
from capva.exceptions import EPICSConnectionError, EPICSGetError, EPICSTimeoutError

PV_NAME = "pva://calcExample"

pv = PVPool.getPV(PV_NAME)
try:
    info = pv.info()
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    PVPool.releasePV(pv)

print(json.dumps(info, indent=2))
