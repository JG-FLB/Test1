"""Simple text-based Revit task planner.

This CLI lets you add, list, complete, and reprioritize tasks without
needing Revit itself. Data is stored locally in ``revit_tasks.json`` so it
persists between runs.
"""
from __future__ import annotations

import argparse
import json
import sys
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
        # Convert raw dict data (typically loaded from JSON) into a Task instance.
        return cls(
            task_id=int(data["task_id"]),
            title=str(data["title"]),
            priority=int(data.get("priority", 3)),
            status=str(data.get("status", "open")),
            due_date=data.get("due_date"),
        )

    def mark_done(self) -> None:
        # Update the status flag so the task is treated as completed.
        self.status = "done"

    def set_priority(self, priority: int) -> None:
        # Store the new priority value (smaller numbers mean higher priority).
        self.priority = priority

    def due_date_as_date(self) -> date | None:
        # Parse the optional YYYY-MM-DD due date string into a ``date`` object.
        if not self.due_date:
            return None
        try:
            return datetime.strptime(self.due_date, "%Y-%m-%d").date()
        except ValueError:
            return None

    def is_overdue(self, today: date | None = None) -> bool:
        # Determine if a task is past its due date and still open.
        today = today or date.today()
        due = self.due_date_as_date()
        if due is None:
            return False
        return self.status != "done" and due < today


class TaskStore:
    # Handles reading and writing tasks to the local JSON file.
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> List[Task]:
        # Load tasks from disk, returning an empty list if the file does not exist.
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Could not read tasks from {self.path}: invalid JSON. "
                "Delete or fix the file and try again."
            ) from exc
        return [Task.from_dict(item) for item in data]

    def save(self, tasks: List[Task]) -> None:
        # Persist the current task list to disk in a human-readable format.
        self.path.write_text(json.dumps([asdict(task) for task in tasks], indent=2))


class TaskPlanner:
    # Core operations for adding, listing, completing, and prioritizing tasks.
    def __init__(self, store: TaskStore) -> None:
        self.store = store

    def add(self, title: str, priority: int, due_date: str | None) -> Task:
        # Create a new task, assign it the next ID, and save it.
        if not title.strip():
            raise ValueError("Title cannot be empty")
        tasks = self.store.load()
        next_id = 1 if not tasks else max(task.task_id for task in tasks) + 1
        task = Task(task_id=next_id, title=title, priority=priority, due_date=due_date)
        tasks.append(task)
        self.store.save(tasks)
        return task

    def list_tasks(self) -> List[Task]:
        # Fetch the current list of tasks from storage.
        return self.store.load()

    def complete(self, task_id: int) -> Task:
        # Mark the matching task as done; raise an error if it does not exist.
        tasks = self.store.load()
        for task in tasks:
            if task.task_id == task_id:
                task.mark_done()
                self.store.save(tasks)
                return task
        raise ValueError(f"Task {task_id} not found")

    def prioritize(self, task_id: int, priority: int) -> Task:
        # Update the priority for the requested task; raise an error if missing.
        tasks = self.store.load()
        for task in tasks:
            if task.task_id == task_id:
                task.set_priority(priority)
                self.store.save(tasks)
                return task
        raise ValueError(f"Task {task_id} not found")


def positive_int(value: str) -> int:
    # argparse helper to ensure numeric arguments are positive integers.
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid integer: {value}") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("Value must be positive")
    return number


def parse_due_date(value: str | None) -> str | None:
    # argparse helper to validate the optional YYYY-MM-DD due date format.
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
    # Define CLI commands, arguments, and help text for the planner.
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
    # Produce a human-readable string with status, ID, priority, and due info.
    status_icon = "✅" if task.status == "done" else "⬜"
    due_part = f" (due {task.due_date})" if task.due_date else ""
    overdue_note = " ⚠️ OVERDUE" if task.is_overdue() else ""
    return f"{status_icon} [{task.task_id}] (P{task.priority}) {task.title}{due_part}{overdue_note}"


def handle_add(args: argparse.Namespace, planner: TaskPlanner) -> None:
    # Command handler: add a new task and echo a confirmation message.
    task = planner.add(args.title, args.priority, args.due_date)
    due_text = f" due {task.due_date}" if task.due_date else ""
    print(
        f"Added task #{task.task_id}: {task.title} (priority {task.priority}){due_text}"
    )


def handle_list(_: argparse.Namespace, planner: TaskPlanner) -> None:
    # Command handler: list tasks, sorted to highlight overdue items first.
    tasks = planner.list_tasks()
    if not tasks:
        print(
            "No tasks yet. Add one with \"python revit_task_planner.py add 'Install add-in'\"."
        )
        return

    for task in sorted(tasks, key=task_sort_key):
        print(format_task(task))


def handle_complete(args: argparse.Namespace, planner: TaskPlanner) -> None:
    # Command handler: mark a task as done and confirm to the user.
    task = planner.complete(args.task_id)
    print(f"Marked task #{task.task_id} as done: {task.title}")


def handle_prioritize(args: argparse.Namespace, planner: TaskPlanner) -> None:
    # Command handler: update a task's priority and confirm the change.
    task = planner.prioritize(args.task_id, args.priority)
    print(f"Updated task #{task.task_id} priority to {task.priority}")


def task_sort_key(task: Task) -> tuple:
    # Sorting helper that surfaces overdue and open tasks before others.
    overdue_rank = 0 if task.is_overdue() else 1
    status_rank = 0 if task.status == "open" else 1
    due_date_value = task.due_date_as_date() or date.max
    return (overdue_rank, status_rank, due_date_value, task.priority, task.task_id)


def main() -> None:
    # Entrypoint: parse CLI args, route to the correct handler, and report errors.
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
    try:
        handler(args, planner)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
