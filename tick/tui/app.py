from __future__ import annotations

import calendar
from datetime import date

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import ContentSwitcher, DataTable, Footer, Header, Label, OptionList
from textual.widgets.option_list import Option

from tick.core.models import Task
from tick.core.services import calendar_counts, group_by_category, is_overdue, list_view_tasks, stats
from tick.storage.json_store import JsonStore
from tick.tui.screens import ConfirmScreen, TaskFormResult, TaskFormScreen, TaskListScreen


class TickApp(App[None]):
    TITLE = "Tick"
    CSS = """
    Screen {
        layout: vertical;
    }

    #main-shell {
        width: 100%;
        height: 1fr;
        border: round $primary;
        padding: 0 1;
    }

    #top-bar {
        width: 100%;
        height: 1;
        content-align: left middle;
        border-bottom: solid $primary;
    }

    #main-body {
        width: 100%;
        height: 1fr;
    }

    #status-bar {
        width: 100%;
        height: 1;
        border-top: solid $primary;
        content-align: left middle;
    }

    #list-view, #calendar-view, #category-view {
        width: 100%;
        height: 1fr;
    }

    OptionList {
        border: none;
    }

    DataTable {
        border: none;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("n", "new_task", "新建"),
        Binding("e", "edit_task", "编辑"),
        Binding("d", "delete_task", "删除"),
        Binding("1", "switch_view('list')", "清单视图"),
        Binding("2", "switch_view('calendar')", "日历视图"),
        Binding("3", "switch_view('category')", "分类视图"),
        Binding("j,down", "cursor_down", "下移"),
        Binding("k,up", "cursor_up", "上移"),
    ]

    def __init__(self, store: JsonStore | None = None) -> None:
        super().__init__()
        self.store = store or JsonStore()
        self.tasks: list[Task] = []
        self._current_view = "list"
        self._selected_task_id: str | None = None
        self._list_task_ids: list[str] = []
        self._calendar_dates: list[date] = []
        self._calendar_tasks_by_day: dict[date, list[Task]] = {}
        self._category_line_items: list[tuple[str, str | None]] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="main-shell"):
            yield Label("", id="top-bar")
            with ContentSwitcher(initial="list-view", id="main-body"):
                yield OptionList(id="list-view")
                yield DataTable(id="calendar-view")
                yield OptionList(id="category-view")
            yield Label("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.tasks = self.store.load_tasks()
        config = self.store.load_config()
        saved_theme = config.get("theme")
        if saved_theme:
            self.theme = saved_theme
        self._refresh_all()
        self.set_focus(self.query_one("#list-view", OptionList))

    def watch_theme(self, old_theme: str, new_theme: str) -> None:
        config = self.store.load_config()
        config["theme"] = new_theme
        self.store.save_config(config)

    def _refresh_all(self) -> None:
        self._render_list_view()
        self._render_calendar_view()
        self._render_category_view()
        self._update_header()
        self._update_status_bar()
        self.query_one("#main-body", ContentSwitcher).current = f"{self._current_view}-view"

    def _view_name(self) -> str:
        return {"list": "清单视图", "calendar": "日历视图", "category": "分类视图"}[self._current_view]

    def _update_header(self) -> None:
        self.query_one("#top-bar", Label).update(f" Tick  [{self._view_name()}]")

    def _update_status_bar(self) -> None:
        s = stats(self.tasks)
        self.query_one("#status-bar", Label).update(
            f" 总数:{s.total} | 已完成:{s.completed} | 当前:{self._view_name()} | 1/2/3切换 n新建 e编辑 d删除 Enter切换 q退出"
        )

    def _task_to_line(self, task: Task, today: date) -> Text:
        status_icon = "[x]" if task.status.value == "completed" else "[ ]"
        due = task.due_date.isoformat() if task.due_date else "-"
        pri = task.priority.value if task.priority else "-"
        cat = task.category or "未分类"
        line = Text(f"{status_icon} {task.title} | 截止:{due} | 优先级:{pri} | 分类:{cat}")
        if task.priority and task.status.value != "completed":
            if task.priority.value == "high":
                line.stylize("bold red")
            elif task.priority.value == "medium":
                line.stylize("yellow")
            else:
                line.stylize("green")
        if is_overdue(task, today):
            line.stylize("reverse red")
        if task.status.value == "completed":
            line.stylize("dim")
        return line

    def _render_list_view(self) -> None:
        today = date.today()
        option_list = self.query_one("#list-view", OptionList)
        option_list.clear_options()
        tasks = list_view_tasks(self.tasks, today=today)
        self._list_task_ids = [task.id for task in tasks]
        if not tasks:
            option_list.add_option(Option("暂无任务，按 n 新建", id="empty"))
            option_list.highlighted = 0
            return
        for task in tasks:
            option_list.add_option(Option(self._task_to_line(task, today), id=task.id))
        if self._selected_task_id and self._selected_task_id in self._list_task_ids:
            option_list.highlighted = self._list_task_ids.index(self._selected_task_id)
        else:
            option_list.highlighted = 0
            self._selected_task_id = self._list_task_ids[0]

    def _render_calendar_view(self) -> None:
        table = self.query_one("#calendar-view", DataTable)
        table.clear(columns=True)
        table.cursor_type = "cell"
        table.add_columns(*["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        today = date.today()
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdatescalendar(today.year, today.month)
        counts = calendar_counts(self.tasks)
        tasks_by_day: dict[date, list[Task]] = {}
        for task in self.tasks:
            if task.due_date:
                tasks_by_day.setdefault(task.due_date, []).append(task)
        self._calendar_tasks_by_day = tasks_by_day
        self._calendar_dates = []
        for week in month_days:
            row = []
            for day in week:
                count = counts.get(day, 0)
                label = f"{day.day:02d}"
                if count:
                    label += f"({count})"
                if day.month != today.month:
                    label = f".{label}"
                overdue_has = any(is_overdue(task, today=today) for task in tasks_by_day.get(day, []))
                if overdue_has:
                    row.append(Text(label, style="reverse red"))
                elif count > 0:
                    row.append(Text(label, style="bold cyan"))
                else:
                    row.append(label)
                self._calendar_dates.append(day)
            table.add_row(*row)
        table.move_cursor(row=0, column=0)

    def _render_category_view(self) -> None:
        option_list = self.query_one("#category-view", OptionList)
        option_list.clear_options()
        groups = group_by_category(self.tasks)
        self._category_line_items = []
        if not groups:
            option_list.add_option(Option("暂无分类任务", id="empty"))
            option_list.highlighted = 0
            return
        for key, items in groups.items():
            option_list.add_option(Option(Text(f"【{key}】({len(items)})", style="bold cyan"), id=f"cat:{key}"))
            self._category_line_items.append((key, None))
            for task in list_view_tasks(items):
                line = self._task_to_line(task, date.today())
                line = Text("  ") + line
                option_list.add_option(Option(line, id=f"task:{task.id}"))
                self._category_line_items.append((key, task.id))
        option_list.highlighted = 0

    def _find_task(self, task_id: str | None) -> Task | None:
        if not task_id:
            return None
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def _selected_list_task(self) -> Task | None:
        option_list = self.query_one("#list-view", OptionList)
        idx = option_list.highlighted
        if idx is None or idx < 0 or idx >= len(self._list_task_ids):
            return None
        task_id = self._list_task_ids[idx]
        self._selected_task_id = task_id
        return self._find_task(task_id)

    def action_new_task(self) -> None:
        def handle_result(result: TaskFormResult | None) -> None:
            if not result:
                return
            task = Task.new(
                title=result["title"],
                due_date=result["due_date"],
                priority=result["priority"],
                category=result["category"],
                note=result["note"],
            )
            self.tasks.append(task)
            self._selected_task_id = task.id
            self.store.save_tasks(self.tasks)
            self._refresh_all()

        self.push_screen(TaskFormScreen(), callback=handle_result)

    def action_edit_task(self) -> None:
        task = self._selected_list_task()
        if task is None:
            self.notify("当前视图无可编辑任务", severity="warning")
            return

        def handle_result(result: TaskFormResult | None) -> None:
            if not result:
                return
            task.update(
                title=result["title"],
                due_date=result["due_date"],
                priority=result["priority"],
                category=result["category"],
                note=result["note"],
            )
            self.store.save_tasks(self.tasks)
            self._refresh_all()

        self.push_screen(TaskFormScreen(task=task), callback=handle_result)

    def action_delete_task(self) -> None:
        task = self._selected_list_task()
        if task is None:
            self.notify("当前视图无可删除任务", severity="warning")
            return

        def handle_result(confirm: bool) -> None:
            if not confirm:
                return
            nonlocal task
            self.tasks = [item for item in self.tasks if item.id != task.id]
            self._selected_task_id = self.tasks[0].id if self.tasks else None
            self.store.save_tasks(self.tasks)
            self._refresh_all()

        self.push_screen(ConfirmScreen(f"确认删除任务：{task.title} ?"), callback=handle_result)

    def action_toggle_task(self) -> None:
        if self._current_view == "list":
            task = self._selected_list_task()
            if task is None:
                return
            task.toggle_completed()
            self.store.save_tasks(self.tasks)
            self._refresh_all()
            return
        if self._current_view == "calendar":
            table = self.query_one("#calendar-view", DataTable)
            coord = table.cursor_coordinate
            day = self._calendar_dates[coord.row * 7 + coord.column]
            day_tasks = self._calendar_tasks_by_day.get(day, [])
            if not day_tasks:
                self.notify(f"{day.isoformat()} 无任务")
                return
            lines = [self._task_to_line(task, today=date.today()) for task in list_view_tasks(day_tasks)]
            self.push_screen(TaskListScreen(title=f"{day.isoformat()} 任务详情", lines=lines))
            return
        if self._current_view == "category":
            option_list = self.query_one("#category-view", OptionList)
            idx = option_list.highlighted
            if idx is None or idx < 0 or idx >= len(self._category_line_items):
                return
            category, task_id = self._category_line_items[idx]
            if task_id:
                task = self._find_task(task_id)
                if task:
                    task.toggle_completed()
                    self.store.save_tasks(self.tasks)
                    self._refresh_all()
                return
            grouped = group_by_category(self.tasks).get(category, [])
            lines = [self._task_to_line(task, today=date.today()) for task in list_view_tasks(grouped)]
            self.push_screen(TaskListScreen(title=f"分类：{category}", lines=lines))

    def action_switch_view(self, view_name: str) -> None:
        if view_name not in {"list", "calendar", "category"}:
            return
        self._current_view = view_name
        self.query_one("#main-body", ContentSwitcher).current = f"{view_name}-view"
        if view_name == "list":
            self.set_focus(self.query_one("#list-view", OptionList))
        elif view_name == "calendar":
            self.set_focus(self.query_one("#calendar-view", DataTable))
        else:
            self.set_focus(self.query_one("#category-view", OptionList))
        self._update_header()
        self._update_status_bar()

    def action_cursor_down(self) -> None:
        if self._current_view == "list":
            self.query_one("#list-view", OptionList).action_cursor_down()
            self._selected_list_task()
        elif self._current_view == "calendar":
            self.query_one("#calendar-view", DataTable).action_cursor_down()
        else:
            self.query_one("#category-view", OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        if self._current_view == "list":
            self.query_one("#list-view", OptionList).action_cursor_up()
            self._selected_list_task()
        elif self._current_view == "calendar":
            self.query_one("#calendar-view", DataTable).action_cursor_up()
        else:
            self.query_one("#category-view", OptionList).action_cursor_up()

    @on(OptionList.OptionSelected, "#list-view")
    def on_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id in {None, "empty"}:
            return
        self._selected_task_id = event.option.id
        task = self._find_task(event.option.id)
        if task:
            task.toggle_completed()
            self.store.save_tasks(self.tasks)
            self._refresh_all()

    @on(OptionList.OptionSelected, "#category-view")
    def on_category_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id in {None, "empty"}:
            return
        if event.option.id.startswith("task:"):
            task_id = event.option.id.split(":", maxsplit=1)[1]
            task = self._find_task(task_id)
            if task:
                task.toggle_completed()
                self.store.save_tasks(self.tasks)
                self._refresh_all()
            return
        if event.option.id.startswith("cat:"):
            category = event.option.id.split(":", maxsplit=1)[1]
            grouped = group_by_category(self.tasks).get(category, [])
            lines = [self._task_to_line(task, today=date.today()) for task in list_view_tasks(grouped)]
            self.push_screen(TaskListScreen(title=f"分类：{category}", lines=lines))

    @on(DataTable.CellSelected, "#calendar-view")
    def on_calendar_cell_selected(self, event: DataTable.CellSelected) -> None:
        day = self._calendar_dates[event.coordinate.row * 7 + event.coordinate.column]
        day_tasks = self._calendar_tasks_by_day.get(day, [])
        if not day_tasks:
            self.notify(f"{day.isoformat()} 无任务")
            return
        lines = [self._task_to_line(task, today=date.today()) for task in list_view_tasks(day_tasks)]
        self.push_screen(TaskListScreen(title=f"{day.isoformat()} 任务详情", lines=lines))
