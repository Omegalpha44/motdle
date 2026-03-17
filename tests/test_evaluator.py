from motdle.core.evaluator import LetterResult, evaluate_guess


def test_all_correct():
    result = evaluate_guess("ARBRE", "ARBRE")
    assert result == [LetterResult.CORRECT] * 5


def test_all_absent():
    result = evaluate_guess("XYLOP", "ARBRE")
    # X, Y, L, O, P ne sont pas dans ARBRE
    # Mais attention, on teste seulement que les lettres absentes sont ABSENT
    for r in result:
        assert r == LetterResult.ABSENT


def test_present_letters():
    # ARBRE = A R B R E
    # BARRE = B A R R E
    # B pos0: cible[0]=A, B present ailleurs -> PRESENT
    # A pos1: cible[1]=R, A present ailleurs -> PRESENT
    # R pos2: cible[2]=B, R present ailleurs -> PRESENT
    # R pos3: cible[3]=R -> CORRECT
    # E pos4: cible[4]=E -> CORRECT
    result = evaluate_guess("BARRE", "ARBRE")
    assert result[0] == LetterResult.PRESENT   # B
    assert result[1] == LetterResult.PRESENT   # A
    assert result[2] == LetterResult.PRESENT   # R
    assert result[3] == LetterResult.CORRECT   # R
    assert result[4] == LetterResult.CORRECT   # E


def test_duplicate_letter_priority():
    # Mot cible: MASSE (deux S)
    # Guess: SOSSE
    # S pos0: S n'est pas en pos0 dans MASSE, mais S est present -> PRESENT
    # O pos1: pas dans MASSE -> ABSENT
    # S pos2: S en pos2 dans MASSE = S -> CORRECT
    # S pos3: S en pos3 dans MASSE = S -> CORRECT
    # E pos4: E en pos4 dans MASSE = E -> CORRECT
    result = evaluate_guess("SOSSE", "MASSE")
    assert result[0] == LetterResult.ABSENT    # S: les 2 S de MASSE sont consommes par pos2,3
    assert result[1] == LetterResult.ABSENT    # O
    assert result[2] == LetterResult.CORRECT   # S
    assert result[3] == LetterResult.CORRECT   # S
    assert result[4] == LetterResult.CORRECT   # E


def test_present_not_double_counted():
    # Cible: AMOUR, Guess: AAAAA
    # A en pos0: CORRECT
    # A en pos1: pas d'autre A dans le restant -> ABSENT
    result = evaluate_guess("AAAAA", "AMOUR")
    assert result[0] == LetterResult.CORRECT
    assert result[1] == LetterResult.ABSENT
    assert result[2] == LetterResult.ABSENT
    assert result[3] == LetterResult.ABSENT
    assert result[4] == LetterResult.ABSENT
