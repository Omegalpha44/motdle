from motdle.core.evaluator import LetterResult
from motdle.core.game import GameState, GameStatus, GuessResult
from motdle.core.words import WordList


def make_game(target: str = "ARBRE") -> GameState:
    wl = WordList()
    return GameState(target=target, word_list=wl)


def test_initial_state():
    game = make_game()
    assert game.status == GameStatus.IN_PROGRESS
    assert game.attempts_remaining == 6
    assert game.guesses == []


def test_valid_guess():
    game = make_game("AMOUR")
    result = game.submit_guess("ARBRE")
    assert isinstance(result, GuessResult)
    assert result.word == "ARBRE"
    assert len(result.letters) == 5
    assert game.status == GameStatus.IN_PROGRESS
    assert game.attempts_remaining == 5


def test_winning_guess():
    game = make_game("ARBRE")
    result = game.submit_guess("ARBRE")
    assert isinstance(result, GuessResult)
    assert game.status == GameStatus.WON


def test_invalid_word():
    game = make_game("ARBRE")
    result = game.submit_guess("ZZZZZ")
    assert isinstance(result, str)
    assert "dictionnaire" in result
    assert game.attempts_remaining == 6


def test_wrong_length():
    game = make_game("ARBRE")
    result = game.submit_guess("AB")
    assert isinstance(result, str)
    assert "5 lettres" in result


def test_lose_after_max_guesses():
    game = make_game("ZOMBI")
    words = ["ARBRE", "AMOUR", "BLANC", "CRIME", "DROIT", "FORTE"]
    for w in words:
        result = game.submit_guess(w)
        assert isinstance(result, GuessResult)
    assert game.status == GameStatus.LOST


def test_keyboard_tracking():
    game = make_game("ARBRE")
    game.submit_guess("AMOUR")
    assert game.keyboard["A"] == LetterResult.CORRECT
    assert game.keyboard["M"] == LetterResult.ABSENT
    assert game.keyboard["R"] == LetterResult.PRESENT
