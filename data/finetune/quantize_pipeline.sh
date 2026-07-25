#!/bin/bash
set -e  # stop on first error

REPO=/workspace/Semantic_models_for-MSE
LLAMA_CPP=$REPO/llama.cpp
FT=$REPO/data/finetune

# ---- 1. Build llama.cpp quantize + imatrix binaries (skips if already built) ----
cd "$LLAMA_CPP"
cmake -B build
cmake --build build --config Release -j"$(nproc)" --target llama-quantize llama-imatrix

# ---- 2. Extract calibration text from training data (chat "content" fields only) ----
cd "$FT"
python3 -c "
import json
with open('query_dataset.jsonl') as f, open('calib_query.txt', 'w') as out:
    for line in f:
        ex = json.loads(line)
        for msg in ex['messages']:
            out.write(msg['content'] + '\n\n')
"
python3 -c "
import json
with open('parse_dataset.jsonl') as f, open('calib_parse.txt', 'w') as out:
    for line in f:
        ex = json.loads(line)
        for msg in ex['messages']:
            out.write(msg['content'] + '\n\n')
"
echo "Calibration files:"
wc -l calib_query.txt calib_parse.txt

# ---- 3. Generate importance matrices (per model, using its own domain data) ----
"$LLAMA_CPP"/build/bin/llama-imatrix \
  -m "$FT"/query_merged.gguf \
  -f "$FT"/calib_query.txt \
  -o "$FT"/query_imatrix.dat \
  --gpu-layers 99

"$LLAMA_CPP"/build/bin/llama-imatrix \
  -m "$FT"/parse_merged.gguf \
  -f "$FT"/calib_parse.txt \
  -o "$FT"/parse_imatrix.dat \
  --gpu-layers 99

# ---- 4. Quantize both models using their imatrix (Q4_K_M) ----
"$LLAMA_CPP"/build/bin/llama-quantize \
  --imatrix "$FT"/query_imatrix.dat \
  "$FT"/query_merged.gguf \
  "$FT"/query_merged.Q4_K_M.gguf \
  Q4_K_M

"$LLAMA_CPP"/build/bin/llama-quantize \
  --imatrix "$FT"/parse_imatrix.dat \
  "$FT"/parse_merged.gguf \
  "$FT"/parse_merged.Q4_K_M.gguf \
  Q4_K_M

echo "Done. Quantized files:"
ls -la "$FT"/*.Q4_K_M.gguf