"""Numeric array base64 encoding for PV value."""

from __future__ import annotations

import base64
from typing import Any, List, Optional, Union

import numpy as np


def _numeric_array_to_base64(array: Union[List, np.ndarray], dtype: str) -> str:
    arr = np.asarray(array, dtype=dtype)
    if arr.dtype.byteorder not in ("<", "="):
        arr = arr.astype("<" + arr.dtype.str[1:])
    return base64.b64encode(arr.tobytes()).decode("ascii")


def encode_array(arr: Any) -> tuple[Optional[str], Optional[str]]:
    """Returns (b64arr, b64dtype) for numeric arrays."""
    if arr is None:
        return None, None

    arr = np.asarray(arr)
    if arr.size == 0:
        return None, None

    if np.issubdtype(arr.dtype, np.floating):
        return _numeric_array_to_base64(arr, "float64"), "float64"

    if np.issubdtype(arr.dtype, np.integer):
        min_val, max_val = arr.min(), arr.max()
        if -128 <= min_val <= max_val <= 127:
            dtype = "int8"
        elif -32768 <= min_val <= max_val <= 32767:
            dtype = "int16"
        elif -2147483648 <= min_val <= max_val <= 2147483647:
            dtype = "int32"
        else:
            dtype = "int64"
        return _numeric_array_to_base64(arr, dtype), dtype

    return None, None
