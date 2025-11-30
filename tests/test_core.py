import pytest
from src.models import Task, Attachment
from src.orchestrator import TodoOrchestrator
import os

@pytest.fixture
def orchestrator(tmp_path):
    return TodoOrchestrator(root_dir=str(tmp_path))

def test_task_creation():
    task = Task(description="Test task")
    assert task.description == "Test task"
    assert task.status == "pending"
    assert task.attachments == []
    assert task.id is not None

def test_orchestrator_add_task(orchestrator):
    task = orchestrator.add_task(description="New Task")
    assert task.description == "New Task"
    assert len(orchestrator.tasks) == 1
    assert orchestrator.get_task(task.id) == task

def test_orchestrator_update_task(orchestrator):
    task = orchestrator.add_task(description="Old Description")
    updated_task = orchestrator.update_task(task.id, description="New Description", status="completed")
    
    assert updated_task.description == "New Description"
    assert updated_task.status == "completed"
    assert orchestrator.get_task(task.id).description == "New Description"

def test_orchestrator_delete_task(orchestrator):
    task = orchestrator.add_task(description="To Delete")
    assert orchestrator.delete_task(task.id) is True
    assert orchestrator.get_task(task.id) is None
    assert orchestrator.delete_task(task.id) is False

def test_orchestrator_add_attachment(orchestrator, tmp_path):
    task = orchestrator.add_task(description="With Attachment")
    
    # Create a dummy file
    file_path = tmp_path / "test.txt"
    file_path.write_text("some content")
    
    updated_task = orchestrator.add_attachment(task.id, str(file_path))
    
    assert len(updated_task.attachments) == 1
    assert updated_task.attachments[0].filename == "test.txt"
    assert updated_task.attachments[0].content_hash is not None

def test_orchestrator_extract_attachment(orchestrator, tmp_path):
    task = orchestrator.add_task(description="With Attachment")
    
    # Create a dummy file
    original_file = tmp_path / "test.txt"
    original_content = "some important content"
    original_file.write_text(original_content)
    
    # Attach it
    orchestrator.add_attachment(task.id, str(original_file))
    
    # Extract to new location
    extracted_file = tmp_path / "extracted.txt"
    success = orchestrator.extract_attachment(task.id, "test.txt", str(extracted_file))
    
    assert success is True
    assert extracted_file.exists()
    assert extracted_file.read_text() == original_content

def test_get_task_version(orchestrator):
    task = orchestrator.add_task(description="Version 1")
    
    # Update twice
    orchestrator.update_task(task.id, description="Version 2")
    orchestrator.update_task(task.id, description="Version 3")
    
    # Get specific versions
    v1 = orchestrator.get_task_version(task.id, 1)
    v2 = orchestrator.get_task_version(task.id, 2)
    v3 = orchestrator.get_task_version(task.id, 3)
    
    assert v1.description == "Version 1"
    assert v2.description == "Version 2"
    assert v3.description == "Version 3"
    
    # Out of bounds
    assert orchestrator.get_task_version(task.id, 0) is None
    assert orchestrator.get_task_version(task.id, 4) is None

def test_duplicate_task(orchestrator, tmp_path):
    # Create task with attachments
    task = orchestrator.add_task(description="Original Task", deadline=None)
    
    # Add attachment
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    orchestrator.add_attachment(task.id, str(test_file))
    
    # Update status
    orchestrator.update_task(task.id, status="completed")
    
    # Get current task
    current = orchestrator.get_task(task.id)
    
    # Duplicate
    duplicate = orchestrator.duplicate_task(task.id)
    
    assert duplicate is not None
    assert duplicate.id != task.id  # Different UUID
    assert duplicate.description == "Original Task"
    assert duplicate.status == "pending"  # Reset status
    assert len(duplicate.attachments) == 1
    assert duplicate.attachments[0].filename == "test.txt"
    assert duplicate.attachments[0].content_hash == current.attachments[0].content_hash

def test_archive_task(orchestrator):
    task = orchestrator.add_task(description="Task to Archive")
    assert not task.archived
    
    updated = orchestrator.archive_task(task.id)
    assert updated.archived
    assert updated.id == task.id
    
    # Verify persistence
    loaded = orchestrator.get_task(task.id)
    assert loaded.archived

def test_unarchive_task(orchestrator):
    task = orchestrator.add_task(description="Task to Unarchive")
    orchestrator.archive_task(task.id)
    assert orchestrator.get_task(task.id).archived
    
    updated = orchestrator.unarchive_task(task.id)
    assert not updated.archived
    
    # Verify persistence
    loaded = orchestrator.get_task(task.id)
    assert not loaded.archived

def test_delete_task_with_attachments(orchestrator, tmp_path):
    # Create task with attachment
    test_file = tmp_path / "delete_test.txt"
    test_file.write_text("content to delete")
    
    task = orchestrator.add_task(description="Task with attachment")
    orchestrator.add_attachment(task.id, str(test_file))
    
    # Get content hash
    task = orchestrator.get_task(task.id)
    content_hash = task.attachments[0].content_hash
    
    # Verify blob exists
    assert orchestrator.storage.get_object(content_hash) is not None
    
    # Delete task
    orchestrator.delete_task(task.id)
    
    # Verify blob is gone
    assert orchestrator.storage.get_object(content_hash) is None

def test_delete_task_shared_attachment(orchestrator, tmp_path):
    # Create task A with attachment
    test_file = tmp_path / "shared.txt"
    test_file.write_text("shared content")
    
    task_a = orchestrator.add_task(description="Task A")
    task_a = orchestrator.add_attachment(task_a.id, str(test_file))
    
    # Duplicate to Task B
    task_b = orchestrator.duplicate_task(task_a.id)
    
    content_hash = task_a.attachments[0].content_hash
    
    # Delete Task A
    orchestrator.delete_task(task_a.id)
    
    # Verify blob still exists (used by B)
    assert orchestrator.storage.get_object(content_hash) is not None
    
    # Delete Task B
    orchestrator.delete_task(task_b.id)
    
    # Verify blob is gone
    assert orchestrator.storage.get_object(content_hash) is None

def test_delete_task(orchestrator):
    task = orchestrator.add_task(description="Task to Delete")
    
    # Delete
    success = orchestrator.delete_task(task.id)
    assert success
    
    # Verify gone
    assert orchestrator.get_task(task.id) is None
    
    # Delete non-existent
    assert not orchestrator.delete_task(task.id)
