# Bulk-ingest entire DataFrame into KG (silent)
from env.modules import *
from llm.ingest_from_txt import ingest_normalized_row
from llm.normalize import RowOut
from ontology.core import g
from utils.KG_dir import *
from parse.parse_multi_exe import df

def _get_str(x):
    return str(x).strip() if x is not None and str(x).strip() not in {"", "nan", "None"} else None

# --- 1) Ingest whole DataFrame (no per-row prints) ---
ingested = 0
for i, r in df.iterrows():
    nr = RowOut(
        material = _get_str(r.get("formula")) or _get_str(r.get("material_id")) or f"Material_{i}",
        formula  = _get_str(r.get("formula")),
        material_id = _get_str(r.get("material_id")),
        crystal_system = _get_str(r.get("crystal_system")),
        is_centrosymmetric = (bool(r["is_centrosymmetric"]) if pd.notna(r.get("is_centrosymmetric")) else None),
        band_gap_eV = (float(r["band_gap_eV"]) if pd.notna(r.get("band_gap_eV")) else None),
    )
    ingest_normalized_row(nr, idx=i)
    ingested += 1

# --- 3) Save lightweight interactive HTML view (limited edges for performance) ---
def _label(term):
    lab = g.value(term, RDFS.label)
    if lab: return str(lab)
    if isinstance(term, URIRef):
        try: return g.namespace_manager.normalizeUri(term)
        except: pass
        s=str(term); return s.rsplit("#",1)[-1].rsplit("/",1)[-1]
    return str(term)

def _nid(term):
    if isinstance(term, (URIRef, BNode)): return str(term)
    return f"lit:{hash((str(term), type(term).__name__))}"

def _style(term):
    types = set(g.objects(term, RDF.type)) if isinstance(term, (URIRef, BNode)) else set()
    def has(local): return any(str(t).endswith(f"#{local}") or str(t).endswith(f"/{local}") for t in types)
    if has("Material"):         return dict(color="#2b8a3e", shape="ellipse")
    if has("CrystalStructure"): return dict(color="#1c7ed6", shape="ellipse")
    if isinstance(term, Literal): return dict(color="#bfbfbf", shape="box")
    return dict(color="#666666", shape="ellipse")

def save_html_subset(g, out_html:str, max_edges:int=5000, show_literals:bool=False, height:str="800px"):
    net = Network(height=height, width="100%", directed=True, notebook=True, cdn_resources="in_line")
    net.toggle_physics(True)
    added=set(); edges=0
    for s,p,o in g.triples((None,None,None)):
        if edges>=max_edges: break
        if not show_literals and isinstance(o, Literal):
            continue
        sid=_nid(s); oid=_nid(o)
        if sid not in added:
            net.add_node(sid, label=_label(s), **_style(s)); added.add(sid)
        if show_literals or not isinstance(o, Literal):
            if oid not in added:
                net.add_node(oid, label=_label(o), **_style(o)); added.add(oid)
        pred = _label(p).replace("ex:","").replace("hasBandGap","band_gap_eV")\
                        .replace("hasCrystalSystem","crystal_system")\
                        .replace("hasCentrosymmetric","centrosymmetric")\
                        .replace("hasFormula","formula").replace("hasExternalId","material_id")
        net.add_edge(sid, oid, label=pred); edges+=1
    net.show(out_html)

HTML_PATH = OUT_DIR / "kg_full.html"
save_html_subset(g, str(HTML_PATH), max_edges=5000, show_literals=False)

# --- 4) Final single-line summary (no verbosity) ---
print(f"Ingested {ingested} rows → Triples: {len(g)} | Saved: {TTL_PATH.name}, {TTL_GZPATH.name}, {NT_PATH.name}, {HTML_PATH.name}")