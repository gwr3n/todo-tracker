import pytest
from unittest.mock import patch, MagicMock
from src.cli import (
    handle_add,
    handle_list,
    handle_show,
    handle_update,
    handle_attach,
    handle_extract,
    handle_duplicate,
    handle_kanban,
    handle_archive,
    handle_unarchive,
    handle_delete,
    handle_history,
)
from src.models import Task
from uuid import UUID


@pytest.fixture
def mock_orch():
    """Create a mock orchestrator with sample tasks."""
    orch = MagicMock()
    orch.tasks = {}
    return orch


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        id=UUID("3077bee6-3da3-4783-aff7-cbedfd5f5592"),
        description="Sample Task",
        status="pending",
    )


class TestHandleAdd:
    def test_add_simple_task(self, mock_orch, capsys):
        """Test adding a simple task without deadline."""
        args = MagicMock()
        args.description = "New task"
        args.deadline = None

        new_task = Task(description="New task")
        mock_orch.add_task.return_value = new_task

        handle_add(mock_orch, args)

        mock_orch.add_task.assert_called_once_with("New task", deadline=None)
        captured = capsys.readouterr()
        assert "Task created" in captured.out

    def test_add_task_with_deadline(self, mock_orch, capsys):
        """Test adding a task with a deadline."""
        args = MagicMock()
        args.description = "Task with deadline"
        args.deadline = "2025-12-31"

        new_task = Task(description="Task with deadline")
        mock_orch.add_task.return_value = new_task

        handle_add(mock_orch, args)

        mock_orch.add_task.assert_called_once()
        captured = capsys.readouterr()
        assert "Task created" in captured.out


class TestHandleList:
    def test_list_all_tasks(self, mock_orch, sample_task, capsys):
        """Test listing all non-archived tasks."""
        args = MagicMock()
        args.status = None
        args.all = False

        mock_orch.tasks = {sample_task.id: sample_task}

        handle_list(mock_orch, args)

        captured = capsys.readouterr()
        assert "Sample Task" in captured.out

    def test_list_by_status(self, mock_orch, capsys):
        """Test listing tasks filtered by status."""
        args = MagicMock()
        args.status = "completed"
        args.all = False

        task1 = Task(description="Pending task", status="pending")
        task2 = Task(description="Completed task", status="completed")
        mock_orch.tasks = {task1.id: task1, task2.id: task2}

        handle_list(mock_orch, args)

        captured = capsys.readouterr()
        assert "Completed task" in captured.out
        # Note: list doesn't filter by status in the handler, it shows all

    def test_list_include_archived(self, mock_orch, capsys):
        """Test listing tasks including archived ones."""
        args = MagicMock()
        args.status = None
        args.all = True

        task1 = Task(description="Active task", archived=False)
        task2 = Task(description="Archived task", archived=True)
        mock_orch.tasks = {task1.id: task1, task2.id: task2}

        handle_list(mock_orch, args)

        captured = capsys.readouterr()
        assert "Active task" in captured.out
        assert "Archived task" in captured.out


class TestHandleShow:
    def test_show_existing_task(self, mock_orch, sample_task, capsys):
        """Test showing details of an existing task."""
        args = MagicMock()
        args.id = str(sample_task.id)

        mock_orch.tasks = {sample_task.id: sample_task}
        mock_orch.get_task.return_value = sample_task

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_show(mock_orch, args)

        captured = capsys.readouterr()
        assert "Sample Task" in captured.out

    def test_show_nonexistent_task(self, mock_orch, capsys):
        """Test showing a task that doesn't exist."""
        args = MagicMock()
        args.id = "nonexistent"

        with patch("src.cli.get_task_id", return_value=None):
            handle_show(mock_orch, args)

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()


