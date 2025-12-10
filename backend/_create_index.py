# create_index_binary.py
import os, json
import numpy as np
import torch
import faiss
from transformers import CLIPModel

# Paths
DATA_DIR = "data"
PRODUCTS_JSON = os.path.join(DATA_DIR, "clean_products.json")
TENSORS_PATH = os.path.join(DATA_DIR, "tensors.pt")

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)

# Load metadata + tensors
with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
    products = json.load(f)
tensors = torch.load(TENSORS_PATH)

pixel_values = tensors["pixel_values"].to(device)
input_ids = tensors["input_ids"].to(device)
attention_mask = tensors["attention_mask"].to(device)

# Generate embeddings in batches
def get_embeddings():
    image_embs, text_embs = [], []
    batch_size = 64
    with torch.no_grad():
        for i in range(0, pixel_values.shape[0], batch_size):
            imgs = pixel_values[i:i+batch_size]
            ids = input_ids[i:i+batch_size]
            mask = attention_mask[i:i+batch_size]

            img_feat = model.get_image_features(pixel_values=imgs)
            txt_feat = model.get_text_features(input_ids=ids, attention_mask=mask)

            # Normalize
            img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
            txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)

            image_embs.append(img_feat.cpu().numpy())
            text_embs.append(txt_feat.cpu().numpy())

    return np.vstack(image_embs).astype("float32"), np.vstack(text_embs).astype("float32")

print("Computing embeddings...")
image_embeddings, text_embeddings = get_embeddings()

# Save FAISS indexes
d = image_embeddings.shape[1]
index_img = faiss.IndexFlatIP(d)
index_txt = faiss.IndexFlatIP(d)
index_img.add(image_embeddings)
index_txt.add(text_embeddings)

faiss.write_index(index_img, os.path.join(DATA_DIR, "image_index.faiss"))
faiss.write_index(index_txt, os.path.join(DATA_DIR, "text_index.faiss"))

# Save ID map
np.save(os.path.join(DATA_DIR, "id_map.npy"), np.array([p["id"] for p in products]))

print("✅ Saved indexes to data/image_index.faiss, data/text_index.faiss, and data/id_map.npy")
