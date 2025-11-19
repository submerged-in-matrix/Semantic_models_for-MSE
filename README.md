# Mini Materials Knowledge Graph (LLM-assisted Ontology)

A short, beginner-friendly project to dive into **semantic modeling** for materials KG.


Built a tiny, end-to-end pipeline that:
1) defines a **small ontology** for semiconductors data,  
2) ingests a **tiny dataset** ,  
3) uses an **LLM (ollama)-assisted extractor from text files or random texts** to propose entities/relations,  
4) converts outputs into **RDF triples** (Linked Data),  
5) loads into a lightweight **triplestore** and runs a few **SPARQL** queries.



##  Stack 
- **Knowledge-graph**: `rdflib` for RDF generation, Regex for converting 'Straucture_Summary.tyt' to 'Pymatgen's Structure Object'
- **SPARQL**: `rdflib` SPARQL   
- **LLM parsing**: Chatgpt and OLLAMA tried. Ollama is used, chatgpt does not provide api access for a plus user as in my case.  
- **Validation**: simple checks for semantic consistency (domain/range sanity).

##  Planned Sub-domain Ideas
- MOFs
- Common semiconductors (used in this project)
- Alloys

 

##  Useful References (for later reading)
- MatVis (BAM-linked): https://github.com/Mat-O-Lab/MatVis  
- Propnet (Materials KG/inference): https://github.com/materialsintelligence/propnet  
- MatKG (materials KG from literature): https://www.nature.com/articles/s41597-024-03039-z and https://arxiv.org/abs/2210.17340  
- MKG via LLMs (2024): https://arxiv.org/abs/2404.03080  
- KG-FM (framework materials KG): https://www.nature.com/articles/s41524-025-01540-6  
- Semi-automated KG pipeline (2025): https://pubs.rsc.org/en/content/articlehtml/2025/dd/d4dd00362d
