"""
Convert Pix3D .obj models to .glb with proper colors and textures
Install: pip install trimesh pygltflib pillow numpy
"""
import os
import json
from pathlib import Path
from tqdm import tqdm
import trimesh
import numpy as np

PIX3D_ROOT = "data/pix3d"
OUT_MODELS_DIR = "data/models"
CLEAN_PRODUCTS_PATH = "data/clean_products.json"

os.makedirs(OUT_MODELS_DIR, exist_ok=True)

# Load product mapping
with open(CLEAN_PRODUCTS_PATH, "r") as f:
    products = json.load(f)

print(f"Found {len(products)} products")
print("Converting .obj models to .glb with colors...")

# Color mapping based on product color field
COLOR_MAP = {
    "red": [0.8, 0.2, 0.2],
    "blue": [0.2, 0.3, 0.8],
    "green": [0.2, 0.7, 0.3],
    "yellow": [0.9, 0.9, 0.2],
    "black": [0.1, 0.1, 0.1],
    "white": [0.95, 0.95, 0.95],
    "brown": [0.5, 0.3, 0.2],
    "grey": [0.5, 0.5, 0.5],
    "gray": [0.5, 0.5, 0.5],
    "pink": [0.9, 0.6, 0.7],
    "purple": [0.6, 0.3, 0.8],
    "orange": [0.9, 0.5, 0.2],
    "beige": [0.9, 0.85, 0.7],
    "tan": [0.8, 0.7, 0.5],
    "navy": [0.1, 0.2, 0.4],
    "burgundy": [0.5, 0.1, 0.2],
}

def get_color_from_name(color_name):
    """Get RGB color from color name"""
    if not color_name or color_name == "unknown":
        return [0.7, 0.7, 0.7]  # Default gray
    
    color_name = color_name.lower()
    return COLOR_MAP.get(color_name, [0.7, 0.7, 0.7])

def extract_texture_from_image(product_id, image_path):
    """Extract dominant color from product image"""
    try:
        from PIL import Image
        
        # Open product image
        img_path = f"data/images/{image_path}"
        if not os.path.exists(img_path):
            return None
        
        img = Image.open(img_path)
        img = img.resize((100, 100))  # Downsample for speed
        img_array = np.array(img.convert('RGB'))
        
        # Get average color
        avg_color = np.mean(img_array, axis=(0, 1))
        # Normalize to 0-1 range
        color_rgb = avg_color / 255.0
        
        return color_rgb.tolist()
    except Exception as e:
        print(f"⚠️ Could not extract color from image: {e}")
        return None

converted = 0
skipped = 0
errors = 0

for product in tqdm(products):
    product_id = product["id"]
    category = product.get("subCategory", "chair").lower()
    color_name = product.get("color", "unknown")
    image_path = product.get("image_path", "")
    
    # Try to find .obj model
    possible_paths = [
        f"{PIX3D_ROOT}/model/{category}/{product_id}.obj",
        f"{PIX3D_ROOT}/model/{product_id}.obj",
        f"{PIX3D_ROOT}/models/{category}/{product_id}.obj",
    ]
    
    obj_path = None
    for path in possible_paths:
        if os.path.exists(path):
            obj_path = path
            break
    
    if not obj_path:
        skipped += 1
        continue
    
    glb_path = f"{OUT_MODELS_DIR}/{product_id}.glb"
    
    # Skip if already converted
    if os.path.exists(glb_path):
        converted += 1
        continue
    
    try:
        # Load .obj file
        mesh = trimesh.load(obj_path, force='mesh', process=False)
        
        # Handle multi-mesh objects
        if isinstance(mesh, trimesh.Scene):
            # Combine all meshes in scene
            meshes = [geom for geom in mesh.geometry.values() if isinstance(geom, trimesh.Trimesh)]
            if meshes:
                mesh = trimesh.util.concatenate(meshes)
            else:
                print(f"⚠️ No valid meshes in scene for {obj_path}")
                errors += 1
                continue
        
        # Center the model
        mesh.vertices -= mesh.centroid
        
        # Scale to reasonable size (1-2 units)
        scale = 1.5 / mesh.extents.max()
        mesh.vertices *= scale
        
        # ===== CRITICAL: Add color/texture =====
        
        # Option 1: Use color from product metadata
        color_rgb = get_color_from_name(color_name)
        
        # Option 2: Try to extract from product image (more accurate)
        if image_path:
            extracted_color = extract_texture_from_image(product_id, image_path)
            if extracted_color:
                color_rgb = extracted_color
        
        # Create material with color
        # Convert to 0-255 range for trimesh
        color_rgba = [int(c * 255) for c in color_rgb] + [255]  # Add alpha
        
        # Apply color to all vertices
        if not hasattr(mesh, 'visual') or mesh.visual is None:
            mesh.visual = trimesh.visual.ColorVisuals()
        
        # Set vertex colors (CRITICAL for .glb)
        vertex_colors = np.tile(color_rgba, (len(mesh.vertices), 1))
        mesh.visual.vertex_colors = vertex_colors
        
        # Also set face colors
        if len(mesh.faces) > 0:
            face_colors = np.tile(color_rgba, (len(mesh.faces), 1))
            mesh.visual.face_colors = face_colors
        
        # Create PBR material (for better rendering)
        material = trimesh.visual.material.PBRMaterial(
            baseColorFactor=color_rgb + [1.0],  # RGBA in 0-1 range
            metallicFactor=0.1,   # Low metallic (furniture is usually not metallic)
            roughnessFactor=0.8,  # High roughness (matte finish)
        )
        
        # Apply material to mesh
        if hasattr(mesh.visual, 'material'):
            mesh.visual.material = material
        
        # Export as .glb with embedded colors
        mesh.export(
            glb_path, 
            file_type='glb',
            include_normals=True,
        )
        
        converted += 1
        
    except Exception as e:
        print(f"\n❌ Error converting {obj_path}: {e}")
        errors += 1

print("\n" + "="*60)
print("✅ Conversion Complete!")
print("="*60)
print(f"✅ Converted: {converted}")
print(f"⏭️  Skipped: {skipped}")
print(f"❌ Errors: {errors}")
print(f"📁 Models saved to: {OUT_MODELS_DIR}")
print("="*60)

# Update products.json with model availability
print("\nUpdating product metadata...")
for product in products:
    product_id = product["id"]
    glb_path = f"{OUT_MODELS_DIR}/{product_id}.glb"
    product["has_3d_model"] = os.path.exists(glb_path)

with open(CLEAN_PRODUCTS_PATH, "w") as f:
    json.dump(products, f, indent=2)

models_with_ar = sum(1 for p in products if p.get("has_3d_model"))
print(f"✅ {models_with_ar}/{len(products)} products now have AR support with colors!")