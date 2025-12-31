This repo is a sandbox.
Goal: learn what Codex can do.
Eventually: small automation or Revit-related tooling.

## Revit task planner (text-based)

Use `revit_task_planner.py` to add, list, complete, and reprioritize tasks from the terminal. Tasks can include optional due dates so overdue work floats to the top when listing.

### Quick start
1. Make sure you have Python 3 available (`python --version`).
2. From this folder, run `python revit_task_planner.py --help` to see all commands.
3. Try the minimal smoke test below to confirm it works end-to-end:

```bash
python revit_task_planner.py add "Collect door schedule" --priority 2 --due-date 2024-05-15
python revit_task_planner.py list
python revit_task_planner.py complete 1
python revit_task_planner.py list
```

Open tasks are shown first; completed tasks move to the bottom with a ✅ icon. Overdue items with a due date highlight at the top of the list. Data is stored in `revit_tasks.json` in this directory so the list persists between runs. If you want to start fresh, delete that file (`rm revit_tasks.json`).

If you run into issues:

- Blank titles are rejected to keep the list readable. Provide a short description for each task.
- If `revit_tasks.json` gets corrupted (e.g., you edited it manually), the CLI will explain what went wrong and prompt you to fix or delete the file.

### More examples

```bash
# Add a high-priority task (1 = highest)
python revit_task_planner.py add "Export sheets to PDF" --priority 1

# Add with a due date and see it bubble up when overdue
python revit_task_planner.py add "Print door schedule" --due-date 2024-05-10

# Change priority after the fact
python revit_task_planner.py prioritize 2 2
```
