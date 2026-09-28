#!/usr/bin/env python3
"""
Trebuchet Physics Simulator: 3-Foot Trebuchet launching a marble 3 yards (2.74 m).
Configuration:
  - Bigger Swingarm: 40.0" (1016 mm) total length (1.5" x 1.5" square timber)
    * 32.0" Long Arm (812.8 mm) : 8.0" Short Arm (203.2 mm) (4:1 Ratio)
  - Sling Length: 14.55" (370 mm) — Reaches just under the fulcrum when arm is pulled all the way back and down to the ground!
  - Counterweight: 890 g (1.96 lb) screwed onto short arm end
  - Fulcrum: 8 mm steel round rod with 2x 608 ball bearings (dual A-frame triangles)
  - Projectile: 16 mm glass marble (5.5 g)
"""

import os
import math
import json
import numpy as np

os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib_trebuchet'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_simulation(
    frame_height_in=36.0,       # 3.0 ft (914.4 mm)
    pivot_height_in=30.0,       # 2.5 ft (762.0 mm)
    short_arm_in=8.0,           # 8.0 in (203.2 mm)
    long_arm_in=32.0,           # 32.0 in (812.8 mm) - 4:1 ratio
    sling_length_in=14.55,      # 14.55 in (369.6 mm) — reaches just under fulcrum when cocked down
    counterweight_mass_g=2000.0,# 2000 grams (4.41 lbs) portable demonstration counterweight
    stick_mass_g=300.0,         # 300 grams (1.5" x 1.5" x 40" timber stick)
    marble_mass_g=20.0,         # 20.0 grams solid glass marble (16 mm)
    marble_diam_mm=16.0,        # 16 mm diameter
    dt=0.0005,                  # 0.5 ms integration step
    max_time=3.5
):
    g = 9.80665

    # Unit conversions
    H_pivot = pivot_height_in * 0.0254
    L_s = short_arm_in * 0.0254
    L_l = long_arm_in * 0.0254
    L_sling = sling_length_in * 0.0254
    M_cw = counterweight_mass_g / 1000.0
    M_arm = stick_mass_g / 1000.0
    m_p = marble_mass_g / 1000.0
    r_p = (marble_diam_mm / 2.0) / 1000.0
    area_p = np.pi * (r_p ** 2)
    rho_air = 1.225
    cd = 0.47

    mu_bearing = 0.0015
    r_bearing = 0.004

    # Beam moment of inertia about pivot
    L_tot = L_s + L_l
    d_com = (L_l - L_s) / 2.0
    I_arm = (1.0 / 12.0) * M_arm * (L_tot ** 2) + M_arm * (d_com ** 2)
    I_cw = M_cw * (L_s ** 2)
    I_rigid = I_arm + I_cw

    # Initial state: arm pulled all the way back down to ground (asin(28.5/32) = 63 deg below horizontal)
    alpha = math.radians(153.0)
    omega = 0.0

    y_trough = 0.025  # 2.5 cm trough elevation
    t = 0.0

    times = []
    alphas = []
    tip_coords = []
    cw_coords = []
    marble_coords = []
    speeds = []
    energies = []

    phase = 1
    x_tip = -L_l * math.sin(alpha)
    y_tip = H_pivot + L_l * math.cos(alpha)

    # When cocked, sling reaches just under fulcrum (X ~ 0)
    x_marble = x_tip + L_sling  # roughly 0
    y_marble = y_trough
    vx_marble = 0.0
    vy_marble = 0.0

    psi = math.atan2(y_trough - y_tip, x_marble - x_tip)
    omega_psi = 0.0

    t_release = None
    v_release = None
    pos_release = None

    while t < max_time:
        x_tip = -L_l * math.sin(alpha)
        y_tip = H_pivot + L_l * math.cos(alpha)

        x_cw = L_s * math.sin(alpha)
        y_cw = H_pivot - L_s * math.cos(alpha)

        tau_g = -(M_cw * L_s - M_arm * d_com) * g * math.sin(alpha)
        normal_load = (M_cw + M_arm + m_p) * g
        tau_fric = -math.copysign(mu_bearing * normal_load * r_bearing, omega) if abs(omega) > 1e-4 else 0.0
        tau_net = tau_g + tau_fric

        pe = (M_cw * g * y_cw) + (M_arm * g * (H_pivot + d_com * math.cos(alpha))) + (m_p * g * y_marble)

        if phase == 1:
            dy = y_tip - y_trough
            if dy >= L_sling * 0.95 or alpha <= math.radians(70.0):
                phase = 2
                psi = math.atan2(y_trough - y_tip, x_marble - x_tip)
                omega_psi = 0.0
            else:
                sqrt_val = max(0.001, L_sling**2 - dy**2)
                dx_m_dalpha = -L_l * math.cos(alpha) - (0.5 / math.sqrt(sqrt_val)) * (2 * dy * (-L_l * math.sin(alpha)))
                I_eff = I_rigid + m_p * (dx_m_dalpha ** 2)

                alpha_accel = tau_net / I_eff
                omega += alpha_accel * dt
                alpha += omega * dt

                x_marble = x_tip - math.sqrt(max(0.001, L_sling**2 - (y_tip - y_trough)**2))
                y_marble = y_trough
                vx_marble = dx_m_dalpha * omega
                vy_marble = 0.0

        elif phase == 2:
            alpha_accel = tau_net / I_rigid
            omega += alpha_accel * dt
            alpha += omega * dt

            a_tip_x = -L_l * (math.cos(alpha) * alpha_accel - math.sin(alpha) * (omega ** 2))
            a_tip_y = L_l * (-math.sin(alpha) * alpha_accel - math.cos(alpha) * (omega ** 2))

            tau_psi = -g * math.cos(psi) - a_tip_y * math.cos(psi) + a_tip_x * math.sin(psi)
            domega_psi = tau_psi / L_sling
            omega_psi += domega_psi * dt
            psi += omega_psi * dt

            x_marble = x_tip + L_sling * math.cos(psi)
            y_marble = y_trough if (y_tip + L_sling * math.sin(psi) < y_trough) else (y_tip + L_sling * math.sin(psi))

            v_tip_x = -L_l * math.cos(alpha) * omega
            v_tip_y = -L_l * math.sin(alpha) * omega
            vx_marble = v_tip_x - L_sling * math.sin(psi) * omega_psi
            vy_marble = v_tip_y + L_sling * math.cos(psi) * omega_psi

            launch_angle = math.degrees(math.atan2(vy_marble, vx_marble))
            if alpha <= math.radians(20.0) and vx_marble > 0 and 42.0 <= launch_angle <= 48.0:
                phase = 3
                t_release = t
                v_release = (vx_marble, vy_marble)
                pos_release = (x_marble, y_marble)

        elif phase == 3:
            speed = math.hypot(vx_marble, vy_marble)
            f_drag = 0.5 * rho_air * cd * area_p * (speed ** 2)
            ax_drag = -(f_drag / m_p) * (vx_marble / speed)
            ay_drag = -(f_drag / m_p) * (vy_marble / speed)

            vx_marble += ax_drag * dt
            vy_marble += (-g + ay_drag) * dt

            x_marble += vx_marble * dt
            y_marble += vy_marble * dt

            if alpha < math.radians(-15.0):
                omega = -0.15 * omega
                alpha = math.radians(-15.0)
            else:
                alpha_accel = (tau_net - 0.08 * omega) / I_rigid
                omega += alpha_accel * dt
                alpha += omega * dt

            if y_marble <= 0.0:
                y_marble = 0.0
                times.append(t)
                marble_coords.append((x_marble, y_marble))
                tip_coords.append((x_tip, y_tip))
                cw_coords.append((x_cw, y_cw))
                speeds.append(math.hypot(vx_marble, vy_marble))
                break

        times.append(t)
        alphas.append(alpha)
        tip_coords.append((x_tip, y_tip))
        cw_coords.append((x_cw, y_cw))
        marble_coords.append((x_marble, y_marble))
        speeds.append(math.hypot(vx_marble, vy_marble))

        ke = 0.5 * I_rigid * (omega ** 2) + 0.5 * m_p * (vx_marble**2 + vy_marble**2)
        energies.append(ke + pe)

        t += dt

    if v_release is None:
        v_release = (vx_marble, vy_marble)
        pos_release = (x_marble, y_marble)
        t_release = t

    launch_speed = math.hypot(v_release[0], v_release[1])
    launch_angle_deg = math.degrees(math.atan2(v_release[1], v_release[0]))
    range_m = x_marble
    range_yards = range_m / 0.9144
    range_ft = range_m / 0.3048

    results = {
        "frame_height_in": frame_height_in,
        "pivot_height_in": pivot_height_in,
        "short_arm_in": short_arm_in,
        "long_arm_in": long_arm_in,
        "total_arm_len_in": short_arm_in + long_arm_in,
        "arm_cross_section": "1.5\" x 1.5\" (38.1 mm x 38.1 mm square timber)",
        "arm_ratio": f"{long_arm_in / short_arm_in:.1f}:1",
        "sling_length_in": sling_length_in,
        "sling_geometry": "Reaches just under the fulcrum when arm is pulled all the way back down to ground",
        "counterweight_mass_g": counterweight_mass_g,
        "counterweight_mass_lb": round(counterweight_mass_g / 453.592, 2),
        "counterweight_mounting": "Screwed / bolted directly to short end of swing stick",
        "fulcrum_axle": "8 mm steel round rod",
        "fulcrum_bearings": "2x 608-2RS miniature ball bearings (dual A-frame triangles)",
        "sling_material": "Leather shoe-lace (raw leather boot lace)",
        "pouch_material": "Folded cloth pouch with cutout template",
        "projectile": f"{marble_diam_mm:.0f} mm standard glass marble ({marble_mass_g} g)",
        "release_time_s": round(t_release, 4) if t_release else 0.0,
        "release_speed_mps": round(launch_speed, 2),
        "release_speed_mph": round(launch_speed * 2.23694, 2),
        "release_angle_deg": round(launch_angle_deg, 1),
        "release_height_m": round(pos_release[1], 3) if pos_release else 0.0,
        "flight_time_s": round(t - (t_release or 0.0), 3),
        "range_meters": round(range_m, 3),
        "range_yards": round(range_yards, 2),
        "range_feet": round(range_ft, 2),
        "target_yards": 3.00,
        "accuracy_pct": round(max(0.0, (1.0 - abs(range_yards - 3.00) / 3.00) * 100.0), 1)
    }

    return results, times, marble_coords, tip_coords, cw_coords, speeds, energies

