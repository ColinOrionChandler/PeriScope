"""Command-line entry point for PeriScope."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Sequence

from .sites import DEFAULT_SITE_CODE, SITE_TIMEZONES, get_site_timezone
from .targets import DEFAULT_TARGET_LIST, load_target_names


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser without importing heavy Dash dependencies."""
    parser = argparse.ArgumentParser(
        prog="periscope",
        description="Run the PeriScope minor-planet observation-planning app.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--objects",
        default=str(DEFAULT_TARGET_LIST),
        help="Path to a text file with one target name per non-empty line.",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Local observing date in YYYY-MM-DD format at the selected site.",
    )
    parser.add_argument(
        "--site",
        default=DEFAULT_SITE_CODE,
        choices=sorted(SITE_TIMEZONES),
        help="JPL Horizons observatory code.",
    )
    parser.add_argument(
        "--step",
        default="15m",
        help="Horizons ephemeris step size.",
    )
    parser.add_argument(
        "--min-elevation",
        type=float,
        default=10.0,
        help="Minimum elevation in degrees, converted to a Horizons airmass limit.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Dash server host.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Dash server port.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run Dash with debug mode enabled.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional title label for the elevation plot.",
    )
    return parser


def parse_observing_date(date_string: str | None) -> str | None:
    """Validate and normalize an optional ISO local observing date."""
    if date_string is None:
        return None

    try:
        return dt.date.fromisoformat(date_string).isoformat()
    except ValueError as exc:
        raise ValueError(
            "--date must use YYYY-MM-DD format, for example 2026-01-01"
        ) from exc


def resolve_target_list(path: str | Path) -> Path:
    """Resolve a target list path from the CWD, source tree, or install prefix."""
    candidate = Path(path).expanduser()
    if candidate.is_file():
        return candidate

    if not candidate.is_absolute():
        # Editable installs and source-tree invocations should find the bundled
        # sample list without requiring users to type an absolute path.
        source_tree_candidate = Path(__file__).resolve().parents[1] / candidate
        if source_tree_candidate.is_file():
            return source_tree_candidate

        # Non-editable installs place data files under the environment prefix.
        installed_data_candidate = Path(sys.prefix) / candidate
        if installed_data_candidate.is_file():
            return installed_data_candidate

    return candidate


def _title_date(date_string: str | None, site_code: str) -> str:
    """Return the date label shown in the plot title."""
    if date_string is not None:
        return date_string
    return dt.datetime.now(get_site_timezone(site_code)).date().isoformat()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line application."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        local_date = parse_observing_date(args.date)
    except ValueError as exc:
        parser.error(str(exc))

    target_list = resolve_target_list(args.objects)
    try:
        targets = load_target_names(target_list)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    # These imports are intentionally delayed so `periscope --help` works before
    # the scientific/Dash stack is imported.
    from .app import create_app
    from .ephemeris import fetch_minor_planet_data_local_noon

    title_label = args.title or target_list.name
    title_local_date = _title_date(local_date, args.site)
    data_df = fetch_minor_planet_data_local_noon(
        local_date_str=local_date,
        site_code=args.site,
        objects=targets,
        step=args.step,
        skip_daylight=True,
        min_elevation=args.min_elevation,
    )
    app = create_app(
        data_df,
        site_code=args.site,
        title_label=title_label,
        title_local_date=title_local_date,
    )

    print(f"Starting PeriScope at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0
