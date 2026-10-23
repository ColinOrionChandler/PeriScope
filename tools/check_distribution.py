"""Validate built artifacts and run the tests against isolated wheel installs.

Run after ``python -m build`` with ``python tools/check_distribution.py dist``.
The caller needs build and twine; temporary environments install runtime and test
requirements. Horizons and Dash server startup are mocked by the test suite.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str | Path, cwd: Path) -> None:
    """Execute a validation command and fail immediately on an error."""
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def check_wheel(wheel: Path) -> None:
    """Verify the wheel contains exact package data and its typing marker."""
    with zipfile.ZipFile(wheel) as archive:
        assert "periscope/py.typed" in archive.namelist()
        assert "periscope/_version.py" in archive.namelist()
        for source in (ROOT / "src/periscope/target_lists").glob("*.lst"):
            assert archive.read(f"periscope/target_lists/{source.name}") == source.read_bytes()


def main() -> None:
    """Check a wheel, rebuild its sdist without Git, and test both installations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist", type=Path)
    dist = parser.parse_args().dist.resolve()
    wheels, sdists = list(dist.glob("*.whl")), list(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        parser.error("Use a clean dist directory containing exactly one wheel and one sdist.")
    wheel, sdist = wheels[0], sdists[0]
    run(sys.executable, "-m", "twine", "check", "--strict", wheel, sdist, cwd=ROOT)
    check_wheel(wheel)

    with tempfile.TemporaryDirectory(prefix="periscope-package-check-") as directory:
        work = Path(directory)
        with tarfile.open(sdist) as archive:
            archive.extractall(work / "source", filter="data")
        source = next((work / "source").iterdir())
        assert not (source / ".git").exists()
        for original in (ROOT / "src/periscope/target_lists").glob("*.lst"):
            assert (
                source / "src/periscope/target_lists" / original.name
            ).read_bytes() == original.read_bytes()
        assert (source / "src/periscope/py.typed").is_file()
        run(sys.executable, "-m", "build", "--wheel", "--outdir", work / "rebuilt", cwd=source)
        rebuilt = next((work / "rebuilt").glob("*.whl"))
        assert rebuilt.name == wheel.name, "The sdist rebuild must preserve the wheel version."
        check_wheel(rebuilt)
        shutil.copytree(ROOT / "tests", work / "tests", ignore=shutil.ignore_patterns("__pycache__"))
        (work / "pytest.ini").write_text("[pytest]\naddopts = --import-mode=importlib\n", encoding="utf-8")
        venv.EnvBuilder(with_pip=True).create(work / "venv")
        bin_dir = work / "venv" / ("Scripts" if sys.platform == "win32" else "bin")
        python = bin_dir / "python"
        for artifact in (wheel, rebuilt):
            run(python, "-m", "pip", "install", "--force-reinstall", "--no-deps", artifact, cwd=work)
            run(python, "-m", "pip", "install", "periscope-planner[test]", cwd=work)
            run(bin_dir / "periscope", "--help", cwd=work)
            run(python, "-m", "periscope", "--help", cwd=work)
            run(python, "-m", "pytest", "-q", "tests", cwd=work)
    print("Wheel and Git-free sdist rebuild passed all packaging and CLI checks.")


if __name__ == "__main__":
    main()
