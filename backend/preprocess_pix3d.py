# import os
# import json
# import torch
# import faiss
# import numpy as np
# from PIL import Image
# from tqdm import tqdm
# from transformers import CLIPProcessor, CLIPModel

# # ========== CONFIG ==========
# PIX3D_META_PATH = "data/pix3d/pix3d.json"
# PIX3D_ROOT = "data/pix3d"  # Root directory where pix3d images are
# OUTPUT_JSON = "data/clean_products.json"
# IMAGE_INDEX_PATH = "data/image_index.faiss"
# TEXT_INDEX_PATH = "data/text_index.faiss"
# ID_MAP_PATH = "data/id_map.npy"

# # Create symlink/copy images to expected location
# IMAGES_OUTPUT_DIR = "data/images"
# os.makedirs(IMAGES_OUTPUT_DIR, exist_ok=True)

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print("🔧 Using device:", device)

# # ========== LOAD CLIP ==========
# print("Loading CLIP model...")
# clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
# clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
# clip_model.eval()

# # ========== LOAD PIX3D METADATA ==========
# print("Loading Pix3D metadata...")
# with open(PIX3D_META_PATH, "r") as f:
#     data = json.load(f)

# print(f"Found {len(data)} items in pix3d.json")

# # ========== PROCESS ITEMS ==========
# products = []
# valid_count = 0
# missing_count = 0

# for i, item in enumerate(data):
#     # item["img"] is like "img/chair/0001.jpg"
#     # Full path should be: data/pix3d/img/chair/0001.jpg
    
#     img_relative = item["img"]  # e.g., "img/chair/0001.jpg"
#     img_full_path = os.path.join(PIX3D_ROOT, img_relative)
    
#     # Normalize path separators for Windows
#     img_full_path = os.path.normpath(img_full_path)
    
#     if not os.path.exists(img_full_path):
#         missing_count += 1
#         if missing_count <= 5:  # Only show first 5 missing files
#             print(f"⚠️  Missing: {img_full_path}")
#         continue
    
#     # Store relative path from IMAGES_OUTPUT_DIR for later use
#     # We'll copy/link images to data/images/ directory
#     category = item["category"]
#     img_filename = os.path.basename(img_relative)
    
#     # Create category subdirectory in images
#     category_dir = os.path.join(IMAGES_OUTPUT_DIR, category)
#     os.makedirs(category_dir, exist_ok=True)
    
#     # Output path: data/images/chair/0001.jpg
#     img_output_path = os.path.join(category_dir, img_filename)
#     img_relative_from_images = os.path.join(category, img_filename)
    
#     # Copy image to images directory if not exists
#     if not os.path.exists(img_output_path):
#         try:
#             import shutil
#             shutil.copy2(img_full_path, img_output_path)
#         except Exception as e:
#             print(f"⚠️  Failed to copy {img_full_path}: {e}")
#             continue
    
#     products.append({
#         "id": valid_count,  # Use sequential ID
#         "productDisplayName": f"{category} furniture",
#         "masterCategory": "Furniture",
#         "subCategory": category,
#         "image_path": img_relative_from_images,  # e.g., "chair/0001.jpg"
#         "model_path": item.get("model", ""),
#         "bbox": item.get("bbox", [])
#     })
    
#     valid_count += 1

# if missing_count > 5:
#     print(f"⚠️  ... and {missing_count - 5} more missing files")

# print(f"✅ Found {valid_count} valid items (skipped {missing_count} missing)")

# if valid_count == 0:
#     print("❌ No valid products found! Check your pix3d directory structure.")
#     print(f"Expected structure:")
#     print(f"  data/pix3d/")
#     print(f"    ├── pix3d.json")
#     print(f"    └── img/")
#     print(f"        ├── chair/")
#     print(f"        ├── table/")
#     print(f"        └── ...")
#     exit(1)

# # ========== BUILD EMBEDDINGS ==========
# def get_image_features(products_list):
#     features = []
#     valid_products = []
    
#     for p in tqdm(products_list, desc="Extracting image embeddings"):
#         img_path = os.path.join(IMAGES_OUTPUT_DIR, p["image_path"])
        
#         try:
#             image = Image.open(img_path).convert("RGB")
#             inputs = clip_processor(images=image, return_tensors="pt").to(device)
            
#             with torch.no_grad():
#                 emb = clip_model.get_image_features(**inputs)
            
#             emb = emb.cpu().numpy()
#             emb /= np.linalg.norm(emb)
            
#             features.append(emb[0])
#             valid_products.append(p)
            
#         except Exception as e:
#             print(f"⚠️  Error processing {img_path}: {e}")
#             continue
    
#     return np.array(features, dtype="float32"), valid_products

# def get_text_features(products_list):
#     features = []
    
#     for p in tqdm(products_list, desc="Extracting text embeddings"):
#         text = p["productDisplayName"]
        
#         inputs = clip_processor(text=[text], return_tensors="pt", padding=True).to(device)
        
#         with torch.no_grad():
#             emb = clip_model.get_text_features(**inputs)
        
#         emb = emb.cpu().numpy()
#         emb /= np.linalg.norm(emb)
#         features.append(emb[0])
    
#     return np.array(features, dtype="float32")

# # Extract features
# image_features, valid_products = get_image_features(products)

# if len(valid_products) == 0:
#     print("❌ No valid embeddings created!")
#     exit(1)

# # Update products list to only valid ones
# products = valid_products

