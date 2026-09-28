#!/usr/bin/env python3
"""
setup_blender_ortho_scene.py
Automated Blender Script:
1. Clears default scene.
2. Imports Trebuchet_3ft.obj preserving all 24 individual named parts.
3. Sets up precision orthographic CAD cameras:
   - Camera_Side_Elevation (Longitudinal View, X-Z plane)
   - Camera_Front_Elevation (Transverse View, Y-Z plane)
   - Camera_Top_Plan (Plan View, X-Y plane)
   - Camera_Isometric (30° Axonometric View)
4. Saves native Trebuchet_3ft.blend file.
"""

import bpy
import math
import os

def setup_scene():
    # Delete all default objects
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # Set metric units
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001 # 1 Blender unit = 1 meter, so 1mm = 0.001

    # Import Trebuchet_3ft.obj
    obj_path = os.path.abspath("Trebuchet_3ft.obj")
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"Cannot find {obj_path}")

    # Blender 4+ / 5+ obj import
    bpy.ops.wm.obj_import(filepath=obj_path)
    print(f"Imported {obj_path} into Blender scene. Object count: {len(bpy.data.objects)}")

    # Create CAD Materials
    mat_wood = bpy.data.materials.new(name="CAD_Wood")
    mat_wood.diffuse_color = (0.05, 0.15, 0.28, 1.0) # Blueprint structural navy

    mat_metal = bpy.data.materials.new(name="CAD_Steel")
    mat_metal.diffuse_color = (0.8, 0.85, 0.9, 1.0)

    mat_cw = bpy.data.materials.new(name="CAD_Counterweight")
    mat_cw.diffuse_color = (1.0, 0.82, 0.4, 1.0) # Gold

    mat_sling = bpy.data.materials.new(name="CAD_Sling")
    mat_sling.diffuse_color = (0.83, 0.64, 0.45, 1.0) # Leather tan

    mat_marble = bpy.data.materials.new(name="CAD_Marble")
    mat_marble.diffuse_color = (0.0, 0.96, 0.83, 1.0) # Cyan

    # Assign materials to objects based on name
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        name = obj.name.lower()
        if 'marble' in name:
            obj.data.materials.append(mat_marble)
        elif 'counterweight' in name or 'weight' in name:
            obj.data.materials.append(mat_cw)
        elif 'rod' in name or 'bolt' in name or 'pin' in name or 'bearing' in name:
            obj.data.materials.append(mat_metal)
        elif 'sling' in name or 'lace' in name or 'pouch' in name:
            obj.data.materials.append(mat_sling)
        else:
            obj.data.materials.append(mat_wood)

    # 1. Camera: Side Elevation (Looking along -Y, X horizontal, Z vertical)
    # Pivot is at X=0, Y=0, Z=762mm. Trebuchet center is roughly Z=475mm.
    cam_side_data = bpy.data.cameras.new("Camera_Side_Elevation")
    cam_side_data.type = 'ORTHO'
    cam_side_data.ortho_scale = 1200.0 # view 1.2 meters wide
    cam_side_obj = bpy.data.objects.new("Camera_Side_Elevation", cam_side_data)
    cam_side_obj.location = (0.0, -2000.0, 475.0)
    cam_side_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bpy.context.collection.objects.link(cam_side_obj)

    # 2. Camera: Front Elevation (Looking along +X down the track, Y horizontal, Z vertical)
    cam_front_data = bpy.data.cameras.new("Camera_Front_Elevation")
    cam_front_data.type = 'ORTHO'
    cam_front_data.ortho_scale = 1100.0
    cam_front_obj = bpy.data.objects.new("Camera_Front_Elevation", cam_front_data)
    cam_front_obj.location = (-2000.0, 0.0, 475.0)
    cam_front_obj.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    bpy.context.collection.objects.link(cam_front_obj)

    # 3. Camera: Top Plan (Looking along -Z, X horizontal, Y vertical)
    cam_top_data = bpy.data.cameras.new("Camera_Top_Plan")
    cam_top_data.type = 'ORTHO'
    cam_top_data.ortho_scale = 1200.0
    cam_top_obj = bpy.data.objects.new("Camera_Top_Plan", cam_top_data)
    cam_top_obj.location = (0.0, 0.0, 2000.0)
    cam_top_obj.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.collection.objects.link(cam_top_obj)

    # 4. Camera: Axonometric Isometric View
    cam_iso_data = bpy.data.cameras.new("Camera_Isometric")
    cam_iso_data.type = 'ORTHO'
    cam_iso_data.ortho_scale = 1300.0
    cam_iso_obj = bpy.data.objects.new("Camera_Isometric", cam_iso_data)
    # Standard isometric position: equal angles
    cam_iso_obj.location = (-1500.0, -1500.0, 1500.0)
    cam_iso_obj.rotation_euler = (math.radians(54.736), 0.0, math.radians(-45.0))
    bpy.context.collection.objects.link(cam_iso_obj)

    # Set default camera
    scene.camera = cam_side_obj

    # Save blend file
    blend_path = os.path.abspath("Trebuchet_3ft.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved Blender scene to {blend_path}")

    # Copy to brain artifact directory as well
    artifact_dir = '/home/steve/.gemini/antigravity/brain/91e1f823-b856-4d61-bc57-2d759f389fdf'
    if os.path.exists(artifact_dir):
        import shutil
        shutil.copy(blend_path, os.path.join(artifact_dir, "Trebuchet_3ft.blend"))
        print(f"Synchronized Trebuchet_3ft.blend to {artifact_dir}")

if __name__ == '__main__':
    setup_scene()
