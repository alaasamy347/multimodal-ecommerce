"""
Simple verification script - just checks local data/ folder
No Kaggle API required
"""
import os
import json
from pathlib import Path

DATA_DIR = "data"
IMAGES_DIR = os.path.join(DATA_DIR, "images")
JSON_PATH = os.path.join(DATA_DIR, "clean_products.json")

print("="*60)
print("🔍 Verifying Local Dataset Structure")
print("="*60)

errors = []
warnings = []

# 1. Check if data directory exists
print("\n1️⃣ Checking data directory...")
if not os.path.exists(DATA_DIR):
    errors.append(f"Data directory not found: {DATA_DIR}")
    print(f"   ❌ {DATA_DIR} not found!")
    print("\n   You need to run preprocessing first:")
    print("   python preprocess_pix3d.py")
    exit(1)
else:
    print(f"   ✅ Found: {DATA_DIR}")

# 2. Check required files
print("\n2️⃣ Checking required files...")
required_files = {
    "clean_products.json": "Product metadata",
    "image_index.faiss": "Image embeddings",
    "text_index.faiss": "Text embeddings",
    "id_map.npy": "ID mapping"
}

for filename, description in required_files.items():
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"   ✅ {filename} ({size_mb:.2f} MB) - {description}")
    else:
        errors.append(f"Missing file: {filename}")
        print(f"   ❌ {filename} - MISSING!")

# 3. Check images directory
print("\n3️⃣ Checking images directory...")
if not os.path.exists(IMAGES_DIR):
    errors.append("Images directory not found")
    print(f"   ❌ {IMAGES_DIR} not found!")
else:
    print(f"   ✅ Found: {IMAGES_DIR}")
    
    # Count images by category
    categories = {}
    total_images = 0
    
    for item in os.listdir(IMAGES_DIR):
        item_path = os.path.join(IMAGES_DIR, item)
        if os.path.isdir(item_path):
            count = len([f for f in os.listdir(item_path) 
                        if f.endswith(('.jpg', '.jpeg', '.png'))])
            categories[item] = count
            total_images += count
    
    print(f"   ✅ Found {len(categories)} categories")
    print(f"   ✅ Total images: {total_images}")
    
    if categories:
        print(f"\n   📊 Images per category:")
        for cat, count in sorted(categories.items()):
            print(f"      - {cat}: {count} images")
    else:
        errors.append("Images directory is empty!")

# 4. Verify JSON structure
print("\n4️⃣ Verifying clean_products.json...")
if os.path.exists(JSON_PATH):
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        print(f"   ✅ Loaded {len(products)} products")
        
        # Show sample product
        if products:
            sample = products[0]
            print(f"\n   📦 Sample product:")
            print(f"      ID: {sample.get('id')}")
            print(f"      Name: {sample.get('productDisplayName')}")
            print(f"      Category: {sample.get('subCategory')}")
            print(f"      Image: {sample.get('image_path')}")
            print(f"      Color: {sample.get('baseColour', 'N/A')}")
            
            # Check if image exists
            image_path = sample.get('image_path', '')
            if image_path:
                full_path = os.path.join(IMAGES_DIR, image_path)
                if os.path.exists(full_path):
                    print(f"      Image exists: ✅")
                else:
                    print(f"      Image exists: ❌ (path: {full_path})")
                    warnings.append(f"Sample image not found: {image_path}")
    
    except Exception as e:
        errors.append(f"Error reading JSON: {e}")
        print(f"   ❌ Error: {e}")

# 5. Show directory structure
print("\n5️⃣ Directory structure:")
print(f"\n{DATA_DIR}/")

def show_tree(path, prefix="", max_files=3):
    """Show simplified tree"""
    try:
        items = sorted(os.listdir(path))
        dirs = [i for i in items if os.path.isdir(os.path.join(path, i))]
        files = [i for i in items if os.path.isfile(os.path.join(path, i))]
        
        # Show files
        for file in files[:max_files]:
            file_path = os.path.join(path, file)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"{prefix}├── {file} ({size_mb:.2f} MB)")
        
        if len(files) > max_files:
            print(f"{prefix}├── ... and {len(files) - max_files} more files")
        
        # Show directories
        for i, dir_name in enumerate(dirs):
            is_last = i == len(dirs) - 1
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "
            
            dir_path = os.path.join(path, dir_name)
            item_count = len(os.listdir(dir_path))
            print(f"{prefix}{connector}{dir_name}/ ({item_count} items)")
            
            # Show first level only
            if dir_name == "images":
                subdirs = [d for d in os.listdir(dir_path) 
                          if os.path.isdir(os.path.join(dir_path, d))]
                for subdir in subdirs[:5]:
                    sub_path = os.path.join(dir_path, subdir)
                    sub_count = len(os.listdir(sub_path))
                    print(f"{prefix}{extension}├── {subdir}/ ({sub_count} images)")
                if len(subdirs) > 5:
                    print(f"{prefix}{extension}└── ... and {len(subdirs)-5} more categories")
    
    except Exception as e:
        print(f"{prefix}Error: {e}")

show_tree(DATA_DIR)

# 6. Calculate total size
print("\n6️⃣ Dataset size:")
total_size = 0
for root, dirs, files in os.walk(DATA_DIR):
    for file in files:
        filepath = os.path.join(root, file)
        total_size += os.path.getsize(filepath)

total_size_mb = total_size / (1024 * 1024)
total_size_gb = total_size / (1024 * 1024 * 1024)

print(f"   📦 Total size: {total_size_mb:.2f} MB ({total_size_gb:.2f} GB)")

# SUMMARY
print("\n" + "="*60)
print("📋 VERIFICATION SUMMARY")
print("="*60)

if not errors:
    print("✅ No errors found!")
    print("\n🎉 Your dataset is ready to upload to Kaggle!")
    
    print("\n📋 Next steps:")
    print("1. Go to: https://www.kaggle.com/datasets/alaasamy1/amazon-data2")
    print("2. Click 'New Version'")
    print("3. Upload these files/folders:")
    print("   - clean_products.json")
    print("   - image_index.faiss")
    print("   - text_index.faiss")
    print("   - id_map.npy")
    print("   - images/ (entire folder)")
    print("4. Click 'Save Version'")
    print("\n5. After upload completes:")
    print("   - Redeploy Modal: modal deploy modal_app.py")
    print("   - Check logs: modal app logs furniture-search-api")
    print("   - Test: curl YOUR_MODAL_URL/test-image")

else:
    print(f"❌ Found {len(errors)} errors:")
    for error in errors:
        print(f"   • {error}")
    
    print("\n🔧 How to fix:")
    print("   Run: python preprocess_pix3d.py")
    print("   This will create all required files in data/")

if warnings:
    print(f"\n⚠️ {len(warnings)} warnings:")
    for warning in warnings:
        print(f"   • {warning}")

print("\n" + "="*60)