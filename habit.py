"""Module 1 — Habit Tracker (OOP + SQLite3)

Provides the Habit data class and HabitTracker manager for creating,
deleting, completing, and querying habits with persistent SQLite3 storage.
"""

import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Optional


class Habit:
    """Represents a single habit with its name, periodicity, and creation time."""

    def __init__(self, name: str, periodicity: str, created_at: Optional[str] = None) -> None:
        """
        Initialise a Habit instance.

        Args:
            name: Unique name of the habit.
            periodicity: Tracking frequency — 'daily' or 'weekly'.
            created_at: ISO 8601 datetime string for when the habit was created.
                        Defaults to the current local time when omitted.
        """
        self.name = name
        self.periodicity = periodicity
        self.created_at = created_at or datetime.now().isoformat()

    def __repr__(self) -> str:
        return f"Habit(name={self.name!r}, periodicity={self.periodicity!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Habit):
            return NotImplemented
        return self.name == other.name


class HabitTracker:
    """
    Manages habits and their completion log using a SQLite3 database.

    On first launch (empty database) five predefined habits are seeded
    together with four weeks of example completion data.
    """

    def __init__(self, db_path: str = "habits.db") -> None:
        """
        Initialise the tracker and open (or create) the SQLite3 database.

        Args:
            db_path: File path for the SQLite3 database.
        """
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()
        self._seed_predefined_habits()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        """Create the habits and completions tables if they do not exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS habits (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT UNIQUE NOT NULL,
                periodicity  TEXT NOT NULL,
                created_at   TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS completions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_name   TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                FOREIGN KEY (habit_name)
                    REFERENCES habits(name)
                    ON DELETE CASCADE
            );
        """)
        self._conn.commit()

    def _seed_predefined_habits(self) -> None:
        """
        Seed five predefined habits with four weeks of sample completions.

        This method runs only when the habits table is empty (i.e. on first
        launch or when using a fresh database).
        """
        count = self._conn.execute("SELECT COUNT(*) FROM habits").fetchone()[0]
        if count > 0:
            return

        today = date.today()
        start = today - timedelta(days=27)  # 4 weeks back
        created_at = datetime(start.year, start.month, start.day).isoformat()

        predefined = [
            ("Exercise",      "daily"),
            ("Read",          "daily"),
            ("Meditate",      "daily"),
            ("Weekly Review", "weekly"),
            ("Meal Prep",     "weekly"),
        ]

        for name, periodicity in predefined:
            self._conn.execute(
                "INSERT INTO habits (name, periodicity, created_at) VALUES (?, ?, ?)",
                (name, periodicity, created_at),
            )

        # Daily habits skip one day per week to keep streaks realistic.
        skip: dict = {
            "Exercise": {3, 10, 17},
            "Read":     {5, 12, 20},
            "Meditate": {7, 14, 21},
        }

        for i in range(28):
            day = start + timedelta(days=i)
            completed_at = datetime(day.year, day.month, day.day, 8, 0, 0).isoformat()
            for name, periodicity in predefined:
                if periodicity == "daily" and i not in skip.get(name, set()):
                    self._conn.execute(
                        "INSERT INTO completions (habit_name, completed_at) VALUES (?, ?)",
                        (name, completed_at),
                    )
                elif periodicity == "weekly" and i in {0, 7, 14, 21}:
                    self._conn.execute(
                        "INSERT INTO completions (habit_name, completed_at) VALUES (?, ?)",
                        (name, completed_at),
                    )

        self._conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def create_habit(
        self,
        name: str,
        periodicity: str,
        created_at: Optional[str] = None,
    ) -> bool:
        """
        Create a new habit and persist it.

        Args:
            name: Unique name for the habit.
            periodicity: 'daily' or 'weekly'.
            created_at: Optional ISO 8601 timestamp; defaults to now.

        Returns:
            True if the habit was created, False if the name already exists.
        """
        try:
            ts = created_at or datetime.now().isoformat()
            self._conn.execute(
                "INSERT INTO habits (name, periodicity, created_at) VALUES (?, ?, ?)",
                (name, periodicity, ts),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_habit(self, name: str) -> bool:
        """
        Delete a habit and all of its completion records.

        Args:
            name: Name of the habit to delete.

        Returns:
            True if the habit existed and was deleted, False otherwise.
        """
        cursor = self._conn.execute("DELETE FROM habits WHERE name = ?", (name,))
        # Explicit delete covers databases where cascading is not enforced.
        self._conn.execute("DELETE FROM completions WHERE habit_name = ?", (name,))
        self._conn.commit()
        return cursor.rowcount > 0

    def complete_habit(self, name: str) -> bool:
        """
        Log a completion for a habit at the current date and time.

        Args:
            name: Name of the habit to mark as completed.

        Returns:
            True if the completion was logged, False if the habit was not found.
        """
        row = self._conn.execute(
            "SELECT name FROM habits WHERE name = ?", (name,)
        ).fetchone()
        if not row:
            return False
        self._conn.execute(
            "INSERT INTO completions (habit_name, completed_at) VALUES (?, ?)",
            (name, datetime.now().isoformat()),
        )
        self._conn.commit()
        return True

    def get_all_habits(self) -> List[Habit]:
        """
        Return all tracked habits ordered alphabetically.

        Returns:
            A list of Habit instances.
        """
        rows = self._conn.execute(
            "SELECT name, periodicity, created_at FROM habits ORDER BY name"
        ).fetchall()
        return [Habit(name, period, created) for name, period, created in rows]

    def get_habit_completions(self, name: str) -> List[str]:
        """
        Return all completion timestamps for a given habit, oldest first.

        Args:
            name: Name of the habit.

        Returns:
            A list of ISO 8601 datetime strings.
        """
        rows = self._conn.execute(
            "SELECT completed_at FROM completions "
            "WHERE habit_name = ? ORDER BY completed_at",
            (name,),
        ).fetchall()
        return [row[0] for row in rows]

    def get_periodicity(self, name: str) -> Optional[str]:
        """
        Return the periodicity of a habit.

        Args:
            name: Name of the habit.

        Returns:
            'daily', 'weekly', or None if the habit does not exist.
        """
        row = self._conn.execute(
            "SELECT periodicity FROM habits WHERE name = ?", (name,)
        ).fetchone()
        return row[0] if row else None
