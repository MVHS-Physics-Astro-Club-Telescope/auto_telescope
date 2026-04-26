"""Sky and weather conditions providers.

We aggregate three free public providers and reconcile them into a single
``ConditionsForecast`` per hour:

* 7Timer! ASTRO: dedicated astronomy forecast (cloud cover, seeing, transparency)
* NOAA NWS:      authoritative US weather (cloud cover, wind, temp, precip)
* Open-Meteo:    high-resolution backup (cloud cover, visibility, wind)

The aggregator tolerates any one provider being down; if all three are down,
``aggregator.fetch`` raises ``AllProvidersDownError`` so the safety layer can
refuse to slew rather than silently observing in unknown conditions.
"""

from auto_telescope.conditions.aggregator import (
    AllProvidersDownError,
    ConditionsAggregator,
    fetch_current_conditions,
    fetch_forecast,
)
from auto_telescope.conditions.cache import ConditionsCache
from auto_telescope.conditions.nws import NWSProvider
from auto_telescope.conditions.open_meteo import OpenMeteoProvider
from auto_telescope.conditions.seven_timer import SevenTimerProvider

__all__ = [
    "AllProvidersDownError",
    "ConditionsAggregator",
    "ConditionsCache",
    "NWSProvider",
    "OpenMeteoProvider",
    "SevenTimerProvider",
    "fetch_current_conditions",
    "fetch_forecast",
]
