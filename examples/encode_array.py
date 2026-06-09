"""Read wfExample, encode numeric array for Web payload, write pvdata.json.

Backend flow: pvget -> PVData.to_dict(..., base64_encode=True) -> JSON payload.
Run decode_array.js next to decode the array on the client (Node.js).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from capva import pvget
from capva.exceptions import EPICSConnectionError, EPICSGetError, EPICSTimeoutError

PV_NAME = "pva://wfExample"
OUT = Path(__file__).resolve().parent / "pvdata.json"


def main() -> None:
    try:
        data = pvget(PV_NAME)
    except (EPICSConnectionError, EPICSTimeoutError, EPICSGetError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    payload = data.to_dict(mode="full", base64_encode=True)
    if "b64arr" not in payload:
        print(
            "error: PV has no encodable numeric array (need a waveform PV)",
            file=sys.stderr,
        )
        sys.exit(1)

    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"pvName: {payload.get('pvName')}")
    print(f"b64dtype: {payload.get('b64dtype')}")
    print("value omitted from payload; run: node examples/decode_array.js")


if __name__ == "__main__":
    main()
