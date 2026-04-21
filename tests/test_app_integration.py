from __future__ import annotations

from datetime import date, datetime

import pytest

from tick.core.models import Task, TaskPriority, TaskStatus
from tick.storage.json_store import JsonStore
from tick.tui.app import TickApp


@pytest.mark.asyncio
async def test_app_boot_and_view_switch(tmp_path) -> None:
    store = JsonStore(root=tmp_path / ".tick")
    store.save_tasks(
        [
            Task(
                id="t1",
                title="任务1",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                due_date=date.today(),
                category="工作",
                note=None,
                created_at=datetime.now().replace(microsecond=0),
                completed_at=None,
            )
        ]
    )
    app = TickApp(store=store)
    async with app.run_test() as pilot:
        assert app._current_view == "list"  # noqa: SLF001
        await pilot.press("2")
        assert app._current_view == "calendar"  # noqa: SLF001
        await pilot.press("3")
        assert app._current_view == "category"  # noqa: SLF001
        await pilot.press("1")
        assert app._current_view == "list"  # noqa: SLF001


@pytest.mark.asyncio
async def test_toggle_completion_from_list(tmp_path) -> None:
    store = JsonStore(root=tmp_path / ".tick")
    task = Task.new(title="任务切换")
    store.save_tasks([task])
    app = TickApp(store=store)
    async with app.run_test() as pilot:
        assert app.tasks[0].status == TaskStatus.PENDING
        await pilot.press("enter")
        assert app.tasks[0].status == TaskStatus.COMPLETED
        await pilot.press("enter")
        assert app.tasks[0].status == TaskStatus.PENDING
