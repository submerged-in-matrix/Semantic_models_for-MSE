from env.modules import *
from llm.ingest_from_txt import ingest_normalized_row
from llm.normalize import RowOut
from ontology.core import g

def _norm_str(x):
    return str(x).strip() if pd.notna(x) and str(x).strip() not in {"", "nan", "None"} else None

def ingest_new_csv(csv_path: str, update_df: bool = False):
    new_df = pd.read_csv(csv_path)

    # align columns 
    rename_map = {
        "band_gap": "band_gap_eV",
        "crystalsystem": "crystal_system",
        "centrosymmetric": "is_centrosymmetric",
    }
    new_df = new_df.rename(columns=rename_map)

    added = 0
    for i, r in new_df.iterrows():
        nr = RowOut(
            material          = _norm_str(r.get("formula")) or _norm_str(r.get("material_id")) or f"Material_new_{i}",
            formula           = _norm_str(r.get("formula")),
            material_id       = _norm_str(r.get("material_id")),
            crystal_system    = _norm_str(r.get("crystal_system")),
            is_centrosymmetric= (bool(r["is_centrosymmetric"]) if pd.notna(r.get("is_centrosymmetric")) else None),
            band_gap_eV       = (float(r["band_gap_eV"]) if pd.notna(r.get("band_gap_eV")) else None),
        )
        # idempotent + dedup-aware
        ingest_normalized_row(nr, idx=1_000_000 + i, source_label="csv_import", source_id=csv_path)
        added += 1

    if update_df:
        global df
        # naive append; optional real dedupe
        # df = pd.concat([df, new_df], ignore_index=True).drop_duplicates(subset=["material_id","formula"], keep="first")
        df = pd.concat([df, new_df], ignore_index=True)

    print(f"Ingested {added} rows from {csv_path}. Triples now: {len(g)}")
    return added