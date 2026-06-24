"""PV class: raw monitor with deferred parsing (queue now, parse later)."""

import sys
import time

from capva import (
    PV,
    RawMonitorEvent,
    parse_raw_monitor_to_metadata_dict,
    parse_raw_monitor_to_update_dict,
)
from capva.exceptions import EPICSConnectionError, EPICSGetError, EPICSTimeoutError

PV_NAME = "pva://calcExample"
MONITOR_SECONDS = 30

events: list[RawMonitorEvent] = []


def on_raw(event: RawMonitorEvent) -> None:
    events.append(event)
    if event.disconnected:
        print(f"  [raw] queued #{len(events)} disconnected (not parsed)")
    else:
        print(f"  [raw] queued #{len(events)} update (not parsed)")


pv = PV(PV_NAME)
handle = None
try:
    handle = pv.monitor_raw(on_raw)
    print(f"Monitoring {PV_NAME!r} (raw) for {MONITOR_SECONDS}s ...")
    time.sleep(MONITOR_SECONDS)
except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    if handle is not None:
        pv.clear_monitor(handle)
    pv.close()

print(f"\nOffline parse of {len(events)} queued event(s):")
metadata_printed = False
for i, event in enumerate(events, 1):
    update = parse_raw_monitor_to_update_dict(event)
    if event.disconnected:
        alarm = update.get("alarm") or {}
        print(f"  #{i} disconnected alarm={alarm.get('message')!r}")
        continue
    print(f"  #{i} value={update.get('value')!r}")
    if not metadata_printed:
        meta = parse_raw_monitor_to_metadata_dict(event)
        if meta:
            display = meta.get("display") or {}
            print(f"       metadata display keys={list(display.keys())}")
            metadata_printed = True

print("Done.")
