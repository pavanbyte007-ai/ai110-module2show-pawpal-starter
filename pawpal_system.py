"""PawPal+ system: Owner, Pet, Task, and Scheduler classes."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from itertools import combinations
from datetime import date, datetime, time, timedelta

# Higher number = more important. Unknown priorities rank below "low".
PRIORITY_RANK: dict[str, int] = {"low": 1, "medium": 2, "high": 3}


def _priority_rank(task: Task) -> int:
    """Return the numeric rank of a task's priority (case-insensitive)."""
    return PRIORITY_RANK.get(str(task.priority).strip().lower(), 0)


def _minutes(t: time) -> int:
    """Return minutes since midnight for a time of day."""
    return t.hour * 60 + t.minute


def _overlaps(a: Task, b: Task) -> bool:
    """Return True if two timed tasks on the same date overlap (touching is fine)."""
    if a.due_time is None or b.due_time is None or a.due_date != b.due_date:
        return False
    a_start, b_start = _minutes(a.due_time), _minutes(b.due_time)
    a_end = a_start + max(a.duration_minutes, 0)
    b_end = b_start + max(b.duration_minutes, 0)
    return a_start < b_end and b_start < a_end


def _span(task: Task) -> str:
    """Return a task's time range like '08:00-08:30' (or just the start time)."""
    if task.due_time is None:
        return "any time"
    start = _minutes(task.due_time)
    end = start + max(task.duration_minutes, 0)
    return f"{start // 60:02d}:{start % 60:02d}-{end // 60 % 24:02d}:{end % 60:02d}"


def _contains(items: list, obj: object) -> bool:
    """Return True if obj is in items by identity (dataclass == compares fields)."""
    return any(item is obj for item in items)


@dataclass
class Task:
    """A single pet-care task (e.g. a walk, feeding, or medication).

    ``due_time`` is a time of day and may be None for unscheduled tasks.
    ``frequency`` is "once", "daily" or "weekly". ``due_date`` is optional:
    None means "today / whenever", and repeated tasks get a date so they do
    not show up in today's plan.
    """

    title: str
    description: str
    duration_minutes: int
    priority: str
    due_time: time | None
    frequency: str
    completed: bool = False
    due_date: date | None = None

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def reschedule(self, new_time: time) -> None:
        """Move this task to a new due time."""
        self.due_time = new_time

    def is_due(self, now: datetime) -> bool:
        """Return True if this task is incomplete and its due time has arrived.

        A task with no due time is considered due whenever it is incomplete.
        A task dated in the future is not due; one dated in the past is overdue.
        """
        if self.completed:
            return False
        if self.due_date is not None:
            if self.due_date > now.date():
                return False
            if self.due_date < now.date():
                return True
        if self.due_time is None:
            return True
        return self.due_time <= now.time()

    def next_occurrence(self) -> Task | None:
        """Return a fresh, incomplete copy for the next repeat, or None.

        Daily tasks repeat one day later and weekly tasks seven days later,
        counted from ``due_date`` (or today if it has none). One-time and
        unknown frequencies do not repeat.
        """
        days = {"daily": 1, "weekly": 7}.get(str(self.frequency).strip().lower())
        if days is None:
            return None
        base = self.due_date or date.today()
        return replace(self, completed=False, due_date=base + timedelta(days=days))


