#!/usr/bin/env python3
import bpy
import math
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.render.fps = 60
TOTAL_FRAMES = 60

bpy.ops.rigidbody.world_add()
world = scene.rigidbody_world
world.substeps_per_frame = 20
world.solver_iterations = 50

# 1. Arm rotating around axle (0, 0, 0.762)
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, 0.762))
axle = bpy.context.active_object
bpy.ops.rigidbody.object_add()
axle.rigid_body.type = 'PASSIVE'

# Arm mesh
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.762))
arm = bpy.context.active_object
arm.dimensions = (0.04, 0.04, 0.9)
arm.location = (0, 0, 0.762)
bpy.ops.rigidbody.object_add()
arm.rigid_body.type = 'ACTIVE'
arm.rigid_body.mass = 0.3

# Hinge at axle
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0.762))
hinge = bpy.context.active_object
bpy.ops.rigidbody.constraint_add()
hinge.rigid_body_constraint.type = 'HINGE'
hinge.rigid_body_constraint.object1 = axle
hinge.rigid_body_constraint.object2 = arm
hinge.rotation_euler = (math.radians(90.0), 0, 0)

# Pin vector from tip:
p_tip = mathutils.Vector((-0.3922, 0.0, 0.0627))
pin_dir = mathutils.Vector((-0.0389, 0.0, -0.0279))
pin_len = pin_dir.length
pin_axis = pin_dir.normalized()

# Loop at p_tip
bpy.ops.mesh.primitive_torus_add(major_radius=0.0055, minor_radius=0.0013, location=p_tip)
loop = bpy.context.active_object
loop.name = "Test_Loop"
bpy.ops.rigidbody.object_add()
loop.rigid_body.type = 'ACTIVE'
loop.rigid_body.mass = 0.003
loop.rigid_body.collision_collections[0] = False
loop.rigid_body.collision_collections[1] = False

# Slider constraint between arm and loop
bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_tip)
slider = bpy.context.active_object
slider.name = "Slider_Pin"
bpy.ops.rigidbody.constraint_add()
sc = slider.rigid_body_constraint
sc.type = 'SLIDER'
sc.object1 = arm
sc.object2 = loop
# In Blender SLIDER constraint: motion is along local X axis!
# Find rotation that maps (1, 0, 0) to pin_axis:
q_rot = mathutils.Vector((1, 0, 0)).rotation_difference(pin_axis)
slider.rotation_euler = q_rot.to_euler()
sc.use_limit_lin_x = True
sc.limit_lin_x_lower = 0.0
sc.limit_lin_x_upper = pin_len
sc.disable_collisions = True

print(f"Pin length: {pin_len:.4f}m. Slider configured.")

# Segment 0 connected to loop:
p_seg0 = p_tip + mathutils.Vector((0.02, 0, 0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.0013, depth=0.02, location=p_seg0)
seg0 = bpy.context.active_object
bpy.ops.rigidbody.object_add()
seg0.rigid_body.type = 'ACTIVE'
seg0.rigid_body.mass = 0.001
seg0.rigid_body.collision_collections[0] = False
seg0.rigid_body.collision_collections[1] = False

# Joint loop <-> seg0
bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_tip)
j_loop = bpy.context.active_object
bpy.ops.rigidbody.constraint_add()
j_loop.rigid_body_constraint.type = 'POINT'
j_loop.rigid_body_constraint.object1 = loop
j_loop.rigid_body_constraint.object2 = seg0
j_loop.rigid_body_constraint.disable_collisions = True

# Step simulation:
for f in range(1, 30):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    l_eval = loop.evaluated_get(dg)
    a_eval = arm.evaluated_get(dg)
    s_eval = seg0.evaluated_get(dg)
    l_pos = l_eval.matrix_world.translation
    s_pos = s_eval.matrix_world.translation
    dist_loop_seg = (l_pos - s_pos).length
    print(f"Frame {f:2d}: loop={l_pos}, seg0={s_pos}, dist={dist_loop_seg:.4f}")

print("Test finished successfully!")
