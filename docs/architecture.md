# Architecture (Phase 1A — Pi-only refactor)

## What changed

The original design was a host+Pi+TCP split (see `auto_telescope_design_v3.md` for
full history). Phase 1A pivots to **single-Pi**: every module lives on the
Raspberry Pi 5 next to the telescope, communicating in-process. Reasons:

* Solo software lead. Two-process designs double the failure surface.
* Pi 5 has more than enough CPU for the celestial math at the cadence we need.
* Eliminating a TCP boundary kills an entire class of bugs (serialization,
  reconnect, partial reads).

The hardware abstraction (motors, GPIO, sensors) is still planned for Phase 1B
and will live alongside this code in `auto_telescope.hardware`. Phase 1A does
NOT include any motor / GPIO control — only the planning brain.

## Module map

```
src/auto_telescope/
├── config/
│   ├── site.py        Site dataclass + MVHS_SITE default
│   └── settings.py    Pydantic settings (env-driven)
├── conditions/
│   ├── seven_timer.py 7Timer! ASTRO adapter (cloud, seeing, transparency)
│   ├── nws.py         NOAA api.weather.gov adapter
│   ├── open_meteo.py  Open-Meteo adapter (backup)
│   ├── aggregator.py  Reconcile 3 providers → ConditionsForecast list
│   └── cache.py       diskcache wrapper for API responses
├── visibility/
│   ├── coordinates.py RA/Dec ↔ Alt/Az transforms (astropy)
│   ├── horizons.py    is_above_horizon, sun_altitude, sun_below_horizon
│   ├── rules.py       is_visible (sun + alt + moon)
│   └── windows.py     compute_windows: contiguous visibility blocks
├── catalog/
│   ├── targets.py     Target dataclass, TargetType, Tier, resolve_target
│   ├── curated.py     ~70 hand-tiered targets for the 10" Dob
│   ├── solar_system.py Live Sun/Moon/planet ephemerides
│   ├── simbad.py      SIMBAD network fallback
│   └── feasibility.py "Should we even attempt this?" check
├── scheduler/
│   └── best_time.py   find_best_windows: ranked observation windows
├── safety/
│   └── interlocks.py  HARD safety checks; fail-CLOSED everywhere
└── __init__.py
```

## Data flow

```
                   ┌─────────────────────────┐
                   │  user / scheduler tick  │
                   └────────────┬────────────┘
                                │ "find best time for M13"
                                ▼
   ┌──────────────────────────────────────────────────┐
   │ scheduler.find_best_windows                      │
   │  1. catalog.resolve_target ─► Target             │
   │  2. visibility.compute_windows ─► [Window]       │
   │  3. conditions.aggregator.fetch ─► [Forecast]    │
   │  4. score(window, forecast) ─► [ScoredWindow]    │
   └────────────┬───────────────────────────────┬─────┘
                │                               │
                ▼                               ▼
       astropy local math               HTTP: 7Timer + NOAA + Open-Meteo
       (Sun/Moon/planet ephemerides)    (parallel-safe; cache 15 min)


   ┌──────────────────────────────────────────────────┐
   │ Before any slew, controller calls:               │
   │   safety.check_can_slew(coord, when, forecast)   │
   │ Refuses on FIRST failure (sun → horizon → wind)  │
   └──────────────────────────────────────────────────┘
```

## Why this layout works for solo maintenance

* **Single-direction imports**: `safety` depends on `visibility` + `conditions`,
  but neither imports `safety`. No cycles.
* **Pure dataclasses across boundaries**: `Target`, `EquatorialCoord`,
  `ConditionsForecast`, `InterlockResult`. These are the only types that cross
  module boundaries. Everything else is private.
* **Every public function is testable in isolation**: the test suite has 87
  cases covering pure logic, property invariants, adversarial safety, real-API
  recordings, and end-to-end pipelines.
* **Fail-CLOSED safety**: if the conditions aggregator can't reach any provider,
  `check_wind` refuses. If a coordinate transform fails, the calling function
  raises. The system never silently slews on incomplete data.

## External integrations

| Service | Purpose | Fallback |
|---------|---------|----------|
| 7Timer! ASTRO | seeing, transparency, cloud | aggregator continues without seeing |
| NOAA api.weather.gov | wind, clouds, temp (US) | aggregator continues |
| Open-Meteo | cloud, visibility, wind (worldwide) | aggregator continues |
| astropy | local Sun/Moon/planet ephemeris | none — local data |
| SIMBAD (astroquery) | resolve unknown target names | catalog.resolve_target raises KeyError |

## Performance budget

On a Pi 5:
* `radec_to_altaz` for one target: ~5 ms.
* 7-day visibility window scan with 15-min steps (672 evaluations): ~3 s.
* All-three-providers fetch: ~2 s (parallel-safe; cached for 15 min).
* `find_best_windows("M13", days=7)` end-to-end: ~5 s on cold cache, < 100 ms
  with warm cache.

This is well within the "scheduler runs every 5 minutes" budget envisioned for
Phase 1B's autonomous operation loop.
