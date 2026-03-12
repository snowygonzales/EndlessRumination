#!/usr/bin/env python3
"""
Enhance App Store screenshots with marketing headlines and polished backgrounds.
Reads raw simulator screenshots from docs/screenshots/{size}/store/,
outputs store-ready composites to docs/screenshots/{size}/enhanced/.

Usage:
    python3 scripts/enhance_screenshots.py                  # all screenshots, both sizes
    python3 scripts/enhance_screenshots.py --only 03        # single screenshot by prefix
    python3 scripts/enhance_screenshots.py --no-shadow      # skip drop shadow
    python3 scripts/enhance_screenshots.py --no-glow        # skip background glow
"""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------------------------
# Colors (from ERColors.swift)
# ---------------------------------------------------------------------------
BG_COLOR = (10, 10, 12)
PRIMARY_TEXT = (240, 236, 228)
SECONDARY_TEXT = (138, 134, 144)
GLOW_WARM = (232, 101, 58)
GLOW_PURPLE = (155, 109, 255)

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT_HEADLINE_PATH = "/System/Library/Fonts/NewYork.ttf"
FONT_SUBLINE_PATH = "/System/Library/Fonts/SFNS.ttf"
HEADLINE_SIZE = 72
SUBLINE_SIZE = 44

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
SIDE_PADDING = 60
HEADLINE_Y = 140
SUBLINE_GAP = 24
SCREENSHOT_Y = 530
CORNER_RADIUS = 40
SHADOW_BLUR = 20
SHADOW_OPACITY = 0.25
SHADOW_OFFSET_Y = 10

# ---------------------------------------------------------------------------
# Output sizes
# ---------------------------------------------------------------------------
SIZES = {
    "6.9-inch": (1320, 2868),
    "6.7-inch": (1284, 2778),
}

# ---------------------------------------------------------------------------
# Screenshot definitions
# ---------------------------------------------------------------------------
SCREENSHOTS = [
    {
        "file": "01_splash.png",
        "headline": "Scroll Your Worries",
        "subline": "A new kind of self-help",
    },
    {
        "file": "02_input.png",
        "headline": "Describe What's Heavy",
        "subline": "Get 5 fresh perspectives",
    },
    {
        "file": "03_takes_comedian.png",
        "headline": "Humor Cuts Through",
        "subline": "20 perspectives, one worry",
    },
    {
        "file": "04_takes_therapist.png",
        "headline": "Reframe the Thought",
        "subline": "Real techniques, real insight",
    },
    {
        "file": "05_takes_dog.png",
        "headline": "Even Your Dog Weighs In",
        "subline": None,
    },
    {
        "file": "06_shop.png",
        "headline": "Unlock Every Voice",
        "subline": "Historical figures, unique takes",
    },
]


# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------
def load_fonts(headline_size, subline_size):
    headline_font = ImageFont.truetype(FONT_HEADLINE_PATH, headline_size)
    headline_font.set_variation_by_name("Bold")
    subline_font = ImageFont.truetype(FONT_SUBLINE_PATH, subline_size)
    subline_font.set_variation_by_name("Medium")
    return headline_font, subline_font


# ---------------------------------------------------------------------------
# Background with optional glow
# ---------------------------------------------------------------------------
def create_background(width, height, glow=True):
    bg = Image.new("RGB", (width, height), BG_COLOR)
    if not glow:
        return bg

    # Subtle radial glow: warm-purple ellipse, heavily blurred, very low opacity
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    # Blend warm and purple for glow color
    glow_color = (
        (GLOW_WARM[0] + GLOW_PURPLE[0]) // 2,
        (GLOW_WARM[1] + GLOW_PURPLE[1]) // 2,
        (GLOW_WARM[2] + GLOW_PURPLE[2]) // 2,
        255,
    )

    # Large ellipse centered behind headline area
    cx, cy = width // 2, int(height * 0.2)
    rx, ry = int(width * 0.5), int(height * 0.12)
    glow_draw.ellipse(
        [cx - rx, cy - ry, cx + rx, cy + ry],
        fill=glow_color,
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=180))

    # Composite at low opacity
    bg_rgba = bg.convert("RGBA")
    blended = Image.blend(bg_rgba, Image.alpha_composite(bg_rgba, glow_layer), 0.04)
    return blended.convert("RGB")


# ---------------------------------------------------------------------------
# Rounded corners
# ---------------------------------------------------------------------------
def round_corners(image, radius):
    """Apply rounded corner mask to an RGBA image."""
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, image.width, image.height], radius=radius, fill=255)
    image.putalpha(mask)
    return image


