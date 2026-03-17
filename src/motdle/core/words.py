import hashlib
import random
from datetime import date
from importlib.resources import files


class WordList:
    def __init__(self, word_file: str | None = None):
        if word_file:
            with open(word_file, "r", encoding="utf-8") as f:
                raw = f.read()
        else:
            raw = (
                files("motdle.data")
                .joinpath("words_fr.txt")
                .read_text(encoding="utf-8")
            )

        self.words: set[str] = set()
        self.target_words: list[str] = []

        for line in raw.strip().splitlines():
            word = line.strip().upper()
            if len(word) == 5 and word.isalpha():
                self.words.add(word)
                self.target_words.append(word)

        self.target_words.sort()

    def is_valid(self, word: str) -> bool:
        return word.upper() in self.words

    def random_target(self) -> str:
        return random.choice(self.target_words)

    def daily_target(self, today: date) -> str:
        digest = hashlib.sha256(today.isoformat().encode()).hexdigest()
        index = int(digest, 16) % len(self.target_words)
        return self.target_words[index]

    def __len__(self) -> int:
        return len(self.words)
