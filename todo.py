#!/usr/bin/env python
import click
import json
import os
from pathlib import Path
from datetime import datetime

from filelock import FileLock
from rich.console import Console
from rich.table import Table

DATA_FILE = "data/tasks.json"
LOCK_FILE = f"{DATA_FILE}.lock"
TASKS_LOCK = FileLock(LOCK_FILE)

console = Console()


def _load_tasks_unlocked():
    """Load tasks without acquiring the file lock."""
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError) as e:
        return _handle_corrupted_data(str(e))

    if not isinstance(data, list):
        return _handle_corrupted_data("does not contain a list")

    return data


def load_tasks():
    """Load tasks from the JSON data file."""
    with TASKS_LOCK:
        return _load_tasks_unlocked()


def _save_tasks_unlocked(tasks):
    """Save tasks without acquiring the file lock."""
    dirpath = os.path.dirname(DATA_FILE)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    temp_path = f"{DATA_FILE}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, DATA_FILE)


def save_tasks(tasks):
    """Save tasks to the JSON data file."""
    with TASKS_LOCK:
        _save_tasks_unlocked(tasks)


def _handle_corrupted_data(message: str | None = None):
    """Handle corrupted data file by backing it up and starting fresh."""
    from time import time
    ts = int(time())
    if os.path.exists(DATA_FILE):
        backup_path = f"{DATA_FILE}-{ts}.bak"
        os.rename(DATA_FILE, backup_path)
        console.print(
            f"[red]✗[/red] Corrupted data file detected. Backed up to {backup_path}. Starting with an empty task list.")

    if message:
        console.print(f"[red]✗[/red] {message}")

    return []


@click.group()
def cli():
    """todocli - A simple command-line to-do list manager."""
    pass


@cli.command()
# TODO: Implement shell completion for task names in the future
@click.argument('task', shell_complete=lambda ctx, param, incomplete: [])
@click.option(
    "--priority",
    type=click.Choice(["high", "medium", "low"], case_sensitive=False),
    default="medium",
    help="Priority level",
)
def add(task, priority):
    """Add a new task to the list."""
    with TASKS_LOCK:
        tasks = _load_tasks_unlocked()
        try:
            new_id = max((t.get("id", 0)
                          for t in tasks if isinstance(t, dict)), default=0) + 1
        except Exception as e:
            tasks = _handle_corrupted_data(str(e))
            new_id = 1
        new_task = {
            "id": new_id,
            "task": task,
            "priority": priority.lower(),
            "status": "pending",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        tasks.append(new_task)
        _save_tasks_unlocked(tasks)

    console.print(f"[green]✓[/green] Added task #{new_id}: {task}")


@cli.command("list")
def list_tasks():
    """Display all tasks in a formatted table."""
    with TASKS_LOCK:
        tasks = _load_tasks_unlocked()

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    table = Table(title="My Tasks", show_lines=True)
    table.add_column("ID", style="cyan", justify="right", width=4)
    table.add_column("Task", style="white", min_width=20)
    table.add_column("Priority", justify="center", width=8)
    table.add_column("Status", justify="center", width=10)

    priority_colors = {"high": "red", "medium": "yellow", "low": "green"}
    for t in tasks:
        if not isinstance(t, dict):
            continue
        priority = t.get("priority", "medium")
        color = priority_colors.get(priority, "white")
        status_display = "✓ done" if t.get("status") == "done" else "○ pending"
        table.add_row(
            str(t.get("id", "")),
            t.get("task", ""),
            f"[{color}]{priority}[/{color}]",
            status_display,
        )

    console.print(table)


@cli.command()
@click.argument("task_id", type=int)
def complete(task_id):
    """Mark a task as done by its ID."""
    with TASKS_LOCK:
        tasks = _load_tasks_unlocked()
        for t in tasks:
            if isinstance(t, dict) and t.get("id") == task_id:
                t["status"] = "done"
                _save_tasks_unlocked(tasks)
                console.print(
                    f"[green]✓[/green] Completed: {t.get('task', '')}")
                return

    console.print(f"[red]✗[/red] Task #{task_id} not found.")


@cli.command()
@click.argument("task_id", type=int)
def delete(task_id):
    """Remove a task by its ID."""
    with TASKS_LOCK:
        tasks = _load_tasks_unlocked()
        original_len = len(tasks)
        tasks = [t for t in tasks if not (
            isinstance(t, dict) and t.get("id") == task_id)]
        if len(tasks) < original_len:
            _save_tasks_unlocked(tasks)
            console.print(f"[green]✓[/green] Deleted task #{task_id}")
            return

    console.print(f"[red]✗[/red] Task #{task_id} not found.")


@cli.command()
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default="tasks_export.json",
    help="Output file path",
)
def export(output):
    """Export all tasks to a JSON file."""
    with TASKS_LOCK:
        tasks = _load_tasks_unlocked()

    if not tasks:
        console.print("[yellow]No tasks to export.[/yellow]")
        return
    with open(output, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)
    console.print(f"[green]✓[/green] Exported to {output}")


if __name__ == "__main__":
    cli()
