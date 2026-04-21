from __future__ import annotations

from datetime import date, datetime

import pytest

from tick.core.models import Task, TaskPriority, TaskStatus, parse_iso_date


def test_task_new_and_toggle() -> None:
    task = Task.new(title="  写测试  ", due_date=date(2026, 4, 25), priority=TaskPriority.HIGH, category=" 工作 ", note=" 备注 ")
    assert task.title == "写测试"
    assert task.status == TaskStatus.PENDING
    assert task.category == "工作"
    assert task.note == "备注"
    task.toggle_completed()
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    task.toggle_completed()
    assert task.status == TaskStatus.PENDING
    assert task.completed_at is None


def test_task_roundtrip() -> None:
    payload = {
        "id": "id-1",
        "title": "任务A",
        "status": "pending",
        "priority": "medium",
        "due_date": "2026-04-25",
        "category": "工作",
        "note": "备注",
        "created_at": "2026-04-20T10:30:00",
        "completed_at": None,
    }
    task = Task.from_dict(payload)
    assert task.to_dict() == payload


def test_task_from_dict_validation() -> None:
    with pytest.raises(ValueError):
        Task.from_dict({"title": "x", "status": "bad", "created_at": "2026-04-20T10:30:00"})
    with pytest.raises(ValueError):
        Task.from_dict({"title": "x", "status": "pending", "priority": "bad", "created_at": "2026-04-20T10:30:00"})
    with pytest.raises(ValueError):
        Task.from_dict({"title": "x", "status": "pending", "created_at": "bad-date"})
    with pytest.raises(ValueError):
        parse_iso_date("2026/04/25")


def test_task_update_requires_title() -> None:
    task = Task.new(title="x")
    with pytest.raises(ValueError):
        task.update(title=" ", due_date=None, priority=None, category=None, note=None)
    task.update(
        title="y",
        due_date=None,
        priority=TaskPriority.LOW,
        category="a",
        note="b",
    )
    assert task.title == "y"
    assert task.priority == TaskPriority.LOW

