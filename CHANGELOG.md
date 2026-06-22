# Changelog

## 0.1.2

- `PV.monitor()` / `pvmonitor()` — optional `include_metadata=True` to parse display, control, and valueAlarm from monitor events (no extra GET).
- `parse_ca_update` / `parse_pva_update` — optional `with_metadata` parameter; `parse_ca` / `parse_pva` unchanged.

## 0.1.1

- Integer arrays beyond int32 encode as `b64dtype: int64`.
- `PVData.is_array()` — array values are Python `lists` after parsing.
- `to_dict(base64_encode=True)` only encodes when `value` is a `list`.
- README and `decode_array.js` updated for `int64`.

## 0.1.0

- Initial release: CA/PVA client, `PVData`, optional numeric array base64 (`float64`, `int8`, `int16`, `int32`).
