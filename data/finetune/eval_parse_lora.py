"""
Evaluates the trained parsing LoRA adapter against the held-out eval set:
checks (1) valid JSON output, (2) correct schema keys, (3) per-field
correctness against gold, and (4) whether rejection cases are correctly
flagged as errors.
"""

import json
from unsloth import FastLanguageModel
from datasets import load_from_disk

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="parse_lora_adapter",
    max_seq_length=1024,
    load_in_4bit=True,
)
FastLanguageModel.for_inference(model)

eval_ds = load_from_disk("eval_ds_parse")
REQUIRED_KEYS = {"material", "formula", "material_id", "crystal_system",
                  "is_centrosymmetric", "band_gap_eV"}

results = []
for row in eval_ds:
    system_msg, user_msg, gold_msg = row["messages"]
    prompt = tokenizer.apply_chat_template(
        [system_msg, user_msg], tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    out = model.generate(**inputs, max_new_tokens=200, temperature=0.0, do_sample=False)
    generated = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    gold = json.loads(gold_msg["content"])
    gold_is_error = "error" in gold

    valid_json = True
    gen_parsed = None
    try:
        gen_parsed = json.loads(generated)
    except Exception:
        valid_json = False

    gen_is_error = valid_json and "error" in gen_parsed
    correct_keys = valid_json and not gen_is_error and set(gen_parsed.keys()) == REQUIRED_KEYS
    error_case_correct = gold_is_error and gen_is_error
    fields_match = None
    if valid_json and not gold_is_error and not gen_is_error and correct_keys:
        fields_match = {k: (gen_parsed.get(k) == gold.get(k)) for k in REQUIRED_KEYS}

    results.append({
        "text": user_msg["content"][:150],
        "generated": generated,
        "gold": gold,
        "valid_json": valid_json,
        "gold_is_error": gold_is_error,
        "gen_is_error": gen_is_error,
        "correct_keys": correct_keys,
        "fields_match": fields_match,
    })

n = len(results)
n_valid_json = sum(r["valid_json"] for r in results)
n_error_cases = sum(r["gold_is_error"] for r in results)
n_error_correct = sum(r["gold_is_error"] and r["gen_is_error"] for r in results)
n_valid_cases = sum(not r["gold_is_error"] for r in results)
n_keys_correct = sum((not r["gold_is_error"]) and r["correct_keys"] for r in results)

print(f"\n=== EVAL SUMMARY ({n} examples) ===")
print(f"Valid JSON output:              {n_valid_json}/{n}")
print(f"Rejection cases correctly flagged: {n_error_correct}/{n_error_cases}")
print(f"Valid cases with correct schema keys: {n_keys_correct}/{n_valid_cases}")

for r in results:
    if r["fields_match"]:
        wrong = [k for k, ok in r["fields_match"].items() if not ok]
        if wrong:
            print(f"\nFIELD MISMATCH on: {r['text']}")
            print(f"  wrong fields: {wrong}")
            print(f"  generated: {r['generated']}")
            print(f"  gold: {r['gold']}")

with open("eval_results_parse.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved full results to eval_results_parse.json")
