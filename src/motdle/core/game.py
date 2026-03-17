from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from motdle.core.evaluator import LetterResult, evaluate_guess
from motdle.core.words import WordList


class GameStatus(Enum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


@dataclass
class GuessResult:
    word: str
    letters: list[LetterResult]


@dataclass
class GameState:
    target: str
    word_list: WordList
    max_guesses: int = 6
    guesses: list[GuessResult] = field(default_factory=list)
    keyboard: dict[str, LetterResult] = field(default_factory=dict)
    date: date | None = None

    @property
    def status(self) -> GameStatus:
        if self.guesses and all(
            r == LetterResult.CORRECT for r in self.guesses[-1].letters
        ):
            return GameStatus.WON
        if len(self.guesses) >= self.max_guesses:
            return GameStatus.LOST
        return GameStatus.IN_PROGRESS

    @property
    def attempts_remaining(self) -> int:
        return self.max_guesses - len(self.guesses)

    def submit_guess(self, word: str) -> GuessResult | str:
        """Soumet un mot. Retourne GuessResult si OK, ou un message d'erreur."""
        word = word.upper().strip()

        if len(word) != 5:
            return "Le mot doit faire exactement 5 lettres."

        if not word.isalpha():
            return "Le mot ne doit contenir que des lettres."

        if not self.word_list.is_valid(word):
            return f"'{word}' n'est pas dans le dictionnaire."

        if self.status != GameStatus.IN_PROGRESS:
            return "La partie est terminee."

        results = evaluate_guess(word, self.target)
        guess_result = GuessResult(word=word, letters=results)
        self.guesses.append(guess_result)

        # Mise a jour du clavier (garde le meilleur resultat par lettre)
        priority = {
            LetterResult.CORRECT: 2,
            LetterResult.PRESENT: 1,
            LetterResult.ABSENT: 0,
        }
        for letter, result in zip(word, results):
            current = self.keyboard.get(letter)
            if current is None or priority[result] > priority[current]:
                self.keyboard[letter] = result

        return guess_result
