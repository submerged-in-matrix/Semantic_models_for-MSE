import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# ---- CONFIGURATION/PER RUN ----
BASE_MODEL = "unsloth/Llama-3.2-3B-Instruct"
ADAPTER_PATH = "parse_lora_adapter"      # change to parse_lora_adapter/query_lora_adapter based on what to merge
OUTPUT_PATH = "parse_merged_merged"             # change to parse_merged/query_merged based on what to merge
# ----------------------------------

print(f"Loading base model: {BASE_MODEL}")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map="cuda",
)
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

print(f"Loading adapter: {ADAPTER_PATH}")
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)

print("Merging adapter into base weights...")
merged_model = model.merge_and_unload()

print(f"Saving merged model to {OUTPUT_PATH}")
merged_model.save_pretrained(OUTPUT_PATH, safe_serialization=True)
tokenizer.save_pretrained(OUTPUT_PATH)

print("Done.")