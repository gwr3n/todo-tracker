from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class Attachment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    content_hash: str

class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    description: str
    deadline: Optional[datetime] = None
    attachments: List[Attachment] = Field(default_factory=list)
    status: str = "pending"
    archived: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    parent: Optional[str] = None  # Hash of the previous version
    version_hash: Optional[str] = None  # Hash of this version's content