@dataclass
class Pet:
    """A pet owned by an Owner, with its own list of care tasks."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet (ignored if this exact task is already added)."""
        if not _contains(self.tasks, task):
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet (ignored if it is not present)."""
        self.tasks = [t for t in self.tasks if t is not task]

    def complete_task(self, task: Task) -> Task | None:
        """Complete a task and queue its next repeat; return the new task, if any.

        Does nothing for an unknown or already-completed task, and does not add
        a repeat that this pet already has, so nothing is duplicated.
        """
        if not _contains(self.tasks, task) or task.completed:
            return None
        task.mark_complete()
        nxt = task.next_occurrence()
        if nxt is None:
            return None
        if any(
            (t.title, t.due_time, t.due_date) == (nxt.title, nxt.due_time, nxt.due_date)
            and not t.completed
            for t in self.tasks
        ):
            return None
        self.tasks.append(nxt)
        return nxt

    def get_pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(
        self,
        name: str,
        email: str,
        available_minutes_per_day: int,
        pets: list[Pet] | None = None,
    ) -> None:
        """Create an owner with a daily time budget and optional starting pets."""
        self.name = name
        self.email = email
        self.available_minutes_per_day = available_minutes_per_day
        self.pets: list[Pet] = []
        for pet in pets or []:
            self.add_pet(pet)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner (ignored if this exact pet is already added)."""
        if not _contains(self.pets, pet):
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner (ignored if it is not present)."""
        self.pets = [p for p in self.pets if p is not pet]

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds and explains a daily care plan for an Owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans for the given owner's pets."""
        self.owner = owner
        self._skipped: list[Task] = []

    def generate_daily_plan(self, today: date | None = None) -> list[Task]:
        """Return the ordered list of tasks planned for today.

        Tasks come from ``owner.get_all_tasks()`` (all pets). Completed tasks
        are excluded. Remaining tasks are considered most important first
        (priority, then earliest time) and kept while they fit within the
        owner's ``available_minutes_per_day``; tasks that don't fit are
        skipped but smaller later ones may still fit. The chosen tasks are
        returned in time order. Tasks dated after ``today`` (default: the real
        date) are left out.
        """
        today = today or date.today()
        pending = [
            t
            for t in self.owner.get_all_tasks()
            if not t.completed and (t.due_date is None or t.due_date <= today)
        ]
        budget = max(self.owner.available_minutes_per_day, 0)
        chosen: list[Task] = []
        self._skipped = []
        for task in self.sort_by_priority(pending):
            duration = max(task.duration_minutes, 0)
            if duration <= budget:
                chosen.append(task)
                budget -= duration
            else:
                self._skipped.append(task)
        return self.sort_by_time(chosen)

    def filter_tasks(
        self, completed: bool | None = None, pet_name: str | None = None
    ) -> list[Task]:
        """Return tasks across all pets, optionally by completion and/or pet name.

        ``None`` means "don't filter on that". Pet names match case-insensitively.
        """
        wanted = pet_name.strip().lower() if pet_name else None
        return [
            task
            for pet in self.owner.pets
            if wanted is None or pet.name.lower() == wanted
            for task in pet.tasks
            if completed is None or task.completed == completed
        ]

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return the tasks sorted by due time (tasks with no time go last)."""
        return sorted(
            tasks,
            key=lambda t: (t.due_time is None, t.due_time or time.min),
        )

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return the tasks sorted by priority, highest first, ties by due time."""
        return sorted(
            self.sort_by_time(tasks),
            key=lambda t: -_priority_rank(t),
        )

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return pairs of tasks whose time ranges overlap.

        A task occupies [due_time, due_time + duration_minutes). Tasks that
        merely touch (one ends when the next starts) do not conflict, and
        tasks without a due time are ignored. Tasks on different due dates
        never conflict.
        """
        scheduled = [t for t in self.sort_by_time(tasks) if t.due_time is not None]
        return [
            (first, second)
            for first, second in combinations(scheduled, 2)
            if _overlaps(first, second)
        ]

    def conflict_warnings(self, tasks: list[Task] | None = None) -> list[str]:
        """Return one readable warning per overlapping pair (empty if none).

        Checks ``tasks`` (default: all of the owner's tasks that are not
        completed). Pets are named when known; conflicts are only reported,
        never prevented.
        """
        if tasks is None:
            tasks = self.filter_tasks(completed=False)
        pet_of = {id(t): p.name for p in self.owner.pets for t in p.tasks}
        warnings = []
        for first, second in self.detect_conflicts(tasks):
            warnings.append(
                f"{first.title} ({pet_of.get(id(first), '?')}, {_span(first)}) "
                f"overlaps {second.title} ({pet_of.get(id(second), '?')}, {_span(second)})"
            )
        return warnings

    def explain_plan(self, today: date | None = None) -> str:
        """Return a human-readable explanation of the daily plan."""
        plan = self.generate_daily_plan(today)
        budget = self.owner.available_minutes_per_day
        if not plan and not self._skipped:
            return "No pending tasks, so there is nothing to plan today."

        owners_of = {
            id(task): pet.name for pet in self.owner.pets for task in pet.tasks
        }
        used = sum(t.duration_minutes for t in plan)
        lines = [
            f"Daily plan for {self.owner.name}: {used} of {budget} available minutes used.",
            "Tasks are chosen by priority (high first), then earliest time, "
            "and shown in time order.",
        ]
        for task in plan:
            when = task.due_time.strftime("%H:%M") if task.due_time else "any time"
            lines.append(
                f"  {when} - {task.title} for {owners_of.get(id(task), '?')} "
                f"({task.duration_minutes} min) [priority: {task.priority}]"
            )
        if self._skipped:
            lines.append("Skipped (not enough time left):")
            for task in self._skipped:
                lines.append(
                    f"  {task.title} for {owners_of.get(id(task), '?')} "
                    f"({task.duration_minutes} min) [priority: {task.priority}]"
                )
        for warning in self.conflict_warnings(plan):
            lines.append(f"Warning - conflict: {warning}")
        return "\n".join(lines)
