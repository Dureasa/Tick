from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from uuid import uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid due_date format: {value}, expected YYYY-MM-DD") from exc


def parse_iso_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid datetime format: {value}") from exc


@dataclass(slots=True)
class Task:
    id: str
    title: str
    status: TaskStatus
    priority: TaskPriority | None
    due_date: date | None
    category: str | None
    note: str | None
    created_at: datetime
    completed_at: datetime | None

    @staticmethod
    def new(
        title: str,
        due_date: date | None = None,
        priority: TaskPriority | None = None,
        category: str | None = None,
        note: str | None = None,
    ) -> "Task":
        title = title.strip()
        if not title:
            raise ValueError("title is required")
        now = datetime.now().replace(microsecond=0)
        return Task(
            id=str(uuid4()),
            title=title,
            status=TaskStatus.PENDING,
            priority=priority,
            due_date=due_date,
            category=category.strip() if category else None,
            note=note.strip() if note else None,
            created_at=now,
            completed_at=None,
        )

    @staticmethod
    def from_dict(data: dict[str, object]) -> "Task":
        title = str(data.get("title", "")).strip()
        if not title:
            raise ValueError("title is required")

        status_raw = data.get("status")
        try:
            status = TaskStatus(str(status_raw))
        except ValueError as exc:
            raise ValueError(f"Invalid status: {status_raw}") from exc

        priority_raw = data.get("priority")
        priority: TaskPriority | None = None
        if priority_raw is not None:
            try:
                priority = TaskPriority(str(priority_raw))
            except ValueError as exc:
                raise ValueError(f"Invalid priority: {priority_raw}") from exc

        due_date_raw = data.get("due_date")
        due_date = parse_iso_date(str(due_date_raw)) if due_date_raw else None

        created_at_raw = data.get("created_at")
        if not created_at_raw:
            raise ValueError("created_at is required")
        created_at = parse_iso_datetime(str(created_at_raw))

        completed_at_raw = data.get("completed_at")
        completed_at = parse_iso_datetime(str(completed_at_raw)) if completed_at_raw else None

        return Task(
            id=str(data.get("id") or uuid4()),
            title=title,
            status=status,
            priority=priority,
            due_date=due_date,
            category=str(data.get("category")).strip() if data.get("category") else None,
            note=str(data.get("note")).strip() if data.get("note") else None,
            created_at=created_at,
            completed_at=completed_at,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value if self.priority else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "category": self.category,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def toggle_completed(self) -> None:
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.now().replace(microsecond=0)
            return
        self.status = TaskStatus.PENDING
        self.completed_at = None

    def update(
        self,
        *,
        title: str,
        due_date: date | None,
        priority: TaskPriority | None,
        category: str | None,
        note: str | None,
    ) -> None:
        title = title.strip()
        if not title:
            raise ValueError("title is required")
        self.title = title
        self.due_date = due_date
        self.priority = priority
        self.category = category.strip() if category else None
        self.note = note.strip() if note else None

