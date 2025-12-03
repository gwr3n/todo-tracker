import pytest
from src.tracker import TodoTracker
from src.cli import main
from unittest.mock import patch


@pytest.fixture
def isolated_tracker(tmp_path):
    """Create an isolated tracker for integration tests."""
    return TodoTracker(root_dir=str(tmp_path / "store"))


class TestTaskLifecycle:
    def test_complete_task_lifecycle(self, isolated_tracker):
        """Test complete lifecycle: add -> update -> archive -> unarchive -> delete."""
        # Add task
        task = isolated_tracker.add_task("Integration test task")
        task_id = task.id
        assert task.status == "pending"
        assert not task.archived

        # Update status
        updated = isolated_tracker.update_task(task_id, status="in-progress")
        assert updated.status == "in-progress"

        # Update description
        updated = isolated_tracker.update_task(task_id, description="Updated task")
        assert updated.description == "Updated task"

        # Complete task
        updated = isolated_tracker.update_task(task_id, status="completed")
        assert updated.status == "completed"

        # Archive task
        archived = isolated_tracker.archive_task(task_id)
        assert archived.archived is True

        # Unarchive task
        unarchived = isolated_tracker.unarchive_task(task_id)
        assert unarchived.archived is False

        # Delete task
        result = isolated_tracker.delete_task(task_id)
        assert result is True

        # Verify deletion
        assert isolated_tracker.get_task(task_id) is None


class TestAttachmentWorkflow:
    def test_attach_and_extract_workflow(self, isolated_tracker, tmp_path):
        """Test complete attachment workflow: add task -> attach file -> extract file"""
        # Create task
        task = isolated_tracker.add_task("Task with attachment")

        # Create a test file
        test_file = tmp_path / "original.txt"
        test_content = "This is test content for attachment workflow"
        test_file.write_text(test_content)

        # Attach file
        updated = isolated_tracker.add_attachment(task.id, str(test_file))
        assert len(updated.attachments) == 1
        assert updated.attachments[0].filename == "original.txt"

        # Extract file
        output_file = tmp_path / "extracted.txt"
        success = isolated_tracker.extract_attachment(
            task.id, "original.txt", str(output_file)
        )
        assert success is True
        assert output_file.exists()
        assert output_file.read_text() == test_content

        # Verify task still exists with attachment
        task = isolated_tracker.get_task(task.id)
        assert len(task.attachments) == 1

    def test_multiple_attachments_workflow(self, isolated_tracker, tmp_path):
        """Test workflow with multiple attachments."""
        task = isolated_tracker.add_task("Multi-attachment task")

        # Attach multiple files
        files = []
        for i in range(3):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append(file_path)
            isolated_tracker.add_attachment(task.id, str(file_path))

        # Verify all attachments
        task = isolated_tracker.get_task(task.id)
        assert len(task.attachments) == 3

        # Extract all attachments
        for i in range(3):
            output = tmp_path / f"extracted{i}.txt"
            success = isolated_tracker.extract_attachment(
                task.id, f"file{i}.txt", str(output)
            )
            assert success is True
            assert output.read_text() == f"Content {i}"


class TestDuplicationWorkflow:
    def test_duplicate_and_modify_workflow(self, isolated_tracker, tmp_path):
        """Test duplicating a task and modifying the duplicate independently."""
        # Create original task with attachment
        original = isolated_tracker.add_task("Original task")

        test_file = tmp_path / "shared.txt"
        test_file.write_text("Shared content")
        isolated_tracker.add_attachment(original.id, str(test_file))

        # Update original to completed
        isolated_tracker.update_task(original.id, status="completed")

        # Duplicate
        duplicate = isolated_tracker.duplicate_task(original.id)

        # Verify duplicate has reset status but same attachment
        assert duplicate.status == "pending"
        assert duplicate.description == "Original task"
        assert len(duplicate.attachments) == 1
        assert duplicate.attachments[0].filename == "shared.txt"

        # Modify duplicate independently
        isolated_tracker.update_task(duplicate.id, description="Duplicated task")

        # Verify original unchanged
        original_reloaded = isolated_tracker.get_task(original.id)
        assert original_reloaded.description == "Original task"
        assert original_reloaded.status == "completed"

        # Verify duplicate changed
        duplicate_reloaded = isolated_tracker.get_task(duplicate.id)
        assert duplicate_reloaded.description == "Duplicated task"
        assert duplicate_reloaded.status == "pending"

    def test_duplicate_chain(self, isolated_tracker):
        """Test creating a chain of duplicates."""
        # Create original
        task1 = isolated_tracker.add_task("Generation 1")

        # Duplicate to create generation 2
        task2 = isolated_tracker.duplicate_task(task1.id)
        isolated_tracker.update_task(task2.id, description="Generation 2")

        # Duplicate generation 2 to create generation 3
        task3 = isolated_tracker.duplicate_task(task2.id)
        isolated_tracker.update_task(task3.id, description="Generation 3")

        # Verify all exist independently
        assert isolated_tracker.get_task(task1.id).description == "Generation 1"
        assert isolated_tracker.get_task(task2.id).description == "Generation 2"
        assert isolated_tracker.get_task(task3.id).description == "Generation 3"


