SPARQL_PREFIX = """PREFIX ex: <http://example.org/mse#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

NL2SPARQL_SYSTEM = f"""
Generate SPARQL SELECT for this ontology:

Class:
  ex:Material

Properties on ex:Material (all literals):
  ex:hasFormula (xsd:string)         -> ?formula
  ex:hasExternalId (xsd:string)
  ex:hasBandGap (xsd:float)          -> ?bandgap
  ex:hasCrystalSystem (xsd:string)   -> ?crystal_system
  ex:hasCentrosymmetric (xsd:boolean)-> ?centro
  

Rules (IMPORTANT):
- Output ONLY a SPARQL SELECT query.
- Include the PREFIX block exactly as given by the user.
- Always BIND variables before filtering them.
- Do NOT use 'NOT'. For non-centrosymmetric: ?m ex:hasCentrosymmetric ?centro . FILTER(?centro = false)
- ?bandgap, ?formula, ?crystal_system, ?centro and ?source_id are ALWAYS required triples. Never wrap them in OPTIONAL.
- Default projection (if unspecified): ?m ?formula ?bandgap ?crystal_system ?centro ?source_id
- Do NOT emit rdfs:label, ex:statedIn, ex:hasProvenanceId, ex:ingestTime, or ex:ingestIndex.
"""