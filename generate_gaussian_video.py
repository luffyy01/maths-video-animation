#!/usr/bin/env python3
import math
import os
import subprocess
import sys
import time
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1920
HEIGHT = 1080
FPS = 24
TOTAL_DURATION = 300.0
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)
OUTPUT_FILENAME = "gaussian_elimination_full_concept.mp4"

COLOR_BG = (10, 14, 26)
COLOR_HEADER_BG = (15, 23, 42)
COLOR_PANEL_BG = (19, 27, 46)
COLOR_PANEL_BORDER = (45, 59, 85)
COLOR_ACCENT_CYAN = (56, 189, 248)
COLOR_ACCENT_GOLD = (251, 191, 36)
COLOR_ACCENT_GREEN = (52, 211, 153)
COLOR_ACCENT_ROSE = (244, 63, 94)
COLOR_ACCENT_PURPLE = (168, 85, 247)
COLOR_TEXT_PRIMARY = (248, 250, 252)
COLOR_TEXT_MUTED = (148, 163, 184)
COLOR_TEXT_DIM = (100, 116, 139)
COLOR_GRID = (24, 33, 52)

CHAPTERS = [
    {"start": 0.0,   "end": 35.0,  "name": "THE FOUNDATIONS & STRATEGY", "badge": "INTRODUCTION"},
    {"start": 35.0,  "end": 75.0,  "name": "EQUATIONS TO AUGMENTED MATRIX", "badge": "MATRIX FORM"},
    {"start": 75.0,  "end": 125.0, "name": "THE 3 ELEMENTARY ROW OPERATIONS", "badge": "THE RULES"},
    {"start": 125.0, "end": 215.0, "name": "FORWARD ELIMINATION TO REF", "badge": "STEP-BY-STEP"},
    {"start": 215.0, "end": 255.0, "name": "BACK-SUBSTITUTION & SOLUTION", "badge": "SOLVING"},
    {"start": 255.0, "end": 280.0, "name": "SPECIAL CASES: INFINITE & NO SOLUTION", "badge": "BEHAVIOR"},
    {"start": 280.0, "end": 300.0, "name": "GAUSS-JORDAN & REAL-WORLD IMPACT", "badge": "APPLICATIONS"},
]

def load_fonts():
    title_path = "/System/Library/Fonts/Helvetica.ttc"
    mono_path = "/System/Library/Fonts/Menlo.ttc"
    body_path = "/System/Library/Fonts/Helvetica.ttc"

    def get_f(path, size):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    return {
        "title_xl": get_f(title_path, 60),
        "title_lg": get_f(title_path, 44),
        "title_md": get_f(title_path, 34),
        "title_sm": get_f(title_path, 26),
        "body_lg":  get_f(body_path, 24),
        "body_md":  get_f(body_path, 20),
        "body_sm":  get_f(body_path, 16),
        "mono_xl":  get_f(mono_path, 42),
        "mono_lg":  get_f(mono_path, 32),
        "mono_md":  get_f(mono_path, 24),
        "mono_sm":  get_f(mono_path, 18),
    }

FONTS = load_fonts()

def clamp(v, min_v=0.0, max_v=1.0):
    return max(min_v, min(max_v, v))

def lerp(a, b, t):
    return a + (b - a) * t

def ease_in_out(t):
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)

def ease_out_cubic(t):
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3

def pulse(t, freq=1.0):
    return 0.5 + 0.5 * math.sin(2.0 * math.pi * freq * t)

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def draw_card(draw, x, y, w, h, fill=COLOR_PANEL_BG, border=COLOR_PANEL_BORDER, radius=16, glow=None, width=2):
    if glow:
        draw_rounded_rect(draw, [x - 4, y - 4, x + w + 4, y + h + 4], radius + 4, outline=glow, width=2)
    draw_rounded_rect(draw, [x, y, x + w, y + h], radius, fill=fill, outline=border, width=width)

def draw_pill(draw, x, y, text, font=FONTS["body_sm"], bg=(30, 41, 59), fg=COLOR_TEXT_PRIMARY, border=None, pad_x=14, pad_y=6):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    w = tw + pad_x * 2
    h = th + pad_y * 2
    draw_rounded_rect(draw, [x, y, x + w, y + h], radius=h // 2, fill=bg, outline=border, width=1)
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, font=font, fill=fg)
    return w, h

def draw_bracket(draw, x, y, h, is_left=True, color=COLOR_ACCENT_CYAN, width=4, corner=14):
    arm = 22
    if is_left:
        draw.line([x + arm, y, x + corner, y], fill=color, width=width)
        draw.arc([x, y, x + corner * 2, y + corner * 2], 180, 270, fill=color, width=width)
        draw.line([x, y + corner, x, y + h - corner], fill=color, width=width)
        draw.arc([x, y + h - corner * 2, x + corner * 2, y + h], 90, 180, fill=color, width=width)
        draw.line([x + corner, y + h, x + arm, y + h], fill=color, width=width)
    else:
        draw.line([x - arm, y, x - corner, y], fill=color, width=width)
        draw.arc([x - corner * 2, y, x, y + corner * 2], 270, 360, fill=color, width=width)
        draw.line([x, y + corner, x, y + h - corner], fill=color, width=width)
        draw.arc([x - corner * 2, y + h - corner * 2, x, y + h], 0, 90, fill=color, width=width)
        draw.line([x - corner, y + h, x - arm, y + h], fill=color, width=width)

def draw_arrow(draw, x0, y0, x1, y1, color=COLOR_ACCENT_CYAN, width=3, head_size=12):
    draw.line([x0, y0, x1, y1], fill=color, width=width)
    angle = math.atan2(y1 - y0, x1 - x0)
    p1 = (x1 - head_size * math.cos(angle - math.pi / 6), y1 - head_size * math.sin(angle - math.pi / 6))
    p2 = (x1 - head_size * math.cos(angle + math.pi / 6), y1 - head_size * math.sin(angle + math.pi / 6))
    draw.polygon([(x1, y1), p1, p2], fill=color)

