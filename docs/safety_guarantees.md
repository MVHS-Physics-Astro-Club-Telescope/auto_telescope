# Safety Guarantees (Phase 1A)

The single largest concern for this project is **the telescope damaging itself
unattended** — a slew into the sun, into a wall, or in high wind that breaks the
mount. This document enumerates every formal safety guarantee, the code that
provides it, and the test that proves it.

If any of these guarantees regresses, the build MUST fail.

---

## Guarantee 1 — Sun avoidance

**Statement**: The system will never instruct the mount to slew within 30°
(default; configurable via `AUTO_TELESCOPE_SUN_AVOIDANCE_DEG`) of the Sun, at
any time, regardless of operator intent.

**Implementation**:
* `auto_telescope.safety.interlocks.check_sun_avoidance` — computes the Sun's
  current AltAz, transforms back to ICRS, takes great-circle separation from
  the target.
* Used by the aggregate `check_can_slew` which all motor commands must call.

**Proving tests**:
* `tests/safety/test_adversarial.py::test_sun_pointings_always_refused` — for
  every hour of June 21 2026, point exactly at the Sun → MUST be refused.
* `tests/unit/test_safety.py::TestCheckSunAvoidance::test_sun_pointing_blocked`
  — direct sun pointing at noon → refused with code `sun_too_close`.

---

## Guarantee 2 — Horizon limit

**Statement**: The system will never instruct the mount to slew below 20°
altitude (default; configurable via `AUTO_TELESCOPE_MIN_ALTITUDE_DEG`). This
prevents the OTA from striking the rooftop platform railings.

**Implementation**:
* `auto_telescope.safety.interlocks.check_horizon` — computes target AltAz at
  the requested time and refuses if altitude < threshold.

**Proving tests**:
* `tests/safety/test_adversarial.py::test_random_below_horizon_pointings_all_refused`
  — 2 000 random RA/Dec pointings; the geometric majority below the horizon
  MUST all be refused.
* `tests/unit/test_safety.py::TestCheckHorizon::test_below_horizon_blocked`.
* `tests/safety/test_adversarial.py::test_polar_target_always_passes_horizon_at_high_lat`
  — Polaris is circumpolar; it must always pass the horizon check at MVHS.

---

## Guarantee 3 — Wind cutoff

**Statement**: The system will refuse to slew when forecast wind > 15 m/s
(default; configurable via `AUTO_TELESCOPE_MAX_WIND_SPEED_MPS`). This prevents
the truss tube from oscillating beyond mount design tolerance.

**Implementation**:
* `auto_telescope.safety.interlocks.check_wind` — refuses if forecast is
  `None` (defense-in-depth: no data ⇒ no slew) or if wind exceeds threshold.

**Proving tests**:
* `tests/unit/test_safety.py::TestCheckWind::test_no_forecast_blocks` —
  forecast None → refused with code `no_forecast`.
* `tests/unit/test_safety.py::TestCheckWind::test_wind_above_threshold_blocks` —
  20 m/s > 15 m/s threshold → refused with code `wind_too_high`.
* `tests/safety/test_adversarial.py::test_wind_check_refuses_on_no_forecast`.

---

## Guarantee 4 — Edge-case time handling

**Statement**: Daylight Savings Time transitions, antimeridian RA values, and
polar declinations must NOT cause the safety checks to crash, return malformed
results, or accidentally accept dangerous pointings.

**Implementation**:
* All time math is done in UTC (`datetime` with `tzinfo=UTC`).
* `radec_to_altaz` and `altaz_to_radec` round-trip at <0.01° (~36").
* `EquatorialCoord` wraps RA into `[0, 360)` automatically.

**Proving tests**:
* `tests/safety/test_adversarial.py::test_dst_transition_safe` — every 30 min
  across the March 8 2026 DST transition; safety check returns a valid bool.
* `tests/safety/test_adversarial.py::test_antimeridian_targets_handled` —
  RA values right around the 0/180/360° wraps.
* `tests/property/test_coordinate_invariants.py::test_radec_altaz_round_trip` —
  Hypothesis-driven property test over arbitrary RA/Dec/time inputs.

---

## Guarantee 5 — Fail-CLOSED on missing data

**Statement**: If any input to a safety check is missing or unreachable
(e.g. weather APIs all down), the safety layer refuses to slew rather than
proceeding without information.

**Implementation**:
* `aggregator.fetch` raises `AllProvidersDownError` when all three providers
  fail, surfacing the failure to the caller.
* `check_wind(None, ...)` returns refusal with code `no_forecast`.

**Proving tests**:
* `tests/unit/test_conditions_parsing.py::TestAggregator::test_all_providers_down_raises`.
* `tests/unit/test_safety.py::TestCheckWind::test_no_forecast_blocks`.
* `tests/simulator/test_end_to_end.py::test_find_best_windows_handles_no_forecasts`
  — even with all providers down, the scheduler degrades gracefully (visibility-
  only windows) without producing fake forecasts.

---

## Guarantee 6 — First-failure reporting

**Statement**: The aggregate `check_can_slew` returns the FIRST failed
interlock, not "all failures lumped together." This ensures the operator UI can
render a single, actionable reason ("sun too close" vs. "horizon AND wind").

**Implementation**:
* `safety.interlocks.check_can_slew` iterates the bundle in sun → horizon →
  wind order and returns immediately on first refusal.

**Proving test**:
* `tests/unit/test_safety.py::TestCheckCanSlew::test_returns_first_failure` —
  below-horizon target with simultaneous high wind → refusal code is
  `below_horizon`, not `wind_too_high`.

---

## What's NOT yet guaranteed (Phase 1B+)

These are explicit non-goals for Phase 1A and will be added when motor / mount
hardware control is wired in:

* Hard mount limit switches (electrical, not software).
* Watchdog timer for the main loop.
* Dew point / lens-fogging detection.
* Instantaneous gust detection (we currently use forecast wind, not anemometer).
* Optical-tube cap detection (slewing with the cap on is mechanically harmless
  but optically embarrassing; will be addressed by a camera image-statistics
  check in Phase 2).

Each of these will get its own row in this document and a proving test before
the corresponding hardware ships.
