# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Run the demo with `python main.py`. Actual output:

```
============================================================
PawPal+ demo for Jordan (Buddy, Whiskers)
============================================================

1. Tasks as entered (out of order)
------------------------------------------------------------
18:00    Buddy    Dinner (10 min, high, daily, pending)
07:30    Buddy    Morning walk (30 min, high, daily, pending)
15:00    Buddy    Bath (45 min, low, weekly, pending)
17:50    Buddy    Vet visit (40 min, medium, once, pending)
17:45    Whiskers Playtime (20 min, medium, daily, pending)
Anytime  Whiskers Brush fur (15 min, low, weekly, pending)
08:00    Whiskers Medication (5 min, high, daily, pending)

2. Sorted by time (missing times last)
------------------------------------------------------------
07:30    Buddy    Morning walk (30 min, high, daily, pending)
08:00    Whiskers Medication (5 min, high, daily, pending)
15:00    Buddy    Bath (45 min, low, weekly, pending)
17:45    Whiskers Playtime (20 min, medium, daily, pending)
17:50    Buddy    Vet visit (40 min, medium, once, pending)
18:00    Buddy    Dinner (10 min, high, daily, pending)
Anytime  Whiskers Brush fur (15 min, low, weekly, pending)

3a. Filter: Whiskers' tasks
------------------------------------------------------------
17:45    Whiskers Playtime (20 min, medium, daily, pending)
Anytime  Whiskers Brush fur (15 min, low, weekly, pending)
08:00    Whiskers Medication (5 min, high, daily, pending)

3b. Filter: completed tasks (all pets)
------------------------------------------------------------
07:30    Buddy    Morning walk (30 min, high, daily, done)

3c. Filter: Buddy's pending tasks
------------------------------------------------------------
18:00    Buddy    Dinner (10 min, high, daily, pending)
15:00    Buddy    Bath (45 min, low, weekly, pending)
17:50    Buddy    Vet visit (40 min, medium, once, pending)

4. Conflict detection (pending tasks, all pets)
------------------------------------------------------------
WARNING: Playtime (Whiskers, 17:45-18:05) overlaps Vet visit (Buddy, 17:50-18:30)
WARNING: Playtime (Whiskers, 17:45-18:05) overlaps Dinner (Buddy, 18:00-18:10)
WARNING: Vet visit (Buddy, 17:50-18:30) overlaps Dinner (Buddy, 18:00-18:10)

5. Recurring tasks
------------------------------------------------------------
Completed 'Dinner' (daily) -> next one created for 2026-10-27
Completing it again adds nothing new: None
Completed 'Vet visit' (once) -> next one created: None

6. Today's plan (future repeats and completed tasks left out)
------------------------------------------------------------
08:00    Whiskers Medication (5 min, high, daily, pending)
15:00    Buddy    Bath (45 min, low, weekly, pending)
17:45    Whiskers Playtime (20 min, medium, daily, pending)
Anytime  Whiskers Brush fur (15 min, low, weekly, pending)

7. Plan explanation
------------------------------------------------------------
Daily plan for Jordan: 85 of 90 available minutes used.
Tasks are chosen by priority (high first), then earliest time, and shown in time order.
  08:00 - Medication for Whiskers (5 min) [priority: high]
  15:00 - Bath for Buddy (45 min) [priority: low]
  17:45 - Playtime for Whiskers (20 min) [priority: medium]
  any time - Brush fur for Whiskers (15 min) [priority: low]

8. Empty owner
------------------------------------------------------------
No pending tasks, so there is nothing to plan today.
```

## Implementation Summary

**Classes** (in `pawpal_system.py`):

- **Task**: one care activity (title, description, duration, priority, due time, frequency, completed flag). It can mark itself complete, be rescheduled, and report whether it is due.
- **Pet**: a pet's name, species and age, plus its own list of tasks. It adds and removes tasks (ignoring duplicates and missing tasks) and returns the pending ones.
- **Owner**: the owner's name, email, daily time budget (`available_minutes_per_day`) and a list of pets. `get_all_tasks()` combines the tasks of every pet.
- **Scheduler**: plans for one owner. It never reads a single pet's list; it always calls `owner.get_all_tasks()`, so every pet is included.

**Scheduling behavior:**

- Completed tasks are excluded. The rest are considered by priority (high, then medium, then low), with ties broken by earliest time.
- A task is kept if it fits in the owner's remaining minutes; otherwise it is skipped and listed in the explanation. The kept tasks are shown in time order, and tasks with no time go last.
- Conflicts are detected by overlap: a task occupies `[due_time, due_time + duration)`, so two tasks conflict if their ranges overlap. Back-to-back tasks do not conflict. Conflicts are reported, not removed from the plan.
- `frequency` is descriptive only; the scheduler plans a single day.

