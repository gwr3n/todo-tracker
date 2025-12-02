import os
import pytest
import hashlib
from src.tracker import TodoTracker


@pytest.fixture
def clean_store(tmp_path):
    store_dir = tmp_path / "store"
    orch = TodoTracker(root_dir=str(store_dir))
    return orch


def test_persistence(clean_store):
    orch = clean_store
    task = orch.add_task("Persist me")
    task_id = task.id

    # Simulate app restart
    new_orch = TodoTracker(root_dir=orch.storage.root_dir)

    loaded_task = new_orch.get_task(task_id)
    assert loaded_task is not None
    assert loaded_task.description == "Persist me"
    assert loaded_task.id == task_id


def test_history(clean_store):
    orch = clean_store
    task = orch.add_task("Version 1")

    # Update 1
    v2 = orch.update_task(task.id, description="Version 2")
    assert v2.description == "Version 2"
    assert v2.parent is not None

    # Update 2
    v3 = orch.update_task(task.id, description="Version 3")
    assert v3.description == "Version 3"
    assert v3.parent == v2.version_hash

    # Check history
    history = orch.get_history(task.id)
    assert len(history) == 3
    assert history[0].description == "Version 3"
    assert history[1].description == "Version 2"
    assert history[2].description == "Version 1"


def test_attachment_deduplication(clean_store, tmp_path):
    orch = clean_store

    # Create a dummy file
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Hello World")

    task1 = orch.add_task("Task 1")
    orch.add_attachment(task1.id, str(test_file))

    task2 = orch.add_task("Task 2")
    orch.add_attachment(task2.id, str(test_file))

    # Check storage
    objects_dir = os.path.join(orch.storage.root_dir, "objects")

    # We expect:
    # 1. Task 1 v1 (no attachment)
    # 2. Task 1 v2 (with attachment)
    # 3. Task 2 v1 (no attachment)
    # 4. Task 2 v2 (with attachment)
    # 5. The attachment blob ITSELF (only once!)

    content_hash = hashlib.sha256(b"Hello World").hexdigest()

    assert os.path.exists(os.path.join(objects_dir, content_hash))

    # Verify that both tasks point to this hash
    t1 = orch.get_task(task1.id)
    t2 = orch.get_task(task2.id)

    assert t1.attachments[0].content_hash == content_hash
    assert t2.attachments[0].content_hash == content_hash
