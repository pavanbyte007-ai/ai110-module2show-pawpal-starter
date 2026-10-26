"""Tests for the PawPal+ core classes and scheduler.

All dates are fixed (never read from the clock) so results are repeatable.
Each test builds its own objects, so tests do not share state.
"""

import sys
from datetime import date, datetime, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

DAY = date(2030, 1, 1)  # a fixed "today" for every test


def make_task(
    title: str = "Morning walk",
    due: time | None = time(8, 0),
    duration: int = 30,
    priority: str = "high",
    frequency: str = "daily",
    due_date: date | None = DAY,
) -> Task:
    return Task(
        title=title,
        description=f"{title} description",
        duration_minutes=duration,
        priority=priority,
        due_time=due,
        frequency=frequency,
        due_date=due_date,
    )


@pytest.fixture
def setup() -> tuple[Scheduler, Pet, Pet]:
    """A scheduler for an owner with a dog and a cat (pytest builds a fresh one per test)."""
    owner = Owner("Jordan", "j@example.com", 120)
    dog = Pet("Buddy", "dog", 4)
    cat = Pet("Whiskers", "cat", 2)
    owner.add_pet(dog)
    owner.add_pet(cat)
    return Scheduler(owner), dog, cat


# ---- 4. task and pet management ----------------------------------------

def test_mark_complete_sets_completed_true():
    task = make_task()
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="dog", age=4)
    task = make_task()
    assert len(pet.tasks) == 0

    pet.add_task(task)

    assert len(pet.tasks) == 1
    assert pet.tasks[0] is task


def test_adding_same_task_twice_and_removing_unknown_task_are_safe():
    pet = Pet("Buddy", "dog", 4)
    task = make_task()
    pet.add_task(task)
    pet.add_task(task)
    pet.remove_task(make_task("never added"))

    assert pet.tasks == [task]
    pet.remove_task(task)
    assert pet.tasks == []


def test_pending_tasks_exclude_completed():
    pet = Pet("Buddy", "dog", 4)
    done, todo = make_task("done"), make_task("todo")
    pet.add_task(done)
    pet.add_task(todo)
    done.mark_complete()

    assert pet.get_pending_tasks() == [todo]


def test_owner_and_scheduler_see_tasks_from_every_pet(setup):
    scheduler, dog, cat = setup
    walk, meds = make_task("walk"), make_task("meds")
    dog.add_task(walk)
    cat.add_task(meds)

    assert scheduler.owner.get_all_tasks() == [walk, meds]
    assert {t.title for t in scheduler.generate_daily_plan(DAY)} == {"walk", "meds"}


def test_pet_with_no_tasks_and_duplicate_or_missing_pets(setup):
    scheduler, dog, cat = setup
    owner = scheduler.owner
    owner.add_pet(dog)               # duplicate add is ignored
    owner.remove_pet(Pet("Ghost", "other", 1))  # removing an unknown pet is ignored
    assert owner.pets == [dog, cat]
    assert owner.get_all_tasks() == []
    assert scheduler.generate_daily_plan(DAY) == []


# ---- 1. sorting ---------------------------------------------------------

def test_sort_by_time_orders_shuffled_tasks_chronologically(setup):
    scheduler, _, _ = setup
    tasks = [make_task(f"t{h}", time(h, 0)) for h in (18, 7, 12, 9)]

    result = scheduler.sort_by_time(tasks)

    assert [t.due_time.hour for t in result] == [7, 9, 12, 18]


def test_sort_by_time_puts_missing_times_last_and_keeps_input_unchanged(setup):
    scheduler, _, _ = setup
    late, none, early = make_task("late", time(18, 0)), make_task("none", None), make_task("early", time(7, 0))
    original = [late, none, early]

    result = scheduler.sort_by_time(original)

    assert [t.title for t in result] == ["early", "late", "none"]
    assert original == [late, none, early]


def test_sort_by_time_with_duplicate_times_keeps_input_order(setup):
    scheduler, _, _ = setup
    first, second = make_task("first", time(8, 0)), make_task("second", time(8, 0))

    assert scheduler.sort_by_time([first, second]) == [first, second]
    assert scheduler.sort_by_time([second, first]) == [second, first]


def test_sort_by_time_handles_empty_list(setup):
    scheduler, _, _ = setup
    assert scheduler.sort_by_time([]) == []


def test_sort_by_priority_high_first_then_time(setup):
    scheduler, _, _ = setup
    tasks = [
        make_task("low", time(7, 0), priority="low"),
        make_task("high-late", time(9, 0), priority="high"),
        make_task("high-early", time(8, 0), priority="high"),
    ]
    result = scheduler.sort_by_priority(tasks)
    assert [t.title for t in result] == ["high-early", "high-late", "low"]


# ---- 2. recurring tasks -------------------------------------------------

