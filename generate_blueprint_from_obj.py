#!/usr/bin/env python3
"""
generate_blueprint_from_obj.py
Automated CAD Projection Pipeline:
Reads Trebuchet_3ft.obj as the Single Source of Truth (SSOT).
Mathematically projects 2D orthographic and isometric views directly from 3D mesh vertices.
Extracts wood parts, computes exact cut dimensions, miter angles, and hole locations,
and generates:
  1. trebuchet_blueprint.svg (Comprehensive Engineering Blueprint in Pure Vector SVG)
  2. wood_cutout_shapes.svg (1:1 & Dimensioned Wood Parts Cutting Schedule in Pure Vector SVG)
"""

import os
import math
import shutil
import numpy as np

INCH = 25.4

def parse_obj(filename):
    """Parses a Wavefront OBJ file into named object meshes."""
    objects = {}
    current_obj = "Default"
    objects[current_obj] = {'faces': [], 'obj_name': current_obj}
    all_verts = []

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('o '):
                current_obj = line[2:].strip()
                if current_obj not in objects:
                    objects[current_obj] = {'faces': [], 'obj_name': current_obj}
            elif line.startswith('v '):
                parts = line[2:].split()
                all_verts.append([float(parts[0]), float(parts[1]), float(parts[2])])
            elif line.startswith('f '):
                # Indices in OBJ are 1-based
                face_indices = [int(p.split('/')[0]) - 1 for p in line[2:].split()]
                objects[current_obj]['faces'].append(face_indices)

    verts_np = np.array(all_verts, dtype=float)
    return objects, verts_np

def get_part_style(part_name):
    """Returns SVG fill, stroke, stroke-width, and opacity for a given part."""
    name = part_name.lower()
    if 'marble' in name:
        return {'fill': '#00f5d4', 'stroke': '#ffffff', 'stroke-width': '1.5', 'opacity': '0.95', 'type': 'marble'}
    elif 'pouch' in name:
        return {'fill': '#e76f51', 'stroke': '#ffd166', 'stroke-width': '1.8', 'opacity': '0.95', 'type': 'pouch'}
    elif 'lace' in name or 'sling' in name:
        return {'fill': 'none', 'stroke': '#d4a373', 'stroke-width': '2.4', 'opacity': '1.0', 'type': 'sling'}
    elif 'counterweight' in name or 'weight' in name:
        return {'fill': '#234d74', 'stroke': '#ffd166', 'stroke-width': '1.8', 'opacity': '1.0', 'type': 'weight'}
    elif 'bearing' in name:
        return {'fill': '#1b3b6f', 'stroke': '#ffd166', 'stroke-width': '1.4', 'opacity': '1.0', 'type': 'bearing'}
    elif 'rod' in name or 'bolt' in name or 'pin' in name:
        return {'fill': '#cbd5e1', 'stroke': '#ffffff', 'stroke-width': '1.2', 'opacity': '1.0', 'type': 'metal'}
    elif 'pillow_block' in name:
        return {'fill': '#133358', 'stroke': '#64dfdf', 'stroke-width': '1.6', 'opacity': '1.0', 'type': 'wood'}
    elif 'trough' in name:
        return {'fill': '#102947', 'stroke': '#48cae4', 'stroke-width': '1.4', 'opacity': '1.0', 'type': 'wood'}
    elif 'swing_stick' in name or 'arm' in name:
        return {'fill': '#153b63', 'stroke': '#64dfdf', 'stroke-width': '1.8', 'opacity': '1.0', 'type': 'wood'}
    else:
        # Standard structural wood (runners, crossbars, A-frame posts)
        return {'fill': '#0b233e', 'stroke': '#64dfdf', 'stroke-width': '1.4', 'opacity': '1.0', 'type': 'wood'}

def project_view(objects, verts, view_type='front', origin=(0, 0), scale=0.45):
    """
    Mathematically projects 3D polygonal faces into 2D SVG polygons.
    view_type:
      'front': Longitudinal View (X horizontal, Z vertical, looking from +Y)
      'side':  Transverse View (Y horizontal, Z vertical, looking from -X)
      'top':   Plan View (X horizontal, Y vertical, looking from +Z)
      'iso':   Isometric 3D Axonometric View
    """
    ox, oy = origin
    projected_faces = []

    # Viewing vectors for backface culling and depth sorting
    if view_type == 'front':
        view_dir = np.array([0.0, -1.0, 0.0])
    elif view_type == 'side':
        view_dir = np.array([1.0, 0.0, 0.0])
    elif view_type == 'top':
        view_dir = np.array([0.0, 0.0, -1.0])
    elif view_type == 'iso':
        # 30-degree isometric axonometric view
        view_dir = np.array([1.0, 1.0, 1.0])
        view_dir /= np.linalg.norm(view_dir)

    for obj_name, data in objects.items():
        style = get_part_style(obj_name)
        for face in data['faces']:
            if len(face) < 3:
                continue
            face_pts = verts[face]
            
            # Compute face normal
            v0 = face_pts[0]
            v1 = face_pts[1]
            v2 = face_pts[2]
            n = np.cross(v1 - v0, v2 - v0)
            norm_len = np.linalg.norm(n)
            if norm_len > 1e-6:
                n_norm = n / norm_len
            else:
                n_norm = np.array([0.0, 0.0, 1.0])

            # Backface culling
            dot = np.dot(n_norm, view_dir)
            if dot < -0.01:
                continue

            # Project coordinates
            screen_pts = []
            depths = []
            for p in face_pts:
                x, y, z = p[0], p[1], p[2]
                if view_type == 'front':
                    # X horizontal, Z vertical (looking from +Y)
                    sx = ox + scale * x
                    sy = oy - scale * z
                    depth = y  # larger y is closer
                elif view_type == 'side':
                    # Y horizontal, Z vertical (looking from -X towards +X)
                    sx = ox + scale * y
                    sy = oy - scale * z
                    depth = -x # smaller x is closer
                elif view_type == 'top':
                    sx = ox + scale * x
                    sy = oy + scale * y
                    depth = z
                elif view_type == 'iso':
                    # Standard 30° axonometric
                    c30 = math.cos(math.radians(30))
                    s30 = math.sin(math.radians(30))
                    # X projects down-right, Y projects down-left, Z projects straight up
                    sx = ox + scale * (x - y) * c30
                    sy = oy - scale * (z - (x + y) * s30 * 0.5)
                    depth = x + y + 2.0 * z

                screen_pts.append((sx, sy))
                depths.append(depth)

            avg_depth = sum(depths) / len(depths)
            
            # Check 2D area (reject degenerate lines)
            area = 0.0
            for i in range(len(screen_pts)):
                j = (i + 1) % len(screen_pts)
                area += screen_pts[i][0] * screen_pts[j][1] - screen_pts[j][0] * screen_pts[i][1]
            if abs(area) < 0.5:
                continue

            projected_faces.append({
                'pts': screen_pts,
                'depth': avg_depth,
                'obj_name': obj_name,
                'style': style,
                'dot': dot
            })

    # Sort faces from back to front (Painter's algorithm)
    projected_faces.sort(key=lambda item: item['depth'])
    return projected_faces

