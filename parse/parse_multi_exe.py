from env.modules import *
from llm.normalize import normalize_row_with_ollama, RowOut
from llm.llm_def import _extract_material_id_from_text, _fabricate_material_id
from llm.ingest_from_txt import ingest_normalized_row
from ontology.core import g
from parse.parse_single_exe import parse_to_kg

def parse_many_to_kg(items: Iterable[Any],
                     *,
                     start_idx: int = 1_000_000,
                     source_label: Optional[str] = None,
                     dry_run: bool = False) -> pd.DataFrame:
    """
    Batch parse & ingest a list of items (texts or dicts).

    Each item gets idx = start_idx + i to keep ingest order stable.
    If source_label is given, it's used for all; otherwise per-item label is inferred.

    Returns a DataFrame with one row per item.
    """
    rows = []
    total_before = len(g)
    for i, it in enumerate(items, 1):
        res = parse_to_kg(
            it,
            idx=(start_idx + i),
            source_label=source_label,
            source_id=(None if isinstance(it, str) else it.get("source_id") if isinstance(it, dict) else None),
            dry_run=dry_run
        )
        rows.append({
            "i": i,
            "ok": res["ok"],
            "reason": res["reason"],
            "material": (res["row"].material if res["ok"] and res["row"] else None),
            "formula": (res["row"].formula if res["ok"] and res["row"] else None),
            "band_gap_eV": (res["row"].band_gap_eV if res["ok"] and res["row"] else None),
            "crystal_system": (res["row"].crystal_system if res["ok"] and res["row"] else None),
            "is_centrosymmetric": (res["row"].is_centrosymmetric if res["ok"] and res["row"] else None),
            "material_id": (res["row"].material_id if res["ok"] and res["row"] else None),
            "added_triples": res["added_triples"],
            "source_label": res["source_label"],
            "source_id": res["source_id"],
            "iri": str(res["material_iri"]) if res["material_iri"] else None,
        })
    total_after = len(g)
    df = pd.DataFrame(rows)
    if not dry_run:
        print(f"Batch added triples: {total_after - total_before} (across {len(rows)} items)")
    else:
        print(f"[dry_run] Would add triples for {len(rows)} items (graph unchanged)")
    return df