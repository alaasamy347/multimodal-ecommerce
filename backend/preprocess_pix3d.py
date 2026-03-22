# """
# Fixed Pix3D Preprocessing Script
# This version properly handles image paths and creates correct mapping
# """
# import os
# import json
# import shutil
# from pathlib import Path
# from tqdm import tqdm
# from PIL import Image
# import numpy as np
# import faiss
# import torch
# from transformers import CLIPProcessor, CLIPModel

# # Color mapping helper
# BASIC_COLORS = {
#     "black": (0, 0, 0),
#     "white": (255, 255, 255),
#     "red": (255, 0, 0),
#     "green": (0, 128, 0),
#     "blue": (0, 0, 255),
#     "yellow": (255, 255, 0),
#     "brown": (150, 75, 0),
#     "gray": (128, 128, 128),
#     "orange": (255, 165, 0),
#     "pink": (255, 192, 203),
#     "purple": (128, 0, 128),
# }

# def rgb_to_basic_name(rgb):
#     """Convert RGB to nearest basic color name"""
#     if rgb is None:
#         return "unknown"
#     r, g, b = rgb
#     best = None
#     bd = 1e9
#     for name, c in BASIC_COLORS.items():
#         d = (r - c[0])**2 + (g - c[1])**2 + (b - c[2])**2
#         if d < bd:
#             bd = d
#             best = name
#     return best or "unknown"

# def extract_color_from_image(img):
#     """Extract dominant color from PIL Image"""
#     try:
#         # Resize for speed
#         img_small = img.resize((100, 100))
#         img_array = np.array(img_small.convert('RGB'))
        
#         # Get average color
#         avg_color = np.mean(img_array, axis=(0, 1))
#         return tuple(avg_color.astype(int))
#     except Exception as e:
#         print(f"⚠️ Color extraction failed: {e}")
#         return None

# # Paths
# PIX3D_ROOT = "data/pix3d"
# OUT_DATA_DIR = "data"
# OUT_IMAGES = os.path.join(OUT_DATA_DIR, "images")
# OUT_JSON = os.path.join(OUT_DATA_DIR, "clean_products.json")
# IMAGE_INDEX = os.path.join(OUT_DATA_DIR, "image_index.faiss")
# TEXT_INDEX = os.path.join(OUT_DATA_DIR, "text_index.faiss")
# ID_MAP = os.path.join(OUT_DATA_DIR, "id_map.npy")

# # Create output directories
# os.makedirs(OUT_IMAGES, exist_ok=True)
# os.makedirs(OUT_DATA_DIR, exist_ok=True)

# # Load Pix3D metadata
# metadata_path = None
# for cand in ["pix3d.json", "dataset.json", "metadata.json"]:
#     p = os.path.join(PIX3D_ROOT, cand)
#     if os.path.exists(p):
#         metadata_path = p
#         break

# if metadata_path is None:
#     raise SystemExit(f"❌ Cannot find Pix3D metadata in {PIX3D_ROOT}")

# print(f"📄 Loading metadata from: {metadata_path}")
# with open(metadata_path, "r", encoding="utf-8") as f:
#     items = json.load(f)

# print(f"📊 Found {len(items)} items in metadata")

# # Setup device and model
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print(f"🔧 Using device: {device}")

# print("🔧 Loading CLIP model...")
# clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
# clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
# clip_model.eval()

# # Storage for embeddings and metadata
# image_embeddings = []
# text_embeddings = []
# clean_products = []
# id_map_list = []

# print("\n" + "="*60)
# print("Processing images and generating embeddings...")
# print("="*60)

# counter = 0
# skipped = 0

# for it in tqdm(items, desc="Processing"):
#     # Get image path - try different keys
#     img_rel = it.get("img") or it.get("img_path") or it.get("img_file") or it.get("image")
#     category = it.get("category") or it.get("class") or "product"
    
#     if img_rel is None:
#         skipped += 1
#         continue
    
#     # Build full path to source image
#     # Handle both "img/bed/0001.png" and direct paths
#     if img_rel.startswith("img/"):
#         img_source_path = os.path.join(PIX3D_ROOT, img_rel)
#     else:
#         img_source_path = os.path.join(PIX3D_ROOT, "img", img_rel)
    
