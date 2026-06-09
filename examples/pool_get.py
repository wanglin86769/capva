"""PVPool: two getPV calls share the same pooled PV instance."""

import sys

from capva import PVPool
from capva.exceptions import EPICSConnectionError, EPICSGetError, EPICSTimeoutError

PV_NAME = "pva://calcExample"

pv1 = PVPool.getPV(PV_NAME)
pv2 = PVPool.getPV(PV_NAME)
try:
    print(f"same instance: {pv1 is pv2}")
    print(f"refs after getPV: {PVPool.getReferenceCount(PV_NAME)}")

    data = pv1.get()
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    PVPool.releasePV(pv1)
    PVPool.releasePV(pv2)
    print(f"refs after release: {PVPool.getReferenceCount(PV_NAME)}")

print(data.to_json(mode="full", indent=2))
