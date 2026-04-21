from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from tick.core.models import Task, TaskPriority, TaskStatus
from tick.core.services import calendar_counts, group_by_category, is_overdue, list_view_tasks, resolve_due_date, stats, visible_in_list


def _task(
    *,
    tid: str,
    title: str,
    status: TaskStatus,
    due: date | None,
    priority: TaskPriority | None,
    created: datetime,
    completed_at: datetime | None = None,
    category: str | None = None,
) -> Task:
    return Task(
        id=tid,
        title=title,
        status=status,
        priority=priority,
        due_date=due,
        category=category,
        note=None,
        created_at=created,
        completed_at=completed_at,
    )


def test_visibility_completed_hide_after_one_day() -> None:
    today = date(2026, 4, 20)
    show = _task(
        tid="1",
        title="a",
        status=TaskStatus.COMPLETED,
        due=None,
        priority=None,
        created=datetime(2026, 4, 20, 12, 0),
        completed_at=datetime(2026, 4, 20, 10, 0),
    )
    hide = _task(
        tid="2",
        title="b",
        status=TaskStatus.COMPLETED,
        due=None,
        priority=None,
        created=datetime(2026, 4, 19, 12, 0),
        completed_at=datetime(2026, 4, 19, 10, 0),
    )
    assert visible_in_list(show, today=today)
    assert not visible_in_list(hide, today=today)


def test_overdue_and_sorting_rules() -> None:
    today = date(2026, 4, 20)
    tasks = [
        _task(
            tid="a",
            title="a",
            status=TaskStatus.PENDING,
            due=date(2026, 4, 22),
            priority=TaskPriority.LOW,
            created=datetime(2026, 4, 20, 10, 0),
        ),
        _task(
            tid="b",
            title="b",
            status=TaskStatus.PENDING,
            due=date(2026, 4, 21),
            priority=TaskPriority.MEDIUM,
            created=datetime(2026, 4, 20, 9, 0),
        ),
        _task(
            tid="c",
            title="c",
            status=TaskStatus.PENDING,
            due=date(2026, 4, 21),
            priority=TaskPriority.HIGH,
            created=datetime(2026, 4, 20, 8, 0),
        ),
        _task(
            tid="d",
            title="d",
            status=TaskStatus.PENDING,
            due=None,
            priority=None,
            created=datetime(2026, 4, 20, 7, 0),
        ),
    ]
    sorted_tasks = list_view_tasks(tasks, today=today)
    assert [t.id for t in sorted_tasks] == ["c", "b", "a", "d"]
    overdue = _task(
        tid="x",
        title="x",
        status=TaskStatus.PENDING,
        due=today - timedelta(days=1),
        priority=None,
        created=datetime(2026, 4, 10, 7, 0),
    )
    assert is_overdue(overdue, today=today)


def test_group_calendar_stats() -> None:
    tasks = [
        _task(
            tid="1",
            title="a",
            status=TaskStatus.PENDING,
            due=date(2026, 4, 20),
            priority=None,
            created=datetime(2026, 4, 20, 10, 0),
            category="工作",
        ),
        _task(
            tid="2",
            title="b",
            status=TaskStatus.COMPLETED,
            due=date(2026, 4, 20),
            priority=None,
            created=datetime(2026, 4, 20, 11, 0),
            completed_at=datetime(2026, 4, 20, 12, 0),
            category=None,
        ),
    ]
    grouped = group_by_category(tasks)
    assert set(grouped.keys()) == {"工作", "未分类"}
    counts = calendar_counts(tasks)
    assert counts[date(2026, 4, 20)] == 2
    s = stats(tasks)
    assert (s.total, s.completed, s.pending) == (2, 1, 1)


def test_resolve_due_date_presets() -> None:
    today = date(2026, 4, 20)  # Monday
    assert resolve_due_date(preset="none", custom_due="", today=today) is None
    assert resolve_due_date(preset="today", custom_due="", today=today) == date(2026, 4, 20)
    assert resolve_due_date(preset="tomorrow", custom_due="", today=today) == date(2026, 4, 21)
    assert resolve_due_date(preset="week", custom_due="", today=today) == date(2026, 4, 26)
    assert resolve_due_date(preset="custom", custom_due="2026-05-01", today=today) == date(2026, 5, 1)
    with pytest.raises(ValueError):
        resolve_due_date(preset="custom", custom_due="", today=today)
