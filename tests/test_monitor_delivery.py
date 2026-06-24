"""Tests for monitor delivery modes (mocked providers)."""

from unittest.mock import MagicMock, patch

import pytest

from capva.monitor_raw import RawMonitorEvent
from capva.protocol import CA
from capva.pv_data import PVData
from capva.providers.ca_pv import CAPV


@pytest.fixture
def mock_epics_pv():
    pv = MagicMock()
    pv.connected = True
    pv.connection_callbacks = []
    pv.add_callback = MagicMock(return_value=7)
    pv.remove_callback = MagicMock()
    return pv


def test_ca_monitor_parses_before_callback(mock_epics_pv):
    callback = MagicMock()
    with patch("capva.providers.ca_pv.epics.PV", return_value=mock_epics_pv):
        capv = CAPV("TEST:PV")
        capv.monitor(callback)

    wrapped = mock_epics_pv.add_callback.call_args.args[0]
    with patch(
        "capva.providers.ca_pv.parse_ca_update",
        wraps=__import__(
            "capva.pv_parser", fromlist=["parse_ca_update"]
        ).parse_ca_update,
    ) as parse_mock:
        wrapped(value=1.0, severity=0, status=0, timestamp=1.0)
    callback.assert_called_once()
    assert isinstance(callback.call_args.args[0], PVData)
    parse_mock.assert_called_once()


def test_ca_monitor_raw_skips_parse(mock_epics_pv):
    callback = MagicMock()
    with patch("capva.providers.ca_pv.epics.PV", return_value=mock_epics_pv):
        capv = CAPV("TEST:PV")
        capv.monitor_raw(callback)

    wrapped = mock_epics_pv.add_callback.call_args.args[0]
    with patch("capva.providers.ca_pv.parse_ca_update") as parse_mock:
        wrapped(value=2.0, severity=0, status=0, timestamp=1.0)
    parse_mock.assert_not_called()
    event = callback.call_args.args[0]
    assert isinstance(event, RawMonitorEvent)
    assert event.protocol == CA
    assert event.payload["value"] == 2.0


def test_ca_monitor_raw_disconnect(mock_epics_pv):
    callback = MagicMock()
    mock_epics_pv.connected = False
    with patch("capva.providers.ca_pv.epics.PV", return_value=mock_epics_pv):
        capv = CAPV("TEST:PV")
        capv.monitor_raw(callback)

    event = callback.call_args.args[0]
    assert event.disconnected is True


def test_ca_monitor_disconnect(mock_epics_pv):
    callback = MagicMock()
    mock_epics_pv.connected = False
    with patch("capva.providers.ca_pv.epics.PV", return_value=mock_epics_pv):
        capv = CAPV("TEST:PV")
        capv.monitor(callback)

    data = callback.call_args.args[0]
    assert isinstance(data, PVData)
    assert data.is_disconnected()
