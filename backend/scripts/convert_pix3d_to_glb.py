import bpy
import sys
from pathlib import Path

# --------------------------------------------------
# Parse CLI arguments
# --------------------------------------------------
argv = sys.argv
argv = argv[argv.index("--") + 1:]

input_obj = Path(argv[0]).resolve()
output_glb = Path(argv[1]).resolve()

print(f"📥 Importing: {input_obj}")
print(f"📤 Exporting to: {output_glb}")

# --------------------------------------------------
# Reset Blender to empty scene
# --------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)

# --------------------------------------------------
# IMPORT OBJ (Blender 5.0+ API)
# --------------------------------------------------
bpy.ops.wm.obj_import(
    filepath=str(input_obj),
    forward_axis='NEGATIVE_Z',
    up_axis='Y'
)

# --------------------------------------------------
# Select all imported objects
# --------------------------------------------------
bpy.ops.object.select_all(action="SELECT")

# --------------------------------------------------
# Apply transforms (important for GLB + AR)
# --------------------------------------------------
bpy.ops.object.transform_apply(
    location=True,
    rotation=True,
    scale=True
)

# --------------------------------------------------
# Ensure output directory exists
# --------------------------------------------------
output_glb.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# EXPORT GLB
# --------------------------------------------------
bpy.ops.export_scene.gltf(
    filepath=str(output_glb),
    export_format="GLB",
    export_apply=True,
)

print(f"✅ Successfully converted → {output_glb}")