def test_completing_daily_task_creates_next_day_incomplete_copy(setup):
    _, dog, _ = setup
    task = make_task("walk", frequency="daily", due_date=date(2030, 1, 1))
    dog.add_task(task)

    new = dog.complete_task(task)

    assert task.completed is True                  # original stays completed
    assert new is not task and new.completed is False
    assert new.due_date == date(2030, 1, 2)
    assert len(dog.tasks) == 2


def test_daily_recurrence_rolls_over_month_and_year():
    task = make_task(due_date=date(2030, 12, 31), frequency="daily")
    assert task.next_occurrence().due_date == date(2031, 1, 1)


def test_completing_weekly_task_repeats_in_seven_days(setup):
    _, dog, _ = setup
    task = make_task("bath", frequency="weekly", due_date=date(2030, 1, 1))
    dog.add_task(task)

    new = dog.complete_task(task)

    assert new.due_date == date(2030, 1, 8)
    assert new.completed is False and task.completed is True


def test_next_occurrence_keeps_task_details():
    task = Task("Meds", "Thyroid pill", 5, "high", time(8, 0), "daily", due_date=DAY)

    new = task.next_occurrence()

    assert (new.title, new.description, new.duration_minutes, new.priority,
            new.due_time, new.frequency) == ("Meds", "Thyroid pill", 5, "high", time(8, 0), "daily")


@pytest.mark.parametrize("frequency", ["once", "sometimes", ""])
def test_one_time_and_unknown_frequencies_do_not_repeat(setup, frequency):
    _, dog, _ = setup
    task = make_task("vet", frequency=frequency)
    dog.add_task(task)

    assert dog.complete_task(task) is None
    assert dog.tasks == [task] and task.completed is True


def test_completing_repeatedly_does_not_duplicate_occurrences(setup):
    _, dog, _ = setup
    task = make_task("walk", frequency="daily")
    dog.add_task(task)

    dog.complete_task(task)
    dog.complete_task(task)
    dog.complete_task(task)

    assert len(dog.tasks) == 2
    assert len(dog.get_pending_tasks()) == 1


def test_complete_task_ignores_task_that_belongs_to_another_pet(setup):
    _, dog, cat = setup
    task = make_task("walk")
    dog.add_task(task)

    assert cat.complete_task(task) is None
    assert task.completed is False


def test_future_recurring_task_is_left_out_of_todays_plan(setup):
    scheduler, dog, _ = setup
    task = make_task("walk", frequency="daily", due_date=DAY)
    dog.add_task(task)
    dog.complete_task(task)  # tomorrow's copy exists now

    assert scheduler.generate_daily_plan(DAY) == []
    assert [t.title for t in scheduler.generate_daily_plan(date(2030, 1, 2))] == ["walk"]


def test_is_due_respects_due_date_and_time():
    now = datetime(2030, 1, 5, 12, 0)
    assert make_task(due_date=date(2030, 1, 6)).is_due(now) is False       # future
    assert make_task(due_date=date(2030, 1, 4), due=time(23, 0)).is_due(now) is True  # overdue
    assert make_task(due_date=date(2030, 1, 5), due=time(13, 0)).is_due(now) is False
    assert make_task(due_date=date(2030, 1, 5), due=time(11, 0)).is_due(now) is True
    assert make_task(due=None, due_date=date(2030, 1, 5)).is_due(now) is True  # no time: due all day
    done = make_task(due_date=date(2030, 1, 4))
    done.mark_complete()
    assert done.is_due(now) is False                                           # completed is never due


# ---- 3. conflict detection ----------------------------------------------

def test_tasks_with_same_start_time_conflict(setup):
    scheduler, _, _ = setup
    a, b = make_task("a", time(8, 0), 30), make_task("b", time(8, 0), 15)

    assert scheduler.detect_conflicts([a, b]) == [(a, b)]


def test_partially_overlapping_tasks_conflict(setup):
    scheduler, _, _ = setup
    walk, feed = make_task("walk", time(8, 0), 30), make_task("feed", time(8, 15), 10)

    assert scheduler.detect_conflicts([feed, walk]) == [(walk, feed)]


def test_touching_and_distant_tasks_do_not_conflict(setup):
    scheduler, _, _ = setup
    walk = make_task("walk", time(8, 0), 30)
    brush = make_task("brush", time(8, 30), 10)   # starts exactly when walk ends
    play = make_task("play", time(12, 0), 20)

    assert scheduler.detect_conflicts([play, brush, walk]) == []


def test_conflicts_found_across_pets_and_within_one_pet(setup):
    scheduler, dog, cat = setup
    walk = make_task("walk", time(8, 0), 30)
    feed = make_task("feed", time(8, 20), 10)    # same pet as walk
    meds = make_task("meds", time(8, 10), 5)     # other pet
    dog.add_task(walk)
    dog.add_task(feed)
    cat.add_task(meds)

    pairs = scheduler.detect_conflicts(scheduler.owner.get_all_tasks())

    assert (walk, meds) in pairs and (walk, feed) in pairs
    assert (meds, feed) not in pairs


