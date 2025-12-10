import os
import json
import trimesh
import numpy as np
from pathlib import Path

# ======================
# CONFIG
# ======================
DATA_DIR = "data"
PIX3D_ROOT = os.path.join(DATA_DIR, "pix3d")
PIX3D_META = os.path.join(PIX3D_ROOT, "pix3d.json")
CLEAN_PRODUCTS_PATH = os.path.join(DATA_DIR, "clean_products.json")
MODELS_DIR = os.path.join(DATA_DIR, "models")

os.makedirs(MODELS_DIR, exist_ok=True)


# ======================
# LOAD METADATA
# ======================
def load_metadata():
    """Load Pix3D + Clean products and build an image→ID mapping."""
    if not os.path.exists(PIX3D_META):
        raise FileNotFoundError(f"❌ Pix3D metadata not found: {PIX3D_META}")

    if not os.path.exists(CLEAN_PRODUCTS_PATH):
        raise FileNotFoundError(f"❌ Clean products not found: {CLEAN_PRODUCTS_PATH}")

    with open(PIX3D_META, "r") as f:
        pix3d_data = json.load(f)

    with open(CLEAN_PRODUCTS_PATH, "r") as f:
        clean_products = json.load(f)

    image_to_id = {}
    for product in clean_products:
        # Normalize key (lowercase + forward slashes)
        key = product["image_path"].lower().replace("\\", "/")
        image_to_id[key] = product["id"]

    print(f"📦 Loaded {len(clean_products)} products with image→ID mapping")
    return pix3d_data, clean_products, image_to_id


# ======================
# HELPERS
# ======================
def find_pix3d_model(entry):
    """Locate 3D model file in Pix3D dataset."""
    model_path = entry.get("model")
    if not model_path:
        return None
    full_path = os.path.join(PIX3D_ROOT, model_path)
    return full_path if os.path.exists(full_path) else None


def normalize_mesh(mesh):
    """Center and scale mesh for AR display."""
    mesh.vertices -= mesh.centroid
    bounds = mesh.bounds
    size = bounds[1] - bounds[0]
    max_dim = np.max(size)
    target_size = 0.6  # Target size (meters)

    if max_dim > 0:
        scale = target_size / max_dim
        mesh.apply_scale(scale)

    return mesh

# ======================
# MAIN EXPORT FUNCTION
# ======================
def export_pix3d_models(limit=None):
    pix3d_data, clean_products, image_to_id = load_metadata()

    print(f"🧩 Found {len(pix3d_data)} Pix3D entries")
    if limit:
        pix3d_data = pix3d_data[:limit]
        print(f"⚠️  Limiting to first {limit} models for testing")

    success, failed, skipped = 0, 0, 0

    for i, entry in enumerate(pix3d_data, 1):
        img_path = entry.get("img", "")
        if not img_path:
            continue

        if img_path.startswith("img/"):
            img_path = img_path[4:]
        img_key = img_path.lower().replace("\\", "/")
        alt_key = (
            img_key.replace(".png", ".jpg")
            if img_key.endswith(".png")
            else img_key.replace(".jpg", ".png")
        )
        product_id = image_to_id.get(img_key) or image_to_id.get(alt_key)
        if product_id is None:
            skipped += 1
            if skipped <= 5:
                print(f"[{i}] ⚠️ No matching ID for {img_key} or {alt_key}")
            continue

        model_path = find_pix3d_model(entry)
        if not model_path:
            failed += 1
            if failed <= 5:
                print(f"[{i}] ❌ No 3D model found for {img_key}")
            continue

        # Locate matching texture image
        texture_path = os.path.join(PIX3D_ROOT, "img", img_key)
        if not os.path.exists(texture_path):
            texture_path = os.path.join(PIX3D_ROOT, "img", alt_key)
        texture_path = os.path.normpath(texture_path)

        output_path = os.path.join(MODELS_DIR, f"{product_id}.glb")

        try:
            mesh = trimesh.load(model_path, force="mesh", process=True)

            # Merge scene if multiple geometries
            if isinstance(mesh, trimesh.Scene):
                mesh = trimesh.util.concatenate([
                    trimesh.Trimesh(vertices=g.vertices, faces=g.faces)
                    for g in mesh.geometry.values()
                ])

            # Attach the image texture
            if os.path.exists(texture_path):
                import PIL.Image
                tex = PIL.Image.open(texture_path).convert("RGB")
                mesh.visual = trimesh.visual.texture.TextureVisuals(
                    image=tex
                )
            else:
                print(f"⚠️  No texture found for {img_key}")

            # Normalize and export
            mesh = normalize_mesh(mesh)
            mesh.export(output_path, file_type="glb")

            size_kb = os.path.getsize(output_path) / 1024
            print(f"[{i}] ✅ {product_id}.glb | {size_kb:.1f} KB")
            success += 1

        except Exception as e:
            failed += 1
            print(f"[{i}] ❌ Failed {product_id}: {e}")

        if i % 50 == 0:
            print(
                f"\n--- Progress: {i}/{len(pix3d_data)} | ✅ {success} | ❌ {failed} | ⏭️ {skipped} ---\n"
            )

    print("\n" + "=" * 60)
    print(f"✅ Export complete!")
    print(f"   Success: {success}/{len(pix3d_data)}")
    print(f"   Failed:  {failed}")
    print(f"   Skipped: {skipped}")
    print(f"   Models saved to: {os.path.abspath(MODELS_DIR)}")
    print("=" * 60)


# ======================
# ENTRY POINT
# ======================
if __name__ == "__main__":
    import sys

    limit = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            limit = 50
            print("🧪 TEST MODE: Exporting 50 models")
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python generate_3d_models.py          # Export all models")
            print("  python generate_3d_models.py --test   # Export 50 for testing")
            exit(0)

    success, failed, skipped = export_pix3d_models(limit=limit)

    if success > 0:
        print(f"\n✅ {success} 3D models ready for AR!")
        print("\n🎯 Next steps:")
        print("1. Restart backend: python main.py")
        print("2. Try searching 'chair', 'bed', or 'table'")
        print("3. Click 'View in AR' to see REAL 3D furniture models.")
    else:
        print("\n⚠️  No models exported successfully. Check missing path mappings above.")
