"""
Genere les 78 images PNG pour les emojis custom Motdle.
26 lettres x 3 couleurs (vert, jaune, gris) = 78 fichiers.

Usage : uv run python scripts/generate_emojis.py
Les images sont sauvegardees dans le dossier emojis/.
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Couleurs du Wordle classique
COLORS = {
    "v": ("#538D4E", "vert"),
    "j": ("#B59F3B", "jaune"),
    "g": ("#3A3A3C", "gris"),
}

# Polices bold a essayer dans l'ordre
FONT_PATHS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

IMG_SIZE = 64
FONT_SIZE = 40
CORNER_RADIUS = 8
OUTPUT_DIR = Path("emojis")


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_emoji(letter: str, color_key: str) -> Path:
    hex_color, _ = COLORS[color_key]
    r, g, b = hex_to_rgb(hex_color)

    img = Image.new("RGBA", (IMG_SIZE, IMG_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fond colore avec coins arrondis
    draw.rounded_rectangle(
        [0, 0, IMG_SIZE - 1, IMG_SIZE - 1],
        radius=CORNER_RADIUS,
        fill=(r, g, b, 255),
    )

    # Lettre blanche centree
    font = load_font(FONT_SIZE)
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (IMG_SIZE - text_w) / 2 - bbox[0]
    y = (IMG_SIZE - text_h) / 2 - bbox[1]
    draw.text((x, y), letter, font=font, fill=(255, 255, 255, 255))

    out_path = OUTPUT_DIR / f"{letter}_{color_key}.png"
    img.save(out_path, "PNG")
    return out_path


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    font = load_font(FONT_SIZE)
    font_path = getattr(font, "path", "defaut")
    print(f"Police utilisee : {font_path}")

    total = 0
    for color_key, (_, color_name) in COLORS.items():
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            generate_emoji(letter, color_key)
            total += 1

    print(f"{total} images generees dans '{OUTPUT_DIR}/'")
    print()
    print("Etape suivante :")
    print("  uv run python scripts/upload_emojis.py --guild VOTRE_GUILD_ID")


if __name__ == "__main__":
    main()
