"""
demos/kg_audit_demo.py — Audit what is actually in the Knowledge Graph.

Separates:
  - ontology scaffolding (class/property declarations)  vs. material data
  - the base dataset (CSV_base)                         vs. everything added later

Every material carries ex:hasSourceId, so the graph can be audited and
selectively rolled back without rebuilding it.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ontology.core import g
from utils.kg_audit import (kg_summary, list_sources, non_base_materials,
                            materials_by_source, find_duplicates, purge_source)

if len(g) < 1000:
    g.parse(ROOT / "data" / "mse_kg_full.ttl", format="turtle")

print("=" * 64)
print("1. GRAPH CENSUS")
print("=" * 64)
kg_summary()

print("\n" + "=" * 64)
print("2. SOURCES")
print("=" * 64)
print(list_sources().to_string(index=False))

print("\n" + "=" * 64)
print("3. MATERIALS NOT FROM THE BASE DATASET")
print("=" * 64)
extra = non_base_materials()
if extra.empty:
    print("None — graph contains only CSV_base materials.")
else:
    cols = [c for c in ["formula", "bandgap", "crystal_system",
                        "centro", "source_id", "ingest_idx"] if c in extra.columns]
    print(f"{len(extra)} material(s):\n")
    print(extra[cols].to_string(index=False))

print("\n" + "=" * 64)
print("4. MULTI-SOURCE MATERIALS (asserted by more than one source)")
print("=" * 64)
dups = find_duplicates()
print("None." if dups.empty else dups.to_string(index=False))

print("\n" + "=" * 64)
print("5. ROLLBACK PREVIEW (dry run — nothing is deleted)")
print("=" * 64)
if not extra.empty:
    for src in extra["source_id"].dropna().unique():
        purge_source(src, dry_run=True)
    print("\nTo commit a rollback:  purge_source('<source_id>', dry_run=False)")
else:
    print("Nothing to roll back.")
