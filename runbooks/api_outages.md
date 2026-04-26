# Runbook: external API outages

This runbook covers what to do when one or more of the three weather providers
goes down. The system is designed to tolerate partial outages, but you may need
to know what's broken and how to verify it.

## Symptoms

* `find_best_windows()` returns results with `forecast=None` or with
  `contributing_providers` containing fewer than 3 names.
* The scheduler logs warnings like
  `provider 7timer failed: HTTPSConnectionPool(...)`.
* `safety.check_can_slew` refuses with code `no_forecast` repeatedly.

## Diagnosis (in order)

### 1. Confirm internet from the Pi

```bash
ping -c 3 8.8.8.8
ping -c 3 www.7timer.info
ping -c 3 api.weather.gov
ping -c 3 api.open-meteo.com
```

If any of these fail, fix the network first. The Pi's DHCP lease may have
lapsed; `sudo dhclient -r && sudo dhclient` usually resolves it.

### 2. Hit each provider directly

```bash
curl -sS 'https://www.7timer.info/bin/api.pl?lon=-122.077&lat=37.366&product=astro&output=json' | head -c 200
curl -sS -H "User-Agent: auto-telescope/0.1 (mvhsphysicsastroclub@gmail.com)" 'https://api.weather.gov/points/37.366,-122.077' | head -c 200
curl -sS 'https://api.open-meteo.com/v1/forecast?latitude=37.366&longitude=-122.077&hourly=cloud_cover,visibility,wind_speed_10m' | head -c 200
```

You should see JSON in each response. Common failure modes:

| Output | Provider | Fix |
|--------|----------|-----|
| HTML 503 page | 7Timer | wait 1-4 hours; 7Timer is a single-server free service |
| `403 Forbidden` | NOAA | confirm User-Agent header is set (NOAA blocks requests without one) |
| `429 Too Many Requests` | Open-Meteo | back off; their free tier limits rapid polling |
| Connection refused / timeout | All | check internet first |

### 3. Verify the aggregator's behavior

```python
from auto_telescope.conditions.aggregator import ConditionsAggregator
agg = ConditionsAggregator()
forecasts = agg.fetch(37.366, -122.077)
print(f"got {len(forecasts)} forecasts, providers in first: {forecasts[0].contributing_providers}")
```

If you get any forecasts at all, the system can still operate (with degraded
confidence) — the safety wind check will still refuse if the surviving
provider reports high wind.

If you see `AllProvidersDownError`, the safety layer correctly refuses to slew.

## Fallback order

When deciding whether to manually authorize observation despite an outage:

1. **All three providers up**: full confidence; trust the forecast.
2. **7Timer down, NWS+Open-Meteo up**: use the wind threshold but accept that
   seeing/transparency are unknown. Lower-power visual targets only.
3. **NWS down, 7Timer+Open-Meteo up**: still good for cloud + wind. NWS is the
   only provider with precipitation probability, so weather changes may blindside
   you. Re-check forecasts at 30-min intervals.
4. **Open-Meteo down, 7Timer+NWS up**: full confidence; Open-Meteo is the
   redundancy backup.
5. **Two of three down**: only operate if the surviving provider shows low cloud
   AND low wind. Manually monitor real-time wind from the rooftop sensor every
   10 minutes.
6. **All three down**: do NOT slew. The safety layer will refuse anyway.
   Investigate per "Diagnosis" above.

## Preventive actions

* Subscribe to NOAA NWS service status: <https://www.weather.gov/notification/>.
* Watch the GitHub issue tracker for `7Timer` or `Open-Meteo` outage notices.
* The `diskcache` layer caches successful responses for 15 min by default, so a
  brief outage during a long observation session is unlikely to interrupt
  scheduling. Tune via `AUTO_TELESCOPE_CACHE_TTL_SECONDS` if needed.

## Last resort

If you need to authorize observation despite all forecasts being unavailable
AND you have a human on-site verifying conditions visually:

1. Set `AUTO_TELESCOPE_MAX_WIND_SPEED_MPS=999` to bypass the wind check
   (DO NOT commit this).
2. Pass an explicit `forecast=ConditionsForecast(...)` mock with conservative
   values to `check_can_slew` from the operator script.
3. Document the manual override in the session log.

Never commit a change that disables a safety check by default.
