# Changelog

## 0.1.1

- Integer arrays beyond int32 encode as `b64dtype: int64`.
- `PVData.is_array()` — array values are Python `lists` after parsing.
- `to_dict(base64_encode=True)` only encodes when `value` is a `list`.
- README and `decode_array.js` updated for `int64`.

## 0.1.0

- Initial release: CA/PVA client, `PVData`, optional numeric array base64 (`float64`, `int8`, `int16`, `int32`).
