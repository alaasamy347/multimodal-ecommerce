import os
import json
import trimesh
from pathlib import Path

# === Directories ===
input_dir = Path("data/pix3d")
output_dir = Path("data/models")
output_dir.mkdir(parents=True, exist_ok=True)

# === Convert .obj → .glb ===
print("🔄 Converting .obj models to .glb ...")

for root, _, files in os.walk(input_dir):
    for file in files:
        if file.endswith(".obj"):
            input_path = Path(root) / file
            output_path = output_dir / (input_path.stem + ".glb")
            try:
                mesh = trimesh.load(input_path)
                mesh.export(output_path)
                print(f"✅ Converted {file} → {output_path.name}")
            except Exception as e:
                print(f"⚠️ Error converting {file}: {e}")

print("\n✅ All model conversions complete.\n")

# === Fix paths in clean_products.json ===
json_path = Path("data/clean_products.json")
if not json_path.exists():
    print(f"⚠️ {json_path} not found. Skipping path fix.")
    exit()

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

updated_count = 0
for item in data:
    img_path = item.get("image_path", "")
    model_path = item.get("model_path", "")

    # Fix image path
    if not img_path.startswith("pix3d/"):
        item["image_path"] = f"pix3d/{img_path}"
        updated_count += 1

    # Fix model path (and point to new .glb)
    if not model_path.startswith("models/"):
        # Use .glb instead of .obj
        glb_name = Path(model_path).stem + ".glb"
        item["model_path"] = f"models/{glb_name}"
        updated_count += 1

# === Save updated JSON ===
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"✅ Updated {updated_count} entries in {json_path}")
print("🎉 Paths and models are now fully synced.")
