from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

WORK_DIR = Path(r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d")
SCENE_BLEND = WORK_DIR / "belvedere_escher_mathe_praesentation.blend"

POINTS = {
    "A": Vector((0, 0, 0)),
    "B": Vector((0, 2, 0)),
    "A_prime": Vector((0, 0, 4)),
    "B_prime": Vector((-2, 0, 4)),
    "P": Vector((0, 0, 2)),
    "Q": Vector((-1, 1, 2)),
}

bpy.ops.wm.open_mainfile(filepath=str(SCENE_BLEND))
scene = bpy.context.scene

for camera_name in [
    "Kamera_2_Fokus_S1_S2",
    "Kamera_3_Winkel_S2_E",
    "Kamera_4_Abstand_PQ",
    "Kamera_5_Vergleich_Escher_vs_Korrekt",
]:
    camera = bpy.data.objects[camera_name]
    print(camera_name, "loc", tuple(round(v, 2) for v in camera.location), "rot", tuple(round(v, 2) for v in camera.rotation_euler))
    for name, point in POINTS.items():
        co = world_to_camera_view(scene, camera, point)
        print(" ", name, tuple(round(v, 3) for v in co))
