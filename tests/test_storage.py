from __future__ import annotations

import json
from datetime import date

from tick.core.models import Task, TaskPriority
from tick.storage.json_store import JsonStore


def test_store_initializes_layout(tmp_path) -> None:
    store = JsonStore(root=tmp_path / ".tick")
    assert store.tasks_file.exists()
    assert store.config_file.exists()
    payload = json.loads(store.tasks_file.read_text(encoding="utf-8"))
    assert payload == {"tasks": []}


def test_store_save_and_load(tmp_path) -> None:
    store = JsonStore(root=tmp_path / ".tick")
    task = Task.new(title="任务", due_date=date(2026, 4, 25), priority=TaskPriority.HIGH, category="工作", note="备注")
    store.save_tasks([task])
    loaded = store.load_tasks()
    assert len(loaded) == 1
    got = loaded[0]
    assert got.title == "任务"
    assert got.due_date == date(2026, 4, 25)
    assert got.priority == TaskPriority.HIGH


def test_store_invalid_tasks_schema(tmp_path) -> None:
    store = JsonStore(root=tmp_path / ".tick")
    store.tasks_file.write_text('{"tasks": {}}', encoding="utf-8")
    try:
        store.load_tasks()
    except ValueError as exc:
        assert "tasks must be a list" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

