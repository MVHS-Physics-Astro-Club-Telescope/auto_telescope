# auto_telescope

Pi-only autonomous control software for the **MVHS Physics & Astronomy Club 10-inch f/4.48 Truss-Tube Dobsonian** telescope.

The telescope sits on a rooftop platform at Mountain View High School. The Raspberry Pi
runs unattended, picks targets, slews, and exposes through an ASI120MC-S camera.
**Safety is the top concern**: the codebase is structured so any uncertainty refuses to slew.

> Phase 1A scope: sky-conditions aggregation, visibility math, smart catalog,
> "best time to observe" scheduler, and hard safety interlocks. Hardware/motor
> control is Phase 1B+ and lives in a separate module.

---

## What this gives you

* **Sky conditions**: `auto_telescope.conditions` aggregates 7Timer! ASTRO + NOAA
  api.weather.gov + Open-Meteo into one pessimistic-consensus hourly forecast,
  tolerating any one provider being down.
* **Visibility math**: `auto_telescope.visibility` does pure-local astropy
  RA/Dec ↔ Alt/Az transforms, sun + moon checks, and contiguous "observation
  window" computation.
* **Smart catalog**: `auto_telescope.catalog` ships ~80 hand-curated targets
  (Tier 1 = beginner-friendly, Tier 2 = challenging, Tier 3 = auto-rejected with
  reason). Solar-system bodies are resolved live via astropy. Anything not in the
  curated list falls through to SIMBAD.
* **Scheduler**: `auto_telescope.scheduler.find_best_windows("M13")` returns the
  top-N quality-scored observation windows over the next N nights for any target.
* **Safety interlocks**: `auto_telescope.safety.check_can_slew()` enforces sun
  avoidance, horizon, and wind limits — fail-CLOSED by default.

---

## Install

Requires Python 3.11+.

```bash
git clone https://github.com/MVHS-Physics-Astro-Club-Telescope/auto_telescope.git
cd auto_telescope
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

On the production Pi, install without `[dev]`:

```bash
pip install -e .
```

---

## Run a smoke test

```python
from auto_telescope.scheduler.best_time import find_best_windows
from auto_telescope.config.site import MVHS_SITE

windows = find_best_windows("M13", site=MVHS_SITE, days=7, limit=5)
for w in windows:
    print(f"{w.window.start_utc:%Y-%m-%d %H:%M UTC}  "
          f"dur={w.window.duration_minutes:.0f}min  "
          f"peak_alt={w.window.peak_altitude_deg:.1f}°  score={w.score:.2f}")
```

This hits the real 7Timer/NOAA/Open-Meteo APIs. Expect results in ~3 seconds.

---

## Test

```bash
pytest                                            # full suite
pytest -m safety                                  # adversarial safety only
pytest --cov=auto_telescope --cov-fail-under=85   # coverage gate
ruff check src tests                              # lint
ruff format --check src tests                     # format
mypy src/                                         # types
```

The test suite is layered:

1. **Unit** — pure logic, ~70 tests, fast.
2. **Property** — Hypothesis invariants (coord round-trip, slew symmetry).
3. **Safety** — adversarial: 2K random pointings, sun pointings every hour,
   DST/antimeridian/polar edges. ALL must pass to ship.
4. **Integration** — recorded against real APIs with vcrpy. Cassettes in
   `tests/integration/cassettes/`.
5. **Simulator** — end-to-end pipeline with stub forecasts.

---

## Configuration

All knobs read from environment variables prefixed `AUTO_TELESCOPE_`. See
`src/auto_telescope/config/settings.py`. Key vars:

| Variable | Default | What |
|----------|---------|------|
| `AUTO_TELESCOPE_LATITUDE` | 37.366 | Site latitude (deg N) |
| `AUTO_TELESCOPE_LONGITUDE` | -122.077 | Site longitude (deg E) |
| `AUTO_TELESCOPE_ELEVATION_M` | 30 | Site elevation (m) |
| `AUTO_TELESCOPE_SUN_AVOIDANCE_DEG` | 30 | Min angular separation from sun |
| `AUTO_TELESCOPE_MIN_ALTITUDE_DEG` | 20 | Min target altitude (horizon safety) |
| `AUTO_TELESCOPE_MAX_WIND_SPEED_MPS` | 15 | Refuse to slew above this wind speed |

---

## Documentation

* `docs/architecture.md` — module boundaries + data flow.
* `docs/safety_guarantees.md` — formal list of guarantees, each linked to its proving test.
* `docs/auto_telescope_design_v3.md` — original full system design (Phase 1+2).
* `runbooks/api_outages.md` — what to do when an API goes down.

---

## Phase 1A acceptance criteria

* [x] Repo reorganized to single Pi-only `src/auto_telescope/` layout
* [x] Real API integrations: 7Timer!, NOAA, Open-Meteo, SIMBAD
* [x] ~80-target curated catalog with tiering + best-month metadata
* [x] Visibility windows with astropy
* [x] `find_best_windows()` end-to-end working against real APIs
* [x] Adversarial safety tests (sun, horizon, DST, antimeridian, polar)
* [x] >85 % coverage (current: 89 %)
* [x] CI matrix Python 3.11 + 3.12
* [x] Pre-commit hooks (ruff lint + format)
* [x] Runbooks for API-down scenarios

---

## Links

* Linear: WOR-21
* GitHub issue: [#17](https://github.com/MVHS-Physics-Astro-Club-Telescope/auto_telescope/issues/17)
* Design doc: `docs/auto_telescope_design_v3.md`

License: MIT.
