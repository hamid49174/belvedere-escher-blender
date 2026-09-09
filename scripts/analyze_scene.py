import mathutils
import bpy

BLEND_PATH = r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d\belvedere_escher_tpe.blend"

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

mins = mathutils.Vector((float("inf"), float("inf"), float("inf")))
maxs = mathutils.Vector((float("-inf"), float("-inf"), float("-inf")))
mesh_names = []

for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    mesh_names.append(obj.name)
    for corner in obj.bound_box:
        world = obj.matrix_world @ mathutils.Vector(corner)
        mins.x = min(mins.x, world.x)
        mins.y = min(mins.y, world.y)
        mins.z = min(mins.z, world.z)
        maxs.x = max(maxs.x, world.x)
        maxs.y = max(maxs.y, world.y)
        maxs.z = max(maxs.z, world.z)

print("MESH_COUNT", len(mesh_names))
print("BOUNDS_MIN", tuple(round(v, 4) for v in mins))
print("BOUNDS_MAX", tuple(round(v, 4) for v in maxs))
print("SIZE", tuple(round(v, 4) for v in (maxs - mins)))
print("FIRST_NAMES", mesh_names[:12])