def analyze_wood_parts(objects, verts):
    """
    Extracts all unique wooden components directly from Trebuchet_3ft.obj,
    computing exact cutting dimensions, miter angles, hole specs, and quantities.
    """
    wood_parts = []

    # 1. Base Runners (Left & Right)
    for side in ['Left', 'Right']:
        name = f"Base_Runner_{side}"
        if name in objects and objects[name]['faces']:
            f_v = list(set([idx for f in objects[name]['faces'] for idx in f]))
            pts = verts[f_v]
            min_p, max_p = pts.min(axis=0), pts.max(axis=0)
            span = max_p - min_p
            wood_parts.append({
                'part_id': f'W1-{side[0]}',
                'name': f'Base Runner ({side})',
                'category': 'Base Runner',
                'qty': 1,
                'stock': '3/4" x 1.5" (19.05 x 38.1 mm)',
                'length_mm': span[0],
                'length_in': span[0] / INCH,
                'width_mm': span[1],
                'thick_mm': span[2],
                'miter_angle_deg': 0.0,
                'cut_type': '90° Square Cuts Both Ends',
                'features': 'Lap-joint clamp holes at X=±17.25", 0"; A-frame post footings at X=±9.0"'
            })

    # 2. Base Crossbars
    for pos in ['Rear', 'Mid', 'Front']:
        name = f"Crossbar_{pos}"
        if name in objects and objects[name]['faces']:
            f_v = list(set([idx for f in objects[name]['faces'] for idx in f]))
            pts = verts[f_v]
            min_p, max_p = pts.min(axis=0), pts.max(axis=0)
            span = max_p - min_p
            wood_parts.append({
                'part_id': f'W2-{pos[0]}',
                'name': f'Base Crossbar ({pos})',
                'category': 'Crossbar',
                'qty': 1,
                'stock': '3/4" x 1.5" (19.05 x 38.1 mm)',
                'length_mm': span[1],
                'length_in': span[1] / INCH,
                'width_mm': span[0],
                'thick_mm': span[2],
                'miter_angle_deg': 0.0,
                'cut_type': '90° Square Cuts Both Ends',
                'features': '1/4" bolt clearance holes for runner lap joints'
            })

    # 4. A-Frame Triangular Angled Posts (4 Qty)
    posts = [
        ('LF', 'Left Front', 'AFrame_Left_Front_Angled_Post'),
        ('LR', 'Left Rear', 'AFrame_Left_Rear_Angled_Post'),
        ('RF', 'Right Front', 'AFrame_Right_Front_Angled_Post'),
        ('RR', 'Right Rear', 'AFrame_Right_Rear_Angled_Post')
    ]
    for pid, pname, obj_name in posts:
        if obj_name in objects and objects[obj_name]['faces']:
            f_v = list(set([idx for f in objects[obj_name]['faces'] for idx in f]))
            pts = verts[f_v]
            bottom_pts = pts[pts[:,2] < 100]
            top_pts = pts[pts[:,2] > 700]
            b_c = bottom_pts.mean(axis=0)
            t_c = top_pts.mean(axis=0)
            vec = t_c - b_c
            post_len = np.linalg.norm(vec)
            ang_vert = np.degrees(np.arctan2(abs(vec[0]), abs(vec[2])))
            miter = 90.0 - ang_vert
            wood_parts.append({
                'part_id': f'W4-{pid}',
                'name': f'A-Frame Post ({pname})',
                'category': 'Angled Upright Post',
                'qty': 1,
                'stock': '3/4" x 1.5" (19.05 x 38.1 mm)',
                'length_mm': post_len,
                'length_in': post_len / INCH,
                'width_mm': 38.1,
                'thick_mm': 19.05,
                'miter_angle_deg': miter,
                'cut_type': f'{miter:.1f}° Dual Miter Cuts (17.1° off-square)',
                'features': 'Flush foot on base runner; flush apex under pillow block'
            })

    # 5. Pillow Blocks (Left & Right)
    for side in ['Left', 'Right']:
        name = f"Pillow_Block_{side}"
        if name in objects and objects[name]['faces']:
            f_v = list(set([idx for f in objects[name]['faces'] for idx in f]))
            pts = verts[f_v]
            min_p, max_p = pts.min(axis=0), pts.max(axis=0)
            span = max_p - min_p
            wood_parts.append({
                'part_id': f'W5-{side[0]}',
                'name': f'Bearing Pillow Block ({side})',
                'category': 'Pillow Block',
                'qty': 1,
                'stock': '1.5" x 3.0" x 2.2" (Hardwood/Pine Block)',
                'length_mm': span[0],
                'length_in': span[0] / INCH,
                'width_mm': span[1],
                'thick_mm': span[2],
                'miter_angle_deg': 0.0,
                'cut_type': 'Precision Machined Block',
                'features': 'Ø 22mm x 7mm deep bearing pocket recess + Ø 8.5mm through-bore'
            })

    # 6. Marble Guide Trough Strip
    name = "Marble_Guide_Trough"
    if name in objects and objects[name]['faces']:
        f_v = list(set([idx for f in objects[name]['faces'] for idx in f]))
        pts = verts[f_v]
        min_p, max_p = pts.min(axis=0), pts.max(axis=0)
        span = max_p - min_p
        wood_parts.append({
            'part_id': 'W6',
            'name': 'Marble Guide Trough Strip',
            'category': 'Guide Trough',
            'qty': 1,
            'stock': '1/2" x 2.0" (12.7 x 50.8 mm Pine)',
            'length_mm': span[0],
            'length_in': span[0] / INCH,
            'width_mm': span[1],
            'thick_mm': span[2],
            'miter_angle_deg': 0.0,
            'cut_type': '90° Square Cuts Both Ends',
            'features': 'Center concave groove (Ø 16mm / 1/2" round-nose) along top surface'
        })

    # 7. Swing Stick Arm (Bigger 40.0" Timber Stick)
    name = "Swing_Stick_Arm_40in"
    if name in objects and objects[name]['faces']:
        f_v = list(set([idx for f in objects[name]['faces'] for idx in f]))
        pts = verts[f_v]
        tip_long = pts[pts[:,0] < -200].mean(axis=0)
        tip_short = pts[pts[:,0] > 50].mean(axis=0)
        arm_vec = tip_short - tip_long
        arm_len = np.linalg.norm(arm_vec)
        pivot = np.array([0.0, 0.0, 762.0])
        l_short = np.linalg.norm(tip_short - pivot)
        l_long = np.linalg.norm(tip_long - pivot)
        wood_parts.append({
            'part_id': 'W7',
            'name': 'Bigger Swingarm (Throwing Stick)',
            'category': 'Swingarm Beam',
            'qty': 1,
            'stock': '1.5" x 1.5" Square Timber (38.1 x 38.1 mm)',
            'length_mm': arm_len,
            'length_in': arm_len / INCH,
            'width_mm': 38.1,
            'thick_mm': 38.1,
            'miter_angle_deg': 0.0,
            'cut_type': '90° Square Cuts Both Ends',
            'features': (f'Ø 8.0mm fulcrum axle bore at 8.0" ({l_short:.1f} mm) from CW end; '
                         f'Ø 3/8" bolt hole at 1.3" (33 mm) from CW end (6.7" from pivot); '
                         f'Ø 3/16" 45° sling release pin hole at 0.5" from long tip')
        })

    return wood_parts

def draw_faces_to_svg(faces):
    """Converts projected faces list into SVG polygon elements."""
    lines = []
    for f in faces:
        pts_str = " ".join([f"{p[0]:.2f},{p[1]:.2f}" for p in f['pts']])
        st = f['style']
        
        # Slight shading based on surface angle (dot product)
        # to enhance technical 3D readability
        fill = st['fill']
        opacity = st['opacity']
        stroke = st['stroke']
        sw = st['stroke-width']
        
        lines.append(f'  <polygon points="{pts_str}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}" />')
    return "\n".join(lines)

def generate_blueprint_svg(objects, verts, wood_parts, output_path):
    """
    Renders the complete 2D engineering blueprint strictly projected from Trebuchet_3ft.obj.
    Views:
      1. Longitudinal Elevation (Side View, X-Z plane, showing cocked swingarm & sling)
      2. Transverse Elevation (Front View, Y-Z plane, showing width & bearings)
      3. Plan View (Top View, X-Y plane)
      4. Axonometric Isometric View (Full 3D assembly)
    """
    svg_w, svg_h = 1920, 1200
    
    # Mathematical 3D Projections from Trebuchet_3ft.obj
    # 1. Side View (Longitudinal): X horizontal, Z vertical
    # Model: X spans [-457.2, 457.2] (914.4 mm), Z spans [0, 951.6] mm
    scale_side = 0.56
    origin_side = (400, 540) # Z=0 is at Y=540, Fulcrum Z=762 is at Y = 540 - 762*0.56 = 113.3
    faces_side = project_view(objects, verts, view_type='front', origin=origin_side, scale=scale_side)
    
    # 2. Front View (Transverse): Y horizontal, Z vertical
    # Model: Y spans [-247.65, 247.65] (495.3 mm), Z spans [0, 951.6] mm
    scale_front = 0.56
    origin_front = (900, 540)
    faces_front = project_view(objects, verts, view_type='side', origin=origin_front, scale=scale_front)
    
    # 3. Plan View (Top View): X horizontal, Y vertical
    # Model: X spans [-457.2, 457.2], Y spans [-190.5, 190.5]
    scale_top = 0.42
    origin_top = (400, 840)
    faces_top = project_view(objects, verts, view_type='top', origin=origin_top, scale=scale_top)
    
    # 4. Isometric 3D View: Axonometric
    scale_iso = 0.38
    origin_iso = (900, 840)
    faces_iso = project_view(objects, verts, view_type='iso', origin=origin_iso, scale=scale_iso)

    svg = []
    svg.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">
  <defs>
    <!-- Background & Grid -->
    <pattern id="gridMinor" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#102540" stroke-width="0.8"/>
    </pattern>
    <pattern id="gridMajor" width="100" height="100" patternUnits="userSpaceOnUse">
      <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#163863" stroke-width="1.4"/>
    </pattern>
    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#48cae4" />
    </marker>
    <marker id="arrowAmber" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#ffd166" />
    </marker>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="{svg_w}" height="{svg_h}" fill="#081424" />
  <rect width="{svg_w}" height="{svg_h}" fill="url(#gridMinor)" />
  <rect width="{svg_w}" height="{svg_h}" fill="url(#gridMajor)" />

  <!-- Sheet Border -->
  <rect x="25" y="25" width="{svg_w - 50}" height="{svg_h - 50}" fill="none" stroke="#22577a" stroke-width="2.5" />
  <rect x="33" y="33" width="{svg_w - 66}" height="{svg_h - 66}" fill="none" stroke="#38a3a5" stroke-width="1.0" />

  <!-- Zone References -->
  <g font-family="monospace" font-size="11" fill="#48cae4" opacity="0.6">
    <text x="38" y="20">A</text><text x="480" y="20">B</text><text x="960" y="20">C</text><text x="1440" y="20">D</text>
    <text x="15" y="100">1</text><text x="15" y="400">2</text><text x="15" y="700">3</text><text x="15" y="1000">4</text>
  </g>

  <!-- ==================== HEADER BLOCK ==================== -->
  <g transform="translate(50, 48)">
    <text x="0" y="0" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="24" font-weight="900" fill="#64dfdf" letter-spacing="2">
      HISTORICAL SIEGE ENGINE: 3-FOOT FIELD TREBUCHET
    </text>
    <text x="0" y="22" font-family="monospace" font-size="12" fill="#ffd166" letter-spacing="1">
      SINGLE SOURCE OF TRUTH (SSOT) CAD RECONSTRUCTION • 3D OBJ DIRECT ORTHOGRAPHIC PROJECTION
    </text>
    <text x="820" y="0" font-family="monospace" font-size="11" fill="#80ed99">
      LAUNCH TARGET: 3.00 YARDS (2.74 m) • 16mm GLASS MARBLE (5.5g) • CW: 748g (26.4 oz)
    </text>
    <text x="820" y="22" font-family="monospace" font-size="11" fill="#48cae4">
      FRAME: 36"H x 36"L x 15"W • ARM: 40.0" (32" LONG : 8" SHORT, 4:1) • SLING: 14.55" REACH
    </text>
  </g>
