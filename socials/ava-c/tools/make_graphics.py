#!/usr/bin/env python3
"""AVA C social graphics. Black + AVA yellow, Inter Display Black.

Usage:
  python3 make_graphics.py                      # rebuild the standard set into ../assets
  python3 make_graphics.py gameday "Orion A" "PÁ 4.12" "18:30" "AWAY"
  python3 make_graphics.py result "Orion A" "3:1" "W"      # W / L
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets"
LOGO = HERE / "ava_logo.png"
FONT_DIR = None  # resolved on first use

YELLOW = (253, 187, 39)
BLACK = (14, 14, 14)
WHITE = (245, 245, 240)
GREY = (120, 120, 115)

STORY = (1080, 1920)
POST = (1080, 1350)
SQUARE = (1080, 1080)



def _font_dir():
    """Inter Display lives in different places on Linux / the Mac (AVA Stats ships it)."""
    import os, glob
    cands = [os.environ.get("AVA_FONT_DIR", ""), "/usr/share/fonts/opentype/inter",
             str(Path.home() / "Library/Fonts"), "/Library/Fonts"]
    cands += glob.glob(str(Path.home() / "**/video/app/assets/fonts"), recursive=False)
    cands += glob.glob(str(Path.home() / "*/video/app/assets/fonts")) + glob.glob(str(Path.home() / "*/*/video/app/assets/fonts"))
    for c in cands:
        if c and Path(c, "InterDisplay-Black.otf").exists() or (c and Path(c, "InterDisplay-BlackItalic.otf").exists()):
            return Path(c)
    sys.exit("Inter Display font not found. Set AVA_FONT_DIR to a folder with InterDisplay-*.otf")


def font(size, weight="Black", italic=False):
    global FONT_DIR
    FONT_DIR = FONT_DIR or _font_dir()
    name = f"InterDisplay-{weight}{'Italic' if italic else ''}.otf"
    for n in (name, f"InterDisplay-{weight}Italic.otf", "InterDisplay-BlackItalic.otf", "InterDisplay-Black.otf"):
        if (FONT_DIR / n).exists():
            return ImageFont.truetype(str(FONT_DIR / n), size)
    raise FileNotFoundError(name)


def logo(size):
    return Image.open(LOGO).convert("RGBA").resize((size, size), Image.LANCZOS)


def text_c(d, y, s, f, fill, w):
    """Centered text; returns bottom y."""
    box = d.textbbox((0, 0), s, font=f)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.text(((w - tw) / 2 - box[0], y - box[1]), s, font=f, fill=fill)
    return y + th


def text_l(d, x, y, s, f, fill):
    box = d.textbbox((0, 0), s, font=f)
    d.text((x - box[0], y - box[1]), s, font=f, fill=fill)
    return y + (box[3] - box[1])


def fit(d, s, weight, max_w, start):
    size = start
    while size > 20:
        f = font(size, weight)
        b = d.textbbox((0, 0), s, font=f)
        if b[2] - b[0] <= max_w:
            return f
        size -= 4
    return font(size, weight)


def stripes(img, color, alpha=40):
    """Diagonal court-line texture."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = img.size
    for x in range(-h, w, 90):
        d.line([(x, h), (x + h, 0)], fill=color + (alpha,), width=14)
    img.alpha_composite(layer)


def save(img, name):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    img.convert("RGB").save(p, quality=95)
    print(p)


# ---------- assets ----------

def profile():
    img = Image.new("RGBA", SQUARE, BLACK + (255,))
    L = logo(760)
    img.alpha_composite(L, (150, 130))
    d = ImageDraw.Draw(img)
    # "C" badge bottom-right
    cx, cy, r = 770, 770, 130
    d.rounded_rectangle([cx - r - 22, cy - r - 22, cx + r + 22, cy + r + 22], radius=60, fill=BLACK)
    d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=44, fill=YELLOW)
    f = font(250)
    b = d.textbbox((0, 0), "C", font=f)
    d.text((cx - (b[2] - b[0]) / 2 - b[0], cy - (b[3] - b[1]) / 2 - b[1]), "C", font=f, fill=BLACK)
    save(img, "00_profile_picture.png")


