from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


WORK_DIR = Path(r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d")
SCENE_BLEND = WORK_DIR / "belvedere_escher_mathe_praesentation.blend"


def look_at(obj, target, track="-Z"):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat(track, "Y").to_euler()


POINTS = {
    "A": Vector((0, 0, 0)),
    "B": Vector((0, 2, 0)),
    "C": Vector((-6, 2, 0)),
    "D": Vector((-6, 0, 0)),
    "A_prime": Vector((0, 0, 4)),
    "B_prime": Vector((-2, 0, 4)),
    "B_korrekt": Vector((0, 2, 4)),
    "B_projection": Vector((-2, 0, 0)),
    "P": Vector((0, 0, 2)),
    "Q": Vector((-1, 1, 2)),
}


def set_camera(name, location, target, ortho_scale=None, lens=None):
    camera = bpy.data.objects[name]
    camera.location = location
    look_at(camera, target)
    if ortho_scale is not None:
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = ortho_scale
    if lens is not None:
        camera.data.type = "PERSP"
        camera.data.lens = lens


def fit_ortho_camera(name, view_dir, points, margin=1.25, distance=12.0):
    camera = bpy.data.objects[name]
    forward = Vector(view_dir).normalized()
    camera.rotation_euler = forward.to_track_quat("-Z", "Y").to_euler()
    rotation = camera.rotation_euler.to_quaternion()
    right = rotation @ Vector((1, 0, 0))
    up = rotation @ Vector((0, 1, 0))

    xs = [Vector(point).dot(right) for point in points]
    ys = [Vector(point).dot(up) for point in points]
    zs = [Vector(point).dot(forward) for point in points]

    x_center = (min(xs) + max(xs)) * 0.5
    y_center = (min(ys) + max(ys)) * 0.5
    z_center = sum(zs) / len(zs)
    center = right * x_center + up * y_center + forward * z_center

    camera.location = center - forward * distance
    camera.rotation_euler = forward.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    aspect = bpy.context.scene.render.resolution_x / bpy.context.scene.render.resolution_y
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    camera.data.ortho_scale = max(height * margin, (width * margin) / aspect, 1.0)


def refine_camera_frame(name, points, padding=0.1, iterations=5):
    scene = bpy.context.scene
    camera = bpy.data.objects[name]
    aspect = scene.render.resolution_x / scene.render.resolution_y
    desired_span = 1.0 - padding * 2.0

    for _ in range(iterations):
        projected = [world_to_camera_view(scene, camera, Vector(point)) for point in points]
        xs = [point.x for point in projected]
        ys = [point.y for point in projected]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        width = xmax - xmin
        height = ymax - ymin

        if width > desired_span or height > desired_span:
            camera.data.ortho_scale *= max(width / desired_span, height / desired_span) * 1.04
            bpy.context.view_layer.update()
            continue

        center_x = (xmin + xmax) * 0.5
        center_y = (ymin + ymax) * 0.5
        dx = center_x - 0.5
        dy = center_y - 0.5
        if abs(dx) < 0.01 and abs(dy) < 0.01:
            break

        rotation = camera.matrix_world.to_quaternion()
        right = rotation @ Vector((1, 0, 0))
        up = rotation @ Vector((0, 1, 0))
        camera.location += right * (dx * camera.data.ortho_scale * aspect)
        camera.location += up * (dy * camera.data.ortho_scale)
        bpy.context.view_layer.update()


bpy.ops.wm.open_mainfile(filepath=str(SCENE_BLEND))

distance_label = bpy.data.objects.get("Label_Abstand_PQ")
if distance_label:
    distance_label.location = Vector((-1.25, -0.35, 2.55))
    distance_label.data.size = 0.14

angle_label = bpy.data.objects.get("Label_Winkel_S2_E")
if angle_label:
    angle_label.location = Vector((-2.05, 0.85, 1.02))
    angle_label.data.size = 0.15

fit_ortho_camera(
    "Kamera_2_Fokus_S1_S2",
    Vector((-0.62, 0.72, -0.35)),
    [
        POINTS["A"],
        POINTS["B"],
        POINTS["C"],
        POINTS["D"],
        POINTS["A_prime"],
        POINTS["B_prime"],
        POINTS["B_korrekt"],
        POINTS["B_projection"],
        POINTS["P"],
        POINTS["Q"],
        Vector((-3.0, 1.0, 4.35)),
        Vector((-3.1, -0.45, 3.6)),
    ],
    margin=1.28,
    distance=14,
)
refine_camera_frame("Kamera_2_Fokus_S1_S2", [
    POINTS["A"],
    POINTS["B"],
    POINTS["C"],
    POINTS["D"],
    POINTS["A_prime"],
    POINTS["B_prime"],
    POINTS["B_korrekt"],
    POINTS["B_projection"],
    POINTS["P"],
    POINTS["Q"],
    Vector((-3.0, 1.0, 4.35)),
    Vector((-3.1, -0.45, 3.6)),
], padding=0.12)

horizontal_dir = (POINTS["B_prime"] - POINTS["B"]).copy()
horizontal_dir.z = 0
horizontal_unit = horizontal_dir.normalized()
angle_points = [
    POINTS["B"],
    POINTS["B_prime"],
    POINTS["B"] + horizontal_unit * 1.15,
    POINTS["B"] + horizontal_unit * 0.65 + Vector((0, 0, 0.65)),
    Vector((-2.05, 0.85, 1.02)),
]
fit_ortho_camera(
    "Kamera_3_Winkel_S2_E",
    Vector((-1.0, 1.0, -0.08)),
    angle_points,
    margin=1.55,
    distance=8,
)
refine_camera_frame("Kamera_3_Winkel_S2_E", angle_points, padding=0.14)
if angle_label:
    look_at(angle_label, bpy.data.objects["Kamera_3_Winkel_S2_E"].location, track="Z")

pq_points = [
    POINTS["P"],
    POINTS["Q"],
    Vector((0, 0, 1.1)),
    Vector((0, 0, 3.0)),
    Vector((-1.45, 1.45, 1.25)),
    Vector((-0.75, 0.25, 2.55)),
]
fit_ortho_camera(
    "Kamera_4_Abstand_PQ",
    Vector((0.85, 0.85, -0.28)),
    pq_points,
    margin=1.45,
    distance=8,
)
refine_camera_frame("Kamera_4_Abstand_PQ", pq_points, padding=0.16)

if distance_label:
    look_at(distance_label, bpy.data.objects["Kamera_4_Abstand_PQ"].location, track="Z")

correct_offset = Vector((9.0, 0.0, 0.0))
comparison_points = [
    POINTS["A"],
    POINTS["B"],
    POINTS["C"],
    POINTS["D"],
    POINTS["A_prime"],
    POINTS["B_prime"],
    POINTS["B_korrekt"],
    POINTS["A"] + correct_offset,
    POINTS["B"] + correct_offset,
    POINTS["C"] + correct_offset,
    POINTS["D"] + correct_offset,
    POINTS["A_prime"] + correct_offset,
    POINTS["B_korrekt"] + correct_offset,
    Vector((6.0, -0.8, 4.9)),
]
fit_ortho_camera(
    "Kamera_5_Vergleich_Escher_vs_Korrekt",
    Vector((-0.58, 0.74, -0.34)),
    comparison_points,
    margin=1.25,
    distance=16,
)
refine_camera_frame("Kamera_5_Vergleich_Escher_vs_Korrekt", comparison_points, padding=0.1)

bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_BLEND))
print("Adjusted mathematical cameras")
