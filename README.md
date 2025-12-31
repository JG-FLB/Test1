This repo is a sandbox.
Goal: learn what Codex can do.
Eventually: small automation or Revit-related tooling.

## Revit task planner (text-based)

Use `revit_task_planner.py` to add, list, complete, and reprioritize tasks from the terminal.

### Quick start
1. Make sure you have Python 3 available (`python --version`).
2. From this folder, run `python revit_task_planner.py --help` to see all commands.
3. Try the minimal smoke test below to confirm it works end-to-end:

```bash
python revit_task_planner.py add "Collect door schedule" --priority 2
python revit_task_planner.py list
python revit_task_planner.py complete 1
python revit_task_planner.py list
```

Open tasks are shown first; completed tasks move to the bottom with a ✅ icon. Data is stored in `revit_tasks.json` in this directory so the list persists between runs. If you want to start fresh, delete that file (`rm revit_tasks.json`).

### More examples

```bash
# Add a high-priority task (1 = highest)
python revit_task_planner.py add "Export sheets to PDF" --priority 1

# Change priority after the fact
python revit_task_planner.py prioritize 2 2
```