def test_conflicts_ignore_empty_missing_times_bad_durations_and_other_dates(setup):
    scheduler, _, _ = setup
    assert scheduler.detect_conflicts([]) == []
    no_time = make_task("no time", None, 30)
    zero = make_task("zero", time(8, 0), 0)
    negative = make_task("negative", time(8, 0), -5)
    other_day = make_task("other day", time(8, 0), 30, due_date=date(2030, 1, 2))
    normal = make_task("normal", time(8, 0), 30)

    assert scheduler.detect_conflicts([no_time, zero, negative, other_day, normal]) == []


def test_conflict_warnings_name_tasks_pets_and_times(setup):
    scheduler, dog, cat = setup
    dog.add_task(make_task("walk", time(8, 0), 30))
    cat.add_task(make_task("meds", time(8, 10), 5))

    assert scheduler.conflict_warnings() == [
        "walk (Buddy, 08:00-08:30) overlaps meds (Whiskers, 08:10-08:15)"
    ]


def test_conflict_warnings_empty_without_tasks_and_skip_completed(setup):
    scheduler, dog, cat = setup
    assert scheduler.conflict_warnings() == []
    dog.add_task(make_task("walk", time(8, 0), 30))
    done = make_task("meds", time(8, 10), 5)
    done.mark_complete()
    cat.add_task(done)

    assert scheduler.conflict_warnings() == []


# ---- 5. filtering -------------------------------------------------------

def test_filter_by_completion_status_across_all_pets(setup):
    scheduler, dog, cat = setup
    walk, feed, meds = make_task("walk"), make_task("feed"), make_task("meds")
    dog.add_task(walk)
    dog.add_task(feed)
    cat.add_task(meds)
    feed.mark_complete()

    assert scheduler.filter_tasks() == [walk, feed, meds]
    assert scheduler.filter_tasks(completed=True) == [feed]
    assert scheduler.filter_tasks(completed=False) == [walk, meds]


def test_filter_by_pet_name_is_case_insensitive_and_combinable(setup):
    scheduler, dog, cat = setup
    walk, feed, meds = make_task("walk"), make_task("feed"), make_task("meds")
    dog.add_task(walk)
    dog.add_task(feed)
    cat.add_task(meds)
    feed.mark_complete()

    assert scheduler.filter_tasks(pet_name="whiskers") == [meds]
    assert scheduler.filter_tasks(completed=False, pet_name="Buddy") == [walk]
    assert scheduler.filter_tasks(completed=True, pet_name="BUDDY") == [feed]


def test_filter_returns_empty_list_when_nothing_matches(setup):
    scheduler, dog, _ = setup
    assert scheduler.filter_tasks() == []                    # no tasks at all
    dog.add_task(make_task("walk"))
    assert scheduler.filter_tasks(pet_name="Nobody") == []   # unknown pet
    assert scheduler.filter_tasks(completed=True) == []      # nothing completed
    assert scheduler.filter_tasks(completed=True, pet_name="Whiskers") == []


# ---- daily plan and explanation -----------------------------------------

def test_daily_plan_skips_completed_respects_budget_and_returns_time_order(setup):
    scheduler, dog, cat = setup
    scheduler.owner.available_minutes_per_day = 40
    dog.add_task(make_task("walk", time(8, 0), 30, "high"))
    cat.add_task(make_task("meds", time(7, 0), 5, "high"))
    cat.add_task(make_task("groom", time(9, 0), 30, "low"))   # does not fit
    done = make_task("done", time(6, 0), 5)
    done.mark_complete()
    cat.add_task(done)

    plan = scheduler.generate_daily_plan(DAY)

    assert [t.title for t in plan] == ["meds", "walk"]


def test_daily_plan_with_no_pets_is_empty_and_explained():
    scheduler = Scheduler(Owner("Solo", "s@example.com", 60))

    assert scheduler.generate_daily_plan(DAY) == []
    assert "nothing to plan" in scheduler.explain_plan(DAY)


def test_explain_plan_lists_tasks_skipped_tasks_and_conflicts(setup):
    scheduler, dog, cat = setup
    scheduler.owner.available_minutes_per_day = 40
    dog.add_task(make_task("walk", time(8, 0), 30))
    cat.add_task(make_task("meds", time(8, 10), 5))
    cat.add_task(make_task("groom", time(9, 0), 30, priority="low"))

    text = scheduler.explain_plan(DAY)

    assert "35 of 40" in text
    assert "walk for Buddy" in text and "meds for Whiskers" in text
    assert "Skipped" in text and "groom for Whiskers" in text
    assert "conflict" in text
