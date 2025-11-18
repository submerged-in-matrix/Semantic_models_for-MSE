from query.exe_query import run_sparql
from kg.SC_KG import df

run_sparql("""
PREFIX ex: <http://example.org/mse#>
SELECT (COUNT(*) AS ?n) WHERE { ?m ex:hasBandGap ?bandgap }
""")

# How many Material nodes?
run_sparql("""
PREFIX ex:<http://example.org/mse#>
SELECT (COUNT(DISTINCT ?m) AS ?materials)
WHERE { ?m a ex:Material }
""")

# How many materials have a band gap?
run_sparql("""
PREFIX ex:<http://example.org/mse#>
SELECT (COUNT(DISTINCT ?m) AS ?materials_with_Eg)
WHERE { ?m ex:hasBandGap ?bandgap }
""")

# (In pandas) how many rows had a non-null band_gap_eV?
df['band_gap_eV'].notna().sum()

# How many unique materials remained after getting filtered by dedupe key(s)?
df['material_id'].nunique(), df['formula'].nunique()
