from env.modules import *
from utils.sel_ollama import _available_ollama_models, OLLAMA_OPTIONS , OLLAMA_MODEL_CANDIDATES
from utils.llm_schema import *
from llm.llm_def import _fetch_url_text, _MODEL, STRICT_SYSTEM, _to_bool, _fabricate_material_id, _extract_material_id_from_text

def normalize_row_with_ollama(input_obj: dict, model: str|None=None) -> RowOut:
    
    # accept plain strings too
    if isinstance(input_obj, str):
        input_obj = {"text": input_obj}

    model = model or _MODEL
    source_url = input_obj.get("url")
    raw_text = _fetch_url_text(source_url) if source_url else str(input_obj.get("text",""))
    payload  = {"text": raw_text, "source_url": source_url} if source_url else input_obj

    # try the chosen model once; if it 404s, pick another available; do not loop forever
    tried = set()
    while True:
        try:
            resp = ollama.chat(
                model=model,
                messages=[{"role":"system","content": STRICT_SYSTEM},
                          {"role":"user","content": f"Extract to schema from: {json.dumps(payload)[:49000]}"}],
                format='json',
                options=OLLAMA_OPTIONS
            )
            data = json.loads(resp['message']['content'])
        except Exception as e:
            tried.add(model)
            # choose another available model
            avail = [m for m in _available_ollama_models() if m not in tried]
            model = next((m for m in OLLAMA_MODEL_CANDIDATES if m in avail), None)
            if not model:
                raise RuntimeError("Ollama call failed and no viable model remains.") from e
            continue


        if isinstance(data, dict) and data.get("error"):
            raise ValueError("Text not informative enough to add in KG")

        data["is_centrosymmetric"] = _to_bool(data.get("is_centrosymmetric"))
        # validate requireds
        material_ok = bool(str(data.get("material","")).strip())
        formula_ok  = bool(str(data.get("formula","")).strip())
        cs_ok       = bool(str(data.get("crystal_system","")).strip())
        centro_ok   = data.get("is_centrosymmetric") in (True, False)
        try:
            data["band_gap_eV"] = float(data["band_gap_eV"])
            bg_ok = True
        except Exception:
            bg_ok = False

        if not ((material_ok or formula_ok) and cs_ok and centro_ok and bg_ok):
            raise ValueError("Text not informative enough to add in KG")
        
        # If caller provided {"text": "..."} use it for id extraction / fabrication
        raw_text = raw_text or source_url.get("text") if isinstance(raw_text or source_url, dict) else None
        source_url = raw_text or source_url.get("url") if isinstance(raw_text or source_url, dict) else None
        
        hinted_id = _extract_material_id_from_text(raw_text or source_url or "")
        if hinted_id:
            data["material_id"] = hinted_id

        # fabricate if still missing
        if not str(data.get("material_id", "")).strip():
            data["material_id"] = _fabricate_material_id(raw_text or source_url or "", data.get("formula"), source_url)

        return RowOut(**data)