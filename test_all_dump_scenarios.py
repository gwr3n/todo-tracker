#!/usr/bin/env python3
"""
Test all dump scenarios to identify the issue.
"""
import tempfile
import shutil
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, '/Users/gwren/ag_projects/todo_orchestrator')

from src.tracker import TodoTracker

def test_all_dump_scenarios():
    # Create a temporary directory for the test
    test_dir = tempfile.mkdtemp()
    storage_dir = Path(test_dir) / ".todo_store"
    
    try:
        print("=" * 70)
        print("Testing All Dump Scenarios")
        print("=" * 70)
        print(f"Test directory: {test_dir}\n")
        
        # Initialize orchestrator
        orch = TodoTracker(root_dir=str(storage_dir))
        
        # Setup: Create Task A (pending -> completed) and Task B (pending only)
        print("SETUP:")
        task_a = orch.add_task("Task A")
        print(f"  1. Created Task A (pending): {task_a.id}")
        
        task_a_updated = orch.update_task(task_a.id, status="completed")
        print(f"  2. Updated Task A to completed")
        
        task_b = orch.add_task("Task B")
        print(f"  3. Created Task B (pending): {task_b.id}")
        print()
        
        # Scenario 1: dump (no flags)
        print("-" * 70)
        print("SCENARIO 1: dump (no flags)")
        print("-" * 70)
        tasks_to_dump = []
        for task in orch.tasks.values():
            if task.archived:
                continue
            tasks_to_dump.append(task.model_dump(mode='json'))
        
        print(f"Tasks in dump: {len(tasks_to_dump)}")
        for i, task_data in enumerate(tasks_to_dump, 1):
            print(f"  {i}. {task_data['description']} - Status: {task_data['status']}")
        print(f"Expected: 2 tasks (Task A completed, Task B pending)")
        print(f"Result: {'✓ PASS' if len(tasks_to_dump) == 2 else '✗ FAIL'}")
        print()
        
        # Scenario 2: dump --history
        print("-" * 70)
        print("SCENARIO 2: dump --history")
        print("-" * 70)
        tasks_to_dump = []
        for task in orch.tasks.values():
            if task.archived:
                continue
            history = orch.get_history(task.id)
            for version in history:
                tasks_to_dump.append(version.model_dump(mode='json'))
        
        print(f"Tasks in dump: {len(tasks_to_dump)}")
        for i, task_data in enumerate(tasks_to_dump, 1):
            print(f"  {i}. {task_data['description']} - Status: {task_data['status']}")
        print(f"Expected: 3 tasks (Task A completed, Task A pending, Task B pending)")
        print(f"Result: {'✓ PASS' if len(tasks_to_dump) == 3 else '✗ FAIL'}")
        print()
        
        # Scenario 3: Archive Task B and dump --history (no -a flag)
        print("-" * 70)
        print("SCENARIO 3: Archive Task B, then dump --history (no -a flag)")
        print("-" * 70)
        orch.archive_task(task_b.id)
        print(f"  Archived Task B")
        
        tasks_to_dump = []
        for task in orch.tasks.values():
            if task.archived:  # Skip archived
                continue
            history = orch.get_history(task.id)
            for version in history:
                tasks_to_dump.append(version.model_dump(mode='json'))
        
        print(f"Tasks in dump: {len(tasks_to_dump)}")
        for i, task_data in enumerate(tasks_to_dump, 1):
            print(f"  {i}. {task_data['description']} - Status: {task_data['status']}")
        print(f"Expected: 2 tasks (Task A completed, Task A pending)")
        print(f"Result: {'✓ PASS' if len(tasks_to_dump) == 2 else '✗ FAIL'}")
        print()
        
        # Scenario 4: dump --history -a (include archived)
        print("-" * 70)
        print("SCENARIO 4: dump --history -a (include archived)")
        print("-" * 70)
        tasks_to_dump = []
        for task in orch.tasks.values():
            # Don't skip archived when -a flag is used
            history = orch.get_history(task.id)
            for version in history:
                tasks_to_dump.append(version.model_dump(mode='json'))
        
        print(f"Tasks in dump: {len(tasks_to_dump)}")
        for i, task_data in enumerate(tasks_to_dump, 1):
            archived_marker = " [ARCHIVED]" if task_data.get('archived') else ""
            print(f"  {i}. {task_data['description']} - Status: {task_data['status']}{archived_marker}")
        print(f"Expected: 4 tasks (Task A v1, Task A v2, Task B v1, Task B v2-archived)")
        print(f"Result: {'✓ PASS' if len(tasks_to_dump) == 4 else '✗ FAIL'}")
        print()
        
        print("=" * 70)
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_all_dump_scenarios()
