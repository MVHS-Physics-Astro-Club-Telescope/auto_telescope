"""Shared pytest fixtures for auto_telescope tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from auto_telescope.config.site import MVHS_SITE, Site


@pytest.fixture()
def mvhs_site() -> Site:
    """The default MVHS observing site."""
    return MVHS_SITE


@pytest.fixture()
def utc_now() -> datetime:
    """Frozen 'now' for deterministic time-based tests."""
    return datetime(2026, 7, 4, 5, 30, tzinfo=UTC)  # 10:30 PM PDT, July 4 2026


@pytest.fixture(scope="module")
def vcr_cassette_dir(request: pytest.FixtureRequest) -> str:
    """Place vcrpy cassettes in tests/integration/cassettes/<test_module>/."""
    return str(
        Path(__file__).parent / "integration" / "cassettes" / request.module.__name__.split(".")[-1]
    )


@pytest.fixture(scope="module")
def vcr_config() -> dict:
    """Default vcrpy config — match by method + URI but ignore the User-Agent."""
    return {
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "filter_headers": ["User-Agent", "Authorization", "Cookie"],
        "decode_compressed_response": True,
    }
