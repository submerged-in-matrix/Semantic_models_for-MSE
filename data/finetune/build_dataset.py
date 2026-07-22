"""
Generates a JSONL fine-tuning dataset for the NL -> SPARQL task
(ask_kg / nl_to_sparql in the Semantic_models_for-MSE pipeline).

Each line: {"messages": [system, user, assistant]}
- system  = exact NL2SPARQL_SYSTEM prompt used in production
- user    = a natural-language question
- assistant = the canonical, clean SPARQL the model should learn to produce

Run: python3 build_dataset.py
Output: query_dataset.jsonl
"""

import json
import random

random.seed(42)

# ---- Exact system prompt from the notebook (kept identical on purpose) ----
NL2SPARQL_SYSTEM = """
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
- If filtering band gap, ensure ?bandgap is bound (OPTIONAL if not central).
- Default projection (if unspecified): ?m ?label ?formula ?bandgap ?crystal_system ?centro ?source_label ?source_id
"""

PREFIX = """PREFIX ex: <http://example.org/mse#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

CRYSTAL_SYSTEMS = ["cubic", "hexagonal", "monoclinic", "orthorhombic",
                   "tetragonal", "triclinic", "trigonal"]

BASE_OPTIONALS = (
    "  OPTIONAL { ?m rdfs:label ?label }\n"
    "  OPTIONAL { ?m ex:statedIn ?source }\n"
    "  OPTIONAL { ?source rdfs:label ?source_label }\n"
    "  OPTIONAL { ?source ex:hasProvenanceId ?source_id }\n"
)

SELECT_HEAD = "SELECT ?m ?label ?formula ?bandgap ?crystal_system ?centro ?source_label ?source_id\n"
SELECT_HEAD_RECENCY = ("SELECT ?m ?label ?formula ?bandgap ?crystal_system ?centro "
                       "?source_label ?source_id ?ingest_time ?ingest_idx\n")

examples = []  # list of (question, sparql)


def add(question, sparql):
    examples.append((question, sparql.strip() + "\n"))


# ---------------------------------------------------------------
# A) Band gap < X
# ---------------------------------------------------------------
phr_lt = [
    "List all materials with band gap less than {x} eV",
    "Show materials with band gap under {x} eV",
    "Which materials have a band gap smaller than {x} eV?",
    "Find semiconductors with Eg < {x} eV",
    "Give me materials whose band gap is below {x} eV",
    "materials with bandgap less than {x}",
]
for x in [0.5, 1, 1.5, 2, 3, 4]:
    sparql = f"""{PREFIX}{SELECT_HEAD}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula ?formula .
  ?m ex:hasBandGap ?bandgap .
  FILTER( BOUND(?bandgap) && xsd:float(?bandgap) < {x} )
  OPTIONAL {{ ?m ex:hasCrystalSystem ?crystal_system }}
  OPTIONAL {{ ?m ex:hasCentrosymmetric ?centro }}
{BASE_OPTIONALS}}}"""
    for phr in random.sample(phr_lt, 3):
        add(phr.format(x=x), sparql)

# ---------------------------------------------------------------
# B) Band gap > X
# ---------------------------------------------------------------
phr_gt = [
    "List all materials with band gap greater than {x} eV",
    "Show materials with band gap above {x} eV",
    "Which materials have Eg > {x} eV?",
    "Find materials with a wide band gap over {x} eV",
    "materials with bandgap more than {x}",
]
for x in [1, 2, 2.5, 3, 3.5, 4]:
    sparql = f"""{PREFIX}{SELECT_HEAD}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula ?formula .
  ?m ex:hasBandGap ?bandgap .
  FILTER( BOUND(?bandgap) && xsd:float(?bandgap) > {x} )
  OPTIONAL {{ ?m ex:hasCrystalSystem ?crystal_system }}
  OPTIONAL {{ ?m ex:hasCentrosymmetric ?centro }}
{BASE_OPTIONALS}}}"""
    for phr in random.sample(phr_gt, 3):
        add(phr.format(x=x), sparql)

# ---------------------------------------------------------------
# C) Band gap between X and Y
# ---------------------------------------------------------------
phr_range = [
    "List materials with band gap between {x} and {y} eV",
    "Show materials with Eg from {x} to {y} eV",
    "Which materials have a band gap in the range {x}-{y} eV?",
    "materials with bandgap {x} to {y} ev",
]
for (x, y) in [(0.5, 1.5), (1, 2), (1.5, 2.5), (2, 3), (2.5, 3.5)]:
    sparql = f"""{PREFIX}{SELECT_HEAD}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula ?formula .
  ?m ex:hasBandGap ?bandgap .
  FILTER( BOUND(?bandgap) && xsd:float(?bandgap) >= {x} && xsd:float(?bandgap) <= {y} )
  OPTIONAL {{ ?m ex:hasCrystalSystem ?crystal_system }}
  OPTIONAL {{ ?m ex:hasCentrosymmetric ?centro }}
{BASE_OPTIONALS}}}"""
    for phr in random.sample(phr_range, 3):
        add(phr.format(x=x, y=y), sparql)

# ---------------------------------------------------------------
# D) Crystal system equality
# ---------------------------------------------------------------
phr_cs = [
    "List all {cs} materials",
    "Show me materials that are {cs}",
    "Which materials have {cs} crystal structure?",
    "Find {cs} semiconductors",
]
for cs in CRYSTAL_SYSTEMS:
    for phr in random.sample(phr_cs, 3):
        sparql = f"""{PREFIX}{SELECT_HEAD}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula ?formula .
  ?m ex:hasBandGap ?bandgap .
  ?m ex:hasCrystalSystem ?crystal_system .
  FILTER( lcase(str(?crystal_system)) = "{cs}" )
  OPTIONAL {{ ?m ex:hasCentrosymmetric ?centro }}
{BASE_OPTIONALS}}}"""
        q = phr.format(cs=cs)
        add(q, sparql)

# ---------------------------------------------------------------
# E) Centrosymmetric true / false
# ---------------------------------------------------------------
phr_centro_true = [
    "List all centrosymmetric materials",
    "Show materials that are centrosymmetric",
    "Which materials have an inversion center?",
]
phr_centro_false = [
    "List all non-centrosymmetric materials",
    "Show materials that are not centrosymmetric",
    "Which materials lack an inversion center?",
]
centro_true_filter = ('FILTER( BOUND(?centro) && ((datatype(?centro)=xsd:boolean '
                      '&& ?centro=true) || lcase(str(?centro))="true") )')
centro_false_filter = ('FILTER( BOUND(?centro) && ((datatype(?centro)=xsd:boolean '
                       '&& ?centro=false) || lcase(str(?centro))="false") )')

for phr in phr_centro_true:
    sparql = f"""{PREFIX}{SELECT_HEAD}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula ?formula .
  ?m ex:hasBandGap ?bandgap .
  ?m ex:hasCentrosymmetric ?centro .
  {centro_true_filter}
  OPTIONAL {{ ?m ex:hasCrystalSystem ?crystal_system }}
{BASE_OPTIONALS}}}"""
    add(phr, sparql)

for phr in phr_centro_false:
    sparql = f"""{PREFIX}{SELECT_HEAD}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula ?formula .
  ?m ex:hasBandGap ?bandgap .
  ?m ex:hasCentrosymmetric ?centro .
  {centro_false_filter}
  OPTIONAL {{ ?m ex:hasCrystalSystem ?crystal_system }}
{BASE_OPTIONALS}}}"""
    add(phr, sparql)

# ---------------------------------------------------------------
# F) Combined: crystal_system + centro + bandgap range (your own example)
# ---------------------------------------------------------------
combos = [
    ("cubic", True, 1, 2),
    ("hexagonal", False, 0.5, 1.5),
    ("monoclinic", True, 3, 4),
    ("trigonal", False, 1, 3),
    ("tetragonal", True, 2, 3.5),
]
phr_combo = [
    "List me {cs} materials with bandgap {x}-{y}ev and are {centro_word}",
    "Show {cs} materials with band gap between {x} and {y} eV that are {centro_word}",
    "Find {centro_word} {cs} semiconductors with Eg from {x} to {y} eV",
]
for (cs, centro, x, y) in combos:
    centro_word = "centrosymmetric" if centro else "non-centrosymmetric"
    centro_filter = centro_true_filter if centro else centro_false_filter
    sparql = f"""{PREFIX}{SELECT_HEAD}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula ?formula .
  ?m ex:hasBandGap ?bandgap .
  FILTER( BOUND(?bandgap) && xsd:float(?bandgap) >= {x} && xsd:float(?bandgap) <= {y} )
  ?m ex:hasCrystalSystem ?crystal_system .
  FILTER( lcase(str(?crystal_system)) = "{cs}" )
  ?m ex:hasCentrosymmetric ?centro .
  {centro_filter}
{BASE_OPTIONALS}}}"""
    for phr in phr_combo:
        add(phr.format(cs=cs, x=x, y=y, centro_word=centro_word), sparql)

# ---------------------------------------------------------------
# G) Recency: latest N entries
# ---------------------------------------------------------------
phr_recent = [
    "Show me the latest {n} entries",
    "What are the {n} most recently added materials?",
    "List the last {n} materials ingested",
    "Give me the {n} newest materials in the graph",
]
for n in [5, 10, 20]:
    sparql = f"""{PREFIX}{SELECT_HEAD_RECENCY}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula ?formula .
  ?m ex:hasBandGap ?bandgap .
  OPTIONAL {{ ?m ex:hasCrystalSystem ?crystal_system }}
  OPTIONAL {{ ?m ex:hasCentrosymmetric ?centro }}
  OPTIONAL {{ ?m ex:ingestTime ?ingest_time }}
  OPTIONAL {{ ?m ex:ingestIndex ?ingest_idx }}
{BASE_OPTIONALS}}}
ORDER BY DESC(?ingest_time) DESC(?ingest_idx)
LIMIT {n}"""
    for phr in random.sample(phr_recent, 3):
        add(phr.format(n=n), sparql)

# ---------------------------------------------------------------
# H) Formula lookup
# ---------------------------------------------------------------
formulas = ["GaN", "ZnO", "InP", "SiC", "AlN", "Ga2O3", "GaAs"]
phr_formula = [
    "Show me materials with {f}",
    "What is the band gap of {f}?",
    "Show me details of material {f}",
    "Give me the crystal system and band gap of {f}",
    "Tell me about {f}",
]
for f in formulas:
    sparql = f"""{PREFIX}{SELECT_HEAD}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula "{f}"^^xsd:string .
  ?m ex:hasFormula ?formula .
  OPTIONAL {{ ?m ex:hasBandGap ?bandgap }}
  OPTIONAL {{ ?m ex:hasCrystalSystem ?crystal_system }}
  OPTIONAL {{ ?m ex:hasCentrosymmetric ?centro }}
{BASE_OPTIONALS}}}"""
    for phr in random.sample(phr_formula, 2):
        add(phr.format(f=f), sparql)

# ---------------------------------------------------------------
# I) Provenance / source
# ---------------------------------------------------------------
sources = ["fabricated_demo", "web_import", "materials_project"]
phr_source = [
    "Which materials came from source {s}?",
    "List materials whose source label is {s}",
    "Show materials imported via {s}",
]
for s in sources:
    sparql = f"""{PREFIX}{SELECT_HEAD}WHERE {{
  ?m a ex:Material .
  ?m ex:hasFormula ?formula .
  OPTIONAL {{ ?m ex:hasBandGap ?bandgap }}
  OPTIONAL {{ ?m ex:hasCrystalSystem ?crystal_system }}
  OPTIONAL {{ ?m ex:hasCentrosymmetric ?centro }}
  ?m ex:statedIn ?source .
  ?source rdfs:label ?source_label .
  FILTER( lcase(str(?source_label)) = "{s.lower()}" )
  OPTIONAL {{ ?source ex:hasProvenanceId ?source_id }}
}}"""
    for phr in random.sample(phr_source, 2):
        add(phr.format(s=s), sparql)

# ---------------------------------------------------------------
# Write JSONL
# ---------------------------------------------------------------
random.shuffle(examples)

with open("query_dataset.jsonl", "w") as f:
    for question, sparql in examples:
        row = {
            "messages": [
                {"role": "system", "content": NL2SPARQL_SYSTEM.strip()},
                {"role": "user", "content": question},
                {"role": "assistant", "content": sparql.strip()},
            ]
        }
        f.write(json.dumps(row) + "\n")

print(f"Wrote {len(examples)} examples to query_dataset.jsonl")
