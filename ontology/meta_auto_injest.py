from env.modules import *
from ontology.core import *
try:
    # Py 3.11+: datetime.UTC exists
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

def iso_now():
    # Always UTC, no microseconds, with 'Z' suffix
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def next_ingest_index(graph):
    existing = []
    for s, p, o in graph.triples((None, EX.ingestIndex, None)):
        try:
            existing.append(int(o.toPython()))
        except Exception:
            pass
    return (max(existing) + 1) if existing else 1

def material_iri(material_id: str):
    safe_id = str(material_id).strip().replace(" ", "_").replace("/", "_")
    return EX[f"material/{safe_id}"]

def add_material_row(row, graph, ingest_idx=None, when_iso=None):
    m = material_iri(row["material_id"])
    graph.add((m, RDF.type, EX.Material))

    # Core fields
    graph.add((m, EX.hasExternalId,      Literal(str(row["material_id"]))))
    graph.add((m, EX.hasFormula,         Literal(str(row["formula"]))))
    graph.add((m, EX.hasBandGap,         Literal(float(row["band_gap"]))))
    graph.add((m, EX.hasCrystalSystem,   Literal(str(row["crystal_system"]))))
    graph.add((m, EX.hasCentrosymmetric, Literal(bool(row["is_centrosymmetric"]))))

    # Ingest metadata (auto)
    if ingest_idx is None:
        ingest_idx = next_ingest_index(graph)
    if when_iso is None:
        when_iso = iso_now()

    graph.add((m, EX.ingestIndex, Literal(int(ingest_idx), datatype=XSD.integer)))

    # Use set() to ensure a single value; avoids deprecated utcnow()
    graph.set((m, EX.ingestTime, Literal(when_iso, datatype=XSD.dateTime)))

    return m