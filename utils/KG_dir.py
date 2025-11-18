from pathlib import Path
import gzip
from ontology.core import g

DATA    = Path("../data/full_dataset_Bandgap_0_to_5_featurized.csv")  # input CSV
TTL_OUT = Path("../data/full_dataset_Bandgap_0_to_5.ttl")             # RDF Turtle output

print("Using data:", DATA.resolve())
print("Will write TTL:", TTL_OUT.resolve())


# --- 2) Save KG (TTL, TTL.GZ, N-Triples) ---
OUT_DIR = Path("../data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
TTL_PATH   = OUT_DIR / "mse_kg_full.ttl"
TTL_GZPATH = OUT_DIR / "mse_kg_full.ttl.gz"
NT_PATH    = OUT_DIR / "mse_kg_full.nt"

ttl_bytes = g.serialize(format="turtle", encoding="utf-8")
TTL_PATH.write_bytes(ttl_bytes)
with gzip.open(TTL_GZPATH, "wb") as f:
    f.write(ttl_bytes)

nt_bytes = g.serialize(format="nt", encoding="utf-8")
NT_PATH.write_bytes(nt_bytes)