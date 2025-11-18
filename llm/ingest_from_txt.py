# LLM → KG: ingest a normalized row (idempotent, dedupe, provenance)
from env.modules import *
from ontology.core import *
from ontology.ingest_meta import ingestIndex, ingestTime
from data.mint_entities import _slugify, mint_entity
from utils.llm_schema import RowOut


#  Ontology add-ons (once) 
statedIn        = EX.statedIn
hasProvenanceId = EX.hasProvenanceId
for prop in [statedIn, hasProvenanceId]:
    g.add((prop, RDF.type, RDF.Property))
    g.add((prop, RDFS.domain, RDFS.Resource))
    g.add((prop, RDFS.range,  RDFS.Resource))

#  Fast lookup indices for dedupe by material_id / formula ---
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

def _mint_material_iri(label: str|None, formula: str|None, idx: int):
    if formula and str(formula).strip():
        safe = _slugify(str(formula))
        iri  = EX[safe]
        g.add((iri, RDF.type, Material))
        g.add((iri, RDFS.label, Literal(str(formula))))
        return iri
    # fallback to generic minting with label or placeholder
    return mint_entity(label, Material, "Material", idx)


# --- 2) Idempotent triple adder ---
def add_once(s, p, o):
    if (s, p, o) not in g:
        g.add((s, p, o))

# --- 3) Get-or-create material with dedupe rules ---
def get_or_create_material(material_id: str|None,
                           formula: str|None,
                           label: str|None,
                           idx: int):
    f = (str(formula).strip() if formula else None)
    mid = (str(material_id).strip() if material_id else None)

    # 1) If formula present, ALWAYS key by formula (do not merge via ID)
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

    # 2) Only if formula missing, use material_id as fallback key
    if mid and mid in MAT_BY_ID:
        return MAT_BY_ID[mid]
    m = _mint_material_iri(label, None, idx)
    if mid:
        add_once(m, hasExternalId, Literal(mid, datatype=XSD.string))
        MAT_BY_ID[mid] = m
    return m


# --- 4) Provenance node helper with small cache to avoid duplicates ---
_SOURCE_CACHE = {}  # key: (label, id) -> BNode

def make_source_node(source_label: Optional[str] = None, source_id: Optional[str] = None):
    key = (source_label or "", source_id or "")
    if key in _SOURCE_CACHE:
        return _SOURCE_CACHE[key]
    src = BNode()
    if source_label:
        add_once(src, RDFS.label, Literal(source_label))
    if source_id:
        add_once(src, hasProvenanceId, Literal(source_id))
    _SOURCE_CACHE[key] = src
    return src

# --- 5) Ingest (idempotent + dedupe + provenance) ---
def tag_ingest_metadata(m, idx: int):
    """Attach ingestIndex & ingestTime once (idempotent)."""
    add_once(m, ingestIndex, Literal(int(idx), datatype=XSD.integer))
    add_once(m, ingestTime, Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime))


def _has_triple(s, p):
    return any(True for _ in g.triples((s, p, None)))

def ingest_normalized_row(nr: RowOut, idx: int = 0,
                          source_label: str | None = None,
                          source_id: str | None = None):
    m = get_or_create_material(
        material_id = getattr(nr, "material_id", None),
        formula     = getattr(nr, "formula", None),
        label       = nr.material,
        idx         = idx
    )

    # identifiers (formula already attached at creation if present)
    if getattr(nr, "material_id", None):
        add_once(m, hasExternalId, Literal(str(nr.material_id), datatype=XSD.string))

    # numeric
    if nr.band_gap_eV is not None:
        add_once(m, hasBandGap, Literal(float(nr.band_gap_eV), datatype=XSD.float))

    # structure facets: add if missing
    if getattr(nr, "crystal_system", None) and not _has_triple(m, hasCrystalSystem):
        add_once(m, hasCrystalSystem, Literal(str(nr.crystal_system), datatype=XSD.string))
    if getattr(nr, "is_centrosymmetric", None) is not None and not _has_triple(m, hasCentrosymmetric):
        add_once(m, hasCentrosymmetric, Literal(bool(nr.is_centrosymmetric), datatype=XSD.boolean))

    # provenance + ingest meta
    if source_label or source_id:
        src = make_source_node(source_label, source_id)
        add_once(m, statedIn, src)
    add_once(m, ingestTime,  Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime))
    add_once(m, ingestIndex, Literal(int(idx), datatype=XSD.integer))

    return m