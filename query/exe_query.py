from env.modules import *
from query.query_rules import SPARQL_PREFIX
from utils.sanitize_query import *
from llm.llm_def import _MODEL
from utils.extract_where import _extract_where_body
from utils.ensure_optional import _ensure_optional_block
from ontology.core import g

def run_sparql(query: str):
    qres = g.query(query)
    cols = [str(v) for v in qres.vars]
    rows = [{str(k): (str(v) if v is not None else None) for k, v in zip(cols, r)} for r in qres]
    return pd.DataFrame(rows, columns=cols)


def ask_kg(question: str,
           n: int | None = None,
           last_n: bool = False,             # kept for API compatibility; ignored if window is set
           window: int | None = None,        # e.g., 100 → pre-filter to last 100 ingested
           pick: str = "last",               # "first" or "last" after windowing
           model=None):


    model = model or _MODEL

    # NL → sanitized SPARQL (already SELECT ... WHERE { ... })
    sparql0 = nl_to_sparql(question, model=model)

    #  Extract WHERE body only (remove SELECT/PREFIX/ORDER/LIMIT)
    body = _extract_where_body(sparql0)

    #  Build a VALID query with an inner sub-SELECT for the recency window
    #  If window is None → no subselect; else wrap in subselect+ORDER+LIMIT
    subselect = ""
    join_ingest_bindings = ""
    if window is not None:
        subselect = (
            "  {\n"
            "    SELECT DISTINCT ?m ?ingest_time ?ingest_idx WHERE {\n"
            "      ?m a ex:Material .\n"
            "      OPTIONAL { ?m ex:ingestTime  ?ingest_time }\n"
            "      OPTIONAL { ?m ex:ingestIndex ?ingest_idx }\n"
            "    }\n"
            "    ORDER BY DESC(?ingest_time) DESC(?ingest_idx)\n"
            f"    LIMIT {int(window)}\n"
            "  }\n"
        )
        join_ingest_bindings = ""  # body already refers to ?m; ingest vars are available from subselect
    else:
        # no window: just ensure the ingest vars are optionally bound so ORDER BY works
        join_ingest_bindings = (
            "  OPTIONAL { ?m ex:ingestTime  ?ingest_time }\n"
            "  OPTIONAL { ?m ex:ingestIndex ?ingest_idx }\n"
        )

    #  Compose a clean SELECT head + WHERE { subselect + body (+optional binds) } + ORDER/LIMIT
    head = (
        SPARQL_PREFIX +
        "SELECT DISTINCT ?m ?label ?formula ?bandgap ?crystal_system ?centro ?source_label ?source_id ?ingest_time ?ingest_idx\n"
    )

    # Ensure OPTIONAL blocks for label/formula/bandgap/system/centro/source, the built sanitizer usually does this, but this keeps the wrapper robust)
    core_optionals = ""
    core_optionals = _ensure_optional_block(core_optionals, "?m rdfs:label ?label")
    core_optionals = _ensure_optional_block(core_optionals, "?m ex:hasFormula ?formula")
    core_optionals = _ensure_optional_block(core_optionals, "?m ex:hasBandGap ?bandgap")
    core_optionals = _ensure_optional_block(core_optionals, "?m ex:hasCrystalSystem ?crystal_system")
    core_optionals = _ensure_optional_block(core_optionals, "?m ex:hasCentrosymmetric ?centro")
    core_optionals += "  OPTIONAL { ?m ex:statedIn ?source }\n"
    core_optionals += "  OPTIONAL { ?source rdfs:label ?source_label }\n"
    core_optionals += "  OPTIONAL { ?source ex:hasProvenanceId ?source_id }\n"

    where_block = "WHERE {\n" + subselect
    # Always anchor to Material; the body may already add it, duplicate is harmless
    where_block += "  ?m a ex:Material .\n"
    if body:
        where_block += "  " + body + "\n"
    where_block += join_ingest_bindings
    where_block += core_optionals
    where_block += "}\n"

    order_block = "ORDER BY DESC(?ingest_time) DESC(?ingest_idx)\n"

    # Apply outer LIMIT for n (final slice); also dedupe  by formula in Python after execution
    limit_block = f"LIMIT {int(n)}\n" if n is not None else ""

    # Final SPARQL
    sparql = head + where_block + order_block + limit_block

    print("SPARQL (sanitized):\n", sparql)

    #  Execute
    df = run_sparql(sparql)

    #  De-dupe by formula (keep first row, which is most recent due to ORDER BY)
    if "formula" in df.columns:
        df = df.dropna(subset=["formula"])
        # if picking last, reverse first to keep last occurrences
        if pick.lower() == "last":
            df = df.iloc[::-1]
        df = df.drop_duplicates(subset=["formula"], keep="first")
        # after dedupe, re-apply n if not applied in SPARQL
        if n is not None:
            df = df.head(n)

        # restore descending recency if reversed
        if pick.lower() == "last":
            df = df.iloc[::-1].reset_index(drop=True)
        else:
            df = df.reset_index(drop=True)

    return df