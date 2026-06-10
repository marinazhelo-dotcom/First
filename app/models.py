from typing import Optional
from sqlmodel import Field, SQLModel
from enum import Enum
from datetime import datetime, UTC, timezone

class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ComputeJob(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=36)
    status: JobStatus = Field(default=JobStatus.PENDING, max_length=20)
    input_data: int # Say, matrix size or complexity level
    result: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))