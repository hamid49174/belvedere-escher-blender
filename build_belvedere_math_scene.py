import math
from pathlib import Path

import bpy
import mathutils
from mathutils import Vector


WORK_DIR = Path(r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d")
SOURCE_BLEND = WORK_DIR / "belvedere_escher_tpe_visible.blend"
OUTPUT_BLEND = WORK_DIR / "belvedere_escher_mathe_praesentation.blend"


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


def clear_collection(name):
    collection = bpy.data.collections.get(name)
    if not collection:
        return
    for child in list(collection.children):
        clear_collection(child.name)
        collection.children.unlink(child)
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def collection(name, parent=None):
    existing = bpy.data.collections.get(name)
    if existing:
        return existing
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


def move_to_collection(obj, target):
    if obj.name not in target.objects:
        target.objects.link(obj)
    for current in list(obj.users_collection):
        if current != target:
            current.objects.unlink(obj)


def mat(name, color, alpha=1.0, metallic=0.0, roughness=0.55):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
    if alpha < 1.0:
        material.use_nodes = True
        material.show_transparent_back = True
        if hasattr(material, "blend_method"):
            material.blend_method = "BLEND"
        if hasattr(material, "surface_render_method"):
            material.surface_render_method = "BLENDED"
        if hasattr(material, "use_screen_refraction"):
            material.use_screen_refraction = True
    return material


def link_obj(obj, col):
    if obj.name not in col.objects:
        col.objects.link(obj)
    for current in list(obj.users_collection):
        if current != col:
            current.objects.unlink(obj)
    return obj


def cylinder_between(name, start, end, radius, material, col, vertices=32):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    length = direction.length
    if length <= 1e-8:
        raise ValueError(f"Cannot create zero length cylinder {name}")
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=length,
        location=(start + end) / 2,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    return link_obj(obj, col)


def dashed_line(name, start, end, radius, material, col, dash_count=10, vertices=16):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    length = direction.length
    unit = direction.normalized()
    dash_length = length / (dash_count * 1.7)
    step = length / dash_count
    parts = []
    for index in range(dash_count):
        a = start + unit * (index * step)
        b = start + unit * min(index * step + dash_length, length)
        parts.append(cylinder_between(f"{name}_dash_{index + 1:02d}", a, b, radius, material, col, vertices))
    return parts


def mesh_plane(name, vertices, material, col):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata([tuple(v) for v in vertices], [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(material)
    col.objects.link(obj)
    return obj


def sphere(name, location, radius, material, col, segments=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=16, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return link_obj(obj, col)


def look_at(obj, target, track="-Z"):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat(track, "Y").to_euler()


def text_label(name, body, location, size, material, col, camera_hint=Vector((6, -8, 6))):
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_Text"
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.006
    obj.data.materials.append(material)
    look_at(obj, camera_hint, track="Z")
    return link_obj(obj, col)


def add_edge_outline(prefix, vertices, material, col, radius=0.025):
    for index, (a, b) in enumerate([(0, 1), (1, 2), (2, 3), (3, 0)], start=1):
        cylinder_between(f"{prefix}_Kante_{index}", vertices[a], vertices[b], radius, material, col, vertices=16)


def raw_bounds():
    mins = Vector((float("inf"), float("inf"), float("inf")))
    maxs = Vector((float("-inf"), float("-inf"), float("-inf")))
    found = False
    for obj in bpy.context.scene.objects:
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
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    return mins, maxs


def add_camera(name, location, target, lens=45, ortho_scale=None):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object
    cam.name = name
    look_at(cam, target)
    if ortho_scale is not None:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho_scale
    else:
        cam.data.lens = lens
    cam.data.dof.use_dof = False
    link_obj(cam, camera_col)
    return cam


def add_area_light(name, location, target, energy, size):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.size = size
    look_at(light, target)
    link_obj(light, light_col)
    return light


def add_sun(name, rotation, energy):
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 15))
    sun = bpy.context.object
    sun.name = name
    sun.rotation_euler = rotation
    sun.data.energy = energy
    link_obj(sun, light_col)
    return sun


def create_correct_model(offset):
    local = lambda point: POINTS[point] + offset
    e_vertices = [local("A"), local("B"), local("C"), local("D")]
    f_vertices = [POINTS["A_prime"] + offset, POINTS["B_korrekt"] + offset, Vector((-6, 2, 4)) + offset, Vector((-6, 0, 4)) + offset]

    empty = bpy.data.objects.new("Korrektes_Modell_Lokales_Koordinatensystem", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.8
    empty.location = offset
    correct_col.objects.link(empty)

    mesh_plane("Korrekt_Ebene_E_z_0", e_vertices, mat_e, correct_col)
    mesh_plane("Korrekt_Ebene_F_z_4", f_vertices, mat_f, correct_col)
    add_edge_outline("Korrekt_E", e_vertices, mat_e_edge, correct_col)
    add_edge_outline("Korrekt_F", f_vertices, mat_f_edge, correct_col)
    cylinder_between("Korrekt_S1_A_nach_A_prime", local("A"), local("A_prime"), 0.045, mat_s1, correct_col)
    cylinder_between("Korrekt_S2_B_nach_B_korrekt", local("B"), local("B_korrekt"), 0.055, mat_correct_green, correct_col)

    for key, label in [
        ("A", "A"),
        ("B", "B"),
        ("A_prime", "A'"),
        ("B_korrekt", "B_korrekt"),
    ]:
        sphere("Korrekt_Punkt_" + key, local(key), 0.095, mat_point, correct_col)
    text_label("Korrekt_Label_Titel", "Mathematisch korrektes Modell", offset + Vector((-3, -0.8, 4.8)), 0.26, mat_text, correct_col, Vector((12, -9, 6)))
    text_label("Korrekt_Label_B_korrekt", "B_korrekt = (0, 2, 4)", local("B_korrekt") + Vector((0.45, 0.15, 0.2)), 0.18, mat_text, correct_col, Vector((12, -9, 6)))
    text_label("Korrekt_Label_S2", "S2 korrekt senkrecht", local("B") + Vector((0.7, 0.05, 2.1)), 0.18, mat_correct_green, correct_col, Vector((12, -9, 6)))
    text_label("Korrekt_Label_Vergleich", "oberer Punkt liegt direkt ueber B", offset + Vector((-3.3, 2.45, 2.1)), 0.16, mat_text, correct_col, Vector((12, -9, 6)))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
bpy.context.scene.name = "Belvedere Mathematik Praesentation"
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0

for generated_name in [
    "Escher-Modell",
    "Mathematisch korrektes Modell",
    "Kameras und Licht",
]:
    clear_collection(generated_name)

for obj in list(bpy.context.scene.objects):
    if obj.type in {"CAMERA", "LIGHT"}:
        bpy.data.objects.remove(obj, do_unlink=True)

escher_col = collection("Escher-Modell")
raw_col = collection("Rohmodell Belvedere", escher_col)
overlay_col = collection("Mathematisches Overlay Escher", escher_col)
correct_col = collection("Mathematisch korrektes Modell")
support_col = collection("Kameras und Licht")
camera_col = collection("Kameras", support_col)
light_col = collection("Licht", support_col)

raw_objects = [obj for obj in list(bpy.context.scene.objects) if obj.type in {"MESH", "EMPTY"}]
for obj in raw_objects:
    move_to_collection(obj, raw_col)

for obj in bpy.context.scene.objects:
    if obj.name == "Visible_Model_Frame":
        obj.name = "Belvedere_Rohmodell_Skaliert"
        obj.location.y += 8.5
    elif obj.parent is None and obj.type in {"MESH", "EMPTY"}:
        obj.location.y += 8.5

for mat_existing in bpy.data.materials:
    if mat_existing:
        mat_existing.diffuse_color = tuple(min(1.0, max(0.0, c)) for c in mat_existing.diffuse_color)

mat_e = mat("MAT_Ebene_E_transparent_blau", (0.05, 0.32, 1.0, 0.24), 0.24)
mat_f = mat("MAT_Ebene_F_transparent_gruen", (0.12, 0.80, 0.38, 0.22), 0.22)
mat_e_edge = mat("MAT_Ebene_E_Kante_blau", (0.0, 0.16, 1.0, 1.0))
mat_f_edge = mat("MAT_Ebene_F_Kante_gruen", (0.0, 0.62, 0.22, 1.0))
mat_s1 = mat("MAT_S1_senkrecht_blau", (0.0, 0.24, 1.0, 1.0))
mat_s2 = mat("MAT_S2_schraeg_rot", (1.0, 0.05, 0.02, 1.0))
mat_pq = mat("MAT_Abstand_PQ_orange", (1.0, 0.58, 0.0, 1.0))
mat_projection = mat("MAT_Projektion_violett", (0.62, 0.12, 1.0, 1.0))
mat_correct_green = mat("MAT_Korrekte_Saeule_gruen", (0.0, 0.72, 0.32, 1.0))
mat_point = mat("MAT_Punkte_weiss", (1.0, 0.96, 0.72, 1.0))
mat_point_bprime = mat("MAT_Punkt_B_prime_rot", (1.0, 0.14, 0.08, 1.0))
mat_text = mat("MAT_Text_dunkel", (0.02, 0.025, 0.03, 1.0))
mat_angle = mat("MAT_Winkel_gold", (1.0, 0.78, 0.05, 1.0))
mat_ground = mat("MAT_Boden_neutral", (0.52, 0.50, 0.46, 1.0))

e_vertices = [POINTS["A"], POINTS["B"], POINTS["C"], POINTS["D"]]
f_vertices = [POINTS["A_prime"], POINTS["B_korrekt"], Vector((-6, 2, 4)), Vector((-6, 0, 4))]

mesh_plane("Ebene_E_z_0_Rechteck_ABCD", e_vertices, mat_e, overlay_col)
mesh_plane("Ebene_F_z_4_obere_Ebene", f_vertices, mat_f, overlay_col)
add_edge_outline("E_z_0", e_vertices, mat_e_edge, overlay_col)
add_edge_outline("F_z_4", f_vertices, mat_f_edge, overlay_col)

cylinder_between("S1_A_nach_A_prime_senkrechte_Saeule", POINTS["A"], POINTS["A_prime"], 0.055, mat_s1, overlay_col)
cylinder_between("S2_B_nach_B_prime_schraege_Saeule", POINTS["B"], POINTS["B_prime"], 0.065, mat_s2, overlay_col)

dashed_line("Hilfslinie_B_prime_senkrechte_Projektion", POINTS["B_prime"], POINTS["B_projection"], 0.026, mat_projection, overlay_col, 9)
cylinder_between("Horizontale_Verschiebung_B_zu_proj_B_prime", POINTS["B"], POINTS["B_projection"], 0.04, mat_projection, overlay_col)
dashed_line("Korrekte_vertikale_Hilfslinie_B_nach_B_korrekt", POINTS["B"], POINTS["B_korrekt"], 0.025, mat_correct_green, overlay_col, 8)
sphere("Punkt_B_korrekt_Referenz", POINTS["B_korrekt"], 0.09, mat_correct_green, overlay_col)

cylinder_between("Abstandsstrecke_PQ_kuerzeste_Verbindung", POINTS["P"], POINTS["Q"], 0.075, mat_pq, overlay_col)

for key, label, offset, point_mat in [
    ("A", "A", Vector((0.22, -0.25, 0.18)), mat_point),
    ("B", "B", Vector((0.28, 0.28, 0.2)), mat_point),
    ("C", "C", Vector((-0.28, 0.28, 0.18)), mat_point),
    ("D", "D", Vector((-0.28, -0.25, 0.18)), mat_point),
    ("A_prime", "A'", Vector((0.32, -0.25, 0.18)), mat_point),
    ("B_prime", "B'", Vector((-0.32, -0.28, 0.18)), mat_point_bprime),
    ("P", "P", Vector((0.24, -0.28, 0.16)), mat_point),
    ("Q", "Q", Vector((-0.30, 0.28, 0.18)), mat_point),
]:
    sphere("Punkt_" + key, POINTS[key], 0.085, point_mat, overlay_col)
    text_label("Label_" + key, label, POINTS[key] + offset, 0.18, mat_text, overlay_col)

text_label("Label_E_z_0", "E: z = 0", Vector((-3, 1, 0.22)), 0.22, mat_e_edge, overlay_col)
text_label("Label_F_z_4", "F: z = 4", Vector((-3, 1, 4.25)), 0.22, mat_f_edge, overlay_col)
text_label("Label_S1", "S1 senkrecht", Vector((0.45, -0.35, 2.3)), 0.18, mat_s1, overlay_col)
text_label("Label_S2", "S2 schraeg", Vector((-1.65, 1.05, 2.55)), 0.18, mat_s2, overlay_col)
text_label("Label_B_prime_nicht_senkrecht", "B' = (-2, 0, 4) liegt nicht ueber B", Vector((-2.9, -0.4, 3.45)), 0.16, mat_s2, overlay_col)
text_label("Label_Verschiebung", "horizontale Verschiebung", Vector((-1.1, 1.0, 0.35)), 0.16, mat_projection, overlay_col)
text_label("Label_B_korrekt_Referenz", "B_korrekt = (0, 2, 4)", POINTS["B_korrekt"] + Vector((0.65, 0.2, 0.1)), 0.16, mat_correct_green, overlay_col)
text_label("Label_Abstand_PQ", "d(S1, S2) = \u221a2 \u2248 1,41 m", Vector((-0.75, 0.25, 2.42)), 0.18, mat_pq, overlay_col)

horizontal_dir = (POINTS["B_prime"] - POINTS["B"]).copy()
horizontal_dir.z = 0
horizontal_unit = horizontal_dir.normalized()
vertical_unit = Vector((0, 0, 1))
theta = math.radians(54.74)
arc_points = []
radius = 0.78
for i in range(22):
    t = theta * i / 21
    arc_points.append(POINTS["B"] + radius * (math.cos(t) * horizontal_unit + math.sin(t) * vertical_unit))
for index in range(len(arc_points) - 1):
    cylinder_between(f"Winkelbogen_S2_E_Segment_{index + 1:02d}", arc_points[index], arc_points[index + 1], 0.035, mat_angle, overlay_col, 16)
cylinder_between("Winkel_Grundrichtung_Projektion_S2_in_E", POINTS["B"], POINTS["B"] + horizontal_unit * 0.95, 0.025, mat_angle, overlay_col, 16)
text_label("Label_Winkel_S2_E", "Winkel(S2, E) = 54,74\u00b0", Vector((-1.25, 0.65, 1.15)), 0.17, mat_angle, overlay_col)

ground_vertices = [
    Vector((-9.5, -2.8, -0.035)),
    Vector((16, -2.8, -0.035)),
    Vector((16, 15, -0.035)),
    Vector((-9.5, 15, -0.035)),
]
mesh_plane("Neutraler_Boden", ground_vertices, mat_ground, support_col)

create_correct_model(Vector((9.0, 0.0, 0.0)))

raw_min, raw_max = raw_bounds()
raw_center = (raw_min + raw_max) * 0.5

add_sun("Sonnenlicht_weich", (math.radians(42), 0, math.radians(35)), 2.0)
add_area_light("Flaechenlicht_vorne", (0, -7, 8), (-1.5, 0.7, 2.2), 520, 5.0)
add_area_light("Flaechenlicht_Modell", (2.5, 1.5, 12), raw_center, 650, 7.5)

cam1 = add_camera("Kamera_1_Titelfolie_Hero", (13, -10, 8.5), raw_center + Vector((0, 0, 1.2)), lens=35)
cam2 = add_camera("Kamera_2_Fokus_S1_S2", (4.5, -6.2, 4.8), (-1.1, 0.8, 2.2), lens=55)
cam3 = add_camera("Kamera_3_Winkel_S2_E", (2.8, -4.2, 2.9), (-0.75, 1.18, 0.95), lens=70)
cam4 = add_camera("Kamera_4_Abstand_PQ", (3.2, -4.5, 3.2), (-0.55, 0.45, 2.05), lens=78)
cam5 = add_camera("Kamera_5_Vergleich_Escher_vs_Korrekt", (5.2, -10.5, 6.2), (2.4, 1.1, 2.3), ortho_scale=10.2)

for frame, cam, label in [
    (1, cam1, "1 Hero"),
    (20, cam2, "2 S1/S2"),
    (40, cam3, "3 Winkel"),
    (60, cam4, "4 Abstand"),
    (80, cam5, "5 Vergleich"),
]:
    marker = bpy.context.scene.timeline_markers.new(label, frame=frame)
    marker.camera = cam

bpy.context.scene.camera = cam1
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 80
bpy.context.scene.render.engine = "BLENDER_EEVEE"
if hasattr(bpy.context.scene, "eevee"):
    bpy.context.scene.eevee.taa_render_samples = 48
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.world.color = (0.78, 0.75, 0.69)

view_settings = bpy.context.scene.view_settings
view_settings.view_transform = "Filmic"
view_settings.look = "Medium High Contrast"
view_settings.exposure = 0
view_settings.gamma = 1

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
print(f"Saved presentation scene: {OUTPUT_BLEND}")
