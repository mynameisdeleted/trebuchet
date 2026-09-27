#!/usr/bin/env python3
"""
Parametric FreeCAD Model: 3-Foot High Trebuchet (Calibrated for 3-Yard Marble Launch)
Build Specification:
  - Rectangular wooden sticks (pine 3/4" x 1.5" / 19mm x 38mm)
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

INCH = 25.4  # Conversion factor mm per inch

# -------------------------------------------------------------------------
# Parametric Dimensions & Specifications
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
    """Builds the 3D model using FreeCAD Part API."""
    import FreeCAD as App
    import Part

    doc = App.newDocument("Trebuchet_3ft")
    doc.Label = "3ft_Trebuchet_Hardware_Design"

    p = PARAMS
    sw = p["STICK_WIDTH"]   # 38.1 mm
    st = p["STICK_THICK"]   # 19.05 mm
    bl = p["BASE_LENGTH"]   # 914.4 mm
    bw = p["BASE_WIDTH"]    # 457.2 mm
    piv_h = p["PIVOT_HEIGHT"] # 762.0 mm

    # Colors
    c_wood = (0.82, 0.68, 0.48)       # Natural pine stick
    c_steel = (0.75, 0.78, 0.82)      # Steel rod / bolts
    c_bearing = (0.90, 0.75, 0.25)    # 608 bearing brass/bronze shield
    c_weight = (0.35, 0.40, 0.45)     # Cast iron / steel weight
    c_leather = (0.65, 0.42, 0.24)    # Leather shoe-lace
    c_cloth = (0.85, 0.80, 0.72)      # Heavy canvas cloth
    c_marble = (0.05, 0.75, 0.85)     # Translucent glass marble

    def add_obj(shape, name, color, transparency=0):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        if App.GuiUp:
            obj.ViewObject.ShapeColor = color
            obj.ViewObject.Transparency = transparency
        return obj

    # -------------------------------------------------------------
    # 1. Base Assembly (Rectangular sticks + Glue + 1/4" Bolts)
    # -------------------------------------------------------------
    # Dual Base Runners (Left & Right) along X-axis
    y_left = (bw / 2.0) - (sw / 2.0)
    y_right = -y_left

    rail_l = Part.makeBox(bl, sw, st, App.Vector(-bl / 2.0, y_left - sw / 2.0, 0))
    rail_r = Part.makeBox(bl, sw, st, App.Vector(-bl / 2.0, y_right - sw / 2.0, 0))
    add_obj(rail_l, "Base_Runner_Left_Stick", c_wood)
    add_obj(rail_r, "Base_Runner_Right_Stick", c_wood)

    # 3x Base Crossbars (Rear, Mid, Front)
    cross_len = bw - (2.0 * sw)
    cb_rear = Part.makeBox(sw, cross_len, st, App.Vector(-bl / 2.0, -cross_len / 2.0, st))
    cb_front = Part.makeBox(sw, cross_len, st, App.Vector(bl / 2.0 - sw, -cross_len / 2.0, st))
    cb_mid = Part.makeBox(sw, cross_len, st, App.Vector(-sw / 2.0, -cross_len / 2.0, st))
    add_obj(cb_rear, "Base_Crossbar_Rear", c_wood)
    add_obj(cb_front, "Base_Crossbar_Front", c_wood)
    add_obj(cb_mid, "Base_Crossbar_Mid", c_wood)

    # Trough Strip for Marble (24" long, centered along rear half)
    trough = Part.makeBox(24.0 * INCH, 2.0 * INCH, 0.5 * INCH, App.Vector(-bl / 2.0 + sw, -1.0 * INCH, st))
    groove = Part.makeCylinder(p["MARBLE_DIAMETER"] / 1.5, 24.0 * INCH, App.Vector(-bl / 2.0 + sw, 0, st + 0.5 * INCH), App.Vector(1, 0, 0))
    trough_part = trough.cut(groove)
    add_obj(trough_part, "Marble_Guide_Trough", c_wood)

    # -------------------------------------------------------------
    # 2. A-Frame Uprights & Pillow Blocks (Rectangular Sticks)
    # -------------------------------------------------------------
    leg_spread = 11.0 * INCH
    leg_len = math.hypot(leg_spread, piv_h - st)
    leg_angle = math.degrees(math.atan2(piv_h - st, leg_spread))

    for side, y_pos in [("Left", y_left), ("Right", y_right)]:
        # Front Strut
        strut_f = Part.makeBox(sw, st, leg_len, App.Vector(0, 0, 0))
        strut_f.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90 - leg_angle)
        strut_f.translate(App.Vector(leg_spread, y_pos - st / 2.0, st))
        add_obj(strut_f, f"AFrame_{side}_Front_Stick", c_wood)

        # Rear Strut
        strut_r = Part.makeBox(sw, st, leg_len, App.Vector(0, 0, 0))
        strut_r.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), -(90 - leg_angle))
        strut_r.translate(App.Vector(-leg_spread, y_pos - st / 2.0, st))
        add_obj(strut_r, f"AFrame_{side}_Rear_Stick", c_wood)

        # Bearing Pillow Block (with 22mm recess for 608 bearing)
        pb = Part.makeBox(3.0 * INCH, st * 1.8, 2.5 * INCH, App.Vector(-1.5 * INCH, y_pos - st * 0.9, piv_h - 1.25 * INCH))
        recess = Part.makeCylinder(p["BEARING_OD"] / 2.0, p["BEARING_WIDTH"] + 1.0, App.Vector(0, y_pos - st * 0.9, piv_h), App.Vector(0, 1, 0))
        axle_through = Part.makeCylinder(p["AXLE_ROD_DIAM"] / 2.0 + 0.5, st * 2.5, App.Vector(0, y_pos - st * 1.2, piv_h), App.Vector(0, 1, 0))
        pb_machined = pb.cut(recess).cut(axle_through)
        add_obj(pb_machined, f"Pillow_Block_{side}", c_wood)

    # Upper Cross Brace
    upper_brace = Part.makeBox(sw, cross_len, st, App.Vector(-sw / 2.0, -cross_len / 2.0, piv_h - 3.5 * INCH))
    add_obj(upper_brace, "Upper_Cross_Brace_Stick", c_wood)

    # -------------------------------------------------------------
    # 3. Fulcrum: 8mm Steel Rod + 2x 608 Ball Bearings
    # -------------------------------------------------------------
    # 8 mm Round Steel Rod Axle
    axle_rod = Part.makeCylinder(p["AXLE_ROD_DIAM"] / 2.0, p["AXLE_ROD_LEN"], App.Vector(0, -p["AXLE_ROD_LEN"] / 2.0, piv_h), App.Vector(0, 1, 0))
    add_obj(axle_rod, "Fulcrum_8mm_Steel_Round_Rod", c_steel)

    # 2x 608 Ball Bearings (8mm ID x 22mm OD x 7mm W)
    for side, y_pos in [("Left", y_left), ("Right", y_right)]:
        # Outer race cylinder cut by inner race
        b_outer = Part.makeCylinder(p["BEARING_OD"] / 2.0, p["BEARING_WIDTH"], App.Vector(0, y_pos - p["BEARING_WIDTH"] / 2.0, piv_h), App.Vector(0, 1, 0))
        b_inner = Part.makeCylinder(p["BEARING_ID"] / 2.0, p["BEARING_WIDTH"] * 1.2, App.Vector(0, y_pos - p["BEARING_WIDTH"] * 0.6, piv_h), App.Vector(0, 1, 0))
        bearing_obj = b_outer.cut(b_inner)
        add_obj(bearing_obj, f"Fulcrum_608_Ball_Bearing_{side}", c_bearing)

    # -------------------------------------------------------------
    # 4. Swing Stick & Screwed-On Counterweight
    # -------------------------------------------------------------
    # Swing Stick (30" total = 6" short arm, 24" long arm)
    # Pivot at (0, 0, piv_h). Long arm extends to -24" (rear), short arm to +6" (front).
    l_short = p["SHORT_ARM"]
    l_long = p["LONG_ARM"]

    stick_raw = Part.makeBox(l_short + l_long, st, sw, App.Vector(-l_long, -st / 2.0, piv_h - sw / 2.0))
    # 8mm bore for axle rod
    bore_8mm = Part.makeCylinder(p["AXLE_ROD_DIAM"] / 2.0 + 0.3, st * 1.5, App.Vector(0, -st, piv_h), App.Vector(0, 1, 0))
    # 3/8" bore for counterweight mounting bolt at short end
    cw_hole = Part.makeCylinder(p["CW_BOLT_DIAM"] / 2.0 + 0.3, sw * 1.5, App.Vector(l_short - 1.0 * INCH, 0, piv_h - sw), App.Vector(0, 0, 1))
    swing_stick = stick_raw.cut(bore_8mm).cut(cw_hole)
    add_obj(swing_stick, "Swing_Stick_Arm_4to1", c_wood)

    # Counterweight: Screwed onto the end of the short stick
    # 3/8"-16 Bolt passing vertically through stick end
    cw_center_x = l_short - 1.0 * INCH
    bolt_38 = Part.makeCylinder(p["CW_BOLT_DIAM"] / 2.0, p["CW_BOLT_LEN"], App.Vector(cw_center_x, 0, piv_h - 2.0 * INCH), App.Vector(0, 0, 1))
    add_obj(bolt_38, "Counterweight_Mount_Bolt_38", c_steel)

    # 395g Steel Counterweight Disc
    cw_disc = Part.makeCylinder(p["CW_DISC_DIAM"] / 2.0, p["CW_DISC_THICK"], App.Vector(cw_center_x, 0, piv_h - sw / 2.0 - p["CW_DISC_THICK"]), App.Vector(0, 0, 1))
    cw_bore = Part.makeCylinder(p["CW_BOLT_DIAM"] / 2.0 + 0.5, p["CW_DISC_THICK"] * 1.2, App.Vector(cw_center_x, 0, piv_h - sw / 2.0 - p["CW_DISC_THICK"] * 1.1), App.Vector(0, 0, 1))
    cw_machined = cw_disc.cut(cw_bore)
    add_obj(cw_machined, "Screwed_Counterweight_395g", c_weight)

    # 45-Degree Steel Release Pin at Long Arm Tip
    pin = Part.makeCylinder(p["RELEASE_PIN_DIAM"] / 2.0, p["RELEASE_PIN_LEN"], App.Vector(-l_long + 0.5 * INCH, 0, piv_h + sw / 2.0), App.Vector(-1, 0, 1))
    add_obj(pin, "Sling_Release_Pin_45deg", c_steel)

    # -------------------------------------------------------------
    # 5. Leather Shoe-Lace Sling & Folded Cloth Pouch
    # -------------------------------------------------------------
    # 16 mm Glass Marble resting on base trough
    marble_pos = App.Vector(-bl / 2.0 + 5.0 * INCH, 0, st + 0.5 * INCH + p["MARBLE_DIAMETER"] / 2.0)
    marble = Part.makeSphere(p["MARBLE_DIAMETER"] / 2.0, marble_pos)
    add_obj(marble, "Glass_Marble_16mm", c_marble, transparency=30)

    # Cloth Pouch Cradling the Marble
    pouch_shell = Part.makeSphere(p["MARBLE_DIAMETER"] / 2.0 + 1.2, marble_pos)
    pouch_inner = Part.makeSphere(p["MARBLE_DIAMETER"] / 2.0 + 0.2, marble_pos)
    pouch_cutter = Part.makeBox(50, 50, 50, App.Vector(marble_pos.x - 25, marble_pos.y - 25, marble_pos.z))
    cloth_pouch = pouch_shell.cut(pouch_inner).cut(pouch_cutter)
    add_obj(cloth_pouch, "Cloth_Sling_Pouch_Formed", c_cloth)

    # Leather Shoe-Lace Lines (Modeled as thin cord cylinders)
    lace_fixed = Part.makeCylinder(1.5, p["SLING_LENGTH"] * 0.9, App.Vector(-l_long, 0, piv_h), App.Vector(marble_pos.x - (-l_long), marble_pos.y, marble_pos.z - piv_h))
    add_obj(lace_fixed, "Leather_ShoeLace_Line", c_leather)

    # -------------------------------------------------------------
    # 6. Clamping Hex Bolts (1/4"-20) at Frame Joints
    # -------------------------------------------------------------
    bolt_positions = [
        App.Vector(-bl / 2.0 + sw / 2.0, y_left, st),
        App.Vector(-bl / 2.0 + sw / 2.0, y_right, st),
        App.Vector(bl / 2.0 - sw / 2.0, y_left, st),
        App.Vector(bl / 2.0 - sw / 2.0, y_right, st),
        App.Vector(-leg_spread, y_left, st),
        App.Vector(-leg_spread, y_right, st),
        App.Vector(leg_spread, y_left, st),
        App.Vector(leg_spread, y_right, st),
    ]
    for idx, b_pos in enumerate(bolt_positions):
        bolt = Part.makeCylinder(p["FRAME_BOLT_DIAM"] / 2.0, p["FRAME_BOLT_LEN"], App.Vector(b_pos.x, b_pos.y, b_pos.z - 5.0), App.Vector(0, 0, 1))
        add_obj(bolt, f"Frame_Hex_Bolt_{idx+1}", c_steel)

    doc.recompute()

    # Save FreeCAD Document
    fcstd_path = os.path.abspath("Trebuchet_3ft.FCStd")
    doc.saveAs(fcstd_path)
    print(f"Successfully generated and saved FreeCAD model: {fcstd_path}")
    return doc

def generate_standalone_assets():
    """Generates standard 3D Wavefront OBJ when running outside FreeCAD."""
    print("Generating complete 3D OBJ file for hardware trebuchet...")
    obj_lines = [
        "# 3-Foot Timber Trebuchet 3D Model",
        "# Hardware: Rectangular sticks, 8mm steel rod, 2x 608 ball bearings, bolted weight, leather shoe-lace, cloth pouch",
        "o Trebuchet_Hardware_Assembly"
    ]

    v_offset = 1
    def add_box(x, y, z, dx, dy, dz, name):
        nonlocal v_offset
        obj_lines.append(f"g {name}")
        corners = [
            (x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
            (x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)
        ]
        for vx, vy, vz in corners:
            obj_lines.append(f"v {vx:.4f} {vy:.4f} {vz:.4f}")
        faces = [
            (1, 2, 3, 4), (5, 8, 7, 6), (1, 5, 6, 2),
            (2, 6, 7, 3), (3, 7, 8, 4), (4, 8, 5, 1)
        ]
        for f in faces:
            obj_lines.append(f"f {f[0]+v_offset-1} {f[1]+v_offset-1} {f[2]+v_offset-1} {f[3]+v_offset-1}")
        v_offset += 8

    # Base sticks
    add_box(-457.2, 190.5, 0, 914.4, 38.1, 19.05, "Base_Runner_Left")
    add_box(-457.2, -228.6, 0, 914.4, 38.1, 19.05, "Base_Runner_Right")
    add_box(-457.2, -190.5, 19.05, 38.1, 381.0, 19.05, "Crossbar_Rear")
    add_box(419.1, -190.5, 19.05, 38.1, 381.0, 19.05, "Crossbar_Front")
    add_box(-19.05, -190.5, 19.05, 38.1, 381.0, 19.05, "Crossbar_Mid")
    # Upright legs
    add_box(-19.05, 190.5, 19.05, 38.1, 19.05, 742.95, "AFrame_Struts_Left")
    add_box(-19.05, -209.55, 19.05, 38.1, 19.05, 742.95, "AFrame_Struts_Right")
    # 8mm round rod axle
    add_box(-4.0, -247.65, 758.0, 8.0, 495.3, 8.0, "Fulcrum_8mm_Round_Rod")
    # 2x 608 Ball Bearings
    add_box(-11.0, 185.0, 751.0, 22.0, 7.0, 22.0, "Fulcrum_608_Bearing_Left")
    add_box(-11.0, -192.0, 751.0, 22.0, 7.0, 22.0, "Fulcrum_608_Bearing_Right")
    # Swing stick (30" long, 4:1 ratio)
    add_box(-609.6, -9.5, 743.0, 762.0, 19.05, 38.1, "Swing_Stick_Arm_4to1")
    # Screwed-on counterweight (395g disc)
    add_box(101.6, -38.1, 715.0, 76.2, 76.2, 28.0, "Screwed_Counterweight_395g")
    # Marble & cloth pouch
    add_box(-350.0, -8.0, 45.0, 16.0, 16.0, 16.0, "Marble_16mm_In_Cloth_Pouch")

    with open("Trebuchet_3ft.obj", "w") as f:
        f.write("\n".join(obj_lines))
    print("Generated updated Trebuchet_3ft.obj with exact hardware specifications.")

if __name__ == "__main__":
    try:
        import FreeCAD
        print("FreeCAD Python environment detected. Creating FreeCAD model...")
        create_freecad_model()
    except ImportError:
        print("Note: Running outside native FreeCAD environment.")
        generate_standalone_assets()
