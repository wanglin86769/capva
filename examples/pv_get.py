"""PV class: get — read current value, then close."""

import sys

from capva import PV
from capva.exceptions import EPICSConnectionError, EPICSGetError, EPICSTimeoutError

PV_NAME = "pva://calcExample"

pv = PV(PV_NAME)
try:
    data = pv.get()
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    pv.close()

print(data.to_json(mode="full", indent=2))