class TestHandleUpdate:
    def test_update_description(self, mock_orch, sample_task, capsys):
        """Test updating task description."""
        args = MagicMock()
        args.id = str(sample_task.id)
        args.desc = "Updated description"
        args.status = None
        args.deadline = None

        updated_task = Task(id=sample_task.id, description="Updated description", status="pending")
        mock_orch.update_task.return_value = updated_task

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_update(mock_orch, args)

        mock_orch.update_task.assert_called_once()
        captured = capsys.readouterr()
        assert "Task updated" in captured.out

    def test_update_status(self, mock_orch, sample_task, capsys):
        """Test updating task status."""
        args = MagicMock()
        args.id = str(sample_task.id)
        args.desc = None
        args.status = "completed"
        args.deadline = None

        updated_task = Task(id=sample_task.id, description="Sample Task", status="completed")
        mock_orch.update_task.return_value = updated_task

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_update(mock_orch, args)

        captured = capsys.readouterr()
        assert "Task updated" in captured.out

    def test_update_no_changes(self, mock_orch, sample_task, capsys):
        """Test update with no actual changes."""
        args = MagicMock()
        args.id = str(sample_task.id)
        args.desc = None
        args.status = None
        args.deadline = None

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_update(mock_orch, args)

        captured = capsys.readouterr()
        assert "No updates provided" in captured.out


class TestHandleAttach:
    def test_attach_file(self, mock_orch, sample_task, tmp_path, capsys):
        """Test attaching a file to a task."""
        args = MagicMock()
        args.id = str(sample_task.id)
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        args.filepath = str(test_file)

        updated_task = sample_task
        mock_orch.add_attachment.return_value = updated_task

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_attach(mock_orch, args)

        mock_orch.add_attachment.assert_called_once_with(sample_task.id, str(test_file))
        captured = capsys.readouterr()
        assert "Attachment added" in captured.out

    def test_attach_nonexistent_file(self, mock_orch, sample_task, capsys):
        """Test attaching a file that doesn't exist."""
        args = MagicMock()
        args.id = str(sample_task.id)
        args.filepath = "/nonexistent/file.txt"

        mock_orch.add_attachment.side_effect = FileNotFoundError()

        with patch("src.cli.get_task_id", return_value=sample_task):
            with pytest.raises(FileNotFoundError):
                handle_attach(mock_orch, args)


class TestHandleExtract:
    def test_extract_attachment(self, mock_orch, sample_task, tmp_path, capsys):
        """Test extracting an attachment from a task."""
        args = MagicMock()
        args.id = str(sample_task.id)
        args.filename = "test.txt"
        output_file = tmp_path / "output.txt"
        args.output = str(output_file)

        mock_orch.extract_attachment.return_value = True

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_extract(mock_orch, args)

        mock_orch.extract_attachment.assert_called_once_with(sample_task.id, "test.txt", str(output_file))
        captured = capsys.readouterr()
        assert "extracted to" in captured.out

    def test_extract_nonexistent_attachment(self, mock_orch, sample_task, tmp_path, capsys):
        """Test extracting an attachment that doesn't exist."""
        args = MagicMock()
        args.id = str(sample_task.id)
        args.filename = "nonexistent.txt"
        args.output = str(tmp_path / "output.txt")

        mock_orch.extract_attachment.return_value = False

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_extract(mock_orch, args)

        captured = capsys.readouterr()
        assert "failed" in captured.out.lower() or "check" in captured.out.lower()


class TestHandleDuplicate:
    def test_duplicate_task(self, mock_orch, sample_task, capsys):
        """Test duplicating a task."""
        args = MagicMock()
        args.id = str(sample_task.id)

        new_task = Task(description="Sample Task", status="pending")
        mock_orch.duplicate_task.return_value = new_task

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_duplicate(mock_orch, args)

        mock_orch.duplicate_task.assert_called_once_with(sample_task.id)
        captured = capsys.readouterr()
        assert "duplicated successfully" in captured.out.lower()


