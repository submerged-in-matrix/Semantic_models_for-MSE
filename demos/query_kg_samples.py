###1) One row per material by most-recent ingest (per formula)--when the latest fact set for each formula, within a recency window.

from query.exe_query import run_sparql
from kg.SC_KG import df

run_sparql(
"""PREFIX ex:   <http://example.org/mse#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

# --- window: only consider the latest N materials by ingest meta
# change LIMIT 100 to your window size
SELECT ?m ?formula ?bandgap ?crystal_system ?centro ?label ?source_label ?source_id ?ingest_time ?ingest_idx
WHERE {
  { SELECT DISTINCT ?m ?formula ?ingest_time ?ingest_idx
    WHERE {
      { SELECT DISTINCT ?m ?ingest_time ?ingest_idx WHERE {
          ?m a ex:Material .
          OPTIONAL { ?m ex:ingestTime  ?ingest_time }
          OPTIONAL { ?m ex:ingestIndex ?ingest_idx }
        }
        ORDER BY DESC(?ingest_time) DESC(?ingest_idx)
        LIMIT 100
      }
      ?m ex:hasFormula ?formula .
      OPTIONAL { ?m ex:ingestTime  ?ingest_time }
      OPTIONAL { ?m ex:ingestIndex ?ingest_idx }

      # keep only the most recent row for this formula
      FILTER NOT EXISTS {
        ?m2 a ex:Material ;
            ex:hasFormula ?formula .
        OPTIONAL { ?m2 ex:ingestTime  ?t2 }
        OPTIONAL { ?m2 ex:ingestIndex ?i2 }
        FILTER(
          COALESCE(?t2, xsd:dateTime("0001-01-01T00:00:00Z")) >  COALESCE(?ingest_time, xsd:dateTime("0001-01-01T00:00:00Z"))
          ||
          ( COALESCE(?t2, xsd:dateTime("0001-01-01T00:00:00Z")) = COALESCE(?ingest_time, xsd:dateTime("0001-01-01T00:00:00Z"))
            && COALESCE(?i2, -1) > COALESCE(?ingest_idx, -1)
          )
        )
      }
    }
  }

  # now attach properties for that chosen material node
  ?m ex:hasBandGap ?bandgap .
  OPTIONAL { ?m ex:hasCrystalSystem ?crystal_system }
  OPTIONAL { ?m ex:hasCentrosymmetric ?centro }
  OPTIONAL { ?m rdfs:label ?label }
  OPTIONAL { ?m ex:statedIn ?source .
            OPTIONAL { ?source rdfs:label       ?source_label }
            OPTIONAL { ?source ex:hasProvenanceId ?source_id } }

  # example filters – tweak as you like
  FILTER( xsd:float(?bandgap) > 3.0 )
  FILTER( !BOUND(?centro) || (datatype(?centro)=xsd:boolean && ?centro=false) || lcase(str(?centro))="false" )
}
ORDER BY DESC(?ingest_time) DESC(?ingest_idx)
LIMIT 10
"""


)

### when  “the highest reported Eg per formula” (and still show one row). is wanted
run_sparql(
""" 
PREFIX ex:   <http://example.org/mse#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

# --- window: latest N materials first (optional but keeps things fast)
# change LIMIT 100 to your window size, or remove the subselect to scan full KG
WITH {
  SELECT DISTINCT ?m ?ingest_time ?ingest_idx WHERE {
    ?m a ex:Material .
    OPTIONAL { ?m ex:ingestTime  ?ingest_time }
    OPTIONAL { ?m ex:ingestIndex ?ingest_idx }
  }
  ORDER BY DESC(?ingest_time) DESC(?ingest_idx)
  LIMIT 100
} AS %win

# compute MAX Eg per formula across the window
SELECT ?formula (MAX(xsd:float(?bandgap)) AS ?bandgap)
       (SAMPLE(?crystal_system) AS ?crystal_system)
       (SAMPLE(?centro) AS ?centro)
       (SAMPLE(?m) AS ?any_m)
WHERE {
  INCLUDE %win
  ?m ex:hasFormula ?formula .
  ?m ex:hasBandGap ?bandgap .
  OPTIONAL { ?m ex:hasCrystalSystem ?crystal_system }
  OPTIONAL { ?m ex:hasCentrosymmetric ?centro }

  # require that some material with this formula is non-centrosymmetric
  FILTER EXISTS {
    ?m2 ex:hasFormula ?formula ;
        ex:hasCentrosymmetric ?c2 .
    FILTER( (datatype(?c2)=xsd:boolean && ?c2=false) || lcase(str(?c2))="false" )
  }
}
GROUP BY ?formula
HAVING (MAX(xsd:float(?bandgap)) > 3.0)
ORDER BY DESC(?bandgap)
LIMIT 10
""")