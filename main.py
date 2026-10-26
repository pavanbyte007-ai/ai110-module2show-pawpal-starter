"""Demo script for PawPal+: sorting, filtering, recurring tasks, and conflicts."""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def describe(task: Task, pet_of: dict[int, str]) -> str:
    """Return a one-line, human-readable description of a task."""
    when = task.due_time.strftime("%H:%M") if task.due_time else "Anytime"
    on = f" on {task.due_date}" if task.due_date else ""
    status = "done" if task.completed else "pending"
    return (
        f"{when:<8} {pet_of.get(id(task), '?'):<8} {task.title} "
        f"({task.duration_minutes} min, {task.priority}, {task.frequency}, {status}){on}"
    )


def show(heading: str, tasks: list[Task], pet_of: dict[int, str]) -> None:
    """Print a heading followed by one line per task."""
    print(f"\n{heading}")
    print("-" * 60)
    if not tasks:
        print("(none)")
    for task in tasks:
        print(describe(task, pet_of))


def main() -> None:
    owner = Owner(name="Jordan", email="jordan@example.com", available_minutes_per_day=90)
    buddy = Pet(name="Buddy", species="dog", age=4)
    whiskers = Pet(name="Whiskers", species="cat", age=2)
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    # Added deliberately out of time order.
    buddy.add_task(Task("Dinner", "Feed one cup of dry food", 10, "high", time(18, 0), "daily"))
    whiskers.add_task(Task("Playtime", "Interactive toy session", 20, "medium", time(17, 45), "daily"))
    buddy.add_task(Task("Morning walk", "30-minute walk", 30, "high", time(7, 30), "daily"))
    whiskers.add_task(Task("Brush fur", "Brush coat", 15, "low", None, "weekly"))
    whiskers.add_task(Task("Medication", "Thyroid pill with a treat", 5, "high", time(8, 0), "daily"))
    buddy.add_task(Task("Bath", "Full bath and towel dry", 45, "low", time(15, 0), "weekly"))
    buddy.add_task(Task("Vet visit", "Annual check-up", 40, "medium", time(17, 50), "once"))

    scheduler = Scheduler(owner)
    pet_of = {id(t): pet.name for pet in owner.pets for t in pet.tasks}

    print("=" * 60)
    print(f"PawPal+ demo for {owner.name} ({', '.join(p.name for p in owner.pets)})")
    print("=" * 60)

    show("1. Tasks as entered (out of order)", owner.get_all_tasks(), pet_of)
    show("2. Sorted by time (missing times last)",
         scheduler.sort_by_time(owner.get_all_tasks()), pet_of)

    show("3a. Filter: Whiskers' tasks", scheduler.filter_tasks(pet_name="Whiskers"), pet_of)
    next(t for t in buddy.tasks if t.title == "Morning walk").mark_complete()
    show("3b. Filter: completed tasks (all pets)", scheduler.filter_tasks(completed=True), pet_of)
    show("3c. Filter: Buddy's pending tasks",
         scheduler.filter_tasks(completed=False, pet_name="Buddy"), pet_of)

    print("\n4. Conflict detection (pending tasks, all pets)")
    print("-" * 60)
    # Vet visit (17:50) deliberately overlaps Playtime (17:45-18:05) and Dinner (18:00).
    warnings = scheduler.conflict_warnings()
    for warning in warnings:
        print(f"WARNING: {warning}")
    if not warnings:
        print("No conflicts.")

    print("\n5. Recurring tasks")
    print("-" * 60)
    dinner = next(t for t in buddy.tasks if t.title == "Dinner")
    dinner.due_date = date.today()
    repeat = buddy.complete_task(dinner)
    print(f"Completed '{dinner.title}' (daily) -> next one created for {repeat.due_date}")
    print(f"Completing it again adds nothing new: {buddy.complete_task(dinner)}")
    vet = next(t for t in buddy.tasks if t.title == "Vet visit")
    print(f"Completed 'Vet visit' (once) -> next one created: {buddy.complete_task(vet)}")
    pet_of = {id(t): pet.name for pet in owner.pets for t in pet.tasks}

    plan = scheduler.generate_daily_plan()
    show("6. Today's plan (future repeats and completed tasks left out)", plan, pet_of)

    print("\n7. Plan explanation")
    print("-" * 60)
    print(scheduler.explain_plan())

    print("\n8. Empty owner")
    print("-" * 60)
    print(Scheduler(Owner("Solo", "solo@example.com", 60)).explain_plan())


if __name__ == "__main__":
    main()
