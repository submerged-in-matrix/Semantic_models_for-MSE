from env.modules import *
from ontology.core import g
from ontology.core import (hasBandGap, hasFormula, hasCrystalSystem,
                           hasCentrosymmetric, hasExternalId, EX)

hasSourceId = EX.hasSourceId

def show_material(f):
    m = next(g.subjects(hasFormula, Literal(f, datatype=XSD.string)), None)
    if not m:
        print("No node with formula:", f); return
    print("Node:", m)
    for (p, name) in [(hasFormula,"formula"),
                      (hasExternalId,"material_id"),
                      (hasBandGap,"bandgap"),
                      (hasCrystalSystem,"crystal_system"),
                      (hasCentrosymmetric,"centro"),
                      (hasSourceId,"source_id")]:
        vals = [str(o) for o in g.objects(m, p)]
        print(f"  {name}: {vals if vals else '—'}")