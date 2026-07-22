"""
Loads the trained query LoRA adapter and evaluates it against the
held-out eval set: checks (1) does the generated SPARQL actually
parse (syntactic validity via rdflib), and (2) how closely it
matches the gold query structurally.

Run: python3 eval_query_lora.py
"""

import json
from unsloth import FastLanguageModel
from datasets import load_from_disk
from rdflib.plugins.sparql import prepareQuery
import re

#  To avoid white spacing in SPARQL
def loose_normalize(q):
    # only fix missing space before '?' when it directly follows a word char,
    # and don't touch anything inside angle-bracket IRIs
    parts = re.split(r'(<[^>]*>)', q)  # split out IRIs, leave them untouched
    for i in range(0, len(parts), 2):  # even indices = non-IRI text
        parts[i] = re.sub(r'(?<=[A-Za-z0-9_\)\}])\?', ' ?', parts[i])
    return ''.join(parts)

# --- load base model + trained adapter together ---
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="query_lora_adapter",   # loads base + adapter, since this dir was saved via model.save_pretrained
    max_seq_length=1024,
    load_in_4bit=True,
)
FastLanguageModel.for_inference(model)  # enables Unsloth's faster inference path

eval_ds = load_from_disk("eval_ds")

results = []
for row in eval_ds:
    system_msg, user_msg, gold_msg = row["messages"]
    prompt = tokenizer.apply_chat_template(
        [system_msg, user_msg],
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    out = model.generate(**inputs, max_new_tokens=400, temperature=0.0, do_sample=False)
    generated = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    gold_sparql = gold_msg["content"]

    parses = True
    parse_error = None
    try:
        prepareQuery(loose_normalize(generated))
    except Exception as e:
        parses = False
        parse_error = str(e)

    results.append({
        "question": user_msg["content"],
        "generated": generated,
        "gold": gold_sparql,
        "parses": parses,
        "parse_error": parse_error,
        "exact_match": generated.strip() == gold_sparql.strip(),
    })

# --- summary ---
n = len(results)
n_parse = sum(r["parses"] for r in results)
n_exact = sum(r["exact_match"] for r in results)

print(f"\n=== EVAL SUMMARY ({n} examples) ===")
print(f"Syntactically valid SPARQL: {n_parse}/{n}  ({100*n_parse/n:.0f}%)")
print(f"Exact text match to gold:   {n_exact}/{n}  ({100*n_exact/n:.0f}%)")

print("\n=== PER-EXAMPLE DETAIL ===")
for r in results:
    status = "PARSE_OK " if r["parses"] else "PARSE_FAIL"
    print(f"\n[{status}] Q: {r['question']}")
    print(f"  Generated:\n{r['generated'][:300]}")
    if not r["parses"]:
        print(f"  Error: {r['parse_error']}")

with open("eval_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved full results to eval_results.json")
