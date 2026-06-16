"""Module 3 — pytest Test Suite

Tests the HabitTracker (habit.py) and Analytics (analytics.py) modules.
Each test uses an isolated temporary SQLite database to ensure independence.
"""

import os
import tempfile
from datetime import date, timedelta

import pytest

from habit import Habit, HabitTracker
import analytics


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tracker():
    """
    Provide a fresh HabitTracker backed by a temporary database.

    Seeded predefined habits are cleared so every test starts with an
    empty database. The connection is closed and the file deleted on teardown.
    """
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    t = HabitTracker(db_path=db_path)
    # Clear seeded data for test isolation
    t._conn.execute("DELETE FROM completions")
    t._conn.execute("DELETE FROM habits")
    t._conn.commit()
    yield t
    t.close()
    os.unlink(db_path)


# ---------------------------------------------------------------------------
# Habit class
# ---------------------------------------------------------------------------


class TestHabitModel:
    def test_defaults_created_at(self):
        h = Habit("Exercise", "daily")
        assert h.created_at is not None

    def test_explicit_created_at(self):
        ts = "2026-01-01T00:00:00"
        h = Habit("Exercise", "daily", created_at=ts)
        assert h.created_at == ts

    def test_equality_by_name(self):
        assert Habit("Exercise", "daily") == Habit("Exercise", "weekly")

    def test_repr_contains_name(self):
        h = Habit("Exercise", "daily")
        assert "Exercise" in repr(h)


# ---------------------------------------------------------------------------
# HabitTracker — create
# ---------------------------------------------------------------------------


class TestHabitCreation:
    def test_create_daily_habit(self, tracker):
        assert tracker.create_habit("Exercise", "daily") is True

    def test_create_weekly_habit(self, tracker):
        assert tracker.create_habit("Meal Prep", "weekly") is True

    def test_duplicate_returns_false(self, tracker):
        tracker.create_habit("Exercise", "daily")
        assert tracker.create_habit("Exercise", "daily") is False

    def test_habit_persisted(self, tracker):
        tracker.create_habit("Read", "daily")
        names = [h.name for h in tracker.get_all_habits()]
        assert "Read" in names

    def test_created_at_is_set(self, tracker):
        tracker.create_habit("Meditate", "daily")
        habit = next(h for h in tracker.get_all_habits() if h.name == "Meditate")
        assert habit.created_at is not None


# ---------------------------------------------------------------------------
# HabitTracker — delete
# ---------------------------------------------------------------------------


class TestHabitDeletion:
    def test_delete_existing(self, tracker):
        tracker.create_habit("Exercise", "daily")
        assert tracker.delete_habit("Exercise") is True

    def test_delete_nonexistent(self, tracker):
        assert tracker.delete_habit("Ghost") is False

    def test_delete_removes_completions(self, tracker):
        tracker.create_habit("Exercise", "daily")
        tracker.complete_habit("Exercise")
        tracker.delete_habit("Exercise")
        assert tracker.get_habit_completions("Exercise") == []

    def test_delete_removes_from_list(self, tracker):
        tracker.create_habit("Exercise", "daily")
        tracker.delete_habit("Exercise")
        names = [h.name for h in tracker.get_all_habits()]
        assert "Exercise" not in names


# ---------------------------------------------------------------------------
# HabitTracker — complete
# ---------------------------------------------------------------------------


class TestHabitCompletion:
    def test_complete_existing(self, tracker):
        tracker.create_habit("Exercise", "daily")
        assert tracker.complete_habit("Exercise") is True

    def test_complete_nonexistent(self, tracker):
        assert tracker.complete_habit("Ghost") is False

    def test_completion_logged_once(self, tracker):
        tracker.create_habit("Exercise", "daily")
        tracker.complete_habit("Exercise")
        assert len(tracker.get_habit_completions("Exercise")) == 1

    def test_multiple_completions(self, tracker):
        tracker.create_habit("Exercise", "daily")
        tracker.complete_habit("Exercise")
        tracker.complete_habit("Exercise")
        assert len(tracker.get_habit_completions("Exercise")) == 2


# ---------------------------------------------------------------------------
# HabitTracker — storage / query
# ---------------------------------------------------------------------------


class TestHabitStorage:
    def test_get_all_empty(self, tracker):
        assert tracker.get_all_habits() == []

    def test_get_all_returns_correct_count(self, tracker):
        tracker.create_habit("Exercise", "daily")
        tracker.create_habit("Meal Prep", "weekly")
        assert len(tracker.get_all_habits()) == 2

    def test_get_periodicity_daily(self, tracker):
        tracker.create_habit("Exercise", "daily")
        assert tracker.get_periodicity("Exercise") == "daily"

    def test_get_periodicity_weekly(self, tracker):
        tracker.create_habit("Meal Prep", "weekly")
        assert tracker.get_periodicity("Meal Prep") == "weekly"

    def test_get_periodicity_unknown(self, tracker):
        assert tracker.get_periodicity("Unknown") is None


