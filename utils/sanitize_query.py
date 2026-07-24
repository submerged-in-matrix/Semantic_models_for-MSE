"""
sanitize_query.py — Clean and simplify model-generated SPARQL for the MSE Knowledge Graph.

KEY CHANGE: actively STRIPS OPTIONAL blocks the KG no longer supports.
The fine-tuned model still emits ?label / ?source_label / ingest* OPTIONALs because
its training data (and NL2SPARQL_SYSTEM) told it to. We cannot retrain right now, so
the symbolic layer enforces the contract instead.
"""

from env.modules import *
from query.query_rules import *
from utils.sel_ollama import QUERY_MODEL

_CMP = r'(>=|<=|!=|>|<|=)'

# Predicates removed from the KG — any pattern referencing these is deleted.
_DROP_PREDICATES = [
    'rdfs:label',
    'ex:statedIn',
    'ex:hasProvenanceId',
    'ex:ingestTime',
    'ex:ingestIndex',
]


def _fix_filter_parens(q: str) -> str:
    """Repair mis-nested parens in model FILTER lines. No-op if already balanced."""
    import re
    out = []
    for line in q.split("\n"):
        if line.strip().upper().startswith("FILTER"):
            diff = line.count("(") - line.count(")")
            while diff < 0:
                new = re.sub(r'\)\)\s*' + _CMP, r') \1', line, count=1)
                if new == line:
                    break
                line, diff = new, diff + 1
            if diff > 0:
                line = line.rstrip() + ")" * diff
            elif diff < 0:
                for _ in range(-diff):
                    i = line.rfind(")")
                    if i != -1:
                        line = line[:i] + line[i + 1:]
        out.append(line)
    return "\n".join(out)


