#!/usr/bin/env python3
import bpy
import mathutils

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'

# Close up camera on pin tip
cam = bpy.data.objects.get('Camera_Closeup')
if not cam:
    cam = bpy.data.objects.new('Camera_Closeup', bpy.data.cameras.new('Cam_Close'))
    scene.collection.objects.link(cam)

cam.data.lens = 85.0
scene.camera = cam

# Pin tip is around (-0.43, 0.0, 0.035) at frame 1, and moves with arm
# Let's create an empty on the arm tip to track
arm = bpy.data.objects['Swing_Stick_Arm_40in']
tt = cam.constraints.new('TRACK_TO')
tt.target = arm
tt.track_axis = 'TRACK_NEGATIVE_Z'
tt.up_axis = 'UP_Y'

# For frame 25, let's see where arm tip is
for f in [1, 20, 28, 32]:
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    arm_eval = arm.evaluated_get(dg)
    tip_w = arm_eval.matrix_world @ mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))
    # Place camera 0.3m away from tip
    cam.location = tip_w + mathutils.Vector((-0.2, 0.25, 0.15))
    scene.render.filepath = f'/home/steve/.gemini/antigravity/brain/91e1f823-b856-4d61-bc57-2d759f389fdf/pin_closeup_f{f}.png'
    bpy.ops.render.render(write_still=True)
    print(f'Rendered pin closeup at frame {f}')
