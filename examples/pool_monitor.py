"""PVPool: monitor on a pooled PV, clear handle, then release."""

import sys
import time

from capva import PVData, PVPool
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


pv = PVPool.getPV(PV_NAME)
handle = None
try:
    handle = pv.monitor(on_update)
    print(f"Monitoring {PV_NAME!r} for {MONITOR_SECONDS}s ...")
    time.sleep(MONITOR_SECONDS)
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    if handle is not None:
        pv.clear_monitor(handle)
    PVPool.releasePV(pv)

print(f"Done. {len(events)} callback(s).")
