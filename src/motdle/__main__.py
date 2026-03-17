import argparse


def main():
    parser = argparse.ArgumentParser(description="Motdle - Wordle Francais")
    parser.add_argument(
        "--test", action="store_true",
        help="Lancer en mode test (terminal)",
    )
    parser.add_argument(
        "--free", action="store_true",
        help="Mode terminal libre : mots aleatoires, rejouable (implique --test)",
    )
    parser.add_argument(
        "--db", default="motdle.db",
        help="Chemin vers la base de donnees SQLite (defaut: motdle.db)",
    )
    args = parser.parse_args()

    if args.test or args.free:
        from motdle.terminal.runner import run_terminal
        run_terminal(free_mode=args.free)
    else:
        from motdle.bot.client import run_bot
        run_bot(db_path=args.db)


if __name__ == "__main__":
    main()