# # Extract text features for valid products only
# text_features = get_text_features(products)

# # Create ID map
# id_map = np.array([p["id"] for p in products])

# # ========== SAVE INDEXES ==========
# print("Building FAISS indexes...")

# image_index = faiss.IndexFlatL2(image_features.shape[1])
# image_index.add(image_features)

# text_index = faiss.IndexFlatL2(text_features.shape[1])
# text_index.add(text_features)

# faiss.write_index(image_index, IMAGE_INDEX_PATH)
# faiss.write_index(text_index, TEXT_INDEX_PATH)
# np.save(ID_MAP_PATH, id_map)

# # Save products metadata
# with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
#     json.dump(products, f, indent=2)

# print("\n" + "="*60)
# print("✅ Preprocessing complete!")
# print(f"📦 Saved {len(products)} products to {OUTPUT_JSON}")
# print(f"📂 Images copied to {IMAGES_OUTPUT_DIR}")
# print(f"💾 Image index: {IMAGE_INDEX_PATH} ({image_features.shape})")
# print(f"💾 Text index: {TEXT_INDEX_PATH} ({text_features.shape})")
# print(f"💾 ID map: {ID_MAP_PATH} ({len(id_map)} items)")
# print("="*60)

# # Show sample products
# print("\n📊 Sample products:")
# for p in products[:3]:
#     print(f"  ID {p['id']}: {p['productDisplayName']} ({p['subCategory']}) - {p['image_path']}")



import os
import json
import shutil
import numpy as np
import torch
import faiss
from PIL import Image
from tqdm import tqdm
from transformers import CLIPProcessor, CLIPModel

# --- Configuration Constants ---
PIX3D_ROOT = "data/pix3d"
OUT_IMAGES = "data/images"
OUT_JSON = "data/clean_products.json"
IMAGE_INDEX = "data/image_index.faiss"
TEXT_INDEX = "data/text_index.faiss"
ID_MAP = "data/id_map.npy"

# Ensure the output image directory exists
os.makedirs(OUT_IMAGES, exist_ok=True)

# --- 1. Load CLIP Model ---
print("📦 Loading CLIP...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
model.eval()

# --- 2. Load Pix3D Metadata ---
# FIX: Adjusted path to account for common Pix3D data structure (PIX3D_ROOT/data/pix3d.json)
metadata_path = os.path.join(PIX3D_ROOT,"pix3d.json")
print(f"Loading metadata from: {metadata_path}")
with open(metadata_path) as f:
    pix_data = json.load(f)

clean_products = []
image_embeddings = []
text_embeddings = []
id_map = []

# --- 3. Process Data and Compute Embeddings ---
for idx, item in enumerate(tqdm(pix_data)):
    # The 'img' path in the metadata is relative to PIX3D_ROOT
    img_path = os.path.join(PIX3D_ROOT, item["img"])
    if not os.path.exists(img_path):
        continue

    # Copy image to your data/images directory
    new_img_path = f"{idx}.jpg"
    shutil.copy(img_path, f"{OUT_IMAGES}/{new_img_path}")

    # Build product entry
    prod = {
        "id": idx,
        "productDisplayName": item.get("category", "Unknown"),
        "masterCategory": item.get("category", ""),
        "subCategory": item.get("category", ""),
        "image_path": new_img_path,
        "description": f"{item.get('category', 'object')} in Pix3D dataset"
    }
    clean_products.append(prod)

    # Load image and process inputs
    img = Image.open(img_path).convert("RGB")
    inputs = processor(images=img, text=[prod["productDisplayName"]], return_tensors="pt", padding=True).to(device)

    # FIX: Separate inputs for image and text feature extraction
    image_inputs = {
        "pixel_values": inputs["pixel_values"]
    }
    text_inputs = {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"]
    }

    with torch.no_grad():
        # Compute image embedding
        img_emb = model.get_image_features(**image_inputs)
        # Compute text embedding
        txt_emb = model.get_text_features(**text_inputs)

    img_emb = img_emb.cpu().numpy()
    txt_emb = txt_emb.cpu().numpy()

    image_embeddings.append(img_emb)
    text_embeddings.append(txt_emb)
    id_map.append(idx)

# --- 4. Prepare and Normalize Embeddings ---
# Convert to arrays
image_embeddings = np.vstack(image_embeddings)
text_embeddings = np.vstack(text_embeddings)
id_map = np.array(id_map)

# Normalize embeddings (essential for distance metrics like L2/dot product)
image_embeddings /= np.linalg.norm(image_embeddings, axis=1, keepdims=True)
text_embeddings /= np.linalg.norm(text_embeddings, axis=1, keepdims=True)

# --- 5. Build FAISS Indexes and Save ---
print("🔍 Building FAISS index...")

dim = image_embeddings.shape[1]

# Use IndexFlatL2 for L2 (Euclidean) distance lookup
img_index = faiss.IndexFlatL2(dim)
txt_index = faiss.IndexFlatL2(dim)

img_index.add(image_embeddings)
txt_index.add(text_embeddings)

# Save the indexes and map
faiss.write_index(img_index, IMAGE_INDEX)
faiss.write_index(txt_index, TEXT_INDEX)
np.save(ID_MAP, id_map)

# Save the product metadata JSON
with open(OUT_JSON, "w") as f:
    json.dump(clean_products, f, indent=2)

print("✅ Pix3D preprocessing complete!")