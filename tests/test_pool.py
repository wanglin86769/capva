"""Tests for PVPool (no EPICS IOC required)."""

from unittest.mock import MagicMock, patch

import pytest

from capva.pool import PVPool
from capva.protocol import parse_protocol


@pytest.fixture(autouse=True)
def clear_pool():
    with PVPool._lock:
        PVPool._entries.clear()
    yield
    with PVPool._lock:
        for entry in PVPool._entries.values():
            entry.pv.close()
        PVPool._entries.clear()


@pytest.fixture
def mock_pv_class():
    instances: list = []

    def make_pv(pvname: str):
        protocol, clean_name = parse_protocol(pvname)
        pv = MagicMock(name=f"PV({pvname})")
        pv.protocol = protocol
        pv.pvname = clean_name
        pv.close = MagicMock()
        instances.append(pv)
        return pv

    with patch("capva.pool.PV", side_effect=make_pv):
        yield instances


def test_same_pv_different_input_forms_share_instance(mock_pv_class):
    pv1 = PVPool.getPV("calcExample")
    pv2 = PVPool.getPV("ca://calcExample")
    assert pv1 is pv2
    assert len(mock_pv_class) == 1


def test_ca_and_pva_are_separate_instances(mock_pv_class):
    ca_pv = PVPool.getPV("ca://x")
    pva_pv = PVPool.getPV("pva://x")
    assert ca_pv is not pva_pv
    assert len(mock_pv_class) == 2


def test_reference_count_across_input_forms(mock_pv_class):
    pv1 = PVPool.getPV("calcExample")
    pv2 = PVPool.getPV("ca://calcExample")
    assert pv1 is pv2
    assert PVPool.getReferenceCount("calcExample") == 2
    assert PVPool.getReferenceCount("ca://calcExample") == 2


def test_release_clears_entry_when_refs_reach_zero(mock_pv_class):
    pv1 = PVPool.getPV("pva://calcExample")
    pv2 = PVPool.getPV("pva://calcExample")
    assert PVPool.getReferenceCount("pva://calcExample") == 2

    PVPool.releasePV(pv1)
    assert PVPool.getReferenceCount("pva://calcExample") == 1
    mock_pv_class[0].close.assert_not_called()

    PVPool.releasePV(pv2)
    assert PVPool.getReferenceCount("pva://calcExample") == 0
    mock_pv_class[0].close.assert_called_once()


def test_get_pv_references_key_format(mock_pv_class):
    PVPool.getPV("pva://calcExample")
    refs = PVPool.getPVReferences()
    assert len(refs) == 1
    key, pv, count = refs[0]
    assert key == "pva://calcExample"
    assert count == 1


def test_key_round_trips_to_get_pv(mock_pv_class):
    pv1 = PVPool.getPV("pva://calcExample")
    key = PVPool.getPVReferences()[0][0]
    pv2 = PVPool.getPV(key)
    assert pv1 is pv2
    assert PVPool.getReferenceCount(key) == 2
