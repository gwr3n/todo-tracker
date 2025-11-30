from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from .models import Task, Attachment
from .storage import ObjectStore

class TodoOrchestrator:
    def __init__(self, root_dir: str = ".todo_store"):
        self.storage = ObjectStore(root_dir=root_dir)
        self.tasks: Dict[UUID, Task] = {}
        self._load_state()

    def _load_state(self):
        """Reconstructs in-memory state from storage refs."""
        # In a real app, we might lazily load, but for now let's load all heads
        if not hasattr(self.storage, 'refs_dir'):
            return
            
        import os
        if os.path.exists(self.storage.refs_dir):
            for filename in os.listdir(self.storage.refs_dir):
                try:
                    task_id = UUID(filename)
                    head_hash = self.storage.get_ref(task_id)
                    if head_hash:
                        task_data = self.storage.get_json(head_hash)
                        if task_data:
                            task = Task(**task_data)
                            task.version_hash = head_hash
                            self.tasks[task_id] = task
                except ValueError:
                    continue

    def _commit_task(self, task: Task) -> Task:
        """Saves the task version and updates the ref."""
        # 1. Serialize task to dict
        task_data = task.model_dump(mode='json')
        
        # 2. Store JSON object
        version_hash = self.storage.store_json(task_data)
        
        # 3. Update task with its own version hash (in memory only, or we'd change the hash!)
        # Actually, the hash is of the content. We can store the hash on the object 
        # after saving, but it won't be IN the saved JSON.
        task.version_hash = version_hash
        
        # 4. Update Ref
        self.storage.update_ref(task.id, version_hash)
        
        # 5. Update in-memory cache
        self.tasks[task.id] = task
        
        return task

    def add_task(self, description: str, deadline=None, attachments=None) -> Task:
        # Process attachments if provided (assuming they are already Attachment objects or similar)
        # For this method, let's assume attachments is a list of Attachment objects
        # But wait, Attachment objects now need content_hash, not location.
        # The user interface for this might need to change, but let's stick to the signature.
        
        real_attachments = []
        if attachments:
            for att in attachments:
                if isinstance(att, Attachment):
                    real_attachments.append(att)
        
        task = Task(
            description=description, 
            deadline=deadline, 
            attachments=real_attachments
        )
        return self._commit_task(task)

    def get_task(self, task_id: UUID) -> Optional[Task]:
        return self.tasks.get(task_id)

    def update_task(self, task_id: UUID, **updates) -> Optional[Task]:
        current_task = self.get_task(task_id)
        if not current_task:
            return None
        
        # Create new task version
        updated_data = current_task.model_copy(update=updates)
        
        # Set parent to the hash of the PREVIOUS version (which is current_task.version_hash)
        # Ensure current_task has a version_hash. If it was just loaded, it should.
        if not current_task.version_hash:
             # Fallback: calculate it if missing (shouldn't happen if loaded correctly)
             pass 

        updated_data.parent = current_task.version_hash
        updated_data.modified_at = datetime.now()
        
        # Commit new version
        return self._commit_task(updated_data)

    def delete_task(self, task_id: UUID) -> bool:
        # In a Git-like system, do we delete? Or just stop referencing?
        # For now, let's remove the ref and the in-memory object.
        # The objects remain (garbage collection would be a separate feature).
        if task_id in self.tasks:
            del self.tasks[task_id]
            # Remove ref file
            import os
            ref_path = os.path.join(self.storage.refs_dir, str(task_id))
            if os.path.exists(ref_path):
                os.remove(ref_path)
            return True
        return False

    def archive_task(self, task_id: UUID) -> Optional[Task]:
        """Archives a task by setting its archived flag to True."""
        return self.update_task(task_id, archived=True)

    def unarchive_task(self, task_id: UUID) -> Optional[Task]:
        """Unarchives a task by setting its archived flag to False."""
        return self.update_task(task_id, archived=False)

    def add_attachment(self, task_id: UUID, file_path: str) -> Optional[Task]:
        """Reads a file, stores it as a blob, and adds it to the task."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        # Read file
        try:
            with open(file_path, "rb") as f:
                content = f.read()
        except FileNotFoundError:
            return None
            
        # Store Blob
        content_hash = self.storage.store_blob(content)
        
        # Create Attachment object
        import os
        filename = os.path.basename(file_path)
        attachment = Attachment(filename=filename, content_hash=content_hash)
        
        # Update Task
        new_attachments = task.attachments + [attachment]
        return self.update_task(task_id, attachments=new_attachments)

    def get_history(self, task_id: UUID) -> List[Task]:
        """Returns the history of a task, newest first."""
        history = []
        current_task = self.get_task(task_id)
        
        while current_task:
            history.append(current_task)
            parent_hash = current_task.parent
            if not parent_hash:
                break
                
            # Load parent
            parent_data = self.storage.get_json(parent_hash)
            if parent_data:
                current_task = Task(**parent_data)
                current_task.version_hash = parent_hash # Important for continuity
            else:
                break
                
        return history

    def extract_attachment(self, task_id: UUID, filename: str, output_path: str) -> bool:
        """Extracts an attachment from a task and saves it to the specified path."""
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Find attachment by filename
        attachment = None
        for att in task.attachments:
            if att.filename == filename:
                attachment = att
                break
        
        if not attachment:
            return False
        
        # Retrieve blob content
        content = self.storage.get_object(attachment.content_hash)
        if not content:
            return False
        
        # Write to output path
        try:
            with open(output_path, "wb") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def get_task_version(self, task_id: UUID, version_number: int) -> Optional[Task]:
        """
        Returns a specific version of a task by version number.
        Version 1 is the oldest (first created), incrementing to the newest.
        """
        history = self.get_history(task_id)
        if not history:
            return None
        
        # history is newest-first, so reverse it for chronological order
        chronological = list(reversed(history))
        
        # Check bounds (1-indexed)
        if version_number < 1 or version_number > len(chronological):
            return None
        
        # Return the version (convert to 0-indexed)
        return chronological[version_number - 1]

    def duplicate_task(self, task_id: UUID) -> Optional[Task]:
        """
        Duplicates an existing task, creating a new task with the same
        description, deadline, and attachments, but with a new UUID and
        status reset to "pending".
        """
        source_task = self.get_task(task_id)
        if not source_task:
            return None
        
        # Create new task with copied properties
        new_task = Task(
            description=source_task.description,
            deadline=source_task.deadline,
            attachments=source_task.attachments.copy(),
            status="pending"
        )
        
        return self._commit_task(new_task)
