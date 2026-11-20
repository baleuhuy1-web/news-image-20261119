#!/usr/bin/env python3
"""Compose the front page for Thursday 19 November 2026 and save entry.png.

Everything on the page is drawn by this script: masthead, date band, six
story panels with headlines and sublines, and the ticker footer.
Only Pillow is used; the story panels come from the local assets folder.
"""

import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

PAGE = 1024
MARGIN = 28
GUTTER = 16
PAPER = (247, 242, 231)
INK = (0, 0, 0)
CRIMSON = (178, 24, 43)
GREY = (90, 90, 90)
WHITE = (255, 255, 255)
BYTE_LIMIT = 1_048_576

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

HERE = os.path.dirname(os.path.abspath(__file__))

STORIES = [
    (
        "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
        "First-ever three-way summit ends with pledge that a nuclear war cannot be won",
    ),
    (
        "GTA VI IS OUT",
        "Rockstar's epic launches at midnight after a 13-year wait",
    ),
    (
        "COURT: MYANMAR COMMITTED GENOCIDE",
        "Top UN court rules against Myanmar over the Rohingya; verdict cannot be appealed",
    ),
    (
        "IRAN WIDENS WAR TO GULF STATES",
        "Tehran hits Gulf targets and tankers after US strikes on Qeshm island",
    ),
    (
        "EU PROPOSES \u20ac45BN LOAN FOR UKRAINE",
        "Brussels unveils joint-debt package as fighting intensifies on the eastern front",
    ),
    (
        "COP31 DRAFT DROPS FOSSIL FUELS",
        "Outcry as latest climate deal text in Antalya omits the phase-out",
    ),
]

TICKER = [
    "ANTHROPIC'S RECORD IPO HITS NASDAQ \u2022 FIJI AND TONGA DECLARE EL NI\u00d1O EMERGENCIES",
    "ISRAEL COMPLETES GAZA OPERATION BEYOND 'YELLOW LINE'",
]


def load(path, size):
    return ImageFont.truetype(path, size)


def shrink_to_fit(canvas, text, path, start_size, max_width):
    """Largest font size at which the text fits inside max_width."""
    size = start_size
    while size > 8:
        candidate = load(path, size)
        if canvas.textlength(text, font=candidate) <= max_width:
            return candidate
        size -= 1
    return load(path, 8)


def wrap_text(canvas, text, face, max_width):
    """Greedy word wrap measured with the real font."""
    lines = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if not current or canvas.textlength(trial, font=face) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def block_height(face, line_count, leading):
    ascent, descent = face.getmetrics()
    return line_count * (ascent + descent + leading) - leading


def main():
    sheet = Image.new("RGB", (PAGE, PAGE), PAPER)
    canvas = ImageDraw.Draw(sheet)
    content_w = PAGE - 2 * MARGIN
    col_w = (content_w - GUTTER) // 2

    # --- Top rules and masthead -------------------------------------------
    y = MARGIN
    canvas.rectangle([MARGIN, y, PAGE - MARGIN, y + 3], fill=INK)
    y += 11
    masthead = shrink_to_fit(canvas, "THE WORLD TODAY", SERIF_BOLD, 118, content_w)
    ascent, descent = masthead.getmetrics()
    canvas.text((PAGE // 2, y), "THE WORLD TODAY", font=masthead, fill=INK, anchor="ma")
    y += ascent + descent + 8
    canvas.rectangle([MARGIN, y, PAGE - MARGIN, y + 3], fill=INK)
    y += 13

    # --- Crimson date band --------------------------------------------------
    canvas.rectangle([MARGIN, y, PAGE - MARGIN, y + 46], fill=CRIMSON)
    date_face = load(SANS_BOLD, 24)
    canvas.text(
        (PAGE // 2, y + 23),
        "THURSDAY 19 NOVEMBER 2026",
        font=date_face,
        fill=WHITE,
        anchor="mm",
    )
    y += 46 + 12
    grid_top = y

    # --- Footer geometry (computed first so the grid can fill the rest) ----
    ticker_face = load(SANS_BOLD, 20)
    for line in TICKER:
        while (
            ticker_face.size > 8
            and canvas.textlength(line, font=ticker_face) > content_w - 16
        ):
            ticker_face = load(SANS_BOLD, ticker_face.size - 1)
    t_ascent, t_descent = ticker_face.getmetrics()
    ticker_line_h = t_ascent + t_descent + 4
    footer_h = 2 * ticker_line_h + 16
    footer_top = PAGE - MARGIN - footer_h

    # --- Story text layout ---------------------------------------------------
    head_face = load(SANS_BOLD, 23)
    sub_face = load(SANS, 16)
    laid_out = []
    for headline, subline in STORIES:
        head_lines = wrap_text(canvas, headline, head_face, col_w)
        sub_lines = wrap_text(canvas, subline, sub_face, col_w)
        laid_out.append((head_lines, sub_lines))
    tallest_text = 0
    for head_lines, sub_lines in laid_out:
        block = (
            block_height(head_face, len(head_lines), 3)
            + 4
            + block_height(sub_face, len(sub_lines), 2)
        )
        tallest_text = max(tallest_text, block)

    row_h = (footer_top - 12 - grid_top) // 3
    panel_h = row_h - tallest_text - 10
    if panel_h < 80:
        panel_h = 80

    # --- Grid of panels ------------------------------------------------------
    for index, ((head_lines, sub_lines)) in enumerate(laid_out):
        row, col = divmod(index, 2)
        cell_x = MARGIN + col * (col_w + GUTTER)
        cell_y = grid_top + row * row_h

        panel_path = os.path.join(HERE, "assets", f"panel{index + 1}.png")
        with Image.open(panel_path) as raw:
            panel = ImageOps.fit(raw.convert("RGB"), (col_w, panel_h), Image.LANCZOS)
        sheet.paste(panel, (cell_x, cell_y))
        canvas.rectangle(
            [cell_x, cell_y, cell_x + col_w - 1, cell_y + panel_h - 1],
            outline=INK,
            width=2,
        )

        text_y = cell_y + panel_h + 6
        for line in head_lines:
            canvas.text((cell_x, text_y), line, font=head_face, fill=INK)
            text_y += head_face.getmetrics()[0] + head_face.getmetrics()[1] + 3
        text_y += 4
        for line in sub_lines:
            canvas.text((cell_x, text_y), line, font=sub_face, fill=GREY)
            text_y += sub_face.getmetrics()[0] + sub_face.getmetrics()[1] + 2

    # --- Black ticker footer ---------------------------------------------------
    canvas.rectangle(
        [MARGIN, footer_top, PAGE - MARGIN, footer_top + footer_h], fill=INK
    )
    line_y = footer_top + 8 + t_ascent
    for line in TICKER:
        canvas.text((PAGE // 2, line_y), line, font=ticker_face, fill=WHITE, anchor="ma")
        line_y += ticker_line_h

    out_path = os.path.join(HERE, "entry.png")
    sheet.save(out_path, "PNG")
    size = os.path.getsize(out_path)
    if size > BYTE_LIMIT:
        sheet.convert("P", palette=Image.ADAPTIVE, colors=256).convert("RGB").save(
            out_path, "PNG"
        )
        size = os.path.getsize(out_path)
    print(f"entry.png: {sheet.size[0]}x{sheet.size[1]}, {size} bytes")


if __name__ == "__main__":
    main()
