import sys
from datetime import date

from motdle.core.evaluator import LetterResult
from motdle.core.game import GameState, GameStatus
from motdle.core.words import WordList

# Couleurs ANSI
COLORS = {
    LetterResult.CORRECT: "\033[42;97m",  # fond vert, texte blanc
    LetterResult.PRESENT: "\033[43;97m",  # fond jaune, texte blanc
    LetterResult.ABSENT: "\033[100;97m",  # fond gris, texte blanc
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

AZERTY_ROWS = ["AZERTYUIOP", "QSDFGHJKLM", "WXCVBN"]


def render_board(game: GameState) -> str:
    date_str = game.date.strftime("%d/%m/%Y") if game.date else ""
    header = f"{BOLD}MOTDLE{RESET}"
    if date_str:
        header += f" du {date_str}"
    header += f"  (Essai {len(game.guesses)}/{game.max_guesses})"

    lines = [f"\n  {header}\n"]

    for guess in game.guesses:
        row = "  "
        for letter, result in zip(guess.word, guess.letters):
            color = COLORS[result]
            row += f"{color} {letter} {RESET} "
        lines.append(row)

    remaining = game.max_guesses - len(game.guesses)
    for _ in range(remaining):
        lines.append(f"  {DIM}" + " _ " * 5 + f"{RESET}")

    return "\n".join(lines)


def render_keyboard(game: GameState) -> str:
    lines = [f"\n  {BOLD}Clavier:{RESET}"]
    for row in AZERTY_ROWS:
        display = "  "
        for letter in row:
            status = game.keyboard.get(letter)
            if status:
                color = COLORS[status]
                display += f"{color} {letter} {RESET}"
            else:
                display += f" {letter} "
        lines.append(display)
    return "\n".join(lines)


def run_terminal(free_mode: bool = False):
    # Active les couleurs ANSI sur Windows
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    word_list = WordList()
    mode_label = "mode libre" if free_mode else "mot du jour"
    print(f"\n  {BOLD}Motdle - Wordle Francais{RESET} ({len(word_list)} mots · {mode_label})")

    if free_mode:
        print(f"  Tapez 'quit' pour quitter, 'new' pour nouvelle partie.\n")
    else:
        today = date.today()
        print(f"  Mot du {today.strftime('%d/%m/%Y')} - une seule tentative !\n")

    while True:
        today = date.today()
        if free_mode:
            target = word_list.random_target()
            game_date = None
        else:
            target = word_list.daily_target(today)
            game_date = today

        game = GameState(target=target, word_list=word_list, date=game_date)

        while game.status == GameStatus.IN_PROGRESS:
            print(render_board(game))
            print(render_keyboard(game))
            print()

            try:
                user_input = input("  Votre mot > ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\n  Au revoir !")
                sys.exit(0)

            if user_input == "QUIT":
                print("\n  Au revoir !")
                sys.exit(0)
            if user_input == "NEW" and free_mode:
                print(f"\n  {DIM}--- Nouvelle partie ---{RESET}")
                break

            result = game.submit_guess(user_input)
            if isinstance(result, str):
                print(f"\n  \u274c {result}")

        # Fin de partie
        print(render_board(game))
        if game.status == GameStatus.WON:
            count = len(game.guesses)
            print(f"\n  \u2705 Bravo ! Trouve en {count} essai{'s' if count > 1 else ''} !")
        elif game.status == GameStatus.LOST:
            print(f"\n  \u274c Perdu ! Le mot etait : {BOLD}{game.target}{RESET}")

        if not free_mode:
            print(f"\n  Revenez demain pour un nouveau mot !")
            break

        try:
            again = input(f"\n  Encore ? (o/n) > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if again != "o":
            break

    print("\n  Au revoir !")
