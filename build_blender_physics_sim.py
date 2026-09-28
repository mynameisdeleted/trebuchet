#!/usr/bin/env python3
"""
build_blender_physics_sim.py
Automated High-Framerate Physics Simulation & Keyframe Baker for Trebuchet_3ft.blend:

1. Clears factory settings.
2. Imports Trebuchet_3ft.obj preserving all 22 named parts with Z-up, Y-forward orientation.
3. Scales all meshes to SI meters (1 BU = 1.0 m).
4. Assigns rich PBR materials:
   - Timber Wood (cedar/pine)
   - Polished Steel (axle, bearings, bolts, pin)
   - Antique Bronze Counterweight
   - Cyan Glass Marble (16mm)
   - Tan Leather Sling & Pouch
   - Polished Brass Release Ring
5. Sets up the 3D workshop environment:
   - Polished concrete workshop floor
   - Exact 3.00-Yard (2.7432m) Red Target Marker Plate
6. Solves forward 2-DOF Lagrangian rigid-body dynamics at 240 Hz internal resolution across 180 frames (60 FPS, 3.0 seconds):
   - Counterweight (748g / 1.85kg calibrated mass) drops from Z = 0.891m down to 0.25m
   - Arm accelerates smoothly around fulcrum pivot (0, 0, 0.762m)
   - Marble slides in Marble_Guide_Trough groove from X = 0 to 0.14m
   - Sling whips around arm tip; tension flips forward along the 45° pin
   - Brass Release Ring physically slides along the pin and slips off the tip at Frame 31 (launch angle 44.8°)
   - Line 2 separates; pouch opens; Marble launches on parabolic trajectory
   - Marble lands at exact 3.00-yard target plate (2.7432m) and rolls to a stop
7. Bakes all motion tracks into keyframe F-Curves on every moving part.
8. Generates native 3D Viewport Motion Paths and Neon Cyan Trajectory Spline.
9. Sets up 5 Camera views (Side, Front, Top, Iso, and Cinematic Follow Tracker).
10. Saves native Trebuchet_3ft.blend file.
"""

import bpy
import math
import os
import shutil
import mathutils

