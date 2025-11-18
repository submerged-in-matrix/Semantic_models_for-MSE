from env.modules import *

OLLAMA_MODEL_CANDIDATES = [
    'llama3.2:1b', 'llama3.2:1b-instruct',
    'llama3.2:3b-instruct-q4_0', 'llama3.2:3b-q4_0', 'llama3.2:3b'
]
OLLAMA_OPTIONS = {'temperature': 0, 'num_ctx': 1024, 'num_batch': 16}

def _available_ollama_models():
    try:
        info = ollama.list()
        return {m['model'] for m in info.get('models', [])}
    except Exception:
        return set()

def _pick_model():
    have = _available_ollama_models()
    for m in OLLAMA_MODEL_CANDIDATES:
        if m in have:
            try:
                ollama.chat(model=m, messages=[{"role":"user","content":"ping"}],
                            options={'num_ctx':128,'temperature':0})
                return m
            except Exception:
                continue
    raise RuntimeError(
        "No suitable local Ollama model found. Pull one of:\n  "
        + "\n  ".join(OLLAMA_MODEL_CANDIDATES)
        + "\nExample:\n  ollama pull llama3.2:1b"
    )