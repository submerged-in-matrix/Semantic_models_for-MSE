from env.modules import *
from ontology.core import g, EX, RDF, RDFS

problems = []

# A) All Materials should have labels
for s in g.subjects(RDF.type, EX.Material):
    if not any(True for _ in g.objects(s, RDFS.label)):
        problems.append(f"Material without label: {s}")

# B) Band gap must be numeric and non-negative
for s, p, o in g.triples((None, EX.hasBandGap, None)):
    try:
        val = float(o.toPython())
        if val < 0:
            problems.append(f"Negative band gap for {s}")
    except Exception:
        problems.append(f"Non-numeric band gap for {s}: {o}")

print("No obvious problems ✅" if not problems else "Consistency problems:")
for x in problems:
    print("-", x)