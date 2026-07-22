"""
Generates a JSONL fine-tuning dataset for the extraction task
(normalize_row_with_ollama / STRICT_SYSTEM in the pipeline).

Each line: {"messages": [system, user, assistant]}
- system    = exact STRICT_SYSTEM prompt used in production
- user      = raw text describing a material
- assistant = the correct JSON the model should output

Includes both:
  - well-formed examples (all required fields present -> valid JSON)
  - rejection examples (a required field missing -> {"error": "..."})

Run: python3 build_parse_dataset.py
Output: parse_dataset.jsonl
"""

import json
import random

random.seed(7)

ALLOWED_CRYSTAL_SYSTEMS = ["cubic", "hexagonal", "monoclinic", "orthorhombic",
                           "tetragonal", "triclinic", "trigonal"]

STRICT_SYSTEM = f"""
You are a materials KG assistant.
Return ONLY JSON with keys EXACTLY:
material, formula, material_id, crystal_system, is_centrosymmetric, band_gap_eV.
Rules:
- Required: (material OR formula) AND crystal_system AND is_centrosymmetric AND band_gap_eV
- material_id is OPTIONAL .
- crystal_system ∈ {ALLOWED_CRYSTAL_SYSTEMS}
- is_centrosymmetric → boolean (true/false; accept yes/no/centro/non-centro)
- band_gap_eV → single float (eV)
- If required fields are missing, return: {{"error":"Text not informative enough to add in KG"}}
"""

MATERIALS = [
    ("GaN", "wurtzite"), ("ZnO", None), ("InP", "zinc blende"),
    ("SiC", None), ("AlN", None), ("Ga2O3", "beta-phase"),
    ("CdS", None), ("BN", "hexagonal-BN"), ("MgO", None),
    ("TiO2", "rutile"), ("SnO2", None), ("BaTiO3", "perovskite"),
]

BANDGAP_PHRASES = [
    "band gap around {x} eV",
    "band gap ~{x} eV",
    "band gap of {x} eV",
    "Eg ~ {x} eV",
    "Eg = {x} eV",
    "a {x} eV band gap",
    "bandgap {x}eV",
]

CENTRO_TRUE_PHRASES = [
    "it's centrosymmetric",
    "is centrosymmetric",
    "has an inversion center",
    "centrosymmetric structure",
]
CENTRO_FALSE_PHRASES = [
    "it's non-centrosymmetric",
    "is non-centrosymmetric",
    "lacks an inversion center",
    "non-centrosymmetric structure",
]

CRYSTAL_PHRASES = [
    "is {cs}",
    "has a {cs} crystal structure",
    "crystallizes in the {cs} system",
    "({cs})",
]

examples = []


def add(text, target):
    examples.append((text, target))


# A) Well-formed examples
for formula, structure_name in MATERIALS:
    for _ in range(4):
        bg = round(random.uniform(0.3, 5.0), 2)
        cs = random.choice(ALLOWED_CRYSTAL_SYSTEMS)
        centro = random.choice([True, False])
        has_material_id = random.random() < 0.4

        bg_phrase = random.choice(BANDGAP_PHRASES).format(x=bg)
        cs_phrase = random.choice(CRYSTAL_PHRASES).format(cs=cs)
        centro_phrase = random.choice(CENTRO_TRUE_PHRASES if centro else CENTRO_FALSE_PHRASES)

        clauses = [f"{formula} has a {bg_phrase}", cs_phrase, centro_phrase]
        random.shuffle(clauses)
        text = "; ".join(clauses) + "."

        material_id = None
        if has_material_id:
            material_id = f"funny:{random.randint(100,999)}"
            text += f" materials_id: {material_id},"

        target = {
            "material": formula,
            "formula": formula,
            "material_id": material_id,
            "crystal_system": cs,
            "is_centrosymmetric": centro,
            "band_gap_eV": bg,
        }
        add(text, target)