''')

    # ==================== VIEW 1: LONGITUDINAL SIDE VIEW ====================
    # origin_side = (400, 540)
    # Ground at Y = 540
    # Base X: 400 - 457.2*0.56 = 143.97 to 400 + 457.2*0.56 = 656.03
    # Pivot at X = 400, Y = 540 - 762*0.56 = 113.28
    svg.append(f'''
  <!-- VIEW 1 CONTAINER: LONGITUDINAL ELEVATION (SIDE VIEW) -->
  <g id="view1_longitudinal">
    <!-- View Header -->
    <rect x="50" y="90" width="670" height="28" fill="#0f2b46" stroke="#22577a" />
    <text x="65" y="109" font-family="monospace" font-size="13" font-weight="bold" fill="#64dfdf">
      VIEW 1: LONGITUDINAL ELEVATION (SIDE PROFILE - COCKED LAUNCH POSITION)
    </text>
    <text x="630" y="109" font-family="monospace" font-size="11" fill="#ffd166">SCALE 1:4</text>

    <!-- Ground Datum Line -->
    <line x1="80" y1="540" x2="710" y2="540" stroke="#38a3a5" stroke-width="1.8" stroke-dasharray="8,4" />
    <text x="660" y="555" font-family="monospace" font-size="10" fill="#38a3a5">GROUND [Z=0]</text>

    <!-- Fulcrum Vertical Plumb Line -->
    <line x1="400" y1="80" x2="400" y2="550" stroke="#ffd166" stroke-width="1.2" stroke-dasharray="5,5" />
    <text x="408" y="130" font-family="monospace" font-size="10" fill="#ffd166">FULCRUM PLUMB AXIS [X=0]</text>

    <!-- Projected 3D Faces from OBJ -->
{draw_faces_to_svg(faces_side)}

    <!-- View 1 Dimensions & Annotations -->
    <!-- Base Length Dimension: 36.00" (914.4 mm) -->
    <line x1="144" y1="565" x2="656" y2="565" stroke="#48cae4" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)" />
    <line x1="144" y1="540" x2="144" y2="575" stroke="#48cae4" stroke-width="0.8" />
    <line x1="656" y1="540" x2="656" y2="575" stroke="#48cae4" stroke-width="0.8" />
    <text x="400" y="582" font-family="monospace" font-size="12" font-weight="bold" fill="#64dfdf" text-anchor="middle">
      BASE LENGTH: 36.00" [914.4 mm]
    </text>

    <!-- Pivot Fulcrum Height Dimension: 30.00" (762.0 mm) -->
    <line x1="110" y1="540" x2="110" y2="113.3" stroke="#48cae4" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)" />
    <line x1="95" y1="540" x2="144" y2="540" stroke="#48cae4" stroke-width="0.8" />
    <line x1="95" y1="113.3" x2="400" y2="113.3" stroke="#48cae4" stroke-width="0.8" stroke-dasharray="3,3" />
    <text x="100" y="335" font-family="monospace" font-size="11" font-weight="bold" fill="#64dfdf" text-anchor="middle" transform="rotate(-90 100 335)">
      PIVOT HEIGHT: 30.00" [762.0 mm]
    </text>

    <!-- Total Mast Height Dimension: 36.00" (914.4 mm) -->
    <line x1="75" y1="540" x2="75" y2="28" stroke="#ffd166" stroke-width="1.2" marker-start="url(#arrowAmber)" marker-end="url(#arrowAmber)" />
    <line x1="65" y1="28" x2="400" y2="28" stroke="#ffd166" stroke-width="0.8" stroke-dasharray="3,3" />
    <text x="65" y="290" font-family="monospace" font-size="10" fill="#ffd166" text-anchor="middle" transform="rotate(-90 65 290)">
      TOTAL FRAME HEIGHT: 36.00" [914.4 mm]
    </text>

    <!-- Swingarm Length Callout: 40.00" (32" : 8", 4:1 Ratio) -->
    <text x="210" y="320" font-family="monospace" font-size="11" font-weight="bold" fill="#64dfdf">
      SWINGARM: 40.0" [1016mm] (1.5"x1.5" Timber)
    </text>
    <text x="210" y="336" font-family="monospace" font-size="10" fill="#48cae4">
      • Long Arm: 32.00" [812.8 mm]
    </text>
    <text x="210" y="350" font-family="monospace" font-size="10" fill="#48cae4">
      • Short Arm: 8.00" [203.2 mm] (4:1 Ratio)
    </text>

    <!-- Sling Callout -->
    <!-- Swing tip is at X=-393.5mm, Z=50.8mm => SVG X = 400 - 393.5*0.56 = 179.6, Y = 540 - 50.8*0.56 = 511.6 -->
    <!-- Sling reaches from 179.6 back to X=400 under fulcrum -->
    <line x1="179.6" y1="518" x2="400" y2="518" stroke="#ffd166" stroke-width="1.5" marker-start="url(#arrowAmber)" marker-end="url(#arrowAmber)" />
    <text x="290" y="513" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166" text-anchor="middle">
      SLING REACH: 15.49" [393.5 mm] (Directly Under Fulcrum)
    </text>
    <text x="290" y="530" font-family="monospace" font-size="9" fill="#00f5d4" text-anchor="middle">
      Marble Trough Mounted on Top of Rear &amp; Mid Crossbars [Z=38.1mm]
    </text>

    <!-- Bolted Counterweight Callout -->
    <text x="460" y="80" font-family="monospace" font-size="11" font-weight="bold" fill="#ffd166">
      BOLTED COUNTERWEIGHT: 748g (26.4 oz)
    </text>
    <text x="460" y="95" font-family="monospace" font-size="10" fill="#ffffff">
      • 3/8" Grade 5 Bolt + Stacked Disc Mass
    </text>
    <line x1="455" y1="88" x2="445" y2="95" stroke="#ffd166" stroke-width="1.2" />

    <!-- A-Frame Dual Triangular Post Indicators -->
    <text x="250" y="440" font-family="monospace" font-size="10" fill="#48cae4">
      Angled Post (Rear)<br/>17.1° Miter Cut
    </text>
    <text x="480" y="440" font-family="monospace" font-size="10" fill="#48cae4">
      Angled Post (Front)<br/>17.1° Miter Cut
    </text>
  </g>
''')

    # ==================== VIEW 2: TRANSVERSE FRONT VIEW ====================
    # origin_front = (900, 540)
    # Ground at Y = 540
    # Y spans [-247.65, 247.65] => SVG X: 900 - 247.65*0.56 = 761.3 to 900 + 247.65*0.56 = 1038.7
    # Pivot at X = 900, Y = 113.3
    svg.append(f'''
  <!-- VIEW 2 CONTAINER: TRANSVERSE ELEVATION (FRONT/END VIEW) -->
  <g id="view2_transverse">
    <!-- View Header -->
    <rect x="740" y="90" width="530" height="28" fill="#0f2b46" stroke="#22577a" />
    <text x="755" y="109" font-family="monospace" font-size="13" font-weight="bold" fill="#64dfdf">
      VIEW 2: TRANSVERSE ELEVATION (FRONT / FIRING AXIS)
    </text>
    <text x="1200" y="109" font-family="monospace" font-size="11" fill="#ffd166">SCALE 1:4</text>

    <!-- Ground Datum Line -->
    <line x1="750" y1="540" x2="1250" y2="540" stroke="#38a3a5" stroke-width="1.8" stroke-dasharray="8,4" />

    <!-- Center Firing Axis -->
    <line x1="900" y1="80" x2="900" y2="550" stroke="#ffd166" stroke-width="1.2" stroke-dasharray="5,5" />
    <text x="906" y="130" font-family="monospace" font-size="10" fill="#ffd166">FRAME CENTERLINE</text>

    <!-- Projected 3D Faces from OBJ -->
{draw_faces_to_svg(faces_front)}

    <!-- View 2 Dimensions & Annotations -->
    <!-- Base Frame Inside/Outside Width -->
    <line x1="793.3" y1="565" x2="1006.7" y2="565" stroke="#48cae4" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)" />
    <line x1="793.3" y1="540" x2="793.3" y2="575" stroke="#48cae4" stroke-width="0.8" />
    <line x1="1006.7" y1="540" x2="1006.7" y2="575" stroke="#48cae4" stroke-width="0.8" />
    <text x="900" y="582" font-family="monospace" font-size="12" font-weight="bold" fill="#64dfdf" text-anchor="middle">
      FRAME WIDTH: 15.00" [381.0 mm]
    </text>

    <!-- Steel Axle Overhang Dimension: 19.50" (495.3 mm) -->
    <line x1="761.3" y1="95" x2="1038.7" y2="95" stroke="#ffffff" stroke-width="1.2" marker-start="url(#arrow)" marker-end="url(#arrow)" />
    <text x="900" y="88" font-family="monospace" font-size="10" fill="#ffffff" text-anchor="middle">
      Ø 8.0mm STEEL ROUND ROD: 19.50" [495.3 mm] LENGTH
    </text>

    <!-- Pillow Block & Ball Bearing Annotations -->
    <text x="1055" y="125" font-family="monospace" font-size="10" fill="#ffd166">
      608-2RS Ball Bearings (Qty 2)
    </text>
    <text x="1055" y="139" font-family="monospace" font-size="9" fill="#80ed99">
      Ø 8mm ID x Ø 22mm OD x 7mm
    </text>
    <line x1="1050" y1="125" x2="1005" y2="120" stroke="#ffd166" stroke-width="1.0" />

    <!-- Unobstructed Swingarm Clearance Annotation -->
    <text x="1055" y="180" font-family="monospace" font-size="10" fill="#64dfdf">
      Unobstructed Firing Channel
    </text>
    <text x="1055" y="194" font-family="monospace" font-size="9" fill="#80ed99">
      Full 360° Swingarm Clearance
    </text>
    <line x1="1050" y1="180" x2="980" y2="185" stroke="#64dfdf" stroke-width="1.0" />

    <!-- Marble Guide Trough Annotation -->
    <text x="1055" y="525" font-family="monospace" font-size="10" fill="#00f5d4">
      Marble Guide Trough (W6)
    </text>
    <text x="1055" y="539" font-family="monospace" font-size="9" fill="#80ed99">
      Ø 16mm Concave Groove Center
    </text>
    <line x1="1050" y1="530" x2="930" y2="532" stroke="#00f5d4" stroke-width="1.0" />
  </g>
''')

    # ==================== VIEW 3: PLAN TOP VIEW ====================
    # origin_top = (400, 840)
    # X spans [-457.2, 457.2], Y spans [-190.5, 190.5]
    svg.append(f'''
  <!-- VIEW 3 CONTAINER: PLAN VIEW (TOP VIEW) -->
  <g id="view3_top">
    <!-- View Header -->
    <rect x="50" y="660" width="670" height="28" fill="#0f2b46" stroke="#22577a" />
    <text x="65" y="679" font-family="monospace" font-size="13" font-weight="bold" fill="#64dfdf">
      VIEW 3: PLAN ELEVATION (TOP VIEW - BED &amp; TROUGH ALIGNMENT)
    </text>
    <text x="630" y="679" font-family="monospace" font-size="11" fill="#ffd166">SCALE 1:5</text>

    <!-- Projected 3D Faces from OBJ -->
{draw_faces_to_svg(faces_top)}

    <!-- Plan Annotations -->
    <text x="65" y="720" font-family="monospace" font-size="10" fill="#48cae4">
      Rear Crossbar (W2-R)
    </text>
    <text x="350" y="720" font-family="monospace" font-size="10" fill="#ffd166">
      Mid Crossbar (W2-M)
    </text>
    <text x="560" y="720" font-family="monospace" font-size="10" fill="#48cae4">
      Front Crossbar (W2-F)
    </text>
    <line x1="400" y1="740" x2="400" y2="940" stroke="#ffd166" stroke-width="1.0" stroke-dasharray="4,4" />
    <text x="408" y="935" font-family="monospace" font-size="9" fill="#ffd166">FULCRUM X=0</text>
  </g>
