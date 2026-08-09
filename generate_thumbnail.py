"""Generate YouTube thumbnail with proper Pillow text rendering."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os


def create_thumbnail(path="static/thumbnail.png"):
    W, H = 1280, 720
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # ── Background: dark radial gradient ──
    cx, cy = W * 0.5, H * 0.32
    for y in range(H):
        for x in range(0, W, 4):  # step by 4 for speed
            dx = (x - cx) / (W * 0.55)
            dy = (y - cy) / (H * 0.55)
            dist = min(1.0, (dx * dx + dy * dy) ** 0.5)
            r = int(18 + 28 * (1 - dist))
            g = int(14 + 22 * (1 - dist))
            b = int(20 + 32 * (1 - dist))
            for ox in range(4):
                if x + ox < W:
                    img.putpixel((x + ox, y), (r, g, b, 255))

    # ── Gold spotlight glow ──
    for y in range(H):
        for x in range(0, W, 8):
            dx = (x - cx) / (W * 0.35)
            dy = (y - cy) / (H * 0.30)
            dist = dx * dx + dy * dy
            if dist < 1.0:
                alpha = int(40 * (1 - dist) ** 2)
                for ox in range(8):
                    if x + ox < W:
                        px = img.getpixel((x + ox, y))
                        r2 = min(255, px[0] + alpha)
                        g2 = min(255, px[1] + int(alpha * 0.75))
                        b2 = min(255, px[2] + int(alpha * 0.1))
                        img.putpixel((x + ox, y), (r2, g2, b2, 255))

    # ── Piano keys at bottom ──
    key_area_y = int(H * 0.66)
    key_height = H - key_area_y
    num_white_keys = 14
    white_w = W / num_white_keys
    for i in range(num_white_keys):
        x0 = int(i * white_w)
        x1 = int((i + 1) * white_w)
        bright = 0.95 if i % 2 == 0 else 0.88
        r = int(245 * bright)
        g_val = int(241 * bright)
        b_val = int(232 * bright)
        for y in range(key_area_y, H):
            for x in range(x0, x1):
                if x < W:
                    img.putpixel((x, y), (r, g_val, b_val, 255))
        # Key separator line
        for y in range(key_area_y, H):
            if x0 < W:
                img.putpixel((x0, y), (180, 150, 70, 255))

    # Black keys
    black_h = int(key_height * 0.58)
    black_pattern = [1, 2, 4, 5, 6]  # C# D# F# G# A#
    for i in range(num_white_keys):
        if i % 7 in black_pattern:
            x0 = int(i * white_w)
            x1 = int(i * white_w + white_w * 0.55)
            for y in range(key_area_y, key_area_y + black_h):
                for x in range(x0, x1):
                    if x < W:
                        img.putpixel((x, y), (8, 6, 10, 255))

    # ── Floating gold particles ──
    particles = [
        (W * 0.15, H * 0.18, 10, 0.7),
        (W * 0.80, H * 0.14, 7, 0.55),
        (W * 0.87, H * 0.26, 5, 0.45),
        (W * 0.20, H * 0.28, 8, 0.6),
        (W * 0.72, H * 0.20, 4, 0.4),
        (W * 0.38, H * 0.10, 6, 0.5),
        (W * 0.55, H * 0.22, 3, 0.35),
        (W * 0.48, H * 0.08, 4, 0.3),
    ]
    for px, py, pr, alpha_max in particles:
        px, py, pr = int(px), int(py), int(pr)
        for y in range(max(0, py - pr), min(H, py + pr + 1)):
            for x in range(max(0, px - pr), min(W, px + pr + 1)):
                dist = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                if dist < pr:
                    alpha = (1 - dist / pr) * alpha_max
                    current = img.getpixel((x, y))
                    r2 = min(255, int(current[0] + 232 * alpha))
                    g2 = min(255, int(current[1] + 200 * alpha))
                    b2 = min(255, int(current[2] + 84 * alpha))
                    img.putpixel((x, y), (r2, g2, b2, 255))

    # ── Featherless badge (top-right) ──
    badge_x, badge_y = int(W * 0.64), int(H * 0.045)
    badge_w, badge_h = 300, 48
    badge_r = 24
    # Draw rounded rectangle
    for y in range(badge_y, badge_y + badge_h):
        for x in range(badge_x, badge_x + badge_w):
            # Check rounded corners
            inside = True
            if x < badge_x + badge_r and y < badge_y + badge_r:
                if (x - badge_x - badge_r) ** 2 + (y - badge_y - badge_r) ** 2 > badge_r ** 2:
                    inside = False
            if x > badge_x + badge_w - badge_r and y < badge_y + badge_r:
                if (x - badge_x - badge_w + badge_r) ** 2 + (y - badge_y - badge_r) ** 2 > badge_r ** 2:
                    inside = False
            if x < badge_x + badge_r and y > badge_y + badge_h - badge_r:
                if (x - badge_x - badge_r) ** 2 + (y - badge_y - badge_h + badge_r) ** 2 > badge_r ** 2:
                    inside = False
            if x > badge_x + badge_w - badge_r and y > badge_y + badge_h - badge_r:
                if (x - badge_x - badge_w + badge_r) ** 2 + (y - badge_y - badge_h + badge_r) ** 2 > badge_r ** 2:
                    inside = False
            if inside:
                # Border check
                border = 2
                in_border = (
                    x < badge_x + border or x > badge_x + badge_w - border or
                    y < badge_y + border or y > badge_y + badge_h - border
                )
                if in_border:
                    img.putpixel((x, y), (200, 168, 78, 255))
                else:
                    img.putpixel((x, y), (16, 14, 20, 255))

    # Badge text
    try:
        badge_font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 16)
    except Exception:
        badge_font = ImageFont.load_default()
    badge_text = "🪶  FEATHERLESS AI  |  DEEPSEEK V3"
    draw.text((badge_x + 14, badge_y + 14), badge_text, fill=(232, 200, 84, 255), font=badge_font)

    # ── Main title "CADENCE" ──
    title_y = int(H * 0.34)
    try:
        title_font = ImageFont.truetype("C:\\Windows\\Fonts\\georgia.ttf", 110)
    except Exception:
        try:
            title_font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 100)
        except Exception:
            title_font = ImageFont.load_default()

    # Gold gradient text — draw with shadow first
    title = "Cadence"
    # Shadow
    shadow_bbox = draw.textbbox((0, 0), title, font=title_font)
    shadow_w = shadow_bbox[2] - shadow_bbox[0]
    shadow_x = (W - shadow_w) // 2
    draw.text((shadow_x + 3, title_y + 3), title, fill=(0, 0, 0, 180), font=title_font)
    # Gold text
    draw.text((shadow_x, title_y), title, fill=(232, 200, 84, 255), font=title_font)

    # ── Subtitle "AI PIANO COACH" ──
    sub_y = title_y + 130
    try:
        sub_font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 28)
    except Exception:
        sub_font = ImageFont.load_default()
    sub_text = "A I   P I A N O   C O A C H"
    sub_bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (W - sub_w) // 2
    draw.text((sub_x, sub_y), sub_text, fill=(200, 195, 185, 255), font=sub_font)

    # ── Iris Hacks IV tag ──
    tag_y = H - 45
    try:
        tag_font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 18)
    except Exception:
        tag_font = ImageFont.load_default()
    tag_text = "IRIS HACKS IV  •  2026  •  SOLO BUILD"
    tag_bbox = draw.textbbox((0, 0), tag_text, font=tag_font)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_x = (W - tag_w) // 2
    draw.text((tag_x, tag_y), tag_text, fill=(160, 155, 145, 255), font=tag_font)

    # ── Gold divider lines ──
    line_y1 = title_y - 15
    line_y2 = sub_y + 42
    for line_y in [line_y1, line_y2]:
        line_w = 300
        line_x0 = (W - line_w) // 2
        for y in range(line_y, line_y + 2):
            for x in range(line_x0, line_x0 + line_w):
                alpha = 1.0 - abs(x - (W // 2)) / (line_w // 2)
                alpha = max(0, alpha)
                r = int(200 * alpha)
                g = int(168 * alpha)
                b = int(78 * alpha)
                current = img.getpixel((x, y))
                r2 = min(255, current[0] + r)
                g2 = min(255, current[1] + g)
                b2 = min(255, current[2] + b)
                img.putpixel((x, y), (r2, g2, b2, 255))

    # ── Save ──
    # Convert to RGB for smaller file
    rgb_img = Image.new("RGB", (W, H), (10, 8, 12))
    rgb_img.paste(img, (0, 0), img)
    rgb_img.save(path, "PNG", optimize=True)
    size_kb = os.path.getsize(path) / 1024
    print(f"Thumbnail saved: {path} ({W}x{H}, {size_kb:.0f} KB)")


if __name__ == "__main__":
    create_thumbnail()
