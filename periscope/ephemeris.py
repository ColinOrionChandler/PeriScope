"""Horizons querying and ephemeris table preparation."""

from __future__ import annotations

import datetime as dt
import re
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from astroquery.jplhorizons import Horizons
from requests.exceptions import ConnectionError, SSLError, Timeout

from .sites import DEFAULT_SITE_CODE, get_site_timezone
from .targets import load_target_names

EPHEMERIS_COLUMNS = [
    "datetime_utc",
    "EL",
    "RA",
    "DEC",
    "V",
    "true_anom",
    "target",
    "object_index",
    "mean_v",
    "mean_ta",
]
AMBIGUOUS_TARGET_PREFIX = "Ambiguous target name"


def empty_ephemeris_frame() -> pd.DataFrame:
    """Return an empty frame with the columns expected by the Dash app."""
    return pd.DataFrame(columns=EPHEMERIS_COLUMNS)


def unmask_column(column) -> np.ndarray:
    """Return a NumPy array, converting Astropy masked values to ``NaN``.

    Horizons tables can contain Astropy ``MaskedColumn`` values. Pandas can carry
    those masked objects into internal blocks, which later causes surprising copy
    and plotting failures. Converting at the boundary keeps the rest of the app
    on ordinary pandas/numpy data.
    """
    if hasattr(column, "filled"):
        if hasattr(column, "dtype") and np.issubdtype(column.dtype, np.integer):
            column = column.astype(float)
        return np.asarray(column.filled(np.nan))

    return np.asarray(column)


def get_magnitude_column(ephem) -> np.ndarray:
    """Pick the best available visual magnitude-like column from Horizons."""
    for column_name in ("V", "Tmag", "Nmag"):
        if column_name in ephem.colnames:
            return unmask_column(ephem[column_name])
    return np.full(len(ephem), np.nan)


def resolve_targets(objects: Iterable[str] | str | Path | None) -> list[str]:
    """Normalize target input to a non-empty list of object names."""
    if objects is None:
        targets = ["Ceres", "Pallas", "Vesta"]
    elif isinstance(objects, (str, Path)):
        object_path = Path(objects).expanduser()
        if object_path.is_file():
            targets = load_target_names(object_path)
        else:
            targets = [str(objects)]
    else:
        targets = [str(target).strip() for target in objects if str(target).strip()]

    if not targets:
        raise ValueError("No target names were provided.")
    return targets


def _normalize_designation(value: str) -> str:
    """Return a whitespace-normalized designation for Horizons table matching."""
    return " ".join(value.upper().split())


def _latest_ambiguous_record_id(target: str, error_message: str) -> str | None:
    """Extract the newest matching Horizons record id from an ambiguity table."""
    if AMBIGUOUS_TARGET_PREFIX not in error_message:
        return None

    normalized_target = _normalize_designation(target)
    candidates: list[tuple[int, int, str]] = []
    for line in error_message.splitlines():
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) < 4 or not parts[0].isdigit() or not parts[1].isdigit():
            continue

        record_id = parts[0]
        epoch_year = int(parts[1])
        match_designation = _normalize_designation(parts[2])
        primary_designation = _normalize_designation(parts[3])
        if normalized_target in {match_designation, primary_designation}:
            candidates.append((epoch_year, int(record_id), record_id))

    if not candidates:
        return None

    return max(candidates)[2]


def _local_noon_window(
    local_date_str: str | None,
    site_code: str,
) -> tuple[str, str, str]:
    """Return Horizons UTC start/stop strings for local noon to local noon."""
    local_tz = get_site_timezone(site_code)
    if local_date_str is None:
        local_date = dt.datetime.now(local_tz).date()
    else:
        local_date = dt.date.fromisoformat(local_date_str)

    # A noon-to-noon window centers the observing night while keeping the user's
    # command date in the observatory's local calendar.
    local_noon_start = dt.datetime.combine(
        local_date,
        dt.time(12, 0),
        tzinfo=local_tz,
    )
    local_noon_end = local_noon_start + dt.timedelta(days=1)
    start_utc = local_noon_start.astimezone(dt.timezone.utc)
    end_utc = local_noon_end.astimezone(dt.timezone.utc)
    return (
        start_utc.strftime("%Y-%m-%d %H:%M"),
        end_utc.strftime("%Y-%m-%d %H:%M"),
        local_date.isoformat(),
    )


def _airmass_limit_for_elevation(min_elevation: float) -> float | None:
    """Convert an elevation cutoff to the airmass limit accepted by Horizons."""
    if min_elevation <= 0.0:
        return None

    elevation_radians = np.radians(min_elevation)
    if elevation_radians <= 0:
        return None
    return float(1.0 / np.sin(elevation_radians))


