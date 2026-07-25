from datasets import load_dataset

dataset = load_dataset("json", data_files="parse_dataset.jsonl", split="train")
dataset = dataset.train_test_split(test_size=0.15, seed=7)
train_ds = dataset["train"]
eval_ds = dataset["test"]
print(f"train: {len(train_ds)}, eval: {len(eval_ds)}")

train_ds.save_to_disk("train_ds_parse")
eval_ds.save_to_disk("eval_ds_parse")
