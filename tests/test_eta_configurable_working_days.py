from datetime import datetime, timezone

from phoenix_production_module.production.integration import (
    _configured_working_day_eta,
)


def test_configured_working_day_eta_excludes_weekends():
    start = datetime(
        2026,
        1,
        2,
        9,
        0,
        tzinfo=timezone.utc,
    )

    configuration = {
        "lead_time_working_days": 1,
        "calendar": {
            "exclude_weekends": True,
            "exclude_public_holidays": False,
            "public_holidays": [],
        },
    }

    result = _configured_working_day_eta(
        start,
        configuration=configuration,
    )

    assert result == datetime(
        2026,
        1,
        5,
        9,
        0,
        tzinfo=timezone.utc,
    )


def test_configured_working_day_eta_excludes_public_holiday():
    start = datetime(
        2026,
        1,
        1,
        9,
        0,
        tzinfo=timezone.utc,
    )

    configuration = {
        "lead_time_working_days": 1,
        "calendar": {
            "exclude_weekends": True,
            "exclude_public_holidays": True,
            "public_holidays": ["2026-01-02"],
        },
    }

    result = _configured_working_day_eta(
        start,
        configuration=configuration,
    )

    assert result == datetime(
        2026,
        1,
        5,
        9,
        0,
        tzinfo=timezone.utc,
    )


def test_configured_working_day_eta_counts_only_working_days():
    start = datetime(
        2026,
        1,
        5,
        9,
        0,
        tzinfo=timezone.utc,
    )

    configuration = {
        "lead_time_working_days": 5,
        "calendar": {
            "exclude_weekends": True,
            "exclude_public_holidays": False,
            "public_holidays": [],
        },
    }

    result = _configured_working_day_eta(
        start,
        configuration=configuration,
    )

    assert result == datetime(
        2026,
        1,
        12,
        9,
        0,
        tzinfo=timezone.utc,
    )


def test_zero_working_day_lead_time_preserves_timestamp():
    start = datetime(
        2026,
        1,
        5,
        9,
        30,
        tzinfo=timezone.utc,
    )

    configuration = {
        "lead_time_working_days": 0,
        "calendar": {
            "exclude_weekends": True,
            "exclude_public_holidays": True,
            "public_holidays": [],
        },
    }

    result = _configured_working_day_eta(
        start,
        configuration=configuration,
    )

    assert result == start


def test_eta_preserves_time_of_day():
    start = datetime(
        2026,
        1,
        5,
        14,
        37,
        22,
        tzinfo=timezone.utc,
    )

    configuration = {
        "lead_time_working_days": 2,
        "calendar": {
            "exclude_weekends": True,
            "exclude_public_holidays": False,
            "public_holidays": [],
        },
    }

    result = _configured_working_day_eta(
        start,
        configuration=configuration,
    )

    assert result == datetime(
        2026,
        1,
        7,
        14,
        37,
        22,
        tzinfo=timezone.utc,
    )


def test_eta_does_not_mutate_start_timestamp():
    start = datetime(
        2026,
        1,
        5,
        9,
        0,
        tzinfo=timezone.utc,
    )

    configuration = {
        "lead_time_working_days": 3,
        "calendar": {
            "exclude_weekends": True,
            "exclude_public_holidays": False,
            "public_holidays": [],
        },
    }

    _configured_working_day_eta(
        start,
        configuration=configuration,
    )

    assert start == datetime(
        2026,
        1,
        5,
        9,
        0,
        tzinfo=timezone.utc,
    )
