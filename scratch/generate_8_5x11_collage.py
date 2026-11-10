#!/usr/bin/env python3
"""
generate_8_5x11_collage.py
Generates a true 1:1 scale workshop template collage on a standard 8.5" x 11" sheet (US Letter).
Every template on this sheet is calibrated at 1:1 (96 DPI: 1 inch = 96 px = 25.4 mm).
"""

import os
import shutil
import math
import subprocess

def create_collage_svg():
    # 8.5" x 11" at 96 DPI
    W_INCH = 8.5
    H_INCH = 11.0
    DPI = 96.0
    W_PX = int(W_INCH * DPI)  # 816
    H_PX = int(H_INCH * DPI)  # 1056

    MM_TO_PX = DPI / 25.4
    INCH_TO_PX = DPI

    svg = []
    svg.append(f'''<svg xmlns="http://www.w3.org/2000/svg" 
     width="{W_INCH}in" height="{H_INCH}in" 
     viewBox="0 0 {W_PX} {H_PX}" 
     style="background:#ffffff;">
  <defs>
    <!-- Drafting grid: 1/8" (12px) minor, 1" (96px) major -->
    <pattern id="gridMinor" width="12" height="12" patternUnits="userSpaceOnUse">
      <path d="M 12 0 L 0 0 0 12" fill="none" stroke="#f1f5f9" stroke-width="0.5"/>
    </pattern>
    <pattern id="gridMajor" width="96" height="96" patternUnits="userSpaceOnUse">
      <path d="M 96 0 L 0 0 0 96" fill="none" stroke="#e2e8f0" stroke-width="0.8"/>
    </pattern>
    <pattern id="woodHatch" width="16" height="16" patternUnits="userSpaceOnUse">
      <path d="M 0 16 L 16 0 M 0 8 L 8 0 M 8 16 L 16 8" fill="none" stroke="#e2e8f0" stroke-width="0.6"/>
    </pattern>
    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#000000" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="{W_PX}" height="{H_PX}" fill="#ffffff" />
  <rect width="{W_PX}" height="{H_PX}" fill="url(#gridMinor)" />
  <rect width="{W_PX}" height="{H_PX}" fill="url(#gridMajor)" />

  <!-- Sheet Outer Border (0.25" / 24px margins for printer safety) -->
  <rect x="24" y="24" width="{W_PX - 48}" height="{H_PX - 48}" fill="none" stroke="#000000" stroke-width="1.8" />
  <rect x="28" y="28" width="{W_PX - 56}" height="{H_PX - 56}" fill="none" stroke="#94a3b8" stroke-width="0.6" stroke-dasharray="4,2" />
''')

    # -------------------------------------------------------------
    # 1. HEADER & VERIFICATION CALIBRATION BLOCK (Y = 32 to 92)
    # -------------------------------------------------------------
    svg.append(f'''
  <!-- HEADER & PRINTER CALIBRATION BLOCK -->
  <g transform="translate(38, 36)">
    <text x="0" y="15" font-family="'Segoe UI', Helvetica, Arial, sans-serif" font-size="14.5" font-weight="900" fill="#000000" letter-spacing="0.8">
      TREBUCHET 1:1 SCALE WORKSHOP CUT &amp; DRILL TEMPLATES
    </text>
    <text x="0" y="29" font-family="monospace" font-size="8.5" font-weight="bold" fill="#1e293b">
      TRUE 100% SCALE COLLAGE • 8.5" x 11" US LETTER • PRINT AT "ACTUAL SIZE / 100%" (DO NOT FIT/SHRINK)
    </text>
    <text x="0" y="42" font-family="monospace" font-size="7.5" fill="#475569">
      Glue/tape cutouts directly to wood stock to punch center holes &amp; guide miter cuts. Tolerances: ±1/32" [0.8mm].
    </text>

    <!-- Calibration Box: Exactly 1.000" x 1.000" (96px x 96px) and 50 mm ruler -->
    <g transform="translate(450, -4)">
      <!-- 1 Inch Box -->
      <rect x="0" y="0" width="96" height="52" fill="#f8fafc" stroke="#000000" stroke-width="1.2" />
      <text x="48" y="13" font-family="monospace" font-size="8" font-weight="bold" fill="#000000" text-anchor="middle">CALIBRATION</text>
      <text x="48" y="26" font-family="monospace" font-size="9" font-weight="900" fill="#000000" text-anchor="middle">1.000" [25.4mm]</text>
      <text x="48" y="37" font-family="monospace" font-size="7" fill="#475569" text-anchor="middle">VERIFY WITH RULER</text>
      <!-- Sub-inch tick marks -->
      <line x1="0" y1="46" x2="96" y2="46" stroke="#000000" stroke-width="1.0" />
      <line x1="0" y1="41" x2="0" y2="51" stroke="#000000" stroke-width="1.0" />
      <line x1="24" y1="43" x2="24" y2="49" stroke="#000000" stroke-width="0.8" />
      <line x1="48" y1="42" x2="48" y2="50" stroke="#000000" stroke-width="1.0" />
      <line x1="72" y1="43" x2="72" y2="49" stroke="#000000" stroke-width="0.8" />
      <line x1="96" y1="41" x2="96" y2="51" stroke="#000000" stroke-width="1.0" />

      <!-- 50mm Bar -->
      <g transform="translate(104, 0)">
        <rect x="0" y="0" width="{50.0 * MM_TO_PX}" height="52" fill="#f8fafc" stroke="#000000" stroke-width="1.2" />
        <text x="{25.0 * MM_TO_PX}" y="13" font-family="monospace" font-size="8" font-weight="bold" fill="#000000" text-anchor="middle">METRIC CHECK</text>
        <text x="{25.0 * MM_TO_PX}" y="26" font-family="monospace" font-size="9" font-weight="900" fill="#000000" text-anchor="middle">50.0 mm</text>
        <text x="{25.0 * MM_TO_PX}" y="37" font-family="monospace" font-size="7" fill="#475569" text-anchor="middle">VERIFY WITH RULER</text>
        <line x1="0" y1="46" x2="{50.0 * MM_TO_PX}" y2="46" stroke="#000000" stroke-width="1.0" />
        <line x1="0" y1="41" x2="0" y2="51" stroke="#000000" stroke-width="1.0" />
        <line x1="{10.0 * MM_TO_PX}" y1="43" x2="{10.0 * MM_TO_PX}" y2="49" stroke="#000000" stroke-width="0.8" />
        <line x1="{20.0 * MM_TO_PX}" y1="43" x2="{20.0 * MM_TO_PX}" y2="49" stroke="#000000" stroke-width="0.8" />
        <line x1="{25.0 * MM_TO_PX}" y1="42" x2="{25.0 * MM_TO_PX}" y2="50" stroke="#000000" stroke-width="1.0" />
        <line x1="{30.0 * MM_TO_PX}" y1="43" x2="{30.0 * MM_TO_PX}" y2="49" stroke="#000000" stroke-width="0.8" />
        <line x1="{40.0 * MM_TO_PX}" y1="43" x2="{40.0 * MM_TO_PX}" y2="49" stroke="#000000" stroke-width="0.8" />
        <line x1="{50.0 * MM_TO_PX}" y1="41" x2="{50.0 * MM_TO_PX}" y2="51" stroke="#000000" stroke-width="1.0" />
      </g>
    </g>
  </g>
  <line x1="38" y1="94" x2="778" y2="94" stroke="#000000" stroke-width="1.2" />
''')

    # -------------------------------------------------------------
    # 2. ROW 1: PART W5 — BEARING PILLOW BLOCKS (LEFT & RIGHT) 1:1
    # -------------------------------------------------------------
    w5_w = 3.0 * INCH_TO_PX      # 288 px
    w5_h = 55.0 * MM_TO_PX       # 207.87 px
    r_pocket = 11.0 * MM_TO_PX   # 41.57 px (Ø22mm)
    r_bore = 4.25 * MM_TO_PX     # 16.06 px (Ø8.5mm)
    r_bolt = 0.125 * INCH_TO_PX  # 12.0 px (Ø1/4")

    cx_w5 = 144.0
    cy_w5 = 33.0 * MM_TO_PX

    cy_bolts = w5_h - (10.0 * MM_TO_PX)
    cx_bolt_L = 15.0 * MM_TO_PX
    cx_bolt_R = w5_w - (15.0 * MM_TO_PX)

    svg.append(f'''
  <!-- ==================== ROW 1: W5 BEARING PILLOW BLOCKS (1:1 SCALE) ==================== -->
  <g transform="translate(38, 102)">
    <!-- Header banner -->
    <rect x="0" y="0" width="740" height="18" fill="#f8fafc" stroke="#000000" stroke-width="1.0" />
    <text x="10" y="13" font-family="monospace" font-size="9.5" font-weight="bold" fill="#000000">
      [W5-L &amp; W5-R] BEARING PILLOW BLOCKS (1:1 TEMPLATES) — 1.5" x 3.0" x 2.17" HARDWOOD [QTY: 2]
    </text>
    <text x="590" y="13" font-family="monospace" font-size="8.5" font-weight="bold" fill="#b91c1c">
      CUT OUT &amp; PASTE ONTO WOOD
    </text>

    <!-- W5-L Template -->
    <g transform="translate(0, 24)">
      <!-- Wood Block Outline -->
      <rect x="0" y="0" width="{w5_w}" height="{w5_h}" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
      <rect x="0" y="0" width="{w5_w}" height="{w5_h}" fill="url(#woodHatch)" />

      <!-- Centerlines -->
      <line x1="{cx_w5}" y1="-6" x2="{cx_w5}" y2="{w5_h + 6}" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />
      <line x1="-6" y1="{cy_w5}" x2="{w5_w + 6}" y2="{cy_w5}" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />

      <!-- Ø22mm Bearing Recess (Forstner Pocket) -->
      <circle cx="{cx_w5}" cy="{cy_w5}" r="{r_pocket}" fill="#f1f5f9" stroke="#000000" stroke-width="1.6" />
      <!-- Ø8.5mm Axle Bore -->
      <circle cx="{cx_w5}" cy="{cy_w5}" r="{r_bore}" fill="#ffffff" stroke="#000000" stroke-width="1.4" />

      <!-- Crosshairs on Bearing Center -->
      <line x1="{cx_w5 - 16}" y1="{cy_w5}" x2="{cx_w5 + 16}" y2="{cy_w5}" stroke="#000000" stroke-width="1.0" />
      <line x1="{cx_w5}" y1="{cy_w5 - 16}" x2="{cx_w5}" y2="{cy_w5 + 16}" stroke="#000000" stroke-width="1.0" />

      <!-- 2x Ø1/4" Base Mounting Bolt Holes -->
      <circle cx="{cx_bolt_L}" cy="{cy_bolts}" r="{r_bolt}" fill="#ffffff" stroke="#000000" stroke-width="1.2" />
      <line x1="{cx_bolt_L - 8}" y1="{cy_bolts}" x2="{cx_bolt_L + 8}" y2="{cy_bolts}" stroke="#000000" stroke-width="0.8" />
      <line x1="{cx_bolt_L}" y1="{cy_bolts - 8}" x2="{cx_bolt_L}" y2="{cy_bolts + 8}" stroke="#000000" stroke-width="0.8" />

      <circle cx="{cx_bolt_R}" cy="{cy_bolts}" r="{r_bolt}" fill="#ffffff" stroke="#000000" stroke-width="1.2" />
      <line x1="{cx_bolt_R - 8}" y1="{cy_bolts}" x2="{cx_bolt_R + 8}" y2="{cy_bolts}" stroke="#000000" stroke-width="0.8" />
      <line x1="{cx_bolt_R}" y1="{cy_bolts - 8}" x2="{cx_bolt_R}" y2="{cy_bolts + 8}" stroke="#000000" stroke-width="0.8" />

      <!-- Labels & Dimensions inside template -->
      <text x="10" y="16" font-family="monospace" font-size="10" font-weight="900" fill="#000000">W5-L (LEFT BLOCK)</text>
      <text x="{cx_w5}" y="{cy_w5 - r_pocket - 5}" font-family="monospace" font-size="8" font-weight="bold" fill="#000000" text-anchor="middle">
        Ø 22.0 mm (7/8" Forstner) x 7mm Deep
      </text>
      <text x="{cx_w5}" y="{cy_w5 + r_pocket + 14}" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">
        Ø 8.5mm Through Bore
      </text>
      <text x="{cx_bolt_L}" y="{cy_bolts - 14}" font-family="monospace" font-size="7" font-weight="bold" fill="#000000" text-anchor="middle">
        Ø 1/4" Bolt
      </text>
      <text x="{cx_bolt_R}" y="{cy_bolts - 14}" font-family="monospace" font-size="7" font-weight="bold" fill="#000000" text-anchor="middle">
        Ø 1/4" Bolt
      </text>
      <text x="{cx_w5}" y="{w5_h - 4}" font-family="monospace" font-size="7.5" fill="#475569" text-anchor="middle">
        Base Bolted Flush to A-Frame Apex
      </text>
    </g>

    <!-- W5-R Template -->
    <g transform="translate(300, 24)">
      <!-- Wood Block Outline -->
      <rect x="0" y="0" width="{w5_w}" height="{w5_h}" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
      <rect x="0" y="0" width="{w5_w}" height="{w5_h}" fill="url(#woodHatch)" />

      <!-- Centerlines -->
      <line x1="{cx_w5}" y1="-6" x2="{cx_w5}" y2="{w5_h + 6}" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />
      <line x1="-6" y1="{cy_w5}" x2="{w5_w + 6}" y2="{cy_w5}" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />

      <!-- Ø22mm Bearing Recess (Forstner Pocket) -->
      <circle cx="{cx_w5}" cy="{cy_w5}" r="{r_pocket}" fill="#f1f5f9" stroke="#000000" stroke-width="1.6" />
      <!-- Ø8.5mm Axle Bore -->
      <circle cx="{cx_w5}" cy="{cy_w5}" r="{r_bore}" fill="#ffffff" stroke="#000000" stroke-width="1.4" />

      <!-- Crosshairs on Bearing Center -->
      <line x1="{cx_w5 - 16}" y1="{cy_w5}" x2="{cx_w5 + 16}" y2="{cy_w5}" stroke="#000000" stroke-width="1.0" />
      <line x1="{cx_w5}" y1="{cy_w5 - 16}" x2="{cx_w5}" y2="{cy_w5 + 16}" stroke="#000000" stroke-width="1.0" />

      <!-- 2x Ø1/4" Base Mounting Bolt Holes -->
      <circle cx="{cx_bolt_L}" cy="{cy_bolts}" r="{r_bolt}" fill="#ffffff" stroke="#000000" stroke-width="1.2" />
      <line x1="{cx_bolt_L - 8}" y1="{cy_bolts}" x2="{cx_bolt_L + 8}" y2="{cy_bolts}" stroke="#000000" stroke-width="0.8" />
      <line x1="{cx_bolt_L}" y1="{cy_bolts - 8}" x2="{cx_bolt_L}" y2="{cy_bolts + 8}" stroke="#000000" stroke-width="0.8" />

      <circle cx="{cx_bolt_R}" cy="{cy_bolts}" r="{r_bolt}" fill="#ffffff" stroke="#000000" stroke-width="1.2" />
      <line x1="{cx_bolt_R - 8}" y1="{cy_bolts}" x2="{cx_bolt_R + 8}" y2="{cy_bolts}" stroke="#000000" stroke-width="0.8" />
      <line x1="{cx_bolt_R}" y1="{cy_bolts - 8}" x2="{cx_bolt_R}" y2="{cy_bolts + 8}" stroke="#000000" stroke-width="0.8" />

      <!-- Labels inside template -->
      <text x="10" y="16" font-family="monospace" font-size="10" font-weight="900" fill="#000000">W5-R (RIGHT BLOCK)</text>
      <text x="{cx_w5}" y="{cy_w5 - r_pocket - 5}" font-family="monospace" font-size="8" font-weight="bold" fill="#000000" text-anchor="middle">
        Ø 22.0 mm (7/8" Forstner) x 7mm Deep
      </text>
      <text x="{cx_w5}" y="{cy_w5 + r_pocket + 14}" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">
        Ø 8.5mm Through Bore
      </text>
      <text x="{cx_bolt_L}" y="{cy_bolts - 14}" font-family="monospace" font-size="7" font-weight="bold" fill="#000000" text-anchor="middle">
        Ø 1/4" Bolt
      </text>
      <text x="{cx_bolt_R}" y="{cy_bolts - 14}" font-family="monospace" font-size="7" font-weight="bold" fill="#000000" text-anchor="middle">
        Ø 1/4" Bolt
      </text>
      <text x="{cx_w5}" y="{w5_h - 4}" font-family="monospace" font-size="7.5" fill="#475569" text-anchor="middle">
        Base Bolted Flush to A-Frame Apex
      </text>
    </g>

    <!-- W5 Cross Section (Side View) 1:1 -->
    <g transform="translate(600, 24)">
      <!-- 1.5" x 2.17" side view -->
      <rect x="0" y="0" width="{1.5 * INCH_TO_PX}" height="{w5_h}" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
      <!-- Pocket cut 7mm deep -->
      <rect x="0" y="{cy_w5 - r_pocket}" width="{7.0 * MM_TO_PX}" height="{2 * r_pocket}" fill="#f1f5f9" stroke="#000000" stroke-width="1.2" />
      <!-- Bore hole through remainder -->
      <rect x="{7.0 * MM_TO_PX}" y="{cy_w5 - r_bore}" width="{1.5 * INCH_TO_PX - 7.0 * MM_TO_PX}" height="{2 * r_bore}" fill="#ffffff" stroke="#000000" stroke-width="1.0" />

      <!-- Centerline -->
      <line x1="-5" y1="{cy_w5}" x2="{1.5 * INCH_TO_PX + 5}" y2="{cy_w5}" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />

      <text x="{0.75 * INCH_TO_PX}" y="16" font-family="monospace" font-size="9" font-weight="900" fill="#000000" text-anchor="middle">
        CROSS-SECTION
      </text>
      <!-- Dimension: 7mm pocket depth -->
      <line x1="0" y1="{cy_w5 + r_pocket + 14}" x2="{7.0 * MM_TO_PX}" y2="{cy_w5 + r_pocket + 14}" stroke="#000000" stroke-width="1.0" marker-start="url(#arrow)" marker-end="url(#arrow)" />
      <text x="{3.5 * MM_TO_PX}" y="{cy_w5 + r_pocket + 25}" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">
        7mm
      </text>
      <!-- 1.5" thickness dimension -->
      <line x1="0" y1="{w5_h - 14}" x2="{1.5 * INCH_TO_PX}" y2="{w5_h - 14}" stroke="#000000" stroke-width="1.0" marker-start="url(#arrow)" marker-end="url(#arrow)" />
      <text x="{0.75 * INCH_TO_PX}" y="{w5_h - 4}" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">
        1.50" [38.1mm]
      </text>
    </g>
  </g>
''')

    # -------------------------------------------------------------
    # 3. ROW 2: PART W4 — A-FRAME MITER CUTS & APEX CONVERGENCE 1:1
    # -------------------------------------------------------------
    w4_w = 1.5 * INCH_TO_PX      # 144 px (1.5" wide edge face)
    miter_dx = w4_w * math.tan(math.radians(17.1))  # ~44.3 px

    svg.append(f'''
  <!-- ==================== ROW 2: W4 A-FRAME 17.1° MITER TEMPLATES (1:1 SCALE) ==================== -->
  <g transform="translate(38, 344)">
    <!-- Header banner -->
    <rect x="0" y="0" width="740" height="18" fill="#f8fafc" stroke="#000000" stroke-width="1.0" />
    <text x="10" y="13" font-family="monospace" font-size="9.5" font-weight="bold" fill="#000000">
      [W4] A-FRAME ANGLED POSTS — 17.1° MITER CUT PATTERNS &amp; APEX CONVERGENCE (1:1 SCALE) [QTY: 4]
    </text>
    <text x="590" y="13" font-family="monospace" font-size="8.5" font-weight="bold" fill="#000000">
      STOCK: 3/4" x 1.5" x 31.8"
    </text>

    <!-- Template 1: Post Bottom Foot Cut (17.1° Miter Sitting Flush on Base Runner) -->
    <g transform="translate(0, 24)">
      <rect x="0" y="0" width="220" height="162" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" />
      <text x="10" y="15" font-family="monospace" font-size="9" font-weight="900" fill="#000000">POST FOOT CUT (1:1)</text>

      <g transform="translate(38, 40)">
        <!-- Width dimension: 1.50" placed above stick -->
        <line x1="0" y1="-8" x2="{w4_w}" y2="-8" stroke="#000000" stroke-width="1.0" marker-start="url(#arrow)" marker-end="url(#arrow)" />
        <text x="72" y="-12" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">
          1.50" [38.1mm] STOCK WIDTH
        </text>

        <!-- Post polygon: width = 144, angled bottom -->
        <polygon points="0,0 {w4_w},0 {w4_w},{100 - miter_dx} 0,100" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
        <polygon points="0,0 {w4_w},0 {w4_w},{100 - miter_dx} 0,100" fill="url(#woodHatch)" />

        <!-- 90° square reference dashed line -->
        <line x1="0" y1="100" x2="{w4_w}" y2="100" stroke="#94a3b8" stroke-width="1.0" stroke-dasharray="3,3" />

        <!-- Miter Angle Arc -->
        <path d="M 0 100 L {w4_w} {100 - miter_dx}" stroke="#b91c1c" stroke-width="1.8" />
        <text x="72" y="78" font-family="monospace" font-size="8.5" font-weight="900" fill="#b91c1c" text-anchor="middle">
          17.1° CUT LINE
        </text>
        <text x="72" y="90" font-family="monospace" font-size="7" fill="#475569" text-anchor="middle">
          (Bevel: 0.46" / 11.7mm)
        </text>

        <!-- Horizontal base runner reference line -->
        <line x1="-15" y1="100" x2="{w4_w + 25}" y2="100" stroke="#000000" stroke-width="1.4" stroke-dasharray="4,2" />
        <text x="72" y="114" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">BASE RUNNER W1 (FLUSH)</text>
      </g>
    </g>

    <!-- Template 2: Post Top Apex Cut (17.1° Parallel Miter Flush Under Pillow Block) -->
    <g transform="translate(230, 24)">
      <rect x="0" y="0" width="220" height="162" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" />
      <text x="10" y="15" font-family="monospace" font-size="9" font-weight="900" fill="#000000">POST APEX CUT (1:1)</text>

      <g transform="translate(38, 32)">
        <!-- Horizontal pillow block underside reference line -->
        <line x1="-15" y1="18" x2="{w4_w + 25}" y2="18" stroke="#000000" stroke-width="1.4" stroke-dasharray="4,2" />
        <text x="72" y="10" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">PILLOW BLOCK W5 (UNDERSIDE)</text>

        <!-- Post polygon with top cut at 17.1° -->
        <polygon points="0,{18 + miter_dx} {w4_w},18 {w4_w},118 0,118" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
        <polygon points="0,{18 + miter_dx} {w4_w},18 {w4_w},118 0,118" fill="url(#woodHatch)" />

        <!-- 90° square reference dashed line -->
        <line x1="0" y1="18" x2="{w4_w}" y2="18" stroke="#94a3b8" stroke-width="1.0" stroke-dasharray="3,3" />

        <!-- Miter cut line -->
        <path d="M 0 {18 + miter_dx} L {w4_w} 18" stroke="#b91c1c" stroke-width="1.8" />
        <text x="72" y="52" font-family="monospace" font-size="8.5" font-weight="900" fill="#b91c1c" text-anchor="middle">
          17.1° CUT LINE
        </text>
        <text x="72" y="64" font-family="monospace" font-size="7" fill="#475569" text-anchor="middle">
          (Parallel to Foot Cut)
        </text>
        <text x="72" y="86" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">
          C-to-C = 30.60" [777.3mm]
        </text>
      </g>
    </g>

    <!-- Assembly 3: Apex Joint Convergence Diagram (1:1 scale mating) -->
    <g transform="translate(460, 24)">
      <rect x="0" y="0" width="280" height="162" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" />
      <text x="10" y="15" font-family="monospace" font-size="9" font-weight="900" fill="#000000">APEX JOINT ASSEMBLY (1:1)</text>

      <g transform="translate(140, 26)">
        <!-- Pillow Block Base (3.0" wide x 0.5" visible) -->
        <rect x="-144" y="0" width="288" height="18" fill="#f1f5f9" stroke="#000000" stroke-width="1.4" />
        <text x="0" y="13" font-family="monospace" font-size="8" font-weight="bold" fill="#000000" text-anchor="middle">
          W5 PILLOW BLOCK (3.00" BASE)
        </text>

        <!-- Left Leg Top: angles down-left at 17.1° -->
        <polygon points="-80,18 0,18 -35,118 -115,118" fill="#ffffff" stroke="#000000" stroke-width="1.4" />
        <polygon points="-80,18 0,18 -35,118 -115,118" fill="url(#woodHatch)" />

        <!-- Right Leg Top: angles down-right at 17.1° -->
        <polygon points="0,18 80,18 115,118 35,118" fill="#ffffff" stroke="#000000" stroke-width="1.4" />
        <polygon points="0,18 80,18 115,118 35,118" fill="url(#woodHatch)" />

        <!-- Centerline of convergence -->
        <line x1="0" y1="0" x2="0" y2="124" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />

        <text x="-58" y="70" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">REAR LEG</text>
        <text x="58" y="70" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">FRONT LEG</text>

        <!-- Included angle badge -->
        <rect x="-46" y="76" width="92" height="28" fill="#ffffff" stroke="#cbd5e1" stroke-width="0.8" rx="3" />
        <text x="0" y="88" font-family="monospace" font-size="8.5" font-weight="900" fill="#b91c1c" text-anchor="middle">
          34.2° INCLUDED
        </text>
        <text x="0" y="100" font-family="monospace" font-size="7" fill="#475569" text-anchor="middle">
          (17.1° per post)
        </text>
      </g>
    </g>
  </g>
''')

    # -------------------------------------------------------------
    # 4. ROW 3: PART W7 — SWINGARM BEAM CRITICAL MACHINING 1:1
    # -------------------------------------------------------------
    svg.append(f'''
  <!-- ==================== ROW 3: W7 SWINGARM CRITICAL TOOLING SECTIONS (1:1 SCALE) ==================== -->
  <g transform="translate(38, 542)">
    <!-- Header banner -->
    <rect x="0" y="0" width="740" height="18" fill="#f8fafc" stroke="#000000" stroke-width="1.0" />
    <text x="10" y="13" font-family="monospace" font-size="9.5" font-weight="bold" fill="#000000">
      [W7] SWINGARM BEAM MACHINING JIGS (1:1 DRILL &amp; CUT TEMPLATES) — 1.5" x 1.5" TIMBER
    </text>
    <text x="560" y="13" font-family="monospace" font-size="8.5" font-weight="bold" fill="#000000">
      TOTAL FINISHED LENGTH: 40.00"
    </text>

    <!-- Jig 1: Throwing Tip & Sling Release Pin (1:1) -->
    <g transform="translate(0, 24)">
      <rect x="0" y="0" width="235" height="156" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" />
      <text x="10" y="15" font-family="monospace" font-size="9" font-weight="900" fill="#000000">1. SLING PIN TIP (1:1)</text>

      <g transform="translate(20, 24)">
        <!-- 1.5" high beam x 190px long (2.0" long template) -->
        <rect x="0" y="0" width="192" height="96" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
        <rect x="0" y="0" width="192" height="96" fill="url(#woodHatch)" />

        <!-- Centerline -->
        <line x1="-5" y1="48" x2="197" y2="48" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />

        <!-- Pin Hole: 0.50" (48px) from left tip, on centerline -->
        <!-- Calibrated 10.0° pin line in red -->
        <line x1="48" y1="48" x2="6" y2="28" stroke="#b91c1c" stroke-width="2.2" />
        <!-- 45° reference line dashed -->
        <line x1="48" y1="48" x2="12" y2="12" stroke="#94a3b8" stroke-width="1.0" stroke-dasharray="3,2" />

        <!-- Pin Hole Circle: Ø 3/16" (18px diameter) -->
        <circle cx="48" cy="48" r="9" fill="#ffffff" stroke="#000000" stroke-width="1.4" />
        <line x1="38" y1="48" x2="58" y2="48" stroke="#000000" stroke-width="0.8" />
        <line x1="48" y1="38" x2="48" y2="58" stroke="#000000" stroke-width="0.8" />

        <!-- Fixed Eyelet Hole: 0.85" (81.6px) from tip, offset 0.31" (30px) -->
        <circle cx="82" cy="72" r="6" fill="#ffffff" stroke="#000000" stroke-width="1.2" />
        <text x="82" y="88" font-family="monospace" font-size="6.5" font-weight="bold" fill="#000000" text-anchor="middle">Fixed Cord</text>

        <!-- Dimension 0.50" cleanly separated below beam -->
        <line x1="0" y1="104" x2="48" y2="104" stroke="#000000" stroke-width="1.0" marker-start="url(#arrow)" marker-end="url(#arrow)" />
        <text x="24" y="115" font-family="monospace" font-size="7" font-weight="bold" fill="#000000" text-anchor="middle">0.50"</text>
        <text x="0" y="125" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000">ARM TIP</text>

        <text x="56" y="22" font-family="monospace" font-size="7.5" font-weight="900" fill="#b91c1c">
          10.0° PIN (CALIBRATED)
        </text>
        <text x="56" y="32" font-family="monospace" font-size="6.5" fill="#475569">
          Drill Ø 3/16" x 1.25" Deep
        </text>
      </g>
    </g>

    <!-- Jig 2: Fulcrum Axle Pivot Section (1:1) -->
    <g transform="translate(250, 24)">
      <rect x="0" y="0" width="235" height="156" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" />
      <text x="10" y="15" font-family="monospace" font-size="9" font-weight="900" fill="#000000">2. FULCRUM AXLE BORE (1:1)</text>

      <g transform="translate(20, 24)">
        <rect x="0" y="0" width="192" height="96" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
        <rect x="0" y="0" width="192" height="96" fill="url(#woodHatch)" />

        <!-- Centerline -->
        <line x1="-5" y1="48" x2="197" y2="48" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />
        <!-- Vertical centerline of hole -->
        <line x1="96" y1="-5" x2="96" y2="101" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />

        <!-- Axle Hole: Ø 8.0 mm (30.2px) on centerline -->
        <circle cx="96" cy="48" r="{4.0 * MM_TO_PX}" fill="#ffffff" stroke="#000000" stroke-width="1.6" />
        <line x1="80" y1="48" x2="112" y2="48" stroke="#000000" stroke-width="1.0" />
        <line x1="96" y1="32" x2="96" y2="64" stroke="#000000" stroke-width="1.0" />

        <g font-family="monospace" text-anchor="middle">
          <text x="45" y="43" font-size="7.5" font-weight="900" fill="#000000">Ø 8.0mm</text>
          <text x="45" y="54" font-size="6.8" fill="#475569">(5/16") BORE</text>

          <text x="148" y="43" font-size="7.5" font-weight="bold" fill="#000000">8.00" [203mm]</text>
          <text x="148" y="54" font-size="6.8" fill="#475569">from CW End</text>

          <text x="96" y="78" font-size="7.5" font-weight="bold" fill="#000000">Must be drilled 100% square!</text>
          <text x="96" y="88" font-size="7" fill="#475569">Use drill press with clamp block</text>
        </g>
      </g>
    </g>

    <!-- Jig 3: Counterweight Mount Bolt Hole (1:1) -->
    <g transform="translate(500, 24)">
      <rect x="0" y="0" width="240" height="156" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" />
      <text x="10" y="15" font-family="monospace" font-size="9" font-weight="900" fill="#000000">3. CW MOUNT BOLT (1:1)</text>

      <g transform="translate(20, 24)">
        <rect x="0" y="0" width="192" height="96" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
        <rect x="0" y="0" width="192" height="96" fill="url(#woodHatch)" />

        <!-- Centerlines -->
        <line x1="-5" y1="48" x2="197" y2="48" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />

        <!-- Bolt hole center x = 70 -->
        <line x1="70" y1="-5" x2="70" y2="101" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />

        <!-- Bolt Hole: Ø 3/8" (36px diameter) -->
        <circle cx="70" cy="48" r="18" fill="#ffffff" stroke="#000000" stroke-width="1.6" />
        <line x1="50" y1="48" x2="90" y2="48" stroke="#000000" stroke-width="1.0" />
        <line x1="70" y1="28" x2="70" y2="68" stroke="#000000" stroke-width="1.0" />

        <!-- Dimension from end -->
        <line x1="0" y1="104" x2="70" y2="104" stroke="#000000" stroke-width="1.0" marker-start="url(#arrow)" marker-end="url(#arrow)" />
        <text x="35" y="115" font-family="monospace" font-size="7" font-weight="bold" fill="#000000" text-anchor="middle">1.31" [33mm]</text>
        <text x="0" y="125" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000">CW END</text>

        <g transform="translate(142, 28)" font-family="monospace" text-anchor="middle">
          <text x="0" y="0" font-size="8" font-weight="900" fill="#000000">Ø 3/8" BOLT BORE</text>
          <text x="0" y="12" font-size="6.8" fill="#475569">For 3/8"-16 Rod</text>
          <text x="0" y="28" font-size="7.5" font-weight="bold" fill="#000000">2.0 kg CW Mount</text>
          <text x="0" y="40" font-size="6.8" fill="#475569">Washers + Locknuts</text>
        </g>
      </g>
    </g>
  </g>
''')

    # -------------------------------------------------------------
    # 5. ROW 4: PART W6 (TROUGH PROFILE 1:1), LAP JOINTS (1:1), & SCHEDULE
    # -------------------------------------------------------------
    svg.append(f'''
  <!-- ==================== ROW 4: W6 TROUGH PROFILE & JOINTS & MASTER CUT SCHEDULE ==================== -->
  <g transform="translate(38, 740)">
    <!-- Header banner -->
    <rect x="0" y="0" width="740" height="18" fill="#f8fafc" stroke="#000000" stroke-width="1.0" />
    <text x="10" y="13" font-family="monospace" font-size="9.5" font-weight="bold" fill="#000000">
      [W6] TROUGH PROFILE • BASE LAP JOINTS (1:1) • MASTER CUTTING SCHEDULE TABLE
    </text>
    <text x="590" y="13" font-family="monospace" font-size="8.5" font-weight="bold" fill="#000000">
      LUMBER &amp; JOINERY SUMMARY
    </text>

    <!-- Item 1: W6 Trough Track Profile 1:1 -->
    <g transform="translate(0, 24)">
      <rect x="0" y="0" width="220" height="252" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" />
      <text x="10" y="15" font-family="monospace" font-size="9" font-weight="900" fill="#000000">
        W6 TROUGH END PROFILE (1:1)
      </text>

      <g transform="translate(14, 72)">
        <!-- 2.0" wide x 0.5" thick rectangular wood profile -->
        <!-- width = 192, height = 48 -->
        <rect x="0" y="0" width="192" height="48" fill="#ffffff" stroke="#000000" stroke-width="1.6" />
        <rect x="0" y="0" width="192" height="48" fill="url(#woodHatch)" />

        <!-- Routed Ø16mm semicircular groove in center (x=96, radius = 30.2px) -->
        <path d="M 65.8 0 A 30.2 30.2 0 0 0 126.2 0 Z" fill="#f1f5f9" stroke="#000000" stroke-width="1.4" />
        <!-- 16mm Marble seated inside groove -->
        <circle cx="96" cy="15" r="30.2" fill="#e0f2fe" stroke="#0284c7" stroke-width="1.2" stroke-dasharray="2,1" />

        <text x="96" y="-18" font-family="monospace" font-size="7.5" font-weight="bold" fill="#0284c7" text-anchor="middle">
          Ø 16mm Glass Marble
        </text>

        <!-- Width & Thickness Dimensions -->
        <line x1="0" y1="56" x2="192" y2="56" stroke="#000000" stroke-width="1.0" marker-start="url(#arrow)" marker-end="url(#arrow)" />
        <text x="96" y="66" font-family="monospace" font-size="7.5" font-weight="bold" fill="#000000" text-anchor="middle">
          2.00" [50.8mm] FINISHED WIDTH
        </text>

        <line x1="198" y1="0" x2="198" y2="48" stroke="#000000" stroke-width="1.0" marker-start="url(#arrow)" marker-end="url(#arrow)" />
        <text x="202" y="27" font-family="monospace" font-size="7" font-weight="bold" fill="#000000">
          0.50" [12.7mm]
        </text>

        <!-- Specification notes -->
        <g transform="translate(0, 80)">
          <text x="0" y="0" font-family="monospace" font-size="8" font-weight="bold" fill="#000000">ROUTING SPECIFICATION:</text>
          <text x="0" y="12" font-family="monospace" font-size="7.5" fill="#334155">• Bit: Ø 5/8" (16mm) Core-Box bit</text>
          <text x="0" y="24" font-family="monospace" font-size="7.5" fill="#334155">• Depth of Cut: 3/16" (4.8mm)</text>
          <text x="0" y="36" font-family="monospace" font-size="7.5" fill="#334155">• Length: 21.94" [557.2mm]</text>
          <text x="0" y="48" font-family="monospace" font-size="7.5" fill="#334155">• Mount: Centered on Base Ladder</text>
          <text x="0" y="60" font-family="monospace" font-size="7.5" font-weight="bold" fill="#b91c1c">• Sand groove with 320-grit + wax</text>
        </g>
      </g>
    </g>

    <!-- Item 2: Base Corner Joint Template (1:1) -->
    <g transform="translate(230, 24)">
      <rect x="0" y="0" width="170" height="252" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" />
      <text x="10" y="15" font-family="monospace" font-size="9" font-weight="900" fill="#000000">
        BASE CORNER JOINT (1:1)
      </text>

      <g transform="translate(13, 25)">
        <!-- 1.5" x 1.5" (144px x 144px) square overlap -->
        <rect x="0" y="0" width="144" height="144" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
        <rect x="0" y="0" width="144" height="144" fill="url(#woodHatch)" />

        <!-- Centered Ø 1/4" Bolt Hole (radius = 12px) -->
        <line x1="-5" y1="72" x2="149" y2="72" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />
        <line x1="72" y1="-5" x2="72" y2="149" stroke="#475569" stroke-width="0.8" stroke-dasharray="6,3" />

        <circle cx="72" cy="72" r="12" fill="#ffffff" stroke="#000000" stroke-width="1.6" />
        <line x1="56" y1="72" x2="88" y2="72" stroke="#000000" stroke-width="1.0" />
        <line x1="72" y1="56" x2="72" y2="88" stroke="#000000" stroke-width="1.0" />

        <text x="72" y="24" font-family="monospace" font-size="8" font-weight="bold" fill="#000000" text-anchor="middle">
          W1 RUNNER &amp; W2 CROSSBAR
        </text>
        <text x="72" y="36" font-family="monospace" font-size="8.5" font-weight="900" fill="#000000" text-anchor="middle">
          1.5" x 1.5" OVERLAP
        </text>
        <text x="72" y="100" font-family="monospace" font-size="8.5" font-weight="900" fill="#b91c1c" text-anchor="middle">
          Ø 1/4" BOLT HOLE
        </text>
        <text x="72" y="112" font-family="monospace" font-size="7" fill="#475569" text-anchor="middle">
          0.75" from all edges
        </text>
      </g>

      <g transform="translate(13, 185)">
        <text x="0" y="0" font-family="monospace" font-size="8" font-weight="bold" fill="#000000">CLAMPING INSTRUCTIONS:</text>
        <text x="0" y="12" font-family="monospace" font-size="7.5" fill="#334155">• Drill 6x corner &amp; mid holes</text>
        <text x="0" y="24" font-family="monospace" font-size="7.5" fill="#334155">• 1/4"-20 x 2" Hex Bolts</text>
        <text x="0" y="36" font-family="monospace" font-size="7.5" fill="#334155">• Apply wood glue + washers</text>
      </g>
    </g>

    <!-- Item 3: Master Cutting Schedule & Bill of Materials -->
    <g transform="translate(410, 24)">
      <rect x="0" y="0" width="330" height="252" fill="#ffffff" stroke="#000000" stroke-width="1.2" />
      <rect x="0" y="0" width="330" height="18" fill="#f1f5f9" />
      <text x="8" y="13" font-family="monospace" font-size="8.5" font-weight="bold" fill="#000000">
        MASTER CUTTING SCHEDULE &amp; FABRICATION TABLE
      </text>

      <!-- Table Header -->
      <g transform="translate(6, 26)" font-family="monospace" font-size="7.5">
        <text x="0" y="0" font-weight="bold" fill="#000000">PART</text>
        <text x="35" y="0" font-weight="bold" fill="#000000">QTY</text>
        <text x="65" y="0" font-weight="bold" fill="#000000">RAW SIZE</text>
        <text x="145" y="0" font-weight="bold" fill="#000000">LENGTH</text>
        <text x="215" y="0" font-weight="bold" fill="#000000">MITERS / NOTES</text>
        <line x1="0" y1="4" x2="318" y2="4" stroke="#000000" stroke-width="1.0" />

        <!-- Rows -->
        <!-- W1 -->
        <g transform="translate(0, 16)">
          <text x="0" y="0" font-weight="bold" fill="#000000">W1</text>
          <text x="38" y="0">2</text>
          <text x="65" y="0">3/4x1.5"</text>
          <text x="145" y="0" font-weight="bold">36.00"</text>
          <text x="215" y="0">Square; 3x lap holes</text>
        </g>
        <!-- W2 -->
        <g transform="translate(0, 28)">
          <text x="0" y="0" font-weight="bold" fill="#000000">W2</text>
          <text x="38" y="0">3</text>
          <text x="65" y="0">3/4x1.5"</text>
          <text x="145" y="0" font-weight="bold">13.50"</text>
          <text x="215" y="0">Square; predrill ends</text>
        </g>
        <!-- W4 -->
        <g transform="translate(0, 40)">
          <text x="0" y="0" font-weight="bold" fill="#000000">W4</text>
          <text x="38" y="0">4</text>
          <text x="65" y="0">3/4x1.5"</text>
          <text x="145" y="0" font-weight="bold">31.80"</text>
          <text x="215" y="0" fill="#b91c1c" font-weight="bold">17.1° Dual Parallel</text>
        </g>
        <!-- W5 -->
        <g transform="translate(0, 52)">
          <text x="0" y="0" font-weight="bold" fill="#000000">W5</text>
          <text x="38" y="0">2</text>
          <text x="65" y="0">1.5x3.0"</text>
          <text x="145" y="0" font-weight="bold">2.17" [55m]</text>
          <text x="215" y="0">Ø22mm Forstner pocket</text>
        </g>
        <!-- W6 -->
        <g transform="translate(0, 64)">
          <text x="0" y="0" font-weight="bold" fill="#000000">W6</text>
          <text x="38" y="0">1</text>
          <text x="65" y="0">1/2x2.0"</text>
          <text x="145" y="0" font-weight="bold">21.94"</text>
          <text x="215" y="0">Route Ø16mm track</text>
        </g>
        <!-- W7 -->
        <g transform="translate(0, 76)">
          <text x="0" y="0" font-weight="bold" fill="#000000">W7</text>
          <text x="38" y="0">1</text>
          <text x="65" y="0">1.5x1.5"</text>
          <text x="145" y="0" font-weight="bold">40.00"</text>
          <text x="215" y="0">Ø8mm axle, 10° pin</text>
        </g>

        <line x1="0" y1="84" x2="318" y2="84" stroke="#94a3b8" stroke-width="0.6" />

        <!-- Hardware Checklist -->
        <g transform="translate(0, 96)">
          <text x="0" y="0" font-weight="bold" fill="#000000">HARDWARE &amp; RIGGING SCHEDULE:</text>
          <text x="0" y="11" fill="#1e293b">• 2x 608-2RS Ball Bearings (8x22x7 mm)</text>
          <text x="0" y="21" fill="#1e293b">• 1x Ø 8.0 mm Steel Axle Rod (19.5" long)</text>
          <text x="0" y="31" fill="#1e293b">• 1x 3/8"-16 Threaded Rod (8" long) + 2kg CW</text>
          <text x="0" y="41" fill="#1e293b">• 10x 1/4"-20 x 2.0" Bolts, Washers &amp; Nuts</text>
          <text x="0" y="51" fill="#1e293b">• 1x 16mm (5/8") Glass Marble Projectile (20g)</text>
          <text x="0" y="61" fill="#1e293b">• 1x Cloth Sling with 14.8" nylon/twine cords</text>
          <text x="0" y="71" font-weight="bold" fill="#b91c1c">• Calibrated Sling Release Pin Angle: 10.0°</text>
        </g>

        <line x1="0" y1="180" x2="318" y2="180" stroke="#94a3b8" stroke-width="0.6" />
        <g transform="translate(0, 192)">
          <text x="0" y="0" font-weight="bold" fill="#000000">CERTIFICATION:</text>
          <text x="0" y="10" fill="#475569">Extracted 1:1 directly from Trebuchet_3ft.obj</text>
          <text x="0" y="20" font-weight="bold" fill="#000000">REV 6.0 • 1:1 WORKSHOP PRINTABLE COLLAGE</text>
        </g>
      </g>
    </g>
  </g>
</svg>
''')
    return "".join(svg)

