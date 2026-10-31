#!/usr/bin/env python3
"""
CTF Image Blend Generator
Blends a transparent, high-visibility flag string onto a dark background image.
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def find_font(font_size: int, custom_font_path: str | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Find a suitable bold monospace or sans-serif font across Linux, Windows, macOS."""
    if custom_font_path and os.path.exists(custom_font_path):
        try:
            return ImageFont.truetype(custom_font_path, font_size)
        except Exception:
            pass

    candidate_paths = [
        # Linux standard font paths
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
        # Windows standard font paths
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/consolab.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        # macOS font paths
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
    ]

    for path in candidate_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue

    # Fallback to default
    try:
        return ImageFont.load_default(size=font_size)
    except TypeError:
        return ImageFont.load_default()


def find_default_input_image() -> str:
    """Detect the background image in the current directory."""
    priority_names = [
        "wallapper.jpg",
        "wallpaper.jpg",
        "wallapper.png",
        "wallpaper.png",
        "background.jpg",
        "background.png",
    ]
    for name in priority_names:
        if os.path.exists(name):
            return name

    # Fallback: first jpg or png file
    for file in Path(".").iterdir():
        if file.suffix.lower() in [".jpg", ".jpeg", ".png"] and file.name != "image.png":
            return str(file)

    raise FileNotFoundError("Could not find any background image in the workspace.")


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert hex string (e.g. #b4f0ff or b4f0ff) to RGB tuple."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join([c * 2 for c in hex_str])
    return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)


def blend_flag(
    flag_text: str,
    input_path: str,
    output_path: str = "image.png",
    opacity: float = 0.80,
    text_color_hex: str = "#B4F0FF",
    glow_color_hex: str = "#00D4FF",
    with_glow: bool = True,
    user_font_size: int | None = None,
    font_path: str | None = None,
) -> None:
    """Render the flag text with soft glow and semi-transparency over the background."""
    print(f"[*] Loading background image: {input_path}")
    base_image = Image.open(input_path).convert("RGBA")
    width, height = base_image.size
    print(f"[*] Canvas dimensions: {width}x{height}")

    # Determine font size if not provided
    # Keep flag width within ~85% of image width
    max_text_width = int(width * 0.85)
    if user_font_size:
        font_size = user_font_size
        font = find_font(font_size, font_path)
    else:
        # Start heuristic estimate
        approx_char_width = max_text_width / max(len(flag_text), 1)
        font_size = max(18, int(approx_char_width * 1.5))
        font = find_font(font_size, font_path)

        # Refine with text measurement
        temp_img = Image.new("RGBA", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), flag_text, font=font)
        rendered_width = bbox[2] - bbox[0]

        if rendered_width > max_text_width:
            scale_ratio = max_text_width / rendered_width
            font_size = max(18, int(font_size * scale_ratio))
            font = find_font(font_size, font_path)

    # Calculate final bounding box for centering
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), flag_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Center position (offset by bbox top/left for precise alignment)
    x = (width - text_w) // 2 - bbox[0]
    y = (height - text_h) // 2 - bbox[1]

    print(f"[*] Flag: '{flag_text}'")
    print(f"[*] Font size: {font_size}px, rendered text size: {text_w}x{text_h}")
    print(f"[*] Placement coordinates: ({x}, {y})")

    # Composite layers
    layers = [base_image]

    # 1. Subtle soft glow / back-shadow for high contrast against dark sand
    if with_glow:
        glow_rgb = hex_to_rgb(glow_color_hex)
        glow_alpha = int(95 * opacity)  # subtle ambient radiance
        glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        glow_draw.text((x, y), flag_text, font=font, fill=(*glow_rgb, glow_alpha))
        # Blur radius proportional to font size
        blur_radius = max(3, int(font_size * 0.08))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
        layers.append(glow_layer)

    # 2. Main text layer with specified opacity
    text_rgb = hex_to_rgb(text_color_hex)
    text_alpha = int(255 * max(0.0, min(1.0, opacity)))
    text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    text_draw.text((x, y), flag_text, font=font, fill=(*text_rgb, text_alpha))
    layers.append(text_layer)

    # Composite all layers together
    result = layers[0]
    for layer in layers[1:]:
        result = Image.alpha_composite(result, layer)

    # Save output (handling RGB for JPEGs and RGBA for PNGs)
    if output_path.lower().endswith((".jpg", ".jpeg")):
        result.convert("RGB").save(output_path, format="JPEG", quality=95)
    else:
        result.save(output_path, format="PNG")
    print(f"[+] Successfully generated blended image: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Blend CTF flag text onto background image.")
    parser.add_argument(
        "--flag", "-f",
        default=os.environ.get("FLAG", "CTF{sample_flag_default}"),
        help="Flag string to blend onto the image (defaults to $FLAG or sample flag)",
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        help="Path to input background image (defaults to wallapper.jpg in workspace)",
    )
    parser.add_argument(
        "--output", "-o",
        default="image.png",
        help="Path for output blended image (default: image.png)",
    )
    parser.add_argument(
        "--opacity",
        type=float,
        default=0.80,
        help="Opacity of the flag text from 0.0 (invisible) to 1.0 (fully opaque). Default: 0.80",
    )
    parser.add_argument(
        "--color",
        default="#B4F0FF",
        help="Hex color for the flag text (default: #B4F0FF ice-cyan for dark backgrounds)",
    )
    parser.add_argument(
        "--glow-color",
        default="#00D4FF",
        help="Hex color for subtle glow/accent (default: #00D4FF)",
    )
    parser.add_argument(
        "--no-glow",
        action="store_true",
        help="Disable soft glow effect",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=None,
        help="Optional explicit font size in pixels (default: auto-fit to image)",
    )
    parser.add_argument(
        "--font",
        default=None,
        help="Optional path to custom TTF/OTF font file",
    )

    args = parser.parse_args()

    input_img = args.input if args.input else find_default_input_image()
    blend_flag(
        flag_text=args.flag,
        input_path=input_img,
        output_path=args.output,
        opacity=args.opacity,
        text_color_hex=args.color,
        glow_color_hex=args.glow_color,
        with_glow=not args.no_glow,
        user_font_size=args.font_size,
        font_path=args.font,
    )


if __name__ == "__main__":
    main()
