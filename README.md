# Mini Materials Knowledge Graph (LLM-assisted Ontology)

A short, beginner-friendly project to demonstrate **semantic modeling** skills that transfer directly to BAM’s role on ontologies and semantic interoperability.

## 🎯 Goal
Build a tiny, end-to-end pipeline that:
1) defines a **small ontology** for a narrow materials sub-domain,  
2) ingests a **tiny dataset** (abstracts or tabular snippets),  
3) uses an **LLM-assisted extractor** to propose entities/relations,  
4) converts outputs into **RDF triples** (Linked Data),  
5) loads into a lightweight **triplestore** and runs a few **SPARQL** queries.

 Target skill: ontology design, semantic consistency, FAIR/linked data, and LLM support—

## 🧭 Roadmap (minimal scope)
- [ ] **Ontology**: start with 6–10 classes (e.g., `Material`, `SynthesisMethod`, `Property`, `Publication`) and 10–20 relations (e.g., `hasProperty`, `synthesizedBy`, `measuredIn`).
- [ ] **Sample data**: a handful of abstracts or 1–2 CSV tables.
- [ ] **LLM-assisted parsing**: prototype prompts/rules to extract (subject, predicate, object) candidates.
- [ ] **RDF conversion**: map to a namespace, produce `.ttl` or `.rdf`.
- [ ] **Queries**: run 3–5 SPARQL queries that demonstrate retrieval & simple reasoning (e.g., “materials synthesized via solvothermal with band gap > X”).
- [ ] **(Optional)** Basic visualization (screenshot or simple graph view).

> Keep it tiny and clean. Depth over breadth.

## 🛠️  Stack (flexible)
- **Python**: `rdflib` for RDF generation.  
- **SPARQL**: `rdflib` SPARQL in-notebook or a local triplestore (e.g., GraphDB Free, QLever Docker, or Apache Jena/Fuseki).  
- **LLM parsing**: Chatgpt and OLLAMA tried. Ollama is used, chatgpt does not provide api access for a plus user as in my case.  
- **Validation**: simple checks for semantic consistency (domain/range sanity).

## 📦 Minimal Setup
```bash
# after cloning
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install rdflib pandas
# (Optional for local store) GraphDB/Jena/QLever via Docker if desired
```

## 🔍 Planned Sub-domain Ideas
- MOFs 101 (very small set)  
- Common semiconductors (Si, GaAs, perovskites)  
- Alloys (Fe-based) with 2–3 properties (e.g., density, hardness, band gap if relevant)  



## 🧪 Notebook
All code will live in: `notebooks/build_mini_mkg.ipynb` 

 

## 📚 Useful References (for later reading)
- MatVis (BAM-linked): https://github.com/Mat-O-Lab/MatVis  
- Propnet (Materials KG/inference): https://github.com/materialsintelligence/propnet  
- MatKG (materials KG from literature): https://www.nature.com/articles/s41597-024-03039-z and https://arxiv.org/abs/2210.17340  
- MKG via LLMs (2024): https://arxiv.org/abs/2404.03080  
- KG-FM (framework materials KG): https://www.nature.com/articles/s41524-025-01540-6  
- Semi-automated KG pipeline (2025): https://pubs.rsc.org/en/content/articlehtml/2025/dd/d4dd00362d


**Author**: Md. Saidul Islam  
**Intent**: Demonstrate semantic modeling & ontology skills relevant to BAM (B8/2266).  
