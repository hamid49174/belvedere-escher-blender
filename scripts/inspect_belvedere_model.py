from pathlib import Path
from collections import defaultdict

import bpy
from mathutils import Vector


WORK_DIR = Path(r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d")
SCENE_BLEND = WORK_DIR / "belvedere_escher_mathe_praesentation.blend"


def bounds_for_objects(objects):
    mins = Vector((float("inf"), float("inf"), float("inf")))
    maxs = Vector((float("-inf"), float("-inf"), float("-inf")))
    found = False
    for obj in objects:
        if obj.type != "MESH":
            continue
        found = True
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, world.x)
            mins.y = min(mins.y, world.y)
            mins.z = min(mins.z, world.z)
            maxs.x = max(maxs.x, world.x)
            maxs.y = max(maxs.y, world.y)
            maxs.z = max(maxs.z, world.z)
    if not found:
        return None
    return mins, maxs


def print_bounds(label, objects):
    result = bounds_for_objects(objects)
    if not result:
        print(label, "NO_MESH")
        return
    mins, maxs = result
    print(label)
    print("  min", tuple(round(v, 3) for v in mins))
    print("  max", tuple(round(v, 3) for v in maxs))
    print("  size", tuple(round(v, 3) for v in (maxs - mins)))
    print("  center", tuple(round(v, 3) for v in ((mins + maxs) * 0.5)))


bpy.ops.wm.open_mainfile(filepath=str(SCENE_BLEND))

raw_col = bpy.data.collections.get("Rohmodell Belvedere")
raw_objects = list(raw_col.objects) if raw_col else []
print_bounds("RAW_COLLECTION", raw_objects)

material_objects = defaultdict(list)
for obj in raw_objects:
    if obj.type != "MESH":
        continue
    mat_name = obj.data.materials[0].name if obj.data.materials else "NO_MATERIAL"
    material_objects[mat_name].append(obj)

for mat_name, objects in sorted(material_objects.items(), key=lambda item: len(item[1]), reverse=True)[:12]:
    mat = bpy.data.materials.get(mat_name)
    color = tuple(round(v, 3) for v in mat.diffuse_color) if mat else None
    print_bounds(f"MATERIAL {mat_name} count={len(objects)} color={color}", objects)

large = []
for obj in raw_objects:
    if obj.type != "MESH":
        continue
    result = bounds_for_objects([obj])
    if not result:
        continue
    mins, maxs = result
    size = maxs - mins
    volume_hint = size.x * size.y * size.z
    large.append((volume_hint, obj.name, mins, maxs, size))

for volume_hint, name, mins, maxs, size in sorted(large, reverse=True)[:30]:
    print(
        "OBJ",
        name,
        "vol",
        round(volume_hint, 3),
        "min",
        tuple(round(v, 3) for v in mins),
        "max",
        tuple(round(v, 3) for v in maxs),
        "size",
        tuple(round(v, 3) for v in size),
    )
