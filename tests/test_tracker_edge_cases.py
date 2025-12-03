import pytest
from src.tracker import TodoTracker
from src.models import Task, Attachment
from uuid import UUID, uuid4
import os


@pytest.fixture
def tracker(tmp_path):
    """Create a tracker with temporary storage."""
    return TodoTracker(root_dir=str(tmp_path / "store"))


class TestInvalidTaskOperations:
    def test_get_nonexistent_task(self, tracker):
        """Test getting a task that doesn't exist."""
        fake_id = uuid4()
        result = tracker.get_task(fake_id)
        assert result is None

    def test_update_nonexistent_task(self, tracker):
        """Test updating a task that doesn't exist."""
        fake_id = uuid4()
        result = tracker.update_task(fake_id, description="New description")
        assert result is None

    def test_delete_nonexistent_task(self, tracker):
        """Test deleting a task that doesn't exist."""
        fake_id = uuid4()
        result = tracker.delete_task(fake_id)
        assert result is False

    def test_archive_nonexistent_task(self, tracker):
        """Test archiving a task that doesn't exist."""
        fake_id = uuid4()
        result = tracker.archive_task(fake_id)
        assert result is None

    def test_unarchive_nonexistent_task(self, tracker):
        """Test unarchiving a task that doesn't exist."""
        fake_id = uuid4()
        result = tracker.unarchive_task(fake_id)
        assert result is None

    def test_duplicate_nonexistent_task(self, tracker):
        """Test duplicating a task that doesn't exist."""
        fake_id = uuid4()
        result = tracker.duplicate_task(fake_id)
        assert result is None


class TestAttachmentEdgeCases:
    def test_add_attachment_nonexistent_file(self, tracker):
        """Test adding an attachment from a file that doesn't exist."""
        task = tracker.add_task("Test task")
        result = tracker.add_attachment(task.id, "/nonexistent/file.txt")
        assert result is None

    def test_add_attachment_to_nonexistent_task(self, tracker, tmp_path):
        """Test adding an attachment to a task that doesn't exist."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        fake_id = uuid4()
        result = tracker.add_attachment(fake_id, str(test_file))
        assert result is None

    def test_extract_attachment_nonexistent_task(self, tracker, tmp_path):
        """Test extracting attachment from a task that doesn't exist."""
        output = tmp_path / "output.txt"
        fake_id = uuid4()
        
        result = tracker.extract_attachment(fake_id, "test.txt", str(output))
        assert result is False

    def test_extract_nonexistent_attachment(self, tracker, tmp_path):
        """Test extracting an attachment that doesn't exist on the task."""
        task = tracker.add_task("Test task")
        output = tmp_path / "output.txt"
        
        result = tracker.extract_attachment(task.id, "nonexistent.txt", str(output))
        assert result is False

    def test_extract_attachment_to_existing_file(self, tracker, tmp_path):
        """Test extracting attachment overwrites existing output file."""
        # Create task with attachment
        task = tracker.add_task("Test task")
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")
        tracker.add_attachment(task.id, str(test_file))
        
        # Create existing output file
        output = tmp_path / "output.txt"
        output.write_text("old content")
        
        # Extract should overwrite
        result = tracker.extract_attachment(task.id, "test.txt", str(output))
        assert result is True
        assert output.read_text() == "original content"

    def test_add_multiple_attachments_same_name(self, tracker, tmp_path):
        """Test adding multiple attachments with the same filename."""
        task = tracker.add_task("Test task")
        
        # Add first attachment
        file1 = tmp_path / "test.txt"
        file1.write_text("content 1")
        tracker.add_attachment(task.id, str(file1))
        
        # Add second attachment with same name but different content
        file2 = tmp_path / "subdir" / "test.txt"
        file2.parent.mkdir()
        file2.write_text("content 2")
        tracker.add_attachment(task.id, str(file2))
        
        # Should have both attachments
        task = tracker.get_task(task.id)
        assert len(task.attachments) == 2
        assert all(a.filename == "test.txt" for a in task.attachments)
        # But different content hashes
        assert task.attachments[0].content_hash != task.attachments[1].content_hash


class TestVersioningEdgeCases:
    def test_get_version_out_of_bounds(self, tracker):
        """Test getting version numbers that are out of bounds."""
        task = tracker.add_task("Version 1")
        tracker.update_task(task.id, description="Version 2")
        
        # Version 0 doesn't exist
        assert tracker.get_task_version(task.id, 0) is None
        
        # Version 3 doesn't exist yet
        assert tracker.get_task_version(task.id, 3) is None
        
        # Negative version
        assert tracker.get_task_version(task.id, -1) is None

    def test_get_version_nonexistent_task(self, tracker):
        """Test getting version of a task that doesn't exist."""
        fake_id = uuid4()
        result = tracker.get_task_version(fake_id, 1)
        assert result is None

    def test_history_nonexistent_task(self, tracker):
        """Test getting history of a task that doesn't exist."""
        fake_id = uuid4()
        result = tracker.get_history(fake_id)
        assert result == []

    def test_history_single_version(self, tracker):
        """Test history for a task with only one version."""
        task = tracker.add_task("Only version")
        history = tracker.get_history(task.id)
        
        assert len(history) == 1
        assert history[0].description == "Only version"

    def test_history_many_versions(self, tracker):
        """Test history for a task with many versions."""
        task = tracker.add_task("Version 1")
        
        # Create 10 more versions
        for i in range(2, 12):
            tracker.update_task(task.id, description=f"Version {i}")
        
        history = tracker.get_history(task.id)
        assert len(history) == 11
        
        # Verify order (newest first)
        assert history[0].description == "Version 11"
        assert history[-1].description == "Version 1"


