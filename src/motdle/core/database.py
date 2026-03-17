import sqlite3
from datetime import date
from pathlib import Path

DB_DEFAULT_PATH = Path("motdle.db")

# Encodage des couleurs : G=Correct, Y=Present, B=Absent
GRID_CODES = {"G": "correct", "Y": "present", "B": "absent"}


def init_db(db_path: str | Path = DB_DEFAULT_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS game_results (
                user_id INTEGER,
                date TEXT,
                attempts INTEGER,
                won INTEGER,
                grid TEXT DEFAULT '',
                PRIMARY KEY (user_id, date)
            )
        """)
        # Migration : ajouter la colonne grid si elle n'existe pas (DB existante)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(game_results)")]
        if "grid" not in cols:
            conn.execute("ALTER TABLE game_results ADD COLUMN grid TEXT DEFAULT ''")


def has_finished_today(db_path: str | Path, user_id: int, today: date) -> bool:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT won, attempts FROM game_results WHERE user_id = ? AND date = ?",
            (user_id, today.isoformat()),
        ).fetchone()
        if not row:
            return False
        return bool(row[0]) or row[1] >= 6

def has_played_today(db_path: str | Path, user_id: int, today: date) -> bool:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM game_results WHERE user_id = ? AND date = ?",
            (user_id, today.isoformat()),
        ).fetchone()
        return row is not None


def get_player_today_result(db_path: str | Path, user_id: int, today: date) -> dict | None:
    """Retourne la ligne de resultat du joueur pour aujourd'hui, ou None."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT user_id, attempts, won, grid FROM game_results WHERE user_id = ? AND date = ?",
            (user_id, today.isoformat()),
        ).fetchone()
        return dict(row) if row else None


def save_result(
    db_path: str | Path,
    user_id: int,
    today: date,
    attempts: int,
    won: bool,
    grid: str = "",
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO game_results
               (user_id, date, attempts, won, grid) VALUES (?, ?, ?, ?, ?)""",
            (user_id, today.isoformat(), attempts, int(won), grid),
        )


def get_today_results(db_path: str | Path, today: date) -> list[dict]:
    """Retourne tous les resultats du jour, tries par gagne d'abord puis par nombre d'essais."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT user_id, attempts, won, grid
               FROM game_results
               WHERE date = ?
               ORDER BY won DESC, attempts ASC, user_id ASC""",
            (today.isoformat(),),
        ).fetchall()
        return [dict(r) for r in rows]


def get_leaderboard(db_path: str | Path, limit: int = 10) -> list[dict]:
    """Classement global par victoires puis par moyenne d'essais (sur les victoires)."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT user_id,
                      SUM(won) AS wins,
                      COUNT(*) AS games,
                      AVG(CASE WHEN won = 1 THEN attempts END) AS avg_attempts
               FROM game_results
               GROUP BY user_id
               ORDER BY wins DESC, avg_attempts ASC, user_id ASC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_player_stats(db_path: str | Path, user_id: int) -> dict | None:
    """Stats individuelles d'un joueur, ou None s'il n'a jamais joue."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """SELECT SUM(won) AS wins,
                      COUNT(*) AS games,
                      AVG(CASE WHEN won = 1 THEN attempts END) AS avg_attempts
               FROM game_results
               WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
        if row is None or row["games"] == 0:
            return None
        return dict(row)


def reset_db(db_path: str | Path) -> int:
    """Supprime tous les résultats. Retourne le nombre de lignes supprimées.""" 
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("DELETE FROM game_results")
        return cur.rowcount

def clear_old_results(db_path: str | Path, today: date) -> int:
    """Supprime tous les résultats antérieurs à la date donnée. Retourne le nombre de lignes supprimées."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("DELETE FROM game_results WHERE date < ?", (today.isoformat(),))