#     # Normalize path
#     img_source_path = os.path.normpath(img_source_path)
    
#     if not os.path.exists(img_source_path):
#         skipped += 1
#         if skipped <= 5:
#             print(f"\n⚠️ Missing: {img_source_path}")
#         continue
    
#     # Create organized output structure: images/category/filename.jpg
#     category_clean = category.lower().replace(" ", "_")
#     category_dir = os.path.join(OUT_IMAGES, category_clean)
#     os.makedirs(category_dir, exist_ok=True)
    
#     # Output filename: category/id.jpg
#     out_filename = f"{counter}.jpg"
#     out_path = os.path.join(category_dir, out_filename)
    
#     # Relative path for JSON (this is what will be stored)
#     # Format: "bed/0.jpg", "chair/1.jpg", etc.
#     image_relative_path = os.path.join(category_clean, out_filename)
#     # Normalize for cross-platform compatibility
#     image_relative_path = image_relative_path.replace("\\", "/")
    
#     try:
#         # Open and process image
#         img = Image.open(img_source_path).convert("RGB")
        
#         # Save to organized location
#         img.save(out_path, "JPEG", quality=95)
        
#         # Extract color
#         rgb = extract_color_from_image(img)
#         color_name = rgb_to_basic_name(rgb)
        
#         # Build product name
#         product_name = f"{color_name.capitalize()} {category.capitalize()}"
        
#         # Create product entry
#         product = {
#             "id": counter,
#             "productDisplayName": product_name,
#             "masterCategory": "Furniture",
#             "subCategory": category.capitalize(),
#             "baseColour": color_name,
#             "color": color_name,  # Add this for backward compatibility
#             "image_path": image_relative_path,  # e.g., "bed/0.jpg"
#             "source_img": img_rel,
#             "has_3d_model": False  # Will be updated by convert script
#         }
        
#         # Generate embeddings
#         # IMAGE embedding
#         img_inputs = clip_processor(
#             images=img,
#             return_tensors="pt"
#         ).to(device)
        
#         # TEXT embedding
#         text_inputs = clip_processor(
#             text=[product_name],
#             return_tensors="pt",
#             padding=True,
#             truncation=True,
#             max_length=77
#         ).to(device)
        
#         with torch.no_grad():
#             # Extract features
#             img_feat = clip_model.get_image_features(
#                 pixel_values=img_inputs['pixel_values']
#             )
            
#             txt_feat = clip_model.get_text_features(
#                 input_ids=text_inputs['input_ids'],
#                 attention_mask=text_inputs['attention_mask']
#             )
        
#         # Convert to numpy and normalize
#         img_feat = img_feat.cpu().numpy()
#         txt_feat = txt_feat.cpu().numpy()
        
#         # L2 normalization
#         img_feat = img_feat / np.linalg.norm(img_feat)
#         txt_feat = txt_feat / np.linalg.norm(txt_feat)
        
#         # Store
#         image_embeddings.append(img_feat)
#         text_embeddings.append(txt_feat)
#         clean_products.append(product)
#         id_map_list.append(counter)
        
#         counter += 1
        
#     except Exception as e:
#         print(f"\n❌ Error processing {img_source_path}: {e}")
#         # Clean up if needed
#         if os.path.exists(out_path):
#             os.remove(out_path)
#         skipped += 1
#         continue

# if skipped > 5:
#     print(f"\n⚠️ Skipped {skipped} items total")

# if len(image_embeddings) == 0:
#     raise SystemExit("❌ No images processed successfully!")

# print(f"\n✅ Successfully processed {counter} images")

# # Stack embeddings
# print("\n📊 Building embedding matrices...")
# image_matrix = np.vstack(image_embeddings).astype("float32")
# text_matrix = np.vstack(text_embeddings).astype("float32")

# print(f"   Image embeddings shape: {image_matrix.shape}")
# print(f"   Text embeddings shape: {text_matrix.shape}")