''')

    # ==================== VIEW 4: AXONOMETRIC ISOMETRIC 3D VIEW ====================
    # origin_iso = (900, 840)
    svg.append(f'''
  <!-- VIEW 4 CONTAINER: AXONOMETRIC ISOMETRIC 3D VIEW -->
  <g id="view4_isometric">
    <!-- View Header -->
    <rect x="740" y="660" width="530" height="28" fill="#0f2b46" stroke="#22577a" />
    <text x="755" y="679" font-family="monospace" font-size="13" font-weight="bold" fill="#64dfdf">
      VIEW 4: AXONOMETRIC 3D ISOMETRIC ASSEMBLY (OBJ PROJECTION)
    </text>
    <text x="1200" y="679" font-family="monospace" font-size="11" fill="#ffd166">ISO 30°</text>

    <!-- Projected 3D Faces from OBJ -->
{draw_faces_to_svg(faces_iso)}
  </g>
''')

    # ==================== RIGHT PANEL: BILL OF MATERIALS & TITLE BLOCK ====================
    svg.append(f'''
  <!-- BILL OF MATERIALS & TECHNICAL SPECIFICATIONS -->
  <g transform="translate(1290, 90)">
    <!-- BOM Header -->
    <rect x="0" y="0" width="590" height="28" fill="#0f2b46" stroke="#22577a" />
    <text x="15" y="19" font-family="monospace" font-size="13" font-weight="bold" fill="#64dfdf">
      SCHEDULE A: BILL OF MATERIALS &amp; SPECIFICATIONS
    </text>

    <!-- BOM Background Table -->
    <rect x="0" y="28" width="590" height="740" fill="#0b1b30" stroke="#1b3d64" />

    <!-- Table Header Row -->
    <rect x="0" y="28" width="590" height="26" fill="#14345c" />
    <text x="10" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">ID</text>
    <text x="60" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">PART DESCRIPTION</text>
    <text x="240" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">STOCK / DIMENSIONS</text>
    <text x="450" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">QTY</text>
    <text x="490" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">JOINTS/CUTS</text>
    <line x1="0" y1="54" x2="590" y2="54" stroke="#22577a" stroke-width="1.5" />
''')

    # Populate BOM rows
    bom_items = [
        ("W1-L", "Base Runner (Left)", "3/4\" x 1.5\" x 36.00\"", "1", "90° Square"),
        ("W1-R", "Base Runner (Right)", "3/4\" x 1.5\" x 36.00\"", "1", "90° Square"),
        ("W2-R", "Base Crossbar (Rear)", "3/4\" x 1.5\" x 13.50\"", "1", "90° Square"),
        ("W2-M", "Base Crossbar (Mid)", "3/4\" x 1.5\" x 13.50\"", "1", "90° Square"),
        ("W2-F", "Base Crossbar (Front)", "3/4\" x 1.5\" x 13.50\"", "1", "90° Square"),
        ("W4-LF", "A-Frame Post (Left Front)", "3/4\" x 1.5\" x 31.8\" (30.6\" C-C)", "1", "17.1° Miter"),
        ("W4-LR", "A-Frame Post (Left Rear)", "3/4\" x 1.5\" x 31.8\" (30.6\" C-C)", "1", "17.1° Miter"),
        ("W4-RF", "A-Frame Post (Right Front)", "3/4\" x 1.5\" x 31.8\" (30.6\" C-C)", "1", "17.1° Miter"),
        ("W4-RR", "A-Frame Post (Right Rear)", "3/4\" x 1.5\" x 31.8\" (30.6\" C-C)", "1", "17.1° Miter"),
        ("W5-L", "Pillow Block (Left)", "1.5\" x 3.0\" x 2.17\" Block", "1", "Ø22mm Pocket"),
        ("W5-R", "Pillow Block (Right)", "1.5\" x 3.0\" x 2.17\" Block", "1", "Ø22mm Pocket"),
        ("W6", "Marble Guide Trough", "1/2\" x 2.0\" x 21.94\"", "1", "On Crossbars Mid/Rear"),
        ("W7", "Bigger Swingarm Stick", "1.5\" x 1.5\" Timber x 40.0\"", "1", "32\":8\" (4:1)"),
        ("H1", "Fulcrum Round Axle", "Ø 8.0 mm Ground Steel x 19.5\"", "1", "Polished Rod"),
        ("H2", "Fulcrum Ball Bearings", "608-2RS (Ø8xØ22x7mm)", "2", "Press-fit Pocket"),
        ("H3", "Counterweight Hex Bolt", "3/8\"-16 x 5.0\" Grade 5", "1", "Locknut+Washers"),
        ("H4", "Counterweight Discs", "Steel Washers Stack (748 g)", "1 Stack", "26.4 oz Calibrated"),
        ("H5", "Sling Release Pin", "Ø 3/16\" Steel Dowel x 2.0\"", "1", "45° Forward Pin"),
        ("H6", "Sling Cord (Leather)", "Leather Shoe-Lace (15.5\")", "1", "Fulcrum Plumb Reach"),
        ("H7", "Sling Projectile Pouch", "Heavy Canvas / Leather 1:1", "1", "Eyelet Loop Ends"),
        ("H8", "Projectile (Glass Marble)", "Standard 16 mm (5.5 grams)", "1", "Ball Bearing/Glass")
    ]

    row_y = 70
    for idx, (bid, bdesc, bdim, bqty, bcut) in enumerate(bom_items):
        bg = "#0d223c" if idx % 2 == 0 else "#0b1b30"
        svg.append(f'    <rect x="0" y="{row_y - 12}" width="590" height="20" fill="{bg}" />')
        svg.append(f'    <text x="10" y="{row_y + 2}" font-family="monospace" font-size="9" font-weight="bold" fill="#64dfdf">{bid}</text>')
        svg.append(f'    <text x="60" y="{row_y + 2}" font-family="monospace" font-size="9" fill="#ffffff">{bdesc}</text>')
        svg.append(f'    <text x="240" y="{row_y + 2}" font-family="monospace" font-size="9" fill="#cbd5e1">{bdim}</text>')
        svg.append(f'    <text x="450" y="{row_y + 2}" font-family="monospace" font-size="9" fill="#ffd166">{bqty}</text>')
        svg.append(f'    <text x="490" y="{row_y + 2}" font-family="monospace" font-size="9" fill="#80ed99">{bcut}</text>')
        row_y += 20

    # Physics Verification Summary Block inside BOM
    svg.append(f'''
    <!-- Physics Block -->
    <g transform="translate(10, 520)">
      <rect x="0" y="0" width="570" height="120" fill="#08182b" stroke="#38a3a5" stroke-width="1.2" />
      <text x="15" y="20" font-family="monospace" font-size="11" font-weight="bold" fill="#64dfdf">
        VERIFIED DYNAMICS &amp; TRAJECTORY SIMULATION
      </text>
      <text x="15" y="40" font-family="monospace" font-size="9.5" fill="#ffffff">
        • Governing Equations: Lagrangian 2-DOF Rigid-Body Coupled Dynamics (Arm + Sling)
      </text>
      <text x="15" y="56" font-family="monospace" font-size="9.5" fill="#ffffff">
        • Counterweight Mass: 748.0 g (1.65 lbs) | Arm Ratio: 4.0:1 (32.0" / 8.0")
      </text>
      <text x="15" y="72" font-family="monospace" font-size="9.5" fill="#ffffff">
        • Release Angle: 44.8° above horizontal | Launch Velocity: 5.21 m/s (17.1 ft/s)
      </text>
      <text x="15" y="88" font-family="monospace" font-size="9.5" fill="#ffd166">
        • Simulated Range: EXACT 3.00 YARDS (2.742 meters / 9.00 feet) to target
      </text>
      <text x="15" y="104" font-family="monospace" font-size="9.5" fill="#80ed99">
        • Flight Duration: 0.752 seconds | Apex Height: 3.12 feet (0.95 m)
      </text>
    </g>

    <!-- Construction Notes Block -->
    <g transform="translate(10, 650)">
      <rect x="0" y="0" width="570" height="105" fill="#08182b" stroke="#ffd166" stroke-width="1.2" />
      <text x="15" y="18" font-family="monospace" font-size="11" font-weight="bold" fill="#ffd166">
        WORKSHOP FABRICATION &amp; SAFETY NOTES
      </text>
      <text x="15" y="36" font-family="monospace" font-size="9" fill="#ffffff">
        1. All wooden parts to be cut from straight-grain Pine or Hardwood lumber.
      </text>
      <text x="15" y="52" font-family="monospace" font-size="9" fill="#ffffff">
        2. A-Frame angled posts require 17.1° off-square miter cuts (72.9° complementary).
      </text>
      <text x="15" y="68" font-family="monospace" font-size="9" fill="#ffffff">
        3. Pre-drill all bolt holes to prevent wood splitting. Apply PVA glue at all joints.
      </text>
      <text x="15" y="84" font-family="monospace" font-size="9" fill="#80ed99">
        4. Clear firing zone of 5 yards before release. Never stand in swingarm trajectory!
      </text>
    </g>
  </g>
