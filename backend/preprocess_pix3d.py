import os
import json
import torch
import faiss
import numpy as np
from PIL import Image
from tqdm import tqdm
from transformers import CLIPProcessor, CLIPModel

# ========== CONFIG ==========
PIX3D_META_PATH = "data/pix3d/pix3d.json"
PIX3D_ROOT = "data/pix3d"  # Root directory where pix3d images are
OUTPUT_JSON = "data/clean_products.json"
IMAGE_INDEX_PATH = "data/image_index.faiss"
TEXT_INDEX_PATH = "data/text_index.faiss"
ID_MAP_PATH = "data/id_map.npy"

# Create symlink/copy images to expected location
IMAGES_OUTPUT_DIR = "data/images"
os.makedirs(IMAGES_OUTPUT_DIR, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("🔧 Using device:", device)

# ========== LOAD CLIP ==========
print("Loading CLIP model...")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model.eval()

# ========== LOAD PIX3D METADATA ==========
print("Loading Pix3D metadata...")
with open(PIX3D_META_PATH, "r") as f:
    data = json.load(f)

print(f"Found {len(data)} items in pix3d.json")

# ========== PROCESS ITEMS ==========
products = []
valid_count = 0
missing_count = 0

for i, item in enumerate(data):
    # item["img"] is like "img/chair/0001.jpg"
    # Full path should be: data/pix3d/img/chair/0001.jpg
    
    img_relative = item["img"]  # e.g., "img/chair/0001.jpg"
    img_full_path = os.path.join(PIX3D_ROOT, img_relative)
    
    # Normalize path separators for Windows
    img_full_path = os.path.normpath(img_full_path)
    
    if not os.path.exists(img_full_path):
        missing_count += 1
        if missing_count <= 5:  # Only show first 5 missing files
            print(f"⚠️  Missing: {img_full_path}")
        continue
    
    # Store relative path from IMAGES_OUTPUT_DIR for later use
    # We'll copy/link images to data/images/ directory
    category = item["category"]
    img_filename = os.path.basename(img_relative)
    
    # Create category subdirectory in images
    category_dir = os.path.join(IMAGES_OUTPUT_DIR, category)
    os.makedirs(category_dir, exist_ok=True)
    
    # Output path: data/images/chair/0001.jpg
    img_output_path = os.path.join(category_dir, img_filename)
    img_relative_from_images = os.path.join(category, img_filename)
    
    # Copy image to images directory if not exists
    if not os.path.exists(img_output_path):
        try:
            import shutil
            shutil.copy2(img_full_path, img_output_path)
        except Exception as e:
            print(f"⚠️  Failed to copy {img_full_path}: {e}")
            continue
    
    products.append({
        "id": valid_count,  # Use sequential ID
        "productDisplayName": f"{category} furniture",
        "masterCategory": "Furniture",
        "subCategory": category,
        "image_path": img_relative_from_images,  # e.g., "chair/0001.jpg"
        "model_path": item.get("model", ""),
        "bbox": item.get("bbox", [])
    })
    
    valid_count += 1

if missing_count > 5:
    print(f"⚠️  ... and {missing_count - 5} more missing files")

print(f"✅ Found {valid_count} valid items (skipped {missing_count} missing)")

if valid_count == 0:
    print("❌ No valid products found! Check your pix3d directory structure.")
    print(f"Expected structure:")
    print(f"  data/pix3d/")
    print(f"    ├── pix3d.json")
    print(f"    └── img/")
    print(f"        ├── chair/")
    print(f"        ├── table/")
    print(f"        └── ...")
    exit(1)

# ========== BUILD EMBEDDINGS ==========
def get_image_features(products_list):
    features = []
    valid_products = []
    
    for p in tqdm(products_list, desc="Extracting image embeddings"):
        img_path = os.path.join(IMAGES_OUTPUT_DIR, p["image_path"])
        
        try:
            image = Image.open(img_path).convert("RGB")
            inputs = clip_processor(images=image, return_tensors="pt").to(device)
            
            with torch.no_grad():
                emb = clip_model.get_image_features(**inputs)
            
            emb = emb.cpu().numpy()
            emb /= np.linalg.norm(emb)
            
            features.append(emb[0])
            valid_products.append(p)
            
        except Exception as e:
            print(f"⚠️  Error processing {img_path}: {e}")
            continue
    
    return np.array(features, dtype="float32"), valid_products

def get_text_features(products_list):
    features = []
    
    for p in tqdm(products_list, desc="Extracting text embeddings"):
        text = p["productDisplayName"]
        
        inputs = clip_processor(text=[text], return_tensors="pt", padding=True).to(device)
        
        with torch.no_grad():
            emb = clip_model.get_text_features(**inputs)
        
        emb = emb.cpu().numpy()
        emb /= np.linalg.norm(emb)
        features.append(emb[0])
    
    return np.array(features, dtype="float32")

# Extract features
image_features, valid_products = get_image_features(products)

if len(valid_products) == 0:
    print("❌ No valid embeddings created!")
    exit(1)

# Update products list to only valid ones
products = valid_products

# Extract text features for valid products only
text_features = get_text_features(products)

# Create ID map
id_map = np.array([p["id"] for p in products])

# ========== SAVE INDEXES ==========
print("Building FAISS indexes...")

image_index = faiss.IndexFlatL2(image_features.shape[1])
image_index.add(image_features)

text_index = faiss.IndexFlatL2(text_features.shape[1])
text_index.add(text_features)

faiss.write_index(image_index, IMAGE_INDEX_PATH)
faiss.write_index(text_index, TEXT_INDEX_PATH)
np.save(ID_MAP_PATH, id_map)

# Save products metadata
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2)

print("\n" + "="*60)
print("✅ Preprocessing complete!")
print(f"📦 Saved {len(products)} products to {OUTPUT_JSON}")
print(f"📂 Images copied to {IMAGES_OUTPUT_DIR}")
print(f"💾 Image index: {IMAGE_INDEX_PATH} ({image_features.shape})")
print(f"💾 Text index: {TEXT_INDEX_PATH} ({text_features.shape})")
print(f"💾 ID map: {ID_MAP_PATH} ({len(id_map)} items)")
print("="*60)

# Show sample products
print("\n📊 Sample products:")
for p in products[:3]:
    print(f"  ID {p['id']}: {p['productDisplayName']} ({p['subCategory']}) - {p['image_path']}")