# # Build FAISS indexes
# print("\n🔍 Building FAISS indexes...")
# d = image_matrix.shape[1]

# img_index = faiss.IndexFlatIP(d)  # Inner product (cosine similarity for normalized vectors)
# txt_index = faiss.IndexFlatIP(d)

# img_index.add(image_matrix)
# txt_index.add(text_matrix)

# # Save everything
# print("\n💾 Saving files...")
# faiss.write_index(img_index, IMAGE_INDEX)
# faiss.write_index(txt_index, TEXT_INDEX)
# np.save(ID_MAP, np.array(id_map_list, dtype=np.int64))

# with open(OUT_JSON, "w", encoding="utf-8") as f:
#     json.dump(clean_products, f, indent=2, ensure_ascii=False)

# print("\n" + "="*60)
# print("✅ Preprocessing Complete!")
# print("="*60)
# print(f"📁 Products JSON: {OUT_JSON}")
# print(f"📁 Image Index:   {IMAGE_INDEX}")
# print(f"📁 Text Index:    {TEXT_INDEX}")
# print(f"📁 ID Map:        {ID_MAP}")
# print(f"📁 Images:        {OUT_IMAGES}")
# print(f"📊 Total indexed: {len(id_map_list)} items")
# print(f"📊 Categories:    {set(p['subCategory'] for p in clean_products)}")
# print(f"📊 Colors found:  {set(p['baseColour'] for p in clean_products)}")
# print("="*60)

# # Show structure
# print("\n📂 Output structure created:")
# print(f"   data/")
# print(f"   ├── clean_products.json")
# print(f"   ├── image_index.faiss")
# print(f"   ├── text_index.faiss")
# print(f"   ├── id_map.npy")
# print(f"   └── images/")
# categories = set(p['subCategory'].lower().replace(" ", "_") for p in clean_products)
# for cat in sorted(categories):
#     count = sum(1 for p in clean_products if p['subCategory'].lower().replace(" ", "_") == cat)
#     print(f"       ├── {cat}/ ({count} images)")

# print("\n📊 Sample products:")
# for p in clean_products[:5]:
#     print(f"   ID {p['id']}: {p['productDisplayName']} - {p['image_path']}")

# print("\n✅ Ready to upload to Kaggle!")
# print("\n📋 Next steps:")
# print("1. Run: python convert_pix3d_models.py (if you need 3D models)")
# print("2. Upload these files to Kaggle:")
# print("   - data/clean_products.json")
# print("   - data/image_index.faiss")
# print("   - data/text_index.faiss")
# print("   - data/id_map.npy")
# print("   - data/images/ (entire folder)")
# print("3. Update modal_app.py with your Kaggle dataset name")
# print("4. Deploy: modal deploy modal_app.py")

"""
Pix3D Preprocessing Script (AR-enabled)
- Generates CLIP embeddings
- Builds FAISS indexes
- Links images to GLB 3D models
"""

import os
import json
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import numpy as np
import faiss
import torch
from transformers import CLIPProcessor, CLIPModel

# =========================
# Color utilities
# =========================

BASIC_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "brown": (150, 75, 0),
    "gray": (128, 128, 128),
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "purple": (128, 0, 128),
}

def rgb_to_basic_name(rgb):
    if rgb is None:
        return "unknown"
    r, g, b = rgb
    best, best_dist = None, 1e9
    for name, c in BASIC_COLORS.items():
        d = (r - c[0])**2 + (g - c[1])**2 + (b - c[2])**2
        if d < best_dist:
            best_dist = d
            best = name
    return best or "unknown"

def extract_color_from_image(img):
    img_small = img.resize((100, 100))
    arr = np.array(img_small.convert("RGB"))
    return tuple(np.mean(arr, axis=(0, 1)).astype(int))

# =========================
# Paths
# =========================

PIX3D_ROOT = "data/pix3d"
PIX3D_GLB_ROOT = os.path.join(PIX3D_ROOT, "glb")