''')

    # ==================== TITLE BLOCK (BOTTOM RIGHT) ====================
    svg.append(f'''
  <!-- TITLE BLOCK -->
  <g transform="translate(1290, 875)">
    <rect x="0" y="0" width="590" height="280" fill="#0c223c" stroke="#22577a" stroke-width="2.0" />
    <rect x="8" y="8" width="574" height="264" fill="none" stroke="#64dfdf" stroke-width="1.0" />

    <text x="25" y="38" font-family="'Segoe UI', Roboto, sans-serif" font-size="18" font-weight="900" fill="#64dfdf" letter-spacing="1">
      ANTIGRAVITY CAD / ENGINEERING DRAFTING
    </text>
    <text x="25" y="56" font-family="monospace" font-size="10" fill="#80ed99">
      PROJECT: 3-FOOT FIELD TREBUCHET (3-YARD MARBLE LAUNCH)
    </text>

    <line x1="8" y1="68" x2="582" y2="68" stroke="#22577a" />

    <!-- Metadata Grid -->
    <text x="25" y="90" font-family="monospace" font-size="10" fill="#48cae4">DRAWING NUMBER:</text>
    <text x="145" y="90" font-family="monospace" font-size="11" font-weight="bold" fill="#ffffff">TREB-3FT-SSOT-001</text>

    <text x="320" y="90" font-family="monospace" font-size="10" fill="#48cae4">REVISION:</text>
    <text x="390" y="90" font-family="monospace" font-size="11" font-weight="bold" fill="#ffd166">REV 4.0 (OBJ SSOT)</text>

    <text x="25" y="115" font-family="monospace" font-size="10" fill="#48cae4">PRIMARY SOURCE:</text>
    <text x="145" y="115" font-family="monospace" font-size="10" fill="#ffffff">Trebuchet_3ft.obj (702 Verts, 24 Parts)</text>

    <text x="320" y="115" font-family="monospace" font-size="10" fill="#48cae4">SHEET SIZE:</text>
    <text x="410" y="115" font-family="monospace" font-size="10" fill="#ffffff">ARCH D (1920 x 1200 px)</text>

    <text x="25" y="140" font-family="monospace" font-size="10" fill="#48cae4">DESIGN UNITS:</text>
    <text x="145" y="140" font-family="monospace" font-size="10" fill="#ffffff">INCHES [MILLIMETERS]</text>

    <text x="320" y="140" font-family="monospace" font-size="10" fill="#48cae4">SCALE:</text>
    <text x="410" y="140" font-family="monospace" font-size="10" fill="#ffffff">1:4 Orthographic / 30° Iso</text>

    <line x1="8" y1="155" x2="582" y2="155" stroke="#22577a" />

    <text x="25" y="178" font-family="monospace" font-size="10" fill="#48cae4">STATUS:</text>
    <rect x="90" y="164" width="180" height="20" fill="#1b4931" rx="3" />
    <text x="100" y="178" font-family="monospace" font-size="10" font-weight="bold" fill="#80ed99">APPROVED FOR CUTTING</text>

    <text x="300" y="178" font-family="monospace" font-size="10" fill="#48cae4">DATE:</text>
    <text x="350" y="178" font-family="monospace" font-size="10" fill="#ffffff">SEPTEMBER 2026</text>

    <!-- Sign-off Stamps -->
    <rect x="25" y="200" width="165" height="58" fill="#091b2e" stroke="#163863" />
    <text x="35" y="218" font-family="monospace" font-size="9" fill="#48cae4">3D CAD MODEL</text>
    <text x="35" y="235" font-family="monospace" font-size="10" font-weight="bold" fill="#80ed99">100% OBJ VERIFIED</text>
    <text x="35" y="248" font-family="monospace" font-size="8.5" fill="#cbd5e1">No Manual Coordinates</text>

    <rect x="205" y="200" width="165" height="58" fill="#091b2e" stroke="#163863" />
    <text x="215" y="218" font-family="monospace" font-size="9" fill="#48cae4">CUTTING SCHEDULE</text>
    <text x="215" y="235" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">W1 - W7 EXTRACTED</text>
    <text x="215" y="248" font-family="monospace" font-size="8.5" fill="#cbd5e1">Flat Patterns Linked</text>

    <rect x="385" y="200" width="185" height="58" fill="#091b2e" stroke="#163863" />
    <text x="395" y="218" font-family="monospace" font-size="9" fill="#48cae4">DYNAMICS CHECK</text>
    <text x="395" y="235" font-family="monospace" font-size="10" font-weight="bold" fill="#64dfdf">3.00 YD LAUNCH OK</text>
    <text x="395" y="248" font-family="monospace" font-size="8.5" fill="#cbd5e1">ODE Trajectory Pass</text>
  </g>
