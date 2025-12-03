import pytest
from src.storage import ObjectStore
from uuid import uuid4
import os
import json


@pytest.fixture
def storage(tmp_path):
    """Create a storage instance with temporary directory."""
    return ObjectStore(root_dir=str(tmp_path / "store"))


class TestStorageEdgeCases:
    def test_get_nonexistent_object(self, storage):
        """Test getting an object that doesn't exist."""
        fake_hash = "nonexistent_hash_12345"
        result = storage.get_object(fake_hash)
        assert result is None

    def test_get_nonexistent_json(self, storage):
        """Test getting a JSON object that doesn't exist."""
        fake_hash = "nonexistent_hash_12345"
        result = storage.get_json(fake_hash)
        assert result is None

    def test_get_ref_nonexistent_task(self, storage):
        """Test getting a ref for a task that doesn't exist."""
        fake_id = uuid4()
        result = storage.get_ref(fake_id)
        assert result is None

    def test_delete_nonexistent_object(self, storage):
        """Test deleting an object that doesn't exist."""
        fake_hash = "nonexistent_hash_12345"
        result = storage.delete_object(fake_hash)
        assert result is False

    def test_store_empty_blob(self, storage):
        """Test storing an empty blob."""
        empty_data = b""
        content_hash = storage.store_blob(empty_data)

        assert content_hash is not None
        retrieved = storage.get_object(content_hash)
        assert retrieved == b""

    def test_store_large_blob(self, storage):
        """Test storing a large blob (1MB)."""
        large_data = b"x" * (1024 * 1024)  # 1MB
        content_hash = storage.store_blob(large_data)

        retrieved = storage.get_object(content_hash)
        assert retrieved == large_data
        assert len(retrieved) == 1024 * 1024

    def test_store_duplicate_blob(self, storage):
        """Test that storing the same blob twice returns same hash."""
        data = b"test content"
        hash1 = storage.store_blob(data)
        hash2 = storage.store_blob(data)

        assert hash1 == hash2

        # Verify only one file exists
        object_path = os.path.join(storage.objects_dir, hash1)
        assert os.path.exists(object_path)

    def test_store_empty_json(self, storage):
        """Test storing an empty JSON object."""
        empty_dict = {}
        content_hash = storage.store_json(empty_dict)

        retrieved = storage.get_json(content_hash)
        assert retrieved == {}

    def test_store_json_with_special_characters(self, storage):
        """Test storing JSON with special characters."""
        data = {
            "description": "Test with 'quotes' and \"double quotes\"",
            "unicode": "Hello 世界 🌍",
            "special": "Line\nBreak\tTab",
        }

        content_hash = storage.store_json(data)
        retrieved = storage.get_json(content_hash)

        assert retrieved == data

    def test_store_json_canonical_order(self, storage):
        """Test that JSON keys are sorted for canonical representation."""
        data1 = {"b": 2, "a": 1, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}

        hash1 = storage.store_json(data1)
        hash2 = storage.store_json(data2)

        # Same content, different order -> same hash
        assert hash1 == hash2

    def test_store_json_with_nested_objects(self, storage):
        """Test storing JSON with nested objects."""
        data = {"task": {"id": "123", "nested": {"deep": {"value": "test"}}}}

        content_hash = storage.store_json(data)
        retrieved = storage.get_json(content_hash)

        assert retrieved == data

    def test_update_ref_multiple_times(self, storage):
        """Test updating a ref multiple times."""
        task_id = uuid4()

        hash1 = "hash1"
        hash2 = "hash2"
        hash3 = "hash3"

        storage.update_ref(task_id, hash1)
        assert storage.get_ref(task_id) == hash1

        storage.update_ref(task_id, hash2)
        assert storage.get_ref(task_id) == hash2

        storage.update_ref(task_id, hash3)
        assert storage.get_ref(task_id) == hash3

    def test_get_json_corrupted_data(self, storage):
        """Test getting JSON when the stored data is corrupted."""
        # Store valid blob
        corrupted_data = b"not valid json {{"
        content_hash = storage.store_blob(corrupted_data)

        # Try to get as JSON
        with pytest.raises(json.JSONDecodeError):
            storage.get_json(content_hash)

    def test_storage_directories_created(self, tmp_path):
        """Test that storage directories are created automatically."""
        store_path = tmp_path / "new_store"
        storage = ObjectStore(root_dir=str(store_path))

        assert os.path.exists(storage.objects_dir)
        assert os.path.exists(storage.refs_dir)

    def test_hash_consistency(self, storage):
        """Test that hash computation is consistent."""
        data = b"test data for hashing"

        hash1 = storage._compute_hash(data)
        hash2 = storage._compute_hash(data)

        assert hash1 == hash2

        # Different data should produce different hash
        different_data = b"different test data"
        hash3 = storage._compute_hash(different_data)

        assert hash1 != hash3

    def test_store_blob_binary_data(self, storage):
        """Test storing actual binary data (not just text)."""
        # Create some binary data (e.g., image-like bytes)
        binary_data = bytes(range(256))

        content_hash = storage.store_blob(binary_data)
        retrieved = storage.get_object(content_hash)

        assert retrieved == binary_data

    def test_delete_object_and_verify(self, storage):
        """Test deleting an object and verifying it's gone."""
        data = b"to be deleted"
        content_hash = storage.store_blob(data)

        # Verify it exists
        assert storage.get_object(content_hash) is not None

        # Delete it
        result = storage.delete_object(content_hash)
        assert result is True

        # Verify it's gone
        assert storage.get_object(content_hash) is None

        # Try to delete again
        result = storage.delete_object(content_hash)
        assert result is False

    def test_ref_file_content(self, storage):
        """Test that ref files contain the correct hash."""
        task_id = uuid4()
        test_hash = "abc123def456"

        storage.update_ref(task_id, test_hash)

        # Read the ref file directly
        ref_path = os.path.join(storage.refs_dir, str(task_id))
        with open(ref_path, "r") as f:
            content = f.read().strip()

        assert content == test_hash

    def test_store_json_with_datetime(self, storage):
        """Test storing JSON with datetime objects (should be converted to string)."""
        from datetime import datetime

        data = {"created_at": datetime(2025, 12, 3, 12, 0, 0), "task": "test"}

        # Should not raise an error (datetime converted to string)
        content_hash = storage.store_json(data)
        retrieved = storage.get_json(content_hash)

        # Datetime should be converted to string
        assert isinstance(retrieved["created_at"], str)
        assert "2025" in retrieved["created_at"]

    def test_multiple_storage_instances_same_dir(self, tmp_path):
        """Test multiple storage instances pointing to the same directory."""
        store_path = tmp_path / "shared_store"

        storage1 = ObjectStore(root_dir=str(store_path))
        storage2 = ObjectStore(root_dir=str(store_path))

        # Store in first instance
        data = b"shared data"
        content_hash = storage1.store_blob(data)

        # Retrieve from second instance
        retrieved = storage2.get_object(content_hash)
        assert retrieved == data

    def test_store_very_long_json_keys(self, storage):
        """Test storing JSON with very long keys."""
        long_key = "k" * 1000
        data = {long_key: "value"}

        content_hash = storage.store_json(data)
        retrieved = storage.get_json(content_hash)

        assert long_key in retrieved
        assert retrieved[long_key] == "value"

    def test_store_json_with_null_values(self, storage):
        """Test storing JSON with null values."""
        data = {"field1": None, "field2": "value", "field3": None}

        content_hash = storage.store_json(data)
        retrieved = storage.get_json(content_hash)

        assert retrieved["field1"] is None
        assert retrieved["field2"] == "value"
        assert retrieved["field3"] is None
