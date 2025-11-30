import hashlib
import json
import os
from typing import Any, Dict, Optional
from uuid import UUID

class ObjectStore:
    def __init__(self, root_dir: str = ".todo_store"):
        self.root_dir = root_dir
        self.objects_dir = os.path.join(root_dir, "objects")
        self.refs_dir = os.path.join(root_dir, "refs")
        self._init_storage()

    def _init_storage(self):
        os.makedirs(self.objects_dir, exist_ok=True)
        os.makedirs(self.refs_dir, exist_ok=True)

    def _compute_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def store_blob(self, data: bytes) -> str:
        """Stores raw binary data and returns its hash."""
        content_hash = self._compute_hash(data)
        path = os.path.join(self.objects_dir, content_hash)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(data)
        return content_hash

    def store_json(self, data: Dict[str, Any]) -> str:
        """Stores a dictionary as canonical JSON and returns its hash."""
        # Sort keys to ensure canonical representation
        json_bytes = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        content_hash = self._compute_hash(json_bytes)
        path = os.path.join(self.objects_dir, content_hash)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(json_bytes)
        return content_hash

    def get_object(self, content_hash: str) -> Optional[bytes]:
        """Retrieves raw object data by hash."""
        path = os.path.join(self.objects_dir, content_hash)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        return None

    def get_json(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves and parses a JSON object by hash."""
        data = self.get_object(content_hash)
        if data:
            return json.loads(data.decode("utf-8"))
        return None

    def update_ref(self, task_id: UUID, content_hash: str):
        """Updates the reference (HEAD) for a task to point to a new hash."""
        path = os.path.join(self.refs_dir, str(task_id))
        with open(path, "w") as f:
            f.write(content_hash)

    def get_ref(self, task_id: UUID) -> Optional[str]:
        """Gets the current hash for a task."""
        path = os.path.join(self.refs_dir, str(task_id))
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read().strip()
        return None

    def delete_object(self, content_hash: str) -> bool:
        """Deletes an object by hash. Returns True if deleted, False if not found."""
        path = os.path.join(self.objects_dir, content_hash)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
