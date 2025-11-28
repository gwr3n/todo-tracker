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
