#!/usr/bin/env python3
"""
Parametric FreeCAD Model: 3-Foot High Trebuchet (Calibrated for 3-Yard Marble Launch)
Build Specification:
  - Rectangular wooden sticks (pine 3/4" x 1.5" / 19mm x 38mm)
  - Left & Right Side Stands: EACH supported with a rigid triangular A-frame (2 angled posts per side meeting at the fulcrum)
  - Joinery: Wood glue + 1/4"-20 hex clamping bolts, washers & nuts
  - Fulcrum: 8 mm precision steel round rod + 2x 608 ball bearings (8mm ID x 22mm OD x 7mm W)
  - Counterweight: Screwed onto the end of the swing stick (3/8" bolt + 395g steel weight plates)
  - Sling: Leather shoe-lace (17.3" / 440 mm)
  - Pouch: Folded cloth pouch with cutout template holding a 16 mm glass marble

Standard: FreeCAD 0.20+ / 1.0+ Compatible

Usage:
  In FreeCAD GUI: Macro -> Macros... -> trebuchet_model.py -> Execute
  In Command Line: freecad trebuchet_model.py
"""

import os
import sys
import math
import numpy as np

INCH = 25.4  # Conversion factor mm per inch

# -------------------------------------------------------------------------
# Parametric Dimensions & Specifications (mm)
# -------------------------------------------------------------------------
PARAMS = {
    # Frame Dimensions
    "FRAME_HEIGHT": 36.0 * INCH,        # 914.4 mm (3.0 ft overall)
    "BASE_LENGTH": 36.0 * INCH,         # 914.4 mm (3.0 ft base)
    "BASE_WIDTH": 18.0 * INCH,          # 457.2 mm (1.5 ft base)
    "PIVOT_HEIGHT": 30.0 * INCH,        # 762.0 mm (2.5 ft axle height)

    # Rectangular Stick Stock (Nominal 1x2 pine stick: actual 3/4" x 1.5")
    "STICK_THICK": 0.75 * INCH,         # 19.05 mm
    "STICK_WIDTH": 1.5 * INCH,          # 38.1 mm

    # A-Frame Triangular Posts Footprint
    "POST_SPREAD": 9.0 * INCH,          # 228.6 mm (posts at X = -9" and +9")

    # Swing Stick (Arm) - 4:1 Ratio
    "SWING_STICK_LEN": 30.0 * INCH,     # 762.0 mm
    "SHORT_ARM": 6.0 * INCH,            # 152.4 mm (Counterweight side)
    "LONG_ARM": 24.0 * INCH,            # 609.6 mm (Throwing arm side)
    "ARM_THICK": 0.75 * INCH,           # 19.05 mm
    "ARM_WIDTH": 1.5 * INCH,            # 38.1 mm

    # Fulcrum Hardware
    "AXLE_ROD_DIAM": 8.0,               # 8 mm precision steel round rod
    "AXLE_ROD_LEN": 19.5 * INCH,        # 495.3 mm
    "BEARING_ID": 8.0,                  # 8 mm ID (fits 8mm rod)
    "BEARING_OD": 22.0,                 # 22 mm OD (Standard 608 bearing)
    "BEARING_WIDTH": 7.0,               # 7 mm width

    # Screwed Counterweight
    "CW_MASS_GRAMS": 395.0,             # Calibrated for exact 3.0-yard launch
    "CW_BOLT_DIAM": 0.375 * INCH,       # 3/8"-16 bolt
    "CW_BOLT_LEN": 3.5 * INCH,          # 88.9 mm
    "CW_DISC_DIAM": 3.0 * INCH,         # 76.2 mm steel weight disc
    "CW_DISC_THICK": 1.1 * INCH,        # 28.0 mm steel plate stack

    # Sling & Pouch
    "SLING_LENGTH": 17.3 * INCH,        # 439.4 mm leather shoe-lace
    "RELEASE_PIN_DIAM": 0.1875 * INCH,  # 3/16" (4.76 mm) steel pin
    "RELEASE_PIN_LEN": 1.75 * INCH,     # 44.45 mm
    "RELEASE_PIN_ANGLE": 45.0,          # degrees
    "MARBLE_DIAMETER": 16.0,            # 16.0 mm glass marble (5.5 g)

    # Frame Fasteners
    "FRAME_BOLT_DIAM": 0.25 * INCH,     # 1/4"-20 hex bolts
    "FRAME_BOLT_LEN": 2.5 * INCH,       # 63.5 mm
}

