"""Tests for encode_array (no EPICS IOC required)."""

import base64

import numpy as np
import pytest

from capva.array_b64 import encode_array


def _decode_round_trip(b64: str, dtype: str, count: int) -> np.ndarray:
    np_dtype = np.dtype(dtype)
    raw = base64.b64decode(b64)
    return np.frombuffer(raw, dtype=np_dtype, count=count)


def test_encode_int32_range():
    arr = np.array([100000, 200000, 300000], dtype=np.int32)
    b64, dtype = encode_array(arr)
    assert b64 is not None
    assert dtype == "int32"
    decoded = _decode_round_trip(b64, dtype, arr.size)
    assert np.array_equal(decoded, arr)


def test_encode_int32_upper_bound():
    arr = np.array([2**31 - 1], dtype=np.int64)
    b64, dtype = encode_array(arr)
    assert dtype == "int32"
    decoded = _decode_round_trip(b64, dtype, arr.size)
    assert decoded[0] == 2**31 - 1


def test_encode_int64_above_int32():
    arr = np.array([2**31, 2**31 + 1], dtype=np.int64)
    b64, dtype = encode_array(arr)
    assert dtype == "int64"
    decoded = _decode_round_trip(b64, dtype, arr.size)
    assert np.array_equal(decoded, arr)


def test_encode_int32_lower_bound():
    arr = np.array([-2**31], dtype=np.int64)
    b64, dtype = encode_array(arr)
    assert dtype == "int32"
    decoded = _decode_round_trip(b64, dtype, arr.size)
    assert decoded[0] == -2**31


def test_encode_int64_below_int32():
    arr = np.array([-2**31 - 1], dtype=np.int64)
    b64, dtype = encode_array(arr)
    assert dtype == "int64"
    decoded = _decode_round_trip(b64, dtype, arr.size)
    assert decoded[0] == -2**31 - 1


def test_encode_int64_large_value():
    arr = np.array([2**40], dtype=np.int64)
    b64, dtype = encode_array(arr)
    assert dtype == "int64"
    decoded = _decode_round_trip(b64, dtype, arr.size)
    assert decoded[0] == 2**40


def test_encode_int8_int16_branches():
    arr8 = np.array([-1, 0, 127], dtype=np.int32)
    b64, dtype = encode_array(arr8)
    assert dtype == "int8"
    assert np.array_equal(_decode_round_trip(b64, dtype, arr8.size), arr8)

    arr16 = np.array([1000, -2000], dtype=np.int32)
    b64, dtype = encode_array(arr16)
    assert dtype == "int16"
    assert np.array_equal(_decode_round_trip(b64, dtype, arr16.size), arr16)


def test_encode_float64():
    arr = np.array([1.5, 2.5], dtype=np.float64)
    b64, dtype = encode_array(arr)
    assert dtype == "float64"
    decoded = _decode_round_trip(b64, dtype, arr.size)
    assert np.array_equal(decoded, arr)


def test_encode_empty_returns_none():
    b64, dtype = encode_array(np.array([], dtype=np.int32))
    assert b64 is None
    assert dtype is None