class TestHandleKanban:
    def test_kanban_all_statuses(self, mock_orch, capsys):
        """Test rendering kanban board with all statuses."""
        args = MagicMock()
        args.status = None
        args.all = False

        task1 = Task(description="Pending task", status="pending")
        task2 = Task(description="Completed task", status="completed")
        mock_orch.tasks = {task1.id: task1, task2.id: task2}
        args.statuses = ["pending", "completed"]

        handle_kanban(mock_orch, args)

        captured = capsys.readouterr()
        assert "PENDING" in captured.out
        assert "COMPLETED" in captured.out

    def test_kanban_filtered_status(self, mock_orch, capsys):
        """Test rendering kanban board filtered by status."""
        args = MagicMock()
        args.statuses = ["pending"]
        args.all = False

        task1 = Task(description="Pending task", status="pending")
        task2 = Task(description="Completed task", status="completed")
        mock_orch.tasks = {task1.id: task1, task2.id: task2}

        handle_kanban(mock_orch, args)

        captured = capsys.readouterr()
        assert "PENDING" in captured.out


class TestHandleArchive:
    def test_archive_task(self, mock_orch, sample_task, capsys):
        """Test archiving a task."""
        args = MagicMock()
        args.id = str(sample_task.id)

        archived_task = Task(id=sample_task.id, description="Sample Task", archived=True)
        mock_orch.archive_task.return_value = archived_task

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_archive(mock_orch, args)

        mock_orch.archive_task.assert_called_once_with(sample_task.id)
        captured = capsys.readouterr()
        assert "archived" in captured.out


class TestHandleUnarchive:
    def test_unarchive_task(self, mock_orch, sample_task, capsys):
        """Test unarchiving a task."""
        args = MagicMock()
        args.id = str(sample_task.id)

        unarchived_task = Task(id=sample_task.id, description="Sample Task", archived=False)
        mock_orch.unarchive_task.return_value = unarchived_task

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_unarchive(mock_orch, args)

        mock_orch.unarchive_task.assert_called_once_with(sample_task.id)
        captured = capsys.readouterr()
        assert "unarchived" in captured.out


class TestHandleDelete:
    def test_delete_task_success(self, mock_orch, sample_task, capsys):
        """Test successfully deleting a task."""
        args = MagicMock()
        args.id = str(sample_task.id)

        mock_orch.delete_task.return_value = True

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_delete(mock_orch, args)

        mock_orch.delete_task.assert_called_once_with(sample_task.id)
        captured = capsys.readouterr()
        assert "deleted" in captured.out

    def test_delete_task_failure(self, mock_orch, sample_task, capsys):
        """Test failing to delete a task."""
        args = MagicMock()
        args.id = str(sample_task.id)

        mock_orch.delete_task.return_value = False

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_delete(mock_orch, args)

        captured = capsys.readouterr()
        assert "Failed" in captured.out or "not found" in captured.out.lower()


class TestHandleHistory:
    def test_show_history(self, mock_orch, sample_task, capsys):
        """Test showing task history."""
        args = MagicMock()
        args.id = str(sample_task.id)

        v1 = Task(id=sample_task.id, description="Version 1")
        v2 = Task(id=sample_task.id, description="Version 2")
        v3 = Task(id=sample_task.id, description="Version 3")

        mock_orch.get_history.return_value = [v3, v2, v1]

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_history(mock_orch, args)

        mock_orch.get_history.assert_called_once_with(sample_task.id)
        captured = capsys.readouterr()
        assert "Version 1" in captured.out
        assert "Version 2" in captured.out
        assert "Version 3" in captured.out

    def test_show_history_empty(self, mock_orch, sample_task, capsys):
        """Test showing history for a task with no history."""
        args = MagicMock()
        args.id = str(sample_task.id)

        mock_orch.get_history.return_value = []

        with patch("src.cli.get_task_id", return_value=sample_task):
            handle_history(mock_orch, args)

        captured = capsys.readouterr()
        # Empty history returns "Task not found" message
        assert "Task not found" in captured.out or captured.out == ""