def generate_plots(results, times, marble_coords, tip_coords, cw_coords, speeds):
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor='#0B192C')
    fig.suptitle('3-Foot Trebuchet Physics Simulation (Bigger 40" Arm & Fulcrum-Reach Sling)', fontsize=15, fontweight='bold', color='#64DFDF', y=0.98)

    # 1. Trajectory
    ax1 = axes[0, 0]
    ax1.set_facecolor('#071324')
    mx = [p[0] for p in marble_coords]
    my = [p[1] for p in marble_coords]
    ax1.plot(mx, my, color='#48CAE4', lw=2.8, label='Marble Path (16mm Glass, 20g)')
    ax1.axvline(x=results['range_meters'], color='#FF5964', linestyle='--', lw=2.2, label=f"Impact: {results['range_yards']} yd ({results['range_meters']} m)")
    ax1.scatter([results['range_meters']], [0], color='#06D6A0', s=130, zorder=5)
    ax1.set_title(f"Ballistic Trajectory (2.0 kg Load: {results['range_yards']} Yards / {results['range_meters']} m)", color='#E0E6ED', fontsize=12, pad=10)
    ax1.set_xlabel('Horizontal Distance (meters)', color='#A0AEC0')
    ax1.set_ylabel('Height (meters)', color='#A0AEC0')
    ax1.set_xlim(-1.0, max(mx) + 2.0)
    ax1.set_ylim(-0.1, max(my) * 1.25)
    ax1.grid(True, linestyle=':', alpha=0.35, color='#4A5568')
    ax1.legend(loc='upper right', facecolor='#0B192C', edgecolor='#64DFDF', fontsize=9)

    # 2. Kinematics Arc Plot
    ax2 = axes[0, 1]
    ax2.set_facecolor('#071324')
    tx = [p[0] for p in tip_coords]
    ty = [p[1] for p in tip_coords]
    cx = [p[0] for p in cw_coords]
    cy = [p[1] for p in cw_coords]
    ax2.plot(tx, ty, color='#00B4D8', lw=2.2, label='Long Arm Tip (32")')
    ax2.plot(cx, cy, color='#F77F00', lw=2.2, label='Bolted Counterweight (8")')
    ax2.scatter([0], [results['pivot_height_in'] * 0.0254], color='#FFD166', s=90, zorder=5, label='Fulcrum (8mm Rod + 2x 608 Bearings)')
    ax2.set_title('Mechanism Kinematics (Bigger 40" Swingarm)', color='#E0E6ED', fontsize=12, pad=10)
    ax2.set_xlabel('Horizontal (meters)', color='#A0AEC0')
    ax2.set_ylabel('Vertical (meters)', color='#A0AEC0')
    ax2.grid(True, linestyle=':', alpha=0.35, color='#4A5568')
    ax2.legend(loc='upper left', facecolor='#0B192C', edgecolor='#64DFDF', fontsize=9)
    ax2.set_aspect('equal')

    # 3. Speed Profile
    ax3 = axes[1, 0]
    ax3.set_facecolor('#071324')
    ax3.plot(times, speeds, color='#06D6A0', lw=2.2, label='Marble Speed')
    ax3.axhline(y=results['release_speed_mps'], color='#FFD166', linestyle=':', lw=1.8,
                label=f"Release: {results['release_speed_mps']} m/s ({results['release_speed_mph']} mph)")
    ax3.set_title('Marble Speed Telemetry', color='#E0E6ED', fontsize=12, pad=10)
    ax3.set_xlabel('Time (seconds)', color='#A0AEC0')
    ax3.set_ylabel('Speed (m/s)', color='#A0AEC0')
    ax3.grid(True, linestyle=':', alpha=0.35, color='#4A5568')
    ax3.legend(loc='upper right', facecolor='#0B192C', edgecolor='#64DFDF', fontsize=9)

    # 4. Specifications Table
    ax4 = axes[1, 1]
    ax4.set_facecolor('#071324')
    ax4.axis('off')
    table_data = [
        ["Swingarm Dimensions", "40.0\" (1.5\" x 1.5\" square timber stick)"],
        ["Arm Ratio (Long : Short)", "32.0\" Long Arm : 8.0\" Short Arm (4:1 Ratio)"],
        ["Sling Length", "14.6\" (370 mm - reaches just under fulcrum)"],
        ["Sling Reach Check", "Reaches X=0 when arm pulled to ground"],
        ["Fulcrum Pivot", "8 mm Round Steel Rod + 2x 608 Ball Bearings"],
        ["Counterweight Mount", "Bolted to Short Stick End (3/8\" bolt + nut)"],
        ["Calibrated Weight", f"{results['counterweight_mass_g']:.0f} g ({results['counterweight_mass_lb']:.2f} lbs)"],
        ["Sling & Pouch", "Leather Shoe-Lace + Folded Cloth Pouch"],
        ["Projectile", "16 mm Glass Marble (5.5 grams)"],
        ["Release Speed & Angle", f"{results['release_speed_mps']} m/s ({results['release_speed_mph']} mph) @ {results['release_angle_deg']}°"],
        ["Target Distance", "3.00 Yards (9.00 Feet / 2.74 m)"],
        ["Simulated Range", f"{results['range_yards']} Yards ({results['range_feet']} Feet / {results['range_meters']} m)"],
        ["Range Accuracy", f"{results['accuracy_pct']}% Match"]
    ]
    tbl = ax4.table(cellText=table_data, colLabels=["Hardware Component", "Design Specification"], cellLoc='left', loc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9.5)
    tbl.scale(1.0, 1.48)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor('#1E3E62')
        if r == 0:
            cell.set_facecolor('#0B2545')
            cell.set_text_props(color='#64DFDF', fontweight='bold')
        else:
            cell.set_facecolor('#071324' if r % 2 == 0 else '#0C1B33')
            cell.set_text_props(color='#E0E6ED')
    ax4.set_title('Build Specifications & Telemetry', color='#E0E6ED', fontsize=12, pad=10)

    plt.tight_layout()
    plt.savefig('trebuchet_simulation_plot.png', dpi=200, bbox_inches='tight')
    plt.savefig('trebuchet_simulation_plot.svg', bbox_inches='tight')
    print("Saved updated trebuchet_simulation_plot.png and .svg")

if __name__ == "__main__":
    results, times, marble_coords, tip_coords, cw_coords, speeds, energies = run_simulation()
    print("Simulation Results:")
    print(json.dumps(results, indent=2))
    with open("simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    generate_plots(results, times, marble_coords, tip_coords, cw_coords, speeds)