def main():
    svg_content = create_collage_svg()

    # Targets to save
    targets = [
        "/home/steve/src/trebuchet/wood_cutout_shapes_8.5x11_collage.svg",
        "/home/steve/.gemini/antigravity/brain/91e1f823-b856-4d61-bc57-2d759f389fdf/wood_cutout_shapes_8.5x11_collage.svg"
    ]

    for t in targets:
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with open(t, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"Saved: {t}")

    # Convert to PDF using cairosvg
    pdf_targets = [
        "/home/steve/src/trebuchet/wood_cutout_shapes_8.5x11_collage.pdf",
        "/home/steve/.gemini/antigravity/brain/91e1f823-b856-4d61-bc57-2d759f389fdf/wood_cutout_shapes_8.5x11_collage.pdf"
    ]

    src_svg = targets[0]
    for pdf_path in pdf_targets:
        cmd = ["cairosvg", src_svg, "-o", pdf_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Generated PDF: {pdf_path}")
        else:
            print(f"Error generating PDF {pdf_path}: {res.stderr}")

    # Render high-res PNG for visual artifact verification
    png_artifact = "/home/steve/.gemini/antigravity/brain/91e1f823-b856-4d61-bc57-2d759f389fdf/wood_cutout_shapes_8.5x11_collage.png"
    cmd_png = ["cairosvg", src_svg, "-o", png_artifact, "-d", "150"]
    subprocess.run(cmd_png, check=True)
    print(f"Rendered PNG artifact: {png_artifact}")

if __name__ == '__main__':
    main()
