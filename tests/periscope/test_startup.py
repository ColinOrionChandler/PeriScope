"""Exercise the installed CLI, Horizons conversion, and Dash construction offline."""

from unittest.mock import Mock

import pytest
from astropy.table import Table
from dash import Dash

from periscope import ephemeris
from periscope.cli import main


@pytest.mark.parametrize("objects", [None, "target_lists/MBC.lst", "target_lists/NEMBC.lst", "custom.lst"])
def test_cli_starts_app_with_mock_horizons(monkeypatch, tmp_path, objects):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "custom.lst").write_text("Ceres\n", encoding="utf-8")
    response = Table(
        {
            "datetime_str": ["2026-Jan-01 20:00", "2026-Jan-01 20:15"],
            "EL": [40.0, 42.0],
            "RA": [100.0, 100.1],
            "DEC": [20.0, 20.1],
            "V": [18.0, 18.1],
            "true_anom": [30.0, 30.1],
        }
    )
    horizons = Mock()
    horizons.return_value.ephemerides.return_value = response
    monkeypatch.setattr(ephemeris, "Horizons", horizons)
    started = []

    def fake_run(app, **kwargs):
        started.append(kwargs)
        client = app.server.test_client()
        assert client.get("/").status_code == 200
        layout = client.get("/_dash-layout")
        assert layout.status_code == 200
        assert "planet-graph" in layout.get_data(as_text=True)
        assert "radec-graph" in layout.get_data(as_text=True)
        assert len(app.callback_map) == 3

    monkeypatch.setattr(Dash, "run", fake_run)
    args = ["--date", "2026-01-01", "--port", "8051"]
    if objects:
        args += ["--objects", objects]
    assert main(args) == 0
    assert started == [{"host": "127.0.0.1", "port": 8051, "debug": False}]
    assert horizons.call_count > 0
    assert horizons.call_args.kwargs["location"] == "705"
    assert horizons.call_args.kwargs["epochs"]["step"] == "15m"
