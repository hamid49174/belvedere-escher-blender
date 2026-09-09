import math
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


WORK_DIR = Path(r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d")
SOURCE_BLEND = WORK_DIR / "belvedere_escher_tpe_visible.blend"
OUTPUT_BLEND = WORK_DIR / "belvedere_escher_mathe_am_modell.blend"


LOCAL = {
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
        raise RuntimeError("No mesh objects found.")
    return mins, maxs


def collection(name, parent=None):
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


def link_obj(obj, col):
    if obj.name not in col.objects:
        col.objects.link(obj)
    for current in list(obj.users_collection):
        if current != col:
            current.objects.unlink(obj)
    return obj


def move_to_collection(obj, target):
    if obj.name not in target.objects:
        target.objects.link(obj)
    for current in list(obj.users_collection):
        if current != target:
            current.objects.unlink(obj)


def mat(name, color, alpha=1.0, roughness=0.58):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Alpha"].default_value = alpha
        bsdf.inputs["Roughness"].default_value = roughness
    if alpha < 1.0:
        material.show_transparent_back = True
        if hasattr(material, "blend_method"):
            material.blend_method = "BLEND"
        if hasattr(material, "surface_render_method"):
            material.surface_render_method = "BLENDED"
    return material


def look_at(obj, target, track="-Z"):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat(track, "Y").to_euler()


def transform_point(local_point):
    point = Vector(local_point)
    return coordinate_origin + point * coordinate_scale


def transform_point_with_offset(local_point, offset):
    return transform_point(Vector(local_point) + Vector(offset))


def cylinder_between(name, start, end, radius, material, col, vertices=32):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    length = direction.length
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


def cone_arrow(name, start, end, radius, material, col):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    length = direction.length
    bpy.ops.mesh.primitive_cone_add(
        vertices=32,
        radius1=radius,
        radius2=0,
        depth=length,
        location=(start + end) / 2,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    return link_obj(obj, col)


def line_with_arrow(name, start, end, radius, material, col):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    unit = direction.normalized()
    head_len = radius * 7.0
    cylinder_between(name + "_Linie", start, end - unit * head_len, radius, material, col, vertices=16)
    cone_arrow(name + "_Pfeil", end - unit * head_len, end, radius * 3.0, material, col)


def dashed_line(name, start, end, radius, material, col, dash_count=9):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    unit = direction.normalized()
    length = direction.length
    dash_len = length / (dash_count * 1.7)
    step = length / dash_count
    for index in range(dash_count):
        a = start + unit * (index * step)
        b = start + unit * min(index * step + dash_len, length)
        cylinder_between(f"{name}_Strich_{index + 1:02d}", a, b, radius, material, col, vertices=16)


def mesh_quad(name, local_points, material, col, offset=Vector((0, 0, 0))):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    verts = [tuple(transform_point(Vector(point) + offset)) for point in local_points]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(material)
    col.objects.link(obj)
    return obj


def slab(name, local_points, thickness, material, col, offset=Vector((0, 0, 0))):
    top = [transform_point(Vector(point) + offset) for point in local_points]
    bottom = [point - Vector((0, 0, thickness)) for point in top]
    verts = [tuple(point) for point in top + bottom]
    faces = [
        (0, 1, 2, 3),
        (7, 6, 5, 4),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(material)
    col.objects.link(obj)
    return obj


def edge_outline(prefix, local_points, material, col, radius, offset=Vector((0, 0, 0))):
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    for index, (a, b) in enumerate(edges, start=1):
        cylinder_between(
            f"{prefix}_Kante_{index}",
            transform_point(Vector(local_points[a]) + offset),
            transform_point(Vector(local_points[b]) + offset),
            radius,
            material,
            col,
            vertices=16,
        )


def sphere(name, local_point, radius, material, col, offset=Vector((0, 0, 0))):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32,
        ring_count=16,
        radius=radius,
        location=transform_point(Vector(local_point) + offset),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return link_obj(obj, col)


def text_label(name, body, local_point, size, material, col, offset=Vector((0, 0, 0)), camera_hint=None):
    bpy.ops.object.text_add(location=transform_point(Vector(local_point) + offset))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = size * 0.025
    obj.data.materials.append(material)
    if camera_hint is None:
        camera_hint = transform_point(Vector((-3.0, -7.0, 4.0)))
    look_at(obj, camera_hint, track="Z")
    return link_obj(obj, col)


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


def fit_ortho_camera(name, view_dir, points, padding=0.12, distance=12.0):
    cam = bpy.data.objects[name]
    forward = Vector(view_dir).normalized()
    cam.rotation_euler = forward.to_track_quat("-Z", "Y").to_euler()
    rotation = cam.rotation_euler.to_quaternion()
    right = rotation @ Vector((1, 0, 0))
    up = rotation @ Vector((0, 1, 0))
    xs = [Vector(point).dot(right) for point in points]
    ys = [Vector(point).dot(up) for point in points]
    zs = [Vector(point).dot(forward) for point in points]
    center = right * ((min(xs) + max(xs)) * 0.5)
    center += up * ((min(ys) + max(ys)) * 0.5)
    center += forward * (sum(zs) / len(zs))
    cam.location = center - forward * distance
    cam.rotation_euler = forward.to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    aspect = bpy.context.scene.render.resolution_x / bpy.context.scene.render.resolution_y
    cam.data.ortho_scale = max((max(ys) - min(ys)) / (1 - 2 * padding), ((max(xs) - min(xs)) / aspect) / (1 - 2 * padding))

    for _ in range(4):
        projected = [world_to_camera_view(bpy.context.scene, cam, point) for point in points]
        min_x, max_x = min(p.x for p in projected), max(p.x for p in projected)
        min_y, max_y = min(p.y for p in projected), max(p.y for p in projected)
        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5
        dx = center_x - 0.5
        dy = center_y - 0.5
        if abs(dx) < 0.01 and abs(dy) < 0.01:
            break
        rotation = cam.matrix_world.to_quaternion()
        right = rotation @ Vector((1, 0, 0))
        up = rotation @ Vector((0, 1, 0))
        cam.location += right * (dx * cam.data.ortho_scale * aspect)
        cam.location += up * (dy * cam.data.ortho_scale)
        bpy.context.view_layer.update()


def build_architecture_over_reference(col):
    e_points = [LOCAL["A"], LOCAL["B"], LOCAL["C"], LOCAL["D"]]
    f_points = [LOCAL["A_prime"], LOCAL["B_korrekt"], Vector((-6, 2, 4)), Vector((-6, 0, 4))]
    slab("Analyse_Untere_Etage_ABCD_Steinplatte", e_points, 0.07 * coordinate_scale, mat_stone, col)
    slab("Analyse_Obere_Etage_F_Steinplatte", f_points, 0.07 * coordinate_scale, mat_stone, col)
    for name, a, b in [
        ("Analyse_Stuetze_A_Aprime", LOCAL["A"], LOCAL["A_prime"]),
        ("Analyse_Stuetze_D", LOCAL["D"], Vector((-6, 0, 4))),
        ("Analyse_Stuetze_C", LOCAL["C"], Vector((-6, 2, 4))),
    ]:
        cylinder_between(name, transform_point(a), transform_point(b), 0.045 * coordinate_scale, mat_stone_dark, col)
    cylinder_between(
        "Analyse_Escher_Schraegsaeule_B_Bprime",
        transform_point(LOCAL["B"]),
        transform_point(LOCAL["B_prime"]),
        0.05 * coordinate_scale,
        mat_stone_dark,
        col,
    )


def build_math_overlay(col, label_camera_hint):
    e_points = [LOCAL["A"], LOCAL["B"], LOCAL["C"], LOCAL["D"]]
    f_points = [LOCAL["A_prime"], LOCAL["B_korrekt"], Vector((-6, 2, 4)), Vector((-6, 0, 4))]

    mesh_quad("Ebene_E_z_0_am_Gebaeude", e_points, mat_e, col)
    mesh_quad("Ebene_F_z_4_am_Gebaeude", f_points, mat_f, col)
    edge_outline("E_z_0", e_points, mat_e_edge, col, 0.018 * coordinate_scale)
    edge_outline("F_z_4", f_points, mat_f_edge, col, 0.018 * coordinate_scale)

    cylinder_between("S1_A_nach_Aprime_senkrecht", transform_point(LOCAL["A"]), transform_point(LOCAL["A_prime"]), 0.045 * coordinate_scale, mat_s1, col)
    cylinder_between("S2_B_nach_Bprime_schraeg", transform_point(LOCAL["B"]), transform_point(LOCAL["B_prime"]), 0.055 * coordinate_scale, mat_s2, col)
    dashed_line("Bprime_senkrechte_Projektion", transform_point(LOCAL["B_prime"]), transform_point(LOCAL["B_projection"]), 0.022 * coordinate_scale, mat_projection, col)
    cylinder_between("Horizontale_Verschiebung_B_zur_Projektion", transform_point(LOCAL["B"]), transform_point(LOCAL["B_projection"]), 0.032 * coordinate_scale, mat_projection, col)
    dashed_line("Vergleich_B_nach_Bkorrekt", transform_point(LOCAL["B"]), transform_point(LOCAL["B_korrekt"]), 0.02 * coordinate_scale, mat_correct, col)
    cylinder_between("Abstand_PQ_kuerzeste_Verbindung", transform_point(LOCAL["P"]), transform_point(LOCAL["Q"]), 0.055 * coordinate_scale, mat_pq, col)

    for key, label, offset, material in [
        ("A", "A", Vector((0.28, -0.18, 0.16)), mat_point),
        ("B", "B", Vector((0.22, 0.22, 0.16)), mat_point),
        ("C", "C", Vector((-0.22, 0.22, 0.16)), mat_point),
        ("D", "D", Vector((-0.22, -0.18, 0.16)), mat_point),
        ("A_prime", "A'", Vector((0.30, -0.12, 0.18)), mat_point),
        ("B_prime", "B'", Vector((-0.28, -0.22, 0.18)), mat_bprime),
        ("P", "P", Vector((0.24, -0.18, 0.14)), mat_point),
        ("Q", "Q", Vector((-0.28, 0.22, 0.14)), mat_point),
    ]:
        sphere("Punkt_" + key, LOCAL[key], 0.08 * coordinate_scale, material, col)
        text_label("Label_" + key, label, LOCAL[key] + offset, 0.18 * coordinate_scale, mat_text, col, camera_hint=label_camera_hint)

    sphere("Punkt_B_korrekt", LOCAL["B_korrekt"], 0.08 * coordinate_scale, mat_correct, col)
    text_label("Label_E_z_0", "E: z = 0", Vector((-3, 1, 0.22)), 0.22 * coordinate_scale, mat_e_edge, col, camera_hint=label_camera_hint)
    text_label("Label_F_z_4", "F: z = 4", Vector((-3, 1, 4.22)), 0.22 * coordinate_scale, mat_f_edge, col, camera_hint=label_camera_hint)
    text_label("Label_S1", "S1 senkrecht", Vector((0.55, -0.35, 2.1)), 0.16 * coordinate_scale, mat_s1, col, camera_hint=label_camera_hint)
    text_label("Label_S2", "S2 schraeg", Vector((-1.55, 0.75, 2.35)), 0.16 * coordinate_scale, mat_s2, col, camera_hint=label_camera_hint)
    text_label("Label_Bprime_nicht_ueber_B", "B' = (-2, 0, 4) liegt nicht senkrecht ueber B", Vector((-2.8, -0.55, 3.35)), 0.14 * coordinate_scale, mat_s2, col, camera_hint=label_camera_hint)
    text_label("Label_Bkorrekt", "B_korrekt = (0, 2, 4)", Vector((0.95, 2.2, 4.25)), 0.14 * coordinate_scale, mat_correct, col, camera_hint=label_camera_hint)
    text_label("Label_Verschiebung", "horizontale Verschiebung", Vector((-1.1, 1.05, 0.25)), 0.14 * coordinate_scale, mat_projection, col, camera_hint=label_camera_hint)
    text_label("Label_Abstand", "d(S1, S2) = \u221a2 \u2248 1,41 m", Vector((-0.72, -0.42, 2.62)), 0.15 * coordinate_scale, mat_pq, col, camera_hint=label_camera_hint)

    horizontal = (LOCAL["B_prime"] - LOCAL["B"]).copy()
    horizontal.z = 0
    horizontal = horizontal.normalized()
    theta = math.radians(54.74)
    arc = []
    for i in range(24):
        t = theta * i / 23
        arc.append(LOCAL["B"] + 0.72 * (math.cos(t) * horizontal + math.sin(t) * Vector((0, 0, 1))))
    for index in range(len(arc) - 1):
        cylinder_between(
            f"Winkelbogen_S2_E_{index + 1:02d}",
            transform_point(arc[index]),
            transform_point(arc[index + 1]),
            0.027 * coordinate_scale,
            mat_angle,
            col,
            vertices=16,
        )
    cylinder_between("Winkel_Grundlinie_Projektion", transform_point(LOCAL["B"]), transform_point(LOCAL["B"] + horizontal * 0.95), 0.022 * coordinate_scale, mat_angle, col)
    text_label("Label_Winkel", "Winkel(S2, E) = 54,74\u00b0", Vector((-1.95, 0.75, 1.0)), 0.15 * coordinate_scale, mat_angle, col, camera_hint=label_camera_hint)


def build_axes(col, label_camera_hint):
    axis_radius = 0.018 * coordinate_scale
    line_with_arrow("Achse_x", transform_point(Vector((-6.7, 0, 0))), transform_point(Vector((0.9, 0, 0))), axis_radius, mat_axis, col)
    line_with_arrow("Achse_y", transform_point(Vector((0, -0.45, 0))), transform_point(Vector((0, 2.8, 0))), axis_radius, mat_axis, col)
    line_with_arrow("Achse_z", transform_point(Vector((0, 0, -0.25))), transform_point(Vector((0, 0, 4.9))), axis_radius, mat_axis, col)
    text_label("Achsen_Label_x", "x", Vector((1.05, 0, 0.05)), 0.18 * coordinate_scale, mat_axis, col, camera_hint=label_camera_hint)
    text_label("Achsen_Label_y", "y", Vector((0, 2.95, 0.05)), 0.18 * coordinate_scale, mat_axis, col, camera_hint=label_camera_hint)
    text_label("Achsen_Label_z", "z", Vector((0, 0, 5.08)), 0.18 * coordinate_scale, mat_axis, col, camera_hint=label_camera_hint)


def build_correct_model(col, local_offset, label_camera_hint):
    e_points = [LOCAL["A"], LOCAL["B"], LOCAL["C"], LOCAL["D"]]
    f_points = [LOCAL["A_prime"], LOCAL["B_korrekt"], Vector((-6, 2, 4)), Vector((-6, 0, 4))]
    mesh_quad("Korrekt_Ebene_E_z_0", e_points, mat_e, col, offset=local_offset)
    mesh_quad("Korrekt_Ebene_F_z_4", f_points, mat_f, col, offset=local_offset)
    edge_outline("Korrekt_E", e_points, mat_e_edge, col, 0.018 * coordinate_scale, offset=local_offset)
    edge_outline("Korrekt_F", f_points, mat_f_edge, col, 0.018 * coordinate_scale, offset=local_offset)
    cylinder_between("Korrekt_S1", transform_point_with_offset(LOCAL["A"], local_offset), transform_point_with_offset(LOCAL["A_prime"], local_offset), 0.045 * coordinate_scale, mat_s1, col)
    cylinder_between("Korrekt_S2_B_nach_Bkorrekt", transform_point_with_offset(LOCAL["B"], local_offset), transform_point_with_offset(LOCAL["B_korrekt"], local_offset), 0.055 * coordinate_scale, mat_correct, col)
    for key in ["A", "B", "A_prime", "B_korrekt"]:
        sphere("Korrekt_Punkt_" + key, LOCAL[key], 0.075 * coordinate_scale, mat_point, col, offset=local_offset)
    text_label("Korrekt_Titel", "Mathematisch korrektes Modell", Vector((-3, -0.65, 4.8)), 0.2 * coordinate_scale, mat_text, col, offset=local_offset, camera_hint=label_camera_hint)
    text_label("Korrekt_Label_B", "B_korrekt = (0, 2, 4)", Vector((0.85, 2.15, 4.2)), 0.14 * coordinate_scale, mat_text, col, offset=local_offset, camera_hint=label_camera_hint)
    text_label("Korrekt_Label_S2", "S2 korrekt senkrecht", Vector((0.75, 2.25, 2.0)), 0.14 * coordinate_scale, mat_correct, col, offset=local_offset, camera_hint=label_camera_hint)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
bpy.context.scene.name = "Belvedere Mathematik am Modell"
bpy.context.scene.unit_settings.system = "METRIC"

for obj in list(bpy.context.scene.objects):
    if obj.type in {"CAMERA", "LIGHT"}:
        bpy.data.objects.remove(obj, do_unlink=True)

escher_col = collection("Escher-Modell")
raw_col = collection("Rohmodell Belvedere", escher_col)
recon_col = collection("Ergaenzte Architektur am Koordinatensystem", escher_col)
overlay_col = collection("Mathematisches Overlay am Gebaeude", escher_col)
correct_col = collection("Mathematisch korrektes Modell")
support_col = collection("Kameras und Licht")
camera_col = collection("Kameras", support_col)
light_col = collection("Licht", support_col)

raw_objects = [obj for obj in list(bpy.context.scene.objects) if obj.type in {"MESH", "EMPTY"}]
for obj in raw_objects:
    move_to_collection(obj, raw_col)
    if obj.name == "Visible_Model_Frame":
        obj.name = "Belvedere_Rohmodell"

mesh_objects = [obj for obj in raw_objects if obj.type == "MESH"]
terrain_materials = {"0061_OliveDrab", "material"}
architecture_objects = []
terrain_objects = []
for obj in mesh_objects:
    material_name = obj.data.materials[0].name if obj.data.materials else ""
    if material_name in terrain_materials:
        terrain_objects.append(obj)
    else:
        architecture_objects.append(obj)

arch_min, arch_max = bounds_for_objects(architecture_objects)
raw_min, raw_max = bounds_for_objects(mesh_objects)

coordinate_scale = (arch_max.x - arch_min.x) / 6.0
lower_z = 8.212
coordinate_origin = Vector((arch_max.x, arch_max.y - 2.0 * coordinate_scale, lower_z))

for obj in terrain_objects:
    for material in obj.data.materials:
        material.diffuse_color = (0.62, 0.72, 0.56, 1)
for obj in architecture_objects:
    for material in obj.data.materials:
        material.diffuse_color = (0.82, 0.79, 0.74, 1)

mat_axis = mat("MAT_Achsen_schwarz", (0.0, 0.0, 0.0, 1.0))
mat_stone = mat("MAT_Ergaenzung_heller_Stein", (0.78, 0.75, 0.68, 0.82), 0.82)
mat_stone_dark = mat("MAT_Ergaenzung_Stuetzen", (0.64, 0.61, 0.56, 1.0))
mat_e = mat("MAT_Ebene_E_blau_transparent", (0.05, 0.30, 1.0, 0.26), 0.26)
mat_f = mat("MAT_Ebene_F_gruen_transparent", (0.02, 0.78, 0.42, 0.24), 0.24)
mat_e_edge = mat("MAT_E_Kante_blau", (0.0, 0.18, 1.0, 1.0))
mat_f_edge = mat("MAT_F_Kante_gruen", (0.0, 0.68, 0.34, 1.0))
mat_s1 = mat("MAT_S1_blau", (0.0, 0.28, 1.0, 1.0))
mat_s2 = mat("MAT_S2_rot", (1.0, 0.08, 0.03, 1.0))
mat_projection = mat("MAT_Projektion_magenta", (0.72, 0.10, 1.0, 1.0))
mat_correct = mat("MAT_Korrekt_gruen", (0.0, 0.78, 0.45, 1.0))
mat_pq = mat("MAT_Abstand_gold", (1.0, 0.70, 0.0, 1.0))
mat_angle = mat("MAT_Winkel_gelb", (1.0, 0.86, 0.05, 1.0))
mat_point = mat("MAT_Punkte_hell", (1.0, 0.96, 0.82, 1.0))
mat_bprime = mat("MAT_Bprime_rot", (1.0, 0.15, 0.08, 1.0))
mat_text = mat("MAT_Text_dunkel", (0.02, 0.02, 0.02, 1.0))
mat_ground = mat("MAT_Boden_neutral", (0.55, 0.53, 0.49, 1.0))

label_camera_hint = transform_point(Vector((4.5, -7.0, 4.2)))
build_architecture_over_reference(recon_col)
build_math_overlay(overlay_col, label_camera_hint)
build_axes(overlay_col, label_camera_hint)
build_correct_model(correct_col, Vector((8.5, 0, 0)), label_camera_hint)

ground_mesh = bpy.data.meshes.new("Boden_Mesh")
ground_z = min(raw_min.z, transform_point(Vector((0, 0, 0))).z) - 0.04
ground_verts = [
    (raw_min.x - 2.0, raw_min.y - 1.5, ground_z),
    (raw_max.x + 8.5, raw_min.y - 1.5, ground_z),
    (raw_max.x + 8.5, raw_max.y + 1.5, ground_z),
    (raw_min.x - 2.0, raw_max.y + 1.5, ground_z),
]
ground_mesh.from_pydata(ground_verts, [], [(0, 1, 2, 3)])
ground_mesh.update()
ground = bpy.data.objects.new("Neutraler_Boden", ground_mesh)
ground.data.materials.append(mat_ground)
support_col.objects.link(ground)

bpy.ops.object.light_add(type="SUN", location=(0, 0, 14))
sun = bpy.context.object
sun.name = "Sonnenlicht_weich"
sun.rotation_euler = (math.radians(42), 0, math.radians(35))
sun.data.energy = 2.1
link_obj(sun, light_col)

for name, loc, target, energy, size in [
    ("Flaechenlicht_vorne", Vector((5, -7, 10)), transform_point(Vector((-2, 1, 2))), 450, 5),
    ("Flaechenlicht_Gebaeude", Vector((-4, -5, 12)), (arch_min + arch_max) * 0.5, 560, 7),
]:
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.size = size
    look_at(light, target)
    link_obj(light, light_col)

bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

hero_cam = add_camera("Kamera_1_Titelfolie_Hero", Vector((7.2, -12.0, 9.0)), (arch_min + arch_max) * 0.5 + Vector((0, 0, 0.8)), lens=38)
math_cam = add_camera("Kamera_2_Koordinaten_am_Gebaeude", Vector((6.0, -8.0, 5.6)), transform_point(Vector((-2.8, 0.95, 2.2))), ortho_scale=5)
angle_cam = add_camera("Kamera_3_Winkel_54_74", Vector((6.2, -8.8, 5.4)), transform_point(Vector((-1.1, 1.0, 0.95))), ortho_scale=3)
distance_cam = add_camera("Kamera_4_Abstand_PQ", Vector((6.4, 6.4, transform_point(Vector((0, 0, 2))).z + 2.0)), transform_point(Vector((-0.5, 0.5, 2))), ortho_scale=2.4)
comparison_cam = add_camera("Kamera_5_Vergleich_Escher_vs_Korrekt", Vector((8.5, -11.0, 7.3)), transform_point(Vector((2.0, 1.1, 2.2))), ortho_scale=8.0)

math_points = [transform_point(point) for point in [LOCAL["A"], LOCAL["B"], LOCAL["C"], LOCAL["D"], LOCAL["A_prime"], LOCAL["B_prime"], LOCAL["B_korrekt"], LOCAL["P"], LOCAL["Q"]]]
fit_ortho_camera("Kamera_2_Koordinaten_am_Gebaeude", Vector((-0.65, 0.72, -0.33)), math_points + [arch_min, arch_max], padding=0.09, distance=12)
fit_ortho_camera("Kamera_3_Winkel_54_74", Vector((-1.0, 1.0, -0.08)), [transform_point(LOCAL["B"]), transform_point(LOCAL["B_prime"]), transform_point(Vector((-1.9, 0.75, 1.0))), transform_point(LOCAL["B_projection"])], padding=0.16, distance=6)
fit_ortho_camera(
    "Kamera_4_Abstand_PQ",
    Vector((-0.65, 0.72, -0.33)),
    [
        transform_point(LOCAL["A"]),
        transform_point(LOCAL["A_prime"]),
        transform_point(LOCAL["B"]),
        transform_point(LOCAL["B_prime"]),
        transform_point(LOCAL["P"]),
        transform_point(LOCAL["Q"]),
        transform_point(Vector((-0.72, -0.42, 2.62))),
        transform_point(Vector((-1.6, 0.75, 2.35))),
        transform_point(Vector((0.55, -0.35, 2.1))),
        transform_point(Vector((-1.4, 1.2, 1.7))),
    ],
    padding=0.16,
    distance=7,
)
correct_points = math_points + [transform_point(Vector(key) + Vector((8.5, 0, 0))) for key in [LOCAL["A"], LOCAL["B"], LOCAL["D"], LOCAL["A_prime"], LOCAL["B_korrekt"]]]
fit_ortho_camera("Kamera_5_Vergleich_Escher_vs_Korrekt", Vector((-0.65, 0.72, -0.33)), correct_points, padding=0.08, distance=14)

for frame, cam, label in [
    (1, hero_cam, "1 Hero"),
    (20, math_cam, "2 Koordinaten am Gebaeude"),
    (40, angle_cam, "3 Winkel"),
    (60, distance_cam, "4 Abstand PQ"),
    (80, comparison_cam, "5 Vergleich"),
]:
    marker = bpy.context.scene.timeline_markers.new(label, frame=frame)
    marker.camera = cam

bpy.context.scene.camera = math_cam
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 80
bpy.context.scene.render.engine = "BLENDER_EEVEE"
if hasattr(bpy.context.scene, "eevee"):
    bpy.context.scene.eevee.taa_render_samples = 64
bpy.context.scene.world.color = (0.78, 0.76, 0.70)
bpy.context.scene.view_settings.view_transform = "Filmic"
bpy.context.scene.view_settings.look = "Medium High Contrast"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
print("Saved aligned scene:", OUTPUT_BLEND)
print("Coordinate origin:", tuple(round(v, 4) for v in coordinate_origin))
print("Coordinate scale:", round(coordinate_scale, 4))
