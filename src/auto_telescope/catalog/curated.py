"""Curated ~80-target catalog for the MVHS 10" Dobsonian.

Target selection is opinionated: every entry is reachable from a Bortle 7 site
(MVHS) with a 10" f/4.48 reflector and an ASI120MC-S camera (≤30 s exposures).
Tiering reflects what an unattended public observatory can deliver:

- Tier.EASY (1):        Bright, large, beginner-friendly. Lock screens for free.
- Tier.CHALLENGING (2): Visible but needs clear, dark conditions and stacking.
- Tier.SKIP (3):        Auto-rejected with explanation (faint/structural fails).

Coordinates are J2000 ICRS RA in decimal degrees. Sources: SIMBAD-canonical values
cross-checked against the Wikipedia Messier list and SEDS.org. Best-months is the
~3-month window when the object transits in evening hours at +37° N.
"""

from __future__ import annotations

from auto_telescope.catalog.targets import Target, TargetType, Tier


def _t(
    id: str,
    display_name: str,
    target_type: TargetType,
    ra_deg: float,
    dec_deg: float,
    *,
    magnitude: float | None,
    angular_size_arcmin: float | None,
    tier: Tier,
    best_months: tuple[int, ...],
    description: str = "",
    aliases: tuple[str, ...] = (),
) -> Target:
    return Target(
        id=id,
        display_name=display_name,
        target_type=target_type,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        magnitude=magnitude,
        angular_size_arcmin=angular_size_arcmin,
        tier=tier,
        best_months=best_months,
        description=description,
        aliases=aliases,
    )