**Run the demo:** `python main.py` (the output is shown in Sample Output above).

**Run the tests:** `python -m pytest`

## 🧪 Testing PawPal+

Run the full test suite from the project folder:

```bash
python -m pytest
```

Add `-v` to list every test. The suite is in `tests/test_pawpal.py` (35 tests). It uses fixed dates, so results do not depend on the clock. It covers:

- **Task completion and management:** `mark_complete()`, adding and removing tasks, duplicate and unknown items, pending tasks, and an owner and scheduler seeing tasks from several pets (including a pet with no tasks).
- **Chronological sorting:** shuffled times come out in order, tasks with no time go last, equal times keep their input order, and an empty list is fine. Priority sorting is also tested.
- **Recurring tasks:** daily (+1 day) and weekly (+7 days) repeats, month and year rollover, details preserved, the original stays complete while the copy starts incomplete, one-time tasks don't repeat, repeated completion doesn't duplicate, and future repeats stay out of today's plan.
- **Conflict detection:** same start time, partial overlap, touching and distant tasks, conflicts across pets and within one pet, plus empty lists, missing times, bad durations and different dates. The warning messages are also checked.
- **Filtering:** by completion status, by pet name (case-insensitive), by both, and cases where nothing matches.
- **Daily plan:** completed tasks are skipped, the time budget is respected, and the explanation lists planned tasks, skipped tasks and conflicts.

Actual output of the last run:

```
============================= test session starts =============================
platform win32 -- Python 3.12.2, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\A110 Project 2\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 35 items

tests\test_pawpal.py ...................................                 [100%]

============================= 35 passed in 0.05s ==============================
```

### Confidence Level: ★★★★☆ (4 of 5)

All 35 tests pass, including edge cases for empty input, missing times and repeated completion. I did not measure code coverage. Remaining limitations:

- The Streamlit UI (`app.py`) has no automated tests. It was only checked with a scripted run and by hand.
- A recurring task with no `due_date` repeats from the real current date, and that path is not tested with a fixed date.
- Tasks with no time are never reported as conflicts.
- The planner is greedy, so it can leave available minutes unused when a better combination of tasks exists.

## 📐 Smarter Scheduling

All of these live in `pawpal_system.py`, are covered by `tests/test_pawpal.py`, and are shown by `python main.py`.

- **Sorting:** `Scheduler.sort_by_time(tasks)` returns a new list ordered by `due_time` using `sorted()` with a key. Tasks with no `due_time` go last, and the original list is not changed. `Scheduler.sort_by_priority(tasks)` orders high, then medium, then low (unknown values last), with ties broken by time.
- **Filtering:** `Scheduler.filter_tasks(completed=None, pet_name=None)` returns tasks from all of the owner's pets, optionally limited by completion status and/or pet name (case-insensitive). `Pet.get_pending_tasks()` does the same for a single pet.
- **Conflict detection:** `Scheduler.detect_conflicts(tasks)` returns pairs of tasks whose time ranges overlap. A task occupies `[due_time, due_time + duration_minutes)`, so a task that starts exactly when another ends is not a conflict. Tasks with no time, or a zero or negative duration, are ignored, and tasks on different `due_date`s never conflict. `Scheduler.conflict_warnings()` turns the pairs into readable messages naming each task, its pet and its time range. Conflicts are only reported; the scheduler never blocks or moves tasks.
- **Recurring tasks:** `Pet.complete_task(task)` marks a task complete and, for `daily` or `weekly` tasks, adds the next occurrence made by `Task.next_occurrence()`. The new `due_date` is the old `due_date` plus 1 day (daily) or 7 days (weekly), using `timedelta`. The copy keeps the title, description, duration, priority, time and frequency, and starts incomplete. Completing the same task twice, or when an identical pending copy already exists, adds nothing. `once` tasks do not repeat. Calling `Task.mark_complete()` directly only marks the task done and does not create a repeat.

**Limitations:** a task with no `due_date` is treated as "today", so its repeat is dated from today's date. `generate_daily_plan()` plans one day and leaves out tasks dated in the future. Tasks without a time are never reported as conflicts. Conflict detection compares every pair of tasks (O(n²)), which is fine for a typical day's task list.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time`, `sort_by_priority` | `sorted()` with a key; tasks with no time go last; input list is not modified |
| Filtering | `Scheduler.filter_tasks(completed, pet_name)` | Works across all pets; either filter can be omitted |
| Conflict handling | `Scheduler.detect_conflicts`, `conflict_warnings` | Overlapping `[time, time + duration)` ranges on the same date; touching tasks and tasks with no time are ignored |
| Recurring tasks | `Task.next_occurrence`, `Pet.complete_task` | Completing a daily/weekly task adds the next copy with a future `due_date`; "once" tasks don't repeat |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