class TestTaskUpdateEdgeCases:
    def test_update_with_no_changes(self, tracker):
        """Test updating a task with no actual changes."""
        task = tracker.add_task("Original")
        
        # Update with empty dict
        updated = tracker.update_task(task.id)
        
        # Should still create a new version
        assert updated.description == "Original"
        history = tracker.get_history(task.id)
        assert len(history) == 2

    def test_update_only_modified_at(self, tracker):
        """Test that modified_at is updated even with no content changes."""
        task = tracker.add_task("Test")
        original_modified = task.modified_at
        
        import time
        time.sleep(0.01)  # Small delay to ensure different timestamp
        
        updated = tracker.update_task(task.id, description="Test")
        
        # Modified time should be different
        assert updated.modified_at >= original_modified

    def test_update_status_to_invalid_value(self, tracker):
        """Test updating status to an arbitrary value (should be allowed)."""
        task = tracker.add_task("Test")
        
        # The system doesn't validate status values, so this should work
        updated = tracker.update_task(task.id, status="custom-status")
        assert updated.status == "custom-status"

    def test_update_archived_flag_directly(self, tracker):
        """Test that updating archived flag directly works."""
        task = tracker.add_task("Test")
        
        # Update archived via update_task (not archive_task)
        updated = tracker.update_task(task.id, archived=True)
        assert updated.archived is True


class TestDuplicationEdgeCases:
    def test_duplicate_preserves_deadline(self, tracker):
        """Test that duplication preserves the deadline."""
        from datetime import datetime
        
        deadline = datetime(2025, 12, 31, 23, 59, 59)
        task = tracker.add_task("Test", deadline=deadline)
        
        duplicate = tracker.duplicate_task(task.id)
        assert duplicate.deadline == deadline

    def test_duplicate_resets_created_at(self, tracker):
        """Test that duplicate has a new created_at timestamp."""
        task = tracker.add_task("Test")
        
        import time
        time.sleep(0.01)
        
        duplicate = tracker.duplicate_task(task.id)
        assert duplicate.created_at >= task.created_at

    def test_duplicate_archived_task(self, tracker):
        """Test duplicating an archived task."""
        task = tracker.add_task("Test")
        tracker.archive_task(task.id)
        
        duplicate = tracker.duplicate_task(task.id)
        
        # Duplicate should not be archived
        assert duplicate.archived is False
        assert duplicate.status == "pending"


class TestPersistenceEdgeCases:
    def test_reload_after_delete(self, tracker):
        """Test that deleted tasks don't reappear after reload."""
        task = tracker.add_task("To delete")
        task_id = task.id
        
        tracker.delete_task(task_id)
        
        # Create new tracker instance (simulates restart)
        new_tracker = TodoTracker(root_dir=tracker.storage.root_dir)
        
        assert new_tracker.get_task(task_id) is None

    def test_reload_preserves_all_fields(self, tracker):
        """Test that all task fields are preserved after reload."""
        from datetime import datetime
        
        deadline = datetime(2025, 12, 31, 23, 59, 59)
        task = tracker.add_task("Test", deadline=deadline)
        tracker.update_task(task.id, status="in-progress")
        tracker.archive_task(task.id)
        
        # Reload
        new_tracker = TodoTracker(root_dir=tracker.storage.root_dir)
        loaded = new_tracker.get_task(task.id)
        
        assert loaded.description == "Test"
        assert loaded.deadline == deadline
        assert loaded.status == "in-progress"
        assert loaded.archived is True

    def test_concurrent_tracker_instances(self, tracker, tmp_path):
        """Test that multiple tracker instances can coexist."""
        # Create task in first tracker
        task = tracker.add_task("Test")
        
        # Create second tracker pointing to same storage
        tracker2 = TodoTracker(root_dir=tracker.storage.root_dir)
        
        # Second tracker should see the task
        loaded = tracker2.get_task(task.id)
        assert loaded is not None
        assert loaded.description == "Test"


class TestEmptyAndNullValues:
    def test_add_task_empty_description(self, tracker):
        """Test adding a task with empty description."""
        task = tracker.add_task("")
        assert task.description == ""

    def test_update_to_empty_description(self, tracker):
        """Test updating a task to have empty description."""
        task = tracker.add_task("Original")
        updated = tracker.update_task(task.id, description="")
        assert updated.description == ""

    def test_add_task_with_none_deadline(self, tracker):
        """Test adding a task with explicit None deadline."""
        task = tracker.add_task("Test", deadline=None)
        assert task.deadline is None

    def test_update_deadline_to_none(self, tracker):
        """Test updating deadline to None (clearing it)."""
        from datetime import datetime
        
        deadline = datetime(2025, 12, 31)
        task = tracker.add_task("Test", deadline=deadline)
        
        updated = tracker.update_task(task.id, deadline=None)
        assert updated.deadline is None
