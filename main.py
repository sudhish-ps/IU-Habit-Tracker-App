"""Entry Point — Habit Tracker CLI Application

Provides the interactive main loop menu for the habit tracker.
"""

from habit import HabitTracker
import analytics


def _print_menu() -> None:
    """Print the main menu."""
    print("\n===== Habit Tracker =====")
    print("1. View all habits")
    print("2. Create a new habit")
    print("3. Delete a habit")
    print("4. Mark habit as completed")
    print("5. Analytics")
    print("6. Exit")


def _print_analytics_menu() -> None:
    """Print the analytics sub-menu."""
    print("\n-- Analytics --")
    print("a. All habits")
    print("b. Filter by periodicity")
    print("c. Longest streak (all habits)")
    print("d. Longest streak (given habit)")
    print("e. Back to main menu")


def _handle_analytics(tracker: HabitTracker) -> None:
    """
    Run the analytics sub-menu loop.

    Args:
        tracker: The active HabitTracker instance.
    """
    while True:
        _print_analytics_menu()
        choice = input("Choose an option: ").strip().lower()

        if choice == "a":
            habits = analytics.get_all_habits(tracker)
            if not habits:
                print("No habits tracked yet.")
            else:
                print("\nAll habits:")
                for h in habits:
                    print(f"  [{h.periodicity:7s}] {h.name}  (since {h.created_at[:10]})")

        elif choice == "b":
            periodicity = input("Periodicity (daily/weekly): ").strip().lower()
            if periodicity not in ("daily", "weekly"):
                print("Please enter 'daily' or 'weekly'.")
                continue
            filtered = analytics.filter_by_periodicity(
                analytics.get_all_habits(tracker), periodicity
            )
            if not filtered:
                print(f"No {periodicity} habits found.")
            else:
                print(f"\n{periodicity.capitalize()} habits:")
                for h in filtered:
                    print(f"  {h.name}  (since {h.created_at[:10]})")

        elif choice == "c":
            name, streak = analytics.longest_streak_all(tracker)
            if not name:
                print("No habits tracked yet.")
            else:
                print(f"\nLongest streak: '{name}' — {streak} consecutive period(s).")

        elif choice == "d":
            name = input("Habit name: ").strip()
            periodicity = tracker.get_periodicity(name)
            if periodicity is None:
                print(f"Habit '{name}' not found.")
            else:
                streak = analytics.longest_streak_single(tracker, name)
                unit = "day(s)" if periodicity == "daily" else "week(s)"
                print(f"\nLongest streak for '{name}': {streak} consecutive {unit}.")

        elif choice == "e":
            break

        else:
            print("Invalid option. Choose a–e.")


def main() -> None:
    """
    Entry point: start the Habit Tracker CLI application.

    Initialises the tracker (and seeds predefined habits on first run),
    then enters the main interactive loop.
    """
    tracker = HabitTracker()
    print("Welcome to Habit Tracker!")
    try:
        while True:
            _print_menu()
            choice = input("Choose an option: ").strip()

            if choice == "1":
                habits = analytics.get_all_habits(tracker)
                if not habits:
                    print("No habits tracked yet.")
                else:
                    print("\nYour habits:")
                    for h in habits:
                        print(
                            f"  [{h.periodicity:7s}] {h.name}"
                            f"  (since {h.created_at[:10]})"
                        )

            elif choice == "2":
                name = input("Habit name: ").strip()
                if not name:
                    print("Name cannot be empty.")
                    continue
                periodicity = input("Periodicity (daily/weekly): ").strip().lower()
                if periodicity not in ("daily", "weekly"):
                    print("Please enter 'daily' or 'weekly'.")
                    continue
                if tracker.create_habit(name, periodicity):
                    print(f"Habit '{name}' created successfully.")
                else:
                    print(f"A habit named '{name}' already exists.")

            elif choice == "3":
                name = input("Habit name to delete: ").strip()
                if tracker.delete_habit(name):
                    print(f"Habit '{name}' deleted.")
                else:
                    print(f"Habit '{name}' not found.")

            elif choice == "4":
                name = input("Habit name to mark as completed: ").strip()
                if tracker.complete_habit(name):
                    print(f"'{name}' marked as completed.")
                else:
                    print(f"Habit '{name}' not found.")

            elif choice == "5":
                _handle_analytics(tracker)

            elif choice == "6":
                print("Goodbye!")
                break

            else:
                print("Invalid option. Please choose 1–6.")

    finally:
        tracker.close()


if __name__ == "__main__":
    main()
