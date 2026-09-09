import bpy

GLB_PATH = r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d\belvedere_escher_tpe.glb"
BLEND_PATH = r"C:\Users\admin\OneDrive - Office\Dokumente\Blender bevelder 3d\belvedere_escher_tpe.blend"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

bpy.ops.import_scene.gltf(filepath=GLB_PATH)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
