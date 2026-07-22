"""
Loads the generated JSONL dataset, splits into train/eval,
and saves both to disk for the training script to consume.

Run: python3 prepare_dataset.py
Requires: query_dataset.jsonl (from build_dataset.py)
Output: train_ds/, eval_ds/
"""

from datasets import load_dataset

dataset = load_dataset("json", data_files="query_dataset.jsonl", split="train")
print(dataset)
print(dataset[0])

dataset = dataset.train_test_split(test_size=0.1, seed=42)
train_ds = dataset["train"]
eval_ds = dataset["test"]
print(f"train: {len(train_ds)}, eval: {len(eval_ds)}")

train_ds.save_to_disk("train_ds")
eval_ds.save_to_disk("eval_ds")
