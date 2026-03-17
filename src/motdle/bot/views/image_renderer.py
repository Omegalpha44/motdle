"""
Rendu du plateau de jeu Motdle sous forme d'image PIL.
Retourne un tuple (discord.Embed, discord.File) pret a etre envoye.
"""

import io
from datetime import date
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageFont

from motdle.core.evaluator import LetterResult
from motdle.core.game import GameState, GameStatus

# ── Palette Wordle ──────────────────────────────────────────────────────────
BG            = (18, 18, 19)
TILE_BORDER   = (86, 87, 88)
TILE_ABSENT   = (58, 58, 60)
TILE_PRESENT  = (181, 159, 59)
TILE_CORRECT  = (83, 141, 78)
KEY_DEFAULT   = (129, 131, 132)
TEXT_COLOR    = (255, 255, 255)

TILE_COLORS = {
    LetterResult.CORRECT: TILE_CORRECT,
    LetterResult.PRESENT: TILE_PRESENT,
    LetterResult.ABSENT:  TILE_ABSENT,
}
KEY_COLORS = {
    LetterResult.CORRECT: TILE_CORRECT,
    LetterResult.PRESENT: TILE_PRESENT,
    LetterResult.ABSENT:  TILE_ABSENT,
}

AZERTY_ROWS = ["AZERTYUIOP", "QSDFGHJKLM", "WXCVBN"]

# ── Dimensions ───────────────────────────────────────────────────────────────
PADDING      = 20
TILE_SIZE    = 58
TILE_GAP     = 6
KEY_W        = 38
KEY_H        = 46
KEY_GAP      = 6
SECTION_GAP  = 20
CORNER_R     = 4

BOARD_W = 5 * TILE_SIZE + 4 * TILE_GAP   # 314
BOARD_H = 6 * TILE_SIZE + 5 * TILE_GAP   # 378
KBD_W   = 10 * KEY_W + 9 * KEY_GAP       # 434  (rangee la plus large)
KBD_H   = 3 * KEY_H  + 2 * KEY_GAP       # 150

IMG_W = KBD_W + 2 * PADDING              # 474
IMG_H = PADDING + BOARD_H + SECTION_GAP + KBD_H + PADDING  # 588

