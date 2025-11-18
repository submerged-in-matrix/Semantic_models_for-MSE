from env.modules import *
from ontology.core import g, EX, Literal, XSD
from utils.KG_dir import TTL_OUT

def propose_triples_from_text(text: str):
    """
    Demo placeholder:
    Pretend we parsed that 'GaN has Eg ~3.4 eV'.
    Later this can be swapped for NLP/LLM-based extraction.
    """
    return [(EX.GaN, EX.hasBandGap, Literal(3.4, datatype=XSD.float))]

# Insert demo triples
for s, p, o in propose_triples_from_text("GaN has band gap ~3.4 eV"):
    g.add((s, p, o))

print("Triples after stub insert:", len(g))

# --- Update the TTL file with new triples ---
TTL_OUT.write_bytes(g.serialize(format="turtle", encoding="utf-8"))

print("Updated:", TTL_OUT.resolve())
print("Triples now in graph:", len(g))