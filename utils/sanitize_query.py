from env.modules import *
from query.query_rules import *
from llm.llm_def import _MODEL

def sanitize_sparql(q: str) -> str:
    import re

    q = q.strip()
    if q.startswith("```"):
        q = q.strip("`").split("\n", 1)[1].strip()

    PREFIX = SPARQL_PREFIX.strip() + "\n"
    if "PREFIX ex:" not in q:
        q = PREFIX + q

    # --- Collect WHERE-ish lines & tail (ORDER/LIMIT)
    lines = [ln.strip() for ln in q.splitlines() if ln.strip()]
    where_lines, tail_order = [], []
    for ln in lines:
        low = ln.lower()
        if low.startswith(("prefix", "select")):
            continue
        if low.startswith(("order by", "limit")):
            tail_order.append(ln)
            continue
        if low.startswith(("where {", "optional", "filter", "bind", "values", "}")) or "?m " in ln or " ex:" in ln or ln.startswith("?"):
            where_lines.append(ln)

    # --- Flatten WHERE body; remove stray braces; clean illegal patterns
    where_txt = "\n".join(where_lines)
    where_txt = where_txt.replace("WHERE {", "").replace("{", "").replace("}", "")
    # kill FILTER(BIND(...)) and self-BIND patterns
    where_txt = re.sub(r'FILTER\s*\(\s*BIND\s*\([^)]+\)[^)]*\)\s*\.?', '', where_txt, flags=re.IGNORECASE)
    where_txt = re.sub(r'BIND\s*\(\s*[a-zA-Z0-9_:]+\s*\(\s*\?([A-Za-z_]\w*)\s*\)\s*AS\s*\?\1\s*\)\s*\.?', '', where_txt)
    # fix centrosymmetry as string triple
    where_txt = re.sub(
        r'\?m\s+ex:hasCentrosymmetric\s+(?:"false"|\'false\'|false)\s*\.\s*',
        '?m ex:hasCentrosymmetric ?centro .\n'
        'FILTER( BOUND(?centro) && ((datatype(?centro)=xsd:boolean && ?centro=false) || lcase(str(?centro))="false") )\n',
        where_txt, flags=re.IGNORECASE
    )
    # remove junk like ") AND ?m ex:hasBandGap ?bandgap)"
    where_txt = re.sub(r'\)\s*AND\s*\?m\s+ex:hasBandGap\s+\?bandgap\)\s*', '', where_txt, flags=re.IGNORECASE)

    # --- Anchor & binding policy (Bandgap KG)
    if " a ex:material" not in where_txt.lower():
        where_txt = "?m a ex:Material .\n" + where_txt

    def ensure_required(txt: str, pattern: str, var: str) -> str:
        req = f"?m ex:{pattern} ?{var} ."
        txt = re.sub(rf"OPTIONAL\s*\{{\s*\?m\s+ex:{pattern}\s+\?{var}\s*\}}\s*", "", txt, flags=re.IGNORECASE)
        if req not in txt:
            txt = req + "\n" + txt
        return txt

    def ensure_optional(txt: str, pattern: str, var: str) -> str:
        req = f"?m ex:{pattern} ?{var} ."
        if req in txt:
            return txt
        if f"ex:{pattern}".lower() not in txt.lower():
            txt += f"\nOPTIONAL {{ ?m ex:{pattern} ?{var} }}"
        return txt

    wl = where_txt.lower()
    uses_bg_filter   = ("bandgap" in wl) and ("filter" in wl)
    uses_centro_flt  = ("centro" in wl) and ("filter" in wl)
    uses_crys_flt    = ("crystal_system" in wl) and ("filter" in wl)

    # ALWAYS required for Bandgap KG:
    where_txt = ensure_required(where_txt, "hasFormula", "formula")
    where_txt = ensure_required(where_txt, "hasBandGap", "bandgap")

    # Conditional required/optional:
    where_txt = ensure_required(where_txt, "hasCentrosymmetric", "centro") if uses_centro_flt else ensure_optional(where_txt, "hasCentrosymmetric", "centro")
    where_txt = ensure_required(where_txt, "hasCrystalSystem", "crystal_system") if uses_crys_flt else ensure_optional(where_txt, "hasCrystalSystem", "crystal_system")

    # Soft extras
    if "rdfs:label" not in wl:
        where_txt += "\nOPTIONAL { ?m rdfs:label ?label }"
    if "ex:statedin" not in wl:
        where_txt += "\nOPTIONAL { ?m ex:statedIn ?source }"
        where_txt += "\nOPTIONAL { ?source rdfs:label ?source_label }"
        where_txt += "\nOPTIONAL { ?source ex:hasProvenanceId ?source_id }"
    if "ex:ingesttime" not in wl:
        where_txt += "\nOPTIONAL { ?m ex:ingestTime ?ingest_time }"
    if "ex:ingestindex" not in wl:
        where_txt += "\nOPTIONAL { ?m ex:ingestIndex ?ingest_idx }"

    # Robust guards
    where_txt = where_txt.replace(
        "FILTER(?centro = false)",
        'FILTER( BOUND(?centro) && ((datatype(?centro)=xsd:boolean && ?centro=false) || lcase(str(?centro))="false") )'
    )
    where_txt = where_txt.replace(
        "FILTER(xsd:float(?bandgap)", "FILTER( BOUND(?bandgap) && xsd:float(?bandgap)"
    ).replace(
        "FILTER(BOUND(xsd:float(?bandgap))", "FILTER( BOUND(?bandgap)"
    )

    head = SPARQL_PREFIX + "SELECT ?m ?label ?formula ?bandgap ?crystal_system ?centro ?source_label ?source_id\n"
    q_clean = f"{head}WHERE {{\n  {where_txt.strip()}\n}}\n"
    if tail_order:
        q_clean += "\n".join(tail_order) + "\n"
    return q_clean

def nl_to_sparql(question: str, model=None):
    model = model or _MODEL
    prompt = f"""{SPARQL_PREFIX}
# Question:
{question}
# Write a valid SPARQL SELECT:"""
    resp = ollama.chat(
        model=model,
        messages=[{"role":"system","content": NL2SPARQL_SYSTEM},
                  {"role":"user","content": prompt}],
        options={'temperature': 0, 'num_ctx': 1024}
    )
    q = resp['message']['content'].strip()
    if q.startswith("```"):
        q = q.strip("`").split("\n",1)[1]
    return sanitize_sparql(q)