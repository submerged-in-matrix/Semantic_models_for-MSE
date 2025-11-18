from env.modules import *
    
def _extract_where_body(q: str) -> str:
        # kill code fences
        q = q.strip()
        if q.startswith("```"):
            q = q.strip("`").split("\n", 1)[1].strip()

        # remove PREFIX lines
        lines = [ln for ln in q.splitlines() if not ln.strip().lower().startswith("prefix")]
        q = "\n".join(lines)

        # pull the chunk inside the outermost WHERE { ... }
        if "WHERE" not in q:
            return ""
        after_where = q.split("WHERE", 1)[1]
        lb = after_where.find("{")
        rb = after_where.rfind("}")
        body = after_where[lb+1:rb].strip() if (lb >= 0 and rb >= 0) else ""

        # drop any trailing ORDER/LIMIT the LLM might’ve put inside the body
        body = re.sub(r'(?is)\bORDER\s+BY\b.*$', '', body).strip()
        body = re.sub(r'(?is)\bLIMIT\s+\d+\s*$', '', body).strip()
        return body
    
