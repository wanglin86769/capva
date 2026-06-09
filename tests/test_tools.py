"""Tests for procedural tools API (no EPICS IOC required)."""

from unittest.mock import MagicMock, patch

import pytest

from capva.constants import DEFAULT_IO_TIMEOUT
from capva.pv_data import PVData, Alarm
from capva.tools import MonitorSession, pvget, pvinfo, pvmonitor, pvput


@pytest.fixture
def mock_pv():
    pvs: list = []

    def make_pv(pvname):
        pv = MagicMock(name=f"PV({pvname})")
        pv.get.return_value = PVData(
            pvName=pvname,
            value=1.0,
            alarm=Alarm(),
            display=None,
        )
        pv.put = MagicMock()
        pv.info = MagicMock(
            return_value={
                "pvName": pvname,
                "protocol": "ca",
                "state": "CONNECTED",
                "host": "ioc:5064",
                "type": "native_double",
                "display": {"units": "mm"},
            }
        )
        handle = MagicMock(name="handle")
        pv.monitor = MagicMock(return_value=handle)
        pv.clear_monitor = MagicMock()
        pv.close = MagicMock()
        pvs.append(pv)
        return pv

    with patch("capva.tools.PV", side_effect=make_pv):
        yield pvs


def test_pvget_returns_pvdata(mock_pv):
    data = pvget("motor:x")
    assert isinstance(data, PVData)
    assert data.value == 1.0
    assert mock_pv[0].get.called
    mock_pv[0].close.assert_called_once()


def test_pvget_to_dict_full(mock_pv):
    mock_pv
    data = pvget("motor:x").to_dict(mode="full")
    assert data["value"] == 1.0
    assert "pvName" in data


def test_pvput(mock_pv):
    pvput("motor:x", 2.5, wait=True)
    mock_pv[0].put.assert_called_once_with(2.5, timeout=DEFAULT_IO_TIMEOUT, wait=True)
    mock_pv[0].close.assert_called_once()


def test_pvinfo(mock_pv):
    info = pvinfo("motor:x")
    assert info["pvName"] == "motor:x"
    assert info["protocol"] == "ca"
    assert info["host"] == "ioc:5064"
    assert info["type"] == "native_double"
    assert info["display"] == {"units": "mm"}
    mock_pv[0].info.assert_called_once_with(timeout=DEFAULT_IO_TIMEOUT)
    mock_pv[0].close.assert_called_once()


def test_pvmonitor_session_close(mock_pv):
    cb = MagicMock()
    session = pvmonitor("motor:x", cb)
    assert isinstance(session, MonitorSession)
    mock_pv[0].monitor.assert_called_once_with(cb)
    mock_pv[0].close.assert_not_called()

    session.close()
    mock_pv[0].clear_monitor.assert_called_once_with(mock_pv[0].monitor.return_value)
    mock_pv[0].close.assert_called_once()

    session.close()
    mock_pv[0].clear_monitor.assert_called_once()
    mock_pv[0].close.assert_called_once()


def test_pvmonitor_separate_sessions(mock_pv):
    pvmonitor("motor:x", MagicMock())
    pvmonitor("motor:x", MagicMock())
    assert len(mock_pv) == 2
