from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from tick.core.models import Task, TaskPriority, TaskStatus

PRIORITY_ORDER: dict[TaskPriority | None, int] = {
    TaskPriority.HIGH: 0,
    TaskPriority.MEDIUM: 1,
    TaskPriority.LOW: 2,
    None: 3,
}


@dataclass(slots=True)
class Stats:
    total: int
    completed: int
    pending: int


def is_overdue(task: Task, today: date | None = None) -> bool:
    day = today or date.today()
    return task.status == TaskStatus.PENDING and task.due_date is not None and task.due_date < day


def visible_in_list(task: Task, today: date | None = None) -> bool:
    day = today or date.today()
    if task.status != TaskStatus.COMPLETED:
        return True
    if task.completed_at is None:
        return False
    return task.completed_at.date() == day


def list_view_tasks(tasks: list[Task], today: date | None = None) -> list[Task]:
    day = today or date.today()
    visible = [task for task in tasks if visible_in_list(task, day)]
    return sorted(
        visible,
        key=lambda task: (
            task.due_date is None,
            task.due_date or date.max,
            PRIORITY_ORDER[task.priority],
            task.created_at,
        ),
    )


def group_by_category(tasks: list[Task]) -> dict[str, list[Task]]:
    grouped: dict[str, list[Task]] = defaultdict(list)
    for task in tasks:
        grouped[task.category or "未分类"].append(task)
    return dict(sorted(grouped.items(), key=lambda item: item[0]))


def calendar_counts(tasks: list[Task]) -> dict[date, int]:
    counts: dict[date, int] = defaultdict(int)
    for task in tasks:
        if task.due_date:
            counts[task.due_date] += 1
    return dict(counts)


def stats(tasks: list[Task]) -> Stats:
    total = len(tasks)
    completed = sum(task.status == TaskStatus.COMPLETED for task in tasks)
    return Stats(total=total, completed=completed, pending=total - completed)


def resolve_due_date(
    *,
    preset: str,
    custom_due: str,
    today: date | None = None,
) -> date | None:
    day = today or date.today()
    if preset == "none":
        return None
    if preset == "today":
        return day
    if preset == "tomorrow":
        return day + timedelta(days=1)
    if preset == "week":
        return day + timedelta(days=6 - day.weekday())
    if preset == "custom":
        if not custom_due:
            raise ValueError("custom due date is required")
        return date.fromisoformat(custom_due)
    raise ValueError(f"unknown due date preset: {preset}")
