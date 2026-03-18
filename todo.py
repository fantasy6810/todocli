#!/usr/bin/env python
import click
import json
import os
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table

DATA_FILE = "data/tasks.json"
console = Console()


def load_tasks():
    """Load tasks from the JSON data file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(tasks):
    """Save tasks to the JSON data file."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


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
    tasks = load_tasks()
    new_id = max((t["id"] for t in tasks), default=0) + 1
    new_task = {
        "id": new_id,
        "task": task,
        "priority": priority.lower(),
        "status": "pending",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    tasks.append(new_task)
    save_tasks(tasks)
    console.print(f"[green]✓[/green] Added task #{new_id}: {task}")


@cli.command("list")
def list_tasks():
    """Display all tasks in a formatted table."""
    tasks = load_tasks()
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
        color = priority_colors.get(t["priority"], "white")
        status_display = "✓ done" if t["status"] == "done" else "○ pending"
        table.add_row(
            str(t["id"]),
            t["task"],
            f"[{color}]{t['priority']}[/{color}]",
            status_display,
        )

    console.print(table)


@cli.command()
@click.argument("task_id", type=int)
def complete(task_id):
    """Mark a task as done by its ID."""
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            save_tasks(tasks)
            console.print(f"[green]✓[/green] Completed: {t['task']}")
            return
    console.print(f"[red]✗[/red] Task #{task_id} not found.")


@cli.command()
@click.argument("task_id", type=int)
def delete(task_id):
    """Remove a task by its ID."""
    tasks = load_tasks()
    original_len = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) < original_len:
        save_tasks(tasks)
        console.print(f"[green]✓[/green] Deleted task #{task_id}")
    else:
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
    tasks = load_tasks()
    if not tasks:
        console.print("[yellow]No tasks to export.[/yellow]")
        return
    with open(output, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)
    console.print(f"[green]✓[/green] Exported to {output}")


if __name__ == "__main__":
    cli()