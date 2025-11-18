    # Guarantee OPTIONAL projection bindings exist (cheap safety)
def _ensure_optional_block(txt: str, triple: str) -> str:
        # if triple is not present, add OPTIONAL {...}
        if triple not in txt:
            return txt + f"  OPTIONAL {{ {triple} }}\n"
        return txt