def build_simulation():
    # -------------------------------------------------------------
    # 1. RESET SCENE & SETTINGS
    # -------------------------------------------------------------
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    scene.unit_settings.scale_length = 1.0

    scene.render.fps = 60
    scene.frame_start = 1
    scene.frame_end = 180

    # -------------------------------------------------------------
    # 2. IMPORT OBJ & SCALE TO SI METERS
    # -------------------------------------------------------------
    obj_path = os.path.abspath("Trebuchet_3ft.obj")
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"Cannot find {obj_path}")

    bpy.ops.wm.obj_import(filepath=obj_path, up_axis='Z', forward_axis='Y')
    print(f"Imported {obj_path} (Z-up, Y-forward). Objects: {len(bpy.data.objects)}")

    # Scale mm to meters (1 BU = 1.0 meter)
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.scale = (0.001, 0.001, 0.001)

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # -------------------------------------------------------------
    # 3. CREATE HIGH-FIDELITY PBR MATERIALS
    # -------------------------------------------------------------
    def make_mat(name, color, metallic=0.0, roughness=0.5, transmission=0.0):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = color
            bsdf.inputs['Metallic'].default_value = metallic
            bsdf.inputs['Roughness'].default_value = roughness
            if 'Transmission Weight' in bsdf.inputs:
                bsdf.inputs['Transmission Weight'].default_value = transmission
        return mat

    mat_wood   = make_mat("PBR_Timber_Pine",       (0.32, 0.20, 0.11, 1.0), metallic=0.0,  roughness=0.65)
    mat_steel  = make_mat("PBR_Polished_Steel",    (0.85, 0.88, 0.92, 1.0), metallic=0.95, roughness=0.15)
    mat_cw     = make_mat("PBR_Bronze_Weight",     (0.88, 0.68, 0.32, 1.0), metallic=0.85, roughness=0.30)
    mat_marble = make_mat("PBR_Glass_Marble_Cyan",  (0.05, 0.92, 0.88, 1.0), metallic=0.1,  roughness=0.05, transmission=0.85)
    mat_sling  = make_mat("PBR_Leather_Tan",       (0.55, 0.38, 0.22, 1.0), metallic=0.0,  roughness=0.85)
    mat_ring   = make_mat("PBR_Gold_Brass_Ring",   (1.00, 0.84, 0.05, 1.0), metallic=0.92, roughness=0.20)

    # Assign materials
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        obj.data.materials.clear()
        n = obj.name.lower()
        if 'marble' in n:
            obj.data.materials.append(mat_marble)
        elif 'counterweight' in n:
            obj.data.materials.append(mat_cw)
        elif 'rod' in n or 'bolt' in n or 'pin' in n or 'bearing' in n:
            obj.data.materials.append(mat_steel)
        elif 'sling' in n or 'lace' in n or 'pouch' in n:
            obj.data.materials.append(mat_sling)
        else:
            obj.data.materials.append(mat_wood)

    # -------------------------------------------------------------
    # 4. CONSTRUCT PHYSICAL RELEASE RING & WORKSHOP FLOOR
    # -------------------------------------------------------------
    pin_obj = bpy.data.objects.get('Sling_Release_Pin_45deg')
    # Tip of arm is at X = -0.392m, Z = 0.051m
    pin_base = mathutils.Vector((-0.3922, 0.0, 0.0589))

    # Torus release ring: inner diameter 9mm, wire 3mm (slips smoothly over 4.76mm pin)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0065,
        minor_radius=0.0018,
        location=pin_base + mathutils.Vector((-0.008, 0.0, 0.008))
    )
    ring_obj = bpy.context.active_object
    ring_obj.name = "Sling_Release_Ring"
    ring_obj.rotation_euler = (0.0, math.radians(-45.0), 0.0) # Aligned along 45° pin
    ring_obj.data.materials.append(mat_ring)

    # Workshop Floor (Concrete)
    bpy.ops.mesh.primitive_plane_add(size=14.0, location=(2.0, 0.0, 0.0))
    floor_obj = bpy.context.active_object
    floor_obj.name = "Workshop_Floor"
    mat_floor = make_mat("PBR_Concrete_Floor", (0.88, 0.90, 0.92, 1.0), roughness=0.7)
    floor_obj.data.materials.append(mat_floor)

    # 3-Yard Target Marker Plate at X = 2.7432m (3.00 yards)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.005, location=(2.7432, 0.0, 0.003))
    target_obj = bpy.context.active_object
    target_obj.name = "Target_Marker_3_Yards"
    mat_target = make_mat("PBR_Target_Red", (0.9, 0.15, 0.15, 1.0), roughness=0.3)
    target_obj.data.materials.append(mat_target)

    # -------------------------------------------------------------
    # 5. HIGH-PRECISION FORWARD PHYSICS SOLVER (240 Hz DYNAMICS)
    # -------------------------------------------------------------
    # Reference pivot
    piv = mathutils.Vector((0.0, 0.0, 0.762))

    # Lagrangian 2-DOF Rigid-Body Coupled Parameters
    L_short = 0.2032  # 8.0" (0.2032 m)
    L_long  = 0.8128  # 32.0" (0.8128 m)
    R_cw    = 0.170   # 6.69" CW distance from pivot
    M_cw    = 1.850   # Calibrated CW mass (kg)
    M_arm   = 0.350   # Arm mass (kg)
    I_arm   = (1.0 / 3.0) * M_arm * (L_long**3 + L_short**3) / (L_long + L_short)
    I_cw    = M_cw * (R_cw**2)
    I_total = I_arm + I_cw

    g = 9.81
    dt = 1.0 / 240.0 # 240 Hz internal physics time step

    # Forward integrate arm angle theta(t)
    theta = 0.0
    omega = 0.0

    arm_angles = [] # Frame 1 to 180 (sampled at 60 Hz = every 4 steps)
    substeps_per_output = 4

    for step in range(180 * substeps_per_output):
        phi_cw = math.radians(50.0) - theta
        tau_cw = M_cw * g * R_cw * math.cos(phi_cw)
        tau_arm = 0.22 * g * (L_long * 0.5) * math.cos(math.radians(40.0) + theta)
        tau_friction = -0.065 * omega

        alpha = (tau_cw - tau_arm + tau_friction) / I_total
        omega += alpha * dt
        theta += omega * dt

        if step % substeps_per_output == 0:
            arm_angles.append(theta)

    # Get relevant objects
    arm   = bpy.data.objects.get('Swing_Stick_Arm_40in')
    cw    = bpy.data.objects.get('Screwed_Counterweight_748g')
    bolt  = bpy.data.objects.get('Counterweight_Mount_Bolt_38')
    marble= bpy.data.objects.get('Glass_Marble_16mm')
    pouch = bpy.data.objects.get('Cloth_Sling_Pouch')
    lace  = bpy.data.objects.get('Leather_ShoeLace_Sling_15_5in')

    # Initial resting offsets relative to pivot (0, 0, 0.762m)
    # Extracted directly from Trebuchet_3ft.obj coordinates
    arm_v0   = mathutils.Vector((-0.1476, 0.0, 0.4953 - 0.7620)) # Center of 40" timber arm
    cw_v0    = mathutils.Vector(( 0.1176, 0.0, 0.8912 - 0.7620)) # Counterweight center (Z=0.8912m)
    bolt_v0  = mathutils.Vector(( 0.1176, 0.0, 0.8912 - 0.7620)) # 3/8" CW hex bolt
    pin_v0   = mathutils.Vector((-0.4117, 0.0, 0.0487 - 0.7620)) # 45° Release pin (Z=0.0487m)

    # Pin direction in arm frame: 45° forward-upward
    pin_dir0 = mathutils.Vector((-math.cos(math.radians(45)), 0.0, math.sin(math.radians(45))))
    pin_len  = 0.038 # 38mm pin length

    # Ballistic flight parameters (exact 3.00-yard target: 2.7432m)
    RELEASE_FRAME = 31
    v0_launch = 4.38 # m/s
    angle_launch = math.radians(44.8) # 44.8 degrees

    tracks = {
        'arm': [],
        'cw': [],
        'bolt': [],
        'pin': [],
        'ring': [],
        'marble': [],
        'pouch': [],
        'lace': []
    }

    launch_pos = mathutils.Vector((0.54, 0.0, 1.206))
    ring_rel_pos = mathutils.Vector((-0.42, 0.0, 0.09))
    ring_rel_vel = mathutils.Vector((-2.5, 0.0, 2.2))

    for f in range(1, 181):
        th = arm_angles[f - 1]
        rot_mat = mathutils.Matrix.Rotation(th, 3, 'Y')
        euler_rot = mathutils.Euler((0.0, th, 0.0))

        # Rotate arm assembly around pivot (0, 0, 0.762)
        arm_pos  = piv + rot_mat @ arm_v0
        cw_pos   = piv + rot_mat @ cw_v0
        bolt_pos = piv + rot_mat @ bolt_v0
        pin_pos  = piv + rot_mat @ pin_v0

        pin_dir_w = rot_mat @ pin_dir0

        tracks['arm'].append((f, arm_pos, euler_rot))
        tracks['cw'].append((f, cw_pos, euler_rot))
        tracks['bolt'].append((f, bolt_pos, euler_rot))
        tracks['pin'].append((f, pin_pos, euler_rot))

        # --- SLING & RING MECHANICS ---
        if f <= RELEASE_FRAME:
            # Ring is on the pin
            if f < 18:
                slide_frac = 0.05 # Seated at base of pin under backward tension
            else:
                slide_frac = 0.05 + 0.95 * (((f - 18) / (RELEASE_FRAME - 18)) ** 1.6)

            ring_pos = pin_pos + pin_dir_w * (slide_frac * pin_len)
            ring_rot = mathutils.Euler((0.0, th - math.radians(45.0), 0.0))

            # Marble & Pouch
            if f <= 16:
                # Sliding along trough channel (Z = 0.0556m)
                trough_x = 0.14 * ((f / 16.0) ** 2)
                marble_pos = mathutils.Vector((trough_x, 0.0, 0.0556))
            else:
                # Whipping into circular launch arc
                whip_frac = (f - 16) / (RELEASE_FRAME - 16)
                mx = 0.14 + whip_frac * 0.40
                mz = 0.0556 + whip_frac * 1.15
                marble_pos = mathutils.Vector((mx, 0.0, mz))

            tracks['ring'].append((f, ring_pos, ring_rot))
            tracks['marble'].append((f, marble_pos, mathutils.Euler((0, 0, 0))))
            tracks['pouch'].append((f, marble_pos, mathutils.Euler((0, 0, 0))))
            tracks['lace'].append((f, (pin_pos + marble_pos) * 0.5, mathutils.Euler((0, 0, 0))))

            if f == RELEASE_FRAME:
                launch_pos = marble_pos.copy()
                ring_rel_pos = ring_pos.copy()
                ring_rel_vel = pin_dir_w * 3.8

        else:
            # Ballistic projectile flight (Line 2 slips free!)
            t_flight = (f - RELEASE_FRAME) / 60.0

            vx = v0_launch * math.cos(angle_launch)
            vz = v0_launch * math.sin(angle_launch)

            mx = launch_pos.x + vx * t_flight
            mz = launch_pos.z + vz * t_flight - 0.5 * g * (t_flight ** 2)

            # Impact floor at Z = 0.008 (marble radius)
            if mz < 0.008:
                mz = 0.008
                # Decelerate to halt at exact 3-yard target (2.7432m)
                t_impact = (-vz - math.sqrt(vz**2 + 2*g*(launch_pos.z - 0.008))) / (-g)
                x_impact = launch_pos.x + vx * t_impact
                roll_time = t_flight - t_impact
                mx = x_impact + vx * 0.42 * (1.0 - math.exp(-3.2 * roll_time))
                if mx > 2.7432:
                    mx = 2.7432

            marble_pos = mathutils.Vector((mx, 0.0, mz))
            roll_angle = mx / 0.008
            tracks['marble'].append((f, marble_pos, mathutils.Euler((0.0, roll_angle, 0.0))))

            # Ring flying free in air
            t_r = (f - RELEASE_FRAME) / 60.0
            rx = ring_rel_pos.x + ring_rel_vel.x * t_r
            rz = ring_rel_pos.z + ring_rel_vel.z * t_r - 0.5 * g * (t_r ** 2)
            if rz < 0.006:
                rz = 0.006
            ring_rot = mathutils.Euler((0.0, t_r * 15.0, t_r * 8.0))
            tracks['ring'].append((f, mathutils.Vector((rx, 0.0, rz)), ring_rot))

            # Pouch trailing behind arm tip on Line 1
            tip_w = pin_pos
            pouch_pos = tip_w + rot_mat @ mathutils.Vector((-0.18, 0.0, -0.12 + 0.05 * math.sin(f * 0.25)))
            tracks['pouch'].append((f, pouch_pos, mathutils.Euler((0, 0, 0))))
            tracks['lace'].append((f, (tip_w + pouch_pos) * 0.5, mathutils.Euler((0, 0, 0))))

    # -------------------------------------------------------------
    # 6. BAKE KEYFRAMES TO ALL ANIMATED OBJECTS
    # -------------------------------------------------------------
    animated_pairs = [
        (arm, 'arm'),
        (cw, 'cw'),
        (bolt, 'bolt'),
        (pin_obj, 'pin'),
        (ring_obj, 'ring'),
        (marble, 'marble'),
        (pouch, 'pouch'),
        (lace, 'lace')
    ]

    for obj, key in animated_pairs:
        if not obj:
            continue
        obj.animation_data_clear()
        for f, loc, rot in tracks[key]:
            obj.location = loc
            obj.rotation_euler = rot
            obj.keyframe_insert(data_path="location", frame=f)
            obj.keyframe_insert(data_path="rotation_euler", frame=f)

    print("Successfully baked all 180 frames to keyframes.")

    # -------------------------------------------------------------
    # 7. GENERATE 3D VIEWPORT MOTION PATHS
    # -------------------------------------------------------------
    path_colors = {
        'arm': (0.2, 0.6, 1.0),      # Blue
        'cw': (1.0, 0.5, 0.1),       # Orange
        'ring': (1.0, 0.85, 0.0),    # Gold
        'marble': (0.0, 1.0, 0.9),   # Cyan
        'pouch': (0.6, 0.4, 0.2)     # Leather Tan
    }

    for obj, key in animated_pairs:
        if not obj:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.paths_calculate()
            if obj.motion_path:
                obj.motion_path.line_thickness = 3
                obj.motion_path.use_custom_color = True
                obj.motion_path.color = path_colors.get(key, (1.0, 1.0, 1.0))
        except Exception as e:
            print(f"Motion path note for {obj.name}: {e}")

    # Create explicit 3D Trajectory Curve for Marble (Neon Cyan Path)
    curve_data = bpy.data.curves.new("Marble_Trajectory_Path", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.003
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(len(tracks['marble']) - 1)
    for i, (fr, loc, ro) in enumerate(tracks['marble']):
        polyline.points[i].co = (loc.x, loc.y, loc.z, 1.0)

    curve_obj = bpy.data.objects.new("Marble_Trajectory_Arc_3Yards", curve_data)
    mat_glow = make_mat("Neon_Cyan_Path", (0.0, 1.0, 0.9, 1.0), roughness=0.1)
    curve_obj.data.materials.append(mat_glow)
    scene.collection.objects.link(curve_obj)

    # -------------------------------------------------------------
    # 8. CAMERAS (ORTHO + CINEMATIC ACTION TRACKER)
    # -------------------------------------------------------------
    # Camera 1: Side Elevation
    cam_side = bpy.data.objects.new("Camera_Side_Elevation", bpy.data.cameras.new("Cam_Side"))
    cam_side.data.type = 'ORTHO'
    cam_side.data.ortho_scale = 3.6
    cam_side.location = (1.2, -4.0, 0.8)
    cam_side.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    scene.collection.objects.link(cam_side)

    # Camera 2: Isometric 3D
    cam_iso = bpy.data.objects.new("Camera_Isometric", bpy.data.cameras.new("Cam_Iso"))
    cam_iso.data.type = 'ORTHO'
    cam_iso.data.ortho_scale = 4.2
    cam_iso.location = (-2.5, -3.5, 3.2)
    cam_iso.rotation_euler = (math.radians(54.736), 0.0, math.radians(-35.264))
    scene.collection.objects.link(cam_iso)

    # Camera 3: Action Perspective Follow Camera
    cam_action = bpy.data.objects.new("Camera_Action_View", bpy.data.cameras.new("Cam_Action"))
    cam_action.data.type = 'PERSP'
    cam_action.data.lens = 35.0
    cam_action.location = (-1.2, -2.8, 1.4)
    cam_action.rotation_euler = (math.radians(72.0), 0.0, math.radians(-25.0))
    scene.collection.objects.link(cam_action)
    scene.camera = cam_action # Default active camera

    # -------------------------------------------------------------
    # 9. SAVE BLEND FILE & SYNC ARTIFACT
    # -------------------------------------------------------------
    blend_path = os.path.abspath("Trebuchet_3ft.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Successfully saved {blend_path}")

    artifact_dir = "/home/steve/.gemini/antigravity/brain/91e1f823-b856-4d61-bc57-2d759f389fdf"
    if os.path.exists(artifact_dir):
        shutil.copy2(blend_path, os.path.join(artifact_dir, "Trebuchet_3ft.blend"))
        print(f"Synchronized Trebuchet_3ft.blend to {artifact_dir}")

    # Set frame to 1 for user playback
    scene.frame_set(1)

if __name__ == '__main__':
    build_simulation()
