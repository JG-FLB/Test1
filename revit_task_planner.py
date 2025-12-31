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
from typing import List

DATA_FILE = Path("revit_tasks.json")


@dataclass
class Task:
    task_id: int
    title: str
    priority: int = 3
    status: str = "open"

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            task_id=int(data["task_id"]),
            title=str(data["title"]),
            priority=int(data.get("priority", 3)),
            status=str(data.get("status", "open")),
        )

    def mark_done(self) -> None:
        self.status = "done"

    def set_priority(self, priority: int) -> None:
        self.priority = priority


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

    def add(self, title: str, priority: int) -> Task:
        tasks = self.store.load()
        next_id = 1 if not tasks else max(task.task_id for task in tasks) + 1
        task = Task(task_id=next_id, title=title, priority=priority)
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
    return f"{status_icon} [{task.task_id}] (P{task.priority}) {task.title}"


def handle_add(args: argparse.Namespace, planner: TaskPlanner) -> None:
    task = planner.add(args.title, args.priority)
    print(f"Added task #{task.task_id}: {task.title} (priority {task.priority})")


def handle_list(_: argparse.Namespace, planner: TaskPlanner) -> None:
    tasks = planner.list_tasks()
    if not tasks:
        print(
            "No tasks yet. Add one with \"python revit_task_planner.py add 'Install add-in'\"."
        )
        return

    for task in sorted(tasks, key=lambda t: (t.status, t.priority, t.task_id)):
        print(format_task(task))


def handle_complete(args: argparse.Namespace, planner: TaskPlanner) -> None:
    task = planner.complete(args.task_id)
    print(f"Marked task #{task.task_id} as done: {task.title}")


def handle_prioritize(args: argparse.Namespace, planner: TaskPlanner) -> None:
    task = planner.prioritize(args.task_id, args.priority)
    print(f"Updated task #{task.task_id} priority to {task.priority}")


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
