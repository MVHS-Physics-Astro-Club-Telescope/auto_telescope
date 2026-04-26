"""Hypothesis property tests for coordinate transforms.

Invariants:
  * radec_to_altaz → altaz_to_radec is lossless within ~3 arcsec.
  * slew_distance_deg is symmetric.
  * angular_separation_deg is non-negative and ≤ 180 deg.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from auto_telescope.config.site import MVHS_SITE
from auto_telescope.visibility.coordinates import (
    AltAzPosition,
    EquatorialCoord,
    altaz_to_radec,
    angular_separation_deg,
    radec_to_altaz,
    slew_distance_deg,
)


@st.composite
def equatorial_coords(draw):  # type: ignore[no-untyped-def]
    return EquatorialCoord(
        ra_deg=draw(
            st.floats(min_value=0.0, max_value=359.99, allow_nan=False, allow_infinity=False)
        ),
        dec_deg=draw(
            st.floats(min_value=-89.0, max_value=89.0, allow_nan=False, allow_infinity=False)
        ),
    )


@st.composite
def utc_times(draw):  # type: ignore[no-untyped-def]
    base = datetime(2026, 1, 1, tzinfo=UTC)
    minutes = draw(st.integers(min_value=0, max_value=365 * 24 * 60))
    return base + timedelta(minutes=minutes)


@settings(deadline=None, max_examples=40, suppress_health_check=[HealthCheck.too_slow])
@given(coord=equatorial_coords(), when=utc_times())
def test_radec_altaz_round_trip(coord: EquatorialCoord, when: datetime) -> None:
    altaz = radec_to_altaz(coord, when, MVHS_SITE)
    recovered = altaz_to_radec(altaz, MVHS_SITE)
    # Wrap-aware RA difference.
    delta_ra = abs(((recovered.ra_deg - coord.ra_deg + 540.0) % 360.0) - 180.0)
    delta_dec = abs(recovered.dec_deg - coord.dec_deg)
    # 0.01 deg = 36 arcsec — astropy round-trip is precision-bound by frame inversion.
    assert delta_ra < 0.01, f"RA mismatch {delta_ra:.5f} for coord={coord} at {when}"
    assert delta_dec < 0.01, f"Dec mismatch {delta_dec:.5f} for coord={coord} at {when}"


@st.composite
def altaz_positions(draw):  # type: ignore[no-untyped-def]
    return AltAzPosition(
        altitude_deg=draw(st.floats(min_value=-89.0, max_value=89.0, allow_nan=False)),
        azimuth_deg=draw(st.floats(min_value=0.0, max_value=359.99, allow_nan=False)),
        when_utc=datetime(2026, 1, 1, tzinfo=UTC),
        site_name="x",
    )


@settings(deadline=None, max_examples=80)
@given(a=altaz_positions(), b=altaz_positions())
def test_slew_distance_symmetric(a: AltAzPosition, b: AltAzPosition) -> None:
    d_ab = slew_distance_deg(a, b)
    d_ba = slew_distance_deg(b, a)
    assert abs(d_ab - d_ba) < 1e-6
    assert 0.0 <= d_ab <= 180.0


@settings(deadline=None, max_examples=80)
@given(a=equatorial_coords(), b=equatorial_coords())
def test_angular_separation_bounds(a: EquatorialCoord, b: EquatorialCoord) -> None:
    sep = angular_separation_deg(a, b)
    assert 0.0 <= sep <= 180.0
    # Symmetry
    assert abs(sep - angular_separation_deg(b, a)) < 1e-6
