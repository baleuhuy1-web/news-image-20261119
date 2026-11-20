#!/usr/bin/env python3
"""Render entry.png: a newspaper front page for Thursday 19 November 2026.

Six illustrated panels sit in assets/.  This script lays them out in a
two-by-three grid on a cream newsprint sheet and draws all lettering with
PIL, so the picture model never has to render words (it would garble them).
The finished page is written to entry.png beside this script: exactly
1024x1024 pixels and inside the competition's 1 MiB size limit.
"""

import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE = os.path.dirname(os.path.abspath(__file__))
PANEL_DIR = os.path.join(BASE, "assets")
TARGET = os.path.join(BASE, "entry.png")
BYTE_LIMIT = 1_048_576

PAGE = 1024
EDGE = 28
GAP = 16
NEWS = (247, 242, 231)
DARK = (22, 20, 18)
MID = (74, 70, 64)
RED = (178, 24, 43)
SNOW = (255, 255, 255)
SOOT = (17, 17, 17)

FONTS = "/usr/share/fonts/truetype/dejavu"
SERIF = os.path.join(FONTS, "DejaVuSerif-Bold.ttf")
SANS_B = os.path.join(FONTS, "DejaVuSans-Bold.ttf")
SANS_R = os.path.join(FONTS, "DejaVuSans.ttf")

# (panel file, headline, subline, crop anchor 0.0=top .. 1.0=bottom)
STORIES = [
    ("panel1.png", "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
     "First-ever three-way summit ends with pledge that a nuclear war "
     "cannot be won", 0.45),
    ("panel2.png", "GTA VI IS OUT",
     "Rockstar's epic launches at midnight after a 13-year wait", 0.55),
    ("panel3.png", "COURT: MYANMAR COMMITTED GENOCIDE",
     "Top UN court rules against Myanmar over the Rohingya; verdict "
     "cannot be appealed", 0.50),
    ("panel4.png", "IRAN WIDENS WAR TO GULF STATES",
     "Tehran hits Gulf targets and tankers after US strikes on "
     "Qeshm island", 0.50),
    ("panel5.png", "EU PROPOSES €45BN LOAN FOR UKRAINE",
     "Brussels unveils joint-debt package as fighting intensifies on "
     "the eastern front", 0.50),
    ("panel6.png", "COP31 DRAFT DROPS FOSSIL FUELS",
     "Outcry as latest climate deal text in Antalya omits the phase-out",
     0.50),
]

TICKER = [
    "ANTHROPIC'S RECORD IPO HITS NASDAQ • FIJI AND TONGA DECLARE "
    "EL NIÑO EMERGENCIES",
    "ISRAEL COMPLETES GAZA OPERATION BEYOND 'YELLOW LINE'",
]


def font(path, size):
    return ImageFont.truetype(path, size)


def shrink_to_fit(draw, words, path, width, top_size, floor=12):
    """Biggest size (no larger than top_size) that keeps words on one line."""
    size = top_size
    while size > floor:
        face = font(path, size)
        if draw.textlength(words, font=face) <= width:
            return face
        size -= 1
    return font(path, floor)


def split_lines(draw, words, face, width):
    """Greedy wrap of words into lines no wider than width."""
    lines, line = [], ""
    for word in words.split():
        candidate = (line + " " + word).strip()
        if draw.textlength(candidate, font=face) <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def centred(draw, middle_x, top, words, face, colour):
    span = draw.textlength(words, font=face)
    draw.text((middle_x - span / 2, top), words, font=face, fill=colour)


