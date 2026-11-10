#!/usr/bin/env python3
import sys
import os

with open('build_blender_physics_sim.py', 'r') as f:
    code = f.read()

# Let's inspect where loop is created and where j_release is created.
# We will write a modified build script to test the loop physics.
print("Reading build_blender_physics_sim.py...")