def draw_matrix_box(draw, x, y, matrix, col_headers=None, row_headers=None,
                    pivot_cell=None, target_cell=None, zero_cells=None,
                    highlight_row=None, scale=1.0, title="AUGMENTED MATRIX",
                    show_triangle_highlight=False, t_local=0.0):
    zero_cells = zero_cells or []
    rows = len(matrix)
    cols = len(matrix[0])

    cell_w = int(88 * scale)
    cell_h = int(68 * scale)
    bracket_pad = int(24 * scale)

    mat_w = cols * cell_w + bracket_pad * 2 + int(20 * scale)
    mat_h = rows * cell_h + int(50 * scale)

    card_x = x
    card_y = y
    card_w = mat_w + int(80 * scale)
    card_h = mat_h + int(100 * scale)
    draw_card(draw, card_x, card_y, card_w, card_h, fill=(15, 23, 42), border=(45, 59, 85), radius=16)

    draw.text((card_x + 24, card_y + 18), title, font=FONTS["title_sm"], fill=COLOR_ACCENT_CYAN)

    start_x = card_x + int(48 * scale)
    start_y = card_y + int(70 * scale)

    if col_headers:
        for c_idx, h_text in enumerate(col_headers):
            offset_c = c_idx * cell_w + (int(16 * scale) if c_idx == 3 else 0)
            cx = start_x + bracket_pad + offset_c + cell_w // 2
            bbox = FONTS["mono_sm"].getbbox(h_text)
            tw = bbox[2] - bbox[0]
            color = COLOR_ACCENT_PURPLE if c_idx < 3 else COLOR_ACCENT_GREEN
            draw.text((cx - tw // 2, start_y), h_text, font=FONTS["mono_sm"], fill=color)

    mat_top = start_y + int(32 * scale)
    mat_bottom = mat_top + rows * cell_h

    if show_triangle_highlight:
        z_x0 = start_x + bracket_pad + 8
        z_y0 = mat_top + cell_h + 8
        z_x1 = start_x + bracket_pad + 2 * cell_w - 8
        z_y1 = mat_top + 3 * cell_h - 8
        draw_rounded_rect(draw, [z_x0, z_y0, z_x1, z_y1], radius=12, fill=(10, 45, 30), outline=COLOR_ACCENT_GREEN, width=2)

    bracket_left_x = start_x + 4
    bracket_right_x = start_x + cols * cell_w + int(16 * scale) + bracket_pad * 2 - 4
    draw_bracket(draw, bracket_left_x, mat_top - 6, rows * cell_h + 12, is_left=True, color=COLOR_ACCENT_CYAN)
    draw_bracket(draw, bracket_right_x, mat_top - 6, rows * cell_h + 12, is_left=False, color=COLOR_ACCENT_CYAN)

    aug_x = start_x + bracket_pad + 3 * cell_w + int(8 * scale)
    for ly in range(mat_top - 2, mat_bottom + 4, 8):
        draw.line([aug_x, ly, aug_x, min(ly + 5, mat_bottom + 4)], fill=COLOR_ACCENT_CYAN, width=2)

    for r_idx in range(rows):
        ry = mat_top + r_idx * cell_h

        if row_headers and r_idx < len(row_headers):
            r_label = row_headers[r_idx]
            r_color = COLOR_ACCENT_GOLD if highlight_row == r_idx else COLOR_TEXT_MUTED
            draw.text((card_x + 14, ry + cell_h // 2 - 10), r_label, font=FONTS["mono_sm"], fill=r_color)

        for c_idx in range(cols):
            offset_c = c_idx * cell_w + (int(16 * scale) if c_idx == 3 else 0)
            cx = start_x + bracket_pad + offset_c
            val = matrix[r_idx][c_idx]

            cell_box = [cx + 4, ry + 4, cx + cell_w - 4, ry + cell_h - 4]

            is_pivot = (pivot_cell == (r_idx, c_idx))
            is_target = (target_cell == (r_idx, c_idx))
            is_zero_eliminated = ((r_idx, c_idx) in zero_cells)

            cell_bg = (23, 33, 56)
            cell_border = (45, 59, 85)
            text_color = COLOR_TEXT_PRIMARY

            if is_pivot:
                p_pulse = pulse(t_local, 2.0)
                cell_bg = (70, 50, 10)
                cell_border = COLOR_ACCENT_GOLD
                text_color = COLOR_ACCENT_GOLD
                ring_offset = int(2 + p_pulse * 4)
                draw_rounded_rect(draw, [cell_box[0] - ring_offset, cell_box[1] - ring_offset,
                                         cell_box[2] + ring_offset, cell_box[3] + ring_offset],
                                  radius=8 + ring_offset, outline=COLOR_ACCENT_GOLD, width=2)
            elif is_target:
                t_pulse = pulse(t_local, 2.5)
                cell_bg = (60, 20, 30)
                cell_border = COLOR_ACCENT_ROSE
                text_color = COLOR_ACCENT_ROSE
                ring_offset = int(2 + t_pulse * 4)
                draw_rounded_rect(draw, [cell_box[0] - ring_offset, cell_box[1] - ring_offset,
                                         cell_box[2] + ring_offset, cell_box[3] + ring_offset],
                                  radius=8 + ring_offset, outline=COLOR_ACCENT_ROSE, width=2)
            elif is_zero_eliminated:
                cell_bg = (10, 45, 30)
                cell_border = COLOR_ACCENT_GREEN
                text_color = COLOR_ACCENT_GREEN
            elif highlight_row == r_idx:
                cell_bg = (28, 42, 68)
                cell_border = (60, 85, 120)

            draw_rounded_rect(draw, cell_box, radius=8, fill=cell_bg, outline=cell_border, width=1)

            val_str = f"{val:2d}" if isinstance(val, int) else f"{val}"
            bbox = FONTS["mono_lg"].getbbox(val_str)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = cx + cell_w // 2 - tw // 2
            ty = ry + cell_h // 2 - th // 2 - bbox[1]
            draw.text((tx, ty), val_str, font=FONTS["mono_lg"], fill=text_color)

    return card_w, card_h

def draw_header(draw, chapter_idx, chapter_title, badge_text):
    draw.rectangle([0, 0, WIDTH, 72], fill=COLOR_HEADER_BG)
    draw.line([0, 72, WIDTH, 72], fill=COLOR_PANEL_BORDER, width=2)

    draw_pill(draw, 40, 18, "[ A | b ]", font=FONTS["mono_sm"], bg=(30, 41, 59), fg=COLOR_ACCENT_CYAN, border=COLOR_ACCENT_CYAN)
    draw.text((180, 23), "GAUSSIAN ELIMINATION MASTERCLASS", font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)

    clean_name = chapter_title.split(". ", 1)[-1]
    chap_text = f"CHAPTER {chapter_idx + 1}: {clean_name}"
    bbox = FONTS["body_md"].getbbox(chap_text)
    tw = bbox[2] - bbox[0]
    draw_pill(draw, WIDTH // 2 - tw // 2 - 20, 18, chap_text, font=FONTS["body_md"], bg=(23, 33, 56), fg=COLOR_ACCENT_GOLD, border=COLOR_PANEL_BORDER)

    draw_pill(draw, WIDTH - 240, 18, f"● {badge_text}", font=FONTS["body_sm"], bg=(16, 37, 30), fg=COLOR_ACCENT_GREEN, border=COLOR_ACCENT_GREEN)

def draw_footer_progress(draw, t, total_t=TOTAL_DURATION):
    bar_y = HEIGHT - 46
    draw.rectangle([0, bar_y - 14, WIDTH, HEIGHT], fill=COLOR_HEADER_BG)
    draw.line([0, bar_y - 14, WIDTH, bar_y - 14], fill=COLOR_PANEL_BORDER, width=2)

    cur_m = int(t) // 60
    cur_s = int(t) % 60
    tot_m = int(total_t) // 60
    tot_s = int(total_t) % 60
    time_str = f"{cur_m:02d}:{cur_s:02d} / {tot_m:02d}:{tot_s:02d}"
    draw.text((40, bar_y - 4), time_str, font=FONTS["mono_sm"], fill=COLOR_TEXT_MUTED)

    bar_x0 = 210
    bar_x1 = WIDTH - 260
    bar_w = bar_x1 - bar_x0
    draw_rounded_rect(draw, [bar_x0, bar_y + 4, bar_x1, bar_y + 12], radius=4, fill=(30, 41, 59))

    progress = clamp(t / total_t)
    fill_w = int(bar_w * progress)
    if fill_w > 4:
        draw_rounded_rect(draw, [bar_x0, bar_y + 4, bar_x0 + fill_w, bar_y + 12], radius=4, fill=COLOR_ACCENT_CYAN)
        draw.ellipse([bar_x0 + fill_w - 6, bar_y + 1, bar_x0 + fill_w + 6, bar_y + 15], fill=COLOR_TEXT_PRIMARY, outline=COLOR_ACCENT_CYAN, width=2)

    for ch in CHAPTERS:
        tick_t = ch["start"]
        if tick_t > 0:
            tx = bar_x0 + int(bar_w * (tick_t / total_t))
            draw.line([tx, bar_y + 1, tx, bar_y + 15], fill=(70, 85, 115), width=2)

    draw.text((WIDTH - 230, bar_y - 4), "PURE VISUAL EXPLANATION", font=FONTS["body_sm"], fill=COLOR_TEXT_MUTED)

def draw_background_grid(draw):
    for gx in range(0, WIDTH, 80):
        draw.line([gx, 72, gx, HEIGHT - 55], fill=COLOR_GRID, width=1)
    for gy in range(72, HEIGHT - 55, 80):
        draw.line([0, gy, WIDTH, gy], fill=COLOR_GRID, width=1)

def render_scene_1(draw, t_local):
    alpha = ease_out_cubic(clamp(t_local / 2.0))
    title_y = int(lerp(140, 110, alpha))
    draw.text((100, title_y), "GAUSSIAN ELIMINATION", font=FONTS["title_xl"], fill=COLOR_TEXT_PRIMARY)
    draw.text((100, title_y + 70), "The Engine of Linear Algebra & System Solving", font=FONTS["title_md"], fill=COLOR_ACCENT_CYAN)

    card1_alpha = ease_out_cubic(clamp((t_local - 2.5) / 1.5))
    if card1_alpha > 0:
        c1_x = int(lerp(50, 100, card1_alpha))
        draw_card(draw, c1_x, 240, 800, 420, fill=(15, 23, 42), border=(45, 59, 85), radius=16)
        draw.text((c1_x + 30, 265), "THE CORE PROBLEM: LINEAR SYSTEMS", font=FONTS["title_sm"], fill=COLOR_ACCENT_GOLD)

        lines = [
            ("Equation 1:", "a11*x  +  a12*y  +  a13*z  =  b1"),
            ("Equation 2:", "a21*x  +  a22*y  +  a23*z  =  b2"),
            ("Equation 3:", "a31*x  +  a32*y  +  a33*z  =  b3"),
        ]
        for idx, (label, eq) in enumerate(lines):
            ly = 330 + idx * 56
            draw.text((c1_x + 35, ly), label, font=FONTS["mono_sm"], fill=COLOR_TEXT_MUTED)
            draw.text((c1_x + 175, ly), eq, font=FONTS["mono_md"], fill=COLOR_TEXT_PRIMARY)

        draw_card(draw, c1_x + 30, 510, 740, 120, fill=(23, 33, 56), border=(56, 189, 248), radius=12)
        draw.text((c1_x + 50, 525), "WHY NOT JUST USE TRIAL & ERROR OR SUBSTITUTION?", font=FONTS["body_md"], fill=COLOR_ACCENT_CYAN)
        msg = "With 3, 10, or 10,000 variables, manual substitution spirals into chaos.\nWe need an exact, deterministic, algorithmic method with NO guessing."
        draw.text((c1_x + 50, 555), msg, font=FONTS["body_sm"], fill=COLOR_TEXT_MUTED)

    card2_alpha = ease_out_cubic(clamp((t_local - 7.0) / 1.5))
    if card2_alpha > 0:
        c2_x = 940
        draw_card(draw, c2_x, 240, 880, 420, fill=(15, 23, 42), border=(45, 59, 85), radius=16)
        draw.text((c2_x + 30, 265), "THE 3-STAGE MASTER STRATEGY", font=FONTS["title_sm"], fill=COLOR_ACCENT_GREEN)

        steps = [
            ("1. MATRIX ENCODING", "Strip variables x, y, z to form the Augmented Matrix [ A | b ].", COLOR_ACCENT_CYAN),
            ("2. FORWARD ELIMINATION", "Apply Row Operations to eliminate entries below diagonal (Row Echelon Form).", COLOR_ACCENT_GOLD),
            ("3. BACK-SUBSTITUTION", "Solve bottom equation (1 variable), then back-substitute upward to solve all.", COLOR_ACCENT_GREEN),
        ]
        for idx, (s_title, s_desc, s_color) in enumerate(steps):
            sy = 325 + idx * 95
            draw_card(draw, c2_x + 30, sy, 820, 80, fill=(23, 33, 56), border=s_color, radius=12)
            draw.text((c2_x + 50, sy + 14), s_title, font=FONTS["title_sm"], fill=s_color)
            draw.text((c2_x + 50, sy + 44), s_desc, font=FONTS["body_sm"], fill=COLOR_TEXT_MUTED)

    card3_alpha = ease_out_cubic(clamp((t_local - 16.0) / 1.5))
    if card3_alpha > 0:
        b_y = 690
        draw_card(draw, 100, b_y, 1720, 180, fill=(15, 23, 42), border=(70, 85, 115), radius=16)
        draw_pill(draw, 130, b_y + 20, "HISTORICAL FACT & APPLICATION", font=FONTS["body_sm"], bg=(30, 41, 59), fg=COLOR_ACCENT_GOLD)

        t1 = "* First documented in China (c. 150 BCE) in 'The Nine Chapters on the Mathematical Art'."
        t2 = "* Formalized by Carl Friedrich Gauss (1809) to compute the asteroid Ceres's orbit."
        t3 = "* Today, it powers Computer Graphics shaders, GPS satellite navigation, and AI/ML model solvers!"
        draw.text((130, b_y + 60), t1, font=FONTS["body_lg"], fill=COLOR_TEXT_PRIMARY)
        draw.text((130, b_y + 95), t2, font=FONTS["body_lg"], fill=COLOR_TEXT_PRIMARY)
        draw.text((130, b_y + 130), t3, font=FONTS["body_lg"], fill=COLOR_ACCENT_CYAN)

    if t_local > 26.0:
        draw_card(draw, 100, 890, 1720, 75, fill=(19, 27, 46), border=COLOR_ACCENT_CYAN, radius=14)
        draw.text((130, 912), "NOW: LET'S TAKE A CONCRETE 3x3 SYSTEM AND SOLVE IT COMPLETELY STEP-BY-STEP -->", font=FONTS["title_sm"], fill=COLOR_ACCENT_CYAN)

def render_scene_2(draw, t_local):
    draw.text((100, 100), "CHAPTER 2: FORMING THE AUGMENTED MATRIX", font=FONTS["title_lg"], fill=COLOR_TEXT_PRIMARY)
    draw.text((100, 155), "Extracting pure numerical coefficients to enable algorithmic computation", font=FONTS["body_lg"], fill=COLOR_TEXT_MUTED)

    draw_card(draw, 100, 210, 740, 510, fill=(15, 23, 42), border=(45, 59, 85), radius=16)
    draw.text((130, 235), "OUR SYSTEM OF 3 LINEAR EQUATIONS", font=FONTS["title_sm"], fill=COLOR_ACCENT_CYAN)

    eqs = [
        ("Row 1 (R1):", " 1x  +  1y  +  1z  =   6", COLOR_ACCENT_CYAN),
        ("Row 2 (R2):", " 2x  +  3y  +  1z  =  11", COLOR_ACCENT_GOLD),
        ("Row 3 (R3):", " 1x  -  1y  +  2z  =   5", COLOR_ACCENT_PURPLE),
    ]
    for idx, (r_name, eq_str, col) in enumerate(eqs):
        ey = 300 + idx * 80
        draw_card(draw, 130, ey, 680, 64, fill=(23, 33, 56), border=col, radius=10)
        draw.text((150, ey + 18), r_name, font=FONTS["mono_sm"], fill=col)
        draw.text((300, ey + 15), eq_str, font=FONTS["mono_md"], fill=COLOR_TEXT_PRIMARY)

    draw.text((130, 560), "Notice the column alignment:", font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)
    draw.text((130, 600), "* Column 1: Multipliers of x  ( 1,  2,  1 )", font=FONTS["body_md"], fill=COLOR_ACCENT_CYAN)
    draw.text((130, 635), "* Column 2: Multipliers of y  ( 1,  3, -1 )", font=FONTS["body_md"], fill=COLOR_ACCENT_PURPLE)
    draw.text((130, 670), "* Column 3: Multipliers of z  ( 1,  1,  2 )", font=FONTS["body_md"], fill=COLOR_ACCENT_GOLD)

    matrix_data = [
        [1,  1,  1,   6],
        [2,  3,  1,  11],
        [1, -1,  2,   5]
    ]

    anim_progress = ease_out_cubic(clamp((t_local - 3.0) / 2.0))
    mat_x = int(lerp(1200, 900, anim_progress))
    draw_matrix_box(
        draw, mat_x, 210, matrix_data,
        col_headers=["x", "y", "z", "b (Constants)"],
        row_headers=["R1", "R2", "R3"],
        scale=1.15,
        title="THE AUGMENTED MATRIX: [ A | b ]",
        t_local=t_local
    )

    if t_local > 5.0 and t_local < 25.0:
        arrow_pulse = pulse(t_local, 1.5)
        arrow_x = int(lerp(840, 890, arrow_pulse))
        draw_arrow(draw, 840, 440, arrow_x, 440, color=COLOR_ACCENT_CYAN, width=4)

    if t_local > 12.0:
        draw_card(draw, 100, 750, 1720, 240, fill=(15, 23, 42), border=(56, 189, 248), radius=16)
        draw.text((130, 775), "ANATOMY OF THE AUGMENTED MATRIX", font=FONTS["title_sm"], fill=COLOR_ACCENT_CYAN)

        blocks = [
            ("COEFFICIENT MATRIX (A)", "The 3x3 grid containing the multipliers of variables x, y, and z. Each column corresponds to exactly one variable.", COLOR_ACCENT_PURPLE),
            ("AUGMENTING LINE ( | )", "Represents the equal signs (=). Keeps coefficients separate from constants while subjecting both to identical operations.", COLOR_ACCENT_CYAN),
            ("CONSTANT VECTOR (b)", "The 3x1 column on the right containing equation outputs (6, 11, 5). Any operation applied to A is also applied to b.", COLOR_ACCENT_GREEN),
        ]
        for b_idx, (b_title, b_desc, b_col) in enumerate(blocks):
            bx = 130 + b_idx * 550
            draw_card(draw, bx, 815, 520, 150, fill=(23, 33, 56), border=b_col, radius=12)
            draw.text((bx + 20, 830), b_title, font=FONTS["body_md"], fill=b_col)
            draw.text((bx + 20, 865), b_desc, font=FONTS["body_sm"], fill=COLOR_TEXT_MUTED)

def render_scene_3(draw, t_local):
    draw.text((100, 100), "CHAPTER 3: THE 3 ELEMENTARY ROW OPERATIONS", font=FONTS["title_lg"], fill=COLOR_TEXT_PRIMARY)
    draw.text((100, 155), "The only 3 valid moves in Gaussian Elimination (they NEVER change the solution set!)", font=FONTS["body_lg"], fill=COLOR_ACCENT_GOLD)

    ops = [
        {
            "num": "OPERATION 1",
            "name": "ROW SWAP (Ri <--> Rj)",
            "color": COLOR_ACCENT_CYAN,
            "desc": "Interchange the entire contents of any two rows.",
            "math": "R1 <--> R2",
            "example_before": "R1: [ 2,  3,  1 | 11 ]\nR2: [ 1,  1,  1 |  6 ]",
            "example_after":  "R1: [ 1,  1,  1 |  6 ]\nR2: [ 2,  3,  1 | 11 ]",
            "why": "Use when a pivot is 0, or to bring a convenient '1' to the top pivot position."
        },
        {
            "num": "OPERATION 2",
            "name": "ROW SCALING (Ri <-- k * Ri)",
            "color": COLOR_ACCENT_GOLD,
            "desc": "Multiply all entries in a row by a non-zero scalar k != 0.",
            "math": "R3 <-- 2 * R3  or  R3 <-- -1 * R3",
            "example_before": "R3: [ 1, -1,  2 |  5 ]",
            "example_after":  "R3: [ 2, -2,  4 | 10 ]  (k = 2)",
            "why": "Use to normalize a pivot to 1, or eliminate fractions from calculations."
        },
        {
            "num": "OPERATION 3",
            "name": "ROW ADDITION (Ri <-- Ri + k * Rj)",
            "color": COLOR_ACCENT_GREEN,
            "desc": "Add or subtract a scalar multiple of row j to/from row i.",
            "math": "R2 <-- R2 - 2 * R1",
            "example_before": "Target R2 has '2'. Pivot R1 has '1'.",
            "example_after":  "Subtract 2*R1 from R2 --> Entry becomes 0!",
            "why": "THE WORKHORSE! This is the exact tool used to eliminate variables and make zeros!"
        }
    ]

    for idx, op in enumerate(ops):
        card_t = clamp((t_local - idx * 6.0) / 1.5)
        card_alpha = ease_out_cubic(card_t)
        if card_alpha > 0:
            cx = 100 + idx * 580
            draw_card(draw, cx, 210, 560, 560, fill=(15, 23, 42), border=op["color"], radius=16)

            draw_pill(draw, cx + 24, 230, op["num"], font=FONTS["mono_sm"], bg=(30, 41, 59), fg=op["color"])
            draw.text((cx + 24, 275), op["name"], font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)
            draw.text((cx + 24, 320), op["desc"], font=FONTS["body_sm"], fill=COLOR_TEXT_MUTED)

            draw_card(draw, cx + 24, 370, 510, 50, fill=(23, 33, 56), border=op["color"], radius=10)
            draw.text((cx + 40, 382), f"Notation: {op['math']}", font=FONTS["mono_sm"], fill=op["color"])

            draw_card(draw, cx + 24, 435, 510, 160, fill=(11, 15, 25), border=(45, 59, 85), radius=10)
            draw.text((cx + 36, 448), "EXAMPLE IN ACTION:", font=FONTS["mono_sm"], fill=COLOR_ACCENT_CYAN)
            draw.text((cx + 36, 480), op["example_before"], font=FONTS["mono_sm"], fill=COLOR_TEXT_MUTED)
            draw.text((cx + 36, 540), op["example_after"], font=FONTS["mono_sm"], fill=COLOR_ACCENT_GREEN)

            draw.text((cx + 24, 615), "WHY WE USE IT:", font=FONTS["mono_sm"], fill=COLOR_ACCENT_GOLD)
            draw.text((cx + 24, 645), op["why"], font=FONTS["body_sm"], fill=COLOR_TEXT_PRIMARY)

    if t_local > 20.0:
        draw_card(draw, 100, 800, 1720, 180, fill=(15, 23, 42), border=COLOR_ACCENT_GOLD, radius=16)
        draw_pill(draw, 130, 820, "THE FUNDAMENTAL THEOREM OF EROs", font=FONTS["body_sm"], bg=(70, 50, 10), fg=COLOR_ACCENT_GOLD)
        t_rule = "Because elementary row operations correspond to performing identical valid algebraic operations on both sides of an equation,"
        t_rule2 = "they produce an EQUIVALENT SYSTEM that has the EXACT SAME SOLUTION VECTOR [x, y, z]T!"
        draw.text((130, 865), t_rule, font=FONTS["body_lg"], fill=COLOR_TEXT_PRIMARY)
        draw.text((130, 905), t_rule2, font=FONTS["title_sm"], fill=COLOR_ACCENT_GREEN)

def render_scene_4(draw, t_local):
    draw.text((100, 90), "CHAPTER 4: FORWARD ELIMINATION (CREATING THE ZERO TRIANGLE)", font=FONTS["title_lg"], fill=COLOR_TEXT_PRIMARY)

    if t_local < 15.0:
        draw.text((100, 145), "The Goal: Transform [ A | b ] into Row Echelon Form (Upper Triangular Matrix)", font=FONTS["body_lg"], fill=COLOR_TEXT_MUTED)

        init_mat = [[1, 1, 1, 6], [2, 3, 1, 11], [1, -1, 2, 5]]
        draw_matrix_box(draw, 100, 200, init_mat, col_headers=["x", "y", "z", "b"], row_headers=["R1", "R2", "R3"], scale=1.1, title="STARTING MATRIX", t_local=t_local)

        draw_arrow(draw, 760, 400, 980, 400, color=COLOR_ACCENT_CYAN, width=6, head_size=18)
        draw.text((760, 430), "ELIMINATE BELOW\nMAIN DIAGONAL", font=FONTS["mono_sm"], fill=COLOR_ACCENT_GOLD)

        target_mat = [["p1", "*", "*", "*"], [" 0", "p2", "*", "*"], [" 0", " 0", "p3", "*"]]
        draw_matrix_box(draw, 1040, 200, target_mat, col_headers=["x", "y", "z", "b"], row_headers=["R1", "R2", "R3"],
                        zero_cells=[(1,0), (2,0), (2,1)], scale=1.1, title="TARGET: ROW ECHELON FORM (REF)",
                        show_triangle_highlight=True, t_local=t_local)

        draw_card(draw, 100, 680, 1720, 280, fill=(15, 23, 42), border=COLOR_ACCENT_CYAN, radius=16)
        draw_pill(draw, 130, 705, "WHAT IS ROW ECHELON FORM (REF)?", font=FONTS["body_sm"], bg=(23, 33, 56), fg=COLOR_ACCENT_CYAN)
        c_lines = [
            "1. PIVOTS: The leading non-zero coefficient in each row is strictly to the right of the pivot in the row above.",
            "2. ZERO TRIANGLE: All numbers below each pivot are systematically eliminated to become EXACT ZEROS (0).",
            "3. DECOUPLING: Once in this form, the bottom equation has only ONE variable! The system is solved from bottom up!"
        ]
        for idx, line in enumerate(c_lines):
            draw.text((130, 755 + idx * 60), line, font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)

    elif t_local < 40.0:
        draw.text((100, 145), "ROUND 1 - STEP A: Eliminating Entry (Row 2, Column 1)", font=FONTS["body_lg"], fill=COLOR_ACCENT_ROSE)

        cur_mat = [[1, 1, 1, 6], [2, 3, 1, 11], [1, -1, 2, 5]]
        if t_local > 28.0:
            cur_mat[1] = [0, 1, -1, -1]

        draw_matrix_box(draw, 100, 200, cur_mat,
                        col_headers=["x", "y", "z", "b"], row_headers=["R1", "R2", "R3"],
                        pivot_cell=(0,0), target_cell=(1,0) if t_local <= 28.0 else None,
                        zero_cells=[(1,0)] if t_local > 28.0 else [],
                        highlight_row=1, scale=1.1, title="CURRENT MATRIX", t_local=t_local)

        draw_card(draw, 840, 200, 980, 760, fill=(15, 23, 42), border=COLOR_ACCENT_GOLD, radius=16)
        draw_pill(draw, 870, 225, "OPERATION BREAKDOWN", font=FONTS["mono_sm"], bg=(70, 50, 10), fg=COLOR_ACCENT_GOLD)
        draw.text((870, 270), "OPERATION:  R2 <-- R2 - 2 * R1", font=FONTS["title_md"], fill=COLOR_ACCENT_CYAN)

        draw.text((870, 335), "Why multiply R1 by 2?", font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)
        draw.text((870, 375), "* The target entry in Row 2 is 2. The pivot in Row 1 is 1.", font=FONTS["body_lg"], fill=COLOR_TEXT_MUTED)
        draw.text((870, 410), "* Therefore:  2 - (2 * 1) = 0!  The x-variable cancels completely!", font=FONTS["body_lg"], fill=COLOR_ACCENT_GREEN)

        draw_card(draw, 870, 470, 920, 310, fill=(11, 15, 25), border=(45, 59, 85), radius=12)
        draw.text((900, 495), "STEP-BY-STEP VECTOR ARITHMETIC:", font=FONTS["mono_sm"], fill=COLOR_ACCENT_CYAN)

        a_lines = [
            ("Old Row 2 (R2):", " [   2,    3,    1  |   11  ]", COLOR_TEXT_MUTED),
            ("- 2 * Row 1 (R1):", "-[   2,    2,    2  |   12  ]", COLOR_ACCENT_ROSE),
            ("-----------------", "---------------------------------", (70, 85, 115)),
            ("New Row 2 (R2):", " [   0,    1,   -1  |   -1  ]", COLOR_ACCENT_GREEN)
        ]
        for idx, (label, val_str, col) in enumerate(a_lines):
            ly = 540 + idx * 55
            draw.text((900, ly), label, font=FONTS["mono_md"], fill=col)
            draw.text((1200, ly), val_str, font=FONTS["mono_md"], fill=col)

        if t_local > 28.0:
            draw_card(draw, 100, 750, 700, 210, fill=(16, 37, 30), border=COLOR_ACCENT_GREEN, radius=14)
            draw.text((120, 775), "SUCCESS: ENTRY (2,1) IS ZERO!", font=FONTS["title_sm"], fill=COLOR_ACCENT_GREEN)
            draw.text((120, 825), "Variable x has been eliminated from Row 2.\nRow 2 now only depends on y and z.", font=FONTS["body_md"], fill=COLOR_TEXT_PRIMARY)

    elif t_local < 65.0:
        draw.text((100, 145), "ROUND 1 - STEP B: Eliminating Entry (Row 3, Column 1)", font=FONTS["body_lg"], fill=COLOR_ACCENT_ROSE)

        cur_mat = [[1, 1, 1, 6], [0, 1, -1, -1], [1, -1, 2, 5]]
        if t_local > 53.0:
            cur_mat[2] = [0, -2, 1, -1]

        draw_matrix_box(draw, 100, 200, cur_mat,
                        col_headers=["x", "y", "z", "b"], row_headers=["R1", "R2", "R3"],
                        pivot_cell=(0,0), target_cell=(2,0) if t_local <= 53.0 else None,
                        zero_cells=[(1,0)] + ([(2,0)] if t_local > 53.0 else []),
                        highlight_row=2, scale=1.1, title="CURRENT MATRIX", t_local=t_local)

        draw_card(draw, 840, 200, 980, 760, fill=(15, 23, 42), border=COLOR_ACCENT_GOLD, radius=16)
        draw_pill(draw, 870, 225, "OPERATION BREAKDOWN", font=FONTS["mono_sm"], bg=(70, 50, 10), fg=COLOR_ACCENT_GOLD)
        draw.text((870, 270), "OPERATION:  R3 <-- R3 - 1 * R1", font=FONTS["title_md"], fill=COLOR_ACCENT_CYAN)

        draw.text((870, 335), "Target entry in Row 3 is 1. Pivot in Row 1 is 1.", font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)
        draw.text((870, 375), "* Direct subtraction cancels x immediately:  1 - 1 = 0!", font=FONTS["body_lg"], fill=COLOR_ACCENT_GREEN)

        draw_card(draw, 870, 440, 920, 340, fill=(11, 15, 25), border=(45, 59, 85), radius=12)
        draw.text((900, 465), "STEP-BY-STEP VECTOR ARITHMETIC:", font=FONTS["mono_sm"], fill=COLOR_ACCENT_CYAN)

        a_lines = [
            ("Old Row 3 (R3):", " [   1,   -1,    2  |    5  ]", COLOR_TEXT_MUTED),
            ("- 1 * Row 1 (R1):", "-[   1,    1,    1  |    6  ]", COLOR_ACCENT_ROSE),
            ("-----------------", "---------------------------------", (70, 85, 115)),
            ("New Row 3 (R3):", " [   0,   -2,    1  |   -1  ]", COLOR_ACCENT_GREEN)
        ]
        for idx, (label, val_str, col) in enumerate(a_lines):
            ly = 515 + idx * 55
            draw.text((900, ly), label, font=FONTS["mono_md"], fill=col)
            draw.text((1200, ly), val_str, font=FONTS["mono_md"], fill=col)

        if t_local > 53.0:
            draw_card(draw, 100, 750, 700, 210, fill=(16, 37, 30), border=COLOR_ACCENT_GREEN, radius=14)
            draw.text((120, 775), "COLUMN 1 COMPLETE!", font=FONTS["title_sm"], fill=COLOR_ACCENT_GREEN)
            draw.text((120, 825), "All entries below Pivot 1 are now ZERO!\nWe now advance to Column 2 and Pivot 2.", font=FONTS["body_md"], fill=COLOR_TEXT_PRIMARY)

    elif t_local < 82.0:
        draw.text((100, 145), "ROUND 2: Advancing to Pivot 2 and Eliminating Entry (3, 2)", font=FONTS["body_lg"], fill=COLOR_ACCENT_ROSE)

        cur_mat = [[1, 1, 1, 6], [0, 1, -1, -1], [0, -2, 1, -1]]
        if t_local > 73.0:
            cur_mat[2] = [0, 0, -1, -3]

        draw_matrix_box(draw, 100, 200, cur_mat,
                        col_headers=["x", "y", "z", "b"], row_headers=["R1", "R2", "R3"],
                        pivot_cell=(1,1), target_cell=(2,1) if t_local <= 73.0 else None,
                        zero_cells=[(1,0), (2,0)] + ([(2,1)] if t_local > 73.0 else []),
                        highlight_row=2, scale=1.1, title="CURRENT MATRIX", t_local=t_local)

        draw_card(draw, 840, 200, 980, 760, fill=(15, 23, 42), border=COLOR_ACCENT_GOLD, radius=16)
        draw_pill(draw, 870, 225, "OPERATION BREAKDOWN", font=FONTS["mono_sm"], bg=(70, 50, 10), fg=COLOR_ACCENT_GOLD)
        draw.text((870, 270), "OPERATION:  R3 <-- R3 + 2 * R2", font=FONTS["title_md"], fill=COLOR_ACCENT_CYAN)

        draw.text((870, 335), "Target entry in Row 3 is -2. Pivot in Row 2 is 1.", font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)
        draw.text((870, 375), "* Adding 2 * (Row 2) produces:  -2 + 2(1) = 0!  y is eliminated!", font=FONTS["body_lg"], fill=COLOR_ACCENT_GREEN)

        draw_card(draw, 870, 440, 920, 340, fill=(11, 15, 25), border=(45, 59, 85), radius=12)
        draw.text((900, 465), "STEP-BY-STEP VECTOR ARITHMETIC:", font=FONTS["mono_sm"], fill=COLOR_ACCENT_CYAN)

        a_lines = [
            ("Old Row 3 (R3):", " [   0,   -2,    1  |   -1  ]", COLOR_TEXT_MUTED),
            ("+ 2 * Row 2 (R2):", "+[   0,    2,   -2  |   -2  ]", COLOR_ACCENT_CYAN),
            ("-----------------", "---------------------------------", (70, 85, 115)),
            ("New Row 3 (R3):", " [   0,    0,   -1  |   -3  ]", COLOR_ACCENT_GREEN)
        ]
        for idx, (label, val_str, col) in enumerate(a_lines):
            ly = 515 + idx * 55
            draw.text((900, ly), label, font=FONTS["mono_md"], fill=col)
            draw.text((1200, ly), val_str, font=FONTS["mono_md"], fill=col)

        if t_local > 73.0:
            draw_card(draw, 100, 750, 700, 210, fill=(16, 37, 30), border=COLOR_ACCENT_GREEN, radius=14)
            draw.text((120, 775), "ZERO TRIANGLE COMPLETE!", font=FONTS["title_sm"], fill=COLOR_ACCENT_GREEN)
            draw.text((120, 825), "Entries (2,1), (3,1), and (3,2) are all 0!\nNow scale Row 3 to make leading pivot +1.", font=FONTS["body_md"], fill=COLOR_TEXT_PRIMARY)

    else:
        draw.text((100, 145), "TRIUMPH: UPPER TRIANGULAR ROW ECHELON FORM ACHIEVED!", font=FONTS["title_lg"], fill=COLOR_ACCENT_GREEN)

        final_mat = [[1, 1, 1, 6], [0, 1, -1, -1], [0, 0, 1, 3]]
        draw_matrix_box(draw, 100, 200, final_mat,
                        col_headers=["x", "y", "z", "b"], row_headers=["R1", "R2", "R3"],
                        zero_cells=[(1,0), (2,0), (2,1)], scale=1.1, title="FINAL ROW ECHELON FORM (REF)",
                        show_triangle_highlight=True, t_local=t_local)

        draw_card(draw, 840, 200, 980, 760, fill=(15, 23, 42), border=COLOR_ACCENT_GREEN, radius=16)
        draw_pill(draw, 870, 225, "KEY INSIGHT", font=FONTS["mono_sm"], bg=(16, 37, 30), fg=COLOR_ACCENT_GREEN)
        draw.text((870, 270), "THE SYSTEM IS NOW COMPLETELY DECOUPLED!", font=FONTS["title_md"], fill=COLOR_TEXT_PRIMARY)

        obs = [
            ("ROW 3 (R3):", "0x + 0y + 1z = 3   -->   z = 3  (ONLY 1 VARIABLE!)", COLOR_ACCENT_GREEN),
            ("ROW 2 (R2):", "0x + 1y - 1z = -1  -->   y - z = -1  (2 VARIABLES)", COLOR_ACCENT_GOLD),
            ("ROW 1 (R1):", "1x + 1y + 1z = 6   -->   x + y + z = 6  (3 VARIABLES)", COLOR_ACCENT_CYAN),
        ]
        for idx, (r_name, r_desc, r_col) in enumerate(obs):
            oy = 340 + idx * 90
            draw_card(draw, 870, oy, 920, 75, fill=(23, 33, 56), border=r_col, radius=12)
            draw.text((890, oy + 12), r_name, font=FONTS["title_sm"], fill=r_col)
            draw.text((890, oy + 42), r_desc, font=FONTS["body_md"], fill=COLOR_TEXT_PRIMARY)

        draw_card(draw, 870, 630, 920, 290, fill=(11, 15, 25), border=(56, 189, 248), radius=12)
        draw.text((890, 655), "WHY GAUSSIAN ELIMINATION IS SO POWERFUL:", font=FONTS["title_sm"], fill=COLOR_ACCENT_CYAN)
        p_text = (
            "We did not have to make any guesses or solve complicated simultaneous substitutions.\n\n"
            "By systematically driving zeros into the lower triangle, each equation becomes simpler\n"
            "than the one above it. We are now ready for the final step: BACK-SUBSTITUTION!"
        )
        draw.text((890, 700), p_text, font=FONTS["body_lg"], fill=COLOR_TEXT_MUTED)

def render_scene_5(draw, t_local):
    draw.text((100, 100), "CHAPTER 5: BACK-SUBSTITUTION (UNLOCKING THE SOLUTIONS)", font=FONTS["title_lg"], fill=COLOR_TEXT_PRIMARY)
    draw.text((100, 155), "Working from the bottom row up: each solved variable unlocks the next!", font=FONTS["body_lg"], fill=COLOR_ACCENT_GREEN)

    draw_card(draw, 100, 210, 680, 750, fill=(15, 23, 42), border=(45, 59, 85), radius=16)
    draw.text((130, 235), "EQUATIONS FROM ROW ECHELON FORM", font=FONTS["title_sm"], fill=COLOR_ACCENT_CYAN)

    eq_cards = [
        ("Row 1 (R1):", "x  +  y  +  z  =   6", COLOR_ACCENT_CYAN),
        ("Row 2 (R2):", "      y  -  z  =  -1", COLOR_ACCENT_GOLD),
        ("Row 3 (R3):", "            z  =   3", COLOR_ACCENT_GREEN),
    ]
    for idx, (lbl, eq, col) in enumerate(eq_cards):
        ey = 290 + idx * 80
        draw_card(draw, 130, ey, 620, 64, fill=(23, 33, 56), border=col, radius=10)
        draw.text((150, ey + 18), lbl, font=FONTS["mono_sm"], fill=col)
        draw.text((320, ey + 15), eq, font=FONTS["mono_md"], fill=COLOR_TEXT_PRIMARY)

    if t_local > 12.0:
        draw_arrow(draw, 640, 460, 640, 390, color=COLOR_ACCENT_GOLD, width=3)
    if t_local > 22.0:
        draw_arrow(draw, 640, 370, 640, 310, color=COLOR_ACCENT_CYAN, width=3)

    draw_card(draw, 820, 210, 1000, 750, fill=(15, 23, 42), border=COLOR_ACCENT_GREEN, radius=16)
    draw.text((850, 235), "THE BACK-SUBSTITUTION CASCADE", font=FONTS["title_sm"], fill=COLOR_ACCENT_GREEN)

    z_alpha = ease_out_cubic(clamp((t_local - 3.0) / 1.5))
    if z_alpha > 0:
        draw_card(draw, 850, 290, 940, 120, fill=(16, 37, 30), border=COLOR_ACCENT_GREEN, radius=12)
        draw_pill(draw, 870, 305, "STEP 1: SOLVE BOTTOM EQUATION (z)", font=FONTS["mono_sm"], bg=(10, 45, 30), fg=COLOR_ACCENT_GREEN)
        draw.text((870, 350), "Equation 3 directly states:   1 * z  =  3   -->   z = 3", font=FONTS["title_sm"], fill=COLOR_ACCENT_GREEN)

    y_alpha = ease_out_cubic(clamp((t_local - 12.0) / 1.5))
    if y_alpha > 0:
        draw_card(draw, 850, 430, 940, 140, fill=(40, 32, 10), border=COLOR_ACCENT_GOLD, radius=12)
        draw_pill(draw, 870, 445, "STEP 2: SUBSTITUTE z = 3 INTO ROW 2 (y)", font=FONTS["mono_sm"], bg=(70, 50, 10), fg=COLOR_ACCENT_GOLD)
        draw.text((870, 490), "y  -  (3)  =  -1   -->   y  =  -1 + 3   -->   y = 2", font=FONTS["title_sm"], fill=COLOR_ACCENT_GOLD)

    x_alpha = ease_out_cubic(clamp((t_local - 22.0) / 1.5))
    if x_alpha > 0:
        draw_card(draw, 850, 590, 940, 140, fill=(15, 35, 55), border=COLOR_ACCENT_CYAN, radius=12)
        draw_pill(draw, 870, 605, "STEP 3: SUBSTITUTE y = 2, z = 3 INTO ROW 1 (x)", font=FONTS["mono_sm"], bg=(23, 45, 70), fg=COLOR_ACCENT_CYAN)
        draw.text((870, 650), "x  +  (2)  +  (3)  =  6   -->   x + 5 = 6   -->   x = 1", font=FONTS["title_sm"], fill=COLOR_ACCENT_CYAN)

    if t_local > 30.0:
        draw_card(draw, 850, 750, 940, 180, fill=(16, 37, 30), border=COLOR_ACCENT_GREEN, radius=14)
        draw.text((870, 770), "FINAL UNIQUE SOLUTION VECTOR [ X ]:", font=FONTS["title_sm"], fill=COLOR_ACCENT_GREEN)
        sol_text = "[ x,  y,  z ]T  =  [ 1,  2,  3 ]T"
        draw.text((870, 815), sol_text, font=FONTS["mono_xl"], fill=COLOR_TEXT_PRIMARY)

        draw.text((870, 880), "VERIFICATION: 1+2+3=6 ok   |   2(1)+3(2)+1(3)=11 ok   |   1(1)-1(2)+2(3)=5 ok", font=FONTS["mono_sm"], fill=COLOR_ACCENT_GREEN)

def render_scene_6(draw, t_local):
    draw.text((100, 100), "CHAPTER 6: SYSTEM CLASSIFICATION & SPECIAL CASES", font=FONTS["title_lg"], fill=COLOR_TEXT_PRIMARY)
    draw.text((100, 155), "Gaussian Elimination naturally reveals the exact geometric nature of any system", font=FONTS["body_lg"], fill=COLOR_ACCENT_CYAN)

    cases = [
        {
            "tag": "CASE 1 (MOST COMMON)",
            "title": "EXACTLY ONE UNIQUE SOLUTION",
            "subtitle": "Consistent & Independent",
            "color": COLOR_ACCENT_GREEN,
            "matrix_sample": "[ 1  *  * | * ]\n[ 0  1  * | * ]\n[ 0  0  1 | * ]",
            "feature": "* Full Rank: Every variable has a pivot.",
            "geom": "* 3 planes intersect at a single point (x,y,z).",
            "conclusion": "Unique numerical answer found!"
        },
        {
            "tag": "CASE 2 (REDUNDANCY)",
            "title": "INFINITELY MANY SOLUTIONS",
            "subtitle": "Consistent & Dependent",
            "color": COLOR_ACCENT_GOLD,
            "matrix_sample": "[ 1  *  * | * ]\n[ 0  1  * | * ]\n[ 0  0  0 | 0 ] <-- 0 = 0",
            "feature": "* Row of all zeros appears: 0 = 0 (always true!).",
            "geom": "* Free variable exists (e.g. z = t).",
            "conclusion": "Planes intersect along a line or whole plane!"
        },
        {
            "tag": "CASE 3 (CONTRADICTION)",
            "title": "NO SOLUTION AT ALL",
            "subtitle": "Inconsistent System",
            "color": COLOR_ACCENT_ROSE,
            "matrix_sample": "[ 1  *  * | * ]\n[ 0  1  * | * ]\n[ 0  0  0 | k ] <-- 0 = k != 0",
            "feature": "* Contradiction row: 0x + 0y + 0z = 5 (impossible!).",
            "geom": "* Parallel or non-intersecting planes.",
            "conclusion": "The system has NO simultaneous solution!"
        }
    ]

    for idx, c in enumerate(cases):
        card_t = clamp((t_local - idx * 3.0) / 1.5)
        card_alpha = ease_out_cubic(card_t)
        if card_alpha > 0:
            cx = 100 + idx * 580
            draw_card(draw, cx, 220, 560, 740, fill=(15, 23, 42), border=c["color"], radius=16)

            draw_pill(draw, cx + 24, 245, c["tag"], font=FONTS["mono_sm"], bg=(30, 41, 59), fg=c["color"])
            draw.text((cx + 24, 290), c["title"], font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)
            draw.text((cx + 24, 335), c["subtitle"], font=FONTS["body_md"], fill=c["color"])

            draw_card(draw, cx + 24, 380, 510, 160, fill=(11, 15, 25), border=(45, 59, 85), radius=10)
            draw.text((cx + 40, 400), c["matrix_sample"], font=FONTS["mono_lg"], fill=c["color"])

            draw.text((cx + 24, 570), c["feature"], font=FONTS["body_md"], fill=COLOR_TEXT_PRIMARY)
            draw.text((cx + 24, 620), c["geom"], font=FONTS["body_md"], fill=COLOR_TEXT_MUTED)

            draw_card(draw, cx + 24, 690, 510, 120, fill=(23, 33, 56), border=c["color"], radius=12)
            draw.text((cx + 40, 715), "DIAGNOSIS:", font=FONTS["mono_sm"], fill=c["color"])
            draw.text((cx + 40, 745), c["conclusion"], font=FONTS["body_lg"], fill=COLOR_TEXT_PRIMARY)

def render_scene_7(draw, t_local):
    draw.text((100, 100), "CHAPTER 7: GAUSS-JORDAN & REAL-WORLD IMPACT", font=FONTS["title_lg"], fill=COLOR_TEXT_PRIMARY)
    draw.text((100, 155), "From textbooks to modern supercomputers: the enduring power of elimination", font=FONTS["body_lg"], fill=COLOR_ACCENT_GOLD)

    draw_card(draw, 100, 220, 840, 450, fill=(15, 23, 42), border=COLOR_ACCENT_CYAN, radius=16)
    draw_pill(draw, 130, 245, "STANDARD GAUSSIAN ELIMINATION", font=FONTS["mono_sm"], bg=(23, 33, 56), fg=COLOR_ACCENT_CYAN)
    draw.text((130, 290), "Forward Elimination + Back-Substitution", font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)
    draw.text((130, 335), "* Reaches Row Echelon Form (REF) / Upper Triangular Matrix.", font=FONTS["body_md"], fill=COLOR_TEXT_MUTED)
    draw.text((130, 375), "* Computational Complexity: ~ (2/3) n3 floating point operations.", font=FONTS["body_md"], fill=COLOR_ACCENT_GREEN)
    draw.text((130, 415), "* Industry Standard: Faster and uses less memory in numerical libraries.", font=FONTS["body_md"], fill=COLOR_TEXT_PRIMARY)

    draw_card(draw, 980, 220, 840, 450, fill=(15, 23, 42), border=COLOR_ACCENT_PURPLE, radius=16)
    draw_pill(draw, 1010, 245, "GAUSS-JORDAN ELIMINATION", font=FONTS["mono_sm"], bg=(35, 25, 55), fg=COLOR_ACCENT_PURPLE)
    draw.text((1010, 290), "Full Elimination Above AND Below Pivots", font=FONTS["title_sm"], fill=COLOR_TEXT_PRIMARY)
    draw.text((1010, 335), "* Reaches Reduced Row Echelon Form (RREF) / Identity Matrix [ I | x ].", font=FONTS["body_md"], fill=COLOR_TEXT_MUTED)
    draw.text((1010, 375), "* Computational Complexity: ~ n3 operations (requires 50% more work!).", font=FONTS["body_md"], fill=COLOR_ACCENT_GOLD)
    draw.text((1010, 415), "* Benefit: Solutions read directly off the matrix with NO back-substitution.", font=FONTS["body_md"], fill=COLOR_TEXT_PRIMARY)

    draw_card(draw, 100, 700, 1720, 260, fill=(15, 23, 42), border=COLOR_ACCENT_GREEN, radius=16)
    draw.text((130, 725), "WHERE GAUSSIAN ELIMINATION POWERS THE WORLD:", font=FONTS["title_sm"], fill=COLOR_ACCENT_GREEN)

    apps = [
        ("3D GRAPHICS", "Perspective projection matrices,\nlighting shaders & 3D camera transforms.", COLOR_ACCENT_CYAN),
        ("GPS POSITIONING", "Solving non-linear satellite sphere\nequations to calculate exact coordinates.", COLOR_ACCENT_GOLD),
        ("CIRCUIT ANALYSIS", "Kirchhoff's current & voltage laws\nfor massive electronic chip designs.", COLOR_ACCENT_PURPLE),
        ("MACHINE LEARNING", "Ordinary least squares regression,\nnormal equations & linear classifiers.", COLOR_ACCENT_GREEN),
    ]
    for a_idx, (a_name, a_desc, a_col) in enumerate(apps):
        ax = 130 + a_idx * 415
        draw_card(draw, ax, 770, 395, 160, fill=(23, 33, 56), border=a_col, radius=12)
        draw.text((ax + 16, 785), a_name, font=FONTS["mono_sm"], fill=a_col)
        draw.text((ax + 16, 825), a_desc, font=FONTS["body_sm"], fill=COLOR_TEXT_MUTED)

def render_frame(frame_idx):
    t = frame_idx / FPS

    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    draw_background_grid(draw)

    chap_idx = 0
    for idx, ch in enumerate(CHAPTERS):
        if ch["start"] <= t <= ch["end"]:
            chap_idx = idx
            break
    ch_info = CHAPTERS[chap_idx]
    t_local = t - ch_info["start"]

    if chap_idx == 0:
        render_scene_1(draw, t_local)
    elif chap_idx == 1:
        render_scene_2(draw, t_local)
    elif chap_idx == 2:
        render_scene_3(draw, t_local)
    elif chap_idx == 3:
        render_scene_4(draw, t_local)
    elif chap_idx == 4:
        render_scene_5(draw, t_local)
    elif chap_idx == 5:
        render_scene_6(draw, t_local)
    elif chap_idx == 6:
        render_scene_7(draw, t_local)

    draw_header(draw, chap_idx, ch_info["name"], ch_info["badge"])
    draw_footer_progress(draw, t, TOTAL_DURATION)

    return img

def main():
    print(f"rendering {TOTAL_FRAMES} frames ({TOTAL_DURATION}s) to {OUTPUT_FILENAME}...")

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "18",
        "-movflags", "+faststart",
        OUTPUT_FILENAME
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    start_time = time.time()
    report_interval = 240

    try:
        for f in range(TOTAL_FRAMES):
            frame_img = render_frame(f)
            proc.stdin.write(frame_img.tobytes())

            if (f + 1) % report_interval == 0 or f == TOTAL_FRAMES - 1:
                pct = ((f + 1) / TOTAL_FRAMES) * 100.0
                fps_render = (f + 1) / max(0.001, time.time() - start_time)
                print(f"progress: frame {f+1}/{TOTAL_FRAMES} ({pct:.1f}%) @ {fps_render:.1f} fps")

    except (KeyboardInterrupt, BrokenPipeError) as e:
        print(f"error: {e}")
    finally:
        proc.stdin.close()
        stderr_output = proc.stderr.read()
        proc.wait()

    if proc.returncode == 0:
        elapsed = time.time() - start_time
        mb = os.path.getsize(OUTPUT_FILENAME) / (1024 * 1024)
        print(f"done! saved {OUTPUT_FILENAME} ({mb:.2f} MB) in {elapsed:.1f}s")
    else:
        print(f"ffmpeg error (exit code {proc.returncode}):")
        print(stderr_output.decode("utf-8", errors="ignore"))
        sys.exit(1)

if __name__ == "__main__":
    main()
