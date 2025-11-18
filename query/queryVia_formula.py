from env.modules import *
from kg.SC_KG import g
from ontology.core import hasBandGap, hasFormula, hasCrystalSystem, hasCentrosymmetric

def show_material(f):
    m = next(g.subjects(hasFormula, Literal(f, datatype=XSD.string)), None)
    if not m:
        print("No node with formula:", f); return
    print("Node:", m)
    for (p, name) in [(hasFormula,"formula"),
                      (hasBandGap,"bandgap"),
                      (hasCrystalSystem,"crystal_system"),
                      (hasCentrosymmetric,"centro")]:
        vals = [str(o) for o in g.objects(m, p)]
        print(f"  {name}: {vals if vals else '—'}")