import pytest
from host.control.desired_position import get_object_coordinates


def test_solar_system_object_visible():
    """
    Test that a known solar system object returns valid coordinates
    and a visibility flag.
    """
    ra, dec, alt, az, visible = get_object_coordinates(
        name="mars",
        lat=34.0,
        lon=-118.0,
        elevation=100
    )

    # Basic sanity checks
    assert 0.0 <= ra < 360.0
    assert -90.0 <= dec <= 90.0
    assert -90.0 <= alt <= 90.0
    assert 0.0 <= az < 360.0
    assert isinstance(visible, bool)


def test_invalid_object_raises_error():
    """
    Ensure invalid object names fail cleanly.
    """
    with pytest.raises(ValueError):
        get_object_coordinates(
            name="not_a_real_object_123",
            lat=0.0,
            lon=0.0,
            elevation=0
        )


def test_solar_system_object_not_visible():
    """
    Test that an object below the horizon returns is_visible=False.
    """
    ra, dec, alt, az, visible = get_object_coordinates(
        name="mars",
        lat=90.0,      # North Pole
        lon=0.0,
        elevation=0
    )
    assert visible is False


def test_named_star_simbad():
    """
    Test that a known star name returns valid coordinates.
    """
    ra, dec, alt, az, visible = get_object_coordinates(
        name="Sirius",
        lat=34.0,
        lon=-118.0,
        elevation=100
    )
    assert 0.0 <= ra < 360.0
    assert -90.0 <= dec <= 90.0
    assert -90.0 <= alt <= 90.0
    assert 0.0 <= az < 360.0
    assert isinstance(visible, bool)


def test_high_elevation():
    """
    Test that function works with elevated observation points.
    """
    ra, dec, alt, az, visible = get_object_coordinates(
        name="Jupiter",
        lat=34.0,
        lon=-118.0,
        elevation=3000  # 3 km elevation
    )
    assert isinstance(visible, bool)
    assert -90.0 <= alt <= 90.0


def test_horizon_edge():
    """
    Test an object that is approximately at the horizon (alt ~ 0).
    """
    ra, dec, alt, az, visible = get_object_coordinates(
        name="Venus",
        lat=0.0,
        lon=0.0,
        elevation=0
    )
    # Altitude could be slightly negative or positive, visibility is bool
    assert isinstance(visible, bool)
    assert -90.0 <= alt <= 90.0


def test_planet_vs_star():
    """
    Ensure function can handle both solar system bodies and named stars.
    """
    bodies = ["mars", "venus", "Sirius", "Betelgeuse"]
    for body in bodies:
        ra, dec, alt, az, visible = get_object_coordinates(
            name=body,
            lat=34.0,
            lon=-118.0,
            elevation=0
        )
        assert 0.0 <= ra < 360.0
        assert -90.0 <= dec <= 90.0
        assert -90.0 <= alt <= 90.0
        assert 0.0 <= az < 360.0
        assert isinstance(visible, bool)


def test_case_insensitivity():
    """
    Ensure that the object name is case-insensitive and trims whitespace.
    Mars, MARS, mars, and '  Mars  ' should all return roughly the same coordinates.
    """
    # Standard input
    ra1, dec1, alt1, az1, vis1 = get_object_coordinates(
        name="mars",
        lat=34.0,
        lon=-118.0,
        elevation=100
    )

    # Uppercase
    ra2, dec2, alt2, az2, vis2 = get_object_coordinates(
        name="MARS",
        lat=34.0,
        lon=-118.0,
        elevation=100
    )

    # Mixed case
    ra3, dec3, alt3, az3, vis3 = get_object_coordinates(
        name="MaRs",
        lat=34.0,
        lon=-118.0,
        elevation=100
    )

    # Leading/trailing spaces
    ra4, dec4, alt4, az4, vis4 = get_object_coordinates(
        name="  Mars  ",
        lat=34.0,
        lon=-118.0,
        elevation=100
    )

    # Use approx to allow tiny floating point differences
    assert ra1 == pytest.approx(ra2)
    assert ra1 == pytest.approx(ra3)
    assert ra1 == pytest.approx(ra4)

    assert dec1 == pytest.approx(dec2)
    assert dec1 == pytest.approx(dec3)
    assert dec1 == pytest.approx(dec4)