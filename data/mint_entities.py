# Featurized CSV columns: material_id, formula, band_gap, crystal_system, is_centrosymmetric
from env.modules import *
from ontology.core import *
from utils.KG_dir import DATA

# load
df_raw = pd.read_csv(DATA)

# rename to stable names (will be treated as gloabal)
df = df_raw.rename(columns={
    "material_id":        "material_id",
    "formula":            "formula",
    "band_gap":           "band_gap_eV",
    "crystal_system":     "crystal_system",
    "is_centrosymmetric": "is_centrosymmetric",
}).copy()



# enforcing dtypes 
for col in ["formula", "material_id", "crystal_system"]:
    if col in df.columns:
        df[col] = df[col].astype("string")

df["band_gap_eV"] = pd.to_numeric(df.get("band_gap_eV"), errors="coerce")

if "is_centrosymmetric" in df.columns:
    # normalize 
    df["is_centrosymmetric"] = df["is_centrosymmetric"].map(
        lambda x: bool(int(x)) if str(x).strip() in {"1","0"} else
                  (str(x).strip().lower() == "true") if pd.notna(x) else None
    )

# --- 2) Helpers (consistent across the notebook) ---
def _slugify(text: str) -> str:
    text = str(text).strip().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
    text = re.sub(r"[^A-Za-z0-9_]", "_", text)
    return text

def mint_entity(label, cls: URIRef, fallback_prefix: str, idx: int):
    if label is None or (pd.isna(label) if hasattr(pd, "isna") else label is None) or str(label).strip() == "":
        safe = f"{fallback_prefix}_{idx}"
        iri  = EX[safe]
        g.add((iri, RDF.type, cls))
        g.add((iri, RDFS.label, Literal(f"{fallback_prefix} #{idx}")))
        return iri
    label_str = str(label)
    safe = _slugify(label_str)
    iri  = EX[safe]
    g.add((iri, RDF.type, cls))
    g.add((iri, RDFS.label, Literal(label_str)))
    return iri

print("Data loaded. Rows:", len(df))
print("Columns:", list(df.columns))