# B) Messier / abstract-style
abstract_templates = [
    "In this work we report {formula}, a {cs} semiconductor with {bg_phrase}. "
    "Structural analysis confirms the material {centro_phrase}.",

    "{formula} was synthesized and characterized; the compound {centro_phrase} and "
    "crystallizes in the {cs} phase, exhibiting {bg_phrase}.",

    "We measured {bg_phrase} for {formula}, consistent with its {cs} structure. "
    "The material {centro_phrase}.",
]
for formula, structure_name in MATERIALS:
    bg = round(random.uniform(0.3, 5.0), 2)
    cs = random.choice(ALLOWED_CRYSTAL_SYSTEMS)
    centro = random.choice([True, False])
    bg_phrase = random.choice(BANDGAP_PHRASES).format(x=bg)
    centro_phrase = random.choice(CENTRO_TRUE_PHRASES if centro else CENTRO_FALSE_PHRASES)

    text = random.choice(abstract_templates).format(
        formula=formula, cs=cs, bg_phrase=bg_phrase, centro_phrase=centro_phrase
    )
    target = {
        "material": formula,
        "formula": formula,
        "material_id": None,
        "crystal_system": cs,
        "is_centrosymmetric": centro,
        "band_gap_eV": bg,
    }
    add(text, target)

# C) Rejection cases
ERROR_TARGET = {"error": "Text not informative enough to add in KG"}

# missing band gap (crystal_system + centro present, no band gap)
missing_bg_phrases = [
    "{formula} is {cs} and {centro_phrase}.",
    "{formula} {centro_phrase}; is {cs}.",
]
for formula, _ in MATERIALS:
    cs = random.choice(ALLOWED_CRYSTAL_SYSTEMS)
    centro_phrase = random.choice(CENTRO_TRUE_PHRASES + CENTRO_FALSE_PHRASES)
    for phr in missing_bg_phrases:
        text = phr.format(formula=formula, cs=cs, centro_phrase=centro_phrase)
        add(text, ERROR_TARGET)

# missing crystal system (band gap + centro present, no crystal system)
missing_cs_phrases = [
    "{formula} has a {bg_phrase} and {centro_phrase}.",
    "{formula} {centro_phrase}, with {bg_phrase}.",
]
for formula, _ in MATERIALS:
    bg = round(random.uniform(0.3, 5.0), 2)
    bg_phrase = random.choice(BANDGAP_PHRASES).format(x=bg)
    centro_phrase = random.choice(CENTRO_TRUE_PHRASES + CENTRO_FALSE_PHRASES)
    for phr in missing_cs_phrases:
        text = phr.format(formula=formula, bg_phrase=bg_phrase, centro_phrase=centro_phrase)
        add(text, ERROR_TARGET)

# missing centrosymmetry info (band gap + crystal system present, no centro)
missing_centro_phrases = [
    "{formula} has a {bg_phrase} and is {cs}.",
    "{formula} is {cs} with {bg_phrase}.",
]
for formula, _ in MATERIALS:
    bg = round(random.uniform(0.3, 5.0), 2)
    cs = random.choice(ALLOWED_CRYSTAL_SYSTEMS)
    bg_phrase = random.choice(BANDGAP_PHRASES).format(x=bg)
    for phr in missing_centro_phrases:
        text = phr.format(formula=formula, bg_phrase=bg_phrase, cs=cs)
        add(text, ERROR_TARGET)

vague_texts = [
    "This material looks interesting for future study.",
    "We plan to investigate this compound further next year.",
    "The sample was stored at room temperature before analysis.",
    "Further characterization is needed to confirm these properties.",
]
for t in vague_texts:
    add(t, ERROR_TARGET)

random.shuffle(examples)

with open("parse_dataset.jsonl", "w") as f:
    for text, target in examples:
        row = {
            "messages": [
                {"role": "system", "content": STRICT_SYSTEM.strip()},
                {"role": "user", "content": f"Extract to schema from: {json.dumps({'text': text})}"},
                {"role": "assistant", "content": json.dumps(target)},
            ]
        }
        f.write(json.dumps(row) + "\n")

n_ok = sum(1 for _, t in examples if "error" not in t)
n_err = sum(1 for _, t in examples if "error" in t)
print(f"Wrote {len(examples)} examples to parse_dataset.jsonl ({n_ok} valid, {n_err} rejection)")
