from pathlib import Path

import bpy


WORK_DIR = Path(r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d")
SCENE_BLEND = WORK_DIR / "belvedere_escher_mathe_praesentation.blend"


def count_objects(collection):
    total = len(collection.objects)
    for child in collection.children:
        total += count_objects(child)
    return total


bpy.ops.wm.open_mainfile(filepath=str(SCENE_BLEND))

for name in ["Escher-Modell", "Mathematisch korrektes Modell", "Kameras und Licht"]:
    collection = bpy.data.collections.get(name)
    if collection:
        print(f"COLLECTION {name}: {count_objects(collection)} objects")
        for child in collection.children:
            print(f"  SUB {child.name}: {count_objects(child)} objects")

important_prefixes = [
    "Ebene_",
    "S1_",
    "S2_",
    "Punkt_",
    "Abstandsstrecke",
    "Winkel",
    "Label_",
    "Korrekt_",
    "Kamera_",
]

important = []
for obj in bpy.context.scene.objects:
    if any(obj.name.startswith(prefix) for prefix in important_prefixes):
        important.append(obj.name)

print("IMPORTANT_COUNT", len(important))
for name in sorted(important)[:120]:
    print("  OBJ", name)