def _nanmean(series: pd.Series) -> float:
    """Return ``NaN`` instead of warning when every value is missing."""
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float, copy=False)
    if np.isnan(values).all():
        return float("nan")
    return float(np.nanmean(values))


def fetch_minor_planet_data_local_noon(
    local_date_str: str | None = None,
    site_code: str = DEFAULT_SITE_CODE,
    objects: Iterable[str] | str | Path | None = None,
    step: str = "15m",
    skip_daylight: bool = True,
    min_elevation: float = 10.0,
    max_tries: int = 5,
    pause_seconds: float = 5.0,
) -> pd.DataFrame:
    """Query Horizons ephemerides and return plotting-ready pandas rows.

    The query window runs from local noon on ``local_date_str`` to local noon the
    next day at ``site_code``. Each target is queried independently so that one
    bad or ambiguous object name does not prevent the remaining list from being
    plotted.
    """
    start_str, end_str, _ = _local_noon_window(local_date_str, site_code)
    targets = resolve_targets(objects)
    airmass_lessthan = _airmass_limit_for_elevation(min_elevation)

    print(
        f"Loaded {len(targets)} targets, starting with {targets[0]} "
        f"and ending with {targets[-1]}."
    )

    all_rows: list[pd.DataFrame] = []
    for object_index, target in enumerate(targets, start=1):
        print(f"Checking ephemeris for {object_index}/{len(targets)}: {target}...")
        horizons_id = target
        retried_ambiguity = False
        unrecoverable_error = False
        ephem = None

        # Target lists often contain objects that are not visible for the chosen
        # night or are ambiguous in Horizons. Keep processing the rest of the
        # list so one miss does not make the whole planning session fail.
        for attempt in range(1, max_tries + 1):
            horizons_obj = Horizons(
                id=horizons_id,
                location=site_code,
                epochs={"start": start_str, "stop": end_str, "step": step},
            )
            try:
                ephem = horizons_obj.ephemerides(
                    skip_daylight=skip_daylight,
                    airmass_lessthan=airmass_lessthan,
                )
                break
            except (SSLError, ConnectionError, Timeout) as exc:
                print(
                    f"Horizons network error for {target} "
                    f"(attempt {attempt}/{max_tries}): {exc}"
                )
                if attempt < max_tries:
                    print(f"Retrying in {pause_seconds:g} seconds...")
                    time.sleep(pause_seconds)
            except ValueError as exc:
                record_id = _latest_ambiguous_record_id(target, str(exc))
                if record_id is not None and not retried_ambiguity:
                    print(
                        f"{target} is ambiguous in Horizons; retrying with "
                        f"latest matching record {record_id}."
                    )
                    horizons_id = record_id
                    retried_ambiguity = True
                    continue
                print(f"Skipping {target} due to Horizons error: {exc}")
                unrecoverable_error = True
                break

        if ephem is None:
            if not unrecoverable_error:
                print(f"Giving up on {target} after {max_tries} attempts.")
            continue

        if len(ephem) == 0:
            print(f"Skipping {target}: 0 rows for {start_str} to {end_str}.")
            continue

        datetime_strings = np.asarray(ephem["datetime_str"]).astype(str)
        df_temp = pd.DataFrame(
            {
                "datetime_utc": pd.to_datetime(datetime_strings, errors="coerce"),
                "EL": pd.to_numeric(unmask_column(ephem["EL"]), errors="coerce"),
                "RA": pd.to_numeric(unmask_column(ephem["RA"]), errors="coerce"),
                "DEC": pd.to_numeric(unmask_column(ephem["DEC"]), errors="coerce"),
                "target": [target] * len(ephem),
                "object_index": [object_index] * len(ephem),
            }
        )

        df_temp["V"] = pd.to_numeric(get_magnitude_column(ephem), errors="coerce")
        if "true_anom" in ephem.colnames:
            df_temp["true_anom"] = pd.to_numeric(
                unmask_column(ephem["true_anom"]),
                errors="coerce",
            )
        else:
            df_temp["true_anom"] = np.nan

        df_temp["object_index"] = df_temp["object_index"].astype(int)
        df_temp["mean_v"] = _nanmean(df_temp["V"])
        df_temp["mean_ta"] = _nanmean(df_temp["true_anom"])
        all_rows.append(df_temp[EPHEMERIS_COLUMNS])

    if not all_rows:
        return empty_ephemeris_frame()

    return pd.concat(all_rows, ignore_index=True)
