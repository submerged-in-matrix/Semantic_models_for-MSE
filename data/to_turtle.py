# --- Serialize graph to Turtle ---encoding="utf-8" ensures rdflib returns bytes --
from env.modules import *
from ontology.core import g
from utils.KG_dir import TTL_OUT

ttl_bytes = g.serialize(format="turtle", encoding="utf-8")
TTL_OUT.write_bytes(ttl_bytes)

# quick sanity check
p = TTL_OUT.resolve()
print("Wrote:", p)
print("Triples in graph:", len(g))
print("File size (bytes):", p.stat().st_size)