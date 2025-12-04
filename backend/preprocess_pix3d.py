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



# scripts/preprocess_pix3d.py
import os
import json
import shutil
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import numpy as np
import faiss
import torch
from transformers import CLIPProcessor, CLIPModel

# Optional: for color quantization
try:
    from colorthief import ColorThief
    COLOR_THIEF_AVAILABLE = True
except Exception:
    COLOR_THIEF_AVAILABLE = False

# small helper to map rgb -> nearest basic color name
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
    best = None
    bd = 1e9
    for name, c in BASIC_COLORS.items():
        d = (r - c[0])**2 + (g - c[1])**2 + (b - c[2])**2
        if d < bd:
            bd = d
            best = name
    return best or "unknown"

# Paths - put PIX3D root where you extracted dataset
PIX3D_ROOT = "data/pix3d"  # update if needed (folder with images and metadata)
OUT_DATA_DIR = "data"
OUT_IMAGES = os.path.join(OUT_DATA_DIR, "images")
OUT_JSON = os.path.join(OUT_DATA_DIR, "clean_products.json")
IMAGE_INDEX = os.path.join(OUT_DATA_DIR, "image_index.faiss")
TEXT_INDEX = os.path.join(OUT_DATA_DIR, "text_index.faiss")
ID_MAP = os.path.join(OUT_DATA_DIR, "id_map.npy")

os.makedirs(OUT_IMAGES, exist_ok=True)
os.makedirs(OUT_DATA_DIR, exist_ok=True)

# Load Pix3D metadata file if exists (common filenames: pix3d.json, dataset.json)
metadata_path = None
for cand in ["pix3d.json", "dataset.json", "metadata.json"]:
    p = os.path.join(PIX3D_ROOT, cand)
    if os.path.exists(p):
        metadata_path = p
        break
if metadata_path is None:
    raise SystemExit(f"Cannot find Pix3D metadata in {PIX3D_ROOT}. Place pix3d.json or equivalent in root.")

with open(metadata_path, "r", encoding="utf-8") as f:
    items = json.load(f)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

print("Loading CLIP model...")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model.eval()

image_embeddings = []
text_embeddings = []
clean_products = []
id_map = []

def build_product_name(category, color, idx):
    """Build descriptive product name with color"""
    category_name = category.capitalize()
    if color and color != "unknown":
        return f"{color.capitalize()} {category_name}"
    return f"{category_name}"

print("Processing dataset and computing embeddings...")
counter = 0
for it in tqdm(items):
    # Pix3D formats vary; try common keys
    img_rel = it.get("img") or it.get("img_path") or it.get("img_file") or it.get("image")
    category = it.get("category") or it.get("class") or "product"
    if img_rel is None:
        continue
    img_path = os.path.join(PIX3D_ROOT, img_rel)
    if not os.path.exists(img_path):
        # try join different subfolders:
        if os.path.exists(os.path.join(PIX3D_ROOT, "images", img_rel)):
            img_path = os.path.join(PIX3D_ROOT, "images", img_rel)
        else:
            # skip missing
            continue

    # Copy to data/images with normalized filename
    out_name = f"{counter}.jpg"
    out_path = os.path.join(OUT_IMAGES, out_name)
    
    try:
        # Open and save as RGB to ensure consistency
        img = Image.open(img_path).convert("RGB")
        img.save(out_path, "JPEG", quality=95)
    except Exception as e:
        print(f"Error copying {img_path}: {e}")
        continue

    # detect color (dominant)
    dom_color = None
    if COLOR_THIEF_AVAILABLE:
        try:
            ct = ColorThief(img_path)
            dom_color = ct.get_color(quality=1)
            dom_name = rgb_to_basic_name(dom_color)
        except Exception:
            dom_name = "unknown"
    else:
        # fallback: sample center pixel
        try:
            w, h = img.size
            px = img.getpixel((w // 2, h // 2))
            dom_name = rgb_to_basic_name(px)
        except Exception:
            dom_name = "unknown"

    # Build product name with color
    product_name = build_product_name(category, dom_name, counter)
    
    product = {
        "id": counter,
        "productDisplayName": product_name,
        "masterCategory": "Furniture",
        "subCategory": category.capitalize(),
        "baseColour": dom_name,  # IMPORTANT: Used for color filtering
        "image_path": out_name,
        "source_img": img_rel
    }
    clean_products.append(product)

    # FIXED: Process image and text SEPARATELY
    try:
        # Process IMAGE
        img_inputs = clip_processor(
            images=img,
            return_tensors="pt"
        ).to(device)
        
        # Process TEXT  
        text_inputs = clip_processor(
            text=[product_name],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=77
        ).to(device)
        
        with torch.no_grad():
            # Get image features (only pass pixel_values)
            img_feat = clip_model.get_image_features(
                pixel_values=img_inputs['pixel_values']
            )
            
            # Get text features (only pass input_ids and attention_mask)
            txt_feat = clip_model.get_text_features(
                input_ids=text_inputs['input_ids'],
                attention_mask=text_inputs['attention_mask']
            )
        
        # Convert to numpy
        img_feat = img_feat.cpu().numpy()
        txt_feat = txt_feat.cpu().numpy()
        
        image_embeddings.append(img_feat)
        text_embeddings.append(txt_feat)
        id_map.append(counter)
        
    except Exception as e:
        print(f"Error embedding {img_path}: {e}")
        # remove previous copied file to keep sets consistent
        if os.path.exists(out_path):
            os.remove(out_path)
        clean_products.pop()
        continue

    counter += 1

if len(image_embeddings) == 0:
    raise SystemExit("No images processed - check PIX3D_ROOT and metadata file")

# stack arrays
image_matrix = np.vstack(image_embeddings).astype("float32")  # (N, D)
text_matrix = np.vstack(text_embeddings).astype("float32")

# normalize rows (cosine similarity)
def normalize_rows(x):
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return x / norms

image_matrix = normalize_rows(image_matrix)
text_matrix = normalize_rows(text_matrix)

# build FAISS IndexFlatIP (inner product on normalized vectors => cosine)
d = image_matrix.shape[1]
print(f"Embedding dim = {d}, total items = {image_matrix.shape[0]}")

img_index = faiss.IndexFlatIP(d)
txt_index = faiss.IndexFlatIP(d)
img_index.add(image_matrix)
txt_index.add(text_matrix)

# save
faiss.write_index(img_index, IMAGE_INDEX)
faiss.write_index(txt_index, TEXT_INDEX)
np.save(ID_MAP, np.array(id_map, dtype=np.int64))
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(clean_products, f, indent=2, ensure_ascii=False)

print("\n" + "="*60)
print("✅ Preprocessing Complete!")
print("="*60)
print(f"📁 Products JSON: {OUT_JSON}")
print(f"📁 Image Index:   {IMAGE_INDEX}")
print(f"📁 Text Index:    {TEXT_INDEX}")
print(f"📁 ID Map:        {ID_MAP}")
print(f"📊 Total indexed: {len(id_map)} items")
print(f"📊 Categories:    {set(p['subCategory'] for p in clean_products)}")
print(f"📊 Colors found:  {set(p['baseColour'] for p in clean_products)}")
print("="*60)