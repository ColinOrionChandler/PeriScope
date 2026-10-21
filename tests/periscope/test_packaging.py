"""Installation contracts shared by editable and isolated wheel tests."""

import importlib.metadata
import subprocess
import sys
from pathlib import Path

import pytest

import periscope
from periscope.cli import main, resolve_target_list
from periscope.targets import INCLUDED_TARGET_LISTS, load_target_names


def test_version_matches_distribution():
    assert periscope.__version__ == importlib.metadata.version("periscope-planner")


def test_typed_marker_is_installed():
    assert Path(periscope.__file__).with_name("py.typed").is_file()


@pytest.mark.parametrize("target_list", INCLUDED_TARGET_LISTS)
def test_bundled_lists_resolve_outside_checkout(monkeypatch, tmp_path, target_list):
    monkeypatch.chdir(tmp_path)
    resolved = resolve_target_list(target_list)
    assert resolved.is_relative_to(Path(periscope.__file__).parent)
    assert load_target_names(resolved)


def test_local_list_overrides_bundled_alias(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    local = tmp_path / "target_lists" / "MBC.lst"
    local.parent.mkdir()
    local.write_text("Ceres\n", encoding="utf-8")
    assert load_target_names(resolve_target_list("target_lists/MBC.lst")) == ["Ceres"]
    assert resolve_target_list(local) == local


@pytest.mark.parametrize("path", ["missing.lst", "elsewhere/MBC.lst", "target_lists/missing.lst"])
def test_missing_custom_lists_do_not_fall_back(monkeypatch, tmp_path, capsys, path):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as error:
        main(["--objects", path])
    assert error.value.code == 2
    assert "Target list not found" in capsys.readouterr().err


def test_missing_absolute_list_does_not_fall_back(tmp_path):
    missing = tmp_path / "target_lists" / "MBC.lst"
    assert resolve_target_list(missing) == missing
    with pytest.raises(FileNotFoundError):
        load_target_names(resolve_target_list(missing))


def test_empty_custom_list_reports_error(tmp_path, capsys):
    empty = tmp_path / "empty.lst"
    empty.write_text("\n", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["--objects", str(empty)])
    assert error.value.code == 2
    assert "Target list is empty" in capsys.readouterr().err


@pytest.mark.parametrize("command", [["-m", "periscope"], ["-c", "from periscope.cli import main; main()"]])
def test_help_outside_checkout(tmp_path, command):
    result = subprocess.run(
        [sys.executable, *command, "--help"], cwd=tmp_path, capture_output=True, text=True, check=True
    )
    assert "--objects" in result.stdout
    assert "--date" in result.stdout


def test_help_does_not_import_scientific_stack(tmp_path):
    code = """
import sys
from periscope.cli import main
try:
    main(["--help"])
except SystemExit as exc:
    assert exc.code == 0
assert not {"dash", "numpy", "pandas", "astroquery"}.intersection(sys.modules)
"""
    subprocess.run([sys.executable, "-c", code], cwd=tmp_path, check=True, capture_output=True)