def launch_carousel():
    W, H = POST
    # 1 — cover
    img = Image.new("RGBA", POST, YELLOW + (255,))
    stripes(img, BLACK, 22)
    d = ImageDraw.Draw(img)
    img.alpha_composite(logo(170), (70, 70))
    y = text_l(d, 70, 420, "AVA C", font(250), BLACK)
    y = text_l(d, 76, y + 50, "New account.", font(92, "Bold"), BLACK)
    y = text_l(d, 76, y + 22, "Same shanked passes.", font(92, "Bold"), BLACK)
    text_l(d, 76, H - 120, "PRAGUE MEN'S VOLLEYBALL  ·  SWIPE →", font(36, "Bold"), BLACK)
    save(img, "01_launch_1_cover.png")

    # 2 — what you get
    img = Image.new("RGBA", POST, BLACK + (255,))
    d = ImageDraw.Draw(img)
    text_l(d, 70, 90, "WHAT YOU'LL GET HERE", font(46, "Bold"), YELLOW)
    rows = [("HIGHLIGHTS", "the rallies we'll brag about"),
            ("LOWLIGHTS", "the ones we won't"),
            ("BENCH CAM", "us, losing it on the sideline"),
            ("BEHIND THE SCENES", "car rides, warm-ups, pivo")]
    y = 230
    for big, small in rows:
        f = fit(d, big, "Black", W - 140, 120)
        y = text_l(d, 70, y, big, f, WHITE)
        y = text_l(d, 74, y + 22, small, font(44, "Medium"), GREY) + 80
    save(img, "01_launch_2_what.png")

    # 3 — highlights vs lowlights
    img = Image.new("RGBA", POST, BLACK + (255,))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H // 2], fill=YELLOW)
    text_c(d, 170, "HIGHLIGHTS", font(150), BLACK, W)
    text_c(d, 390, "we're actually decent", font(52, "Bold"), BLACK, W)
    text_c(d, H // 2 + 170, "LOWLIGHTS", font(150), YELLOW, W)
    text_c(d, H // 2 + 390, "…sometimes", font(52, "Bold"), WHITE, W)
    save(img, "01_launch_3_both.png")

    # 4 — CTA
    img = Image.new("RGBA", POST, YELLOW + (255,))
    stripes(img, BLACK, 22)
    d = ImageDraw.Draw(img)
    img.alpha_composite(logo(330), ((W - 330) // 2, 170))
    y = text_c(d, 600, "FOLLOW FOR", font(110), BLACK, W)
    y = text_c(d, y + 30, "the good,", font(90, "Bold"), BLACK, W)
    y = text_c(d, y + 20, "the bad", font(90, "Bold"), BLACK, W)
    y = text_c(d, y + 20, "& the shanked.", font(90, "Bold"), BLACK, W)
    text_c(d, H - 130, "NEXT: FRI 4.12 vs ORION A", font(40, "Bold"), BLACK, W)
    save(img, "01_launch_4_follow.png")


def gameday(opp, day, time, ha, fname=None):
    W, H = STORY
    img = Image.new("RGBA", STORY, BLACK + (255,))
    stripes(img, YELLOW, 18)
    d = ImageDraw.Draw(img)
    img.alpha_composite(logo(220), ((W - 220) // 2, 200))
    y = text_c(d, 520, "GAME", font(270), YELLOW, W)
    y = text_c(d, y + 30, "DAY", font(270), YELLOW, W)
    y = text_c(d, y + 120, "AVA C", font(110), WHITE, W)
    y = text_c(d, y + 30, "vs", font(60, "Bold"), GREY, W)
    y = text_c(d, y + 30, opp.upper(), fit(d, opp.upper(), "Black", W - 120, 110), WHITE, W)
    # info bar
    d.rectangle([0, 1560, W, 1720], fill=YELLOW)
    text_c(d, 1605, f"{day}  ·  {time}  ·  {ha}", font(64, "Black"), BLACK, W)
    save(img, fname or f"gameday_{opp.lower().replace(' ', '_')}.png")


def result(opp, score, wl, fname=None):
    W, H = STORY
    win = wl.upper().startswith("W")
    bg, fg = (YELLOW, BLACK) if win else (BLACK, YELLOW)
    img = Image.new("RGBA", STORY, bg + (255,))
    stripes(img, fg, 18)
    d = ImageDraw.Draw(img)
    img.alpha_composite(logo(200), ((W - 200) // 2, 180))
    text_c(d, 470, "FULL TIME", font(90, "Bold"), fg, W)
    text_c(d, 640, score, font(400), fg, W)
    text_c(d, 1150, "AVA C", font(100), fg, W)
    text_c(d, 1290, "vs " + opp.upper(), fit(d, "vs " + opp.upper(), "Black", W - 120, 90), fg, W)
    tag = "WE TAKE IT." if win else "WE'LL BE BACK."
    text_c(d, 1560, tag, font(80, "Black", italic=True), fg, W)
    save(img, fname or f"result_{opp.lower().replace(' ', '_')}.png")


def overlay(label, fname, yellow_band=True):
    """Transparent 9:16 PNG with a top label, to drop on a Reel/TikTok in CapCut or the IG editor."""
    W, H = STORY
    img = Image.new("RGBA", STORY, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    band = YELLOW if yellow_band else BLACK
    txt = BLACK if yellow_band else YELLOW
    if label:
        d.rectangle([60, 250, W - 60, 400], fill=band + (255,))
        f = fit(d, label, "Black", W - 200, 96)
        b = d.textbbox((0, 0), label, font=f)
        d.text(((W - (b[2] - b[0])) / 2 - b[0], 325 - (b[3] - b[1]) / 2 - b[1]), label, font=f, fill=txt)
    L = logo(120)
    img.alpha_composite(L, (W - 200, H - 420))
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / fname)
    print(OUT / fname)


def overlay_landscape(label, fname):
    """Transparent 16:9 PNG: optional yellow label top-left, small logo bottom-right."""
    W, H = 1920, 1080
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if label:
        f = font(64)
        b = d.textbbox((0, 0), label, font=f)
        tw, th = b[2] - b[0], b[3] - b[1]
        y0 = H - 60 - (th + 50)  # bottom-left: the AVA Clips scoreboard sits at the top
        d.rectangle([60, y0, 60 + tw + 70, y0 + th + 50], fill=YELLOW + (255,))
        d.text((95 - b[0], y0 + 25 - b[1]), label, font=f, fill=BLACK)
    img.alpha_composite(logo(110), (W - 170, H - 170))
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / fname)
    print(OUT / fname)


def build_all():
    profile()
    launch_carousel()
    gameday("Orion A", "PÁ / FRI 4.12", "18:30", "AWAY", "02_gameday_orion_a.png")
    gameday("Prosek B", "PO / MON 7.12", "19:30", "AWAY", "03_gameday_prosek_b.png")
    result("Orion A", "3:1", "W", "example_result_win.png")
    result("Orion A", "1:3", "L", "example_result_loss.png")
    overlay("HIGHLIGHTS", "overlay_highlight.png", True)
    overlay("", "overlay_lowlight.png", False)  # lowlights: no label, only the funny text
    overlay_landscape("HIGHLIGHTS", "overlay_highlight_landscape.png")
    overlay_landscape("", "overlay_lowlight_landscape.png")
    overlay("BENCH CAM", "overlay_benchcam.png", True)
    overlay("PLAYER Qs", "overlay_player_qs.png", True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        build_all()
    elif a[0] == "gameday":
        gameday(a[1], a[2], a[3], a[4] if len(a) > 4 else "")
    elif a[0] == "result":
        result(a[1], a[2], a[3])
    else:
        print(__doc__)