# fmt: off
_TIER1: tuple[Target, ...] = (
    # --- Globular clusters ----------------------------------------------------------------
    _t("M13",   "Hercules Globular Cluster (M13)",       TargetType.GLOBULAR_CLUSTER, 250.4234,  36.4613, magnitude=5.8,  angular_size_arcmin=20.0, tier=Tier.EASY, best_months=(5, 6, 7), description="Brightest northern globular. Easily resolves edge stars at 100x.", aliases=("NGC 6205",)),
    _t("M22",   "M22 (Sagittarius Globular)",            TargetType.GLOBULAR_CLUSTER, 279.0997, -23.9047, magnitude=5.1,  angular_size_arcmin=24.0, tier=Tier.EASY, best_months=(6, 7, 8), description="Low in the south from MVHS but worth chasing for its size.", aliases=("NGC 6656",)),
    _t("M5",    "M5 (Serpens Globular)",                 TargetType.GLOBULAR_CLUSTER, 229.6385,   2.0810, magnitude=5.7,  angular_size_arcmin=23.0, tier=Tier.EASY, best_months=(5, 6, 7), description="Big, bright, easily resolved.", aliases=("NGC 5904",)),
    _t("M3",    "M3 (Canes Venatici Globular)",          TargetType.GLOBULAR_CLUSTER, 205.5484,  28.3773, magnitude=6.2,  angular_size_arcmin=18.0, tier=Tier.EASY, best_months=(4, 5, 6), description="Excellent globular for spring evenings.", aliases=("NGC 5272",)),
    _t("M15",   "M15 (Pegasus Globular)",                TargetType.GLOBULAR_CLUSTER, 322.4930,  12.1670, magnitude=6.2,  angular_size_arcmin=18.0, tier=Tier.EASY, best_months=(8, 9, 10), description="Dense core, partly resolvable.", aliases=("NGC 7078",)),
    _t("M2",    "M2 (Aquarius Globular)",                TargetType.GLOBULAR_CLUSTER, 323.3625,  -0.8233, magnitude=6.5,  angular_size_arcmin=16.0, tier=Tier.EASY, best_months=(8, 9, 10), description="Symmetric, compact.", aliases=("NGC 7089",)),
    _t("M71",   "M71 (Sagitta Globular)",                TargetType.GLOBULAR_CLUSTER, 298.4438,  18.7792, magnitude=8.2,  angular_size_arcmin=7.2,  tier=Tier.EASY, best_months=(7, 8, 9), description="Loose globular, almost cluster-like.", aliases=("NGC 6838",)),

    # --- Planetary nebulae ----------------------------------------------------------------
    _t("M27",   "Dumbbell Nebula (M27)",                 TargetType.PLANETARY_NEBULA, 299.9015,  22.7211, magnitude=7.5,  angular_size_arcmin=8.0,  tier=Tier.EASY, best_months=(7, 8, 9), description="Large planetary nebula; UHC filter helps.", aliases=("NGC 6853",)),
    _t("M57",   "Ring Nebula (M57)",                     TargetType.PLANETARY_NEBULA, 283.3960,  33.0292, magnitude=8.8,  angular_size_arcmin=1.4,  tier=Tier.EASY, best_months=(6, 7, 8), description="Iconic smoke ring. Small but unmistakable.", aliases=("NGC 6720",)),
    _t("M97",   "Owl Nebula (M97)",                      TargetType.PLANETARY_NEBULA, 168.6987,  55.0190, magnitude=9.9,  angular_size_arcmin=3.4,  tier=Tier.EASY, best_months=(3, 4, 5), description="Faint but distinctive 'owl-eye' planetary.", aliases=("NGC 3587",)),
    _t("NGC6543", "Cat's Eye Nebula (NGC 6543)",         TargetType.PLANETARY_NEBULA, 269.6391,  66.6326, magnitude=8.8,  angular_size_arcmin=0.4,  tier=Tier.EASY, best_months=(5, 6, 7), description="Tiny but bright; reveals teal color through 10\".", aliases=("Caldwell 6",)),

    # --- Double / multiple stars ----------------------------------------------------------
    _t("Albireo", "Albireo (β Cygni)",                   TargetType.DOUBLE_STAR,      292.6804,  27.9597, magnitude=3.1,  angular_size_arcmin=0.6,  tier=Tier.EASY, best_months=(7, 8, 9), description="Most beautiful double in the sky. Gold + sapphire.", aliases=("Beta Cygni",)),
    _t("Mizar", "Mizar (ζ UMa) + Alcor",                 TargetType.DOUBLE_STAR,      200.9814,  54.9254, magnitude=2.2,  angular_size_arcmin=14.4, tier=Tier.EASY, best_months=(3, 4, 5), description="Naked-eye double; itself a quad in the eyepiece.", aliases=("Zeta UMa",)),
    _t("Castor", "Castor (α Geminorum)",                 TargetType.DOUBLE_STAR,      113.6500,  31.8883, magnitude=1.6,  angular_size_arcmin=0.1,  tier=Tier.EASY, best_months=(1, 2, 3), description="Tight white-white pair, best at 200x.", aliases=("Alpha Gem",)),
    _t("EpsLyr", "Epsilon Lyrae (Double Double)",        TargetType.DOUBLE_STAR,      281.0837,  39.6708, magnitude=4.7,  angular_size_arcmin=3.5,  tier=Tier.EASY, best_months=(6, 7, 8), description="Each component is itself a double — four stars.", aliases=("ε Lyr",)),

    # --- Open clusters --------------------------------------------------------------------
    _t("M11",   "Wild Duck Cluster (M11)",               TargetType.OPEN_CLUSTER,     282.7708,  -6.2700, magnitude=6.3,  angular_size_arcmin=14.0, tier=Tier.EASY, best_months=(6, 7, 8), description="Densest open cluster; almost globular.", aliases=("NGC 6705",)),
    _t("M37",   "M37 (Auriga)",                          TargetType.OPEN_CLUSTER,      88.0700,  32.5500, magnitude=6.2,  angular_size_arcmin=24.0, tier=Tier.EASY, best_months=(12, 1, 2), description="Best of Auriga's three open clusters.", aliases=("NGC 2099",)),
    _t("M36",   "M36 (Auriga)",                          TargetType.OPEN_CLUSTER,      84.0833,  34.1333, magnitude=6.3,  angular_size_arcmin=12.0, tier=Tier.EASY, best_months=(12, 1, 2), description="Compact young cluster.", aliases=("NGC 1960",)),
    _t("M38",   "M38 (Auriga)",                          TargetType.OPEN_CLUSTER,      82.1750,  35.8500, magnitude=7.4,  angular_size_arcmin=21.0, tier=Tier.EASY, best_months=(12, 1, 2), description="Cross-shaped open cluster.", aliases=("NGC 1912",)),
    _t("M35",   "M35 (Gemini)",                          TargetType.OPEN_CLUSTER,      92.2700,  24.3300, magnitude=5.3,  angular_size_arcmin=28.0, tier=Tier.EASY, best_months=(12, 1, 2), description="Bright, naked-eye-visible cluster.", aliases=("NGC 2168",)),
    _t("NGC869_884", "Double Cluster (NGC 869/884)",     TargetType.OPEN_CLUSTER,      34.7500,  57.1333, magnitude=4.3,  angular_size_arcmin=60.0, tier=Tier.EASY, best_months=(10, 11, 12), description="Side-by-side open clusters in Perseus. Stunning at low power.", aliases=("Caldwell 14", "h+chi Persei")),
    _t("Hyades", "Hyades (Mel 25)",                      TargetType.OPEN_CLUSTER,      66.7250,  15.8670, magnitude=0.5,  angular_size_arcmin=330.0, tier=Tier.EASY, best_months=(11, 12, 1), description="Nearest open cluster. Use widest-field eyepiece.", aliases=("Mel 25",)),
    _t("M44",   "Beehive Cluster (M44)",                 TargetType.OPEN_CLUSTER,     130.1000,  19.6700, magnitude=3.7,  angular_size_arcmin=95.0, tier=Tier.EASY, best_months=(2, 3, 4), description="Naked-eye fuzzy patch in Cancer.", aliases=("NGC 2632", "Praesepe")),
    _t("M67",   "M67 (Cancer)",                          TargetType.OPEN_CLUSTER,     132.8250,  11.8000, magnitude=6.1,  angular_size_arcmin=30.0, tier=Tier.EASY, best_months=(2, 3, 4), description="Old, rich open cluster.", aliases=("NGC 2682",)),
    _t("M45",   "Pleiades (M45) — partial FOV",          TargetType.OPEN_CLUSTER,      56.7500,  24.1167, magnitude=1.6,  angular_size_arcmin=110.0, tier=Tier.EASY, best_months=(11, 12, 1), description="Naked-eye showpiece. Will not fit our FOV; image one bright member at a time.", aliases=("NGC 1432", "Seven Sisters")),

    # --- Galaxies (bright spring sample) --------------------------------------------------
    _t("M81",   "Bode's Galaxy (M81)",                   TargetType.GALAXY,           148.8883,  69.0653, magnitude=6.9,  angular_size_arcmin=26.9, tier=Tier.EASY, best_months=(2, 3, 4), description="Bright spiral; pairs with M82 in low-power FOV.", aliases=("NGC 3031",)),
    _t("M82",   "Cigar Galaxy (M82)",                    TargetType.GALAXY,           148.9683,  69.6797, magnitude=8.4,  angular_size_arcmin=11.2, tier=Tier.EASY, best_months=(2, 3, 4), description="Edge-on starburst. Dark dust lane visible.", aliases=("NGC 3034",)),
    _t("M51",   "Whirlpool Galaxy (M51)",                TargetType.GALAXY,           202.4696,  47.1953, magnitude=8.4,  angular_size_arcmin=11.2, tier=Tier.EASY, best_months=(4, 5, 6), description="Face-on spiral with companion NGC 5195.", aliases=("NGC 5194",)),
    _t("M104",  "Sombrero Galaxy (M104)",                TargetType.GALAXY,           189.9976, -11.6231, magnitude=8.0,  angular_size_arcmin=8.7,  tier=Tier.EASY, best_months=(4, 5, 6), description="Edge-on with prominent dust lane.", aliases=("NGC 4594",)),
    _t("M65",   "M65 (Leo Triplet)",                     TargetType.GALAXY,           169.7333,  13.0925, magnitude=9.3,  angular_size_arcmin=8.7,  tier=Tier.EASY, best_months=(3, 4, 5), description="Part of the Leo Triplet with M66 + NGC 3628.", aliases=("NGC 3623",)),
    _t("M66",   "M66 (Leo Triplet)",                     TargetType.GALAXY,           170.0625,  12.9914, magnitude=8.9,  angular_size_arcmin=9.1,  tier=Tier.EASY, best_months=(3, 4, 5), description="Brighter member of the Leo Triplet.", aliases=("NGC 3627",)),

    # --- Nebula ---------------------------------------------------------------------------
    _t("M42_core", "Orion Nebula core (M42)",            TargetType.EMISSION_NEBULA,   83.8221,  -5.3911, magnitude=4.0,  angular_size_arcmin=85.0, tier=Tier.EASY, best_months=(11, 12, 1), description="Brightest emission nebula. Trapezium resolves at 200x.", aliases=("NGC 1976",)),

    # --- More Tier 1 fillers (frequent crowd favorites) -----------------------------------
    _t("M4",    "M4 (Scorpius Globular)",                TargetType.GLOBULAR_CLUSTER, 245.8967, -26.5258, magnitude=5.6,  angular_size_arcmin=26.0, tier=Tier.EASY, best_months=(5, 6, 7), description="Loose globular near Antares; low altitude from MVHS.", aliases=("NGC 6121",)),
    _t("M10",   "M10 (Ophiuchus Globular)",              TargetType.GLOBULAR_CLUSTER, 254.2880,  -4.1006, magnitude=6.6,  angular_size_arcmin=15.1, tier=Tier.EASY, best_months=(5, 6, 7), description="Bright globular, mid-sized.", aliases=("NGC 6254",)),
    _t("M12",   "M12 (Ophiuchus Globular)",              TargetType.GLOBULAR_CLUSTER, 251.8092,  -1.9486, magnitude=6.7,  angular_size_arcmin=14.5, tier=Tier.EASY, best_months=(5, 6, 7), description="Companion of M10 — same FOV at low power.", aliases=("NGC 6218",)),
    _t("M92",   "M92 (Hercules Globular)",               TargetType.GLOBULAR_CLUSTER, 259.2808,  43.1357, magnitude=6.4,  angular_size_arcmin=14.0, tier=Tier.EASY, best_months=(5, 6, 7), description="Often overshadowed by M13, but tighter and beautiful.", aliases=("NGC 6341",)),
    _t("M53",   "M53 (Coma Berenices Globular)",         TargetType.GLOBULAR_CLUSTER, 198.2304,  18.1683, magnitude=7.7,  angular_size_arcmin=13.0, tier=Tier.EASY, best_months=(4, 5, 6), description="High-galactic-latitude globular.", aliases=("NGC 5024",)),
    _t("M14",   "M14 (Ophiuchus Globular)",              TargetType.GLOBULAR_CLUSTER, 264.4008,  -3.2461, magnitude=7.6,  angular_size_arcmin=11.7, tier=Tier.EASY, best_months=(5, 6, 7), description="Compact and concentrated.", aliases=("NGC 6402",)),

    _t("M52",   "M52 (Cassiopeia)",                      TargetType.OPEN_CLUSTER,     351.2000,  61.5933, magnitude=7.3,  angular_size_arcmin=13.0, tier=Tier.EASY, best_months=(9, 10, 11), description="Rich open cluster in Cassiopeia.", aliases=("NGC 7654",)),
    _t("M103",  "M103 (Cassiopeia)",                     TargetType.OPEN_CLUSTER,      23.3417,  60.6583, magnitude=7.4,  angular_size_arcmin=6.0,  tier=Tier.EASY, best_months=(10, 11, 12), description="Compact triangular open cluster.", aliases=("NGC 581",)),
    _t("M34",   "M34 (Perseus)",                         TargetType.OPEN_CLUSTER,      40.5000,  42.7833, magnitude=5.5,  angular_size_arcmin=35.0, tier=Tier.EASY, best_months=(10, 11, 12), description="Bright, sparse open cluster.", aliases=("NGC 1039",)),
    _t("M39",   "M39 (Cygnus)",                          TargetType.OPEN_CLUSTER,     323.4750,  48.4333, magnitude=4.6,  angular_size_arcmin=32.0, tier=Tier.EASY, best_months=(8, 9, 10), description="Loose, large open cluster.", aliases=("NGC 7092",)),
    _t("M29",   "M29 (Cygnus)",                          TargetType.OPEN_CLUSTER,     305.9667,  38.5333, magnitude=6.6,  angular_size_arcmin=7.0,  tier=Tier.EASY, best_months=(7, 8, 9), description="Small but distinct open cluster near gamma Cygni.", aliases=("NGC 6913",)),
    _t("M41",   "M41 (Canis Major)",                     TargetType.OPEN_CLUSTER,     101.5000, -20.7167, magnitude=4.5,  angular_size_arcmin=38.0, tier=Tier.EASY, best_months=(1, 2, 3), description="Bright cluster south of Sirius.", aliases=("NGC 2287",)),
    _t("M50",   "M50 (Monoceros)",                       TargetType.OPEN_CLUSTER,     105.7000,  -8.3500, magnitude=5.9,  angular_size_arcmin=16.0, tier=Tier.EASY, best_months=(1, 2, 3), description="Heart-shaped open cluster.", aliases=("NGC 2323",)),
    _t("M48",   "M48 (Hydra)",                           TargetType.OPEN_CLUSTER,     123.4167,  -5.8000, magnitude=5.8,  angular_size_arcmin=54.0, tier=Tier.EASY, best_months=(2, 3, 4), description="Large, bright, sparse cluster.", aliases=("NGC 2548",)),

    # --- Bright stars (alignment + crowd-favorites) ---------------------------------------
    _t("Vega",     "Vega (α Lyrae)",                     TargetType.STAR,             279.2347,  38.7837, magnitude=0.0,  angular_size_arcmin=None, tier=Tier.EASY, best_months=(6, 7, 8), description="Brightest star of summer; alignment reference.", aliases=("Alpha Lyr",)),
    _t("Sirius",   "Sirius (α CMa)",                     TargetType.STAR,             101.2871, -16.7161, magnitude=-1.5, angular_size_arcmin=None, tier=Tier.EASY, best_months=(12, 1, 2), description="Brightest star in night sky.", aliases=("Alpha CMa",)),
    _t("Arcturus", "Arcturus (α Boo)",                   TargetType.STAR,             213.9153,  19.1825, magnitude=-0.05,angular_size_arcmin=None, tier=Tier.EASY, best_months=(4, 5, 6), description="Brightest star of spring; orange giant.", aliases=("Alpha Boo",)),
    _t("Capella",  "Capella (α Aur)",                    TargetType.STAR,              79.1722,  45.9980, magnitude=0.08, angular_size_arcmin=None, tier=Tier.EASY, best_months=(12, 1, 2), description="Yellow giant pair; alignment reference.", aliases=("Alpha Aur",)),
    _t("Polaris",  "Polaris (α UMi)",                    TargetType.STAR,              37.9542,  89.2642, magnitude=2.0,  angular_size_arcmin=None, tier=Tier.EASY, best_months=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), description="The North Star — circumpolar from MVHS.", aliases=("Alpha UMi",)),
    _t("Betelgeuse", "Betelgeuse (α Ori)",               TargetType.STAR,              88.7929,   7.4071, magnitude=0.5,  angular_size_arcmin=None, tier=Tier.EASY, best_months=(12, 1, 2), description="Red supergiant in Orion's shoulder.", aliases=("Alpha Ori",)),
    _t("Rigel",    "Rigel (β Ori)",                      TargetType.STAR,              78.6346,  -8.2017, magnitude=0.13, angular_size_arcmin=None, tier=Tier.EASY, best_months=(12, 1, 2), description="Blue supergiant; tight companion at 200x.", aliases=("Beta Ori",)),
    _t("Deneb",    "Deneb (α Cyg)",                      TargetType.STAR,             310.3580,  45.2803, magnitude=1.25, angular_size_arcmin=None, tier=Tier.EASY, best_months=(8, 9, 10), description="Tail of the Swan; Summer Triangle anchor.", aliases=("Alpha Cyg",)),
    _t("Altair",   "Altair (α Aql)",                     TargetType.STAR,             297.6958,   8.8683, magnitude=0.77, angular_size_arcmin=None, tier=Tier.EASY, best_months=(7, 8, 9), description="Summer Triangle anchor; rapid rotator.", aliases=("Alpha Aql",)),
)


