"""SIMBAD integration test.

Note: SIMBAD's astroquery client uses pyvo's TAP machinery which doesn't always
play nicely with vcrpy's HTTP interception (it can use a separate transport).
We therefore skip when running offline, but verify the live path works when run
locally. The cassette recording for SIMBAD is left out; CI will skip this test.
"""

from __future__ import annotations

import os

import pytest

from auto_telescope.catalog.simbad import lookup_simbad

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="SIMBAD live calls are flaky from CI; tested locally before each release.",
)
def test_simbad_resolves_m31() -> None:
    """SIMBAD should resolve M31 (Andromeda) to its known coordinates."""
    result = lookup_simbad("M31")
    assert result is not None, "SIMBAD failed to resolve M31"
    assert result.id == "M31"
    # Andromeda RA ~ 10.68 deg, Dec ~ +41.27 deg
    assert abs(result.ra_deg - 10.68) < 1.0
    assert abs(result.dec_deg - 41.27) < 1.0
