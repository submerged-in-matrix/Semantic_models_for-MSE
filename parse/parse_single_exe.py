from env.modules import *
from llm.normalize import normalize_row_with_ollama, RowOut
from llm.llm_def import _extract_material_id_from_text, _fabricate_material_id
from llm.ingest_from_txt import ingest_normalized_row
from ontology.core import g

def parse_to_kg(input_obj: Any,
                *,
                idx: Optional[int] = None,
                source_label: Optional[str] = None,
                source_id: Optional[str] = None,
                dry_run: bool = False) -> dict:
    """
    Parse one item (text or {text|url,...}) with Ollama and  ingest into the KG.

    Parameters
    ----------
    input_obj : str | dict
        The text to parse, or a dict with "text" or "url" (and optional extra metadata).
    idx : int | None
        Ingest index to stamp (if None, we won't add ex:ingestIndex).
    source_label : str | None
        Human-friendly provenance label (e.g., paper title, "arXiv abstract", etc.)
    source_id : str | None
        Stable provenance id (e.g., DOI, URL hash, internal tag).
    dry_run : bool
        If True, do not mutate the KG; only return what would be ingested.

    Returns
    -------
    dict
      {
        "ok": bool,
        "reason": str | None,
        "row": RowOut | None,
        "material_iri": rdflib.term.Identifier | None,
        "added_triples": int,
        "source_label": str | None,
        "source_id": str | None,
      }
    """
    # allow plain strings
    if isinstance(input_obj, str):
        input_obj = {"text": input_obj}

    # Normalize → RowOut (use my STRICT_SYSTEM + fabrication of material_id if missing)
    try:
        nr = normalize_row_with_ollama(input_obj)
    except Exception as e:
        return {"ok": False, "reason": f"normalize failed: {e}", "row": None,
                "material_iri": None, "added_triples": 0,
                "source_label": source_label, "source_id": source_id}

    # If caller forgot provenance, try to glean from input_obj
    if isinstance(input_obj, dict):
        if source_label is None:
            source_label = input_obj.get("source_label") or input_obj.get("title") or "text"
        if source_id is None:
            source_id = input_obj.get("source_id") or input_obj.get("url") or _extract_material_id_from_text(str(input_obj.get("text","")))

    # Ingest (with diff-count)
    before = set(g)
    material_iri = None
    try:
        if dry_run:
            # no mutation: just report what WOULD be added
            return {"ok": True, "reason": "dry_run", "row": nr,
                    "material_iri": None, "added_triples": 0,
                    "source_label": source_label, "source_id": source_id}
        material_iri = ingest_normalized_row(
            nr,
            idx=(idx if idx is not None else int(datetime.now(timezone.utc).timestamp())),
            source_label=source_label,
            source_id=source_id
        )
    except Exception as e:
        return {"ok": False, "reason": f"ingest failed: {e}", "row": nr,
                "material_iri": None, "added_triples": 0,
                "source_label": source_label, "source_id": source_id}

    added = len(set(g) - before)
    return {"ok": True, "reason": None, "row": nr,
            "material_iri": material_iri, "added_triples": added,
            "source_label": source_label, "source_id": source_id}
