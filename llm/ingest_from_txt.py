"""
ingest_from_txt.py — LLM -> KG ingestion (idempotent, dedupe, mandatory provenance).

Changes:
- REMOVED rdfs:label on materials (formula is the identifier and the display name)
- REMOVED BNode provenance node + ex:statedIn + ex:hasProvenanceId
- ADDED ex:hasSourceId as a MANDATORY direct literal on every material
  -> eliminates a 2-hop BNode join and the unbound-variable cross product
     that made queries pathologically slow
- ingestTime / ingestIndex use g.set (single-valued, not accumulating)
"""

from env.modules import *
from ontology.core import *
from ontology.ingest_meta import ingestIndex, ingestTime
from data.mint_entities import _slugify, mint_entity
from utils.llm_schema import RowOut

hasSourceId = EX.hasSourceId

# Canonical provenance values
SOURCE_CSV_BASE     = "CSV_base"        # the featurized CSV the KG was built from
SOURCE_CSV_EXTERNAL = "CSV_external"    # another CSV parsed via parse-lora
SOURCE_ANONYMOUS    = "anonymous_text"  # free text with no identifiable source
# a URL is used verbatim as its own source_id


# ─── Lookup indices for dedupe ─────────────────────────────────────────────────
def _index_materials():
    by_formula, by_id = {}, {}
    for m in g.subjects(RDF.type, Material):
        for f in g.objects(m, hasFormula):
            by_formula[str(f)] = m
        mid = g.value(m, hasExternalId)
        if mid:
            by_id[str(mid)] = m
    return by_formula, by_id


MAT_BY_FORMULA, MAT_BY_ID = _index_materials()


def add_once(s, p, o):
    if (s, p, o) not in g:
        g.add((s, p, o))


def _mint_material_iri(label: str | None, formula: str | None, idx: int):
    """Mint an IRI. No rdfs:label — formula serves that role."""
    if formula and str(formula).strip():
        iri = EX[_slugify(str(formula))]
        g.add((iri, RDF.type, Material))
        return iri
    return mint_entity(label, Material, "Material", idx)


def get_or_create_material(material_id: str | None,
                           formula: str | None,
                           label: str | None,
                           idx: int):
    f = (str(formula).strip() if formula else None)
    mid = (str(material_id).strip() if material_id else None)

    if f:
        if f in MAT_BY_FORMULA:
            return MAT_BY_FORMULA[f]
        m = _mint_material_iri(label, f, idx)
        add_once(m, hasFormula, Literal(f, datatype=XSD.string))
        MAT_BY_FORMULA[f] = m
        if mid:
            add_once(m, hasExternalId, Literal(mid, datatype=XSD.string))
            MAT_BY_ID[mid] = m
        return m

    if mid and mid in MAT_BY_ID:
        return MAT_BY_ID[mid]
    m = _mint_material_iri(label, None, idx)
    if mid:
        add_once(m, hasExternalId, Literal(mid, datatype=XSD.string))
        MAT_BY_ID[mid] = m
    return m


def _resolve_source_id(source_id: str | None) -> str:
    """source_id is mandatory — fall back to the anonymous marker."""
    s = str(source_id).strip() if source_id is not None else ""
    return s if s else SOURCE_ANONYMOUS


def _has_triple(s, p):
    return any(True for _ in g.triples((s, p, None)))


def ingest_normalized_row(nr: RowOut, idx: int = 0,
                          source_id: str | None = None,
                          source_label: str | None = None):   # accepted, ignored
    """
    Ingest one validated row. source_label is accepted for backward compatibility
    but no longer written to the graph.
    """
    m = get_or_create_material(
        material_id=getattr(nr, "material_id", None),
        formula=getattr(nr, "formula", None),
        label=nr.material,
        idx=idx,
    )

    if getattr(nr, "material_id", None):
        add_once(m, hasExternalId, Literal(str(nr.material_id), datatype=XSD.string))

    if nr.band_gap_eV is not None:
        add_once(m, hasBandGap, Literal(float(nr.band_gap_eV), datatype=XSD.float))

    if getattr(nr, "crystal_system", None) and not _has_triple(m, hasCrystalSystem):
        add_once(m, hasCrystalSystem,
                 Literal(str(nr.crystal_system).strip().lower(), datatype=XSD.string))

    if getattr(nr, "is_centrosymmetric", None) is not None and not _has_triple(m, hasCentrosymmetric):
        add_once(m, hasCentrosymmetric,
                 Literal(bool(nr.is_centrosymmetric), datatype=XSD.boolean))

    # MANDATORY provenance, direct literal (no BNode hop)
    add_once(m, hasSourceId, Literal(_resolve_source_id(source_id), datatype=XSD.string))

    # ingest metadata: single-valued
    g.set((m, ingestTime,  Literal(datetime.now(timezone.utc).isoformat(),
                                   datatype=XSD.dateTime)))
    g.set((m, ingestIndex, Literal(int(idx), datatype=XSD.integer)))

    return m