OUT_DIR = "data"
OUT_IMAGES = os.path.join(OUT_DIR, "images")
OUT_JSON = os.path.join(OUT_DIR, "clean_products.json")
IMAGE_INDEX = os.path.join(OUT_DIR, "image_index.faiss")
TEXT_INDEX = os.path.join(OUT_DIR, "text_index.faiss")
ID_MAP = os.path.join(OUT_DIR, "id_map.npy")

os.makedirs(OUT_IMAGES, exist_ok=True)

# =========================
# Load metadata
# =========================

metadata_path = os.path.join(PIX3D_ROOT, "pix3d.json")
if not os.path.exists(metadata_path):
    raise SystemExit("❌ pix3d.json not found")

with open(metadata_path, "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"📄 Loaded {len(items)} Pix3D entries")

# =========================
# CLIP setup
# =========================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
clip_model = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32"
).to(device).eval()
clip_processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32"
)

# =========================
# Storage
# =========================

image_embeddings = []
text_embeddings = []
products = []
id_map = []

counter = 0

# =========================
# Main loop
# =========================

for it in tqdm(items, desc="Processing Pix3D"):
    img_rel = it.get("img")
    category = it.get("category", "object").lower()

    if not img_rel:
        continue

    img_path = os.path.join(PIX3D_ROOT, img_rel)
    if not os.path.exists(img_path):
        continue

    # ---------- AR MODEL LINKING ----------
    model_rel = it.get("model")
    has_3d_model = False
    glb_path = None

    if model_rel:
        model_id = Path(model_rel).parts[-2]
        candidate_glb = os.path.join(
            PIX3D_GLB_ROOT,
            category,
            f"{model_id}.glb"
        )
        if os.path.exists(candidate_glb):
            has_3d_model = True
            glb_path = f"{category}/{model_id}.glb"

    # ---------- IMAGE SAVE ----------
    cat_dir = os.path.join(OUT_IMAGES, category)
    os.makedirs(cat_dir, exist_ok=True)

    out_img_name = f"{counter}.jpg"
    out_img_path = os.path.join(cat_dir, out_img_name)

    img = Image.open(img_path).convert("RGB")
    img.save(out_img_path, "JPEG", quality=95)

    # ---------- METADATA ----------
    rgb = extract_color_from_image(img)
    color = rgb_to_basic_name(rgb)
    product_name = f"{color.capitalize()} {category.capitalize()}"

    product = {
        "id": counter,
        "productDisplayName": product_name,
        "masterCategory": "Furniture",
        "subCategory": category.capitalize(),
        "baseColour": color,
        "image_path": f"{category}/{out_img_name}",
        "has_3d_model": has_3d_model,
        "glb_path": glb_path,
    }

    # ---------- EMBEDDINGS ----------
    img_inputs = clip_processor(images=img, return_tensors="pt").to(device)
    txt_inputs = clip_processor(
        text=[product_name],
        return_tensors="pt",
        padding=True
    ).to(device)

    with torch.no_grad():
        img_feat = clip_model.get_image_features(**img_inputs)
        txt_feat = clip_model.get_text_features(**txt_inputs)

    img_feat = img_feat.cpu().numpy()
    txt_feat = txt_feat.cpu().numpy()

    img_feat /= np.linalg.norm(img_feat)
    txt_feat /= np.linalg.norm(txt_feat)

    image_embeddings.append(img_feat)
    text_embeddings.append(txt_feat)
    products.append(product)
    id_map.append(counter)

    counter += 1

# =========================
# Save FAISS + JSON
# =========================

image_matrix = np.vstack(image_embeddings).astype("float32")
text_matrix = np.vstack(text_embeddings).astype("float32")

d = image_matrix.shape[1]
img_index = faiss.IndexFlatIP(d)
txt_index = faiss.IndexFlatIP(d)

img_index.add(image_matrix)
txt_index.add(text_matrix)

faiss.write_index(img_index, IMAGE_INDEX)
faiss.write_index(txt_index, TEXT_INDEX)
np.save(ID_MAP, np.array(id_map))

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2)

print("✅ Preprocessing complete")
print(f"📦 Products: {len(products)}")
print(f"🧊 With 3D models: {sum(p['has_3d_model'] for p in products)}")