_TIER2: tuple[Target, ...] = (
    _t("M31",   "Andromeda Galaxy (M31)",                TargetType.GALAXY,            10.6847,  41.2687, magnitude=3.4,  angular_size_arcmin=178.0, tier=Tier.CHALLENGING, best_months=(9, 10, 11), description="Largest galaxy in the sky. Will overflow FOV — image core only.", aliases=("NGC 224",)),
    _t("M33",   "Triangulum Galaxy (M33)",               TargetType.GALAXY,            23.4621,  30.6602, magnitude=5.7,  angular_size_arcmin=70.8, tier=Tier.CHALLENGING, best_months=(10, 11, 12), description="Low surface brightness; needs dark sky + stacking.", aliases=("NGC 598",)),
    _t("M101",  "Pinwheel Galaxy (M101)",                TargetType.GALAXY,           210.8025,  54.3486, magnitude=7.9,  angular_size_arcmin=28.8, tier=Tier.CHALLENGING, best_months=(4, 5, 6), description="Face-on spiral, low surface brightness.", aliases=("NGC 5457",)),
    _t("NGC891","NGC 891 (Andromeda edge-on)",           TargetType.GALAXY,            35.6396,  42.3492, magnitude=10.1, angular_size_arcmin=13.5, tier=Tier.CHALLENGING, best_months=(10, 11, 12), description="Classic edge-on with dust lane; needs darkness.", aliases=("Caldwell 23",)),
    _t("Veil",  "Veil Nebula (NGC 6960/6992)",           TargetType.SUPERNOVA_REMNANT, 312.7500,  30.7000, magnitude=7.0,  angular_size_arcmin=180.0, tier=Tier.CHALLENGING, best_months=(8, 9, 10), description="Supernova remnant; OIII filter mandatory.", aliases=("Cygnus Loop",)),
    _t("M16",   "Eagle Nebula (M16)",                    TargetType.EMISSION_NEBULA,  274.7000, -13.8000, magnitude=6.0,  angular_size_arcmin=35.0, tier=Tier.CHALLENGING, best_months=(6, 7, 8), description="Pillars of Creation are too faint, but cluster + nebula glow visible.", aliases=("NGC 6611",)),
    _t("M17",   "Omega/Swan Nebula (M17)",               TargetType.EMISSION_NEBULA,  275.1958, -16.1772, magnitude=6.0,  angular_size_arcmin=11.0, tier=Tier.CHALLENGING, best_months=(6, 7, 8), description="Bright but low altitude from MVHS.", aliases=("NGC 6618",)),
    _t("M20",   "Trifid Nebula (M20)",                   TargetType.EMISSION_NEBULA,  270.6042, -23.0303, magnitude=6.3,  angular_size_arcmin=28.0, tier=Tier.CHALLENGING, best_months=(6, 7, 8), description="Very low at MVHS; image around transit only.", aliases=("NGC 6514",)),
    _t("M8",    "Lagoon Nebula (M8)",                    TargetType.EMISSION_NEBULA,  270.9042, -24.3867, magnitude=6.0,  angular_size_arcmin=90.0, tier=Tier.CHALLENGING, best_months=(6, 7, 8), description="Very low (max alt ~28 deg from MVHS); transit-only.", aliases=("NGC 6523",)),
    _t("NGC7000","North America Nebula (NGC 7000)",      TargetType.EMISSION_NEBULA,  314.7500,  44.3333, magnitude=4.0,  angular_size_arcmin=120.0, tier=Tier.CHALLENGING, best_months=(8, 9, 10), description="Huge HII region; needs HII filter + dark sky.", aliases=("Caldwell 20",)),
)


