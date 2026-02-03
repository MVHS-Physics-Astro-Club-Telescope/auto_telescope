from astropy.coordinates import SkyCoord, EarthLocation, AltAz, get_body
from astropy.time import Time
from astroquery.jplhorizons import Horizons
import astropy.units as u

def get_object_coordinates(name, lat, lon, elevation):
    """
    Returns RA, Dec, Alt, Az, and visibility for a celestial object
    given the observer's latitude, longitude, and elevation.
    """
    name_original = name.strip()
    name_lower = name.lower().strip()

    t = Time.now()

    location = EarthLocation(
        lat=lat * u.deg,
        lon=lon * u.deg,
        height=elevation * u.m
    )

    solar_system_objects = [
        "sun", "moon", "mercury", "venus", "earth", "mars",
        "jupiter", "saturn", "uranus", "neptune", "pluto"
    ]

    # Solar system objects (case-insensitive)
    if name_lower in solar_system_objects:
        try:
            body = get_body(name_lower, t)
            ra = body.ra.deg
            dec = body.dec.deg
        except:
            pass
        else:
            altaz = body.transform_to(AltAz(obstime=t, location=location))
            alt_deg = altaz.alt.deg
            az_deg = altaz.az.deg
            is_visible = bool(alt_deg > 0)
            return ra, dec, alt_deg, az_deg, is_visible

    # JPL Horizons (keep original case)
    try:
        obj = Horizons(id=name_original, location='500', epochs=t.jd)
        eph = obj.ephemerides()
        ra = float(eph['RA'][0])
        dec = float(eph['DEC'][0])
    except:
        pass
    else:
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
        altaz = coord.transform_to(AltAz(obstime=t, location=location))
        alt_deg = altaz.alt.deg
        az_deg = altaz.az.deg
        is_visible = bool(alt_deg > 0)
        return ra, dec, alt_deg, az_deg, is_visible

    # SIMBAD / Name resolution (keep original case)
    try:
        coord = SkyCoord.from_name(name_original)
    except:
        pass
    else:
        ra = coord.ra.deg
        dec = coord.dec.deg
        altaz = coord.transform_to(AltAz(obstime=t, location=location))
        alt_deg = altaz.alt.deg
        az_deg = altaz.az.deg
        is_visible = bool(alt_deg > 0)
        return ra, dec, alt_deg, az_deg, is_visible

    raise ValueError(
        f"Object '{name_original}' not found in solar system DB, Horizons, or SIMBAD."
    )
