"""auto_telescope — Pi-only autonomous control software for the MVHS 10" Truss-Tube Dobsonian.

Phase 1A modules:
- conditions: real-time sky / weather conditions (7Timer!, NOAA, Open-Meteo)
- visibility: celestial coordinate transforms + horizon/altitude windows (astropy)
- catalog:    curated ~80 target list + SIMBAD lookups + solar-system ephemerides
- scheduler:  best-time-to-observe selection across the next N nights
- safety:     hard interlocks (sun avoidance, horizon, mount limits)
- config:     site location and runtime settings

This package is designed to run unattended on a Raspberry Pi 5 next to the telescope.
The single biggest concern is "telescope damages itself unattended"; safety is module #1.
"""

__version__ = "0.1.0"
