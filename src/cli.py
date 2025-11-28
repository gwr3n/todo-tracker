#!/usr/bin/env python3
import argparse
import sys
from uuid import UUID
from datetime import datetime
from typing import Optional

# Add src to path if running directly
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator import TodoOrchestrator
from src.alias import generate_alias, resolve_alias

def format_task(task, full=False):
    if not task:
        return "Task not found."
    
    alias = generate_alias(task.id)
    if not full:
        task_id = f"{task.id} ({alias})"
        return f"{task_id:<50} | {task.status.ljust(10)} | {task.description}"
    
    lines = [
        f"ID:          {task.id} ({alias})",
        f"Description: {task.description}",
        f"Status:      {task.status}",
        f"Created:     {task.created_at}",
        f"Deadline:    {task.deadline}",
        f"Version:     {task.version_hash}",
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


def main():
    parser = argparse.ArgumentParser(description="Todo Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # ADD
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("description", help="Task description")
    add_parser.add_argument("--deadline", help="Deadline (YYYY-MM-DD)")

    # LIST
    subparsers.add_parser("list", help="List all tasks")

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

    # HISTORY
    history_parser = subparsers.add_parser("history", help="Show task history")
    history_parser.add_argument("id", help="Task UUID")


    args = parser.parse_args()
    
    orch = TodoOrchestrator()

    if args.command == "add":
        deadline = None
        if args.deadline:
            try:
                deadline = datetime.strptime(args.deadline, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD")
                return

        task = orch.add_task(args.description, deadline=deadline)
        print(f"Task created: {task.id}")

    elif args.command == "list":
        if not orch.tasks:
            print("No tasks found.")
        else:
            print(f"{'ID (ALIAS)':<50} | {'STATUS':<10} | DESCRIPTION")
            print("-" * 80)
            for task in orch.tasks.values():
                print(format_task(task))

    elif args.command == "show":
        try:
            task = get_task_id(orch, args.id, allow_version=True)
            if task:
                print(format_task(task, full=True))
            else:
                print("Task not found.")
        except ValueError:
            print("Invalid UUID or Alias")

    elif args.command == "update":
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

    elif args.command == "attach":
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

    elif args.command == "extract":
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

    elif args.command == "history":
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

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
