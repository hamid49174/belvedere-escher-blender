from pathlib import Path

import bpy


WORK_DIR = Path(r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d")
SCENE_BLEND = WORK_DIR / "belvedere_escher_mathe_am_modell.blend"
RENDER_DIR = WORK_DIR / "renders_aligned"


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


def set_collection_visibility(raw=True, recon=True, overlay=True, correct=True):
    col("Rohmodell Belvedere").hide_render = not raw
    col("Ergaenzte Architektur am Koordinatensystem").hide_render = not recon
    col("Mathematisches Overlay am Gebaeude").hide_render = not overlay
    col("Mathematisch korrektes Modell").hide_render = not correct


def set_object_prefix_visibility(hidden_prefixes=None):
    hidden_prefixes = hidden_prefixes or []
    for obj in bpy.context.scene.objects:
        obj.hide_render = any(obj.name.startswith(prefix) for prefix in hidden_prefixes)


def render_view(filename, camera_name, raw=True, recon=True, overlay=True, correct=False, hide_prefixes=None):
    set_collection_visibility(raw=raw, recon=recon, overlay=overlay, correct=correct)
    set_object_prefix_visibility(hide_prefixes)
    bpy.context.scene.camera = cam(camera_name)
    bpy.context.scene.render.filepath = str(RENDER_DIR / filename)
    bpy.ops.render.render(write_still=True)
    print("Rendered", RENDER_DIR / filename)


bpy.ops.wm.open_mainfile(filepath=str(SCENE_BLEND))
RENDER_DIR.mkdir(exist_ok=True)

marker_cameras = [(marker, marker.camera) for marker in bpy.context.scene.timeline_markers]
for marker, _camera in marker_cameras:
    marker.camera = None

bpy.context.scene.render.engine = "BLENDER_EEVEE"
if hasattr(bpy.context.scene, "eevee"):
    bpy.context.scene.eevee.taa_render_samples = 64
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

render_view(
    "01_hero_escher_modell_korrigiert.png",
    "Kamera_1_Titelfolie_Hero",
    raw=True,
    recon=True,
    overlay=False,
    correct=False,
)
render_view(
    "02_koordinaten_und_mathe_am_gebaeude.png",
    "Kamera_2_Koordinaten_am_Gebaeude",
    raw=True,
    recon=True,
    overlay=True,
    correct=False,
)
render_view(
    "03_vergleich_escher_vs_korrekt_am_modell.png",
    "Kamera_5_Vergleich_Escher_vs_Korrekt",
    raw=False,
    recon=True,
    overlay=True,
    correct=True,
)
render_view(
    "04_nahaufnahme_winkel_54_74_am_modell.png",
    "Kamera_3_Winkel_54_74",
    raw=False,
    recon=True,
    overlay=True,
    correct=False,
    hide_prefixes=["Abstand_PQ", "Label_Abstand"],
)
render_view(
    "05_nahaufnahme_abstand_wurzel2_am_modell.png",
    "Kamera_4_Abstand_PQ",
    raw=False,
    recon=True,
    overlay=True,
    correct=False,
    hide_prefixes=[
        "Winkelbogen",
        "Winkel_Grundlinie",
        "Label_Winkel",
        "Label_Bprime",
        "Label_Verschiebung",
        "Label_E",
        "Label_F",
        "Achsen_Label",
    ],
)

set_collection_visibility(raw=True, recon=True, overlay=True, correct=True)
set_object_prefix_visibility()
for marker, camera in marker_cameras:
    marker.camera = camera
bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_BLEND))
print("Saved final aligned scene state")