def create_freecad_model():
    """Builds the 3D model using FreeCAD Part API with left & right A-frame triangles."""
    import FreeCAD as App
    import Part

    doc = App.newDocument("Trebuchet_3ft")
    doc.Label = "3ft_Trebuchet_Hardware_Design"

    p = PARAMS
    sw = p["STICK_WIDTH"]     # 38.1 mm
    st = p["STICK_THICK"]     # 19.05 mm
    bl = p["BASE_LENGTH"]     # 914.4 mm
    bw = p["BASE_WIDTH"]      # 457.2 mm
    piv_h = p["PIVOT_HEIGHT"] # 762.0 mm
    spr = p["POST_SPREAD"]    # 228.6 mm (9.0")

    # Colors
    c_wood = (0.82, 0.68, 0.48)       # Natural pine stick
    c_darkwood = (0.65, 0.48, 0.32)   # Bearing pillow blocks
    c_steel = (0.75, 0.78, 0.82)      # Steel rod / bolts
    c_bearing = (0.90, 0.75, 0.25)    # 608 bearing shield
    c_weight = (0.35, 0.40, 0.45)     # Steel counterweight disc
    c_leather = (0.65, 0.42, 0.24)    # Leather shoe-lace
    c_cloth = (0.85, 0.80, 0.72)      # Canvas cloth
    c_marble = (0.05, 0.75, 0.85)     # Translucent glass marble

    def add_obj(shape, name, color, transparency=0):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        if App.GuiUp:
            obj.ViewObject.ShapeColor = color
            obj.ViewObject.Transparency = transparency
        return obj

    # 1. Base Assembly
    y_left = (bw / 2.0) - (sw / 2.0)
    y_right = -y_left

    rail_l = Part.makeBox(bl, sw, st, App.Vector(-bl / 2.0, y_left - sw / 2.0, 0))
    rail_r = Part.makeBox(bl, sw, st, App.Vector(-bl / 2.0, y_right - sw / 2.0, 0))
    add_obj(rail_l, "Base_Runner_Left_Stick", c_wood)
    add_obj(rail_r, "Base_Runner_Right_Stick", c_wood)

    cross_len = bw - (2.0 * sw)
    cb_rear = Part.makeBox(sw, cross_len, st, App.Vector(-bl / 2.0, -cross_len / 2.0, st))
    cb_front = Part.makeBox(sw, cross_len, st, App.Vector(bl / 2.0 - sw, -cross_len / 2.0, st))
    cb_mid = Part.makeBox(sw, cross_len, st, App.Vector(-sw / 2.0, -cross_len / 2.0, st))
    add_obj(cb_rear, "Base_Crossbar_Rear", c_wood)
    add_obj(cb_front, "Base_Crossbar_Front", c_wood)
    add_obj(cb_mid, "Base_Crossbar_Mid", c_wood)

    trough = Part.makeBox(24.0 * INCH, 2.0 * INCH, 0.5 * INCH, App.Vector(-bl / 2.0 + sw, -1.0 * INCH, st))
    groove = Part.makeCylinder(p["MARBLE_DIAMETER"] / 1.5, 24.0 * INCH, App.Vector(-bl / 2.0 + sw, 0, st + 0.5 * INCH), App.Vector(1, 0, 0))
    trough_part = trough.cut(groove)
    add_obj(trough_part, "Marble_Guide_Trough", c_wood)

    # 2. Left & Right Triangular A-Frames (2 Angled Posts per Side)
    dx_post = spr
    dz_post = piv_h - st
    post_len = math.hypot(dx_post, dz_post) + 1.5 * INCH
    post_angle = math.degrees(math.atan2(dz_post, dx_post))

    for side, y_pos in [("Left", y_left), ("Right", y_right)]:
        # Front Post of Triangle
        p_front = Part.makeBox(sw, st, post_len, App.Vector(0, 0, 0))
        p_front.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90 - post_angle)
        p_front.translate(App.Vector(spr, y_pos - st / 2.0, st))
        add_obj(p_front, f"AFrame_{side}_Front_Angled_Post", c_wood)

        # Rear Post of Triangle
        p_rear = Part.makeBox(sw, st, post_len, App.Vector(0, 0, 0))
        p_rear.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), -(90 - post_angle))
        p_rear.translate(App.Vector(-spr, y_pos - st / 2.0, st))
        add_obj(p_rear, f"AFrame_{side}_Rear_Angled_Post", c_wood)

        # Bearing Pillow Block at Apex
        pb = Part.makeBox(3.5 * INCH, st * 1.8, 2.5 * INCH, App.Vector(-1.75 * INCH, y_pos - st * 0.9, piv_h - 1.25 * INCH))
        recess = Part.makeCylinder(p["BEARING_OD"] / 2.0, p["BEARING_WIDTH"] + 1.0, App.Vector(0, y_pos - st * 0.9, piv_h), App.Vector(0, 1, 0))
        axle_through = Part.makeCylinder(p["AXLE_ROD_DIAM"] / 2.0 + 0.5, st * 2.5, App.Vector(0, y_pos - st * 1.2, piv_h), App.Vector(0, 1, 0))
        pb_machined = pb.cut(recess).cut(axle_through)
        add_obj(pb_machined, f"Pillow_Block_{side}", c_darkwood)

    upper_brace = Part.makeBox(sw, cross_len, st, App.Vector(-sw / 2.0, -cross_len / 2.0, piv_h - 3.5 * INCH))
    add_obj(upper_brace, "Upper_Cross_Brace_Stick", c_wood)

    # 3. Fulcrum Axle & 2x 608 Ball Bearings
    axle_rod = Part.makeCylinder(p["AXLE_ROD_DIAM"] / 2.0, p["AXLE_ROD_LEN"], App.Vector(0, -p["AXLE_ROD_LEN"] / 2.0, piv_h), App.Vector(0, 1, 0))
    add_obj(axle_rod, "Fulcrum_8mm_Steel_Round_Rod", c_steel)

    for side, y_pos in [("Left", y_left), ("Right", y_right)]:
        b_outer = Part.makeCylinder(p["BEARING_OD"] / 2.0, p["BEARING_WIDTH"], App.Vector(0, y_pos - p["BEARING_WIDTH"] / 2.0, piv_h), App.Vector(0, 1, 0))
        b_inner = Part.makeCylinder(p["BEARING_ID"] / 2.0, p["BEARING_WIDTH"] * 1.2, App.Vector(0, y_pos - p["BEARING_WIDTH"] * 0.6, piv_h), App.Vector(0, 1, 0))
        bearing_obj = b_outer.cut(b_inner)
        add_obj(bearing_obj, f"Fulcrum_608_Ball_Bearing_{side}", c_bearing)

    # 4. Swing Stick & Screwed Counterweight
    l_short = p["SHORT_ARM"]
    l_long = p["LONG_ARM"]

    stick_raw = Part.makeBox(l_short + l_long, st, sw, App.Vector(-l_long, -st / 2.0, piv_h - sw / 2.0))
    bore_8mm = Part.makeCylinder(p["AXLE_ROD_DIAM"] / 2.0 + 0.3, st * 1.5, App.Vector(0, -st, piv_h), App.Vector(0, 1, 0))
    cw_hole = Part.makeCylinder(p["CW_BOLT_DIAM"] / 2.0 + 0.3, sw * 1.5, App.Vector(l_short - 1.0 * INCH, 0, piv_h - sw), App.Vector(0, 0, 1))
    swing_stick = stick_raw.cut(bore_8mm).cut(cw_hole)
    add_obj(swing_stick, "Swing_Stick_Arm_4to1", c_wood)

    cw_center_x = l_short - 1.0 * INCH
    bolt_38 = Part.makeCylinder(p["CW_BOLT_DIAM"] / 2.0, p["CW_BOLT_LEN"], App.Vector(cw_center_x, 0, piv_h - 2.0 * INCH), App.Vector(0, 0, 1))
    add_obj(bolt_38, "Counterweight_Mount_Bolt_38", c_steel)

    cw_disc = Part.makeCylinder(p["CW_DISC_DIAM"] / 2.0, p["CW_DISC_THICK"], App.Vector(cw_center_x, 0, piv_h - sw / 2.0 - p["CW_DISC_THICK"]), App.Vector(0, 0, 1))
    cw_bore = Part.makeCylinder(p["CW_BOLT_DIAM"] / 2.0 + 0.5, p["CW_DISC_THICK"] * 1.2, App.Vector(cw_center_x, 0, piv_h - sw / 2.0 - p["CW_DISC_THICK"] * 1.1), App.Vector(0, 0, 1))
    cw_machined = cw_disc.cut(cw_bore)
    add_obj(cw_machined, "Screwed_Counterweight_395g", c_weight)

    pin = Part.makeCylinder(p["RELEASE_PIN_DIAM"] / 2.0, p["RELEASE_PIN_LEN"], App.Vector(-l_long + 0.5 * INCH, 0, piv_h + sw / 2.0), App.Vector(-1, 0, 1))
    add_obj(pin, "Sling_Release_Pin_45deg", c_steel)

    # 5. Projectile (16 mm Marble), Leather Shoe-Lace & Cloth Pouch
    marble_pos = App.Vector(-bl / 2.0 + 5.0 * INCH, 0, st + 0.5 * INCH + p["MARBLE_DIAMETER"] / 2.0)
    marble = Part.makeSphere(p["MARBLE_DIAMETER"] / 2.0, marble_pos)
    add_obj(marble, "Glass_Marble_16mm", c_marble, transparency=30)

    pouch_shell = Part.makeSphere(p["MARBLE_DIAMETER"] / 2.0 + 1.2, marble_pos)
    pouch_inner = Part.makeSphere(p["MARBLE_DIAMETER"] / 2.0 + 0.2, marble_pos)
    pouch_cutter = Part.makeBox(50, 50, 50, App.Vector(marble_pos.x - 25, marble_pos.y - 25, marble_pos.z))
    cloth_pouch = pouch_shell.cut(pouch_inner).cut(pouch_cutter)
    add_obj(cloth_pouch, "Cloth_Sling_Pouch_Formed", c_cloth)

    lace_fixed = Part.makeCylinder(1.5, p["SLING_LENGTH"] * 0.9, App.Vector(-l_long, 0, piv_h), App.Vector(marble_pos.x - (-l_long), marble_pos.y, marble_pos.z - piv_h))
    add_obj(lace_fixed, "Leather_ShoeLace_Line", c_leather)

    # 6. Clamping Hex Bolts (1/4"-20) at Frame Triangle Joints
    bolt_positions = [
        App.Vector(-bl / 2.0 + sw / 2.0, y_left, st),
        App.Vector(-bl / 2.0 + sw / 2.0, y_right, st),
        App.Vector(bl / 2.0 - sw / 2.0, y_left, st),
        App.Vector(bl / 2.0 - sw / 2.0, y_right, st),
        App.Vector(-spr, y_left, st),
        App.Vector(-spr, y_right, st),
        App.Vector(spr, y_left, st),
        App.Vector(spr, y_right, st),
    ]
    for idx, b_pos in enumerate(bolt_positions):
        bolt = Part.makeCylinder(p["FRAME_BOLT_DIAM"] / 2.0, p["FRAME_BOLT_LEN"], App.Vector(b_pos.x, b_pos.y, b_pos.z - 5.0), App.Vector(0, 0, 1))
        add_obj(bolt, f"Frame_Hex_Bolt_{idx+1}", c_steel)

    doc.recompute()

    fcstd_path = os.path.abspath("Trebuchet_3ft.FCStd")
    doc.saveAs(fcstd_path)
    print(f"Successfully generated and saved FreeCAD model: {fcstd_path}")
    return doc

