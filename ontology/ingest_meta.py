from env.modules import *
from ontology.core import *

ingestIndex = EX.ingestIndex        # integer, sequence number of ingest
ingestTime  = EX.ingestTime         # xsd:dateTime when ingested

for prop, rng, comment in [
    (ingestIndex, XSD.integer,  "Monotonic ingest sequence number for this material record."),
    (ingestTime,  XSD.dateTime, "Timestamp when this record was ingested into the KG (ISO 8601)."),
]:
    if (prop, RDF.type, RDF.Property) not in g:
        g.add((prop, RDF.type,   RDF.Property))
        g.add((prop, RDFS.domain, EX.Material))
        g.add((prop, RDFS.range,  rng))
        
        # comment must be an RDF term (Literal), not a Python str
        g.add((prop, RDFS.comment, Literal(comment)))

print("Ingest metadata properties declared (idempotent).")
print("Triples so far:", len(g))
