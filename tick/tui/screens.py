from __future__ import annotations

from datetime import date
from typing import TypedDict

from textual import on
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, OptionList, Select, TextArea
from textual.widgets.option_list import Option

from tick.core.models import Task, TaskPriority
from tick.core.services import resolve_due_date


PRIORITY_OPTIONS = [
    ("无", "none"),
    ("high", "high"),
    ("medium", "medium"),
    ("low", "low"),
]

DUE_DATE_OPTIONS = [
    ("无", "none"),
    ("今日", "today"),
    ("明日", "tomorrow"),
    ("本周", "week"),
    ("自定义", "custom"),
]


class TaskFormResult(TypedDict):
    title: str
    due_date: date | None
    priority: TaskPriority | None
    category: str | None
    note: str | None


class TaskFormScreen(ModalScreen[TaskFormResult | None]):
    CSS = """
    TaskFormScreen {
        align: center middle;
    }

    #task-form {
        width: 80;
        max-width: 90%;
        height: auto;
        border: round $accent;
        padding: 1 2;
        background: $surface;
    }

    .row {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }

    #task-note {
        height: 6;
    }

    #task-buttons {
        width: 100%;
        height: auto;
        align: right middle;
        margin-top: 1;
    }
    """

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, task: Task | None = None) -> None:
        super().__init__()
        self._task = task

    def compose(self):
        due_date_value = self._task.due_date.isoformat() if self._task and self._task.due_date else ""
        due_preset = "custom" if due_date_value else "none"
        selected_priority = self._task.priority.value if self._task and self._task.priority else "none"
        yield Container(
            Vertical(
                Label("编辑任务" if self._task else "新建任务"),
                Label("标题（必填）"),
                Input(value=self._task.title if self._task else "", id="task-title", placeholder="输入任务标题"),
                Label("时间选择"),
                Select(DUE_DATE_OPTIONS, value=due_preset, allow_blank=False, id="task-due-preset"),
                Label("自定义日期（YYYY-MM-DD，仅自定义时生效）"),
                Input(value=due_date_value, id="task-due-date", placeholder="例如 2026-04-25"),
                Label("优先级（可选）"),
                Select(PRIORITY_OPTIONS, value=selected_priority, allow_blank=False, id="task-priority"),
                Label("分类（可选）"),
                Input(value=self._task.category if self._task and self._task.category else "", id="task-category", placeholder="例如 工作"),
                Label("备注（可选）"),
                TextArea(text=self._task.note if self._task and self._task.note else "", id="task-note"),
                Horizontal(
                    Button("取消", id="cancel", variant="default"),
                    Button("保存", id="save", variant="primary"),
                    id="task-buttons",
                ),
            ),
            id="task-form",
        )

    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def on_save(self) -> None:
        title = self.query_one("#task-title", Input).value.strip()
        if not title:
            self.notify("标题不能为空", severity="error")
            return

        due_date_raw = self.query_one("#task-due-date", Input).value.strip()
        due_preset = str(self.query_one("#task-due-preset", Select).value)
        try:
            due_date = resolve_due_date(preset=due_preset, custom_due=due_date_raw)
        except ValueError:
            self.notify("日期选择无效，自定义需 YYYY-MM-DD", severity="error")
            return

        priority_raw = self.query_one("#task-priority", Select).value
        priority = None if priority_raw == "none" else TaskPriority(str(priority_raw))
        category = self.query_one("#task-category", Input).value.strip() or None
        note = self.query_one("#task-note", TextArea).text.strip() or None
        self.dismiss(TaskFormResult(title=title, due_date=due_date, priority=priority, category=category, note=note))


class ConfirmScreen(ModalScreen[bool]):
    CSS = """
    ConfirmScreen {
        align: center middle;
    }

    #confirm-box {
        width: 60;
        max-width: 90%;
        height: auto;
        border: round $warning;
        padding: 1 2;
        background: $surface;
    }

    #confirm-buttons {
        width: 100%;
        height: auto;
        align: right middle;
        margin-top: 1;
    }
    """

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self):
        yield Container(
            Vertical(
                Label(self._message),
                Horizontal(
                    Button("取消", id="cancel", variant="default"),
                    Button("确认", id="confirm", variant="error"),
                    id="confirm-buttons",
                ),
            ),
            id="confirm-box",
        )

    def action_cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#confirm")
    def on_confirm(self) -> None:
        self.dismiss(True)


class TaskListScreen(ModalScreen[None]):
    CSS = """
    TaskListScreen {
        align: center middle;
    }

    #task-list-box {
        width: 90;
        max-width: 95%;
        height: 24;
        border: round $accent;
        padding: 1;
        background: $surface;
    }

    #task-list {
        width: 100%;
        height: 1fr;
    }
    """

    BINDINGS = [("escape,q", "dismiss", "Close")]

    def __init__(self, title: str, lines: list[object]) -> None:
        super().__init__()
        self._title = title
        self._lines = lines

    def compose(self):
        options = [Option(line) for line in self._lines] if self._lines else [Option("暂无任务")]
        yield Container(
            Vertical(
                Label(self._title),
                OptionList(*options, id="task-list"),
            ),
            id="task-list-box",
        )
