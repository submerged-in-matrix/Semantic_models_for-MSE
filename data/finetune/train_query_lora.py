from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from datasets import load_from_disk
from trl import SFTTrainer, SFTConfig
import json

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.2-3B-Instruct",
    max_seq_length=1024,
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=16,
    lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

train_ds = load_from_disk("train_ds")
eval_ds = load_from_disk("eval_ds")

def formatting_func(examples):
    texts = [
        tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
        for msgs in examples["messages"]
    ]
    return {"text": texts}

train_ds = train_ds.map(formatting_func, batched=True)
eval_ds = eval_ds.map(formatting_func, batched=True)

print("SAMPLE FORMATTED TEXT:\n", train_ds[0]["text"][:800])

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_ds,
    eval_dataset=eval_ds,
    dataset_text_field="text",
    max_seq_length=1024,
    args=SFTConfig(
        output_dir="outputs",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        warmup_steps=5,
        logging_steps=1,
        optim="adamw_8bit",
        eval_strategy="epoch",
        save_strategy="epoch",
        seed=3407,
        report_to="none",
    ),
)

trainer = train_on_responses_only(
    trainer,
    instruction_part="<|start_header_id|>user<|end_header_id|>\n\n",
    response_part="<|start_header_id|>assistant<|end_header_id|>\n\n",
)

trainer_stats = trainer.train()
print(trainer_stats)
with open("training_log_query.json", "w") as f:
    json.dump(trainer.state.log_history, f, indent=2)
print("Saved training log to training_log_query.json")

model.save_pretrained("query_lora_adapter")
tokenizer.save_pretrained("query_lora_adapter")
print("Saved adapter to query_lora_adapter/")