_TIER3_REJECTED: tuple[Target, ...] = (
    # Auto-rejected with explanation. We surface these so users learn WHY we won't try.
    _t("Horsehead", "Horsehead Nebula (B33) — REJECTED", TargetType.EMISSION_NEBULA,  85.2458,  -2.4583, magnitude=15.0, angular_size_arcmin=8.0, tier=Tier.SKIP, best_months=(11, 12, 1), description="Below detection threshold for 30-s unguided exposures. Skip and explain."),
    _t("M76", "Little Dumbbell (M76) — REJECTED",        TargetType.PLANETARY_NEBULA,  25.5821,  51.5753, magnitude=10.1, angular_size_arcmin=2.7, tier=Tier.SKIP, best_months=(10, 11, 12), description="Faint planetary; OIII filter required. Skip in current automation."),
    _t("M74", "Phantom Galaxy (M74) — REJECTED",         TargetType.GALAXY,            24.1742,  15.7836, magnitude=9.4,  angular_size_arcmin=10.5, tier=Tier.SKIP, best_months=(10, 11, 12), description="Notoriously hard for small scopes; below SNR floor."),
    _t("M110", "M110 — REJECTED",                        TargetType.GALAXY,            10.0917,  41.6850, magnitude=8.5,  angular_size_arcmin=21.9, tier=Tier.SKIP, best_months=(9, 10, 11), description="Surface brightness too low without long stacking."),
)
# fmt: on


CURATED_TARGETS: tuple[Target, ...] = _TIER1 + _TIER2 + _TIER3_REJECTED


_BY_KEY: dict[str, Target] = {}
for _tgt in CURATED_TARGETS:
    _BY_KEY[_tgt.id.lower()] = _tgt
    _BY_KEY[_tgt.display_name.lower()] = _tgt
    for _alias in _tgt.aliases:
        _BY_KEY[_alias.lower()] = _tgt


def get_curated_target(name: str) -> Target | None:
    """Look up a curated target by id, display name, or alias (case-insensitive)."""
    return _BY_KEY.get(name.strip().lower())
