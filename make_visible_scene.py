import math
import mathutils
import bpy

SOURCE_BLEND = r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d\belvedere_escher_tpe.blend"
VISIBLE_BLEND = r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d\belvedere_escher_tpe_visible.blend"


def mesh_bounds():
    mins = mathutils.Vector((float("inf"), float("inf"), float("inf")))
    maxs = mathutils.Vector((float("-inf"), float("-inf"), float("-inf")))
    found = False

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        found = True
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            mins.x = min(mins.x, world.x)
            mins.y = min(mins.y, world.y)
            mins.z = min(mins.z, world.z)
            maxs.x = max(maxs.x, world.x)
            maxs.y = max(maxs.y, world.y)
            maxs.z = max(maxs.z, world.z)

    if not found:
        raise RuntimeError("No mesh objects were found in the scene.")

    return mins, maxs


def look_at(obj, target):
    direction = mathutils.Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=SOURCE_BLEND)

for obj in bpy.context.scene.objects:
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.hide_render = False

mins, maxs = mesh_bounds()
center = (mins + maxs) * 0.5
size = maxs - mins
scale = 18.0 / max(size.x, size.y, size.z)

wrapper = bpy.data.objects.new("Visible_Model_Frame", None)
bpy.context.collection.objects.link(wrapper)

top_level = [obj for obj in bpy.context.scene.objects if obj.parent is None and obj != wrapper]
for obj in top_level:
    obj.parent = wrapper

wrapper.location = (-center.x * scale, -center.y * scale, -mins.z * scale)
wrapper.scale = (scale, scale, scale)

for obj in bpy.context.scene.objects:
    obj.select_set(False)
wrapper.select_set(True)
bpy.context.view_layer.objects.active = wrapper

bpy.ops.object.light_add(type="SUN", location=(0, -4, 10))
sun = bpy.context.object
sun.name = "Key Sun"
sun.data.energy = 2.0
sun.rotation_euler = (math.radians(45), 0, math.radians(35))

bpy.ops.object.light_add(type="AREA", location=(-6, -8, 12))
area = bpy.context.object
area.name = "Soft Fill"
area.data.energy = 450
area.data.size = 6

target = mathutils.Vector((0, 0, (size.z * scale) * 0.48))
camera_distance = 26
bpy.ops.object.camera_add(location=(13, -20, 11))
camera = bpy.context.object
look_at(camera, target)
camera.data.lens = 35
camera.data.dof.use_dof = False
bpy.context.scene.camera = camera

bpy.context.scene.render.resolution_x = 1600
bpy.context.scene.render.resolution_y = 1200
bpy.context.scene.world.color = (0.72, 0.66, 0.57)

bpy.ops.wm.save_as_mainfile(filepath=VISIBLE_BLEND)
print(f"Saved visible scene: {VISIBLE_BLEND}")
