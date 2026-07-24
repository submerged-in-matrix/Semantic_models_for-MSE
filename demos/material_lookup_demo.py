"""
demos/material_lookup_demo.py — Look up a material when you already know its formula.

This path deliberately does NOT use SPARQL. `g.subjects(hasFormula, ...)` is a hash
lookup on rdflib's (predicate, object) index; the equivalent SPARQL query costs
tokenization, parse-tree construction, join planning and filter evaluation to
retrieve a node you can already address directly.

Benchmarked on a 5,000-material graph: 0.125 ms direct vs 6.29 ms via SPARQL (~126x).

Use ask_kg()        when you don't know what you're looking for :D.
Use show_material() when you do.
"""

import sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ontology.core import g
from query.queryVia_formula import show_material

# Load the KG if it isn't already populated (e.g. when run standalone)
if len(g) < 1000:
    ttl = ROOT / "data" / "mse_kg_full.ttl"
    t = time.perf_counter()
    g.parse(ttl, format="turtle")
    print(f"Loaded {len(g):,} triples from {ttl.name} ({time.perf_counter()-t:.1f}s)\n")
else:
    print(f"Graph already populated: {len(g):,} triples\n")


FORMULAS = [
    # "Ga5O33N5Cl7",     # ingested via parse-lora demo
    # "Ga8O3N5Cl7",      # ingested via parse-lora demo
    # "Ga2O3N5Cl73",     # deliberately absent 
    "GaAs", 
]

print("=" * 1)
for f in FORMULAS:
    t = time.perf_counter()
    show_material(f)
    print(f"  [{(time.perf_counter()-t)*1000:.2f} ms]")
    print("-" * 1)

# Timing over a batch, for comparison against ask_kg's SPARQL numbers
sample = FORMULAS * 20
t = time.perf_counter()
for f in sample:
    show_material(f)
per = (time.perf_counter() - t) / len(sample) * 1000
print(f"\nMean over {len(sample)} lookups: {per:.2f} ms each")
