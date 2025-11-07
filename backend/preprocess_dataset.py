# preprocess_dataset_binary.py
# =====================================================
# Preprocess dataset with CLIP (binary-safe version)
# =====================================================

# 👇 disable TensorFlow/XLA (we only want PyTorch here)
import os
os.environ["TRANSFORMERS_NO_TF"] = "1"

import json
import pandas as pd
from PIL import Image
import torch
from transformers import CLIPProcessor

# ==========================
# Settings
# ==========================
CSV_PATH = "data/styles.csv"
IMG_DIR = "data/images"
OUTPUT_JSON = "data/clean_products.json"   # metadata only
OUTPUT_TENSORS = "data/tensors.pt"         # binary tensors
BATCH_SIZE = 32

# ==========================
# Load dataset
# ==========================
print("Loading dataset...")
df = pd.read_csv(CSV_PATH, on_bad_lines="skip")
df = df.dropna(subset=["productDisplayName"]).reset_index(drop=True)

# ==========================
# Init processor + device
# ==========================
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)

# ==========================
# Preprocess in batches
# ==========================
metas = []
all_image_tensors = []
all_input_ids = []
all_attention_masks = []


def process_batch(batch_df):
    images, texts, batch_metas = [], [], []

    for _, row in batch_df.iterrows():
        img_path = os.path.join(IMG_DIR, f"{row['id']}.jpg")
        if not os.path.exists(img_path):
            continue
        try:
            img = Image.open(img_path).convert("RGB")
            images.append(img)
            texts.append(str(row["productDisplayName"]))
            batch_metas.append({
                "id": int(row["id"]),
                "productDisplayName": str(row["productDisplayName"]),
                "masterCategory": str(row.get("masterCategory", "")),
                "subCategory": str(row.get("subCategory", "")),
                "image_path": f"{row['id']}.jpg"
            })
        except Exception as e:
            print(f"Skipping {row['id']} due to error: {e}")
            continue

    if not images:
        return [], None

    inputs = processor(
        images=images,
        text=texts,
        return_tensors="pt",
        padding="max_length",  # 👈 pad to fixed length
        truncation=True,
        max_length=processor.tokenizer.model_max_length
    ).to(device)

    return batch_metas, inputs


print("Processing images in batches...")
for i in range(0, len(df), BATCH_SIZE):
    batch_df = df.iloc[i:i+BATCH_SIZE]
    batch_metas, inputs = process_batch(batch_df)

    if not batch_metas:
        continue

    metas.extend(batch_metas)
    all_image_tensors.append(inputs["pixel_values"].cpu())
    all_input_ids.append(inputs["input_ids"].cpu())
    all_attention_masks.append(inputs["attention_mask"].cpu())

    if i % 1000 == 0:
        print(f"Processed {i}/{len(df)} products...")

# ==========================
# Save results
# ==========================
os.makedirs("data", exist_ok=True)

# Save metadata (JSON)
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(metas, f, ensure_ascii=False, indent=2)

# Save tensors (binary .pt)
torch.save({
    "pixel_values": torch.cat(all_image_tensors, dim=0),
    "input_ids": torch.cat(all_input_ids, dim=0),
    "attention_mask": torch.cat(all_attention_masks, dim=0)
}, OUTPUT_TENSORS)

print(f"✅ Preprocessing complete! Saved {len(metas)} items.")
print(f"📄 Metadata: {OUTPUT_JSON}")
print(f"💾 Tensors: {OUTPUT_TENSORS}")
