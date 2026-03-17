from enum import Enum


class LetterResult(Enum):
    CORRECT = "correct"   # Bonne lettre, bonne position (vert)
    PRESENT = "present"   # Bonne lettre, mauvaise position (jaune)
    ABSENT = "absent"     # Lettre absente du mot (gris)


def evaluate_guess(guess: str, target: str) -> list[LetterResult]:
    """Evalue un mot de 5 lettres contre le mot cible (algorithme 2 passes)."""
    n = len(target)
    results = [LetterResult.ABSENT] * n
    target_remaining = list(target)

    # Passe 1 : correspondances exactes
    for i in range(n):
        if guess[i] == target[i]:
            results[i] = LetterResult.CORRECT
            target_remaining[i] = None

    # Passe 2 : lettres presentes mais mal placees
    for i in range(n):
        if results[i] is LetterResult.CORRECT:
            continue
        if guess[i] in target_remaining:
            results[i] = LetterResult.PRESENT
            target_remaining[target_remaining.index(guess[i])] = None

    return results