# ---------------------------------------------------------------------------
# Analytics — get_all_habits
# ---------------------------------------------------------------------------


class TestAnalyticsGetAll:
    def test_returns_all(self, tracker):
        tracker.create_habit("Exercise", "daily")
        tracker.create_habit("Meal Prep", "weekly")
        assert len(analytics.get_all_habits(tracker)) == 2

    def test_returns_empty(self, tracker):
        assert analytics.get_all_habits(tracker) == []


# ---------------------------------------------------------------------------
# Analytics — filter_by_periodicity
# ---------------------------------------------------------------------------


class TestAnalyticsFilter:
    def test_filter_daily(self, tracker):
        tracker.create_habit("Exercise", "daily")
        tracker.create_habit("Meal Prep", "weekly")
        habits = analytics.get_all_habits(tracker)
        daily = analytics.filter_by_periodicity(habits, "daily")
        assert len(daily) == 1
        assert daily[0].name == "Exercise"

    def test_filter_weekly(self, tracker):
        tracker.create_habit("Exercise", "daily")
        tracker.create_habit("Meal Prep", "weekly")
        habits = analytics.get_all_habits(tracker)
        weekly = analytics.filter_by_periodicity(habits, "weekly")
        assert len(weekly) == 1
        assert weekly[0].name == "Meal Prep"

    def test_filter_no_results(self, tracker):
        tracker.create_habit("Exercise", "daily")
        habits = analytics.get_all_habits(tracker)
        assert analytics.filter_by_periodicity(habits, "weekly") == []


# ---------------------------------------------------------------------------
# Analytics — longest_streak_all
# ---------------------------------------------------------------------------


class TestAnalyticsLongestStreakAll:
    def test_empty_returns_empty_string_and_zero(self, tracker):
        name, streak = analytics.longest_streak_all(tracker)
        assert name == "" and streak == 0

    def test_finds_habit_with_longer_streak(self, tracker):
        tracker.create_habit("Exercise", "daily")
        tracker.create_habit("Read", "daily")
        today = date.today()
        # Exercise: 5 consecutive days
        for i in range(5):
            d = (today - timedelta(days=4 - i)).isoformat() + "T08:00:00"
            tracker._conn.execute(
                "INSERT INTO completions (habit_name, completed_at) VALUES (?, ?)",
                ("Exercise", d),
            )
        # Read: 3 consecutive days
        for i in range(3):
            d = (today - timedelta(days=2 - i)).isoformat() + "T08:00:00"
            tracker._conn.execute(
                "INSERT INTO completions (habit_name, completed_at) VALUES (?, ?)",
                ("Read", d),
            )
        tracker._conn.commit()
        name, streak = analytics.longest_streak_all(tracker)
        assert name == "Exercise"
        assert streak == 5


# ---------------------------------------------------------------------------
# Analytics — longest_streak_single
# ---------------------------------------------------------------------------


class TestAnalyticsLongestStreakSingle:
    def test_unknown_habit_returns_zero(self, tracker):
        assert analytics.longest_streak_single(tracker, "Ghost") == 0

    def test_no_completions_returns_zero(self, tracker):
        tracker.create_habit("Exercise", "daily")
        assert analytics.longest_streak_single(tracker, "Exercise") == 0

    def test_daily_streak_no_gaps(self, tracker):
        tracker.create_habit("Exercise", "daily")
        today = date.today()
        for i in range(7):
            d = (today - timedelta(days=6 - i)).isoformat() + "T08:00:00"
            tracker._conn.execute(
                "INSERT INTO completions (habit_name, completed_at) VALUES (?, ?)",
                ("Exercise", d),
            )
        tracker._conn.commit()
        assert analytics.longest_streak_single(tracker, "Exercise") == 7

    def test_daily_streak_with_gap(self, tracker):
        tracker.create_habit("Exercise", "daily")
        today = date.today()
        # offsets 5,4,3 → streak 3; gap at 2; offsets 1,0 → streak 2
        for offset in [5, 4, 3, 1, 0]:
            d = (today - timedelta(days=offset)).isoformat() + "T08:00:00"
            tracker._conn.execute(
                "INSERT INTO completions (habit_name, completed_at) VALUES (?, ?)",
                ("Exercise", d),
            )
        tracker._conn.commit()
        assert analytics.longest_streak_single(tracker, "Exercise") == 3

    def test_weekly_streak_four_consecutive_weeks(self, tracker):
        tracker.create_habit("Weekly Review", "weekly")
        today = date.today()
        # One completion per week for 4 consecutive weeks (7-day intervals guarantee
        # consecutive ISO weeks).
        for i in range(4):
            d = (today - timedelta(weeks=3 - i)).isoformat() + "T08:00:00"
            tracker._conn.execute(
                "INSERT INTO completions (habit_name, completed_at) VALUES (?, ?)",
                ("Weekly Review", d),
            )
        tracker._conn.commit()
        assert analytics.longest_streak_single(tracker, "Weekly Review") == 4
