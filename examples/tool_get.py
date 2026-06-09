"""Procedural API: pvget — read and print PVData."""

import sys

from capva import pvget
from capva.exceptions import EPICSConnectionError, EPICSGetError, EPICSTimeoutError

PV_NAME = "pva://calcExample"

try:
    data = pvget(PV_NAME)
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)

print(data.to_json(mode="full", indent=2))