class TestHistoryTracking:
    def test_history_across_updates(self, isolated_tracker):
        """Test that history is properly tracked across multiple updates."""
        # Create task
        task = isolated_tracker.add_task("Version 1")

        # Make several updates
        isolated_tracker.update_task(task.id, description="Version 2")
        isolated_tracker.update_task(task.id, description="Version 3")
        isolated_tracker.update_task(task.id, status="in-progress")
        isolated_tracker.update_task(task.id, description="Version 5")

        # Get history
        history = isolated_tracker.get_history(task.id)

        # Should have 5 versions
        assert len(history) == 5

        # Verify order (newest first)
        assert history[0].description == "Version 5"
        assert history[1].description == "Version 3"  # Description unchanged in v4
        assert history[4].description == "Version 1"

        # Verify we can get specific versions
        v1 = isolated_tracker.get_task_version(task.id, 1)
        v3 = isolated_tracker.get_task_version(task.id, 3)
        v5 = isolated_tracker.get_task_version(task.id, 5)

        assert v1.description == "Version 1"
        assert v3.description == "Version 3"
        assert v5.description == "Version 5"


class TestPersistenceWorkflow:
    def test_persistence_across_restarts(self, tmp_path):
        """Test that data persists across tracker restarts."""
        store_path = tmp_path / "persistent_store"

        # Session 1: Create and modify tasks
        tracker1 = TodoTracker(root_dir=str(store_path))
        task1 = tracker1.add_task("Persistent task 1")
        task2 = tracker1.add_task("Persistent task 2")
        tracker1.update_task(task1.id, status="completed")
        tracker1.archive_task(task2.id)

        task1_id = task1.id
        task2_id = task2.id

        # Session 2: Reload and verify
        tracker2 = TodoTracker(root_dir=str(store_path))

        loaded1 = tracker2.get_task(task1_id)
        loaded2 = tracker2.get_task(task2_id)

        assert loaded1 is not None
        assert loaded1.description == "Persistent task 1"
        assert loaded1.status == "completed"

        assert loaded2 is not None
        assert loaded2.description == "Persistent task 2"
        assert loaded2.archived is True

        # Session 3: Make more changes and verify
        tracker2.update_task(task1_id, description="Updated in session 2")

        tracker3 = TodoTracker(root_dir=str(store_path))
        loaded1_again = tracker3.get_task(task1_id)
        assert loaded1_again.description == "Updated in session 2"

    def test_persistence_with_attachments(self, tmp_path):
        """Test that attachments persist across restarts."""
        store_path = tmp_path / "attachment_store"

        # Session 1: Add task with attachment
        tracker1 = TodoTracker(root_dir=str(store_path))
        task = tracker1.add_task("Task with attachment")

        test_file = tmp_path / "test.txt"
        test_file.write_text("Persistent content")
        tracker1.add_attachment(task.id, str(test_file))

        task_id = task.id

        # Session 2: Reload and extract attachment
        tracker2 = TodoTracker(root_dir=str(store_path))
        loaded = tracker2.get_task(task_id)

        assert len(loaded.attachments) == 1
        assert loaded.attachments[0].filename == "test.txt"

        # Extract and verify content
        output = tmp_path / "extracted.txt"
        success = tracker2.extract_attachment(task_id, "test.txt", str(output))
        assert success is True
        assert output.read_text() == "Persistent content"


