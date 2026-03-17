import tempfile
from datetime import date
from pathlib import Path

from motdle.core.database import (
    get_leaderboard,
    get_player_stats,
    has_played_today,
    init_db,
    save_result,
)


def make_db() -> str:
    tmp = tempfile.mktemp(suffix=".db")
    init_db(tmp)
    return tmp


def test_init_creates_table(tmp_path):
    db = str(tmp_path / "test.db")
    init_db(db)
    assert Path(db).exists()


def test_has_not_played_initially():
    db = make_db()
    assert not has_played_today(db, 123, date(2026, 3, 16))


def test_save_and_has_played():
    db = make_db()
    today = date(2026, 3, 16)
    save_result(db, 123, today, attempts=3, won=True)
    assert has_played_today(db, 123, today)
    assert not has_played_today(db, 456, today)
    assert not has_played_today(db, 123, date(2026, 3, 17))


def test_save_idempotent():
    db = make_db()
    today = date(2026, 3, 16)
    save_result(db, 123, today, attempts=3, won=True)
    save_result(db, 123, today, attempts=1, won=True)  # remplace le premier (REPLACE)
    stats = get_player_stats(db, 123)
    assert stats["games"] == 1


def test_leaderboard_order():
    db = make_db()
    d1, d2, d3 = date(2026, 3, 14), date(2026, 3, 15), date(2026, 3, 16)
    # Joueur 1 : 2 victoires, moy 2.0
    save_result(db, 1, d1, attempts=2, won=True)
    save_result(db, 1, d2, attempts=2, won=True)
    # Joueur 2 : 2 victoires, moy 4.0
    save_result(db, 2, d1, attempts=4, won=True)
    save_result(db, 2, d2, attempts=4, won=True)
    # Joueur 3 : 1 victoire
    save_result(db, 3, d1, attempts=1, won=True)
    save_result(db, 3, d2, attempts=3, won=False)

    lb = get_leaderboard(db)
    assert lb[0]["user_id"] == 1   # 2 victoires, meilleure moyenne
    assert lb[1]["user_id"] == 2   # 2 victoires, moins bonne moyenne
    assert lb[2]["user_id"] == 3   # 1 victoire


def test_player_stats_none_if_no_games():
    db = make_db()
    assert get_player_stats(db, 999) is None


def test_player_stats():
    db = make_db()
    d1, d2 = date(2026, 3, 15), date(2026, 3, 16)
    save_result(db, 7, d1, attempts=3, won=True)
    save_result(db, 7, d2, attempts=5, won=False)
    stats = get_player_stats(db, 7)
    assert stats["wins"] == 1
    assert stats["games"] == 2
    assert stats["avg_attempts"] == 3.0  # seulement les victoires
