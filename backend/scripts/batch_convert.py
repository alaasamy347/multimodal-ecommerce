import subprocess
from pathlib import Path

# --------------------------------------------------
# Paths
# --------------------------------------------------
BLENDER_CMD = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"  # already in PATH
SCRIPT_PATH = Path("scripts/convert_pix3d_to_glb.py")

PIX3D_MODEL_DIR = Path("data/pix3d/model")
PIX3D_GLB_DIR = Path("data/pix3d/glb")

# --------------------------------------------------
# Find all OBJ files
# --------------------------------------------------
obj_files = list(PIX3D_MODEL_DIR.rglob("model.obj"))

if not obj_files:
    print("⚠️ No OBJ files found.")
    exit(0)

print(f"🔍 Found {len(obj_files)} OBJ files")

# --------------------------------------------------
# Convert each OBJ
# --------------------------------------------------
for obj_path in obj_files:
    # Expected structure:
    # data/pix3d/model/<category>/<model_id>/model.obj

    category = obj_path.parts[-3]
    model_id = obj_path.parts[-2]

    output_glb = (
        PIX3D_GLB_DIR /
        category /
        f"{model_id}.glb"
    )

    print(f"\n🔄 Converting: {obj_path}")
    print(f"📁 Category: {category}")
    print(f"🪑 Model ID: {model_id}")
    print(f"➡️ Output: {output_glb}")

    subprocess.run(
        [
            BLENDER_CMD,
            "--background",
            "--python", str(SCRIPT_PATH),
            "--",
            str(obj_path),
            str(output_glb)
        ],
        check=True
    )

print("\n🎉 All Pix3D models converted successfully.")
