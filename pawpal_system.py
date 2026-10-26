"""PawPal+ system skeleton: Owner, Pet, Task, and Scheduler classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time


@dataclass
class Task:
    """A single pet-care task (e.g. a walk, feeding, or medication)."""

    title: str
    description: str
    duration_minutes: int
    priority: str
    due_time: time
    frequency: str
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        raise NotImplementedError

    def reschedule(self, new_time: time) -> None:
        """Move this task to a new due time."""
        raise NotImplementedError

    def is_due(self, now: datetime) -> bool:
        """Return True if this task is due at the given moment."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet owned by an Owner, with its own list of care tasks."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        raise NotImplementedError

    def get_pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that are not yet completed."""
        raise NotImplementedError


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(
        self,
        name: str,
        email: str,
        available_minutes_per_day: int,
        pets: list[Pet] | None = None,
    ) -> None:
        self.name = name
        self.email = email
        self.available_minutes_per_day = available_minutes_per_day
        self.pets: list[Pet] = pets if pets is not None else []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        raise NotImplementedError

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        raise NotImplementedError


class Scheduler:
    """Builds and explains a daily care plan for an Owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_daily_plan(self) -> list[Task]:
        """Return the ordered list of tasks planned for today."""
        raise NotImplementedError

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return the tasks sorted by due time."""
        raise NotImplementedError

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return the tasks sorted by priority."""
        raise NotImplementedError

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple]:
        """Return pairs of tasks whose scheduled times conflict."""
        raise NotImplementedError

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the daily plan."""
        raise NotImplementedError
