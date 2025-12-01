#!/usr/bin/env python3
import argparse
import sys
import json
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional

# Add src to path if running directly
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator import TodoOrchestrator
from src.alias import generate_alias, resolve_alias

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def format_task(task, full=False):
    if not task:
        return "Task not found."
    
    alias = generate_alias(task.id)
    if not full:
        task_id = f"{str(task.id)[:6]} ({alias})"

        # Format modified_at timestamp (just date and time, no microseconds)
        modified_str = task.modified_at.strftime("%Y-%m-%d %H:%M")
        
        if task.attachments:
            return f"{task_id:<20} @ | {task.status.ljust(10)} | {modified_str:<16} | {task.description.splitlines()[0]:<22}"
        else: 
            return f"{task_id:<22} | {task.status.ljust(10)} | {modified_str:<16} | {task.description.splitlines()[0]:<22}"
    
    lines = [
        f"ID:          {task.id} ({alias})",
        f"Description: {task.description}",
        f"Status:      {task.status}",
        f"Created:     {task.created_at}",
        f"Modified:    {task.modified_at}",
        f"Deadline:    {task.deadline}",
        f"ID (hash):   {task.version_hash}",
        f"Parent:      {task.parent}",
        "Attachments:"
    ]
    for att in task.attachments:
        lines.append(f"  - {att.filename} (Hash: {att.content_hash})")
    
    return "\n".join(lines)

def get_task_id(orch, id_str, allow_version=False):
    """
    Resolves an ID string to a Task object.
    If allow_version=True, supports versioned aliases like "Misty-Rat-2".
    Returns a Task object (either current or historical version).
    """
    try:
        # Try parsing as UUID
        task_id = UUID(id_str)
        return orch.get_task(task_id)
    except ValueError:
        # Try as alias
        candidates = list(orch.tasks.keys())
        resolved = resolve_alias(id_str, candidates)
        if resolved:
            uuid, version = resolved
            if version is not None and allow_version:
                # Get specific version
                return orch.get_task_version(uuid, version)
            else:
                # Get current version
                return orch.get_task(uuid)
        raise ValueError("Invalid UUID or Alias")

def render_kanban_board(tasks_by_status, statuses):
    """Renders tasks in a kanban board layout with ASCII box-drawing characters."""
    COL_WIDTH = 22
    
    # Prepare columns
    columns = []
    for status in statuses:
        tasks = tasks_by_status.get(status, [])
        col_data = []
        for task in tasks:
            alias = generate_alias(task.id)
            # Truncate description
            desc = task.description[:COL_WIDTH-2] if len(task.description) > COL_WIDTH-2 else task.description
            col_data.append(f"{desc}")
            col_data.append(f"({alias})")
            col_data.append("")  # Spacing
        columns.append(col_data)
    
    # Find max rows
    max_rows = max(len(col) for col in columns) if columns else 0
    
    # Pad columns to same height
    for col in columns:
        while len(col) < max_rows:
            col.append("")
    
    # Build output
    output = []
    
    # Top border
    top = "┌" + "┬".join(["─" * COL_WIDTH for _ in statuses]) + "┐"
    output.append(top)
    
    # Headers
    header_cells = [status.upper().center(COL_WIDTH)[:COL_WIDTH] for status in statuses]
    output.append("│" + "│".join(header_cells) + "│")
    
    # Header separator
    sep = "├" + "┼".join(["─" * COL_WIDTH for _ in statuses]) + "┤"
    output.append(sep)
    
    # Rows
    for row_idx in range(max_rows):
        row_cells = []
        for col in columns:
            cell = col[row_idx] if row_idx < len(col) else ""
            row_cells.append(cell.ljust(COL_WIDTH)[:COL_WIDTH])
        output.append("│" + "│".join(row_cells) + "│")
    
    # Bottom border
    bottom = "└" + "┴".join(["─" * COL_WIDTH for _ in statuses]) + "┘"
    output.append(bottom)
    
    return "\n".join(output)

# --- Command Handlers ---

