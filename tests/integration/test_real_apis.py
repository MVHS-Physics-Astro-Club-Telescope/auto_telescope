"""Integration tests against the real APIs, recorded with vcrpy.

To re-record cassettes, delete the corresponding YAML in cassettes/ and run pytest
with internet connectivity. Cassettes are committed so CI can replay them.
"""

from __future__ import annotations

import pytest

from auto_telescope.conditions.aggregator import ConditionsAggregator
from auto_telescope.conditions.nws import NWSProvider
from auto_telescope.conditions.open_meteo import OpenMeteoProvider
from auto_telescope.conditions.seven_timer import SevenTimerProvider

pytestmark = pytest.mark.integration


@pytest.mark.vcr()
def test_seven_timer_real_call() -> None:
    provider = SevenTimerProvider(timeout_seconds=15.0)
    slots = provider.fetch(latitude=37.366, longitude=-122.077)
    assert len(slots) > 5
    s = slots[0]
    assert 0.0 <= s.cloud_cover_pct <= 100.0
    assert 0.4 <= s.seeing_arcsec <= 5.0


@pytest.mark.vcr()
def test_nws_real_call() -> None:
    provider = NWSProvider(timeout_seconds=15.0)
    slots = provider.fetch(latitude=37.366, longitude=-122.077)
    assert len(slots) > 12
    s = slots[0]
    assert -50.0 < s.temperature_c < 60.0


@pytest.mark.vcr()
def test_open_meteo_real_call() -> None:
    provider = OpenMeteoProvider(timeout_seconds=15.0)
    slots = provider.fetch(latitude=37.366, longitude=-122.077)
    assert len(slots) > 12


@pytest.mark.vcr()
def test_aggregator_real_call() -> None:
    agg = ConditionsAggregator()
    forecasts = agg.fetch(latitude=37.366, longitude=-122.077)
    assert len(forecasts) > 0
    # At least one forecast should have multiple providers.
    multi = [f for f in forecasts if len(f.contributing_providers) >= 2]
    assert len(multi) > 0
