# Ontology skeleton for: material_id, formula, band_gap, crystal_system, is_centrosymmetric
# (structure captured via crystal system + inversion center only)

from env.modules import *

g = Graph()

# Namespaces
EX = Namespace("http://example.org/mse#")
g.bind("ex", EX)
g.bind("rdfs", RDFS)
g.bind("xsd", XSD)

# Classes
Material         = EX.Material
CrystalStructure = EX.CrystalStructure
Property         = EX.Property  # generic placeholder

for cls in [Material, CrystalStructure, Property]:
    g.add((cls, RDF.type, RDFS.Class))

# Datatype properties (aligned to featurized CSV)
hasExternalId     = EX.hasExternalId        # -> material_id
hasFormula        = EX.hasFormula           # -> formula (composition string)
hasBandGap        = EX.hasBandGap           # -> band_gap (eV)
hasCrystalSystem  = EX.hasCrystalSystem     # -> crystal_system (e.g., cubic, hexagonal)
hasCentrosymmetric= EX.hasCentrosymmetric   # -> is_centrosymmetric (True/False)

for prop in [hasExternalId, hasFormula, hasBandGap, hasCrystalSystem, hasCentrosymmetric]:
    g.add((prop, RDF.type, RDF.Property))

# Domain/Range annotations
g.add((hasExternalId,      RDFS.domain, Material)); g.add((hasExternalId,      RDFS.range, XSD.string))
g.add((hasFormula,         RDFS.domain, Material)); g.add((hasFormula,         RDFS.range, XSD.string))
g.add((hasBandGap,         RDFS.domain, Material)); g.add((hasBandGap,         RDFS.range, XSD.float))
g.add((hasCrystalSystem,   RDFS.domain, Material)); g.add((hasCrystalSystem,   RDFS.range, XSD.string))
g.add((hasCentrosymmetric, RDFS.domain, Material)); g.add((hasCentrosymmetric, RDFS.range, XSD.boolean))

print("Ontology initialized (structure via crystal_system + inversion center, plus composition & bandgap).")
print("Triples so far:", len(g))