def handle_add(orch, args):
    deadline = None
    if args.deadline:
        try:
            deadline = datetime.strptime(args.deadline, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            return

    task = orch.add_task(args.description, deadline=deadline)
    print(f"Task created: {task.id}")

def handle_list(orch, args):
    if not orch.tasks:
        print("No tasks found.")
    else:
        print(f"{'ID (ALIAS)':<22} | {'STATUS':<10} | {'MODIFIED':<16} | DESCRIPTION")
        print("-" * 120)
        for task in orch.tasks.values():
            if not args.all and task.archived:
                continue
            print(format_task(task))

def handle_show(orch, args):
    try:
        task = get_task_id(orch, args.id, allow_version=True)
        if task:
            print(format_task(task, full=True))
        else:
            print("Task not found.")
    except ValueError:
        print("Invalid UUID or Alias")

def handle_update(orch, args):
    try:
        task = get_task_id(orch, args.id)
        if not task:
            print("Task not found.")
            return
        
        updates = {}
        if args.desc:
            updates['description'] = args.desc
        if args.status:
            updates['status'] = args.status
        
        if updates:
            updated_task = orch.update_task(task.id, **updates)
            if updated_task:
                print("Task updated.")
                print(format_task(updated_task, full=True))
            else:
                print("Task not found.")
        else:
            print("No updates provided.")
    except ValueError:
        print("Invalid UUID or Alias")

def handle_attach(orch, args):
    try:
        task = get_task_id(orch, args.id)
        if not task:
            print("Task not found.")
            return
        
        updated_task = orch.add_attachment(task.id, args.filepath)
        if updated_task:
            print("Attachment added.")
            print(format_task(updated_task, full=True))
        else:
            print("Task not found or file error.")
    except ValueError:
        print("Invalid UUID or Alias")

def handle_extract(orch, args):
    try:
        task = get_task_id(orch, args.id, allow_version=True)
        if not task:
            print("Task not found.")
            return
        
        success = orch.extract_attachment(task.id, args.filename, args.output)
        if success:
            print(f"Attachment '{args.filename}' extracted to '{args.output}'")
        else:
            print("Failed to extract attachment. Check task ID and filename.")
    except ValueError:
        print("Invalid UUID or Alias")

def handle_duplicate(orch, args):
    try:
        task = get_task_id(orch, args.id, allow_version=True)
        if not task:
            print("Task not found.")
            return
        
        new_task = orch.duplicate_task(task.id)
        if new_task:
            new_alias = generate_alias(new_task.id)
            print(f"Task duplicated successfully!")
            print(f"New task: {new_task.id} ({new_alias})")
            print(format_task(new_task, full=True))
        else:
            print("Failed to duplicate task.")
    except ValueError:
        print("Invalid UUID or Alias")

def handle_kanban(orch, args):
    # Group tasks by status (case-insensitive)
    status_map = {}
    for status in args.statuses:
        status_map[status.lower()] = status
    
    tasks_by_status = {status: [] for status in args.statuses}
    
    for task in orch.tasks.values():
        if task.archived:
            continue
        task_status_lower = task.status.lower()
        if task_status_lower in status_map:
            original_status = status_map[task_status_lower]
            tasks_by_status[original_status].append(task)
    
    # Render and display
    board = render_kanban_board(tasks_by_status, args.statuses)
    print(board)

def handle_archive(orch, args):
    try:
        task = get_task_id(orch, args.id)
        if not task:
            print("Task not found.")
            return
        
        updated_task = orch.archive_task(task.id)
        if updated_task:
            print(f"Task {task.id} archived.")
        else:
            print("Failed to archive task.")
    except ValueError:
        print("Invalid UUID or Alias")

def handle_unarchive(orch, args):
    try:
        task = get_task_id(orch, args.id)
        if not task:
            print("Task not found.")
            return
        
        updated_task = orch.unarchive_task(task.id)
        if updated_task:
            print(f"Task {task.id} unarchived.")
        else:
            print("Failed to unarchive task.")
    except ValueError:
        print("Invalid UUID or Alias")

def handle_delete(orch, args):
    try:
        task = get_task_id(orch, args.id)
        if not task:
            print("Task not found.")
            return
        
        success = orch.delete_task(task.id)
        if success:
            print(f"Task {task.id} deleted.")
        else:
            print("Failed to delete task.")
    except ValueError:
        print("Invalid UUID or Alias")

def handle_dump(orch, args):
    tasks_to_dump = []
    for task in orch.tasks.values():
        if not args.all and task.archived:
            continue
        
        if args.history:
            history = orch.get_history(task.id)
            for version in history:
                tasks_to_dump.append(version.model_dump(mode='json'))
        else:
            tasks_to_dump.append(task.model_dump(mode='json'))
    
    json_output = json.dumps(tasks_to_dump, indent=2, default=str)
    
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"Dumped {len(tasks_to_dump)} tasks to {args.output}")
        except IOError as e:
            print(f"Error writing to file: {e}")
    else:
        print(json_output)