# Polices a essayer dans l'ordre
_FONT_PATHS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _center_text(draw, cx: float, cy: float, text: str, font, fill=None) -> None:
    """Dessine `text` centre autour du point (cx, cy)."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), text, font=font, fill=fill or TEXT_COLOR)


def _draw_tile(draw, x: int, y: int, letter: str | None, result: LetterResult | None, font) -> None:
    if result is None:
        # Tuile vide : fond transparent avec bordure
        draw.rounded_rectangle(
            [x, y, x + TILE_SIZE - 1, y + TILE_SIZE - 1],
            radius=CORNER_R,
            fill=BG,
            outline=TILE_BORDER,
            width=2,
        )
    else:
        draw.rounded_rectangle(
            [x, y, x + TILE_SIZE - 1, y + TILE_SIZE - 1],
            radius=CORNER_R,
            fill=TILE_COLORS[result],
        )
        if letter:
            _center_text(draw, x + TILE_SIZE / 2, y + TILE_SIZE / 2, letter, font)


def _draw_key(draw, x: int, y: int, letter: str, result: LetterResult | None, font) -> None:
    color = KEY_COLORS.get(result, KEY_DEFAULT)
    draw.rounded_rectangle(
        [x, y, x + KEY_W - 1, y + KEY_H - 1],
        radius=CORNER_R,
        fill=color,
    )
    _center_text(draw, x + KEY_W / 2, y + KEY_H / 2, letter, font)


def render_game_image(game: GameState) -> bytes:
    """Genere le plateau de jeu sous forme d'image PNG et retourne les octets."""
    img   = Image.new("RGB", (IMG_W, IMG_H), BG)
    draw  = ImageDraw.Draw(img)
    tile_font = _font(34)
    key_font  = _font(20)

    board_x = (IMG_W - BOARD_W) // 2
    board_y = PADDING

    # ── Grille ────────────────────────────────────────────────────────────────
    for row in range(6):
        for col in range(5):
            tx = board_x + col * (TILE_SIZE + TILE_GAP)
            ty = board_y + row * (TILE_SIZE + TILE_GAP)
            if row < len(game.guesses):
                g = game.guesses[row]
                _draw_tile(draw, tx, ty, g.word[col], g.letters[col], tile_font)
            else:
                _draw_tile(draw, tx, ty, None, None, tile_font)

    # ── Clavier AZERTY ────────────────────────────────────────────────────────
    kbd_y = board_y + BOARD_H + SECTION_GAP
    for row_idx, row_letters in enumerate(AZERTY_ROWS):
        row_w  = len(row_letters) * KEY_W + (len(row_letters) - 1) * KEY_GAP
        row_x  = (IMG_W - row_w) // 2
        row_y  = kbd_y + row_idx * (KEY_H + KEY_GAP)
        for col_idx, letter in enumerate(row_letters):
            kx = row_x + col_idx * (KEY_W + KEY_GAP)
            _draw_key(draw, kx, row_y, letter, game.keyboard.get(letter), key_font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()


def render_game(game: GameState) -> tuple[discord.Embed, discord.File]:
    """Retourne l'embed de statut + le fichier image pret a envoyer sur Discord."""
    status = game.status
    date_str   = game.date.strftime("%d/%m/%Y") if game.date else ""
    date_label = f" du {date_str}" if date_str else ""

    if status == GameStatus.WON:
        color       = discord.Color.green()
        title       = f"\u2705 Motdle{date_label} - Gagné !"
        description = f"Bravo ! Trouvé en **{len(game.guesses)}/{game.max_guesses}** essais."
    elif status == GameStatus.LOST:
        color       = discord.Color.red()
        title       = f"\u274c Motdle{date_label} - Perdu !"
        description = f"Le mot était : **{game.target}**"
    else:
        color       = discord.Color.blurple()
        title       = f"Motdle{date_label}"
        description = f"Essai {len(game.guesses) + 1}/{game.max_guesses}"

    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_image(url="attachment://motdle.png")
    if status == GameStatus.IN_PROGRESS:
        embed.set_footer(text="Cliquez 'Deviner' pour proposer un mot")

    image_bytes = render_game_image(game)
    file = discord.File(io.BytesIO(image_bytes), filename="motdle.png")
    return embed, file


# ── Comparaison quotidienne ──────────────────────────────────────────────────
MINI_TILE    = 20
MINI_GAP     = 3
MINI_CORNER  = 3
MINI_BOARD_W = 5 * MINI_TILE + 4 * MINI_GAP   # 112
MINI_BOARD_H = 6 * MINI_TILE + 5 * MINI_GAP   # 135

CARD_SIDE_PAD  = 10
CARD_TOP_PAD   = 10
CARD_BOT_PAD   = 10
NAME_H         = 22
NAME_BOT_GAP   = 8
GRID_BOT_GAP   = 6
STAT_H         = 18
CARD_W = CARD_SIDE_PAD + MINI_BOARD_W + CARD_SIDE_PAD                                         # 132
CARD_H = CARD_TOP_PAD + NAME_H + NAME_BOT_GAP + MINI_BOARD_H + GRID_BOT_GAP + STAT_H + CARD_BOT_PAD  # 209

CARD_COL_GAP = 14
CARD_ROW_GAP = 14
CMP_PADDING  = 22
MAX_CMP_COLS = 4

_GRID_COLOR_CODE = {'G': TILE_CORRECT, 'Y': TILE_PRESENT, 'B': TILE_ABSENT}
_STATUS_RED  = (197,  73,  61)
_CARD_BG     = ( 42,  44,  51)
_CARD_BORDER = ( 72,  74,  82)
_RANK_COLOR  = (160, 162, 170)
_EMPTY_TILE  = ( 55,  57,  65)
_EMPTY_BORDER= ( 90,  92, 100)


def _decode_grid(grid_str: str) -> list[tuple[str, str]]:
    """Decode 'CRANE:BABGG,ARBRE:GGGGG' -> [('CRANE','BABGG'), ('ARBRE','GGGGG')]"""
    if not grid_str:
        return []
    result = []
    for part in grid_str.split(','):
        if ':' in part:
            word, codes = part.split(':', 1)
            result.append((word.strip(), codes.strip()))
    return result


def _player_name(uid: int, guild: discord.Guild | None, max_len: int = 13, names: dict[int, str] | None = None) -> str:
    """Retourne le nom affichable d'un joueur."""
    name = None
    if names:
        name = names.get(uid)
    if name is None and guild:
        member = guild.get_member(uid)
        if member:
            name = member.display_name
    if name is None:
        name = f"#{str(uid)[-4:]}"
    if len(name) > max_len:
        name = name[: max_len - 1] + "\u2026"
    return name


def render_daily_comparison(
    today_results: list[dict],
    guild: discord.Guild | None,
    viewer_id: int,
    reveal: bool,
    today: date,
    names: dict[int, str] | None = None,
) -> tuple[discord.Embed, discord.File | None]:
    """Retourne l'embed de comparaison du jour.

    reveal=False : tuiles colorees sans lettres (silhouette).
    reveal=True  : tuiles avec lettres.
    """
    date_str = today.strftime("%d/%m/%Y")

    if not today_results:
        embed = discord.Embed(
            title=f"\U0001f4ca Comparaison du {date_str}",
            description="Personne n'a encore joué aujourd'hui !",
            color=discord.Color.blurple(),
        )
        return embed, None

    n    = len(today_results)
    cols = min(n, MAX_CMP_COLS)
    rows = (n + cols - 1) // cols

    title_h   = 32
    title_gap = 14

    img_w = CMP_PADDING + cols * CARD_W + (cols - 1) * CARD_COL_GAP + CMP_PADDING
    img_h = (
        CMP_PADDING + title_h + title_gap
        + rows * CARD_H + (rows - 1) * CARD_ROW_GAP
        + CMP_PADDING
    )

    img  = Image.new("RGB", (img_w, img_h), BG)
    draw = ImageDraw.Draw(img)

    title_font = _font(22)
    name_font  = _font(14)
    rank_font  = _font(12)
    stat_font  = _font(13)
    mini_font  = _font(11)

    _center_text(draw, img_w / 2, CMP_PADDING + title_h / 2, f"Comparaison du {date_str}", title_font)

    card_start_y = CMP_PADDING + title_h + title_gap

    for i, result in enumerate(today_results):
        r_row = i // cols
        r_col = i % cols

        cx = CMP_PADDING + r_col * (CARD_W + CARD_COL_GAP)
        cy = card_start_y + r_row * (CARD_H + CARD_ROW_GAP)

        uid       = result["user_id"]
        is_viewer = uid == viewer_id
        won       = bool(result["won"])
        attempts  = result["attempts"]
        guesses   = _decode_grid(result.get("grid", ""))

        # ── Fond de carte ─────────────────────────────────────────────────────
        border_color = TILE_CORRECT if is_viewer else _CARD_BORDER
        border_width = 2
        draw.rounded_rectangle(
            [cx, cy, cx + CARD_W - 1, cy + CARD_H - 1],
            radius=8,
            fill=_CARD_BG,
            outline=border_color,
            width=border_width,
        )

        # ── Ligne nom ─────────────────────────────────────────────────────────
        name = _player_name(uid, guild, names=names)
        name_y = cy + CARD_TOP_PAD + NAME_H / 2

        # Rang (gauche)
        rank_str = f"{i + 1}."
        draw.text(
            (cx + CARD_SIDE_PAD, name_y - 7),
            rank_str, font=rank_font, fill=_RANK_COLOR,
        )

        # Indicateur victoire/defaite (droite)
        if won:
            icon_str = f"\u2713 {attempts}/6"
            icon_color = TILE_CORRECT
        elif attempts >= 6:
            icon_str = "\u2717"
            icon_color = _STATUS_RED
        else:
            icon_str = f"{attempts}/6"
            icon_color = TILE_PRESENT
        icon_bbox  = draw.textbbox((0, 0), icon_str, font=rank_font)
        icon_w     = icon_bbox[2] - icon_bbox[0]
        draw.text(
            (cx + CARD_W - CARD_SIDE_PAD - icon_w, name_y - 7),
            icon_str, font=rank_font, fill=icon_color,
        )

        # Nom (centre)
        _center_text(draw, cx + CARD_W / 2, name_y, name, name_font)

        # ── Mini grille ───────────────────────────────────────────────────────
        board_x = cx + CARD_SIDE_PAD
        board_y = cy + CARD_TOP_PAD + NAME_H + NAME_BOT_GAP

        for gr in range(6):
            for gc in range(5):
                tx = board_x + gc * (MINI_TILE + MINI_GAP)
                ty = board_y + gr * (MINI_TILE + MINI_GAP)

                if gr < len(guesses):
                    word, codes = guesses[gr]
                    code  = codes[gc] if gc < len(codes) else 'B'
                    color = _GRID_COLOR_CODE.get(code, TILE_ABSENT)
                    draw.rounded_rectangle(
                        [tx, ty, tx + MINI_TILE - 1, ty + MINI_TILE - 1],
                        radius=MINI_CORNER,
                        fill=color,
                    )
                    if reveal and gc < len(word):
                        _center_text(
                            draw,
                            tx + MINI_TILE / 2,
                            ty + MINI_TILE / 2,
                            word[gc],
                            mini_font,
                        )
                else:
                    draw.rounded_rectangle(
                        [tx, ty, tx + MINI_TILE - 1, ty + MINI_TILE - 1],
                        radius=MINI_CORNER,
                        fill=_EMPTY_TILE,
                        outline=_EMPTY_BORDER,
                        width=1,
                    )

        # ── Statut sous la grille ─────────────────────────────────────────────
        stat_y   = board_y + MINI_BOARD_H + GRID_BOT_GAP + STAT_H / 2
        if won:
            stat_text  = "Réussi !"
            stat_color = TILE_CORRECT
        else:
            stat_text  = "Perdu"
            stat_color = _STATUS_RED
        _center_text(draw, cx + CARD_W / 2, stat_y, stat_text, stat_font, fill=stat_color)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)

    hint = "" if reveal else " \u00b7 Terminez votre partie pour voir les lettres !"
    embed = discord.Embed(
        title=f"\U0001f4ca Comparaison du {date_str}",
        description=f"{n} joueur{'s' if n != 1 else ''} aujourd'hui{hint}",
        color=discord.Color.green() if reveal else discord.Color.blurple(),
    )
    embed.set_image(url="attachment://comparison.png")
    file = discord.File(buf, filename="comparison.png")
    return embed, file
