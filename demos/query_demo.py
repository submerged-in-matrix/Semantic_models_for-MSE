import time
from pathlib import Path
import sys, os

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["OLLAMA_HOST"] = "http://172.18.20.199:11434"

from ontology.core import g
from query.exe_query import ask_kg

t0 = time.perf_counter()
g.parse(ROOT / "data" / "mse_kg_full.ttl", format="turtle")
print(f"Triples: {len(g)}  (load {time.perf_counter()-t0:.1f}s)")

print(ask_kg("Show materials with a cubic crystal system and a band gap between 1 eV and 2 eV", n=5))