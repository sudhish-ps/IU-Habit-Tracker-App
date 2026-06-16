# Habit Tracker

A command-line habit tracker application built with Python, SQLite3, and pytest.

## Project Overview

Manage and analyse your daily and weekly habits through an interactive CLI menu.
Create and delete habits, log completions, and view streak analytics — all persisted
in a local SQLite3 database.

On **first launch** five predefined habits are automatically created with four weeks
of sample completion data so you can explore the analytics immediately.

---

## Prerequisites / Dependencies

| Requirement | Version      |
|-------------|--------------|
| Python      | 3.7 or later |
| pytest      | any recent   |

No third-party packages are required beyond `pytest` — all other dependencies
(`sqlite3`, `datetime`, etc.) are part of the Python standard library.

---

## Installation

1. **Clone or download** this repository and navigate into the folder:

   ```bash
   cd IU-Habit-Tracker-App
   ```

2. **(Recommended) Create and activate a virtual environment:**

   Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   macOS / Linux:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install pytest
   ```

---

## How to Run the Application

```bash
python main.py
```

You will be presented with an interactive menu:

```
===== Habit Tracker =====
1. View all habits
2. Create a new habit
3. Delete a habit
4. Mark habit as completed
5. Analytics
   └── a. All habits
   └── b. Filter by periodicity
   └── c. Longest streak (all habits)
   └── d. Longest streak (given habit)
6. Exit
```

A `habits.db` SQLite3 database file is created automatically on first run in the
same directory.

---

## How to Run the Tests

```bash
pytest test_habit.py -v
```

All tests are self-contained and use isolated temporary databases — no manual
setup or teardown is required.

---

## Project Structure

```
habit-tracker/
├── main.py          # Entry point — CLI main loop & menu
├── habit.py         # Module 1 — OOP habit tracker + SQLite3
├── analytics.py     # Module 2 — Functional analytics
├── test_habit.py    # Module 3 — pytest test suite
├── habits.db        # SQLite3 database (auto-created on first run)
└── README.md        # This file
```

---

## Predefined Habits (seeded on first launch)

| Habit          | Periodicity |
|----------------|-------------|
| Exercise       | daily       |
| Read           | daily       |
| Meditate       | daily       |
| Weekly Review  | weekly      |
| Meal Prep      | weekly      |

Each predefined habit includes four weeks of example completion data so streak
analytics work out of the box.
