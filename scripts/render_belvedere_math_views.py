from pathlib import Path

import bpy


WORK_DIR = Path(r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d")
SCENE_BLEND = WORK_DIR / "belvedere_escher_mathe_praesentation.blend"
RENDER_DIR = WORK_DIR / "renders"


def col(name):
    collection = bpy.data.collections.get(name)
    if not collection:
        raise RuntimeError(f"Collection not found: {name}")
    return collection


def cam(name):
    camera = bpy.data.objects.get(name)
    if not camera:
        raise RuntimeError(f"Camera not found: {name}")
    return camera


def set_visibility(raw=True, overlay=True, correct=True):
    col("Rohmodell Belvedere").hide_render = not raw
    col("Mathematisches Overlay Escher").hide_render = not overlay
    col("Mathematisch korrektes Modell").hide_render = not correct


TEMP_RENDER_PREFIXES = [
    "Winkelbogen",
    "Winkel_Grundrichtung",
    "Label_Winkel_S2_E",
    "Abstandsstrecke",
    "Label_Abstand_PQ",
]


def set_temp_object_visibility(hidden_prefixes=None):
    hidden_prefixes = hidden_prefixes or []
    for obj in bpy.context.scene.objects:
        if any(obj.name.startswith(prefix) for prefix in TEMP_RENDER_PREFIXES):
            obj.hide_render = any(obj.name.startswith(prefix) for prefix in hidden_prefixes)


def render_view(filename, camera_name, raw=True, overlay=True, correct=False, hide_prefixes=None):
    set_visibility(raw=raw, overlay=overlay, correct=correct)
    set_temp_object_visibility(hide_prefixes)
    bpy.context.scene.camera = cam(camera_name)
    bpy.context.scene.render.filepath = str(RENDER_DIR / filename)
    bpy.ops.render.render(write_still=True)
    print("Rendered", RENDER_DIR / filename)


bpy.ops.wm.open_mainfile(filepath=str(SCENE_BLEND))
RENDER_DIR.mkdir(exist_ok=True)

bpy.context.scene.render.engine = "BLENDER_EEVEE"
if hasattr(bpy.context.scene, "eevee"):
    bpy.context.scene.eevee.taa_render_samples = 48
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.film_transparent = False

marker_cameras = [(marker, marker.camera) for marker in bpy.context.scene.timeline_markers]
for marker, _camera in marker_cameras:
    marker.camera = None

render_view(
    "01_hero_escher_modell.png",
    "Kamera_1_Titelfolie_Hero",
    raw=True,
    overlay=False,
    correct=False,
)
render_view(
    "02_escher_mit_mathematischem_overlay.png",
    "Kamera_2_Fokus_S1_S2",
    raw=True,
    overlay=True,
    correct=False,
)
render_view(
    "03_vergleich_escher_vs_korrekt.png",
    "Kamera_5_Vergleich_Escher_vs_Korrekt",
    raw=False,
    overlay=True,
    correct=True,
)
render_view(
    "04_nahaufnahme_winkel_54_74.png",
    "Kamera_3_Winkel_S2_E",
    raw=False,
    overlay=True,
    correct=False,
    hide_prefixes=["Abstandsstrecke", "Label_Abstand_PQ"],
)
render_view(
    "05_nahaufnahme_abstand_wurzel2.png",
    "Kamera_4_Abstand_PQ",
    raw=False,
    overlay=True,
    correct=False,
    hide_prefixes=["Winkelbogen", "Winkel_Grundrichtung", "Label_Winkel_S2_E"],
)

set_visibility(raw=True, overlay=True, correct=True)
set_temp_object_visibility()
for marker, camera in marker_cameras:
    marker.camera = camera
bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_BLEND))
print("Saved render-ready scene state")
