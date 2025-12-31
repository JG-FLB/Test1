"""Simple text-based Revit task planner.

This CLI lets you add, list, complete, and reprioritize tasks without
needing Revit itself. Data is stored locally in ``revit_tasks.json`` so it
persists between runs.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import date, datetime
from typing import List

DATA_FILE = Path("revit_tasks.json")


@dataclass
class Task:
    task_id: int
    title: str
    priority: int = 3
    status: str = "open"
    due_date: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            task_id=int(data["task_id"]),
            title=str(data["title"]),
            priority=int(data.get("priority", 3)),
            status=str(data.get("status", "open")),
            due_date=data.get("due_date"),
        )

    def mark_done(self) -> None:
        self.status = "done"

    def set_priority(self, priority: int) -> None:
        self.priority = priority

    def due_date_as_date(self) -> date | None:
        if not self.due_date:
            return None
        try:
            return datetime.strptime(self.due_date, "%Y-%m-%d").date()
        except ValueError:
            return None

    def is_overdue(self, today: date | None = None) -> bool:
        today = today or date.today()
        due = self.due_date_as_date()
        if due is None:
            return False
        return self.status != "done" and due < today


class TaskStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> List[Task]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text())
        return [Task.from_dict(item) for item in data]

    def save(self, tasks: List[Task]) -> None:
        self.path.write_text(json.dumps([asdict(task) for task in tasks], indent=2))


class TaskPlanner:
    def __init__(self, store: TaskStore) -> None:
        self.store = store

    def add(self, title: str, priority: int, due_date: str | None) -> Task:
        tasks = self.store.load()
        next_id = 1 if not tasks else max(task.task_id for task in tasks) + 1
        task = Task(task_id=next_id, title=title, priority=priority, due_date=due_date)
        tasks.append(task)
        self.store.save(tasks)
        return task

    def list_tasks(self) -> List[Task]:
        return self.store.load()

    def complete(self, task_id: int) -> Task:
        tasks = self.store.load()
        for task in tasks:
            if task.task_id == task_id:
                task.mark_done()
                self.store.save(tasks)
                return task
        raise ValueError(f"Task {task_id} not found")

    def prioritize(self, task_id: int, priority: int) -> Task:
        tasks = self.store.load()
        for task in tasks:
            if task.task_id == task_id:
                task.set_priority(priority)
                self.store.save(tasks)
                return task
        raise ValueError(f"Task {task_id} not found")


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid integer: {value}") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("Value must be positive")
    return number


def parse_due_date(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Due date must be in YYYY-MM-DD format"
        ) from exc
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Text-based Revit task planner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", help="Short description of the task")
    add_parser.add_argument(
        "--priority",
        type=positive_int,
        default=3,
        help="Priority (1=highest, larger=lower priority)",
    )
    add_parser.add_argument(
        "--due-date",
        type=parse_due_date,
        help="Due date in YYYY-MM-DD format",
    )

    subparsers.add_parser("list", help="List tasks")

    complete_parser = subparsers.add_parser("complete", help="Mark a task as done")
    complete_parser.add_argument("task_id", type=positive_int, help="Task ID to complete")

    prioritize_parser = subparsers.add_parser(
        "prioritize", help="Update the priority of a task"
    )
    prioritize_parser.add_argument("task_id", type=positive_int, help="Task ID to update")
    prioritize_parser.add_argument("priority", type=positive_int, help="New priority value")

    return parser


def format_task(task: Task) -> str:
    status_icon = "✅" if task.status == "done" else "⬜"
    due_part = f" (due {task.due_date})" if task.due_date else ""
    overdue_note = " ⚠️ OVERDUE" if task.is_overdue() else ""
    return f"{status_icon} [{task.task_id}] (P{task.priority}) {task.title}{due_part}{overdue_note}"


def handle_add(args: argparse.Namespace, planner: TaskPlanner) -> None:
    task = planner.add(args.title, args.priority, args.due_date)
    due_text = f" due {task.due_date}" if task.due_date else ""
    print(
        f"Added task #{task.task_id}: {task.title} (priority {task.priority}){due_text}"
    )


def handle_list(_: argparse.Namespace, planner: TaskPlanner) -> None:
    tasks = planner.list_tasks()
    if not tasks:
        print(
            "No tasks yet. Add one with \"python revit_task_planner.py add 'Install add-in'\"."
        )
        return

    for task in sorted(tasks, key=task_sort_key):
        print(format_task(task))


def handle_complete(args: argparse.Namespace, planner: TaskPlanner) -> None:
    task = planner.complete(args.task_id)
    print(f"Marked task #{task.task_id} as done: {task.title}")


def handle_prioritize(args: argparse.Namespace, planner: TaskPlanner) -> None:
    task = planner.prioritize(args.task_id, args.priority)
    print(f"Updated task #{task.task_id} priority to {task.priority}")


def task_sort_key(task: Task) -> tuple:
    overdue_rank = 0 if task.is_overdue() else 1
    status_rank = 0 if task.status == "open" else 1
    due_date_value = task.due_date_as_date() or date.max
    return (overdue_rank, status_rank, due_date_value, task.priority, task.task_id)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    planner = TaskPlanner(TaskStore(DATA_FILE))
    handlers = {
        "add": handle_add,
        "list": handle_list,
        "complete": handle_complete,
        "prioritize": handle_prioritize,
    }

    handler = handlers[args.command]
    handler(args, planner)


if __name__ == "__main__":
    main()
