from __future__ import annotations

import json
from pathlib import Path

from tick.core.models import Task


class JsonStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.home() / ".tick"
        self.tasks_file = self.root / "tasks.json"
        self.config_file = self.root / "config.json"
        self._ensure_layout()

    def _ensure_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.tasks_file.exists():
            self._atomic_write(self.tasks_file, {"tasks": []})
        if not self.config_file.exists():
            self._atomic_write(
                self.config_file,
                {
                    "keys": {
                        "new": "n",
                        "edit": "e",
                        "delete": "d",
                        "quit": "q",
                        "list_view": "1",
                        "calendar_view": "2",
                        "category_view": "3",
                    }
                },
            )

    def _atomic_write(self, path: Path, data: dict[str, object]) -> None:
        temp = path.with_suffix(path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        temp.replace(path)

    def load_tasks(self) -> list[Task]:
        with self.tasks_file.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        tasks_data = raw.get("tasks", [])
        if not isinstance(tasks_data, list):
            raise ValueError("tasks.json format invalid: tasks must be a list")
        return [Task.from_dict(item) for item in tasks_data]

    def save_tasks(self, tasks: list[Task]) -> None:
        payload = {"tasks": [task.to_dict() for task in tasks]}
        self._atomic_write(self.tasks_file, payload)

    def load_config(self) -> dict[str, object]:
        with self.config_file.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def save_config(self, config: dict[str, object]) -> None:
        self._atomic_write(self.config_file, config)

