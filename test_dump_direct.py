#!/usr/bin/env python3
"""
Direct test of the dump --history scenario using the tracker API.
This bypasses CLI parsing issues to test the core logic.
"""
import tempfile
import shutil
import json
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, '/Users/gwren/ag_projects/todo-tracker')

from src.tracker import TodoTracker

def test_dump_history():
    # Create a temporary directory for the test
    test_dir = tempfile.mkdtemp()
    storage_dir = Path(test_dir) / ".todo_store"
    
    try:
        print(f"Test directory: {test_dir}\n")
        
        # Initialize tracker
        tracker = TodoTracker(root_dir=str(storage_dir))
        
        # Step 1: Create Task A (pending)
        print("Step 1: Creating Task A (pending)")
        task_a = tracker.add_task("Task A")
        print(f"  - Task A ID: {task_a.id}")
        print(f"  - Status: {task_a.status}")
        print(f"  - Version hash: {task_a.version_hash}\n")
        
        # Step 2: Update Task A to completed
        print("Step 2: Updating Task A to completed")
        task_a_updated = tracker.update_task(task_a.id, status="completed")
        print(f"  - Task A ID: {task_a_updated.id}")
        print(f"  - Status: {task_a_updated.status}")
        print(f"  - Version hash: {task_a_updated.version_hash}")
        print(f"  - Parent hash: {task_a_updated.parent}\n")
        
        # Step 3: Create Task B (pending, never modified)
        print("Step 3: Creating Task B (pending)")
        task_b = tracker.add_task("Task B")
        print(f"  - Task B ID: {task_b.id}")
        print(f"  - Status: {task_b.status}")
        print(f"  - Version hash: {task_b.version_hash}\n")
        
        # Step 4: Check history for Task A
        print("Step 4: Getting history for Task A")
        history_a = tracker.get_history(task_a.id)
        print(f"  - History length: {len(history_a)}")
        for i, version in enumerate(history_a):
            print(f"    Version {i+1}: status={version.status}, hash={version.version_hash[:8]}")
        print()
        
        # Step 5: Check history for Task B
        print("Step 5: Getting history for Task B")
        history_b = tracker.get_history(task_b.id)
        print(f"  - History length: {len(history_b)}")
        for i, version in enumerate(history_b):
            print(f"    Version {i+1}: status={version.status}, hash={version.version_hash[:8]}")
        print()
        
        # Step 6: Simulate dump --history logic
        print("Step 6: Simulating dump --history")
        tasks_to_dump = []
        for task in tracker.tasks.values():
            history = tracker.get_history(task.id)
            for version in history:
                tasks_to_dump.append(version.model_dump(mode='json'))
        
        print(f"  - Total tasks in dump: {len(tasks_to_dump)}")
        print(f"  - Expected: 3 (Task A pending, Task A completed, Task B pending)\n")
        
        # Step 7: Analyze the dump
        print("Step 7: Analyzing dump contents")
        for i, task_data in enumerate(tasks_to_dump, 1):
            print(f"  {i}. {task_data['description']} - Status: {task_data['status']} - ID: {task_data['id'][:8]}")
        print()
        
        # Verification
        print("=" * 60)
        if len(tasks_to_dump) == 3:
            print("✓ SUCCESS: Dump contains 3 tasks as expected!")
        else:
            print(f"✗ FAILURE: Dump contains {len(tasks_to_dump)} tasks, expected 3!")
            print("\nThis confirms the bug reported by the user.")
        print("=" * 60)
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_dump_history()
