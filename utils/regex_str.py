from env.modules import *
# -------- Paths ----------
DATA_DIR   = Path("../data").resolve()
INPUT_XLSX = DATA_DIR / "full_dataset_Bandgap_0_to_5.xlsx"
OUTPUT_CSV = DATA_DIR / "full_dataset_Bandgap_0_to_5_featurized.csv"

# -------- Regex helpers for the pretty string  (see regex documentation. Regex - "verbose mode" can be used to write it in a columnar manner)----------
re_abc     = re.compile(r"abc\s*:\s*([-\d\.Ee+]+)\s+([-\d\.Ee+]+)\s+([-\d\.Ee+]+)", re.I)  # case-insensitive

re_angles  = re.compile(r"angles\s*:\s*([-\d\.Ee+]+)\s+([-\d\.Ee+]+)\s+([-\d\.Ee+]+)", re.I)

re_pbc     = re.compile(r"pbc\s*:\s*(True|False)\s+(True|False)\s+(True|False)", re.I)

re_sites_header = re.compile(r"Sites\s*\(\d+\)", re.I)

re_site_row = re.compile(
    r"^\s*\d+\s+([A-Za-z][a-z]?)\s+([-\d\.Ee+]+)\s+([-\d\.Ee+]+)\s+([-\d\.Ee+]+)",
    re.I
)

def parse_pretty_structure(txt):
    """Parse pymatgen's pretty-printed Structure summary into a Structure."""
    if not isinstance(txt, str):
        return None
    s = txt.strip()

    # Lattice params
    m_abc = re_abc.search(s)
    m_ang = re_angles.search(s)
    if not (m_abc and m_ang):
        return None
    a, b, c = map(float, m_abc.groups())
    alpha, beta, gamma = map(float, m_ang.groups())

    # PBC (default: True,True,True)
    m_pbc = re_pbc.search(s)
    pbc = tuple(map(lambda x: x.lower()=="true", m_pbc.groups())) if m_pbc else (True, True, True)

    # Sites block: find header, then parse subsequent lines
    lines = s.splitlines()
    try:
        start_idx = next(i for i, ln in enumerate(lines) if re_sites_header.search(ln))
    except StopIteration:
        return None

    species, frac_coords = [], []
    for ln in lines[start_idx+1:]:
        m = re_site_row.match(ln)
        if not m:
            continue
        sp, fa, fb, fc = m.groups()
        species.append(sp)
        frac_coords.append([float(fa), float(fb), float(fc)])

    if not species:
        return None

    # Build lattice & structure
    lat = Lattice.from_parameters(a=a, b=b, c=c, alpha=alpha, beta=beta, gamma=gamma)
    try:
        # pymatgen Structure ignores PBC per-axis in initializer; periodicity is assumed.
        struct = Structure(lattice=lat, species=species, coords=frac_coords, coords_are_cartesian=False)
        return struct
    except Exception:
        return None