def handle_history(orch, args):
    try:
        task = get_task_id(orch, args.id)
        if not task:
            print("Task not found.")
            return
        
        history = orch.get_history(task.id)
        if not history:
            print("Task not found.")
        else:
            for i, task_version in enumerate(history):
                print(f"--- Version {len(history) - i} ---")
                print(format_task(task_version, full=True))
                print("")
    except ValueError:
        print("Invalid UUID or Alias")

def main():
    parser = argparse.ArgumentParser(description="Todo Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # ADD
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("description", help="Task description")
    add_parser.add_argument("--deadline", help="Deadline (YYYY-MM-DD)")

    # LIST
    list_parser = subparsers.add_parser("list", help="List all tasks")
    list_parser.add_argument("-a", "--all", action="store_true", help="Show all tasks including archived")

    # SHOW
    show_parser = subparsers.add_parser("show", help="Show task details")
    show_parser.add_argument("id", help="Task UUID")

    # UPDATE
    update_parser = subparsers.add_parser("update", help="Update a task")
    update_parser.add_argument("id", help="Task UUID")
    update_parser.add_argument("--desc", help="New description")
    update_parser.add_argument("--status", help="New status")
    
    # ATTACH
    attach_parser = subparsers.add_parser("attach", help="Attach a file to a task")
    attach_parser.add_argument("id", help="Task UUID")
    attach_parser.add_argument("filepath", help="Path to file")

    # EXTRACT
    extract_parser = subparsers.add_parser("extract", help="Extract an attachment from a task")
    extract_parser.add_argument("id", help="Task UUID or Alias")
    extract_parser.add_argument("filename", help="Attachment filename")
    extract_parser.add_argument("--output", required=True, help="Output path")

    # DUPLICATE
    duplicate_parser = subparsers.add_parser("duplicate", help="Duplicate a task")
    duplicate_parser.add_argument("id", help="Task UUID or Alias")

    kanban_parser = subparsers.add_parser("kanban", help="Display kanban board")
    kanban_parser.add_argument("statuses", nargs="+", help="Status values to display as columns")

    # ARCHIVE
    archive_parser = subparsers.add_parser("archive", help="Archive a task")
    archive_parser.add_argument("id", help="Task UUID or Alias")

    # UNARCHIVE
    unarchive_parser = subparsers.add_parser("unarchive", help="Unarchive a task")
    unarchive_parser.add_argument("id", help="Task UUID or Alias")

    # DELETE
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("id", help="Task UUID or Alias")

    # DUMP
    dump_parser = subparsers.add_parser("dump", help="Dump tasks to JSON")
    dump_parser.add_argument("-a", "--all", action="store_true", help="Include archived tasks")
    dump_parser.add_argument("--history", action="store_true", help="Include all versions of tasks")
    dump_parser.add_argument("--output", help="Output file path")

    # HISTORY
    history_parser = subparsers.add_parser("history", help="Show task history")
    history_parser.add_argument("id", help="Task UUID")

    args = parser.parse_args()
    
    orch = TodoOrchestrator()

    handlers = {
        "add": handle_add,
        "list": handle_list,
        "show": handle_show,
        "update": handle_update,
        "attach": handle_attach,
        "extract": handle_extract,
        "duplicate": handle_duplicate,
        "kanban": handle_kanban,
        "archive": handle_archive,
        "unarchive": handle_unarchive,
        "delete": handle_delete,
        "dump": handle_dump,
        "history": handle_history
    }

    if args.command in handlers:
        handlers[args.command](orch, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
