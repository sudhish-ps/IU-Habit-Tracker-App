"""Module 2 — Analytics (Functional Programming)

All functions are pure functions that operate on data provided as arguments.
No class state is modified.
"""

from datetime import date
from typing import List, Tuple

from habit import Habit, HabitTracker


def get_all_habits(tracker: HabitTracker) -> List[Habit]:
    """
    Return every currently tracked habit.

    Args:
        tracker: The HabitTracker instance.

    Returns:
        A list of all Habit objects in the database.
    """
    return tracker.get_all_habits()


def filter_by_periodicity(habits: List[Habit], periodicity: str) -> List[Habit]:
    """
    Filter a list of habits by their periodicity.

    Args:
        habits: A list of Habit objects to filter.
        periodicity: The target frequency — 'daily' or 'weekly'.

    Returns:
        A new list containing only habits whose periodicity matches.
    """
    return list(filter(lambda h: h.periodicity == periodicity, habits))


# ---- Streak helpers (pure functions) ------------------------------------


def _completion_dates(completions: List[str]) -> List[date]:
    """
    Convert a list of ISO datetime strings to a sorted list of unique dates.

    Args:
        completions: ISO 8601 datetime strings.

    Returns:
        Sorted list of unique date objects.
    """
    return sorted(set(date.fromisoformat(c[:10]) for c in completions))


def _longest_day_streak(dates: List[date]) -> int:
    """
    Compute the longest streak of consecutive calendar days.

    Args:
        dates: Sorted list of unique date objects.

    Returns:
        Length of the longest consecutive-day streak.
    """
    if not dates:
        return 0
    max_streak = current = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 1
    return max_streak


def _longest_week_streak(dates: List[date]) -> int:
    """
    Compute the longest streak of consecutive ISO calendar weeks.

    Args:
        dates: Sorted list of unique date objects.

    Returns:
        Length of the longest consecutive-week streak.
    """
    if not dates:
        return 0
    weeks: List[Tuple[int, int]] = sorted(
        set((d.isocalendar()[0], d.isocalendar()[1]) for d in dates)
    )
    if not weeks:
        return 0
    max_streak = current = 1
    for i in range(1, len(weeks)):
        y0, w0 = weeks[i - 1]
        y1, w1 = weeks[i]
        consecutive = (y0 == y1 and w1 == w0 + 1) or (
            y1 == y0 + 1 and w1 == 1 and w0 >= 52
        )
        if consecutive:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 1
    return max_streak


def compute_streak(completions: List[str], periodicity: str) -> int:
    """
    Compute the longest streak from a list of completion timestamps.

    For 'daily' habits a streak counts consecutive calendar days.
    For 'weekly' habits a streak counts consecutive ISO calendar weeks.

    Args:
        completions: List of ISO 8601 datetime strings.
        periodicity: 'daily' or 'weekly'.

    Returns:
        The longest streak as an integer. Returns 0 for an empty list.
    """
    dates = _completion_dates(completions)
    if periodicity == "daily":
        return _longest_day_streak(dates)
    if periodicity == "weekly":
        return _longest_week_streak(dates)
    return 0


def longest_streak_all(tracker: HabitTracker) -> Tuple[str, int]:
    """
    Return the habit with the longest run streak across all tracked habits.

    Args:
        tracker: The HabitTracker instance.

    Returns:
        A tuple (habit_name, streak_length).
        Returns ('', 0) when no habits are tracked.
    """
    habits = tracker.get_all_habits()
    if not habits:
        return ("", 0)
    streaks = (
        (h.name, compute_streak(tracker.get_habit_completions(h.name), h.periodicity))
        for h in habits
    )
    return max(streaks, key=lambda x: x[1])


def longest_streak_single(tracker: HabitTracker, habit_name: str) -> int:
    """
    Return the longest run streak for a specific habit.

    Args:
        tracker: The HabitTracker instance.
        habit_name: Name of the habit to analyse.

    Returns:
        The longest streak as an integer.
        Returns 0 if the habit is not found or has no completions.
    """
    periodicity = tracker.get_periodicity(habit_name)
    if periodicity is None:
        return 0
    return compute_streak(tracker.get_habit_completions(habit_name), periodicity)