def sanitize_sparql(q: str) -> str:
    import re

    q = q.strip()
    if q.startswith("```"):
        q = q.strip("`").split("\n", 1)[1].strip()

    if "PREFIX ex:" not in q:
        q = SPARQL_PREFIX.strip() + "\n" + q

    # 1. Keep only WHERE-body lines; ORDER/LIMIT tail discarded (ask_kg owns those)
    where_lines = []
    for ln in (l.strip() for l in q.splitlines() if l.strip()):
        low = ln.lower()
        if low.startswith(("prefix", "select", "order by", "limit")):
            continue
        if low.startswith(("where {", "optional", "filter", "bind", "values", "}")) \
           or "?m " in ln or " ex:" in ln or ln.startswith("?"):
            where_lines.append(ln)

    where_txt = "\n".join(where_lines)
    where_txt = where_txt.replace("WHERE {", "").replace("{", "").replace("}", "")

    # 2. Restore OPTIONAL braces stripped above
    where_txt = re.sub(r'(?im)^[ \t]*OPTIONAL\s+(?!\{)(.+?)\s*\.?\s*$',
                       r'OPTIONAL { \1 }', where_txt)

    # 3. Repair model paren bugs
    where_txt = _fix_filter_parens(where_txt)

    # 4. STRIP unsupported patterns  <-- THE CRITICAL FIX
    for pred in _DROP_PREDICATES:
        # OPTIONAL blocks referencing a dropped predicate
        where_txt = re.sub(
            r'(?im)^[ \t]*OPTIONAL\s*\{[^}]*' + re.escape(pred) + r'[^}]*\}[ \t]*\.?[ \t]*$\n?',
            '', where_txt)
        # bare triples using a dropped predicate
        where_txt = re.sub(
            r'(?im)^[ \t]*\?\w+\s+' + re.escape(pred) + r'\s+\?\w+\s*\.?[ \t]*$\n?',
            '', where_txt)

    # 5. Remove known junk patterns
    where_txt = re.sub(r'FILTER\s*\(\s*BIND\s*\([^)]+\)[^)]*\)\s*\.?', '',
                       where_txt, flags=re.IGNORECASE)
    where_txt = re.sub(r'BIND\s*\(\s*[a-zA-Z0-9_:]+\s*\(\s*\?([A-Za-z_]\w*)\s*\)\s*AS\s*\?\1\s*\)\s*\.?',
                       '', where_txt)
    where_txt = re.sub(r'\)\s*AND\s*\?m\s+ex:hasBandGap\s+\?bandgap\)\s*', '',
                       where_txt, flags=re.IGNORECASE)

    # 6. Centro literal triple -> variable + simple FILTER
    for val in ("false", "true"):
        where_txt = re.sub(
            rf'\?m\s+ex:hasCentrosymmetric\s+(?:"{val}"|\'{val}\'|{val})\s*\.\s*',
            f'?m ex:hasCentrosymmetric ?centro .\nFILTER(?centro = {val})\n',
            where_txt, flags=re.IGNORECASE)

    # 7. Simplify FILTERs: drop BOUND guards, xsd:float casts, lcase/str calls
    where_txt = re.sub(
        r'FILTER\s*\(\s*BOUND\s*\(\s*\?bandgap\s*\)\s*&&\s*xsd:float\s*\(\s*\?bandgap\s*\)\s*'
        r'(>=?|<=?)\s*([0-9.]+)\s*&&\s*xsd:float\s*\(\s*\?bandgap\s*\)\s*(>=?|<=?)\s*([0-9.]+)\s*\)',
        r'FILTER(?bandgap \1 \2 && ?bandgap \3 \4)', where_txt, flags=re.IGNORECASE)
    where_txt = re.sub(
        r'FILTER\s*\(\s*BOUND\s*\(\s*\?bandgap\s*\)\s*&&\s*xsd:float\s*\(\s*\?bandgap\s*\)\s*'
        r'(>=?|<=?|!=|=)\s*([0-9.]+)\s*\)',
        r'FILTER(?bandgap \1 \2)', where_txt, flags=re.IGNORECASE)
    where_txt = re.sub(r'xsd:float\s*\(\s*\?bandgap\s*\)', '?bandgap',
                       where_txt, flags=re.IGNORECASE)
    where_txt = re.sub(r'lcase\s*\(\s*str\s*\(\s*\?crystal_system\s*\)\s*\)', '?crystal_system',
                       where_txt, flags=re.IGNORECASE)
    where_txt = re.sub(r'FILTER\s*\(\s*BOUND\s*\(\s*\?centro\s*\)\s*&&\s*\(\(.*?\)\)\s*\)',
                       'FILTER(?centro = false)', where_txt,
                       flags=re.IGNORECASE | re.DOTALL)

    # 8. Anchor to Material
    if " a ex:material" not in where_txt.lower():
        where_txt = "?m a ex:Material .\n" + where_txt

    # 9. Dedup identical lines, drop blanks
    seen, deduped = set(), []
    for line in where_txt.split("\n"):
        s = line.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        deduped.append(s)
    where_txt = "\n".join(deduped)

    # 10. All five properties are mandatory now -> zero OPTIONALs in the final query
    def ensure_required(txt: str, pattern: str, var: str) -> str:
        req = f"?m ex:{pattern} ?{var} ."
        txt = re.sub(rf"OPTIONAL\s*\{{\s*\?m\s+ex:{pattern}\s+\?{var}\s*\}}\s*", "",
                     txt, flags=re.IGNORECASE)
        if req not in txt:
            txt = req + "\n" + txt
        return txt

    for pat, var in [("hasFormula", "formula"),
                     ("hasBandGap", "bandgap"),
                     ("hasCrystalSystem", "crystal_system"),
                     ("hasCentrosymmetric", "centro"),
                     ("hasSourceId", "source_id")]:
        where_txt = ensure_required(where_txt, pat, var)

    # 11. Assemble
    head = SPARQL_PREFIX + "SELECT ?m ?formula ?bandgap ?crystal_system ?centro ?source_id\n"
    return f"{head}WHERE {{\n  {where_txt.strip()}\n}}\n"


def nl_to_sparql(question: str, model=None):
    model = model or QUERY_MODEL
    prompt = f"""{SPARQL_PREFIX}
# Question:
{question}
# Write a valid SPARQL SELECT:"""
    resp = ollama.chat(
        model=model,
        messages=[{"role": "system", "content": NL2SPARQL_SYSTEM},
                  {"role": "user",   "content": prompt}],
        options={'temperature': 0, 'num_ctx': 1024}
    )
    q = resp['message']['content'].strip()
    if q.startswith("```"):
        q = q.strip("`").split("\n", 1)[1]
    return sanitize_sparql(q)