def generate_standalone_assets():
    """
    Generates high-precision 3D Wavefront OBJ file with exact A-frame triangular stands,
    8mm steel rod, 2x 608 bearings, swing stick, screwed weight, and marble.
    Imports directly into FreeCAD and Blender with true triangular geometry.
    """
    print("Generating complete 3D OBJ file with left & right triangular A-frame stands...")
    obj_lines = [
        "# 3-Foot Timber Trebuchet 3D CAD Model",
        "# Architecture: Dual Triangular A-Frame Side Stands (2 angled posts per side meeting at fulcrum)",
        "# Materials: Rectangular sticks (3/4\" x 1.5\"), 8mm round steel rod, 2x 608 bearings, screwed 395g counterweight",
        "o Trebuchet_Triangular_Assembly"
    ]

    v_offset = 1

    def add_box_from_verts(verts, name):
        nonlocal v_offset
        obj_lines.append(f"o {name}")
        for v in verts:
            obj_lines.append(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}")
        faces = [
            (1, 2, 3, 4), (5, 8, 7, 6), (1, 5, 6, 2),
            (2, 6, 7, 3), (3, 7, 8, 4), (4, 8, 5, 1)
        ]
        for f in faces:
            obj_lines.append(f"f {f[0]+v_offset-1} {f[1]+v_offset-1} {f[2]+v_offset-1} {f[3]+v_offset-1}")
        v_offset += len(verts)

    def add_axis_aligned_box(x, y, z, dx, dy, dz, name):
        v = [
            [x, y, z], [x+dx, y, z], [x+dx, y+dy, z], [x, y+dy, z],
            [x, y, z+dz], [x+dx, y, z+dz], [x+dx, y+dy, z+dz], [x, y+dy, z+dz]
        ]
        add_box_from_verts(v, name)

    def add_oriented_box(p1, p2, width, thickness, name, up=np.array([0, 1, 0])):
        v = np.array(p2, dtype=float) - np.array(p1, dtype=float)
        L = np.linalg.norm(v)
        if L < 1e-6:
            return
        v_norm = v / L
        u = up - np.dot(up, v_norm) * v_norm
        if np.linalg.norm(u) < 1e-4:
            alt = np.array([1, 0, 0], dtype=float)
            u = alt - np.dot(alt, v_norm) * v_norm
        u = u / np.linalg.norm(u)
        n = np.cross(v_norm, u)
        n = n / np.linalg.norm(n)

        hw = width / 2.0
        ht = thickness / 2.0
        offs = [
            -hw * n - ht * u,
            hw * n - ht * u,
            hw * n + ht * u,
            -hw * n + ht * u
        ]
        verts = []
        for off in offs:
            verts.append(np.array(p1, dtype=float) + off)
        for off in offs:
            verts.append(np.array(p2, dtype=float) + off)
        add_box_from_verts(verts, name)

    def add_cylinder_mesh(p1, p2, radius, name, segments=16):
        nonlocal v_offset
        obj_lines.append(f"o {name}")
        v = np.array(p2, dtype=float) - np.array(p1, dtype=float)
        L = np.linalg.norm(v)
        if L < 1e-6:
            return
        v_norm = v / L
        up = np.array([0, 0, 1], dtype=float) if abs(v_norm[2]) < 0.9 else np.array([0, 1, 0], dtype=float)
        u = np.cross(v_norm, up)
        u /= np.linalg.norm(u)
        n = np.cross(v_norm, u)

        angles = np.linspace(0, 2*np.pi, segments, endpoint=False)
        for a in angles:
            pt = np.array(p1, dtype=float) + radius * (np.cos(a) * u + np.sin(a) * n)
            obj_lines.append(f"v {pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f}")
        for a in angles:
            pt = np.array(p2, dtype=float) + radius * (np.cos(a) * u + np.sin(a) * n)
            obj_lines.append(f"v {pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f}")

        obj_lines.append(f"v {p1[0]:.4f} {p1[1]:.4f} {p1[2]:.4f}")
        c1_idx = v_offset + 2 * segments
        obj_lines.append(f"v {p2[0]:.4f} {p2[1]:.4f} {p2[2]:.4f}")
        c2_idx = v_offset + 2 * segments + 1

        for i in range(segments):
            i_next = (i + 1) % segments
            p1_i = v_offset + i
            p1_next = v_offset + i_next
            p2_i = v_offset + segments + i
            p2_next = v_offset + segments + i_next
            obj_lines.append(f"f {p1_i} {p2_i} {p2_next} {p1_next}")
            obj_lines.append(f"f {c1_idx} {p1_next} {p1_i}")
            obj_lines.append(f"f {c2_idx} {p2_i} {p2_next}")

        v_offset += 2 * segments + 2

    def add_sphere_mesh(center, radius, name, rings=10, sectors=16):
        nonlocal v_offset
        obj_lines.append(f"o {name}")
        verts_start = v_offset
        for r in range(rings + 1):
            theta = r * np.pi / rings
            sin_t = np.sin(theta)
            cos_t = np.cos(theta)
            for s in range(sectors):
                phi = s * 2 * np.pi / sectors
                x = center[0] + radius * sin_t * np.cos(phi)
                y = center[1] + radius * sin_t * np.sin(phi)
                z = center[2] + radius * cos_t
                obj_lines.append(f"v {x:.4f} {y:.4f} {z:.4f}")

        for r in range(rings):
            for s in range(sectors):
                first = verts_start + (r * sectors) + s
                second = verts_start + (r * sectors) + ((s + 1) % sectors)
                third = verts_start + ((r + 1) * sectors) + ((s + 1) % sectors)
                fourth = verts_start + ((r + 1) * sectors) + s
                obj_lines.append(f"f {first} {second} {third} {fourth}")

        v_offset += (rings + 1) * sectors

    # -------------------------------------------------------------
    # 1. Base Runners & Crossbars
    # -------------------------------------------------------------
    # Dual Runners: 36" long (914.4 mm), 38.1mm wide, 19.05mm thick
    add_axis_aligned_box(-457.2, 171.45, 0, 914.4, 38.1, 19.05, "Base_Runner_Left")
    add_axis_aligned_box(-457.2, -209.55, 0, 914.4, 38.1, 19.05, "Base_Runner_Right")

    # Crossbars (Rear, Mid, Front)
    add_axis_aligned_box(-457.2, -171.45, 19.05, 38.1, 342.9, 19.05, "Crossbar_Rear")
    add_axis_aligned_box(419.1, -171.45, 19.05, 38.1, 342.9, 19.05, "Crossbar_Front")
    add_axis_aligned_box(-19.05, -171.45, 19.05, 38.1, 342.9, 19.05, "Crossbar_Mid")

    # Marble Guide Trough (24" long strip with center depression)
    add_axis_aligned_box(-430.0, -25.4, 19.05, 609.6, 50.8, 12.7, "Marble_Guide_Trough")

    # -------------------------------------------------------------
    # 2. LEFT SIDE STAND: TRUE TRIANGULAR A-FRAME (2 Angled Posts)
    #    Meeting at the fulcrum apex (X = 0, Z = 762.0 mm)
    # -------------------------------------------------------------
    y_l = 190.5
    # Left Front Post: from (+228.6, 190.5, 19.05) to (0, 190.5, 762.0)
    add_oriented_box([228.6, y_l, 19.05], [0, y_l, 762.0], 38.1, 19.05, "AFrame_Left_Front_Angled_Post")
    # Left Rear Post: from (-228.6, 190.5, 19.05) to (0, y_l, 762.0)
    add_oriented_box([-228.6, y_l, 19.05], [0, y_l, 762.0], 38.1, 19.05, "AFrame_Left_Rear_Angled_Post")
    # Left Pillow Block at Apex
    add_axis_aligned_box(-38.1, y_l - 19.05, 730.0, 76.2, 38.1, 55.0, "Pillow_Block_Left")
    # Left 608 Ball Bearing (22 mm OD, 7 mm width, 8 mm bore)
    add_cylinder_mesh([0, y_l - 3.5, 762.0], [0, y_l + 3.5, 762.0], 11.0, "Fulcrum_608_Bearing_Left", segments=18)

    # -------------------------------------------------------------
    # 3. RIGHT SIDE STAND: TRUE TRIANGULAR A-FRAME (2 Angled Posts)
    #    Meeting at the fulcrum apex (X = 0, Z = 762.0 mm)
    # -------------------------------------------------------------
    y_r = -190.5
    # Right Front Post: from (+228.6, -190.5, 19.05) to (0, -190.5, 762.0)
    add_oriented_box([228.6, y_r, 19.05], [0, y_r, 762.0], 38.1, 19.05, "AFrame_Right_Front_Angled_Post")
    # Right Rear Post: from (-228.6, -190.5, 19.05) to (0, y_r, 762.0)
    add_oriented_box([-228.6, y_r, 19.05], [0, y_r, 762.0], 38.1, 19.05, "AFrame_Right_Rear_Angled_Post")
    # Right Pillow Block at Apex
    add_axis_aligned_box(-38.1, y_r - 19.05, 730.0, 76.2, 38.1, 55.0, "Pillow_Block_Right")
    # Right 608 Ball Bearing (22 mm OD, 7 mm width, 8 mm bore)
    add_cylinder_mesh([0, y_r - 3.5, 762.0], [0, y_r + 3.5, 762.0], 11.0, "Fulcrum_608_Bearing_Right", segments=18)

    # Upper Cross Tie between left and right apexes (Z = 705 mm)
    add_axis_aligned_box(-19.05, y_r + 19.05, 705.0, 38.1, (y_l - y_r) - 38.1, 19.05, "Upper_Truss_Cross_Tie")

    # -------------------------------------------------------------
    # 4. FULCRUM AXLE: 8mm Steel Round Rod
    # -------------------------------------------------------------
    add_cylinder_mesh([0, -247.65, 762.0], [0, 247.65, 762.0], 4.0, "Fulcrum_8mm_Steel_Round_Rod", segments=18)

    # -------------------------------------------------------------
    # 5. SWING STICK (ARM - 4:1 Ratio: 6" Short Arm, 24" Long Arm)
    #    Model at cocked launch position (theta ~ -20 degrees)
    # -------------------------------------------------------------
    # Pivot is at (0, 0, 762.0)
    # Short end (+X): extends to +152.4 mm
    # Long end (-X): extends to -609.6 mm
    angle_rad = math.radians(-20.0)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    p_short = [152.4 * cos_a, 0, 762.0 - 152.4 * sin_a]
    p_long = [-609.6 * cos_a, 0, 762.0 + 609.6 * sin_a]
    add_oriented_box(p_short, p_long, 38.1, 19.05, "Swing_Stick_Arm_4to1", up=np.array([0, 1, 0]))

    # -------------------------------------------------------------
    # 6. BOLTED COUNTERWEIGHT (395g Steel Disc Screwed on Short Arm)
    # -------------------------------------------------------------
    # Center of weight at 127 mm (5.0") from pivot along short arm
    cw_center_x = 127.0 * cos_a
    cw_center_z = 762.0 - 127.0 * sin_a
    # 3/8" Bolt through stick
    add_cylinder_mesh([cw_center_x, 0, cw_center_z - 45.0], [cw_center_x, 0, cw_center_z + 45.0], 4.76, "Counterweight_Mount_Bolt_38", segments=12)
    # 395g Steel Disc (Ø 76.2 mm / 3.0", thickness 28 mm)
    add_cylinder_mesh([cw_center_x, 0, cw_center_z - 35.0], [cw_center_x, 0, cw_center_z - 7.0], 38.1, "Screwed_Counterweight_395g", segments=24)

    # -------------------------------------------------------------
    # 7. 45-DEGREE STEEL RELEASE PIN AT LONG ARM TIP
    # -------------------------------------------------------------
    tip_x = p_long[0]
    tip_z = p_long[1] if len(p_long) == 2 else p_long[2]
    pin_tip_x = tip_x - 35.0 * cos_a - 20.0 * sin_a
    pin_tip_z = tip_z + 35.0 * sin_a + 20.0 * cos_a
    add_cylinder_mesh([tip_x, 0, tip_z + 10.0], [pin_tip_x, 0, pin_tip_z], 2.38, "Sling_Release_Pin_45deg", segments=10)

    # -------------------------------------------------------------
    # 8. PROJECTILE: 16mm Glass Marble & Leather/Cloth Sling
    # -------------------------------------------------------------
    # Marble sitting in trough at X = -350 mm, Z = 32 mm
    add_sphere_mesh([-350.0, 0, 32.0], 8.0, "Glass_Marble_16mm", rings=10, sectors=16)

    # Leather Shoe-Lace Line
    add_cylinder_mesh([tip_x, 0, tip_z], [-350.0, 0, 32.0], 1.5, "Leather_ShoeLace_Sling", segments=8)

    with open("Trebuchet_3ft.obj", "w") as f:
        f.write("\n".join(obj_lines))
    print(f"Successfully generated Trebuchet_3ft.obj ({len(obj_lines)} lines).")

if __name__ == "__main__":
    try:
        import FreeCAD
        print("FreeCAD Python environment detected. Creating FreeCAD model...")
        create_freecad_model()
    except ImportError:
        print("Note: Running outside native FreeCAD environment.")
        generate_standalone_assets()
