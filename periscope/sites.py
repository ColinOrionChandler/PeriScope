"""Observing-site metadata used by PeriScope."""

from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SITE_TIMEZONES = {
    "304": "America/Santiago",  # Las Campanas Observatory
    "705": "America/Denver",  # Apache Point Observatory
}

DEFAULT_SITE_CODE = "705"


def get_site_timezone(site_code: str) -> ZoneInfo:
    """Return the IANA timezone for a supported Horizons observatory code."""
    try:
        timezone_name = SITE_TIMEZONES[site_code]
    except KeyError as exc:
        supported = ", ".join(sorted(SITE_TIMEZONES))
        raise ValueError(
            f"Unsupported site code {site_code!r}. Supported codes: {supported}."
        ) from exc

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(
            f"Timezone data for {timezone_name!r} is not available. "
            "Install the tzdata package or use a Python with system timezone data."
        ) from exc
