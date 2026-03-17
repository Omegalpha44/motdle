"""
Upload les emojis Motdle sur un serveur Discord et genere emoji_ids.json.

Usage :
  uv run python scripts/upload_emojis.py --guild GUILD_ID

Le token est lu depuis .env (DISCORD_TOKEN).
Le fichier emoji_ids.json est cree a la racine du projet.

Permissions requises : "Manage Emojis and Stickers" sur le serveur.

Note : Discord limite les emojis par serveur (50 sans boost, 100 en level 1,
150 en level 2, 250 en level 3). Ce script uploade 78 emojis.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

import discord
from dotenv import load_dotenv

EMOJIS_DIR = Path("emojis")
OUTPUT_FILE = Path("emoji_ids.json")
EMOJI_PREFIX = "mtd"


async def upload(guild_id: int, token: str, force: bool = False) -> None:
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    emoji_ids: dict[str, int] = {}

    # Charger les IDs existants si le fichier existe deja
    if OUTPUT_FILE.exists() and not force:
        with open(OUTPUT_FILE) as f:
            emoji_ids = json.load(f)

    @client.event
    async def on_ready():
        guild = client.get_guild(guild_id)
        if not guild:
            print(f"Serveur {guild_id} introuvable. Verifiez l'ID et que le bot est bien sur le serveur.")
            await client.close()
            return

        existing = {e.name: e for e in guild.emojis}
        print(f"Serveur : {guild.name}")
        print(f"Emojis actuels : {len(existing)}/{guild.emoji_limit}")
        print()

        png_files = sorted(EMOJIS_DIR.glob("*.png"))
        if not png_files:
            print(f"Aucune image trouvee dans '{EMOJIS_DIR}/'. Lancez d'abord generate_emojis.py")
            await client.close()
            return

        uploaded = 0
        skipped = 0
        errors = 0

        for png_path in png_files:
            # A_v.png -> key="A_v", discord_name="mtd_A_v"
            key = png_path.stem
            discord_name = f"{EMOJI_PREFIX}_{key}"

            if key in emoji_ids and not force:
                skipped += 1
                continue

            # Verifier si l'emoji existe deja sur le serveur
            if discord_name in existing and not force:
                emoji_ids[key] = existing[discord_name].id
                skipped += 1
                continue

            try:
                with open(png_path, "rb") as f:
                    image_data = f.read()

                emoji = await guild.create_custom_emoji(
                    name=discord_name,
                    image=image_data,
                    reason="Motdle setup",
                )
                emoji_ids[key] = emoji.id
                uploaded += 1
                print(f"  Upload : {discord_name}")
                await asyncio.sleep(0.3)  # eviter le rate limit Discord

            except discord.Forbidden:
                print(f"Permission refusee. Le bot doit avoir 'Manage Emojis and Stickers'.")
                errors += 1
                break
            except discord.HTTPException as e:
                if e.status == 429:
                    print(f"  Rate limit, pause 5s...")
                    await asyncio.sleep(5)
                elif "Maximum number of emojis" in str(e):
                    print(f"\nLimite d'emojis atteinte ({guild.emoji_limit}).")
                    print("Boostez votre serveur pour augmenter la limite.")
                    errors += 1
                    break
                else:
                    print(f"  Erreur pour {discord_name}: {e}")
                    errors += 1

        # Sauvegarder
        with open(OUTPUT_FILE, "w") as f:
            json.dump(emoji_ids, f, indent=2, sort_keys=True)

        print()
        print(f"Upload : {uploaded}  |  Deja existants : {skipped}  |  Erreurs : {errors}")
        print(f"{len(emoji_ids)} IDs sauvegardes dans '{OUTPUT_FILE}'")

        if errors == 0 and len(emoji_ids) == 78:
            print("\nSetup termine ! Relancez le bot pour utiliser les emojis custom.")
        elif len(emoji_ids) < 78:
            print(f"\nAttention : seulement {len(emoji_ids)}/78 emojis charges.")
            print("Le bot utilisera les emojis par defaut pour les lettres manquantes.")

        await client.close()

    await client.start(token)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Upload les emojis Motdle sur Discord"
    )
    parser.add_argument(
        "--guild", type=int, required=True,
        help="ID du serveur Discord (clic droit sur le serveur -> Copier l'identifiant)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-uploader meme si les emojis existent deja",
    )
    args = parser.parse_args()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN manquant dans .env")

    if not EMOJIS_DIR.exists() or not list(EMOJIS_DIR.glob("*.png")):
        raise SystemExit(
            f"Dossier '{EMOJIS_DIR}' vide ou absent.\n"
            "Lancez d'abord : uv run python scripts/generate_emojis.py"
        )

    asyncio.run(upload(args.guild, token, force=args.force))


if __name__ == "__main__":
    main()