def compose():
    sheet = Image.new("RGB", (PAGE, PAGE), NEWS)
    pen = ImageDraw.Draw(sheet)
    span = PAGE - 2 * EDGE
    middle = PAGE // 2

    # ---- masthead ------------------------------------------------------
    top = 18
    pen.rectangle([EDGE, top, PAGE - EDGE, top + 5], fill=DARK)
    top += 9
    pen.rectangle([EDGE, top, PAGE - EDGE, top + 2], fill=DARK)
    top += 12
    title_face = shrink_to_fit(pen, "THE WORLD TODAY", SERIF, span, 112)
    box = pen.textbbox((0, 0), "THE WORLD TODAY", font=title_face)
    centred(pen, middle, top - box[1], "THE WORLD TODAY", title_face, DARK)
    top += (box[3] - box[1]) + 12

    ribbon_h = 46
    pen.rectangle([EDGE, top, PAGE - EDGE, top + ribbon_h], fill=RED)
    day = "THURSDAY 19 NOVEMBER 2026"
    day_face = shrink_to_fit(pen, day, SANS_B, span - 40, 28)
    dbox = pen.textbbox((0, 0), day, font=day_face)
    day_top = top + (ribbon_h - (dbox[3] - dbox[1])) // 2 - dbox[1]
    centred(pen, middle, day_top, day, day_face, SNOW)
    top += ribbon_h + 8
    pen.rectangle([EDGE, top, PAGE - EDGE, top + 2], fill=DARK)
    grid_start = top + 14

    # ---- story grid ----------------------------------------------------
    strip_h = 68
    grid_end = PAGE - strip_h - 12
    col_w = (span - GAP) // 2
    row_h = (grid_end - grid_start) // 3

    head_face = font(SANS_B, 23)
    sub_face = font(SANS_R, 16)
    head_step, sub_step, head_sub_gap = 27, 20, 4

    for row in range(3):
        pair = STORIES[row * 2: row * 2 + 2]
        # Wrap every caption first so both pictures in the row share a
        # height and their headlines line up.
        captions = []
        tallest = 0
        for _, headline, subline, _ in pair:
            heads = split_lines(pen, headline, head_face, col_w)
            subs = split_lines(pen, subline, sub_face, col_w)
            captions.append((heads, subs))
            height = (len(heads) * head_step + head_sub_gap
                      + len(subs) * sub_step)
            tallest = max(tallest, height)
        pic_h = row_h - tallest - 8
        row_top = grid_start + row * row_h

        for col, (story, (heads, subs)) in enumerate(zip(pair, captions)):
            name, _, _, anchor = story
            left = EDGE + col * (col_w + GAP)
            picture = Image.open(os.path.join(PANEL_DIR, name)).convert("RGB")
            picture = ImageOps.fit(picture, (col_w, pic_h),
                                   method=Image.LANCZOS,
                                   centering=(0.5, anchor))
            sheet.paste(picture, (left, row_top))
            pen.rectangle([left, row_top, left + col_w - 1,
                           row_top + pic_h - 1], outline=DARK, width=2)
            cursor = row_top + pic_h + 6
            for line in heads:
                pen.text((left, cursor), line, font=head_face, fill=DARK)
                cursor += head_step
            cursor += head_sub_gap
            for line in subs:
                pen.text((left, cursor), line, font=sub_face, fill=MID)
                cursor += sub_step

    # ---- ticker strip --------------------------------------------------
    strip_top = PAGE - strip_h
    pen.rectangle([0, strip_top, PAGE, PAGE], fill=SOOT)
    step = 27
    cursor = strip_top + (strip_h - step * len(TICKER)) // 2
    for line in TICKER:
        # Long ticker lines must shrink to fit the page instead of
        # running off its edges.
        tick_face = shrink_to_fit(pen, line, SANS_B, PAGE - 32, 20)
        centred(pen, middle, cursor, line, tick_face, SNOW)
        cursor += step

    # ---- save, keeping under the 1 MiB ceiling -------------------------
    sheet.save(TARGET, optimize=True)
    size = os.path.getsize(TARGET)
    if size > BYTE_LIMIT:
        flat = sheet.quantize(colors=256, method=Image.MEDIANCUT)
        flat.save(TARGET, optimize=True)
        size = os.path.getsize(TARGET)
    print(f"entry.png: {sheet.size[0]}x{sheet.size[1]}, {size} bytes")
    return size


if __name__ == "__main__":
    compose()
