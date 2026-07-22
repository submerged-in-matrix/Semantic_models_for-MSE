<div align="center">

# 🔬 Semantic Models for Materials Science & Engineering

**A Neuro-Symbolic Pipeline: LLM-Wired Knowledge Graph for Semiconductor Band-Gap Data**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-96.5%25-3776AB?logo=python&logoColor=white)](.)
[![LLM](https://img.shields.io/badge/LLM-Llama_3.2_3B-orange)](.)
[![RDF](https://img.shields.io/badge/Linked_Data-RDF%2FSPARQL-blue)](.)

</div>

---

## The Problem

Materials science is drowning in disconnected data. Band-gap values live in CSVs. Crystal structures live in CIF files. Composition metadata lives in API responses. Literature findings live in PDFs. Each source uses its own schema, its own naming conventions, its own units. Having a single, queryable source of truth — where one can ask *"Give me all cubic, centrosymmetric materials with a band gap between 1.0 and 2.0 eV"* and get a provenance-tracked answer spanning structured databases, featurized datasets, and unstructured text — is increasingly important for reproducibility and automation in data-driven materials research.

**This project is a working prototype of that idea.**

## What This Is

A complete neuro-symbolic pipeline that combines a **hand-designed RDF ontology** with **LLM-assisted ingestion and querying** to create a queryable knowledge graph of semiconductor band-gap data. The graph can be queried directly via **SPARQL** or through **natural language** (LLM-translated to SPARQL). The system has two modes:

### Mode 1 — LLM-Assisted Ingestion (Primary)

Feed the system raw text — a URL, a PDF, a fabricated paragraph, a lab notebook snippet — and a local **Llama 3.2 (3B)** model extracts material entities and relationships, deduplicates them against the existing graph, normalizes types, and produces clean RDF triples ready for ingestion. No manual triple-writing required.

```
Raw Text / URL / PDF  →  LLM extraction  →  Deduplication & Sanitization  →  Typed RDF Triples  →  KG
```

### Mode 2 — Natural Language Querying (Secondary)

Ask a question in plain English. The same LLM translates it into an executable **SPARQL** query, runs it against the triplestore, and returns structured results. Guardrails prevent malformed or semantically invalid queries from reaching the graph.

```
"Which cubic materials have band gaps above 1.5 eV?"  →  LLM  →  SPARQL  →  Results
```

## The Ontology

The RDF schema connects materials to their measurable and structural properties through five core relationships:

```
                    ┌─── hasBandGap ──────→  xsd:float (eV)
                    │
                    ├─── hasCrystalSystem ─→  xsd:string
                    │
    mse:Material ───┼─── hasCentrosymmetry → xsd:boolean
                    │
                    ├─── hasComposition ───→  xsd:string
                    │
                    └─── hasSource ────────→  xsd:string (provenance)
```

This is deliberately minimal — the point is a clean, extensible foundation, not a monolithic ontology. Every triple carries provenance metadata, making it possible to trace any fact back to its origin (Materials Project API, featurized CSV, LLM-extracted text, etc.).

## Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                          │
│  Materials Project API  ·  CSVs  ·  PDFs  ·  Raw text/URLs  │
└──────────────┬───────────────────────────────┬───────────────┘
               │                               │
               ▼                               ▼
    ┌─────────────────────┐        ┌───────────────────────┐
    │   Structured Ingest │        │   LLM-Assisted Ingest │
    │   (parse/)          │        │   (llm/ + parse/)     │
    │                     │        │                       │
    │  CSV → Pymatgen     │        │  NL text → Llama 3.2  │
    │  Structure Object   │        │  → entity extraction   │
    │  → typed RDF        │        │  → dedup & sanitize    │
    │  triples            │        │  → typed RDF triples   │
    └────────┬────────────┘        └───────────┬───────────┘
             │                                 │
             └────────────┬────────────────────┘
                          ▼
              ┌───────────────────────┐
              │   RDF Knowledge Graph │
              │   (kg/)               │
              │                       │
              │   rdflib triplestore  │
              │   + provenance meta   │
              │   + domain/range      │
              │     validation        │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Query Interface     │
              │   (query/)            │
              │                       │
              │   NL → SPARQL (LLM)   │
              │   + guardrails        │
              │   + typed row         │
              │     normalization     │
              └───────────────────────┘
```

## Key Design Decisions

**Why a local 3B model?** Running Llama 3.2 (3B) via Ollama means no API costs, no data leaving the machine, and reproducible results. It's deliberately lightweight — proving that one don't need GPT-4 to build a functional NL→KG pipeline for a constrained domain.

**Why RDF and not a property graph (Neo4j)?** RDF triples are the native language of scientific linked data. They compose naturally with existing materials ontologies (MatOnto, EMMO, ChEBI), support federated SPARQL queries across institutions, and enforce schema constraints through domain/range validation. This is a bet on interoperability.

**Why provenance as a first-class property?** Every triple tracks its source. When three different sources disagree on a band gap value, one needs to know which came from DFT calculations, which from experiment, and which was LLM-extracted from a paper abstract. Without provenance, a KG is just a database with extra steps.

**Why guardrailed NL→SPARQL?** Raw LLM-generated SPARQL is unreliable. The pipeline validates generated queries against the ontology schema before execution — checking that properties exist, types match, and the query structure is semantically valid. Malformed queries are caught and re-prompted, not silently executed.

## Repository Structure

```
Semantic_models_for-MSE/
├── ontology/          # RDF schema definition — the backbone
├── kg/                # Knowledge graph construction & triplestore management
├── llm/               # LLM integration (Ollama / Llama 3.2:3b)
│                        — NL→triples extraction
│                        — NL→SPARQL translation
├── parse/             # Data parsers
│                        — CSV → Pymatgen Structure → RDF
│                        — Structure_Summary.txt → regex → Structure Object
├── query/             # SPARQL query engine with guardrails
├── data/              # Source datasets (Materials Project band-gap data)
├── demos/             # ⭐ End-to-end demos — start here to see the KG in action
├── examples/          # Example queries and ingestion runs
├── notebooks/         # Jupyter notebooks for exploration
├── utils/             # Shared utilities
├── env/               # Environment configuration
├── export             # KG export utilities
└── README.md
```

## See It In Action

The [`demos/`](demos/) folder contains end-to-end walkthroughs showing everything the KG can do — structured ingestion, LLM-assisted triple extraction from raw text, SPARQL querying, and natural-language querying. Start there for a hands-on overview before diving into individual modules.

## Tech Stack

| Component | Technology |
|---|---|
| **Knowledge Graph** | `rdflib` — RDF triple generation, storage, SPARQL execution |
| **LLM** | Llama 3.2 (3B) via Ollama (local, no API keys) |
| **Parsing** | Regex + Pymatgen for crystal structure conversion |
| **Validation** | Domain/range semantic consistency checks |
| **Data Source** | Materials Project (via `mp-api`) |
| **Visualization** | JavaScript (3.5% of codebase) |

## Planned Extensions

| Domain | Status |
|---|---|
| Common Semiconductors | ✅ Current |
| Metal-Organic Frameworks (MOFs) | 🔜 Planned |
| Alloys | 🔜 Planned |

## Related Work & References

This project sits in a growing ecosystem of materials knowledge graphs and LLM-assisted scientific data tools:

- **MatVis** (BAM) — [github.com/Mat-O-Lab/MatVis](https://github.com/Mat-O-Lab/MatVis)
- **Propnet** — materials KG with property inference — [github.com/materialsintelligence/propnet](https://github.com/materialsintelligence/propnet)
- **MatKG** — KG from materials literature — [Nature Scientific Data (2024)](https://www.nature.com/articles/s41597-024-03039-z) · [arXiv:2210.17340](https://arxiv.org/abs/2210.17340)
- **MKG via LLMs** (2024) — [arXiv:2404.03080](https://arxiv.org/abs/2404.03080)
- **KG-FM** — framework materials KG — [Nature Comp. Materials (2025)](https://www.nature.com/articles/s41524-025-01540-6)
- **Semi-automated KG pipeline** (2025) — [RSC Digital Discovery](https://pubs.rsc.org/en/content/articlehtml/2025/dd/d4dd00362d)

---

<div align="center">

📬 sayeed.shahriar@gmail.com · [Portfolio](https://submerged-in-matrix.github.io/projects/semantic-models/) · [GitHub](https://github.com/submerged-in-matrix)

</div>
