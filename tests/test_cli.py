from pathlib import Path

import pytest

from periscope.cli import build_parser, parse_observing_date, resolve_target_list
from periscope.targets import (
    DEFAULT_TARGET_LIST,
    INCLUDED_TARGET_LISTS,
    load_target_names,
)


def test_parser_defaults_to_sample_target_list():
    args = build_parser().parse_args([])

    assert args.objects == str(DEFAULT_TARGET_LIST)
    assert args.site == "705"
    assert args.port == 8050


def test_parse_observing_date_accepts_iso_date():
    assert parse_observing_date("2026-01-01") == "2026-01-01"


def test_parse_observing_date_rejects_bad_date():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_observing_date("01/01/2026")


def test_resolve_target_list_falls_back_to_source_tree_sample():
    path = resolve_target_list(DEFAULT_TARGET_LIST)

    assert path.name == "aa_year1_paper.lst"
    assert path.is_file()


def test_included_target_lists_are_resolvable_and_non_empty():
    for target_list in INCLUDED_TARGET_LISTS:
        path = resolve_target_list(target_list)

        assert path.is_file()
        assert load_target_names(path)


def test_load_target_names_strips_blank_lines(tmp_path: Path):
    target_file = tmp_path / "targets.lst"
    target_file.write_text("\nCeres\n  Pallas  \n\n", encoding="utf-8")

    assert load_target_names(target_file) == ["Ceres", "Pallas"]
