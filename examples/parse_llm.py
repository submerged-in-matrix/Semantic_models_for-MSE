from parse.parse_multi_exe import parse_many_to_kg
from query.queryVia_formula import show_material

texts = [
    "Ga2O3N5Cl7 has a band gap around 4.8 eV and is monoclinic; it's centrosymmetric. materials_id: funny:001,",
    "Ga8O3N5Cl7 band gap ~1.34 eV; non-centrosymmetric & hexagonal; materials_id: funny:002,",
    "Ga5O33N5Cl7 has band gap ≈ 3.3 eV; is non-centrosymmetric & cubic; materials_id: funny:003,",
] 
df_summary = parse_many_to_kg(texts, start_idx=1_000_000, source_label="fabricated_demo")  
df_summary = df_summary.iloc[:, 4:-1]
df_summary.head()

# diagnosis via formula

show_material("Ga5O33N5Cl7")
show_material("Ga8O3N5Cl7")
show_material("Ga2O3N5Cl73") 