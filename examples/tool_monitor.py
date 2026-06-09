"""Procedural API: pvmonitor — subscribe, then close the session."""

import sys
import time

from capva import PVData, pvmonitor
from capva.exceptions import EPICSConnectionError, EPICSGetError, EPICSTimeoutError

PV_NAME = "pva://calcExample"
MONITOR_SECONDS = 30

events: list[str] = []


def on_update(data: PVData) -> None:
    if data.is_disconnected():
        events.append("disconnected")
        print("  [callback] disconnected")
    else:
        msg = f"value={data.value!r}"
        events.append(msg)
        print(f"  [callback] {msg}")


session = pvmonitor(PV_NAME, on_update)
try:
    print(f"Monitoring {PV_NAME!r} for {MONITOR_SECONDS}s ...")
    time.sleep(MONITOR_SECONDS)
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    session.close()

print(f"Done. {len(events)} callback(s).")
