"""PV class: info — read channel metadata, then close."""

import json
import sys

from capva import PV
from capva.exceptions import EPICSConnectionError, EPICSGetError, EPICSTimeoutError

PV_NAME = "pva://calcExample"

pv = PV(PV_NAME)
try:
    info = pv.info()
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    pv.close()

print(json.dumps(info, indent=2))
