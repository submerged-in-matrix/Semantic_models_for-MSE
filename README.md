# Mini Materials Knowledge Graph (LLM-assisted Ontology)

A short, beginner-friendly project to demonstrate **semantic modeling** skills that transfer directly to BAM’s role on ontologies and semantic interoperability.

> Job context: Postdoctoral Research Associate – Development and Application of Ontologies and Semantic Models (BAM)  
> Link (provided by user): https://www.bam.de/umantis/DE/2266.html

## 🎯 Goal
Build a tiny, end-to-end pipeline that:
1) defines a **small ontology** for a narrow materials sub-domain,  
2) ingests a **tiny dataset** (abstracts or tabular snippets),  
3) uses an **LLM-assisted extractor** to propose entities/relations,  
4) converts outputs into **RDF triples** (Linked Data),  
5) loads into a lightweight **triplestore** and runs a few **SPARQL** queries.

This showcases: ontology design, semantic consistency, FAIR/linked data, and LLM support—core themes of the BAM role.

## 🧭 Roadmap (minimal scope)
- [ ] **Ontology**: start with 6–10 classes (e.g., `Material`, `SynthesisMethod`, `Property`, `Publication`) and 10–20 relations (e.g., `hasProperty`, `synthesizedBy`, `measuredIn`).
- [ ] **Sample data**: a handful of abstracts or 1–2 CSV tables.
- [ ] **LLM-assisted parsing**: prototype prompts/rules to extract (subject, predicate, object) candidates.
- [ ] **RDF conversion**: map to a namespace, produce `.ttl` or `.rdf`.
- [ ] **Queries**: run 3–5 SPARQL queries that demonstrate retrieval & simple reasoning (e.g., “materials synthesized via solvothermal with band gap > X”).
- [ ] **(Optional)** Basic visualization (screenshot or simple graph view).

> Keep it tiny and clean. Depth over breadth.

## 🛠️ Suggested Stack (flexible)
- **Python**: `rdflib` for RDF generation.  
- **SPARQL**: `rdflib` SPARQL in-notebook or a local triplestore (e.g., GraphDB Free, QLever Docker, or Apache Jena/Fuseki).  
- **LLM parsing**: placeholder functions; you can swap any provider/API later.  
- **Validation**: simple checks for semantic consistency (domain/range sanity).

## 📦 Minimal Setup
```bash
# after cloning
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install rdflib pandas
# (Optional for local store) GraphDB/Jena/QLever via Docker if desired
```

## 🔍 Suggested Sub-domain Ideas
- MOFs 101 (very small set)  
- Common semiconductors (Si, GaAs, perovskites)  
- Alloys (Fe-based) with 2–3 properties (e.g., density, hardness, band gap if relevant)  

Pick **one** and keep it tiny (5–10 materials total).

## 🧪 Notebook
All code will live in: `notebooks/build_mini_mkg.ipynb` (currently empty; you will code inside).

## 🧩 How this maps to BAM requirements
- **Ontology & semantic consistency** → define classes/relations, domain/range checks.  
- **Semantic interoperability** → RDF + namespaces + SPARQL.  
- **New technologies (LLMs)** → LLM-assisted entity/relation suggestion.  
- **Documentation & training** → this README and clear, reproducible steps.  

## 📚 Useful References (for later reading)
- MatVis (BAM-linked): https://github.com/Mat-O-Lab/MatVis  
- Propnet (Materials KG/inference): https://github.com/materialsintelligence/propnet  
- MatKG (materials KG from literature): https://www.nature.com/articles/s41597-024-03039-z and https://arxiv.org/abs/2210.17340  
- MKG via LLMs (2024): https://arxiv.org/abs/2404.03080  
- KG-FM (framework materials KG): https://www.nature.com/articles/s41524-025-01540-6  
- Semi-automated KG pipeline (2025): https://pubs.rsc.org/en/content/articlehtml/2025/dd/d4dd00362d

> Keep the repo minimal now. We’ll structure `src/`, `data/`, `docs/` later if needed.

## 🚀 Get Started (when ready)
```bash
# initialize repo (local)
git init
git add README.md notebooks/build_mini_mkg.ipynb
git commit -m "init: mini MKG (LLM-assisted ontology)"
# create a remote on GitHub first, then:
git branch -M main
git remote add origin <your_repo_url>
git push -u origin main
```

---

**Author**: Md. Saidul Islam  
**Intent**: Demonstrate semantic modeling & ontology skills relevant to BAM (B8/2266).  
