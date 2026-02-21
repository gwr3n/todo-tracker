#!/usr/bin/env python3
"""
Test all dump scenarios to identify the issue.
"""

import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.tracker import TodoTracker  # noqa: E402


def test_all_dump_scenarios():
    # Create a temporary directory for the test
    test_dir = tempfile.mkdtemp()
    storage_dir = Path(test_dir) / ".todo_store"

    try:
        print("=" * 70)
        print("Testing All Dump Scenarios")
        print("=" * 70)
        print(f"Test directory: {test_dir}\n")

        # Initialize tracker
        tracker = TodoTracker(root_dir=str(storage_dir))

        # Setup: Create Task A (pending -> completed) and Task B (pending only)
        print("SETUP:")
        task_a = tracker.add_task("Task A")
        print(f"  1. Created Task A (pending): {task_a.id}")

        tracker.update_task(task_a.id, status="completed")
        print("  2. Updated Task A to completed")

        task_b = tracker.add_task("Task B")
        print(f"  3. Created Task B (pending): {task_b.id}")
        print()

        # Scenario 1: dump (no flags)
        print("-" * 70)
        print("SCENARIO 1: dump (no flags)")
        print("-" * 70)
        tasks_to_dump = []
        for task in tracker.tasks.values():
            if task.archived:
                continue
            tasks_to_dump.append(task.model_dump(mode="json"))

        print(f"Tasks in dump: {len(tasks_to_dump)}")
        for i, task_data in enumerate(tasks_to_dump, 1):
            print(f"  {i}. {task_data['description']} - Status: {task_data['status']}")
        print("Expected: 2 tasks (Task A completed, Task B pending)")
        print(f"Result: {'✓ PASS' if len(tasks_to_dump) == 2 else '✗ FAIL'}")
        print()

        # Scenario 2: dump --history
        print("-" * 70)
        print("SCENARIO 2: dump --history")
        print("-" * 70)
        tasks_to_dump = []
        for task in tracker.tasks.values():
            if task.archived:
                continue
            history = tracker.get_history(task.id)
            for version in history:
                tasks_to_dump.append(version.model_dump(mode="json"))

        print(f"Tasks in dump: {len(tasks_to_dump)}")
        for i, task_data in enumerate(tasks_to_dump, 1):
            print(f"  {i}. {task_data['description']} - Status: {task_data['status']}")
        print("Expected: 3 tasks (Task A completed, Task A pending, Task B pending)")
        print(f"Result: {'✓ PASS' if len(tasks_to_dump) == 3 else '✗ FAIL'}")
        print()

        # Scenario 3: Archive Task B and dump --history (no -a flag)
        print("-" * 70)
        print("SCENARIO 3: Archive Task B, then dump --history (no -a flag)")
        print("-" * 70)
        tracker.archive_task(task_b.id)
        print("  Archived Task B")

        tasks_to_dump = []
        for task in tracker.tasks.values():
            if task.archived:  # Skip archived
                continue
            history = tracker.get_history(task.id)
            for version in history:
                tasks_to_dump.append(version.model_dump(mode="json"))

        print(f"Tasks in dump: {len(tasks_to_dump)}")
        for i, task_data in enumerate(tasks_to_dump, 1):
            print(f"  {i}. {task_data['description']} - Status: {task_data['status']}")
        print("Expected: 2 tasks (Task A completed, Task A pending)")
        print(f"Result: {'✓ PASS' if len(tasks_to_dump) == 2 else '✗ FAIL'}")
        print()

        # Scenario 4: dump --history -a (include archived)
        print("-" * 70)
        print("SCENARIO 4: dump --history -a (include archived)")
        print("-" * 70)
        tasks_to_dump = []
        for task in tracker.tasks.values():
            # Don't skip archived when -a flag is used
            history = tracker.get_history(task.id)
            for version in history:
                tasks_to_dump.append(version.model_dump(mode="json"))

        print(f"Tasks in dump: {len(tasks_to_dump)}")
        for i, task_data in enumerate(tasks_to_dump, 1):
            archived_marker = " [ARCHIVED]" if task_data.get("archived") else ""
            print(f"  {i}. {task_data['description']} - " f"Status: {task_data['status']}{archived_marker}")
        print("Expected: 4 tasks (Task A v1, Task A v2, Task B v1, Task B v2-archived)")
        print(f"Result: {'✓ PASS' if len(tasks_to_dump) == 4 else '✗ FAIL'}")
        print()

        print("=" * 70)

    finally:
        # Cleanup
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_all_dump_scenarios()
