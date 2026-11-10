#!/usr/bin/env python3
import bpy
import math
import os
import mathutils
import time

# We will test the simulation logic with collision_collections[1] = True
# on arm, pouch, and line1_segs, line2_segs!

# Let's import build_blender_physics_sim and run with collision enabled:
import sys
sys.path.append(os.path.abspath('.'))

# Let's read build_blender_physics_sim.py content, adjust collision settings in memory, and execute
with open('build_blender_physics_sim.py', 'r') as f:
    code = f.read()

# Replace arm collision:
old_arm = """    arm.rigid_body.collision_collections[0] = False
    arm.rigid_body.collision_collections[1] = False"""

new_arm = """    arm.rigid_body.collision_shape = 'CONVEX_HULL'
    arm.rigid_body.use_margin = True
    arm.rigid_body.collision_margin = 0.001
    arm.rigid_body.friction = 0.4
    arm.rigid_body.restitution = 0.2
    arm.rigid_body.collision_collections[0] = False
    arm.rigid_body.collision_collections[1] = True"""

# Replace pouch collision:
old_pouch = """        pouch.rigid_body.collision_collections[0] = False
        pouch.rigid_body.collision_collections[1] = False"""

new_pouch = """        pouch.rigid_body.collision_shape = 'CONVEX_HULL'
        pouch.rigid_body.use_margin = True
        pouch.rigid_body.collision_margin = 0.001
        pouch.rigid_body.friction = 0.4
        pouch.rigid_body.restitution = 0.2
        pouch.rigid_body.collision_collections[0] = False
        pouch.rigid_body.collision_collections[1] = True"""

# Replace s1 collision:
old_s1 = """        s1.rigid_body.collision_collections[0] = False
        s1.rigid_body.collision_collections[1] = False"""

new_s1 = """        s1.rigid_body.collision_shape = 'CAPSULE'
        s1.rigid_body.use_margin = True
        s1.rigid_body.collision_margin = 0.0005
        s1.rigid_body.friction = 0.4
        s1.rigid_body.restitution = 0.2
        s1.rigid_body.collision_collections[0] = False
        s1.rigid_body.collision_collections[1] = True"""

# Replace s2 collision:
old_s2 = """        s2.rigid_body.collision_collections[0] = False
        s2.rigid_body.collision_collections[1] = False"""

new_s2 = """        s2.rigid_body.collision_shape = 'CAPSULE'
        s2.rigid_body.use_margin = True
        s2.rigid_body.collision_margin = 0.0005
        s2.rigid_body.friction = 0.4
        s2.rigid_body.restitution = 0.2
        s2.rigid_body.collision_collections[0] = False
        s2.rigid_body.collision_collections[1] = True"""

code_mod = code.replace(old_arm, new_arm).replace(old_pouch, new_pouch).replace(old_s1, new_s1).replace(old_s2, new_s2)

with open('scratch/sim_collision_test.py', 'w') as f:
    f.write(code_mod)

print("Created scratch/sim_collision_test.py successfully.")