# ---------------------------------------------------------------------------
# Drop shadow
# ---------------------------------------------------------------------------
def create_shadow(width, height, radius, blur_radius, opacity, offset_y):
    """Create a blurred shadow image slightly larger than the screenshot."""
    expand = blur_radius * 2
    shadow = Image.new(
        "RGBA",
        (width + expand * 2, height + expand * 2),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(shadow)
    alpha = int(255 * opacity)
    draw.rounded_rectangle(
        [expand, expand, expand + width, expand + height],
        radius=radius,
        fill=(0, 0, 0, alpha),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return shadow, expand


# ---------------------------------------------------------------------------
# Process one screenshot
# ---------------------------------------------------------------------------
def process_screenshot(defn, size_name, canvas_size, fonts, args, project_root):
    cw, ch = canvas_size
    headline_font, subline_font = fonts

    # Scale layout proportionally for different canvas sizes
    scale = cw / 1320.0
    side_pad = int(SIDE_PADDING * scale)
    headline_y = int(HEADLINE_Y * scale)
    subline_gap = int(SUBLINE_GAP * scale)
    screenshot_y = int(SCREENSHOT_Y * scale)
    corner_r = int(CORNER_RADIUS * scale)

    # Load raw screenshot
    input_dir = project_root / "docs" / "screenshots" / size_name / "store"
    input_path = input_dir / defn["file"]
    if not input_path.exists():
        print(f"  SKIP {defn['file']} (not found at {input_path})")
        return

    screenshot = Image.open(input_path).convert("RGBA")

    # Scale screenshot to fit within canvas minus padding
    target_w = cw - 2 * side_pad
    scale_factor = target_w / screenshot.width
    target_h = int(screenshot.height * scale_factor)
    screenshot = screenshot.resize((target_w, target_h), Image.LANCZOS)

    # Round corners
    screenshot = round_corners(screenshot, corner_r)

    # Create background
    canvas = create_background(cw, ch, glow=not args.no_glow).convert("RGBA")

    # Drop shadow
    if not args.no_shadow:
        shadow_img, expand = create_shadow(
            target_w, target_h, corner_r, SHADOW_BLUR, SHADOW_OPACITY, SHADOW_OFFSET_Y
        )
        shadow_x = side_pad - expand
        shadow_y = screenshot_y - expand + int(SHADOW_OFFSET_Y * scale)
        canvas.paste(
            shadow_img, (shadow_x, shadow_y), shadow_img
        )

    # Paste screenshot
    canvas.paste(screenshot, (side_pad, screenshot_y), screenshot)

    # Draw text
    draw = ImageDraw.Draw(canvas)

    # Headline -- centered
    draw.text(
        (cw // 2, headline_y),
        defn["headline"],
        font=headline_font,
        fill=PRIMARY_TEXT,
        anchor="mt",
    )

    # Subline -- centered below headline
    if defn.get("subline"):
        bbox = headline_font.getbbox(defn["headline"])
        text_height = bbox[3] - bbox[1]
        subline_y = headline_y + text_height + subline_gap
        draw.text(
            (cw // 2, subline_y),
            defn["subline"],
            font=subline_font,
            fill=SECONDARY_TEXT,
            anchor="mt",
        )

    # Save
    output_dir = project_root / "docs" / "screenshots" / size_name / "enhanced"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / defn["file"]
    canvas.convert("RGB").save(output_path, "PNG", optimize=True)
    print(f"  {output_path.relative_to(project_root)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Enhance App Store screenshots")
    parser.add_argument("--only", help="Process only screenshots matching this prefix")
    parser.add_argument("--no-shadow", action="store_true", help="Skip drop shadow")
    parser.add_argument("--no-glow", action="store_true", help="Skip background glow")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    # Filter screenshots if --only specified
    screenshots = SCREENSHOTS
    if args.only:
        screenshots = [s for s in screenshots if s["file"].startswith(args.only)]
        if not screenshots:
            print(f"No screenshots matching prefix '{args.only}'")
            return

    for size_name, canvas_size in SIZES.items():
        print(f"\n{size_name} ({canvas_size[0]}x{canvas_size[1]}):")

        # Scale font sizes proportionally
        scale = canvas_size[0] / 1320.0
        h_size = int(HEADLINE_SIZE * scale)
        s_size = int(SUBLINE_SIZE * scale)
        fonts = load_fonts(h_size, s_size)

        for defn in screenshots:
            process_screenshot(defn, size_name, canvas_size, fonts, args, project_root)

    print("\nDone.")


if __name__ == "__main__":
    main()