class TestKanbanWorkflow:
    def test_kanban_with_multiple_statuses(self, isolated_tracker):
        """Test kanban board with tasks in various statuses."""
        # Create tasks with different statuses
        _ = isolated_tracker.add_task("Task 1")
        _ = isolated_tracker.add_task("Task 2")

        task3 = isolated_tracker.add_task("Task 3")
        isolated_tracker.update_task(task3.id, status="in-progress")

        task4 = isolated_tracker.add_task("Task 4")
        isolated_tracker.update_task(task4.id, status="completed")

        task5 = isolated_tracker.add_task("Task 5")
        isolated_tracker.update_task(task5.id, status="completed")

        # Group by status
        tasks_by_status = {}
        for task in isolated_tracker.tasks.values():
            if not task.archived:
                status = task.status
                if status not in tasks_by_status:
                    tasks_by_status[status] = []
                tasks_by_status[status].append(task)

        # Verify grouping
        assert len(tasks_by_status["pending"]) == 2
        assert len(tasks_by_status["in-progress"]) == 1
        assert len(tasks_by_status["completed"]) == 2


class TestCLIIntegration:
    def test_cli_add_and_list(self, tmp_path):
        """Test CLI add and list commands integration."""
        with patch("src.cli.TodoTracker") as MockTracker:
            orch = MockTracker.return_value
            orch.tasks = {}

            from src.models import Task

            # Add task via CLI
            new_task = Task(description="CLI task")
            orch.add_task.return_value = new_task

            with patch("sys.argv", ["cli.py", "add", "CLI task"]):
                main()

            orch.add_task.assert_called_once()

    def test_cli_full_workflow(self, tmp_path, capsys):
        """Test a complete CLI workflow with mocked tracker."""
        with patch("src.cli.TodoTracker") as MockTracker:
            orch = MockTracker.return_value

            from src.models import Task
            from uuid import UUID

            task_id = UUID("3077bee6-3da3-4783-aff7-cbedfd5f5592")
            task = Task(id=task_id, description="Test task", status="pending")

            orch.tasks = {task_id: task}
            orch.add_task.return_value = task
            orch.get_task.return_value = task

            # Add task
            with patch("sys.argv", ["cli.py", "add", "Test task"]):
                main()

            # List tasks
            with patch("sys.argv", ["cli.py", "list"]):
                main()
                captured = capsys.readouterr()
                assert "Test task" in captured.out


class TestErrorRecovery:
    def test_recover_from_failed_update(self, isolated_tracker):
        """Test that failed updates don't corrupt the task."""
        task = isolated_tracker.add_task("Original")
        original_description = task.description

        # Try to update with invalid task ID (should fail)
        from uuid import uuid4

        fake_id = uuid4()

        try:
            isolated_tracker.update_task(fake_id, description="Should fail")
        except KeyError:
            pass

        # Original task should be unchanged
        task = isolated_tracker.get_task(task.id)
        assert task.description == original_description

    def test_delete_with_shared_attachments(self, isolated_tracker, tmp_path):
        """Test that deleting a task with shared attachments works correctly."""
        # Create two tasks sharing an attachment
        task1 = isolated_tracker.add_task("Task 1")
        task2 = isolated_tracker.add_task("Task 2")

        test_file = tmp_path / "shared.txt"
        test_file.write_text("Shared content")

        isolated_tracker.add_attachment(task1.id, str(test_file))
        isolated_tracker.add_attachment(task2.id, str(test_file))

        # Get content hash
        task1_loaded = isolated_tracker.get_task(task1.id)
        content_hash = task1_loaded.attachments[0].content_hash

        # Delete task 1
        isolated_tracker.delete_task(task1.id)

        # Attachment should still exist (used by task 2)
        assert isolated_tracker.storage.get_object(content_hash) is not None

        # Delete task 2
        isolated_tracker.delete_task(task2.id)

        # Now attachment should be deleted
        assert isolated_tracker.storage.get_object(content_hash) is None
