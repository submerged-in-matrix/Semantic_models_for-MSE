"""
exe_query.py — NL query interface for the MSE Knowledge Graph.

Changes:
- No subselect: filter first, limit last
- SELECT (not DISTINCT); each material appears once
- Default sort ORDER BY ASC(?bandgap); sort_by="ingest" for recency
- No core_optionals block (sanitizer owns the body)
- show_material(): direct rdflib index lookup, no SPARQL, no LLM)
"""

import time
from env.modules import *
from query.query_rules import SPARQL_PREFIX
from utils.sanitize_query import nl_to_sparql
from utils.sel_ollama import QUERY_MODEL
from utils.extract_where import _extract_where_body
from ontology.core import (g, EX, Material, hasFormula, hasBandGap,
                           hasCrystalSystem, hasCentrosymmetric, hasExternalId)



def run_sparql(query: str):
    """Execute SPARQL against the in-memory graph, return a DataFrame."""
    qres = g.query(query)
    cols = [str(v) for v in qres.vars]
    rows = [{str(k): (str(v) if v is not None else None)
             for k, v in zip(cols, r)} for r in qres]
    return pd.DataFrame(rows, columns=cols)


def ask_kg(question: str,
           n: int = 10,
           window: int | None = None,
           sort_by: str = "bandgap",       # "bandgap" (ASC) | "ingest" (DESC)
           model=None):
    """
    Natural language -> SPARQL -> DataFrame.

    Flow: all materials -> filter -> sort -> limit
    (Previously: all materials -> latest N -> filter, which lost matches.)
    """
    model = model or QUERY_MODEL

    t = time.perf_counter()
    sparql0 = nl_to_sparql(question, model=model)
    t_llm = time.perf_counter() - t

    body = _extract_where_body(sparql0)

    projection = "?m ?formula ?bandgap ?crystal_system ?centro ?source_id"
    if sort_by == "ingest":
        projection += " ?ingest_time ?ingest_idx"

    where_block = "WHERE {\n"
    if body:
        where_block += "  " + body.replace("\n", "\n  ") + "\n"
    if sort_by == "ingest":
        # ingest metadata is provenance-only; bind it solely when sorting by it
        where_block += "  OPTIONAL { ?m ex:ingestTime ?ingest_time }\n"
        where_block += "  OPTIONAL { ?m ex:ingestIndex ?ingest_idx }\n"
    where_block += "}\n"

    order_block = ("ORDER BY DESC(?ingest_time) DESC(?ingest_idx)\n"
                   if sort_by == "ingest" else "ORDER BY ASC(?bandgap)\n")

    limit = window if window is not None else n
    limit_block = f"LIMIT {int(limit)}\n" if limit is not None else ""

    sparql = SPARQL_PREFIX + f"SELECT {projection}\n" + where_block + order_block + limit_block
    print("SPARQL (final):\n", sparql)

    t = time.perf_counter()
    df = run_sparql(sparql)
    t_sparql = time.perf_counter() - t
    print(f"[timing] LLM {t_llm:.1f}s | SPARQL {t_sparql:.1f}s")

    if "formula" in df.columns and not df.empty:
        df = df.drop_duplicates(subset=["formula"], keep="first").reset_index(drop=True)
        if window is not None:
            df = df.head(n)

    return df