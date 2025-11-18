from env.modules import *
from utils.sel_ollama import _pick_model
from utils.llm_schema import allowed_crystal_systems

_MODEL = _pick_model()
print("Using Ollama model:", _MODEL)

STRICT_SYSTEM = f"""
You are a materials KG assistant.
Return ONLY JSON with keys EXACTLY:
material, formula, material_id, crystal_system, is_centrosymmetric, band_gap_eV.
Rules:
- Required: (material OR formula) AND crystal_system AND is_centrosymmetric AND band_gap_eV
- material_id is OPTIONAL .
- crystal_system ∈ {allowed_crystal_systems}
- is_centrosymmetric → boolean (true/false; accept yes/no/centro/non-centro)
- band_gap_eV → single float (eV)
- If required fields are missing, return: {{"error":"Text not informative enough to add in KG"}}
"""

def _to_bool(x):
    if x is None: return None
    s = str(x).strip().lower()
    if s in {"true","yes","y","1","t"}: return True
    if s in {"false","no","n","0","f"}: return False
    if "non" in s and "centro" in s: return False
    if "centro" in s: return True
    return None

def _fetch_url_text(url: str, max_chars: int = 50000) -> str:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script","style","nav","footer","header","noscript"]): tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ").strip())
    return text[:max_chars]

def _fabricate_material_id(raw_text: str, formula: str | None, source_url: str | None) -> str:
    if source_url:
        return "url::" + hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:12]
    base = (formula or "") + "|" + raw_text[:2048]
    return "text::" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]

def _extract_material_id_from_text(text: str) -> str|None:
    import re
    m = re.search(r'\bmaterial[s]?_id\s*:\s*([^\s;,\)]+)', text, re.I)
    return m.group(1).strip() if m else None