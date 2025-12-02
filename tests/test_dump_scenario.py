"""
Test the exact scenario described: Task A (pending -> completed) and Task B (pending
only)
"""

from src.tracker import TodoTracker


def test_dump_history_scenario(tmp_path):
    """
    Test scenario:
    - Task A: created as pending, then marked as completed
    - Task B: created as pending, never modified

    Expected dump --history output: 3 tasks
    - Task A version 1 (pending)
    - Task A version 2 (completed)
    - Task B version 1 (pending)
    """
    # Use a temporary storage directory
    storage_dir = tmp_path / ".todo_store"
    orch = TodoTracker(root_dir=str(storage_dir))

    # Create Task A (pending)
    task_a = orch.add_task("Task A")
    assert task_a.status == "pending"
    task_a_id = task_a.id

    # Update Task A to completed
    task_a_completed = orch.update_task(task_a_id, status="completed")
    assert task_a_completed.status == "completed"

    # Create Task B (pending, never modified)
    task_b = orch.add_task("Task B")
    assert task_b.status == "pending"
    # task_b_id = task_b.id  # Unused

    # Now simulate the dump --history logic
    tasks_to_dump = []
    for task in orch.tasks.values():
        history = orch.get_history(task.id)
        for version in history:
            tasks_to_dump.append(version.model_dump(mode="json"))

    # Verify we have 3 tasks in the dump
    assert len(tasks_to_dump) == 3, f"Expected 3 tasks, got {len(tasks_to_dump)}"

    # Verify the descriptions
    descriptions = [t["description"] for t in tasks_to_dump]
    assert descriptions.count("Task A") == 2, "Should have 2 versions of Task A"
    assert descriptions.count("Task B") == 1, "Should have 1 version of Task B"

    # Verify the statuses
    statuses = [t["status"] for t in tasks_to_dump]
    assert (
        statuses.count("pending") == 2
    ), "Should have 2 pending tasks (Task A v1 and Task B v1)"
    assert statuses.count("completed") == 1, "Should have 1 completed task (Task A v2)"

    print(f"\n✓ Dump contains {len(tasks_to_dump)} tasks as expected")
    task_a_pending = [
        t
        for t in tasks_to_dump
        if t["description"] == "Task A" and t["status"] == "pending"
    ][0]
    print(f"  - Task A (pending): {task_a_pending['id'][:8]}")

    task_a_completed = [
        t
        for t in tasks_to_dump
        if t["description"] == "Task A" and t["status"] == "completed"
    ][0]
    print(f"  - Task A (completed): {task_a_completed['id'][:8]}")

    task_b_pending = [t for t in tasks_to_dump if t["description"] == "Task B"][0]
    print(f"  - Task B (pending): {task_b_pending['id'][:8]}")
