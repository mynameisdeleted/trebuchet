import math
import mathutils

def generate_slack_sling_path(p_start, p_end, num_segments, slack_m=0.025, n_waves=2):
    # p_start: Arm tip or loop (X ~ -0.3922)
    # p_end: Pouch (X ~ -0.0350)
    # Direct vector
    span_vec = p_end - p_start
    span_len = span_vec.length
    target_len = span_len + slack_m
    
    # We want a curve r(t) for t in [0, 1] such that arc length is target_len
    # Transverse direction in Y:
    # Let y(t) = A * sin(n_waves * pi * t)
    # Let's find A by bisection
    A_low = 0.0
    A_high = 0.025 # max 25mm to stay inside trough
    
    dt = 1.0 / 200.0
    best_A = 0.015
    for _ in range(20):
        A_mid = 0.5 * (A_low + A_high)
        # compute arc length
        length = 0.0
        for step in range(200):
            t0 = step * dt
            t1 = (step + 1) * dt
            
            p0 = p_start + t0 * span_vec + mathutils.Vector((0.0, A_mid * math.sin(n_waves * math.pi * t0), 0.0))
            p1 = p_start + t1 * span_vec + mathutils.Vector((0.0, A_mid * math.sin(n_waves * math.pi * t1), 0.0))
            length += (p1 - p0).length
            
        if length < target_len:
            A_low = A_mid
        else:
            A_high = A_mid
        best_A = A_mid
        
    # Now generate points along the curve spaced equally by arc length
    # Arc length per segment: seg_len = target_len / num_segments
    seg_len = target_len / num_segments
    
    # Sample dense points along curve
    dense_pts = []
    dense_dists = [0.0]
    total_dist = 0.0
    N_dense = 1000
    for s in range(N_dense + 1):
        t = s / N_dense
        # Droop in Z into trough floor
        # p_start.z = 0.0627, p_end.z = 0.0593, trough floor = 0.0508
        z_droop = -0.008 * math.sin(math.pi * t)
        pt = p_start + t * span_vec + mathutils.Vector((0.0, best_A * math.sin(n_waves * math.pi * t), z_droop))
        dense_pts.append(pt)
        if s > 0:
            total_dist += (dense_pts[-1] - dense_pts[-2]).length
            dense_dists.append(total_dist)
            
    # Sample num_segments + 1 joint locations along equal arc lengths
    joint_locs = [p_start.copy()]
    target_dists = [i * (total_dist / num_segments) for i in range(num_segments + 1)]
    
    dense_idx = 0
    for i in range(1, num_segments):
        td = target_dists[i]
        while dense_idx < len(dense_dists) - 1 and dense_dists[dense_idx + 1] < td:
            dense_idx += 1
        # Linear interpolate between dense_idx and dense_idx + 1
        d0 = dense_dists[dense_idx]
        d1 = dense_dists[dense_idx + 1]
        frac = (td - d0) / max(1e-6, (d1 - d0))
        pt = dense_pts[dense_idx].lerp(dense_pts[dense_idx + 1], frac)
        joint_locs.append(pt)
    joint_locs.append(p_end.copy())
    
    # Midpoints and orientations for segments
    seg_centers = []
    seg_rotations = []
    for i in range(num_segments):
        j0 = joint_locs[i]
        j1 = joint_locs[i + 1]
        mid = 0.5 * (j0 + j1)
        seg_centers.append(mid)
        
        # Segment orientation: cylinder default along local Z
        v_seg = (j1 - j0).normalized()
        q = mathutils.Vector((0, 0, 1)).rotation_difference(v_seg)
        seg_rotations.append(q.to_euler())
        
    return {
        'target_len': total_dist,
        'seg_len': total_dist / num_segments,
        'joint_locs': joint_locs,
        'seg_centers': seg_centers,
        'seg_rotations': seg_rotations,
        'amplitude': best_A
    }

if __name__ == '__main__':
    p0 = mathutils.Vector((-0.3922, -0.008, 0.0627))
    p1 = mathutils.Vector((-0.0350, -0.008, 0.0593))
    res = generate_slack_sling_path(p0, p1, 16, slack_m=0.020, n_waves=2)
    print(f"Generated path: len={res['target_len']*1000:.1f}mm, seg_len={res['seg_len']*1000:.1f}mm, A={res['amplitude']*1000:.1f}mm")
    print(f"Num joints: {len(res['joint_locs'])}, Num segs: {len(res['seg_centers'])}")
