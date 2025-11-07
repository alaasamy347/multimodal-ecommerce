import os
import json
import numpy as np
import faiss
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm

DATA_IMAGES_DIR = "data/images"
CLEAN_PRODUCTS_PATH = "data/clean_products.json"
IMAGE_INDEX_PATH = "data/image_index.faiss"
TEXT_INDEX_PATH = "data/text_index.faiss"
ID_MAP_PATH = "data/id_map.npy"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🔧 Using device: {device}")

print("🔄 Loading CLIP...")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model.eval()

print("📂 Loading metadata...")
with open(CLEAN_PRODUCTS_PATH, "r", encoding="utf-8") as f:
    products = json.load(f)

print(f"Found {len(products)} products in metadata")

img_embs, txt_embs, ids = [], [], []
skipped = 0

for p in tqdm(products, desc="Processing products"):
    pid = int(p["id"])
    img_path = os.path.join(DATA_IMAGES_DIR, p["image_path"])
    
    # Normalize path for Windows
    img_path = os.path.normpath(img_path)
    
    if not os.path.exists(img_path):
        skipped += 1
        if skipped <= 5:  # Only show first 5
            print(f"\n⚠️  Missing: {img_path}")
        continue

    try:
        image = Image.open(img_path).convert("RGB")
        text = p.get("productDisplayName", "furniture item")

        with torch.no_grad():
            img_inputs = clip_processor(images=image, return_tensors="pt").to(device)
            text_inputs = clip_processor(text=[text], return_tensors="pt", padding=True).to(device)

            img_feat = clip_model.get_image_features(**img_inputs)
            txt_feat = clip_model.get_text_features(**text_inputs)

        # Normalize
        img_feat /= img_feat.norm(dim=-1, keepdim=True)
        txt_feat /= txt_feat.norm(dim=-1, keepdim=True)

        img_embs.append(img_feat.cpu().numpy())
        txt_embs.append(txt_feat.cpu().numpy())
        ids.append(pid)
        
    except Exception as e:
        print(f"\n⚠️  Error processing {img_path}: {e}")
        skipped += 1
        continue

if skipped > 5:
    print(f"⚠️  ... and {skipped - 5} more skipped")

if len(img_embs) == 0:
    print("\n❌ No valid embeddings created! Check your image paths.")
    print(f"Expected images in: {os.path.abspath(DATA_IMAGES_DIR)}")
    exit(1)

print(f"\n✅ Successfully processed {len(img_embs)} products (skipped {skipped})")

print("💾 Creating FAISS indexes...")
img_matrix = np.vstack(img_embs).astype("float32")
txt_matrix = np.vstack(txt_embs).astype("float32")
id_map = np.array(ids)

print(f"  Image embeddings shape: {img_matrix.shape}")
print(f"  Text embeddings shape: {txt_matrix.shape}")

# Create and populate indexes
image_index = faiss.IndexFlatL2(img_matrix.shape[1])
text_index = faiss.IndexFlatL2(txt_matrix.shape[1])

image_index.add(img_matrix)
text_index.add(txt_matrix)

# Save indexes
faiss.write_index(image_index, IMAGE_INDEX_PATH)
faiss.write_index(text_index, TEXT_INDEX_PATH)
np.save(ID_MAP_PATH, id_map)

print("\n" + "="*60)
print("✅ Index building complete!")
print(f"💾 Image index: {IMAGE_INDEX_PATH}")
print(f"💾 Text index: {TEXT_INDEX_PATH}")
print(f"💾 ID map: {ID_MAP_PATH}")
print(f"📊 Total indexed: {len(ids)} products")
print("="*60)