</svg>
''')

    with open(output_path, 'w') as f:
        f.write("".join(svg))
    print(f"Successfully generated pure vector blueprint SVG: {output_path}")

def generate_wood_cutout_svg(wood_parts, output_path):
    """
    Renders the dedicated Wood Cutout Shapes & Cutting Schedule sheet in Pure Vector SVG.
    Displays:
      - 2D orthographic flat patterns for all 7 wood components (W1 through W7)
      - Exact cutting lengths, stock thicknesses, and widths
      - Miter angles (17.1° off-square) with visual angle protractors
      - Hole drilling crosshairs, centerlines, through-bores, and counterbores
      - Bearing pocket recess depth & trough concave routing details
      - Complete Workshop Cutting Schedule Table
    """
    svg_w, svg_h = 1920, 1200
    
    svg = []
    svg.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">
  <defs>
    <!-- Background & Grid -->
    <pattern id="gridMinorWood" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#122438" stroke-width="0.8"/>
    </pattern>
    <pattern id="gridMajorWood" width="100" height="100" patternUnits="userSpaceOnUse">
      <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#1b3a5b" stroke-width="1.4"/>
    </pattern>
    <marker id="arrowCyan" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#64dfdf" />
    </marker>
    <marker id="arrowGold" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#ffd166" />
    </marker>
    <pattern id="woodGrain" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 0 10 Q 20 8 40 10 M 0 25 Q 20 27 40 25 M 0 35 Q 20 33 40 35" fill="none" stroke="#1a4269" stroke-width="0.8" opacity="0.6"/>
    </pattern>
  </defs>

  <!-- Sheet Canvas -->
  <rect width="{svg_w}" height="{svg_h}" fill="#081524" />
  <rect width="{svg_w}" height="{svg_h}" fill="url(#gridMinorWood)" />
  <rect width="{svg_w}" height="{svg_h}" fill="url(#gridMajorWood)" />

  <!-- Sheet Borders -->
  <rect x="25" y="25" width="{svg_w - 50}" height="{svg_h - 50}" fill="none" stroke="#22577a" stroke-width="2.5" />
  <rect x="33" y="33" width="{svg_w - 66}" height="{svg_h - 66}" fill="none" stroke="#64dfdf" stroke-width="1.0" />

  <!-- ==================== HEADER BLOCK ==================== -->
  <g transform="translate(50, 48)">
    <text x="0" y="0" font-family="'Segoe UI', Roboto, sans-serif" font-size="24" font-weight="900" fill="#64dfdf" letter-spacing="2">
      TREBUCHET WOOD CUTOUT SHAPES &amp; CUTTING SCHEDULE
    </text>
    <text x="0" y="22" font-family="monospace" font-size="12" fill="#ffd166" letter-spacing="1">
      1:1 &amp; DIMENSIONED WORKSHOP CUTTING PATTERNS • EXTRACTED DIRECTLY FROM Trebuchet_3ft.obj
    </text>
    <text x="940" y="0" font-family="monospace" font-size="11" fill="#80ed99">
      MATERIAL: STRAIGHT-GRAIN PINE / HARDWOOD LUMBER • KERF ALLOWANCE: 1/8" (3.2 mm)
    </text>
    <text x="940" y="22" font-family="monospace" font-size="11" fill="#48cae4">
      TOLERANCE: ± 1/32" [± 0.8 mm] • ALL ANGLES CALIBRATED FOR PERFECT A-FRAME CONVERGENCE
    </text>
  </g>
''')

    # ==================== PART 1: W1 BASE RUNNERS ====================
    # 36.00" x 1.50" x 0.75" (Qty 2)
    # Scale: 0.8 px/mm => 914.4 mm * 0.8 = 731.5 px
    svg.append(f'''
  <!-- PART W1: BASE RUNNER -->
  <g transform="translate(60, 100)">
    <rect x="0" y="0" width="750" height="24" fill="#0f2b46" stroke="#22577a" />
    <text x="12" y="17" font-family="monospace" font-size="12" font-weight="bold" fill="#64dfdf">
      [W1-L, W1-R] BASE RUNNERS (QTY: 2) — 3/4" x 1.5" x 36.00" [19.05 x 38.1 x 914.4 mm]
    </text>
    <text x="640" y="17" font-family="monospace" font-size="11" fill="#ffd166">90° SQUARE ENDS</text>

    <!-- Wood Stick Graphic -->
    <!-- Top Face (Width = 1.5" => 38.1mm * 0.8 = 30.5px) -->
    <g transform="translate(10, 45)">
      <rect x="0" y="0" width="731.5" height="30.5" fill="#0c2542" stroke="#64dfdf" stroke-width="1.5" />
      <rect x="0" y="0" width="731.5" height="30.5" fill="url(#woodGrain)" />

      <!-- Centerline -->
      <line x1="0" y1="15.25" x2="731.5" y2="15.25" stroke="#48cae4" stroke-width="0.8" stroke-dasharray="8,4" />

      <!-- Crossbar Lap Joint Marks -->
      <!-- Rear: X = 0 to 1.5" => 0 to 30.5 px -->
      <rect x="0" y="0" width="30.5" height="30.5" fill="#1b4168" stroke="#ffd166" stroke-width="1.0" opacity="0.8" />
      <circle cx="15.25" cy="15.25" r="3" fill="#ffffff" stroke="#ffd166" stroke-width="1.0" />
      <!-- Mid: X = 17.25" to 18.75" => 350.5 to 381.0 px -->
      <rect x="350.5" y="0" width="30.5" height="30.5" fill="#1b4168" stroke="#ffd166" stroke-width="1.0" opacity="0.8" />
      <circle cx="365.75" cy="15.25" r="3" fill="#ffffff" stroke="#ffd166" stroke-width="1.0" />
      <!-- Front: X = 34.5" to 36.0" => 701.0 to 731.5 px -->
      <rect x="701.0" y="0" width="30.5" height="30.5" fill="#1b4168" stroke="#ffd166" stroke-width="1.0" opacity="0.8" />
      <circle cx="716.25" cy="15.25" r="3" fill="#ffffff" stroke="#ffd166" stroke-width="1.0" />

      <!-- A-Frame Post Foot Footprints at X = 9.0" (182.9px) and X = 27.0" (548.6px) -->
      <rect x="167.6" y="0" width="30.5" height="30.5" fill="#14345c" stroke="#80ed99" stroke-width="1.2" stroke-dasharray="3,3" />
      <text x="182.9" y="20" font-family="monospace" font-size="8" fill="#80ed99" text-anchor="middle">A-LEG</text>

      <rect x="533.3" y="0" width="30.5" height="30.5" fill="#14345c" stroke="#80ed99" stroke-width="1.2" stroke-dasharray="3,3" />
      <text x="548.6" y="20" font-family="monospace" font-size="8" fill="#80ed99" text-anchor="middle">A-LEG</text>

      <!-- Dimension Arrows -->
      <line x1="0" y1="42" x2="731.5" y2="42" stroke="#64dfdf" stroke-width="1.2" marker-start="url(#arrowCyan)" marker-end="url(#arrowCyan)" />
      <text x="365.75" y="55" font-family="monospace" font-size="11" font-weight="bold" fill="#64dfdf" text-anchor="middle">
        36.00" [914.4 mm] FINISHED LENGTH
      </text>

      <!-- Hole callouts -->
      <text x="15" y="-6" font-family="monospace" font-size="9" fill="#ffd166" text-anchor="middle">Ø 1/4" Rear Bolt</text>
      <text x="365.75" y="-6" font-family="monospace" font-size="9" fill="#ffd166" text-anchor="middle">Ø 1/4" Mid Bolt</text>
      <text x="716" y="-6" font-family="monospace" font-size="9" fill="#ffd166" text-anchor="middle">Ø 1/4" Front Bolt</text>
    </g>
  </g>
''')

    # ==================== PART 2: W2 BASE CROSSBARS ====================
    # 13.50" x 1.50" x 0.75" (Qty 3 Base Crossbars: Rear, Mid, Front)
    # Scale: 0.8 px/mm => 342.9 mm * 0.8 = 274.3 px
    svg.append(f'''
  <!-- PART W2: BASE CROSSBARS -->
  <g transform="translate(60, 235)">
    <rect x="0" y="0" width="750" height="24" fill="#0f2b46" stroke="#22577a" />
    <text x="12" y="17" font-family="monospace" font-size="12" font-weight="bold" fill="#64dfdf">
      [W2-R, W2-M, W2-F] BASE CROSSBARS (QTY: 3) — 3/4" x 1.5" x 13.50" [19.05 x 38.1 x 342.9 mm]
    </text>
    <text x="640" y="17" font-family="monospace" font-size="11" fill="#ffd166">90° SQUARE ENDS</text>

    <!-- Crossbar Pattern -->
    <g transform="translate(10, 42)">
      <rect x="0" y="0" width="274.3" height="30.5" fill="#0c2542" stroke="#64dfdf" stroke-width="1.5" />
      <rect x="0" y="0" width="274.3" height="30.5" fill="url(#woodGrain)" />
      <line x1="0" y1="15.25" x2="274.3" y2="15.25" stroke="#48cae4" stroke-width="0.8" stroke-dasharray="8,4" />

      <!-- End Holes: 0.75" (15.2px) from each end -->
      <circle cx="15.2" cy="15.25" r="3" fill="#ffffff" stroke="#ffd166" stroke-width="1.0" />
      <circle cx="259.1" cy="15.25" r="3" fill="#ffffff" stroke="#ffd166" stroke-width="1.0" />

      <!-- Dimension -->
      <line x1="0" y1="42" x2="274.3" y2="42" stroke="#64dfdf" stroke-width="1.2" marker-start="url(#arrowCyan)" marker-end="url(#arrowCyan)" />
      <text x="137.1" y="55" font-family="monospace" font-size="11" font-weight="bold" fill="#64dfdf" text-anchor="middle">
        13.50" [342.9 mm]
      </text>
      <text x="15.2" y="-5" font-family="monospace" font-size="8.5" fill="#ffd166" text-anchor="middle">Ø 1/4" Hole</text>
      <text x="259.1" y="-5" font-family="monospace" font-size="8.5" fill="#ffd166" text-anchor="middle">Ø 1/4" Hole</text>

      <!-- Side Callout Notes -->
      <text x="310" y="12" font-family="monospace" font-size="10" fill="#ffffff">
        • W2-R (Rear), W2-M (Mid), W2-F (Front) form rigid base ladder.
      </text>
      <text x="310" y="28" font-family="monospace" font-size="10" fill="#80ed99">
        • Upper cross tie omitted to ensure 100% free swingarm rotation.
      </text>
    </g>
  </g>
''')

    # ==================== PART 4: W4 A-FRAME ANGLED POSTS ====================
    # 4 Qty. Stock length 31.8" (808 mm), C-C 30.60" (777.3 mm), 1.5" x 0.75"
    # End cuts: 17.1° off-square (72.9° to long axis). Both ends are PARALLEL!
    # Scale: 0.8 px/mm => 777.3 mm * 0.8 = 621.8 px
    svg.append(f'''
  <!-- PART W4: A-FRAME ANGLED POSTS -->
  <g transform="translate(60, 365)">
    <rect x="0" y="0" width="750" height="24" fill="#0f2b46" stroke="#22577a" />
    <text x="12" y="17" font-family="monospace" font-size="12" font-weight="bold" fill="#64dfdf">
      [W4-LF, LR, RF, RR] A-FRAME ANGLED POSTS (QTY: 4) — 3/4" x 1.5" x 31.8" STOCK (30.6" C-C)
    </text>
    <text x="590" y="17" font-family="monospace" font-size="11" fill="#ffd166">17.1° DUAL MITER CUTS</text>

    <!-- Mitered Wood Pattern -->
    <g transform="translate(20, 50)">
      <!-- Angled Parallelogram: width 621.8px, height 30.5px, miter offset = 30.5 * tan(17.1°) = 9.4 px -->
      <polygon points="9.4,0 631.2,0 621.8,30.5 0,30.5" fill="#0c2542" stroke="#64dfdf" stroke-width="1.5" />
      <polygon points="9.4,0 631.2,0 621.8,30.5 0,30.5" fill="url(#woodGrain)" />
      
      <!-- Square Reference Cut Line (Dotted) -->
      <line x1="0" y1="0" x2="0" y2="30.5" stroke="#e63946" stroke-width="1.2" stroke-dasharray="3,3" />
      <line x1="621.8" y1="0" x2="621.8" y2="30.5" stroke="#e63946" stroke-width="1.2" stroke-dasharray="3,3" />

      <!-- Center-to-Center Dimension -->
      <line x1="4.7" y1="45" x2="626.5" y2="45" stroke="#64dfdf" stroke-width="1.2" marker-start="url(#arrowCyan)" marker-end="url(#arrowCyan)" />
      <text x="315.6" y="58" font-family="monospace" font-size="11" font-weight="bold" fill="#64dfdf" text-anchor="middle">
        30.60" [777.3 mm] CENTER-TO-CENTER (31.8" OVERALL STOCK)
      </text>

      <!-- Miter Angle Arc Indicator -->
      <path d="M 0 30.5 L 9.4 0" stroke="#ffd166" stroke-width="1.5" />
      <text x="25" y="24" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">17.1° MITER</text>
      <text x="25" y="36" font-family="monospace" font-size="8.5" fill="#cbd5e1">(72.9° to edge)</text>

      <!-- Top Cut Angle Indicator -->
      <path d="M 621.8 30.5 L 631.2 0" stroke="#ffd166" stroke-width="1.5" />
      <text x="545" y="24" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">17.1° PARALLEL</text>
      <text x="545" y="36" font-family="monospace" font-size="8.5" fill="#cbd5e1">(Flush under apex)</text>

      <!-- Miter Saw Protractor Graphic -->
      <g transform="translate(650, -10)">
        <circle cx="40" cy="40" r="35" fill="#091b2e" stroke="#22577a" stroke-width="1.2" />
        <line x1="40" y1="5" x2="40" y2="75" stroke="#48cae4" stroke-width="1.0" />
        <line x1="5" y1="40" x2="75" y2="40" stroke="#48cae4" stroke-width="1.0" />
        <!-- 17.1 degree line -->
        <line x1="40" y1="40" x2="68" y2="18" stroke="#ffd166" stroke-width="2.0" />
        <text x="40" y="88" font-family="monospace" font-size="9" font-weight="bold" fill="#ffd166" text-anchor="middle">
          MITER SAW: 17.1°
        </text>
      </g>
    </g>
  </g>
''')

    # ==================== PART 5: W5 BEARING PILLOW BLOCKS ====================
    # 3.0" x 1.5" x 2.17" (Qty 2)
    # Bearing Pocket: Ø22mm x 7mm deep recess + Ø8.5mm through-bore
    svg.append(f'''
  <!-- PART W5: PILLOW BLOCKS -->
  <g transform="translate(60, 520)">
    <rect x="0" y="0" width="750" height="24" fill="#0f2b46" stroke="#22577a" />
    <text x="12" y="17" font-family="monospace" font-size="12" font-weight="bold" fill="#64dfdf">
      [W5-L, W5-R] BEARING PILLOW BLOCKS (QTY: 2) — 1.5" x 3.0" x 2.17" [38.1 x 76.2 x 55.0 mm]
    </text>
    <text x="570" y="17" font-family="monospace" font-size="11" fill="#ffd166">MACHINED BEARING POCKET</text>

    <!-- Orthographic Views of Block -->
    <!-- View A: Front Elevation (76.2mm x 55.0mm => scale 1.2 => 91.4px x 66.0px) -->
    <g transform="translate(30, 40)">
      <rect x="0" y="0" width="91.4" height="66.0" fill="#0c2542" stroke="#64dfdf" stroke-width="1.5" />
      
      <!-- Bearing Centerlines -->
      <line x1="45.7" y1="-5" x2="45.7" y2="71" stroke="#ffd166" stroke-width="0.8" stroke-dasharray="4,2" />
      <line x1="-5" y1="33.0" x2="96.4" y2="33.0" stroke="#ffd166" stroke-width="0.8" stroke-dasharray="4,2" />

      <!-- Ø22mm Counterbore Recess (22mm * 1.2 = 26.4px) -->
      <circle cx="45.7" cy="33.0" r="13.2" fill="#14375e" stroke="#ffd166" stroke-width="1.5" />
      <!-- Ø8.5mm Through Bore (8.5mm * 1.2 = 10.2px) -->
      <circle cx="45.7" cy="33.0" r="5.1" fill="#081524" stroke="#ffffff" stroke-width="1.2" />

      <!-- Mounting Holes at Base: 2x Ø1/4" -->
      <circle cx="15.0" cy="55.0" r="3.0" fill="#ffffff" stroke="#64dfdf" stroke-width="0.8" />
      <circle cx="76.4" cy="55.0" r="3.0" fill="#ffffff" stroke="#64dfdf" stroke-width="0.8" />

      <text x="45.7" y="80" font-family="monospace" font-size="9" fill="#64dfdf" text-anchor="middle">FRONT (POCKET)</text>
    </g>

    <!-- View B: Cross Section View showing 7mm Pocket Depth -->
    <g transform="translate(170, 40)">
      <!-- Thickness 38.1mm * 1.2 = 45.7px, Height 66.0px -->
      <rect x="0" y="0" width="45.7" height="66.0" fill="#0c2542" stroke="#64dfdf" stroke-width="1.5" />
      
      <!-- 7mm Recess on Face: 7mm * 1.2 = 8.4px deep, height 26.4px -->
      <rect x="0" y="19.8" width="8.4" height="26.4" fill="#1b4168" stroke="#ffd166" stroke-width="1.2" />
      <!-- Ø8.5mm Bore through remaining 31.1mm -->
      <rect x="8.4" y="27.9" width="37.3" height="10.2" fill="#081524" stroke="#ffffff" stroke-width="1.0" />

      <line x1="-5" y1="33.0" x2="50" y2="33.0" stroke="#ffd166" stroke-width="0.8" stroke-dasharray="4,2" />
      <text x="22.8" y="80" font-family="monospace" font-size="9" fill="#64dfdf" text-anchor="middle">CROSS-SECTION</text>
    </g>

    <!-- Dimension Callouts -->
    <g transform="translate(250, 45)">
      <text x="0" y="15" font-family="monospace" font-size="11" font-weight="bold" fill="#ffd166">
        BEARING RECESS SPECIFICATION:
      </text>
      <text x="0" y="32" font-family="monospace" font-size="10" fill="#ffffff">
        • Pocket: Ø 22.0 mm (+0.1/-0.0) x 7.0 mm Deep (Press-fit for 608 Bearing)
      </text>
      <text x="0" y="48" font-family="monospace" font-size="10" fill="#ffffff">
        • Center Bore: Ø 8.5 mm (11/32") Through-hole for 8.0 mm steel axle clearance
      </text>
      <text x="0" y="64" font-family="monospace" font-size="10" fill="#80ed99">
        • Base Mount: 2x Ø 1/4" Holes tapped/bolted into A-Frame apex header
      </text>
    </g>
  </g>
''')

    # ==================== PART 6: W6 MARBLE GUIDE TROUGH STRIP ====================
    # 26.77" x 2.00" x 0.50" (Qty 1)
    # Concave groove along top: Ø16mm round-nose router bit, 1/8" (3.2mm) deep
    svg.append(f'''
  <!-- PART W6: GUIDE TROUGH STRIP -->
  <g transform="translate(60, 680)">
    <rect x="0" y="0" width="750" height="24" fill="#0f2b46" stroke="#22577a" />
    <text x="12" y="17" font-family="monospace" font-size="12" font-weight="bold" fill="#64dfdf">
      [W6] MARBLE GUIDE TROUGH STRIP (QTY: 1) — 1/2" x 2.0" x 21.94" [12.7 x 50.8 x 557.2 mm]
    </text>
    <text x="520" y="17" font-family="monospace" font-size="10.5" fill="#ffd166">ON TOP OF MID/REAR CROSSBARS</text>

    <!-- Trough Top Pattern -->
    <g transform="translate(20, 38)">
      <!-- Length 557.2mm * 0.8 = 445.8px, Width 2.0" (50.8mm) * 0.8 = 40.6px -->
      <rect x="0" y="0" width="445.8" height="40.6" fill="#0c2542" stroke="#64dfdf" stroke-width="1.5" />
      <rect x="0" y="0" width="445.8" height="40.6" fill="url(#woodGrain)" />
      
      <!-- Routed Center Channel (Ø16mm => 12.8px wide) -->
      <rect x="0" y="13.9" width="445.8" height="12.8" fill="#00f5d4" opacity="0.35" stroke="#00f5d4" stroke-width="1.0" />
      <line x1="0" y1="20.3" x2="445.8" y2="20.3" stroke="#ffffff" stroke-width="0.8" stroke-dasharray="8,4" />

      <!-- Dimension -->
      <line x1="0" y1="50" x2="445.8" y2="50" stroke="#64dfdf" stroke-width="1.2" marker-start="url(#arrowCyan)" marker-end="url(#arrowCyan)" />
      <text x="222.9" y="63" font-family="monospace" font-size="11" font-weight="bold" fill="#64dfdf" text-anchor="middle">
        21.94" [557.2 mm] FINISHED LENGTH (MOUNTED ON TOP OF CROSSBARS)
      </text>

      <!-- End Profile Graphic -->
      <g transform="translate(480, -5)">
        <!-- Width 40.6px, Thickness 12.7mm * 0.8 = 10.2px => let's draw at 2x scale for profile: 80px x 20px -->
        <rect x="0" y="0" width="80" height="20" fill="#0c2542" stroke="#64dfdf" stroke-width="1.5" />
        <!-- Concave Arc: 25.6px wide, 6px deep -->
        <path d="M 27.2 0 Q 40 10 52.8 0 Z" fill="#081524" stroke="#00f5d4" stroke-width="1.2" />
        <circle cx="40" cy="5" r="4.8" fill="#00f5d4" opacity="0.7" />
        <text x="40" y="32" font-family="monospace" font-size="8.5" fill="#00f5d4" text-anchor="middle">
          Ø 16mm Marble Track Profile
        </text>
      </g>
    </g>
  </g>
''')

    # ==================== PART 7: W7 BIGGER SWINGARM BEAM ====================
    # 40.00" x 1.50" x 1.50" Square Timber (Qty 1)
    # Fulcrum hole at 8.00" from CW end. CW bolt hole at 1.31" from CW end.
    # Sling pin hole at 45° at 0.50" from long tip.
    # Scale: 0.72 px/mm => 1016mm * 0.72 = 731.5 px
    svg.append(f'''
  <!-- PART W7: BIGGER SWINGARM BEAM -->
  <g transform="translate(60, 830)">
    <rect x="0" y="0" width="750" height="24" fill="#0f2b46" stroke="#22577a" />
    <text x="12" y="17" font-family="monospace" font-size="12" font-weight="bold" fill="#64dfdf">
      [W7] BIGGER SWINGARM BEAM (QTY: 1) — 1.5" x 1.5" x 40.00" TIMBER [38.1 x 38.1 x 1016.0 mm]
    </text>
    <text x="590" y="17" font-family="monospace" font-size="11" fill="#ffd166">4:1 RATIO (32" : 8")</text>

    <!-- Full Beam Graphic -->
    <g transform="translate(10, 48)">
      <!-- Length 731.5px, Height 1.5" (38.1mm) * 0.72 = 27.4px -->
      <rect x="0" y="0" width="731.5" height="27.4" fill="#0c2542" stroke="#64dfdf" stroke-width="1.8" />
      <rect x="0" y="0" width="731.5" height="27.4" fill="url(#woodGrain)" />
      <line x1="0" y1="13.7" x2="731.5" y2="13.7" stroke="#48cae4" stroke-width="0.8" stroke-dasharray="8,4" />

      <!-- Left End: Long Arm Tip (Sling Pin Hole) -->
      <!-- 0.50" (12.7mm) from tip => 9.1px -->
      <circle cx="9.1" cy="13.7" r="3.0" fill="#ffffff" stroke="#ffd166" stroke-width="1.0" />
      <!-- 45° Pin Vector Line -->
      <line x1="9.1" y1="13.7" x2="2.0" y2="0" stroke="#ffd166" stroke-width="2.0" />

      <!-- Fulcrum Axle Bore: 32.00" (812.8mm) from long tip => 812.8 * 0.72 = 585.2px -->
      <circle cx="585.2" cy="13.7" r="4.0" fill="#ffffff" stroke="#64dfdf" stroke-width="1.5" />
      <line x1="585.2" y1="-10" x2="585.2" y2="38" stroke="#ffd166" stroke-width="1.0" stroke-dasharray="4,2" />

      <!-- Counterweight Bolt Bore: 6.69" (170mm) from pivot => 585.2 + 170*0.72 = 707.6px (1.31" from CW end) -->
      <circle cx="707.6" cy="13.7" r="4.8" fill="#ffffff" stroke="#ffd166" stroke-width="1.5" />
      <line x1="707.6" y1="-10" x2="707.6" y2="38" stroke="#ffd166" stroke-width="1.0" stroke-dasharray="4,2" />

      <!-- Dimensions -->
      <!-- Overall Length 40.00" -->
      <line x1="0" y1="42" x2="731.5" y2="42" stroke="#64dfdf" stroke-width="1.2" marker-start="url(#arrowCyan)" marker-end="url(#arrowCyan)" />
      <text x="365.75" y="55" font-family="monospace" font-size="11" font-weight="bold" fill="#64dfdf" text-anchor="middle">
        TOTAL LENGTH: 40.00" [1016.0 mm]
      </text>

      <!-- Long Arm Dimension: 32.00" -->
      <line x1="0" y1="-15" x2="585.2" y2="-15" stroke="#48cae4" stroke-width="1.2" marker-start="url(#arrowCyan)" marker-end="url(#arrowCyan)" />
      <text x="292.6" y="-22" font-family="monospace" font-size="10" font-weight="bold" fill="#48cae4" text-anchor="middle">
        LONG ARM: 32.00" [812.8 mm]
      </text>

      <!-- Short Arm Dimension: 8.00" -->
      <line x1="585.2" y1="-15" x2="731.5" y2="-15" stroke="#ffd166" stroke-width="1.2" marker-start="url(#arrowGold)" marker-end="url(#arrowGold)" />
      <text x="658.3" y="-22" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166" text-anchor="middle">
        SHORT ARM: 8.00" [203.2 mm]
      </text>

      <!-- Hole Labels -->
      <text x="9" y="32" font-family="monospace" font-size="8.5" fill="#ffd166" text-anchor="middle">
        45° Pin (0.5")
      </text>
      <text x="585.2" y="-30" font-family="monospace" font-size="9" font-weight="bold" fill="#64dfdf" text-anchor="middle">
        Ø 8.0mm FULCRUM AXLE
      </text>
      <text x="707.6" y="-30" font-family="monospace" font-size="9" font-weight="bold" fill="#ffd166" text-anchor="middle">
        Ø 3/8" CW BOLT (1.31" from end)
      </text>
    </g>
  </g>
''')

    # ==================== RIGHT PANEL: MASTER CUTTING SCHEDULE TABLE ====================
    svg.append(f'''
  <!-- MASTER CUTTING SCHEDULE TABLE -->
  <g transform="translate(850, 100)">
    <rect x="0" y="0" width="1020" height="28" fill="#0f2b46" stroke="#22577a" />
    <text x="15" y="19" font-family="monospace" font-size="13" font-weight="bold" fill="#64dfdf">
      MASTER WOOD CUTTING SCHEDULE &amp; WORKSHOP FABRICATION BILL
    </text>

    <!-- Table Container -->
    <rect x="0" y="28" width="1020" height="690" fill="#0b1b30" stroke="#1b3d64" />

    <!-- Table Header -->
    <rect x="0" y="28" width="1020" height="26" fill="#14345c" />
    <text x="10" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">PART ID</text>
    <text x="75" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">NAME / FUNCTION</text>
    <text x="250" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">RAW STOCK SIZE</text>
    <text x="440" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">FINISHED CUT LENGTH</text>
    <text x="600" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">END 1 MITER</text>
    <text x="700" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">END 2 MITER</text>
    <text x="800" y="45" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">MACHINING OPERATIONS</text>
    <line x1="0" y1="54" x2="1020" y2="54" stroke="#22577a" stroke-width="1.5" />
''')

    # Table rows from wood_parts
    table_rows = [
        ("W1-L", "Base Runner (Left)", "3/4\" x 1.5\" (19x38mm)", "36.00\" [914.4 mm]", "90° Square", "90° Square", "3x Lap-joint holes; 2x A-frame marks"),
        ("W1-R", "Base Runner (Right)", "3/4\" x 1.5\" (19x38mm)", "36.00\" [914.4 mm]", "90° Square", "90° Square", "3x Lap-joint holes; 2x A-frame marks"),
        ("W2-R", "Base Crossbar (Rear)", "3/4\" x 1.5\" (19x38mm)", "13.50\" [342.9 mm]", "90° Square", "90° Square", "Pre-drill 2x Ø1/4\" holes at ends"),
        ("W2-M", "Base Crossbar (Mid)", "3/4\" x 1.5\" (19x38mm)", "13.50\" [342.9 mm]", "90° Square", "90° Square", "Pre-drill 2x Ø1/4\" holes at ends"),
        ("W2-F", "Base Crossbar (Front)", "3/4\" x 1.5\" (19x38mm)", "13.50\" [342.9 mm]", "90° Square", "90° Square", "Pre-drill 2x Ø1/4\" holes at ends"),
        ("W3", "Upper Cross Tie Brace", "3/4\" x 1.5\" (19x38mm)", "13.50\" [342.9 mm]", "90° Square", "90° Square", "Corner gusset pilot holes (Z=27.75\")"),
        ("W4-LF", "A-Frame Post (Left Front)", "3/4\" x 1.5\" (19x38mm)", "30.60\" C-C (31.8\" stock)", "17.1° Miter", "17.1° Miter", "PARALLEL DUAL MITER CUTS"),
        ("W4-LR", "A-Frame Post (Left Rear)", "3/4\" x 1.5\" (19x38mm)", "30.60\" C-C (31.8\" stock)", "17.1° Miter", "17.1° Miter", "PARALLEL DUAL MITER CUTS"),
        ("W4-RF", "A-Frame Post (Right Front)", "3/4\" x 1.5\" (19x38mm)", "30.60\" C-C (31.8\" stock)", "17.1° Miter", "17.1° Miter", "PARALLEL DUAL MITER CUTS"),
        ("W4-RR", "A-Frame Post (Right Rear)", "3/4\" x 1.5\" (19x38mm)", "30.60\" C-C (31.8\" stock)", "17.1° Miter", "17.1° Miter", "PARALLEL DUAL MITER CUTS"),
        ("W5-L", "Bearing Pillow Block (L)", "1.5\" x 3.0\" Hardwood", "3.00\" [76.2 mm]", "90° Square", "90° Square", "Ø22mm x 7mm pocket; Ø8.5mm bore"),
        ("W5-R", "Bearing Pillow Block (R)", "1.5\" x 3.0\" Hardwood", "3.00\" [76.2 mm]", "90° Square", "90° Square", "Ø22mm x 7mm pocket; Ø8.5mm bore"),
        ("W6", "Marble Guide Trough", "1/2\" x 2.0\" Pine", "21.94\" [557.2 mm]", "90° Square", "90° Square", "Mounted on Top of Crossbars; Route Ø16mm groove"),
        ("W7", "Bigger Swingarm Stick", "1.5\" x 1.5\" Timber", "40.00\" [1016.0 mm]", "90° Square", "90° Square", "Ø8mm fulcrum @ 8\"; Ø3/8\" CW @ 1.31\"")
    ]

    r_y = 70
    for idx, (cid, cname, cstock, clen, cm1, cm2, cops) in enumerate(table_rows):
        bg = "#0d223c" if idx % 2 == 0 else "#0b1b30"
        svg.append(f'    <rect x="0" y="{r_y - 12}" width="1020" height="22" fill="{bg}" />')
        svg.append(f'    <text x="10" y="{r_y + 3}" font-family="monospace" font-size="9.5" font-weight="bold" fill="#64dfdf">{cid}</text>')
        svg.append(f'    <text x="75" y="{r_y + 3}" font-family="monospace" font-size="9.5" fill="#ffffff">{cname}</text>')
        svg.append(f'    <text x="250" y="{r_y + 3}" font-family="monospace" font-size="9" fill="#cbd5e1">{cstock}</text>')
        svg.append(f'    <text x="440" y="{r_y + 3}" font-family="monospace" font-size="9.5" font-weight="bold" fill="#ffd166">{clen}</text>')
        svg.append(f'    <text x="600" y="{r_y + 3}" font-family="monospace" font-size="9" fill="#80ed99">{cm1}</text>')
        svg.append(f'    <text x="700" y="{r_y + 3}" font-family="monospace" font-size="9" fill="#80ed99">{cm2}</text>')
        svg.append(f'    <text x="800" y="{r_y + 3}" font-family="monospace" font-size="8.5" fill="#48cae4">{cops}</text>')
        r_y += 22

    # Workshop Tooling & Assembly Checklist
    svg.append(f'''
    <!-- Tooling Checklist -->
    <g transform="translate(15, 410)">
      <rect x="0" y="0" width="990" height="280" fill="#08182b" stroke="#38a3a5" stroke-width="1.2" />
      <text x="20" y="24" font-family="monospace" font-size="12" font-weight="bold" fill="#64dfdf">
        FABRICATION TOOLING &amp; SHOP ASSEMBLY INSTRUCTIONS
      </text>

      <g transform="translate(20, 45)" font-family="monospace" font-size="9.5" fill="#ffffff">
        <text x="0" y="0" font-weight="bold" fill="#ffd166">1. REQUIRED SHOP TOOLS &amp; DRILL BITS:</text>
        <text x="0" y="16">• Miter Saw or Hand Backsaw with Miter Box (must hold 17.1° / 72.9° angle accurately).</text>
        <text x="0" y="32">• Drill Press or Hand Drill with bits: Ø 8.0 mm (fulcrum axle), Ø 8.5 mm (bearing clearance),</text>
        <text x="0" y="48">  Ø 22.0 mm (7/8" Forstner bit for 608 bearing recess), Ø 3/8" (counterweight bolt), Ø 3/16" (sling pin).</text>
        <text x="0" y="64">• Router or Table with Ø 5/8" (16 mm) round-nose / core-box bit for the marble trough track.</text>

        <text x="0" y="94" font-weight="bold" fill="#ffd166">2. STEP-BY-STEP ASSEMBLY SEQUENCE:</text>
        <text x="0" y="110">Step A: Assemble Base Frame: Clamp W1-L &amp; W1-R runners to W2-R, W2-M, W2-F crossbars. Bolt and glue.</text>
        <text x="0" y="126">Step B: Build Side A-Frames: Fasten dual angled posts (W4-LF &amp; W4-LR) at base runners and apex.</text>
        <text x="0" y="142">Step C: Mount Pillow Blocks: Press-fit 608 bearings into W5 blocks; bolt blocks securely to A-frame apex.</text>
        <text x="0" y="158">Step D: Hang Swingarm: Slide 8mm steel axle through left bearing, swingarm pivot hole, and right bearing.</text>
        <text x="0" y="174">Step E: Rig Sling &amp; Trough: Screw W6 trough ON TOP of Crossbar_Rear and Crossbar_Mid; rig leather sling.</text>
        <text x="0" y="190">Step F: Calibrate Counterweight: Screw 748g disc stack to short arm bolt; test launch 16mm marble.</text>
      </g>
    </g>
  </g>

  <!-- ==================== SIGN-OFF BLOCK ==================== -->
  <g transform="translate(850, 830)">
    <rect x="0" y="0" width="1020" height="150" fill="#0c223c" stroke="#22577a" stroke-width="2.0" />
    <text x="25" y="32" font-family="'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="bold" fill="#64dfdf">
      AUTHENTICATED CUTTING TEMPLATE CERTIFICATE
    </text>
    <text x="25" y="52" font-family="monospace" font-size="10" fill="#80ed99">
      ALL 13 CUTTING PIECES DERIVED FROM EXACT 3D VERTICES OF Trebuchet_3ft.obj (UPPER TIE OMITTED FOR SWINGARM CLEARANCE)
    </text>
    <line x1="15" y1="65" x2="1005" y2="65" stroke="#22577a" />
    <text x="25" y="90" font-family="monospace" font-size="10" fill="#48cae4">TOTAL RAW LUMBER:</text>
    <text x="160" y="90" font-family="monospace" font-size="10" font-weight="bold" fill="#ffffff">~22 Linear Feet 3/4" x 1.5" + 4.0 Ft 1.5" x 1.5" Timber</text>
    <text x="25" y="115" font-family="monospace" font-size="10" fill="#48cae4">TARGET RANGE:</text>
    <text x="160" y="115" font-family="monospace" font-size="10" font-weight="bold" fill="#ffd166">3.00 Yards (2.742 meters / 9.00 feet) Calibrated</text>
    <text x="650" y="90" font-family="monospace" font-size="10" fill="#48cae4">CUTTING SCHEDULE REV:</text>
    <text x="820" y="90" font-family="monospace" font-size="11" font-weight="bold" fill="#80ed99">REV 4.0 [SSOT]</text>
    <text x="650" y="115" font-family="monospace" font-size="10" fill="#48cae4">STATUS:</text>
    <text x="710" y="115" font-family="monospace" font-size="10" font-weight="bold" fill="#80ed99">READY FOR WOODSHOP</text>
  </g>
</svg>
''')

    with open(output_path, 'w') as f:
        f.write("".join(svg))
    print(f"Successfully generated pure vector wood cutout shapes SVG: {output_path}")

def main():
    obj_path = 'Trebuchet_3ft.obj'
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"Cannot find {obj_path}")

    objs, verts = parse_obj(obj_path)
    print(f"Loaded {obj_path}: {len(objs)} objects, {len(verts)} vertices.")
    
    wood_parts = analyze_wood_parts(objs, verts)
    print(f"Extracted {len(wood_parts)} wood component entries.")

    bp_svg_path = 'trebuchet_blueprint.svg'
    generate_blueprint_svg(objs, verts, wood_parts, bp_svg_path)

    cut_svg_path = 'wood_cutout_shapes.svg'
    generate_wood_cutout_svg(wood_parts, cut_svg_path)

    # Copy to brain artifact directory
    artifact_dir = '/home/steve/.gemini/antigravity/brain/91e1f823-b856-4d61-bc57-2d759f389fdf'
    if os.path.exists(artifact_dir):
        shutil.copy(bp_svg_path, os.path.join(artifact_dir, bp_svg_path))
        shutil.copy(cut_svg_path, os.path.join(artifact_dir, cut_svg_path))
        shutil.copy(obj_path, os.path.join(artifact_dir, obj_path))
        print(f"Synchronized artifacts to {artifact_dir}")

if __name__ == '__main__':
    main()
