"""Procedural API: pvinfo — read and print channel metadata."""

import json
import sys

from capva import pvinfo
from capva.exceptions import EPICSConnectionError, EPICSGetError, EPICSTimeoutError

PV_NAME = "pva://calcExample"

try:
    info = pvinfo(PV_NAME)
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)

print(json.dumps(info, indent=2))
