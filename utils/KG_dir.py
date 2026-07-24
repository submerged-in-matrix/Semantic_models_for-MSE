from pathlib import Path
import gzip
from ontology.core import g

ROOT = Path(__file__).resolve().parent.parent      # repo root, cwd-independent

DATA    = ROOT / "data" / "full_dataset_Bandgap_0_to_5_featurized.csv"
TTL_OUT = ROOT / "data" / "full_dataset_Bandgap_0_to_5.ttl"

OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TTL_PATH   = OUT_DIR / "mse_kg_full.ttl"
TTL_GZPATH = OUT_DIR / "mse_kg_full.ttl.gz"
NT_PATH    = OUT_DIR / "mse_kg_full.nt"


def save_kg(min_triples: int = 1000):
    """Serialize the graph. Refuses to overwrite a real KG with a near-empty one."""
    if len(g) < min_triples:
        raise RuntimeError(f"Refusing to save: graph has only {len(g)} triples.")
    ttl_bytes = g.serialize(format="turtle", encoding="utf-8")
    TTL_PATH.write_bytes(ttl_bytes)
    with gzip.open(TTL_GZPATH, "wb") as f:
        f.write(ttl_bytes)
    NT_PATH.write_bytes(g.serialize(format="nt", encoding="utf-8"))
    print(f"Saved {len(g)} triples → {TTL_PATH.name}")